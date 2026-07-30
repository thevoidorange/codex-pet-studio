# Codex Pet Studio — Agent Instructions

## Mission and workflow authority

Help the user turn personal inspiration into a distinctive, validated Codex pet
through focused review and reversible decisions. This is a durable co-design
workspace, not a one-shot generator.

Keep three authority scopes separate:

- **Creative truth:** current user steering, private approvals, and exact evidence.
- **Conduct and method:** this file for rules and `$pet-studio` for workflow.
- **Target truth:** installed `$hatch-pet`; checked-in target docs are a dated
  snapshot.

Read [the product model](docs/product-model.md) for roles and target boundaries.
Codex Pet v2 is the only supported Delivery Target.

## Re-enter before acting

Do not mistake a new Codex task for a new project. Before changing files:

1. confirm the root, branch, and dirty worktree;
2. inspect `pet-studio.json`, populated `design/`, Candidates, Takes, `build/`, unresolved QA, and any focused Previewer URL;
3. summarize `Locked`, `Open`, `Current Focus`, and `Next`;
4. resume by the shortest truthful route.

For a true cold start, run idempotent initialization and readiness checks,
classify inspiration as private, populate only the inspiration brief, and stop
for alignment before visual generation.

## Route by user intent

Use `$pet-studio` and its references to route work:

- new inspiration: begin with inspiration understanding;
- existing character: resume at the first unresolved creative decision;
- one focused Keyframe or Take: use the additive single-frame Take workflow;
- existing pack repair: validate first and repair only the affected unit;
- preview, validation, packaging, export, or explicit installation: perform it
  without restarting ideation;
- repository maintenance: work directly without manufacturing creative gates.

Creative gates apply only to new or reopened creative decisions. Adjacent
gates may be combined when the user wants, but unresolved dependencies remain
open.

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

Do not commit personal inspiration, names, home imagery, anecdotes,
credentials, machine paths, metadata, personal skills, or private UI kits.
Public examples must be neutral project-owned fixtures with reviewed rights.

Before commit, export, or publication, run the privacy check and inspect staged
paths, visuals, and metadata. External upload or publication requires explicit
permission.

## Language and repository conventions

Collaborate in the user's language. Keep public docs, filenames, IDs, schema
keys, code, and reusable artifacts in natural English.

Use **Candidate** for a coherent proposal, **Keyframe** for a reviewed target
sample, and **Take** for an additive one-frame alternative. `versions` is a
legacy Previewer data field, not user-facing terminology.

Author every UI locale natively from shared facts; do not translate sentence by
sentence. Review each locale in the rendered interface.

## Verification and truthful status

Run proportionate checks. Separate character, motion, target, pack, Previewer,
privacy, and rights QA. Automated success does not overrule a visible
regression.

Report `generated`, `reviewed`, `approved`, `validated`, `packaged`,
`exported`, `installed`, and `published` as distinct outcomes. Claim only the
statuses verified for the exact artifact.

Installation and publication always require explicit user requests.

## Standard project commands

Prefer the checked-in dependency-free tool:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py doctor
python3 .agents/skills/pet-studio/scripts/studio.py preview
python3 .agents/skills/pet-studio/scripts/studio.py privacy-check
python3 -m unittest discover -s tests -v
```

Use `studio.py --help` for validation, Take registration, export, and explicit-destination installation.
