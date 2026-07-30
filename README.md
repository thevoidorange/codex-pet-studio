# Codex Pet Studio

Make a distinctive animated Codex pet with Codex, one creative decision at a
time.

You bring inspiration, taste, and feedback. Codex remembers the decisions,
creates and refines the visual work, handles the technical production, and
checks the final pet. A local Previewer gives both of you the same place to
look, compare, and point at exact frames.

> Design together in Codex, review together in the Previewer, then bring the
> pet to life on your desktop.

Beyond access to Codex, the recommended flow requires no terminal, separate Pet
Studio backend or account, or separate OpenAI API key.

## Start in two steps

### 1. Give this repository to Codex

Start a blank Codex task and paste:

> I want to use this GitHub project to design my own Codex pet:
> https://github.com/thevoidorange/codex-pet-studio. I do not use Git or the
> terminal. Please set up the project for me and guide me one creative decision
> at a time. Start by asking for my inspiration, and do not generate the full
> pet yet.

Codex should prepare a private local workspace and explain any environment
limitation instead of handing setup work back to a nontechnical user.

### 2. Share your inspiration

Inspiration can be:

- a photo and personality description of your own pet;
- an original drawing;
- a shape, material, object, or visual reference;
- a behavioral idea or emotional presence;
- any combination of these.

You do not need to write a formal brief. Personal inspiration stays out of the
public repository, exports, and publication by default.

## What the first session feels like

Codex does not begin by producing a complete animation pack.

First, it reflects back:

- what it can directly observe;
- what it thinks matters about the character;
- which visual and behavioral qualities should survive;
- which generic or unwanted directions to avoid;
- the one decision worth making next.

After you correct or approve that reading, Codex proposes a small visual
comparison for the next question. The process moves from character essence to
default form, variable mechanisms, state acting, motion, and finally
production. Steps may combine or loop; approved work is not silently replaced.

## How to work with Codex

You can speak naturally:

> I like the second direction, but keep the first one's brim.

> This frame needs a lower head. Do not move the hem.

> Make two more Takes for the frame I am looking at.

> This is the one. Keep these details fixed and continue.

> Validate and install this pet in Codex.

Codex should know what is already locked, what remains open, and what the
current Previewer link is focused on. Reopening the same local project in a new
task should restore that context from its private files rather than restart
from inspiration.

## The Previewer

Codex opens the local Previewer when there is a real Candidate worth reviewing.
It helps you:

- compare Candidates without losing an approved direction;
- play and compare all runtime states;
- pause on an exact Keyframe;
- audition multiple Takes for that Keyframe;
- inspect real runtime cadence, loop seams, gaze, and desktop display sizes;
- give feedback such as “change this” without restating technical context.

The Previewer is intentionally read-only. It does not generate, upload, save,
package, install, or publish assets.

Clicking a Take only auditions it. Previewer Confirm remembers a temporary
choice for that browser session. To approve a visual decision, say so in the
Codex conversation; Codex records the exact asset and the details that must
remain unchanged.

## The creative workflow

The studio resolves six practical questions:

1. **Inspiration** — what feels specific and worth preserving?
2. **Character** — what makes the default form unmistakable?
3. **Mechanisms** — what may move, fold, stretch, hide, or relocate?
4. **States** — how does each action express a different intention?
5. **Motion** — how do weight, material, stillness, and settling feel?
6. **Delivery** — does the selected Candidate pass visual, motion, pack, and
   privacy QA?

Each round should show the smallest artifact that resolves the current
uncertainty. Rejected options remain useful evidence. An approved Candidate is
preserved before material changes continue.

## What “finished” means

A file existing is not the same as a finished pet. Codex Pet Studio keeps these
outcomes separate:

- the art was generated;
- the exact result was reviewed;
- the user approved it;
- character and motion QA passed;
- the Codex Pet package validated;
- the package was staged or exported;
- the user explicitly requested installation and it was verified;
- the user separately authorized publication.

The current release delivers **Codex Pet v2** packages. Its animation slots and
runtime cadence come from the Codex client, so Codex designs the acting inside
those real constraints instead of inventing settings the pet cannot carry.
Those exact checked-in constraints live in one machine-readable Delivery
Target contract; the CLI, Previewer, sample generator, and QA derive from it.

## Privacy and ownership

The public repository contains the workflow, tools, neutral Example, and
templates. Private inspiration, design decisions, generated Candidates,
builds, and exports stay in ignored local folders.

Codex should never publish personal photos, names, home interiors, local paths,
credentials, private skills, or identifying metadata without explicit,
reviewed permission. Public examples and finished community pets also require
reviewed rights.

See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for the
project's reporting and contribution policies.

## For manual setup and contributors

If you prefer a manual checkout, clone or create a repository from this project
and open it in Codex. The core readiness check is:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py doctor
```

Verify that the selected Delivery Target and its static Previewer adapter are
in sync with:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py target check
```

Start the local Previewer with:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py preview
```

The project is intentionally inspectable and dependency-free. Useful entry
points:

- [Product model](docs/product-model.md) — roles, domain model, and the
  Studio Core / Delivery Target boundary
- [Codex Pet v2 contract](delivery-targets/codex-pet-v2.json) — the canonical
  checked-in geometry, state, cadence, lifecycle, and display facts
- [Agent instructions](AGENTS.md) — repository routing, privacy, and operating
  rules
- [Pet Studio Skill](.agents/skills/pet-studio/SKILL.md) — the detailed
  creative, review, production, and QA method
- [Previewer](previewer/) — the bilingual read-only review workbench
- [Templates](templates/) — reusable private decision artifacts
- [Neutral demo](examples/neutral-demo/) — fictional public example material
- [Tests](tests/) — dependency-free regression coverage

The architecture keeps approved creative work separate from platform-specific
sampling, but Codex Pet v2 is the only supported Delivery Target today. Future
targets should be added only after they work end to end.

## License

Repository code, documentation, and templates are available under the
[MIT License](LICENSE).

That license does not grant rights to third-party characters, trademarks,
photographs, or reference material. Generated pet assets may require their own
permission and attribution record.

Codex Pet Studio is an independent community project and is not affiliated
with or endorsed by OpenAI.
