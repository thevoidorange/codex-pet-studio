from __future__ import annotations

import contextlib
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path

from tests.test_studio_cli import make_png, make_runtime_atlas_png


ROOT = Path(__file__).resolve().parents[1]
CHROME_CANDIDATES = (
    os.environ.get("CHROME_BIN"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    shutil.which("google-chrome"),
    shutil.which("chromium"),
    shutil.which("chromium-browser"),
)
CHROME = next((Path(path) for path in CHROME_CANDIDATES if path and Path(path).is_file()), None)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return


@contextlib.contextmanager
def serve(root: Path):
    handler = functools.partial(QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@unittest.skipUnless(CHROME, "headless Chrome/Chromium is unavailable")
class PreviewerBrowserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "previewer", self.root / "previewer")
        example_dir = self.root / "examples" / "raincoat-cat"
        example_dir.mkdir(parents=True)
        shutil.copy2(
            ROOT / "examples" / "raincoat-cat" / "spritesheet.png",
            example_dir / "spritesheet.png",
        )
        review = self.root / "build" / "review"
        self.review = review
        (review / "candidates" / "healthy" / "static").mkdir(parents=True)
        (review / "candidates" / "opaque-sibling" / "static").mkdir(parents=True)
        (review / "candidates" / "healthy" / "static" / "original.png").write_bytes(
            make_png(32, 32, alpha_mode="mixed")
        )
        (
            review / "candidates" / "opaque-sibling" / "static" / "original.png"
        ).write_bytes(make_png(32, 32, alpha_mode="opaque"))
        config = {
            "schemaVersion": 1,
            "deliveryTarget": {"id": "codex-pet-v2", "revision": 2},
            "pet": {"name": "Sanitized Fixture"},
            "versions": [
                {
                    "id": "healthy",
                    "displayName": "Healthy",
                    "isDefault": True,
                    "static": {
                        "assetUrl": "./candidates/healthy/static/original.png",
                        "takes": [],
                    },
                    "stateIds": [],
                    "lookDirectionsAvailable": False,
                },
                {
                    "id": "opaque-sibling",
                    "displayName": "Opaque Sibling",
                    "static": {
                        "assetUrl": "./candidates/opaque-sibling/static/original.png",
                        "takes": [],
                    },
                    "stateIds": [],
                    "lookDirectionsAvailable": False,
                },
            ],
        }
        self.config = config
        (review / "preview.json").write_text(
            json.dumps(config, indent=2) + "\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def dump_dom(self, url: str) -> str:
        profile = self.root / f"chrome-{len(list(self.root.glob('chrome-*')))}"
        command = [
            str(CHROME),
            "--headless=new",
            "--disable-gpu",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--virtual-time-budget=6000",
            f"--user-data-dir={profile}",
            "--dump-dom",
            url,
        ]
        try:
            completed = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=12,
            )
            output = completed.stdout
        except subprocess.TimeoutExpired as error:
            # Some macOS Chrome builds emit a complete --dump-dom document but
            # keep the browser parent alive after renderer shutdown.  Python's
            # run() has already killed and reaped that parent here; accept only
            # a demonstrably complete document, never a partial timeout dump.
            output = error.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
        if "</html>" not in output:
            self.fail("headless Chrome did not produce a complete DOM document")
        return output

    def test_healthy_focus_renders_while_opaque_sibling_is_disabled(self) -> None:
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config=../build/review/preview.json"
                "&candidate=healthy&state=static&frame=1&take=original"
            )
        workspace = re.search(r'<section id="workspace"[^>]*>', dom)
        self.assertIsNotNone(workspace)
        self.assertNotIn("hidden", workspace.group(0))
        self.assertIn("candidates/healthy/static/original.png", dom)
        self.assertRegex(
            dom,
            r'<option value="opaque-sibling" disabled(?:="")?>'
            r'Opaque Sibling — unavailable · ASSET_FULLY_OPAQUE</option>',
        )

    def test_default_healthy_candidate_isolated_without_url_focus(self) -> None:
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config=../build/review/preview.json"
            )
        workspace = re.search(r'<section id="workspace"[^>]*>', dom)
        self.assertIsNotNone(workspace)
        self.assertNotIn("hidden", workspace.group(0))
        self.assertIn("candidates/healthy/static/original.png", dom)
        self.assertRegex(
            dom,
            r'<option value="opaque-sibling" disabled(?:="")?>'
            r'Opaque Sibling — unavailable · ASSET_FULLY_OPAQUE</option>',
        )

    def test_focused_opaque_candidate_fails_closed_with_safe_details(self) -> None:
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config=../build/review/preview.json"
                "&candidate=opaque-sibling&state=static&frame=1&take=original"
            )
        error_panel = re.search(r'<section id="configError"[^>]*>', dom)
        workspace = re.search(r'<section id="workspace"[^>]*>', dom)
        self.assertIsNotNone(error_panel)
        self.assertNotIn("hidden", error_panel.group(0))
        self.assertIn('tabindex="-1"', error_panel.group(0))
        self.assertIsNotNone(workspace)
        self.assertIn("hidden", workspace.group(0))
        self.assertIn('<dd id="configErrorCode">ASSET_FULLY_OPAQUE</dd>', dom)
        self.assertIn('<dd id="configErrorCandidate">opaque-sibling</dd>', dom)
        self.assertNotIn("/" + "Us" + "ers" + "/", dom)
        self.assertNotIn("Example.RaincoatCat: Character Study", dom)

    def test_global_target_mismatch_blocks_every_candidate(self) -> None:
        self.config["deliveryTarget"]["revision"] = 999
        (self.review / "preview.json").write_text(
            json.dumps(self.config, indent=2) + "\n", encoding="utf-8"
        )
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config=../build/review/preview.json"
                "&candidate=healthy&state=static&frame=1&take=original"
            )
        error_panel = re.search(r'<section id="configError"[^>]*>', dom)
        workspace = re.search(r'<section id="workspace"[^>]*>', dom)
        topbar = re.search(r'<header id="topbar"[^>]*>', dom)
        self.assertIsNotNone(error_panel)
        self.assertNotIn("hidden", error_panel.group(0))
        self.assertIsNotNone(workspace)
        self.assertIn("hidden", workspace.group(0))
        self.assertIsNotNone(topbar)
        self.assertIn("hidden", topbar.group(0))
        self.assertIn('<dd id="configErrorCode">TARGET_MISMATCH</dd>', dom)
        self.assertNotIn("Example.RaincoatCat: Character Study", dom)

    def test_unknown_declared_state_fails_before_asset_render(self) -> None:
        self.config["versions"][0]["stateIds"] = ["ghost-state"]
        (self.review / "preview.json").write_text(
            json.dumps(self.config, indent=2) + "\n", encoding="utf-8"
        )
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config=../build/review/preview.json"
                "&candidate=healthy&state=static&frame=1&take=original"
            )
        workspace = re.search(r'<section id="workspace"[^>]*>', dom)
        self.assertIsNotNone(workspace)
        self.assertIn("hidden", workspace.group(0))
        self.assertIn('<dd id="configErrorCode">UNKNOWN_STATE_ID</dd>', dom)
        self.assertIn('<dd id="configErrorCandidate">healthy</dd>', dom)
        self.assertNotIn("candidates/healthy/static/original.png&quot;", dom)

    def test_standard_intermediate_projection_uses_target_geometry(self) -> None:
        candidate_root = self.review / "candidates" / "runtime-review"
        (candidate_root / "static").mkdir(parents=True)
        (candidate_root / "runtime").mkdir(parents=True)
        (candidate_root / "static" / "original.png").write_bytes(
            make_png(32, 32, alpha_mode="mixed")
        )
        (candidate_root / "runtime" / "projection.png").write_bytes(
            make_runtime_atlas_png(11, state_ids=("idle",))
        )
        self.config["versions"].append(
            {
                "id": "runtime-review",
                "displayName": "Runtime Review",
                "static": {
                    "assetUrl": "./candidates/runtime-review/static/original.png",
                    "takes": [],
                },
                "atlasUrl": "./candidates/runtime-review/runtime/projection.png",
                "atlasPhase": "standard-intermediate",
                "stateIds": ["idle"],
                "lookDirectionsAvailable": False,
            }
        )
        (self.review / "preview.json").write_text(
            json.dumps(self.config, indent=2) + "\n", encoding="utf-8"
        )
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config=../build/review/preview.json"
                "&candidate=runtime-review&state=idle&frame=1&take=original"
            )
        workspace = re.search(r'<section id="workspace"[^>]*>', dom)
        badge = re.search(r'<span id="atlasPhaseBadge"[^>]*>', dom)
        look_tab = re.search(r'<button id="lookTab"[^>]*>', dom)
        self.assertIsNotNone(workspace)
        self.assertNotIn("hidden", workspace.group(0))
        self.assertIsNotNone(badge)
        self.assertNotIn("hidden", badge.group(0))
        self.assertIn("8×9 · REVIEW ONLY", dom)
        self.assertIsNotNone(look_tab)
        self.assertIn("disabled", look_tab.group(0))
        self.assertIn("projection.png", dom)
        self.assertIn("background-size: 800% 1100%", dom)

    def test_diagnostic_facts_redact_credentials_paths_and_long_payloads(self) -> None:
        private_root = "/" + "Us" + "ers"
        private_segment = "private" + "-person"
        username = "ali" + "ce"
        password = "sec" + "ret"
        unsafe_candidate = (
            f"https://{username}:{password}@example.test"
            f"{private_root}/{private_segment}/project"
            "?token=" + "x" * 320
        )
        encoded_candidate = urllib.parse.quote(unsafe_candidate, safe="")
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config=../build/review/preview.json"
                f"&candidate={encoded_candidate}"
            )
        self.assertIn(
            '<dd id="configErrorConfig">/build/review/preview.json</dd>',
            dom,
        )
        self.assertIn("https://example.test/[local path]?…", dom)
        self.assertNotIn(username, dom)
        self.assertNotIn(password, dom)
        self.assertNotIn(private_segment, dom)
        self.assertNotIn("x" * 80, dom)

    def test_file_config_reference_is_redacted(self) -> None:
        private_root = "/" + "Us" + "ers"
        private_segment = "private" + "-person"
        local_config = urllib.parse.quote(
            f"file://{private_root}/{private_segment}/Secret/preview.json",
            safe=":/",
        )
        with serve(self.root) as origin:
            dom = self.dump_dom(
                f"{origin}/previewer/?config={local_config}"
            )
        self.assertIn('<dd id="configErrorConfig">Local Previewer config</dd>', dom)
        self.assertNotIn(private_root + "/", dom)
        self.assertNotIn(private_segment, dom)

if __name__ == "__main__":
    unittest.main()
