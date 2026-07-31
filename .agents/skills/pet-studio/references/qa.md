# QA policy

## Contents

- Independent gates
- Creative and visual failures
- Review Workbench QA
- Motion and state QA
- Pack and release QA
- Repair discipline
- Clean-room forward tests

## Independent gates

Judge these independently:

1. **Identity** — Is this unmistakably the approved character?
2. **Semantics** — Does every state communicate its intended behavior?
3. **Motion** — Does target-sampled playback have coherent weight and
   continuity?
4. **Review integrity** — Does Previewer context identify the exact work under
   discussion without mutating it?
5. **Target validity** — Does the sampled output, atlas, and manifest match the
   selected Delivery Target contract?
6. **Privacy and rights** — Is every exported artifact safe and authorized?

A pass in one category never compensates for a failure in another.

## Creative and visual failures

### Identity drift

Symptoms:

- face, proportions, materials, anchors, or asymmetry change across outputs;
- an approved fold or opening becomes a separate object;
- appendages acquire unapproved anatomy;
- a precise edit redraws unrelated parts.

Prevention:

- attach the authoritative visual and current identity locks;
- name the one allowed delta;
- compare against the canonical form and nearby states;
- stop after repeated drift and change generation strategy.

### State sameness

Symptoms:

- only pupils or one limb change;
- face and focal location remain fixed across most states;
- waiting and Idle differ only in amplitude or playback speed;
- active states reuse one silhouette and rhythm.

Prevention:

- define intention, focal location, silhouette, mechanisms, and rhythm before
  row production;
- compare unlabeled representative stills;
- require each state to explain its contrast from the nearest neighbor.

### Excessive or generic motion

Symptoms:

- every loop bounces;
- all elements move at once;
- no visual hold or settled seam;
- secondary motion has no physical cause.

Prevention:

- name the lead element and material response;
- allocate stillness deliberately;
- use target sampling and pose spacing as perceived easing;
- reserve the strongest deformation for the state accent.

### Human-like or broken material logic

Symptoms:

- detached limbs read as a standing person;
- limbs emerge away from the approved shared opening;
- cloth behaves like rubber or heavy mass snaps;
- rigid parts melt without an approved mechanism.

Prevention:

- preserve anchors and attachment continuity;
- animate material continuations rather than generic hands;
- keep lag, fold, compression, and settle rules consistent.

## Review Workbench QA

For every external Previewer config in the current `codex-pet-v2` adapter:

- resolve the real config path inside the current project;
- reject remote, traversal, symlink-escaped, or fallback-only write targets;
- validate Candidate, Static asset, and stable state IDs;
- accept a Static-only Candidate, Static plus any exact runtime-state subset,
  or an atlas Candidate with any exact non-empty state subset;
- require Static to contain one standalone image with optional Takes and no
  runtime timing entry;
- require every Previewer render asset to contain visible and transparent
  pixels before any CSS rendering; inspect every reachable atlas cell rather
  than accepting transparency only in unused cells;
- require Static source evidence to remain byte-exact and separate from the
  transparent review derivative referenced by `assetUrl`;
- require every declared runtime state to have a real source row, and keep
  undeclared states absent from navigation, playback, and timing;
- validate one-based URL frame and zero-based config `frameIndex`;
- validate Take IDs, asset paths, and selected-target cell dimensions;
- confirm missing external config invalidates the whole review handoff;
- confirm bundled example IDs are never used to satisfy failed project context.
- confirm a cold start opens the bundled selector entry with the exact
  language-independent label `Example.RaincoatCat` and no Current/status
  suffix;
- confirm the first-image handoff restores the exact project Static asset,
  not a regenerated copy, placeholder, or bundled Example.

For every new Take:

- source frame and selected reference are correct;
- only one new standalone asset is created;
- new Take ID does not collide;
- source atlas, existing Takes, neighboring frames, and unrelated config remain
  unchanged;
- config update is atomic and preserves existing query parameters;
- returned URL restores the exact Candidate, state, Keyframe, and auditioned
  Take;
- audition and Confirm do not approve, promote, package, install, or publish.

For a Static Take, require the same transparent PNG format and canvas
dimensions as the Static review original. Target-cell geometry applies only to
runtime Keyframe Takes.

For Previewer regressions:

- Static-only, one-state, non-Idle one-state, mixed partial-state, and complete
  Candidates all load without fabricated coverage;
- Candidate comparison tolerates different truthful state subsets;
- runtime-only controls disable or hide when their required state or asset is
  absent;
- runtime ticks, Auto Orbit, pointer following, and all-state playback do not
  rewrite deliberate review focus;
- language and compatible Candidate changes preserve supported state;
- gaze review clears animation frame/Take context;
- every supported locale is reviewed as native product copy, including
  tooltips, accessibility labels, long controls, and narrow layouts;
- pet assets retain their original color while the interface may remain
  grayscale.
- opaque, unreadable, fully transparent, wrong-size, or unsafe assets fail the
  project handoff closed; they never render first and fail later.

## Motion and target-state QA

1. Inspect representative Keyframes without labels.
2. Inspect the contact sheet.
3. Inspect every state at the selected target's real cadence.
4. Inspect first frame, accent, final settle, and loop seam.
5. Compare state intention, focal location, silhouette, and rhythm.
6. Inspect every directional or asymmetric mechanic required by the target.
7. Inspect target look or input samples as one coherent ordered system.
8. Review at the target's minimum, representative, and maximum display sizes.

During progressive review, run these checks only against states that actually
exist and report missing required target coverage as open work. Before
production or release, require the selected Delivery Target's complete state
and mechanic coverage.

Require:

- stable identity and anchors;
- readable state difference at desktop size;
- physically caused anticipation, follow-through, and damping;
- no unintended scale or baseline popping;
- no visible loop reset;
- unmistakable cardinals and coherent adjacent directions when the target
  includes gaze.

For `codex-pet-v2`, use `$hatch-pet` for authoritative row, direction, atlas,
chroma, and visual QA. Another Delivery Target requires its own authoritative
compiler and QA contract before it can be considered supported.

## Pack and release QA

For the current `codex-pet-v2` target, require:

- correct v2 manifest and atlas dimensions;
- correct row and used-cell mapping;
- non-empty used cells and transparent unused cells;
- clean transparency with no clipped or overlapping sprite;
- shared `$prepare-transparent-assets` separation and cleanup reports match the
  exact staged derivative;
- packaged assets match approved Previewer evidence;
- project validation passes;
- privacy check passes;
- export contains only allowlisted public files.

Treat validation, export, installation, and publication as separate outcomes.
For a package-only request, verify that no live Codex pets path was written.
For installation, verify the explicit destination before reporting success.

## Repair discipline

After a failure:

1. classify it as identity, semantics, motion, review context, geometry,
   extraction, transparency, continuity, privacy, or release;
2. preserve every passing artifact and decision;
3. use deterministic correction for deterministic failures;
4. regenerate only when the source visual is wrong;
5. repair the smallest valid production unit;
6. compare the repair against the previous result and regression locks.

For a one-frame review request, the smallest valid unit is a new Take, not a
neighboring frame. For production rows or gaze rows, follow the current
`$hatch-pet` repair unit rather than patching an unsupported final cell.

Record `pass`, `warning`, or `fail`. A repaired visual requires independent
review or explicit user inspection before packaging.

## Clean-room forward tests

Before releasing a material Skill change, run fresh-context tests for:

1. **New inspiration** — completes setup, starts or reuses the Previewer,
   opens `Example.RaincoatCat`, and verifies the visible Example before
   creative production. In the same setup-completion message, it reports the
   README `Model guidance` in the user's language exactly once and in its
   published order: full-experience recommendation first, demanding visual and
   animation work second, and not-recommended configurations last, with the
   bare-bones minimum mentioned only inside that final warning. Repeated setup
   checks, Previewer restarts, and project re-entry do not repeat it. It then
   begins private intake with a concise provisional
   interpretation, asks no more than one genuinely blocking question, and
   produces a bounded first static character study before any full
   questionnaire or pack. The agent stages that exact image as a
   semantically named Static Candidate, validates the project config, switches
   to its focused project URL, verifies that no bundled Example was
   substituted, and stops for visual review. The study tests neutral form only
   and remains unapproved.
2. **Focused Take request** — resolves a valid review URL, changes one frame,
   preserves neighbors, and returns a focused URL without approval or install.
3. **Existing pack, package only** — validates and exports the existing pack,
   preserves private inputs, and performs no installation.
4. **Post-selection acting** — after a default form is selected, produces one
   focused relationship, emotional, or behavior Keyframe comparison and stops
   before broader mechanism, state, or motion production.
5. **True blocker** — when a required source is missing or every visual
   direction would be misleading, asks one specific question instead of
   fabricating evidence or starting a questionnaire cascade.
6. **Progressive coverage** — a Static-only Candidate, a one-state Candidate
   without Idle, and a partial-state Candidate expose only real assets; missing
   states, timing rows, and gaze controls do not appear.
7. **Project re-entry** — reopens the latest valid project focus and never
   presents the bundled Example as the user's current Candidate.

Pass only when the agent discovers the project Skill, chooses the correct route,
uses deterministic tools for fragile operations, and reports actual outcomes
without needing hidden prior chat context.
