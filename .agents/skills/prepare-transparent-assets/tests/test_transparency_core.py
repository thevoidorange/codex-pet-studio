from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "transparency_core.py"
)
SPEC = importlib.util.spec_from_file_location(
    "creatures_transparency_core",
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORE)


class TransparencyCoreTests(unittest.TestCase):
    def test_existing_saturated_matte_uses_border_and_corner_evidence(self) -> None:
        image = Image.new("RGB", (160, 160), "#FF00FF")
        for y in range(36, 124):
            for x in range(36, 124):
                if x < 66:
                    color = (0, 255, 0)
                elif x < 96:
                    color = (255, 255, 0)
                else:
                    color = (255, 127, 0)
                image.putpixel((x, y), color)

        report = CORE.detect_existing_saturated_matte(image)

        self.assertEqual("high", report["confidence"])
        self.assertEqual("#FF00FF", report["candidate_hex"])
        self.assertEqual(4, report["evidence"]["corner_matches"])
        self.assertGreaterEqual(
            min(report["evidence"]["edge_coverage"].values()),
            0.75,
        )

    def test_low_chroma_border_stays_outside_saturated_matte_detection(
        self,
    ) -> None:
        image = Image.new("RGB", (128, 128), "#F4F4F1")
        for y in range(32, 96):
            for x in range(32, 96):
                image.putpixel((x, y), (32, 64, 128))

        report = CORE.detect_existing_saturated_matte(image)

        self.assertEqual("none", report["confidence"])
        self.assertIn("not a saturated matte", report["reason"])

    def test_existing_alpha_stays_outside_saturated_matte_detection(self) -> None:
        image = Image.new("RGBA", (128, 128), (255, 0, 255, 0))
        for y in range(24, 104):
            for x in range(24, 104):
                image.putpixel((x, y), (20, 80, 180, 255))

        report = CORE.detect_existing_saturated_matte(image)

        self.assertEqual("none", report["confidence"])
        self.assertIn("already contains alpha", report["reason"])

    def test_subject_crossing_one_edge_does_not_receive_high_confidence(
        self,
    ) -> None:
        image = Image.new("RGB", (128, 128), "#FF00FF")
        for y in range(0, 128):
            for x in range(0, 20):
                image.putpixel((x, y), (32, 48, 96))

        report = CORE.detect_existing_saturated_matte(image)

        self.assertEqual("medium", report["confidence"])
        self.assertLess(report["evidence"]["edge_coverage"]["left"], 0.75)

    def test_chroma_key_is_inclusive_and_preserves_other_alpha(self) -> None:
        image = Image.new("RGBA", (3, 1))
        image.putdata(
            [
                (0, 255, 0, 255),
                (10, 255, 0, 255),
                (11, 255, 0, 128),
            ]
        )

        result = CORE.remove_chroma_background(
            image,
            (0, 255, 0),
            10,
        )

        self.assertEqual((0, 0, 0, 0), result.getpixel((0, 0)))
        self.assertEqual((0, 0, 0, 0), result.getpixel((1, 0)))
        self.assertEqual((11, 255, 0, 128), result.getpixel((2, 0)))
        self.assertEqual((0, 255, 0, 255), image.getpixel((0, 0)))

    def test_preserve_alpha_clears_hidden_rgb_without_changing_alpha(self) -> None:
        image = Image.new("RGBA", (2, 1))
        image.putdata([(200, 100, 50, 0), (20, 40, 60, 128)])

        result, report = CORE.prepare_transparent_image(
            image,
            mode="preserve-alpha",
        )

        self.assertEqual((0, 0, 0, 0), result.getpixel((0, 0)))
        self.assertEqual((20, 40, 60, 128), result.getpixel((1, 0)))
        self.assertTrue(report["cleanup"]["alpha_preserved"])

    def test_auto_border_separates_gradient_and_unmixes_foreground(self) -> None:
        width = 192
        height = 192
        y, x = np.mgrid[0:height, 0:width]
        background = np.stack(
            [
                246 - 5 * (x / width) ** 2,
                242 - 4 * (y / height) ** 2,
                232 - 3 * ((x + y) / (width + height)) ** 2,
            ],
            axis=-1,
        )
        source = background.copy()
        foreground = np.array([35, 95, 190], dtype=np.float32)
        alpha = np.zeros((height, width), dtype=np.float32)
        radius = np.sqrt((x - 96) ** 2 + (y - 96) ** 2)
        alpha[radius <= 40] = 0.68
        alpha[(radius > 40) & (radius <= 44)] = (
            (44 - radius[(radius > 40) & (radius <= 44)]) / 4 * 0.68
        )
        source = (
            alpha[..., None] * foreground
            + (1 - alpha[..., None]) * source
        )
        image = Image.fromarray(
            np.uint8(np.clip(source + 0.5, 0, 255)),
            "RGB",
        )

        result, report = CORE.prepare_transparent_image(
            image,
            mode="auto-border",
        )

        summary = CORE.require_meaningful_transparency(result)
        self.assertGreater(summary["transparent_pixels"], 0)
        self.assertGreater(result.getpixel((96, 96))[3], 100)
        self.assertEqual((0, 0, 0, 0), result.getpixel((0, 0)))
        recovered = result.getpixel((96, 96))
        self.assertAlmostEqual(recovered[0], foreground[0], delta=24)
        self.assertAlmostEqual(recovered[1], foreground[1], delta=24)
        self.assertAlmostEqual(recovered[2], foreground[2], delta=24)
        self.assertEqual(
            "robust-polynomial-auto-border-matte",
            report["separation"]["algorithm"],
        )
        self.assertEqual(
            "background-unmix-alpha-cleanup",
            report["cleanup"]["algorithm"],
        )

    def test_chroma_edge_cleanup_preserves_alpha_and_cell_isolation(self) -> None:
        image = Image.new("RGBA", (384, 208), (0, 0, 0, 0))
        image.putpixel((191, 100), (220, 40, 180, 128))
        image.putpixel((192, 100), (20, 80, 220, 255))

        cleaned, report = CORE.decontaminate_image(
            image,
            chroma_key=(255, 0, 255),
            edge_radius=1,
            cell_size=(192, 208),
        )

        red, green, blue, alpha = cleaned.getpixel((191, 100))
        self.assertEqual((red, green, blue), (red, red, red))
        self.assertEqual(128, alpha)
        self.assertTrue(report["alpha_preserved"])

    def test_composed_chroma_cleanup_smooths_alpha_inside_each_cell(self) -> None:
        image = Image.new("RGBA", (384, 208), (0, 0, 0, 0))
        for y in range(98, 103):
            for x in range(186, 191):
                image.putpixel((x, y), (20, 80, 220, 255))

        cleaned, report = CORE.clean_chroma_edges(
            image,
            chroma_key=(255, 0, 255),
            edge_radius=3,
            cell_size=(192, 208),
            alpha_blur_radius=1,
        )

        smoothed_edge = cleaned.getpixel((191, 100))
        self.assertGreater(smoothed_edge[3], 0)
        self.assertLess(smoothed_edge[3], 255)
        self.assertNotEqual((0, 0, 0), smoothed_edge[:3])
        self.assertEqual((0, 0, 0, 0), cleaned.getpixel((192, 100)))
        self.assertTrue(
            report["alpha_smoothing"]["alpha_smoothed"]
        )
        self.assertFalse(report["alpha_preserved"])

    def test_cell_isolation_rejects_an_inexact_grid(self) -> None:
        image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        image.putpixel((5, 5), (20, 80, 220, 255))

        with self.assertRaisesRegex(
            CORE.TransparencyError,
            "exactly divide the canvas",
        ):
            CORE.clean_chroma_edges(
                image,
                chroma_key=(255, 0, 255),
                cell_size=(6, 5),
            )


if __name__ == "__main__":
    unittest.main()
