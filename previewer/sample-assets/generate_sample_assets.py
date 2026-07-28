#!/usr/bin/env python3
"""Generate the public Previewer fixture atlas and native GIF loops."""

from __future__ import annotations

import argparse
import io
import math
import struct
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw


FRAME_WIDTH = 192
FRAME_HEIGHT = 208
ATLAS_COLUMNS = 8
ATLAS_ROWS = 11
SUPERSAMPLE = 4

STATES = (
    ("idle", 0, (280, 110, 110, 140, 140, 320)),
    ("running-right", 1, (120, 120, 120, 120, 120, 120, 120, 220)),
    ("running-left", 2, (120, 120, 120, 120, 120, 120, 120, 220)),
    ("waving", 3, (140, 140, 140, 280)),
    ("jumping", 4, (140, 140, 140, 140, 280)),
    ("failed", 5, (140, 140, 140, 140, 140, 140, 140, 240)),
    ("waiting", 6, (150, 150, 150, 150, 150, 260)),
    ("running", 7, (120, 120, 120, 120, 120, 220)),
    ("review", 8, (150, 150, 150, 150, 150, 280)),
)

DIRECTIONS = (
    (0, 9, 0),
    (22.5, 9, 1),
    (45, 9, 2),
    (67.5, 9, 3),
    (90, 9, 4),
    (112.5, 9, 5),
    (135, 9, 6),
    (157.5, 9, 7),
    (180, 10, 0),
    (202.5, 10, 1),
    (225, 10, 2),
    (247.5, 10, 3),
    (270, 10, 4),
    (292.5, 10, 5),
    (315, 10, 6),
    (337.5, 10, 7),
)


def cubic(
    start: tuple[float, float],
    control_a: tuple[float, float],
    control_b: tuple[float, float],
    end: tuple[float, float],
    steps: int = 24,
) -> list[tuple[float, float]]:
    points = []
    for index in range(1, steps + 1):
        t = index / steps
        inverse = 1 - t
        points.append(
            (
                inverse**3 * start[0]
                + 3 * inverse**2 * t * control_a[0]
                + 3 * inverse * t**2 * control_b[0]
                + t**3 * end[0],
                inverse**3 * start[1]
                + 3 * inverse**2 * t * control_a[1]
                + 3 * inverse * t**2 * control_b[1]
                + t**3 * end[1],
            )
        )
    return points


def quadratic(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    steps: int = 20,
) -> list[tuple[float, float]]:
    points = []
    for index in range(1, steps + 1):
        t = index / steps
        inverse = 1 - t
        points.append(
            (
                inverse**2 * start[0]
                + 2 * inverse * t * control[0]
                + t**2 * end[0],
                inverse**2 * start[1]
                + 2 * inverse * t * control[1]
                + t**2 * end[1],
            )
        )
    return points


def body_path(variant: int) -> list[tuple[float, float]]:
    if variant >= 2:
        start = (-52.0, 42.0)
        points = [start]
        end = (-30.0, -53.0)
        points.extend(cubic(start, (-60, 17), (-54, -35), end))
        start = end
        end = (46.0, -38.0)
        points.extend(cubic(start, (-10, -68), (30, -62), end))
        start = end
        end = (50.0, 43.0)
        points.extend(cubic(start, (62, -14), (58, 24), end))
        points.extend(quadratic(end, (0, 56), (-52, 42)))
        return points

    start = (-52.0, 43.0)
    points = [start, (-47.0, -23.0)]
    end = (-8.0, -60.0)
    points.extend(quadratic(points[-1], (-43, -55), end))
    points.extend(((42.0, -38.0), (53.0, 42.0)))
    points.extend(quadratic(points[-1], (0, 53), (-52, 43)))
    return points


def motion_values(
    state_id: str,
    phase: float,
    direction: float | None,
) -> tuple[float, float, float, float, float, float]:
    wave = math.sin(phase * math.pi * 2)
    offset_x = 0.0
    offset_y = 0.0
    scale_x = 1.0
    scale_y = 1.0
    eye_shift_x = 0.0
    eye_shift_y = 0.0

    if state_id == "idle":
        scale_y += wave * 0.018
        offset_y -= wave * 1.6
    elif state_id == "running-right":
        offset_x = (phase - 0.5) * 24
        scale_x = 1 + math.sin(phase * math.pi) * 0.05
    elif state_id == "running-left":
        offset_x = (0.5 - phase) * 24
        scale_x = 1 + math.sin(phase * math.pi) * 0.05
    elif state_id == "waving":
        offset_x = math.sin(phase * math.pi) * 8
        offset_y = -math.sin(phase * math.pi) * 6
    elif state_id == "jumping":
        offset_y = -math.sin(phase * math.pi) * 34
        scale_y = 1 - math.sin(phase * math.pi * 2) * 0.035
    elif state_id == "failed":
        offset_y = math.sin(phase * math.pi) * 11
        scale_y = 1 - math.sin(phase * math.pi) * 0.1
    elif state_id == "waiting":
        offset_x = math.sin(phase * math.pi) * 10
        eye_shift_x = 2
    elif state_id == "running":
        eye_shift_x = math.cos(phase * math.pi * 2) * 5
        eye_shift_y = math.sin(phase * math.pi * 2) * 4
    elif state_id == "review":
        offset_x = math.sin(phase * math.pi) * 11
        scale_x = 1 + math.sin(phase * math.pi) * 0.04

    if direction is not None:
        radians = direction * math.pi / 180
        eye_shift_x = math.sin(radians) * 7
        eye_shift_y = -math.cos(radians) * 6
        offset_x = math.sin(radians) * 2
        offset_y = -math.cos(radians) * 1.5

    return (
        offset_x,
        offset_y,
        scale_x,
        scale_y,
        eye_shift_x,
        eye_shift_y,
    )


def render_frame(
    *,
    state_id: str,
    durations: tuple[int, ...],
    column: int,
    variant: int,
    direction: float | None = None,
) -> Image.Image:
    width = FRAME_WIDTH * SUPERSAMPLE
    height = FRAME_HEIGHT * SUPERSAMPLE
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    duration_count = max(2, len(durations))
    phase = min(column, duration_count - 1) / (duration_count - 1)
    (
        offset_x,
        offset_y,
        scale_x,
        scale_y,
        eye_shift_x,
        eye_shift_y,
    ) = motion_values(state_id, phase, direction)

    center_x = FRAME_WIDTH / 2 + offset_x
    center_y = FRAME_HEIGHT / 2 + 12 + offset_y

    def transform(point: tuple[float, float]) -> tuple[float, float]:
        return (
            (center_x + point[0] * scale_x) * SUPERSAMPLE,
            (center_y + point[1] * scale_y) * SUPERSAMPLE,
        )

    draw.polygon([transform(point) for point in body_path(variant)], fill="#111111")

    blink = state_id == "idle" and column == min(3, len(durations) - 1)
    if blink:
        for x in (-21, 8):
            left, top = transform((x + eye_shift_x, -23 + eye_shift_y))
            right, bottom = transform(
                (x + 13 + eye_shift_x, -21 + eye_shift_y)
            )
            draw.rectangle((left, top, right, bottom), fill="#ffffff")
    else:
        for x in (-15, 15):
            center = transform((x + eye_shift_x, -22 + eye_shift_y))
            radius_x = 5 * scale_x * SUPERSAMPLE
            radius_y = 8 * scale_y * SUPERSAMPLE
            draw.ellipse(
                (
                    center[0] - radius_x,
                    center[1] - radius_y,
                    center[0] + radius_x,
                    center[1] + radius_y,
                ),
                fill="#ffffff",
            )

    bar_left, bar_top = transform((-13, 20))
    bar_right, bar_bottom = transform((13, 23))
    draw.rectangle(
        (bar_left, bar_top, bar_right, bar_bottom),
        fill="#8a8a8a",
    )
    return image.resize(
        (FRAME_WIDTH, FRAME_HEIGHT),
        Image.Resampling.LANCZOS,
    )


def to_gif_frames(frames: Iterable[Image.Image]) -> list[Image.Image]:
    rgba_frames = list(frames)
    palette_source = rgba_frames[0].convert("RGB").quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    output = []
    for rgba in rgba_frames:
        indexed = rgba.convert("RGB").quantize(
            palette=palette_source,
            dither=Image.Dither.NONE,
        )
        palette = indexed.getpalette() or []
        palette.extend([0] * (768 - len(palette)))
        pixels = bytearray(indexed.tobytes())
        for offset, alpha in enumerate(rgba.getchannel("A").tobytes()):
            if alpha < 128:
                pixels[offset] = 255
        transparent = Image.frombytes("P", indexed.size, bytes(pixels))
        transparent.putpalette(palette[:768])
        transparent.info["transparency"] = 255
        output.append(transparent)
    return output


def single_gif_parts(frame: Image.Image) -> tuple[bytes, bytes]:
    buffer = io.BytesIO()
    frame.save(
        buffer,
        format="GIF",
        transparency=255,
        disposal=2,
        optimize=False,
    )
    data = buffer.getvalue()
    cursor = 13
    packed = data[10]
    if packed & 0x80:
        cursor += 3 * (2 ** ((packed & 0x07) + 1))
    header = data[:cursor]

    while cursor < len(data):
        marker = data[cursor]
        if marker == 0x21:
            cursor += 2
            while True:
                block_size = data[cursor]
                cursor += 1
                if block_size == 0:
                    break
                cursor += block_size
            continue
        if marker == 0x2C:
            image_start = cursor
            cursor += 10
            descriptor_packed = data[cursor - 1]
            if descriptor_packed & 0x80:
                cursor += 3 * (2 ** ((descriptor_packed & 0x07) + 1))
            cursor += 1
            while True:
                block_size = data[cursor]
                cursor += 1
                if block_size == 0:
                    return header, data[image_start:cursor]
                cursor += block_size
        if marker == 0x3B:
            break
        raise RuntimeError(f"Unexpected GIF marker 0x{marker:02x}")
    raise RuntimeError("Single-frame GIF did not contain an image block")


def save_gif(
    path: Path,
    frames: list[Image.Image],
    durations: tuple[int, ...],
) -> None:
    encoded = [single_gif_parts(frame) for frame in frames]
    header = encoded[0][0]
    if any(frame_header != header for frame_header, _ in encoded[1:]):
        raise RuntimeError("Fixture frames did not retain one shared GIF palette")

    output = bytearray(header)
    output.extend(b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00")
    for duration, (_, image_block) in zip(durations, encoded, strict=True):
        delay = duration // 10
        output.extend(b"\x21\xf9\x04\x09")
        output.extend(struct.pack("<H", delay))
        output.extend(b"\xff\x00")
        output.extend(image_block)
    output.append(0x3B)
    path.write_bytes(output)


def generate_version(output_root: Path, version_id: str, variant: int) -> None:
    version_root = output_root / version_id
    gif_root = version_root / "gifs"
    gif_root.mkdir(parents=True, exist_ok=True)
    atlas = Image.new(
        "RGBA",
        (FRAME_WIDTH * ATLAS_COLUMNS, FRAME_HEIGHT * ATLAS_ROWS),
        (0, 0, 0, 0),
    )
    idle_durations = STATES[0][2]

    for state_id, row, durations in STATES:
        frames = []
        for column in range(ATLAS_COLUMNS):
            frame = render_frame(
                state_id=state_id,
                durations=durations,
                column=column,
                variant=variant,
            )
            atlas.alpha_composite(
                frame,
                (column * FRAME_WIDTH, row * FRAME_HEIGHT),
            )
            if column < len(durations):
                frames.append(frame)

        gif_frames = to_gif_frames(frames)
        save_gif(
            gif_root / f"{state_id}.gif",
            gif_frames,
            durations,
        )

    for degree, row, column in DIRECTIONS:
        frame = render_frame(
            state_id="idle",
            durations=idle_durations,
            column=column,
            variant=variant,
            direction=degree,
        )
        atlas.alpha_composite(
            frame,
            (column * FRAME_WIDTH, row * FRAME_HEIGHT),
        )

    atlas.save(
        version_root / "spritesheet.png",
        format="PNG",
        optimize=True,
        compress_level=9,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    args = parser.parse_args()
    generate_version(args.output_root, "v001", 1)
    generate_version(args.output_root, "v002", 2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
