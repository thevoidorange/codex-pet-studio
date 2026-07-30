from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "pet-studio"
SKILL_MD = SKILL / "SKILL.md"


class SkillBundleTests(unittest.TestCase):
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
        self.assertIn("current project", metadata)
        self.assertIn("resume", metadata)

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


if __name__ == "__main__":
    unittest.main()
