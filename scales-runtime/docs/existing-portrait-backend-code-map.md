# Existing Portrait Backend Code Map

## Purpose

Before adding portrait CLI support, we need a factual map of what the existing
portrait backend already is.

This document records the current code reality across:

- `Resonnet`
- `topiclab-backend`
- the current frontend wiring
- the new `scales-runtime` work

The goal is to answer one practical question:

- which backend code already owns which part of the portrait system
- and therefore where CLI work should attach first

## Executive Summary

The historical portrait system is not owned by one single backend.

It is currently split into three backend layers:

### 1. `Resonnet` owns the legacy portrait-builder runtime

This includes:

- portrait chat
- block chat
- session creation and reset
- profile markdown generation
- forum-profile generation
- structured parsing
- scientist matching
- export/download
- legacy scale submission persistence
- publish-to-library bridge

In practice, the old portrait product runtime lives here.

### 2. `topiclab-backend` already owns account-linked portrait persistence

This includes:

- `digital_twins`
- active twin materialization
- twin snapshots
- OpenClaw key issuance
- OpenClaw twin runtime endpoints

In practice, user-account-bound portrait ownership already lives here.

### 3. `topiclab-backend` now also contains the new scale runtime

This includes:

- `/api/v1/scales/...`
- canonical session lifecycle for the new scale runtime
- server-side scoring
- result persistence

This is the new path being built for CLI-friendly and agent-friendly scale
interaction.

## Frontend Reality

The current portrait frontend still targets legacy profile-helper routes for the
main portrait experience.

Primary file:

- `frontend/src/modules/profile-helper/profileHelperApi.ts`

Current calls include:

- `GET /api/profile-helper/session`
- `POST /api/profile-helper/chat`
- `POST /api/profile-helper/chat/blocks`
- `GET /api/profile-helper/profile/{session_id}`
- `GET /api/profile-helper/profile/{session_id}/structured`
- `POST /api/profile-helper/scales/submit`
- `GET /api/profile-helper/profile/{session_id}/scientists/famous`
- `GET /api/profile-helper/profile/{session_id}/scientists/field`
- `POST /api/profile-helper/publish-to-library`
- `POST /api/profile-helper/session/reset/{session_id}`

This means the current web portrait UI is still mainly driven by `Resonnet`.

## Resonnet: Existing Portrait Runtime

### Router registration

Primary file:

- `Resonnet/main.py`

Relevant registration:

- `app.include_router(profile_helper_router.router, prefix="/profile-helper", tags=["profile-helper"])`

This is the main historical backend entry for portrait features.

### Main API surface

Primary file:

- `Resonnet/app/api/profile_helper.py`

This file currently owns these portrait-facing routes:

- `/profile-helper/session`
- `/profile-helper/chat`
- `/profile-helper/chat/blocks`
- `/profile-helper/scales/submit`
- `/profile-helper/scales/{session_id}`
- `/profile-helper/publish-to-library`
- `/profile-helper/session/reset/{session_id}`
- profile export/download endpoints
- profile/scientist endpoints

This is the best single file to treat as the old portrait backend façade.

### Session and filesystem working state

Primary file:

- `Resonnet/app/services/profile_helper/sessions.py`

What it owns:

- in-memory session registry
- session TTL / cleanup
- loading or creating a profile session
- reading and writing `profile.md`
- reading and writing `forum_profile.md`
- reading and writing legacy `scales.json`
- message-history persistence
- auto-sync to `digital_twins`
- auto-write of `user_agents/my_twin`

Important architectural fact:

`sessions.py` is where the historical portrait runtime mixes:

- transient session state
- filesystem cache
- scale storage
- account sync side effects

So this is the most important legacy coupling point.

### Chat and portrait generation

Primary files:

- `Resonnet/app/services/profile_helper/agent.py`
- `Resonnet/app/services/profile_helper/block_agent.py`

What they own:

- the interactive portrait conversation
- prompt/tool orchestration
- block-based streaming output
- profile content generation in session context

For current portrait building, this is the generation engine.

### Skill-driven orchestration is the real old kernel

Primary files:

- `Resonnet/app/services/profile_helper/prompts.py`
- `Resonnet/app/services/profile_helper/tools.py`
- `Resonnet/libs/profile_helper/skills/*/SKILL.md`

This old portrait product was not merely "chat plus scales".

Its real orchestration kernel was:

- the system prompt forced the agent to call `read_skill(...)` first before
  acting
- each user intent mapped to a specific skill playbook
- the skill playbook then determined:
  - what questions to ask
  - which UI tool to use
  - when to write profile data
  - when to infer missing dimensions
  - when to review / update / export / publish

Historically important skill inventory:

- `collect-basic-info`
- `administer-rcss`
- `administer-ams`
- `administer-mini-ipip`
- `infer-profile-dimensions`
- `review-profile`
- `update-profile`
- `generate-ai-memory-prompt`
- `import-ai-memory`
- `import-ai-memory-v2`
- `generate-forum-profile`
- `modify-profile-schema`

This means the old user-facing product contract was actually:

- a skill-routed portrait collection workflow
- backed by a block/UI protocol
- backed by a markdown portrait schema
- backed by auto-save, export, scientist matching, and publish side effects

If the refactor is meant to preserve the old product kernel, this skill-driven
behavior must be treated as first-class migration scope rather than as optional
prompt sugar.

### Block UI protocol was also part of the old kernel

Primary file:

- `Resonnet/app/services/profile_helper/block_agent.py`

The block agent exposed a structured UI protocol, not just free-form text:

- `ask_choice`
- `ask_text`
- `ask_rating`
- `show_copyable`
- `show_profile_chart`
- `show_actions`

It also contained fast paths and non-LLM shortcuts for:

- welcome/onboarding
- AI-memory prompt generation

So the old portrait system was explicitly designed around:

- one-question-per-turn collection
- UI-native question types
- display blocks and action buttons
- copyable prompt handoff surfaces

This is broader than the current minimal `respond(text|choice|external_text)`
session loop.

### Old portrait product behaviors that were more than data storage

The legacy portrait system already bundled several derived/product behaviors
around the generated profile:

- AI-memory prompt generation and import
- automatic completeness checks and forced inference of missing dimensions
- review flow over the whole portrait
- update flow over any portrait field
- forum-profile generation with privacy exposure decisions
- scientist matching and field recommendations
- PDF/image export
- publish-to-library bridge and account sync

### Full old portrait product loop after file-by-file reading

After fully rereading the legacy code, skills, prompts, template, and docs, the
real old product loop is more specific than "chat plus scales":

1. welcome and privacy notice
   - block fast path showed the privacy notice first
   - the user was explicitly asked whether to start from AI memory or direct
     collection
2. AI-memory-first or direct basic collection
   - `collect-basic-info` did not begin by asking for a name
   - it first asked whether to use remembered context from another AI product
   - it then collected:
     - basic identity
     - ability/process self-ratings
     - current needs
   - it incrementally wrote profile content after each batch
3. forced full-profile completion
   - the product contract was not "optional incomplete profile forever"
   - after basic info, the system forced completion of RCSS / AMS / Mini-IPIP
     either by:
     - immediate inference, or
     - later calibration through formal scales
4. review and update
   - the whole portrait could be reviewed dimension by dimension
   - any field could be updated later
   - remeasurement of a scale was an explicit update path
5. derived product outputs
   - forum-profile generation with privacy scope selection
   - scientist matching and same-field recommendations
   - PDF export
   - long-image export
   - publish-to-library and `my_twin` sync
6. durable trace and recovery
   - append-only JSONL session logs
   - session reset / conversation reset
   - message-history persistence
   - filesystem persistence plus account sync side effects

This means the historical portrait product was a complete, skill-routed product
workflow rather than a thin runtime shell.

### Full legacy API surface that mattered to the product

The old façade in `Resonnet/app/api/profile_helper.py` exposed all of the
following product-facing routes:

- `GET /profile-helper/session`
- `POST /profile-helper/chat`
- `POST /profile-helper/chat/blocks`
- `GET /profile-helper/profile/{session_id}`
- `GET /profile-helper/chat-history/{session_id}`
- `GET /profile-helper/profile/{session_id}/structured`
- `GET /profile-helper/profile/{session_id}/scientists/famous`
- `GET /profile-helper/profile/{session_id}/scientists/field`
- `GET /profile-helper/download/{session_id}`
- `GET /profile-helper/export/{session_id}/pdf`
- `GET /profile-helper/export/{session_id}/image`
- `GET /profile-helper/download/{session_id}/forum`
- `POST /profile-helper/scales/submit`
- `GET /profile-helper/scales/{session_id}`
- `POST /profile-helper/publish-to-library`
- `POST /profile-helper/session/reset/{session_id}`

If the new architecture claims "old product parity", it eventually needs
equivalent ownership for this full surface, not only for scale sessions and
dialogue sessions.

### Old-kernel invariants that should be treated as non-negotiable

The following historical behaviors are core invariants rather than optional UI
details:

1. skill-first orchestration
   - user intent was routed to a named skill with an explicit playbook
2. block-native interaction protocol
   - one interactive question per turn
   - explicit support for:
     - `ask_choice`
     - `ask_text`
     - `ask_rating`
     - `show_copyable`
     - `show_profile_chart`
     - `show_actions`
3. complete portrait guarantee
   - after build completion, no core profile dimensions were allowed to remain
     blank
4. current-needs ownership
   - `current needs` was part of the portrait kernel, not a side note
   - it affected later interpretation and support behavior
5. AI-memory import as a first-class path
   - both prompt generation and import/parsing were part of the default product
     flow
6. optional scale calibration over an already-complete inferred portrait
   - scale measurement was an improvement path, not the only path to completion
7. derived outputs and publication side effects
   - forum profile
   - scientist matching
   - export/download
   - publish-to-library
8. append-only traceability
   - per-session logs and recoverable working state were part of the product
     contract
- append-only per-session conversation analytics logs

These were product behaviors, not just implementation details.

Therefore, "full migration" should mean preserving these capabilities under the
new backend architecture, even if the runtime/storage model changes.

### Structured parsing

Primary file:

- `Resonnet/app/services/profile_helper/profile_parser.py`

What it owns:

- converting generated markdown portrait into structured JSON
- parsing identity, capability, needs, cognitive style, motivation, personality,
  and interpretation sections

This is the bridge from generated markdown into frontend-renderable structured
portrait data.

### Scientist matching

Primary files:

- `Resonnet/app/services/profile_helper/scientist_match.py`
- `Resonnet/app/services/profile_helper/scientists_db.py`

What they own:

- matching the current portrait to predefined scientists
- producing top-3 match output
- producing scatter-plot data
- field recommendations
- in-session and filesystem caching of scientist results

This is already a real portrait-analysis submodule, not just UI glue.

### Export and sharing

Primary file:

- `Resonnet/app/services/profile_helper/export_service.py`

What it owns:

- exporting profile markdown to PDF
- exporting profile markdown to image

This supports the current share/export surfaces.

### Publish to library bridge

Primary path:

- `Resonnet/app/api/profile_helper.py` → `publish_to_library(...)`

What it does:

- chooses brief/full content
- imports a forum-style profile into the experts library
- writes a local `my_twin` agent workspace
- calls account sync to TopicLab-side persistence

So this is the historical bridge from portrait generation into the account-owned
digital-twin layer.

## topiclab-backend: Existing Portrait Persistence And Twin Runtime

### Backend registration

Primary file:

- `topiclab-backend/main.py`

Relevant routers:

- `auth_router`
- `openclaw_twin_runtime_router`
- `scales_router`

This shows that the account service already contains twin and scale ownership.

### Account-linked digital-twin persistence

Primary file:

- `topiclab-backend/app/api/auth.py`

Relevant routes include:

- `POST /auth/digital-twins/upsert`
- `GET /auth/digital-twins`
- `GET /auth/digital-twins/{agent_name}`
- `GET /auth/digital-twins/by-user/{user_id}`
- `GET /auth/openclaw-key`
- `POST /auth/openclaw-key`

What these routes own:

- storing account-linked portrait/twin records
- reading twin detail
- exposing bind key / bootstrap path
- letting Resonnet recover the latest profile markdown by user id

Important architectural fact:

Even before the new CLI work, TopicLab-side account state already owns the
long-lived portrait/twin records.

### Active twin and snapshots runtime

Primary file:

- `topiclab-backend/app/services/twin_runtime.py`

What it owns:

- `twin_core`
- `twin_snapshots`
- creating/updating the active twin for a user
- scene overlays
- versioning
- backfill from legacy digital twin data

This is the durable runtime side of the profile after it leaves the temporary
portrait-building session.

### OpenClaw-facing twin runtime

Primary file:

- `topiclab-backend/app/api/openclaw_twin_runtime.py`

What it owns:

- runtime-profile retrieval
- observation writing
- runtime-state patching
- active twin lookup under OpenClaw auth

This is already a CLI/agent-facing runtime for twins, but it is not the same as
the portrait-building flow.

It is downstream of portrait creation.

### Database bootstrap

Primary file:

- `topiclab-backend/app/storage/database/postgres_client.py`

This file already initializes:

- `users`
- auth tables
- digital twin related tables
- and now the new scale-runtime tables

So it is the correct place to own new durable portrait-domain tables when they
need to become account-level runtime data.

## Portrait User Data Map

If we ask, "What portrait-related data does one user have today?", the factual
answer is: it is split between filesystem working state in `Resonnet` and
account-bound persistent state in `topiclab-backend`.

### 1. Account identity data

Primary store:

- `topiclab-backend` database

Primary table:

- `users`

Fields include:

- `id`
- `phone`
- `password`
- `username`
- `handle`
- guest-related fields

This is durable account identity state, not portrait content itself.

### 2. Legacy portrait-builder working session data

Primary owner:

- `Resonnet/app/services/profile_helper/sessions.py`

Working-state model:

- in-memory `_sessions`
- TTL cleanup
- rebuilt from disk when possible

This state contains:

- `session_id`
- `user_id`
- `messages`
- `profile`
- `forum_profile`
- `scales`
- timestamps

Persistence behavior:

- **not fully durable by itself**
- session memory is transient
- but several fields are mirrored to disk

### 3. Filesystem portrait working cache

Primary owner:

- `Resonnet/app/services/profile_helper/sessions.py`
- path helpers from `Resonnet/app/core/config.py`

Filesystem roots:

- anonymous portrait working files:
  - `workspace/profile_helper/profiles/`
- logged-in user portrait working files:
  - `workspace/users/{user_id}/profile/`
- user agent workspace:
  - `workspace/users/{user_id}/agents/`

Persisted files currently include:

- `profile.md`
- `forum_profile.md`
- `messages.json`
- `scales.json`
- anonymous `messages-{sid}.json`
- anonymous `*-{sid}.md` portrait files

Important fact:

This is the historical "working memory" of the portrait builder. It is durable
on disk, but not normalized as account-owned runtime data.

### 4. Legacy scale payloads

Primary owner:

- `Resonnet/app/api/profile_helper.py`
- `Resonnet/app/services/profile_helper/sessions.py`

Legacy saved payload per scale includes:

- `answers`
- `scores`
- `result_summary`
- `completed_at`

Persistence behavior:

- saved into the portrait working session
- for logged-in users, also written to `scales.json`

This is the old scale submodule that the new runtime is replacing.

### 5. Account-bound digital twin record

Primary owner:

- `topiclab-backend/app/api/auth.py`

Primary table:

- `digital_twins`

Persisted fields include:

- `user_id`
- `agent_name`
- `display_name`
- `expert_name`
- `visibility`
- `exposure`
- `session_id`
- `source`
- `role_content`
- timestamps

This is the durable account-side twin/profile record that Resonnet syncs into.

### 6. Active twin runtime and history

Primary owner:

- `topiclab-backend/app/services/twin_runtime.py`

Primary tables:

- `twin_core`
- `twin_snapshots`
- `twin_scene_overlays`
- `twin_runtime_states`
- `twin_observations`

This is more structured and more durable than `digital_twins`.

It stores:

- one active twin core per user
- snapshot history
- scene-specific overlays
- runtime state per instance
- downstream observations for future profile evolution

This is the strongest long-term portrait state the system has today.

### 7. OpenClaw / CLI bind and identity state

Primary owner:

- `topiclab-backend/app/api/auth.py`
- `topiclab-backend/app/api/openclaw.py`

Primary tables:

- `openclaw_api_keys`
- related OpenClaw identity tables

This stores:

- bind/bootstrap key metadata
- bound user linkage
- token lifecycle metadata

This is not portrait content, but it is required for agent/CLI access to the
portrait application.

### 8. New scale runtime data

Primary owner:

- `topiclab-backend/app/portrait/services/scales_service.py`
- `topiclab-backend/app/portrait/storage/scales_repository.py`

Primary tables:

- `scale_sessions`
- `scale_session_answers`
- `scale_results`

This is the new normalized replacement for legacy `scales.json`.

It stores:

- one scale session at a time
- per-question answers
- canonical server-side results
- definition/scoring versions
- explicit lifecycle state

Important architectural fact:

For the scale slice, data ownership is now much cleaner than in the legacy
profile-helper path.

## Target Persistence Direction

The current system still has split ownership, but the target direction should
now be explicit:

- transient local state is allowed only as cache or adapter state
- important portrait data should be persisted to server-owned storage

That future rule applies to all portrait interactions, including:

- scale sessions and results
- conversation transcripts
- prompt handoff records
- pasted external-AI outputs
- portrait update history
- agent execution logs and runtime traces

So the architectural movement is:

- away from `Resonnet` in-memory + filesystem truth
- toward normalized account-owned or portrait-domain-owned storage in
  `topiclab-backend`

## New Scale Runtime: The First CLI-Friendly Portrait Slice

### New backend routes

Primary files:

- `topiclab-backend/app/api/scales.py`
- `topiclab-backend/app/services/scales_service.py`
- `topiclab-backend/app/services/scales_scoring.py`

What they own:

- `GET /api/v1/scales`
- `GET /api/v1/scales/{scale_id}`
- `POST /api/v1/scales/sessions`
- answer writes
- finalize
- result reads

This is the first portrait-related backend surface designed from the start to be
CLI-usable and resumable.

### Domain assets

Primary directory:

- `Tashan-TopicLab/scales-runtime/`

What it owns:

- normalized scale definitions
- fixtures
- schemas
- CLI/runtime docs
- standalone validation CLI

This is not a new backend service.

It is the portrait-domain asset workspace that feeds the real backend runtime in
`topiclab-backend`.

## Practical Ownership Conclusion

If we ask, "What is the portrait backend today?", the factual answer is:

- portrait generation runtime: mostly `Resonnet`
- portrait account persistence: mostly `topiclab-backend`
- new CLI-friendly scale runtime: `topiclab-backend`

So there is no single historical backend file to "add CLI to" for the whole
portrait system.

Instead, there are two sensible attachment strategies:

### Strategy A. Start with scales

Attach CLI first to the new scale runtime in `topiclab-backend`.

Why this is the best first move:

- the new routes already exist
- the session model is already CLI-shaped
- the standalone CLI is already proven locally
- scale testing is the easiest existing portrait slice to make agent-usable

### Strategy B. Treat legacy profile-helper CLI as a later phase

Only after scales are stable should we decide how to expose:

- portrait chat
- block chat
- prompt handoff
- pasted-result ingestion

Because those capabilities are still historically centered in `Resonnet`, and
their current coupling is much heavier than the scale runtime.

## Decision Clarification: Why Not Just Extend Old Resonnet First?

This is the most important design question.

### Is the old Resonnet portrait backend usable today?

Yes, for the current web portrait experience, the old Resonnet path is clearly
usable.

Evidence:

- the current frontend still calls `profile-helper` routes
- `Resonnet/app/api/profile_helper.py` is still the active façade
- the portrait builder, block chat, scientist matching, export, and publish
  flows are all implemented there
- Resonnet's own architecture docs still describe this as the current working
  portrait-builder path

So the answer is not:

- "the old system is broken, therefore we must throw it away"

The real answer is:

- "the old system works for the current web flow, but it is not a clean first
  base for CLI-first runtime work"

### Why is it not a good first CLI base?

Because the legacy path mixes too many responsibilities in one runtime:

- in-memory sessions
- filesystem working cache
- conversation state
- profile generation
- scientist matching
- export
- scale storage in `scales.json`
- account sync side effects into `digital_twins`

The heaviest coupling is in:

- `Resonnet/app/services/profile_helper/sessions.py`

This means that if we try to make the entire old Resonnet portrait-builder
CLI-grade first, we immediately inherit all of that complexity.

### What architectural problem is already visible?

There is already a split-brain issue between stores and responsibilities.

For example:

- working portrait markdown lives in Resonnet filesystem cache
- long-lived account portrait state lives in `topiclab-backend` `digital_twins`
- legacy scale state lives in Resonnet `scales.json`
- the new approved architecture docs already say scale data should belong to
  `topiclab-backend`

So trying to make the old Resonnet path the first formal CLI runtime would
solidify a shape that the architecture is already trying to move away from.

### Are we rebuilding the whole portrait backend from scratch?

No.

That would be the wrong interpretation.

What is happening is narrower:

- keep the old Resonnet portrait-builder path working for the current web flow
- extract the cleanest first slice into a proper runtime
- make that slice CLI-grade
- migrate callers gradually

That cleanest first slice is the scale runtime.

### Why start with scales instead of the whole portrait builder?

Because scales are the part of the portrait domain that are:

- already structured
- naturally sessionized
- easy to score canonically
- easiest to validate by fixtures
- easiest to expose to both humans and agents
- easiest to move under account-owned backend truth

This is exactly why the new scale runtime was placed in:

- `topiclab-backend/app/api/scales.py`
- `topiclab-backend/app/services/scales_service.py`
- `topiclab-backend/app/services/scales_scoring.py`

### So what is the actual migration strategy?

The intended strategy is:

1. do **not** replace the whole Resonnet portrait builder first
2. keep the existing web portrait flow working
3. make the new scale runtime real and CLI-usable in `topiclab-backend`
4. let standalone CLI and later `TopicLab-CLI` attach to that new runtime
5. only then decide how to expose the heavier legacy profile-helper flows
   through CLI or a future unified runtime

### What would "replace everything first" cost?

If we first tried to fully rework old Resonnet before any CLI slice shipped, we
would be taking on all of these at once:

- conversation runtime redesign
- working-cache redesign
- account-sync redesign
- scale-storage migration
- web compatibility risk
- CLI design

That is much higher risk than:

- making one bounded slice clean first

### Practical conclusion

So the correct reading is:

- old Resonnet is not being discarded
- old Resonnet is still the current portrait-builder backend
- but the first CLI-grade foundation should be built on the newer
  `topiclab-backend` scale runtime, not on the most coupled part of the old
  profile-helper stack

This is not "redoing everything."

It is phased extraction plus gradual migration.

## What This Means For CLI Planning

For immediate CLI work, the correct path is:

1. keep `topiclab-backend` as the formal owner of the new scale CLI runtime
2. keep the standalone CLI as the proving adapter
3. later migrate the same command surface into `TopicLab-CLI`
4. only after that, plan how to expose the remaining legacy portrait-builder
   flows from `Resonnet`

This avoids two common mistakes:

- trying to bolt new CLI semantics directly onto the old `Resonnet` profile
  helper first
- pretending the whole portrait system has already been unified into one
  backend, when it has not

## Current Best Single-File Entry Points

If someone needs to re-open this system quickly, the best entry files are:

### Old portrait builder

- `Resonnet/app/api/profile_helper.py`
- `Resonnet/app/services/profile_helper/sessions.py`

### TopicLab account/twin side

- `topiclab-backend/app/api/auth.py`
- `topiclab-backend/app/services/twin_runtime.py`

### New CLI-friendly scale slice

- `topiclab-backend/app/api/scales.py`
- `topiclab-backend/app/services/scales_service.py`
- `Tashan-TopicLab/scales-runtime/docs/`
