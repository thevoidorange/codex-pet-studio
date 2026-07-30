# Review workbench protocol

Use this reference for Previewer Candidate, state, Keyframe, Take, URL, and
single-frame revision work.

The current Take registration and fixed-frame inspection path is the
`codex-pet-v2` review adapter. Future targets require their own validated frame
geometry and review mapping before this workflow can write target-specific
Takes.

## Contents

- Product boundary
- Review vocabulary
- URL contract
- Safe local mapping
- Frame indexing
- Additive Take creation
- Continuity and authority
- Review handoff

## Product boundary

The Previewer is a read-only co-design review surface. The Codex conversation
creates assets and changes project files.

Do not add:

- an embedded agent prompt or “Request New Take” field;
- upload, draw, replace, save, or source-write controls;
- install, package, publish, promote, or QA actions.

Previewer controls may change local review state only.

## Review vocabulary

- A **Candidate** is a coherent proposal. The implementation may retain a
  legacy `versions` collection, but user-facing and decision language uses
  Candidate.
- A **Keyframe** is a fixed state slot.
- A **Take** is an additive option for one exact Keyframe.
- Clicking a Take auditions it.
- Confirming a Take records session-only review metadata and collapses the
  rail. It is not approval or writeback.
- Conversational approval records an authoritative visual decision in the
  private project artifacts.

## URL contract

The deliberate review focus uses:

```text
?config=<config-url>&candidate=<id>&state=<id>&frame=<one-based>&take=<id|original>
```

Rules:

- Preserve unrelated query parameters, including `config`.
- Validate Candidate, state, frame, and Take against the successfully loaded
  config before restoring focus.
- Treat `take=original` as the source atlas frame.
- Treat a valid Take ID as the current visual reference, not approval.
- Keep the URL stable during runtime frame ticks, Auto Orbit, pointer movement,
  all-state playback, language changes, and compatible Candidate switches.
- Clear animation `frame` and `take` when entering gaze-direction review.
- If `frame` and `take` are absent, do not infer a prior animation frame.
- If an explicit external config cannot load, invalidate the whole handoff.
  Never resolve colliding IDs against the bundled example.

## Map URL context to a local project safely

Before editing:

1. Identify the active Previewer server root and current repository root.
2. Resolve the `config` URL to its canonical local path.
3. Require the real path to remain under the current project root.
4. Reject remote origins, path traversal, symlink escape, fallback data, and
   config files that cannot be mapped to an editable local file.
5. Ask one concise path/project question only when safe resolution is
   impossible.

Never derive a writable path from Candidate, state, frame, or Take IDs.

## One-based and zero-based frames

The URL is human-facing and one-based:

```text
frame=2
```

Previewer config is data-facing and zero-based:

```json
{
  "stateId": "idle",
  "frameIndex": 1
}
```

Always convert:

```text
config.frameIndex = URL frame - 1
URL frame = config.frameIndex + 1
```

Reject zero, negative, non-integer, or out-of-range URL frames.

## Create an additive Take

1. Resolve the exact Candidate, state, Keyframe, and selected source.
2. Extract or load only that one `192×208` source frame.
3. Read identity locks and the user's requested delta.
4. Generate one standalone `192×208` transparent asset under the private
   `design/takes/<candidate>/<state>/fNN/` working directory.
5. Keep source atlas, existing Takes, neighboring frames, and unrelated config
   semantically unchanged.
6. Register the Take through the deterministic CLI:

```bash
python3 .agents/skills/pet-studio/scripts/studio.py take add --help
```

The command owns:

- non-colliding Take ID validation;
- URL-frame to `frameIndex` conversion;
- safe asset placement and relative URL creation;
- Candidate/state/frame validation;
- atomic config update;
- output of a focused review URL.

The CLI copies the review asset into generated `build/takes/` staging. The
private working source remains under `design/`; neither location is part of a
public export unless a separate allowlist explicitly includes it.

Do not hand-edit a Take registration when the command is available.

## Continuity and authority

Use neighboring frames as read-only evidence. If the requested Take creates a
continuity concern, create another Take for the requested Keyframe. Do not
silently revise either neighbor.

Previewer Confirm remains temporary. When the user explicitly approves a Take
in conversation:

- record Candidate, state, Keyframe, Take ID, exact asset path, and locked
  details in the active private decision artifact;
- keep the asset available as production grounding;
- do not promote the Candidate until full state and motion QA passes.

## Review handoff

After adding a Take:

1. validate the config and asset;
2. load the returned URL;
3. confirm it restores the intended Candidate, state, Keyframe, and auditioned
   Take;
4. confirm no approval or install state changed;
5. return the focused URL and one sentence describing only the requested
   visual delta.
