#!/usr/bin/env python3
"""Compatibility adapter for the shared Creatures alpha-edge cleanup."""

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
    DEFAULT_ATLAS_CELL_SIZE,
    EDGE_CLEANUP_ALGORITHM,
    TransparencyError,
    cell_edge_band,
    chroma_saturation,
    chroma_similarity,
    decontaminate_image as shared_decontaminate_image,
    edge_band,
    linear_to_srgb,
    parse_hex_color as shared_parse_hex_color,
    srgb_to_linear,
    suppress_boundary_spill as shared_suppress_boundary_spill,
)


CELL_WIDTH, CELL_HEIGHT = DEFAULT_ATLAS_CELL_SIZE
ALGORITHM = EDGE_CLEANUP_ALGORITHM


def parse_hex_color(value: str) -> tuple[int, int, int]:
    try:
        return shared_parse_hex_color(value)
    except TransparencyError as exc:
        raise SystemExit(str(exc)) from exc


def compatible_atlas_cell_size(
    size: tuple[int, int],
) -> tuple[int, int] | None:
    width, height = size
    if width % CELL_WIDTH or height % CELL_HEIGHT:
        return None
    return DEFAULT_ATLAS_CELL_SIZE


def atlas_edge_band(alpha: Image.Image, radius: int) -> list[bool]:
    return cell_edge_band(
        alpha,
        radius,
        compatible_atlas_cell_size(alpha.size),
    )


def suppress_boundary_spill(
    pixels: list[tuple[int, int, int, int]],
    *,
    size: tuple[int, int],
    boundary: list[bool],
    key_linear: tuple[float, float, float],
    strength: float,
    edge_radius: int,
    spill_tolerance: float,
    minimum_saturation: float,
) -> tuple[list[tuple[int, int, int, int]], list[bool]]:
    return shared_suppress_boundary_spill(
        pixels,
        size=size,
        boundary=boundary,
        key_linear=key_linear,
        strength=strength,
        edge_radius=edge_radius,
        spill_tolerance=spill_tolerance,
        minimum_saturation=minimum_saturation,
        cell_size=compatible_atlas_cell_size(size),
    )


def decontaminate_image(
    image: Image.Image,
    *,
    chroma_key: tuple[int, int, int],
    strength: float = 1,
    edge_radius: int = 5,
    spill_tolerance: float = 0.15,
    minimum_saturation: float = 0.1,
) -> tuple[Image.Image, dict[str, object]]:
    return shared_decontaminate_image(
        image,
        chroma_key=chroma_key,
        strength=strength,
        edge_radius=edge_radius,
        spill_tolerance=spill_tolerance,
        minimum_saturation=minimum_saturation,
        cell_size=compatible_atlas_cell_size(image.size),
    )


def save_image(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".webp":
        image.save(
            path,
            format="WEBP",
            lossless=True,
            quality=100,
            method=6,
            exact=True,
        )
    else:
        image.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--webp-output")
    parser.add_argument("--json-out")
    parser.add_argument("--chroma-key", required=True)
    parser.add_argument("--strength", type=float, default=1)
    parser.add_argument("--edge-radius", type=int, default=5)
    parser.add_argument("--spill-tolerance", type=float, default=0.15)
    parser.add_argument("--minimum-saturation", type=float, default=0.1)
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    with Image.open(input_path) as opened:
        cleaned, report = decontaminate_image(
            opened,
            chroma_key=parse_hex_color(args.chroma_key),
            strength=args.strength,
            edge_radius=args.edge_radius,
            spill_tolerance=args.spill_tolerance,
            minimum_saturation=args.minimum_saturation,
        )

    output_path = Path(args.output).expanduser().resolve()
    save_image(cleaned, output_path)
    if args.webp_output:
        save_image(
            cleaned,
            Path(args.webp_output).expanduser().resolve(),
        )

    result = {
        "ok": True,
        "input": str(input_path),
        "output": str(output_path),
        "chroma_key": args.chroma_key.upper(),
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
