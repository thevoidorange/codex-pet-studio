// Generated from the canonical Delivery Target contract.
// Run `studio.py target sync` after intentionally revising that contract.
window.PET_DELIVERY_TARGET = {
  "$schema": "../.agents/skills/pet-studio/schemas/delivery-target.schema.json",
  "atlas": {
    "cellHeightPx": 208,
    "cellWidthPx": 192,
    "columns": 8,
    "rows": 11
  },
  "display": {
    "maximumPx": 224,
    "minimumPx": 80,
    "owner": "codex-client-setting"
  },
  "displayName": "Codex Pet v2",
  "id": "codex-pet-v2",
  "lookDirections": {
    "clockwise": true,
    "coordinateSystem": "screen-clockwise-from-up",
    "neutralReferenceSlot": {
      "column": 6,
      "row": 0
    },
    "neutralStateId": "idle",
    "slots": [
      {
        "column": 0,
        "degree": 0,
        "key": "up",
        "row": 9
      },
      {
        "column": 1,
        "degree": 22.5,
        "key": "upRight",
        "row": 9
      },
      {
        "column": 2,
        "degree": 45,
        "key": "upRight",
        "row": 9
      },
      {
        "column": 3,
        "degree": 67.5,
        "key": "upRight",
        "row": 9
      },
      {
        "column": 4,
        "degree": 90,
        "key": "right",
        "row": 9
      },
      {
        "column": 5,
        "degree": 112.5,
        "key": "downRight",
        "row": 9
      },
      {
        "column": 6,
        "degree": 135,
        "key": "downRight",
        "row": 9
      },
      {
        "column": 7,
        "degree": 157.5,
        "key": "downRight",
        "row": 9
      },
      {
        "column": 0,
        "degree": 180,
        "key": "down",
        "row": 10
      },
      {
        "column": 1,
        "degree": 202.5,
        "key": "downLeft",
        "row": 10
      },
      {
        "column": 2,
        "degree": 225,
        "key": "downLeft",
        "row": 10
      },
      {
        "column": 3,
        "degree": 247.5,
        "key": "downLeft",
        "row": 10
      },
      {
        "column": 4,
        "degree": 270,
        "key": "left",
        "row": 10
      },
      {
        "column": 5,
        "degree": 292.5,
        "key": "upLeft",
        "row": 10
      },
      {
        "column": 6,
        "degree": 315,
        "key": "upLeft",
        "row": 10
      },
      {
        "column": 7,
        "degree": 337.5,
        "key": "upLeft",
        "row": 10
      }
    ]
  },
  "package": {
    "manifestFile": "pet.json",
    "manifestSchema": ".agents/skills/pet-studio/schemas/pet-v2.schema.json",
    "spriteVersionNumber": 2,
    "spritesheetFormats": [
      "png",
      "webp"
    ]
  },
  "revision": 2,
  "runtime": {
    "actionLoops": 3,
    "actionReturnStateId": "idle",
    "idleDurationMultiplier": 6,
    "idleStateId": "idle",
    "owner": "codex-client"
  },
  "schemaVersion": 1,
  "states": [
    {
      "durationsMs": [
        280,
        110,
        110,
        140,
        140,
        320
      ],
      "firstColumn": 0,
      "id": "idle",
      "row": 0
    },
    {
      "durationsMs": [
        120,
        120,
        120,
        120,
        120,
        120,
        120,
        220
      ],
      "firstColumn": 0,
      "id": "running-right",
      "row": 1
    },
    {
      "durationsMs": [
        120,
        120,
        120,
        120,
        120,
        120,
        120,
        220
      ],
      "firstColumn": 0,
      "id": "running-left",
      "row": 2
    },
    {
      "durationsMs": [
        140,
        140,
        140,
        280
      ],
      "firstColumn": 0,
      "id": "waving",
      "row": 3
    },
    {
      "durationsMs": [
        140,
        140,
        140,
        140,
        280
      ],
      "firstColumn": 0,
      "id": "jumping",
      "row": 4
    },
    {
      "durationsMs": [
        140,
        140,
        140,
        140,
        140,
        140,
        140,
        240
      ],
      "firstColumn": 0,
      "id": "failed",
      "row": 5
    },
    {
      "durationsMs": [
        150,
        150,
        150,
        150,
        150,
        260
      ],
      "firstColumn": 0,
      "id": "waiting",
      "row": 6
    },
    {
      "durationsMs": [
        120,
        120,
        120,
        120,
        120,
        220
      ],
      "firstColumn": 0,
      "id": "running",
      "row": 7
    },
    {
      "durationsMs": [
        150,
        150,
        150,
        150,
        150,
        280
      ],
      "firstColumn": 0,
      "id": "review",
      "row": 8
    }
  ],
  "verifiedAgainst": {
    "authority": "installed-hatch-pet",
    "build": "5848",
    "date": "2026-07-28",
    "product": "Codex Desktop",
    "version": "26.721.41059"
  }
};
