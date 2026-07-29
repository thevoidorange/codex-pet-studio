from __future__ import annotations

import re
import struct
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
        self.assertNotIn("function withStateOverrides(", self.app)
        self.assertIn("states: cloneValue(base.states)", self.app)
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

    def test_bundled_example_uses_only_the_smooth_atlas(self) -> None:
        version_id = "v002"
        version_root = PREVIEWER / "sample-assets" / version_id
        atlas = version_root / "spritesheet.png"
        self.assertTrue(atlas.is_file(), atlas)
        self.assertFalse((PREVIEWER / "sample-assets" / "v001").exists())
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
        self.assertNotIn("gifRoot", self.data)
        self.assertNotIn("gifByState", self.data)
        self.assertNotIn('id: "v001"', self.data)
        self.assertNotIn("sampleVariant", self.data)
        self.assertNotIn("variant >= 2", self.app)

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
            "    inspectFrame(activeFrameIndex + delta);",
            self.app,
        )
        self.assertIn('let playbackMode = "runtime";', self.app)
        self.assertIn("let isInspectingFrame = false;", self.app)
        self.assertIn("function resumeSelectedPlayback()", self.app)
        self.assertNotIn('setPreviewMode("frames"', self.app)
        self.assertNotIn('playbackMode = "frames"', self.app)

    def test_keyframes_can_reveal_take_rail_and_confirm_explicitly(self) -> None:
        self.assertIn("frameTakes: [", self.data)
        self.assertIn('id: "t001"', self.data)
        self.assertIn('id: "t002"', self.data)
        self.assertIn("function frameTakesFor(", self.app)
        self.assertIn("function renderTakeRail(", self.app)
        self.assertIn("function positionTakeRail(", self.app)
        self.assertIn('class="take-rail"', self.app)
        self.assertIn('class="take-card ${', self.app)
        self.assertIn("grid-column: 1 / -1;", self.css)
        self.assertIn("activeFrameTake = {", self.app)
        self.assertIn("versionId: activeVersionId", self.app)
        self.assertIn("stateId: state.id", self.app)
        self.assertIn("frameIndex: activeFrameIndex", self.app)
        self.assertIn("clearFrameTakeState();", self.app)
        self.assertIn('id="confirmTakeButton"', self.html)
        self.assertLess(
            self.html.index('id="nextFrameButton"'),
            self.html.index('id="confirmTakeButton"'),
        )
        self.assertLess(
            self.html.index('id="confirmTakeButton"'),
            self.html.index('id="restartButton"'),
        )
        self.assertIn("const confirmedFrameTakeIds = new Map();", self.app)
        self.assertIn("confirmedFrameTakeIds.has(key)", self.app)
        self.assertIn("function confirmedSelectionForFrame(", self.app)
        self.assertIn("function hasConfirmedFrameTakeForFrame(", self.app)
        self.assertIn("function previewFrameTake(takeId)", self.app)
        self.assertIn("function confirmFrameTake()", self.app)
        self.assertIn("function stepTake(delta)", self.app)
        self.assertIn("function stepTransport(delta)", self.app)
        self.assertIn(
            "if (expandedTakeFrameIndex !== null) stepTake(delta);",
            self.app,
        )
        self.assertIn(
            "confirmedFrameTakeIds.set(key, takeId);",
            self.app,
        )
        self.assertIn('id="transportControls"', self.html)
        self.assertIn('id="takeStatus"', self.html)
        self.assertIn("function announceTakeConfirmation(", self.app)
        self.assertIn('"ui.takeTransportAria"', self.app)
        self.assertIn("function focusPreviewedTake()", self.app)
        self.assertIn("focusFrameButton(frameIndex);", self.app)
        self.assertIn("focusFrameButton(activeFrameIndex);", self.app)
        self.assertIn(".take-card.is-confirmed", self.css)
        self.assertIn(".frame-take-confirmed", self.css)
        self.assertNotIn('type="file"', self.html)
        self.assertNotIn("upload", self.html.lower())
        self.assertNotIn("promote", self.html.lower())

    def test_take_audition_is_temporary_and_confirmed_take_feeds_playback(self) -> None:
        render_player = self.app.split(
            "function renderPlayer() {",
            1,
        )[1].split(
            "function refreshActiveClasses()",
            1,
        )[0]
        self.assertIn("displayedTakeForCurrentFrame()", render_player)
        self.assertIn("confirmedTakeForFrame(", render_player)
        self.assertIn("setTakeSpriteFrame(", render_player)
        self.assertIn(
            "const playbackState = displayedState();\n"
            "    const confirmedTake = confirmedTakeForFrame(",
            render_player,
        )
        self.assertIn(
            "setSpriteFrame(playbackState.row, activeFrameIndex);",
            render_player,
        )
        readme = (PREVIEWER / "README.md").read_text(encoding="utf-8")
        self.assertIn("Confirmation is session-only review metadata.", readme)
        self.assertNotIn("frameTakes", self.data.split("states: [", 1)[1])

    def test_frame_take_sources_and_ids_are_fail_closed(self) -> None:
        self.assertIn('const ORIGINAL_TAKE_ID = "original";', self.app)
        self.assertIn("takeId === ORIGINAL_TAKE_ID", self.app)
        self.assertIn("Number.isInteger(candidate.frameIndex)", self.app)
        self.assertIn("candidate.frameIndex < state.durations.length", self.app)
        self.assertIn("groups.flatMap((group) => group.takes)", self.app)
        self.assertIn("usedIds.has(takeId)", self.app)
        self.assertIn("function isSafeTakeAssetUrl(path)", self.app)
        self.assertIn('["http:", "https:"].includes(url.protocol)', self.app)
        self.assertIn("url.origin === baseUrl.origin", self.app)
        self.assertIn("!url.username", self.app)
        self.assertIn("!url.password", self.app)
        self.assertIn("Boolean(hasAsset) === Boolean(hasAtlasSlot)", self.app)
        self.assertIn("probe.naturalWidth !== config.sprite.frameWidth", self.app)
        self.assertIn("probe.naturalHeight !== config.sprite.frameHeight", self.app)
        self.assertIn("function invalidateTakeAsset(", self.app)
        self.assertIn("function currentTakeAssetUsage(", self.app)
        self.assertIn("function removeConfirmedSelectionsForAsset(", self.app)
        self.assertIn("currentTakeAssetUsage(assetUrl).controls", self.app)
        self.assertIn(".icon-button:disabled", self.css)

    def test_candidate_and_take_copy_is_localized(self) -> None:
        self.assertIn('version: "Candidate"', self.i18n)
        self.assertIn('version: "方案"', self.i18n)
        self.assertIn('originalFrame: "Original"', self.i18n)
        self.assertIn('originalFrame: "原始"', self.i18n)
        self.assertIn('confirmTake: "Confirm Current Take"', self.i18n)
        self.assertIn('confirmTake: "确认当前 Take"', self.i18n)
        self.assertIn('previousTake: "Previous Take"', self.i18n)
        self.assertIn('nextTake: "下一个 Take"', self.i18n)

    def test_preview_size_is_display_only(self) -> None:
        self.assertIn('id="previewSizeInput"', self.html)
        self.assertIn('id="previewSizeValue"', self.html)
        self.assertIn('min="80"', self.html)
        self.assertIn('max="224"', self.html)
        self.assertIn('value="160"', self.html)
        self.assertIn("const PREVIEW_SIZE_MIN_PX = 80;", self.app)
        self.assertIn("const PREVIEW_SIZE_MAX_PX = 224;", self.app)
        self.assertIn("--preview-width", self.css)
        self.assertIn("width: var(--preview-width);", self.css)
        self.assertNotIn("--preview-scale", self.css)
        self.assertIn('elements.stage.style.setProperty(', self.app)
        self.assertIn('event.target.closest(".preview-size-control")', self.app)
        self.assertNotIn("previewSizePercent", self.data)

    def test_all_state_autoplay_is_one_clear_toggle(self) -> None:
        self.assertIn('id="autoPlayStatesToggle"', self.html)
        self.assertIn('aria-pressed="false"', self.html)
        self.assertNotIn('id="stopTourButton"', self.html)
        self.assertIn("function toggleAllStatePlayback()", self.app)
        self.assertIn(
            "if (tourState.active) stopTour();\n    else startTour();",
            self.app,
        )
        self.assertIn("autoPlayAllStates: \"Auto-Play All States\"", self.i18n)
        self.assertIn("autoPlayAllStates: \"自动播放全部状态\"", self.i18n)
        self.assertNotIn("Tour all states", self.i18n)
        self.assertNotIn("巡演全部状态", self.i18n)

    def test_runtime_contract_is_fixed_read_only_and_visible(self) -> None:
        for element_id in (
            "timingEditor",
            "timingDurationInput",
            "timingDecreaseButton",
            "timingIncreaseButton",
            "timingUndoButton",
            "timingResetStateButton",
            "timingUpdateButton",
        ):
            self.assertNotIn(f'id="{element_id}"', self.html)

        for removed in (
            "TIMING_STEP_MS",
            "TIMING_MIN_MS",
            "TIMING_MAX_MS",
            "timingSelectedFrameIndex",
            "timingHistory",
            "timingWriteSession",
            "/__pet-studio__/session",
            "/__pet-studio__/timing",
            "withStateOverrides",
            "config.runtime",
        ):
            self.assertNotIn(removed, self.app)
        self.assertNotIn("5000", self.html + self.app + self.i18n)

        self.assertIn("const FIXED_ACTION_LOOPS = 3;", self.app)
        self.assertIn("const FIXED_IDLE_SLOWDOWN = 6;", self.app)
        self.assertIn("sprite: cloneValue(base.sprite)", self.app)
        self.assertIn("states: cloneValue(base.states)", self.app)
        self.assertIn("directions: cloneValue(base.directions)", self.app)
        self.assertNotIn("...(next.sprite || {})", self.app)
        self.assertNotIn("next.directions", self.app)
        expected_contract = {
            "idle": (0, [280, 110, 110, 140, 140, 320]),
            "running-right": (1, [120, 120, 120, 120, 120, 120, 120, 220]),
            "running-left": (2, [120, 120, 120, 120, 120, 120, 120, 220]),
            "waving": (3, [140, 140, 140, 280]),
            "jumping": (4, [140, 140, 140, 140, 280]),
            "failed": (5, [140, 140, 140, 140, 140, 140, 140, 240]),
            "waiting": (6, [150, 150, 150, 150, 150, 260]),
            "running": (7, [120, 120, 120, 120, 120, 220]),
            "review": (8, [150, 150, 150, 150, 150, 280]),
        }
        for state_id, (row, durations) in expected_contract.items():
            match = re.search(
                rf'id:\s*"{re.escape(state_id)}",\s*'
                rf"row:\s*(\d+),\s*durations:\s*\[([^\]]+)\]",
                self.data,
            )
            self.assertIsNotNone(match, state_id)
            self.assertEqual(row, int(match.group(1)), state_id)
            self.assertEqual(
                durations,
                [int(value.strip()) for value in match.group(2).split(",")],
                state_id,
            )
        self.assertIn("function runtimeFrameDuration(state, frameIndex)", self.app)
        self.assertIn(
            "? baseDuration * FIXED_IDLE_SLOWDOWN",
            self.app,
        )
        self.assertIn(
            "const delay = runtimeFrameDuration(state, activeFrameIndex);",
            self.app,
        )
        self.assertIn(
            "state.durations.length * FIXED_ACTION_LOOPS",
            self.app,
        )
        self.assertIn("let runtimeFramesCompleted = 0;", self.app)
        self.assertIn("runtimeFramesCompleted += 1;", self.app)
        self.assertIn(
            "runtimeFramesCompleted / state.durations.length",
            self.app,
        )
        self.assertIn('class="frame-duration"', self.app)
        self.assertIn("runtimeDurationLabel(state, index)", self.app)
        self.assertIn(
            'idleFrameDuration: "{duration} ms × {multiplier}"',
            self.i18n,
        )
        self.assertIn(
            'idleFrameDuration: "{duration} 毫秒 × {multiplier}"',
            self.i18n,
        )
        self.assertIn('keyframes: "Keyframes"', self.i18n)
        self.assertIn('keyframes: "关键帧"', self.i18n)
        self.assertIn('class="mechanics-duration"', self.app)
        self.assertIn(
            "runtimeDurationLabel(state, index)",
            self.app,
        )
        self.assertIn("elements.tourProgress.hidden = !(", self.app)

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
        self.assertIn(
            'setLookControlMode(isAnimation ? "manual" : "pointer");',
            self.app,
        )
        self.assertIn('lookControlMode === "orbit"', self.app)
        self.assertIn('lookControlMode === "pointer"', self.app)
        self.assertIn('elements.directionTarget.style.display = "none";', self.app)
        self.assertIn('elements.directionTarget.style.display = "block";', self.app)
        self.assertNotIn(
            'elements.stage.addEventListener("pointerenter"',
            self.app,
        )
        self.assertNotIn("let pointerFollow =", self.app)
        self.assertNotIn("pointerFollowOn", self.i18n)
        self.assertNotIn("pointerFollowOff", self.i18n)
        self.assertNotIn("stopOrbit", self.i18n)
        for key in ("lookModeAria", "autoOrbit", "pointerFollow"):
            self.assertIn(key, self.i18n)
        self.assertIn('autoOrbit: "Auto Orbit"', self.i18n)
        self.assertIn('pointerFollow: "Pointer Follow"', self.i18n)
        self.assertIn("const LOOK_ORBIT_STEP_MS = 120;", self.app)
        self.assertIn("}, LOOK_ORBIT_STEP_MS);", self.app)
        self.assertIn("transform: translate(12px, -50%);", self.css)
        self.assertNotIn("transform: translate(14px, -50%);", self.css)

    def test_english_control_copy_uses_title_case(self) -> None:
        expected = (
            'autoPlayAllStates: "Auto-Play All States"',
            'animationStates: "Animation States"',
            'lookDirections: "16 Look Directions"',
            'runtimeTiming: "Runtime Simulation"',
            'endlessLoop: "Endless Loop"',
            'previousTake: "Previous Take"',
            'nextTake: "Next Take"',
            'confirmTake: "Confirm Current Take"',
            'keyframes: "Keyframes"',
            'mechanicsTitle: "Motion Timing Board"',
            'title: "Resting Nearby"',
            'label: "Move Right"',
            'title: "Moving Right"',
            'label: "Move Left"',
            'title: "Moving Left"',
            'title: "A Quiet Hello"',
            'title: "A Light Jump"',
            'title: "Recovering From A Setback"',
            'title: "Waiting For A Response"',
            'title: "Focused Activity"',
            'title: "Inspecting A Result"',
        )
        for copy in expected:
            self.assertIn(copy, self.i18n)
        self.assertIn("padding: 3px 12px;", self.css)

    def test_playback_modes_have_explanatory_copy(self) -> None:
        for key in (
            "runtimeTimingTitle",
            "endlessLoopTitle",
            "endlessModeHelp",
            "runtimeModeHelp",
            "frameInspectionEndlessHelp",
            "frameInspectionRuntimeHelp",
            "takeRailHelp",
            "frameInspectionLabel",
            "previewSizeTitle",
        ):
            self.assertIn(key, self.i18n)
        self.assertIn('id="previewModeHelp"', self.html)
        self.assertIn('id="runtimeModeButton"', self.html)
        self.assertIn('id="endlessModeButton"', self.html)
        self.assertLess(
            self.html.index('id="runtimeModeButton"'),
            self.html.index('id="endlessModeButton"'),
        )
        self.assertNotIn('id="frameModeButton"', self.html)
        self.assertNotIn('id="gifModeButton"', self.html)
        self.assertNotIn('id="gifPlayer"', self.html)
        self.assertNotIn("frameModeHelp", self.i18n)
        self.assertIn('playbackMode === "runtime"', self.app)
        self.assertIn('playbackMode === "loop"', self.app)
        self.assertIn('setPlaybackMode("loop")', self.app)
        self.assertIn("!isInspectingFrame", self.app)
        self.assertNotIn('id="speedSelect"', self.html)
        self.assertNotIn("speedSelect", self.app)
        self.assertNotIn("let speed =", self.app)
        self.assertIn(
            "const delay = runtimeFrameDuration(state, activeFrameIndex);",
            self.app,
        )
        self.assertNotIn("gifRequestSerial", self.app)
        self.assertNotIn("gifAvailabilityFor", self.app)
        self.assertNotIn("declaredGifUrlFor", self.app)
        self.assertNotIn("failedGifs", self.app)
        self.assertIn('setPlaybackMode("runtime");', self.app)

    def test_pointer_follow_coalesces_updates_and_skips_same_direction(self) -> None:
        self.assertIn("let pointerFrameRequest = null;", self.app)
        self.assertIn("let pendingPointerSample = null;", self.app)
        self.assertIn(
            "pointerFrameRequest = window.requestAnimationFrame(flushPointerMove);",
            self.app,
        )
        self.assertIn("function cancelPointerUpdate()", self.app)
        self.assertIn(
            "if (directionIndex !== activeDirectionIndex) {\n"
            "      setDirection(directionIndex);\n"
            "    }",
            self.app,
        )
        self.assertIn("translate3d(", self.app)

        set_direction = self.app.split("function setDirection(index)", 1)[1].split(
            "function clearOrbitTimer()", 1
        )[0]
        self.assertNotIn("setSpriteFrame(", set_direction)

    def test_look_mechanics_title_stays_stable_while_direction_changes(self) -> None:
        look_details = self.app.split("function renderLookDetails()", 1)[1].split(
            "function renderControlLabels()", 1
        )[0]
        self.assertIn(
            'elements.stateTitle.textContent = t("ui.lookTitle");',
            look_details,
        )
        self.assertNotIn("activeDirectionIndex", look_details)
        self.assertIn('lookTitle: "Following Attention"', self.i18n)
        self.assertIn('lookTitle: "视线跟随"', self.i18n)
        self.assertIn(
            "`${direction.degree}° · ${directionLabel(direction)}`",
            self.app,
        )

    def test_background_pages_suspend_animation_work(self) -> None:
        self.assertIn(
            'let pageVisible = document.visibilityState !== "hidden";',
            self.app,
        )
        self.assertIn("function handleVisibilityChange()", self.app)
        self.assertIn(
            'document.addEventListener("visibilitychange", handleVisibilityChange);',
            self.app,
        )
        self.assertIn("pageVisible &&", self.app)
        visibility_handler = self.app.split(
            "function handleVisibilityChange()", 1
        )[1].split("function showNextTourState()", 1)[0]
        for call in (
            "clearFrameTimer();",
            "clearOrbitTimer();",
            "cancelPointerUpdate();",
            "clearTourTimers();",
        ):
            self.assertIn(call, visibility_handler)
        animation_section = self.app.split(
            "if (isAnimation) {", 1
        )[1].split("} else {", 1)[0]
        self.assertIn("renderFrameReadout();", animation_section)

    def test_rendering_avoids_large_blur_and_eager_offscreen_paint(self) -> None:
        workspace_rule = self.css.split(".workspace {", 1)[1].split("}", 1)[0]
        self.assertNotIn("backdrop-filter", workspace_rule)
        self.assertIn("content-visibility: auto;", self.css)
        self.assertIn("contain-intrinsic-size: auto 230px;", self.css)
        self.assertIn("transform: scaleX(0);", self.css)
        self.assertIn("const TOUR_PROGRESS_STEP_MS = 160;", self.app)

    def test_fixed_timing_labels_cover_keyframes_and_mechanics_cards(self) -> None:
        self.assertIn('class="mechanics-duration"', self.app)
        self.assertIn('class="frame-duration"', self.app)
        self.assertGreaterEqual(
            self.app.count("runtimeDurationLabel(state, index)"),
            3,
        )
        self.assertNotIn("refreshMechanicsDurations", self.app)
        self.assertNotIn("updateSelectedTiming", self.app)

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
