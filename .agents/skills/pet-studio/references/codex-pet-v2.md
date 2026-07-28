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

## Current client row snapshot

| Row | State | Used cells | Current client base durations |
| ---: | --- | ---: | --- |
| 0 | idle | 6 | 280, 110, 110, 140, 140, 320 ms |
| 1 | running-right | 8 | 120, 120, 120, 120, 120, 120, 120, 220 ms |
| 2 | running-left | 8 | 120, 120, 120, 120, 120, 120, 120, 220 ms |
| 3 | waving | 4 | 140, 140, 140, 280 ms |
| 4 | jumping | 5 | 140, 140, 140, 140, 280 ms |
| 5 | failed | 8 | 140, 140, 140, 140, 140, 140, 140, 240 ms |
| 6 | waiting | 6 | 150, 150, 150, 150, 150, 260 ms |
| 7 | running | 6 | 120, 120, 120, 120, 120, 220 ms |
| 8 | review | 6 | 150, 150, 150, 150, 150, 280 ms |
| 9 | look directions 000°–157.5° | 8 | fixed 22.5° direction steps |
| 10 | look directions 180°–337.5° | 8 | fixed 22.5° direction steps |

All sixteen look cells are used in fixed 22.5-degree clockwise steps. Neutral/front gaze uses idle at runtime.

The current client plays each non-Idle action for three loops and then returns to Idle. Idle uses six times the row-0 base durations. These durations and loop rules are client-owned: they are not stored in `pet.json`, cannot be customized by the package, and may change in a future client. Pet display size is likewise a client setting, currently 80–224 px, rather than package metadata.

Treat this table as a verified current-client planning snapshot. Re-read the installed `$hatch-pet` skill before production.

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
