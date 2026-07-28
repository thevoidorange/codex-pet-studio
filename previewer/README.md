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

The language and version selectors preserve the current state, frame, selected playback mode, and temporary inspection state when the selected version supports them. Runtime Simulation always follows the configured Previewer timing metadata.

## Playback modes and display size

- **GIF Loop** plays the native exported QA GIF at its encoded timing. When a state has no exported GIF, the mode is disabled and visibly marked as not generated; the Previewer never silently substitutes atlas playback.
- **Runtime Simulation** uses Previewer metadata for frame durations, action-loop count, and slowed Idle behavior. It is a production approximation, not an exact trace of the Codex client.
- **Frame inspection** is a temporary tool rather than a third playback mode. Pause, Previous, Next, a frame thumbnail, or a timing-board card enters inspection; Play returns to the previously selected GIF Loop or Runtime Simulation. A browser cannot freeze a native GIF at its exact internal frame, so GIF inspection opens the corresponding atlas sequence instead.

**Keyframes & Timing** combines frame inspection and duration editing in the right rail. Select a keyframe to inspect it and edit its duration in 5 ms steps. Runtime Simulation and the Production Timing Board update immediately. The selected timing frame stays pinned while playback continues.

When the page is opened through `studio.py preview` with an external project config, **Update Timing** writes all dirty `states[].durations` directly to that same JSON file. State timing is project-level metadata, so it is shared by every visual version in that config. **Undo** reverses the latest draft change in the current state. **Reset** restores the last loaded or successfully updated values. A successful update becomes the new baseline and clears the draft history.

The write endpoint exists only on the loopback Studio Preview server. It uses a session token, accepts only same-project JSON paths, rejects symlinks and protected files, validates state IDs and frame counts, and atomically replaces the source file. The bundled example, a page opened from `file://`, a remote config, or a network-exposed preview server is read-only. Use the Studio server rather than a generic static file server when you want direct updates.

The 5 ms step and the editor's input bounds are Previewer product guardrails, not Codex Pet technical limits. A v2 Pet package does not carry custom frame durations. Likewise, `actionLoops: 3` and `idleSlowdown: 6` mirror the current desktop runtime cadence for review, but they are not fields written into the installed pet package and may change with the client.

Updating the Preview JSON does not regenerate GIFs or alter the installed Codex pet. GIF timing remains whatever was encoded when that GIF was exported.

The **Size** slider in the upper-right corner of the grid stage changes only the displayed preview scale. It never resizes, rewrites, or re-exports the spritesheet or GIF.

The bundled geometric Example includes native GIFs for all nine standard states,
so both playback modes remain testable even before a user project has exported
its own GIFs.
