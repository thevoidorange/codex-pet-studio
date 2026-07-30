# Previewer configuration

The Previewer works with the bundled neutral fixture or a project-specific JSON file.

Start the local server from the repository root:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py preview
```

Open the bundled fixture:

```text
http://127.0.0.1:8765/previewer/
```

Open an external configuration:

```text
http://127.0.0.1:8765/previewer/?config=../build/preview.json
```

Asset paths are resolved relative to the external JSON file.

The current Delivery Target contract lives at
[`delivery-targets/codex-pet-v2.json`](../delivery-targets/codex-pet-v2.json).
`target-data.js` is a generated browser adapter for that contract so the
Previewer continues to work from both the local server and `file://`. After an
intentional contract change, regenerate the adapter with
`studio.py target sync`; do not edit the adapter by hand.

## Review-context URLs

The Previewer keeps deliberate review focus in the URL:

```text
http://127.0.0.1:8765/previewer/?config=../build/preview.json&candidate=v002&state=idle&frame=2&take=t003
```

- `candidate` is a loaded Candidate ID.
- `state` is a loaded runtime state ID.
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

If an explicitly requested external `config` fails to load, the Previewer may show its bundled example as a fallback, but it removes all review-context fields and stops writing them. This prevents a project link from being mistaken for a colliding example Candidate, frame, or Take.

## Minimal shape

```json
{
  "schemaVersion": 1,
  "deliveryTarget": {
    "id": "codex-pet-v2",
    "revision": 1
  },
  "pet": {
    "name": "Example Pet"
  },
  "versions": [
    {
      "id": "v001",
      "displayName": "v001",
      "atlasUrl": "./v001/spritesheet.webp",
      "isDefault": true
    },
    {
      "id": "v002",
      "displayName": "v002",
      "atlasUrl": "./v002/spritesheet.webp"
    }
  ]
}
```

`deliveryTarget` is optional for legacy configs. When present, it must match the
contract loaded by the Previewer; a mismatched target or revision fails closed.

Any number of project versions is supported. When an external config supplies at least one project version, the Previewer selects the project default (or its first version) on load and appends one bundled `Example` option to the version dropdown. The example remains available for orientation without taking over the first view. Keep the same state IDs and atlas contract across versions for like-for-like review.

## Codex-managed frame takes

A Candidate may optionally expose several temporary visual takes for one
Keyframe. Codex authors and manages these files and config entries; the
Previewer does not upload, save, approve, or rewrite them.

```json
{
  "id": "v002",
  "atlasUrl": "./v002/spritesheet.webp",
  "frameTakes": [
    {
      "stateId": "idle",
      "frameIndex": 1,
      "takes": [
        {
          "id": "t001",
          "label": "Take 01",
          "assetUrl": "./v002/takes/idle/f02/t001.webp"
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

`assetUrl` points to one standalone frame matching the Delivery Target cell
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
Runtime Simulation, and Endless Loop so continuity can be reviewed.

Confirmation is session-only review metadata. It does not rewrite the source
atlas, Previewer JSON, Take asset, neighboring frame, Candidate, or QA status,
and it is cleared by a page reload. Reopen the Keyframe rail to audition and
confirm a different Take or return to Original. Motion Timing continues
to show the source atlas.

## Delivery Target-owned behavior

State IDs, atlas rows, frame counts, per-frame durations, look slots,
action-loop behavior, Idle cadence, sprite geometry, and display limits come
from the generated Delivery Target adapter. External Previewer JSON cannot
override them. A project may still provide localized labels and descriptions,
mechanics-board copy, backgrounds, Candidates, Takes, and asset paths.

Motion Timing covers every target state in atlas-row order. Partial `mechanics`
overrides are merged by `stateId`, so a project can replace one state's anchors
without making the remaining states disappear.

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

The bundled geometric Example uses the same atlas for both playback modes, so
their only behavioral difference is the client-style return to Idle versus an
endless repeat of the selected row.
