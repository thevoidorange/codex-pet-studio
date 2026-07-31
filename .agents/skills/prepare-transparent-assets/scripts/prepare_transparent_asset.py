#!/usr/bin/env python3
"""Run background separation and alpha-edge cleanup for any Creature asset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from transparency_core import (
    TransparencyError,
    parse_hex_color,
    prepare_transparent_image,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode",
        choices=("auto", "auto-border", "chroma", "preserve-alpha"),
        default="auto",
    )
    parser.add_argument("--chroma-key")
    parser.add_argument("--chroma-threshold", type=float, default=96)
    parser.add_argument("--strength", type=float, default=1)
    parser.add_argument("--edge-radius", type=int, default=5)
    parser.add_argument("--spill-tolerance", type=float, default=0.15)
    parser.add_argument("--minimum-saturation", type=float, default=0.1)
    parser.add_argument("--alpha-blur-radius", type=float, default=0.65)
    parser.add_argument("--cell-width", type=int)
    parser.add_argument("--cell-height", type=int)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    if (args.cell_width is None) != (args.cell_height is None):
        raise SystemExit(
            "ERROR: --cell-width and --cell-height must be supplied together"
        )
    cell_size = (
        (args.cell_width, args.cell_height)
        if args.cell_width is not None
        else None
    )
    if cell_size and (cell_size[0] < 1 or cell_size[1] < 1):
        raise SystemExit("ERROR: cell dimensions must be positive")

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    try:
        with Image.open(input_path) as opened:
            source = opened.copy()
        chroma_key = (
            parse_hex_color(args.chroma_key)
            if args.chroma_key
            else None
        )
        prepared, report = prepare_transparent_image(
            source,
            mode=args.mode,
            chroma_key=chroma_key,
            chroma_threshold=args.chroma_threshold,
            edge_strength=args.strength,
            edge_radius=args.edge_radius,
            spill_tolerance=args.spill_tolerance,
            minimum_saturation=args.minimum_saturation,
            cell_size=cell_size,
            alpha_blur_radius=args.alpha_blur_radius,
        )
    except (OSError, TransparencyError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.save(output_path, format="PNG")
    result = {
        **report,
        "input": str(input_path),
        "output_path": str(output_path),
    }
    if args.json_out:
        json_path = Path(args.json_out).expanduser().resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
