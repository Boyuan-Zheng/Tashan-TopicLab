# Portrait Prompt And Import First Batch

## Purpose

This document records the first executable backend batch for:

- prompt handoff runtime
- import-result runtime

The goal of this batch was not to finish the whole portrait pipeline, but to
prove that external-AI handoff and pasted-result import can live inside the new
`topiclab-backend/app/portrait/` domain with durable server-side storage.

## Scope Of This Batch

Implemented in this step:

- prompt handoff request creation
- prompt artifact persistence
- handoff listing / lookup
- handoff cancel
- imported external result persistence
- deterministic parse runs
- parsed-result reread

Not claimed as complete in this batch:

- richer parser strategies beyond the first deterministic pass
- artifact download / export surface
- full CLI command surface for prompt/import

## Implemented Backend Files

### API

- `app/portrait/api/prompt_handoff.py`
- `app/portrait/api/import_results.py`
- `app/api/prompt_handoff.py`
- `app/api/import_results.py`

### Services

- `app/portrait/services/prompt_handoff_service.py`
- `app/portrait/services/import_result_service.py`
- `app/portrait/services/import_parse_service.py`

### Storage

- `app/portrait/storage/prompt_handoff_repository.py`
- `app/portrait/storage/import_result_repository.py`

### Schemas

- `app/portrait/schemas/prompt_handoff.py`
- `app/portrait/schemas/import_results.py`

### Shared integration touched in this batch

- `app/portrait/storage/portrait_state_repository.py`
- `app/storage/database/postgres_client.py`
- `main.py`

## Implemented Routes

### Prompt handoff

- `POST /api/v1/portrait/prompt-handoffs`
- `GET /api/v1/portrait/prompt-handoffs`
- `GET /api/v1/portrait/prompt-handoffs/{handoff_id}`
- `POST /api/v1/portrait/prompt-handoffs/{handoff_id}/cancel`

### Import result

- `POST /api/v1/portrait/import-results`
- `GET /api/v1/portrait/import-results/{import_id}`
- `POST /api/v1/portrait/import-results/{import_id}/parse`
- `GET /api/v1/portrait/import-results/{import_id}/parsed`

## Added Durable Tables

- `portrait_prompt_handoffs`
- `portrait_prompt_artifacts`
- `portrait_import_results`
- `portrait_import_parse_runs`

## Runtime Behavior Proven In This Batch

### Prompt handoff

The prompt handoff runtime can now:

- create a handoff record from:
  - optional `dialogue_session_id`
  - optional `portrait_state_id`
  - optional `note_text`
- generate and persist a prompt artifact
- list and reread handoff records
- cancel a pending handoff

The first prompt generation path is deterministic and server-owned. It does not
depend on the frontend to keep prompt text as the source of truth.

### Import result

The import-result runtime can now:

- persist external AI output payloads
- create parse runs
- return deterministic parse outputs
- auto-apply parsed results into canonical portrait state

The first parser behaviors validated in this batch are:

- `json_passthrough`
- `text_outline`

The current parsed output shape still returns a
`candidate_state_patch`-style payload, but the first executable implementation
now also immediately materializes that patch into canonical portrait state
through `portrait_state_service.apply_update(source_type="import_result", ...)`.

That means parse now returns:

- `import_result`
- `parse_run`
- `state_update`
- `auto_applied_to_portrait_state = true`

## Validation Completed

### Local validation

Executed:

```bash
cd topiclab-backend
python3 -m py_compile \
  app/portrait/services/prompt_handoff_service.py \
  app/portrait/services/import_parse_service.py \
  app/portrait/services/import_result_service.py \
  app/portrait/api/prompt_handoff.py \
  app/portrait/api/import_results.py \
  app/api/prompt_handoff.py \
  app/api/import_results.py \
  tests/test_prompt_import_runtime_api.py

python3 -m pytest -q \
  tests/test_prompt_import_runtime_api.py \
  tests/test_portrait_state_api.py \
  tests/test_dialogue_runtime_api.py \
  tests/test_scales_runtime_api.py
```

Observed result:

- `14 passed`

### Remote AutoDL staging validation

Executed on the staging workspace after file sync:

```bash
cd /root/topiclab-portrait-staging/topiclab-backend
/root/miniconda3/bin/python -m pytest -q \
  tests/test_prompt_import_runtime_api.py \
  tests/test_portrait_state_api.py
```

Observed result:

- `5 passed`

### Public no-SSH validation

Validation was performed against the AutoDL custom-service HTTPS URL, not
through SSH tunneling.

Observed public path:

1. create portrait-state update
2. create prompt handoff
3. create import result
4. parse import result
5. observe auto-created portrait-state update

Observed public runtime artifacts:

- `portrait_state_id = pst_103b9a790c864f75`
- `handoff_id = phf_30a45386b3be4a29`
- `import_id = pir_4d10cc62192f49eb`

The public parsed payload contained a deterministic
`candidate_state_patch.external_import` block derived from the pasted text, and
that parse result was then auto-materialized into the canonical
`portrait_current_states` substrate.

## Real Operational Pitfall

On AutoDL, the public custom-service process bound to internal `6006` did not
restart reliably from a blind `nohup` unless the shell explicitly loaded the
project `.env`.

Without explicit environment loading, startup could fail with:

- `ValueError("DATABASE_URL is not set")`

For this staging target, process startup should therefore source the project
environment before launching `uvicorn`.

## What Remains After This Batch

- CLI command surface for prompt handoff / import-result
- richer parsing strategies
- artifact/export runtime
- deeper orchestration between dialogue, prompt handoff, import, and portrait
  state
