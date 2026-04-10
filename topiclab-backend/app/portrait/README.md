# Portrait Domain Package

This directory is the target bounded domain for TopicLab backend portrait
runtime code.

## Why It Exists

TopicLab is a larger product with many existing capabilities.

Portrait should grow as an internal business domain inside the existing backend,
not as a scattering of portrait-specific files across generic `app/api/` and
`app/services/` forever.

The goal is:

- keep portrait logic as independent as possible from unrelated product areas
- still reuse shared backend infrastructure such as auth, db session helpers,
  and router registration
- support a gradual migration instead of a disruptive rewrite

## Current Status

Executable portrait runtime code now exists here.

Implemented portrait-domain slices:

- `scales`
  - `app/portrait/api/scales.py`
  - `app/portrait/services/scales_service.py`
  - `app/portrait/services/scales_scoring.py`
  - `app/portrait/storage/scales_repository.py`
  - `app/portrait/runtime/definitions_loader.py`
  - `app/portrait/schemas/scales.py`
- `dialogue` first-batch skeleton
  - `app/portrait/api/dialogue.py`
  - `app/portrait/services/dialogue_service.py`
  - `app/portrait/services/dialogue_runtime_service.py`
  - `app/portrait/services/dialogue_summary_service.py`
  - `app/portrait/storage/dialogue_repository.py`
  - `app/portrait/schemas/dialogue.py`
- `portrait_state` first batch
  - `app/portrait/api/portrait_state.py`
  - `app/portrait/services/portrait_state_service.py`
  - `app/portrait/storage/portrait_state_repository.py`
  - `app/portrait/schemas/portrait_state.py`
- `prompt_handoff / import_result` first batch
  - `app/portrait/api/prompt_handoff.py`
  - `app/portrait/services/prompt_handoff_service.py`
  - `app/portrait/storage/prompt_handoff_repository.py`
  - `app/portrait/schemas/prompt_handoff.py`
  - `app/portrait/api/import_results.py`
  - `app/portrait/services/import_result_service.py`
  - `app/portrait/services/import_parse_service.py`
  - `app/portrait/storage/import_result_repository.py`
  - `app/portrait/schemas/import_results.py`
- `portrait_session` first batch
  - `app/portrait/api/session.py`
  - `app/portrait/services/portrait_session_service.py`
  - `app/portrait/services/portrait_orchestration_service.py`
  - `app/portrait/services/portrait_skill_policy_service.py`
  - `app/portrait/storage/portrait_session_repository.py`
  - `app/portrait/schemas/session.py`
  - `app/portrait/runtime/block_protocol.py`
  - `app/portrait/runtime/ai_memory_prompt_loader.py`
  - current routed paths already cover:
    - `text -> dialogue -> portrait_state`
    - `choice(scale:<id>) -> scales -> portrait_state`
    - `choice(prompt_handoff) -> prompt_handoff`
    - `external_text|external_json -> import_result -> portrait_state`
    - `confirm -> completed`
  - current executable `legacy_product` path now routes through the migrated
    old kernel bridge instead of the handwritten policy welcome flow
  - current verified closure:
    - `start(mode=legacy_product)` boots the migrated old-kernel agent loop
    - `respond(...)` normalizes CLI/API inputs into natural-language turns for
      the old kernel
    - runtime refs include:
      - `legacy_kernel_session`
      - `portrait_state`
    - old-kernel snapshots are durably stored in
      `portrait_legacy_kernel_sessions`
    - canonical `portrait_state` is synchronized from legacy markdown plus raw
      `legacy_kernel` state on every turn
  - current cloud-verified behavior:
    - public HTTPS staging can run
      - register
      - session start
      - legacy-product respond
      - result fetch
    - server logs show real migrated old-kernel tool calls such as
      `read_skill`, `read_profile`, `write_profile`
- `legacy_kernel` migration first batch
  - `app/portrait/legacy_kernel/prompts.py`
  - `app/portrait/legacy_kernel/tools.py`
  - `app/portrait/legacy_kernel/profile_parser.py`
  - `app/portrait/legacy_kernel/assets/_template.md`
  - `app/portrait/legacy_kernel/assets/docs/*.md`
  - `app/portrait/legacy_kernel/assets/skills/*/SKILL.md`
  - current factual purpose:
    - own the copied old portrait prompt/tool/skill assets inside the new
      backend package
    - own the migrated old agent loop and its storage/LLM boundary adapters
    - expose that migrated loop through the unified portrait session runtime

Compatibility wrappers remain at old top-level paths where needed, so route
registration and imports can stay stable while internal ownership moves into
this package.

## Intended Layout

```text
app/portrait/
├── __init__.py
├── README.md
├── api/
├── legacy_kernel/
├── services/
├── storage/
├── schemas/
└── runtime/
```

Expected long-term responsibility split:

- `api/`
  - portrait-domain routes only
- `services/`
  - scale runtime
  - portrait dialogue orchestration
  - prompt handoff / import-result handling
- `storage/`
  - portrait repositories and persistence helpers
- `schemas/`
  - request/response payloads and internal contract objects
- `runtime/`
  - loaders, builders, and runtime composition helpers
- `legacy_kernel/`
  - copied old portrait-builder kernel code and assets
  - boundary-adapted incrementally into the new backend

## Migration Principle

Migration into this package should be gradual:

1. keep existing executable paths working
2. move the cleanest bounded slice first
3. keep adapter layers thin
4. avoid touching unrelated product features

The first fully validated slice to migrate here was the new scale runtime.

The second slice now starting to land here is the durable portrait dialogue
runtime skeleton.

The third slice now starting to land here is the canonical portrait-state
runtime.

The fourth slice now starting to land here is the prompt-handoff and
import-result runtime.

The fifth slice now starting to land here is the unified portrait-session
orchestrator.

The sixth migration track now explicitly starts here as well:

- direct old-kernel migration from the accessible historical baseline into
  `app/portrait/legacy_kernel/`

The next old-product-equivalence targets are now explicitly:

- forum profile generation
- scientist matching / recommendations
- export / download artifacts
- publish-to-library side effects

Important current distinction:

- `legacy_product` core collection now runs through the migrated old kernel
- several newer product-side services still exist beside it:
  - scientist matching
  - structured export
  - publish
- those newer services are not the same thing as the old portrait kernel and
  should not be confused with it in migration progress reporting

Those targets now have a first backend batch under this package as well:

- `app/portrait/api/products.py`
- `app/portrait/services/portrait_projection_service.py`
- `app/portrait/services/portrait_artifact_service.py`
- `app/portrait/services/portrait_forum_service.py`
- `app/portrait/services/portrait_scientist_service.py`
- `app/portrait/services/portrait_export_service.py`
- `app/portrait/services/portrait_publish_service.py`
- `app/portrait/storage/portrait_artifact_repository.py`
- `app/portrait/runtime/scientists_reference.py`

That first batch means the new backend now owns:

- forum projection generation
- scientist matching and recommendations
- structured / markdown / HTML export
- PDF / image export endpoints with runtime-dependent rendering
- persisted binary artifact storage plus later re-download
- publish into twin runtime and legacy-compatible twin storage
- durable artifact traceability

Current cloud-validated binary export facts:

- the backend can now render and persist:
  - `profile-pdf`
  - `profile-image`
- durable binary files are stored under:
  - `topiclab-backend/storage/portrait_artifacts/`
- artifact metadata persists:
  - filename
  - content type
  - size
  - server-side storage path
  - re-download route
- the staging runtime requires:
  - a Python interpreter that can import `uvicorn`
  - a real headless-capable browser binary such as
    `google-chrome-stable`

Related implementation note:

- `../../docs/portrait-scales-first-batch.md`
- `../../docs/portrait-dialogue-first-batch.md`
- `../../docs/portrait-state-first-batch.md`
- `../../docs/portrait-prompt-import-first-batch.md`
- `../../docs/portrait-session-first-batch.md`
