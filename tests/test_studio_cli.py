from __future__ import annotations

import contextlib
import http.server
import importlib.util
import inspect
import json
import re
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
import zipfile
import zlib
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / ".agents" / "skills" / "pet-studio" / "scripts" / "studio.py"
PREVIEW_SCHEMA = (
    REPO_ROOT
    / ".agents"
    / "skills"
    / "pet-studio"
    / "schemas"
    / "preview-config.schema.json"
)
PREVIEW_DATA = REPO_ROOT / "previewer" / "preview-data.js"


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
        ">I", zlib.crc32(kind + payload) & 0xFFFFFFFF
    )


def make_png(
    width: int,
    height: int,
    text: bytes | None = None,
    *,
    alpha_mode: str = "mixed",
    filter_type: int = 0,
    bit_depth: int = 8,
    color_type: int = 6,
    interlace: int = 0,
) -> bytes:
    result = b"\x89PNG\r\n\x1a\n"
    result += png_chunk(
        b"IHDR",
        struct.pack(
            ">IIBBBBB",
            width,
            height,
            bit_depth,
            color_type,
            0,
            0,
            interlace,
        ),
    )
    if text is not None:
        result += png_chunk(b"tEXt", text)
    decoded_rows: list[bytes] = []
    for y in range(height):
        decoded_row = bytearray()
        for x in range(width):
            if alpha_mode == "opaque":
                alpha = 255
            elif alpha_mode == "transparent":
                alpha = 0
            elif alpha_mode == "mixed":
                alpha = 255 if x < max(1, width // 2) else 0
                if width == 1 and height > 1:
                    alpha = 255 if y % 2 == 0 else 0
            else:
                raise ValueError(f"Unknown alpha mode: {alpha_mode}")
            decoded_row.extend((32, 48, 64, alpha))
        decoded_rows.append(bytes(decoded_row))

    rows = bytearray()
    previous = bytes(width * 4)
    for decoded_row in decoded_rows:
        rows.append(filter_type)
        if filter_type > 4:
            rows.extend(decoded_row)
            previous = decoded_row
            continue
        encoded_row = bytearray(len(decoded_row))
        for index, value in enumerate(decoded_row):
            left = decoded_row[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            else:
                prediction = left + above - upper_left
                distance_left = abs(prediction - left)
                distance_above = abs(prediction - above)
                distance_upper_left = abs(prediction - upper_left)
                if (
                    distance_left <= distance_above
                    and distance_left <= distance_upper_left
                ):
                    predictor = left
                elif distance_above <= distance_upper_left:
                    predictor = above
                else:
                    predictor = upper_left
            encoded_row[index] = (value - predictor) & 0xFF
        rows.extend(encoded_row)
        previous = decoded_row
    result += png_chunk(b"IDAT", zlib.compress(bytes(rows)))
    result += png_chunk(b"IEND", b"")
    return result


def make_header_only_png(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IEND", b"")
    )


def make_webp_vp8x(width: int, height: int) -> bytes:
    payload = b"\x00\x00\x00\x00"
    payload += (width - 1).to_bytes(3, "little")
    payload += (height - 1).to_bytes(3, "little")
    chunk = b"VP8X" + struct.pack("<I", len(payload)) + payload
    return b"RIFF" + struct.pack("<I", len(chunk) + 4) + b"WEBP" + chunk


def load_studio_module():
    module_name = "pet_studio_cli_for_tests"
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load studio.py for direct transaction testing.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def serve_config_responses(
    responses: list[tuple[int, bytes, dict[str, str] | None]],
):
    class ConfigHandler(http.server.BaseHTTPRequestHandler):
        request_count = 0

        def do_GET(self) -> None:
            if urllib.parse.urlsplit(self.path).path != "/build/review/preview.json":
                self.send_error(404)
                return
            index = min(type(self).request_count, len(responses) - 1)
            type(self).request_count += 1
            status, body, headers = responses[index]
            self.send_response(status)
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ConfigHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", ConfigHandler
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


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

    def write_preview_config(self, root: Path) -> tuple[Path, dict]:
        config = {
            "schemaVersion": 1,
            "pet": {"name": "Example Pet"},
            "versions": [
                {
                    "id": "v001",
                    "displayName": "v001",
                    "atlasUrl": "./v001/spritesheet.webp",
                },
                {
                    "id": "v002",
                    "displayName": "v002",
                    "atlasUrl": "./v002/spritesheet.webp",
                    "customCandidateField": {"preserve": True},
                    "frameTakes": [
                        {
                            "stateId": "idle",
                            "frameIndex": 1,
                            "takes": [
                                {
                                    "id": "t001",
                                    "label": "Take 01",
                                    "atlasSlot": {"row": 0, "column": 0},
                                },
                                {
                                    "id": "t003",
                                    "label": "Take 03",
                                    "atlasSlot": {"row": 0, "column": 2},
                                },
                            ],
                        }
                    ],
                },
            ],
            "customTopLevelField": {"preserve": "yes"},
        }
        path = root / "build" / "review" / "preview.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return path, config

    def test_init_doctor_and_preview_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            second_init = self.run_cli("init", "--root", str(root))
            self.assertIn("already initialized", second_init.stdout)
            self.assertTrue((root / "pet-studio.json").is_file())
            self.assertTrue((root / ".pet-studio-private.json").is_file())
            self.assertTrue((root / "design" / "takes").is_dir())
            (root / "previewer").mkdir()
            (root / "previewer" / "index.html").write_text("<!doctype html>", encoding="utf-8")
            doctor = self.run_cli("doctor", "--root", str(root), "--json")
            payload = json.loads(doctor.stdout)
            self.assertTrue(payload["ok"])
            preview = self.run_cli("preview", "--root", str(root), "--check")
            self.assertIn("/previewer/", preview.stdout)

    def test_preview_server_has_no_timing_write_api(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "/__pet-studio__/session",
            "/__pet-studio__/timing",
            "timing_write_token",
            "timing_write_enabled",
            "def do_POST",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_take_help_and_preview_schema_are_available(self) -> None:
        help_result = self.run_cli("take", "--help")
        self.assertIn("add", help_result.stdout)
        schema = json.loads(PREVIEW_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schemaVersion"]["const"], 1)
        self.assertIn("frameTakeGroup", schema["$defs"])
        asset_pattern = schema["$defs"]["take"]["properties"]["assetUrl"]["pattern"]
        self.assertIsNotNone(re.fullmatch(asset_pattern, "./takes/t001.png"))
        for unsafe in (
            "javascript:alert(1)",
            "//example.com/t001.png",
            "/takes/t001.png",
            "../takes/t001.png",
            "./takes/../t001.png",
            "./takes/%2e%2e/t001.png",
            "./takes/%252e%252e/t001.png",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertIsNone(re.fullmatch(asset_pattern, unsafe))

    def test_take_state_frame_counts_match_previewer_contract(self) -> None:
        studio = load_studio_module()
        preview_data = PREVIEW_DATA.read_text(encoding="utf-8")
        for state_id, expected_count in studio.TAKE_STATE_FRAME_COUNTS.items():
            state_tail = preview_data.split(f'id: "{state_id}"', 1)[1]
            duration_text = state_tail.split("durations: [", 1)[1].split("]", 1)[0]
            durations = [value.strip() for value in duration_text.split(",") if value.strip()]
            self.assertEqual(
                len(durations),
                expected_count,
                f"{state_id} must match the fixed Previewer contract",
            )

    def test_take_command_validates_the_exact_asset_bytes_it_registers(self) -> None:
        studio = load_studio_module()
        command_source = inspect.getsource(studio.command_take_add_with_context)
        self.assertIn("read_take_png(", command_source)
        self.assertNotIn("read_image_file(", command_source)
        self.assertNotIn("read_image_dimensions(", command_source)
        self.assertNotIn("asset_source.read_bytes(", command_source)

    def test_take_png_requires_decodable_rgba_with_visible_transparency(self) -> None:
        studio = load_studio_module()
        path = Path("candidate.png")
        for filter_type in range(5):
            studio.validate_take_png(
                make_png(192, 208, filter_type=filter_type),
                path,
            )
        valid = make_png(192, 208)

        bad_crc = bytearray(valid)
        idat_type_offset = valid.index(b"IDAT")
        bad_crc[idat_type_offset + 4] ^= 0x01
        invalid_cases = {
            "header-only": make_header_only_png(192, 208),
            "truncated": valid[:-4],
            "bad CRC": bytes(bad_crc),
            "fully transparent": make_png(
                192,
                208,
                alpha_mode="transparent",
            ),
            "fully opaque": make_png(192, 208, alpha_mode="opaque"),
            "invalid filter": make_png(192, 208, filter_type=5),
            "wrong bit depth": make_png(192, 208, bit_depth=16),
            "interlaced": make_png(192, 208, interlace=1),
            "WebP": make_webp_vp8x(192, 208),
        }
        for label, image in invalid_cases.items():
            with self.subTest(label=label):
                with self.assertRaises(studio.StudioError):
                    studio.validate_take_png(image, path)

    def test_take_asset_url_rejects_absolute_and_traversal_forms(self) -> None:
        studio = load_studio_module()
        studio.validate_take_asset_url(
            "./takes/v002/idle/f02/t004.png",
            "assetUrl",
        )
        for unsafe in (
            "/takes/t001.png",
            "../takes/t001.png",
            "./takes/../t001.png",
            "./takes/%2e%2e/t001.png",
            "./takes/%2E%2E%2Ft001.png",
            "./takes/%252e%252e/t001.png",
            r".\takes\..\t001.png",
        ):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(studio.StudioError):
                    studio.validate_take_asset_url(unsafe, "assetUrl")

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

    def test_take_add_registers_standalone_frame_and_preserves_review_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            config_path, original = self.write_preview_config(root)
            source = root / "design" / "takes" / "new-frame.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(make_png(192, 208))
            review_url = (
                "/previewer/?config=../build/review/preview.json"
                "&candidate=v002&state=idle&frame=2&take=original&qa=one"
            )
            config_bytes = config_path.read_bytes()
            with serve_config_responses([(200, config_bytes, None)]) as (
                origin,
                handler,
            ):
                review_url = origin + review_url
                completed = self.run_cli(
                    "take",
                    "add",
                    "--root",
                    str(root),
                    "--review-url",
                    review_url,
                    "--asset",
                    str(source),
                    "--json",
                )
                self.assertEqual(handler.request_count, 2)
            result = json.loads(completed.stdout)
            self.assertEqual(result["takeId"], "t004")
            self.assertEqual(result["frame"], 2)
            self.assertEqual(result["frameIndex"], 1)
            self.assertFalse(result["checkOnly"])

            updated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(
                updated["customTopLevelField"],
                original["customTopLevelField"],
            )
            candidate = updated["versions"][1]
            self.assertEqual(
                candidate["customCandidateField"],
                original["versions"][1]["customCandidateField"],
            )
            takes = candidate["frameTakes"][0]["takes"]
            self.assertEqual([take["id"] for take in takes], ["t001", "t003", "t004"])
            self.assertEqual(
                takes[-1]["assetUrl"],
                "./takes/v002/idle/f02/t004.png",
            )
            copied = config_path.parent / "takes" / "v002" / "idle" / "f02" / "t004.png"
            self.assertEqual(copied.read_bytes(), source.read_bytes())

            query = urllib.parse.parse_qs(
                urllib.parse.urlsplit(result["reviewUrl"]).query
            )
            self.assertEqual(query["config"], ["../build/review/preview.json"])
            self.assertEqual(query["candidate"], ["v002"])
            self.assertEqual(query["state"], ["idle"])
            self.assertEqual(query["frame"], ["2"])
            self.assertEqual(query["take"], ["t004"])
            self.assertEqual(query["qa"], ["one"])

            second_url = review_url.replace(
                "state=idle&frame=2&take=original",
                "state=waiting&frame=6&take=original",
            )
            with serve_config_responses(
                [(200, config_path.read_bytes(), None)]
            ) as (origin, handler):
                second_url = origin + urllib.parse.urlsplit(second_url).path + (
                    "?" + urllib.parse.urlsplit(second_url).query
                )
                second = self.run_cli(
                    "take",
                    "add",
                    "--root",
                    str(root),
                    "--review-url",
                    second_url,
                    "--asset",
                    str(source),
                    "--json",
                )
                self.assertEqual(handler.request_count, 2)
            self.assertEqual(json.loads(second.stdout)["takeId"], "t001")
            updated = json.loads(config_path.read_text(encoding="utf-8"))
            new_group = updated["versions"][1]["frameTakes"][1]
            self.assertEqual(new_group["stateId"], "waiting")
            self.assertEqual(new_group["frameIndex"], 5)
            self.assertEqual(new_group["takes"][0]["id"], "t001")

    def test_take_add_check_is_read_only_and_rejects_bad_context_or_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            config_path, _ = self.write_preview_config(root)
            before = config_path.read_bytes()
            good_source = root / "design" / "take.png"
            good_source.parent.mkdir(parents=True, exist_ok=True)
            good_source.write_bytes(make_png(192, 208))
            base_url = (
                "file://"
                + str(root / "previewer" / "index.html")
                + "?config=../build/review/preview.json"
                + "&candidate=v002&state=idle&frame=2&take=original"
            )

            checked = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                base_url,
                "--asset",
                str(good_source),
                "--check",
                "--json",
            )
            self.assertTrue(json.loads(checked.stdout)["checkOnly"])
            self.assertEqual(config_path.read_bytes(), before)
            self.assertFalse((config_path.parent / "takes").exists())

            invalid_frame = base_url.replace("&frame=2", "&frame=7")
            result = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                invalid_frame,
                "--asset",
                str(good_source),
                expected=1,
            )
            self.assertIn("out of range", result.stderr)

            missing_candidate = base_url.replace("candidate=v002", "candidate=missing")
            result = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                missing_candidate,
                "--asset",
                str(good_source),
                expected=1,
            )
            self.assertIn("is not present", result.stderr)

            invalid_state = base_url.replace("state=idle", "state=unknown")
            result = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                invalid_state,
                "--asset",
                str(good_source),
                expected=1,
            )
            self.assertIn("Unknown Codex Pet state", result.stderr)

            escaped_config = base_url.replace(
                "../build/review/preview.json",
                "../outside.json",
            )
            (root / "outside.json").write_bytes(before)
            result = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                escaped_config,
                "--asset",
                str(good_source),
                expected=1,
            )
            self.assertIn("escapes", result.stderr)

            bad_source = root / "design" / "bad.png"
            bad_source.write_bytes(make_png(193, 208))
            result = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                base_url,
                "--asset",
                str(bad_source),
                expected=1,
            )
            self.assertIn("expected a standalone 192x208 frame", result.stderr)

            remote_url = (
                "http://example.com/previewer/"
                "?config=../build/review/preview.json"
                "&candidate=v002&state=idle&frame=2&take=original"
            )
            result = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                remote_url,
                "--asset",
                str(good_source),
                expected=1,
            )
            self.assertIn("loopback host", result.stderr)
            self.assertEqual(config_path.read_bytes(), before)

    def test_take_add_requires_an_explicit_focused_take(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            self.write_preview_config(root)
            source = root / "design" / "take.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(make_png(192, 208))
            base_url = (
                "file://"
                + str(root / "previewer" / "index.html")
                + "?config=../build/review/preview.json"
                + "&candidate=v002&state=idle&frame=2"
            )
            for suffix, message in (
                ("", "missing the 'take' parameter"),
                ("&take=", "empty 'take' parameter"),
                ("&take=missing", "Focused Take 'missing' is not loaded"),
            ):
                with self.subTest(suffix=suffix):
                    result = self.run_cli(
                        "take",
                        "add",
                        "--root",
                        str(root),
                        "--review-url",
                        base_url + suffix,
                        "--asset",
                        str(source),
                        "--check",
                        expected=1,
                    )
                    self.assertIn(message, result.stderr)

    def test_take_add_rejects_non_png_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            self.write_preview_config(root)
            source = root / "design" / "take.webp"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(make_webp_vp8x(192, 208))
            url = (
                "file://"
                + str(root / "previewer" / "index.html")
                + "?config=../build/review/preview.json"
                + "&candidate=v002&state=idle&frame=2&take=original"
            )
            result = self.run_cli(
                "take",
                "add",
                "--root",
                str(root),
                "--review-url",
                url,
                "--asset",
                str(source),
                "--check",
                expected=1,
            )
            self.assertIn("Take asset must be a PNG", result.stderr)

    def test_take_http_binding_rejects_other_checkout_redirect_and_lock_race(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            config_path, original = self.write_preview_config(root)
            source = root / "design" / "take.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(make_png(192, 208))
            local_bytes = config_path.read_bytes()
            other = json.loads(json.dumps(original))
            other["pet"]["name"] = "Another Checkout"
            other_bytes = json.dumps(other, indent=2).encode("utf-8")
            path_and_query = (
                "/previewer/?config=../build/review/preview.json"
                "&candidate=v002&state=idle&frame=2&take=original"
            )

            cases = (
                (
                    "other checkout",
                    [(200, other_bytes, None)],
                    "does not match this local project checkout",
                    1,
                ),
                (
                    "redirect",
                    [
                        (
                            302,
                            b"",
                            {"Location": "/build/review/preview.json"},
                        )
                    ],
                    "redirected with HTTP 302",
                    1,
                ),
                (
                    "changed while waiting for lock",
                    [
                        (200, local_bytes, None),
                        (200, other_bytes, None),
                    ],
                    "does not match this local project checkout",
                    2,
                ),
            )
            for label, responses, message, expected_requests in cases:
                with self.subTest(label=label):
                    with serve_config_responses(responses) as (origin, handler):
                        result = self.run_cli(
                            "take",
                            "add",
                            "--root",
                            str(root),
                            "--review-url",
                            origin + path_and_query,
                            "--asset",
                            str(source),
                            expected=1,
                        )
                        self.assertEqual(handler.request_count, expected_requests)
                    self.assertIn(message, result.stderr)
                    self.assertEqual(config_path.read_bytes(), local_bytes)
                    self.assertFalse((config_path.parent / "takes").exists())

    def test_take_add_rejects_reserved_or_colliding_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            config_path, _ = self.write_preview_config(root)
            source = root / "design" / "take.webp"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(make_webp_vp8x(192, 208))
            url = (
                "file://"
                + str(root / "previewer" / "index.html")
                + "?config=../build/review/preview.json"
                + "&candidate=v002&state=idle&frame=2&take=original"
            )
            before = config_path.read_bytes()
            for take_id, expected_message in (
                ("t001", "already exists"),
                ("original", "cannot be 'original'"),
                ("../t004", "URL-safe ASCII"),
            ):
                with self.subTest(take_id=take_id):
                    result = self.run_cli(
                        "take",
                        "add",
                        "--root",
                        str(root),
                        "--review-url",
                        url,
                        "--asset",
                        str(source),
                        "--id",
                        take_id,
                        expected=1,
                    )
                    self.assertIn(expected_message, result.stderr)
                    self.assertEqual(config_path.read_bytes(), before)

    def test_take_transaction_rolls_back_promoted_asset_if_config_replace_fails(self) -> None:
        studio = load_studio_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "preview.json"
            original_config = {
                "schemaVersion": 1,
                "pet": {"name": "Example Pet"},
                "versions": [
                    {
                        "id": "v001",
                        "atlasUrl": "./spritesheet.png",
                    }
                ],
            }
            config_path.write_text(json.dumps(original_config), encoding="utf-8")
            updated_config = json.loads(json.dumps(original_config))
            updated_config["versions"][0]["frameTakes"] = [
                {
                    "stateId": "idle",
                    "frameIndex": 0,
                    "takes": [
                        {
                            "id": "t001",
                            "label": "Take 01",
                            "assetUrl": "./takes/v001/idle/f01/t001.png",
                        }
                    ],
                }
            ]
            asset_path = root / "takes" / "v001" / "idle" / "f01" / "t001.png"
            original_bytes = config_path.read_bytes()

            def fail_config_replace(source, destination):
                raise OSError("simulated config replace failure")

            with mock.patch.object(studio.os, "replace", side_effect=fail_config_replace):
                with self.assertRaises(OSError):
                    studio.atomic_register_take(
                        config_path,
                        updated_config,
                        asset_path,
                        make_png(192, 208),
                    )
            self.assertEqual(config_path.read_bytes(), original_bytes)
            self.assertFalse(asset_path.exists())

    def test_take_add_serializes_writers_with_a_config_lock(self) -> None:
        studio = load_studio_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.initialize(root)
            config_path, _ = self.write_preview_config(root)
            source = root / "design" / "take.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(make_png(192, 208))
            url = (
                "file://"
                + str(root / "previewer" / "index.html")
                + "?config=../build/review/preview.json"
                + "&candidate=v002&state=idle&frame=2&take=original"
            )
            before = config_path.read_bytes()
            with studio.exclusive_take_config_lock(config_path):
                result = self.run_cli(
                    "take",
                    "add",
                    "--root",
                    str(root),
                    "--review-url",
                    url,
                    "--asset",
                    str(source),
                    expected=1,
                )
            self.assertIn("Another Take registration", result.stderr)
            self.assertEqual(config_path.read_bytes(), before)
            self.assertFalse((config_path.parent / "takes").exists())

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
