# Motion and state contract

## Shared mechanism model

Animate states from the same approved elements. Each element may have:

- `position`: bounded x/y movement
- `rotation`: local angular movement
- `scale`: small controlled compression or extension
- `deformation`: named shape modes rather than arbitrary redraws
- `visibility`: hidden, emerging, visible, retracting
- `layer`: approved front/behind relationships
- `attachment`: fixed anchor or bounded sliding anchor

Use normalized creative ranges in planning documents. Production pixel geometry belongs to `$hatch-pet`.

## Global motion language

Define these once:

- **lead element** — initiates motion
- **follow elements** — respond with delay
- **settle order** — returns from large mass to small detail, or the reverse
- **material easing** — how pose spacing and deformation make the fixed slots feel sharp, elastic, viscous, cloth-like, mechanical, or restrained
- **overshoot limit** — maximum readable excess before identity deforms
- **stillness budget** — deliberate quiet time within a loop
- **loop seam** — where motion can repeat without a visible reset

Secondary motion should have a cause. If every element oscillates independently, the pet reads as noise.

## Current v2 client playback snapshot

The current Codex v2 pack uses 192×208 cells in an 8-column × 11-row atlas. The final atlas is 1536×2288.

This snapshot was verified against Codex Desktop `26.721.41059` (build `5848`) on 2026-07-28. Treat the version and date as provenance, not as a promise that future clients remain identical.

| Row | Stable state ID | Used cells | Current client base durations |
| ---: | --- | ---: | --- |
| 0 | `idle` | 6 | 280, 110, 110, 140, 140, 320 ms |
| 1 | `running-right` | 8 | 120, 120, 120, 120, 120, 120, 120, 220 ms |
| 2 | `running-left` | 8 | 120, 120, 120, 120, 120, 120, 120, 220 ms |
| 3 | `waving` | 4 | 140, 140, 140, 280 ms |
| 4 | `jumping` | 5 | 140, 140, 140, 140, 280 ms |
| 5 | `failed` | 8 | 140, 140, 140, 140, 140, 140, 140, 240 ms |
| 6 | `waiting` | 6 | 150, 150, 150, 150, 150, 260 ms |
| 7 | `running` | 6 | 120, 120, 120, 120, 120, 220 ms |
| 8 | `review` | 6 | 150, 150, 150, 150, 150, 280 ms |
| 9 | `look-directions-a` | 8 | 000° through 157.5° clockwise |
| 10 | `look-directions-b` | 8 | 180° through 337.5° clockwise |

For the current client:

- each non-Idle action row plays three complete loops, then returns to Idle;
- Idle plays with each row-0 base duration multiplied by six;
- the package carries no per-frame duration, action-loop, Idle-multiplier, or display-size field;
- display size is a client setting from 80 to 224 px.

These are verified current-client facts, not a permanent public API. Re-read the installed `$hatch-pet` skill before production and prefer newer authoritative instructions when they differ.

The Previewer exposes two atlas-based readings of these same immutable slots:

- **Runtime Simulation** plays three action loops and then returns to Idle at one-sixth speed.
- **Endless Loop** keeps the selected row repeating with the identical per-frame durations.

Use Runtime Simulation to validate the state lifecycle. Use Endless Loop to
inspect the loop seam and physical continuity. Do not substitute an exported
GIF for either view; GIF palette quantization and alpha thresholds are not part
of the Codex pet runtime.

## Designing motion without editable timing

The duration schedule is immutable from the pet package. Do not add timing controls to project JSON or imply that a Previewer can change the installed runtime. The animation's easing comes from what changes between the fixed slots.

- **Long visual hold:** keep the main mass and focal feature nearly unchanged across adjacent slots; let only a blink, edge settle, or material micro-shift move.
- **Short transition:** make one clear directional change between neighboring slots instead of distributing weak movement everywhere.
- **Anticipation:** compress or counter-move before the accent, while keeping the attachment and center of mass legible.
- **Accent:** reserve the largest silhouette or deformation difference for the state-defining pose.
- **Follow-through:** let cloth, appendages, or props lag one slot behind the lead mass.
- **Final settle:** use the longer final slot for a stable landing, acknowledgment, or seam that can return cleanly to frame 1.

Repeated or near-repeated drawings are valid and often necessary. They create a hold under fixed time without inventing extra motion. Judge the result at 80, 144, and 224 px.

## State intentions

### `idle`

Quiet presence with the lowest visual noise. Because the client multiplies the six base durations by six, avoid distributing large changes across the row. Keep most pose spacing tight, place one restrained breath/blink/fold change in the short middle slots, and use the 320 ms base final slot as the cleanest rest/seam. The first frame must also work as a reduced-motion still.

### `running-right` and `running-left`

Screen-directional locomotion. Use the seven 120 ms transition slots for a clear alternating gait or traveling mass cycle, then let the 220 ms final slot plant the weight. Preserve the character's face and identity while letting body mass, fabric, appendages, or props lag by a slot. Mirror only when handedness and asymmetric identity remain correct.

### `waving`

A readable greeting or request for attention: notice, extend, acknowledge, and return. With only four slots, do not spend one on filler: use a neutral/notice pose, a clear extension, an acknowledgment/accent, and a 280 ms returned settle. The gesture need not be a literal hand wave when another approved mechanism is more characteristic.

### `jumping`

Map the five slots directly to anticipation, launch, peak, descent, and the 280 ms settle. The silhouette must leave or clearly unload its baseline. Use pose spacing to accelerate into lift and decelerate into landing; avoid universal springiness when the character's material suggests another motion.

### `failed`

Use the eight slots for a readable recognition-to-deflation arc rather than eight equal shakes: hold the initial read briefly through close poses, concentrate collapse or recoil in a few middle transitions, then make the 240 ms final pose a dignified settled disappointment. Avoid detached decorative effects as a substitute for acting.

### `waiting`

Expectant attention directed toward the user. Use the five 150 ms slots for a restrained ask/check/hesitate pattern and the 260 ms final slot for waiting without agitation. It should differ from Idle through intention, placement, or repeated checking—not merely larger breathing.

### `running`

Active processing or task work, not literal left/right locomotion. Use the five 120 ms slots for a compact purposeful cycle—curiosity, inspection, manipulation, pacing, or internal mechanism activity—and let the 220 ms final slot confirm or reset the task beat.

### `review`

Focused inspection of completed output. Use the five 150 ms slots to move attention through distinct checkpoints, not a generic oscillation, and use the 280 ms final slot for the conclusion or measured settle.

### look directions

Use one cohesive clockwise 16-pose loop. Direction may be expressed by eyes, face, head, body surface, fold, appendage, or a natural aiming feature. Cardinals must be unmistakable. Do not rotate the whole sprite merely to fake gaze unless whole-object rotation is an approved identity mechanism.

## Keyframe planning

Before generating a row, define:

1. `rest`
2. `anticipation`
3. `action`
4. `accent`
5. `settle`

Not every state needs all five visible frames. Map the semantic beats onto the available cells without inventing filler poses.

## High-precision animation

"Maximum precision" means using the fixed cells to describe physically meaningful transitions, not maximizing motion per frame or inventing editable milliseconds.

- Keep anchors stable unless their movement communicates intention.
- Use small non-linear differences between adjacent frames.
- Let secondary elements lag by one logical beat.
- Reserve the strongest shape change for the accent frame.
- Use near-repeated poses to create visual holds where the fixed schedule needs stillness.
- Put a stable pose in the longer final slot so the loop can settle.
- Review at 80, 144, and 224 px at the current client cadence.
