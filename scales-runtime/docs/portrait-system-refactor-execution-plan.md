# Portrait System Refactor Execution Plan

## Purpose

This document defines the staged execution plan for refactoring the portrait
system inside TopicLab.

It follows the architecture defined in:

- `portrait-system-refactor-architecture.md`

The goal is to move from today's mixed legacy state toward a cleaner
portrait-domain runtime without breaking the current product.

## Execution Strategy

The execution strategy is:

1. write architecture and boundary docs first
2. migrate one bounded slice at a time
3. validate each slice with tests and smoke before expanding scope
4. keep old callers stable until new runtime paths are proven
5. only migrate adapters after backend/runtime ownership is clear

This is a gradual refactor, not a single cutover.

One operational rule also needs to stay explicit:

- SSH is for deploy, staging validation, and operator tasks
- the product-facing closure must become `local CLI -> remote portrait runtime`
- every staging step should therefore move us closer to HTTP/API-based
  interaction and farther away from manual in-server usage

## Current Correction

The next implementation phase is now explicitly corrected to a stricter rule:

- old portrait kernel code should be migrated into
  `topiclab-backend/app/portrait/`
- existing old code should be copied first
- only minimum boundary modifications should be made
- handwritten parity logic should no longer expand faster than direct kernel
  migration

Why this correction is necessary:

- the project already proved storage, API, CLI, and cloud-deploy rails
- but those rails are not the same thing as migrating the historical portrait
  kernel itself
- the historical kernel still lives in the old baseline source tree and needs
  to become the primary business-logic source again inside the new backend

The dedicated execution document for that phase is:

- `topiclab-backend/docs/portrait-old-kernel-migration-plan.md`

## Current Main-Entry Status

The portrait runtime now has three staging-proven HTTP/API closures:

- `TopicLab-CLI -> scales runtime -> AutoDL public URL`
- `TopicLab-CLI -> portrait dialogue runtime -> AutoDL public URL`
- `TopicLab-CLI -> portrait state runtime -> AutoDL public URL`

The `scales` path is already wired into `TopicLab-CLI`.

The `dialogue` path is now also wired into `TopicLab-CLI` for the first thin
command surface:

- `topiclab portrait auth ensure`
- `topiclab portrait dialogue start`
- `topiclab portrait dialogue status`
- `topiclab portrait dialogue send`
- `topiclab portrait dialogue messages`
- `topiclab portrait dialogue derived-state`
- `topiclab portrait dialogue close`

The `portrait state` path is now also wired into `TopicLab-CLI` for:

- `topiclab portrait state current`
- `topiclab portrait state versions`
- `topiclab portrait state version`
- `topiclab portrait state apply`
- `topiclab portrait state update`
- `topiclab portrait state observations`

The backend now also has a first executable `portrait state runtime` under:

- `/api/v1/portrait/state/current`
- `/api/v1/portrait/state/versions`
- `/api/v1/portrait/state/versions/{version_id}`
- `/api/v1/portrait/state/updates`
- `/api/v1/portrait/state/updates/{update_id}`
- `/api/v1/portrait/state/observations`

The state slice is now durable, locally validated, and publicly validated
through the AutoDL HTTPS staging URL for:

- `current`
- `apply`
- `versions`
- `observations`

The backend now also has a first executable prompt-handoff and import-result
runtime under:

- `/api/v1/portrait/prompt-handoffs`
- `/api/v1/portrait/import-results`

That slice has been locally validated, remotely revalidated on AutoDL staging,
and publicly validated over HTTPS without SSH by creating a prompt handoff,
creating an import result, and parsing it into a deterministic
`candidate_state_patch`.

The backend now also has a first executable unified portrait-session
orchestrator under:

- `POST /api/v1/portrait/sessions`
- `GET /api/v1/portrait/sessions/{session_id}`
- `POST /api/v1/portrait/sessions/{session_id}/respond`
- `GET /api/v1/portrait/sessions/{session_id}/result`

That slice is now locally validated, wired into `TopicLab-CLI` as a first
executable main entry, and publicly validated over the AutoDL HTTPS custom
service URL without SSH. It already proves:

- durable top-level `portrait_sessions`
- durable runtime refs
- durable session events
- `respond(text)` routing into:
  - `dialogue`
  - then `portrait_state`
- `respond(choice="scale:<id>")` routing into:
  - `scales`
  - then `portrait_state`
- `respond(choice="prompt_handoff")` routing into:
  - `prompt_handoff`
- `respond(external_text|external_json)` routing into:
  - `import_result`
  - then `portrait_state`
- `respond(choice="forum:generate")` routing into:
  - `forum artifact generation`
- `respond(choice="scientist:famous" | "scientist:field")` routing into:
  - `scientist matching / recommendation artifacts`
- `respond(choice="publish:brief" | "publish:full")` routing into:
  - `publish artifact generation`
  - `twin sync`
- `respond(confirm)` completion

The unified main-entry surface in `TopicLab-CLI` is now:

- `topiclab portrait start`
- `topiclab portrait respond`
- `topiclab portrait status`
- `topiclab portrait result`
- `topiclab portrait resume`
- `topiclab portrait history`
- `topiclab portrait reset`
- `topiclab portrait export`

The checked-in `Tashan-TopicLab/topiclab-cli` submodule now already contains
that portrait main entry and the helper bootstrap script:

- `npm run portrait:preview:bootstrap`

### Real cloud validation on 2026-04-11

The AutoDL HTTPS staging closure was revalidated end-to-end with the local
CLI build talking to the cloud runtime at:

- `https://u394499-8634-23d284fb.westb.seetacloud.com:8443`

Verified artifacts from that run:

- portrait session:
  - `pts_558f1c332faa41b9`
- forum artifact:
  - `par_6dd696c0944d43b1`
- scientist artifact:
  - `par_9d14793069c642f6`
- export artifact:
  - `par_f9e70bff60774732`
- publish artifact:
  - `par_af5569b6fa1e4cc3`
- published twin:
  - `twin_8a66279ee612a3a0`

This validation proved:

- local CLI installation and state are local-only
- portrait runtime execution, persistence, and logs are cloud-owned
- no SSH tunnel is required for agent usage once the backend is deployed

That means the current staging runtime is no longer only a developer slice
validation surface. It is now also a first user-facing portrait CLI flow for
agents who use the checked-out `TopicLab-CLI` repository build locally.

## Completion Criteria For The Full Program

The portrait refactor should only be considered complete when:

1. important portrait-domain data is server-owned and durable
2. the main portrait interactions are runtime-backed rather than UI-glued
3. CLI and web callers share the same backend contracts
4. legacy `Resonnet` ownership is reduced to either compatibility or removed
5. future portrait update loops can build on durable runtime data

## Phase 0. Architecture And Boundary Definition

### Goal

Freeze the direction before large-scale code movement.

### Deliverables

- portrait application architecture docs
- backend bounded-domain docs
- persistence-direction docs
- existing code/data map docs

### Status

- completed

### Main docs

- `unified-portrait-interaction-architecture.md`
- `portrait-system-refactor-architecture.md`
- `existing-portrait-backend-code-map.md`
- `topiclab-backend/docs/portrait-domain-architecture.md`

## Phase 1. First Executable Slice: Scales

### Goal

Refactor the cleanest portrait slice first and prove the migration pattern.

### Scope

- canonical definitions
- canonical scoring
- session lifecycle
- per-question persistence
- result materialization
- compatibility wrappers

### Deliverables

- `/api/v1/scales/...`
- `topiclab-backend/app/portrait/` scales implementation
- standalone CLI local closure
- focused tests
- smoke script

### Status

- locally implemented and validated

### Validation already completed

- focused API tests
- standalone smoke
- syntax / import validation
- public AutoDL no-SSH closure through the custom-service HTTPS URL

### Exit criteria

- old routes still stable
- new portrait-domain ownership proven
- no adapter rewrite required to use the runtime

## Phase 1.5. Dialogue Runtime Hardening

### Goal

Turn the new dialogue slice from durable skeleton into a real model-backed and
publicly reachable portrait runtime.

### Newly validated facts

- the dialogue slice now uses a shared `topiclab-backend`
  `AI_GENERATION_API_KEYS` rotation-capable caller
- the current provided `sk-...` DashScope keys worked with:
  - `https://dashscope.aliyuncs.com/compatible-mode/v1`
- the same keys did **not** work with:
  - `https://coding.dashscope.aliyuncs.com/v1`
- public AutoDL dialogue validation required:
  - a real `DATABASE_URL`
  - a staging-only `REGISTER_SKIP_SMS_UNTIL` bypass

### Staging validation path already completed

1. public `GET /health`
2. public `POST /auth/register`
3. public `POST /api/v1/portrait/dialogue/sessions`
4. public `POST /messages`
5. public `GET /messages`
6. public `GET /derived-state`
7. public `POST /close`

### What is still missing after this validation

- `resume`
- `summarize`
- richer result projection and progress semantics for more slice combinations

## Phase 1.75. Portrait State First Batch

### Goal

Create the first durable backend-owned answer to:

- what is the current portrait state?
- what update changed it?
- what version snapshot was produced?

### Newly validated facts

- a first canonical portrait-state runtime now exists under
  `topiclab-backend/app/portrait/`
- it owns durable:
  - current portrait state
  - update events
  - version snapshots
  - observations
- it currently supports explicit materialization from:
  - `manual`
  - `dialogue_session`
  - `scale_session`
- the runtime deliberately uses explicit source-driven updates rather than
  hidden automatic coupling

### Local validation already completed

1. `GET /api/v1/portrait/state/current`
2. `GET /api/v1/portrait/state/versions`
3. `GET /api/v1/portrait/state/versions/{version_id}`
4. `POST /api/v1/portrait/state/updates`
5. `GET /api/v1/portrait/state/updates/{update_id}`
6. `GET /api/v1/portrait/state/observations`

Observed validation result:

- focused backend tests passed:
  - `12 passed`
- standalone smoke successfully materialized:
  - one dialogue session into canonical state
  - one finalized scale session into the same canonical state
- smoke-observed state included:
  - dialogue latest session block
  - RCSS result block with `CSI = 24.0`
- version history and observation history both incremented as expected

### What is still missing after this batch

- `TopicLab-CLI` wiring for portrait-state commands
- prompt handoff / import-result source integration
- automatic portrait-state materialization policy
- richer portrait normalization beyond first dialogue/scale projections

Note:

- the first item above is now complete
- the remaining items are still open

## Phase 1.875. Prompt Handoff And Import First Batch

### Goal

Create a durable backend-owned path for:

- generating prompt handoff artifacts from portrait context
- storing pasted external-AI results
- parsing them into deterministic portrait-relevant structures

### Newly validated facts

- prompt handoff and import-result now both execute under
  `topiclab-backend/app/portrait/`
- prompt artifacts are now server-owned rather than UI-only glue
- external AI pasted results now persist in durable tables
- deterministic parse runs can already return a
  `candidate_state_patch`-style payload for later portrait-state updates

### Local validation already completed

1. focused backend tests passed:
   - `14 passed`
2. prompt handoff create/list/get/cancel validated
3. import result create/get/parse/parsed validated

### Remote staging validation already completed

1. prompt/import backend files synced to AutoDL staging
2. focused remote tests passed:
   - `5 passed`
3. public HTTPS validation completed without SSH tunnels

### Public validation already completed

1. create portrait-state update
2. create prompt handoff
3. create import result
4. parse import result

Observed public IDs:

- `portrait_state_id = pst_103b9a790c864f75`
- `handoff_id = phf_30a45386b3be4a29`
- `import_id = pir_4d10cc62192f49eb`

### Operational pitfall discovered on AutoDL

For the public custom-service process bound to internal `6006`, a blind `nohup`
restart was not enough. The shell needed to explicitly source the project
`.env`, otherwise startup could fail with:

- `ValueError("DATABASE_URL is not set")`

## Phase 1.9. Unified Portrait Session Orchestrator First Batch

### Goal

Turn the unified portrait-session protocol from paper design into a first
executable backend slice.

### Newly validated facts

- a first executable unified portrait-session backend now exists under
  `topiclab-backend/app/portrait/`
- the top-level session layer already has durable:
  - session rows
  - runtime refs
  - orchestration events
- the executable main-entry path now works for:
  - `start`
  - `status`
  - `respond(text)`
  - `respond(choice="scale:<id>")`
  - numeric `respond(choice=<scale_value>)`
  - `respond(choice="prompt_handoff")`
  - `respond(choice="forum:generate")`
  - `respond(choice="scientist:famous" | "scientist:field")`
  - `respond(choice="export:structured" | "export:profile_markdown" | "export:forum_markdown")`
  - `respond(choice="publish:brief" | "publish:full")`
  - `respond(external_text|external_json)`
  - `respond(confirm)`
  - `result`
- routed `respond(...)` calls now reach:
  - `dialogue`
  - `scales`
  - `prompt_handoff`
  - `import_result`
  - `portrait_state`
  - `forum`
  - `scientist`
  - `export`
  - `publish`
- `TopicLab-CLI` now already exposes:
  - `topiclab portrait start`
  - `topiclab portrait respond`
  - `topiclab portrait status`
  - `topiclab portrait result`
  - `topiclab portrait resume`
  - `topiclab portrait history`
  - `topiclab portrait reset`
  - `topiclab portrait export`
- the unified main-entry loop has now also been publicly validated through the
  AutoDL HTTPS custom-service URL without SSH

### Local validation already completed

1. syntax/import validation for the new session files
2. focused backend tests passed:
   - `22 passed`
3. standalone smoke passed:
   - `scripts/portrait_session_runtime_smoke.py`

### What is still missing after this batch

- `resume` and `summarize`
- richer stage transitions and progress semantics beyond the first executable
  loop
- stronger result normalization across more slice combinations
- richer canonical portrait-state filling after very short dialogue-only runs,
  because forum/export/publish now work end-to-end but remain semantically
  sparse when `basic_info`, capability fields, and current-needs fields have
  not yet been materialized

### First user-facing operator handoff now required

Because the unified main entry and the first user-flow control commands are now
real and publicly validated over HTTPS, portrait work is no longer only a
backend migration topic.

At this stage the project also needs:

- a user-facing CLI agent manual
- a reusable local skill that tells other agents how to:
  - build the checked-out CLI locally
  - log in with their own account
  - use `start/respond/status/result`
  - use `resume/history/reset/export`

## Phase 2. Productionize The Scale Runtime

### Goal

Turn the locally-proven scale slice into a real production-owned runtime.

### Preferred rollout order

The scale runtime should **not** go directly to the public production
environment first.

Validated rollout order:

1. local closure
2. dedicated staging server
3. limited internal validation
4. canary or controlled production exposure
5. general production rollout

### Preferred staging target

The preferred first remote target is the AMD test server:

- `aup-test-01`

This target was selected because the local infrastructure documents already
describe it as the compute-oriented external research server and as the
existing Tashan Phase 1 development environment.

### Known staging facts already documented

The deployment docs inside `0310_huaxiang` already contain the following
staging-relevant information for `aup-test-01`:

- host identity:
  - machine name `aup-test-01`
  - internal IP `192.168.0.117`
  - shared public egress IP `20.189.201.170`
  - login user `aup`
- connection path:
  - persistent `bore` tunnel is the preferred AI connection method
  - direct port-forward SSH on `20.189.201.170:2222` is also documented as a
    stable human path
  - current tunnel port should be read from `/home/aup/bore_port.txt` on the
    AMD server or `/tmp/aup_bore_port` on the Aliyun side
- local runtime environment:
  - Ubuntu 24.04
  - PostgreSQL 16 already installed
  - local test database `tashan_dev`
  - local env file `~/tashan.env`
  - local auth mode `jwt_local`
- current Tashan Phase 1 environment:
  - frontend port `3100`
  - backend port `8100`
  - shared JWT model already documented in the infrastructure handbook

Primary source documents:

- `/_内部总控/开发规范/部署与基础设施全景手册.md`
- `/_内部总控/开发规范/双服务器完整架构分析_v1.0.md`
- `/_内部总控/开发规范/服务器操作日志.md`

### What is still dynamic or must be re-checked at deploy time

The docs are already sufficient to choose the staging target and understand the
deployment path, but a real deploy still requires checking a few current-state
values:

- the current `bore` port
- whether the target repo checkout already exists on `aup-test-01`, and where
- whether `docker`, `docker compose`, and any needed reverse-proxy pieces are
  currently healthy on that server
- whether ports `7860` and `8000` are still occupied by unrelated processes
- whether we want a direct process run, docker-compose-based staging, or a
  branch-specific preview path for this slice

### Connectivity verification note

On `2026-04-10`, a non-invasive connectivity check was run from the local Mac
development machine.

What was verified:

- local SSH key `~/.ssh/id_ed25519` exists
- TCP reachability to `20.189.201.170:2222` succeeds
- TCP reachability to `20.189.201.170:22` also succeeds

What was learned:

- `20.189.201.170:22` should still be treated as the wrong machine path for the
  AMD server, consistent with the infrastructure handbook
- `20.189.201.170:2222` is **not yet safe to treat as a guaranteed AI deploy
  path**
- an SSH attempt to `2222` reached the remote side but failed during key
  exchange with:
  - `kex_exchange_identification: Connection closed by remote host`

Current interpretation:

- for actual staging deployment work, the dynamic `bore` port remains the
  preferred documented path
- `2222` may still be useful for humans or under certain conditions, but it
  should be treated as needing live confirmation rather than as a fixed deploy
  assumption

### First live preflight on the AMD staging host

When a human has already opened a remote desktop onto `aup-test-01`, the first
check should stay entirely inside the Ubuntu 24 WSL terminal and should remain
read-only.

Do not use the Windows PowerShell window for deployment work.

Recommended first read-only checks:

1. identify the current machine and user
2. confirm the current working shell and home directory
3. confirm whether the dynamic `bore` port file exists
4. confirm whether the Tashan repo checkout already exists
5. confirm whether `docker` and `docker compose` are installed
6. confirm whether likely ports are already occupied

Suggested command batch:

```bash
whoami
hostname
pwd
echo "$HOME"
uname -a
ls -la /home/$(whoami)
ls -la /home/$(whoami)/bore_port.txt
find /home/$(whoami) -maxdepth 3 \( -name Tashan-TopicLab -o -name topiclab-backend \)
docker --version
docker compose version
ss -tlnp | grep -E ':2222|:7860|:8000|:8100|:3100|:8001'
```

These checks should happen before any code pull, env edit, service restart, or
deploy command.

### Live preflight result on 2026-04-10

A first human-assisted read-only preflight was performed from the Ubuntu 24 WSL
terminal opened through remote desktop on the AMD machine.

Observed facts:

- current user: `gmk`
- hostname: `NucBoxEVO-X2`
- current shell home: `/home/gmk`
- distro: Ubuntu 24.04 on WSL2
- `/home/gmk/bore_port.txt` does not exist
- no `Tashan-TopicLab` or `topiclab-backend` checkout was found under
  `/home/gmk` within the first three directory levels
- a Windows-side checkout exists at:
  - `/mnt/c/Users/gmk/Desktop/Tashan-TopicLab`
- Windows-side SSH key material exists at:
  - `/mnt/c/Users/gmk/.ssh/id_ed25519`
- `docker` is not currently available inside this WSL distro
- the environment printed the standard Docker Desktop WSL integration hint
- `/etc/wsl.conf` enables `systemd`

Immediate interpretation:

- this is not currently behaving like the previously documented standalone
  Linux server shape
- the active staging entry point is a Windows host with a WSL Ubuntu runtime
- before any deploy work, we must determine:
  - whether this WSL distro is the intended deployment runtime
  - whether the Windows-mounted checkout should be used directly or moved into
    Linux-side storage before runtime work
  - where the actual project checkout lives
  - whether Docker should be used through Docker Desktop integration or whether
    another runtime path is intended

This finding blocks deploy execution, but it does not block further read-only
environment discovery.

### Security handling

The infrastructure docs contain real secrets and connection material. This
execution plan intentionally does **not** duplicate those raw values. Operators
should retrieve them from the infrastructure single-source-of-truth documents
at deploy time rather than copying them into portrait-domain notes.

### Alternative staging host verification on 2026-04-10

A second remote staging candidate was later provided and verified via direct
SSH access.

Observed facts from the first read-only login:

- remote login as `root` succeeds
- hostname is `autodl-container-ad3a418634-23d284fb`
- OS is Ubuntu 22.04.5 LTS
- filesystem root has about `30G` available
- RAM is large (`377Gi`)
- GPU is visible:
  - `NVIDIA GeForce RTX 3080 Ti`
- `git` exists
- `docker` is not installed or not on `PATH`
- `python3` is not on `PATH`
- `uv` is not on `PATH`
- `systemctl` exists but reports runtime state `offline`
- `ss` is not currently available
- no `Tashan-TopicLab` or `topiclab-backend` checkout was found under `/root`
  or `/home/gmk` within the first few directory levels

Current interpretation:

- this host is reachable and may be usable as a staging target
- however, it currently looks more like a cloud container runtime than a
  ready-made TopicLab staging machine
- deploy work on this host still requires deciding the runtime strategy first:
  - containerized deploy after installing Docker
  - process-based deploy using the existing Conda/Python toolchain
  - or a hybrid path

This host is therefore a viable candidate, but not yet a zero-config staging
environment.

### Scope

- deploy `/api/v1/scales/...` to the live environment
- validate remote standalone CLI against the live backend
- confirm bind-key auth + remote scale flow end-to-end
- establish rollout-safe observability for this slice

### Deliverables

- live scale routes
- remote smoke run record
- production validation notes
- minimal operational logging for the scale runtime

### Exit criteria

- live `list / get / start / answer / finalize / result` path works
- no reliance on local-only validation

## Phase 3. Thin Migration Into `TopicLab-CLI`

### Goal

Move the proven command surface into the shared CLI without moving business
logic into the CLI repo.

### Scope

- add `topiclab scales ...`
- reuse `TopicLab-CLI` auth/session infrastructure
- keep CLI implementation thin

### Deliverables

- `TopicLab-CLI` command adapter
- JSON-first contract parity with standalone CLI
- migration notes from standalone adapter to shared CLI

### Exit criteria

- same runtime, same API, same semantics
- no duplicated scoring or portrait business logic in CLI

## Phase 4. Web Scale Flow Migration

### Goal

Move the web scale experience off the legacy `Resonnet` scale submit path and
onto the new runtime.

### Scope

- update web scale pages to use the new `topiclab-backend` routes
- preserve current UX while changing backend truth
- decide compatibility plan for legacy `scales.json`

### Deliverables

- frontend API migration
- backward-compatibility note
- migration or bridge plan for old scale data

### Exit criteria

- web and CLI both use the same scale runtime
- old `Resonnet` scale path is no longer the primary truth

## Phase 5. Dialogue Runtime Extraction

### Goal

Refactor the lightweight portrait dialogue flow into the portrait domain with
durable transcript storage.

### Scope

- dialogue session model
- portrait message transcript persistence
- server-owned conversation state
- clear separation from legacy `Resonnet` in-memory working state

### Required persistence

- dialogue sessions
- dialogue messages
- message metadata
- derived runtime status

### Exit criteria

- important conversation state is durable
- dialogue can be resumed without relying only on filesystem cache

## Phase 6. Prompt Handoff And Import-Result Runtime

### Goal

Turn external-AI prompt handoff and pasted-result return into proper runtime
interactions instead of UI-only glue.

### Scope

- prompt request record
- generated prompt artifact persistence
- pasted external-AI output persistence
- parse-result persistence
- linkage to portrait updates

### Required persistence

- prompt handoff records
- external result payloads
- import status
- parse outputs

### Exit criteria

- prompt/export/import paths are traceable and replayable
- the system can reason about what was handed off and what came back

## Phase 7. Portrait Update And Memory Loop

### Goal

Add durable history for portrait evolution so the system can support richer
self-understanding and future memory management.

### Scope

- portrait update events
- version history
- runtime observations
- future memory/update orchestration hooks

### Required persistence

- update log
- observation log
- execution trace / debug log
- versioned portrait deltas or snapshots

### Exit criteria

- the system can answer not only "what is the current portrait?"
- but also "how did it become this way?" and "what changed over time?"

## Phase 8. Legacy Reduction And Cleanup

### Goal

Reduce the amount of portrait truth still owned by the old `Resonnet` path.

### Scope

- remove or downgrade obsolete compatibility bridges
- reduce dependence on `scales.json`
- reduce dependence on local-only working truth
- keep only necessary compatibility where still justified

### Exit criteria

- portrait domain truth is primarily in `topiclab-backend`
- legacy Resonnet portrait-builder ownership is no longer the default truth

## Backend-Only Remaining Work Snapshot (2026-04-10)

This section answers a narrower planning question:

- if frontend migration is temporarily ignored, what is still missing on the
  new portrait backend?

### What is already done in the new backend

Today, `scales` is the first fully validated slice in the new executable
ownership model, a durable `dialogue` slice now exists, and a first canonical
`portrait state` slice now also exists.

Implemented under `topiclab-backend/app/portrait/`:

- `api/scales.py`
- `services/scales_service.py`
- `services/scales_scoring.py`
- `storage/scales_repository.py`
- `runtime/definitions_loader.py`
- `schemas/scales.py`
- `api/dialogue.py`
- `services/dialogue_service.py`
- `services/dialogue_runtime_service.py`
- `services/dialogue_summary_service.py`
- `storage/dialogue_repository.py`
- `schemas/dialogue.py`
- `api/portrait_state.py`
- `services/portrait_state_service.py`
- `storage/portrait_state_repository.py`
- `schemas/portrait_state.py`

This means the new backend already has:

- canonical scale definitions
- server-side scoring
- durable scale session / answer / result persistence
- stable `/api/v1/scales/...` routes
- staging validation through standalone CLI and `TopicLab-CLI`
- durable dialogue-session / message / derived-state persistence
- first `/api/v1/portrait/dialogue/...` routes
- a model-backed assistant reply path wired to the shared `AI_GENERATION_*`
  backend configuration
- a first canonical portrait-state runtime with:
  - current-state reads
  - explicit update materialization
  - durable update events
  - durable version snapshots
  - durable observations
- local `TopicLab-CLI` main-entry coverage for:
  - `topiclab portrait dialogue start`
  - `topiclab portrait dialogue status`
  - `topiclab portrait dialogue send`
  - `topiclab portrait dialogue messages`
  - `topiclab portrait dialogue derived-state`
  - `topiclab portrait dialogue close`

### What is not done yet in the new backend

Ignoring frontend migration for now, the remaining backend work is still
substantial.

#### 1. Portrait dialogue runtime hardening and generation integration

Still missing:

- resume / summarize paths
- downstream hooks into prompt handoff and portrait-state updates
- live deploy environments still need `AI_GENERATION_*` configured for the new
  dialogue runtime to generate real replies

This is the backend replacement for the current legacy `Resonnet`
`/profile-helper/chat` and `/profile-helper/chat/blocks` ownership.

#### 2. Prompt handoff and pasted-result import runtime

Still missing:

- prompt handoff API surface
- durable prompt artifact persistence
- pasted external-AI output persistence
- parse-result persistence and status tracking
- linkage from imported result back into portrait updates

This is the backend replacement for the current UI-glued prompt export /
copy-paste return flow.

#### 3. Canonical portrait state hardening and broader source integration

Still missing:

- broader source integration beyond `manual`, `dialogue_session`, and
  `scale_session`
- automatic materialization policy and orchestration
- richer normalized portrait aggregate design
- linkage into future prompt handoff / import-result flows

Right now the new backend does own a first durable canonical portrait state,
but it is still an explicit first batch rather than the full long-term update
loop.

#### 4. Durable execution logs and runtime traces

Still missing:

- portrait-domain execution log persistence
- runtime trace records for debugging and replay
- import / update / orchestration event logs

This matters because the target system is supposed to support future iteration,
debugging, and richer agent self-understanding.

#### 5. Legacy bridge reduction on the backend side

Still missing:

- a backend bridge strategy for legacy `Resonnet` dialogue and prompt flows
- a compatibility plan for old filesystem-owned portrait working state
- a clear backfill or coexistence plan for old portrait-derived data

Even if frontend is ignored for now, backend ownership is still split between
`Resonnet` and `topiclab-backend` for the heavier portrait flows.

### Recommended backend-only build order from here

If the next goal is to finish the new backend first and postpone frontend
adapter work, the recommended order is:

1. finish hardening the `scales` slice as the reference runtime pattern
2. harden portrait dialogue runtime beyond the first public slice
3. build prompt handoff / import-result runtime
4. harden and extend canonical portrait state + update/version history
5. add durable execution logs and traceability
6. only then decide how to retire or bridge the legacy `Resonnet` backend

### Short summary

If frontend migration is ignored, the new portrait backend is **not** "almost
done" yet.

The accurate current state is:

- `scales` is done enough to serve as the first real migrated slice
- `dialogue` now has a real CLI-visible first batch
- `portrait state` now has a real backend-owned first batch
- the next backend milestones are prompt handoff/import, portrait-state
  hardening, and logging

## Cross-Phase Rules

These rules apply in every phase.

### Rule 1. Do not touch unrelated TopicLab features

Portrait refactor work should stay inside the portrait domain boundary.

### Rule 2. Always document the real path

If a migration step is proven, record:

- what changed
- what stayed compatible
- what was verified
- what remains incomplete

### Rule 3. Persist before optimizing UX

If data is important for continuity, debugging, or future product iteration, it
should be persisted before UI polish becomes the priority.

### Rule 4. Preserve adapter thinness

Web and CLI should remain callers, not logic owners.

### Rule 5. Prefer staged replacement over hidden rewrites

Keep old callers stable while new ownership is proven.

## Immediate Next Step

The next concrete backend-only step after this point should be:

1. keep `scales`, `dialogue`, and `portrait state` stable as the reference
   pattern trio
2. build prompt handoff / import-result runtime on top of the new durable
   dialogue and state substrate
3. only then decide where automatic portrait-state updates should happen
4. keep old callers stable until the heavier portrait slices are equally
   runtime-backed

Current status:

- `topiclab-cli scales ...` is already staging-proven
- `topiclab portrait dialogue ...` first thin adapter is already staging-proven
- `portrait state runtime` first batch is locally validated but not yet wired
  into `TopicLab-CLI`

## Validated Alternative Staging Run (2026-04-10)

An alternative root-access staging host was used to validate the first remote
runtime loop without touching production.

### What was actually done

- synced only the minimum slice needed for portrait-scale staging:
  - `topiclab-backend/`
  - `scales-runtime/`
  - `scripts/scales_runtime_smoke.py`
- excluded unrelated repo content and did not touch production services
- used the host's existing Miniconda Python instead of Docker because Docker was
  not available there
- installed the minimum backend dependencies with editable install
- ran focused API tests remotely
- ran the existing in-process smoke remotely
- imported `topiclab-backend/main.py` remotely with a staging SQLite database
- started a dedicated staging process with:
  - bind address `127.0.0.1`
  - port `18000`
  - SQLite database at `topiclab-backend/runtime_stage.sqlite3`
- validated a real HTTP loop:
  - `/health`
  - `/auth/register-config`
  - `/auth/register` or reuse existing user
  - `/auth/login`
  - `/auth/me`
  - `/api/v1/scales`
  - `/api/v1/scales/rcss`
  - `/api/v1/scales/sessions`
  - `/answer-batch`
  - `/finalize`
  - `/result`

### What worked

- remote dependency installation succeeded with the host's existing Python
- remote focused tests passed:
  - `5 passed`
- remote in-process smoke passed
- remote `main.py` import passed
- remote process-based staging server started successfully
- remote HTTP route-level scale loop completed successfully

### Concrete runtime facts discovered

- the host was usable as a process-based staging environment
- Docker was not available there, so Docker-compose deployment was not the
  right first path
- the server process was left running as:
  - `uvicorn main:app --host 127.0.0.1 --port 18000`
- runtime pid was recorded under:
  - `/root/topiclab-portrait-staging/logs/topiclab_backend_18000.pid`
- runtime log was recorded under:
  - `/root/topiclab-portrait-staging/logs/topiclab_backend_18000.log`

### Real pitfall discovered

The first remote HTTP smoke failed once for a non-backend reason:

- the smoke request used the wrong RCSS question ids (`q1` ... `q8`)
- the canonical definition actually uses `A1` ... `A4` and `B1` ... `B4`

That pitfall was fixed and then converted into a reusable project script:

- `scripts/scales_runtime_http_smoke.py`

### Current best-known staging path

For early portrait-runtime validation, prefer this order:

1. process-based staging on a non-production host
2. remote HTTP smoke using `scripts/scales_runtime_http_smoke.py`
3. only then decide whether Dockerized deployment is necessary for that host
4. only after staging is stable, move toward shared CLI adapters and production

### Important network conclusion from SSH-side diagnostics

Further SSH-side diagnostics on the staging host established the following:

- the host is running inside a container-style network namespace
- the container-visible address is private:
  - `172.17.0.2`
- the current portrait staging process is listening on:
  - `0.0.0.0:18000`

This means:

- the remote runtime is healthy from inside the host
- but the current platform path still does not expose that runtime as a usable
  public HTTP service
- so the current user-facing CLI closure still depends on an operator bridge
  such as SSH port forwarding or a separate public tunnel layer

Observed external behavior from the local machine:

- TCP to external ports `80`, `443`, and `18000` was reachable
- `http://connect.westb.seetacloud.com:18000/health` still closed without a
  usable HTTP response
- `http://connect.westb.seetacloud.com/health` still closed without a usable
  HTTP response
- `https://connect.westb.seetacloud.com/health` still failed TLS/HTTP
- direct public-IP probes on `http://116.172.93.108:18000/health` and
  `http://116.172.93.108/health` returned `503 Service Unavailable`
- a direct no-SSH CLI probe against
  `http://116.172.93.108:18000` returned:
  - `{"ok": false, "status_code": 503, "detail": "Service Unavailable"}`

Current best interpretation:

- the platform or edge path exists
- but the application is still not exposed as a real public HTTP service for
  arbitrary external callers
- rebinding the runtime from `127.0.0.1` to `0.0.0.0` was necessary, but not
  sufficient
- the remaining blocker is now clearly at the provider ingress / public
  exposure layer, not at the portrait runtime itself

So, at this stage, SSH was sufficient to confirm the main blocker:

- the product path is now blocked primarily by provider-side ingress / public
  exposure, not by missing portrait business logic

### AutoDL-specific ingress resolution that actually worked

The same non-production host was later confirmed to be an AutoDL instance with
official "custom service" ingress already enabled:

- `6006 -> http`
- `6008 -> http`

The effective public mapping obtained from the platform UI was:

- `http://127.0.0.1:6006`
  ->
  `https://u394499-8634-23d284fb.westb.seetacloud.com:8443`

What was then done:

- started the portrait runtime directly on:
  - `127.0.0.1:6006`
- kept the same staging SQLite database and testing env values
- probed the AutoDL public custom-service URL directly from the local machine
- validated the standalone CLI against that public HTTPS URL with no SSH tunnel

What worked:

- `GET /health` on the AutoDL public HTTPS URL returned `200`
- standalone CLI `auth ensure` succeeded against the public URL
- standalone CLI `list` succeeded against the public URL
- standalone CLI `run --scale rcss` succeeded against the public URL
- standalone CLI `result <session_id>` succeeded from a separate invocation

Concrete validated result:

- the direct no-SSH public CLI closure succeeded on:
  - `https://u394499-8634-23d284fb.westb.seetacloud.com:8443`
- returned RCSS result still matched expectation:
  - `CSI = 24.0`
  - `type = 强整合型`

Updated interpretation:

- raw public-IP or raw custom port probing is not the right product path on
  AutoDL
- the correct product path is the platform-provided HTTPS custom-service URL
- on AutoDL, the public-ingress problem is solved by the platform's custom
  service layer rather than by direct port exposure

### Cloud-side persistence revalidated from a real CLI test

On 2026-04-11, after a separate agent reported a successful RCSS run through
the unified portrait CLI entry, the cloud staging host was checked directly to
confirm that the interaction was not merely local CLI state.

The reported runtime identifiers were:

- portrait session:
  - `pts_35a0dca6ba754303`
- scale session:
  - `scs_6869507974d242a2`

Cloud-side checks that were run:

- grepped the staging HTTP log:
  - `/root/topiclab-portrait-staging/logs/topiclab_backend_6006.log`
- queried the staging SQLite database:
  - `/root/topiclab-portrait-staging/topiclab-backend/topiclab_staging.sqlite3`

What was confirmed on the cloud host:

- repeated `POST /api/v1/portrait/sessions/pts_35a0dca6ba754303/respond`
  requests were present in the HTTP log
- the portrait session row existed in `portrait_sessions`
- linked refs existed in `portrait_session_runtime_refs` for:
  - `dialogue_session = dgs_48660b8a48dc4185`
  - `scale_session = scs_6869507974d242a2`
  - `portrait_state = pst_9ad02a8a52464266`
- the full event trail existed in `portrait_session_events`
- the scale session row existed in `scale_sessions` with:
  - `scale_id = rcss`
  - `status = completed`
- all 8 answers existed in `scale_session_answers`
- the computed RCSS result existed in `scale_results` with:
  - `integration = 24`
  - `depth = 13`
  - `CSI = 11`
  - `type = 倾向整合型`
- the portrait state row and observations existed in:
  - `portrait_current_states`
  - `portrait_observations`

This revalidated the intended product shape:

- local CLI installation does not imply local-only runtime behavior
- the CLI is the client surface
- the actual portrait workflow, logs, and durable records live on the cloud
  staging host
