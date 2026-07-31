# Transparency contract

## Output invariant

A Previewer render derivative is an 8-bit RGBA PNG with:

- at least one visible pixel;
- at least one pixel below alpha 255;
- RGB zero wherever alpha is zero;
- the same canvas dimensions as its preserved source for Static review;
- no background-color fringe that changes the intended silhouette or palette.

Runtime atlases and Takes additionally obey their selected Delivery Target
geometry. Target geometry does not belong to this skill.

## Auto-border model

`auto-border` samples the outer 17 percent of the canvas, keeps bright
low-chroma candidates, and robustly fits a fourth-degree two-dimensional
polynomial illumination field per RGB channel. Four trimming rounds reject
foreground or shadow contamination. The operation stops rather than guessing
when there are too few samples, the fit is rank deficient, the residual is too
large, or the model extrapolates outside a safe range.

For observed color `C`, fitted background `B`, and foreground `F`, compositing
uses:

```text
C = alpha * F + (1 - alpha) * B
```

The separator computes the minimum physically valid alpha that keeps recovered
foreground channels in range, then applies a conservative alpha power. Cleanup
smooths only that matte, solves the equation for foreground RGB, and clears
fully transparent RGB.

This is a deterministic matte for smooth generated backgrounds, not semantic
segmentation. A single opaque RGB image cannot reveal ground-truth alpha for
glass or other refractive material.

## Chroma mode

Chroma separation uses inclusive Euclidean RGB distance:

```text
distance(pixel, key) <= threshold
```

Matching pixels become `(0, 0, 0, 0)`; all other source pixels retain their
RGBA values. Cleanup applies one small Gaussian alpha-smoothing pass, then
works only in the transparency boundary band and recovers interior color in
linear light. Both alpha smoothing and RGB recovery isolate atlas cells when
`cell_size` is supplied, so neighboring poses cannot bleed into each other.
An inexact cell grid is rejected rather than silently falling back to whole-
image processing.
Set `--alpha-blur-radius 0` only when an already-authoritative matte must remain
bit-exact.

## Report contract

The composed command reports:

- `mode`;
- `separation.algorithm` plus fit/key parameters and alpha counts;
- `cleanup.algorithm` plus separate `alpha_smoothing` and
  `contamination_cleanup` facts for chroma assets;
- `output` alpha counts and visible bounding box;
- input and output paths.

The report is processing evidence, not creative approval.
