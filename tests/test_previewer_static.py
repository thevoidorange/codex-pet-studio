from __future__ import annotations

import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEWER = ROOT / "previewer"


def parse_gif(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise AssertionError(f"Not a GIF: {path}")
    width, height = struct.unpack_from("<HH", data, 6)
    packed = data[10]
    cursor = 13
    if packed & 0x80:
        cursor += 3 * (2 ** ((packed & 0x07) + 1))

    delays: list[int] = []
    extension_labels: list[int] = []
    loop_count = None
    pending_delay = 0

    def read_sub_blocks(position: int) -> tuple[bytes, int]:
        payload = bytearray()
        while True:
            block_size = data[position]
            position += 1
            if block_size == 0:
                return bytes(payload), position
            payload.extend(data[position : position + block_size])
            position += block_size

    while cursor < len(data):
        marker = data[cursor]
        cursor += 1
        if marker == 0x3B:
            break
        if marker == 0x21:
            label = data[cursor]
            extension_labels.append(label)
            cursor += 1
            if label == 0xF9:
                block_size = data[cursor]
                cursor += 1
                block = data[cursor : cursor + block_size]
                cursor += block_size
                cursor += 1
                pending_delay = struct.unpack_from("<H", block, 1)[0]
            elif label == 0xFF:
                block_size = data[cursor]
                cursor += 1
                application = data[cursor : cursor + block_size]
                cursor += block_size
                payload, cursor = read_sub_blocks(cursor)
                if (
                    application.startswith(b"NETSCAPE")
                    and payload[:1] == b"\x01"
                ):
                    loop_count = struct.unpack_from("<H", payload, 1)[0]
            else:
                _, cursor = read_sub_blocks(cursor)
            continue
        if marker == 0x2C:
            descriptor = data[cursor : cursor + 9]
            cursor += 9
            if descriptor[8] & 0x80:
                cursor += 3 * (2 ** ((descriptor[8] & 0x07) + 1))
            cursor += 1
            _, cursor = read_sub_blocks(cursor)
            delays.append(pending_delay)
            pending_delay = 0
            continue
        raise AssertionError(f"Unexpected GIF marker 0x{marker:02x}: {path}")

    return {
        "size": (width, height),
        "delays": delays,
        "loop_count": loop_count,
        "extension_labels": extension_labels,
    }


class PreviewerStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (PREVIEWER / "index.html").read_text(encoding="utf-8")
        self.app = (PREVIEWER / "app.js").read_text(encoding="utf-8")
        self.data = (PREVIEWER / "preview-data.js").read_text(encoding="utf-8")
        self.i18n = (PREVIEWER / "i18n.js").read_text(encoding="utf-8")
        self.css = (PREVIEWER / "styles.css").read_text(encoding="utf-8")

    def test_static_references_and_dom_ids_exist(self) -> None:
        for reference in ("styles.css", "i18n.js", "preview-data.js", "app.js"):
            self.assertTrue((PREVIEWER / reference).is_file(), reference)
            self.assertIn(f"./{reference}", self.html)

        queried_ids = set(re.findall(r'querySelector\("#([^"]+)"\)', self.app))
        html_ids = set(re.findall(r'\bid="([^"]+)"', self.html))
        self.assertTrue(queried_ids)
        self.assertEqual(set(), queried_ids - html_ids)

    def test_uses_stable_v2_state_ids(self) -> None:
        expected = {
            "idle",
            "running-right",
            "running-left",
            "waving",
            "jumping",
            "failed",
            "waiting",
            "running",
            "review",
        }
        observed = set(re.findall(r'\bid:\s*"([^"]+)"', self.data))
        self.assertTrue(expected.issubset(observed))
        self.assertFalse({"moveRight", "moveLeft", "greeting", "working"} & observed)

    def test_timing_board_covers_all_standard_states(self) -> None:
        expected = [
            "idle",
            "running-right",
            "running-left",
            "waving",
            "jumping",
            "failed",
            "waiting",
            "running",
            "review",
        ]
        mechanics_block = self.data.split("mechanics: [", 1)[1].split(
            "],\n  backgrounds:",
            1,
        )[0]
        observed = re.findall(r'stateId:\s*"([^"]+)"', mechanics_block)
        self.assertEqual(expected, observed)
        self.assertIn("function withStateOverrides(", self.app)
        self.assertIn(
            "states: withStateOverrides(base.states, next.states)",
            self.app,
        )
        self.assertIn("function withMechanicsOverrides(", self.app)
        self.assertIn(
            "mechanics: withMechanicsOverrides(base.mechanics, next.mechanics)",
            self.app,
        )
        self.assertIn("const mechanicsBoards = config.states.map(", self.app)
        self.assertIn("states: mechanicsBoards.length", self.app)

        motion_boards = self.i18n.split("motionBoard: {")[1:]
        self.assertEqual(2, len(motion_boards))
        for board in motion_boards:
            for state_id in expected:
                state_key = re.escape(state_id)
                self.assertRegex(
                    board,
                    rf'(?:"{state_key}"|{state_key}):\s*\{{',
                    state_id,
                )

        state_frames = {
            state_id: len(
                re.search(
                    rf'id:\s*"{re.escape(state_id)}".*?durations:\s*\[([^\]]+)\]',
                    self.data,
                    re.DOTALL,
                )
                .group(1)
                .split(",")
            )
            for state_id in expected
        }
        mechanic_frames = {
            state_id: len(
                re.search(
                    rf'stateId:\s*"{re.escape(state_id)}".*?anchors:\s*\[([^\]]+)\]',
                    mechanics_block,
                    re.DOTALL,
                )
                .group(1)
                .split(",")
            )
            for state_id in expected
        }
        self.assertEqual(state_frames, mechanic_frames)
        self.assertEqual(57, sum(state_frames.values()))

    def test_version_and_locale_controls_are_generic(self) -> None:
        self.assertIn('id="versionSelect"', self.html)
        self.assertIn('id="languageSelect"', self.html)
        self.assertIn('new URLSearchParams(window.location.search).get("config")', self.app)
        self.assertIn("config.versions", self.app)
        self.assertIn("window.localStorage", self.app)
        self.assertIn('"zh-CN"', self.i18n)
        self.assertIn('"en"', self.i18n)

    def test_external_versions_keep_example_but_load_project_first(self) -> None:
        self.assertIn("withBundledExample(projectVersions, base.versions)", self.app)
        self.assertIn("return [...versions, example];", self.app)
        self.assertIn("isBundledExample: true", self.app)
        self.assertIn("isDefault: false", self.app)
        self.assertIn("config = normalizeConfig(loaded.data, loaded.isExternal)", self.app)
        self.assertIn('exampleVersion: "Example"', self.i18n)
        example_translation = "".join(chr(code) for code in (0x793A, 0x4F8B))
        self.assertIn(f'exampleVersion: "{example_translation}"', self.i18n)
        self.assertIn("version && version.isBundledExample", self.app)
        self.assertIn("? window.location.href", self.app)

    def test_bundled_example_has_native_gifs(self) -> None:
        expected_states = {
            "idle": (280, 110, 110, 140, 140, 320),
            "running-right": (120, 120, 120, 120, 120, 120, 120, 220),
            "running-left": (120, 120, 120, 120, 120, 120, 120, 220),
            "waving": (140, 140, 140, 280),
            "jumping": (140, 140, 140, 140, 280),
            "failed": (140, 140, 140, 140, 140, 140, 140, 240),
            "waiting": (150, 150, 150, 150, 150, 260),
            "running": (120, 120, 120, 120, 120, 220),
            "review": (150, 150, 150, 150, 150, 280),
        }
        for version_id in ("v001", "v002"):
            version_root = PREVIEWER / "sample-assets" / version_id
            atlas = version_root / "spritesheet.png"
            self.assertTrue(atlas.is_file(), atlas)
            atlas_data = atlas.read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", atlas_data[:8])
            self.assertEqual(
                (1536, 2288),
                struct.unpack(">II", atlas_data[16:24]),
            )
            self.assertIn(
                f'atlasUrl: "./sample-assets/{version_id}/spritesheet.png"',
                self.data,
            )
            self.assertIn(
                f'gifRoot: "./sample-assets/{version_id}/gifs"',
                self.data,
            )
            for state_id, durations in expected_states.items():
                gif = version_root / "gifs" / f"{state_id}.gif"
                self.assertTrue(gif.is_file(), gif)
                parsed = parse_gif(gif)
                self.assertEqual((192, 208), parsed["size"])
                self.assertEqual(
                    [duration // 10 for duration in durations],
                    parsed["delays"],
                )
                self.assertEqual(0, parsed["loop_count"])
                self.assertNotIn(0xFE, parsed["extension_labels"])

    def test_css_palette_is_grayscale(self) -> None:
        colors = re.findall(r"#([0-9a-fA-F]{6})\b", self.css)
        self.assertTrue(colors)
        for value in colors:
            red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
            self.assertEqual(red, green, value)
            self.assertEqual(green, blue, value)

    def test_pet_content_preserves_source_color(self) -> None:
        self.assertNotIn("grayscale(", self.css)

    def test_frame_step_preserves_position_and_moves_exactly_once(self) -> None:
        self.assertIn("function stepFrame(delta)", self.app)
        self.assertIn(
            "function stepFrame(delta) {\n"
            "    enterFrameInspection();\n"
            "    setFrame(activeFrameIndex + delta);",
            self.app,
        )
        self.assertIn('let playbackMode = "runtime";', self.app)
        self.assertIn("let isInspectingFrame = false;", self.app)
        self.assertIn("function resumeSelectedPlayback()", self.app)
        self.assertNotIn('setPreviewMode("frames"', self.app)
        self.assertNotIn('playbackMode = "frames"', self.app)

    def test_preview_size_is_display_only(self) -> None:
        self.assertIn('id="previewSizeInput"', self.html)
        self.assertIn('id="previewSizeValue"', self.html)
        self.assertIn("--preview-scale", self.css)
        self.assertIn("transform: scale(var(--preview-scale));", self.css)
        self.assertIn('elements.stage.style.setProperty(', self.app)
        self.assertIn('event.target.closest(".preview-size-control")', self.app)
        self.assertNotIn("previewSizePercent", self.data)

    def test_look_controls_are_mutually_exclusive_toggles(self) -> None:
        self.assertRegex(
            self.html,
            r'id="orbitButton"\s+class="button look-toggle"\s+'
            r'type="button"\s+aria-pressed="false"',
        )
        self.assertRegex(
            self.html,
            r'id="followPointerButton"\s+class="button look-toggle"\s+'
            r'type="button"\s+aria-pressed="false"',
        )
        self.assertIn('role="group"', self.html)
        self.assertIn('data-i18n-aria-label="ui.lookModeAria"', self.html)
        self.assertIn('.look-toggle[aria-pressed="true"]', self.css)
        self.assertIn('let lookControlMode = "manual";', self.app)
        self.assertIn("function setLookControlMode(mode)", self.app)
        self.assertIn("function toggleLookControlMode(mode)", self.app)
        self.assertIn('toggleLookControlMode("orbit")', self.app)
        self.assertIn('toggleLookControlMode("pointer")', self.app)
        self.assertIn('setLookControlMode("manual");', self.app)
        self.assertIn('lookControlMode === "orbit"', self.app)
        self.assertIn('lookControlMode === "pointer"', self.app)
        self.assertIn('elements.directionTarget.style.display = "none";', self.app)
        self.assertNotIn("let pointerFollow =", self.app)
        self.assertNotIn("pointerFollowOn", self.i18n)
        self.assertNotIn("pointerFollowOff", self.i18n)
        self.assertNotIn("stopOrbit", self.i18n)
        for key in ("lookModeAria", "autoOrbit", "pointerFollow"):
            self.assertIn(key, self.i18n)

    def test_playback_modes_have_explanatory_copy(self) -> None:
        for key in (
            "gifPlaybackTitle",
            "gifPlaybackMissing",
            "gifPlaybackMissingTitle",
            "gifPlaybackFailed",
            "gifPlaybackFailedTitle",
            "runtimeTimingTitle",
            "gifModeHelp",
            "runtimeModeHelp",
            "frameInspectionGifHelp",
            "frameInspectionRuntimeHelp",
            "frameInspectionLabel",
            "gifLoadFailedHelp",
            "previewSizeTitle",
        ):
            self.assertIn(key, self.i18n)
        self.assertIn('id="previewModeHelp"', self.html)
        self.assertIn('id="gifModeButton"', self.html)
        self.assertIn('id="runtimeModeButton"', self.html)
        self.assertNotIn('id="frameModeButton"', self.html)
        self.assertNotIn("gifFallbackModeHelp", self.i18n)
        self.assertNotIn("simulatedLoop", self.i18n)
        self.assertNotIn("frameModeHelp", self.i18n)
        self.assertIn("function declaredGifUrlFor(", self.app)
        self.assertIn("function gifAvailabilityFor(", self.app)
        self.assertIn("elements.gifModeButton.disabled = !gifAvailable;", self.app)
        self.assertIn('playbackMode === "runtime"', self.app)
        self.assertIn("!isInspectingFrame", self.app)
        self.assertNotIn('(playbackMode === "gif" && !usesNativeGif())', self.app)
        self.assertIn(
            "elements.speedSelect.disabled = playbackMode === \"gif\";",
            self.app,
        )
        self.assertIn("let gifRequestSerial = 0;", self.app)
        self.assertIn("const requestSerial = ++gifRequestSerial;", self.app)
        self.assertIn(
            "if (requestSerial !== gifRequestSerial) return;",
            self.app,
        )
        self.assertIn(
            'const nextPlayer = document.createElement("img");',
            self.app,
        )
        self.assertIn("elements.gifPlayer.replaceWith(nextPlayer);", self.app)
        self.assertIn("failedGifs.add(failureKey);", self.app)
        self.assertIn('setPlaybackMode("runtime");', self.app)

    def test_chinese_ui_copy_is_isolated_to_i18n(self) -> None:
        chinese = re.compile(r"[\u3400-\u9fff]")
        self.assertRegex(self.i18n, chinese)
        for path in PREVIEWER.iterdir():
            if not path.is_file() or path.name == "i18n.js":
                continue
            if path.suffix not in {".html", ".js", ".css", ".md"}:
                continue
            self.assertIsNone(chinese.search(path.read_text(encoding="utf-8")), path.name)


if __name__ == "__main__":
    unittest.main()
