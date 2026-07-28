# Codex pet v2 summary

This file is a concise planning reference. The installed `$hatch-pet` skill is authoritative for production and may evolve.

## Package

```text
<pet-id>/
├── pet.json
└── spritesheet.webp
```

Example manifest:

```json
{
  "id": "example-pet",
  "displayName": "Example Pet",
  "description": "A concise public description.",
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp"
}
```

## Atlas

- 8 columns × 11 rows
- 192 × 208 pixels per cell
- 1536 × 2288 pixels total
- PNG or WebP
- used cells contain one complete readable sprite
- unused cells are fully transparent

## Rows

| Row | State |
| ---: | --- |
| 0 | idle |
| 1 | running-right |
| 2 | running-left |
| 3 | waving |
| 4 | jumping |
| 5 | failed |
| 6 | waiting |
| 7 | running |
| 8 | review |
| 9 | look directions 000°–157.5° |
| 10 | look directions 180°–337.5° |

All sixteen look cells are used in fixed 22.5-degree clockwise steps. Neutral/front gaze uses idle at runtime.

## Responsibility boundary

Pet Studio owns:

- creative collaboration
- decision gates
- identity and mechanism lock
- state choreography
- motion bible
- versioned review
- public-project privacy

`$hatch-pet` owns:

- production image jobs
- row geometry
- deterministic atlas assembly
- direction registration and semantic QA
- contact sheets and motion previews
- v2 validation
- package staging

Do not locally synthesize missing production rows to avoid a failed generation or skipped approval.
