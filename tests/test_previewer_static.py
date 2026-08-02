from __future__ import annotations

import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEWER = ROOT / "previewer"
TARGET_PATH = ROOT / "delivery-targets" / "codex-pet-v2.json"


class PreviewerStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (PREVIEWER / "index.html").read_text(encoding="utf-8")
        self.app = (PREVIEWER / "app.js").read_text(encoding="utf-8")
        self.data = (PREVIEWER / "preview-data.js").read_text(encoding="utf-8")
        self.target_data = (PREVIEWER / "target-data.js").read_text(
            encoding="utf-8"
        )
        self.target = json.loads(TARGET_PATH.read_text(encoding="utf-8"))
        self.i18n = (PREVIEWER / "i18n.js").read_text(encoding="utf-8")
        self.css = (PREVIEWER / "styles.css").read_text(encoding="utf-8")

    def test_static_references_and_dom_ids_exist(self) -> None:
        self.assertIn('<link rel="icon" href="data:," />', self.html)
        for reference in (
            "styles.css",
            "i18n.js",
            "target-data.js",
            "preview-data.js",
            "app.js",
        ):
            self.assertTrue((PREVIEWER / reference).is_file(), reference)
            self.assertIn(f"./{reference}", self.html)
        self.assertLess(
            self.html.index("./target-data.js"),
            self.html.index("./preview-data.js"),
        )
        self.assertLess(
            self.html.index("./preview-data.js"),
            self.html.index("./app.js"),
        )

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
        observed = {state["id"] for state in self.target["states"]}
        self.assertEqual(expected, observed)
        self.assertFalse({"moveRight", "moveLeft", "greeting", "working"} & observed)
        self.assertIn("window.PET_DELIVERY_TARGET", self.target_data)

    def test_timing_board_covers_all_standard_states(self) -> None:
        expected = [state["id"] for state in self.target["states"]]
        mechanics_block = self.data.split("mechanics: [", 1)[1].split(
            "],\n  backgrounds:",
            1,
        )[0]
        observed = re.findall(r'stateId:\s*"([^"]+)"', mechanics_block)
        self.assertEqual(expected, observed)
        self.assertNotIn("function withStateOverrides(", self.app)
        self.assertIn("states: deliveryTarget.states.map(", self.app)
        self.assertIn("function withMechanicsOverrides(", self.app)
        self.assertIn(
            "mechanics: withMechanicsOverrides(base.mechanics, next.mechanics)",
            self.app,
        )
        self.assertIn("const runtimeStates = currentRuntimeStates();", self.app)
        self.assertIn("const mechanicsBoards = runtimeStates.map(", self.app)
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
            state["id"]: len(state["durationsMs"])
            for state in self.target["states"]
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

    def test_previewer_has_no_duplicate_delivery_target_facts(self) -> None:
        self.assertNotRegex(self.data, r"(?m)^\s*(?:sprite|states|directions):")
        self.assertNotIn("FIXED_ACTION_LOOPS", self.app)
        self.assertNotIn("FIXED_IDLE_SLOWDOWN", self.app)
        self.assertNotIn("PREVIEW_SIZE_MIN_PX", self.app)
        self.assertNotIn("PREVIEW_SIZE_MAX_PX", self.app)
        self.assertIn("const deliveryTarget = window.PET_DELIVERY_TARGET;", self.app)
        self.assertIn("function targetBackedConfig()", self.app)
        self.assertIn("function assertCompatibleTarget(projectConfig)", self.app)
        self.assertIn("runtime: cloneValue(deliveryTarget.runtime)", self.app)
        self.assertIn("display: cloneValue(deliveryTarget.display)", self.app)
        self.assertIn(
            "directions: cloneValue(deliveryTarget.lookDirections.slots)",
            self.app,
        )
        for duplicate in (
            "FRAME_WIDTH =",
            "FRAME_HEIGHT =",
            "ATLAS_COLUMNS =",
            "ATLAS_ROWS =",
            "STATES =",
            "DIRECTIONS =",
        ):
            self.assertNotIn(duplicate, self.data)

    def test_version_and_locale_controls_are_generic(self) -> None:
        self.assertIn('id="versionSelect"', self.html)
        self.assertIn('id="languageSelect"', self.html)
        self.assertIn('new URLSearchParams(window.location.search).get("config")', self.app)
        self.assertIn("config.versions", self.app)
        self.assertIn("window.localStorage", self.app)
        self.assertIn('"zh-CN"', self.i18n)
        self.assertIn('"en"', self.i18n)

    def test_review_context_url_is_validated_stable_and_agent_readable(self) -> None:
        for key in ("candidate", "state", "frame", "take"):
            self.assertIn(f'{key}: "{key}"', self.app)
        self.assertIn("function readReviewContextFromUrl()", self.app)
        self.assertIn("function syncReviewContextToUrl()", self.app)
        self.assertIn("function clearReviewContextFromUrl()", self.app)
        self.assertIn("function restoreReviewContextFromUrl(context)", self.app)
        self.assertIn(
            "window.history.replaceState(window.history.state, \"\", url.href);",
            self.app,
        )
        self.assertRegex(
            self.app,
            r"url\.searchParams\.set\(\s*"
            r"REVIEW_CONTEXT_PARAMS\.frame,\s*"
            r"String\(reviewFocus\.frameIndex \+ 1\),",
        )
        self.assertIn(
            "url.searchParams.delete(REVIEW_CONTEXT_PARAMS.frame);",
            self.app,
        )
        self.assertIn(
            "url.searchParams.delete(REVIEW_CONTEXT_PARAMS.take);",
            self.app,
        )
        self.assertIn(
            "(version) => version.id === context.candidateId",
            self.app,
        )
        self.assertIn(
            "(state) => state.id === context.stateId",
            self.app,
        )
        self.assertIn("Number.isInteger(frameNumber)", self.app)
        self.assertIn("frameNumber >= 1", self.app)
        self.assertIn("frameNumber <= frameCount", self.app)
        self.assertIn("let reviewFocus = {", self.app)
        self.assertIn("function setReviewFocusFromCurrent({", self.app)
        self.assertIn("function validReviewTakeId(", self.app)
        self.assertIn("let canRestoreState = false;", self.app)
        self.assertIn("let canRestoreFrame = false;", self.app)
        self.assertIn("canRestoreFrame &&", self.app)
        self.assertIn("/^[1-9]\\d*$/.test(context.frame)", self.app)
        self.assertIn(
            "const requestedReviewContext = readReviewContextFromUrl();",
            self.app,
        )
        self.assertIn(
            "restoreReviewContextFromUrl(requestedReviewContext);",
            self.app,
        )
        self.assertIn("reviewContextReady = true;", self.app)
        restore_context = self.app.split(
            "function restoreReviewContextFromUrl(context) {",
            1,
        )[1].split(
            "function idleState()",
            1,
        )[0]
        self.assertNotIn("confirmedFrameTakeIds.set", restore_context)
        self.assertLess(
            restore_context.index("if (context.candidateId !== null)"),
            restore_context.index("if (canRestoreState && context.stateId !== null)"),
        )
        self.assertLess(
            restore_context.index("if (canRestoreState && context.stateId !== null)"),
            restore_context.index("canRestoreFrame &&"),
        )
        self.assertIn(
            "activeVersionId = requestedVersion.id;\n"
            "        canRestoreState = true;",
            restore_context,
        )
        self.assertIn(
            "activeStateIndex = requestedStateIndex;\n"
            "        canRestoreFrame = true;",
            restore_context,
        )

        sync_context = self.app.split(
            "function syncReviewContextToUrl() {",
            1,
        )[1].split(
            "function restoreReviewContextFromUrl(context)",
            1,
        )[0]
        self.assertIn("reviewFocus.candidateId", sync_context)
        self.assertIn("reviewFocus.stateId", sync_context)
        self.assertIn("reviewFocus.frameIndex", sync_context)
        self.assertIn("reviewFocus.takeId", sync_context)
        self.assertNotIn("isInspectingFrame", sync_context)
        self.assertNotIn("activeFrameIndex", sync_context)

        set_frame = self.app.split(
            "function setFrame(index) {",
            1,
        )[1].split(
            "function shouldScheduleFrames()",
            1,
        )[0]
        scheduler = self.app.split(
            "function scheduleNextFrame() {",
            1,
        )[1].split(
            "function restartPlayback(",
            1,
        )[0]
        self.assertNotIn("syncReviewContextToUrl", set_frame)
        self.assertNotIn("syncReviewContextToUrl", scheduler)
        for function_name, next_function in (
            ("restartPlayback()", "enterFrameInspection("),
            ("resumeSelectedPlayback()", "inspectFrame("),
            ("setPlaybackMode(mode)", "stepFrame("),
        ):
            function_body = self.app.split(
                f"function {function_name} {{",
                1,
            )[1].split(
                f"function {next_function}",
                1,
            )[0]
            self.assertNotIn("syncReviewContextToUrl", function_body)
            self.assertNotIn("setReviewFocusFromCurrent", function_body)
        self.assertIn("if (!options.fromTour) {", self.app)
        self.assertIn(
            "includeFrame: isStaticState(currentState()),",
            self.app,
        )
        self.assertIn("setReviewFocusFromCurrent({ includeFrame: true });", self.app)
        self.assertNotIn("syncContext", self.app)

        load_config = self.app.split(
            "async function loadConfig(requestedReviewContext) {",
            1,
        )[1].split(
            "function normalizeConfig(",
            1,
        )[0]
        self.assertIn("externalLoadFailed: false", load_config)
        self.assertIn("externalLoadFailed: true", load_config)
        self.assertIn("selectedCandidateId", load_config)
        self.assertIn("activeDiagnostic", load_config)
        boot = self.app.split(
            "async function boot() {",
            1,
        )[1].split(
            "\n  boot();",
            1,
        )[0]
        self.assertIn("if (loaded.globalDiagnostic) {", boot)
        self.assertIn("if (loaded.activeDiagnostic) {", boot)
        self.assertIn("showDiagnostic(loaded.globalDiagnostic", boot)
        self.assertIn("showDiagnostic(loaded.activeDiagnostic", boot)
        self.assertIn("return;", boot)
        self.assertIn("restoreReviewContextFromUrl(requestedReviewContext);", boot)
        self.assertLess(
            boot.index("if (loaded.globalDiagnostic) {"),
            boot.index("restoreReviewContextFromUrl(requestedReviewContext);"),
        )

        set_section = self.app.split(
            "function setSection(mode, { updateReviewFocus = false } = {}) {",
            1,
        )[1].split(
            "function setDirection(",
            1,
        )[0]
        self.assertIn("const sectionChanged = sectionMode !== mode;", set_section)
        self.assertIn(
            "if (sectionChanged && updateReviewFocus) {",
            set_section,
        )
        self.assertRegex(
            set_section,
            r'includeFrame:\s*mode === "animation" &&\s*'
            r"\(isInspectingFrame \|\| isStaticState\(currentState\(\)\)\)",
        )
        self.assertIn(
            'setSection("look", { updateReviewFocus: true })',
            self.app,
        )

        invalidate_take = self.app.split(
            "function invalidateTakeAsset(assetUrl) {",
            1,
        )[1].split(
            "function setTakeSpriteFrame(",
            1,
        )[0]
        self.assertIn("reviewFocus.candidateId", invalidate_take)
        self.assertIn("reviewFocus.stateId", invalidate_take)
        self.assertIn("reviewFocus.frameIndex", invalidate_take)
        self.assertIn("reviewFocus.takeId", invalidate_take)
        self.assertIn("focusedAssetUrl === assetUrl", invalidate_take)
        self.assertNotIn(
            "reviewFocus.frameIndex === activeFrameIndex",
            invalidate_take,
        )

        previewer_readme = (PREVIEWER / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "&candidate=<semantic-candidate-id>&state=idle&frame=2&take=t003",
            previewer_readme,
        )
        self.assertIn("`frame` is one-based.", previewer_readme)
        self.assertIn("Existing query parameters, including `config`, are preserved.", previewer_readme)

    def test_previewer_has_no_embedded_agent_or_install_action(self) -> None:
        public_ui = (self.html + self.i18n).lower()
        for forbidden in (
            "install in codex",
            "request new take",
            "agent prompt",
            "type=\"file\"",
        ):
            self.assertNotIn(forbidden, public_ui)

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = (
            ROOT / ".agents" / "skills" / "pet-studio" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for instructions in (agents, skill):
            self.assertIn("Install in Codex", instructions)
            self.assertIn("Request New Take", instructions)
            self.assertIn("candidate", instructions)
            self.assertIn("one-based", instructions)
            self.assertIn("adjacent frame", instructions)
            self.assertIn("conversation", instructions.lower())

    def test_external_versions_keep_example_but_load_project_first(self) -> None:
        self.assertIn("withBundledExample(projectVersions, base.versions)", self.app)
        self.assertIn("return [...versions, example];", self.app)
        self.assertIn("isBundledExample: true", self.app)
        self.assertIn("isDefault: false", self.app)
        self.assertIn("config = normalizeConfig(loaded.data, loaded.isExternal)", self.app)
        self.assertEqual(
            2,
            self.i18n.count('exampleVersion: "Example.RaincoatCat"'),
        )
        self.assertIn('id: "example-raincoat-cat"', self.data)
        self.assertIn('labelKey: "ui.exampleVersion"', self.data)
        self.assertNotIn('statusKey: "ui.currentVersion"', self.data)
        self.assertIn('let exampleId = "example-raincoat-cat";', self.app)
        self.assertIn('displayName: "Example.RaincoatCat"', self.app)
        self.assertNotIn(
            "const status = version.statusKey ? t(version.statusKey) : \"\";",
            self.app,
        )
        self.assertIn("return version.displayName || version.id;", self.app)
        self.assertIn("version && version.isBundledExample", self.app)
        self.assertIn("? window.location.href", self.app)

    def test_candidates_can_progress_from_static_to_partial_runtime(self) -> None:
        self.assertIn('id="staticSection"', self.html)
        self.assertIn('id="staticList"', self.html)
        self.assertLess(
            self.html.index('id="staticSection"'),
            self.html.index('id="stateList"'),
        )
        for function_name in (
            "staticReviewState",
            "runtimeStatesFor",
            "reviewStatesFor",
            "currentRuntimeStates",
            "currentVersionSupportsLook",
            "setStandaloneImage",
            "setOriginalFrame",
        ):
            self.assertIn(f"function {function_name}(", self.app)

        runtime_states = self.app.split(
            "function runtimeStatesFor(version) {",
            1,
        )[1].split(
            "function reviewStatesFor(version)",
            1,
        )[0]
        self.assertIn("if (!version || !version.atlasUrl) return [];", runtime_states)
        self.assertIn(
            "if (!Array.isArray(version.stateIds)) return config.states;",
            runtime_states,
        )
        self.assertIn(
            "return config.states.filter((state) => availableIds.has(state.id));",
            runtime_states,
        )

        review_states = self.app.split(
            "function reviewStatesFor(version) {",
            1,
        )[1].split(
            "function currentReviewStates()",
            1,
        )[0]
        self.assertIn("...(staticState ? [staticState] : [])", review_states)
        self.assertIn("...runtimeStatesFor(version)", review_states)

        supports_look = self.app.split(
            "function currentVersionSupportsLook() {",
            1,
        )[1].split(
            "function currentState()",
            1,
        )[0]
        self.assertIn("if (!version || !version.atlasUrl) return false;", supports_look)
        self.assertIn("version.lookDirectionsAvailable", supports_look)

        self.assertIn('static: "Static"', self.i18n)
        self.assertIn('staticImage: "1 image"', self.i18n)
        self.assertIn('staticTakes: "Static Image & Takes"', self.i18n)
        self.assertIn('static: "静态形象"', self.i18n)
        self.assertIn('staticTakes: "静态图与 Takes"', self.i18n)

    def test_standard_intermediate_atlas_is_visibly_review_only(self) -> None:
        self.assertIn('id="atlasPhaseBadge"', self.html)
        self.assertIn(
            'const STANDARD_INTERMEDIATE_PHASE = "standard-intermediate";',
            self.app,
        )
        self.assertNotIn("function atlasRowsForVersion(version) {", self.app)
        self.assertIn(
            "version.atlasPhase === STANDARD_INTERMEDIATE_PHASE",
            self.app,
        )
        self.assertIn(
            "if (version.atlasPhase === STANDARD_INTERMEDIATE_PHASE) return false;",
            self.app,
        )
        self.assertIn('t("ui.atlasPhaseReviewOnly")', self.app)
        self.assertIn('atlasPhaseReviewOnly: "8×9 · REVIEW ONLY"', self.i18n)
        self.assertIn('atlasPhaseReviewOnly: "8×9 · 仅供审阅"', self.i18n)
        self.assertIn('code: "ATLAS_PHASE_MISMATCH"', self.app)
        self.assertIn(
            "deliveryTarget.atlas.rows *\n          deliveryTarget.atlas.cellHeightPx",
            self.app,
        )
        self.assertIn(
            "`${config.sprite.columns * 100}% ${config.sprite.rows * 100}%`",
            self.app,
        )

    def test_bundled_example_is_the_sanitized_raincoat_cat_pack(self) -> None:
        version_id = "example-raincoat-cat"
        version_root = ROOT / "examples" / "raincoat-cat"
        atlas = version_root / "spritesheet.png"
        manifest_path = version_root / "pet.json"
        self.assertTrue(atlas.is_file(), atlas)
        self.assertTrue(manifest_path.is_file(), manifest_path)
        self.assertFalse((ROOT / "examples" / "neutral-demo").exists())
        self.assertFalse((PREVIEWER / "sample-assets").exists())
        atlas_data = atlas.read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", atlas_data[:8])
        self.assertEqual(
            (1536, 2288),
            struct.unpack(">II", atlas_data[16:24]),
        )
        self.assertIn(
            'atlasUrl: "../examples/raincoat-cat/spritesheet.png"',
            self.data,
        )
        self.assertIn('name: "Raincoat Cat"', self.data)
        self.assertIn(f'id: "{version_id}"', self.data)
        self.assertNotIn("gifRoot", self.data)
        self.assertNotIn("gifByState", self.data)
        self.assertNotIn("sampleVariant", self.data)
        self.assertNotIn("variant >= 2", self.app)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("raincoat-cat", manifest["id"])
        self.assertEqual("Raincoat Cat", manifest["displayName"])
        self.assertEqual(2, manifest["spriteVersionNumber"])
        self.assertEqual("spritesheet.png", manifest["spritesheetPath"])
        serialized = json.dumps(manifest, ensure_ascii=False).lower()
        private_names = (
            "".join(chr(code) for code in (0x963F, 0x5E03)),
            "".join(chr(code) for code in (0x5916, 0x5957, 0x963F, 0x5E03)),
            '"' + "a" + "bu" + '"',
            '"' + "ab" + "bu" + '"',
        )
        for forbidden in private_names:
            self.assertNotIn(forbidden, serialized)

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
        self.assertIn('id: "t003"', self.data)
        self.assertIn('id: "t004"', self.data)
        self.assertIn('id: "t005"', self.data)
        self.assertIn("atlasSlot: { row: 0, column: 0 }", self.data)
        self.assertIn("atlasSlot: { row: 0, column: 2 }", self.data)
        self.assertIn("atlasSlot: { row: 0, column: 3 }", self.data)
        self.assertIn("atlasSlot: { row: 0, column: 4 }", self.data)
        self.assertIn("atlasSlot: { row: 0, column: 5 }", self.data)
        self.assertIn("function frameTakesFor(", self.app)
        self.assertIn("function renderTakeRail(", self.app)
        self.assertIn("function positionTakeRail(", self.app)
        self.assertIn("function updateTakeRailNavigation()", self.app)
        self.assertIn("function scrollTakeRail(delta)", self.app)
        self.assertIn('class="take-rail"', self.app)
        self.assertIn('class="take-card ${', self.app)
        self.assertIn("grid-column: 1 / -1;", self.css)
        self.assertIn("activeFrameTake = {", self.app)
        self.assertIn("versionId: activeVersionId", self.app)
        self.assertIn("stateId: state.id", self.app)
        self.assertIn("frameIndex: activeFrameIndex", self.app)
        self.assertIn("clearFrameTakeState();", self.app)
        self.assertNotIn('id="confirmTakeButton"', self.html)
        self.assertIn('class="take-rail-layout"', self.app)
        self.assertIn('class="take-rail-nav-button take-rail-previous"', self.app)
        self.assertIn('class="take-rail-nav-button take-rail-next"', self.app)
        self.assertIn('class="take-rail-confirm-button"', self.app)
        self.assertIn("display: flex;", self.css)
        self.assertIn(".take-rail-nav-button", self.css)
        self.assertIn(
            ".take-rail-confirm-button {\n"
            "  display: grid;\n"
            "  width: 28px;\n"
            "  height: 28px;\n"
            "  flex: 0 0 28px;",
            self.css,
        )
        self.assertIn(
            "const hasOverflow = track.scrollWidth > viewport.clientWidth + 2;",
            self.app,
        )
        self.assertIn(
            'rail.style.setProperty("--take-anchor-x", `${railAnchor}px`);',
            self.app,
        )
        self.assertIn(
            "activeCardOffset + activeCard.offsetWidth / 2 - viewportAnchor",
            self.app,
        )
        self.assertIn("previousButton.hidden = !hasOverflow;", self.app)
        self.assertIn("nextButton.hidden = !hasOverflow;", self.app)
        self.assertIn(
            'previousButton.setAttribute(\n      "aria-disabled"',
            self.app,
        )
        self.assertIn(
            'nextButton.setAttribute("aria-disabled"',
            self.app,
        )
        self.assertIn("scrollTakeRail(-1)", self.app)
        self.assertIn("scrollTakeRail(1)", self.app)
        self.assertIn(
            "activeCard.getBoundingClientRect().left -\n"
            "      track.getBoundingClientRect().left",
            self.app,
        )
        self.assertIn(
            "card.getBoundingClientRect().left - trackLeft",
            self.app,
        )
        scroll_take_rail = self.app.split(
            "function scrollTakeRail(delta) {",
            1,
        )[1].split(
            "function scheduleTakeRailPosition()",
            1,
        )[0]
        self.assertNotIn("previewFrameTake(", scroll_take_rail)
        self.assertIn(
            'const railActionControl = event.target.closest(',
            self.app,
        )
        self.assertIn(
            'if (["ArrowLeft", "ArrowRight"].includes(event.key)) {\n'
            "          event.preventDefault();",
            self.app,
        )
        self.assertIn("const confirmedFrameTakeIds = new Map();", self.app)
        self.assertIn("confirmedFrameTakeIds.has(key)", self.app)
        self.assertIn("function confirmedSelectionForFrame(", self.app)
        self.assertIn("function hasConfirmedFrameTakeForFrame(", self.app)
        self.assertIn("function previewFrameTake(takeId)", self.app)
        self.assertIn("function confirmFrameTake()", self.app)
        self.assertIn(
            "function activeTakeReadyForConfirmation()",
            self.app,
        )
        self.assertIn("function stepTake(delta)", self.app)
        self.assertNotIn("function stepTransport(delta)", self.app)
        self.assertIn("stepFrame(-1)", self.app)
        self.assertIn("stepFrame(1)", self.app)
        self.assertIn(
            "confirmedFrameTakeIds.set(key, takeId);",
            self.app,
        )
        self.assertIn('id="transportControls"', self.html)
        self.assertIn('id="takeStatus"', self.html)
        self.assertIn("function announceTakeConfirmation(", self.app)
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
        self.assertIn("setOriginalFrame(playbackState, activeFrameIndex);", render_player)
        self.assertIn("function displayedTakeForFrame(", self.app)
        self.assertIn(
            "expandedTakeFrameIndex === frameIndex &&\n"
            "      isInspectingFrame",
            self.app,
        )
        self.assertIn(
            "return confirmedTakeForFrame(version, state, frameIndex);",
            self.app,
        )
        self.assertIn("function refreshMechanicsFrameTake(", self.app)
        self.assertIn("function refreshMechanicsTakeFrames()", self.app)
        preview_take = self.app.split(
            "function previewFrameTake(takeId) {",
            1,
        )[1].split(
            "function primeFrameTakeFromConfirmed()",
            1,
        )[0]
        self.assertIn("refreshMechanicsFrameTake(", preview_take)
        mechanics_board = self.app.split(
            "function renderMechanicsBoard() {",
            1,
        )[1].split(
            "function renderDirectionList()",
            1,
        )[0]
        self.assertIn("displayedTakeForFrame(", mechanics_board)
        self.assertIn("frameTakeStyle(", mechanics_board)
        readme = (PREVIEWER / "README.md").read_text(encoding="utf-8")
        self.assertIn("Confirmation is session-only review metadata.", readme)
        self.assertIn(
            "Motion Timing follows the currently auditioned",
            readme,
        )
        self.assertNotIn(
            "Motion Timing continues\n"
            "to show the source atlas.",
            readme,
        )
        self.assertNotIn("frameTakes", self.target_data)

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
        invalidate_take = self.app.split(
            "function invalidateTakeAsset(assetUrl) {",
            1,
        )[1].split(
            "function setTakeSpriteFrame(",
            1,
        )[0]
        self.assertIn("refreshMechanicsTakeFrames();", invalidate_take)
        self.assertIn(".icon-button:disabled", self.css)

    def test_all_render_assets_are_preflighted_for_transparency(self) -> None:
        self.assertIn(
            "async function assertTransparentCandidateAssets(",
            self.app,
        )
        self.assertIn(
            "function projectAssetEntries(\n    version,",
            self.app,
        )
        self.assertIn(
            "function atlasCellsForVersion(version)",
            self.app,
        )
        self.assertIn(
            "function requireTransparentPixels(context, rect, entry, field = entry.field)",
            self.app,
        )
        self.assertIn(
            'code: "ASSET_FULLY_OPAQUE"',
            self.app,
        )
        self.assertIn(
            "entry.cells.forEach((cell) =>",
            self.app,
        )
        self.assertIn(
            "`${version.id}/look-${slot.degree}-${slot.key}`",
            self.app,
        )
        load_config = self.app.split(
            "async function loadConfig(requestedReviewContext) {",
            1,
        )[1].split(
            "function normalizeConfig(",
            1,
        )[0]
        self.assertIn("const result = await inspectCandidate(selected", load_config)
        self.assertNotIn("assertTransparentProjectAssets", self.app)
        background = self.app.split(
            "function startBackgroundCandidateDiagnostics(loaded) {",
            1,
        )[1].split("function resolveAssetUrl(", 1)[0]
        self.assertIn("loaded.backgroundCandidates.map", background)
        self.assertIn("Promise.allSettled(jobs)", background)
        self.assertIn("trustedBundled: true", background)
        self.assertIn("ASSET_PREFLIGHT_TIMEOUT_MS", self.app)

    def test_candidate_isolation_has_typed_safe_diagnostics(self) -> None:
        self.assertIn('role="alert"', self.html)
        self.assertIn('tabindex="-1"', self.html)
        for field in (
            "configErrorConfig",
            "configErrorCandidate",
            "configErrorField",
            "configErrorCode",
            "configErrorExpected",
            "configErrorActual",
            "configErrorNextStep",
        ):
            self.assertIn(f'id="{field}"', self.html)
        for code in (
            "TARGET_MISMATCH",
            "UNSAFE_ASSET_URL",
            "DUPLICATE_STATE_ID",
            "UNKNOWN_STATE_ID",
            "ASSET_FULLY_OPAQUE",
            "ATLAS_GEOMETRY_MISMATCH",
        ):
            self.assertIn(code, self.app)
        self.assertIn("PROJECT_ASSET_URL_PATTERN", self.app)
        self.assertIn("candidateUnavailableReasonSuffix", self.app)
        self.assertIn('${unavailable ? "disabled" : ""}', self.app)
        self.assertIn("safeConfigReference", self.app)
        self.assertIn('if (resolved.protocol === "file:")', self.app)
        self.assertIn('t("ui.localPreviewConfig")', self.app)
        self.assertIn("sanitizedUrlFact", self.app)
        self.assertIn('return "[local file]";', self.app)
        self.assertIn('"[local path]"', self.app)
        self.assertIn("DIAGNOSTIC_FACT_MAX_LENGTH", self.app)
        self.assertIn("escapeHtml(safeFact(activeVersionId))", self.app)
        self.assertIn('value="" selected disabled', self.app)
        self.assertIn("Promise.allSettled(jobs)", self.app)
        self.assertIn('candidateErrorTitle: "Candidate Preview Unavailable"', self.i18n)
        self.assertIn('candidateErrorTitle: "当前方案暂不可预览"', self.i18n)

    def test_legacy_candidate_ids_remain_compatible(self) -> None:
        self.assertNotIn("CANDIDATE_ID_PATTERN", self.app)
        self.assertIn('typeof version.id !== "string"', self.app)
        self.assertIn("!version.id.trim()", self.app)

    def test_candidate_and_take_copy_is_localized(self) -> None:
        self.assertIn('version: "Candidate"', self.i18n)
        self.assertIn('version: "方案"', self.i18n)
        self.assertIn('originalFrame: "Original"', self.i18n)
        self.assertIn('originalFrame: "原始"', self.i18n)
        self.assertIn('confirmTake: "Confirm Take"', self.i18n)
        self.assertIn('confirmTake: "确认当前 Take"', self.i18n)
        self.assertIn('previousTakes: "Previous Takes"', self.i18n)
        self.assertIn('nextTakes: "Next Takes"', self.i18n)
        self.assertIn('previousTakes: "向左查看更多 Takes"', self.i18n)
        self.assertIn('nextTakes: "向右查看更多 Takes"', self.i18n)

    def test_preview_size_is_display_only(self) -> None:
        self.assertIn('id="previewSizeInput"', self.html)
        self.assertIn('id="previewSizeValue"', self.html)
        self.assertNotIn('min="80"', self.html)
        self.assertNotIn('max="224"', self.html)
        self.assertIn('value="160"', self.html)
        self.assertIn("config.display.minimumPx", self.app)
        self.assertIn("config.display.maximumPx", self.app)
        self.assertIn(
            "elements.previewSizeInput.min = String(config.display.minimumPx);",
            self.app,
        )
        self.assertIn(
            "elements.previewSizeInput.max = String(config.display.maximumPx);",
            self.app,
        )
        self.assertEqual(80, self.target["display"]["minimumPx"])
        self.assertEqual(224, self.target["display"]["maximumPx"])
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
        self.assertIn("autoPlayAllStates: \"Play All States\"", self.i18n)
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
        ):
            self.assertNotIn(removed, self.app)
        self.assertNotIn("5000", self.html + self.app + self.i18n)

        self.assertNotIn("FIXED_ACTION_LOOPS", self.app)
        self.assertNotIn("FIXED_IDLE_SLOWDOWN", self.app)
        self.assertIn("const deliveryTarget = window.PET_DELIVERY_TARGET;", self.app)
        self.assertIn("sprite: {", self.app)
        self.assertIn("columns: deliveryTarget.atlas.columns", self.app)
        self.assertIn("rows: deliveryTarget.atlas.rows", self.app)
        self.assertIn("states: deliveryTarget.states.map(", self.app)
        self.assertIn(
            "directions: cloneValue(deliveryTarget.lookDirections.slots)",
            self.app,
        )
        self.assertIn("runtime: cloneValue(deliveryTarget.runtime)", self.app)
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
            state = next(
                item for item in self.target["states"] if item["id"] == state_id
            )
            self.assertEqual(row, state["row"], state_id)
            self.assertEqual(durations, state["durationsMs"], state_id)
        self.assertIn("function runtimeFrameDuration(state, frameIndex)", self.app)
        self.assertIn(
            "? baseDuration * config.runtime.idleDurationMultiplier",
            self.app,
        )
        self.assertIn(
            "const delay = runtimeFrameDuration(state, activeFrameIndex);",
            self.app,
        )
        self.assertIn(
            "state.durations.length * config.runtime.actionLoops",
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

    def test_autoplay_progress_belongs_to_state_panel(self) -> None:
        state_panel = self.html.split(
            '<aside class="state-panel">',
            1,
        )[1].split(
            "</aside>",
            1,
        )[0]
        detail_panel = self.html.split(
            '<aside class="detail-panel">',
            1,
        )[1].split(
            "</aside>",
            1,
        )[0]
        self.assertIn('id="tourProgress"', state_panel)
        self.assertNotIn('id="tourProgress"', detail_panel)
        self.assertIn("margin-top: auto;", self.css)
        self.assertIn("#tourLabel", self.css)
        self.assertIn("text-overflow: ellipsis;", self.css)
        self.assertIn("#tourProgressText", self.css)
        self.assertIn("font-variant-numeric: tabular-nums;", self.css)
        self.assertRegex(
            self.css,
            r"@media \(max-width: 1080px\)[\s\S]*?"
            r"\.frame-section\s*\{[\s\S]*?grid-column: 1 / -1;",
        )
        self.assertRegex(
            self.css,
            r"@media \(max-width: 760px\)[\s\S]*?"
            r"\.frame-section\s*\{[\s\S]*?grid-column: auto;",
        )

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

    def test_english_copy_is_native_and_contextual(self) -> None:
        expected = (
            'autoPlayAllStates: "Play All States"',
            'animationStates: "State Animations"',
            'lookDirections: "Gaze Directions"',
            'runtimeTiming: "Runtime Simulation"',
            'endlessLoop: "Endless Loop"',
            'confirmTake: "Confirm Take"',
            'keyframes: "Keyframes"',
            'mechanicsTitle: "Motion Timing"',
            'title: "Resting Nearby"',
            'label: "Move Right"',
            'title: "Moving Right"',
            'label: "Move Left"',
            'title: "Moving Left"',
            'title: "A Quiet Hello"',
            'title: "A Light Jump"',
            'title: "Bouncing Back"',
            'title: "Waiting for You"',
            'title: "Focused on the Task"',
            'title: "Checking the Result"',
            'lookTitle: "Responsive Gaze"',
            'takeAssetLoading: "Loading Take…"',
            'duration: "{frames} frames · {seconds} s per loop{runtimeNote}"',
        )
        for copy in expected:
            self.assertIn(copy, self.i18n)
        for awkward in (
            "Auto-Play All States",
            "pauses on the atlas",
            "Following Attention",
            "A task is processing",
            "6× Idle",
            "Slow Idle",
            "Scroll Takes Left",
            "Scroll Takes Right",
            "replace through preview-data.js",
            "Direction reads at full strength",
            "Cadence closes cleanly",
        ):
            self.assertNotIn(awkward, self.i18n)
        self.assertIn(
            'runtimeIdleModeHelp:',
            self.i18n,
        )
        self.assertIn(
            "currentState().id === config.runtime.idleStateId\n"
            '              ? "ui.runtimeIdleModeHelp"\n'
            '              : "ui.runtimeModeHelp"',
            self.app,
        )
        self.assertIn("padding: 3px 12px;", self.css)

    def test_playback_modes_have_explanatory_copy(self) -> None:
        for key in (
            "runtimeTimingTitle",
            "endlessLoopTitle",
            "endlessModeHelp",
            "runtimeIdleModeHelp",
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
        self.assertIn("let lookIsNeutral = false;", self.app)
        self.assertIn(
            "neutralLookStateId: deliveryTarget.lookDirections.neutralStateId",
            self.app,
        )
        self.assertIn(
            "pointerFrameRequest = window.requestAnimationFrame(flushPointerMove);",
            self.app,
        )
        self.assertIn("function cancelPointerUpdate()", self.app)
        self.assertIn(
            "if (lookIsNeutral || directionIndex !== activeDirectionIndex) {\n"
            "      setDirection(directionIndex);\n"
            "    }",
            self.app,
        )
        self.assertIn("function setLookNeutral()", self.app)
        self.assertIn(
            "if (Math.hypot(deltaX, deltaY) < 28) {\n"
            '      elements.directionTarget.style.display = "none";\n'
            "      setLookNeutral();\n"
            "      return;\n"
            "    }",
            self.app,
        )
        self.assertIn(
            'elements.stage.addEventListener("pointerleave", () => {',
            self.app,
        )
        self.assertIn('lookNeutralReadout: "Pointer Dead Zone · {state}"', self.i18n)
        self.assertIn('lookNeutralReadout: "指针中心区 · {state}"', self.i18n)
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
        self.assertIn('lookTitle: "Responsive Gaze"', self.i18n)
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
        stage_rule = self.css.split(".stage {", 1)[1].split("}", 1)[0]
        self.assertIn("contain: layout paint;", stage_rule)
        sprite_rule = self.css.split(".sprite-player {", 1)[1].split("}", 1)[0]
        self.assertNotIn("filter:", sprite_rule)
        size_control_rule = self.css.split(
            ".preview-size-control {", 1
        )[1].split("}", 1)[0]
        self.assertNotIn("backdrop-filter", size_control_rule)
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
