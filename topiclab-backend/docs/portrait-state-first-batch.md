# Portrait State First-Batch Runtime

## Purpose

This document defines the first executable implementation batch for the
canonical portrait-state runtime inside `topiclab-backend`.

The goal of this batch is deliberately narrow:

- create the first durable backend-owned answer to "what is the current
  portrait state?"
- make portrait updates explicit instead of hiding them inside ad-hoc UI or
  process-local glue
- materialize state from already migrated portrait slices first
- validate that dialogue-derived and scale-derived state can already land in a
  canonical server-owned store
- avoid pretending that the full portrait update / regeneration loop has
  already been migrated

This is the third concrete portrait-domain code batch after `scales` and the
first durable `dialogue` runtime batch.

## Status

Implemented and locally validated.

This batch introduces a first executable portrait-state runtime inside
`app/portrait`, plus a compatibility router at the old top-level backend path.

## Scope

### Included in this batch

- portrait-domain portrait-state router
- durable current portrait-state persistence
- durable portrait update-event persistence
- durable portrait version-snapshot persistence
- durable portrait observation persistence
- explicit state materialization from:
  - `dialogue_session`
  - `scale_session`
  - `import_result`
  - `manual`
- focused API tests
- standalone in-process smoke script

### Explicitly excluded from this batch

- automatic state writes from every dialogue/scale action
- prompt handoff linkage
- import-result linkage
- portrait export / download
- `TopicLab-CLI` command surface for portrait state
- frontend migration
- legacy `Resonnet` bridge reduction for heavier portrait flows

## Design Rule

This batch is a **canonical-state ownership batch**, not a full portrait-update
loop migration.

That means:

- the backend now owns a durable current portrait state
- updates are explicit and traceable
- state is materialized from already durable slices first
- the runtime does **not** yet claim automatic integration with all future
  portrait flows

The central rule is:

- if portrait state changes, the backend should know what source caused the
  change and persist that as an update event and version snapshot

## Target Internal Shape

After this batch, the portrait-state slice lives in:

```text
topiclab-backend/app/
  portrait/
    api/
      portrait_state.py
    services/
      portrait_state_service.py
    storage/
      portrait_state_repository.py
    schemas/
      portrait_state.py
```

Compatibility surface:

- `app/api/portrait_state.py`

## What This First Batch Actually Does

Implemented runtime behaviors:

- read the current canonical portrait state
- list portrait versions
- read one portrait version snapshot
- apply a portrait update from an explicit source
- read one update event
- list portrait observations

Supported update sources in this batch:

- `manual`
- `dialogue_session`
- `scale_session`
- `import_result`

Current materialization behavior:

- `dialogue_session`
  - reads the durable transcript and derived dialogue state
  - writes a normalized `dialogue.latest_session` block into the current state
- `scale_session`
  - reads the finalized canonical scale result
  - writes a normalized `scales.results[scale_id]` block into the current
    state
- `manual`
  - merges the provided patch directly into the current state
- `import_result`
  - reads the durable import result and latest parse run
  - merges the parse-run `candidate_state_patch` into current state
  - writes a normalized `imports.latest_import_id` / `imports.results[...]`
    block so later review and export paths can trace imported evidence

Persisted tables:

- `portrait_current_states`
- `portrait_update_events`
- `portrait_version_snapshots`
- `portrait_observations`

## Why This Batch Exists Before Prompt Handoff / Import

The target portrait system is supposed to answer at least two questions:

- what is the current portrait?
- how did it become this way?

Before prompt handoff, external-result import, export, or richer memory loops
can be refactored cleanly, the backend needs a stable place where portrait
truth accumulates.

This batch creates that first durable substrate.

## Validation Plan

This batch is only done if all of the following hold:

1. the new portrait-state files compile
2. focused portrait-state API tests pass
3. existing `dialogue` and `scales` focused tests still pass after the new DDL
   and router registration
4. a standalone smoke can materialize both dialogue-derived and scale-derived
   state into the same canonical portrait state

## Validation Result

The following commands were run:

```bash
python3 -m py_compile \
  topiclab-backend/app/api/portrait_state.py \
  topiclab-backend/app/portrait/api/portrait_state.py \
  topiclab-backend/app/portrait/schemas/portrait_state.py \
  topiclab-backend/app/portrait/storage/portrait_state_repository.py \
  topiclab-backend/app/portrait/services/portrait_state_service.py \
  topiclab-backend/tests/test_portrait_state_api.py \
  scripts/portrait_state_runtime_smoke.py

python3 -m pytest -q \
  topiclab-backend/tests/test_portrait_state_api.py \
  topiclab-backend/tests/test_dialogue_runtime_api.py \
  topiclab-backend/tests/test_scales_runtime_api.py

python3 scripts/portrait_state_runtime_smoke.py
```

Observed result:

- syntax compilation passed
- focused backend tests passed:
  - `12 passed`
- standalone portrait-state smoke completed successfully

What the smoke explicitly proved:

- one dialogue session can be materialized into canonical portrait state
- one finalized scale session can also be materialized into the same canonical
  portrait state
- the resulting current state contains both dialogue and scale sections
- version history and update history both increment
- observation rows are written for both materialization paths

Observed smoke facts included:

- `version_count = 2`
- `update_count = 2`
- observations include:
  - `dialogue_state_materialized`
  - `scale_result_materialized`

## Real Constraint Discovered

This first batch intentionally uses **explicit materialization**, not hidden
cross-slice coupling.

That means:

- dialogue writes do not yet automatically update canonical portrait state
- scale finalize does not yet automatically update canonical portrait state
- later orchestration work must still decide when and how automatic updates
  should happen

This is deliberate, because explicit source-driven updates are easier to test,
reason about, and evolve than silent side effects during early migration.

## What Is Still Missing After This Batch

Even after this batch, the following are still intentionally missing:

- prompt handoff integration as an explicit source selector
- automatic portrait rebuild orchestration
- richer normalization beyond the first dialogue/scale projections
- CLI command surface for portrait state
- portrait artifact / export linkage

Those should be layered on top of this canonical state substrate rather than
reintroducing working truth into legacy caches or UI-only flows.
