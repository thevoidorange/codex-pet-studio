# Visual iteration protocol

Use this reference before generating or editing any Pet Studio visual. The goal
is controlled comparison, not image volume.

## Choose the operation

- Use broad generation only while identity or default form is genuinely open.
- Use image editing when the user has selected a visual and requests a bounded
  change.
- Use a mechanism board when testing one reusable range or attachment.
- Use a single-frame Take when changing one fixed state slot.
- Use `$hatch-pet` row generation only after state and motion decisions are
  approved.

Do not turn an exact edit request into a fresh redesign.

## Build the visual brief

Every visual job must state:

1. **Question** — the one decision this output answers.
2. **Authoritative reference** — the selected Candidate, Keyframe, or Take.
3. **Locked identity** — silhouette, proportions, face, material, anchors,
   attachment points, and approved asymmetry that must remain unchanged.
4. **Allowed delta** — the exact element, direction, or range that may change.
5. **Continuity evidence** — neighboring frames or related states that may be
   inspected but not edited.
6. **Anti-goals** — prior failed readings and generic substitutions to avoid.
7. **Output contract** — count, canvas, background, scale, and comparison
   layout.

Attach only the references needed for this decision. Label each reference by
role so a layout guide, identity source, current frame, and neighboring frame
cannot be confused.

## Produce a reviewable comparison

- Hold approved features constant across options.
- Use stable neutral IDs rather than descriptive names that bias selection.
- Prefer three to six options for an open design question.
- Prefer one new option for a precise edit or Take request.
- Keep backgrounds, scale, framing, and rendering treatment comparable.
- Show normal-size views when small-scale readability is part of the decision.
- Do not mix several independent visual questions into one board.

## Protect identity during editing

Treat the selected visual as the primary source of truth. Include explicit
negative instructions against changing unrelated anatomy, clothing,
proportions, texture, line quality, or placement.

When the user says a region must remain exactly unchanged, preserve those
source pixels with a mask or deterministic composite. A generative instruction
alone is not evidence that the lock survived.

For a single-frame Take:

- materialize exactly one source frame at the selected target's cell size;
- preserve transparent canvas geometry;
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
