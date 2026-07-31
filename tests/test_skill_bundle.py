from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "pet-studio"
SKILL_MD = SKILL / "SKILL.md"
HATCH_SKILL = ROOT / ".agents" / "skills" / "hatch-pet"


class SkillBundleTests(unittest.TestCase):
    def test_agent_contract_puts_the_user_first(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(
            "Treat the person using this project—not the repository",
            agents,
        )
        for protected_interest in (
            "agency",
            "intent",
            "preferences",
            "privacy",
            "creative ownership",
            "interests",
        ):
            self.assertIn(protected_interest, agents)
        self.assertIn("pause and ask rather than infer consent", agents)

    def test_hatch_pet_production_skill_is_bundled_and_exported(self) -> None:
        project = json.loads((ROOT / "pet-studio.json").read_text(encoding="utf-8"))
        hatch_markdown = (HATCH_SKILL / "SKILL.md").read_text(encoding="utf-8")
        hatch_license = (HATCH_SKILL / "LICENSE.txt").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        pet_studio = SKILL_MD.read_text(encoding="utf-8")

        self.assertIn(".agents/skills/hatch-pet/**", project["export"]["include"])
        self.assertIn("Apache License", hatch_license)
        self.assertIn("project-bundled `$hatch-pet`", agents)
        self.assertIn("project-bundled `$hatch-pet`", pet_studio)
        self.assertIn("Modified for Codex Pet Studio", hatch_markdown)
        self.assertIn(
            "Do not use for cold-start inspiration or early concept exploration",
            hatch_markdown,
        )
        self.assertIn(
            'PET_DIR="${PET_OUTPUT_DIR:-$RUN_DIR/package/$PET_ID}"',
            hatch_markdown,
        )
        self.assertNotIn(
            'PET_DIR="${CODEX_HOME:-$HOME/.codex}/pets/$PET_ID"',
            hatch_markdown,
        )
        prepare = (
            HATCH_SKILL / "scripts" / "prepare_pet_run.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'Path.cwd() / "build" / "hatch-pet"',
            prepare,
        )
        self.assertNotIn(
            'Path.cwd() / "output" / "hatch-pet"',
            prepare,
        )
        self.assertIn("output/", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        workflow = (
            ROOT / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("Pillow>=10,<13", workflow)
        self.assertIn(
            "python -m unittest discover -s .agents/skills/hatch-pet/tests -v",
            workflow,
        )
        self.assertGreaterEqual(
            len(list((HATCH_SKILL / "scripts").glob("*.py"))),
            10,
        )

    def test_readme_leads_with_the_suite_and_single_paste_start(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        hero = ROOT / "docs" / "assets" / "codex-pet-studio-preview.png"
        self.assertIn(
            "complete co-design suite",
            readme,
        )
        self.assertIn("your own Codex locally", readme)
        self.assertIn("guided agent skills, a live Previewer", readme)
        self.assertIn("production tooling, and QA", readme)
        self.assertIn("in one project.", readme)
        self.assertIn(
            "![Codex Pet Studio Previewer showing Raincoat Cat states, "
            "animation playback, and Keyframes]"
            "(docs/assets/codex-pet-studio-preview.png)",
            readme,
        )
        self.assertTrue(hero.is_file(), hero)
        self.assertIn("## Start a blank Codex task and paste:", readme)
        self.assertNotIn("## Start in two steps", readme)
        self.assertNotIn("### 2. Share your inspiration", readme)

    def test_skill_frontmatter_and_trigger_cover_all_entry_routes(self) -> None:
        content = SKILL_MD.read_text(encoding="utf-8")
        match = re.match(r"^---\n(?P<frontmatter>.*?)\n---\n", content, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group("frontmatter")
        self.assertRegex(frontmatter, r"(?m)^name: pet-studio$")
        description_match = re.search(
            r"(?m)^description: (?P<description>.+)$",
            frontmatter,
        )
        self.assertIsNotNone(description_match)
        description = description_match.group("description")
        for phrase in (
            "inspiration",
            "existing project",
            "Candidate/Keyframe/Take",
            "existing-pack maintenance",
            "explicitly install",
        ):
            self.assertIn(phrase, description)

    def test_skill_markdown_links_resolve(self) -> None:
        markdown_files = [SKILL_MD, *(SKILL / "references").glob("*.md")]
        for markdown in markdown_files:
            content = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", content):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (markdown.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(
                    resolved.is_file(),
                    f"{markdown.relative_to(ROOT)} links to missing {target}",
                )

    def test_long_references_have_contents_map(self) -> None:
        for reference in (SKILL / "references").glob("*.md"):
            lines = reference.read_text(encoding="utf-8").splitlines()
            if len(lines) > 100:
                self.assertIn(
                    "## Contents",
                    lines,
                    f"{reference.name} needs a contents map",
                )

    def test_review_workbench_is_deterministic_and_non_mutating(self) -> None:
        content = SKILL_MD.read_text(encoding="utf-8")
        for phrase in (
            "studio.py take add --help",
            "one-based",
            "neighboring frames",
            "auditioned, not approved",
            "session-only",
        ):
            self.assertIn(phrase, content)

    def test_openai_metadata_matches_resumable_skill(self) -> None:
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Codex Pet Studio"', metadata)
        self.assertIn("$pet-studio", metadata)
        self.assertIn("immediately open the Previewer", metadata)
        self.assertIn("preserve existing approvals", metadata)

    def test_new_inspiration_route_is_image_first_and_not_questionnaire_first(
        self,
    ) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        creative = (SKILL / "references" / "creative-workflow.md").read_text(
            encoding="utf-8"
        )
        visual = (SKILL / "references" / "visual-iteration.md").read_text(
            encoding="utf-8"
        )
        qa = (SKILL / "references" / "qa.md").read_text(encoding="utf-8")
        combined = "\n".join((SKILL_MD.read_text(encoding="utf-8"), agents))
        normalized = " ".join(combined.lower().split())

        self.assertIn("multimodal alignment", normalized)
        self.assertIn("first static character study", normalized)
        self.assertIn("at most one genuinely blocking question", normalized)
        self.assertIn(
            "stop before the next dependent creative layer",
            normalized,
        )
        self.assertIn("same creative round", creative)
        self.assertIn("not a final\npresentation step", visual)
        self.assertIn("neutral identity and default form", visual)
        self.assertIn("Stop after each visual checkpoint", visual)
        self.assertIn(
            "before any full questionnaire or pack",
            " ".join(qa.split()),
        )
        self.assertNotIn(
            "Do not generate until the user approves the Gate 1 reading",
            combined,
        )
        self.assertNotIn(
            "wait for explicit alignment before image generation",
            creative,
        )

    def test_readme_sets_clear_model_experience_tiers(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        normalized = " ".join(readme.split())
        recommended = (
            "Recommended for the full experience: GPT‑5.6 Sol, Medium+"
        )
        demanding = (
            "For demanding visual and animation work: "
            "GPT‑5.6 Sol, High or Ultra"
        )
        not_recommended = (
            "Not recommended: GPT‑5.6 Luna or any model at Low effort"
        )
        bare_bones_minimum = (
            "minimum usable fallback is GPT‑5.6 Terra, Medium"
        )
        for phrase in (
            recommended,
            demanding,
            not_recommended,
            bare_bones_minimum,
            "for bare-bones workflow completion only",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotIn("- **Minimum usable", readme)
        self.assertLess(
            normalized.index(recommended),
            normalized.index(demanding),
        )
        self.assertLess(
            normalized.index(demanding),
            normalized.index(not_recommended),
        )
        self.assertLess(
            normalized.index(not_recommended),
            normalized.index(bare_bones_minimum),
        )

    def test_true_cold_start_reports_model_guidance_once(self) -> None:
        skill = " ".join(SKILL_MD.read_text(encoding="utf-8").split())
        agents = " ".join(
            (ROOT / "AGENTS.md").read_text(encoding="utf-8").split()
        )
        qa = " ".join(
            (SKILL / "references" / "qa.md").read_text(encoding="utf-8").split()
        )
        readme = " ".join(
            (ROOT / "README.md").read_text(encoding="utf-8").split()
        )

        self.assertIn("one-time model-guidance report", skill)
        self.assertIn("preserving the README's published order", skill)
        self.assertIn(
            "README `Model guidance` in its published order",
            agents,
        )
        self.assertIn("full-experience recommendation first", agents)
        self.assertIn(
            "demanding visual and animation work second",
            agents,
        )
        self.assertIn("not-recommended configurations last", agents)
        self.assertIn(
            "bare-bones minimum mentioned only inside that final warning",
            agents,
        )
        self.assertIn("same setup-completion message", agents)
        self.assertIn("exactly once", agents)
        self.assertIn("Previewer restarts, task re-entry", agents)
        self.assertIn("before the first creative decision", agents)
        self.assertIn(
            "README `Model guidance` in the user's language exactly once "
            "and in its published order",
            qa,
        )
        self.assertIn("not-recommended configurations last", qa)
        self.assertIn(
            "bare-bones minimum mentioned only inside that final warning",
            qa,
        )
        self.assertIn("project re-entry do not repeat it", qa)
        self.assertIn(
            "After setup succeeds, your Codex should proactively summarize "
            "these recommendations once, in the order above",
            readme,
        )

    def test_cold_start_opens_example_then_hands_off_to_semantic_candidate(
        self,
    ) -> None:
        skill = SKILL_MD.read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        review = (SKILL / "references" / "review-workbench.md").read_text(
            encoding="utf-8"
        )
        creative = (SKILL / "references" / "creative-workflow.md").read_text(
            encoding="utf-8"
        )
        qa = (SKILL / "references" / "qa.md").read_text(encoding="utf-8")
        combined = "\n".join((skill, agents, readme, review, creative, qa))

        for content in (skill, agents, readme, review, creative, qa):
            self.assertIn("Example.RaincoatCat", content)
        self.assertIn("immediately after project setup", readme)
        self.assertIn("Cold-start Previewer handoff", review)
        self.assertIn("switch the same\nPreviewer session", review)
        self.assertIn("semantically named Static Candidate", skill)
        self.assertIn("<semantic-candidate-id>", skill)
        self.assertIn("not a sequential revision", review)
        self.assertNotIn("Use sortable IDs such as `v001`", combined)
        self.assertNotIn("--candidate v001", combined)

    def test_checked_in_path_schemas_reject_escape_paths(self) -> None:
        project_schema = json.loads(
            (SKILL / "schemas" / "project.schema.json").read_text(encoding="utf-8")
        )
        pet_schema = json.loads(
            (SKILL / "schemas" / "pet-v2.schema.json").read_text(encoding="utf-8")
        )
        project_pattern = project_schema["properties"]["paths"]["properties"]["pet"][
            "pattern"
        ]
        sprite_pattern = pet_schema["properties"]["spritesheetPath"]["pattern"]
        for unsafe in ("/tmp/pet", "../pet", "build/../pet", r"C:\pets\pet"):
            self.assertIsNone(re.fullmatch(project_pattern, unsafe), unsafe)
        self.assertIsNotNone(re.fullmatch(project_pattern, "build/pet"))
        self.assertIsNone(re.fullmatch(sprite_pattern, "../spritesheet.webp"))
        self.assertIsNotNone(re.fullmatch(sprite_pattern, "spritesheet.webp"))

    def test_product_model_and_agent_router_share_one_target_boundary(self) -> None:
        product_model = (ROOT / "docs" / "product-model.md").read_text(
            encoding="utf-8"
        )
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        project = json.loads((ROOT / "pet-studio.json").read_text(encoding="utf-8"))

        for content in (product_model, agents, readme):
            normalized = " ".join(content.split())
            self.assertIn("Codex Pet v2", normalized)
            self.assertIn("only supported Delivery Target", normalized)
        self.assertIn("Studio Core", product_model)
        self.assertIn("Behavior Driver", product_model)
        self.assertIn("docs/**", project["export"]["include"])
        self.assertLessEqual(len(agents.splitlines()), 130)

    def test_motion_language_is_separate_from_codex_target_sampling(self) -> None:
        skill = SKILL_MD.read_text(encoding="utf-8")
        targets = (SKILL / "references" / "delivery-targets.md").read_text(
            encoding="utf-8"
        )
        motion = (SKILL / "references" / "motion-and-state-contract.md").read_text(
            encoding="utf-8"
        )
        codex_target = (SKILL / "references" / "codex-pet-v2.md").read_text(
            encoding="utf-8"
        )
        studio = (SKILL / "scripts" / "studio.py").read_text(encoding="utf-8")
        target_contract = json.loads(
            (ROOT / "delivery-targets" / "codex-pet-v2.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("delivery-targets.md", skill)
        self.assertIn("Studio Core", targets)
        self.assertIn("Motion Language is Studio Core truth", motion)
        self.assertNotIn("1536×2288", motion)
        self.assertNotIn("280, 110, 110", motion)
        self.assertIn("codex-pet-v2.json", codex_target)
        self.assertNotIn("1536×2288", codex_target)
        self.assertNotIn("280, 110, 110", codex_target)
        self.assertNotIn("192x208", studio)
        atlas = target_contract["atlas"]
        self.assertEqual(
            1536,
            atlas["columns"] * atlas["cellWidthPx"],
        )
        self.assertEqual(
            [280, 110, 110, 140, 140, 320],
            target_contract["states"][0]["durationsMs"],
        )

    def test_public_templates_use_candidate_and_target_language(self) -> None:
        templates = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "templates").glob("*.md"))
        )
        self.assertNotIn("Status: `draft | review | approved`", templates)
        self.assertNotIn("Version ID:", templates)
        self.assertNotIn("Package target:", templates)
        self.assertIn("Delivery Target", templates)
        self.assertIn("Behavior Intent", templates)


if __name__ == "__main__":
    unittest.main()
