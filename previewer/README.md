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

Any number of versions is supported. Keep the same state IDs and atlas contract across versions for like-for-like review.

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

The language and version selectors preserve the current state, frame, mode, speed, and playback state when the selected version supports them.
