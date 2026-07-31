#!/usr/bin/env python3
"""Stage-agnostic raster transparency primitives for Creatures assets.

Portions are derived from the project-bundled Hatch Pet edge-cleanup
implementation. Modified for Codex Pet Studio on 2026-07-31 to separate
background removal from alpha-edge cleanup and make both stages reusable
throughout the Creatures workflow. See the skill's LICENSE.txt and NOTICE.txt.
"""

from __future__ import annotations

import math
import re
from typing import Any

from PIL import Image, ImageFilter


CHROMA_KEY_ALGORITHM = "rgb-distance-chroma-key"
EDGE_CLEANUP_ALGORITHM = "edge-local-chroma-spill-suppression"
ALPHA_SMOOTHING_ALGORITHM = "cell-isolated-gaussian-alpha-smoothing"
CHROMA_CLEANUP_ALGORITHM = (
    "alpha-smoothing-and-edge-local-chroma-spill-suppression"
)
AUTO_BORDER_ALGORITHM = "robust-polynomial-auto-border-matte"
AUTO_BORDER_CLEANUP_ALGORITHM = "background-unmix-alpha-cleanup"
DEFAULT_ATLAS_CELL_SIZE = (192, 208)


class TransparencyError(ValueError):
    """Raised when an image cannot be prepared without unsafe guessing."""


def flattened_data(image: Image.Image) -> Any:
    getter = getattr(image, "get_flattened_data", None)
    return getter() if getter is not None else image.getdata()


def parse_hex_color(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise TransparencyError(
            f"invalid chroma key color: {value}; expected #RRGGBB"
        )
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def color_distance(
    red: int,
    green: int,
    blue: int,
    key: tuple[int, int, int],
) -> float:
    return math.sqrt(
        (red - key[0]) ** 2
        + (green - key[1]) ** 2
        + (blue - key[2]) ** 2
    )


def alpha_summary(image: Image.Image) -> dict[str, int | float | list[int]]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    histogram = alpha.histogram()
    total = rgba.width * rgba.height
    transparent = histogram[0]
    opaque = histogram[255]
    visible = total - transparent
    translucent = total - transparent - opaque
    bbox = alpha.getbbox()
    return {
        "pixels": total,
        "transparent_pixels": transparent,
        "translucent_pixels": translucent,
        "opaque_pixels": opaque,
        "visible_pixels": visible,
        "transparent_fraction": transparent / total if total else 0,
        "translucent_fraction": translucent / total if total else 0,
        "opaque_fraction": opaque / total if total else 0,
        "visible_bbox": list(bbox) if bbox else [],
    }


def require_meaningful_transparency(
    image: Image.Image,
    *,
    label: str = "asset",
) -> dict[str, int | float | list[int]]:
    summary = alpha_summary(image)
    if summary["visible_pixels"] == 0:
        raise TransparencyError(f"{label} is fully transparent")
    if summary["transparent_pixels"] == 0:
        raise TransparencyError(f"{label} is fully opaque")
    return summary


def has_meaningful_transparency(image: Image.Image) -> bool:
    try:
        require_meaningful_transparency(image)
    except TransparencyError:
        return False
    return True


def clear_hidden_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    source = list(flattened_data(rgba))
    output = Image.new("RGBA", rgba.size)
    output.putdata(
        [
            (0, 0, 0, 0) if pixel[3] == 0 else pixel
            for pixel in source
        ]
    )
    return output


def require_exact_cell_grid(
    size: tuple[int, int],
    cell_size: tuple[int, int] | None,
) -> tuple[int, int] | None:
    if cell_size is None:
        return None
    width, height = size
    cell_width, cell_height = cell_size
    if (
        cell_width < 1
        or cell_height < 1
        or width % cell_width
        or height % cell_height
    ):
        raise TransparencyError(
            "cell isolation requires dimensions that exactly divide the canvas"
        )
    return cell_size


def smooth_alpha_matte(
    image: Image.Image,
    *,
    radius: float = 0.65,
    alpha_floor: int = 2,
    cell_size: tuple[int, int] | None = None,
) -> tuple[Image.Image, dict[str, Any]]:
    """Smooth alpha once without allowing neighboring atlas cells to mix."""
    if radius < 0:
        raise TransparencyError("alpha smoothing radius must not be negative")
    if not 0 <= alpha_floor <= 255:
        raise TransparencyError("alpha floor must be between 0 and 255")

    rgba = image.convert("RGBA")
    width, height = rgba.size
    source_alpha = rgba.getchannel("A")
    exact_cell_size = require_exact_cell_grid(rgba.size, cell_size)
    if exact_cell_size is not None:
        cell_width, cell_height = exact_cell_size
    else:
        cell_width, cell_height = width, height

    if radius:
        smoothed_alpha = Image.new("L", rgba.size)
        for top in range(0, height, cell_height):
            for left in range(0, width, cell_width):
                cell = source_alpha.crop(
                    (
                        left,
                        top,
                        left + cell_width,
                        top + cell_height,
                    )
                )
                smoothed_alpha.paste(
                    cell.filter(ImageFilter.GaussianBlur(radius)),
                    (left, top),
                )
    else:
        smoothed_alpha = source_alpha.copy()

    source_alpha_values = list(flattened_data(source_alpha))
    alpha_values = [
        0 if value < alpha_floor else value
        for value in flattened_data(smoothed_alpha)
    ]
    output_pixels = []
    for pixel, alpha in zip(flattened_data(rgba), alpha_values):
        output_pixels.append(
            (0, 0, 0, 0)
            if alpha == 0
            else (pixel[0], pixel[1], pixel[2], alpha)
        )
    output = Image.new("RGBA", rgba.size)
    output.putdata(output_pixels)
    changed_alpha_pixels = sum(
        before != after
        for before, after in zip(source_alpha_values, alpha_values)
    )
    return output, {
        "algorithm": ALPHA_SMOOTHING_ALGORITHM,
        "radius": radius,
        "alpha_floor": alpha_floor,
        "cell_size": list(cell_size) if cell_size else None,
        "changed_alpha_pixels": changed_alpha_pixels,
        "alpha_smoothed": bool(radius and changed_alpha_pixels),
    }


def remove_chroma_background(
    image: Image.Image,
    chroma_key: tuple[int, int, int],
    threshold: float,
) -> Image.Image:
    """Remove a known flat key without changing non-key pixels or their alpha."""
    if threshold < 0:
        raise TransparencyError("chroma threshold must not be negative")
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, _alpha = pixels[x, y]
            if color_distance(red, green, blue, chroma_key) <= threshold:
                pixels[x, y] = (0, 0, 0, 0)
    return rgba


def separate_chroma_background(
    image: Image.Image,
    *,
    chroma_key: tuple[int, int, int],
    threshold: float,
) -> tuple[Image.Image, dict[str, Any]]:
    output = remove_chroma_background(image, chroma_key, threshold)
    return output, {
        "algorithm": CHROMA_KEY_ALGORITHM,
        "chroma_key": list(chroma_key),
        "threshold": threshold,
        **alpha_summary(output),
    }


def srgb_to_linear(value: float) -> float:
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def linear_to_srgb(value: float) -> float:
    if value <= 0.0031308:
        return value * 12.92
    return 1.055 * value ** (1 / 2.4) - 0.055


def edge_band(alpha: Image.Image, radius: int) -> list[bool]:
    visible = [value > 0 for value in flattened_data(alpha)]
    transparent = Image.new("L", alpha.size)
    transparent.putdata([0 if value else 255 for value in visible])
    expanded = transparent.filter(ImageFilter.MaxFilter(radius * 2 + 1))
    return [
        is_visible and nearby > 0
        for is_visible, nearby in zip(visible, flattened_data(expanded))
    ]


def cell_edge_band(
    alpha: Image.Image,
    radius: int,
    cell_size: tuple[int, int] | None,
) -> list[bool]:
    width, height = alpha.size
    boundary = edge_band(alpha, radius)
    exact_cell_size = require_exact_cell_grid(alpha.size, cell_size)
    if exact_cell_size is None:
        return boundary
    cell_width, cell_height = exact_cell_size

    for top in range(0, height, cell_height):
        for left in range(0, width, cell_width):
            cell = alpha.crop(
                (left, top, left + cell_width, top + cell_height)
            )
            for index, is_boundary in enumerate(edge_band(cell, radius)):
                if is_boundary:
                    x = left + index % cell_width
                    y = top + index // cell_width
                    boundary[y * width + x] = True
    return boundary


def chroma_similarity(
    color: tuple[float, float, float],
    key: tuple[float, float, float],
) -> float:
    color_mean = sum(color) / 3
    key_mean = sum(key) / 3
    color_chroma = tuple(channel - color_mean for channel in color)
    key_chroma = tuple(channel - key_mean for channel in key)
    denominator = sum(channel * channel for channel in color_chroma) * sum(
        channel * channel for channel in key_chroma
    )
    if denominator <= 1e-12:
        return -1
    return (
        sum(
            color_channel * key_channel
            for color_channel, key_channel in zip(color_chroma, key_chroma)
        )
        / denominator**0.5
    )


def chroma_saturation(color: tuple[float, float, float]) -> float:
    maximum = max(color)
    if maximum <= 0:
        return 0
    return (maximum - min(color)) / maximum


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
    cell_size: tuple[int, int] | None,
) -> tuple[list[tuple[int, int, int, int]], list[bool]]:
    width, height = size
    colors_linear = [
        tuple(srgb_to_linear(channel / 255) for channel in pixel[:3])
        for pixel in pixels
    ]
    similarity_threshold = 1 - min(spill_tolerance, 1)
    pending = [
        pixel[3] > 0
        and is_boundary
        and (
            pixel[3] < 250
            or (
                chroma_saturation(color) >= minimum_saturation
                and chroma_similarity(color, key_linear) >= similarity_threshold
            )
        )
        for pixel, color, is_boundary in zip(
            pixels,
            colors_linear,
            boundary,
        )
    ]
    filled = [
        pixel[3] > 0 and not is_pending
        for pixel, is_pending in zip(pixels, pending)
    ]
    output = pixels.copy()
    suppressed = [False] * len(pixels)
    exact_cell_size = require_exact_cell_grid(size, cell_size)
    if exact_cell_size is not None:
        cell_width, cell_height = exact_cell_size
    else:
        cell_width, cell_height = width, height

    for _ in range(edge_radius * 2 + 1):
        updates: list[tuple[int, tuple[float, float, float]]] = []
        for index, is_pending in enumerate(pending):
            if not is_pending:
                continue
            x = index % width
            y = index // width
            cell_left = x // cell_width * cell_width
            cell_top = y // cell_height * cell_height
            references = []
            for neighbor_y in range(
                max(cell_top, y - 1),
                min(cell_top + cell_height, y + 2),
            ):
                for neighbor_x in range(
                    max(cell_left, x - 1),
                    min(cell_left + cell_width, x + 2),
                ):
                    neighbor = neighbor_y * width + neighbor_x
                    if neighbor != index and filled[neighbor]:
                        references.append(colors_linear[neighbor])
            if not references:
                continue

            reference = tuple(
                sum(color[channel] for color in references) / len(references)
                for channel in range(3)
            )
            observed = colors_linear[index]
            cleaned = tuple(
                channel + (reference_channel - channel) * strength
                for channel, reference_channel in zip(observed, reference)
            )
            updates.append((index, cleaned))

        if not updates:
            break
        for index, cleaned in updates:
            colors_linear[index] = cleaned
            filled[index] = True
            pending[index] = False
            output[index] = (
                *(
                    round(
                        linear_to_srgb(min(1, max(0, channel))) * 255
                    )
                    for channel in cleaned
                ),
                pixels[index][3],
            )
            suppressed[index] = output[index] != pixels[index]

    for index, is_pending in enumerate(pending):
        if not is_pending:
            continue
        observed = colors_linear[index]
        luminance = sum(observed) / 3
        cleaned = tuple(
            channel + (luminance - channel) * strength
            for channel in observed
        )
        output[index] = (
            *(
                round(linear_to_srgb(min(1, max(0, channel))) * 255)
                for channel in cleaned
            ),
            pixels[index][3],
        )
        suppressed[index] = output[index] != pixels[index]

    return output, suppressed


def decontaminate_image(
    image: Image.Image,
    *,
    chroma_key: tuple[int, int, int],
    strength: float = 1,
    edge_radius: int = 5,
    spill_tolerance: float = 0.15,
    minimum_saturation: float = 0.1,
    cell_size: tuple[int, int] | None = None,
) -> tuple[Image.Image, dict[str, Any]]:
    if not 0 <= strength <= 1:
        raise TransparencyError("strength must be between 0 and 1")
    if edge_radius < 1:
        raise TransparencyError("edge_radius must be at least 1")
    if spill_tolerance < 0:
        raise TransparencyError("spill_tolerance must not be negative")
    if minimum_saturation < 0:
        raise TransparencyError("minimum_saturation must not be negative")

    rgba = image.convert("RGBA")
    width, _ = rgba.size
    source = list(flattened_data(rgba))
    boundary = cell_edge_band(
        rgba.getchannel("A"),
        edge_radius,
        cell_size,
    )
    key_linear = tuple(
        srgb_to_linear(channel / 255) for channel in chroma_key
    )
    output_pixels, suppressed = suppress_boundary_spill(
        source,
        size=rgba.size,
        boundary=boundary,
        key_linear=key_linear,
        strength=strength,
        edge_radius=edge_radius,
        spill_tolerance=spill_tolerance,
        minimum_saturation=minimum_saturation,
        cell_size=cell_size,
    )
    output_pixels = [
        (0, 0, 0, 0) if pixel[3] == 0 else output_pixel
        for pixel, output_pixel in zip(source, output_pixels)
    ]
    decontaminated_pixels = sum(
        is_suppressed and pixel[3] < 255
        for pixel, is_suppressed in zip(source, suppressed)
    )
    spill_suppressed_pixels = sum(suppressed)

    changed_by_cell: dict[str, int] = {}
    report_cell_size = cell_size or rgba.size
    for index, (source_pixel, output_pixel) in enumerate(
        zip(source, output_pixels)
    ):
        if output_pixel != source_pixel:
            x = index % width
            y = index // width
            cell = (
                f"r{y // report_cell_size[1]}"
                f"c{x // report_cell_size[0]}"
            )
            changed_by_cell[cell] = changed_by_cell.get(cell, 0) + 1

    output = Image.new("RGBA", rgba.size)
    output.putdata(output_pixels)
    return output, {
        "algorithm": EDGE_CLEANUP_ALGORITHM,
        "strength": strength,
        "edge_radius": edge_radius,
        "spill_tolerance": spill_tolerance,
        "minimum_saturation": minimum_saturation,
        "cell_size": list(cell_size) if cell_size else None,
        "changed_pixels": sum(changed_by_cell.values()),
        "decontaminated_pixels": decontaminated_pixels,
        "spill_suppressed_pixels": spill_suppressed_pixels,
        "rejected_pixels": 0,
        "changed_by_cell": dict(
            sorted(
                changed_by_cell.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ),
        "alpha_preserved": True,
    }


def clean_chroma_edges(
    image: Image.Image,
    *,
    chroma_key: tuple[int, int, int],
    strength: float = 1,
    edge_radius: int = 5,
    spill_tolerance: float = 0.15,
    minimum_saturation: float = 0.1,
    cell_size: tuple[int, int] | None = None,
    alpha_blur_radius: float = 0.65,
    alpha_floor: int = 2,
) -> tuple[Image.Image, dict[str, Any]]:
    """Smooth the separated matte, then clean its contaminated edge RGB."""
    smoothed, smoothing_report = smooth_alpha_matte(
        image,
        radius=alpha_blur_radius,
        alpha_floor=alpha_floor,
        cell_size=cell_size,
    )
    cleaned, contamination_report = decontaminate_image(
        smoothed,
        chroma_key=chroma_key,
        strength=strength,
        edge_radius=edge_radius,
        spill_tolerance=spill_tolerance,
        minimum_saturation=minimum_saturation,
        cell_size=cell_size,
    )
    return cleaned, {
        "algorithm": CHROMA_CLEANUP_ALGORITHM,
        "alpha_smoothing": smoothing_report,
        "contamination_cleanup": contamination_report,
        "alpha_preserved": not smoothing_report["changed_alpha_pixels"],
        "hidden_rgb_cleared": True,
        "changed_alpha_pixels": smoothing_report[
            "changed_alpha_pixels"
        ],
        "changed_pixels": contamination_report["changed_pixels"],
        "decontaminated_pixels": contamination_report[
            "decontaminated_pixels"
        ],
        "spill_suppressed_pixels": contamination_report[
            "spill_suppressed_pixels"
        ],
        "changed_by_cell": contamination_report["changed_by_cell"],
        **alpha_summary(cleaned),
    }


def _numpy() -> Any:
    try:
        import numpy
    except ImportError as exc:
        raise TransparencyError(
            "auto-border separation requires NumPy in the workspace runtime"
        ) from exc
    return numpy


def _polynomial_design(
    np: Any,
    x_normalized: Any,
    y_normalized: Any,
    degree: int,
) -> Any:
    return np.stack(
        [
            x_normalized**x_degree
            * y_normalized ** (total_degree - x_degree)
            for total_degree in range(degree + 1)
            for x_degree in range(total_degree + 1)
        ],
        axis=-1,
    ).astype(np.float32, copy=False)


def _evaluate_background(
    np: Any,
    coefficients: Any,
    *,
    width: int,
    height: int,
    degree: int,
    tile_rows: int = 128,
) -> Any:
    background = np.empty((height, width, 3), dtype=np.float32)
    x = np.arange(width, dtype=np.float32)
    x_normalized = x / max(1, width - 1) * 2 - 1
    for top in range(0, height, tile_rows):
        bottom = min(height, top + tile_rows)
        y = np.arange(top, bottom, dtype=np.float32)[:, None]
        y_normalized = y / max(1, height - 1) * 2 - 1
        tile_x = np.broadcast_to(
            x_normalized[None, :],
            (bottom - top, width),
        )
        tile_y = np.broadcast_to(
            y_normalized,
            (bottom - top, width),
        )
        design = _polynomial_design(
            np,
            tile_x,
            tile_y,
            degree,
        )
        background[top:bottom] = design @ coefficients
    return background


def fit_auto_border_background(
    image: Image.Image,
    *,
    border_fraction: float = 0.17,
    polynomial_degree: int = 4,
    minimum_channel: float = 205,
    maximum_chroma: float = 45,
    robust_iterations: int = 4,
    sample_stride: int = 3,
) -> tuple[Any, dict[str, Any]]:
    """Fit a smooth illumination field from predictable bright border pixels."""
    np = _numpy()
    if not 0.05 <= border_fraction <= 0.45:
        raise TransparencyError(
            "border_fraction must be between 0.05 and 0.45"
        )
    if not 1 <= polynomial_degree <= 4:
        raise TransparencyError("polynomial_degree must be between 1 and 4")
    if robust_iterations < 1:
        raise TransparencyError("robust_iterations must be at least 1")
    if sample_stride < 1:
        raise TransparencyError("sample_stride must be at least 1")

    source = np.asarray(image.convert("RGB"), dtype=np.float32)
    height, width, _ = source.shape
    if width < 32 or height < 32:
        raise TransparencyError(
            "auto-border separation requires an image at least 32x32"
        )
    y, x = np.mgrid[0:height, 0:width]
    outer = (
        (x < border_fraction * width)
        | (x > (1 - border_fraction) * width)
        | (y < border_fraction * height)
        | (y > (1 - border_fraction) * height)
    )
    chroma = source.max(axis=2) - source.min(axis=2)
    base = (
        outer
        & (source.min(axis=2) > minimum_channel)
        & (chroma < maximum_chroma)
    )
    base_fraction = float(base.mean())
    if base_fraction < 0.10:
        raise TransparencyError(
            "auto-border could not find enough predictable bright border "
            "background; use a known chroma key or an explicit matte"
        )

    x_normalized = x / max(1, width - 1) * 2 - 1
    y_normalized = y / max(1, height - 1) * 2 - 1
    sample_grid = (x % sample_stride == 0) & (y % sample_stride == 0)
    term_count = (polynomial_degree + 1) * (polynomial_degree + 2) // 2
    mask = base.copy()
    coefficients = None
    residual = None
    rank = 0

    for _ in range(robust_iterations):
        sample = mask & sample_grid
        sample_count = int(sample.sum())
        if sample_count < term_count * 20:
            raise TransparencyError(
                "auto-border background fit has too few inlier samples"
            )
        design = _polynomial_design(
            np,
            x_normalized[sample].astype(np.float32),
            y_normalized[sample].astype(np.float32),
            polynomial_degree,
        )
        channel_coefficients = []
        ranks = []
        for channel in range(3):
            fitted, _residuals, channel_rank, _singular = np.linalg.lstsq(
                design,
                source[sample, channel],
                rcond=None,
            )
            channel_coefficients.append(fitted)
            ranks.append(int(channel_rank))
        rank = min(ranks)
        if rank < term_count:
            raise TransparencyError(
                "auto-border background model is rank deficient"
            )
        coefficients = np.stack(channel_coefficients, axis=-1)
        predicted = _evaluate_background(
            np,
            coefficients,
            width=width,
            height=height,
            degree=polynomial_degree,
        )
        residual = np.sqrt(
            np.sum((source - predicted) ** 2, axis=2)
        )
        values = residual[mask]
        median = float(np.median(values))
        mad = float(1.4826 * np.median(np.abs(values - median)))
        cutoff = min(
            float(np.percentile(values, 75)),
            median + 2.5 * mad,
        )
        if cutoff <= median:
            cutoff = median + 0.25
        mask = base & (residual < cutoff)

    if coefficients is None or residual is None:
        raise TransparencyError("auto-border background fit did not run")
    predicted = _evaluate_background(
        np,
        coefficients,
        width=width,
        height=height,
        degree=polynomial_degree,
    )
    inlier_values = residual[mask]
    residual_p95 = float(np.percentile(inlier_values, 95))
    if not np.isfinite(predicted).all() or residual_p95 > 4:
        raise TransparencyError(
            "auto-border background is not smooth enough to separate safely"
        )
    predicted_min = float(predicted.min())
    predicted_max = float(predicted.max())
    if predicted_min < -32 or predicted_max > 287:
        raise TransparencyError(
            "auto-border background model extrapolates outside a safe range"
        )

    return np.clip(predicted, 0, 255), {
        "algorithm": AUTO_BORDER_ALGORITHM,
        "border_fraction": border_fraction,
        "polynomial_degree": polynomial_degree,
        "minimum_channel": minimum_channel,
        "maximum_chroma": maximum_chroma,
        "robust_iterations": robust_iterations,
        "sample_stride": sample_stride,
        "base_fraction": base_fraction,
        "inlier_fraction": float(mask.mean()),
        "sample_count": int((mask & sample_grid).sum()),
        "model_rank": rank,
        "residual_p95": residual_p95,
        "predicted_range": [predicted_min, predicted_max],
    }


def separate_auto_border_background(
    image: Image.Image,
    *,
    background: Any | None = None,
    model_report: dict[str, Any] | None = None,
    noise_tolerance: float = 2.5,
    alpha_power: float = 1.65,
    **fit_options: Any,
) -> tuple[Image.Image, Any, dict[str, Any]]:
    """Create an unsmoothed matte; RGB cleanup is intentionally separate."""
    np = _numpy()
    if noise_tolerance < 0:
        raise TransparencyError("noise_tolerance must not be negative")
    if alpha_power <= 0:
        raise TransparencyError("alpha_power must be positive")
    source = np.asarray(image.convert("RGB"), dtype=np.float32)
    if background is None:
        background, model_report = fit_auto_border_background(
            image,
            **fit_options,
        )
    darker = (
        np.maximum(background - source - noise_tolerance, 0)
        / np.maximum(background, 32)
    )
    lighter = (
        np.maximum(source - background - noise_tolerance, 0)
        / np.maximum(255 - background, 32)
    )
    minimum_alpha = np.maximum(darker, lighter).max(axis=2)
    alpha = 1 - np.power(
        1 - np.clip(minimum_alpha, 0, 1),
        alpha_power,
    )
    alpha[minimum_alpha < 0.008] = 0
    alpha_bytes = np.uint8(np.clip(alpha * 255 + 0.5, 0, 255))
    rgba = np.dstack(
        [
            np.asarray(image.convert("RGB"), dtype=np.uint8),
            alpha_bytes,
        ]
    )
    separated = Image.fromarray(rgba, "RGBA")
    return separated, background, {
        "algorithm": AUTO_BORDER_ALGORITHM,
        "noise_tolerance": noise_tolerance,
        "alpha_power": alpha_power,
        "background_model": model_report or {},
        **alpha_summary(separated),
    }


def clean_auto_border_edges(
    separated: Image.Image,
    *,
    source: Image.Image,
    background: Any,
    alpha_blur_radius: float = 0.65,
    alpha_floor: int = 2,
) -> tuple[Image.Image, dict[str, Any]]:
    """Smooth the matte, unmix the fitted background, and clear hidden RGB."""
    np = _numpy()
    if alpha_blur_radius < 0:
        raise TransparencyError("alpha_blur_radius must not be negative")
    if not 0 <= alpha_floor <= 255:
        raise TransparencyError("alpha_floor must be between 0 and 255")

    alpha_image = separated.convert("RGBA").getchannel("A")
    if alpha_blur_radius:
        alpha_image = alpha_image.filter(
            ImageFilter.GaussianBlur(alpha_blur_radius)
        )
    alpha_bytes = np.asarray(alpha_image, dtype=np.uint8).copy()
    alpha = alpha_bytes.astype(np.float32) / 255
    alpha[alpha_bytes < alpha_floor] = 0
    alpha_bytes = np.uint8(np.clip(alpha * 255 + 0.5, 0, 255))

    observed = np.asarray(source.convert("RGB"), dtype=np.float32)
    denominator = np.maximum(alpha[..., None], 1 / 255)
    foreground = np.clip(
        (
            observed
            - (1 - alpha[..., None]) * background
        )
        / denominator,
        0,
        255,
    )
    foreground[alpha == 0] = 0
    rgba = np.dstack(
        [
            np.uint8(foreground + 0.5),
            alpha_bytes,
        ]
    )
    cleaned = Image.fromarray(rgba, "RGBA")
    return cleaned, {
        "algorithm": AUTO_BORDER_CLEANUP_ALGORITHM,
        "alpha_blur_radius": alpha_blur_radius,
        "alpha_floor": alpha_floor,
        "alpha_smoothed": bool(alpha_blur_radius),
        "background_unmixed": True,
        "hidden_rgb_cleared": True,
        **alpha_summary(cleaned),
    }


def prepare_transparent_image(
    image: Image.Image,
    *,
    mode: str = "auto",
    chroma_key: tuple[int, int, int] | None = None,
    chroma_threshold: float = 96,
    edge_strength: float = 1,
    edge_radius: int = 5,
    spill_tolerance: float = 0.15,
    minimum_saturation: float = 0.1,
    cell_size: tuple[int, int] | None = None,
    alpha_blur_radius: float = 0.65,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose separation and cleanup while keeping their reports independent."""
    if mode not in {"auto", "auto-border", "chroma", "preserve-alpha"}:
        raise TransparencyError(f"unsupported transparency mode: {mode}")

    source_rgba = image.convert("RGBA")
    alpha_extrema = source_rgba.getchannel("A").getextrema()
    resolved_mode = mode
    if mode == "auto":
        resolved_mode = (
            "preserve-alpha"
            if alpha_extrema[0] < 255
            else "auto-border"
        )

    if resolved_mode == "preserve-alpha":
        require_meaningful_transparency(source_rgba, label="source asset")
        cleaned = clear_hidden_rgb(source_rgba)
        report = {
            "mode": resolved_mode,
            "separation": {
                "algorithm": "preserve-existing-alpha",
                **alpha_summary(source_rgba),
            },
            "cleanup": {
                "algorithm": "clear-hidden-rgb",
                "alpha_preserved": True,
                "hidden_rgb_cleared": True,
            },
        }
    elif resolved_mode == "chroma":
        if chroma_key is None:
            raise TransparencyError("chroma mode requires a chroma key")
        separated, separation_report = separate_chroma_background(
            image,
            chroma_key=chroma_key,
            threshold=chroma_threshold,
        )
        cleaned, cleanup_report = clean_chroma_edges(
            separated,
            chroma_key=chroma_key,
            strength=edge_strength,
            edge_radius=edge_radius,
            spill_tolerance=spill_tolerance,
            minimum_saturation=minimum_saturation,
            cell_size=cell_size,
            alpha_blur_radius=alpha_blur_radius,
        )
        report = {
            "mode": resolved_mode,
            "separation": separation_report,
            "cleanup": cleanup_report,
        }
    else:
        separated, background, separation_report = (
            separate_auto_border_background(image)
        )
        cleaned, cleanup_report = clean_auto_border_edges(
            separated,
            source=image,
            background=background,
            alpha_blur_radius=alpha_blur_radius,
        )
        report = {
            "mode": resolved_mode,
            "separation": separation_report,
            "cleanup": cleanup_report,
        }

    final_summary = require_meaningful_transparency(
        cleaned,
        label="prepared asset",
    )
    return cleaned, {
        "ok": True,
        **report,
        "output": final_summary,
    }
