# QA policy

## Five independent questions

Run QA as separate gates:

1. **Identity:** Is this unmistakably the approved character?
2. **Semantics:** Does each state communicate the correct intention?
3. **Motion:** Does the physical behavior feel coherent at actual speed?
4. **Technical:** Does the atlas and manifest match the Codex v2 contract?
5. **Privacy:** Is every publishable artifact safe to share?

A pass in one category cannot compensate for a failure in another.

## Common creative failures

### Identity drift

Symptoms:

- face proportions change across states
- appendages acquire anatomy that was never approved
- a fold becomes a separate object
- materials or line language change between rows

Prevention:

- attach the canonical reference and mechanism limits to every state task
- compare state keyframes side by side before row production
- repair the smallest failing row

### State sameness

Symptoms:

- only the limb moves while face, body, and spatial focus remain fixed
- waiting and idle differ only in speed
- active states reuse the same silhouette

Prevention:

- define intention, location, silhouette, and fixed-slot rhythm before drawing
- use different approved ranges of the same mechanisms
- compare state stills without labels

### Excessive animation

Symptoms:

- every loop bounces
- every feature moves at once
- no rest frame
- secondary motion leads without a cause

Prevention:

- define the lead element
- allocate a stillness budget
- create restrained easing through pose spacing and material deformation

### Human-like anatomy

Symptoms:

- floating arms read as a standing person
- limbs emerge far from the face or shared opening
- hands become generic mitten shapes

Prevention:

- preserve approved emergence points
- model appendages as material continuations when appropriate
- judge the silhouette before interior detail

### Broken material logic

Symptoms:

- cloth behaves like rubber
- a heavy mass snaps into place
- rigid elements melt without an approved mechanism

Prevention:

- record material behavior in the motion bible
- use consistent lag, fold, compression, and settle rules

## Common production failures

- wrong atlas dimensions
- incorrect `spriteVersionNumber`
- blank used cells
- nontransparent unused cells
- cropped or overlapping sprites
- identity-changing scale jumps
- reversed directional gait
- ambiguous cardinal directions
- visible loop reset
- forbidden detached effects
- filenames or JSON fields inconsistent with the manifest

Use `$hatch-pet` for the authoritative production checks. Use `studio.py validate` as a fast structural gate, not a substitute for full visual QA.

## Review protocol

1. Inspect the contact sheet.
2. Inspect each state at the current fixed client cadence.
3. Inspect first frame, accent frame, and loop seam.
4. Compare unlabeled state stills for semantic distinction.
5. Inspect the 16 direction cells as one ordered loop.
6. Review at 80, 144, and 224 px.
7. Record `pass`, `warning`, or `fail`.

Warnings remain visible in the release summary. A repaired visual row requires independent review or explicit user inspection before packaging.

## Clean-room onboarding test

Before release, use a fresh Codex task with no private project context. Give it only the public repository and a realistic prompt:

> Use these inspirations to design a Codex pet with me. Start by understanding and discussing them; do not generate the full pack at once.

The test passes when Codex:

- discovers the project skill
- speaks the user's language
- starts with interpretation rather than generation
- treats inputs as private
- explains the next approval gate
- does not require an API key or hosted service
- can start the Previewer and run deterministic checks
