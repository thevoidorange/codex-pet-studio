# Creative workflow

Use this reference only for new or resumed creative decisions. Preview-only,
single-frame Take, validation, packaging, and installation requests use their
shorter routes.

## Contents

- Resume and preflight
- Decision records and approval
- Gate 1: inspiration
- Gate 2: creative genome
- Gate 3: default form
- Gate 4: variable mechanics
- Gate 5: state choreography
- Gate 6: motion language
- Gate 7: production readiness
- Gate 8: release readiness
- Scope shortcuts

## Resume and preflight

When a project exists:

1. Read `pet-studio.json`.
2. Read populated private decisions under `design/`.
3. Inspect Candidates, selected assets, unresolved warnings, and available
   Previewer review context.
4. Tell the user only what is locked, what remains open, and the next useful
   creative decision.

Prefer current files over older chat summaries. Do not reinterpret an approved
choice because an older conversation used different wording.

For a cold start, run idempotent `init` and `doctor`. Classify supplied images,
sketches, descriptions, and references as private by default. Populate only
`design/inspiration-brief.md`; activate later templates only when their gate
begins.

## Decision records and approval

End each gate with a compact record in the user's language:

```markdown
## G3 Default form

Status: approved
Selected: D3
Locked:
- ...
Open:
- ...
Rejected:
- D1 — ...
Evidence:
- explicit user feedback or visual observation
Next question:
- ...
```

Use stable English gate and option IDs.

Status meanings:

- `open` — unresolved or not started
- `candidate` — viable but not selected
- `approved` — explicitly selected and safe to build upon
- `superseded` — replaced by a newer approved decision
- `blocked` — a material input or choice is missing

Do not treat “better,” “interesting,” a Previewer selection, or silence as
approval. When a decision changes, identify only the dependent gates that need
review.

## Gate 1: inspiration

Separate the source into:

1. **Subject truth** — observed behavior, posture, rhythm, material, or
   personality.
2. **Taste signal** — abstraction, proportion, line, weight, restraint, humor,
   or visual tension the user responds to.
3. **Transferable principle** — a generative rule that can shape a new pet.
4. **Literal detail** — source-specific content that should not automatically
   be copied.

Offer one concise working reading and wait for explicit alignment before image
generation or Gate 2. Ask only when one ambiguity would materially change the
direction.

## Gate 2: creative genome

Record:

- three to seven identity rules;
- three to seven behavioral truths grounded in observable actions;
- three to seven visual constraints;
- explicit anti-goals;
- one short “this is / this is not” statement.

Each rule must exclude a plausible wrong result. Replace adjectives such as
“friendly” with behavior such as “approaches, pauses, asks, and returns after
being ignored.”

## Gate 3: default form

Explore only the neutral form. Hold treatment stable unless treatment is the
question.

Judge in this order:

1. silhouette at 80–224 px;
2. mass, center of gravity, and visual weight;
3. relationship between primary forms;
4. focal or face placement;
5. negative space;
6. minimum surviving identity details;
7. compatibility with the intended mechanism system.

Use three to six stable, neutrally labeled options. Record why rejected
silhouettes failed. Do not polish surface detail to rescue weak structure.

## Gate 4: variable mechanics

Populate the private `design/mechanism-board.md` that `init` scaffolded from
the public template. Keep the inventory small.

For each mechanism, define:

- neutral form and anchor or emergence point;
- allowed translation, rotation, deformation, visibility, and layer changes;
- useful range and extreme-but-valid range;
- interaction with adjacent elements;
- rest behavior;
- forbidden anatomical, material, or object reading.

Use separate range, attachment, and occlusion boards only when one combined
board cannot answer the current question. A mechanism is approved when the
user understands what can change while the character remains itself.

## Gate 5: state choreography

Design the nine standard runtime states as different intentions, not cosmetic
variants. Start with state briefs and representative Keyframes, not atlas rows.

For each state record:

- purpose and trigger context;
- starting composition and focal location;
- active mechanisms and silhouette;
- anticipation, action, accent, settle, and seam;
- secondary material response;
- contrast from the nearest neighboring state.

Evaluate state contrast on four axes:

| Axis | Test |
| --- | --- |
| Intention | Does this state want or do something different? |
| Location | Does the focal feature occupy a meaningfully different region? |
| Silhouette | Is it distinguishable without interior detail? |
| Rhythm | Does fixed-slot pose spacing create a different motion character? |

Subtle motion is acceptable. Reusing nearly identical composition across most
states is not.

## Gate 6: motion language

Define once:

- lead element and follow hierarchy;
- perceived material and pose-spacing character;
- squash, stretch, overshoot, and damping limits;
- stillness budget and visual holds;
- settle order and loop philosophy;
- reduced-motion first-frame behavior.

Map state beats onto the fixed client slots only after the state intentions
work as stills. Review the first frame, accent, final settle, seam, normal
cadence, and 80/144/224 px views. Approve the felt motion, not only enlarged
Keyframes.

## Gate 7: production readiness

Hand off:

- canonical identity reference;
- creative genome and anti-goals;
- mechanism inventory;
- state choreography;
- motion bible;
- explicitly approved Keyframes and Takes;
- selected Candidate ID;
- privacy classification.

Production may make deterministic registration, transparency, extraction, and
spacing corrections that preserve the approved visual truth. Any change to
silhouette, feature relationships, state meaning, or motion language returns
to the relevant creative decision.

## Gate 8: release readiness

Require:

- the intended Candidate passed all applicable QA;
- export contents are allowlisted;
- privacy, rights, and attribution are complete;
- package, installation, and publication targets are distinguished;
- remaining warnings are visible.

Installation success, export success, and publication success are separate
claims.

## Scope shortcuts

- Existing valid pack, preview only: open the Previewer.
- Existing approved art, animate it: confirm identity lock, then begin at
  variable mechanics.
- Existing rows, package only: validate contract and privacy, then stage and
  export without reopening creative gates.
- Repair one production state: preserve passing rows, diagnose the affected
  row, and repair that row.
- Review one Keyframe: use the Take workflow instead of this creative sequence.
- Change identity: create a new Candidate and return to default-form lock.
