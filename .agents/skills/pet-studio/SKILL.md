---
name: pet-studio
description: Co-design, review, refine, repair, validate, package, export, or explicitly install a Codex desktop pet from inspiration or an existing project. Use for staged creative decisions, first-image Static Candidate and progressive Previewer handoff, identity and mechanism locks, fixed-slot state motion, Candidate/Keyframe/Take review, exact one-frame alternatives, existing-pack maintenance, and Codex v2 production without losing prior approvals or private inputs.
---

# Pet Studio

Build a distinctive Codex pet through reversible creative decisions and
deterministic production. Treat the Previewer as a co-design review workbench
and the Codex conversation as the editing surface.

## Operating contract

- Prefer current project files and a validated Previewer config over chat
  summaries. Use a validated review URL as the current focus, never as approval.
- Collaborate in the user's language. Keep filenames, IDs, schema keys, code,
  and reusable project artifacts in English.
- Treat personal references as private local inputs unless the user explicitly
  approves publication.
- Separate creative approval, review selection, technical validation,
  packaging, installation, and publication. One never implies another.
- Preserve approved work before exploration. Add a Candidate or Take instead
  of silently overwriting the only accepted result.
- Keep Studio Core creative truth separate from Delivery Target sampling.
  Platform constraints may shape runtime frames without redefining the approved
  character.
- For new designs, resolve the smallest useful visual question before broad
  state production. Do not use image volume as a substitute for a decision.
- Make multimodal alignment the default creative loop. Once there is enough
  inspiration for a meaningful direction, deliver the first static character
  study in the next substantive response. Do not require approval of a
  prose-only brief first.
- On a true project cold start, complete setup, start or reuse the local
  Previewer immediately, open it on the bundled `Example.RaincoatCat`, and
  verify that the Example is visible. Treat it as an orientation surface only,
  never as project evidence.
- At that verified cold-start handoff, complete the one-time model-guidance
  report required by the root `AGENTS.md`, preserving the README's published
  order.
- As soon as that first reviewable static image exists, preserve the exact
  asset as a Static Candidate, create or update a validated project Previewer
  config, and move the already-running Previewer to a URL focused on that
  image. Do not wait for an atlas, animation, or all nine runtime states.
- Ask at most one genuinely blocking question before the first visual.
  Otherwise make restrained, visible assumptions and let the user correct the
  image.
- Use focused visuals to align each later layer: default form, relationship or
  emotional stance, variable mechanisms, state acting, and motion.
  Never defer all imagery until an all-in-one multimodal delivery.
- Use `$imagegen` for visual generation and editing. For the current
  `codex-pet-v2` target, use the project-bundled `$hatch-pet` skill as the
  authoritative production compiler and validator.
- Never install or publish unless the user explicitly requests that action.

## Re-enter and route

Before acting, inspect `pet-studio.json`, the selected Delivery Target, current
`design/` decisions, available Candidates, `build/`, unresolved QA, and any
valid Previewer URL in task context. Preserve current work and resume through
the shortest truthful route. Reopen the latest valid project-focused Previewer
URL when reviewable work already exists; do not replace it with the bundled
Example. When no project Candidate exists yet, start or reuse the Previewer and
open its base URL so `Example.RaincoatCat` is visible while creative work
begins. If no target is recorded, the current repository supports
`codex-pet-v2` only:

| User situation | Route |
| --- | --- |
| New inspiration or an undeveloped idea | Run idempotent `init` and `doctor`, start or reuse the Previewer, open the bundled `Example.RaincoatCat`, and verify that it renders. Record a concise provisional reading, then produce the smallest useful static character study as soon as there is enough direction. Stage that exact image as a semantically named Static Candidate, validate its config, switch the Previewer to its focused URL, and verify that the visible asset belongs to the project. Do not wait for a complete questionnaire, prose-only Gate 1 approval, an atlas, or nine states. |
| Existing approved character or partial project | State what is locked and open, reopen the latest valid project review focus when available, then resume at the first unresolved creative decision. Do not restart ideation or fill missing work with Example assets. |
| Feedback on one Previewer Keyframe or Take | Resolve the exact review context and use the single-frame Take workflow. Do not reopen unrelated gates. |
| Existing pack maintenance | Validate provenance and scope, preserve passing rows, and repair only the affected production unit. Return to a creative gate only when identity, state meaning, or motion language changes. |
| Preview, validate, export, or explicit install | Use the deterministic project command for that operation without reopening creative decisions. |

Read [creative-workflow.md](references/creative-workflow.md) for inspiration,
identity, default-form, mechanism, state, and motion decisions.

For the first-image handoff, prefer the deterministic command:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py review stage-static \
  --asset <path-to-exact-png-or-webp> \
  --candidate <semantic-candidate-id> \
  --default
```

Choose the Candidate ID and display name from the actual proposal. Use a
stable, concise English identifier; do not manufacture `v001`, `v002`, or
another sequential version scheme unless the project already uses one
deliberately. Use the returned project-focused URL. Read
[review-workbench.md](references/review-workbench.md) for candidate updates,
safe URL restoration, and progressive runtime coverage.

## Use one decision loop

For each creative round:

1. State the one uncertainty being resolved.
2. Name what is locked, what may change, and the relevant anti-goals.
3. Produce the smallest visual comparison that can answer the question. If
   form, mechanism, acting, emotion, or motion is being decided, prose alone is
   not a completed round.
4. Stage the exact review artifact in the current Candidate and open or refresh
   its focused Previewer URL. A first still uses `state=static`; later runtime
   work exposes only the states that actually exist.
5. Review at realistic desktop size when readability matters.
6. Record the selection, rejection reasons, remaining open variables, and next
   dependent decision.

Do not treat “better,” “interesting,” a Previewer click, or silence as approval.
The user may combine adjacent gates, but unresolved dependencies remain open.
The first exploratory image is a working hypothesis, not an approved Identity
Lock.

After delivering a visual checkpoint, stop before the next dependent creative
layer and ask for correction or selection. Continue only after explicit review,
unless the user explicitly asked to combine those exact adjacent layers.

Before generating or editing visuals, read
[visual-iteration.md](references/visual-iteration.md). Before planning states
or animation rows, read [delivery-targets.md](references/delivery-targets.md)
and
[motion-and-state-contract.md](references/motion-and-state-contract.md).

## Keep the domain model explicit

- **Candidate** — one coherent, reviewable proposal at its current level of
  completion. It may begin as one Static image and accumulate an exact subset
  of runtime states over time. A Candidate is not a revision number: parallel
  Candidates may represent different characters, pets, or creative directions.
  Let the project's Codex choose a stable semantic ID and natural display name
  from the actual proposal.
- **Static** — one standalone character-study image plus optional Takes. It is
  a review surface before runtime sampling, not a runtime state, Keyframe row,
  timing entry, or fabricated one-frame animation.
- **Keyframe** — one named visual time sample. In the current target's
  Candidate, it maps to one fixed runtime slot inside one state row.
- **Take** — one additive visual alternative for one exact Candidate and
  review slot: either Static or one runtime Keyframe.
- **Audition** — temporary Take viewing. It changes no project decision.
- **Confirm** — session-only Previewer selection for that Keyframe. It changes
  no source asset, config, Candidate, QA result, or approval state.
- **Approval** — an explicit conversational decision such as “use this” or
  “this is final.” Record the exact asset and the locked details in the current
  private design decision artifact.
- **Promotion** — moving an approved, fully reviewed Candidate into production
  or release. A single approved Take never promotes a Candidate by itself.

Treat an explicitly approved Take as authoritative visual evidence. Pass the
exact asset into production grounding. Do not silently redraw it. If the
current compiler requires row-level synthesis and cannot preserve exact pixels,
keep the approved asset, explain the constraint before production, and obtain
direction rather than substituting a similar result.

## Handle one-frame review requests deterministically

The Previewer reviews work; it does not author or mutate it. Do not add a
**Request New Take** field, embedded prompt, upload, save, **Install in Codex**,
packaging, promotion, or QA action.

When the user refers to “this,” “this frame,” or asks for another Take:

1. Read and validate the current `config`, `candidate`, `state`, one-based
   `frame`, and `take` values.
2. Resolve the external config to a canonical local file under the current
   project root. If it is missing, remote, fallback-only, or unsafe to map, ask
   one concise project/path question instead of guessing.
3. Resolve the selected source exactly. For `state=static`, use the standalone
   Static image and preserve its canvas. For a runtime state, load the selected
   Delivery Target contract and materialize exactly one target-cell-sized
   frame. Treat neighboring frames only as read-only continuity evidence.
4. Apply only the requested delta and every current identity/mechanism lock.
   For a bare “another Take,” make a restrained same-brief variation unless the
   intended difference is genuinely ambiguous.
5. Generate exactly one standalone image at the source slot's dimensions. Do
   not change the Static original, source atlas, current Take, adjacent frames,
   or unrelated config.
6. Register it atomically with
   `python3 .agents/skills/pet-studio/scripts/studio.py take add --help`.
7. Validate the refreshed config and asset, then return the focused URL with
   the new Take auditioned, not approved.

Read [review-workbench.md](references/review-workbench.md) before executing this
route. A continuity concern creates another Take for the requested frame unless
the user explicitly broadens the scope.

## Design inside the selected Delivery Target

Define Behavior Intents and Motion Language in target-neutral terms, then map
them into the selected target's states, mechanics, frame slots, cadence, and
lifecycle. Preserve canonical identity and motion truth separately from the
sampled target build.

For the current `codex-pet-v2` target, the pet package cannot customize frame
durations, loop counts, Idle slowdown, or display size. Treat the installed
`$hatch-pet` instructions as authoritative and the checked-in Codex target
contract as the exact checked-in planning snapshot. Run `studio.py target
check` before Previewer review or production so handwritten project code
cannot drift from that contract.

Create state difference through intention, focal location, silhouette,
mechanism use, weight, and fixed-slot pose spacing. Subtle motion is valid;
nearly identical composition across states is not. Favor caused follow-through,
material continuity, visual holds, and settled seams over universal bounce.

Review source-atlas playback through both Previewer modes:

- **Runtime Simulation** checks the real action lifecycle and return to Idle.
- **Endless Loop** repeats the same fixed cadence for seam and continuity
  inspection.

Neither mode is an exported GIF or a timing editor. Review at the selected
target's minimum, representative, and maximum display sizes.

Runtime review is progressive. Declare the exact runtime state IDs present in
each Candidate and show only those states. Keep missing states absent; never
duplicate an available row, synthesize a placeholder, or borrow the bundled
Example to imply coverage. Static remains independently reviewable while
runtime states accumulate. Require complete target coverage only at the
production or release gate that actually needs it.

## Produce, maintain, and release

The production path below is for the currently supported `codex-pet-v2`
Delivery Target.

For a new design, hand off to `$hatch-pet` only after the default form,
mechanisms, state intentions, representative Keyframes, fixed-slot motion plan,
selected Candidate, Delivery Target, behavior-to-runtime mapping, and privacy
scope are approved.

For existing-pack maintenance, validate first and use only the affected row or
production unit. Do not require unrelated creative gates when identity and
semantics are unchanged.

Pass production:

- the canonical identity reference and anti-goals;
- mechanism limits and material rules;
- Behavior Intents, target state mapping, and Motion Language;
- target-specific slot choreography and production plan;
- every explicitly approved Keyframe or Take as a named grounding asset;
- the exact Candidate ID, Delivery Target ID, and privacy classification.

Stage validated output under `build/pet`. If the bundled `$hatch-pet`
workflow would write directly to a live Codex pets directory, stop before that
copy step and stage the validated manifest and atlas in the project instead.
Run project validation and privacy checks before export. Run
`studio.py install` only after an explicit installation request and to an
explicit destination.

Read [codex-pet-v2.md](references/codex-pet-v2.md) for the production boundary.
If a newer externally installed `$hatch-pet` differs, report the discrepancy
and reconcile the checked-in target intentionally before adopting it.

## Validate and hand off honestly

Read [qa.md](references/qa.md) for creative, Previewer, motion, pack, and
clean-room checks. Read [privacy.md](references/privacy.md) before export,
publication, or any work involving personal references.

Report `pass`, `warning`, and `fail` separately. Do not claim that a generated
file is a finished pet, that a package is installed, or that a Candidate is
approved without evidence for that exact outcome.

Deliver the current Candidate and decision summary, a focused Previewer URL,
validated pack or export paths when applicable, visible warnings, and the next
smallest useful step.

## Resource routing

- Creative definition or resumed design:
  [creative-workflow.md](references/creative-workflow.md)
- Visual generation, editing, identity drift, or convergence:
  [visual-iteration.md](references/visual-iteration.md)
- Candidate, Keyframe, Take, Confirm, or review URL:
  [review-workbench.md](references/review-workbench.md)
- Behavior Intent, Motion Language, or target-neutral precision:
  [motion-and-state-contract.md](references/motion-and-state-contract.md)
- Studio Core, target selection, behavior mapping, or future retargeting:
  [delivery-targets.md](references/delivery-targets.md)
- Acceptance, repair, Previewer integrity, or release:
  [qa.md](references/qa.md)
- Personal inputs, export, or publishing:
  [privacy.md](references/privacy.md)
- Codex fixed slots, timing, lifecycle, display sizes, atlas, compiler, or
  installation:
  [codex-pet-v2.md](references/codex-pet-v2.md)
