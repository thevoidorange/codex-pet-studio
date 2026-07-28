# Workflow and routing

## Core principle

The studio is a conversation with durable artifacts. Each phase should reduce a specific uncertainty. Do not use image volume as a substitute for a clear decision.

## Resume before creating

When a project exists:

1. Read `pet-studio.json`.
2. Read the latest private project notes under `design/`, when present.
3. Inspect the selected version and any unresolved warnings.
4. Tell the user what is locked, what remains open, and the next smallest useful decision.

Do not reinterpret an approved choice from an older chat summary when current project files disagree.

## Preflight: intake and privacy

Preflight is required but is not an approval gate. It establishes safe inputs before Gate 1.

Collect only what the user volunteers:

- inspiration images, sketches, photographs, or written ideas
- desired relationship to a real animal, object, place, or brand
- intended emotional tone
- any strong dislikes or anti-goals
- whether references may be committed or must remain local

Default all inputs to local-only. Record source roles without exposing absolute paths in publishable files.

Output:

- an input inventory with neutral IDs
- privacy classification for each input
- a one-paragraph interpretation in the user's language

## Gate 1: inspiration understanding

Separate observations into four layers:

1. **Subject truth** — behavior, posture, rhythm, material, or personality grounded in the source.
2. **Taste signal** — what the user likes about abstraction, proportion, line, weight, restraint, or humor.
3. **Transferable principle** — a rule that can shape a new character without copying the source.
4. **Literal detail** — a feature that should not automatically be reproduced.

Ask for correction when one interpretation would materially change the direction. Otherwise, offer a concise working reading and continue.

Gate: the user agrees that the interpretation captures the intended attraction.

## Gate 2: creative genome

Create:

- three to seven identity rules
- three to seven behavioral truths
- three to seven visual constraints
- explicit anti-goals
- a short "this is / this is not" statement

Avoid personality adjectives without behavioral evidence. Replace "friendly" with an observable pattern such as "approaches, pauses, asks, then returns if ignored."

Gate: the user can recognize the intended character without seeing a finished design.

## Gate 3: default-form lock

Explore only the default neutral form. Hold color and rendering treatment stable unless those are the decision under review.

Evaluate:

- silhouette at normal pet size
- center of gravity and visual weight
- relationship between primary masses
- minimum identity cues
- negative space
- which details survive downscaling
- whether the form invites the intended motion system

Create small boards with stable option IDs. Record both the selected option and why alternatives failed.

Gate: one canonical default form is explicitly selected.

## Gate 4: variable mechanics

Define a small parameter system from the canonical form. Use `templates/mechanism-board.md`.

For every mechanism, distinguish:

- fixed identity rule
- permitted range
- state-dependent use
- physically impossible or visually misleading use

Use mechanism boards to test one relationship at a time. Examples include opening geometry, face travel, fold depth, limb emergence, drawstring behavior, or temporary appendage visibility.

Gate: the user understands what can move and still remain the same character.

## Gate 5: state choreography

Design the nine standard runtime states as different intentions rather than cosmetic variants. Start with state briefs and representative keyframes. Do not produce atlas rows yet.

For each state, record:

- purpose
- starting composition
- action beats
- most readable keyframe
- secondary motion
- settle or loop seam
- contrast from neighboring states

Gate: the state set has enough semantic and spatial contrast without breaking the identity.

## Gate 6: motion language and versions

Define global motion rules:

- tempo range
- easing character
- squash/stretch limits
- overshoot and damping
- lead and follow hierarchy
- stillness budget
- loop philosophy
- reduced-motion first-frame behavior

Then define state-specific timing. Preview at normal size and at intended playback speed.

Gate: the user approves the feel, not just isolated frames.

## Gate 7: production and QA

Use the installed `$hatch-pet` skill. Provide it with approved inputs, not the entire exploratory history.

Handoff bundle:

- canonical reference
- creative genome
- anti-goals
- mechanism inventory
- state choreography
- motion bible
- selected version ID
- privacy classification

`$hatch-pet` owns image generation for production rows, deterministic atlas assembly, direction rows, technical validation, visual QA, packaging, and installation staging.

## Gate 8: release

Run:

- repository tests
- pack validation
- privacy check
- Previewer review
- clean-room onboarding test

Publish only allowlisted artifacts. Treat Git history as part of the public surface.

## Scope shortcuts

Use the shortest route that preserves truth:

- **Existing valid pack, preview only:** skip creative phases and open the Previewer.
- **Existing approved art, animate it:** confirm the design lock, then start at variable mechanics.
- **Existing animation rows, package only:** validate contract and privacy, then invoke the relevant `$hatch-pet` assembly path.
- **Repair one state:** preserve the current version, diagnose the smallest failing row, and repair only that row.
- **Change the identity:** create a new creative version and return to default-form lock.
