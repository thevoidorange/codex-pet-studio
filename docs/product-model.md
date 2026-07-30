# Codex Pet Studio Product Model

## Product promise

Codex Pet Studio is a repository-shaped, agent-native co-design workspace for
making a distinctive animated pet with Codex.

The user brings taste, inspiration, feedback, and approval. Codex carries the
creative process, project memory, production work, and QA. The Previewer gives
both sides a shared place to look at the same Candidate, state, Keyframe, and
Take. The result is a validated pet that can run in its intended environment.

The simplest description is:

> Design together in Codex, review together in the Previewer, then deliver a
> real running pet.

The product is not a one-prompt asset generator, a browser drawing tool, or a
hosted service.

## Roles and surfaces

### User: creative director

The user supplies inspiration, corrects interpretation, compares focused
options, approves creative decisions, and explicitly authorizes installation
or publication. They should not need to understand Git, JSON, spritesheets, or
local paths.

### Codex: designer, producer, and project memory

Codex prepares the private workspace, interprets inspiration, creates visual
options, records decisions, manages Candidates and Takes, preserves approved
work, performs production and QA, and resumes from current project evidence
without asking the user to restate known context.

### Previewer: read-only co-design review workbench

The Previewer makes visual work easy to compare and inspect. It supports
Candidate comparison, state playback, Keyframe inspection, Take audition,
runtime-scale review, and target-specific mechanics such as gaze directions.

It does not generate, upload, save, package, install, publish, or approve
assets. Previewer Confirm is a temporary session choice. Durable approval
happens explicitly in the Codex conversation and is recorded in project files.

### Runtime pet: delivered outcome

The running pet is the final target-specific output. Its supported states,
frame slots, timing, image format, display range, triggers, and lifecycle are
owned by its Delivery Target.

## One conversation, two working surfaces, one durable project

The Codex task is the editing surface. The Previewer is the review surface.
Private project files are the durable memory used when the same local project
is reopened across tasks.

```text
Inspiration
  -> Codex interpretation and focused visual production
  -> Previewer comparison and inspection
  -> natural-language feedback in Codex
  -> additive refinement and recorded approval
  -> target production, QA, and explicit delivery
```

Returning to a project should restore four things before new work begins:

- **Locked** — decisions that have explicit approval
- **Open** — unresolved creative or technical questions
- **Current Focus** — the validated Previewer Candidate, state, Keyframe, and
  Take, when present
- **Next** — the smallest useful action that advances the project

## Durable domain model

- **Inspiration** — private source material and the user's description of what
  matters about it
- **Creative Genome** — identity, behavior, taste, and anti-goal rules
- **Identity Lock** — the approved default form and features that must survive
  later work
- **Mechanism** — a bounded way an element may move, deform, hide, or change
  layer while remaining the same character
- **Behavior Intent** — a target-neutral acting idea such as greeting,
  waiting, inspecting, disappointment, or locomotion
- **Motion Language** — material, weight, lead/follow order, pose spacing,
  stillness, overshoot, settling, and seam rules
- **Candidate** — one coherent proposal across the character or relevant state
  set
- **Keyframe** — one sampled visual slot in a Candidate for the selected
  Delivery Target
- **Take** — one additive visual alternative for one exact Candidate, target
  state, and Keyframe
- **Approval** — an explicit conversational decision tied to exact evidence
- **Delivery Target** — the platform contract that maps approved creative work
  into a runnable artifact

Candidate is the public design term. `versions` may remain as a legacy
implementation field in existing Previewer JSON, but it is not the user model.

## Studio Core and Delivery Targets

The project separates creative truth from platform sampling.

### Studio Core

Studio Core preserves the work that should survive a change of runtime:

- inspiration and privacy classification;
- Creative Genome and anti-goals;
- default form and Identity Lock;
- mechanism ranges and attachment rules;
- Behavior Intents and state contrast;
- Motion Language;
- Candidates, canonical high-quality source assets, and approval evidence;
- review history and unresolved QA.

### Delivery Target

A Delivery Target defines the constraints needed to make that work runnable:

- supported runtime state IDs and their semantic mapping;
- frame or slot counts;
- frame cadence, holds, loops, and lifecycle;
- target mechanics and input signals;
- cell, atlas, image, and manifest requirements;
- display-size range;
- compiler and validation authority;
- staging, packaging, signing, installation, and publication rules.

For each supported runtime, these exact technical facts live in one
machine-readable contract. CLI validation, Previewer playback, sample
generation, and QA consume that contract; they do not own parallel copies.

Target-derived Keyframes, Takes, sampled rows, atlases, previews, and packages
are build and review evidence. Preserve them as provenance, but keep them
distinct from canonical source art and resample them when a new target
requires a different mapping.

Changing a Delivery Target may require new state mapping, slot choreography,
sampling, target QA, and packaging. It must not silently reopen approved
identity, inspiration, or mechanism decisions.

## Current delivery scope

The only supported Delivery Target today is **Codex Pet v2**. It uses the
installed `$hatch-pet` skill as the current production and client-contract
authority.

The target abstraction exists to keep project truth clean, not to claim that
macOS, watchOS, or other runtimes are already implemented. The repository must
not expose a target selector or promise multi-target delivery until a second
target works end to end.

## Future behavior seam

Creative Behavior Intents should not depend on how a platform detects events.
A future runtime may introduce a Behavior Driver:

```text
environment or agent signals
  -> behavior driver
  -> semantic intent
  -> target state mapping
  -> runtime animation
```

For the current Codex Pet target, trigger behavior is owned by the client and
is not configurable by this project. The seam is documented now so a future
standalone runtime can add richer signals without redefining the character.

## Approval and status truth

These outcomes are distinct and must never be collapsed:

1. **Generated** — files exist
2. **Reviewed** — a human or agent inspected the exact result
3. **Approved** — the user explicitly selected the exact creative evidence
4. **Validated** — applicable automated and visual checks passed
5. **Packaged** — a target artifact was staged successfully
6. **Exported** — an allowlisted share artifact was created
7. **Installed** — the validated target artifact was copied to an explicit
   runtime destination and verified
8. **Published** — an authorized artifact reached an external destination

Previewer audition or Confirm never changes these statuses.

## Privacy model

Personal inspiration and active design work are private by default. The public
repository contains the method, neutral fixtures, schemas, and tools. Private
inputs, design decisions, generated builds, exports, local settings, names,
paths, credentials, and identifying metadata must stay outside public Git
history unless the user explicitly authorizes a reviewed artifact.

## Product boundaries

Codex Pet Studio should remain:

- conversation-first;
- local and inspectable;
- resumable across Codex tasks;
- additive rather than destructive;
- explicit about approval and delivery status;
- nontechnical for the user;
- rigorous about target-specific QA.

It should not become:

- an embedded prompt box or drawing application;
- a hosted account product;
- a silent auto-publishing pipeline;
- a generic multi-platform promise before multiple targets exist;
- a replacement for the native production compiler of a target.
