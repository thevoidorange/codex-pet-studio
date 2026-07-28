---
name: pet-studio
description: Co-design a Codex desktop pet from personal inspirations through staged visual decisions, motion mechanics, state animation, preview, QA, and Codex v2 packaging. Use when a user wants to create, refine, compare, validate, export, or install a Codex pet without jumping directly from references to a finished sprite atlas.
---

# Pet Studio

Turn inspiration into a production-ready Codex pet through a paced creative partnership. Preserve the user's taste and the character's behavioral truth while making every approved decision reproducible, previewable, and technically valid.

## Non-negotiable behavior

- Speak and write project-facing decision notes in the user's language unless the user requests another language.
- Keep repository filenames, IDs, schema keys, code, comments, and reusable templates in English.
- Treat reference files as private inputs by default. Never commit, publish, or copy them into a public example.
- Do not generate a complete pet pack at the beginning. Move through approval gates and ask for visual alignment at the smallest useful scope.
- Preserve the latest approved work before exploring a new direction. Create a new version instead of silently overwriting it.
- Separate creative approval from technical validity. Passing atlas validation does not mean the character feels right; liking a still does not mean the pack is valid.
- Use the installed `$hatch-pet` skill as the production compiler after the creative gates are approved. Do not duplicate or bypass its atlas, direction, QA, packaging, or installation contract.

## Start from the user's actual request

If the user provides only inspiration, begin by observing and discussing it. Do not generate images yet.

If the user already has an approved character, inspect the existing project state and resume at the first unfinished gate. Do not restart ideation.

If the user asks only to preview, validate, export, or install an existing pack, use the matching deterministic tool path and avoid reopening creative decisions.

Read [workflow.md](references/workflow.md) for the complete routing rules and required artifacts.

## The eight gates

1. **Inspiration understanding** — identify what the user responds to, what belongs to the subject, and what must not be copied literally.
2. **Creative genome** — lock a short list of identity rules, personality evidence, aesthetic constraints, and explicit anti-goals.
3. **Default form** — approve one neutral silhouette at normal desktop-pet size before designing states.
4. **Variable mechanics** — define the few elements that can move, deform, appear, disappear, or change layer.
5. **State choreography** — design each runtime state as a distinct intention, spatial composition, and motion arc.
6. **Motion language and preview** — approve fixed-slot pose spacing, material easing, weight, continuity, and versioned playback in the Previewer.
7. **Production and QA** — hand the approved design to `$hatch-pet`, then run semantic, visual, technical, privacy, and packaging gates.
8. **Release** — export, install, or publish only the selected, allowlisted, reviewed result.

Never combine gates merely to save time when the next gate depends on an unresolved visual choice. It is fine to combine adjacent gates when the user explicitly approves the shared decision.

Read [design-gates.md](references/design-gates.md) before proposing visual rounds.

## Work in small visual questions

Generate a board only when it answers one concrete question. Good examples:

- Which default silhouette best preserves the creative genome?
- How far may the face travel without changing identity?
- Which fold mechanism reads as clothing rather than a cut or a separate object?
- How should a short limb emerge from the same opening as the face?
- Which waiting pose feels polite rather than generic?

For each board:

1. State the single decision being tested.
2. Hold all already-approved features constant.
3. Vary only the necessary mechanism.
4. Label options with stable neutral IDs.
5. Show them at or near normal pet size when readability matters.
6. Record the user's selection, rejection reasons, and immutable details.

Use `$imagegen` for image generation or editing. Attach only the references needed for the current decision. Do not ask image generation to redesign approved anatomy, proportions, or mechanics unless the user requests that change.

## Define mechanisms before states

Create a compact mechanism inventory. For each variable element, record:

- anchor or emergence point
- allowed translation, rotation, deformation, visibility, and layer changes
- range limits
- relationship to neighboring elements
- forbidden readings
- rest behavior

Keep the inventory small. A pet with three well-defined mechanisms is easier to animate consistently than one with twelve vague ones.

Then assemble states from those shared mechanisms. Do not independently redesign the pet inside every state.

Read [motion-and-state-contract.md](references/motion-and-state-contract.md) before building state keyframes or production rows.

## Design for immutable client time slots

The current v2 client, not the pet package, owns playback timing. `pet.json` has no fields for frame duration, action-loop count, Idle slowdown, or display size. Under the current client snapshot:

- standard rows use fixed frame counts and fixed duration arrays;
- every non-Idle action plays three loops, then returns to Idle;
- Idle uses six times its listed base durations;
- display size is a client setting from 80 to 224 px.

Treat this as a current-client snapshot that can change. Re-read the installed `$hatch-pet` skill before production and prefer its newer contract if it differs.

Do not invent a timing editor or promise that Previewer JSON changes runtime cadence. Control perceived easing through pose spacing and material deformation:

- keep neighboring poses close during a visual hold;
- spend short transition slots on clear directional change;
- place the strongest deformation at the accent;
- use the final long slot for a clean settle or loop seam;
- let secondary material lag by one slot only when that lag remains readable.

Review at 80, 144, and 224 px so the same fixed sequence works across the client size range.

Use both Previewer playback views for different questions:

- **Runtime Simulation** verifies the real state lifecycle: three action loops, then the slowed Idle row.
- **Endless Loop** uses the exact same fixed per-frame durations but repeats the selected row indefinitely, making loop seams, pose spacing, weight transfer, and material follow-through easier to inspect.

Neither mode plays an exported GIF. Both render the source atlas directly so GIF palette and edge artifacts cannot be mistaken for sprite defects.

## Preserve personality through behavior

Translate personality evidence into observable behavior, not decorative symbols. A state must communicate:

- **intention** — what the pet wants now
- **approach** — how it asks, investigates, works, recovers, or celebrates
- **space** — where the face/body/mechanism moves within the silhouette
- **weight** — what leads, lags, settles, or overshoots
- **return** — how the pet gets back to a reusable loop or rest pose

Favor a few meaningful physical details over excessive bounce. Secondary motion should follow the main action with plausible lag and damping.

## Version rather than overwrite

Use monotonically increasing version IDs such as `v001`, `v002`, and `v003`. A version represents a coherent reviewable proposal, not every saved file.

Before a material revision:

- preserve the current approved or candidate version
- write what changes and what stays locked
- keep stable state and element IDs
- compare the new version in the Previewer

The Previewer language and version selectors must not reset the current state, frame, mode, or playback when the selected version supports them.

Use single-frame Takes only for a narrow visual choice inside one Candidate.
Manage private working assets under
`design/takes/<candidate>/<state>/fNN/`, expose only the review Takes needed by
Previewer config, and keep Take selection temporary. Never treat a Take click
as approval or writeback. If the new frame has a continuity problem, generate
another Take for that requested frame; do not silently revise either adjacent
frame.

## Use deterministic project tools

Run commands from the repository root:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py init
python3 .agents/skills/pet-studio/scripts/studio.py doctor
python3 .agents/skills/pet-studio/scripts/studio.py preview
python3 .agents/skills/pet-studio/scripts/studio.py validate --pet-dir <pack-directory>
python3 .agents/skills/pet-studio/scripts/studio.py privacy-check
```

`init` is idempotent: in a cloned template it preserves `pet-studio.json` and creates only the missing local private workspace. In a blank directory it also creates the public project configuration.

Use `--help` for the exact optional arguments supported by the checked-in version. Prefer these scripts over one-off replacements so that the same checks run for every contributor.

## Production handoff

Invoke `$hatch-pet` only when all of these are true:

- the default form is explicitly approved
- variable mechanics and their limits are recorded
- all nine standard state intentions are defined
- representative keyframes and their mapping to the fixed row slots are approved
- the user has selected the version to produce
- reference privacy and publication scope are clear

If `$hatch-pet` is not available, continue only through the creative and Previewer gates. Ask Codex to enable or install the official skill before production; do not improvise a replacement production pipeline.

Pass `$hatch-pet` the approved canonical reference, state choreography, motion bible, locked identity rules, anti-goals, and version ID. Its v2 contract is summarized in [codex-pet-v2.md](references/codex-pet-v2.md), but its installed instructions are authoritative.

## QA and delivery

Do not claim completion until all applicable gates pass:

- identity and design-lock review
- state-semantic review
- motion and loop review
- direction review
- atlas/package validation
- privacy check
- normal-size Previewer review

Read [qa.md](references/qa.md) and [privacy.md](references/privacy.md). Report failures and warnings separately. Do not convert a warning into a pass by omission.

Deliver:

- the selected version and decision summary
- a Previewer path or URL
- validated pack files when production is complete
- remaining warnings
- the exact next useful step

Do not install or publish unless the user asks for it or the current request clearly includes installation or publication.
