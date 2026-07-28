from __future__ import annotations

import http.client
import http.server
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
import zlib
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / ".agents" / "skills" / "pet-studio" / "scripts" / "studio.py"


def load_studio_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pet_studio_cli_tests", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


STUDIO = load_studio_module()


@contextmanager
def preview_server(root: Path, *, writable: bool = True) -> Iterator[int]:
    token = "unit-test-token" if writable else None
    STUDIO.NoCacheHandler.project_root = root
    STUDIO.NoCacheHandler.project_preview_dir = root / "previewer"
    STUDIO.NoCacheHandler.timing_write_enabled = writable
    STUDIO.NoCacheHandler.timing_write_token = token

    def handler(*args: object, **kwargs: object) -> STUDIO.NoCacheHandler:
        return STUDIO.NoCacheHandler(*args, directory=str(root), **kwargs)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield int(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request_json(
    port: int,
    method: str,
    path: str,
    payload: object | bytes | None = None,
    *,
    token: str | None = None,
    host_header: str | None = None,
) -> tuple[int, dict[str, object]]:
    if isinstance(payload, bytes):
        body = payload
    elif payload is None:
        body = None
    else:
        body = json.dumps(payload).encode("utf-8")
    headers: dict[str, str] = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["X-Pet-Studio-Token"] = token
    if host_header is not None:
        headers["Host"] = host_header
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        result = json.loads(response.read().decode("utf-8"))
        return response.status, result
    finally:
        connection.close()


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

    def test_preview_timing_endpoint_updates_only_durations_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            (root / "previewer").mkdir()
            (root / "previewer" / "index.html").write_text(
                "<!doctype html>",
                encoding="utf-8",
            )
            config_dir = root / "build" / "session with space"
            config_dir.mkdir(parents=True)
            preview_config = config_dir / "preview.json"
            preview_config.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "pet": {"name": "Private Test Pet"},
                        "versions": [{"id": "v001", "atlasUrl": "./sheet.webp"}],
                        "states": [
                            {
                                "id": "waving",
                                "label": "preserve-me",
                                "durations": [140, 140, 140, 280],
                            }
                        ],
                        "custom": {"preserve": True},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            previous_inode = preview_config.stat().st_ino

            with preview_server(root) as port:
                status, invalid_host = request_json(
                    port,
                    "GET",
                    "/__pet-studio__/session",
                    host_header="previewer.attacker.example",
                )
                self.assertEqual(421, status)
                self.assertEqual("invalid_host", invalid_host["error"])
                self.assertNotIn("token", invalid_host)

                status, session = request_json(
                    port,
                    "GET",
                    "/__pet-studio__/session",
                )
                self.assertEqual(200, status)
                self.assertEqual(
                    {"writable": True, "token": "unit-test-token"},
                    session,
                )

                status, denied = request_json(
                    port,
                    "POST",
                    "/__pet-studio__/timing",
                    {
                        "configPath": "/build/session%20with%20space/preview.json",
                        "states": [
                            {
                                "id": "idle",
                                "durations": [280, 110, 115, 140, 140, 320],
                            }
                        ],
                    },
                )
                self.assertEqual(403, status)
                self.assertEqual("invalid_token", denied["error"])

                status, result = request_json(
                    port,
                    "POST",
                    "/__pet-studio__/timing",
                    {
                        "configPath": "/build/session%20with%20space/preview.json",
                        "states": [
                            {
                                "id": "idle",
                                "durations": [280, 110, 115, 140, 140, 320],
                            },
                            {
                                "id": "waving",
                                "durations": [140, 150, 140, 280],
                            },
                        ],
                    },
                    token="unit-test-token",
                )
                self.assertEqual(200, status)
                self.assertEqual(
                    {
                        "ok": True,
                        "configPath": "build/session with space/preview.json",
                        "updatedStates": ["idle", "waving"],
                    },
                    result,
                )

            updated = json.loads(preview_config.read_text(encoding="utf-8"))
            self.assertEqual({"preserve": True}, updated["custom"])
            self.assertEqual("Private Test Pet", updated["pet"]["name"])
            states = {item["id"]: item for item in updated["states"]}
            self.assertEqual(
                [280, 110, 115, 140, 140, 320],
                states["idle"]["durations"],
            )
            self.assertEqual(
                [140, 150, 140, 280],
                states["waving"]["durations"],
            )
            self.assertEqual("preserve-me", states["waving"]["label"])
            self.assertNotEqual(previous_inode, preview_config.stat().st_ino)
            self.assertEqual([], list(config_dir.glob(".preview.json.*.tmp")))

    def test_preview_timing_endpoint_rejects_unsafe_targets_and_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            (root / "previewer").mkdir()
            (root / "previewer" / "index.html").write_text(
                "<!doctype html>",
                encoding="utf-8",
            )
            (root / "previewer" / "fixture.json").write_text(
                '{"schemaVersion": 1}',
                encoding="utf-8",
            )
            build_dir = root / "build"
            build_dir.mkdir(exist_ok=True)
            valid_config = build_dir / "preview.json"
            valid_config.write_text(
                '{"schemaVersion": 1, "versions": []}\n',
                encoding="utf-8",
            )
            symlink_config = build_dir / "linked.json"
            symlink_config.symlink_to(valid_config)
            idle_update = {
                "id": "idle",
                "durations": [280, 110, 110, 140, 140, 320],
            }

            with preview_server(root) as port:
                invalid_cases = (
                    {
                        "configPath": "/pet-studio.json",
                        "states": [idle_update],
                    },
                    {
                        "configPath": "/previewer/fixture.json",
                        "states": [idle_update],
                    },
                    {
                        "configPath": "/build/linked.json",
                        "states": [idle_update],
                    },
                    {
                        "configPath": "/build/%2e%2e/pet-studio.json",
                        "states": [idle_update],
                    },
                    {
                        "configPath": "/build/preview.json",
                        "states": [
                            {
                                "id": "idle",
                                "durations": [280, 110],
                            }
                        ],
                    },
                    {
                        "configPath": "/build/preview.json",
                        "states": [
                            {
                                "id": "unknown-state",
                                "durations": [100],
                            }
                        ],
                    },
                    {
                        "configPath": "/build/preview.json",
                        "states": [
                            {
                                "id": "idle",
                                "durations": [19, 110, 110, 140, 140, 320],
                            }
                        ],
                    },
                    {
                        "configPath": "/build/preview.json",
                        "states": [
                            {
                                "id": "idle",
                                "durations": [280, 110, 110, 140, 140, 5001],
                            }
                        ],
                    },
                )
                for payload in invalid_cases:
                    with self.subTest(payload=payload):
                        status, response = request_json(
                            port,
                            "POST",
                            "/__pet-studio__/timing",
                            payload,
                            token="unit-test-token",
                        )
                        self.assertEqual(400, status)
                        self.assertEqual("invalid_timing_update", response["error"])

                status, response = request_json(
                    port,
                    "POST",
                    "/__pet-studio__/timing",
                    b"x" * (STUDIO.MAX_TIMING_REQUEST_BYTES + 1),
                    token="unit-test-token",
                )
                self.assertEqual(413, status)
                self.assertEqual("request_too_large", response["error"])

            with preview_server(root, writable=False) as port:
                status, session = request_json(
                    port,
                    "GET",
                    "/__pet-studio__/session",
                )
                self.assertEqual(200, status)
                self.assertEqual({"writable": False, "token": None}, session)
                status, response = request_json(
                    port,
                    "POST",
                    "/__pet-studio__/timing",
                    {
                        "configPath": "/build/preview.json",
                        "states": [idle_update],
                    },
                    token="unit-test-token",
                )
                self.assertEqual(403, status)
                self.assertEqual("read_only", response["error"])

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
