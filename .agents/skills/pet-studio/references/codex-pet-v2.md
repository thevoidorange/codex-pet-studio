# Codex Pet v2 Delivery Target

Delivery Target ID: `codex-pet-v2`

## Contents

- Authority and provenance
- Runtime sampling contract
- Runtime lifecycle and Previewer modes
- Behavior Intent mapping
- Fixed-slot acting strategy
- Look directions
- Staging package
- Responsibility boundary
- Preserve approved visuals
- Target QA
- Package, export, install, and publish

## Authority and provenance

The exact checked-in runtime facts live in the machine-readable
[Codex Pet v2 Delivery Target contract](../../../../delivery-targets/codex-pet-v2.json).
It owns the atlas geometry, states, slot durations, runtime lifecycle, look
directions, package requirements, and display range used by project tooling
and the Previewer. This file explains how to design inside those facts; it is
not a second technical contract.

The contract records the Codex Desktop build and date it was verified against.
Treat that provenance as a snapshot, not a promise that later clients remain
identical. Re-read the installed `$hatch-pet` skill before every production or
repair run. If it conflicts with the checked-in contract, stop, report the
discrepancy, and revise the contract intentionally before continuing.

Run:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py target check
```

This validates both the canonical JSON and the generated static adapter used
by `file://` Previewer sessions. After an intentional contract revision, run
`studio.py target sync`, review both files, and commit them together.

Read [delivery-targets.md](delivery-targets.md) for the Studio Core / Delivery
Target boundary and
[motion-and-state-contract.md](motion-and-state-contract.md)
for target-neutral Motion Language.

## Runtime sampling contract

Read the contract rather than copying its dimensions, row lengths, timings, or
display limits into another file. Every consumer derives these values from the
selected target. The package itself carries no per-frame duration,
action-loop, Idle-multiplier, or display-size field.

Do not add controls or project settings for values that the package cannot
carry. Motion easing comes from the differences drawn into the immutable
slots.

## Runtime lifecycle and Previewer modes

The runtime lifecycle is client-owned and declared read-only in the Delivery
Target contract. It identifies the Idle state, the Idle duration multiplier,
the number of action loops, and the state returned to after an action.

The Previewer exposes two readings of the same source atlas and cadence:

- **Runtime Simulation** plays the current action lifecycle, then returns to
  Idle at the client slowdown;
- **Endless Loop** repeats the selected row indefinitely with the same
  per-frame durations.

Use Runtime Simulation to review lifecycle and return behavior. Use Endless
Loop to inspect physical continuity and the seam. Neither mode is an exported
GIF or a timing editor.

## Behavior Intent mapping

The stable IDs below belong to this Delivery Target. Record the project's
target-neutral Behavior Intent separately.

### `idle`

Map to quiet presence and the lowest visual noise. Because the client slows the
row by six, keep most drawings close. Let one restrained breath, blink, fold,
or curiosity beat occupy the shorter middle slots. Make the final slot the
cleanest rest and seam. The first slot must work as a reduced-motion still.

### `running-right` and `running-left`

Map to screen-directional locomotion. Use the repeated transition slots for a
clear traveling mass cycle and the longer final slot to plant weight. Preserve
the face and identity while approved cloth, appendages, or props follow by a
logical beat. Mirror only when asymmetric identity and handedness remain
correct.

### `waving`

Map to greeting or a polite request for attention: notice, extend,
acknowledge, return. Four slots leave no room for filler. The gesture does not
need to be a literal hand wave when another approved mechanism is more
characteristic.

### `jumping`

Map the five slots to anticipation, launch, peak, descent, and settled landing.
The silhouette must visibly unload or leave its baseline. Do not make the
motion generically springy when the approved material suggests another
response.

### `failed`

Map to recognition and deflation rather than eight equal shakes. Hold the read
through close initial drawings, concentrate recoil or collapse in the middle,
and use the final slot for a dignified settled disappointment.

### `waiting`

Map to expectant attention toward the user. Use a restrained
ask/check/hesitate sequence and end in patient stillness. Differentiate it from
Idle through intention, placement, silhouette, or repeated checking, not only
larger breathing.

### `running`

Map to active processing or task work, not directional locomotion. A compact
purposeful cycle may show curiosity, inspection, manipulation, pacing, or
internal mechanism activity. The final slot confirms or resets the task beat.

### `review`

Map to focused inspection of completed output. Move attention through distinct
checkpoints, then use the final slot for a conclusion or measured settle.

## Fixed-slot acting strategy

- **Visual hold** — keep the main mass and focal feature nearly unchanged
  across adjacent slots; move only a blink, edge settle, or micro-shift.
- **Short transition** — make one clear directional difference between
  neighboring slots instead of distributing weak movement everywhere.
- **Anticipation** — compress or counter-move before the accent while keeping
  the anchor and center of mass legible.
- **Accent** — reserve the largest silhouette or deformation difference for
  the state-defining pose.
- **Follow-through** — let approved cloth, appendages, or props lag one logical
  slot behind the lead mass.
- **Final settle** — use the longer final slot for a stable landing,
  acknowledgment, conclusion, or clean seam.

Repeated or near-repeated drawings are valid and often necessary. Review the
first slot, accent, final settle, seam, and complete current cadence at the
target's minimum, representative, and maximum display sizes.

## Look directions

Use one cohesive clockwise 16-pose loop. Direction may be expressed through
eyes, face, head, body surface, fold, appendage, or another approved aiming
feature. Cardinals must be unmistakable and adjacent directions coherent.

Do not rotate the entire sprite merely to fake gaze unless whole-object
rotation is part of the approved mechanism system.

## Staging package

Stage the validated result under `build/pet`:

```text
build/pet/
├── pet.json
└── spritesheet.webp
```

Minimum manifest:

```json
{
  "id": "example-pet",
  "displayName": "Example Pet",
  "description": "A concise description.",
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp"
}
```

Used cells contain one complete readable sprite. Unused cells are fully
transparent.

## Responsibility boundary

Pet Studio owns:

- inspiration and privacy intake;
- target-neutral creative decisions and durable approvals;
- Identity Lock, mechanism, Behavior Intent, and Motion Language;
- Candidate and Take review;
- Codex Pet v2 state mapping and production grounding;
- project staging, public export, and installation authorization.

`$hatch-pet` owns:

- supported production visual jobs and repair units;
- row geometry and deterministic atlas assembly;
- look-direction registration and semantic QA;
- contact sheets and motion previews;
- chroma, v2 validation, and final production evidence.

Do not synthesize missing production rows or unsupported final cells to bypass
the compiler contract.

## Preserve approved visuals

Pass every explicitly approved Keyframe or Take to production as a named
grounding asset. Preserve its identity, feature relationships, and requested
details.

If the current compiler requires coherent row generation and cannot guarantee
bit-identical preservation:

1. keep the exact approved asset;
2. explain the row-level constraint before generation;
3. use the asset as authoritative grounding;
4. compare the produced row against it;
5. return to user review when a material visual detail changes.

Never silently replace an approved visual with a similar regeneration.

## Target QA

Require:

- correct manifest and atlas dimensions;
- correct row, used-cell, and direction mapping;
- non-empty used cells and transparent unused cells;
- clean transparency with no clipping or overlap;
- exact fixed cadence in Previewer review;
- stable identity at the target's minimum, representative, and maximum display
  sizes;
- readable state contrast and physically caused follow-through;
- no visible loop reset or return-to-Idle pop;
- packaged assets matching approved Previewer evidence;
- passing project validation and privacy checks.

Use `$hatch-pet` for authoritative row, direction, atlas, chroma, and visual
QA.

## Package, export, install, and publish

Treat these as separate operations:

1. **Produce** — create and validate atlas evidence.
2. **Stage** — write the manifest and atlas under `build/pet`.
3. **Export** — create an allowlisted share artifact.
4. **Install** — copy a validated stage to an explicit Codex pet destination.
5. **Publish** — send an authorized artifact to an external destination.

Do not let production write to a live Codex pets directory when the user asked
only to validate, package, or export. If installed compiler instructions
include a live copy step, stop before it and stage the validated files in the
project. Run installation only after an explicit conversational request.
