# Codex Pet Studio — Agent Instructions

## Mission

Help the user create a distinctive Codex pet through collaborative design, versioned preview, rigorous QA, and final packaging.

The repository is a creative studio, not a one-shot asset generator. Preserve the user’s taste and approvals while doing the technical work autonomously.

Use the project-local `$pet-studio` skill for inspiration, ideation, mechanics, state, motion, preview, QA, packaging, and installation requests.

## First response in a new project

1. Inspect the repository and any inspiration the user has supplied.
2. Summarize what appears important in plain language.
3. Separate observations from interpretation.
4. Ask only the questions that materially affect the first design direction.
5. Propose the next small reviewable artifact.

Do not begin by generating every state or packaging a pet.

## Language boundary

- Collaborate in the user’s preferred language.
- Keep canonical filenames, state IDs, version IDs, and reusable internal artifacts in English.
- The Previewer may be bilingual, pairing stable English identifiers with Chinese labels.
- Do not translate or rename technical identifiers differently across versions.

## Required phase gates

Treat each phase as an explicit approval gate:

1. **Inspiration understanding**
2. **Creative genome**
3. **Default form and identity lock**
4. **Variable mechanics**
5. **State choreography and key poses**
6. **Motion language and version comparison**
7. **Production and QA**
8. **Release, optional installation, or publication**

At each gate:

- show the smallest artifact that can resolve the current uncertainty;
- explain what is fixed, what remains variable, and what decision is needed;
- record the user’s feedback precisely;
- do not treat silence or partial approval as a global lock;
- keep prior approved work available.

Loops are allowed. When a decision changes, identify the dependent phases that need review.

Keep private project artifacts under `design/`, using the matching English templates from `templates/`. `init` may scaffold all blank templates for convenience, but start by populating only `inspiration-brief.md`. Populate and treat the identity, mechanism, state, motion, QA, and attribution files as active only when their gate begins.

## Creative conduct

- Derive character rules from the user’s inspiration; do not merely trace it.
- Preserve asymmetry, restraint, oddness, or subtlety when those are deliberate.
- Avoid generic “cute pet” defaults unless the user asks for them.
- Judge states at real desktop scale, not only on large artboards.
- Distinguish states through intention, spatial composition, pose spacing, and physical response—not only eye direction or small limb changes.
- Use motion to express personality.
- Prefer a few strong, reviewable variations over a large undirected batch.

## Identity lock

Before broad state production, document:

- default silhouette and proportions;
- facial rules;
- fixed visual anchors;
- permitted deformations;
- forbidden substitutions;
- signature behaviors;
- desktop-scale readability constraints.

When refining one component, explicitly protect the other approved components. Do not allow a regeneration step to silently redesign the face, body, hands, or silhouette.

## Mechanism and state design

For each variable element, define:

- its neutral form;
- movement or deformation range;
- attachment and continuity rules;
- interaction with adjacent elements;
- conditions under which it may hide or appear;
- what it must never resemble.

For each state, define:

- behavioral intention;
- screen position and facing;
- key poses;
- anticipation, action, settle, and loop behavior;
- differences from neighboring states;
- transitions into and out of the state;
- how the required poses map onto the fixed frame slots and client durations.

Do not use maximal movement everywhere. Quiet states may be subtle, but they must still be legible and intentional.

## Current client playback snapshot

Treat runtime behavior as a current-client snapshot, not a permanent public API. Before production, re-read the installed `$hatch-pet` skill and update the project only when newer authoritative instructions disagree.

In the current v2 client:

- the nine standard animation rows have fixed used-cell counts and fixed per-cell durations;
- each non-Idle action plays three loops, then returns to Idle;
- Idle plays at six times the listed base durations;
- `pet.json` carries no frame-duration, loop-count, Idle-multiplier, or display-size fields;
- pet display size is a client setting from 80 to 224 px.

Do not promise that a Previewer value changes runtime timing. The creative control surface is the drawing inside the immutable slots: pose spacing, silhouette change, deformation, anticipation, follow-through, and which slot receives the visual hold. Prefer long visual holds, short readable transitions, and a settled final frame.

## Version rules

- Never overwrite the only approved version.
- Create a new version for material changes.
- Keep version IDs stable and sortable, such as `v001`, `v002`, and `v003`.
- Record a concise change note for each version.
- Use the Previewer version dropdown to compare like-for-like states.
- Promote only an explicitly approved version to packaging.

## Preview and QA

Preview work before claiming completion.

### Character QA

- silhouette remains recognizable;
- face and signature elements remain within the identity lock;
- no accidental anatomy or costume symbolism has appeared;
- no state looks like a different character.

### Motion QA

- state differences are visible at desktop scale;
- motion has continuity, weight, anticipation, and settling;
- loops do not pop at their seam;
- moving left and right preserve approved physical details;
- fixed-slot pose spacing feels intentional rather than uniformly bouncy;
- expressive elements do not drift away from their intended attachment points.

### Pack QA

- atlas dimensions and frame cells are correct;
- transparency is clean;
- no frame is clipped;
- state rows and direction cells map correctly;
- used-cell counts match the current client contract;
- motion was reviewed at the current fixed client cadence;
- previews match the packaged assets;
- installation is verified before reporting success.

If an automated check passes but the visual result is wrong, the work is not finished.

## `hatch-pet` boundary

Use the official `$hatch-pet` skill as the final compiler and validator after creative approval.

- Do not invoke it as a replacement for ideation, identity locking, or motion direction.
- Provide it with the approved design and state plan.
- Review its contact sheets, animation previews, and validation output.
- Return to the studio workflow if packaging introduces a visual regression.

## Privacy and network boundary

- Treat personal inspiration as private unless the user explicitly says otherwise.
- Do not commit personal photos or identifying metadata.
- Do not upload material to external services without explicit permission.
- Never request that an API key be pasted into repository files or chat.
- The core workflow must not depend on a hosted service, login, or separate API key.
- Redact local paths, usernames, and private anecdotes from public documentation and examples.

## Rights and publishing

Before publishing or accepting public example assets:

- confirm the contributor owns the work or has a compatible license;
- record the source and license;
- avoid unlicensed branded characters and derivative fan packs;
- preserve required attribution;
- obtain explicit permission before submitting to a third-party catalog.

Petdex and awesome-codex-pet may be mentioned as optional downstream destinations only. Do not imply affiliation, endorsement, or guaranteed acceptance.

## Repository hygiene

- Preserve user changes and unrelated work.
- Keep public repository documentation in English.
- Do not add secrets, personal inspiration, generated caches, or machine-specific paths.
- Prefer deterministic and inspectable outputs.
- Report actual verification status. A local write is not proof of successful packaging or installation.

## Deterministic project tools

Prefer the checked-in dependency-free CLI over one-off scripts:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py doctor
python3 .agents/skills/pet-studio/scripts/studio.py preview
python3 .agents/skills/pet-studio/scripts/studio.py privacy-check
```

Use `--help` for validate, export, and explicit-destination install options. Run the privacy gate before committing or exporting public material.
