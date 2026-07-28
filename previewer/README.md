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

An external config may override state timing, labels, descriptions, mechanics boards, backgrounds, and runtime behavior. Missing values fall back to `preview-data.js`.

The Production Timing Board always covers all nine standard states in atlas-row order. Partial `states` and `mechanics` overrides are merged by `id` and `stateId`, so a project can replace one state's durations or anchors without making the other eight states disappear.

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

The language and version selectors preserve the current state, frame, selected playback mode, speed, and temporary inspection state when the selected version supports them.

## Playback modes and display size

- **GIF Loop** plays the native exported QA GIF at its encoded timing. When a state has no exported GIF, the mode is disabled and visibly marked as not generated; the Previewer never silently substitutes atlas playback.
- **Runtime Simulation** uses Previewer metadata for frame durations, action-loop count, and slowed Idle behavior. It is a production approximation, not an exact trace of the Codex client.
- **Frame inspection** is a temporary tool rather than a third playback mode. Pause, Previous, Next, a frame thumbnail, or a timing-board card enters inspection; Play returns to the previously selected GIF Loop or Runtime Simulation. A browser cannot freeze a native GIF at its exact internal frame, so GIF inspection opens the corresponding atlas sequence instead.

The **Size** slider in the upper-right corner of the grid stage changes only the displayed preview scale. It never resizes, rewrites, or re-exports the spritesheet or GIF.

The bundled geometric Example includes native GIFs for all nine standard states,
so both playback modes remain testable even before a user project has exported
its own GIFs.
