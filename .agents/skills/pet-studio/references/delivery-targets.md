# Delivery Targets

## Contents

- Why the boundary exists
- Studio Core
- Delivery Target contract
- Choose and record a target
- Map behavior into runtime states
- Sample motion into target slots
- Preserve canonical sources
- Retarget without restarting
- Current Codex Pet v2 target
- Future behavior drivers

## Why the boundary exists

Keep the approved character independent from the first runtime that delivers
it. A platform may constrain state names, frame counts, cadence, dimensions,
input signals, or packaging. Those constraints should shape target sampling
without becoming the definition of the character.

Do not advertise multiple target support merely because this boundary exists.
A Delivery Target is supported only after its compiler, Previewer behavior,
QA, packaging, and installation path work end to end.

## Studio Core

Treat these as target-neutral creative truth:

- inspiration and privacy classification;
- Creative Genome and anti-goals;
- Identity Lock and default form;
- mechanisms, anchors, and deformation ranges;
- Behavior Intents;
- Motion Language;
- Candidates and exact approval evidence;
- canonical source assets.

A runtime change must not silently reinterpret or reopen these decisions.

## Delivery Target contract

A target-specific contract owns:

- stable target ID and version;
- runtime state IDs and semantic mapping;
- required frame or slot counts;
- fixed or configurable timing and lifecycle;
- direction, gaze, pointer, sensor, or input mechanics;
- cell, atlas, image, manifest, and package format;
- supported display range;
- compiler and validation authority;
- staging, installation, signing, and publication rules.

Target-derived Keyframes, sampled rows, atlases, previews, and packages are
build evidence. Keep them distinct from canonical source art.

Each supported target has one canonical machine-readable contract. Project
code, schemas, tests, sample generators, and Previewer adapters must derive
target facts from it rather than keeping independent constants. Human
references may explain acting and responsibility boundaries, but must link to
the contract for exact values.

## Choose and record a target

Before state-slot planning or production:

1. identify the supported Delivery Target;
2. read its current authoritative contract;
3. record the target ID in project production context;
4. distinguish target facts from creative preferences;
5. report any mismatch between the repository snapshot and the installed
   production authority.

If no target is recorded in the current repository, use `codex-pet-v2`; it is
the only supported target today. Do not invent a target selector.

For repository checks, run `studio.py target check`. When intentionally
changing a contract, increment its revision, run `studio.py target sync`, and
review the canonical JSON and generated Previewer adapter together.

## Map behavior into runtime states

Define Behavior Intents before runtime IDs. An intent describes what the
character wants, notices, or does. A target state describes where that acting
must be sampled for one platform.

For each required target state, record:

- mapped Behavior Intent;
- target trigger or lifecycle, if known;
- state-specific composition and contrast;
- mechanisms used;
- target frame-slot beat map;
- entry, settle, loop, and return behavior.

One Behavior Intent may map to more than one target state, and one target state
may combine compatible intents. Preserve the semantic distinction in the
project record.

## Sample motion into target slots

Define Motion Language before frame sampling:

- material and weight;
- lead and follow order;
- stillness and visual holds;
- deformation and overshoot limits;
- settle order and seam behavior.

Then map those rules into the target cadence. Frame spacing is a sampling
decision, not a new creative identity. Fixed slots may require near-repeated
drawings, concentrated transitions, or a long visual hold.

Never add controls for a parameter that the target package cannot carry.

## Preserve canonical sources

Keep the highest-quality approved source for every identity-defining visual and
explicitly approved Take. Production may extract, register, composite, or
sample it, but should not silently replace it with a similar regeneration.

When a target compiler cannot preserve exact pixels:

1. retain the approved source;
2. explain the target constraint;
3. use the source as named grounding;
4. compare the result against it;
5. reopen review only for the affected target output.

## Retarget without restarting

Changing Delivery Target may reopen:

- runtime state mapping;
- target mechanics;
- slot choreography;
- target previews;
- technical and runtime QA;
- packaging and installation.

It does not automatically reopen:

- inspiration understanding;
- Creative Genome;
- Identity Lock;
- approved mechanism rules;
- canonical Motion Language;
- exact approved visual evidence.

Name the smallest platform-sensitive decisions that require review.

## Current Codex Pet v2 target

Use target ID `codex-pet-v2`.

Read the machine-readable
[Codex Pet v2 contract](../../../../delivery-targets/codex-pet-v2.json) for
exact target facts and [codex-pet-v2.md](codex-pet-v2.md) for their acting,
staging, and compiler boundary. Read
[motion-and-state-contract.md](motion-and-state-contract.md)
for target-neutral Motion Language. Re-read the project-bundled `$hatch-pet`
skill before production. If a newer external copy conflicts with the repository
snapshot, stop and reconcile the contract intentionally before adopting it.

## Future behavior drivers

A future standalone runtime may map environmental or agent signals into
Behavior Intents before selecting target states:

```text
signals -> behavior driver -> semantic intent -> target state -> animation
```

This is an architecture seam, not a current feature. Do not implement or imply
configurable intelligent triggers for the Codex Pet target.
