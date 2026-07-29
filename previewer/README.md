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

## Minimal shape

```json
{
  "schemaVersion": 1,
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

`assetUrl` points to one standalone 192×208 frame relative to the Previewer
JSON. `atlasSlot` points to one cell in the Candidate atlas. Supply exactly one
source per Take. Keep private working files under
`design/takes/<candidate>/<state>/fNN/`; copy only the review assets that the
Previewer needs into the generated build beside its JSON.

Clicking a Keyframe with Takes reveals a smaller rail below that Keyframe row.
Clicking a Take, or using Previous / Next while the rail is open, only auditions
that option. The small Confirm button beside Next records the current choice for
that exact Candidate, state, and Keyframe, then closes the rail. The confirmed
Take is used by the Keyframe thumbnail, Runtime Simulation, and Endless Loop so
continuity can be reviewed.

Confirmation is session-only review metadata. It does not rewrite the source
atlas, Previewer JSON, Take asset, neighboring frame, Candidate, or QA status,
and it is cleared by a page reload. Reopen the Keyframe rail to audition and
confirm a different Take or return to Original. Motion Timing Board continues
to show the source atlas.

## Stable state IDs

The bundled defaults use the Codex v2 identifiers:

- `idle`
- `running-right`
- `running-left`
- `waving`
- `jumping`
- `failed`
- `waiting`
- `running`
- `review`

State rows, frame counts, per-frame durations, action-loop count, and Idle slowdown are fixed by the current Codex desktop runtime. External Previewer JSON cannot override them. A project may still provide localized labels and descriptions, mechanics-board copy, backgrounds, versions, and asset paths.

The Motion Timing Board always covers all nine standard states in atlas-row order. Partial `mechanics` overrides are merged by `stateId`, so a project can replace one state's anchors without making the other eight states disappear.

## Fixed desktop runtime contract

The Previewer pins the current Codex v2 desktop cadence:

This snapshot was verified against Codex Desktop `26.721.41059` (build `5848`) on 2026-07-28. Re-check it when the installed client or `$hatch-pet` contract changes.

| State | Row | Fixed base durations |
| --- | ---: | --- |
| `idle` | 0 | `280, 110, 110, 140, 140, 320 ms`, each multiplied by `6` at runtime |
| `running-right` | 1 | `120, 120, 120, 120, 120, 120, 120, 220 ms` |
| `running-left` | 2 | `120, 120, 120, 120, 120, 120, 120, 220 ms` |
| `waving` | 3 | `140, 140, 140, 280 ms` |
| `jumping` | 4 | `140, 140, 140, 140, 280 ms` |
| `failed` | 5 | `140, 140, 140, 140, 140, 140, 140, 240 ms` |
| `waiting` | 6 | `150, 150, 150, 150, 150, 260 ms` |
| `running` | 7 | `120, 120, 120, 120, 120, 220 ms` |
| `review` | 8 | `150, 150, 150, 150, 150, 280 ms` |

Non-Idle actions play exactly three loops, then return to the slowed Idle loop. These values are client behavior, not editable Pet Pack fields. The pack itself contains the atlas and basic manifest only.

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

- **Runtime Simulation** reproduces the pinned current Codex desktop cadence: fixed per-frame durations, three action loops, then 6× Idle.
- **Endless Loop** uses the same spritesheet and fixed per-frame durations, but repeats the selected state indefinitely instead of returning to Idle.
- **Frame inspection** is a temporary tool rather than a third playback mode. Pause, Previous, Next, a frame thumbnail, or a timing-board card enters inspection; Play returns to the previously selected Runtime Simulation or Endless Loop.

**Keyframes** is read-only. Each thumbnail shows its fixed runtime duration; Idle shows the base duration together with its `× 6` runtime multiplier. Selecting a thumbnail opens frame inspection without changing the source JSON.

The **Size** slider in the upper-right corner of the grid stage mirrors the desktop setting range of `80–224 px`. It changes only the displayed preview size and never resizes, rewrites, or re-exports the spritesheet.

The bundled geometric Example uses the same atlas for both playback modes, so
their only behavioral difference is the client-style return to Idle versus an
endless repeat of the selected row.
