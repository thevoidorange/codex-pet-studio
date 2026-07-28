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
      "gifRoot": "./v001/previews",
      "isDefault": true
    },
    {
      "id": "v002",
      "displayName": "v002",
      "atlasUrl": "./v002/spritesheet.webp",
      "gifRoot": "./v002/previews"
    }
  ]
}
```

Any number of project versions is supported. When an external config supplies at least one project version, the Previewer selects the project default (or its first version) on load and appends one bundled `Example` option to the version dropdown. The example remains available for orientation without taking over the first view. Keep the same state IDs and atlas contract across versions for like-for-like review.

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

The language and version selectors preserve the current state, frame, selected playback mode, and temporary inspection state when the selected version supports them. Runtime Simulation always follows the fixed contract above.

## Playback modes and display size

- **GIF Loop** plays the native exported QA GIF at its encoded timing. When a state has no exported GIF, the mode is disabled and visibly marked as not generated; the Previewer never silently substitutes atlas playback.
- **Runtime Simulation** reproduces the pinned current Codex desktop cadence: fixed per-frame durations, three action loops, then 6× Idle.
- **Frame inspection** is a temporary tool rather than a third playback mode. Pause, Previous, Next, a frame thumbnail, or a timing-board card enters inspection; Play returns to the previously selected GIF Loop or Runtime Simulation. A browser cannot freeze a native GIF at its exact internal frame, so GIF inspection opens the corresponding atlas sequence instead.

**Keyframes** is read-only. Each thumbnail shows its fixed runtime duration; Idle shows the base duration together with its `× 6` runtime multiplier. Selecting a thumbnail opens frame inspection without changing the source JSON.

The **Size** slider in the upper-right corner of the grid stage mirrors the desktop setting range of `80–224 px`. It changes only the displayed preview size and never resizes, rewrites, or re-exports the spritesheet or GIF.

The bundled geometric Example includes native GIFs for all nine standard states,
so both playback modes remain testable even before a user project has exported
its own GIFs.
