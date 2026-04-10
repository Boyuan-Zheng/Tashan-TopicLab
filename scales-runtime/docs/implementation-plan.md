# Scale Runtime Implementation Plan

## Purpose

This document turns the scale-runtime architecture into an execution plan.

It focuses on:

- where new code should land
- which storage objects should exist first
- how definition and scoring versioning should work
- how to validate correctness before migrating callers

It is intentionally conservative. The priority is to introduce the new runtime without colliding with parallel work on TopicLab topics, OpenClaw, twins, or existing profile-helper behavior.

## Implementation Principles

### 1. Build the new path beside the old path

Do not rewrite the existing Resonnet profile-helper scale path first.

Instead:

- add the new TopicLab-owned runtime
- validate it independently
- migrate callers only after correctness is proven

### 2. Keep ownership localized

New executable code should be concentrated in dedicated files.

Do not spread scale-runtime behavior across unrelated modules.

### 3. Treat frontend definitions as reference material, not final authority

The current frontend question registry and scoring code are the currently verified implementation, but the new runtime should become the canonical execution path.

### 4. Make validation explicit

The new runtime should not be trusted because it "looks equivalent".

It should be verified by:

- fixture answer sheets
- expected dimension scores
- expected derived scores
- parity checks against the current frontend formulas

## Recommended Code Placement

### In `Tashan-TopicLab/topiclab-backend`

Recommended new files:

- `app/api/scales.py`
- `app/services/scales_service.py`
- `app/services/scales_scoring.py`
- `app/services/scales_repository.py`

Recommended table/bootstrap changes:

- extend `app/storage/database/postgres_client.py`
- add dedicated DDL helpers for scale-runtime tables, similar to other bounded domains

### In `TopicLab-CLI`

Recommended minimal additions:

- extend `src/cli.ts`
- add a small transport-oriented helper such as `src/scales.ts`

No question definitions or scoring formulas should become long-term CLI assets.

### In `Tashan-TopicLab/scales-runtime`

Recommended next asset files:

- `definitions/registry.json`
- `definitions/rcss.json`
- `definitions/mini-ipip.json`
- `definitions/ams-gsr-28.json`
- `scoring/rcss.md`
- `scoring/mini-ipip.md`
- `scoring/ams-gsr-28.md`
- `fixtures/*.json`

The exact file format can still change, but this directory should become the durable domain workspace that documents what the system means.

## Recommended Persistence Model

The new runtime needs three storage layers.

### 1. `scale_sessions`

Purpose:

- mutable in-progress session state

Recommended fields:

- `id`
- `user_id`
- `scale_id`
- `status`
- `actor_type`
- `actor_id`
- `definition_version`
- `scoring_version`
- `created_at`
- `updated_at`
- `completed_at`
- `abandoned_at`

Recommended invariants:

- session belongs to exactly one user
- one session targets exactly one scale
- completed sessions become read-only

### 2. `scale_session_answers`

Purpose:

- normalized answer storage for mutable sessions

Recommended fields:

- `id`
- `session_id`
- `question_id`
- `value`
- `answered_at`
- optional `source`
- optional `source_detail`

Recommended invariants:

- unique `(session_id, question_id)`
- later write updates the same logical answer record

### 3. `scale_results`

Purpose:

- immutable finalized result object

Recommended fields:

- `id`
- `session_id`
- `user_id`
- `scale_id`
- `definition_version`
- `scoring_version`
- `answers_json`
- `dimension_scores_json`
- `derived_scores_json`
- `result_summary_json`
- `completed_at`

Recommended invariants:

- unique `session_id`
- result only created from `ready_to_finalize`

## Why Not Reuse `digital_twins`

`digital_twins` is already carrying active profile state.

Scale runtime should not be folded into that table because:

- session lifecycle is different
- answer granularity is different
- result immutability needs a separate model
- CLI recovery needs first-class session records

The correct relationship is:

- scale runtime produces durable results
- downstream portrait logic may later read those results

But the storage should remain separate.

## Definition Versioning Strategy

Every runtime object should carry both:

- `definition_version`
- `scoring_version`

### `definition_version`

Bumps when:

- question text changes
- reverse-key flags change
- dimension membership changes
- answer range changes

### `scoring_version`

Bumps when:

- dimension formula changes
- derived score calculation changes
- normalization or rounding changes
- result-summary generation changes in a score-affecting way

Important rule:

- a completed result should always record the exact versions used at finalize time

## Fixture Strategy

Before migrating any caller, create a golden-fixture set.

Recommended fixture categories:

### A. Minimal valid answer sheets

One valid full answer sheet per scale.

Purpose:

- smoke test finalize success

### B. Range and validation fixtures

Examples:

- invalid question id
- out-of-range answer value
- missing required questions
- finalize before completion

Purpose:

- validate error semantics

### C. Known-score parity fixtures

For each scale:

- at least 3 full answer sheets
- expected `dimension_scores`
- expected `derived_scores`

Purpose:

- prove backend parity with current frontend formulas

### D. Session-resume fixtures

Examples:

- answer one question then read status
- partial batch write then continue
- finalize completed session twice

Purpose:

- prove agent-safe resumability

## Recommended Implementation Phases

### Phase A: domain assets and schema docs

Deliverables:

- `scales-runtime/` docs
- first normalized definition drafts
- first fixture drafts

Status:

- architecture/protocol docs are already in place
- first normalized definition files now exist under `scales-runtime/definitions/`

### Phase B: backend storage and API skeleton

Deliverables:

- DDL for `scale_sessions`, `scale_session_answers`, `scale_results`
- `app/api/scales.py`
- `app/services/scales_service.py`
- placeholder result serialization

Success criteria:

- can create session
- can write answers
- can inspect session state

Current local status:

- a thin `app/api/scales.py` and `app/services/scales_service.py` skeleton now exist
- definition listing and definition reads now work
- session create / answer / finalize / result now work in backend
- parity fixtures now exist for all three scale families
- standalone smoke coverage now exists through:
  - `topiclab-backend/tests/test_scales_runtime_api.py`
  - `scripts/scales_runtime_smoke.py`

### Phase C: canonical scoring implementation

Deliverables:

- `app/services/scales_scoring.py`
- parity fixtures for RCSS, Mini-IPIP, AMS-GSR 28

Success criteria:

- the same answer sheet matches current frontend outputs

### Phase D: CLI thin adapter

Deliverables:

- `topiclab scales ...` commands in `TopicLab-CLI`

Success criteria:

- CLI can complete full session flow entirely against TopicLab backend

### Phase E: internal validation with built-in twins

Deliverables:

- internal runners can open scale sessions through the same CLI/API contract

Success criteria:

- no scientist-specific protocol fork is needed

### Phase F: web migration

Deliverables:

- `ScaleTestPage` becomes a client of TopicLab backend runtime

Success criteria:

- frontend local scoring is no longer the final authority

### Phase G: legacy cleanup

Deliverables:

- deprecate Resonnet `profile-helper/scales/submit`
- remove canonical reliance on `scales.json`

Success criteria:

- one scoring truth
- one durable runtime

## Recommended Non-Goals For First Code Pass

Do not include these in the first code pass:

- scientist-specific evidence provenance
- batch classification logic
- share-card generation
- profile interpretation rewrite
- a large shared package refactor across frontend, backend, and CLI

The first code pass should only make the runtime real and correct.

## Verification Checklist Before Coding Migration

Before moving the web UI or twin flows, confirm:

- session lifecycle works end-to-end
- finalize is idempotent and immutable
- parity fixtures pass for all three scales
- CLI errors are machine-readable
- results include enough structure for downstream reuse
- no new dependency on Resonnet workspace storage exists in the new path

## Recommended Next Work Item

The next concrete artifact after this plan should be one of:

- normalized definition files in `scales-runtime/definitions/`
- or backend endpoint stubs in `topiclab-backend/app/api/scales.py`

The safer order is:

1. define normalized definitions
2. define golden fixtures
3. implement backend runtime against those assets
4. validate with standalone tests and smoke
5. only then add the CLI adapter
