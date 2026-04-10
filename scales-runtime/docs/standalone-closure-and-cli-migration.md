# Standalone Closure And CLI Migration Strategy

## Purpose

This document defines the delivery strategy for the new scale runtime.

It answers one practical question:

How do we get a fully working scale-runtime loop without prematurely coupling it to the existing `topiclab-cli`, while still making later migration into `topiclab-cli` simple and low-risk?

The answer is:

- build the runtime as an independent bounded domain first
- run a complete local closed loop against backend APIs first
- only then add the thin `topiclab-cli` command surface
- migrate existing callers in phases after the runtime is proven stable

## Core Decision

The current work should **not** start by modifying the existing `topiclab-cli`.

Instead, it should start by making this sequence work end-to-end:

1. canonical scale definitions
2. TopicLab-backend scale API skeleton
3. durable session model
4. canonical scoring
5. direct local closed-loop verification

Only after that should we do:

6. thin `topiclab-cli` integration
7. human-facing web migration
8. internal twin/scientist-batch runs through the same contract

This is a sequencing decision, not a rejection of `topiclab-cli`.

## Why This Is The Right Sequence

### 1. `topiclab-cli` is already a thin transport kernel

The existing `TopicLab-CLI` repository is not a good place to incubate portrait-specific runtime logic.

Verified local findings:

- `src/cli.ts` is a command surface and dispatcher
- `src/session.ts` is a session/auth transport helper with auto-renew behavior
- `src/http.ts` is a generic JSON/form/binary transport layer
- `src/config.ts` persists generic CLI state in `state.json`

This is good news.

It means `topiclab-cli` is already shaped like a thin adapter, which is exactly why we should avoid pushing unfinished scale-runtime business logic into it too early.

### 2. We still need to validate the runtime model itself

Right now, the hard part is not "can we add a command".

The hard part is:

- can the new runtime hold durable sessions
- can it resume without drift
- can it score identically across surfaces
- can it produce structured results suitable for later twins and UI use

Those questions should be answered before adding CLI polish.

### 3. Parallel development risk is real

This repository already has multiple active workstreams:

- TopicLab topics and OpenClaw routes
- twin runtime
- skill hub
- portrait and scientist assets
- existing profile-helper compatibility paths

If we start by editing `topiclab-cli` deeply, we create unnecessary coupling before the runtime contract itself is stable.

## Strategic Split

The work should be split into three layers.

### A. Independent runtime domain

Lives in:

- `scales-runtime/`
- `topiclab-backend/app/api/scales.py`
- `topiclab-backend/app/services/scales_*`

Responsibilities:

- definitions
- schemas
- scoring
- session lifecycle
- result materialization

This is the real product.

### B. Standalone local closure harness

This should be built and validated before touching `topiclab-cli`.

Recommended first closure path:

- start TopicLab-backend locally
- call `/api/v1/scales/...` directly
- use fixtures or a small local harness to:
  - list scales
  - get one definition
  - create a session
  - answer questions
  - finalize
  - read result

Important point:

This harness does not need to become a user-facing product.
Its job is to prove the runtime.

### C. Thin CLI adapter

Only after the standalone closure works, add:

- `topiclab scales ...`

to `TopicLab-CLI`.

At that point, `topiclab-cli` only needs to:

- parse arguments
- call the already-proven API
- reuse its existing auth/session transport
- print JSON

That is a safe late-stage integration.

## Recommended Standalone Closure Design

### What "closed loop" means here

A true closed loop means the following all work together:

1. definitions can be discovered
2. a scale session can be created
3. answers can be persisted incrementally
4. session state can be resumed
5. finalize performs canonical scoring
6. structured results can be fetched later

If any of these is missing, the runtime is not actually closed.

### What to use before `topiclab-cli`

For the standalone verification stage, prefer one of these:

- direct HTTP calls against TopicLab-backend
- a tiny local runner or smoke script in the TopicLab repository
- fixture-driven tests inside backend

Do not make the temporary harness the new long-term interface.

The temporary harness should exist only to validate the contract.

### Where the temporary harness should live

Recommended location:

- inside `Tashan-TopicLab`, not inside `TopicLab-CLI`

Reason:

- it belongs to runtime validation
- it is coupled to evolving definitions and fixtures
- it should not pollute the reusable CLI package during early development

Good future locations include:

- `scales-runtime/fixtures/`
- `scales-runtime/docs/`
- `topiclab-backend/tests/`
- or a focused smoke script under the main TopicLab repo

## How To Keep Future CLI Migration Simple

The runtime should be built as if a CLI adapter already exists, even before the adapter is written.

That means:

### 1. Use stable JSON responses from day one

Every backend endpoint should already return machine-readable payloads suitable for CLI use.

### 2. Use explicit machine-readable error codes

This avoids rewriting backend error semantics later just to support CLI.

### 3. Keep session and auth assumptions transport-neutral

The backend should not assume:

- browser-only callers
- frontend-only state
- one-shot submission

### 4. Avoid embedding frontend-specific result shaping

The result object should already be portable enough for:

- CLI
- web
- internal twins

### 5. Keep route design CLI-friendly

The `/api/v1/scales/...` family should already map cleanly onto eventual CLI verbs, even if the CLI command is not implemented yet.

## Recommended Migration Phases

### Phase 1: independent runtime foundation

Deliver:

- definitions
- schemas
- backend route skeleton
- backend service skeleton

Status:

- already started

### Phase 2: durable backend closure

Deliver:

- persistence
- scoring
- finalize/result
- fixtures
- standalone smoke loop

Success criterion:

- a full scale run can be completed locally without `topiclab-cli`

### Phase 3: thin CLI integration

Deliver:

- `topiclab scales ...` command group in `TopicLab-CLI`

Success criterion:

- CLI is only an adapter; no business rules duplicated

### Phase 4: caller migration

Deliver:

- internal twin/scientist runs move onto the runtime
- web scale page begins migrating

### Phase 5: legacy cleanup

Deliver:

- old Resonnet `scales.json` path is deprecated

## What This Strategy Explicitly Avoids

This strategy deliberately avoids:

- starting with a CLI UX problem before the runtime exists
- tying temporary runtime assumptions to `TopicLab-CLI`
- duplicating scale logic across backend and CLI
- creating a second unfinished mini-runtime just for testing

## Verified Local Evidence

This document is based on actual local inspection of `TopicLab-CLI`:

- `README.md`
  - describes it as a TopicLab-specific npm-native execution CLI
- `docs/architecture.md`
  - describes it as a local execution kernel and JSON-first adapter
- `src/cli.ts`
  - central command registration
- `src/session.ts`
  - auth/session transport helper with auto-renew
- `src/http.ts`
  - generic request layer
- `src/config.ts`
  - state persistence

These findings support the strategy:

- incubate the runtime outside the CLI
- integrate into the CLI only after the runtime closes cleanly

## Recommended Next Step

The next step should not be "add `topiclab scales` now".

The next step should be:

- complete the backend closed loop
- add fixtures
- prove end-to-end runtime correctness locally

Only after that should the CLI adapter be added.

## Verified Local Closure Path

The following standalone closure path has now been validated locally:

- canonical definitions under `scales-runtime/definitions/`
- backend runtime under:
  - `topiclab-backend/app/api/scales.py`
  - `topiclab-backend/app/services/scales_service.py`
  - `topiclab-backend/app/services/scales_scoring.py`
- fixture-backed API test:
  - `topiclab-backend/tests/test_scales_runtime_api.py`
- standalone smoke script:
  - `scripts/scales_runtime_smoke.py`

The validated loop is:

1. list scales
2. get one definition
3. create a session
4. write answers
5. finalize
6. read result

This original smoke-only closure is now complemented by a real standalone CLI:

- `scales-runtime/cli/standalone_scales_cli.py`

That CLI has also been validated to:

1. show usage
2. bootstrap local auth
3. list and read definitions
4. answer RCSS questions from terminal input
5. finalize and persist results
6. re-read the finalized result in a later invocation

See:

- `scales-runtime/docs/standalone-cli.md`

## Real Pitfalls Encountered

The local verification process surfaced two environment issues that are not part of the scale runtime itself:

- the local `python3` is older than some project modules expect
  - `content_moderation.py` uses `@dataclass(slots=True)`
  - `oss_upload.py` imports `datetime.UTC`
- importing the full `topiclab-backend/main.py` in tests also pulls in unrelated routes that require optional multipart dependencies

As a result, the validated standalone tests intentionally use a **minimal FastAPI app** that mounts only:

- `/auth`
- `/api/v1/scales`

This is an important implementation fact, not just a testing convenience:

- it keeps standalone runtime verification focused
- it avoids unrelated app-surface dependencies masking scale-runtime regressions
