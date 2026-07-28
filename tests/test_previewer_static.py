from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEWER = ROOT / "previewer"


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
        self.assertIn("const nextFrameIndex = activeFrameIndex + delta;", self.app)
        self.assertIn('setPreviewMode("frames", {', self.app)
        self.assertIn("preserveFrame: true", self.app)
        self.assertIn("autoplay: false", self.app)
        self.assertIn("setFrame(nextFrameIndex);", self.app)
        self.assertNotIn(
            'setPreviewMode("frames");\n      pausePlayback();\n      setFrame(activeFrameIndex',
            self.app,
        )

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
            "runtimeTimingTitle",
            "frameInspectionTitle",
            "gifModeHelp",
            "gifFallbackModeHelp",
            "runtimeModeHelp",
            "frameModeHelp",
            "previewSizeTitle",
        ):
            self.assertIn(key, self.i18n)
        self.assertIn('id="previewModeHelp"', self.html)
        self.assertIn(
            'failedGifs.add(`${currentVersion().id}:${state.id}`);\n'
            "      elements.stageModeLabel.textContent = t(\"ui.gifError\");\n"
            "      renderControlLabels();",
            self.app,
        )

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
