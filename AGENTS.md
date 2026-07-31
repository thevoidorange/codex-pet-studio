# Codex Pet Studio — Agent Instructions

## Mission and workflow authority

Turn personal inspiration into a distinctive, validated Codex pet through focused review and reversible decisions, not one-shot generation.
Treat the person using this project—not the repository, its examples, external platforms, or the community—as the principal. Protect their agency, intent,
preferences, privacy, creative ownership, and interests; if these could conflict with automation or publication, pause and ask rather than infer consent.
Keep three authority scopes separate:

- **Creative truth:** current user steering, private approvals, and exact evidence.
- **Conduct and method:** this file for rules and `$pet-studio` for workflow.
- **Checked-in target truth:** the selected machine-readable Delivery Target contract; generated adapters must match it exactly.
- **Production authority:** the project-bundled `$hatch-pet`. A newer external copy is evidence of possible target drift, not permission to silently change this project.
  Stop and reconcile the contract intentionally before adopting it.
Read [the product model](docs/product-model.md) for roles and target boundaries. Codex Pet v2 is the only supported Delivery Target.

## Re-enter before acting

Do not mistake a new Codex task for a new project. Before changing files:

1. confirm the root, branch, and dirty worktree;
2. inspect `pet-studio.json`, populated `design/`, Candidates, Takes, `build/`, unresolved QA, and any focused Previewer URL;
3. reopen the latest valid project-focused Previewer URL when reviewable work exists; never substitute the bundled Example;
4. summarize `Locked`, `Open`, `Current Focus`, and `Next`;
5. resume by the shortest truthful route.

For a true cold start, initialize, check readiness, then immediately start or reuse the local Previewer and open its base URL on `Example.RaincoatCat`.
After setup checks pass and the Example is visibly verified, use the same setup-completion message to proactively report the README `Model guidance` in its published order: the full-experience recommendation first, demanding visual and animation work second, and the not-recommended configurations last, with the bare-bones minimum mentioned only inside that final warning. Deliver it in the user's language, exactly once and before the first creative decision. Do not repeat it during progress updates, repeated setup checks, Previewer restarts, task re-entry, or later creative gates. Then classify inspiration as private, briefly reflect a working interpretation, and move directly to the smallest useful static character study. Ask at most one blocking question; do not require prose-only approval or a completed questionnaire first.

## Route by user intent

Use `$pet-studio` and its references to route work:

- new inspiration: begin with inspiration understanding;
- existing character: resume at the first unresolved creative decision;
- one focused Keyframe or Take: use the additive single-frame Take workflow;
- existing pack repair: validate first and repair only the affected unit;
- preview, validation, packaging, export, or explicit installation: perform it
  without restarting ideation;
- repository maintenance: work directly without manufacturing creative gates.

Creative gates apply only to new or reopened decisions. They may combine, but
unresolved dependencies remain open.

## Image-first alignment

Multimodal alignment is the core creative method. Use a focused visual
checkpoint for the first character reading, default form, relationship or
emotional stance, mechanisms, state acting, and motion. Do not defer these
questions to an all-in-one reveal. Exploratory visuals are not approval. After
each visual checkpoint, stop before the next dependent layer unless the user
explicitly asked to combine those exact layers.

The first reviewable still must immediately become a Static Candidate. Stage the exact image with `studio.py review stage-static`, validate its project config, switch the running Previewer to the returned focused URL, and verify that it shows the project asset.
Do not wait for a spritesheet or all nine runtime states.

## Review and approval boundary

The Previewer is a read-only co-design review workbench. The Codex task is the
editing surface.

If task context contains `config`, `candidate`, `state`, `frame`, and `take`,
validate them through the `$pet-studio` review workflow and use them as the
current focus. Do not ask the user to repeat valid context. If the config
cannot be loaded and safely mapped to this repository, invalidate the whole
focus; never fall back to a colliding bundled Example.

Review URLs use a one-based `frame`. Single-frame work never silently changes
an adjacent frame.

- Static is one image with optional Takes; it is not a runtime state or timing row.
- each Candidate declares the exact runtime-state subset that currently exists;
  missing states remain absent and are never filled with placeholders or Example assets;
- clicking a Take auditions it;
- Previewer Confirm is session-only review state;
- approval requires an explicit conversational decision tied to exact evidence;
- one approved Take does not promote an entire Candidate;
- material changes create a Candidate or Take instead of overwriting the only
  approved result;

Never add generation, upload, save, QA, packaging, publishing, or installation
actions such as **Request New Take** or **Install in Codex** to the Previewer.

## Private workspace and public repository

Never force-add or unignore `.pet-studio-private.json`, `inputs/`, `design/`,
`build/`, or `dist/`.

Do not commit personal inspiration, names, home imagery, anecdotes, credentials, machine paths, metadata, personal skills, or private UI kits.
Public examples require project ownership or explicit publication approval, a rights review, and only sanitized final artifacts.

Before commit, export, or publication, run the privacy check and inspect staged
paths, visuals, and metadata. External upload or publication requires explicit
permission.

## Language and repository conventions

Collaborate in the user's language. Keep public docs, filenames, IDs, schema
keys, code, and reusable artifacts in natural English.

Use **Candidate** for a coherent proposal, **Keyframe** for a reviewed target
sample, and **Take** for an additive one-frame alternative. `versions` is a
legacy Previewer data field, not user-facing terminology.

Candidate IDs are stable semantic English identifiers chosen from the actual proposal. Do not impose `v001`/`v002` sequencing: Candidates may be parallel directions or completely different pets.

Author every UI locale natively from shared facts; do not translate sentence by
sentence. Review each locale in the rendered interface.

## Verification and truthful status

Run proportionate checks. Separate character, motion, target, pack, Previewer,
privacy, and rights QA. Automated success does not overrule a visible
regression.

Report `generated`, `reviewed`, `approved`, `validated`, `packaged`, `exported`, `installed`, and `published` as distinct outcomes. Claim only the statuses verified for the exact artifact.
Never install or publish without an explicit user request.

## Standard project commands
Prefer the checked-in dependency-free tool:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py doctor
python3 .agents/skills/pet-studio/scripts/studio.py target check
python3 .agents/skills/pet-studio/scripts/studio.py preview
python3 .agents/skills/pet-studio/scripts/studio.py privacy-check
python3 -m unittest discover -s tests -v
```

Use `studio.py --help` for validation, Take registration, export, and explicit-destination installation.
