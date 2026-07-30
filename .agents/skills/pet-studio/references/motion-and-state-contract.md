# Motion Language

## Contents

- Purpose and boundary
- Shared mechanism model
- Global Motion Language
- Behavior beats
- Target sampling handoff
- High-precision animation
- Review questions

## Purpose and boundary

Use this reference to define how the character moves before sampling that
movement into a runtime.

Motion Language is Studio Core truth. It should survive a change of Delivery
Target. Frame counts, durations, display sizes, state IDs, look mechanics, and
package lifecycle belong to a target-specific reference.

For the current target, read
[codex-pet-v2.md](codex-pet-v2.md)
after defining the Motion Language.

## Shared mechanism model

Animate every state from the same approved element system. A variable element
may have:

- `position` — bounded local or global movement;
- `rotation` — movement around an approved pivot;
- `scale` — controlled compression or extension;
- `deformation` — named modes rather than arbitrary redraws;
- `visibility` — hidden, emerging, visible, or retracting;
- `layer` — approved front and behind relationships;
- `attachment` — a fixed anchor or bounded sliding anchor.

Plan creative ranges in normalized terms. Target-specific pixel geometry
belongs to the selected compiler.

## Global Motion Language

Define these once:

- **lead element** — initiates an action;
- **follow elements** — respond with a meaningful delay;
- **settle order** — the order in which mass, cloth, limbs, face, or detail
  returns to rest;
- **material response** — how the approved material bends, compresses, drags,
  rebounds, or resists;
- **weight** — where mass appears to collect and how it transfers;
- **friction** — how easily the form starts, stops, slides, or plants;
- **overshoot limit** — the largest valid excess before identity breaks;
- **stillness budget** — deliberate quiet within an action;
- **visual hold** — a sustained pose that lets intention read;
- **loop seam** — the resting or continuing moment where repetition is
  believable.

Secondary motion must have a cause. If every element moves independently, the
pet reads as noise rather than a physical character.

## Behavior beats

Define Behavior Intents without assuming a target state ID. Useful semantic
beats include:

1. `rest`
2. `notice`
3. `anticipation`
4. `action`
5. `accent`
6. `follow-through`
7. `settle`
8. `continue` or `return`

Not every intent needs every beat. A quiet check may be `rest -> notice ->
settle`; a jump may need the full anticipation-to-landing arc.

For each intent, record:

- what the character wants or notices;
- which element leads;
- how the center of mass responds;
- which mechanisms activate;
- the strongest silhouette moment;
- what remains quiet;
- how the material follows and settles;
- whether the action returns, loops, or holds.

## Target sampling handoff

After the acting works in stills and semantic beats:

1. select the supported Delivery Target;
2. map the Behavior Intent to required runtime state IDs;
3. inspect its frame slots, cadence, lifecycle, display range, and mechanics;
4. assign beats to available slots;
5. decide which slots create holds, transitions, accents, and settle;
6. review target playback and repair only the affected mapping or sample.

Target sampling may use repeated or nearly repeated drawings. It may
concentrate a transition into fewer slots or hold an approved pose longer. It
must not invent unsupported timing fields or silently redraw canonical art.

## High-precision animation

Maximum precision means that every sampled difference serves intention and
physical continuity. It does not mean maximizing motion or making every frame
unique.

- Keep anchors stable unless moving them communicates the action.
- Use non-linear differences between adjacent samples.
- Concentrate the strongest shape change at the semantic accent.
- Let follow elements lag by one logical beat.
- Preserve the approved center of mass and attachment logic.
- Use near-repeats when the target needs a visual hold.
- Give the target's longest or final hold a stable, intentional drawing.
- Make the first sample work as a reduced-motion still when the target may
  pause there.
- Design the seam as part of the action rather than accepting a visible reset.
- Judge motion at the target's minimum, representative, and maximum display
  sizes.

## Review questions

- Does the action still read without labels?
- Is the lead/follow relationship physically caused?
- Does the material remain itself throughout deformation?
- Is the accent concentrated enough to be legible?
- Does stillness support the character rather than look unfinished?
- Are neighboring Behavior Intents different in intention, focal location,
  silhouette, or rhythm?
- Did target sampling preserve the approved Identity Lock?
- Does the result settle, continue, or return without an accidental pop?
