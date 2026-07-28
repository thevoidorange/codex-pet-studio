# Codex Pet Studio

Codex Pet Studio is a Codex-native creative workflow for turning personal inspiration into a distinctive, technically valid Codex pet—without flattening the design process into one prompt.

> Open this repository in Codex, add or describe your inspiration, and say: **“Help me design a Codex pet from this inspiration, one approval gate at a time.”**

No hosted service, account, cloud backend, or separate OpenAI API key is required. The work happens in the repository and in your Codex conversation.

## Why this project exists

Making a good pet is not mainly a spritesheet problem. The difficult part is preserving a character while deciding:

- what must never change;
- which parts can move or transform;
- how states differ at desktop scale;
- how motion expresses personality rather than generic animation;
- when a visual direction is approved strongly enough to package.

Codex Pet Studio treats those decisions as a sequence of visible, reversible approvals. It is a creative studio first. Packaging comes last.

## Quick start

### Fastest: give the repository link to Codex

You do not need to clone the repository or use a terminal.

1. Start a new blank Codex task.
2. Paste:

   > I want to use this GitHub project to design my own Codex pet: https://github.com/thevoidorange/codex-pet-studio. I do not use Git or the terminal. Please set up the project for me and guide me through its recommended process one approval gate at a time. Start by asking for my inspiration; do not generate the full pack yet.

3. Give Codex your inspiration when it asks.

Codex should obtain the repository, read its project instructions, prepare a private local workspace, and begin with inspiration understanding. The repository must be public, or the user’s Codex environment must already have permission to access it.

### Manual setup

If you prefer to control the local checkout:

1. Create a repository from this project or clone it locally.
2. Open the repository as a workspace in Codex.
3. Attach your inspiration in the Codex task, or place local references in a private, untracked input folder.
4. Say:

   > Help me design a Codex pet from this inspiration, one approval gate at a time.

Codex should begin with interpretation and a small number of design questions. It should not generate a full pack immediately.

The repository already contains a safe placeholder project configuration. Codex can verify it with:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py doctor
```

Your inspiration can be:

- a photo of your own pet;
- an original drawing;
- a shape, texture, object, or visual reference;
- a description of a personality or behavior;
- a combination of these.

You do not need to prepare a formal brief before starting.

## The studio workflow

Each phase produces a reviewable artifact. Codex must receive approval before treating that phase as locked.

| Phase | Question being answered | Reviewable output |
| --- | --- | --- |
| 1. Inspiration | What is emotionally and visually important? | Inspiration brief |
| 2. Creative genome | Which identity, behavior, taste, and anti-goal rules define the character? | Creative genome and no-go list |
| 3. Default form | What makes the neutral character unmistakable at desktop scale? | Default form and identity lock |
| 4. Mechanisms | Which elements may move, fold, stretch, hide, or relocate? | Mechanism board |
| 5. States | How does each state communicate a different intention? | State choreography and key poses |
| 6. Motion and versions | How should weight, timing, continuity, and candidate comparison feel? | Motion bible and versioned previews |
| 7. Production and QA | Is the selected version expressive, valid, and regression-free? | Compiled v2 pack and QA report |
| 8. Release | Is the allowlisted result safe to export, install, or publish? | Validated release or explicit remaining block |

The phases may loop. Returning to an earlier decision is expected; silently overwriting an approved direction is not.

## Collaboration language

Codex should collaborate in the user’s preferred language. Canonical filenames, state identifiers, version identifiers, and reusable repository artifacts stay in English so projects remain portable.

The Previewer is intentionally bilingual:

- stable English identifiers support packaging and debugging;
- user-facing labels may also appear in Chinese;
- a version dropdown makes approved and experimental candidates directly comparable.

## Version discipline

An approved version is evidence, not scratch space.

- Keep approved versions available.
- Create a new version before making a material visual or motion change.
- Use the Previewer’s version dropdown to compare the same state across versions.
- Promote a version only after the user explicitly approves it.
- Record what changed and which identity rules were preserved.

This prevents a successful face, silhouette, or motion detail from being lost while another state is refined.

Use sortable IDs such as `v001`, `v002`, and `v003`. A version should represent one coherent review candidate, not every saved file.

## Local Previewer

Start the dependency-free Previewer from the repository root:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py preview
```

Then open `http://127.0.0.1:8765/previewer/`.

The Previewer includes:

- English and Simplified Chinese UI with browser-language detection;
- an arbitrary-version dropdown rather than hardcoded V1/V2 controls;
- state, runtime-timing, frame-inspection, and all-state tour modes;
- the 16 v2 look directions, auto orbit, and pointer following;
- keyframe and motion-timing boards;
- grayscale preview backgrounds;
- external JSON loading through `?config=<relative-or-absolute-url>`.

Changing language or version preserves the current state, frame, playback mode, speed, and paused/playing state when the selected version supports them.

The built-in geometric figure is a non-production fixture for testing the UI. Replace `previewer/preview-data.js`, or supply an external JSON config, when a real version is ready.

## Deterministic tools

The project tool is dependency-free and exposes:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py --help
```

- `doctor` checks local readiness.
- `preview` serves only on loopback unless network exposure is explicitly allowed.
- `validate` performs fast structural validation of a v2 PNG or WebP pack.
- `privacy-check` scans paths, private terms, credentials, symlinks, archives, and image metadata.
- `export` creates a deterministic, allowlisted share bundle.
- `install` validates and copies only the manifest and atlas to an explicit destination.

These checks complement the visual and production QA in `$hatch-pet`; they do not replace it.

## Packaging with `hatch-pet`

Codex Pet Studio designs and directs the character. The official `hatch-pet` skill is the compiler at the end of the workflow.

Use `$hatch-pet` only after the identity, mechanisms, state choreography, and motion plan are approved. It can assemble, validate, preview, and package the approved work for Codex. It should not replace the earlier creative decisions with a one-shot generation pass.

`doctor` reports whether `$hatch-pet` is visible in standard local skill paths. Its absence does not block ideation, mechanics, state design, or Previewer work. Before production, ask Codex to enable or install the official skill if it is unavailable; do not replace it with locally synthesized production rows.

## Quality standard

A finished pet should pass three layers of QA:

1. **Character QA** — the silhouette, face, proportions, and signature mechanisms still belong to the approved character.
2. **Motion QA** — states are visibly distinct, transitions have physical continuity, and the animation feels intentional at real desktop size.
3. **Pack QA** — dimensions, transparency, frame order, direction mapping, clipping, timing, and package metadata are valid.

“The files were generated” is not the same as “the pet is finished.”

## Privacy

Personal inspiration stays private by default.

- Do not commit personal photos, names, home interiors, screenshots, conversations, or identifying metadata.
- Do not upload user material to an external service without explicit permission.
- Do not place API keys or other secrets in this repository.
- Use neutral or properly licensed material in public examples.
- Remove embedded metadata before publishing derived assets when it could identify a person or location.

See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for reporting and contribution rules.

## Publishing finished pets

Publishing is optional and separate from creation. With the creator’s permission and a completed rights review, a finished pack may be submitted to community catalogs such as [Petdex](https://github.com/crafter-station/petdex) or [awesome-codex-pet](https://github.com/legeling/awesome-codex-pet).

Those projects are independent. Mentioning them is not an endorsement, affiliation, or guarantee of acceptance. Review their current package, attribution, and submission requirements before publishing.

## Repository guide

- [AGENTS.md](AGENTS.md) — operating instructions for Codex
- [`.agents/skills/pet-studio/`](.agents/skills/pet-studio/) — the project-local studio skill
- [`pet-studio.json`](pet-studio.json) — public project configuration and export allowlist
- [`previewer/`](previewer/) — bilingual, versioned local review UI
- [`templates/`](templates/) — reusable phase artifacts
- [`examples/neutral-demo/`](examples/neutral-demo/) — a fictional, text-only walkthrough
- [`tests/`](tests/) — dependency-free integration tests
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution and rights requirements
- [SECURITY.md](SECURITY.md) — private reporting and sensitive-data guidance

## License and attribution

Repository code, documentation, and templates are available under the [MIT License](LICENSE).

That license does not grant rights to third-party characters, trademarks, photographs, or reference material. Generated pet assets may require their own attribution and licensing record. Use [`templates/asset-attribution.md`](templates/asset-attribution.md) before publishing.

Codex Pet Studio is an independent community project and is not affiliated with or endorsed by OpenAI.
