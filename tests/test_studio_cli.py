from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / ".agents" / "skills" / "pet-studio" / "scripts" / "studio.py"


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
        ">I", zlib.crc32(kind + payload) & 0xFFFFFFFF
    )


def make_png(width: int, height: int, text: bytes | None = None) -> bytes:
    result = b"\x89PNG\r\n\x1a\n"
    result += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    if text is not None:
        result += png_chunk(b"tEXt", text)
    result += png_chunk(b"IEND", b"")
    return result


def make_webp_vp8x(width: int, height: int) -> bytes:
    payload = b"\x00\x00\x00\x00"
    payload += (width - 1).to_bytes(3, "little")
    payload += (height - 1).to_bytes(3, "little")
    chunk = b"VP8X" + struct.pack("<I", len(payload)) + payload
    return b"RIFF" + struct.pack("<I", len(chunk) + 4) + b"WEBP" + chunk


class StudioCliTests(unittest.TestCase):
    def run_cli(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != expected:
            self.fail(
                f"expected {expected}, got {completed.returncode}\n"
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )
        return completed

    def initialize(self, root: Path) -> None:
        self.run_cli("init", "--root", str(root), "--name", "Example Pet")

    def write_pet(self, root: Path, image: bytes, suffix: str = "png", version: int = 2) -> Path:
        pet_dir = root / "build" / "pet"
        pet_dir.mkdir(parents=True, exist_ok=True)
        sheet_name = f"spritesheet.{suffix}"
        (pet_dir / sheet_name).write_bytes(image)
        (pet_dir / "pet.json").write_text(
            json.dumps(
                {
                    "id": "example-pet",
                    "displayName": "Example Pet",
                    "description": "A neutral test pet.",
                    "spriteVersionNumber": version,
                    "spritesheetPath": sheet_name,
                }
            ),
            encoding="utf-8",
        )
        return pet_dir

    def test_init_doctor_and_preview_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            second_init = self.run_cli("init", "--root", str(root))
            self.assertIn("already initialized", second_init.stdout)
            self.assertTrue((root / "pet-studio.json").is_file())
            self.assertTrue((root / ".pet-studio-private.json").is_file())
            (root / "previewer").mkdir()
            (root / "previewer" / "index.html").write_text("<!doctype html>", encoding="utf-8")
            doctor = self.run_cli("doctor", "--root", str(root), "--json")
            payload = json.loads(doctor.stdout)
            self.assertTrue(payload["ok"])
            preview = self.run_cli("preview", "--root", str(root), "--check")
            self.assertIn("/previewer/", preview.stdout)

    def test_validate_png_and_webp_v2(self) -> None:
        for suffix, image in (
            ("png", make_png(1536, 2288)),
            ("webp", make_webp_vp8x(1536, 2288)),
        ):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.initialize(root)
                self.write_pet(root, image, suffix)
                result = self.run_cli("validate", "--root", str(root), "--json")
                payload = json.loads(result.stdout)
                self.assertEqual(payload["width"], 1536)
                self.assertEqual(payload["height"], 2288)
                self.assertEqual(payload["format"].casefold(), suffix)

    def test_validate_rejects_v1_and_bad_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            self.write_pet(root, make_png(1536, 1872), version=1)
            result = self.run_cli("validate", "--root", str(root), expected=1)
            self.assertIn("spriteVersionNumber must be 2", result.stderr)
            self.write_pet(root, make_png(100, 100), version=2)
            result = self.run_cli("validate", "--root", str(root), expected=1)
            self.assertIn("expected 1536x2288", result.stderr)

    def test_privacy_detects_local_path_secret_term_and_png_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            private_path = "/" + "Users" + "/sample-person/project"
            fake_key = "sk" + "-" + ("x" * 40)
            (root / "notes.txt").write_text(
                f"{private_path}\n{fake_key}\nprivate-character\n",
                encoding="utf-8",
            )
            (root / "image.png").write_bytes(
                make_png(1, 1, b"Comment\x00generated note")
            )
            result = self.run_cli(
                "privacy-check",
                "--root",
                str(root),
                "--blocked-term",
                "private-character",
                "--json",
                expected=1,
            )
            payload = json.loads(result.stdout)
            kinds = {item["kind"] for item in payload["findings"]}
            self.assertIn("absolute_or_private_path", kinds)
            self.assertIn("openai_key", kinds)
            self.assertIn("private_term", kinds)
            self.assertIn("image_metadata", kinds)

    def test_export_is_allowlisted_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / ".gitignore").write_text("inputs/\n", encoding="utf-8")
            skill_script = (
                root
                / ".agents"
                / "skills"
                / "pet-studio"
                / "scripts"
                / "studio.py"
            )
            skill_script.parent.mkdir(parents=True)
            skill_script.write_text("# fixture\n", encoding="utf-8")
            (root / "previewer").mkdir()
            (root / "previewer" / "index.html").write_text("<!doctype html>", encoding="utf-8")
            (root / "inputs" / "private-note.txt").write_text("not exported", encoding="utf-8")
            output_a = root / "first.zip"
            output_b = root / "second.zip"
            self.run_cli("export", "--root", str(root), "--output", str(output_a))
            self.run_cli("export", "--root", str(root), "--output", str(output_b))
            self.assertEqual(output_a.read_bytes(), output_b.read_bytes())
            with zipfile.ZipFile(output_a) as archive:
                names = set(archive.namelist())
                self.assertIn("README.md", names)
                self.assertIn("previewer/index.html", names)
                self.assertIn(".gitignore", names)
                self.assertIn(
                    ".agents/skills/pet-studio/scripts/studio.py",
                    names,
                )
                self.assertIn("export-manifest.json", names)
                self.assertNotIn("inputs/private-note.txt", names)
                self.assertNotIn(".pet-studio-private.json", names)

    def test_install_requires_destination_and_copies_only_pet_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            self.write_pet(root, make_png(1536, 2288))
            missing = subprocess.run(
                [sys.executable, str(SCRIPT), "install", "--root", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(missing.returncode, 2)
            destination = root / "installed"
            self.run_cli(
                "install",
                "--root",
                str(root),
                "--destination",
                str(destination),
            )
            target = destination / "example-pet"
            self.assertTrue((target / "pet.json").is_file())
            self.assertTrue((target / "spritesheet.png").is_file())
            self.assertEqual(
                {path.name for path in target.iterdir()},
                {"pet.json", "spritesheet.png"},
            )


if __name__ == "__main__":
    unittest.main()
