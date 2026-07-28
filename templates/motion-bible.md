# Motion Bible

## Motion character

- Three motion adjectives:
- Perceived material:
- Weight:
- Elasticity:
- Friction:
- Default emotional temperature:

## Current client snapshot

Record the `$hatch-pet` version or client snapshot checked before production. The current v2 snapshot uses fixed row counts and durations, plays each non-Idle action three loops, then returns to Idle at six times its base durations. The package cannot override those values. Client display size is 80–224 px.

- Contract checked on:
- Source checked:
- Differences from the repository snapshot:

## Global fixed-slot rules

- Visual hold strategy:
- Pose-spacing / perceived easing:
- Material deformation:
- Overshoot policy:
- Final-slot settle:
- Loop seam rule:
- Maximum acceptable bounce:

## Physical continuity

- Primary center of mass:
- Anchored regions:
- Flexible regions:
- Follow-through order:
- Compression and extension rules:
- How left/right motion affects the character:

## Fixed state slots

Do not edit these durations in the project. Map the acting onto them.

| State ID | Fixed cells | Current base durations |
| --- | ---: | --- |
| `idle` | 6 | 280, 110, 110, 140, 140, 320 ms; client plays at 6× |
| `running-right` | 8 | 120, 120, 120, 120, 120, 120, 120, 220 ms |
| `running-left` | 8 | 120, 120, 120, 120, 120, 120, 120, 220 ms |
| `waving` | 4 | 140, 140, 140, 280 ms |
| `jumping` | 5 | 140, 140, 140, 140, 280 ms |
| `failed` | 8 | 140, 140, 140, 140, 140, 140, 140, 240 ms |
| `waiting` | 6 | 150, 150, 150, 150, 150, 260 ms |
| `running` | 6 | 120, 120, 120, 120, 120, 220 ms |
| `review` | 6 | 150, 150, 150, 150, 150, 280 ms |

## Slot choreography

Use every required cell, but do not invent movement merely to fill it. Near-repeated drawings create holds; larger pose gaps create faster perceived transitions.

| State ID | Slot-by-slot beats | Visual holds / near-repeats | Accent slot | Final settle and seam |
| --- | --- | --- | --- | --- |
| `idle` |  |  |  |  |

## Secondary motion

- Element:
- Slot delay after primary motion:
- Arc:
- Damping:
- Settle:

## Motion no-go list

- Unwanted bounce:
- Unwanted stiffness:
- Unwanted speed:
- Unwanted symmetry:
- Other:

## Phase decision

- Status: `draft | review | approved`
- Approved by:
- Decision notes:
