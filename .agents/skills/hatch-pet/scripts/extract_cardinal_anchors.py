#!/usr/bin/env python3
"""Extract and validate a four-pose cardinal anchor strip."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

SHARED_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "prepare-transparent-assets"
    / "scripts"
)
if not (SHARED_SCRIPTS / "transparency_core.py").is_file():
    raise RuntimeError(
        "Missing project-bundled $prepare-transparent-assets dependency: "
        f"{SHARED_SCRIPTS}"
    )
sys.path.insert(0, str(SHARED_SCRIPTS))
from transparency_core import (  # noqa: E402
    TransparencyError,
    parse_hex_color as shared_parse_hex_color,
    remove_chroma_background,
)

CARDINALS = ["000", "090", "180", "270"]
CELL_WIDTH = 192
CELL_HEIGHT = 208


def parse_hex_color(value: str) -> tuple[int, int, int]:
    try:
        return shared_parse_hex_color(value)
    except TransparencyError as exc:
        raise SystemExit(str(exc)) from exc


def alpha_count(image: Image.Image) -> int:
    alpha = image if image.mode == "L" else image.getchannel("A")
    return sum(alpha.histogram()[1:])


def edge_alpha_count(image: Image.Image, margin: int) -> int:
    alpha = image.getchannel("A")
    width, height = alpha.size
    return sum(
        alpha_count(alpha.crop(box))
        for box in (
            (0, 0, width, margin),
            (0, height - margin, width, height),
            (0, 0, margin, height),
            (width - margin, 0, width, height),
        )
    )


def fit_to_cell(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    target = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    if bbox is None:
        return target
    sprite = image.crop(bbox)
    scale = min((CELL_WIDTH - 10) / sprite.width, (CELL_HEIGHT - 10) / sprite.height, 1.0)
    if scale != 1.0:
        sprite = sprite.resize(
            (max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale))),
            Image.Resampling.LANCZOS,
        )
    target.alpha_composite(
        sprite,
        ((CELL_WIDTH - sprite.width) // 2, (CELL_HEIGHT - sprite.height) // 2),
    )
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strip", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--chroma-key", required=True)
    parser.add_argument("--chroma-threshold", type=float, default=96.0)
    parser.add_argument("--edge-margin", type=int, default=2)
    parser.add_argument("--edge-pixel-threshold", type=int, default=24)
    parser.add_argument("--min-used-pixels", type=int, default=400)
    args = parser.parse_args()

    strip_path = Path(args.strip).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(strip_path) as opened:
        strip = remove_chroma_background(
            opened,
            parse_hex_color(args.chroma_key),
            args.chroma_threshold,
        )

    slot_width = strip.width / len(CARDINALS)
    anchors = []
    errors = []
    for index, label in enumerate(CARDINALS):
        left = round(index * slot_width)
        right = round((index + 1) * slot_width)
        source_cell = strip.crop((left, 0, right, strip.height))
        used_pixels = alpha_count(source_cell)
        edge_pixels = edge_alpha_count(source_cell, args.edge_margin)
        output = output_dir / f"{label}.png"
        fit_to_cell(source_cell).save(output)
        if used_pixels < args.min_used_pixels:
            errors.append(f"{label} is empty or too sparse ({used_pixels} pixels)")
        if edge_pixels > args.edge_pixel_threshold:
            errors.append(
                f"{label} has {edge_pixels} non-transparent pixels near its source slot edge"
            )
        anchors.append(
            {
                "direction": label,
                "source_box": [left, 0, right, strip.height],
                "used_pixels": used_pixels,
                "edge_pixels": edge_pixels,
                "output": str(output),
            }
        )

    result = {
        "ok": not errors,
        "strip": str(strip_path),
        "directions": CARDINALS,
        "errors": errors,
        "anchors": anchors,
    }
    json_out = Path(args.json_out).expanduser().resolve()
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "anchors"}, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
