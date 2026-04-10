# Scale CLI Runtime Architecture

## Why This Exists

TopicLab is a larger product with many existing capabilities. The work here is
to add and strengthen the portrait domain inside that product without
restructuring unrelated features.

Within that portrait domain, TopicLab already has three serious portrait scales
and working frontend pages for human self-report.

What is missing is not the questionnaire content itself, but a stable runtime contract that:

- can be used by `topiclab-cli`
- can be used by agents repeatedly without drifting or stopping mid-run
- can later be opened to users as a first-class interaction surface
- can feed one canonical scoring and result pipeline

This document defines that architecture.

It intentionally treats "scale runtime" as a dedicated portrait-domain runtime
instead of scattering portrait-specific logic across generic CLI or unrelated
TopicLab modules.

## Design Goals

### 1. Decouple business assets from shared infrastructure

`topiclab-cli` is shared infrastructure. It should expose commands and JSON output, but it should not become the place where portrait-specific rules, question banks, and scoring logic are maintained.

Scale- and portrait-specific assets should live in a dedicated domain directory
so they can evolve without colliding with parallel work on topics, arcade,
apps, or other OpenClaw flows.

### 2. Keep the CLI thin

The CLI should not become a second scoring engine or a second source of truth.

Its job is:

- parse commands
- call backend APIs
- print machine-readable results
- support resumable interaction

It should not own:

- canonical question text
- scoring formulas
- result interpretation rules
- persistence decisions

### 3. Make agent interaction durable instead of one-shot

The runtime must be designed as a session state machine.

That means:

- an agent can start a scale session
- answer one question or many questions
- ask what remains
- continue later
- finalize only when the session is complete

The protocol should never depend on the agent "remembering" where it left off.

### 4. Preserve one scoring truth

A given answer sheet must always produce the same result, regardless of whether it came from:

- the web UI
- the CLI
- an internal scientist twin
- a scripted regression test

This means scoring must be canonical and server-owned.

### 5. Return structured results, not only raw numbers

The runtime must return enough structure for downstream use:

- per-question answers
- per-dimension scores
- derived indices such as `CSI` and `RAI`
- result metadata and scoring version

This allows later reuse by profile rendering, analysis, and internal batch runs.

## Domain Boundary

The architecture is split into four layers.

### A. Domain assets: `scales-runtime/`

This directory is the scale domain workspace.

It should own:

- canonical scale definitions
- canonical scoring specifications
- session / answer / result schemas
- fixtures and regression examples
- architecture and rollout docs

It should not own executable CLI infrastructure or generic TopicLab API routing.

### B. CLI surface: `TopicLab-CLI`

`TopicLab-CLI` should expose the command surface, for example:

- `topiclab scales list`
- `topiclab scales get <scale_id>`
- `topiclab scales session start`
- `topiclab scales session status`
- `topiclab scales answer`
- `topiclab scales answer-batch`
- `topiclab scales finalize`
- `topiclab scales result`

The CLI should remain a thin adapter:

- command parsing
- backend requests
- JSON-first stdout
- stable error mapping

The CLI may have a small local helper module for the `scales` command group, but that helper should stay transport-oriented, not domain-authoritative.

### C. Backend runtime: `topiclab-backend`

`topiclab-backend` should own:

- scale session lifecycle
- answer persistence
- completion checks
- canonical scoring execution
- result materialization
- authenticated access control

The backend is the correct place for "truth":

- which answers belong to a session
- whether a session is complete
- which scoring version produced a result
- what the final structured output is

### D. Frontend and downstream consumers

The frontend profile-helper pages and later internal twin runners should consume
the same runtime outputs.

This means:

- the existing TopicLab frontend can add new portrait pages and flows without
  disturbing unrelated product areas
- the portrait web UI should gradually become a client of the same
  session/result APIs
- scientist-twin testing should eventually call the same CLI or backend contract instead of inventing a separate scoring path

## Recommended Repository Shape

### In `Tashan-TopicLab`

```text
scales-runtime/
├── definitions/
├── scoring/
├── schemas/
├── fixtures/
└── docs/
```

Recommended future file ownership:

- `definitions/`
  - one canonical file per scale family or one normalized registry file
- `scoring/`
  - formula specs and derived-index definitions
- `schemas/`
  - session, answer, and result schemas
- `fixtures/`
  - known-good answer sheets and expected outputs
- `docs/`
  - protocol docs, rollout notes, test strategy, and caveats

### In `TopicLab-CLI`

Keep changes minimal and localized:

- extend `src/cli.ts`
- if needed, add a small `src/scales.ts` helper

No scale definitions or scoring formulas should be maintained there as the long-term source of truth.

### In `topiclab-backend`

Add scale-specific entry points in dedicated files, instead of mixing them into unrelated modules:

- a scale API module
- a scale service module
- a scale scoring module

This keeps the runtime cohesive and easier to test.

## Runtime Model

### Session Lifecycle

The runtime should behave as a resumable session system.

Recommended states:

- `initialized`
- `in_progress`
- `ready_to_finalize`
- `completed`
- `abandoned`

Key rules:

- `initialized` means the session exists but nothing is answered yet.
- `in_progress` means answers exist but required questions are still missing.
- `ready_to_finalize` means all required questions are present and scoring can run.
- `completed` means scoring is frozen for that session and results are materialized.
- `abandoned` is optional, but useful for stale sessions or internal cleanup.

### Interaction Contract

Each CLI/API interaction should return enough state for an agent to continue deterministically.

Recommended response fields:

- `session_id`
- `scale_id`
- `status`
- `answered_count`
- `remaining_count`
- `missing_question_ids`
- `next_question`
- `allowed_actions`

This is the main guard against agent dropout or stalled multi-turn execution.

### Canonical Scoring Path

Scoring should happen in exactly one place: server-side.

The frontend currently contains the active question and scoring implementation, but that should be treated as the current reference, not the final ownership model.

Migration direction:

1. use the existing frontend definitions as the verified source material
2. establish server-side canonical scoring and definitions inside the scale runtime domain
3. have CLI and later frontend paths both call the same backend scoring flow

During the migration period, any copied logic must be tracked carefully and versioned so mismatches are visible.

### Result Model

The runtime should return structured results, not just raw dimension scores.

Recommended result shape:

- `session`
- `scale`
- `answers`
- `dimension_scores`
- `derived_scores`
- `result_summary`
- `scoring_version`
- `completed_at`

Examples of derived scores:

- `RCSS`
  - `integration`
  - `depth`
  - `CSI`
  - `type`
- `AMS`
  - `intrinsicTotal`
  - `extrinsicTotal`
  - `RAI`
- `Mini-IPIP`
  - five dimension averages and optional level labels

## Why This Must Be Separate From Scientist Logic

The internal plan is to later let 120 built-in scientist twins use the same scale runtime.

But that is a downstream caller problem, not part of the runtime contract itself.

This separation is intentional:

- the runtime should be user-openable
- the same contract should work for humans, agents, and internal twins
- scientist-specific answering heuristics should not leak into the base protocol

So the order is:

1. build a clean universal scale runtime
2. validate it with internal twins
3. later add specialized callers on top

## Initial Implementation Plan

### Phase 1: protocol and structure

- create the dedicated domain folder
- define the architecture and ownership model
- define the command surface and session state machine

### Phase 2: backend canonical runtime

- add scale session APIs in `topiclab-backend`
- add canonical scoring service
- persist results and expose stable result payloads

### Phase 3: CLI integration

- add `topiclab scales ...` commands
- ensure JSON-first output
- ensure resumable agent workflows

### Phase 4: frontend alignment

- gradually align the existing profile-helper scale pages to the same backend session/result path

### Phase 5: internal twin testing

- use built-in twins as early callers to stress-test resumability, stability, and result consistency

## Non-Goals For The First Version

- no scientist-specific answering protocol yet
- no automatic type-classification system in this runtime layer
- no premature refactor of all portrait UI code
- no attempt to solve all share-card or portrait rendering concerns here

## Decision Summary

The scale runtime should be treated as a dedicated domain inside the main TopicLab repository.

The recommended split is:

- `scales-runtime/` owns the scale domain assets and docs
- `topiclab-cli` owns only the thin command surface
- `topiclab-backend` owns session truth, scoring truth, and result truth

This is the cleanest way to support both future public user access and internal twin-driven testing without tangling portrait logic into the general CLI infrastructure.
