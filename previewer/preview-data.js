window.PET_PREVIEW_CONFIG = {
  schemaVersion: 1,
  pet: {
    name: "Sample Pet",
  },
  sprite: {
    columns: 8,
    rows: 11,
    frameWidth: 192,
    frameHeight: 208,
  },
  runtime: {
    actionLoops: 3,
    idleSlowdown: 6,
  },
  versions: [
    {
      id: "v002",
      displayName: "v002",
      statusKey: "ui.currentVersion",
      atlasUrl: null,
      gifRoot: null,
      sampleVariant: 2,
      isDefault: true,
    },
    {
      id: "v001",
      displayName: "v001",
      statusKey: "ui.baselineVersion",
      atlasUrl: null,
      gifRoot: null,
      sampleVariant: 1,
    },
  ],
  states: [
    {
      id: "idle",
      row: 0,
      durations: [280, 110, 110, 140, 140, 320],
    },
    {
      id: "running-right",
      row: 1,
      durations: [120, 120, 120, 120, 120, 120, 120, 220],
    },
    {
      id: "running-left",
      row: 2,
      durations: [120, 120, 120, 120, 120, 120, 120, 220],
    },
    {
      id: "waving",
      row: 3,
      durations: [140, 140, 140, 280],
    },
    {
      id: "jumping",
      row: 4,
      durations: [140, 140, 140, 140, 280],
    },
    {
      id: "failed",
      row: 5,
      durations: [140, 140, 140, 140, 140, 140, 140, 240],
    },
    {
      id: "waiting",
      row: 6,
      durations: [150, 150, 150, 150, 150, 260],
    },
    {
      id: "running",
      row: 7,
      durations: [120, 120, 120, 120, 120, 220],
    },
    {
      id: "review",
      row: 8,
      durations: [150, 150, 150, 150, 150, 280],
    },
  ],
  directions: [
    { degree: 0, key: "up", row: 9, column: 0 },
    { degree: 22.5, key: "upRight", row: 9, column: 1 },
    { degree: 45, key: "upRight", row: 9, column: 2 },
    { degree: 67.5, key: "upRight", row: 9, column: 3 },
    { degree: 90, key: "right", row: 9, column: 4 },
    { degree: 112.5, key: "downRight", row: 9, column: 5 },
    { degree: 135, key: "downRight", row: 9, column: 6 },
    { degree: 157.5, key: "downRight", row: 9, column: 7 },
    { degree: 180, key: "down", row: 10, column: 0 },
    { degree: 202.5, key: "downLeft", row: 10, column: 1 },
    { degree: 225, key: "downLeft", row: 10, column: 2 },
    { degree: 247.5, key: "downLeft", row: 10, column: 3 },
    { degree: 270, key: "left", row: 10, column: 4 },
    { degree: 292.5, key: "upLeft", row: 10, column: 5 },
    { degree: 315, key: "upLeft", row: 10, column: 6 },
    { degree: 337.5, key: "upLeft", row: 10, column: 7 },
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
