# Portrait Scales First-Batch Migration

## Purpose

This document defines the first migration batch for the portrait domain inside
`topiclab-backend`.

The goal of this batch is deliberately narrow:

- migrate the **internal ownership** of the new scale runtime toward
  `app/portrait/`
- keep the **external API surface unchanged**
- keep current tests and standalone smoke behavior working
- avoid touching unrelated TopicLab functionality

This is the first concrete implementation step after creating the portrait
bounded-domain package.

## Status

Implemented and validated.

The first batch now exists in code, with internal ownership migrated into
`app/portrait/` and the old top-level files preserved as compatibility shims.

## Scope

### Included in this batch

- scale definition loading
- scale repository and DB read/write helpers
- scale service orchestration
- canonical scale scoring
- portrait-domain API module for scales
- compatibility wrappers at the old import paths

### Explicitly excluded from this batch

- `Resonnet` profile-helper chat flows
- `Resonnet` block chat flows
- prompt handoff
- external-AI pasted-result ingestion
- `TopicLab-CLI` integration
- frontend migration
- account/twin runtime refactor

## Design Rule

This batch is an **ownership migration**, not a product-surface change.

That means:

- callers should keep using the current `/api/v1/scales/...` endpoints
- tests should keep importing the same active router surface
- the migration should mostly be invisible outside the backend code layout

## Target Internal Shape

After this batch, the desired shape is:

```text
topiclab-backend/app/
  portrait/
    api/
      scales.py
    services/
      scales_service.py
      scales_scoring.py
    storage/
      scales_repository.py
    runtime/
      definitions_loader.py
```

Old locations remain as compatibility shims:

- `app/api/scales.py`
- `app/services/scales_service.py`
- `app/services/scales_scoring.py`

## Why This Batch First

Scales are the cleanest portrait slice to migrate first because they are:

- already structured
- already sessionized
- already fixture-testable
- already the first CLI-friendly runtime slice

This makes them the lowest-risk place to establish the new domain ownership
pattern.

## File-Level Plan

### 1. `app/portrait/runtime/definitions_loader.py`

Responsibilities:

- load `registry.json`
- load per-scale definition files
- keep the current `scales-runtime/definitions/` directory as the domain asset
  source

### 2. `app/portrait/storage/scales_repository.py`

Responsibilities:

- read/write `scale_sessions`
- read/write `scale_session_answers`
- read/write `scale_results`
- keep SQL isolated from service orchestration logic

### 3. `app/portrait/services/scales_scoring.py`

Responsibilities:

- canonical dimension scoring
- derived score calculation
- result summary construction

### 4. `app/portrait/services/scales_service.py`

Responsibilities:

- session lifecycle
- answer validation
- finalize orchestration
- result retrieval

### 5. `app/portrait/api/scales.py`

Responsibilities:

- router definition
- request models
- auth wiring
- response passthrough to the portrait-domain service

### 6. Compatibility wrappers

Old active file paths should remain, but become thin wrappers that import from
the new portrait-domain location.

This keeps:

- route registration stable
- tests stable
- deployment diff smaller

## Validation Plan

This batch is only done if all of the following hold:

1. `topiclab-backend/tests/test_scales_runtime_api.py` still passes
2. the standalone smoke flow still works
3. `/api/v1/scales/...` route behavior is unchanged
4. old import paths still resolve

## Validation Result

All four conditions above were verified.

Commands run:

```bash
python3 -m py_compile \
  topiclab-backend/app/api/scales.py \
  topiclab-backend/app/services/scales_service.py \
  topiclab-backend/app/services/scales_scoring.py \
  topiclab-backend/app/portrait/api/scales.py \
  topiclab-backend/app/portrait/services/scales_service.py \
  topiclab-backend/app/portrait/services/scales_scoring.py \
  topiclab-backend/app/portrait/storage/scales_repository.py \
  topiclab-backend/app/portrait/runtime/definitions_loader.py \
  topiclab-backend/app/portrait/schemas/scales.py

python3 -m pytest -q topiclab-backend/tests/test_scales_runtime_api.py

python3 scripts/scales_runtime_smoke.py
```

Observed result:

- syntax compilation passed
- API tests passed: `5 passed`
- standalone smoke completed successfully
- RCSS smoke result still returned:
  - `CSI = 24.0`
  - `type = 强整合型`

## Remote Staging Validation

This first batch was also validated on a separate non-production staging host.

What was actually validated there:

- minimal portrait-scale slice synced to the host
- backend dependencies installed with the host's existing Miniconda Python
- focused API tests run remotely
- `scripts/scales_runtime_smoke.py` run remotely
- `topiclab-backend/main.py` imported remotely with a staging SQLite database
- a dedicated `uvicorn` process started on `127.0.0.1:18000`
- a real authenticated HTTP loop completed against the running service

That remote HTTP loop covered:

- `/health`
- `/auth/register-config`
- `/auth/register`
- `/auth/login`
- `/auth/me`
- `/api/v1/scales`
- `/api/v1/scales/rcss`
- `/api/v1/scales/sessions`
- `/api/v1/scales/sessions/{id}/answer-batch`
- `/api/v1/scales/sessions/{id}/finalize`
- `/api/v1/scales/sessions/{id}/result`

Remote observed result:

- route-level staging smoke succeeded
- authenticated scale session reached `completed`
- RCSS remote HTTP result still returned:
  - `CSI = 24.0`
  - `type = 强整合型`

The reusable project script added for this path is:

- `/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scripts/scales_runtime_http_smoke.py`

Real pitfall discovered during remote validation:

- the first HTTP smoke attempt used the wrong RCSS answer keys
- the canonical RCSS definition uses `A1` ... `A4` and `B1` ... `B4`
- after fixing that mismatch, the remote HTTP loop passed

## Actual Implemented Shape

The first batch now uses this internal structure:

```text
topiclab-backend/app/
  portrait/
    api/
      scales.py
    services/
      scales_service.py
      scales_scoring.py
    storage/
      scales_repository.py
    runtime/
      definitions_loader.py
    schemas/
      scales.py
```

And keeps these old paths as thin shims:

- `app/api/scales.py`
- `app/services/scales_service.py`
- `app/services/scales_scoring.py`

## Compatibility Caveats

This first batch improves the dedicated scale runtime substantially, but it is
not yet a perfect 1:1 semantic replacement for every behavior of the legacy
`Resonnet` profile-helper scale flow.

Important differences discovered during comparison:

- the legacy path stored scales inside the broader portrait-builder session and
  wrote a per-user `scales.json` cache
- the legacy path accepted a final client-computed payload:
  - `answers`
  - `scores`
  - `result_summary`
- the new runtime owns scale sessions separately and computes canonical results
  server-side
- the new runtime currently assumes a real authenticated TopicLab user because
  `scale_sessions.user_id` is required
- historical `scales.json` data is not automatically backfilled into the new
  `scale_results` tables yet

So the correct claim for this batch is:

- for the dedicated authenticated scale-runtime use case, the new module is
  stronger and cleaner than the legacy one
- for full legacy profile-helper semantics, compatibility work is still needed

## What Is Better Now

Compared with the legacy `Resonnet` scale submodule, the new runtime adds:

- explicit session lifecycle instead of implicit scale blobs inside a larger
  portrait session
- per-question persistence via `scale_session_answers`
- canonical server-side scoring
- explicit result objects via `scale_results`
- definition versioning and scoring versioning
- resumable progress and session status inspection
- a cleaner path for future CLI and agent interaction

## Non-Goals

This batch does **not** try to solve the whole portrait-backend migration.

It only establishes the first real executable slice under the new portrait
domain package.
