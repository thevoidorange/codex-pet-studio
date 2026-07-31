#!/usr/bin/env python3
"""Smooth alpha and remove background contamination from a separated asset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from transparency_core import (
    TransparencyError,
    clean_auto_border_edges,
    clean_chroma_edges,
    clear_hidden_rgb,
    fit_auto_border_background,
    parse_hex_color,
    require_meaningful_transparency,
)


def optional_cell_size(args: argparse.Namespace) -> tuple[int, int] | None:
    if args.cell_width is None and args.cell_height is None:
        return None
    if args.cell_width is None or args.cell_height is None:
        raise TransparencyError(
            "--cell-width and --cell-height must be supplied together"
        )
    if args.cell_width < 1 or args.cell_height < 1:
        raise TransparencyError("cell dimensions must be positive")
    return args.cell_width, args.cell_height


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--webp-output")
    parser.add_argument(
        "--mode",
        choices=("auto-border", "chroma", "preserve-alpha"),
        required=True,
    )
    parser.add_argument(
        "--background-source",
        help="original opaque source used to refit auto-border background",
    )
    parser.add_argument("--chroma-key")
    parser.add_argument("--strength", type=float, default=1)
    parser.add_argument("--edge-radius", type=int, default=5)
    parser.add_argument("--spill-tolerance", type=float, default=0.15)
    parser.add_argument("--minimum-saturation", type=float, default=0.1)
    parser.add_argument("--alpha-blur-radius", type=float, default=0.65)
    parser.add_argument("--cell-width", type=int)
    parser.add_argument("--cell-height", type=int)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    try:
        with Image.open(input_path) as opened:
            separated = opened.copy()
        require_meaningful_transparency(
            separated,
            label="separated asset",
        )
        if args.mode == "auto-border":
            if not args.background_source:
                raise TransparencyError(
                    "auto-border cleanup requires --background-source"
                )
            source_path = Path(args.background_source).expanduser().resolve()
            with Image.open(source_path) as opened:
                source = opened.copy()
            if source.size != separated.size:
                raise TransparencyError(
                    "background source and separated asset must share a canvas"
                )
            background, model_report = fit_auto_border_background(source)
            cleaned, report = clean_auto_border_edges(
                separated,
                source=source,
                background=background,
                alpha_blur_radius=args.alpha_blur_radius,
            )
            report["background_model"] = model_report
        elif args.mode == "chroma":
            if not args.chroma_key:
                raise TransparencyError(
                    "chroma cleanup requires --chroma-key #RRGGBB"
                )
            cleaned, report = clean_chroma_edges(
                separated,
                chroma_key=parse_hex_color(args.chroma_key),
                strength=args.strength,
                edge_radius=args.edge_radius,
                spill_tolerance=args.spill_tolerance,
                minimum_saturation=args.minimum_saturation,
                cell_size=optional_cell_size(args),
                alpha_blur_radius=args.alpha_blur_radius,
            )
        else:
            cleaned = clear_hidden_rgb(separated)
            report = {
                "algorithm": "clear-hidden-rgb",
                "alpha_preserved": True,
                "hidden_rgb_cleared": True,
            }
        require_meaningful_transparency(
            cleaned,
            label="cleaned asset",
        )
    except (OSError, TransparencyError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.save(output_path, format="PNG")
    webp_output_path = (
        Path(args.webp_output).expanduser().resolve()
        if args.webp_output
        else None
    )
    if webp_output_path is not None:
        webp_output_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned.save(
            webp_output_path,
            format="WEBP",
            lossless=True,
            quality=100,
            method=6,
            exact=True,
        )
    result = {
        "ok": True,
        "stage": "alpha-edge-cleanup",
        "mode": args.mode,
        "input": str(input_path),
        "output": str(output_path),
        "webp_output": (
            str(webp_output_path)
            if webp_output_path is not None
            else None
        ),
        **report,
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
