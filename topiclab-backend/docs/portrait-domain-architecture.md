# TopicLab Backend Portrait Domain Architecture

## Purpose

This document defines how portrait-related backend code should be structured
inside `topiclab-backend`.

It exists because TopicLab is a large product, while the portrait system is a
specialized business domain inside it. That domain needs to remain as decoupled
as possible from unrelated backend features, while still reusing the common
backend foundation:

- auth
- database session management
- router registration
- shared API conventions

## Current Reality

Today, portrait-related backend behavior is split across multiple places.

### In `Resonnet`

The historical portrait-builder runtime still lives mainly in:

- `Resonnet/app/api/profile_helper.py`
- `Resonnet/app/services/profile_helper/sessions.py`
- related profile-helper services

This is still the active path for the current web portrait builder.

### In `topiclab-backend`

Account-bound and twin-bound portrait persistence already lives here:

- `app/api/auth.py`
- `app/services/twin_runtime.py`
- `app/api/openclaw_twin_runtime.py`

And the new CLI-friendly scale runtime has already started here:

- `app/api/scales.py`
- `app/services/scales_service.py`
- `app/services/scales_scoring.py`

So the backend is already moving toward TopicLab-owned portrait runtime slices.

## Architectural Decision

Portrait should become a distinct bounded domain inside `topiclab-backend`.

The target package is:

- `app/portrait/`

This does **not** mean creating a separate backend service.

It means:

- one existing backend service
- one dedicated portrait domain package inside it
- minimal coupling to unrelated product modules

## Domain Boundary

The portrait domain should own portrait-specific runtime behavior, but it should
not duplicate generic platform infrastructure.

### Portrait domain should own

- scale runtime logic
- unified portrait-session orchestration
- legacy-compatible portrait skill policy and block contract parity
- portrait dialogue orchestration
- portrait prompt handoff / import-result flows
- portrait-specific repositories
- portrait-specific schemas
- portrait-specific runtime composition helpers

### Portrait domain should not own

- generic auth issuance
- shared db connection/session setup
- unrelated topics / apps / arcade / literature behavior
- generic OpenClaw infrastructure

## Persistence Rule

The portrait domain should be treated as a server-owned application domain, not
as a thin UI helper.

Important portrait data should not remain only in:

- frontend local storage
- standalone CLI local state
- backend process memory
- legacy filesystem caches

Those mechanisms can still exist as adapters or caches, but they should not be
the long-term source of truth.

The long-term source of truth should move into durable storage owned by
`topiclab-backend`.

Validated executable portrait slices now already cover:

- scale sessions, answers, and results
- top-level portrait sessions, runtime refs, and session events
- portrait dialogue sessions, transcript messages, and derived state
- canonical portrait current state, update events, version snapshots, and
  observations
- prompt handoff requests and persisted prompt artifacts
- pasted external-AI results and deterministic parse runs

Future portrait persistence should cover at least:

- direct scale sessions, answers, and results
- portrait dialogue sessions and message transcripts
- prompt handoff requests and generated prompt artifacts
- pasted external-AI outputs and parse results
- portrait update events and version history
- execution logs and runtime traces needed for debugging and product iteration

Design rule:

- if losing the data would harm continuity, introspection, debugging, or future
  product iteration, it belongs in durable server-side storage

## Package Layout

The target package layout is:

```text
app/portrait/
├── __init__.py
├── README.md
├── api/
├── services/
├── storage/
├── schemas/
└── runtime/
```

### `app/portrait/api/`

Expected future contents:

- scale routes after migration
- top-level portrait-session routes
- portrait dialogue routes if/when those are moved into TopicLab-owned runtime
- prompt handoff / import-result routes
- portrait-state routes

This layer should only own:

- route registration
- request validation
- auth wiring
- response serialization

### `app/portrait/services/`

Expected future contents:

- `scales_service.py`
- `scales_scoring.py`
- portrait-session orchestration services
- portrait dialogue orchestration services
- prompt-runtime services
- import-result parsing and application services
- portrait-state materialization services
- result normalization / summary builders

This layer should own runtime behavior, not router glue.

### `app/portrait/storage/`

Expected future contents:

- portrait repositories
- portrait-session persistence helpers
- scale-session persistence helpers
- portrait build persistence helpers
- compatibility adapters for legacy migration

### `app/portrait/schemas/`

Expected future contents:

- request/response models
- top-level portrait-session protocol objects
- internal typed contract objects
- result schemas

### `app/portrait/runtime/`

Expected future contents:

- definition loaders
- runtime builders
- prompt/runtime composition helpers
- loader shims for `scales-runtime` assets

## Why This Structure Is Better

### 1. It reduces scattering

Without a dedicated package, portrait code keeps spreading across:

- `app/api/`
- `app/services/`
- `app/storage/`

That is manageable for one file, but not for a growing portrait application
that will later include:

- scales
- dialogue
- prompt handoff
- pasted-result import
- self-updating portrait loops

### 2. It supports gradual refactor instead of big-bang rewrite

We do not need to move everything now.

We can:

1. create the domain boundary first
2. keep current executable files alive
3. migrate one bounded slice at a time

### 3. It keeps future CLI integration clean

The CLI should talk to stable portrait-domain APIs.

If portrait runtime code lives as a recognizable bounded domain, future
`TopicLab-CLI` migration remains a thin adapter problem, not a multi-module
forensics problem.

## Compatibility Bridge Principle

The new portrait runtime should not only own durable storage and clean slice
boundaries. It also has to recover the old portrait product contract.

That means the unified portrait-session layer is allowed to carry a temporary
compatibility mode while migration is still in progress.

Current first bridge:

- `start(mode=legacy_product)`

This mode does **not** replace the newer runtime-first session flow yet.
Instead, it gives the new backend a safe place to recover:

- old skill-routed collection behavior
- old block/UI-native response contracts
- AI-memory-first start flow

without discarding the already-validated durable slice runtimes underneath.

The currently recovered parity is now broader than the initial bridge:

- full direct `collect-basic-info` first pass
  - basic identity
  - process-ability ratings + notes
  - technical capability
  - current-needs capture
- deterministic `infer-profile-dimensions` automatically triggered after basic
  collection completes
- first executable `review-profile` parity
  - summary blocks
  - chart block
  - targeted update choices
- first executable `update-profile` parity
  - update basic identity
  - update technical capability
  - update process ability
  - update current needs
- top-level session history parity
  - recent orchestration events
  - runtime refs
  - portrait-state versions
  - portrait observations

Still not yet recovered:

- forum-profile generation
- scientist matching / recommendation flows
- export / download artifact parity
- publish-to-library side effects
- old-grade append-only execution logs

## Recommended Migration Order

### Phase 0. Create the domain package

Done in this step:

- `app/portrait/`
- `app/portrait/api/`
- `app/portrait/services/`
- `app/portrait/storage/`
- `app/portrait/schemas/`
- `app/portrait/runtime/`

At this phase, code may still execute from old locations.

### Phase 1. Keep scales as the first migrated slice

Reason:

- scales are already the cleanest CLI-friendly portrait slice
- they already have dedicated backend files
- they already have a standalone validation CLI

Practical approach:

- keep current imports and routes working
- move implementation into `app/portrait/`
- keep old top-level paths as compatibility wrappers
- preserve the external `/api/v1/scales/...` surface while changing internal
  ownership only

Detailed first-batch execution note:

- `portrait-scales-first-batch.md`
- detailed follow-up backend backlog:
  - `portrait-backend-backlog.md`

Current status:

- implemented
- internal ownership for the new scale runtime now lives under:
  - `app/portrait/api/scales.py`
  - `app/portrait/services/scales_service.py`
  - `app/portrait/services/scales_scoring.py`
  - `app/portrait/storage/scales_repository.py`
  - `app/portrait/runtime/definitions_loader.py`
- old top-level locations remain as thin compatibility shims:
  - `app/api/scales.py`
  - `app/services/scales_service.py`
  - `app/services/scales_scoring.py`
  - `app/api/dialogue.py`
- a first dialogue-runtime skeleton now also lives under:
  - `app/portrait/api/dialogue.py`
  - `app/portrait/services/dialogue_service.py`
  - `app/portrait/services/dialogue_runtime_service.py`
  - `app/portrait/services/dialogue_summary_service.py`
  - `app/portrait/storage/dialogue_repository.py`
  - `app/portrait/schemas/dialogue.py`
- a first canonical portrait-state runtime now also lives under:
  - `app/portrait/api/portrait_state.py`
  - `app/portrait/services/portrait_state_service.py`
  - `app/portrait/storage/portrait_state_repository.py`
  - `app/portrait/schemas/portrait_state.py`

### Phase 2. Add new portrait-domain code only inside `app/portrait/`

Any new portrait backend capability after this point should default to the new
domain package rather than being added into generic top-level `app/api/` and
`app/services/`.

### Phase 3. Reassess the old Resonnet portrait-builder path

Only after scales are stable and CLI-ready should we decide how to handle the
heavier legacy portrait-builder flows:

- portrait chat
- block chat
- prompt handoff
- import-result flow

Those should be migrated carefully, not mixed into the scale-runtime rollout.

## Important Current Constraint

The scale runtime migration is only the **first executable portrait slice**.

What is already true:

- internal implementation ownership for scales has been moved into
  `app/portrait/`
- callers can keep using the current `/api/v1/scales/...` routes
- old import paths still resolve through compatibility shims

What is **not** true yet:

- the heavier portrait-builder flows from `Resonnet` have not been migrated
- frontend callers have not been re-pointed away from legacy portrait routes
- `TopicLab-CLI` is now wired into `scales` and the first dialogue slice, but
  not yet into portrait-state or portrait-artifact runtime
- the new dialogue runtime is still a durable first slice rather than a full
  portrait-generation replacement
- the new portrait-state runtime is still an explicit materialization batch,
  not yet an automatically orchestrated portrait update loop
- live model generation still depends on `AI_GENERATION_*` being configured in
  the deployed environment; rotation-aware portrait runtime callers may use
  `AI_GENERATION_API_KEYS` while legacy-compatible callers continue to read
  `AI_GENERATION_API_KEY`

So the portrait-domain migration is underway:

- `scales` is the first fully validated executable slice
- `dialogue` now has the first durable executable slice in the new ownership
  model, including `TopicLab-CLI` main-entry wiring
- `portrait_state` now has the first durable executable canonical-state slice
  in the new ownership model
- the heavier portrait-generator logic is still pending

## Verified Path

The first migrated slice has been validated with:

- Python syntax compilation of the new portrait-domain files
- `python3 -m pytest -q topiclab-backend/tests/test_scales_runtime_api.py`
- `python3 scripts/scales_runtime_smoke.py`

Those checks confirmed:

- the compatibility router still works
- portrait-domain service and repository imports resolve correctly
- session -> answer -> finalize -> result still works end-to-end

The second portrait-domain slice has now also been validated with:

- `python3 -m pytest -q topiclab-backend/tests/test_dialogue_runtime_api.py`
- `python3 scripts/dialogue_runtime_smoke.py`

Those checks confirmed:

- the compatibility dialogue router resolves correctly
- durable dialogue sessions and transcript writes work end-to-end
- derived runtime state can already be rebuilt from persisted transcript data

The third portrait-domain slice has now also been validated with:

- `python3 -m pytest -q topiclab-backend/tests/test_portrait_state_api.py topiclab-backend/tests/test_dialogue_runtime_api.py topiclab-backend/tests/test_scales_runtime_api.py`
- `python3 scripts/portrait_state_runtime_smoke.py`

Those checks confirmed:

- the compatibility portrait-state router resolves correctly
- a canonical portrait current state can be read even before any update exists
- dialogue-derived state can be materialized into the canonical portrait state
- finalized scale-derived state can also be materialized into the same
  canonical portrait state
- update events, version snapshots, and observations are all durably written

## Rule For Future Work

From this point on, portrait backend work should follow this rule:

- if the work is portrait-domain-specific and not just generic infrastructure,
  prefer putting it under `app/portrait/`
- if the work creates important portrait data, prefer durable server-side
  persistence over local-only state

That is how the backend gradually becomes cleaner without breaking current
features.
