# Visual iteration protocol

Use this reference before generating or editing any Pet Studio visual. The goal
is controlled comparison, not image volume.

## Contents

- Make images part of the thinking
- Choose the operation
- Build the visual brief
- Produce a reviewable comparison
- Protect identity during editing
- Converge instead of flooding
- Review and record

## Make images part of the thinking

Multimodal alignment is the primary creative strategy, not a final
presentation step.

- After inspiration arrives, produce a first static character study as soon as
  there is enough direction to make one meaningful.
- Immediately preserve that exact image as the Candidate's creative source,
  prepare a transparent same-canvas review derivative through
  `$prepare-transparent-assets`, stage both through the deterministic review
  command, and open the focused project Previewer URL. Do not wait for an
  atlas or nine states, and do not regenerate the image merely to make it
  previewable.
- Ask at most one genuinely blocking question first. Do not run a questionnaire
  to completion.
- Keep the first study small and exploratory. It exists to reveal
  misunderstandings early; it is not an Identity Lock or a miniature full
  pack.
- Limit that first study to neutral identity and default form: silhouette,
  proportion, face or focal placement, and broad material reading. Do not add
  relationship poses, emotions, mechanism ranges, state acting, or motion
  unless the user explicitly made one of those the first question.
- Return to visuals at every decision that cannot be proven in prose: default
  form, mechanism range, relationship or emotional stance, state contrast, and
  motion beats.
- Do not accumulate those decisions into one all-in-one reveal. Let feedback on
  each visual constrain the next one.
- Keep the Previewer current after each checkpoint. Static holds one image with
  optional Takes; runtime navigation exposes only rows that actually exist.
  Missing states remain absent rather than becoming placeholders or Example
  assets.
- Stop after each visual checkpoint. Do not advance to its dependent creative
  layer until the user corrects or selects it, unless the user explicitly
  requested those exact layers together.

If a required reference is missing, generation is unsafe, rights are unclear,
or one ambiguity would make every direction misleading, stop for that specific
blocker. Otherwise make the smallest reversible visual and state the
assumptions it tests.

## Choose the operation

- Use broad generation only while identity or default form is genuinely open.
- Use image editing when the user has selected a visual and requests a bounded
  change.
- Use a mechanism board when testing one reusable range or attachment.
- Use a single-frame Take when changing one fixed state slot.
- Use a Static Take when changing the one-image character study before runtime
  Keyframes exist.
- Use `$hatch-pet` row generation only after state and motion decisions are
  approved.

Do not turn an exact edit request into a fresh redesign.

## Build the visual brief

Before generating or editing a Creature asset, apply the material- and
palette-aware source matte strategy from `$prepare-transparent-assets`. Put the
selected matte clause in the actual `$imagegen` prompt; naming a background in
the brief without constraining the generated source is not enough.

Every visual job must state:

1. **Question** — the one decision this output answers.
2. **Authoritative reference** — the selected Candidate, Keyframe, or Take.
3. **Locked identity** — silhouette, proportions, face, material, anchors,
   attachment points, and approved asymmetry that must remain unchanged.
4. **Allowed delta** — the exact element, direction, or range that may change.
5. **Continuity evidence** — neighboring frames or related states that may be
   inspected but not edited.
6. **Anti-goals** — prior failed readings and generic substitutions to avoid.
7. **Material and matte plan** — edge palette, material profile, true-alpha or
   matte route, exact background clause, intended separation mode, and any
   review limitation.
8. **Output contract** — count, canvas, background, scale, and comparison
   layout.

Attach only the references needed for this decision. Label each reference by
role so a layout guide, identity source, current frame, and neighboring frame
cannot be confused.

## Produce a reviewable comparison

- Hold approved features constant across options.
- Use stable neutral IDs rather than descriptive names that bias selection.
- Prefer three to six options for an open design question.
- Prefer one new option for a precise edit or Take request.
- Keep scale, framing, and rendering treatment comparable. Keep one background
  only when it is extraction-safe for every option; otherwise use each
  option's recorded safe matte and compare the transparent derivatives on the
  same Previewer backgrounds.
- Show normal-size views when small-scale readability is part of the decision.
- Do not mix several independent visual questions into one board.
- Preserve the exact comparison source selected for review and stage its
  transparent derivative. A Previewer handoff must point to the project
  Candidate and visible project derivative, never an opaque source or the
  bundled Example.

## Protect identity during editing

Treat the selected visual as the primary source of truth. Include explicit
negative instructions against changing unrelated anatomy, clothing,
proportions, texture, line quality, or placement.

When the user says a region must remain exactly unchanged, preserve those
source pixels with a mask or deterministic composite. A generative instruction
alone is not evidence that the lock survived.

For a single-frame Take:

- materialize exactly one source slot;
- preserve the Static source and review original's canvas for Static work or
  the selected target's cell size and transparent geometry for a runtime
  Keyframe;
- use adjacent frames only to understand continuity;
- produce exactly one standalone result at that same target cell size;
- never paste the new result into the atlas during audition;
- never revise a neighbor to make the new Take appear continuous.

If the user supplies or explicitly approves an exact frame, preserve that asset
as durable evidence. Do not assume a later generative pass will reproduce it.

## Converge instead of flooding

After each round, classify the result:

- **direction works, detail wrong** — edit the selected option narrowly;
- **mechanism works, range wrong** — run a smaller mechanism-range board;
- **identity drift** — stop, re-anchor to the approved reference and locks;
- **wrong visual reading** — rewrite the structural mechanism, not surface
  adjectives;
- **model repeats the same failure twice** — change strategy, source selection,
  or operation rather than requesting more variants.

Do not keep generating because none of a large batch feels right. Return to the
last approved visual and identify the smallest failed relationship.

Avoid questionnaire cascades, prose-only approval gates, visual debt
(mechanism or acting claims without images), first-image all-in-one reveals,
advancing past an unreviewed checkpoint, and premature atlas production.

## Review and record

Review:

- silhouette before internal detail;
- feature relationships before polish;
- the allowed delta versus every locked element;
- unintended anatomy, costume, object, or material readings;
- readability at the intended display range;
- why each rejected option failed.

Record the exact selected asset path or ID, not only a prose description. A
selected option becomes authoritative only after explicit conversational
approval.
