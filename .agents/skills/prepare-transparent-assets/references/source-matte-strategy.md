# Source matte strategy

Use this strategy before generating or editing any Creature image that may
become a Static, Take, Keyframe, row, repair, or packaged runtime asset.
Reference-only mood boards and layout guides are outside this contract.

## Record the route

Before generation, record these facts in the visual brief:

- `material_profile`: `existing-alpha`, `opaque`, `soft-edge`,
  `translucent`, `refractive`, or `mixed`;
- `edge_palette`: the important colors and highlights at the real silhouette;
- `source_route`: `true-alpha`, `near-white-matte`, `contrast-key`, or a
  Delivery Target override;
- `matte_color`: the requested or known flat background color;
- `detected_matte`: border/corner candidate, confidence, and evidence when an
  opaque source already has a saturated matte;
- `separation_mode`: `preserve-alpha`, `auto-border`, or `chroma`;
- `limitation`: `none` or the exact material uncertainty that requires review.

Classify by the most extraction-sensitive visible boundary, not by the
dominant interior color. Material sensitivity outranks the convenience of one
preferred background color.

For an opaque reference that may already carry a deliberate saturated matte,
inspect all four border bands and corners before choosing a new key. Reuse a
high-confidence, spatially consistent candidate. Require an explicit key for a
medium-confidence candidate. If references, request text, style notes, and an
explicit key disagree, stop before generation or run-folder writes; do not
silently choose a second color. This detector is only a source-contract guard:
bright low-chroma borders continue through the material-aware `auto-border`
route, and none of the alpha, despill, blur, or chroma thresholds change.

## Choose by color and material

| Subject | Preferred source route | Matte rule |
| --- | --- | --- |
| Existing meaningful alpha | `true-alpha` | Preserve it. Never composite onto a matte merely to remove that matte again. |
| Opaque with dark, midtone, or saturated edges | `near-white-matte` | Default to one neutral near-white field around `#F4F4F1` when it naturally separates the contour. Record the actual border rather than assuming the requested value was reproduced exactly. |
| Opaque with white, pale-gray, silver, or highlight-heavy edges | `contrast-key` | Choose one flat, recorded color that is absent from the subject and clearly separated from the real contour. Do not recolor the subject or add an outline to manufacture contrast. |
| Fur, hair, feathers, fibers, or another soft edge | `true-alpha` when reliable; otherwise the safest recorded matte | Prefer a low-contamination matte whose luminance or hue separates the actual fine edge. Treat a single opaque composite as an approximation and inspect it on dark backgrounds. |
| Glass, translucent membranes, smoke, glow, or refractive material | `true-alpha` when reliable; otherwise `near-white-matte` for review-quality approximation | Prefer a uniform low-chroma near-white matte over saturated spill. Preserve conservative alpha and state that one opaque composite cannot reveal ground-truth transparency. |
| Mixed materials | Route for the most sensitive edge | Do not let an easy opaque region justify a matte that contaminates the translucent or fine-edge region. |
| Delivery Target with a required key | Delivery Target override | Use its recorded key and deterministic extraction path. Keep the shared purity, padding, no-shadow, and QA rules; do not replace the target key with near-white. |

Near-white is the default preference, not an unconditional requirement. It
also makes tiny neutral residuals less conspicuous on light UI, but that is
only a tie-breaker. A derivative must still survive gray, black, checker, and
actual runtime-size review.

Prefer a slightly offset neutral such as `#F4F4F1` over clipped pure white
when the edge palette allows it. The small gap keeps white specular highlights
measurably separate from the matte instead of flattening both to `#FFFFFF`.
When that gap is still too small, use an unused contrast key rather than
forcing near-white.

Do not generate independent white-background and black-background variants
and treat them as a multi-matte render. Separately generated images are not
pixel-identical evidence for alpha recovery.

## Mandatory generation clause

Adapt the bracketed values and include this clause in the actual image
generation or edit prompt:

```text
Render only the complete subject on one perfectly uniform [matte color]
background chosen for the subject's real edge palette and material. Keep
10–15% clean background padding around the full silhouette and keep the matte
constant to every canvas edge. No gradient, texture, vignette, horizon,
scenery, floor, depth of field, cast/contact/drop shadow, background glow,
ambient haze, or matte-colored lighting spill. Preserve the subject's approved
colors and material; do not add an outline or change the design to create
contrast. Optimize the source for deterministic alpha extraction.
```

For a Delivery Target chroma job, replace `[matte color]` with the exact
recorded key and explicitly keep that color and close colors out of the
subject, props, highlights, and effects.

## Reject before processing

Inspect the generated source before background separation. Reject or regenerate
it when:

- the background has a gradient, vignette, texture, floor, shadow, haze, or
  other scene content;
- the subject touches the canvas edge or lacks clean padding;
- an opaque contour is visually lost against the matte at intended size;
- a known key appears in identity-bearing subject pixels;
- background color or lighting has visibly contaminated glass, hair, smoke,
  glow, or another sensitive material.

Do not tune alpha power, noise tolerance, blur radius, chroma threshold, or
another raster parameter to rescue a source that violates this strategy. Keep
the existing deterministic processing defaults and obtain a better source.

## Review after processing

Review the derivative on white, gray, black, checker, and the actual runtime
surface at 1x size. Near-white residue being hard to see on a light background
does not close QA. Preserve fine identity-bearing detail, report material
uncertainty, and fail closed when the derivative is not trustworthy enough to
enter Previewer.
