# Design gates

## Gate format

Every gate should end with a compact decision record:

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
- D2 — ...
Evidence:
- user feedback or visual observation
Next question:
- ...
```

Use the user's language for decision records. Keep the gate ID and stable option IDs in English.

## Approval vocabulary

- `open` — exploration has not started or is incomplete
- `candidate` — viable proposal, not yet selected
- `approved` — explicitly selected and safe to build upon
- `superseded` — replaced by a newer approved decision
- `blocked` — cannot proceed without a material choice or missing input

Never treat "better" or "interesting" as final approval when the user is still comparing.

## Gate 1: inspiration

Confirm:

- the emotional and aesthetic attraction
- what is source-specific versus transferable
- intended abstraction level
- privacy status

Do not force a species, object category, or narrative too early.

## Gate 2: creative genome

Keep the genome short enough to remember while drawing. Each rule should rule something out.

Strong:

- "The face emerges from the same opening as the short limbs."
- "Affection is requested through approach–pause–return, not constant waving."
- "The body reads as folded material before it reads as anatomy."

Weak:

- "Cute."
- "Dynamic."
- "Unique."

Anti-goals are equally important. Record rejected readings such as human-like posture, generic mascot roundness, excessive bounce, detached limbs, or a silhouette that resembles an unrelated object.

## Gate 3: default form

Judge the design in this order:

1. silhouette
2. mass and weight
3. primary feature relationship
4. face placement
5. small identity marks

Do not polish surface detail to rescue a weak silhouette.

Recommended first board:

- three to six variants
- same scale and background
- no state acting
- one intended rest pose

## Gate 4: variable mechanics

Recommended boards:

- element range board
- emergence/anchor board
- layering/occlusion board
- extreme-but-valid board

Show the neutral position, two useful variations, and one invalid extreme when the boundary is hard to explain.

## Gate 5: state set

Evaluate contrast on four axes:

| Axis | Question |
| --- | --- |
| Intention | Does the state want something different? |
| Location | Does the focal feature occupy a meaningfully different area? |
| Silhouette | Is the pose recognizable without interior detail? |
| Rhythm | Does its timing differ for a reason? |

Subtle motion is acceptable. Identical composition across most states is not.

## Gate 6: motion

Review:

- first frame
- strongest keyframe
- loop seam
- normal-speed playback
- reduced-motion readability

Avoid choosing solely from slow motion. Motion that looks elegant frame-by-frame may feel noisy at runtime.

## Gate 7: production

Creative approval freezes identity, not every pixel. Production may make small registration, spacing, transparency, and continuity repairs without reopening the design.

Any repair that changes silhouette, feature relationship, state meaning, or motion language returns to the relevant creative gate.

## Gate 8: release

Confirm:

- the selected production version passed all required QA
- only allowlisted files are exported
- privacy and rights records are complete
- install or publication target is explicit
- remaining warnings are visible to the user

Installation success and publication success are separate claims. Report only the action that was actually verified.
