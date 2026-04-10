# Portrait Dialogue First-Batch Skeleton

## Purpose

This document defines the first executable implementation batch for the portrait
dialogue runtime inside `topiclab-backend`.

The goal of this batch is deliberately narrow:

- create the first durable dialogue-session runtime under `app/portrait/`
- keep the external API surface small and explicit
- validate that transcript persistence and derived state can already work
  without frontend migration
- add a model-backed assistant-reply path on top of the durable transcript flow
- avoid pretending that the heavier legacy portrait-builder flow has already
  been fully migrated

This is the second concrete portrait-domain code batch after `scales`.

## Status

Implemented and locally validated.

This batch introduces a durable dialogue runtime inside `app/portrait`, plus a
compatibility router at the old top-level backend path.

It now also includes a shared AI-generation caller with multi-key rotation and
has been validated against the public AutoDL staging URL.

## Scope

### Included in this batch

- portrait-domain dialogue router
- durable dialogue session persistence
- durable transcript-message persistence
- durable derived-state persistence
- first dialogue service orchestration skeleton
- model-backed assistant reply generation path
- focused API tests
- standalone in-process smoke script

### Explicitly excluded from this batch

- old `Resonnet` `/profile-helper/chat` replacement
- block-chat migration
- prompt handoff
- pasted-result import
- portrait export/download
- `TopicLab-CLI` command surface for dialogue
- frontend migration

## Design Rule

This batch is a **first executable runtime batch**, not a full
portrait-generator migration.

That means:

- the new backend now owns durable dialogue sessions and transcripts
- user messages can trigger backend assistant generation through the existing
  `AI_GENERATION_*` model configuration
- but it does **not** yet claim to reproduce the full legacy portrait builder
- the main value of this batch is to establish clean ownership and durable
  persistence for later dialogue/generation work

## Target Internal Shape

After this batch, the dialogue skeleton lives in:

```text
topiclab-backend/app/
  portrait/
    api/
      dialogue.py
    services/
      dialogue_service.py
      dialogue_runtime_service.py
      dialogue_summary_service.py
    storage/
      dialogue_repository.py
    schemas/
      dialogue.py
```

Compatibility surface:

- `app/api/dialogue.py`

## What This Skeleton Actually Does

Implemented runtime behaviors:

- create a dialogue session
- read current dialogue-session status
- append transcript messages
- when a user message is appended, optionally generate a backend assistant reply
- read the full transcript
- read a derived state object built from the transcript
- close a session and prevent further writes

Shared generation caller behavior:

- `app/services/ai_generation_client.py` now owns the portrait-side
  OpenAI-compatible generation transport
- `AI_GENERATION_API_KEY` remains the single-key compatibility fallback
- `AI_GENERATION_API_KEYS` adds comma-separated round-robin rotation
- HTTP 429 marks the current key into temporary cooldown and retries with the
  next key

Persisted tables:

- `portrait_dialogue_sessions`
- `portrait_dialogue_messages`
- `portrait_dialogue_states`

What the derived state currently includes:

- session status
- message counts
- last message metadata
- a lightweight summary of early and latest transcript points

## Why This Batch Exists Before Real Generation

The legacy portrait flow currently mixes together:

- in-memory working session state
- filesystem artifacts
- transcript handling
- portrait parsing
- downstream exports

That makes it too large to migrate in one jump.

This batch isolates the part that should clearly become server-owned first:

- dialogue session lifecycle
- transcript durability
- derived intermediate state

That gives later generation work a stable substrate instead of forcing future
work to depend on legacy file caches.

## Validation Plan

This batch is only done if all of the following hold:

1. the new portrait-domain files compile
2. the focused dialogue API tests pass
3. the scales tests still pass after dialogue DDL/router changes
4. a standalone smoke can create a dialogue session, write messages, read
   transcript, read derived state, and close the session

## Validation Result

The following commands were run:

```bash
python3 -m py_compile \
  topiclab-backend/main.py \
  topiclab-backend/app/api/dialogue.py \
  topiclab-backend/app/portrait/api/dialogue.py \
  topiclab-backend/app/portrait/schemas/dialogue.py \
  topiclab-backend/app/portrait/services/dialogue_service.py \
  topiclab-backend/app/portrait/services/dialogue_runtime_service.py \
  topiclab-backend/app/portrait/services/dialogue_summary_service.py \
  topiclab-backend/app/portrait/storage/dialogue_repository.py \
  topiclab-backend/app/storage/database/postgres_client.py \
  topiclab-backend/tests/test_dialogue_runtime_api.py \
  scripts/dialogue_runtime_smoke.py

python3 -m pytest -q topiclab-backend/tests/test_dialogue_runtime_api.py
python3 -m pytest -q topiclab-backend/tests/test_scales_runtime_api.py
python3 scripts/dialogue_runtime_smoke.py
```

Observed result:

- syntax compilation passed
- focused dialogue API tests passed
- existing scales API tests still passed
- standalone dialogue smoke completed successfully

## Real Constraint Discovered

This batch proves durable dialogue state plus the first model-backed assistant
generation hook, not the whole portrait-generator migration.

So even after this batch, the following are still intentionally missing:

- portrait draft materialization
- prompt export/import
- portrait artifact generation

Those should be layered on top of this runtime skeleton instead of being
smuggled back into process-local state.

## Additional Validation Note

The local focused tests and the standalone smoke validate orchestration using a
deterministic generation stub, not a live remote model call.

That is intentional for repeatable local verification.

The real runtime path now uses the existing backend-wide:

- `AI_GENERATION_BASE_URL`
- `AI_GENERATION_API_KEY`
- `AI_GENERATION_API_KEYS` (optional multi-key rotation, comma-separated)
- `AI_GENERATION_MODEL`

The dialogue runtime now prefers the shared `topiclab-backend` AI-generation
client, which supports:

- single-key compatibility through `AI_GENERATION_API_KEY`
- multi-key round-robin rotation through `AI_GENERATION_API_KEYS`
- 429 cooldown-based temporary key eviction

This keeps the dialogue slice aligned with the older proven `Resonnet`
rotation strategy while moving the ownership into `topiclab-backend`.

If those are missing at runtime, the current behavior is:

- the user message is still durably persisted
- the API returns `generation_status = failed`
- the response includes:
  - `generation_error.code = dialogue_generation_failed`

This behavior was explicitly validated so missing AI config does not destroy the
dialogue session state.

## Live Validation Notes Added After Local And Staging Runs

### 1. The provided `sk-...` DashScope keys did not work with `coding.dashscope.aliyuncs.com/v1`

Observed result:

- `401 invalid_api_key`

The same keys worked correctly with:

- `https://dashscope.aliyuncs.com/compatible-mode/v1`

Confirmed working local/staging combination:

- `AI_GENERATION_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `AI_GENERATION_MODEL=qwen3.5-plus`

### 2. Public AutoDL dialogue validation required a real `DATABASE_URL`

When the staging service ran without `DATABASE_URL`, public dialogue session
creation failed with:

- `ValueError("DATABASE_URL is not set")`

This was treated as expected architecture behavior, not something to patch away
with in-memory fallback.

For staging, the service was reconfigured to use a durable local SQLite file:

- `sqlite:////root/topiclab-portrait-staging/topiclab-backend/topiclab_staging.sqlite3`

### 3. Public staging registration used a staging-only SMS bypass

To validate the public dialogue flow without using the real SMS chain, AutoDL
staging was restarted with:

- `REGISTER_SKIP_SMS_UNTIL=2099-01-01T00:00:00+08:00`

This is only a staging/test convenience and should not be copied into the
production rollout path.

### 4. Public AutoDL dialogue closure is now proven

Validated public flow:

1. `GET /health`
2. `POST /auth/register`
3. `POST /api/v1/portrait/dialogue/sessions`
4. `POST /api/v1/portrait/dialogue/sessions/{id}/messages`
5. `GET /messages`
6. `GET /derived-state`
7. `POST /close`

Observed behavior:

- user message persisted
- assistant reply generated through live DashScope
- transcript round-trip succeeded
- derived state round-trip succeeded
- close succeeded
