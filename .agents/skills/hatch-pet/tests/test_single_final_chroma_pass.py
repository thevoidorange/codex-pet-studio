import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


class SingleFinalChromaPassTest(unittest.TestCase):
    def test_cleanup_runs_only_after_v2_assembly(self) -> None:
        instructions = SKILL.read_text()

        shared_cleanup = (
            "$TRANSPARENCY_SKILL_DIR/scripts/clean_alpha_edges.py"
        )
        self.assertEqual(instructions.count(shared_cleanup), 1)
        self.assertNotIn("scripts/despill_chroma_edges.py", instructions)
        self.assertNotIn("chroma-despill-standard.json", instructions)
        self.assertIn("--alpha-blur-radius 0.65", instructions)
        self.assertIn("--cell-width 192", instructions)
        self.assertIn("--cell-height 208", instructions)
        self.assertLess(
            instructions.index("scripts/assemble_extended_atlas.py"),
            instructions.index(shared_cleanup),
        )


if __name__ == "__main__":
    unittest.main()
