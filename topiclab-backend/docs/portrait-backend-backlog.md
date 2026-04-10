# Portrait Backend Backlog

## Purpose

This document turns the portrait-system refactor direction into a concrete
backend backlog.

It answers one practical question:

- if frontend migration is deferred, what backend work still needs to be built
  under the new portrait architecture?

This is a backend-only planning document.

## Product Framing Correction

The backlog should now be read under one stronger framing:

- the portrait system is not merely a test page
- it is becoming the entry application for a broader agent self-cognition
  infrastructure

That means the backend is responsible not only for:

- measurement
- profile generation

but also for a longer-lived cognition loop:

- reflection
- portrait updates
- memory / experience organization
- recoverable self-knowledge
- future platform-side personalized support

This framing does **not** invalidate the older portrait product.
Instead, it explains why old-product parity must be preserved while the new
backend is cleaned up and made more durable.

## Current Backend Reality

Today, four portrait-domain slices already exist in executable form under
`topiclab-backend/app/portrait/`:

- `scales`
- `dialogue`
- `portrait_state`
- `prompt_handoff / import_result`

### Current product-facing portrait surface

From a product point of view, today's portrait system is better understood as
four primary capabilities plus a few supporting actions:

1. three direct scale tests
   - `RCSS`
   - `Mini-IPIP`
   - `AMS`
2. one integrated portrait-generation flow
   - interactive portrait dialogue
   - later structured portrait materialization
3. portrait viewing / reading
4. portrait update / regeneration / continued refinement
5. portrait export / download

For backend refactor planning, these should map into a small number of durable
portrait-domain runtimes rather than many UI-glued handlers.

Implemented files:

- `app/portrait/api/scales.py`
- `app/portrait/services/scales_service.py`
- `app/portrait/services/scales_scoring.py`
- `app/portrait/storage/scales_repository.py`
- `app/portrait/runtime/definitions_loader.py`
- `app/portrait/schemas/scales.py`
- `app/portrait/api/dialogue.py`
- `app/portrait/services/dialogue_service.py`
- `app/portrait/services/dialogue_runtime_service.py`
- `app/portrait/services/dialogue_summary_service.py`
- `app/portrait/storage/dialogue_repository.py`
- `app/portrait/schemas/dialogue.py`
- `app/portrait/api/portrait_state.py`
- `app/portrait/services/portrait_state_service.py`
- `app/portrait/storage/portrait_state_repository.py`
- `app/portrait/schemas/portrait_state.py`
- `app/portrait/api/prompt_handoff.py`
- `app/portrait/services/prompt_handoff_service.py`
- `app/portrait/storage/prompt_handoff_repository.py`
- `app/portrait/schemas/prompt_handoff.py`
- `app/portrait/api/import_results.py`
- `app/portrait/services/import_result_service.py`
- `app/portrait/services/import_parse_service.py`
- `app/portrait/storage/import_result_repository.py`
- `app/portrait/schemas/import_results.py`

This means the following are already real:

- stable `/api/v1/scales/...` routes
- canonical scale definitions
- durable scale sessions / answers / results
- server-side scoring
- CLI-compatible runtime behavior
- durable dialogue sessions / transcript messages / derived state
- first `/api/v1/portrait/dialogue/...` routes
- model-backed assistant reply path wired to the existing `AI_GENERATION_*`
  backend config
- a first canonical portrait-state runtime with:
  - current-state reads
  - explicit update materialization
  - durable update events
  - durable version snapshots
  - durable observations
- explicit materialization from:
  - `dialogue_session`
  - `scale_session`
  - `manual`
- a first prompt-handoff runtime with:
  - handoff creation
  - prompt artifact persistence
  - handoff list / reread
  - handoff cancel
- a first import-result runtime with:
  - imported payload persistence
  - deterministic parse runs
  - parsed-result reread
  - `candidate_state_patch`-style parse output
  - automatic materialization into canonical portrait state
- a first unified portrait-session orchestrator with:
  - top-level `start / status / respond / result` routes
  - durable runtime refs and orchestration events
  - routed `respond(...)` paths for:
    - `dialogue`
    - `scales`
    - `prompt_handoff`
    - `import_result`
    - `portrait_state`

What is **not** migrated yet:

- deeper portrait dialogue and generation runtime features
- broader portrait-state orchestration and source integration
- public staging validation for the unified portrait-session routes
- a CLI command surface for prompt handoff / import-result as expert/debug
  commands
- execution logs / runtime traces
- legacy bridge reduction for heavier portrait flows

## Current Correction On Migration Strategy

The next backend phase is now intentionally narrowed:

- stop treating handwritten parity logic as the default path when old portrait
  kernel code already exists
- migrate the accessible old portrait kernel baseline into
  `topiclab-backend/app/portrait/` first
- use the new backend's storage, router, auth, and deployment layers as
  adapters around that copied kernel

The dedicated migration document is:

- `topiclab-backend/docs/portrait-old-kernel-migration-plan.md`

This correction does **not** invalidate the already landed work in:

- `scales`
- `portrait_state`
- `prompt_handoff / import_result`
- unified `portrait_session`
- artifacts / export / publish
- CLI / cloud staging closure

But it does change their role:

- they are supporting rails
- they are not a reason to keep postponing direct old-kernel migration

## Old-kernel equivalence requirements

The historical portrait product in `Resonnet` was not only a set of endpoints.
It encoded a stronger product contract that the refactor should preserve.

The most important old-kernel behaviors were:

1. skill-routed orchestration
   - user intent first mapped to a specific portrait skill
   - each skill dictated collection/update/review behavior
2. block/UI-native interaction protocol
   - one question per turn
   - choice / text / rating / copyable / chart / actions as first-class blocks
3. markdown-profile-centric materialization
   - a canonical profile document still drove parsing, review, and export
4. completeness guarantees
   - missing RCSS / AMS / Mini-IPIP dimensions were not optional forever
   - the system actively forced inference or later completion
5. portrait product surfaces beyond collection
   - AI-memory prompt generation/import
   - review flow
   - update flow
   - forum-profile generation
   - scientist matching / recommendations
   - PDF / image export
   - publish-to-library bridge
   - per-session append-only logs

This means "new backend almost complete" would be false if we only count
runtime slices and ignore these product-level invariants.

The backlog below should therefore be interpreted as:

- durable architecture migration
- while preserving the old portrait product kernel

not as a license to simplify away historical behaviors.

## Current gap versus the old portrait product

Today, the new backend is strongest in:

- durable runtime ownership
- CLI-friendly state machines
- cloud persistence
- unified session orchestration

But compared with the old portrait product, the new backend still lacks full
equivalence in these areas:

- explicit skill-routed portrait orchestration semantics
- full block/UI protocol parity
- review/update/forum-profile product flows
- scientist recommendation runtime
- export/download artifact parity
- publish-to-library parity
- append-only execution and interaction logs at the old product level

So the next implementation phases should be driven by old-kernel equivalence,
not only by infrastructure neatness.

### What "old-kernel parity" concretely still means

After fully rereading the legacy code, prompt policy, skills, template, and
supporting docs, the remaining parity work is not abstract. It specifically
means recovering these historical product contracts on top of the new durable
runtime base:

1. skill-routed portrait policy
   - equivalent ownership for:
     - `collect-basic-info`
     - `infer-profile-dimensions`
     - `review-profile`
     - `update-profile`
     - `generate-ai-memory-prompt`
     - `import-ai-memory-v2`
     - `generate-forum-profile`
     - optional explicit scale-administration skills
2. block/UI protocol parity
   - a backend response contract equivalent to:
     - `ask_choice`
     - `ask_text`
     - `ask_rating`
     - `show_copyable`
     - `show_profile_chart`
     - `show_actions`
   - including the old rule of one interactive question per turn
3. complete portrait guarantee
   - a finished portrait session must not leave core dimensions empty
   - inference and later calibration both need to be supported
4. full derived-product parity
   - forum-profile generation with privacy gating
   - scientist matching / field recommendations
   - PDF / image export
   - publish-to-library side effects
5. old-grade traceability
   - append-only conversation / orchestration logs
   - session reset semantics
   - durable recoverability of in-progress state

This is the correct definition of "backend basically complete" for this domain.
Until these are covered, the new backend should be considered a strong runtime
foundation rather than full old-product replacement.

### Old-kernel-equivalent implementation order

To preserve the old product while still benefiting from the new architecture,
the next build order should change from pure runtime slicing to
product-equivalence slicing:

1. portrait session policy and block contract parity
   - unify `start/respond/status/result` with server-driven next-step payloads
   - reintroduce block-native question and action outputs
   - encode the old skill-routing semantics in the new orchestrator
   - executable sub-order:
     - pass 1a: explicit block contract (`text / choice / text_input / rating / copyable / actions`)
     - pass 1b: top-level session responses expose `blocks`, `interactive_block`, and `policy`
     - pass 1c: first legacy-compatible skill flow under a compatibility mode
   - first executable batch now landed under `mode=legacy_product`
2. AI-memory-first portrait build parity
   - make prompt generation and import-result the canonical build-first path
   - ensure basic-info collection, current-needs capture, and forced inference
     match the old product
   - executable sub-order:
     - pass 2a: `ai_memory` prompt kind in the new prompt-handoff runtime
     - pass 2b: deterministic AI-memory import parsing into canonical `profile`
     - pass 2c: continue collection from the first still-missing core field
3. review/update/reset/history parity
   - dimension-by-dimension review
   - targeted updates
   - explicit reset and recovery semantics
   - current factual status:
     - first executable review/update/history pass is now landed
     - review supports summary + chart + update actions
     - targeted updates cover:
       - basic identity
       - technical capability
       - process ability
       - current needs
     - session history now has a top-level backend route
   - still remaining:
     - deeper old-product review semantics
     - richer history / replay surfaces
4. forum/scientist/export/publish parity
   - derived forum profile
   - scientist recommendation runtime
   - PDF/image export runtime
   - library publish bridge
5. harden logs/traces and migration bridges

### What was actually completed in the latest parity pass

This backlog is intentionally updated with factual progress only.

Just completed:

- `collect-basic-info` direct path first full pass
  - research stage
  - fields
  - method
  - institution
  - advisor/team
  - academic network
  - six process-ability ratings + notes
  - tool stack
  - representative outputs
  - current-needs sequence
- deterministic `infer-profile-dimensions` chained automatically after
  collection completeness
- first `review-profile` parity
- first `update-profile` parity
- top-level `/api/v1/portrait/sessions/{session_id}/history`

Now started from the old-product-equivalence tail:

- forum-profile generation first backend batch
- scientist matching / field recommendation first backend batch
- export / download first backend batch
- publish-to-twin first backend batch

Still remaining after that first batch:

- richer wording / rendering quality parity
- stronger PDF/image runtime hardening across deployment environments
- tighter publish bridge semantics where old library surfaces still need to
  read the new outputs
- preserve old-grade traceability
- only then reduce `Resonnet` ownership aggressively

### Newly landed first artifact/twin batch

This batch intentionally moved the remaining old product surfaces onto a clean
projection + artifact model instead of rebuilding old file-cache behavior.

Implemented:

- canonical projection layer from `portrait_state`
  - `app/portrait/services/portrait_projection_service.py`
- durable artifact persistence
  - `portrait_artifacts` table
  - `app/portrait/storage/portrait_artifact_repository.py`
  - `app/portrait/services/portrait_artifact_service.py`
- forum profile generation
  - `app/portrait/services/portrait_forum_service.py`
- scientist matching / field recommendations
  - `app/portrait/services/portrait_scientist_service.py`
- structured / markdown / HTML export
  - `app/portrait/services/portrait_export_service.py`
- publish into twin runtime plus legacy-compatible `digital_twins` sync
  - `app/portrait/services/portrait_publish_service.py`
- new backend routes
  - `/api/v1/portrait/forum/generate`
  - `/api/v1/portrait/scientists/famous`
  - `/api/v1/portrait/scientists/field`
  - `/api/v1/portrait/export/structured`
  - `/api/v1/portrait/export/profile-markdown`
  - `/api/v1/portrait/export/forum-markdown`
  - `/api/v1/portrait/export/profile-html`
  - `/api/v1/portrait/export/profile-pdf`
  - `/api/v1/portrait/export/profile-image`
  - `/api/v1/portrait/publish`
  - `/api/v1/portrait/artifacts`

What this first batch still does not claim:

- pixel-perfect parity with the old PDF/image styling
- full old library/expert-import semantics
- rich canonical-state filling from very short dialogue-only sessions

### Newly landed unified-session product-action parity

The first artifact/twin batch is no longer only exposed as standalone routes.
It is now also wired back into the unified top-level portrait-session loop.

Implemented:

- unified `respond(...)` routing for:
  - `forum:generate`
  - `scientist:famous`
  - `scientist:field`
  - `export:structured`
  - `export:profile_markdown`
  - `export:forum_markdown`
  - `publish:brief`
  - `publish:full`
- unified runtime refs for generated artifacts and publish side effects
- review-summary parity path can now trigger the same product actions and then
  return to the review flow
- `TopicLab-CLI` now exposes a minimal top-level portrait entry that can call
  these capabilities through:
  - `topiclab portrait start`
  - `topiclab portrait respond`
  - `topiclab portrait status`
  - `topiclab portrait result`
  - `topiclab portrait resume`
  - `topiclab portrait history`
  - `topiclab portrait reset`
  - `topiclab portrait export`

Cloud closure revalidated on 2026-04-11:

- local CLI build -> AutoDL HTTPS staging URL -> cloud backend -> cloud DB/logs
- validated top-level session:
  - `pts_558f1c332faa41b9`
- validated generated refs:
  - `forum_artifact = par_6dd696c0944d43b1`
  - `scientist_famous_artifact = par_9d14793069c642f6`
  - `publish_brief_artifact = par_af5569b6fa1e4cc3`
  - `published_twin = twin_8a66279ee612a3a0`

This means the remaining parity gap is no longer "these product surfaces are
missing from the new backend". The remaining gap is that their underlying
canonical portrait state can still be too thin if the session has not yet
collected enough durable profile facts.

### First executable batch of skill policy + block parity

The first parity batch is intentionally narrow and compatibility-safe.

It does **not** yet claim that the whole old portrait product has been
recovered. It proves that the new durable portrait runtime can already host
the old product kernel semantics instead of only raw runtime transitions.

Implemented in this batch:

- explicit block helpers in `app/portrait/runtime/block_protocol.py`
- a legacy-compatible skill-policy layer in
  `app/portrait/services/portrait_skill_policy_service.py`
- `start(mode=legacy_product)` now returns:
  - privacy / welcome text
  - AI-memory-vs-direct start-method choice
- the first direct `collect-basic-info` sequence now exists in unified session:
  - research stage
  - research field / direction / cross-discipline note
  - method paradigm
  - institution
  - academic network
- the first AI-memory-first branch now exists in unified session:
  - create prompt handoff with `prompt_kind=ai_memory`
  - return a copyable AI-memory prompt block
  - accept pasted AI output back into the same top-level session
  - parse imported A/C answers into canonical portrait state
- scale question steps now expose block-style rating payloads

What this first batch still leaves for later parity:

- the rest of `collect-basic-info`
- `infer-profile-dimensions`
- `review-profile`
- `update-profile`
- forum profile generation
- scientist matching
- export / publish
- old-grade append-only logs beyond current orchestration events

### Recommended runtime grouping in the new backend

Even though the current user-facing product feels like "three scales + one
portrait generator + view/update/download", the new backend should group those
capabilities into four durable runtime families:

1. `scales runtime`
   - owns the three direct tests
2. `dialogue and portrait-generation runtime`
   - owns interactive portrait-building conversation
3. `portrait state runtime`
   - owns current portrait view, update, and version history
4. `portrait artifact runtime`
   - owns export / download artifacts and related traceability

This grouping keeps the backend decoupled without losing the product-level
mental model.

## Priority Order

Recommended backend-only build order:

1. finish hardening the `scales` slice as the reference runtime pattern
2. harden and extend the portrait dialogue runtime
3. harden and extend prompt handoff and import-result runtime
4. harden and extend canonical portrait state + version history
5. build durable execution logs and traces
6. build legacy bridge / coexistence support only where needed

## Slice 0. Scale Runtime Hardening

This slice already exists, but it is not the whole portrait backend.

### Goal

Turn `scales` into the stable reference pattern for later portrait slices.

### API

Already present:

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

Still recommended on the backend side:

- add more explicit operational logging around finalize and result read paths
- decide whether admin/internal read endpoints are needed for debugging
- decide whether bridge reads from legacy `scales.json` are needed during
  migration

### Services

Already present:

- `app/portrait/services/scales_service.py`
- `app/portrait/services/scales_scoring.py`

Still recommended:

- a result-summary builder if more normalized portrait-consumer output is
  needed
- a migration/bridge helper if legacy scale coexistence becomes necessary

### Storage

Already present:

- `app/portrait/storage/scales_repository.py`

### Schemas

Already present:

- `app/portrait/schemas/scales.py`

### Tables

Already present:

- `scale_sessions`
- `scale_session_answers`
- `scale_results`

## Slice 1. Portrait Dialogue Runtime

### Status

First executable batch implemented.

### Goal

Move the lightweight portrait conversation flow out of legacy `Resonnet`
working state and into durable portrait-domain runtime ownership.

### API

Recommended new routes:

- `POST /api/v1/portrait/dialogue/sessions`
- `GET /api/v1/portrait/dialogue/sessions/{session_id}`
- `GET /api/v1/portrait/dialogue/sessions/{session_id}/messages`
- `POST /api/v1/portrait/dialogue/sessions/{session_id}/messages`
- `POST /api/v1/portrait/dialogue/sessions/{session_id}/close`
- `GET /api/v1/portrait/dialogue/sessions/{session_id}/derived-state`

Optional later routes:

- `POST /api/v1/portrait/dialogue/sessions/{session_id}/resume`
- `POST /api/v1/portrait/dialogue/sessions/{session_id}/summarize`

### Services

Recommended new files:

- `app/portrait/services/dialogue_service.py`
- `app/portrait/services/dialogue_runtime_service.py`
- `app/portrait/services/dialogue_summary_service.py`

Responsibilities:

- create and resume dialogue sessions
- persist transcript messages
- maintain session status
- produce derived runtime state used by later portrait updates
- call the configured generation model to produce backend assistant replies

### Storage

Recommended new files:

- `app/portrait/storage/dialogue_repository.py`

Responsibilities:

- session row CRUD
- message append/list
- derived-state persistence

### Schemas

Recommended new files:

- `app/portrait/schemas/dialogue.py`

Suggested schema areas:

- session create request
- message append request
- session status response
- transcript item response
- derived-state response

### Tables

Recommended new tables:

- `portrait_dialogue_sessions`
- `portrait_dialogue_messages`
- `portrait_dialogue_states`

Suggested minimum columns:

- `portrait_dialogue_sessions`
  - `session_id`
  - `user_id`
  - `actor_type`
  - `actor_id`
  - `status`
  - `created_at`
  - `updated_at`
  - `closed_at`

- `portrait_dialogue_messages`
  - `message_id`
  - `session_id`
  - `role`
  - `content_text`
  - `content_json`
  - `source`
  - `created_at`

- `portrait_dialogue_states`
  - `session_id`
  - `last_message_id`
  - `derived_state_json`
  - `updated_at`

## Slice 2. Prompt Handoff Runtime

### Status

First executable batch implemented.

### Goal

Turn the current prompt-export flow into a durable backend contract instead of
UI-only glue.

### API

Recommended new routes:

- `POST /api/v1/portrait/prompt-handoffs`
- `GET /api/v1/portrait/prompt-handoffs/{handoff_id}`
- `GET /api/v1/portrait/prompt-handoffs`
- `POST /api/v1/portrait/prompt-handoffs/{handoff_id}/cancel`

### Services

Recommended new files:

- `app/portrait/services/prompt_handoff_service.py`
- `app/portrait/services/prompt_artifact_service.py`

Already implemented in the first batch:

- `app/portrait/services/prompt_handoff_service.py`

Responsibilities:

- create a prompt handoff request from portrait context
- persist generated prompt artifacts
- track handoff status

### Storage

Recommended new files:

- `app/portrait/storage/prompt_handoff_repository.py`

Already implemented in the first batch:

- `app/portrait/storage/prompt_handoff_repository.py`

### Schemas

Recommended new files:

- `app/portrait/schemas/prompt_handoff.py`

Already implemented in the first batch:

- `app/portrait/schemas/prompt_handoff.py`

Suggested schema areas:

- handoff create request
- generated artifact response
- handoff status response

### Tables

Recommended new tables:

- `portrait_prompt_handoffs`
- `portrait_prompt_artifacts`

Already implemented in the first batch:

- `portrait_prompt_handoffs`
- `portrait_prompt_artifacts`

Suggested minimum columns:

- `portrait_prompt_handoffs`
  - `handoff_id`
  - `user_id`
  - `dialogue_session_id`
  - `portrait_state_id`
  - `status`
  - `requested_at`
  - `completed_at`

- `portrait_prompt_artifacts`
  - `artifact_id`
  - `handoff_id`
  - `artifact_type`
  - `content_text`
  - `content_json`
  - `created_at`

## Slice 3. Import-Result Runtime

### Status

First executable batch implemented.

### Goal

Turn pasted external-AI results into traceable backend-owned runtime events.

### API

Recommended new routes:

- `POST /api/v1/portrait/import-results`
- `GET /api/v1/portrait/import-results/{import_id}`
- `POST /api/v1/portrait/import-results/{import_id}/parse`
- `GET /api/v1/portrait/import-results/{import_id}/parsed`

Optional later routes:

- `POST /api/v1/portrait/import-results/{import_id}/retry`
- `POST /api/v1/portrait/import-results/{import_id}/apply`

### Services

Recommended new files:

- `app/portrait/services/import_result_service.py`
- `app/portrait/services/import_parse_service.py`

Already implemented in the first batch:

- `app/portrait/services/import_result_service.py`
- `app/portrait/services/import_parse_service.py`

Responsibilities:

- persist pasted payloads
- track import status
- parse imported text into normalized portrait-relevant structures
- prepare inputs for portrait update events

### Storage

Recommended new files:

- `app/portrait/storage/import_result_repository.py`

Already implemented in the first batch:

- `app/portrait/storage/import_result_repository.py`

### Schemas

Recommended new files:

- `app/portrait/schemas/import_results.py`

Already implemented in the first batch:

- `app/portrait/schemas/import_results.py`

Suggested schema areas:

- pasted payload request
- import status response
- parsed result response

### Tables

Recommended new tables:

- `portrait_import_results`
- `portrait_import_parse_runs`

Already implemented in the first batch:

- `portrait_import_results`
- `portrait_import_parse_runs`

Suggested minimum columns:

- `portrait_import_results`
  - `import_id`
  - `user_id`
  - `handoff_id`
  - `source_type`
  - `payload_text`
  - `payload_json`
  - `status`
  - `created_at`
  - `updated_at`

- `portrait_import_parse_runs`
  - `parse_run_id`
  - `import_id`
  - `parser_version`
  - `status`
  - `parsed_output_json`
  - `error_text`
  - `created_at`

## Slice 4. Canonical Portrait State And Version History

### Status

First executable batch implemented.

### Goal

Give the new backend a durable answer to:

- what is the current portrait?
- what changed?
- how did it change over time?

### API

Recommended new routes:

- `GET /api/v1/portrait/state/current`
- `GET /api/v1/portrait/state/versions`
- `GET /api/v1/portrait/state/versions/{version_id}`
- `POST /api/v1/portrait/state/updates`
- `GET /api/v1/portrait/state/updates/{update_id}`
- `GET /api/v1/portrait/state/observations`

Optional later routes:

- `POST /api/v1/portrait/state/rebuild`
- `GET /api/v1/portrait/state/observations`

### Services

Recommended new files:

- `app/portrait/services/portrait_state_service.py`
- `app/portrait/services/portrait_update_service.py`
- `app/portrait/services/portrait_versioning_service.py`

Responsibilities:

- materialize current portrait state
- write update events from scales/dialogue/import inputs
- snapshot or delta-store portrait changes over time

Current first-batch implemented file:

- `app/portrait/services/portrait_state_service.py`

### Storage

Recommended new files:

- `app/portrait/storage/portrait_state_repository.py`
- `app/portrait/storage/portrait_update_repository.py`

Current first-batch implemented file:

- `app/portrait/storage/portrait_state_repository.py`

### Schemas

Recommended new files:

- `app/portrait/schemas/portrait_state.py`
- `app/portrait/schemas/portrait_updates.py`

Current first-batch implemented file:

- `app/portrait/schemas/portrait_state.py`

Suggested schema areas:

- current portrait response
- version snapshot response
- update event response
- observation response

### Tables

Recommended new tables:

- `portrait_current_states`
- `portrait_update_events`
- `portrait_version_snapshots`
- `portrait_observations`

Suggested minimum columns:

- `portrait_current_states`
  - `portrait_state_id`
  - `user_id`
  - `state_json`
  - `source_summary_json`
  - `updated_at`

- `portrait_update_events`
  - `update_id`
  - `user_id`
  - `source_type`
  - `source_id`
  - `change_summary_json`
  - `created_at`

- `portrait_version_snapshots`
  - `version_id`
  - `user_id`
  - `portrait_state_id`
  - `snapshot_json`
  - `created_at`

- `portrait_observations`
  - `observation_id`
  - `user_id`
  - `source_type`
  - `source_id`
  - `observation_json`
  - `created_at`

Current first-batch support:

- explicit update sources:
  - `manual`
  - `dialogue_session`
  - `scale_session`
- current state aggregation is explicit, not automatic
- the next hardening step is to decide where automatic materialization should
  happen without creating hidden cross-slice coupling

## Slice 4.5. Unified Portrait Session Orchestrator

### Status

First executable backend batch implemented.

### Goal

Create one agent-facing top-level session layer above the slice runtimes so the
future product loop can converge toward:

- `start`
- `respond`
- `status`
- `result`

without making callers understand `scales`, `dialogue`, `prompt_handoff`,
`import_result`, and `portrait_state` separately.

### API

Current first-batch routes:

- `POST /api/v1/portrait/sessions`
- `GET /api/v1/portrait/sessions/{session_id}`
- `POST /api/v1/portrait/sessions/{session_id}/respond`
- `GET /api/v1/portrait/sessions/{session_id}/result`

Current supported input families:

- `text`
- `choice`
- `external_text`
- `external_json`
- `confirm`

Current supported high-level choice families:

- `scale:<id>`
- numeric scale values
- `prompt_handoff`
- `forum:generate`
- `scientist:famous`
- `scientist:field`
- `export:structured`
- `export:profile_markdown`
- `export:forum_markdown`
- `publish:brief`
- `publish:full`

Still recommended later:

- top-level `resume` semantics
- top-level `result` normalization across more slice combinations

### Services

Current first-batch implemented files:

- `app/portrait/services/portrait_session_service.py`
- `app/portrait/services/portrait_orchestration_service.py`

Responsibilities already implemented:

- create durable top-level portrait sessions
- return normalized current step instructions
- route `respond(text)` into:
  - `dialogue`
  - then `portrait_state`
- route `respond(choice="scale:<id>")` into:
  - `scales`
  - then `portrait_state`
- route `respond(choice="prompt_handoff")` into:
  - `prompt_handoff`
- route product-action choices into:
  - `forum`
  - `scientist`
  - `export`
  - `publish`
- route `respond(external_text|external_json)` into:
  - `import_result`
  - then `portrait_state`
- route `respond(confirm)` into session completion
- keep runtime refs and event history
- keep generated artifact refs and publish/twin refs inside the same top-level
  session

Still recommended later:

- unify result projection and progress calculation
- add richer orchestration policies for stage switching
- improve canonical-state completeness before forum/export/publish so outputs
  stay meaningful even after very short conversations

### Storage

Current first-batch implemented file:

- `app/portrait/storage/portrait_session_repository.py`

Responsibilities already implemented:

- session row CRUD
- runtime-ref upsert/list
- event insertion/count

### Schemas

Current first-batch implemented file:

- `app/portrait/schemas/session.py`

Current schema areas:

- start request
- respond request
- normalized input-family validation

### Tables

Current first-batch implemented tables:

- `portrait_sessions`
- `portrait_session_runtime_refs`
- `portrait_session_events`

Suggested next hardening step:

- decide whether a separate durable `portrait_session_progress` object is
  needed or whether current-step columns + event history are sufficient

## Slice 5. Execution Logs And Runtime Traces

### Goal

Persist enough runtime detail for debugging, replay, analytics, and future
portrait-memory features.

### API

Public read APIs should stay minimal at first.

Recommended initial backend routes:

- `GET /api/v1/portrait/ops/logs/{flow_id}`
- `GET /api/v1/portrait/ops/traces/{trace_id}`

These may remain internal/admin-only at first.

### Services

Recommended new files:

- `app/portrait/services/execution_log_service.py`
- `app/portrait/services/runtime_trace_service.py`

Responsibilities:

- write step-level execution records
- correlate logs across scales / dialogue / handoff / import / update flows
- support debugging and replay

### Storage

Recommended new files:

- `app/portrait/storage/execution_log_repository.py`

### Schemas

Recommended new files:

- `app/portrait/schemas/execution_logs.py`

### Tables

Recommended new tables:

- `portrait_execution_logs`
- `portrait_runtime_traces`

Suggested minimum columns:

- `portrait_execution_logs`
  - `log_id`
  - `user_id`
  - `flow_type`
  - `flow_id`
  - `level`
  - `event_type`
  - `payload_json`
  - `created_at`

- `portrait_runtime_traces`
  - `trace_id`
  - `user_id`
  - `flow_type`
  - `flow_id`
  - `trace_json`
  - `created_at`

## Slice 6. Legacy Bridge And Migration Support

### Goal

Reduce backend truth still owned by legacy `Resonnet` without requiring a
big-bang replacement.

### API

Prefer to keep legacy façade routes where needed and bridge internally, rather
than inventing new user-facing compatibility routes first.

### Services

Recommended new files:

- `app/portrait/services/legacy_bridge_service.py`
- `app/portrait/services/legacy_backfill_service.py`

Responsibilities:

- dual-read / dual-write where temporarily necessary
- backfill old portrait-derived data into the new durable model
- record migration progress

### Storage

Recommended new files:

- `app/portrait/storage/legacy_bridge_repository.py`

### Schemas

Recommended new files:

- `app/portrait/schemas/legacy_bridge.py`

### Tables

Only add durable tables here if migration state truly needs to survive process
restarts.

Recommended optional tables:

- `portrait_legacy_backfill_jobs`
- `portrait_legacy_bridge_events`

## Definition Of "Backend Done Enough"

Ignoring frontend migration, the portrait backend should be considered
substantially complete only when:

1. `scales`, `dialogue`, `prompt handoff`, and `import-result` all have
   durable portrait-domain ownership in `topiclab-backend/app/portrait/`
2. the backend owns a canonical current portrait state and version history
3. the backend owns one unified portrait-session orchestration layer above the
   slice runtimes
4. important portrait flows leave durable execution traces
5. legacy `Resonnet` ownership is reduced to compatibility rather than primary
   truth

Until then, the new portrait backend should be treated as:

- successfully started
- already real for `scales`
- already real for first-batch `dialogue`, `portrait_state`, `prompt/import`,
  and unified `portrait_session` slices
- not yet complete as the full replacement for the historical portrait system
