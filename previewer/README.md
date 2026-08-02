# Previewer configuration

The Previewer works with the bundled Raincoat Cat Example or a project-specific JSON file.

Start the local server from the repository root:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py preview
```

Open the bundled fixture:

```text
http://127.0.0.1:8765/previewer/
```

After project setup, Codex should start or reuse this server, open the base
URL, and verify that the Candidate selector shows exactly
`Example.RaincoatCat`. This gives the user a working review surface immediately.

Open an external configuration:

```text
http://127.0.0.1:8765/previewer/?config=../build/preview.json
```

Asset paths are resolved relative to the external JSON file.

For the first reviewable character image, prefer the deterministic staging
command:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py review stage-static \
  --asset path/to/character-study-source.png \
  --preview-asset path/to/character-study-transparent.png \
  --candidate <semantic-candidate-id> \
  --default
```

It preserves the exact PNG or WebP source, copies the prepared transparent
RGBA PNG into the ignored review build, references only the derivative from
the validated config, and returns a URL focused on that project Static asset.
Use the project-bundled `$prepare-transparent-assets` skill to create the
derivative before staging. Codex chooses a stable semantic ID and natural
display name from the actual proposal; do not prescribe a sequential
`v001`/`v002` convention. Switch the already-running Previewer to that URL and
verify it before producing later creative layers.

Before rendering, the browser validates the focused Candidate's structure,
decodes its declared Static, standalone Takes, and reachable atlas cells, and
requires both visible and transparent pixels. The project-level target,
schema, and asset boundary remain global gates. An invalid focused or default
Candidate fails closed; an invalid sibling is diagnosed and disabled without
blocking a healthy focus. The Previewer never substitutes the bundled Example.

The current Delivery Target contract lives at
[`delivery-targets/codex-pet-v2.json`](../delivery-targets/codex-pet-v2.json).
`target-data.js` is a generated browser adapter for that contract. Open the
Previewer through `studio.py preview` on localhost; direct `file://` use is not
supported because transparent-pixel validation requires a trustworthy browser
origin. After an intentional contract change, regenerate the adapter with
`studio.py target sync`; do not edit the adapter by hand.

## Review-context URLs

The Previewer keeps deliberate review focus in the URL:

```text
http://127.0.0.1:8765/previewer/?config=../build/preview.json&candidate=<semantic-candidate-id>&state=idle&frame=2&take=t003
```

- `candidate` is a loaded Candidate ID.
- `state` is `static` or a loaded runtime state ID.
- `frame` is one-based.
- `take` is a loaded Take ID or the explicit value `original`.
- Existing query parameters, including `config`, are preserved.

Candidate, state, Keyframe, and Take selections update the URL without
reloading the page. Switching to Gaze Directions clears the animation `frame`
and `take`; Auto Orbit and pointer movement then leave the remaining review
context unchanged. Runtime frame ticks and all-state playback also do not
rewrite it. A valid review link restores the selected frame in inspection mode
and auditions its Take; it does not confirm, approve, save, generate, install,
or publish anything.

Unknown or stale values fail closed and are replaced with valid project defaults. URL values are matched only against the loaded config and cannot introduce an arbitrary asset path.

If an explicitly requested external `config` fails a global gate, or if the
focused/default Candidate fails its own preflight, the Previewer shows an
actionable local diagnostic and does not render that Candidate. Diagnostics
identify a safe config reference, Candidate, field/error code, expected and
actual fact, and next step; they never expose filesystem paths, payloads, or a
stack trace. A bad sibling remains unavailable in the Candidate selector and
does not block a healthy focus.

The bundled Example is never project data. Codex must not use it to fill a
missing project state, replace a failed Static handoff, or claim that project
work is reviewable. Repair the project config or asset instead.

Its selector label is always `Example.RaincoatCat` in every supported locale.

## Progressive Candidate shape

A Candidate may begin with one Static image and no runtime states:

```json
{
  "schemaVersion": 1,
  "deliveryTarget": {
    "id": "codex-pet-v2",
    "revision": 2
  },
  "pet": {
    "name": "Working Pet"
  },
  "versions": [
    {
      "id": "<semantic-candidate-id>",
      "displayName": "<candidate-name>",
      "isDefault": true,
      "static": {
        "assetUrl": "./candidates/<semantic-candidate-id>/static/original.png",
        "takes": []
      },
      "stateIds": [],
      "lookDirectionsAvailable": false
    }
  ]
}
```

`deliveryTarget` is optional for legacy configs. When present, it must match the
contract loaded by the Previewer; a mismatched target or revision fails closed.

Static contains exactly one standalone image plus optional Takes. It is not a
runtime state, atlas row, Keyframe timing entry, or one-frame animation. Its
focused URL is:

```text
?config=../build/review/preview.json&candidate=<semantic-candidate-id>&state=static&frame=1&take=original
```

When real runtime rows become available, register them on the same Candidate
with the official bridge:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py review stage-runtime \
  --atlas path/to/spritesheet.png \
  --candidate <semantic-candidate-id> \
  --states idle,waving
```

Use `--check --json` to validate and inspect the complete zero-write plan. The
command preserves Static, copies source and review assets atomically, updates
the exact state subset, and returns a focused URL. Its resulting Candidate
shape is equivalent to:

```json
{
  "id": "<semantic-candidate-id>",
  "displayName": "<candidate-name>",
  "static": {
    "assetUrl": "./candidates/<semantic-candidate-id>/static/original.png",
    "takes": []
  },
  "atlasUrl": "./candidates/<semantic-candidate-id>/spritesheet.webp",
  "atlasPhase": "standard-intermediate",
  "stateIds": ["idle", "waving"],
  "lookDirectionsAvailable": false
}
```

`stateIds` may contain one state. Missing target states remain absent from
navigation, playback, and Motion Timing; never duplicate an available row or
borrow the bundled Example. Add a state only when its real atlas row exists.
Set `lookDirectionsAvailable` to `true` only when the Candidate has the real
direction-review asset required by the target.

The bridge accepts an 8x9 source only as `standard-intermediate`, preserves it,
and creates a review-only 8x11 projection internally. It never treats that
projection as a completed v2 atlas. A `codex-pet-v2-final` Candidate requires a
real 8x11 source with every look cell and the neutral reference present. Do not
copy assets, edit `atlasUrl`/`stateIds`, or add empty padding rows by hand.

For compatibility, an atlas Candidate that omits `stateIds` uses the legacy
complete target-state interpretation. New progressive configs should always
declare their exact subset.

Any number of project Candidates is supported, and each Candidate may have a
different truthful level of completion. When an external config supplies at
least one project Candidate, the Previewer selects the project default (or its
first Candidate) on load and appends one bundled `Example` option to the
Candidate dropdown as `Example.RaincoatCat`. The Example remains available for orientation without
taking over the first view or contributing assets to the project.

## Static Takes

Static Takes are transparent standalone PNGs on the same canvas as the Static
review original:

```json
{
  "id": "<semantic-candidate-id>",
  "static": {
    "assetUrl": "./candidates/<semantic-candidate-id>/static/original.png",
    "takes": [
      {
        "id": "t001",
        "label": "Take 01",
        "assetUrl": "./takes/<semantic-candidate-id>/static/f01/t001.png"
      }
    ]
  },
  "stateIds": []
}
```

Use `state=static&frame=1` when adding or focusing a Static Take. The
Previewer auditions and confirms it with the same session-only interaction as
a runtime Take, but no runtime cadence or target-cell geometry is assigned.

## Codex-managed frame takes

A Candidate may optionally expose several temporary visual takes for one
Keyframe. Codex authors and manages these files and config entries; the
Previewer does not upload, save, approve, or rewrite them.

```json
{
  "id": "<semantic-candidate-id>",
  "atlasUrl": "./candidates/<semantic-candidate-id>/spritesheet.webp",
  "frameTakes": [
    {
      "stateId": "idle",
      "frameIndex": 1,
      "takes": [
        {
          "id": "t001",
          "label": "Take 01",
          "assetUrl": "./takes/<semantic-candidate-id>/idle/f02/t001.webp"
        },
        {
          "id": "t002",
          "label": "Take 02",
          "atlasSlot": { "row": 0, "column": 2 }
        }
      ]
    }
  ]
}
```

For runtime Keyframes, `assetUrl` points to one standalone frame matching the Delivery Target cell
size, relative to the Previewer JSON. `atlasSlot` points to one cell in the
Candidate atlas. Supply exactly one source per Take. Keep private working files under
`design/takes/<candidate>/<state>/fNN/`; copy only the review assets that the
Previewer needs into the generated build beside its JSON.

Clicking a Keyframe with Takes reveals a smaller rail below that Keyframe row.
When the rail overflows, its own Previous / Next arrows only reveal more Takes;
they never change the auditioned option. Clicking a Take auditions it. The fixed
Confirm button at the right edge records the current choice for that exact
Candidate, state, and Keyframe, then closes the rail. The Viewer Previous / Next
controls always move between Keyframes; arrow keys move between Takes only while
a Take card has focus. The confirmed Take is used by the Keyframe thumbnail,
Runtime Simulation, Endless Loop, and Motion Timing so continuity can be
reviewed. While a rail is open, Motion Timing follows the currently auditioned
Take immediately, including Original.

Confirmation is session-only review metadata. It does not rewrite the source
atlas, Previewer JSON, Take asset, neighboring frame, Candidate, or QA status,
and it is cleared by a page reload. Reopen the Keyframe rail to audition and
confirm a different Take or return to Original.

## Delivery Target-owned behavior

Available state IDs come from each Candidate's declared subset. For those
states, atlas rows, frame counts, per-frame durations, look slots,
action-loop behavior, Idle cadence, sprite geometry, and display limits come
from the generated Delivery Target adapter. External Previewer JSON cannot
override them. A project may still provide localized labels and descriptions,
mechanics-board copy, backgrounds, Candidates, Takes, and asset paths.

Motion Timing covers only the Candidate's available runtime states in target
atlas-row order. Static never appears there. Partial `mechanics` overrides are
merged by `stateId`; they do not create missing states.

The canonical contract also records which installed `$hatch-pet` and Codex
Desktop build the snapshot was verified against. Re-check that provenance when
the installed client contract changes. Runtime cadence remains client behavior,
not editable Pet Pack metadata; the pack itself contains the atlas and basic
manifest only.

## Localized project copy

Keep reusable identifiers in English. Add pet-specific user-facing copy without changing the UI bundle:

```json
{
  "i18n": {
    "messages": {
      "en": {
        "states": {
          "idle": {
            "title": "A project-specific title"
          }
        }
      },
      "zh-CN": {
        "states": {
          "idle": {
            "title": "A Simplified Chinese project title"
          }
        }
      }
    }
  }
}
```

The language and version selectors preserve the current state, frame, selected playback mode, and temporary inspection state. Both playback modes use the fixed contract above.

## Playback modes and display size

- **Runtime Simulation** reproduces the Delivery Target's client cadence,
  including its action-loop return and Idle timing.
- **Endless Loop** uses the same spritesheet and fixed per-frame durations, but repeats the selected state indefinitely instead of returning to Idle.
- **Frame inspection** is a temporary tool rather than a third playback mode. Pause, Previous, Next, a frame thumbnail, or a timing-board card enters inspection; Play returns to the previously selected Runtime Simulation or Endless Loop.

**Keyframes** is read-only. Each thumbnail shows the target-defined runtime
duration; Idle also shows its target-defined multiplier. Selecting a thumbnail
opens frame inspection without changing the source JSON.

The **Size** slider in the upper-right corner of the grid stage reads its limits
from the Delivery Target. It changes only the displayed preview size and never
resizes, rewrites, or re-exports the spritesheet.

Runtime-only controls disable or disappear when their required state or asset
does not exist. A Static-only Candidate remains fully reviewable, and a
one-state Candidate can use the runtime controls that are truthful for that
state. All-state playback never invents missing states.

The bundled Raincoat Cat Example uses the same atlas for both playback modes, so
their only behavioral difference is the client-style return to Idle versus an
endless repeat of the selected row.
