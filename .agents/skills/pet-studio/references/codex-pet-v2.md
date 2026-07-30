# Codex pet v2 production boundary

This is a planning boundary, not a replacement for the installed `$hatch-pet`
skill. Re-read the installed skill before every production or repair run.

## Project staging package

Stage the validated result under `build/pet`:

```text
build/pet/
├── pet.json
└── spritesheet.webp
```

Minimum manifest:

```json
{
  "id": "example-pet",
  "displayName": "Example Pet",
  "description": "A concise description.",
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp"
}
```

The v2 atlas uses 8 columns × 11 rows of 192×208 cells, for a final
1536×2288 PNG or WebP. Used cells contain one complete readable sprite; unused
cells are fully transparent.

Read
[motion-and-state-contract.md](motion-and-state-contract.md)
for the dated row, frame-count, duration, and look-direction planning snapshot.
The client owns those values; the package cannot customize them.

## Responsibility boundary

Pet Studio owns:

- inspiration and privacy intake;
- creative decisions and durable approvals;
- identity, mechanism, state, and motion locks;
- Candidate and Take review;
- production grounding and explicit scope;
- project staging, public export, and installation authorization.

`$hatch-pet` owns:

- production visual jobs and supported repair units;
- row geometry and deterministic atlas assembly;
- look-direction registration and semantic QA;
- contact sheets and motion previews;
- chroma, v2 validation, and final production evidence.

Do not synthesize missing production rows or unsupported final cells to bypass
the compiler contract.

## Preserve approved visuals

Pass every explicitly approved Keyframe or Take to production as a named
grounding asset. Preserve its identity, feature relationships, and requested
details.

If the current compiler requires coherent row generation and cannot guarantee
bit-identical preservation:

1. keep the exact approved asset;
2. explain the row-level constraint before generation;
3. use the asset as authoritative grounding;
4. compare the produced row against it;
5. return to user review when a material visual detail changes.

Never silently replace an approved visual with a similar regeneration.

## Package, export, install, and publish

Treat these as separate operations:

1. **Produce** — create and validate atlas evidence.
2. **Stage** — write the manifest and atlas under `build/pet`.
3. **Export** — create an allowlisted share artifact.
4. **Install** — copy a validated stage to an explicit Codex pet destination.
5. **Publish** — send an authorized artifact to an external destination.

Do not let production write to a live Codex pets directory when the user asked
only to validate, package, or export. If the installed compiler instructions
include a live copy step, stop before it and stage the validated files in the
project. Run installation only after an explicit conversational request.
