# Scale Runtime Backend API Mapping

## Purpose

This document connects three things that currently live apart:

- the existing human-facing scale flow in `frontend/profile-helper`
- the existing Resonnet `profile-helper/scales` persistence path
- the new CLI-first scale runtime proposed under `scales-runtime/`

The goal is to define one backend ownership model and one migration path without forcing a risky all-at-once rewrite.

This document is intentionally implementation-facing. It answers:

- where the new runtime APIs should live
- how `topiclab scales ...` should map onto backend endpoints
- how the old profile-helper scale flow should coexist during migration
- which part of the system owns session truth, scoring truth, and result truth at each phase

## Current Reality

### Existing frontend flow

Today the scale page is still a web-only self-report flow:

- questionnaire definitions live in `frontend/src/modules/profile-helper/data/scales.ts`
- scoring logic lives in `frontend/src/modules/profile-helper/utils/scoring.ts`
- the page submits answers through `submitScale(...)`
- `submitScale(...)` calls `POST /profile-helper/scales/submit`

In practice this means the human scale path is still tied to the legacy profile-helper API surface.

### Existing backend flow

Today scale persistence still runs through Resonnet:

- `POST /profile-helper/scales/submit`
- `GET /profile-helper/scales/{session_id}`

That path persists data in Resonnet workspace storage, specifically `scales.json`.

This flow works for the current portrait UI, but it is not the right long-term home for:

- CLI-first session interaction
- resumable agent use
- user-openable terminal access
- canonical cross-surface scoring truth

### Important mismatch already confirmed

The current portrait stack has a real split-brain problem:

- the scale page writes `scales.json`
- the structured portrait page reads `profile.md`

So the current system does not yet have one canonical runtime for measurement data.

That mismatch is acceptable as a legacy compatibility state, but not as the final architecture.

## Ownership Decision

### Canonical runtime owner

The new scale runtime should be owned by `topiclab-backend`, not by Resonnet.

Reason:

- scale sessions are user-account state
- finalized results should be durable account-linked artifacts
- CLI and future user-open terminal usage already fit the TopicLab-side authenticated API model
- Resonnet is better treated as an execution and workspace layer, not the durable authority for long-lived scale sessions and results

### Domain assets vs executable ownership

The split should be:

- `scales-runtime/`
  - owns business-domain assets and protocol docs
  - canonical definitions, schemas, fixtures, scoring specs
- `topiclab-backend`
  - owns executable API/runtime behavior
  - session lifecycle, persistence, scoring execution, result materialization
- `TopicLab-CLI`
  - owns command parsing and JSON output only
- `Resonnet`
  - remains on the old path during migration
  - should eventually stop being the canonical home for scale persistence

## Proposed Backend Route Family

The new runtime should live under a dedicated TopicLab API family:

```text
/api/v1/scales/...
```

Recommended first routes:

- `GET /api/v1/scales`
- `GET /api/v1/scales/{scale_id}`
- `POST /api/v1/scales/sessions`
- `GET /api/v1/scales/sessions/{session_id}`
- `POST /api/v1/scales/sessions/{session_id}/answers`
- `POST /api/v1/scales/sessions/{session_id}/answer-batch`
- `POST /api/v1/scales/sessions/{session_id}/finalize`
- `GET /api/v1/scales/sessions/{session_id}/result`
- `GET /api/v1/scales/sessions`
- `POST /api/v1/scales/sessions/{session_id}/abandon`

This route family keeps the scale runtime independent from:

- `/profile-helper/...`
- `/openclaw/topics/...`
- `/openclaw/twins/...`
- `/auth/...`

It is domain-specific without polluting unrelated API namespaces.

## CLI To Backend Mapping

The new CLI surface should be a thin projection of the backend route family.

| CLI command | Backend route | Notes |
|---|---|---|
| `topiclab scales list --json` | `GET /api/v1/scales` | returns available definitions |
| `topiclab scales get <scale_id> --json` | `GET /api/v1/scales/{scale_id}` | returns definition payload |
| `topiclab scales session start --scale <scale_id> --json` | `POST /api/v1/scales/sessions` | creates session |
| `topiclab scales session status <session_id> --json` | `GET /api/v1/scales/sessions/{session_id}` | recovery / polling entrypoint |
| `topiclab scales answer <session_id> ... --json` | `POST /api/v1/scales/sessions/{session_id}/answers` | single-question write |
| `topiclab scales answer-batch <session_id> ... --json` | `POST /api/v1/scales/sessions/{session_id}/answer-batch` | batch write |
| `topiclab scales finalize <session_id> --json` | `POST /api/v1/scales/sessions/{session_id}/finalize` | canonical scoring |
| `topiclab scales result <session_id> --json` | `GET /api/v1/scales/sessions/{session_id}/result` | immutable result read |
| `topiclab scales sessions list --json` | `GET /api/v1/scales/sessions` | session listing |
| `topiclab scales sessions abandon <session_id> --json` | `POST /api/v1/scales/sessions/{session_id}/abandon` | explicit stop |

The CLI should not add hidden behavior on top of these routes.

## Recommended Backend Module Shape

To keep this work decoupled from parallel development, the executable backend implementation should be localized.

Recommended files inside `topiclab-backend`:

- `app/api/scales.py`
- `app/services/scales_service.py`
- `app/services/scales_scoring.py`
- optional persistence helper such as:
  - `app/services/scales_repository.py`

Recommended responsibilities:

### `app/api/scales.py`

Owns:

- route registration
- request validation
- auth guard wiring
- response serialization

Does not own:

- scoring formulas
- session transition logic
- question registry contents

### `app/services/scales_service.py`

Owns:

- session creation
- answer writes
- transition rules
- finalize orchestration
- result fetch logic

### `app/services/scales_scoring.py`

Owns:

- canonical scoring execution
- derived metric calculation
- scoring versioning

This file should become the one scoring truth for CLI and web.

## Auth Model

The new runtime should follow the existing TopicLab authenticated API model.

Recommended default:

- user-authenticated sessions only in v1
- anonymous support can be added later, but should not complicate the first durable runtime

Recommended identity fields at session start:

- `actor_type`
  - `human`
  - `agent`
  - `internal`
- `actor_id`
  - optional but useful for audit trails

Important principle:

- auth decides who owns the session
- `actor_type` only explains how the session is being driven

## Persistence Model

The new runtime should persist two different kinds of objects:

### 1. Mutable session state

This includes:

- scale id
- status
- answers-in-progress
- timestamps
- missing question ids
- versions

### 2. Immutable finalized result

This includes:

- frozen answers
- dimension scores
- derived scores
- result summary
- scoring version

The finalized result should never depend on the caller recomputing scores locally.

## Coexistence With The Legacy Flow

The existing Resonnet `profile-helper` path should not be ripped out immediately.

Instead, the migration should run in phases.

### Phase 0: current state

Current truth:

- frontend scale page calls Resonnet `POST /profile-helper/scales/submit`
- Resonnet persists `scales.json`
- frontend scoring is local

This phase remains the compatibility baseline.

### Phase 1: define the new runtime without touching old flow

Work introduced in this phase:

- `scales-runtime/` domain docs and assets
- new TopicLab-side scale API design
- no user-facing behavior changes yet

This is the phase we are in now.

### Phase 2: implement TopicLab canonical scale runtime

New behavior:

- add TopicLab backend routes under `/api/v1/scales/...`
- add canonical server-side scoring
- add CLI command surface in `TopicLab-CLI`

Legacy flow remains untouched.

At this point:

- CLI and automated callers use the new runtime
- web profile-helper still uses the old Resonnet submit path

### Phase 3: migrate the web scale page

Change:

- `ScaleTestPage` stops computing the final truth locally
- the page becomes a client of the new TopicLab runtime
- existing frontend question rendering may remain temporarily, but session and scoring truth move server-side

Preferred direction:

- `frontend` reads definitions from the new runtime
- answers are stored in TopicLab runtime sessions
- result rendering consumes `scale_result`

### Phase 4: deprecate Resonnet `scales.json`

Only after the web path is migrated:

- stop writing new scale answers to Resonnet `scales.json`
- keep compatibility readers temporarily if needed
- remove old API docs and tests that treat `/profile-helper/scales/submit` as canonical

This is the moment when split-brain is actually removed.

## Migration Policy For Definitions And Scoring

The current question definitions and formulas live in frontend code.

That is acceptable as source material, but not as the final ownership model.

Recommended migration order:

1. treat existing frontend `scales.ts` and `scoring.ts` as the verified reference
2. reproduce those definitions and formulas server-side under the new runtime
3. validate that the same answer sheet produces the same outputs
4. only then migrate frontend callers to the new backend truth
5. later, if needed, extract a shared machine-readable registry from the scale runtime domain

This sequence minimizes the risk of breaking the current UI during protocol work.

## Result Contract Across Surfaces

By the end of migration, the following surfaces should all rely on the same result object:

- CLI
- future terminal-facing user workflow
- future built-in scientist-twin validation runs
- web scale page
- downstream portrait interpretation

That result object should always come from TopicLab backend finalize/result endpoints, not from local recomputation.

## What Should Not Be Implemented In V1

To keep the work decoupled and low-risk, v1 should explicitly avoid:

- moving all portrait logic into CLI
- making scientist-specific answer provenance part of the base protocol
- forcing frontend and CLI to share a large new package before the runtime is validated
- rewriting old Resonnet profile-helper flows before the new runtime works end-to-end

## Verified Local Evidence Behind This Document

This architecture is based on the currently verified local code paths:

- `frontend/src/modules/profile-helper/profileHelperApi.ts`
  - `submitScale(...)` still posts to `/profile-helper/scales/submit`
- `frontend/src/modules/profile-helper/data/scales.ts`
  - still holds active question definitions
- `frontend/src/modules/profile-helper/utils/scoring.ts`
  - still holds active frontend scoring logic
- `frontend/src/modules/profile-helper/pages/ScaleTestPage.tsx`
  - still drives the human questionnaire page
- `Resonnet/app/api/profile_helper.py`
  - still owns `POST /profile-helper/scales/submit`
- `Resonnet/app/services/profile_helper/sessions.py`
  - still persists `scales.json`
- `docs/cognition-portrait/full-portrait-scale-and-skill-audit.md`
  - already records the current split between `scales.json` and `profile.md`
- `Resonnet/docs/profile-architecture-final.md`
  - records the intended direction that scale data should move to TopicLab-side ownership

## Next Document

After this mapping, the next implementation-facing document should define the executable rollout in more detail:

- persistence model choice
- table or storage shape
- versioning strategy for definitions and scoring
- regression-test fixture plan
