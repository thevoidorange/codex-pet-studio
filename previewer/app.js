(() => {
  "use strict";

  const STORAGE_KEY = "codexPetStudio.previewer.locale";
  const i18nBundle = window.PET_PREVIEW_I18N;
  const deliveryTarget = window.PET_DELIVERY_TARGET;
  const bundledConfig = window.PET_PREVIEW_CONFIG;
  const generatedAtlases = new Map();
  const takeAssetStatus = new Map();
  const PREVIEW_SIZE_INITIAL_PX = 160;
  const LOOK_ORBIT_STEP_MS = 120;
  const TOUR_PROGRESS_STEP_MS = 160;
  const ASSET_PREFLIGHT_TIMEOUT_MS = 8000;
  const STANDARD_INTERMEDIATE_PHASE = "standard-intermediate";
  const FINAL_V2_PHASE = "codex-pet-v2-final";
  const DIAGNOSTIC_FACT_MAX_LENGTH = 180;
  const URL_FACT_PATTERN = /\b[a-z][a-z0-9+.-]*:\/\/[^\s<>"']+/gi;
  const KEYFRAME_COLUMNS = 4;
  const ORIGINAL_TAKE_ID = "original";
  const STATIC_STATE_ID = "static";
  const PROJECT_ASSET_URL_PATTERN = /^(?:\.\/)?(?!\.\.(?:\/|$))[A-Za-z0-9._~-]+(?:\/(?!\.\.(?:\/|$))[A-Za-z0-9._~-]+)*$/;
  const REVIEW_CONTEXT_PARAMS = Object.freeze({
    candidate: "candidate",
    state: "state",
    frame: "frame",
    take: "take",
  });

  const elements = {
    animationControls: document.querySelector("#animationControls"),
    animationTab: document.querySelector("#animationTab"),
    atlasPhaseBadge: document.querySelector("#atlasPhaseBadge"),
    autoPlayStatesToggle: document.querySelector("#autoPlayStatesToggle"),
    configError: document.querySelector("#configError"),
    configErrorActual: document.querySelector("#configErrorActual"),
    configErrorActualRow: document.querySelector("#configErrorActualRow"),
    configErrorCandidate: document.querySelector("#configErrorCandidate"),
    configErrorCandidateRow: document.querySelector("#configErrorCandidateRow"),
    configErrorCode: document.querySelector("#configErrorCode"),
    configErrorConfig: document.querySelector("#configErrorConfig"),
    configErrorExpected: document.querySelector("#configErrorExpected"),
    configErrorExpectedRow: document.querySelector("#configErrorExpectedRow"),
    configErrorField: document.querySelector("#configErrorField"),
    configErrorFieldRow: document.querySelector("#configErrorFieldRow"),
    configErrorNextStep: document.querySelector("#configErrorNextStep"),
    configErrorScope: document.querySelector("#configErrorScope"),
    configErrorSummary: document.querySelector("#configErrorSummary"),
    configErrorTitle: document.querySelector("#configErrorTitle"),
    directionList: document.querySelector("#directionList"),
    directionTarget: document.querySelector("#directionTarget"),
    endlessModeButton: document.querySelector("#endlessModeButton"),
    followPointerButton: document.querySelector("#followPointerButton"),
    frameReadout: document.querySelector("#frameReadout"),
    frameSectionTitle: document.querySelector("#frameSectionTitle"),
    frameStrip: document.querySelector("#frameStrip"),
    languageSelect: document.querySelector("#languageSelect"),
    lookControls: document.querySelector("#lookControls"),
    lookTab: document.querySelector("#lookTab"),
    mechanicsBoard: document.querySelector("#mechanicsBoard"),
    mechanicsRows: document.querySelector("#mechanicsRows"),
    mechanicsSummary: document.querySelector("#mechanicsSummary"),
    nextFrameButton: document.querySelector("#nextFrameButton"),
    orbitButton: document.querySelector("#orbitButton"),
    playPauseButton: document.querySelector("#playPauseButton"),
    previewModeHelp: document.querySelector("#previewModeHelp"),
    previewSizeInput: document.querySelector("#previewSizeInput"),
    previewSizeValue: document.querySelector("#previewSizeValue"),
    previousFrameButton: document.querySelector("#previousFrameButton"),
    previewFooter: document.querySelector("#previewFooter"),
    restartButton: document.querySelector("#restartButton"),
    runtimeModeButton: document.querySelector("#runtimeModeButton"),
    runtimeStateHeading: document.querySelector("#runtimeStateHeading"),
    spritePlayer: document.querySelector("#spritePlayer"),
    stage: document.querySelector("#stage"),
    stageModeLabel: document.querySelector("#stageModeLabel"),
    staticList: document.querySelector("#staticList"),
    staticSection: document.querySelector("#staticSection"),
    stateCount: document.querySelector("#stateCount"),
    stateDescription: document.querySelector("#stateDescription"),
    stateDuration: document.querySelector("#stateDuration"),
    stateIntent: document.querySelector("#stateIntent"),
    stateList: document.querySelector("#stateList"),
    stateTag: document.querySelector("#stateTag"),
    stateTitle: document.querySelector("#stateTitle"),
    stateTrigger: document.querySelector("#stateTrigger"),
    takeStatus: document.querySelector("#takeStatus"),
    tourLabel: document.querySelector("#tourLabel"),
    tourProgress: document.querySelector("#tourProgress"),
    tourProgressBar: document.querySelector("#tourProgressBar"),
    tourProgressText: document.querySelector("#tourProgressText"),
    topbar: document.querySelector("#topbar"),
    transportControls: document.querySelector("#transportControls"),
    versionSelect: document.querySelector("#versionSelect"),
    versionStatus: document.querySelector("#versionStatus"),
    workspace: document.querySelector("#workspace"),
  };

  let config = null;
  let configBaseUrl = window.location.href;
  let activeDiagnostic = null;
  let configReference = "";
  const candidateAvailability = new Map();
  let reviewContextReady = false;
  let reviewFocus = {
    candidateId: "",
    stateId: "",
    frameIndex: null,
    takeId: null,
  };
  let locale = resolveInitialLocale();
  let activeVersionId = "";
  let activeStateIndex = 0;
  let activeFrameIndex = 0;
  let expandedTakeFrameIndex = null;
  let activeFrameTake = null;
  const confirmedFrameTakeIds = new Map();
  let activeDirectionIndex = 0;
  let lookIsNeutral = false;
  let playbackMode = "runtime";
  let isInspectingFrame = false;
  let sectionMode = "animation";
  let isPlaying = true;
  let previewSizePx = PREVIEW_SIZE_INITIAL_PX;
  let activeBackground = "paper";
  let frameTimer = null;
  let orbitTimer = null;
  let pointerFrameRequest = null;
  let pendingPointerSample = null;
  let lookControlMode = "manual";
  let pageVisible = document.visibilityState !== "hidden";
  let runtimeFramesCompleted = 0;
  let runtimeLoopsCompleted = 0;
  let runtimeFellBack = false;
  let tourTimer = null;
  let tourProgressTimer = null;
  let tourState = {
    active: false,
    completed: false,
    index: 0,
    startedAt: 0,
    holdMs: 0,
  };
  let stateButtons = [];
  let frameButtons = [];
  let takeButtons = [];
  let takeConfirmButton = null;
  let directionButtons = [];
  const spriteStyleCache = new WeakMap();

  function getStoredLocale() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  }

  function storeLocale(nextLocale) {
    try {
      window.localStorage.setItem(STORAGE_KEY, nextLocale);
    } catch {
      return;
    }
  }

  function supportedLocale(candidate) {
    if (!candidate) return null;
    const normalized = candidate.toLowerCase();
    const exact = i18nBundle.locales.find(
      (item) => item.id.toLowerCase() === normalized,
    );
    if (exact) return exact.id;
    if (normalized.startsWith("zh")) return "zh-CN";
    if (normalized.startsWith("en")) return "en";
    return null;
  }

  function resolveInitialLocale() {
    const stored = supportedLocale(getStoredLocale());
    if (stored) return stored;

    const browserLocales = [
      ...(window.navigator.languages || []),
      window.navigator.language,
    ];
    for (const browserLocale of browserLocales) {
      const match = supportedLocale(browserLocale);
      if (match) return match;
    }
    return i18nBundle.fallbackLocale;
  }

  function valueAtPath(source, path) {
    return path
      .split(".")
      .reduce(
        (value, segment) =>
          value && Object.prototype.hasOwnProperty.call(value, segment)
            ? value[segment]
            : undefined,
        source,
      );
  }

  function interpolate(value, variables) {
    if (typeof value !== "string") return value;
    return value.replace(/\{([a-zA-Z0-9_]+)\}/g, (match, key) =>
      Object.prototype.hasOwnProperty.call(variables, key)
        ? String(variables[key])
        : match,
    );
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function t(key, variables = {}) {
    const currentMessages = i18nBundle.messages[locale] || {};
    const fallbackMessages =
      i18nBundle.messages[i18nBundle.fallbackLocale] || {};
    let value = valueAtPath(currentMessages, key);
    if (value === undefined) value = valueAtPath(fallbackMessages, key);
    if (value === undefined) {
      console.warn(`Missing translation: ${key}`);
      return key;
    }
    return interpolate(value, variables);
  }

  function deepMerge(target, source) {
    if (!source || typeof source !== "object") return target;
    Object.entries(source).forEach(([key, value]) => {
      if (
        value &&
        typeof value === "object" &&
        !Array.isArray(value) &&
        target[key] &&
        typeof target[key] === "object" &&
        !Array.isArray(target[key])
      ) {
        deepMerge(target[key], value);
      } else {
        target[key] = value;
      }
    });
    return target;
  }

  function cloneValue(value) {
    return JSON.parse(JSON.stringify(value));
  }

  class PreviewDiagnosticError extends Error {
    constructor(diagnostic, cause = null) {
      super(diagnostic.code);
      this.name = "PreviewDiagnosticError";
      this.diagnostic = diagnostic;
      this.cause = cause;
    }
  }

  function boundedDiagnosticFact(value) {
    if (value.length <= DIAGNOSTIC_FACT_MAX_LENGTH) return value;
    return `${value.slice(0, DIAGNOSTIC_FACT_MAX_LENGTH - 1)}…`;
  }

  function sanitizedUrlFact(value) {
    try {
      const url = new URL(value);
      if (url.protocol === "file:") return "[local file]";
      if (!["http:", "https:"].includes(url.protocol)) {
        return "[external URL]";
      }
      const sensitivePath =
        /^\/(?:Users|home|private|tmp|Volumes)(?:\/|$)/i.test(
          url.pathname,
        ) || /^\/var\/folders(?:\/|$)/i.test(url.pathname);
      return (
        `${url.protocol}//${url.host}` +
        `${sensitivePath ? "/[local path]" : url.pathname}` +
        `${url.search ? "?…" : ""}`
      );
    } catch {
      return "[invalid URL]";
    }
  }

  function safeFact(value) {
    if (value === null || value === undefined || value === "") return "";
    const urls = [];
    let text = Array.isArray(value) ? value.join(", ") : String(value);
    text = text
      .replace(/[\u0000-\u001f\u007f]/g, " ")
      .replace(URL_FACT_PATTERN, (url) => {
        const index = urls.push(sanitizedUrlFact(url)) - 1;
        return `DIAGNOSTIC_URL_${index}_TOKEN`;
      })
      .replace(
        /(^|[\s([{=:'"])(\/(?!\/)[^\s<>"'`;,)\]}]*)/g,
        (_match, prefix) => `${prefix}[local path]`,
      )
      .replace(/\b[A-Za-z]:\\[^\s<>"'`;,)\]}]*/g, "[local path]");
    urls.forEach((url, index) => {
      text = text.replace(`DIAGNOSTIC_URL_${index}_TOKEN`, url);
    });
    return boundedDiagnosticFact(text);
  }

  function makeDiagnostic({
    scope,
    code,
    candidateId = "",
    field = "",
    expected = "",
    actual = "",
    nextStepKey = "ui.diagnosticNextRestage",
  }) {
    return Object.freeze({
      scope,
      code,
      configRef: configReference || "preview config",
      candidateId: safeFact(candidateId),
      field: safeFact(field),
      expected: safeFact(expected),
      actual: safeFact(actual),
      nextStepKey,
    });
  }

  function failDiagnostic(facts, cause = null) {
    throw new PreviewDiagnosticError(makeDiagnostic(facts), cause);
  }

  function diagnosticFromError(error, fallback) {
    if (error instanceof PreviewDiagnosticError) return error.diagnostic;
    return makeDiagnostic(fallback);
  }

  function safeConfigReference(url) {
    try {
      const resolved = new URL(url, window.location.href);
      if (resolved.protocol === "file:") return t("ui.localPreviewConfig");
      if (!["http:", "https:"].includes(resolved.protocol)) {
        return "preview config";
      }
      const sensitivePath =
        /^\/(?:Users|home|private|tmp|Volumes)(?:\/|$)/i.test(
          resolved.pathname,
        ) || /^\/var\/folders(?:\/|$)/i.test(resolved.pathname);
      return boundedDiagnosticFact(
        `${sensitivePath ? "/[local path]" : resolved.pathname}` +
          `${resolved.search ? "?…" : ""}`,
      );
    } catch {
      return "preview config";
    }
  }

  function targetBackedConfig() {
    if (
      !deliveryTarget ||
      !deliveryTarget.atlas ||
      !deliveryTarget.runtime ||
      !deliveryTarget.display ||
      !Array.isArray(deliveryTarget.states) ||
      !deliveryTarget.lookDirections ||
      typeof deliveryTarget.lookDirections.neutralStateId !== "string" ||
      !deliveryTarget.lookDirections.neutralReferenceSlot ||
      !Array.isArray(deliveryTarget.lookDirections.slots)
    ) {
      throw new Error("The generated Delivery Target adapter is missing or invalid.");
    }

    return {
      deliveryTarget: {
        id: deliveryTarget.id,
        revision: deliveryTarget.revision,
      },
      sprite: {
        columns: deliveryTarget.atlas.columns,
        rows: deliveryTarget.atlas.rows,
        frameWidth: deliveryTarget.atlas.cellWidthPx,
        frameHeight: deliveryTarget.atlas.cellHeightPx,
      },
      runtime: cloneValue(deliveryTarget.runtime),
      display: cloneValue(deliveryTarget.display),
      states: deliveryTarget.states.map((state) => ({
        id: state.id,
        row: state.row,
        firstColumn: state.firstColumn,
        durations: cloneValue(state.durationsMs),
      })),
      neutralLookStateId: deliveryTarget.lookDirections.neutralStateId,
      neutralLookReferenceSlot: cloneValue(
        deliveryTarget.lookDirections.neutralReferenceSlot,
      ),
      directions: cloneValue(deliveryTarget.lookDirections.slots),
    };
  }

  function assertCompatibleTarget(projectConfig) {
    const requested = projectConfig && projectConfig.deliveryTarget;
    if (!requested) return;
    if (
      requested.id !== deliveryTarget.id ||
      requested.revision !== deliveryTarget.revision
    ) {
      failDiagnostic({
        scope: "global",
        code: "TARGET_MISMATCH",
        field: "deliveryTarget",
        expected: `${deliveryTarget.id} revision ${deliveryTarget.revision}`,
        actual: `${safeFact(requested.id)} revision ${safeFact(requested.revision)}`,
        nextStepKey: "ui.diagnosticNextTarget",
      });
    }
  }

  function declaredCandidateAssetReferences(version) {
    const references = [];
    const add = (value, field) => {
      if (value !== undefined && value !== null) references.push({ value, field });
    };
    add(version && version.atlasUrl, "atlasUrl");
    if (version && version.static) {
      add(version.static.assetUrl, "static.assetUrl");
      if (Array.isArray(version.static.takes)) {
        version.static.takes.forEach((take, index) => {
          add(take && take.assetUrl, `static.takes[${index}].assetUrl`);
        });
      }
    }
    if (version && Array.isArray(version.frameTakes)) {
      version.frameTakes.forEach((group, groupIndex) => {
        if (!group || !Array.isArray(group.takes)) return;
        group.takes.forEach((take, takeIndex) => {
          if (take && Object.prototype.hasOwnProperty.call(take, "assetUrl")) {
            add(
              take.assetUrl,
              `frameTakes[${groupIndex}].takes[${takeIndex}].assetUrl`,
            );
          }
        });
      });
    }
    return references;
  }

  function assertSafeProjectAssetReference(reference, candidateId) {
    if (
      typeof reference.value !== "string" ||
      !PROJECT_ASSET_URL_PATTERN.test(reference.value)
    ) {
      failDiagnostic({
        scope: "global",
        code: "UNSAFE_ASSET_URL",
        candidateId,
        field: `Candidate ${candidateId}.${reference.field}`,
        expected: "a config-relative path without .., query, or fragment",
        actual: "unsafe or invalid asset reference",
        nextStepKey: "ui.diagnosticNextSafeUrl",
      });
    }
  }

  function assertProjectEnvelope(projectConfig, { trustedBundled = false } = {}) {
    if (
      !projectConfig ||
      projectConfig.schemaVersion !== 1 ||
      !projectConfig.pet ||
      typeof projectConfig.pet.name !== "string" ||
      !projectConfig.pet.name.trim() ||
      !Array.isArray(projectConfig.versions) ||
      projectConfig.versions.length === 0
    ) {
      failDiagnostic({
        scope: "global",
        code: "CONFIG_INVALID",
        field: "schemaVersion, pet, or versions",
        expected: "schemaVersion 1 with a named pet and at least one Candidate",
        actual: "missing or invalid project config fields",
        nextStepKey: "ui.diagnosticNextRestage",
      });
    }
    assertCompatibleTarget(projectConfig);
    const ids = new Set();
    projectConfig.versions.forEach((version, index) => {
      if (
        !version ||
        typeof version.id !== "string" ||
        !version.id.trim()
      ) {
        failDiagnostic({
          scope: "global",
          code: "CONFIG_INVALID",
          field: `versions[${index}].id`,
          expected: "a unique non-empty Candidate id",
          actual: "missing or invalid Candidate id",
        });
      }
      if (ids.has(version.id)) {
        failDiagnostic({
          scope: "global",
          code: "DUPLICATE_CANDIDATE_ID",
          candidateId: version.id,
          field: `versions[${index}].id`,
          expected: "a unique Candidate id",
          actual: version.id,
        });
      }
      ids.add(version.id);
      if (!trustedBundled) {
        declaredCandidateAssetReferences(version).forEach((reference) =>
          assertSafeProjectAssetReference(reference, version.id),
        );
      }
    });
  }

  function assertReviewableCandidate(version) {
    const candidateId = version.id;
    const hasStatic = Boolean(
      version.static &&
        typeof version.static.assetUrl === "string" &&
        version.static.assetUrl,
    );
    const hasAtlas =
      typeof version.atlasUrl === "string" && Boolean(version.atlasUrl);
    if (!hasStatic && !hasAtlas) {
      failDiagnostic({
        scope: "candidate",
        code: "CANDIDATE_INVALID",
        candidateId,
        field: `Candidate ${candidateId}`,
        expected: "a Static asset or runtime atlas",
        actual: "no reviewable asset",
      });
    }
    if (version.stateIds !== undefined) {
      if (
        !Array.isArray(version.stateIds) ||
        version.stateIds.some((stateId) => typeof stateId !== "string")
      ) {
        failDiagnostic({
          scope: "candidate",
          code: "INVALID_STATE_IDS",
          candidateId,
          field: `Candidate ${candidateId}.stateIds`,
          expected: "an array of Delivery Target state ids",
          actual: "invalid stateIds",
          nextStepKey: "ui.diagnosticNextStates",
        });
      }
      const uniqueIds = new Set(version.stateIds);
      if (uniqueIds.size !== version.stateIds.length) {
        failDiagnostic({
          scope: "candidate",
          code: "DUPLICATE_STATE_ID",
          candidateId,
          field: `Candidate ${candidateId}.stateIds`,
          expected: "each state exactly once",
          actual: version.stateIds,
          nextStepKey: "ui.diagnosticNextStates",
        });
      }
      const knownIds = new Set(deliveryTarget.states.map((state) => state.id));
      const unknownIds = version.stateIds.filter((stateId) => !knownIds.has(stateId));
      if (unknownIds.length) {
        failDiagnostic({
          scope: "candidate",
          code: "UNKNOWN_STATE_ID",
          candidateId,
          field: `Candidate ${candidateId}.stateIds`,
          expected: [...knownIds],
          actual: unknownIds,
          nextStepKey: "ui.diagnosticNextStates",
        });
      }
      if (version.stateIds.length > 0 && !hasAtlas) {
        failDiagnostic({
          scope: "candidate",
          code: "MISSING_ATLAS",
          candidateId,
          field: `Candidate ${candidateId}.atlasUrl`,
          expected: "an atlas for declared runtime states",
          actual: "missing",
          nextStepKey: "ui.diagnosticNextAtlas",
        });
      }
      if (version.stateIds.length === 0 && !hasStatic) {
        failDiagnostic({
          scope: "candidate",
          code: "MISSING_STATE",
          candidateId,
          field: `Candidate ${candidateId}.stateIds`,
          expected: "at least one state or a Static study",
          actual: "no reviewable state",
          nextStepKey: "ui.diagnosticNextStates",
        });
      }
    }
    if (
      version.lookDirectionsAvailable !== undefined &&
      typeof version.lookDirectionsAvailable !== "boolean"
    ) {
      failDiagnostic({
        scope: "candidate",
        code: "INVALID_LOOK_DIRECTIONS",
        candidateId,
        field: `Candidate ${candidateId}.lookDirectionsAvailable`,
        expected: "true or false",
        actual: version.lookDirectionsAvailable,
        nextStepKey: "ui.diagnosticNextAtlas",
      });
    }
    if (version.lookDirectionsAvailable === true && !hasAtlas) {
      failDiagnostic({
        scope: "candidate",
        code: "MISSING_ATLAS",
        candidateId,
        field: `Candidate ${candidateId}.atlasUrl`,
        expected: "an atlas for look directions",
        actual: "missing",
        nextStepKey: "ui.diagnosticNextAtlas",
      });
    }
    const atlasPhase = version.atlasPhase;
    if (
      atlasPhase !== undefined &&
      ![STANDARD_INTERMEDIATE_PHASE, FINAL_V2_PHASE].includes(atlasPhase)
    ) {
      failDiagnostic({
        scope: "candidate",
        code: "INVALID_ATLAS_PHASE",
        candidateId,
        field: `Candidate ${candidateId}.atlasPhase`,
        expected: [STANDARD_INTERMEDIATE_PHASE, FINAL_V2_PHASE],
        actual: atlasPhase,
        nextStepKey: "ui.diagnosticNextAtlas",
      });
    }
    if (atlasPhase !== undefined && !hasAtlas) {
      failDiagnostic({
        scope: "candidate",
        code: "MISSING_ATLAS",
        candidateId,
        field: `Candidate ${candidateId}.atlasPhase`,
        expected: "atlasUrl for a declared atlas phase",
        actual: "missing atlasUrl",
        nextStepKey: "ui.diagnosticNextAtlas",
      });
    }
    if (
      atlasPhase === STANDARD_INTERMEDIATE_PHASE &&
      version.lookDirectionsAvailable !== false
    ) {
      failDiagnostic({
        scope: "candidate",
        code: "ATLAS_PHASE_MISMATCH",
        candidateId,
        field: `Candidate ${candidateId}.lookDirectionsAvailable`,
        expected: "false for a standard-intermediate review atlas",
        actual: version.lookDirectionsAvailable,
        nextStepKey: "ui.diagnosticNextAtlas",
      });
    }
    if (
      atlasPhase === FINAL_V2_PHASE &&
      version.lookDirectionsAvailable !== true
    ) {
      failDiagnostic({
        scope: "candidate",
        code: "ATLAS_PHASE_MISMATCH",
        candidateId,
        field: `Candidate ${candidateId}.lookDirectionsAvailable`,
        expected: "true for a codex-pet-v2-final atlas",
        actual: version.lookDirectionsAvailable,
        nextStepKey: "ui.diagnosticNextAtlas",
      });
    }
  }

  function resolveSafeProjectAssetUrl(
    path,
    baseUrl,
    { candidateId, field, trustedBundled = false },
  ) {
    if (
      typeof path !== "string" ||
      !path.trim() ||
      (!trustedBundled && !PROJECT_ASSET_URL_PATTERN.test(path.trim()))
    ) {
      failDiagnostic({
        scope: trustedBundled ? "candidate" : "global",
        code: "UNSAFE_ASSET_URL",
        candidateId,
        field,
        expected: "a safe config-relative asset path",
        actual: "unsafe or invalid asset reference",
        nextStepKey: "ui.diagnosticNextSafeUrl",
      });
    }
    const url = new URL(path.trim(), baseUrl);
    const base = new URL(baseUrl, window.location.href);
    if (
      !["http:", "https:"].includes(url.protocol) ||
      url.origin !== base.origin ||
      url.username ||
      url.password
    ) {
      failDiagnostic({
        scope: trustedBundled ? "candidate" : "global",
        code: "UNSAFE_ASSET_URL",
        candidateId,
        field,
        expected: "a same-origin HTTP asset URL without credentials",
        actual: "unsafe asset origin",
        nextStepKey: "ui.diagnosticNextSafeUrl",
      });
    }
    return url.href;
  }

  function atlasCellsForVersion(version) {
    const cells = new Map();
    const addCell = (row, column, label) => {
      if (
        Number.isInteger(row) &&
        Number.isInteger(column) &&
        row >= 0 &&
        row < deliveryTarget.atlas.rows &&
        column >= 0 &&
        column < deliveryTarget.atlas.columns
      ) {
        cells.set(`${row}:${column}`, { row, column, label });
      }
    };
    const stateIds = Array.isArray(version.stateIds)
      ? new Set(version.stateIds)
      : null;
    deliveryTarget.states.forEach((state) => {
      if (stateIds && !stateIds.has(state.id)) return;
      state.durationsMs.forEach((_duration, index) => {
        addCell(
          state.row,
          state.firstColumn + index,
          `${version.id}/${state.id}/frame-${index + 1}`,
        );
      });
    });
    const hasLookDirections =
      typeof version.lookDirectionsAvailable === "boolean"
        ? version.lookDirectionsAvailable
        : !stateIds;
    if (hasLookDirections) {
      deliveryTarget.lookDirections.slots.forEach((slot) => {
        addCell(
          slot.row,
          slot.column,
          `${version.id}/look-${slot.degree}-${slot.key}`,
        );
      });
      const neutral = deliveryTarget.lookDirections.neutralReferenceSlot;
      addCell(
        neutral.row,
        neutral.column,
        `${version.id}/look-neutral`,
      );
    }
    if (Array.isArray(version.frameTakes)) {
      version.frameTakes.forEach((group) => {
        if (!group || !Array.isArray(group.takes)) return;
        group.takes.forEach((take) => {
          if (take && take.atlasSlot) {
            addCell(
              take.atlasSlot.row,
              take.atlasSlot.column,
              `${version.id}/atlas Take ${String(take.id)}`,
            );
          }
        });
      });
    }
    return [...cells.values()];
  }

  function projectAssetEntries(
    version,
    baseUrl,
    { trustedBundled = false } = {},
  ) {
    const entries = [];
    const versionLabel = `Candidate ${String(version.id)}`;
    const resolveEntryUrl = (path, field) =>
      resolveSafeProjectAssetUrl(path, baseUrl, {
        candidateId: version.id,
        field,
        trustedBundled,
      });
    if (version.static && version.static.assetUrl) {
      const field = `Candidate ${version.id}.static.assetUrl`;
      entries.push({
        url: resolveEntryUrl(version.static.assetUrl, field),
        label: `${versionLabel} Static`,
        field,
        kind: "standalone",
        candidateId: version.id,
      });
      if (Array.isArray(version.static.takes)) {
        version.static.takes.forEach((take, index) => {
          if (!take || !take.assetUrl) return;
          const takeField =
            `Candidate ${version.id}.static.takes[${index}].assetUrl`;
          entries.push({
            url: resolveEntryUrl(take.assetUrl, takeField),
            label: `${versionLabel} Static Take ${String(take.id)}`,
            field: takeField,
            kind: "standalone",
            candidateId: version.id,
          });
        });
      }
    }
    if (version.atlasUrl) {
      const field = `Candidate ${version.id}.atlasUrl`;
      entries.push({
        url: resolveEntryUrl(version.atlasUrl, field),
        label: `${versionLabel} atlas`,
        field,
        kind: "atlas",
        cells: atlasCellsForVersion(version),
        candidateId: version.id,
      });
    }
    if (Array.isArray(version.frameTakes)) {
      version.frameTakes.forEach((group, groupIndex) => {
        if (!group || !Array.isArray(group.takes)) return;
        group.takes.forEach((take, takeIndex) => {
          if (!take || !take.assetUrl) return;
          const field =
            `Candidate ${version.id}.frameTakes[${groupIndex}]` +
            `.takes[${takeIndex}].assetUrl`;
          entries.push({
            url: resolveEntryUrl(take.assetUrl, field),
            label: `${versionLabel} runtime Take ${String(take.id)}`,
            field,
            kind: "runtime-take",
            candidateId: version.id,
          });
        });
      });
    }
    return entries;
  }

  function loadAssetForPreflight(entry) {
    return new Promise((resolve, reject) => {
      const probe = new Image();
      let settled = false;
      const finish = (callback, value) => {
        if (settled) return;
        settled = true;
        window.clearTimeout(timeoutId);
        callback(value);
      };
      const timeoutId = window.setTimeout(
        () =>
          finish(
            reject,
            new PreviewDiagnosticError(
              makeDiagnostic({
                scope: "candidate",
                code: "ASSET_LOAD_TIMEOUT",
                candidateId: entry.candidateId,
                field: entry.field,
                expected: "a locally readable staged asset",
                actual: "asset load timed out",
                nextStepKey: "ui.diagnosticNextRestage",
              }),
            ),
          ),
        ASSET_PREFLIGHT_TIMEOUT_MS,
      );
      probe.decoding = "async";
      probe.addEventListener("load", () => finish(resolve, probe), {
        once: true,
      });
      probe.addEventListener(
        "error",
        () =>
          finish(
            reject,
            new PreviewDiagnosticError(
              makeDiagnostic({
                scope: "candidate",
                code: "ASSET_DECODE_FAILED",
                candidateId: entry.candidateId,
                field: entry.field,
                expected: "a decodable transparent image",
                actual: "asset could not be decoded",
              }),
            ),
          ),
        { once: true },
      );
      probe.src = entry.url;
    });
  }

  function alphaFacts(imageData) {
    let hasVisible = false;
    let hasTransparent = false;
    for (let index = 3; index < imageData.length; index += 4) {
      const alpha = imageData[index];
      hasVisible = hasVisible || alpha > 0;
      hasTransparent = hasTransparent || alpha < 255;
      if (hasVisible && hasTransparent) break;
    }
    return { hasVisible, hasTransparent };
  }

  function requireTransparentPixels(context, rect, entry, field = entry.field) {
    const pixels = context.getImageData(
      rect.x,
      rect.y,
      rect.width,
      rect.height,
    ).data;
    const facts = alphaFacts(pixels);
    if (!facts.hasVisible) {
      failDiagnostic({
        scope: "candidate",
        code: "ASSET_FULLY_TRANSPARENT",
        candidateId: entry.candidateId,
        field,
        expected: "visible pixels with transparent background",
        actual: "fully transparent",
      });
    }
    if (!facts.hasTransparent) {
      failDiagnostic({
        scope: "candidate",
        code: "ASSET_FULLY_OPAQUE",
        candidateId: entry.candidateId,
        field,
        expected: "visible pixels with transparent background",
        actual: "fully opaque",
        nextStepKey: "ui.diagnosticNextTransparency",
      });
    }
  }

  async function assertTransparentCandidateAssets(
    version,
    baseUrl,
    { trustedBundled = false } = {},
  ) {
    assertReviewableCandidate(version);
    const entries = projectAssetEntries(version, baseUrl, { trustedBundled });
    const imageCache = new Map();
    for (const entry of entries) {
      let imagePromise = imageCache.get(entry.url);
      if (!imagePromise) {
        imagePromise = loadAssetForPreflight(entry);
        imageCache.set(entry.url, imagePromise);
      }
      const image = await imagePromise;
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const context = canvas.getContext("2d", {
        alpha: true,
        willReadFrequently: true,
      });
      if (!context) {
        failDiagnostic({
          scope: "candidate",
          code: "ASSET_INSPECTION_FAILED",
          candidateId: entry.candidateId,
          field: entry.field,
          expected: "browser transparency inspection",
          actual: "canvas unavailable",
        });
      }
      context.drawImage(image, 0, 0);
      if (entry.kind === "atlas") {
        const expectedWidth =
          deliveryTarget.atlas.columns *
          deliveryTarget.atlas.cellWidthPx;
        const expectedHeight =
          deliveryTarget.atlas.rows *
          deliveryTarget.atlas.cellHeightPx;
        if (
          image.naturalWidth !== expectedWidth ||
          image.naturalHeight !== expectedHeight
        ) {
          failDiagnostic({
            scope: "candidate",
            code: "ATLAS_GEOMETRY_MISMATCH",
            candidateId: entry.candidateId,
            field: entry.field,
            expected: `${expectedWidth}x${expectedHeight}`,
            actual: `${image.naturalWidth}x${image.naturalHeight}`,
            nextStepKey: "ui.diagnosticNextAtlas",
          });
        }
        entry.cells.forEach((cell) => {
          requireTransparentPixels(
            context,
            {
              x: cell.column * deliveryTarget.atlas.cellWidthPx,
              y: cell.row * deliveryTarget.atlas.cellHeightPx,
              width: deliveryTarget.atlas.cellWidthPx,
              height: deliveryTarget.atlas.cellHeightPx,
            },
            entry,
            `Candidate ${entry.candidateId}.atlas.${cell.label}`,
          );
        });
      } else {
        if (
          entry.kind === "runtime-take" &&
          (image.naturalWidth !== deliveryTarget.atlas.cellWidthPx ||
            image.naturalHeight !== deliveryTarget.atlas.cellHeightPx)
        ) {
          failDiagnostic({
            scope: "candidate",
            code: "ASSET_GEOMETRY_MISMATCH",
            candidateId: entry.candidateId,
            field: entry.field,
            expected:
              `${deliveryTarget.atlas.cellWidthPx}x` +
              `${deliveryTarget.atlas.cellHeightPx}`,
            actual: `${image.naturalWidth}x${image.naturalHeight}`,
            nextStepKey: "ui.diagnosticNextAtlas",
          });
        }
        requireTransparentPixels(
          context,
          {
            x: 0,
            y: 0,
            width: image.naturalWidth,
            height: image.naturalHeight,
          },
          entry,
        );
      }
    }
  }

  function withMechanicsOverrides(baseMechanics, projectMechanics) {
    if (!Array.isArray(projectMechanics)) {
      return baseMechanics;
    }

    const overrides = new Map(
      projectMechanics
        .filter((item) => item && item.stateId)
        .map((item) => [item.stateId, item]),
    );
    return baseMechanics.map((board) => {
      const override = overrides.get(board.stateId);
      if (!override) return board;
      const overrideAnchors = Array.isArray(override.anchors)
        ? override.anchors
        : [];
      const anchorCount = Math.max(
        board.anchors.length,
        overrideAnchors.length,
      );
      return {
        ...board,
        ...override,
        stateId: board.stateId,
        anchors: Array.from(
          { length: anchorCount },
          (_, index) =>
            overrideAnchors[index] || board.anchors[index] || `A${index}`,
        ),
      };
    });
  }

  function withBundledExample(projectVersions, bundledVersions) {
    const versions = cloneValue(projectVersions);
    const usedIds = new Set(versions.map((version) => version.id));
    let exampleId = "example-raincoat-cat";
    let suffix = 2;
    while (usedIds.has(exampleId)) {
      exampleId = `example-raincoat-cat-${suffix}`;
      suffix += 1;
    }

    const bundledDefault =
      bundledVersions.find((version) => version.isDefault) ||
      bundledVersions[0];
    const example = {
      ...cloneValue(bundledDefault),
      id: exampleId,
      displayName: "Example.RaincoatCat",
      labelKey: "ui.exampleVersion",
      statusKey: null,
      isDefault: false,
      isBundledExample: true,
    };
    return [...versions, example];
  }

  async function inspectCandidate(
    version,
    baseUrl,
    { trustedBundled = false } = {},
  ) {
    try {
      await assertTransparentCandidateAssets(version, baseUrl, {
        trustedBundled,
      });
      return { status: "valid", diagnostic: null };
    } catch (error) {
      console.warn(`Could not validate Candidate ${version.id}.`, error);
      return {
        status: "invalid",
        diagnostic: diagnosticFromError(error, {
          scope: "candidate",
          code: "CANDIDATE_INVALID",
          candidateId: version.id,
          field: `Candidate ${version.id}`,
          expected: "a reviewable Candidate",
          actual: "validation failed",
        }),
      };
    }
  }

  function preferredCandidate(projectConfig, requestedCandidateId) {
    if (requestedCandidateId !== null) {
      return (
        projectConfig.versions.find(
          (version) => version.id === requestedCandidateId,
        ) || null
      );
    }
    return (
      projectConfig.versions.find((version) => version.isDefault) ||
      projectConfig.versions[0]
    );
  }

  async function loadConfig(requestedReviewContext) {
    candidateAvailability.clear();
    const configUrl = new URLSearchParams(window.location.search).get("config");
    if (!configUrl) {
      configReference = safeConfigReference(window.location.href);
      try {
        assertProjectEnvelope(bundledConfig, { trustedBundled: true });
        const selected = preferredCandidate(
          bundledConfig,
          requestedReviewContext.candidateId,
        );
        if (!selected) {
          const diagnostic = makeDiagnostic({
            scope: "focus",
            code: "CANDIDATE_NOT_FOUND",
            candidateId: requestedReviewContext.candidateId,
            field: "candidate",
            expected: bundledConfig.versions.map((version) => version.id),
            actual: requestedReviewContext.candidateId,
            nextStepKey: "ui.diagnosticNextCandidate",
          });
          return {
            data: bundledConfig,
            baseUrl: window.location.href,
            isExternal: false,
            externalLoadFailed: false,
            globalDiagnostic: null,
            activeDiagnostic: diagnostic,
            selectedCandidateId: requestedReviewContext.candidateId,
            backgroundCandidates: [...bundledConfig.versions],
          };
        }
        candidateAvailability.set(selected.id, { status: "checking" });
        const result = await inspectCandidate(selected, window.location.href, {
          trustedBundled: true,
        });
        candidateAvailability.set(selected.id, result);
        return {
          data: bundledConfig,
          baseUrl: window.location.href,
          isExternal: false,
          externalLoadFailed: false,
          globalDiagnostic: null,
          activeDiagnostic: result.diagnostic,
          selectedCandidateId: selected.id,
          backgroundCandidates: bundledConfig.versions.filter(
            (version) => version.id !== selected.id,
          ),
        };
      } catch (error) {
        console.warn("Could not validate bundled preview assets.", error);
        return {
          data: bundledConfig,
          baseUrl: window.location.href,
          isExternal: false,
          externalLoadFailed: true,
          globalDiagnostic: diagnosticFromError(error, {
            scope: "global",
            code: "CONFIG_INVALID",
            field: "bundled Previewer config",
            expected: "a valid bundled Example",
            actual: "validation failed",
          }),
          activeDiagnostic: null,
          selectedCandidateId: "",
          backgroundCandidates: [],
        };
      }
    }

    try {
      const resolvedUrl = new URL(configUrl, window.location.href);
      configReference = safeConfigReference(resolvedUrl.href);
      const response = await window.fetch(resolvedUrl);
      if (!response.ok) {
        failDiagnostic({
          scope: "global",
          code: "CONFIG_FETCH_FAILED",
          field: "config",
          expected: "HTTP 200",
          actual: `HTTP ${response.status}`,
          nextStepKey: "ui.diagnosticNextConfig",
        });
      }
      let data;
      try {
        data = await response.json();
      } catch (error) {
        failDiagnostic(
          {
            scope: "global",
            code: "CONFIG_JSON_INVALID",
            field: "config",
            expected: "valid JSON",
            actual: "JSON could not be decoded",
            nextStepKey: "ui.diagnosticNextConfig",
          },
          error,
        );
      }
      assertProjectEnvelope(data);
      data.versions.forEach((version) =>
        candidateAvailability.set(version.id, { status: "checking" }),
      );
      const selected = preferredCandidate(
        data,
        requestedReviewContext.candidateId,
      );
      if (!selected) {
        const diagnostic = makeDiagnostic({
          scope: "focus",
          code: "CANDIDATE_NOT_FOUND",
          candidateId: requestedReviewContext.candidateId,
          field: "candidate",
          expected: data.versions.map((version) => version.id),
          actual: requestedReviewContext.candidateId,
          nextStepKey: "ui.diagnosticNextCandidate",
        });
        return {
          data,
          baseUrl: resolvedUrl.href,
          isExternal: true,
          externalLoadFailed: false,
          globalDiagnostic: null,
          activeDiagnostic: diagnostic,
          selectedCandidateId: requestedReviewContext.candidateId,
          backgroundCandidates: [...data.versions],
        };
      }
      const result = await inspectCandidate(selected, resolvedUrl.href);
      candidateAvailability.set(selected.id, result);
      return {
        data,
        baseUrl: resolvedUrl.href,
        isExternal: true,
        externalLoadFailed: false,
        globalDiagnostic: null,
        activeDiagnostic: result.diagnostic,
        selectedCandidateId: selected.id,
        backgroundCandidates: data.versions.filter(
          (version) => version.id !== selected.id,
        ),
      };
    } catch (error) {
      console.warn("Could not load external preview config.", error);
      return {
        data: bundledConfig,
        baseUrl: window.location.href,
        isExternal: false,
        externalLoadFailed: true,
        globalDiagnostic: diagnosticFromError(error, {
          scope: "global",
          code: "CONFIG_FETCH_FAILED",
          field: "config",
          expected: "a readable project config",
          actual: "request failed",
          nextStepKey: "ui.diagnosticNextConfig",
        }),
        activeDiagnostic: null,
        selectedCandidateId: "",
        backgroundCandidates: [],
      };
    }
  }

  function normalizeConfig(input, includeBundledExample = false) {
    const base = cloneValue(bundledConfig);
    const target = targetBackedConfig();
    const next = input && typeof input === "object" ? input : {};
    const projectVersions =
      Array.isArray(next.versions) && next.versions.length
        ? next.versions
        : null;
    const normalized = {
      ...base,
      ...target,
      pet: { ...base.pet, ...(next.pet || {}) },
      versions: projectVersions
        ? includeBundledExample
          ? withBundledExample(projectVersions, base.versions)
          : projectVersions
        : base.versions,
      mechanics: withMechanicsOverrides(base.mechanics, next.mechanics),
      backgrounds:
        Array.isArray(next.backgrounds) && next.backgrounds.length
          ? next.backgrounds
          : base.backgrounds,
    };

    if (next.i18n && next.i18n.messages) {
      Object.entries(next.i18n.messages).forEach(
        ([messageLocale, messageOverrides]) => {
          if (!i18nBundle.messages[messageLocale]) {
            i18nBundle.messages[messageLocale] = {};
          }
          deepMerge(
            i18nBundle.messages[messageLocale],
            cloneValue(messageOverrides),
          );
        },
      );
    }

    return normalized;
  }

  function applyCandidateAvailability(candidateId, result) {
    candidateAvailability.set(candidateId, result);
    if (config) populateVersionSelect();
    if (candidateId === activeVersionId && result.status === "invalid") {
      showDiagnostic(result.diagnostic, { global: false, focus: true });
    }
  }

  function startBackgroundCandidateDiagnostics(loaded) {
    const jobs = loaded.backgroundCandidates.map((version) =>
      inspectCandidate(version, loaded.baseUrl).then((result) => {
        applyCandidateAvailability(version.id, result);
        return result;
      }),
    );
    const bundledExample = config.versions.find(
      (version) => version.isBundledExample,
    );
    if (bundledExample) {
      candidateAvailability.set(bundledExample.id, { status: "checking" });
      jobs.push(
        inspectCandidate(bundledExample, window.location.href, {
          trustedBundled: true,
        }).then((result) => {
          applyCandidateAvailability(bundledExample.id, result);
          return result;
        }),
      );
    }
    populateVersionSelect();
    void Promise.allSettled(jobs);
  }

  function resolveAssetUrl(path, version = null) {
    if (!path) return null;
    try {
      const baseUrl =
        version && version.isBundledExample
          ? window.location.href
          : configBaseUrl;
      return new URL(path, baseUrl).href;
    } catch {
      return path;
    }
  }

  function currentVersion() {
    return config.versions.find((version) => version.id === activeVersionId) || null;
  }

  function staticReviewState(version) {
    if (
      !version ||
      !version.static ||
      typeof version.static.assetUrl !== "string" ||
      !version.static.assetUrl.trim()
    ) {
      return null;
    }
    const assetUrl = version.static.assetUrl.trim();
    if (!isSafeTakeAssetUrl(assetUrl)) {
      throw new Error(
        `Candidate ${String(version.id)} has an unsafe Static asset URL.`,
      );
    }
    return {
      id: STATIC_STATE_ID,
      kind: STATIC_STATE_ID,
      durations: [0],
      assetUrl,
    };
  }

  function runtimeStatesFor(version) {
    if (!version || !version.atlasUrl) return [];
    if (!Array.isArray(version.stateIds)) return config.states;
    const availableIds = new Set(version.stateIds);
    return config.states.filter((state) => availableIds.has(state.id));
  }

  function reviewStatesFor(version) {
    const staticState = staticReviewState(version);
    return [
      ...(staticState ? [staticState] : []),
      ...runtimeStatesFor(version),
    ];
  }

  function currentReviewStates() {
    return reviewStatesFor(currentVersion());
  }

  function currentRuntimeStates() {
    return runtimeStatesFor(currentVersion());
  }

  function stateForVersion(version, stateId) {
    return reviewStatesFor(version).find((state) => state.id === stateId);
  }

  function isStaticState(state) {
    return Boolean(state && state.kind === STATIC_STATE_ID);
  }

  function currentVersionSupportsLook() {
    const version = currentVersion();
    if (!version || !version.atlasUrl) return false;
    if (version.atlasPhase === STANDARD_INTERMEDIATE_PHASE) return false;
    if (typeof version.lookDirectionsAvailable === "boolean") {
      return version.lookDirectionsAvailable;
    }
    return !Array.isArray(version.stateIds);
  }

  function currentState() {
    const states = currentReviewStates();
    return states[activeStateIndex] || states[0];
  }

  function readReviewContextFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return {
      candidateId: params.get(REVIEW_CONTEXT_PARAMS.candidate),
      stateId: params.get(REVIEW_CONTEXT_PARAMS.state),
      frame: params.get(REVIEW_CONTEXT_PARAMS.frame),
      takeId: params.get(REVIEW_CONTEXT_PARAMS.take),
    };
  }

  function reviewTakeIdForCurrentFrame() {
    if (expandedTakeFrameIndex === activeFrameIndex) {
      return activeTakeIdForCurrentFrame();
    }
    return confirmedTakeIdForFrame(
      currentVersion(),
      currentState(),
      activeFrameIndex,
    );
  }

  function validReviewTakeId(version, state, frameIndex, takeId) {
    const requestedTake = takeOptionsFor(version, state, frameIndex).find(
      (option) =>
        option.id === takeId &&
        !isFrameTakeUnavailable(option.take, version),
    );
    return requestedTake ? requestedTake.id : ORIGINAL_TAKE_ID;
  }

  function setReviewFocusFromCurrent({
    includeFrame = false,
    takeId = null,
  } = {}) {
    const version = currentVersion();
    const state = currentState();
    const frameIndex = includeFrame ? activeFrameIndex : null;
    const resolvedTakeId = includeFrame
      ? validReviewTakeId(
          version,
          state,
          frameIndex,
          takeId ?? reviewTakeIdForCurrentFrame(),
        )
      : null;
    reviewFocus = {
      candidateId: version.id,
      stateId: state.id,
      frameIndex,
      takeId: resolvedTakeId,
    };
    syncReviewContextToUrl();
  }

  function syncReviewContextToUrl() {
    if (
      !reviewContextReady ||
      !config ||
      !reviewFocus.candidateId ||
      !reviewFocus.stateId
    ) {
      return;
    }
    const url = new URL(window.location.href);
    url.searchParams.set(
      REVIEW_CONTEXT_PARAMS.candidate,
      reviewFocus.candidateId,
    );
    url.searchParams.set(
      REVIEW_CONTEXT_PARAMS.state,
      reviewFocus.stateId,
    );

    if (Number.isInteger(reviewFocus.frameIndex)) {
      url.searchParams.set(
        REVIEW_CONTEXT_PARAMS.frame,
        String(reviewFocus.frameIndex + 1),
      );
      url.searchParams.set(
        REVIEW_CONTEXT_PARAMS.take,
        reviewFocus.takeId || ORIGINAL_TAKE_ID,
      );
    } else {
      url.searchParams.delete(REVIEW_CONTEXT_PARAMS.frame);
      url.searchParams.delete(REVIEW_CONTEXT_PARAMS.take);
    }

    window.history.replaceState(window.history.state, "", url.href);
  }

  function clearReviewContextFromUrl() {
    const url = new URL(window.location.href);
    Object.values(REVIEW_CONTEXT_PARAMS).forEach((parameter) => {
      url.searchParams.delete(parameter);
    });
    window.history.replaceState(window.history.state, "", url.href);
  }

  function restoreReviewContextFromUrl(context) {
    clearFrameTimer();
    clearFrameTakeState();
    resetRuntimePlayback();
    activeFrameIndex = 0;
    isInspectingFrame = false;
    isPlaying = true;

    let canRestoreState = false;
    if (context.candidateId !== null) {
      const requestedVersion = config.versions.find(
        (version) => version.id === context.candidateId,
      );
      if (requestedVersion) {
        activeVersionId = requestedVersion.id;
        canRestoreState = true;
      }
    }

    let canRestoreFrame = false;
    if (canRestoreState && context.stateId !== null) {
      const requestedStateIndex = currentReviewStates().findIndex(
        (state) => state.id === context.stateId,
      );
      if (requestedStateIndex >= 0) {
        activeStateIndex = requestedStateIndex;
        canRestoreFrame = true;
      }
    }

    let restoredFrameIndex = null;
    let restoredTakeId = null;
    const frameNumber = Number(context.frame);
    const frameCount = currentState().durations.length;
    if (
      canRestoreFrame &&
      context.frame !== null &&
      /^[1-9]\d*$/.test(context.frame) &&
      Number.isInteger(frameNumber) &&
      frameNumber >= 1 &&
      frameNumber <= frameCount
    ) {
      activeFrameIndex = frameNumber - 1;
      restoredFrameIndex = activeFrameIndex;
      isInspectingFrame = true;
      isPlaying = false;

      const options = takeOptionsFor(
        currentVersion(),
        currentState(),
        activeFrameIndex,
      );
      restoredTakeId = validReviewTakeId(
        currentVersion(),
        currentState(),
        activeFrameIndex,
        context.takeId,
      );
      if (options.length > 1) {
        expandedTakeFrameIndex = activeFrameIndex;
        if (restoredTakeId !== ORIGINAL_TAKE_ID) {
          activeFrameTake = {
            versionId: activeVersionId,
            stateId: currentState().id,
            frameIndex: activeFrameIndex,
            takeId: restoredTakeId,
          };
        }
      }
    }

    const defaultStaticFrame =
      restoredFrameIndex === null && isStaticState(currentState()) ? 0 : null;
    reviewFocus = {
      candidateId: activeVersionId,
      stateId: currentState().id,
      frameIndex: restoredFrameIndex ?? defaultStaticFrame,
      takeId:
        restoredTakeId ??
        (defaultStaticFrame === null ? null : ORIGINAL_TAKE_ID),
    };
    elements.versionSelect.value = activeVersionId;
    renderStateList();
    renderFrameStrip();
    renderMechanicsBoard();
    renderDetails();
    renderControlLabels();
    renderAvailability();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function runtimeIdleState() {
    return (
      currentRuntimeStates().find(
        (state) => state.id === config.runtime.idleStateId,
      ) || null
    );
  }

  function idleState() {
    return runtimeIdleState() || currentRuntimeStates()[0] || currentState();
  }

  function actionReturnState() {
    const states = currentRuntimeStates();
    return (
      states.find(
        (state) => state.id === config.runtime.actionReturnStateId,
      ) || idleState()
    );
  }

  function stateFrameColumn(state, frameIndex) {
    return state.firstColumn + frameIndex;
  }

  function displayedState() {
    return !isInspectingFrame && playbackMode === "runtime" && runtimeFellBack
      ? actionReturnState()
      : currentState();
  }

  function stateCopy(state) {
    return {
      label: t(`states.${state.id}.label`),
      title: t(`states.${state.id}.title`),
      short: t(`states.${state.id}.short`),
      description: t(`states.${state.id}.description`),
      intent: t(`states.${state.id}.intent`),
      trigger: t(`states.${state.id}.trigger`),
    };
  }

  function versionLabel(version) {
    if (version.labelKey) {
      return t(version.labelKey);
    }
    if (version.labels && version.labels[locale]) {
      return version.labels[locale];
    }
    return version.displayName || version.id;
  }

  function directionLabel(direction) {
    return t(`directions.${direction.key}`);
  }

  function runtimeFrameDuration(state, frameIndex) {
    const baseDuration = state.durations[frameIndex];
    if (isStaticState(state)) return 0;
    return state.id === config.runtime.idleStateId
      ? baseDuration * config.runtime.idleDurationMultiplier
      : baseDuration;
  }

  function runtimeDurationLabel(state, frameIndex) {
    if (isStaticState(state)) return t("ui.staticImage");
    const baseDuration = state.durations[frameIndex];
    if (state.id === config.runtime.idleStateId) {
      return t("ui.idleFrameDuration", {
        duration: baseDuration,
        multiplier: config.runtime.idleDurationMultiplier,
      });
    }
    return t("ui.frameDurationFixed", { duration: baseDuration });
  }

  function totalDuration(state, runtimeEffective = false) {
    return state.durations.reduce(
      (sum, _duration, index) =>
        sum +
        (runtimeEffective
          ? runtimeFrameDuration(state, index)
          : state.durations[index]),
      0,
    );
  }

  function gridPosition(column, row) {
    const x =
      config.sprite.columns > 1
        ? (column / (config.sprite.columns - 1)) * 100
        : 0;
    const y =
      config.sprite.rows > 1 ? (row / (config.sprite.rows - 1)) * 100 : 0;
    return `${x}% ${y}%`;
  }

  function atlasBackgroundSize() {
    return `${config.sprite.columns * 100}% ${config.sprite.rows * 100}%`;
  }

  function createFixtureAtlas(version) {
    const cacheKey = `${version.id}:${config.sprite.columns}:${config.sprite.rows}:${config.sprite.frameWidth}:${config.sprite.frameHeight}`;
    if (generatedAtlases.has(cacheKey)) {
      return generatedAtlases.get(cacheKey);
    }

    const canvas = document.createElement("canvas");
    canvas.width = config.sprite.columns * config.sprite.frameWidth;
    canvas.height = config.sprite.rows * config.sprite.frameHeight;
    const context = canvas.getContext("2d");
    context.clearRect(0, 0, canvas.width, canvas.height);

    config.states.forEach((state) => {
      for (let column = 0; column < config.sprite.columns; column += 1) {
        drawFixtureFrame(context, {
          column,
          row: state.row,
          state,
          version,
          direction: null,
        });
      }
    });

    config.directions.forEach((direction) => {
      drawFixtureFrame(context, {
        column: direction.column,
        row: direction.row,
        state: idleState(),
        version,
        direction,
      });
    });

    const atlasUrl = canvas.toDataURL("image/png");
    generatedAtlases.set(cacheKey, atlasUrl);
    return atlasUrl;
  }

  function drawFixtureFrame(
    context,
    { column, row, state, version, direction },
  ) {
    const frameWidth = config.sprite.frameWidth;
    const frameHeight = config.sprite.frameHeight;
    const originX = column * frameWidth;
    const originY = row * frameHeight;
    const durationCount = Math.max(2, state.durations.length);
    const phase = Math.min(column, durationCount - 1) / (durationCount - 1);
    const wave = Math.sin(phase * Math.PI * 2);

    let offsetX = 0;
    let offsetY = 0;
    let scaleX = 1;
    let scaleY = 1;
    let eyeShiftX = 0;
    let eyeShiftY = 0;

    if (state.id === config.runtime.idleStateId) {
      scaleY += wave * 0.018;
      offsetY -= wave * 1.6;
    } else if (state.id === "running-right") {
      offsetX = (phase - 0.5) * 24;
      scaleX = 1 + Math.sin(phase * Math.PI) * 0.05;
    } else if (state.id === "running-left") {
      offsetX = (0.5 - phase) * 24;
      scaleX = 1 + Math.sin(phase * Math.PI) * 0.05;
    } else if (state.id === "waving") {
      offsetX = Math.sin(phase * Math.PI) * 8;
      offsetY = -Math.sin(phase * Math.PI) * 6;
    } else if (state.id === "jumping") {
      offsetY = -Math.sin(phase * Math.PI) * 34;
      scaleY = 1 - Math.sin(phase * Math.PI * 2) * 0.035;
    } else if (state.id === "failed") {
      offsetY = Math.sin(phase * Math.PI) * 11;
      scaleY = 1 - Math.sin(phase * Math.PI) * 0.1;
    } else if (state.id === "waiting") {
      offsetX = Math.sin(phase * Math.PI) * 10;
      eyeShiftX = 2;
    } else if (state.id === "running") {
      eyeShiftX = Math.cos(phase * Math.PI * 2) * 5;
      eyeShiftY = Math.sin(phase * Math.PI * 2) * 4;
    } else if (state.id === "review") {
      offsetX = Math.sin(phase * Math.PI) * 11;
      scaleX = 1 + Math.sin(phase * Math.PI) * 0.04;
    }

    if (direction) {
      const radians = (direction.degree * Math.PI) / 180;
      eyeShiftX = Math.sin(radians) * 7;
      eyeShiftY = -Math.cos(radians) * 6;
      offsetX = Math.sin(radians) * 2;
      offsetY = -Math.cos(radians) * 1.5;
    }

    const centerX = originX + frameWidth / 2 + offsetX;
    const centerY = originY + frameHeight / 2 + 12 + offsetY;

    context.save();
    context.translate(centerX, centerY);
    context.scale(scaleX, scaleY);
    context.fillStyle = "#111111";
    context.beginPath();
    context.moveTo(-52, 42);
    context.bezierCurveTo(-60, 17, -54, -35, -30, -53);
    context.bezierCurveTo(-10, -68, 30, -62, 46, -38);
    context.bezierCurveTo(62, -14, 58, 24, 50, 43);
    context.quadraticCurveTo(0, 56, -52, 42);
    context.closePath();
    context.fill();

    context.fillStyle = "#ffffff";
    const blink =
      state.id === idleState().id &&
      column === Math.min(3, state.durations.length - 1);
    if (blink) {
      context.fillRect(-21 + eyeShiftX, -23 + eyeShiftY, 13, 2);
      context.fillRect(8 + eyeShiftX, -23 + eyeShiftY, 13, 2);
    } else {
      context.beginPath();
      context.ellipse(
        -15 + eyeShiftX,
        -22 + eyeShiftY,
        5,
        8,
        0,
        0,
        Math.PI * 2,
      );
      context.ellipse(
        15 + eyeShiftX,
        -22 + eyeShiftY,
        5,
        8,
        0,
        0,
        Math.PI * 2,
      );
      context.fill();
    }

    context.fillStyle = "#8a8a8a";
    context.fillRect(-13, 20, 26, 3);
    context.restore();
  }

  function atlasUrlFor(version) {
    return version.atlasUrl
      ? resolveAssetUrl(version.atlasUrl, version)
      : createFixtureAtlas(version);
  }

  function setStandaloneImage(
    assetUrl,
    target = elements.spritePlayer,
    version = currentVersion(),
  ) {
    const image = `url("${resolveAssetUrl(assetUrl, version)}")`;
    const size = "contain";
    const position = "center";
    const cached = spriteStyleCache.get(target) || {};

    if (cached.image !== image) target.style.backgroundImage = image;
    if (cached.size !== size) target.style.backgroundSize = size;
    if (cached.position !== position) {
      target.style.backgroundPosition = position;
    }

    spriteStyleCache.set(target, { image, size, position });
  }

  function setSpriteFrame(row, column, target = elements.spritePlayer) {
    const image = `url("${atlasUrlFor(currentVersion())}")`;
    const size = atlasBackgroundSize();
    const position = gridPosition(column, row);
    const cached = spriteStyleCache.get(target) || {};

    if (cached.image !== image) target.style.backgroundImage = image;
    if (cached.size !== size) target.style.backgroundSize = size;
    if (cached.position !== position) target.style.backgroundPosition = position;

    spriteStyleCache.set(target, { image, size, position });
  }

  function setOriginalFrame(
    state,
    frameIndex,
    target = elements.spritePlayer,
    version = currentVersion(),
  ) {
    if (isStaticState(state)) {
      setStandaloneImage(state.assetUrl, target, version);
      return;
    }
    setSpriteFrame(
      state.row,
      stateFrameColumn(state, frameIndex),
      target,
    );
  }

  function isValidAtlasSlot(slot) {
    return (
      slot &&
      Number.isInteger(slot.row) &&
      Number.isInteger(slot.column) &&
      slot.row >= 0 &&
      slot.row < config.sprite.rows &&
      slot.column >= 0 &&
      slot.column < config.sprite.columns
    );
  }

  function frameTakesFor(version, state, frameIndex) {
    if (
      isStaticState(state) &&
      frameIndex === 0 &&
      version &&
      version.static &&
      Array.isArray(version.static.takes)
    ) {
      const usedIds = new Set();
      return version.static.takes.reduce((takes, take) => {
        const takeId =
          take && typeof take.id === "string" ? take.id.trim() : "";
        const assetUrl =
          take && typeof take.assetUrl === "string"
            ? take.assetUrl.trim()
            : "";
        if (
          !takeId ||
          takeId === ORIGINAL_TAKE_ID ||
          usedIds.has(takeId) ||
          !isSafeTakeAssetUrl(assetUrl)
        ) {
          return takes;
        }
        usedIds.add(takeId);
        takes.push({ ...take, id: takeId, assetUrl });
        return takes;
      }, []);
    }
    if (!version || !Array.isArray(version.frameTakes)) return [];
    const groups = version.frameTakes.filter(
      (candidate) =>
        candidate &&
        candidate.stateId === state.id &&
        Number.isInteger(candidate.frameIndex) &&
        candidate.frameIndex >= 0 &&
        candidate.frameIndex < state.durations.length &&
        candidate.frameIndex === frameIndex &&
        Array.isArray(candidate.takes),
    );
    if (!groups.length) return [];

    const usedIds = new Set();
    return groups.flatMap((group) => group.takes).reduce((takes, take) => {
      const takeId =
        take && typeof take.id === "string" ? take.id.trim() : "";
      if (
        !take ||
        !takeId ||
        takeId === ORIGINAL_TAKE_ID ||
        usedIds.has(takeId)
      ) {
        return takes;
      }
      const assetUrl =
        typeof take.assetUrl === "string" ? take.assetUrl.trim() : "";
      const hasAsset = isSafeTakeAssetUrl(assetUrl);
      const hasAtlasSlot = isValidAtlasSlot(take.atlasSlot);
      if (Boolean(hasAsset) === Boolean(hasAtlasSlot)) return takes;
      usedIds.add(takeId);
      takes.push({
        ...take,
        id: takeId,
        ...(hasAsset ? { assetUrl } : {}),
      });
      return takes;
    }, []);
  }

  function frameTakeSelectionKey(versionId, stateId, frameIndex) {
    return JSON.stringify([versionId, stateId, frameIndex]);
  }

  function takeOptionsFor(version, state, frameIndex) {
    return [
      { id: ORIGINAL_TAKE_ID, take: null },
      ...frameTakesFor(version, state, frameIndex).map((take) => ({
        id: take.id,
        take,
      })),
    ];
  }

  function isFrameTakeUnavailable(take, version = currentVersion()) {
    if (!take || !take.assetUrl) return false;
    const assetUrl = resolveAssetUrl(take.assetUrl, version);
    return takeAssetStatus.get(assetUrl) === "failed";
  }

  function availableTakeOptionsFor(version, state, frameIndex) {
    return takeOptionsFor(version, state, frameIndex).filter(
      (option) => !isFrameTakeUnavailable(option.take, version),
    );
  }

  function confirmedSelectionForFrame(version, state, frameIndex) {
    const key = frameTakeSelectionKey(version.id, state.id, frameIndex);
    if (!confirmedFrameTakeIds.has(key)) {
      return {
        hasSelection: false,
        id: ORIGINAL_TAKE_ID,
        take: null,
      };
    }

    const takeId = confirmedFrameTakeIds.get(key);
    if (takeId === ORIGINAL_TAKE_ID) {
      return {
        hasSelection: true,
        id: ORIGINAL_TAKE_ID,
        take: null,
      };
    }

    const take =
      frameTakesFor(version, state, frameIndex).find(
        (candidate) => candidate.id === takeId,
      ) || null;
    if (take && !isFrameTakeUnavailable(take, version)) {
      return { hasSelection: true, id: takeId, take };
    }

    confirmedFrameTakeIds.delete(key);
    return {
      hasSelection: false,
      id: ORIGINAL_TAKE_ID,
      take: null,
    };
  }

  function hasConfirmedFrameTakeForFrame(version, state, frameIndex) {
    return confirmedSelectionForFrame(version, state, frameIndex).hasSelection;
  }

  function confirmedTakeIdForFrame(version, state, frameIndex) {
    return confirmedSelectionForFrame(version, state, frameIndex).id;
  }

  function confirmedTakeForFrame(version, state, frameIndex) {
    return confirmedSelectionForFrame(version, state, frameIndex).take;
  }

  function isSafeTakeAssetUrl(path) {
    if (
      !path ||
      !/^[A-Za-z0-9._~!$&*+,/:@?%#=-]+$/.test(path) ||
      (/^[a-z][a-z0-9+.-]*:/i.test(path) && !/^https?:/i.test(path))
    ) {
      return false;
    }
    try {
      const url = new URL(path, configBaseUrl);
      const baseUrl = new URL(configBaseUrl, window.location.href);
      return (
        ["http:", "https:"].includes(url.protocol) &&
        url.origin === baseUrl.origin &&
        !url.username &&
        !url.password
      );
    } catch {
      return false;
    }
  }

  function frameTakeLabel(take, index) {
    if (take.labels && take.labels[locale]) return take.labels[locale];
    if (typeof take.label === "string" && take.label.trim()) {
      return take.label;
    }
    return `Take ${String(index + 1).padStart(2, "0")}`;
  }

  function frameTakeStyle(
    take,
    state,
    frameIndex,
    version = currentVersion(),
  ) {
    if (!take || isFrameTakeUnavailable(take, version)) {
      return frameThumbnailStyle(state, frameIndex, version);
    }
    if (take.assetUrl) {
      return [
        `background-image:url('${resolveAssetUrl(take.assetUrl, version)}')`,
        "background-size:contain",
        "background-position:center",
      ].join(";");
    }
    return [
      `background-image:url('${atlasUrlFor(version)}')`,
      `background-size:${atlasBackgroundSize()}`,
      `background-position:${gridPosition(take.atlasSlot.column, take.atlasSlot.row)}`,
    ].join(";");
  }

  function activeTakeForCurrentFrame() {
    if (
      !activeFrameTake ||
      activeFrameTake.versionId !== activeVersionId ||
      activeFrameTake.stateId !== currentState().id ||
      activeFrameTake.frameIndex !== activeFrameIndex
    ) {
      return null;
    }
    return (
      frameTakesFor(currentVersion(), currentState(), activeFrameIndex).find(
        (take) =>
          take.id === activeFrameTake.takeId &&
          !isFrameTakeUnavailable(take),
      ) || null
    );
  }

  function activeTakeIdForCurrentFrame() {
    const take = activeTakeForCurrentFrame();
    return take ? take.id : ORIGINAL_TAKE_ID;
  }

  function displayedTakeForFrame(version, state, frameIndex) {
    if (
      version.id === activeVersionId &&
      state.id === currentState().id &&
      frameIndex === activeFrameIndex &&
      expandedTakeFrameIndex === frameIndex &&
      isInspectingFrame
    ) {
      return activeTakeForCurrentFrame();
    }
    return confirmedTakeForFrame(version, state, frameIndex);
  }

  function displayedTakeForCurrentFrame() {
    return displayedTakeForFrame(
      currentVersion(),
      currentState(),
      activeFrameIndex,
    );
  }

  function refreshMechanicsFrameTake(version, state, frameIndex) {
    if (
      !version ||
      !state ||
      version.id !== activeVersionId ||
      isStaticState(state)
    ) {
      return;
    }
    const card = [...elements.mechanicsRows.querySelectorAll(".mechanics-card")]
      .find(
        (candidate) =>
          candidate.dataset.stateId === state.id &&
          Number(candidate.dataset.frameIndex) === frameIndex,
      );
    const sprite = card?.querySelector(".mechanics-sprite");
    if (!sprite) return;
    sprite.setAttribute(
      "style",
      frameTakeStyle(
        displayedTakeForFrame(version, state, frameIndex),
        state,
        frameIndex,
        version,
      ),
    );
  }

  function refreshMechanicsTakeFrames() {
    const version = currentVersion();
    elements.mechanicsRows
      .querySelectorAll(".mechanics-card")
      .forEach((card) => {
        const state = stateForVersion(version, card.dataset.stateId);
        const frameIndex = Number(card.dataset.frameIndex);
        if (!state || !Number.isInteger(frameIndex)) return;
        refreshMechanicsFrameTake(version, state, frameIndex);
      });
  }

  function clearFrameTakeState({ closeRail = true } = {}) {
    const previousVersion =
      config && Number.isInteger(expandedTakeFrameIndex)
        ? currentVersion()
        : null;
    const previousState = previousVersion ? currentState() : null;
    const previousFrameIndex = expandedTakeFrameIndex;
    activeFrameTake = null;
    if (closeRail) expandedTakeFrameIndex = null;
    if (Number.isInteger(previousFrameIndex)) {
      refreshMechanicsFrameTake(
        previousVersion,
        previousState,
        previousFrameIndex,
      );
    }
  }

  function previewFrameTake(takeId) {
    const state = currentState();
    const takes = frameTakesFor(currentVersion(), state, activeFrameIndex);
    if (takeId === ORIGINAL_TAKE_ID) {
      activeFrameTake = null;
    } else {
      const take = takes.find((candidate) => candidate.id === takeId);
      if (!take || isFrameTakeUnavailable(take)) return;
      activeFrameTake = {
        versionId: activeVersionId,
        stateId: state.id,
        frameIndex: activeFrameIndex,
        takeId: take.id,
      };
    }
    refreshTakeClasses();
    renderPlayer();
    renderFrameReadout();
    renderControlLabels();
    refreshMechanicsFrameTake(
      currentVersion(),
      state,
      activeFrameIndex,
    );
    scheduleTakeRailPosition();
    setReviewFocusFromCurrent({
      includeFrame: true,
      takeId: activeTakeIdForCurrentFrame(),
    });
  }

  function primeFrameTakeFromConfirmed() {
    const takeId = confirmedTakeIdForFrame(
      currentVersion(),
      currentState(),
      activeFrameIndex,
    );
    if (takeId === ORIGINAL_TAKE_ID) {
      activeFrameTake = null;
      return;
    }
    activeFrameTake = {
      versionId: activeVersionId,
      stateId: currentState().id,
      frameIndex: activeFrameIndex,
      takeId,
    };
  }

  function confirmFrameTake() {
    if (
      expandedTakeFrameIndex === null ||
      expandedTakeFrameIndex !== activeFrameIndex
    ) {
      return;
    }
    const activeTake = activeTakeForCurrentFrame();
    if (
      activeTake &&
      activeTake.assetUrl &&
      takeAssetStatus.get(
        resolveAssetUrl(activeTake.assetUrl, currentVersion()),
      ) !== "ready"
    ) {
      return;
    }
    const frameIndex = activeFrameIndex;
    const key = frameTakeSelectionKey(
      activeVersionId,
      currentState().id,
      frameIndex,
    );
    const takeId = activeTakeIdForCurrentFrame();
    const takes = frameTakesFor(
      currentVersion(),
      currentState(),
      frameIndex,
    );
    const takeLabel = activeTake
      ? frameTakeLabel(activeTake, takes.indexOf(activeTake))
      : t("ui.originalFrame");
    confirmedFrameTakeIds.set(key, takeId);
    clearFrameTakeState();
    renderFrameStrip();
    renderControlLabels();
    renderPlayer();
    renderFrameReadout();
    announceTakeConfirmation(takeLabel);
    focusFrameButton(frameIndex);
    setReviewFocusFromCurrent({ includeFrame: true, takeId });
  }

  function activeTakeReadyForConfirmation() {
    const activeTake =
      expandedTakeFrameIndex === activeFrameIndex
        ? activeTakeForCurrentFrame()
        : null;
    return (
      !activeTake ||
      !activeTake.assetUrl ||
      takeAssetStatus.get(
        resolveAssetUrl(activeTake.assetUrl, currentVersion()),
      ) === "ready"
    );
  }

  function announceTakeConfirmation(takeLabel) {
    elements.takeStatus.textContent = "";
    window.requestAnimationFrame(() => {
      elements.takeStatus.textContent = t("ui.takeConfirmedStatus", {
        take: takeLabel,
      });
    });
  }

  function stepTake(delta) {
    if (
      expandedTakeFrameIndex === null ||
      expandedTakeFrameIndex !== activeFrameIndex
    ) {
      return;
    }
    const options = availableTakeOptionsFor(
      currentVersion(),
      currentState(),
      activeFrameIndex,
    );
    const activeIndex = Math.max(
      0,
      options.findIndex(
        (option) => option.id === activeTakeIdForCurrentFrame(),
      ),
    );
    const nextIndex = Math.min(
      options.length - 1,
      Math.max(0, activeIndex + delta),
    );
    if (nextIndex === activeIndex) return;
    previewFrameTake(options[nextIndex].id);
  }

  function rawTakeForSelection(version, state, frameIndex, takeId) {
    if (!version || !state || takeId === ORIGINAL_TAKE_ID) return null;
    return (
      frameTakesFor(version, state, frameIndex).find(
        (take) => take.id === takeId,
      ) || null
    );
  }

  function takeAssetUrlForSelection(version, state, frameIndex, takeId) {
    const take = rawTakeForSelection(version, state, frameIndex, takeId);
    return take && take.assetUrl
      ? resolveAssetUrl(take.assetUrl, version)
      : null;
  }

  function activeTakeAssetUrl() {
    if (!activeFrameTake) return null;
    const version = config.versions.find(
      (candidate) => candidate.id === activeFrameTake.versionId,
    );
    const state = stateForVersion(version, activeFrameTake.stateId);
    return takeAssetUrlForSelection(
      version,
      state,
      activeFrameTake.frameIndex,
      activeFrameTake.takeId,
    );
  }

  function confirmedTakeAssetUrl(version, state, frameIndex) {
    const key = frameTakeSelectionKey(version.id, state.id, frameIndex);
    if (!confirmedFrameTakeIds.has(key)) return null;
    return takeAssetUrlForSelection(
      version,
      state,
      frameIndex,
      confirmedFrameTakeIds.get(key),
    );
  }

  function currentTakeAssetUsage(assetUrl) {
    const version = currentVersion();
    const state = currentState();
    const playbackState = displayedState();
    const activeUrl = activeTakeAssetUrl();
    const currentConfirmedUrl = confirmedTakeAssetUrl(
      version,
      state,
      activeFrameIndex,
    );
    const playbackConfirmedUrl = confirmedTakeAssetUrl(
      version,
      playbackState,
      activeFrameIndex,
    );
    const stageUrl = isInspectingFrame
      ? expandedTakeFrameIndex === activeFrameIndex
        ? activeUrl
        : currentConfirmedUrl
      : playbackConfirmedUrl;
    const railContainsAsset =
      expandedTakeFrameIndex === activeFrameIndex &&
      frameTakesFor(version, state, activeFrameIndex).some(
        (take) =>
          take.assetUrl &&
          resolveAssetUrl(take.assetUrl, version) === assetUrl,
      );
    return {
      rail: railContainsAsset,
      stage: stageUrl === assetUrl,
      controls: activeUrl === assetUrl,
    };
  }

  function removeConfirmedSelectionsForAsset(assetUrl) {
    confirmedFrameTakeIds.forEach((takeId, key) => {
      let versionId;
      let stateId;
      let frameIndex;
      try {
        [versionId, stateId, frameIndex] = JSON.parse(key);
      } catch {
        confirmedFrameTakeIds.delete(key);
        return;
      }
      const version = config.versions.find(
        (candidate) => candidate.id === versionId,
      );
      const state = stateForVersion(version, stateId);
      if (
        takeAssetUrlForSelection(
          version,
          state,
          frameIndex,
          takeId,
        ) === assetUrl
      ) {
        confirmedFrameTakeIds.delete(key);
      }
    });
  }

  function invalidateTakeAsset(assetUrl) {
    const usage = currentTakeAssetUsage(assetUrl);
    const restoreTakeFocus =
      document.activeElement instanceof Element &&
      Boolean(document.activeElement.closest(".take-card"));
    takeAssetStatus.set(assetUrl, "failed");
    removeConfirmedSelectionsForAsset(assetUrl);
    if (activeTakeAssetUrl() === assetUrl) {
      activeFrameTake = null;
    }
    refreshMechanicsTakeFrames();
    if (usage.rail) {
      renderFrameStrip();
      renderControlLabels();
      if (restoreTakeFocus) focusPreviewedTake();
    } else if (usage.controls) {
      renderControlLabels();
    }
    if (usage.stage) {
      renderPlayer();
      renderFrameReadout();
    }
    if (
      Number.isInteger(reviewFocus.frameIndex) &&
      reviewFocus.takeId !== ORIGINAL_TAKE_ID
    ) {
      const focusedVersion = config.versions.find(
        (version) => version.id === reviewFocus.candidateId,
      );
      const focusedState = stateForVersion(
        focusedVersion,
        reviewFocus.stateId,
      );
      const focusedAssetUrl = takeAssetUrlForSelection(
        focusedVersion,
        focusedState,
        reviewFocus.frameIndex,
        reviewFocus.takeId,
      );
      if (focusedAssetUrl === assetUrl) {
        reviewFocus.takeId = ORIGINAL_TAKE_ID;
        syncReviewContextToUrl();
      }
    }
  }

  function setTakeSpriteFrame(
    take,
    target = elements.spritePlayer,
    fallbackState = currentState(),
    frameIndex = activeFrameIndex,
  ) {
    if (take.assetUrl) {
      const version = currentVersion();
      const assetUrl = resolveAssetUrl(take.assetUrl, version);
      if (takeAssetStatus.get(assetUrl) === "failed") {
        setOriginalFrame(fallbackState, frameIndex, target, version);
        return;
      }
      if (!takeAssetStatus.has(assetUrl)) {
        takeAssetStatus.set(assetUrl, "loading");
        const probe = new Image();
        probe.addEventListener("load", () => {
          if (
            !isStaticState(fallbackState) &&
            (probe.naturalWidth !== config.sprite.frameWidth ||
              probe.naturalHeight !== config.sprite.frameHeight)
          ) {
            invalidateTakeAsset(assetUrl);
            return;
          }
          takeAssetStatus.set(assetUrl, "ready");
          if (currentTakeAssetUsage(assetUrl).controls) {
            renderControlLabels();
          }
        });
        probe.addEventListener("error", () => {
          invalidateTakeAsset(assetUrl);
        });
        probe.src = assetUrl;
      }
      const image = `url("${assetUrl}")`;
      const size = "contain";
      const position = "center";
      const cached = spriteStyleCache.get(target) || {};
      if (cached.image !== image) target.style.backgroundImage = image;
      if (cached.size !== size) target.style.backgroundSize = size;
      if (cached.position !== position) {
        target.style.backgroundPosition = position;
      }
      spriteStyleCache.set(target, { image, size, position });
      return;
    }
    setSpriteFrame(take.atlasSlot.row, take.atlasSlot.column, target);
  }

  function setDiagnosticRow(row, output, value) {
    const visible = Boolean(value);
    row.hidden = !visible;
    output.textContent = visible ? value : "";
  }

  function showDiagnostic(
    diagnostic,
    { global = diagnostic.scope === "global", focus = false } = {},
  ) {
    activeDiagnostic = diagnostic;
    elements.configErrorScope.textContent = t(
      global ? "ui.diagnosticScopeGlobal" : "ui.diagnosticScopeCandidate",
    );
    elements.configErrorTitle.textContent = t(
      global ? "ui.configErrorTitle" : "ui.candidateErrorTitle",
    );
    elements.configErrorSummary.textContent = t(
      global ? "ui.globalDiagnosticSummary" : "ui.candidateDiagnosticSummary",
      { candidate: diagnostic.candidateId || t("ui.notAvailable") },
    );
    elements.configErrorConfig.textContent =
      diagnostic.configRef || t("ui.notAvailable");
    elements.configErrorCode.textContent = diagnostic.code;
    setDiagnosticRow(
      elements.configErrorCandidateRow,
      elements.configErrorCandidate,
      diagnostic.candidateId,
    );
    setDiagnosticRow(
      elements.configErrorFieldRow,
      elements.configErrorField,
      diagnostic.field,
    );
    setDiagnosticRow(
      elements.configErrorExpectedRow,
      elements.configErrorExpected,
      diagnostic.expected,
    );
    setDiagnosticRow(
      elements.configErrorActualRow,
      elements.configErrorActual,
      diagnostic.actual,
    );
    elements.configErrorNextStep.textContent = t(diagnostic.nextStepKey);
    elements.configError.hidden = false;
    elements.topbar.hidden = global;
    elements.workspace.hidden = true;
    elements.mechanicsBoard.hidden = true;
    elements.previewFooter.hidden = true;
    if (focus) elements.configError.focus({ preventScroll: true });
  }

  function hideDiagnostic() {
    activeDiagnostic = null;
    elements.configError.hidden = true;
    elements.topbar.hidden = false;
    elements.workspace.hidden = false;
    elements.previewFooter.hidden = false;
  }

  function applyStaticTranslations() {
    document.documentElement.lang = locale;
    document.title = t("documentTitle");
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n);
    });
    document
      .querySelectorAll("[data-i18n-aria-label]")
      .forEach((node) => {
        node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel));
      });
    document.querySelectorAll("[data-i18n-title]").forEach((node) => {
      node.setAttribute("title", t(node.dataset.i18nTitle));
    });
  }

  function populateLanguageSelect() {
    elements.languageSelect.innerHTML = i18nBundle.locales
      .map(
        (item) =>
          `<option value="${escapeHtml(item.id)}">${escapeHtml(item.nativeName)}</option>`,
      )
      .join("");
    elements.languageSelect.value = locale;
  }

  function populateVersionSelect() {
    const options = config.versions
      .map(
        (version) => {
          const availability = candidateAvailability.get(version.id) || {
            status: "checking",
          };
          const unavailable = availability.status !== "valid";
          const suffix =
            availability.status === "invalid"
              ? t("ui.candidateUnavailableReasonSuffix", {
                  code: availability.diagnostic.code,
                })
              : availability.status === "checking"
                ? t("ui.candidateCheckingSuffix")
                : "";
          return (
            `<option value="${escapeHtml(version.id)}" ` +
            `${unavailable ? "disabled" : ""}>` +
            `${escapeHtml(versionLabel(version))}${escapeHtml(suffix)}</option>`
          );
        },
      )
      .join("");
    const missingFocusedCandidate =
      activeVersionId &&
      !config.versions.some((version) => version.id === activeVersionId);
    elements.versionSelect.innerHTML = missingFocusedCandidate
      ? '<option value="" selected disabled>' +
        `${escapeHtml(safeFact(activeVersionId))}${escapeHtml(
          t("ui.candidateUnavailableSuffix"),
        )}</option>${options}`
      : options;
    if (!missingFocusedCandidate) {
      elements.versionSelect.value = activeVersionId;
    }
  }

  function renderStateList() {
    const states = currentReviewStates();
    const runtimeStates = currentRuntimeStates();
    const staticState = states.find((state) => isStaticState(state));
    elements.stateCount.textContent = t("ui.stateCount", {
      count: runtimeStates.length,
    });
    elements.staticSection.hidden = !staticState;
    elements.runtimeStateHeading.hidden = runtimeStates.length === 0;

    function stateButtonMarkup(state, index) {
        const copy = stateCopy(state);
        const indexLabel = isStaticState(state)
          ? "S"
          : String(runtimeStates.indexOf(state) + 1).padStart(2, "0");
        return `
          <button
            class="state-button ${index === activeStateIndex ? "is-active" : ""}"
            data-state-index="${index}"
            type="button"
            aria-label="${escapeHtml([copy.title, copy.label].join(" · "))}"
          >
            <span class="state-index">${indexLabel}</span>
            <span class="state-name">
              <strong>${escapeHtml(copy.title)}</strong>
              <small>${escapeHtml(copy.label)}</small>
            </span>
          </button>
        `;
    }

    elements.staticList.innerHTML = staticState
      ? stateButtonMarkup(staticState, states.indexOf(staticState))
      : "";
    elements.stateList.innerHTML = runtimeStates
      .map((state) => stateButtonMarkup(state, states.indexOf(state)))
      .join("");

    stateButtons = [
      ...elements.staticList.querySelectorAll(".state-button"),
      ...elements.stateList.querySelectorAll(".state-button"),
    ];
    stateButtons.forEach((button) => {
      button.addEventListener("click", () => {
        stopTour();
        setState(Number(button.dataset.stateIndex));
      });
    });
  }

  function runtimeNoteFor(state) {
    if (playbackMode === "loop") {
      return t("ui.endlessLoopNote");
    }
    if (state.id === config.runtime.idleStateId) {
      return t("ui.runtimeIdleNote");
    }
    return t("ui.runtimeActionNote", {
      loops: config.runtime.actionLoops,
    });
  }

  function renderDetails() {
    const state = currentState();
    const copy = stateCopy(state);
    const runtimeIndex = currentRuntimeStates().indexOf(state);
    elements.stateTag.textContent = isStaticState(state)
      ? copy.label
      : `${String(runtimeIndex + 1).padStart(2, "0")} · ${copy.label}`;
    elements.stateTitle.textContent = copy.title;
    elements.stateDescription.textContent = copy.description;
    elements.stateIntent.textContent = copy.intent;
    elements.stateTrigger.textContent = copy.trigger;
    elements.stateDuration.textContent = isStaticState(state)
      ? t("ui.staticAssetCount")
      : t("ui.duration", {
          frames: state.durations.length,
          seconds: (totalDuration(state, true) / 1000).toFixed(2),
          runtimeNote: runtimeNoteFor(state),
        });
    elements.frameSectionTitle.textContent = t(
      isStaticState(state) ? "ui.staticTakes" : "ui.keyframes",
    );
    const alt = t("ui.assetAlt", {
      pet: config.pet.name,
      state: copy.title,
    });
    elements.spritePlayer.setAttribute("aria-label", alt);
  }

  function frameThumbnailStyle(
    state,
    index,
    version = currentVersion(),
  ) {
    if (isStaticState(state)) {
      return [
        `background-image:url('${resolveAssetUrl(
          state.assetUrl,
          version,
        )}')`,
        "background-size:contain",
        "background-position:center",
      ].join(";");
    }
    return [
      `background-image:url('${atlasUrlFor(version)}')`,
      `background-size:${atlasBackgroundSize()}`,
      `background-position:${gridPosition(
        stateFrameColumn(state, index),
        state.row,
      )}`,
    ].join(";");
  }

  function renderTakeRail(state, frameIndex, takes) {
    const options = [
      {
        id: ORIGINAL_TAKE_ID,
        label: t("ui.originalFrame"),
        take: null,
      },
      ...takes.map((take, index) => ({
        id: take.id,
        label: frameTakeLabel(take, index),
        take,
      })),
    ];
    const activeTakeId = activeTakeIdForCurrentFrame();
    const hasConfirmedTake = hasConfirmedFrameTakeForFrame(
      currentVersion(),
      state,
      frameIndex,
    );
    const confirmedTakeId = confirmedTakeIdForFrame(
      currentVersion(),
      state,
      frameIndex,
    );
    const activeTakeReady = activeTakeReadyForConfirmation();
    const railId = `take-rail-${state.id}-${frameIndex}`;
    const viewportId = `${railId}-viewport`;
    return `
      <div
        id="${escapeHtml(railId)}"
        class="take-rail"
        role="group"
        aria-label="${escapeHtml(
          t("ui.takeRailAria", { frame: frameIndex + 1 }),
        )}"
        data-frame-index="${frameIndex}"
      >
        <div class="take-rail-layout">
          <button
            class="take-rail-nav-button take-rail-previous"
            type="button"
            title="${escapeHtml(t("ui.previousTakes"))}"
            aria-label="${escapeHtml(t("ui.previousTakes"))}"
            aria-controls="${escapeHtml(viewportId)}"
            hidden
          >
            ←
          </button>
          <div
            id="${escapeHtml(viewportId)}"
            class="take-rail-viewport"
          >
            <div class="take-track">
              ${options
                .map(
                  (option) => {
                    const unavailable = isFrameTakeUnavailable(
                      option.take,
                      currentVersion(),
                    );
                    const confirmed =
                      hasConfirmedTake && option.id === confirmedTakeId;
                    return `
                    <button
                      class="take-card ${
                        option.id === activeTakeId ? "is-previewing" : ""
                      } ${
                        confirmed ? "is-confirmed" : ""
                      } ${unavailable ? "is-unavailable" : ""}"
                      type="button"
                      data-take-id="${escapeHtml(option.id)}"
                      ${unavailable ? "disabled" : ""}
                      aria-pressed="${String(option.id === activeTakeId)}"
                      aria-label="${escapeHtml(
                        t(
                          unavailable
                            ? "ui.takeUnavailableAria"
                            : confirmed
                              ? "ui.takeConfirmedAria"
                              : "ui.takeAria",
                          {
                            frame: frameIndex + 1,
                            take: option.label,
                          },
                        ),
                      )}"
                    >
                      <span
                        class="take-thumbnail"
                        style="${frameTakeStyle(
                          option.take,
                          state,
                          frameIndex,
                        )}"
                      ></span>
                      <small>${escapeHtml(option.label)}</small>
                      ${
                        confirmed
                          ? '<span class="take-confirmed-mark" aria-hidden="true">✓</span>'
                          : ""
                      }
                    </button>
                  `;
                  },
                )
                .join("")}
            </div>
          </div>
          <button
            class="take-rail-nav-button take-rail-next"
            type="button"
            title="${escapeHtml(t("ui.nextTakes"))}"
            aria-label="${escapeHtml(t("ui.nextTakes"))}"
            aria-controls="${escapeHtml(viewportId)}"
            hidden
          >
            →
          </button>
          <button
            class="take-rail-confirm-button"
            type="button"
            title="${escapeHtml(
              t(activeTakeReady ? "ui.confirmTake" : "ui.takeAssetLoading"),
            )}"
            aria-label="${escapeHtml(
              t(activeTakeReady ? "ui.confirmTake" : "ui.takeAssetLoading"),
            )}"
            ${activeTakeReady ? "" : "disabled"}
          >
            ✓
          </button>
        </div>
      </div>
    `;
  }

  function updateTakeRailNavigation() {
    const rail = elements.frameStrip.querySelector(".take-rail");
    if (!rail) return;
    const viewport = rail.querySelector(".take-rail-viewport");
    const previousButton = rail.querySelector(".take-rail-previous");
    const nextButton = rail.querySelector(".take-rail-next");
    if (
      !viewport ||
      !previousButton ||
      !nextButton ||
      previousButton.hidden ||
      nextButton.hidden
    ) {
      return;
    }
    const maxScroll = Math.max(0, viewport.scrollWidth - viewport.clientWidth);
    previousButton.disabled = viewport.scrollLeft <= 1;
    nextButton.disabled = viewport.scrollLeft >= maxScroll - 1;
    previousButton.setAttribute(
      "aria-disabled",
      String(previousButton.disabled),
    );
    nextButton.setAttribute("aria-disabled", String(nextButton.disabled));
  }

  function positionTakeRail() {
    const rail = elements.frameStrip.querySelector(".take-rail");
    if (!rail) return;
    const viewport = rail.querySelector(".take-rail-viewport");
    const track = rail.querySelector(".take-track");
    const previousButton = rail.querySelector(".take-rail-previous");
    const nextButton = rail.querySelector(".take-rail-next");
    const selectedFrame = elements.frameStrip.querySelector(
      `.frame-button[data-frame-index="${expandedTakeFrameIndex}"]`,
    );
    if (
      !viewport ||
      !track ||
      !previousButton ||
      !nextButton ||
      !selectedFrame
    ) {
      return;
    }

    track.style.marginInlineStart = "0px";
    previousButton.hidden = true;
    nextButton.hidden = true;
    const hasOverflow = track.scrollWidth > viewport.clientWidth + 2;
    previousButton.hidden = !hasOverflow;
    nextButton.hidden = !hasOverflow;

    const viewportRect = viewport.getBoundingClientRect();
    const railRect = rail.getBoundingClientRect();
    const frameRect = selectedFrame.getBoundingClientRect();
    const frameCenter = frameRect.left + frameRect.width / 2;
    const viewportAnchor = Math.min(
      viewport.clientWidth,
      Math.max(0, frameCenter - viewportRect.left),
    );
    const railAnchor = Math.min(
      rail.clientWidth,
      Math.max(0, frameCenter - railRect.left),
    );
    rail.style.setProperty("--take-anchor-x", `${railAnchor}px`);

    const trackWidth = track.scrollWidth;
    if (!hasOverflow) {
      const desiredLeft = viewportAnchor - trackWidth / 2;
      const boundedLeft = Math.min(
        viewport.clientWidth - trackWidth,
        Math.max(0, desiredLeft),
      );
      track.style.marginInlineStart = `${boundedLeft}px`;
      viewport.scrollLeft = 0;
      updateTakeRailNavigation();
      return;
    }

    const activeCard = track.querySelector(".take-card.is-previewing");
    if (!activeCard) {
      updateTakeRailNavigation();
      return;
    }
    const activeCardOffset =
      activeCard.getBoundingClientRect().left -
      track.getBoundingClientRect().left;
    const desiredScroll =
      activeCardOffset + activeCard.offsetWidth / 2 - viewportAnchor;
    viewport.scrollLeft = Math.min(
      trackWidth - viewport.clientWidth,
      Math.max(0, desiredScroll),
    );
    updateTakeRailNavigation();
  }

  function scrollTakeRail(delta) {
    const rail = elements.frameStrip.querySelector(".take-rail");
    if (!rail) return;
    const viewport = rail.querySelector(".take-rail-viewport");
    const track = rail.querySelector(".take-track");
    const cards = [...rail.querySelectorAll(".take-card")];
    if (!viewport || !track || cards.length === 0) return;

    const currentScroll = viewport.scrollLeft;
    const maxScroll = Math.max(0, viewport.scrollWidth - viewport.clientWidth);
    const trackLeft = track.getBoundingClientRect().left;
    const cardOffsets = cards.map((card) => ({
      card,
      left: card.getBoundingClientRect().left - trackLeft,
    }));
    let targetScroll = currentScroll;
    if (delta > 0) {
      const nextCard = cardOffsets.find(
        (entry) => entry.left > currentScroll + 1,
      );
      targetScroll = nextCard ? nextCard.left : maxScroll;
    } else {
      const previousCards = cardOffsets.filter(
        (entry) => entry.left < currentScroll - 1,
      );
      const previousCard = previousCards.at(-1);
      targetScroll = previousCard ? previousCard.left : 0;
    }
    viewport.scrollTo({
      left: Math.min(maxScroll, Math.max(0, targetScroll)),
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
    });
  }

  function scheduleTakeRailPosition() {
    window.requestAnimationFrame(positionTakeRail);
  }

  function focusFrameButton(frameIndex) {
    window.requestAnimationFrame(() => {
      const button = elements.frameStrip.querySelector(
        `.frame-button[data-frame-index="${frameIndex}"]`,
      );
      if (button) button.focus({ preventScroll: true });
    });
  }

  function focusPreviewedTake() {
    window.requestAnimationFrame(() => {
      const previewedTake = elements.frameStrip.querySelector(
        ".take-card.is-previewing",
      );
      if (previewedTake) previewedTake.focus({ preventScroll: true });
    });
  }

  function renderFrameStrip() {
    const state = currentState();
    const takesByFrame = new Map(
      state.durations.map((_duration, index) => [
        index,
        frameTakesFor(currentVersion(), state, index),
      ]),
    );
    const expandedTakes =
      expandedTakeFrameIndex === null
        ? []
        : takesByFrame.get(expandedTakeFrameIndex) || [];
    if (!isInspectingFrame || expandedTakes.length === 0) {
      expandedTakeFrameIndex = null;
      activeFrameTake = null;
    }
    const expandedRowEnd =
      expandedTakeFrameIndex === null
        ? null
        : Math.min(
            state.durations.length - 1,
            Math.floor(expandedTakeFrameIndex / KEYFRAME_COLUMNS) *
              KEYFRAME_COLUMNS +
              (KEYFRAME_COLUMNS - 1),
          );
    const content = [];

    state.durations.forEach((duration, index) => {
      const takes = takesByFrame.get(index) || [];
      const hasConfirmedTake = hasConfirmedFrameTakeForFrame(
        currentVersion(),
        state,
        index,
      );
      const confirmedTakeId = confirmedTakeIdForFrame(
        currentVersion(),
        state,
        index,
      );
      const confirmedTake = confirmedTakeForFrame(
        currentVersion(),
        state,
        index,
      );
      const isExpanded =
        expandedTakeFrameIndex === index && takes.length > 0;
      const railId = `take-rail-${state.id}-${index}`;
      content.push(`
          <button
            class="frame-button ${
              index === activeFrameIndex &&
              !runtimeFellBack &&
              (isInspectingFrame ||
                playbackMode === "runtime" ||
                playbackMode === "loop")
                ? "is-active"
                : ""
            }"
            data-frame-index="${index}"
            data-take-count="${takes.length}"
            type="button"
            ${takes.length ? `aria-expanded="${String(isExpanded)}"` : ""}
            ${isExpanded ? `aria-controls="${escapeHtml(railId)}"` : ""}
            aria-label="${escapeHtml(
              takes.length
                ? t(
                    hasConfirmedTake
                      ? "ui.frameWithConfirmedTakeAria"
                      : "ui.frameWithTakesAria",
                    {
                      frame: index + 1,
                      duration: runtimeDurationLabel(state, index),
                      count: takes.length,
                      take:
                        confirmedTakeId === ORIGINAL_TAKE_ID
                          ? t("ui.originalFrame")
                          : frameTakeLabel(
                              confirmedTake,
                              takes.indexOf(confirmedTake),
                            ),
                    },
                  )
                : t("ui.frameAria", {
                    frame: index + 1,
                    duration: runtimeDurationLabel(state, index),
                  }),
            )}"
          >
            <span class="frame-thumbnail" style="${frameTakeStyle(
              confirmedTake,
              state,
              index,
            )}"></span>
            <small class="frame-duration">${escapeHtml(
              runtimeDurationLabel(state, index),
            )}</small>
            ${
              hasConfirmedTake
                ? '<span class="frame-take-confirmed" aria-hidden="true">✓</span>'
                : ""
            }
          </button>
      `);
      if (expandedRowEnd === index) {
        content.push(
          renderTakeRail(state, expandedTakeFrameIndex, expandedTakes),
        );
      }
    });
    elements.frameStrip.innerHTML = content.join("");

    frameButtons = [...elements.frameStrip.querySelectorAll(".frame-button")];
    frameButtons.forEach((button) => {
      button.addEventListener("click", () => {
        stopTour();
        const frameIndex = Number(button.dataset.frameIndex);
        const wasExpanded = expandedTakeFrameIndex === frameIndex;
        inspectFrame(frameIndex, {
          revealTakes: !wasExpanded,
          restoreFocus: true,
        });
      });
    });

    takeButtons = [...elements.frameStrip.querySelectorAll(".take-card")];
    takeButtons.forEach((button) => {
      button.addEventListener("click", () => {
        previewFrameTake(button.dataset.takeId);
      });
    });
    takeConfirmButton = elements.frameStrip.querySelector(
      ".take-rail-confirm-button",
    );
    if (takeConfirmButton) {
      takeConfirmButton.addEventListener("click", confirmFrameTake);
    }
    const takePreviousButton = elements.frameStrip.querySelector(
      ".take-rail-previous",
    );
    const takeNextButton = elements.frameStrip.querySelector(
      ".take-rail-next",
    );
    const takeRailViewport = elements.frameStrip.querySelector(
      ".take-rail-viewport",
    );
    if (takePreviousButton) {
      takePreviousButton.addEventListener("click", () => scrollTakeRail(-1));
    }
    if (takeNextButton) {
      takeNextButton.addEventListener("click", () => scrollTakeRail(1));
    }
    if (takeRailViewport) {
      takeRailViewport.addEventListener(
        "scroll",
        updateTakeRailNavigation,
        { passive: true },
      );
    }
    if (expandedRowEnd !== null) scheduleTakeRailPosition();
  }

  function renderMechanicsBoard() {
    const runtimeStates = currentRuntimeStates();
    elements.mechanicsBoard.hidden = runtimeStates.length === 0;
    const mechanicsBoards = runtimeStates.map((state) => {
      const configured = config.mechanics.find(
        (board) => board.stateId === state.id,
      );
      return configured || { stateId: state.id, anchors: [] };
    });
    const totalFrames = runtimeStates.reduce(
      (sum, state) => sum + state.durations.length,
      0,
    );
    elements.mechanicsSummary.textContent = t("ui.mechanicsSummary", {
      states: mechanicsBoards.length,
      frames: totalFrames,
    });
    elements.versionStatus.textContent = t("ui.viewingVersion", {
      version: versionLabel(currentVersion()),
    });

    elements.mechanicsRows.innerHTML = mechanicsBoards
      .map((board) => {
        const state = runtimeStates.find(
          (candidate) => candidate.id === board.stateId,
        );
        if (!state) return "";
        const boardCopy =
          valueAtPath(
            i18nBundle.messages[locale],
            `motionBoard.${board.stateId}`,
          ) ||
          valueAtPath(
            i18nBundle.messages[i18nBundle.fallbackLocale],
            `motionBoard.${board.stateId}`,
          ) ||
          {};
        const beats = boardCopy.beats || [];
        const physics = boardCopy.physics || [];
        const cards = state.durations
          .map(
            (duration, index) => `
              <button
                class="mechanics-card"
                type="button"
                data-state-id="${state.id}"
                data-frame-index="${index}"
              >
                <span
                  class="mechanics-sprite"
                  style="${frameTakeStyle(
                    displayedTakeForFrame(
                      currentVersion(),
                      state,
                      index,
                    ),
                    state,
                    index,
                  )}"
                ></span>
                <span class="mechanics-copy">
                  <span class="mechanics-frame-meta">
                    <span>F${index + 1}</span>
                    <span class="mechanics-duration">${escapeHtml(
                      runtimeDurationLabel(state, index),
                    )}</span>
                  </span>
                  <strong>${escapeHtml(
                    (Array.isArray(board.anchors) && board.anchors[index]) ||
                      `A${index}`,
                  )} · ${escapeHtml(beats[index] || "—")}</strong>
                  <p>${escapeHtml(physics[index] || "—")}</p>
                </span>
              </button>
            `,
          )
          .join("");
        return `
          <article class="mechanics-row">
            <div class="mechanics-state">
              <h3>${escapeHtml(boardCopy.title || stateCopy(state).title)}</h3>
              <p>${escapeHtml(boardCopy.summary || stateCopy(state).short)}</p>
            </div>
            <div class="mechanics-frames">${cards}</div>
          </article>
        `;
      })
      .join("");

    elements.mechanicsRows
      .querySelectorAll(".mechanics-card")
      .forEach((card) => {
        card.addEventListener("click", () => {
          const stateIndex = currentReviewStates().findIndex(
            (state) => state.id === card.dataset.stateId,
          );
          stopTour();
          setSection("animation");
          setState(stateIndex);
          inspectFrame(Number(card.dataset.frameIndex), {
            revealTakes: true,
          });
          window.scrollTo({
            top: 0,
            behavior: window.matchMedia("(prefers-reduced-motion: reduce)")
              .matches
              ? "auto"
              : "smooth",
          });
        });
      });
  }

  function renderDirectionList() {
    elements.directionList.innerHTML = config.directions
      .map(
        (direction, index) => `
          <button
            class="direction-button ${!lookIsNeutral && index === activeDirectionIndex ? "is-active" : ""}"
            data-direction-index="${index}"
            type="button"
          >
            ${Number(direction.degree)}°<br>${escapeHtml(directionLabel(direction))}
          </button>
        `,
      )
      .join("");

    directionButtons = [
      ...elements.directionList.querySelectorAll(".direction-button"),
    ];
    directionButtons.forEach((button) => {
      button.addEventListener("click", () => {
        setLookControlMode("manual");
        setDirection(Number(button.dataset.directionIndex));
      });
    });
  }

  function renderLookDetails() {
    elements.stateTag.textContent = t("ui.lookTag");
    elements.stateTitle.textContent = t("ui.lookTitle");
    elements.stateDescription.textContent = t("ui.lookDescription");
    elements.stateIntent.textContent = t("ui.lookIntent");
    elements.stateTrigger.textContent = t("ui.lookTrigger");
    const directionStep =
      config.directions.length > 1
        ? Math.abs(
            config.directions[1].degree - config.directions[0].degree,
          )
        : 0;
    elements.stateDuration.textContent = t("ui.lookDuration", {
      count: config.directions.length,
      step: Number(directionStep),
    });
    elements.spritePlayer.setAttribute(
      "aria-label",
      t("ui.assetAlt", {
        pet: config.pet.name,
        state: t("ui.lookTitle"),
      }),
    );
  }

  function renderControlLabels() {
    const reviewOnly =
      currentVersion() &&
      currentVersion().atlasPhase === STANDARD_INTERMEDIATE_PHASE;
    elements.atlasPhaseBadge.hidden = !reviewOnly;
    elements.atlasPhaseBadge.textContent = reviewOnly
      ? t("ui.atlasPhaseReviewOnly")
      : "";
    elements.atlasPhaseBadge.title = reviewOnly
      ? t("ui.atlasPhaseReviewOnlyTitle")
      : "";
    elements.playPauseButton.textContent = isInspectingFrame
      ? t("ui.play")
      : t("ui.pause");
    elements.endlessModeButton.textContent = t("ui.endlessLoop");
    elements.endlessModeButton.title = t("ui.endlessLoopTitle");
    elements.endlessModeButton.classList.toggle(
      "is-active",
      playbackMode === "loop",
    );
    elements.endlessModeButton.setAttribute(
      "aria-pressed",
      String(playbackMode === "loop"),
    );
    elements.runtimeModeButton.textContent = t("ui.runtimeTiming");
    elements.runtimeModeButton.title = t("ui.runtimeTimingTitle");
    elements.runtimeModeButton.classList.toggle(
      "is-active",
      playbackMode === "runtime",
    );
    elements.runtimeModeButton.setAttribute(
      "aria-pressed",
      String(playbackMode === "runtime"),
    );
    const browsingTakes = expandedTakeFrameIndex !== null;
    const activeTakeReady = activeTakeReadyForConfirmation();
    if (takeConfirmButton) {
      takeConfirmButton.disabled = !activeTakeReady;
      takeConfirmButton.title = t(
        activeTakeReady ? "ui.confirmTake" : "ui.takeAssetLoading",
      );
      takeConfirmButton.setAttribute(
        "aria-label",
        t(activeTakeReady ? "ui.confirmTake" : "ui.takeAssetLoading"),
      );
    }
    elements.transportControls.setAttribute(
      "aria-label",
      t("ui.transportAria"),
    );
    elements.previousFrameButton.title = t("ui.previousFrame");
    elements.previousFrameButton.setAttribute(
      "aria-label",
      t("ui.previousFrame"),
    );
    elements.nextFrameButton.title = t("ui.nextFrame");
    elements.nextFrameButton.setAttribute(
      "aria-label",
      t("ui.nextFrame"),
    );
    elements.previousFrameButton.disabled = false;
    elements.nextFrameButton.disabled = false;
    const modeHelp = t(
      browsingTakes
        ? "ui.takeRailHelp"
        : isInspectingFrame
          ? playbackMode === "loop"
            ? "ui.frameInspectionEndlessHelp"
            : "ui.frameInspectionRuntimeHelp"
          : playbackMode === "loop"
            ? "ui.endlessModeHelp"
            : currentState().id === config.runtime.idleStateId
              ? "ui.runtimeIdleModeHelp"
              : "ui.runtimeModeHelp",
      {
        loops: config.runtime.actionLoops,
      },
    );
    elements.previewModeHelp.textContent = modeHelp;
    const orbitActive = lookControlMode === "orbit";
    const pointerFollowActive = lookControlMode === "pointer";
    elements.orbitButton.textContent = t("ui.autoOrbit");
    elements.orbitButton.setAttribute(
      "aria-pressed",
      String(orbitActive),
    );
    elements.followPointerButton.textContent = t("ui.pointerFollow");
    elements.followPointerButton.setAttribute(
      "aria-pressed",
      String(pointerFollowActive),
    );
  }

  function renderAvailability() {
    const supportsLook = currentVersionSupportsLook();
    const runtimeStateCount = currentRuntimeStates().length;
    const supportsRuntimeSimulation = Boolean(runtimeIdleState());
    elements.lookTab.disabled = !supportsLook;
    elements.lookTab.setAttribute(
      "aria-disabled",
      String(!supportsLook),
    );
    elements.autoPlayStatesToggle.disabled = runtimeStateCount < 2;
    elements.runtimeModeButton.disabled = !supportsRuntimeSimulation;
    elements.animationControls.hidden =
      sectionMode !== "animation" || isStaticState(currentState());
  }

  function renderTourStatus() {
    const states = currentRuntimeStates();
    elements.tourProgress.hidden = !(
      tourState.active || tourState.completed
    );
    elements.autoPlayStatesToggle.setAttribute(
      "aria-pressed",
      String(tourState.active),
    );
    elements.autoPlayStatesToggle.title = t(
      tourState.active
        ? "ui.stopAutoPlayTitle"
        : "ui.startAutoPlayTitle",
    );

    if (tourState.active) {
      const state = states[tourState.index] || currentState();
      elements.tourLabel.textContent = t("ui.autoPlayingState", {
        state: stateCopy(state).title,
      });
      elements.tourProgressText.textContent = `${tourState.index + 1} / ${states.length}`;
      return;
    }

    if (tourState.completed) {
      elements.tourLabel.textContent = t("ui.allStatesPlayed");
      elements.tourProgressText.textContent = `${states.length} / ${states.length}`;
      setTourProgress(100);
      return;
    }

    elements.tourLabel.textContent = "";
    elements.tourProgressText.textContent = "";
  }

  function renderFrameReadout() {
    if (sectionMode === "look") {
      if (lookIsNeutral) {
        elements.frameReadout.textContent = t("ui.lookNeutralReadout", {
          state: stateCopy(neutralLookState()).title,
        });
        return;
      }
      const direction = config.directions[activeDirectionIndex];
      elements.frameReadout.textContent = `${direction.degree}° · ${directionLabel(direction)}`;
      return;
    }

    const state = currentState();
    if (isStaticState(state) && !isInspectingFrame) {
      elements.frameReadout.textContent = t("ui.staticReadout");
      return;
    }
    if (isInspectingFrame) {
      const take = displayedTakeForCurrentFrame();
      elements.frameReadout.textContent = take
        ? t("ui.takeFrameReadout", {
            frame: activeFrameIndex + 1,
            count: state.durations.length,
            take: frameTakeLabel(
              take,
              frameTakesFor(
                currentVersion(),
                state,
                activeFrameIndex,
              ).indexOf(take),
            ),
          })
        : t("ui.frameReadout", {
            frame: activeFrameIndex + 1,
            count: state.durations.length,
          });
      return;
    }

    if (playbackMode === "loop") {
      elements.frameReadout.textContent = t("ui.endlessLoopReadout", {
        frame: activeFrameIndex + 1,
        count: state.durations.length,
      });
      return;
    }

    if (playbackMode === "runtime") {
      const playbackState = displayedState();
      if (runtimeFellBack) {
        elements.frameReadout.textContent = t("ui.runtimeReturnedIdle", {
          frame: activeFrameIndex + 1,
          count: playbackState.durations.length,
        });
      } else if (state.id === config.runtime.idleStateId) {
        elements.frameReadout.textContent = t("ui.runtimeSlowIdle", {
          frame: activeFrameIndex + 1,
          count: state.durations.length,
        });
      } else {
        elements.frameReadout.textContent = t("ui.runtimeLoopReadout", {
          loop: runtimeLoopsCompleted + 1,
          loops: config.runtime.actionLoops,
          frame: activeFrameIndex + 1,
          count: state.durations.length,
        });
      }
      return;
    }

  }

  function renderPlayer() {
    if (sectionMode === "look") {
      elements.spritePlayer.style.display = "block";
      if (lookIsNeutral) {
        setSpriteFrame(
          config.neutralLookReferenceSlot.row,
          config.neutralLookReferenceSlot.column,
        );
        elements.stageModeLabel.textContent = t("ui.neutralLookFrame");
        return;
      }
      const direction = config.directions[activeDirectionIndex];
      setSpriteFrame(direction.row, direction.column);
      elements.stageModeLabel.textContent = t("ui.finalLookFrame");
      return;
    }

    if (isInspectingFrame) {
      elements.spritePlayer.style.display = "block";
      const state = currentState();
      const take = displayedTakeForCurrentFrame();
      if (take) {
        setTakeSpriteFrame(
          take,
          elements.spritePlayer,
          state,
          activeFrameIndex,
        );
      } else {
        setOriginalFrame(state, activeFrameIndex);
      }
      elements.stageModeLabel.textContent = isStaticState(state)
        ? t("ui.static")
        : t("ui.frameInspectionLabel");
      clearFrameTimer();
      return;
    }

    elements.spritePlayer.style.display = "block";
    const playbackState = displayedState();
    const confirmedTake = confirmedTakeForFrame(
      currentVersion(),
      playbackState,
      activeFrameIndex,
    );
    if (confirmedTake) {
      setTakeSpriteFrame(
        confirmedTake,
        elements.spritePlayer,
        playbackState,
        activeFrameIndex,
      );
    } else {
      setOriginalFrame(playbackState, activeFrameIndex);
    }
    elements.stageModeLabel.textContent = isStaticState(playbackState)
      ? t("ui.static")
      :
      playbackMode === "loop"
        ? t("ui.endlessLoop")
        : runtimeFellBack
          ? t("ui.runtimeBackToIdle")
          : currentState().id === config.runtime.idleStateId
            ? t("ui.runtimeIdle")
            : t("ui.runtimeAction", {
                loops: config.runtime.actionLoops,
              });
  }

  function refreshActiveClasses() {
    stateButtons.forEach((button, index) => {
      button.classList.toggle("is-active", index === activeStateIndex);
    });
    frameButtons.forEach((button, index) => {
      button.classList.toggle(
        "is-active",
        index === activeFrameIndex &&
          !runtimeFellBack &&
          (isInspectingFrame ||
            playbackMode === "runtime" ||
            playbackMode === "loop"),
      );
    });
    refreshTakeClasses();
  }

  function refreshTakeClasses() {
    const activeTakeId = activeTakeIdForCurrentFrame();
    const hasConfirmedTake = hasConfirmedFrameTakeForFrame(
      currentVersion(),
      currentState(),
      activeFrameIndex,
    );
    const confirmedTakeId = confirmedTakeIdForFrame(
      currentVersion(),
      currentState(),
      activeFrameIndex,
    );
    takeButtons.forEach((button) => {
      const isActive = button.dataset.takeId === activeTakeId;
      const isConfirmed =
        hasConfirmedTake && button.dataset.takeId === confirmedTakeId;
      button.classList.toggle("is-previewing", isActive);
      button.classList.toggle("is-confirmed", isConfirmed);
      button.setAttribute("aria-pressed", String(isActive));
    });
  }

  function clearFrameTimer() {
    if (frameTimer) {
      window.clearTimeout(frameTimer);
      frameTimer = null;
    }
  }

  function resetRuntimePlayback() {
    runtimeFramesCompleted = 0;
    runtimeLoopsCompleted = 0;
    runtimeFellBack = false;
  }

  function setFrame(index) {
    const state = displayedState();
    activeFrameIndex =
      ((index % state.durations.length) + state.durations.length) %
      state.durations.length;
    renderPlayer();
    refreshActiveClasses();
    renderFrameReadout();
  }

  function shouldScheduleFrames() {
    return (
      isPlaying &&
      pageVisible &&
      !isInspectingFrame &&
      sectionMode === "animation" &&
      !isStaticState(currentState())
    );
  }

  function scheduleNextFrame() {
    clearFrameTimer();
    if (!shouldScheduleFrames()) return;

    const state = displayedState();
    const delay = runtimeFrameDuration(state, activeFrameIndex);

    frameTimer = window.setTimeout(() => {
      const wrapped = activeFrameIndex + 1 >= state.durations.length;

      if (
        playbackMode === "runtime" &&
        !runtimeFellBack &&
        currentState().id !== config.runtime.idleStateId
      ) {
        runtimeFramesCompleted += 1;
        runtimeLoopsCompleted = Math.floor(
          runtimeFramesCompleted / state.durations.length,
        );
        if (
          runtimeFramesCompleted >=
          state.durations.length * config.runtime.actionLoops
        ) {
          runtimeFellBack = true;
          activeFrameIndex = 0;
          renderPlayer();
          refreshActiveClasses();
          renderFrameReadout();
          scheduleNextFrame();
          return;
        }
      }

      setFrame(wrapped ? 0 : activeFrameIndex + 1);
      scheduleNextFrame();
    }, delay);
  }

  function restartPlayback() {
    clearFrameTakeState();
    resetRuntimePlayback();
    activeFrameIndex = 0;
    isInspectingFrame = false;
    isPlaying = true;
    renderFrameStrip();
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function enterFrameInspection({ render = true } = {}) {
    clearFrameTakeState();
    if (runtimeFellBack) activeFrameIndex = 0;
    resetRuntimePlayback();
    activeFrameIndex = Math.min(
      activeFrameIndex,
      currentState().durations.length - 1,
    );
    isInspectingFrame = true;
    isPlaying = false;
    clearFrameTimer();
    if (!render) return;
    renderFrameStrip();
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    setReviewFocusFromCurrent({ includeFrame: true });
  }

  function resumeSelectedPlayback() {
    clearFrameTakeState();
    resetRuntimePlayback();
    isInspectingFrame = false;
    isPlaying = true;
    renderFrameStrip();
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function inspectFrame(
    index,
    { revealTakes = false, restoreFocus = false } = {},
  ) {
    enterFrameInspection({ render: false });
    const frameCount = currentState().durations.length;
    activeFrameIndex =
      ((index % frameCount) + frameCount) % frameCount;
    const takes = frameTakesFor(
      currentVersion(),
      currentState(),
      activeFrameIndex,
    );
    expandedTakeFrameIndex =
      revealTakes && takes.length ? activeFrameIndex : null;
    if (expandedTakeFrameIndex !== null) {
      primeFrameTakeFromConfirmed();
    }
    renderFrameStrip();
    renderControlLabels();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    if (restoreFocus) focusFrameButton(activeFrameIndex);
    setReviewFocusFromCurrent({ includeFrame: true });
  }

  function setPreviewSize(value) {
    const numericValue = Number(value);
    const boundedValue = Number.isFinite(numericValue)
      ? Math.min(
          config.display.maximumPx,
          Math.max(config.display.minimumPx, numericValue),
        )
      : PREVIEW_SIZE_INITIAL_PX;
    previewSizePx = Math.round(boundedValue);
    elements.previewSizeInput.min = String(config.display.minimumPx);
    elements.previewSizeInput.max = String(config.display.maximumPx);
    elements.previewSizeInput.value = String(previewSizePx);
    elements.previewSizeValue.textContent = `${previewSizePx} px`;
    elements.stage.style.setProperty(
      "--preview-width",
      `${previewSizePx}px`,
    );
    elements.stage.style.setProperty(
      "--preview-height",
      `${Math.round(
        (previewSizePx * config.sprite.frameHeight) /
          config.sprite.frameWidth,
      )}px`,
    );
  }

  function togglePlayback() {
    if (isInspectingFrame) resumeSelectedPlayback();
    else enterFrameInspection();
  }

  function setState(index, options = {}) {
    clearFrameTakeState();
    const states = currentReviewStates();
    activeStateIndex =
      ((index % states.length) + states.length) % states.length;
    activeFrameIndex = 0;
    resetRuntimePlayback();
    if (!runtimeIdleState() && playbackMode === "runtime") {
      playbackMode = "loop";
    }
    isInspectingFrame = false;
    isPlaying = true;
    renderStateList();
    renderDetails();
    renderControlLabels();
    renderAvailability();
    renderFrameStrip();
    renderPlayer();
    renderFrameReadout();
    scheduleNextFrame();

    if (!options.fromTour) {
      tourState.completed = false;
      setTourProgress(0);
      renderTourStatus();
      setReviewFocusFromCurrent({
        includeFrame: isStaticState(currentState()),
        takeId: ORIGINAL_TAKE_ID,
      });
    }
  }

  function setPlaybackMode(mode) {
    if (!["loop", "runtime"].includes(mode)) return;
    if (mode === "runtime" && !runtimeIdleState()) return;
    clearFrameTakeState();
    clearFrameTimer();
    playbackMode = mode;
    resetRuntimePlayback();
    activeFrameIndex = 0;
    isInspectingFrame = false;
    isPlaying = true;
    renderFrameStrip();
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function stepFrame(delta) {
    inspectFrame(activeFrameIndex + delta);
  }

  function setSection(mode, { updateReviewFocus = false } = {}) {
    if (mode === "look" && !currentVersionSupportsLook()) {
      mode = "animation";
    }
    const sectionChanged = sectionMode !== mode;
    if (tourState.active) stopTour();
    clearFrameTakeState();
    sectionMode = mode;
    const isAnimation = mode === "animation";
    elements.animationTab.classList.toggle("is-active", isAnimation);
    elements.animationTab.setAttribute(
      "aria-selected",
      String(isAnimation),
    );
    elements.lookTab.classList.toggle("is-active", !isAnimation);
    elements.lookTab.setAttribute("aria-selected", String(!isAnimation));
    elements.lookTab.disabled = !currentVersionSupportsLook();
    elements.lookTab.setAttribute(
      "aria-disabled",
      String(!currentVersionSupportsLook()),
    );
    elements.stateList.style.opacity = isAnimation ? "1" : "0.42";
    elements.stateList.style.pointerEvents = isAnimation ? "auto" : "none";
    elements.staticList.style.opacity = isAnimation ? "1" : "0.42";
    elements.staticList.style.pointerEvents = isAnimation ? "auto" : "none";
    elements.animationControls.hidden =
      !isAnimation || isStaticState(currentState());
    elements.lookControls.hidden = isAnimation;
    elements.frameStrip.parentElement.hidden = !isAnimation;
    renderAvailability();
    setLookControlMode(isAnimation ? "manual" : "pointer");

    if (isAnimation) {
      renderDetails();
      renderFrameStrip();
      renderControlLabels();
      renderPlayer();
      renderFrameReadout();
      scheduleNextFrame();
    } else {
      clearFrameTimer();
      if (lookControlMode !== "pointer") {
        setDirection(activeDirectionIndex);
      }
    }
    if (sectionChanged && updateReviewFocus) {
      setReviewFocusFromCurrent({
        includeFrame:
          mode === "animation" &&
          (isInspectingFrame || isStaticState(currentState())),
        takeId: isStaticState(currentState())
          ? ORIGINAL_TAKE_ID
          : null,
      });
    }
  }

  function setDirection(index) {
    lookIsNeutral = false;
    activeDirectionIndex =
      ((index % config.directions.length) + config.directions.length) %
      config.directions.length;
    directionButtons.forEach((button, buttonIndex) => {
      button.classList.toggle(
        "is-active",
        buttonIndex === activeDirectionIndex,
      );
    });
    renderLookDetails();
    renderFrameReadout();
    renderPlayer();
  }

  function neutralLookState() {
    return (
      config.states.find(
        (state) => state.id === config.neutralLookStateId,
      ) ||
      idleState()
    );
  }

  function setLookNeutral() {
    if (lookIsNeutral) return;
    lookIsNeutral = true;
    directionButtons.forEach((button) => {
      button.classList.remove("is-active");
    });
    renderLookDetails();
    renderFrameReadout();
    renderPlayer();
  }

  function clearOrbitTimer() {
    if (!orbitTimer) return;
    window.clearInterval(orbitTimer);
    orbitTimer = null;
  }

  function startOrbitTimer() {
    clearOrbitTimer();
    if (
      !pageVisible ||
      lookControlMode !== "orbit" ||
      sectionMode !== "look"
    ) {
      return;
    }
    let directionIndex = activeDirectionIndex;
    orbitTimer = window.setInterval(() => {
      directionIndex = (directionIndex + 1) % config.directions.length;
      setDirection(directionIndex);
    }, LOOK_ORBIT_STEP_MS);
  }

  function cancelPointerUpdate() {
    pendingPointerSample = null;
    if (pointerFrameRequest === null) return;
    window.cancelAnimationFrame(pointerFrameRequest);
    pointerFrameRequest = null;
  }

  function setLookControlMode(mode) {
    const nextMode = ["manual", "orbit", "pointer"].includes(mode)
      ? mode
      : "manual";
    clearOrbitTimer();
    cancelPointerUpdate();
    elements.directionTarget.style.display = "none";
    lookControlMode = nextMode;

    if (lookControlMode === "pointer" && sectionMode === "look") {
      setLookNeutral();
    } else if (lookControlMode === "orbit") {
      setDirection(activeDirectionIndex);
      startOrbitTimer();
    } else if (sectionMode === "look" && lookIsNeutral) {
      setDirection(activeDirectionIndex);
    }
    renderControlLabels();
  }

  function toggleLookControlMode(mode) {
    setLookControlMode(lookControlMode === mode ? "manual" : mode);
  }

  function handlePointerMove(event) {
    if (lookControlMode !== "pointer" || sectionMode !== "look") return;
    if (
      event.target instanceof Element &&
      event.target.closest(".preview-size-control")
    ) {
      return;
    }
    pendingPointerSample = {
      clientX: event.clientX,
      clientY: event.clientY,
    };
    if (pointerFrameRequest !== null) return;
    pointerFrameRequest = window.requestAnimationFrame(flushPointerMove);
  }

  function flushPointerMove() {
    pointerFrameRequest = null;
    const sample = pendingPointerSample;
    pendingPointerSample = null;
    if (
      !sample ||
      !pageVisible ||
      lookControlMode !== "pointer" ||
      sectionMode !== "look"
    ) {
      return;
    }

    const rect = elements.stage.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const deltaX = sample.clientX - centerX;
    const deltaY = sample.clientY - centerY;
    if (Math.hypot(deltaX, deltaY) < 28) {
      elements.directionTarget.style.display = "none";
      setLookNeutral();
      return;
    }

    const degrees =
      (Math.atan2(deltaX, -deltaY) * (180 / Math.PI) + 360) % 360;
    const directionIndex =
      Math.round(degrees / (360 / config.directions.length)) %
      config.directions.length;
    if (lookIsNeutral || directionIndex !== activeDirectionIndex) {
      setDirection(directionIndex);
    }
    elements.directionTarget.style.display = "block";
    elements.directionTarget.style.transform =
      `translate3d(${sample.clientX - rect.left}px, ${sample.clientY - rect.top}px, 0) ` +
      "translate(-50%, -50%)";
  }

  function clearTourTimers() {
    if (tourTimer) window.clearTimeout(tourTimer);
    if (tourProgressTimer) window.clearInterval(tourProgressTimer);
    tourTimer = null;
    tourProgressTimer = null;
  }

  function stopTour({ completed = false } = {}) {
    clearTourTimers();
    tourState = {
      active: false,
      completed,
      index: completed ? currentRuntimeStates().length - 1 : 0,
      startedAt: 0,
      holdMs: 0,
    };
    if (!completed) setTourProgress(0);
    renderTourStatus();
  }

  function setTourProgress(percent) {
    const bounded = Math.min(100, Math.max(0, Number(percent) || 0));
    elements.tourProgressBar.style.transform = `scaleX(${bounded / 100})`;
  }

  function handleVisibilityChange() {
    pageVisible = document.visibilityState !== "hidden";

    if (!pageVisible) {
      clearFrameTimer();
      clearOrbitTimer();
      cancelPointerUpdate();
      clearTourTimers();
      return;
    }

    if (tourState.active) {
      showNextTourState();
      return;
    }

    if (lookControlMode === "orbit") startOrbitTimer();
    renderPlayer();
    scheduleNextFrame();
  }

  function showNextTourState() {
    const states = currentRuntimeStates();
    if (tourState.index >= states.length) {
      stopTour({ completed: true });
      return;
    }

    const state = states[tourState.index];
    const reviewStateIndex = currentReviewStates().findIndex(
      (candidate) => candidate.id === state.id,
    );
    setState(reviewStateIndex, { fromTour: true });
    restartPlayback();
    const runtimeMultiplier =
      state.id === config.runtime.idleStateId
        ? config.runtime.idleDurationMultiplier
        : config.runtime.actionLoops;
    tourState.holdMs = Math.max(
      3600,
      totalDuration(state) * runtimeMultiplier,
    );
    tourState.startedAt = performance.now();
    renderTourStatus();

    if (tourProgressTimer) window.clearInterval(tourProgressTimer);
    tourProgressTimer = window.setInterval(() => {
      const elapsed = performance.now() - tourState.startedAt;
      const withinState = Math.min(1, elapsed / tourState.holdMs);
      const overall =
        ((tourState.index + withinState) / states.length) * 100;
      setTourProgress(overall);
    }, TOUR_PROGRESS_STEP_MS);

    tourTimer = window.setTimeout(() => {
      if (tourProgressTimer) window.clearInterval(tourProgressTimer);
      tourProgressTimer = null;
      tourState.index += 1;
      showNextTourState();
    }, tourState.holdMs);
  }

  function startTour() {
    stopTour();
    setSection("animation");
    setPlaybackMode("runtime");
    tourState.active = true;
    tourState.completed = false;
    tourState.index = 0;
    showNextTourState();
  }

  function toggleAllStatePlayback() {
    if (tourState.active) stopTour();
    else startTour();
  }

  function setBackground(name) {
    if (!config.backgrounds.includes(name)) return;
    activeBackground = name;
    config.backgrounds.forEach((background) => {
      elements.stage.classList.remove(`stage-${background}`);
    });
    elements.stage.classList.add(`stage-${name}`);
    document.querySelectorAll(".swatch").forEach((swatch) => {
      swatch.classList.toggle(
        "is-active",
        swatch.dataset.background === name,
      );
    });
  }

  function setVersion(versionId) {
    const nextVersion = config.versions.find(
      (version) => version.id === versionId,
    );
    if (!nextVersion) return;
    const availability = candidateAvailability.get(nextVersion.id);
    if (!availability || availability.status !== "valid") {
      if (availability && availability.diagnostic) {
        showDiagnostic(availability.diagnostic, {
          global: false,
          focus: true,
        });
      }
      return;
    }

    clearFrameTakeState();
    const previousStateId = currentState() ? currentState().id : null;
    const wasPlaying = isPlaying;
    const wasInspectingFrame = isInspectingFrame;
    clearFrameTimer();
    activeVersionId = nextVersion.id;
    hideDiagnostic();
    reviewContextReady = true;
    const nextStates = currentReviewStates();
    const preservedStateIndex = nextStates.findIndex(
      (state) => state.id === previousStateId,
    );
    activeStateIndex = preservedStateIndex >= 0 ? preservedStateIndex : 0;
    if (!runtimeIdleState() && playbackMode === "runtime") {
      playbackMode = "loop";
    }
    if (sectionMode === "look" && !currentVersionSupportsLook()) {
      sectionMode = "animation";
    }
    elements.versionSelect.value = activeVersionId;
    isInspectingFrame = wasInspectingFrame;
    isPlaying = wasInspectingFrame ? false : wasPlaying;
    const frameCount = currentState().durations.length;
    activeFrameIndex = Math.min(activeFrameIndex, frameCount - 1);
    renderFrameStrip();
    renderStateList();
    renderMechanicsBoard();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    renderControlLabels();
    renderAvailability();
    refreshActiveClasses();
    scheduleNextFrame();
    setSection(sectionMode);
    setReviewFocusFromCurrent({
      includeFrame:
        sectionMode === "animation" &&
        (isInspectingFrame || isStaticState(currentState())),
      takeId: isStaticState(currentState())
        ? ORIGINAL_TAKE_ID
        : null,
    });
  }

  function setLocale(nextLocale) {
    const supported = supportedLocale(nextLocale);
    if (!supported) return;
    locale = supported;
    storeLocale(locale);
    applyStaticTranslations();
    populateLanguageSelect();
    populateVersionSelect();
    if (activeDiagnostic) {
      showDiagnostic(activeDiagnostic, {
        global: activeDiagnostic.scope === "global",
      });
      return;
    }
    renderStateList();
    if (sectionMode === "look") renderLookDetails();
    else renderDetails();
    renderFrameStrip();
    renderMechanicsBoard();
    renderDirectionList();
    renderControlLabels();
    renderAvailability();
    renderTourStatus();
    renderPlayer();
    renderFrameReadout();
  }

  function attachEvents() {
    elements.animationTab.addEventListener("click", () =>
      setSection("animation", { updateReviewFocus: true }),
    );
    elements.lookTab.addEventListener("click", () =>
      setSection("look", { updateReviewFocus: true }),
    );
    elements.runtimeModeButton.addEventListener("click", () =>
      setPlaybackMode("runtime"),
    );
    elements.endlessModeButton.addEventListener("click", () =>
      setPlaybackMode("loop"),
    );
    elements.playPauseButton.addEventListener("click", togglePlayback);
    elements.previousFrameButton.addEventListener("click", () =>
      stepFrame(-1),
    );
    elements.nextFrameButton.addEventListener("click", () =>
      stepFrame(1),
    );
    elements.restartButton.addEventListener("click", restartPlayback);
    elements.previewSizeInput.addEventListener("input", () =>
      setPreviewSize(elements.previewSizeInput.value),
    );
    elements.orbitButton.addEventListener("click", () => {
      toggleLookControlMode("orbit");
    });
    elements.followPointerButton.addEventListener("click", () => {
      toggleLookControlMode("pointer");
    });
    elements.stage.addEventListener("pointermove", handlePointerMove);
    elements.stage.addEventListener("pointerleave", () => {
      cancelPointerUpdate();
      if (lookControlMode === "pointer") {
        elements.directionTarget.style.display = "none";
        setLookNeutral();
      }
    });
    elements.autoPlayStatesToggle.addEventListener(
      "click",
      toggleAllStatePlayback,
    );
    elements.versionSelect.addEventListener("change", () =>
      setVersion(elements.versionSelect.value),
    );
    elements.languageSelect.addEventListener("change", () =>
      setLocale(elements.languageSelect.value),
    );
    document.querySelectorAll(".swatch").forEach((swatch) => {
      swatch.addEventListener("click", () =>
        setBackground(swatch.dataset.background),
      );
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && expandedTakeFrameIndex !== null) {
        const frameIndex = expandedTakeFrameIndex;
        clearFrameTakeState();
        renderFrameStrip();
        renderControlLabels();
        renderPlayer();
        renderFrameReadout();
        focusFrameButton(frameIndex);
        setReviewFocusFromCurrent({ includeFrame: true });
        return;
      }
      if (event.target.matches("select, input, textarea")) return;
      const railActionControl = event.target.closest(
        ".take-rail-nav-button, .take-rail-confirm-button",
      );
      if (railActionControl) {
        if (["ArrowLeft", "ArrowRight"].includes(event.key)) {
          event.preventDefault();
        }
        return;
      }
      if (
        sectionMode === "look" &&
        [" ", "ArrowLeft", "ArrowRight"].includes(event.key)
      ) {
        return;
      }
      if (["ArrowLeft", "ArrowRight"].includes(event.key)) {
        event.preventDefault();
        const focusedTake = event.target.closest(".take-card");
        const focusedFrame = event.target.closest(".frame-button");
        const delta = event.key === "ArrowLeft" ? -1 : 1;
        if (focusedTake && expandedTakeFrameIndex !== null) {
          stepTake(delta);
          focusPreviewedTake();
        } else {
          stepFrame(delta);
          if (focusedFrame) focusFrameButton(activeFrameIndex);
        }
        return;
      }
      if (event.target.matches("button")) return;
      if (event.key === " ") {
        event.preventDefault();
        togglePlayback();
      } else if (/^[1-9]$/.test(event.key)) {
        const stateIndex = Number(event.key) - 1;
        const runtimeState = currentRuntimeStates()[stateIndex];
        if (runtimeState) {
          const reviewStateIndex = currentReviewStates().findIndex(
            (state) => state.id === runtimeState.id,
          );
          setSection("animation");
          setState(reviewStateIndex);
        }
      }
    });
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("resize", scheduleTakeRailPosition);

  }

  async function boot() {
    const requestedReviewContext = readReviewContextFromUrl();
    const loaded = await loadConfig(requestedReviewContext);
    configBaseUrl = loaded.baseUrl;
    config = normalizeConfig(loaded.data, loaded.isExternal);
    activeVersionId = loaded.selectedCandidateId;

    applyStaticTranslations();
    populateLanguageSelect();
    populateVersionSelect();
    attachEvents();
    if (loaded.globalDiagnostic) {
      showDiagnostic(loaded.globalDiagnostic, { global: true, focus: true });
      return;
    }
    if (loaded.activeDiagnostic) {
      showDiagnostic(loaded.activeDiagnostic, { global: false, focus: true });
      startBackgroundCandidateDiagnostics(loaded);
      return;
    }

    hideDiagnostic();
    renderStateList();
    renderDirectionList();
    renderFrameStrip();
    renderMechanicsBoard();
    renderControlLabels();
    renderTourStatus();
    setBackground(activeBackground);
    setPreviewSize(previewSizePx);
    setState(0);
    setSection("animation");
    restoreReviewContextFromUrl(requestedReviewContext);
    reviewContextReady = true;
    syncReviewContextToUrl();
    startBackgroundCandidateDiagnostics(loaded);
  }

  boot();
})();
