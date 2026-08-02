import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


SKILL_DIR = Path(__file__).resolve().parents[1]
COMPOSE = SKILL_DIR / "scripts" / "compose_atlas.py"
VALIDATE = SKILL_DIR / "scripts" / "validate_atlas.py"
ASSEMBLE = SKILL_DIR / "scripts" / "assemble_extended_atlas.py"
ROW_COUNTS = (6, 8, 8, 4, 5, 8, 6, 6, 6)


def make_atlas(path: Path, rows: int, *, include_looks: bool) -> None:
    image = Image.new("RGBA", (1536, rows * 208), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for row, frame_count in enumerate(ROW_COUNTS):
        for column in range(frame_count):
            left = column * 192
            top = row * 208
            draw.rectangle((left + 40, top + 40, left + 120, top + 140), fill="navy")
    if include_looks:
        for row in (9, 10):
            for column in range(8):
                left = column * 192
                top = row * 208
                draw.rectangle((left + 40, top + 40, left + 120, top + 140), fill="navy")
        draw.rectangle((6 * 192 + 40, 40, 6 * 192 + 120, 140), fill="navy")
    image.save(path)


class AtlasPhaseContractTest(unittest.TestCase):
    def run_validator(
        self,
        atlas: Path,
        *arguments: str,
        expected: int,
    ) -> dict:
        completed = subprocess.run(
            [sys.executable, str(VALIDATE), str(atlas), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            expected,
            completed.returncode,
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )
        return json.loads(completed.stdout)

    def test_standard_intermediate_requires_explicit_phase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            atlas = root / "standard.png"
            make_atlas(atlas, 9, include_looks=False)

            default_result = self.run_validator(atlas, expected=1)
            self.assertEqual("codex-pet-v2-final", default_result["artifact_phase"])
            self.assertFalse(default_result["delivery_ready"])
            self.assertIn("codex-pet-v2-final", default_result["errors"][0])

            intermediate = self.run_validator(
                atlas,
                "--phase",
                "standard-intermediate",
                expected=0,
            )
            self.assertTrue(intermediate["ok"])
            self.assertEqual(
                "standard-intermediate",
                intermediate["artifact_phase"],
            )
            self.assertFalse(intermediate["delivery_ready"])
            self.assertIn("stage-runtime", intermediate["next_step"])

    def test_final_phase_requires_real_look_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            padded = root / "padded.png"
            make_atlas(padded, 11, include_looks=False)
            padded_result = self.run_validator(padded, expected=1)
            self.assertFalse(padded_result["delivery_ready"])
            self.assertTrue(
                any("look-" in error and "empty" in error for error in padded_result["errors"])
            )

            final = root / "final.png"
            make_atlas(final, 11, include_looks=True)
            final_result = self.run_validator(final, expected=0)
            self.assertTrue(final_result["delivery_ready"])
            self.assertEqual("codex-pet-v2-final", final_result["artifact_phase"])
            self.assertEqual(2, final_result["sprite_version_number"])

            legacy_alias = self.run_validator(
                final,
                "--phase",
                "final-v2",
                expected=0,
            )
            self.assertEqual(
                "codex-pet-v2-final",
                legacy_alias["artifact_phase"],
            )

    def test_malformed_extra_row_returns_structured_geometry_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = root / "twelve-rows.png"
            make_atlas(malformed, 12, include_looks=True)

            result = self.run_validator(malformed, expected=1)

            self.assertFalse(result["ok"])
            self.assertEqual(12, result["rows"])
            self.assertTrue(
                any("expected 1536x2288" in error for error in result["errors"])
            )
            self.assertIn("Fix the listed validation errors", result["next_step"])

    def test_compose_and_assemble_manifests_name_their_phase_and_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            output = root / "standard.png"
            report = root / "standard.json"
            make_atlas(source, 9, include_looks=False)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(COMPOSE),
                    "--source-atlas",
                    str(source),
                    "--output",
                    str(output),
                    "--json-out",
                    str(report),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("standard-intermediate", result["artifact_phase"])
            self.assertFalse(result["delivery_ready"])
            self.assertIn("review-only", completed.stdout)
            self.assertIn("stage-runtime", result["next_step"])

            spec = importlib.util.spec_from_file_location("phase_assembler", ASSEMBLE)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            manifest_path = root / "extended.json"
            module.write_manifest(manifest_path, root / "extended.webp")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("codex-pet-v2-final", manifest["artifactPhase"])
            self.assertFalse(manifest["deliveryReady"])
            self.assertIn("--phase codex-pet-v2-final", manifest["nextStep"])


if __name__ == "__main__":
    unittest.main()
