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
4. Reopen the latest valid project-focused Previewer URL when reviewable work
   exists. Never replace missing project context with the bundled Example.
5. Tell the user only what is locked, what remains open, and the next useful
   creative decision.

Prefer current files over older chat summaries. Do not reinterpret an approved
choice because an older conversation used different wording.

For a cold start, run idempotent `init` and `doctor`. Classify supplied images,
sketches, descriptions, and references as private by default. Populate only
`design/inspiration-brief.md`; activate later templates only when their gate
begins.

Immediately start or reuse the local Previewer, open its base URL, and verify
that `Example.RaincoatCat` is visible. This is an orientation handoff, not a
project Candidate or creative decision. Keep it open while the first useful
project visual is being made.

Do not fill the entire inspiration template as a questionnaire before making
anything visible or read its empty fields back to the user as questions. Fill
only what is already known, label assumptions as provisional, ask at most one
question that truly blocks a meaningful image, and move to the first static
character study.

Every project visual checkpoint is a handoff. Stop after showing it so the user can
correct or select before the next dependent layer. Combine exact adjacent
layers only when the user explicitly asks.

The first reviewable static image begins the project Candidate lifecycle. Stage
that exact asset as the Candidate's one-image Static review slot, create or
update a validated config, switch the already-running Previewer to its focused
URL, and verify that it displays the project image rather than the bundled
Example. Do not wait for an atlas or a complete runtime state set. Read
[review-workbench.md](review-workbench.md) for the progressive handoff
contract.

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

Offer one concise working reading, then use it to make the smallest useful
static character study in the same creative round whenever enough direction is
available. Do not require explicit approval of a prose-only reading before
image generation. Preserve the exact result as a Static Candidate and open it
in the Previewer for correction. The study is exploratory evidence, not Gate 1
approval.

Ask at most one question before that image, and only when the missing answer
would materially change every viable direction. Otherwise expose the
assumption through the visual so the user can correct something concrete.

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

The Creative Genome begins as a provisional interpretation and is refined from
the user's response to the first static study. Do not insist on finishing or
approving the entire genome before visual exploration.

Do not present the full genome inventory as a user-facing confirmation exercise
before the first visual. Derive only the minimum provisional rules needed for
that study, then complete the record from visual feedback.

## Gate 3: default form

Explore only the neutral form. Hold treatment stable unless treatment is the
question.

Judge in this order:

1. silhouette at the selected target's minimum, representative, and maximum
   display sizes;
2. mass, center of gravity, and visual weight;
3. relationship between primary forms;
4. focal or face placement;
5. negative space;
6. minimum surviving identity details;
7. compatibility with the intended mechanism system.

Use three to six stable, neutrally labeled options. Record why rejected
silhouettes failed. Do not polish surface detail to rescue weak structure.

If Gate 1 already produced a promising static study, preserve it as the
authoritative starting point and refine narrowly. Do not restart with unrelated
directions merely because Gate 3 has begun.

The first static study tests neutral identity and default form only: silhouette,
proportion, face or focal placement, and broad material reading. Do not add
relationship poses, emotions, mechanism ranges, state acting, or motion unless
the user explicitly made one of those the first visual question.

Static remains one image with optional Takes. It does not acquire runtime
timing or become a fabricated Idle loop. When a later default-form image
supersedes the working study, preserve the older Candidate and stage the exact
new image as a new Candidate or approved replacement according to the user's
decision.

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

Mechanism rules require a visual mechanism board. A prose inventory alone is
not sufficient evidence that anchors, ranges, occlusion, and material
continuity read correctly.

## Gate 5: state choreography

Define target-neutral Behavior Intents first. Then map them into every required
state of the selected Delivery Target. For the current `codex-pet-v2` target,
this means the nine standard runtime action states plus its direction mechanics.
Start with state briefs and representative Keyframes, not atlas rows.

Preview and review runtime work progressively. The first real state row may be
added by itself. Each Candidate declares the exact runtime state subset that
currently exists, and the Previewer shows only that subset alongside Static.
Never duplicate a finished row, create a placeholder, or borrow Example assets
to imply missing coverage. All required states remain a production-readiness
obligation, not a prerequisite for review.

Do not settle relationship stance, emotional baseline, or behavior rules only
in prose. Show a small set of representative static Keyframes so the user can
judge whether the character actually feels specific before motion production.

Relationship or interaction posture and the core emotional baseline may be
explored immediately after default form, before completing every mechanism
range. Reconcile the approved acting with the shared mechanism model before
state production.

For each Behavior Intent, record what the character wants, notices, or does.
For each mapped target state, record:

- mapped Behavior Intent and target trigger context;
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
| Rhythm | Does motion remain distinct under the target's sampling constraints? |

Subtle motion is acceptable. Reusing nearly identical composition across most
states is not.

Keep the Behavior Intent record reusable. A future Delivery Target may use
different state IDs, frame slots, or triggers without changing the approved
acting idea.

## Gate 6: motion language

Define the target-neutral Motion Language once:

- lead element and follow hierarchy;
- perceived material and pose-spacing character;
- squash, stretch, overshoot, and damping limits;
- stillness budget and visual holds;
- settle order and loop philosophy;
- reduced-motion first-frame behavior.

Only after the state intentions work as stills, create a separate target
sampling plan that maps beats onto its fixed or configurable slots. For the
current Codex target, review the first frame, accent, final settle, seam,
runtime cadence, and minimum/representative/maximum target-size views. Approve
the felt motion, not only enlarged Keyframes.

Use a visual beat board or short Previewer sequence to align the motion
language. A written timing plan is preparation, not motion approval.

## Gate 7: production readiness

Hand off:

- canonical identity reference;
- creative genome and anti-goals;
- mechanism inventory;
- state choreography;
- target-neutral Motion Language;
- selected Delivery Target and target sampling plan;
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
- the selected Delivery Target passed its runtime and package QA;
- export contents are allowlisted;
- privacy, rights, and attribution are complete;
- package, installation, and publication targets are distinguished;
- remaining warnings are visible.

Installation success, export success, and publication success are separate
claims.

## Scope shortcuts

- Existing valid pack, preview only: open the Previewer.
- First static study only: stage the exact image as Static, validate the
  project config, open the focused Previewer URL, and stop for review.
- Existing approved art, animate it: confirm identity lock, then begin at
  variable mechanics.
- Existing rows, package only: validate contract and privacy, then stage and
  export without reopening creative gates.
- Repair one production state: preserve passing output and repair the smallest
  unit supported by the selected target. For Codex Pet v2, this is usually one
  row.
- Review one Keyframe: use the Take workflow instead of this creative sequence.
- Change identity: create a new Candidate and return to default-form lock.
