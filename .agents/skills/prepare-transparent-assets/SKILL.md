---
name: prepare-transparent-assets
description: Plan material- and palette-aware source mattes, then prepare transparent PNG derivatives for any Creature asset before Previewer review or final production. Use before generating or editing Static Candidates, Static Takes, runtime Takes, atlas rows, or repairs, and for known chroma-key art, opaque images on a smooth bright border background, existing alpha cleanup, soft-edge preservation, hidden-RGB cleanup, and background-color spill removal. Run whenever an image may enter Previewer; this capability is stage-agnostic and is not limited to hatch-pet production.
---

# Prepare Transparent Assets

## Contract

Every image rendered by Previewer must be a transparent derivative with both
visible and transparent pixels. Preserve the exact creative source separately;
never overwrite it merely to make it review-compatible.

This skill owns two independent deterministic stages:

1. **Background separation** creates alpha.
2. **Alpha-edge cleanup** smooths the new matte where appropriate, removes
   background contamination from visible edge RGB, and clears RGB under
   alpha zero.

`$pet-studio` owns review staging. `$hatch-pet` owns target geometry and final
production orchestration. Both consume this shared raster capability.

## Plan the source matte

Before `$imagegen` or another visual editor creates an asset that may enter
Previewer, read
[source-matte-strategy.md](references/source-matte-strategy.md). Classify the
subject by its real edge palette and most extraction-sensitive material, record
the selected alpha or matte route in the visual brief, and include the chosen
background clause in the actual generation prompt.

Use neutral near-white by default only when it naturally separates the
silhouette. Switch to a recorded unused contrast key for pale opaque edges.
Prefer reliable true alpha for glass, translucent, refractive, hair, smoke, or
glow; when only one opaque composite is available, use the strategy's
conservative review-quality approximation and state the limitation. A
Delivery Target's required key overrides the near-white default.

When an opaque source already appears to have a flat saturated matte, use the
shared border/corner detector as contract evidence before selecting another
key. Reuse only a high-confidence candidate; require an explicit decision for
medium confidence. A conflicting source, request, style-note, or Delivery
Target key is a pre-generation error, not permission to tune raster cleanup.

Source-matte planning is upstream of the two deterministic raster stages. It
does not combine background separation with alpha cleanup and does not change
their default parameters. Reject or regenerate a bad source instead of tuning
the raster pipeline around one case.

## Runtime

Call `load_workspace_dependencies` first. Set `PYTHON` to the exact Python
executable it returns. The scripts require Pillow; `auto-border` also requires
NumPy. Do not use a bare system Python.

```bash
SKILL_DIR="<absolute project path>/.agents/skills/prepare-transparent-assets"
```

## Choose a mode

- `preserve-alpha` — the source already has meaningful alpha; preserve it and
  clear hidden RGB.
- `chroma` — the source uses a known flat `#RRGGBB` key. Supply the exact key.
- `auto-border` — the source is opaque and its outer border is a predictable
  bright, low-chroma illumination field. The fit fails closed on scene-like or
  unreliable borders.
- `auto` — preserve existing alpha when present; otherwise use `auto-border`.

Do not call a natural-scene image “processed” merely because the command ran.
When `auto-border` rejects it, obtain a deliberate matte or generate a true
transparent source instead of weakening the confidence gate.

## Normal route

Run both stages through the composed command:

```bash
"$PYTHON" "$SKILL_DIR/scripts/prepare_transparent_asset.py" \
  /absolute/path/to/source.png \
  --output /absolute/path/to/review-transparent.png \
  --mode auto \
  --json-out /absolute/path/to/transparency-report.json
```

For a known chroma key:

```bash
"$PYTHON" "$SKILL_DIR/scripts/prepare_transparent_asset.py" \
  /absolute/path/to/chroma-source.png \
  --output /absolute/path/to/review-transparent.png \
  --mode chroma \
  --chroma-key "#FF00FF" \
  --json-out /absolute/path/to/transparency-report.json
```

The report keeps `separation` and `cleanup` as distinct records even when the
composed command is used.

## Run the stages separately

Background separation only:

```bash
"$PYTHON" "$SKILL_DIR/scripts/remove_background.py" \
  /absolute/path/to/source.png \
  --output /absolute/path/to/separated.png \
  --mode auto-border
```

Then smooth alpha and unmix the fitted background:

```bash
"$PYTHON" "$SKILL_DIR/scripts/clean_alpha_edges.py" \
  /absolute/path/to/separated.png \
  --output /absolute/path/to/review-transparent.png \
  --mode auto-border \
  --background-source /absolute/path/to/source.png
```

For an atlas, use chroma cleanup with explicit cell isolation so edge colors
never bleed across cells:

```bash
"$PYTHON" "$SKILL_DIR/scripts/clean_alpha_edges.py" \
  /absolute/path/to/atlas.png \
  --output /absolute/path/to/atlas.png \
  --webp-output /absolute/path/to/atlas.webp \
  --mode chroma \
  --chroma-key "#FF00FF" \
  --cell-width 192 \
  --cell-height 208
```

Only `$hatch-pet` decides the target cell dimensions and when the final atlas
cleanup runs.

## Review handoff

For a Static Candidate, pass both files:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py review stage-static \
  --root /absolute/path/to/project \
  --asset /absolute/path/to/source.png \
  --preview-asset /absolute/path/to/review-transparent.png \
  --candidate <semantic-id>
```

`--asset` is preserved as source evidence. Only `--preview-asset` is referenced
by Previewer. Static and runtime Takes must likewise be prepared transparent
PNGs before `studio.py take add`.

## QA

Before handoff:

1. verify the report has `ok: true`;
2. inspect the derivative on white, gray, black, and checker backgrounds;
3. confirm holes are transparent and identity-bearing fine detail remains;
4. confirm there is no colored matte fringe or hidden RGB under alpha zero;
5. treat approval, validation, staging, production, and packaging as separate
   outcomes.

An opaque RGB image cannot uniquely recover true glass, hair, smoke, or
refractive alpha from one background. Prefer detail-preserving uncertainty,
report the limitation, and return for visual review.

Read [transparency-contract.md](references/transparency-contract.md) for
algorithm and report details.
