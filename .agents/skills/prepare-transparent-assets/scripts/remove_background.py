#!/usr/bin/env python3
"""Separate a Creature asset from its background without edge cleanup."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from transparency_core import (
    TransparencyError,
    clear_hidden_rgb,
    parse_hex_color,
    require_meaningful_transparency,
    separate_auto_border_background,
    separate_chroma_background,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode",
        choices=("auto-border", "chroma", "preserve-alpha"),
        required=True,
    )
    parser.add_argument("--chroma-key")
    parser.add_argument("--chroma-threshold", type=float, default=96)
    parser.add_argument("--json-out")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    try:
        with Image.open(input_path) as opened:
            source = opened.copy()
        if args.mode == "auto-border":
            separated, _background, report = (
                separate_auto_border_background(source)
            )
        elif args.mode == "chroma":
            if not args.chroma_key:
                raise TransparencyError(
                    "chroma mode requires --chroma-key #RRGGBB"
                )
            separated, report = separate_chroma_background(
                source,
                chroma_key=parse_hex_color(args.chroma_key),
                threshold=args.chroma_threshold,
            )
        else:
            require_meaningful_transparency(
                source,
                label="source asset",
            )
            separated = clear_hidden_rgb(source)
            report = {
                "algorithm": "preserve-existing-alpha",
                "alpha_preserved": True,
            }
        require_meaningful_transparency(
            separated,
            label="separated asset",
        )
    except (OSError, TransparencyError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    separated.save(output_path, format="PNG")
    result = {
        "ok": True,
        "stage": "background-separation",
        "mode": args.mode,
        "input": str(input_path),
        "output": str(output_path),
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
