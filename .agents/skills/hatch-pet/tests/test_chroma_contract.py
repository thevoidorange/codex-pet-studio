from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


SKILL_DIR = Path(__file__).resolve().parents[1]
PREPARE = SKILL_DIR / "scripts" / "prepare_pet_run.py"


class ChromaContractTest(unittest.TestCase):
    def make_reference(self, root: Path, matte: str = "#FF00FF") -> Path:
        path = root / "synthetic-reference.png"
        image = Image.new("RGB", (160, 160), matte)
        draw = ImageDraw.Draw(image)
        draw.rectangle((36, 36, 65, 123), fill="#00FF00")
        draw.rectangle((66, 36, 95, 123), fill="#FFFF00")
        draw.rectangle((96, 36, 123, 123), fill="#FF7F00")
        image.save(path)
        return path

    def run_prepare(
        self,
        run_dir: Path,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(PREPARE),
                "--pet-name",
                "Synthetic Contract Pet",
                "--pet-notes",
                "a geometric test mascot",
                "--output-dir",
                str(run_dir),
                *extra,
            ],
            capture_output=True,
            text=True,
        )

    def test_auto_reuses_high_confidence_existing_magenta_matte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = self.make_reference(root)
            run_dir = root / "run"

            completed = self.run_prepare(
                run_dir,
                "--reference",
                str(reference),
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            request = json.loads((run_dir / "pet_request.json").read_text())
            contract = request["chroma_key"]
            self.assertEqual("#FF00FF", contract["hex"])
            self.assertEqual("existing-matte", contract["selection"])
            self.assertEqual(
                "high",
                contract["source_matte_detections"][0]["confidence"],
            )
            manifest = json.loads(
                (run_dir / "imagegen-jobs.json").read_text()
            )
            self.assertNotIn("hex", manifest["chroma_contract"])
            self.assertEqual(
                "/chroma_key",
                manifest["chroma_contract"]["json_pointer"],
            )
            for prompt_path in (run_dir / "prompts").rglob("*.md"):
                prompt = prompt_path.read_text(encoding="utf-8")
                self.assertIn("#FF00FF", prompt, prompt_path)
                self.assertNotIn("#00FFFF", prompt, prompt_path)

    def test_subject_color_near_background_word_is_not_a_matte_directive(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_dir = Path(temporary_directory) / "run"

            completed = self.run_prepare(
                run_dir,
                "--style-notes",
                "A green furry pet on a clean simple background.",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            request = json.loads((run_dir / "pet_request.json").read_text())
            self.assertEqual([], request["chroma_key"]["text_matte_directives"])

    def test_conflicting_style_matte_fails_before_run_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = self.make_reference(root)
            run_dir = root / "run"

            completed = self.run_prepare(
                run_dir,
                "--reference",
                str(reference),
                "--style-notes",
                "Use a cyan #00FFFF matte background.",
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("conflicts", completed.stderr)
            self.assertFalse(run_dir.exists())

    def test_explicit_key_is_deterministic_when_source_and_request_agree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = self.make_reference(root)
            run_dir = root / "run"

            completed = self.run_prepare(
                run_dir,
                "--reference",
                str(reference),
                "--chroma-key",
                "#FF00FF",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            request = json.loads((run_dir / "pet_request.json").read_text())
            self.assertEqual("#FF00FF", request["chroma_key"]["hex"])
            self.assertEqual("manual", request["chroma_key"]["selection"])

    def test_explicit_key_cannot_silently_override_detected_source_matte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = self.make_reference(root)
            run_dir = root / "run"

            completed = self.run_prepare(
                run_dir,
                "--reference",
                str(reference),
                "--chroma-key",
                "#00FFFF",
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("existing saturated source matte", completed.stderr)
            self.assertFalse(run_dir.exists())

    def test_medium_confidence_matte_requires_explicit_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            reference = root / "ambiguous-reference.png"
            image = Image.new("RGB", (128, 128), "#FF00FF")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 19, 127), fill="#203060")
            image.save(reference)
            run_dir = root / "run"

            blocked = self.run_prepare(
                run_dir,
                "--reference",
                str(reference),
            )

            self.assertNotEqual(0, blocked.returncode)
            self.assertIn("needs confirmation", blocked.stderr)
            self.assertFalse(run_dir.exists())

            explicit = self.run_prepare(
                run_dir,
                "--reference",
                str(reference),
                "--chroma-key",
                "#FF00FF",
            )
            self.assertEqual(0, explicit.returncode, explicit.stderr)

    def test_conflicting_high_confidence_reference_mattes_always_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            magenta = root / "synthetic-magenta-reference.png"
            self.make_reference(root, "#FF00FF").replace(magenta)
            cyan = root / "synthetic-cyan-reference.png"
            self.make_reference(root, "#00FFFF").replace(cyan)
            run_dir = root / "run"

            completed = self.run_prepare(
                run_dir,
                "--reference",
                str(magenta),
                "--reference",
                str(cyan),
                "--chroma-key",
                "#FF00FF",
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("across references", completed.stderr)
            self.assertFalse(run_dir.exists())

    def test_force_refresh_preserves_completed_job_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run_dir = root / "run"
            first = self.run_prepare(run_dir)
            self.assertEqual(0, first.returncode, first.stderr)

            manifest_path = run_dir / "imagegen-jobs.json"
            manifest = json.loads(manifest_path.read_text())
            base = next(job for job in manifest["jobs"] if job["id"] == "base")
            base["status"] = "complete"
            base["attempt_count"] = 1
            base["completed_at"] = "2026-08-02T00:00:00+00:00"
            base["source_path"] = "synthetic-output.png"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            Image.new("RGBA", (64, 64), (20, 30, 40, 255)).save(
                run_dir / "decoded" / "base.png"
            )

            refreshed = self.run_prepare(run_dir, "--force")

            self.assertEqual(0, refreshed.returncode, refreshed.stderr)
            refreshed_manifest = json.loads(manifest_path.read_text())
            refreshed_base = next(
                job for job in refreshed_manifest["jobs"] if job["id"] == "base"
            )
            self.assertEqual("complete", refreshed_base["status"])
            self.assertEqual(1, refreshed_base["attempt_count"])
            self.assertEqual(
                "2026-08-02T00:00:00+00:00",
                refreshed_base["completed_at"],
            )
            self.assertEqual(2, refreshed_manifest["schema_version"])


if __name__ == "__main__":
    unittest.main()
