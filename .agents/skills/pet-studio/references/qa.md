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
3. **Motion** — Does fixed-slot playback have coherent weight and continuity?
4. **Review integrity** — Does Previewer context identify the exact work under
   discussion without mutating it?
5. **Technical validity** — Does the atlas and manifest match the current Codex
   v2 contract?
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
- use fixed-slot pose spacing as easing;
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

For every external Previewer config:

- resolve the real config path inside the current project;
- reject remote, traversal, symlink-escaped, or fallback-only write targets;
- validate Candidate and stable state IDs;
- validate one-based URL frame and zero-based config `frameIndex`;
- validate Take IDs, asset paths, and `192×208` dimensions;
- confirm missing external config invalidates the whole review handoff;
- confirm bundled example IDs are never used to satisfy failed project context.

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

For Previewer regressions:

- runtime ticks, Auto Orbit, pointer following, and all-state playback do not
  rewrite deliberate review focus;
- language and compatible Candidate changes preserve supported state;
- gaze review clears animation frame/Take context;
- every supported locale is reviewed as native product copy, including
  tooltips, accessibility labels, long controls, and narrow layouts;
- pet assets retain their original color while the interface may remain
  grayscale.

## Motion and state QA

1. Inspect representative Keyframes without labels.
2. Inspect the contact sheet.
3. Inspect every state at current fixed client cadence.
4. Inspect first frame, accent, final settle, and loop seam.
5. Compare state intention, focal location, silhouette, and rhythm.
6. Inspect left/right cadence and approved asymmetry.
7. Inspect all 16 gaze cells as one ordered loop.
8. Review at 80, 144, and 224 px.

Require:

- stable identity and anchors;
- readable state difference at desktop size;
- physically caused anticipation, follow-through, and damping;
- no unintended scale or baseline popping;
- no visible loop reset;
- unmistakable gaze cardinals and coherent adjacent directions.

Use `$hatch-pet` for authoritative row, direction, atlas, chroma, and visual QA.

## Pack and release QA

Require:

- correct v2 manifest and atlas dimensions;
- correct row and used-cell mapping;
- non-empty used cells and transparent unused cells;
- clean transparency with no clipped or overlapping sprite;
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

1. **New inspiration** — begins with private intake and interpretation, creates
   no full pack, and waits for Gate 1 approval.
2. **Focused Take request** — resolves a valid review URL, changes one frame,
   preserves neighbors, and returns a focused URL without approval or install.
3. **Existing pack, package only** — validates and exports the existing pack,
   preserves private inputs, and performs no installation.

Pass only when the agent discovers the project Skill, chooses the correct route,
uses deterministic tools for fragile operations, and reports actual outcomes
without needing hidden prior chat context.
