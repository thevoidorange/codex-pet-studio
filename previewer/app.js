(() => {
  "use strict";

  const STORAGE_KEY = "codexPetStudio.previewer.locale";
  const i18nBundle = window.PET_PREVIEW_I18N;
  const bundledConfig = window.PET_PREVIEW_CONFIG;
  const generatedAtlases = new Map();
  const FIXED_ACTION_LOOPS = 3;
  const FIXED_IDLE_SLOWDOWN = 6;
  const PREVIEW_SIZE_MIN_PX = 80;
  const PREVIEW_SIZE_MAX_PX = 224;
  const PREVIEW_SIZE_INITIAL_PX = 160;
  const LOOK_ORBIT_STEP_MS = 120;
  const TOUR_PROGRESS_STEP_MS = 160;

  const elements = {
    animationControls: document.querySelector("#animationControls"),
    animationTab: document.querySelector("#animationTab"),
    autoPlayStatesToggle: document.querySelector("#autoPlayStatesToggle"),
    directionList: document.querySelector("#directionList"),
    directionTarget: document.querySelector("#directionTarget"),
    endlessModeButton: document.querySelector("#endlessModeButton"),
    followPointerButton: document.querySelector("#followPointerButton"),
    frameReadout: document.querySelector("#frameReadout"),
    frameStrip: document.querySelector("#frameStrip"),
    languageSelect: document.querySelector("#languageSelect"),
    lookControls: document.querySelector("#lookControls"),
    lookTab: document.querySelector("#lookTab"),
    mechanicsRows: document.querySelector("#mechanicsRows"),
    mechanicsSummary: document.querySelector("#mechanicsSummary"),
    nextFrameButton: document.querySelector("#nextFrameButton"),
    orbitButton: document.querySelector("#orbitButton"),
    playPauseButton: document.querySelector("#playPauseButton"),
    previewModeHelp: document.querySelector("#previewModeHelp"),
    previewSizeInput: document.querySelector("#previewSizeInput"),
    previewSizeValue: document.querySelector("#previewSizeValue"),
    previousFrameButton: document.querySelector("#previousFrameButton"),
    restartButton: document.querySelector("#restartButton"),
    runtimeModeButton: document.querySelector("#runtimeModeButton"),
    spritePlayer: document.querySelector("#spritePlayer"),
    stage: document.querySelector("#stage"),
    stageModeLabel: document.querySelector("#stageModeLabel"),
    stateCount: document.querySelector("#stateCount"),
    stateDescription: document.querySelector("#stateDescription"),
    stateDuration: document.querySelector("#stateDuration"),
    stateIntent: document.querySelector("#stateIntent"),
    stateList: document.querySelector("#stateList"),
    stateTag: document.querySelector("#stateTag"),
    stateTitle: document.querySelector("#stateTitle"),
    stateTrigger: document.querySelector("#stateTrigger"),
    tourLabel: document.querySelector("#tourLabel"),
    tourProgress: document.querySelector("#tourProgress"),
    tourProgressBar: document.querySelector("#tourProgressBar"),
    tourProgressText: document.querySelector("#tourProgressText"),
    versionSelect: document.querySelector("#versionSelect"),
    versionStatus: document.querySelector("#versionStatus"),
  };

  let config = null;
  let configBaseUrl = window.location.href;
  let locale = resolveInitialLocale();
  let activeVersionId = "";
  let activeStateIndex = 0;
  let activeFrameIndex = 0;
  let activeDirectionIndex = 0;
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
    let exampleId = "example";
    let suffix = 2;
    while (usedIds.has(exampleId)) {
      exampleId = `example-${suffix}`;
      suffix += 1;
    }

    const bundledDefault =
      bundledVersions.find((version) => version.isDefault) ||
      bundledVersions[0];
    const example = {
      ...cloneValue(bundledDefault),
      id: exampleId,
      displayName: "Example",
      labelKey: "ui.exampleVersion",
      statusKey: null,
      isDefault: false,
      isBundledExample: true,
    };
    return [...versions, example];
  }

  async function loadConfig() {
    const configUrl = new URLSearchParams(window.location.search).get("config");
    if (!configUrl) {
      return {
        data: bundledConfig,
        baseUrl: window.location.href,
        isExternal: false,
      };
    }

    try {
      const resolvedUrl = new URL(configUrl, window.location.href);
      const response = await window.fetch(resolvedUrl);
      if (!response.ok) {
        throw new Error(`Config request failed with ${response.status}`);
      }
      const data = await response.json();
      return {
        data,
        baseUrl: resolvedUrl.href,
        isExternal: true,
      };
    } catch (error) {
      console.warn("Could not load external preview config.", error);
      return {
        data: bundledConfig,
        baseUrl: window.location.href,
        isExternal: false,
      };
    }
  }

  function normalizeConfig(input, includeBundledExample = false) {
    const base = cloneValue(bundledConfig);
    const next = input && typeof input === "object" ? input : {};
    const projectVersions =
      Array.isArray(next.versions) && next.versions.length
        ? next.versions
        : null;
    const normalized = {
      ...base,
      pet: { ...base.pet, ...(next.pet || {}) },
      sprite: cloneValue(base.sprite),
      versions: projectVersions
        ? includeBundledExample
          ? withBundledExample(projectVersions, base.versions)
          : projectVersions
        : base.versions,
      states: cloneValue(base.states),
      directions: cloneValue(base.directions),
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
    return (
      config.versions.find((version) => version.id === activeVersionId) ||
      config.versions[0]
    );
  }

  function currentState() {
    return config.states[activeStateIndex] || config.states[0];
  }

  function idleState() {
    return (
      config.states.find((state) => state.id === "idle") || config.states[0]
    );
  }

  function displayedState() {
    return !isInspectingFrame && playbackMode === "runtime" && runtimeFellBack
      ? idleState()
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
    const status = version.statusKey ? t(version.statusKey) : "";
    return [version.displayName || version.id, status]
      .filter(Boolean)
      .join(" · ");
  }

  function directionLabel(direction) {
    return t(`directions.${direction.key}`);
  }

  function runtimeFrameDuration(state, frameIndex) {
    const baseDuration = state.durations[frameIndex];
    return state.id === idleState().id
      ? baseDuration * FIXED_IDLE_SLOWDOWN
      : baseDuration;
  }

  function runtimeDurationLabel(state, frameIndex) {
    const baseDuration = state.durations[frameIndex];
    if (state.id === idleState().id) {
      return t("ui.idleFrameDuration", {
        duration: baseDuration,
        multiplier: FIXED_IDLE_SLOWDOWN,
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

    if (state.id === "idle") {
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
      state.id === "idle" &&
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
    elements.versionSelect.innerHTML = config.versions
      .map(
        (version) =>
          `<option value="${escapeHtml(version.id)}">${escapeHtml(versionLabel(version))}</option>`,
      )
      .join("");
    elements.versionSelect.value = activeVersionId;
  }

  function renderStateList() {
    elements.stateCount.textContent = t("ui.stateCount", {
      count: config.states.length,
    });
    elements.stateList.innerHTML = config.states
      .map((state, index) => {
        const copy = stateCopy(state);
        return `
          <button
            class="state-button ${index === activeStateIndex ? "is-active" : ""}"
            data-state-index="${index}"
            type="button"
            aria-label="${escapeHtml([copy.title, copy.label].join(" · "))}"
          >
            <span class="state-index">${String(index + 1).padStart(2, "0")}</span>
            <span class="state-name">
              <strong>${escapeHtml(copy.title)}</strong>
              <small>${escapeHtml(copy.label)}</small>
            </span>
          </button>
        `;
      })
      .join("");

    stateButtons = [...elements.stateList.querySelectorAll(".state-button")];
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
    if (state.id === idleState().id) {
      return t("ui.runtimeIdleNote");
    }
    return t("ui.runtimeActionNote", {
      loops: FIXED_ACTION_LOOPS,
    });
  }

  function renderDetails() {
    const state = currentState();
    const copy = stateCopy(state);
    elements.stateTag.textContent = `${String(activeStateIndex + 1).padStart(2, "0")} · ${copy.label}`;
    elements.stateTitle.textContent = copy.title;
    elements.stateDescription.textContent = copy.description;
    elements.stateIntent.textContent = copy.intent;
    elements.stateTrigger.textContent = copy.trigger;
    elements.stateDuration.textContent = t("ui.duration", {
      frames: state.durations.length,
      seconds: (totalDuration(state, true) / 1000).toFixed(2),
      runtimeNote: runtimeNoteFor(state),
    });
    const alt = t("ui.assetAlt", {
      pet: config.pet.name,
      state: copy.title,
    });
    elements.spritePlayer.setAttribute("aria-label", alt);
  }

  function frameThumbnailStyle(state, index) {
    return [
      `background-image:url('${atlasUrlFor(currentVersion())}')`,
      `background-size:${atlasBackgroundSize()}`,
      `background-position:${gridPosition(index, state.row)}`,
    ].join(";");
  }

  function renderFrameStrip() {
    const state = currentState();
    elements.frameStrip.innerHTML = state.durations
      .map(
        (duration, index) => `
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
            type="button"
            aria-label="${escapeHtml(
              t("ui.frameAria", {
                frame: index + 1,
                duration: runtimeDurationLabel(state, index),
              }),
            )}"
          >
            <span class="frame-thumbnail" style="${frameThumbnailStyle(state, index)}"></span>
            <small class="frame-duration">${escapeHtml(
              runtimeDurationLabel(state, index),
            )}</small>
          </button>
        `,
      )
      .join("");

    frameButtons = [...elements.frameStrip.querySelectorAll(".frame-button")];
    frameButtons.forEach((button) => {
      button.addEventListener("click", () => {
        enterFrameInspection();
        setFrame(Number(button.dataset.frameIndex));
      });
    });
  }

  function renderMechanicsBoard() {
    const mechanicsBoards = config.states.map((state) => {
      const configured = config.mechanics.find(
        (board) => board.stateId === state.id,
      );
      return configured || { stateId: state.id, anchors: [] };
    });
    const totalFrames = config.states.reduce(
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
        const state = config.states.find(
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
                  style="${frameThumbnailStyle(state, index)}"
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
          const stateIndex = config.states.findIndex(
            (state) => state.id === card.dataset.stateId,
          );
          stopTour();
          setSection("animation");
          setState(stateIndex);
          enterFrameInspection();
          setFrame(Number(card.dataset.frameIndex));
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
            class="direction-button ${index === activeDirectionIndex ? "is-active" : ""}"
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
    const direction = config.directions[activeDirectionIndex];
    elements.stateTag.textContent = t("ui.lookTag");
    elements.stateTitle.textContent = t("ui.lookTitle", {
      degree: direction.degree,
      direction: directionLabel(direction),
    });
    elements.stateDescription.textContent = t("ui.lookDescription");
    elements.stateIntent.textContent = t("ui.lookIntent");
    elements.stateTrigger.textContent = t("ui.lookTrigger");
    elements.stateDuration.textContent = t("ui.lookDuration");
  }

  function renderControlLabels() {
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
    const modeHelp = t(
      isInspectingFrame
        ? playbackMode === "loop"
          ? "ui.frameInspectionEndlessHelp"
          : "ui.frameInspectionRuntimeHelp"
        : playbackMode === "loop"
          ? "ui.endlessModeHelp"
          : "ui.runtimeModeHelp",
      {
        loops: FIXED_ACTION_LOOPS,
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

  function renderTourStatus() {
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
      const state = config.states[tourState.index] || currentState();
      elements.tourLabel.textContent = t("ui.autoPlayingState", {
        state: stateCopy(state).title,
      });
      elements.tourProgressText.textContent = `${tourState.index + 1} / ${config.states.length}`;
      return;
    }

    if (tourState.completed) {
      elements.tourLabel.textContent = t("ui.allStatesPlayed");
      elements.tourProgressText.textContent = `${config.states.length} / ${config.states.length}`;
      setTourProgress(100);
      return;
    }

    elements.tourLabel.textContent = "";
    elements.tourProgressText.textContent = "";
  }

  function renderFrameReadout() {
    if (sectionMode === "look") {
      const direction = config.directions[activeDirectionIndex];
      elements.frameReadout.textContent = `${direction.degree}° · ${directionLabel(direction)}`;
      return;
    }

    const state = currentState();
    if (isInspectingFrame) {
      elements.frameReadout.textContent = t("ui.frameReadout", {
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
      } else if (state.id === idleState().id) {
        elements.frameReadout.textContent = t("ui.runtimeSlowIdle", {
          frame: activeFrameIndex + 1,
          count: state.durations.length,
        });
      } else {
        elements.frameReadout.textContent = t("ui.runtimeLoopReadout", {
          loop: runtimeLoopsCompleted + 1,
          loops: FIXED_ACTION_LOOPS,
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
      const direction = config.directions[activeDirectionIndex];
      setSpriteFrame(direction.row, direction.column);
      elements.stageModeLabel.textContent = t("ui.finalLookFrame");
      return;
    }

    if (isInspectingFrame) {
      elements.spritePlayer.style.display = "block";
      const state = currentState();
      setSpriteFrame(state.row, activeFrameIndex);
      elements.stageModeLabel.textContent = t("ui.frameInspectionLabel");
      clearFrameTimer();
      return;
    }

    elements.spritePlayer.style.display = "block";
    const playbackState = displayedState();
    setSpriteFrame(playbackState.row, activeFrameIndex);
    elements.stageModeLabel.textContent =
      playbackMode === "loop"
        ? t("ui.endlessLoop")
        : runtimeFellBack
          ? t("ui.runtimeBackToIdle")
          : currentState().id === idleState().id
            ? t("ui.runtimeIdle")
            : t("ui.runtimeAction", {
                loops: FIXED_ACTION_LOOPS,
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
    setSpriteFrame(state.row, activeFrameIndex);
    refreshActiveClasses();
    renderFrameReadout();
  }

  function shouldScheduleFrames() {
    return (
      isPlaying &&
      pageVisible &&
      !isInspectingFrame &&
      sectionMode === "animation"
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
        currentState().id !== idleState().id
      ) {
        runtimeFramesCompleted += 1;
        runtimeLoopsCompleted = Math.floor(
          runtimeFramesCompleted / state.durations.length,
        );
        if (
          runtimeFramesCompleted >=
          state.durations.length * FIXED_ACTION_LOOPS
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
    resetRuntimePlayback();
    activeFrameIndex = 0;
    isInspectingFrame = false;
    isPlaying = true;
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function enterFrameInspection() {
    if (runtimeFellBack) activeFrameIndex = 0;
    resetRuntimePlayback();
    activeFrameIndex = Math.min(
      activeFrameIndex,
      currentState().durations.length - 1,
    );
    isInspectingFrame = true;
    isPlaying = false;
    clearFrameTimer();
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
  }

  function resumeSelectedPlayback() {
    resetRuntimePlayback();
    isInspectingFrame = false;
    isPlaying = true;
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function setPreviewSize(value) {
    const numericValue = Number(value);
    const boundedValue = Number.isFinite(numericValue)
      ? Math.min(
          PREVIEW_SIZE_MAX_PX,
          Math.max(PREVIEW_SIZE_MIN_PX, numericValue),
        )
      : PREVIEW_SIZE_INITIAL_PX;
    previewSizePx = Math.round(boundedValue);
    elements.previewSizeInput.value = String(previewSizePx);
    elements.previewSizeValue.textContent = `${previewSizePx} px`;
    elements.stage.style.setProperty(
      "--preview-width",
      `${previewSizePx}px`,
    );
    elements.stage.style.setProperty(
      "--preview-height",
      `${Math.round((previewSizePx * 208) / 192)}px`,
    );
  }

  function togglePlayback() {
    if (isInspectingFrame) resumeSelectedPlayback();
    else enterFrameInspection();
  }

  function setState(index, options = {}) {
    activeStateIndex =
      ((index % config.states.length) + config.states.length) %
      config.states.length;
    activeFrameIndex = 0;
    resetRuntimePlayback();
    isInspectingFrame = false;
    isPlaying = true;
    renderStateList();
    renderDetails();
    renderControlLabels();
    renderFrameStrip();
    renderPlayer();
    renderFrameReadout();
    scheduleNextFrame();

    if (!options.fromTour) {
      tourState.completed = false;
      setTourProgress(0);
      renderTourStatus();
    }
  }

  function setPlaybackMode(mode) {
    if (!["loop", "runtime"].includes(mode)) return;
    clearFrameTimer();
    playbackMode = mode;
    resetRuntimePlayback();
    activeFrameIndex = 0;
    isInspectingFrame = false;
    isPlaying = true;
    renderControlLabels();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function stepFrame(delta) {
    enterFrameInspection();
    setFrame(activeFrameIndex + delta);
  }

  function setSection(mode) {
    if (tourState.active) stopTour();
    sectionMode = mode;
    const isAnimation = mode === "animation";
    elements.animationTab.classList.toggle("is-active", isAnimation);
    elements.animationTab.setAttribute(
      "aria-selected",
      String(isAnimation),
    );
    elements.lookTab.classList.toggle("is-active", !isAnimation);
    elements.lookTab.setAttribute("aria-selected", String(!isAnimation));
    elements.stateList.style.opacity = isAnimation ? "1" : "0.42";
    elements.stateList.style.pointerEvents = isAnimation ? "auto" : "none";
    elements.animationControls.hidden = !isAnimation;
    elements.lookControls.hidden = isAnimation;
    elements.frameStrip.parentElement.hidden = !isAnimation;
    setLookControlMode(isAnimation ? "manual" : "pointer");

    if (isAnimation) {
      renderDetails();
      renderFrameStrip();
      renderPlayer();
      renderFrameReadout();
      scheduleNextFrame();
    } else {
      clearFrameTimer();
      setDirection(activeDirectionIndex);
    }
  }

  function setDirection(index) {
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

    if (lookControlMode === "orbit") {
      startOrbitTimer();
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
    if (Math.hypot(deltaX, deltaY) < 28) return;

    const degrees =
      (Math.atan2(deltaX, -deltaY) * (180 / Math.PI) + 360) % 360;
    const directionIndex =
      Math.round(degrees / (360 / config.directions.length)) %
      config.directions.length;
    if (directionIndex !== activeDirectionIndex) {
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
      index: completed ? config.states.length - 1 : 0,
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
    if (tourState.index >= config.states.length) {
      stopTour({ completed: true });
      return;
    }

    setState(tourState.index, { fromTour: true });
    restartPlayback();
    const state = config.states[tourState.index];
    const runtimeMultiplier =
      state.id === idleState().id
        ? FIXED_IDLE_SLOWDOWN
        : FIXED_ACTION_LOOPS;
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
        ((tourState.index + withinState) / config.states.length) * 100;
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

    const wasPlaying = isPlaying;
    const wasInspectingFrame = isInspectingFrame;
    clearFrameTimer();
    activeVersionId = nextVersion.id;
    elements.versionSelect.value = activeVersionId;
    isInspectingFrame = wasInspectingFrame;
    isPlaying = wasInspectingFrame ? false : wasPlaying;
    const frameCount = currentState().durations.length;
    activeFrameIndex = Math.min(activeFrameIndex, frameCount - 1);
    renderFrameStrip();
    renderMechanicsBoard();
    renderDetails();
    renderPlayer();
    renderFrameReadout();
    renderControlLabels();
    refreshActiveClasses();
    scheduleNextFrame();
  }

  function setLocale(nextLocale) {
    const supported = supportedLocale(nextLocale);
    if (!supported) return;
    locale = supported;
    storeLocale(locale);
    applyStaticTranslations();
    populateLanguageSelect();
    populateVersionSelect();
    renderStateList();
    if (sectionMode === "look") renderLookDetails();
    else renderDetails();
    renderFrameStrip();
    renderMechanicsBoard();
    renderDirectionList();
    renderControlLabels();
    renderTourStatus();
    renderPlayer();
    renderFrameReadout();
  }

  function attachEvents() {
    elements.animationTab.addEventListener("click", () =>
      setSection("animation"),
    );
    elements.lookTab.addEventListener("click", () => setSection("look"));
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
    elements.nextFrameButton.addEventListener("click", () => stepFrame(1));
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
      if (event.target.matches("select, button, input, textarea")) return;
      if (
        sectionMode === "look" &&
        [" ", "ArrowLeft", "ArrowRight"].includes(event.key)
      ) {
        return;
      }
      if (event.key === " ") {
        event.preventDefault();
        togglePlayback();
      } else if (event.key === "ArrowLeft") {
        stepFrame(-1);
      } else if (event.key === "ArrowRight") {
        stepFrame(1);
      } else if (/^[1-9]$/.test(event.key)) {
        const stateIndex = Number(event.key) - 1;
        if (stateIndex < config.states.length) {
          setSection("animation");
          setState(stateIndex);
        }
      }
    });
    document.addEventListener("visibilitychange", handleVisibilityChange);

  }

  function initialVersionId() {
    const defaultVersion = config.versions.find(
      (version) => version.isDefault,
    );
    return (defaultVersion || config.versions[0]).id;
  }

  async function boot() {
    const loaded = await loadConfig();
    configBaseUrl = loaded.baseUrl;
    config = normalizeConfig(loaded.data, loaded.isExternal);
    activeVersionId = initialVersionId();

    applyStaticTranslations();
    populateLanguageSelect();
    populateVersionSelect();
    renderStateList();
    renderDirectionList();
    renderFrameStrip();
    renderMechanicsBoard();
    renderControlLabels();
    renderTourStatus();
    attachEvents();
    setBackground(activeBackground);
    setPreviewSize(previewSizePx);
    setState(0);
    setSection("animation");
  }

  boot();
})();
