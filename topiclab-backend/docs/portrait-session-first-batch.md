# Portrait Session First Batch

## Purpose

This document records the first executable batch of the unified portrait
session orchestrator, plus the first routing expansion that turned it from a
paper protocol into a real cross-slice backend path.

The goal here is still **not** to claim the whole portrait protocol is
finished. The goal is narrower and factual:

- prove a durable top-level portrait session exists
- prove one agent-facing `start / status / respond / result` loop can execute
  above the already-implemented slice runtimes
- then prove that the same top-level loop can route into:
  - `dialogue`
  - `scales`
  - `prompt_handoff`
  - `import_result`
  - `portrait_state`

## Scope

This executable batch introduces one new top-level orchestration slice under
`topiclab-backend/app/portrait/`.

Implemented files:

- `app/portrait/api/session.py`
- `app/api/portrait_session.py`
- `app/portrait/services/portrait_session_service.py`
- `app/portrait/services/portrait_orchestration_service.py`
- `app/portrait/services/portrait_skill_policy_service.py`
- `app/portrait/storage/portrait_session_repository.py`
- `app/portrait/schemas/session.py`
- `app/portrait/runtime/block_protocol.py`
- `app/portrait/runtime/ai_memory_prompt_loader.py`

Updated integration points:

- `app/storage/database/postgres_client.py`
- `main.py`
- `app/portrait/services/import_result_service.py`
- `app/portrait/services/portrait_state_service.py`

Validation assets:

- `tests/test_portrait_session_api.py`
- `scripts/portrait_session_runtime_smoke.py`

## Implemented Routes

This batch adds:

- `POST /api/v1/portrait/sessions`
- `GET /api/v1/portrait/sessions`
- `GET /api/v1/portrait/sessions/{session_id}`
- `GET /api/v1/portrait/sessions/{session_id}/history`
- `POST /api/v1/portrait/sessions/{session_id}/respond`
- `POST /api/v1/portrait/sessions/{session_id}/reset`
- `GET /api/v1/portrait/sessions/{session_id}/result`

These are the first executable backend routes aligned with the unified
portrait-session protocol discussed in:

- `../../scales-runtime/docs/unified-portrait-session-protocol.md`

## Durable Tables

This batch adds three top-level orchestration tables:

- `portrait_sessions`
- `portrait_session_runtime_refs`
- `portrait_session_events`

Responsibilities:

- `portrait_sessions`
  - owns the top-level user-facing session identity and current step
- `portrait_session_runtime_refs`
  - links the top-level session to lower slice runtime objects such as
    `dialogue_session`, `scale_session`, `prompt_handoff`, `import_result`,
    and `portrait_state`
- `portrait_session_events`
  - records step-level orchestration events

## Executable Behavior In This Batch

### `start`

`POST /api/v1/portrait/sessions` creates a durable top-level session row and
returns a normalized first step.

Current first step:

- `stage = dialogue`
- `input_kind = text`
- the message asks the caller to introduce its research direction, work style,
  and long-term goals

### `respond`

The executable unified session layer now supports these input families:

- `choice`
- `text`
- `external_text`
- `external_json`
- `confirm`

Unsupported input families return a machine-readable `400`:

```json
{
  "code": "unsupported_portrait_session_input",
  "supported": ["choice", "text", "external_text", "external_json", "confirm"]
}
```

Unsupported `choice` values at the wrong stage return a more specific `400`:

```json
{
  "code": "unsupported_portrait_session_choice",
  "choice": "3"
}
```

If a scale-question step receives a non-numeric `choice`, the service returns:

```json
{
  "code": "invalid_scale_choice_value",
  "choice": "abc",
  "expected": "numeric"
}
```

### `respond(text)`

The current routed text path is:

1. create or reuse a linked `dialogue_session`
2. append the user message into the existing dialogue runtime
3. let the dialogue runtime generate an assistant reply
4. explicitly materialize a `portrait_state` update from that
   `dialogue_session`
5. update the top-level portrait session with:
   - latest step
   - runtime refs
   - result preview
   - orchestration events

### `respond(choice)`

The unified session layer now supports three routed choice families:

- `continue_dialogue`
  - returns to the dialogue-style follow-up step
- `scale:<scale_id>`
  - creates and links a `scale_session`
  - routes numeric follow-up answers into the `scales` runtime
  - finalizes the scale when complete
  - explicitly materializes a `portrait_state` update from that finalized scale
- `prompt_handoff`
  - creates and links a `prompt_handoff`
  - switches the top-level session into `import_result`
  - returns the generated prompt artifact in the normalized payload

### `respond(external_text)` / `respond(external_json)`

When the current stage is `import_result`, the unified session layer can now:

1. create an `import_result`
2. parse it
3. auto-apply the parsed result into canonical `portrait_state`
4. link both `import_result` and `portrait_state` back to the top-level
   session
5. return to a dialogue-style follow-up step

This is the first executable end-to-end path that proves external AI output can
re-enter the new portrait runtime without routing through legacy frontend-only
glue.

### `respond(confirm)`

The current completion path is:

1. close the linked `dialogue_session` if one exists
2. mark the top-level portrait session as `completed`
3. return a normalized final step pointing callers to `result`

### `result`

`GET /api/v1/portrait/sessions/{session_id}/result` currently returns:

- current linked `portrait_state`
- top-level `result_preview`
- linked runtime refs

This is still intentionally simple at this stage.

## First legacy-kernel parity landed on top of the session layer

After the full reread of the legacy portrait product, this batch was extended
with the first executable compatibility bridge:

- `start(mode=legacy_product)`

This mode now proves the new session orchestrator can carry old-product
semantics rather than only slice-to-slice runtime routing.

### What `legacy_product` now actually does

1. `start(mode=legacy_product)`
   - returns privacy / welcome text
   - returns one choice block asking whether to:
     - start from AI memory
     - or start direct collection
2. `respond(choice="direct")`
   - enters the `collect-basic-info` sequence
   - one interactive question per turn
   - the currently recovered direct path now covers:
     - research stage
     - primary / secondary / cross-discipline field statement
     - method paradigm
     - institution
     - advisor / team
     - academic network
     - six process-ability ratings plus one note per dimension
     - technical tool stack
     - representative outputs
     - current time occupation
     - time feeling
     - pain points
     - desired support
     - desired change
3. `respond(choice="ai_memory")`
   - creates a prompt handoff with `prompt_kind=ai_memory`
   - returns a copyable AI-memory prompt block
   - waits for the pasted AI reply
4. pasted AI-memory reply
   - creates an `import_result`
   - parses the imported A/C answers deterministically
   - materializes the extracted fields into canonical `portrait_state`
   - resumes direct collection from the first still-missing core field
5. when the direct path becomes complete
   - the new backend now immediately runs deterministic
     `infer-profile-dimensions`
   - writes the inferred patch into canonical `portrait_state`
   - switches into a `review-profile` step instead of leaving the caller on a
     raw collection checkpoint
6. review/update/history parity now has a first executable pass
   - `review_summary` returns:
     - text summary
     - profile chart block
     - actions / update choices
   - targeted update paths now exist for:
     - basic identity
     - technical capability
     - process ability
     - current needs
   - `GET /history` now exposes:
     - top-level session row
     - runtime refs
     - recent orchestration events
     - portrait-state versions
     - portrait observations

### New response-contract fields

Top-level session responses now also expose:

- `blocks`
- `interactive_block`
- `policy`

This is the first backend-owned block contract parity with the old
`block_agent` flow, but hosted inside the new durable portrait-session
runtime.

### What still remains outside this first parity batch

This first parity bridge still does **not** recover the full old product:

- forum profile generation
- scientist matching / field recommendations
- PDF / image export
- publish-to-library side effects
- old-grade append-only conversation and execution logging
- richer legacy review flows beyond the current targeted-update first pass

### `list`

`GET /api/v1/portrait/sessions` now returns recent top-level portrait sessions
for the authenticated user plus `current_active_session_id`.

This is the first backend-owned path that supports a higher-level `history`
surface without forcing callers to read lower-level slice tables directly.

### `reset`

`POST /api/v1/portrait/sessions/{session_id}/reset` now provides a first
server-owned reset behavior for the unified session layer.

The current reset path:

1. closes the linked `dialogue_session` if one exists
2. abandons the linked `scale_session` if one exists
3. marks the top-level portrait session as `reset`
4. records a reset event in `portrait_session_events`
5. returns the final top-level session plus linked runtime refs

This gives the user-facing CLI a stable reset primitive without having to
reconstruct per-slice cleanup logic locally.

## What This Batch Proves

The current executable unified portrait session layer now proves:

- top-level portrait sessions can be durable and server-owned
- one normalized `start / status / respond / result` loop already exists
- the unified layer can route into:
  - `dialogue`
  - `portrait_state`
  - `scales`
  - `prompt_handoff`
  - `import_result`
- the unified layer can keep runtime refs instead of forcing callers to track
  lower-level slice IDs manually

## What This Batch Does Not Yet Prove

This batch does **not** yet prove:

- richer resume/recovery semantics beyond the current first pass
- a smaller final input-kind vocabulary than the current executable batch
  (`text_or_choice`, `external_text_or_json`)
- a full product-ready `TopicLab-CLI` rollout for the main entry across
  staging/prod environments

Those remain follow-up work.

## Validation Completed

The following validations were actually run for this batch.

### Syntax / import validation

```bash
python3 -m py_compile \
  topiclab-backend/app/portrait/services/portrait_session_service.py \
  topiclab-backend/app/portrait/services/portrait_state_service.py \
  topiclab-backend/app/portrait/services/import_result_service.py \
  topiclab-backend/app/portrait/services/portrait_orchestration_service.py \
  scripts/portrait_session_runtime_smoke.py
```

### Focused backend tests

```bash
cd topiclab-backend
python3 -m pytest -q \
  tests/test_portrait_session_api.py \
  tests/test_prompt_import_runtime_api.py \
  tests/test_portrait_state_api.py \
  tests/test_dialogue_runtime_api.py \
  tests/test_scales_runtime_api.py
```

Observed result:

- `7 passed` for `tests/test_portrait_session_api.py`
- `14 passed` for the existing regression suites
- `21 passed` total across the focused portrait-session and slice-regression
  suites

### Standalone smoke

```bash
cd ..
python3 scripts/portrait_session_runtime_smoke.py
```

Observed smoke facts:

- `start_stage = dialogue`
- `scale_stage_after_start = scale_question`
- `stage_after_scale_finalize = dialogue`
- `stage_after_import = dialogue`
- `final_status = completed`
- runtime refs included:
  - `dialogue_session`
  - `portrait_state`
- the current canonical state already contained:
  - `dialogue`
  - `scales`
  - `imports`
  - `external_import`

### Real pitfall encountered during this parity pass

While extending the legacy-compatible `collect-basic-info -> infer -> review`
path, SQLite test runs hit a real `database is locked` failure.

The cause was:

- outer `get_db_session()` blocks still holding a write transaction
- while `_finalize_legacy_basic_info(...)` triggered a nested
  `portrait_state_service.apply_update(...)`
  that opened its own database session

The fix that was actually applied:

- explicitly commit the outer transaction at the handful of legacy parity
  branch points that immediately hand off into `_finalize_legacy_basic_info`
- then let the inference / portrait-state materialization path open its own
  write session safely

This pitfall matters because future legacy-product parity work is likely to
revisit the same "outer orchestration write + inner state materialization"
pattern.

### Public AutoDL no-SSH validation

The unified session main entry was also validated through the AutoDL custom
service HTTPS URL via the local `TopicLab-CLI`, without SSH tunneling.

Validated public command path:

```bash
topiclab portrait auth ensure --base-url <AutoDL HTTPS URL> ...
topiclab portrait start --json
topiclab portrait respond <session_id> --text ...
topiclab portrait respond <session_id> --choice scale:rcss
topiclab portrait respond <session_id> --choice 7
topiclab portrait respond <session_id> --choice prompt_handoff
topiclab portrait respond <session_id> --external-text ...
topiclab portrait status <session_id> --json
topiclab portrait result <session_id> --json
topiclab portrait resume --json
topiclab portrait history --versions --json
topiclab portrait export --format markdown --output /tmp/portrait-result.md --json
topiclab portrait reset --restart --json
```

Observed public facts:

- `start_stage = dialogue`
- `stage_after_text = dialogue`
- `generation_status = completed`
- `stage_after_scale = dialogue`
- `stage_after_prompt = import_result`
- `stage_after_import = dialogue`
- `resume` returned the remembered current portrait session
- `history` returned recent top-level portrait sessions plus portrait-state
  versions
- `export` successfully wrote a local Markdown portrait artifact
- `reset --restart` successfully returned a reset top-level session and a fresh
  restarted session
- the final `current_state.state_json` already contained:
  - `dialogue`
  - `scales`
  - `imports`
  - `external_import`

### AutoDL staging startup is now script-owned

After the legacy-kernel public validation exposed the fragility of manual
`nohup` restarts, the staging service path was hardened into a repo-owned
script:

- `topiclab-backend/scripts/portrait_staging_service.sh`

Validated on the AutoDL host:

- `status` detects both managed and unmanaged listeners on `127.0.0.1:6006`
- `restart` can take over an older unmanaged `nohup` process and replace it
  with a managed pid-file-backed process
- `health` returns the normal FastAPI health payload after restart
- `logs` tails the validated backend log file at:
  - `/root/topiclab-portrait-staging/logs/topiclab_backend_6006.log`

The concrete verified restart path used:

```bash
cd /root/topiclab-portrait-staging/topiclab-backend
TOPICLAB_PYTHON_BIN=/root/miniconda3/bin/python \
  bash scripts/portrait_staging_service.sh restart
TOPICLAB_PYTHON_BIN=/root/miniconda3/bin/python \
  bash scripts/portrait_staging_service.sh health
```

Observed facts after takeover:

- old unmanaged listener pid:
  - `25934`
- new managed listener pid:
  - `26859`
- health payload:
  - `{"status":"ok","service":"topiclab-backend"}`

### AutoDL staging restart path was hardened again on April 11

The next real staging validation exposed two additional operational pitfalls:

- the script defaulted to system `python3`, but the actually provisioned
  runtime with `uvicorn`, `fastapi`, and `sqlalchemy` lived at:
  - `/root/miniconda3/bin/python`
- the host had `/usr/bin/chromium-browser`, but on this AutoDL image it was a
  snap wrapper rather than a usable headless browser binary

What changed in repo-owned runtime code:

- `topiclab-backend/scripts/portrait_staging_service.sh`
  - now auto-detects a Python interpreter that can actually import `uvicorn`
  - currently resolves to `/root/miniconda3/bin/python` on the validated
    AutoDL host without needing a manual env override
- `app/portrait/services/portrait_export_service.py`
  - now prefers real Chrome binaries before `chromium-browser`, so the staging
    host selects `/usr/bin/google-chrome-stable` once installed

What was installed on the AutoDL host during validation:

- `google-chrome-stable`

Concrete verified path after those fixes:

```bash
cd /root/topiclab-portrait-staging/topiclab-backend
bash scripts/portrait_staging_service.sh restart
bash scripts/portrait_staging_service.sh health
```

Observed facts after the April 11 validation:

- managed listener pid after restart:
  - `31691`
- health payload:
  - `{"status":"ok","service":"topiclab-backend"}`
- real cloud requests returned `200 OK` for:
  - `GET /api/v1/portrait/export/profile-pdf`
  - `GET /api/v1/portrait/export/profile-image`
  - `GET /api/v1/portrait/artifacts`
  - `GET /api/v1/portrait/artifacts/{artifact_id}/download`
- persisted binary artifacts were written to:
  - `/root/topiclab-portrait-staging/topiclab-backend/storage/portrait_artifacts/user-7/`
- matching sqlite rows existed in:
  - `/root/topiclab-portrait-staging/topiclab-backend/topiclab_staging.sqlite3`
  - table: `portrait_artifacts`

Validated artifact examples:

- PDF:
  - `par_ce0b7f58fcbb46f2`
  - size: `46623`
- image:
  - `par_76710431128e413c`
  - size: `77298`

## Practical Interpretation

This work means the unified portrait session orchestrator has now moved from:

- target protocol design only

to:

- first executable backend slice with cross-slice routing

It also means the first user-facing session-control layer can now be built on
top of durable backend routes rather than local CLI-only heuristics:

- `resume`
- `history`
- `reset`
- `export`

It is still incomplete, but it is no longer hypothetical.
