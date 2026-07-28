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
- **easing** — sharp, elastic, viscous, cloth-like, mechanical, or restrained
- **overshoot limit** — maximum readable excess before identity deforms
- **stillness budget** — deliberate quiet time within a loop
- **loop seam** — where motion can repeat without a visible reset

Secondary motion should have a cause. If every element oscillates independently, the pet reads as noise.

## V2 standard states

The current Codex v2 pack uses 192×208 cells in an 8-column × 11-row atlas. The final atlas is 1536×2288.

| Row | Stable state ID | Used cells | Default timing |
| ---: | --- | ---: | --- |
| 0 | `idle` | 6 | 280, 110, 110, 140, 140, 320 ms |
| 1 | `running-right` | 8 | 120 ms each, final 220 ms |
| 2 | `running-left` | 8 | 120 ms each, final 220 ms |
| 3 | `waving` | 4 | 140 ms each, final 280 ms |
| 4 | `jumping` | 5 | 140 ms each, final 280 ms |
| 5 | `failed` | 8 | 140 ms each, final 240 ms |
| 6 | `waiting` | 6 | 150 ms each, final 260 ms |
| 7 | `running` | 6 | 120 ms each, final 220 ms |
| 8 | `review` | 6 | 150 ms each, final 280 ms |
| 9 | `look-directions-a` | 8 | 000° through 157.5° clockwise |
| 10 | `look-directions-b` | 8 | 180° through 337.5° clockwise |

Treat these as the installed `$hatch-pet` contract. Re-read that skill before production because the upstream contract can change.

The atlas dimensions, row order, and used-cell counts belong to the v2 package contract. The timing values above are the current `$hatch-pet` and desktop-runtime defaults, not custom fields in `pet.json`. The package has no per-frame duration setting and no documented 5000 ms state or frame ceiling. Previewer timing edits are design and QA metadata; they help evaluate rhythm but do not change the installed client runtime.

## State intentions

### `idle`

Quiet presence with the lowest visual noise. It should preserve attention for the user's work. Use subtle breathing, blink, fold settling, or a restrained emergence. The first frame must also work as a reduced-motion still.

### `running-right` and `running-left`

Screen-directional locomotion. Preserve the character's face and identity while letting body mass, fabric, appendages, or props show physical lag. Mirror only when handedness and asymmetric identity remain correct.

### `waving`

A readable greeting or request for attention: notice, extend, acknowledge, and return. The gesture need not be a literal hand wave when another approved mechanism is more characteristic.

### `jumping`

Anticipation, launch, peak, descent, and settle. The silhouette must leave or clearly unload its baseline. Avoid universal springiness when the character's material suggests another motion.

### `failed`

A concise deflation, error, or disappointment. Preserve dignity and identity. Avoid detached decorative effects as a substitute for acting.

### `waiting`

Expectant attention directed toward the user. It should feel different from idle through intention, placement, or repeated checking—not merely faster breathing.

### `running`

Active processing or task work, not literal left/right locomotion. Use curiosity, inspection, manipulation, pacing, or internal mechanism activity.

### `review`

Focused inspection of completed output. Show attention moving through something, a measured check, and a conclusion or settle.

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

"Maximum precision" means using the available cells to describe physically meaningful transitions, not maximizing motion per frame.

- Keep anchors stable unless their movement communicates intention.
- Use small non-linear differences between adjacent frames.
- Let secondary elements lag by one logical beat.
- Reserve the strongest shape change for the accent frame.
- Spend enough time in rest and settle frames to avoid constant agitation.
- Review at normal size and actual timing.
