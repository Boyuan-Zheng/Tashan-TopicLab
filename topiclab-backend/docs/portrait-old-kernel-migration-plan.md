# Portrait Old-Kernel Migration Plan

## Purpose

This document defines the direct migration plan for moving the historical
portrait-builder kernel out of the old backend baseline and into
`topiclab-backend/app/portrait/`.

The migration rule is intentionally strict:

- old portrait kernel code should be copied first
- only the minimum necessary modifications should be made
- new code should mainly wrap storage, auth, routing, and deployment
- new abstractions must not replace old kernel behavior prematurely

This document is the execution baseline for the next implementation phase.

## Why This Document Exists

The project already proved several important things:

- durable portrait-domain storage is now possible in `topiclab-backend`
- unified portrait session APIs are executable
- `TopicLab-CLI` can already talk to the cloud staging runtime
- staging deployment and public HTTPS closure are working

Those results are useful, but they are not the same thing as migrating the old
portrait product kernel.

The correction from this point onward is:

- do not keep rebuilding old product logic from scratch where old code already
  exists
- instead, move the old kernel into the new portrait domain package and adapt
  only its boundaries

## Retrospective Pitfall

One important execution mistake already happened and must not be repeated:

- infrastructure closure was proved too early
  - unified session API
  - CLI thin entry
  - staging deployment
  - product-adjacent runtimes
- but the old portrait kernel itself was not migrated first

That work is not useless, but relative to the actual project priority it was a
detour.

The user priority is stricter than "the new backend can produce a portrait-like
result":

- the core old portrait product behavior must be preserved first
- then CLI and cloud closure should expose that migrated core

So from this point onward, progress should not be judged mainly by:

- how many new routes exist
- how many CLI commands exist
- whether a preview runtime can complete a session

It should be judged mainly by:

- whether the historical portrait agent loop has been moved into
  `app/portrait/legacy_kernel/`
- whether `mode=legacy_product` is powered by that migrated loop rather than a
  handwritten approximation
- whether the old product's multi-turn collection-to-portrait path is preserved
  with only boundary-level changes

## Source Baseline

The current accessible old portrait kernel baseline is in the workspace
reference tree:

- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/app/services/profile_helper/agent.py`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/app/services/profile_helper/llm_client.py`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/app/services/profile_helper/profile_parser.py`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/app/services/profile_helper/prompts.py`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/app/services/profile_helper/sessions.py`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/app/services/profile_helper/tools.py`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/app/api/profile_helper.py`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/libs/profile_helper/_template.md`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/libs/profile_helper/docs/*.md`
- `/Users/boyuan/aiwork/0310_huaxiang/reference/Tashan-TopicLab/backend/libs/profile_helper/skills/*/SKILL.md`

Accessible skill inventory in that baseline:

- `collect-basic-info`
- `administer-ams`
- `administer-mini-ipip`
- `administer-rcss`
- `generate-ai-memory-prompt`
- `generate-forum-profile`
- `import-ai-memory`
- `infer-profile-dimensions`
- `modify-profile-schema`
- `review-profile`
- `update-profile`

### Source pitfall discovered

The historical code map and older docs mention `block_agent.py`, but that file
is not present in the currently accessible reference baseline inside this
workspace.

So the migration plan uses this factual rule:

- treat the accessible `reference/Tashan-TopicLab/backend/...` tree as the
  executable source baseline
- keep current block-protocol compatibility code alive until the missing
  `block_agent.py` source is recovered from another snapshot, if needed

## Target Layout In The New Backend

The migration target is:

- real domain ownership in `topiclab-backend/app/portrait/`
- public routes still exposed through `/api/v1/...`
- `app/api/*` kept only as thin compatibility re-export layers

The old kernel should be copied into a clearly separated package first:

```text
app/portrait/legacy_kernel/
├── __init__.py
├── README.md
├── agent.py
├── llm_client.py
├── profile_parser.py
├── prompts.py
├── tools.py
└── assets/
    ├── _template.md
    ├── docs/
    └── skills/
```

That package is intentionally explicit:

- copied old kernel code lives there first
- later thin adapters can call into it
- storage/session/auth replacements should happen around it, not by rewriting
  its business rules prematurely

## Minimal-Modification Rule

Allowed modifications during migration:

1. import-path updates
2. asset-path updates
3. replacing old filesystem/in-memory session ownership with new portrait
   storage adapters
4. replacing old save/sync side effects with:
   - `portrait_state`
   - `portrait_artifacts`
   - `portrait_publish_service`
5. replacing old API/router glue with new `app/portrait/api/*`

Not allowed as the default migration path:

1. reinterpreting skill behavior into a new handwritten policy layer unless the
   old code is truly unavailable
2. redesigning prompt logic before the old prompt/kernel is present
3. adding new product semantics before old ones are executable

## Migration Phases

### Phase K0. Freeze The Baseline

Deliverables:

- this migration plan
- explicit source-path inventory
- explicit target package layout
- explicit minimal-modification rule

Status:

- completed

### Phase K1. Move Prompt / Tool / Skill Assets First

Goal:

- make the new backend own the old portrait kernel assets locally

Actions:

1. copy old:
   - `prompts.py`
   - `tools.py`
   - `profile_parser.py`
   - `_template.md`
   - `docs/*.md`
   - `skills/*/SKILL.md`
2. adapt only import paths and local asset discovery paths
3. add focused tests proving the copied asset registry works inside
   `topiclab-backend/app/portrait/`

Exit criteria:

- skill list is loaded from the new package
- docs/template are loaded from the new package
- no dependency on external reference paths is required for these assets

### Phase K2. Move The Old Agent Loop

Goal:

- copy `agent.py` and `llm_client.py` into the new package with only boundary
  changes

Actions:

1. copy old agent loop first
2. preserve:
   - `read_skill`
   - `read_doc`
   - `read_profile`
   - `write_profile`
   - `write_forum_profile`
   - tool-call iteration controls
3. adapt LLM client boundary to current `topiclab-backend` AI generation
   config/runtime

Exit criteria:

- the old skill-routed agent loop runs from inside `app/portrait/legacy_kernel`
- no direct dependency remains on the old backend package structure

### Phase K3. Replace Old Session / File Ownership With New Storage Adapters

Goal:

- keep old kernel behavior while swapping out old persistence ownership

Actions:

1. treat old `sessions.py` as behavior source, not persistence owner
2. move ownership of:
   - current profile state
   - forum profile
   - scale results
   - history
   - publish side effects
   onto:
   - `portrait_session`
   - `portrait_state`
   - `portrait_artifacts`
   - `portrait_publish_service`
3. preserve old user-visible behavior during the swap

Exit criteria:

- old kernel no longer depends on local profile markdown files as source of
  truth
- current truth lives in the new portrait domain storage

### Phase K4. Reconnect Old Product Skills Through The New Session Layer

Goal:

- make the unified session layer call the migrated old kernel rather than a
  handwritten approximation

Actions:

1. route old skill decisions through the migrated old kernel package
2. keep current top-level API surface:
   - `start`
   - `respond`
   - `status`
   - `result`
   - `history`
   - `reset`
3. keep CLI thin; it should call backend contracts only

Exit criteria:

- backend skill-routing comes from migrated old kernel logic
- current CLI remains usable without learning old internal modules

Status update on 2026-04-11:

- `app/portrait/legacy_kernel/agent.py`, `llm_client.py`, `sessions.py`,
  `bridge.py` and `storage/legacy_kernel_session_repository.py` are now wired
  into the executable path
- `mode=legacy_product` no longer starts from the handwritten
  `portrait_skill_policy_service` welcome flow
- `start(mode=legacy_product)` now bootstraps the migrated old kernel
- `respond(...)` in `legacy_product` mode now normalizes CLI/API inputs into
  natural-language turns and sends them through the migrated old kernel bridge
- migrated legacy-session snapshots are now stored in
  `portrait_legacy_kernel_sessions`
- `portrait_state` is synchronized from old-kernel profile markdown plus
  `legacy_kernel` raw state on every turn

Verified path in this round:

- local API tests passed against the migrated old-kernel path
- staging cloud runtime was updated and exercised through the public HTTPS
  entrance
- verified public flow:
  - register
  - `POST /api/v1/portrait/sessions` with `mode=legacy_product`
  - `POST /api/v1/portrait/sessions/{id}/respond`
  - `GET /api/v1/portrait/sessions/{id}/result`
- verified runtime refs on cloud:
  - `legacy_kernel_session`
  - `portrait_state`
- verified cloud logs show real migrated old-kernel tool calls such as:
  - `read_skill`
  - `read_profile`
  - `write_profile`

Pitfall discovered during cloud validation:

- the first legacy-kernel LLM adapter reused the async shared HTTP client via
  `asyncio.run(...)` from a sync loop
- under FastAPI async request handling this caused
  `RuntimeError: Event loop is closed`
- the fix in this round was:
  - add `post_ai_generation_chat_sync(...)`
  - make `legacy_kernel/llm_client.py` use the sync path directly

Residual gaps after this round:

- the old handwritten compatibility services still exist in the codebase, but
  `legacy_product` start/respond no longer depends on them
- partial old-kernel markdown can still produce imperfect canonical field
  extraction in edge cases; this round added stricter cleanup for obvious label
  bleed, but parser hardening is not fully finished

Operational update on 2026-04-11:

- AutoDL staging startup is no longer dependent on an ad-hoc shell history
- repo-owned service script added:
  - `topiclab-backend/scripts/portrait_staging_service.sh`
- validated remote path:
  - `/root/topiclab-portrait-staging/topiclab-backend/scripts/portrait_staging_service.sh`
- validated actions:
  - `status`
  - `restart`
  - `health`
  - `logs`
- the script now handles the real transition case where port `6006` is already
  occupied by an older unmanaged `nohup` process:
  - `status` reports `running unmanaged ...`
  - `restart` stops that unmanaged listener
  - then starts a managed process and writes a pid file
- validated managed process after takeover:
  - `pid=26859`
- validated health response after takeover:
  - `{"status":"ok","service":"topiclab-backend"}`
- validated CLI closure after takeover:
  - local `topiclab-cli` bootstrap env
  - `portrait auth ensure`
  - `portrait start --mode legacy_product`
  - `portrait respond --choice direct`
  - `portrait status`
  - public HTTPS runtime remained healthy and server log recorded the session
    follow-up requests for:
    - `pts_33eaa70a7d6f48e3`

### Phase K5. Decommission Temporary Reimplementations

Goal:

- remove or shrink the handwritten compatibility logic that was added before
  the kernel-first correction

Actions:

1. compare migrated old-kernel paths against current handwritten parity code
2. keep reusable infrastructure:
   - storage
   - schemas
   - API routers
   - CLI
   - deployment wiring
3. replace handwritten business logic where the copied old kernel now owns the
   same behavior more faithfully

Exit criteria:

- `app/portrait` owns the portrait product kernel
- old behavior is primarily inherited from copied baseline code plus boundary
  adapters
- temporary parity code is reduced to thin glue or removed

## What Previous Work Remains Valid

The following work remains useful and should be preserved:

- new scales runtime ownership
- canonical portrait-state storage
- prompt-handoff / import-result persistence
- unified portrait session tables and APIs
- artifact/export/publish storage
- TopicLab-CLI portrait entry
- staging deployment and cloud validation path

These are infrastructure rails, not wasted work.

What changes now is priority:

- they should support the old-kernel migration
- they should not keep displacing it

## Immediate Execution Order From This Document

Start now with:

1. Phase K1 asset migration
2. then Phase K2 copied old agent loop
3. then Phase K3 storage/session adapter replacement

That is the current correct critical path.
