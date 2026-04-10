# Scales Runtime

This directory is the dedicated domain workspace for TopicLab's reusable scale runtime.

It exists to keep portrait- and scale-specific assets decoupled from the rest of the product while still integrating cleanly with the existing CLI-first infrastructure.

## Scope

This domain is responsible for:

- canonical scale definitions
- canonical scoring rules
- session / answer / result schemas
- fixtures for regression tests and batch runs
- architecture and rollout docs for scale CLI support

This domain is not responsible for:

- generic `topiclab-cli` infrastructure
- unrelated TopicLab topic / arcade / skill-hub behavior
- frontend page rendering details
- long-term scientist typing logic

## Directory Layout

```text
scales-runtime/
├── README.md
├── definitions/   # Canonical scale definitions shared by user and agent workflows
├── scoring/       # Canonical scoring rules and derived-index logic
├── schemas/       # Stable session / answer / result payload contracts
├── fixtures/      # Sample inputs / outputs for regression and smoke validation
└── docs/          # Architecture, protocol, rollout, and implementation notes
```

## Integration Boundary

- `TopicLab-CLI` should stay thin and call stable backend APIs.
- `topiclab-backend` should own session lifecycle, result persistence, and server-side scoring truth.
- This directory should own the domain-specific assets and docs that define what the scale system means.

## Current Focus

The current implementation target is:

1. define a reusable scale CLI protocol for humans and agents
2. ensure sessions can continue instead of collapsing into one-shot interactions
3. ensure answers always flow through one canonical scoring path
4. return structured results that can later feed portrait rendering and internal scientist-twin testing

## Current Local Status

The workspace now contains:

- normalized definition files for `rcss`, `mini-ipip`, and `ams`
- a registry file for runtime discovery
- a thin TopicLab-backend skeleton that can already expose scale definitions under the new `/api/v1/scales` route family
- a working backend runtime loop for session -> answer -> finalize -> result
- a first portrait-domain migration batch in `topiclab-backend/app/portrait/`
  with compatibility shims preserving the old scale-runtime entry points
- a real standalone CLI under `scales-runtime/cli/`
- a dual-provider auth structure in that standalone CLI:
  - `local_password` for independent local closure
  - `bind_key` for future `TopicLab-CLI` migration compatibility
- standalone validation assets:
  - `topiclab-backend/tests/test_scales_runtime_api.py`
  - `scripts/scales_runtime_smoke.py`
  - `scripts/scales_runtime_http_smoke.py`

What is still intentionally missing:

- full migration of the portrait command surface into `TopicLab-CLI`
- migration of the heavier legacy portrait-builder flows out of `Resonnet`

## Verified Portrait Runtime Slices

The first executable portrait-domain slice is `scales`.

Validated path:

- backend implementation lives under `topiclab-backend/app/portrait/`
- old top-level backend files stay as compatibility adapters
- focused API tests pass
- standalone smoke still passes after the ownership move
- remote process-based staging validation has also passed on a non-production host
- direct no-SSH public CLI closure has been validated on a non-production
  AutoDL host through its official custom-service HTTPS URL
- an initial thin `topiclab-cli` adapter now exists for the `scales` slice
- a first durable `dialogue` runtime skeleton now also exists under
  `topiclab-backend/app/portrait/`, with focused tests and standalone smoke
- a first thin `topiclab-cli` adapter now also exists for the `dialogue`
  slice:
  - `topiclab portrait auth ensure`
  - `topiclab portrait dialogue start`
  - `topiclab portrait dialogue status`
  - `topiclab portrait dialogue send`
  - `topiclab portrait dialogue messages`
  - `topiclab portrait dialogue derived-state`
  - `topiclab portrait dialogue close`
- that dialogue path has been validated end-to-end against the AutoDL public
  HTTPS custom-service URL without using SSH tunnels
- a first canonical `portrait state` runtime now also exists under
  `topiclab-backend/app/portrait/`, with:
  - current-state reads
  - explicit update materialization
  - version snapshots
  - observations
- a thin `topiclab-cli` adapter now also exists for the `portrait state` slice:
  - `topiclab portrait state current`
  - `topiclab portrait state versions`
  - `topiclab portrait state version`
  - `topiclab portrait state apply`
  - `topiclab portrait state update`
  - `topiclab portrait state observations`
- that state slice has been locally validated through focused API tests and
  `scripts/portrait_state_runtime_smoke.py`, and public AutoDL HTTPS validation
  has now been completed for `current`, `apply`, `versions`, and
  `observations`
- a first prompt-handoff and import-result runtime now also exists under
  `topiclab-backend/app/portrait/`, with:
  - prompt handoff creation, lookup, list, and cancel
  - prompt artifact persistence
  - import-result persistence
  - deterministic parse runs
  - parsed-result reread
- that prompt/import slice has been locally validated, revalidated on AutoDL
  staging, and publicly validated over AutoDL HTTPS without SSH by creating a
  prompt handoff, creating an import result, and parsing it into a
  `candidate_state_patch`-style payload
- a first executable unified `portrait session` orchestrator now also exists
  under `topiclab-backend/app/portrait/`, with:
  - top-level `/api/v1/portrait/sessions` routes
  - durable `portrait_sessions`, runtime refs, and orchestration events
  - `respond(text)` routing into `dialogue` and then `portrait_state`
  - `respond(choice="scale:<id>")` routing into `scales` and then
    `portrait_state`
  - `respond(choice="prompt_handoff")` routing into `prompt_handoff`
  - `respond(external_text|external_json)` routing into `import_result` and
    then `portrait_state`
  - `respond(confirm)` completion path
- that unified session slice has been locally validated through focused backend
  tests and `scripts/portrait_session_runtime_smoke.py`
- it has now been wired into `TopicLab-CLI` as:
  - `topiclab portrait start`
  - `topiclab portrait respond`
  - `topiclab portrait status`
  - `topiclab portrait result`
- the first user-flow control commands now also exist in `TopicLab-CLI`:
  - `topiclab portrait resume`
  - `topiclab portrait history`
  - `topiclab portrait reset`
  - `topiclab portrait export`
- that unified session main entry has now also been publicly validated over
  AutoDL HTTPS without SSH by running:
  - `portrait start`
  - `portrait respond --text`
  - `portrait respond --choice scale:rcss`
  - repeated numeric `portrait respond --choice 7`
  - `portrait respond --choice prompt_handoff`
  - `portrait respond --external-text`
  - `portrait status`
  - `portrait result`
  - `portrait resume`
  - `portrait history`
  - `portrait reset --restart`
  - `portrait export`

## Document Map

- [docs/architecture.md](docs/architecture.md): domain boundary, ownership split, state-machine direction, and canonical scoring policy
- [docs/cli-protocol.md](docs/cli-protocol.md): proposed `topiclab scales ...` command surface and response contract
- [docs/session-and-result-schema.md](docs/session-and-result-schema.md): session lifecycle, answer payloads, finalize semantics, and result object shape
- [docs/backend-api-mapping.md](docs/backend-api-mapping.md): how the new CLI/runtime maps onto TopicLab backend routes, and how it coexists with the legacy Resonnet `profile-helper/scales` flow during migration
- [docs/implementation-plan.md](docs/implementation-plan.md): phased execution plan covering storage objects, versioning, fixtures, CLI rollout, and eventual migration away from Resonnet `scales.json`
- [docs/standalone-closure-and-cli-migration.md](docs/standalone-closure-and-cli-migration.md): why the runtime should be proven in a standalone local closed loop first, and only then be migrated into the existing `topiclab-cli`
- [docs/standalone-cli.md](docs/standalone-cli.md): validated standalone CLI usage, actual command sequence, and the real constraints discovered while running it
- [docs/cli-usage-guide.md](docs/cli-usage-guide.md): user-facing command reference with auth modes, arguments, workflows, examples, and common errors
- [docs/unified-portrait-interaction-architecture.md](docs/unified-portrait-interaction-architecture.md): explains that TopicLab is one portrait application with multiple adapters, and that CLI/agents should extend the same runtime instead of creating a parallel system
- [docs/portrait-system-refactor-architecture.md](docs/portrait-system-refactor-architecture.md): top-level architecture for gradually refactoring the whole portrait system into a dedicated TopicLab application domain with durable server-owned truth
- [docs/unified-portrait-session-protocol.md](docs/unified-portrait-session-protocol.md): target agent-facing main-entry protocol that collapses multiple portrait slices into one server-driven session loop
- [docs/portrait-system-refactor-execution-plan.md](docs/portrait-system-refactor-execution-plan.md): staged execution plan for the full portrait-system refactor: what to migrate first, what to delay, and what counts as done
- [docs/existing-portrait-backend-code-map.md](docs/existing-portrait-backend-code-map.md): factual code map of the historical portrait backend across Resonnet, topiclab-backend, the current frontend wiring, and the new scale-runtime slice
- [../topiclab-cli/skills/topiclab-portrait-cli-test-agent/SKILL.md](../topiclab-cli/skills/topiclab-portrait-cli-test-agent/SKILL.md): single canonical skill in the TopicLab-CLI repo for agents using the new portrait product through local `TopicLab-CLI` against the cloud staging runtime
- [../topiclab-backend/docs/portrait-domain-architecture.md](../topiclab-backend/docs/portrait-domain-architecture.md): defines the target bounded-domain package structure for portrait code inside `topiclab-backend` and the gradual migration rule
- [../topiclab-backend/docs/portrait-scales-first-batch.md](../topiclab-backend/docs/portrait-scales-first-batch.md): concrete first batch for migrating the new scale runtime into the portrait domain while keeping external routes and callers unchanged
- [../topiclab-backend/docs/portrait-dialogue-first-batch.md](../topiclab-backend/docs/portrait-dialogue-first-batch.md): concrete first batch for landing durable portrait dialogue sessions, transcript persistence, and derived-state ownership under `app/portrait/`
- [../topiclab-backend/docs/portrait-state-first-batch.md](../topiclab-backend/docs/portrait-state-first-batch.md): concrete first batch for landing canonical portrait state, explicit update events, version snapshots, and observations under `app/portrait/`
- [../topiclab-backend/docs/portrait-prompt-import-first-batch.md](../topiclab-backend/docs/portrait-prompt-import-first-batch.md): concrete first batch for landing durable prompt handoff requests, prompt artifacts, pasted external-AI results, and deterministic parse runs under `app/portrait/`
- [../topiclab-backend/docs/portrait-session-first-batch.md](../topiclab-backend/docs/portrait-session-first-batch.md): concrete first batch for landing the first executable unified portrait-session orchestrator above `dialogue` and `portrait_state`
- [../topiclab-backend/docs/portrait-backend-backlog.md](../topiclab-backend/docs/portrait-backend-backlog.md): concrete backend-only backlog for the remaining portrait slices after `scales`, including APIs, services, storage, schemas, and proposed tables
