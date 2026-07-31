// Project-facing data for the bundled Raincoat Cat Example. Delivery Target facts
// are generated separately in target-data.js from the canonical contract.
window.PET_PREVIEW_CONFIG = {
  schemaVersion: 1,
  pet: {
    name: "Raincoat Cat",
  },
  versions: [
    {
      id: "example-raincoat-cat",
      displayName: "Example.RaincoatCat",
      labelKey: "ui.exampleVersion",
      atlasUrl: "../examples/raincoat-cat/spritesheet.png",
      isDefault: true,
      frameTakes: [
        {
          stateId: "idle",
          frameIndex: 1,
          takes: [
            {
              id: "t001",
              label: "Take 01",
              atlasSlot: { row: 0, column: 0 },
            },
            {
              id: "t002",
              label: "Take 02",
              atlasSlot: { row: 0, column: 2 },
            },
            {
              id: "t003",
              label: "Take 03",
              atlasSlot: { row: 0, column: 3 },
            },
            {
              id: "t004",
              label: "Take 04",
              atlasSlot: { row: 0, column: 4 },
            },
            {
              id: "t005",
              label: "Take 05",
              atlasSlot: { row: 0, column: 5 },
            },
          ],
        },
      ],
    },
  ],
  mechanics: [
    {
      stateId: "idle",
      anchors: ["A0", "A0 +2", "A0 +4", "A0 +4", "A0 +2", "A0"],
    },
    {
      stateId: "running-right",
      anchors: ["A0", "A1R", "A2R", "A3R", "A4R", "A3R", "A2R", "A1R"],
    },
    {
      stateId: "running-left",
      anchors: ["A0", "A1L", "A2L", "A3L", "A4L", "A3L", "A2L", "A1L"],
    },
    {
      stateId: "waving",
      anchors: ["A0", "A1", "A2", "A1"],
    },
    {
      stateId: "jumping",
      anchors: ["A0", "A1", "A4", "A2", "A0"],
    },
    {
      stateId: "failed",
      anchors: ["A0", "A1", "A2", "A3", "A4", "A3", "A2", "A1"],
    },
    {
      stateId: "waiting",
      anchors: ["A1", "A2", "A2", "A2", "A2", "A1"],
    },
    {
      stateId: "running",
      anchors: ["A0", "A3", "A4", "A5", "A6", "A1"],
    },
    {
      stateId: "review",
      anchors: ["A0", "A1", "A2", "A3", "A2", "A1"],
    },
  ],
  backgrounds: ["paper", "gray", "dark"],
};
