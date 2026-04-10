# Scale CLI Protocol

## Purpose

This document defines the proposed CLI surface for the reusable scale runtime.

The goal is not to make `topiclab-cli` smart about portrait logic. The goal is to expose a stable, resumable, JSON-first command surface that any caller can use:

- a human operating from the terminal
- an OpenClaw or other agent runtime
- an internal batch runner
- future validation workflows based on built-in twins

The CLI is intentionally thin. It should call backend APIs and return state, not reimplement scoring or business interpretation locally.

## Design Principles

### 1. State machine first

The CLI should never assume a caller can remember prior state.

Every command should either:

- create a new scale session
- advance a session
- inspect a session
- finalize a session
- read the finalized result

### 2. JSON-first for agent use

Every scale command should support `--json`.

This is mandatory because the main target is durable agent use, not only manual terminal usage.

### 3. Thin command surface

The CLI should avoid embedding:

- question banks
- scoring formulas
- scale interpretation text

Those belong to backend truth and the scale runtime domain assets.

### 4. Stable failure semantics

Failures must be machine-readable. Agents should not have to parse prose to know whether to retry, continue, or restart.

## Command Groups

The proposed namespace is:

- `topiclab scales ...`

Recommended first version:

- `topiclab scales list`
- `topiclab scales get <scale_id>`
- `topiclab scales session start`
- `topiclab scales session status`
- `topiclab scales answer`
- `topiclab scales answer-batch`
- `topiclab scales finalize`
- `topiclab scales result`
- `topiclab scales sessions list`
- `topiclab scales sessions abandon`

## Command Details

### `topiclab scales list`

Purpose:

- list scale definitions that are currently available for CLI/runtime use

Example:

```bash
topiclab scales list --json
```

Expected payload:

- list of scale ids
- display names
- short descriptions
- question counts
- min/max score range per scale

Recommended JSON shape:

```json
{
  "list": [
    {
      "scale_id": "rcss",
      "name": "科研认知风格量表 (RCSS)",
      "question_count": 8,
      "score_range": { "min": 1, "max": 7 }
    }
  ]
}
```

### `topiclab scales get <scale_id>`

Purpose:

- fetch one scale definition for machine or UI use

Example:

```bash
topiclab scales get rcss --json
```

Expected payload:

- scale metadata
- question list
- dimension list
- answer range labels

This command should be sufficient for:

- custom terminal UIs
- agents reading the next question
- regression tests verifying the question registry

### `topiclab scales session start`

Purpose:

- create a new answer session for one scale

Example:

```bash
topiclab scales session start --scale rcss --json
```

Recommended options:

- `--scale <scale_id>` required
- optional `--mode <mode>`
- optional `--actor-type <human|agent|internal>`
- optional `--actor-id <id>`
- optional `--context-json <json>`

The first version does not need every option implemented, but the session format should leave room for them.

Expected response:

- `session_id`
- `status`
- `scale`
- `answered_count`
- `remaining_count`
- `next_question`
- `allowed_actions`

### `topiclab scales session status <session_id>`

Purpose:

- read current state without mutating anything

Example:

```bash
topiclab scales session status scs_123 --json
```

This is the main recovery entrypoint for interrupted agents.

Expected response:

- session summary
- answered question ids
- missing question ids
- next unanswered question
- whether finalize is allowed

### `topiclab scales answer <session_id>`

Purpose:

- submit one question answer at a time

Example:

```bash
topiclab scales answer scs_123 --question-id A1 --value 6 --json
```

Recommended required options:

- `--question-id <id>`
- `--value <number>`

Expected response:

- updated session state
- accepted answer echo
- new `next_question`
- `allowed_actions`

This command is the safest primitive for persistent agents.

### `topiclab scales answer-batch <session_id>`

Purpose:

- submit multiple answers in one request when the caller already has a full or partial sheet

Example:

```bash
topiclab scales answer-batch scs_123 --answers-json '{"A1":6,"A2":5}' --json
```

Recommended behavior:

- validate every submitted question id
- reject invalid values with a structured error
- accept partial sheets
- return merged session state

### `topiclab scales finalize <session_id>`

Purpose:

- freeze answers and trigger canonical scoring

Example:

```bash
topiclab scales finalize scs_123 --json
```

Rules:

- should fail if required questions are still missing
- should be idempotent once completed
- should return structured result payload, not just `ok: true`

### `topiclab scales result <session_id>`

Purpose:

- fetch the finalized result without mutating the session

Example:

```bash
topiclab scales result scs_123 --json
```

Expected use cases:

- user revisit
- frontend read
- scientist-twin batch pipeline
- regression testing

### `topiclab scales sessions list`

Purpose:

- list recent sessions for the current caller

Useful filters:

- `--status`
- `--scale`
- `--limit`

This is useful for both users and agents resuming work.

### `topiclab scales sessions abandon <session_id>`

Purpose:

- explicitly mark a session as abandoned or inactive

This is optional in v1 but useful for state hygiene and agent recovery.

## Recommended Response Envelope

For stateful commands, the response should be structurally consistent.

Recommended top-level envelope:

```json
{
  "session": {},
  "scale": {},
  "progress": {},
  "next_question": null,
  "allowed_actions": []
}
```

Suggested meanings:

- `session`: identity and lifecycle state
- `scale`: lightweight scale metadata
- `progress`: counters and missing ids
- `next_question`: the next unresolved prompt or `null`
- `allowed_actions`: explicit machine-readable next steps

## `allowed_actions` Convention

This field is important for durable agent execution.

Recommended values:

- `answer`
- `answer_batch`
- `finalize`
- `read_result`
- `abandon`

This avoids forcing agents to infer control flow from prose.

## Error Model

Errors should remain JSON-first and use stable error codes.

Recommended failure families:

- `scale_not_found`
- `session_not_found`
- `session_completed`
- `session_not_ready`
- `invalid_question_id`
- `invalid_answer_value`
- `duplicate_finalize`
- `auth_required`
- `permission_denied`
- `backend_unavailable`

Recommended error payload:

```json
{
  "ok": false,
  "error": {
    "code": "invalid_answer_value",
    "message": "Answer value must be within the scale range.",
    "detail": {
      "question_id": "A1",
      "expected_min": 1,
      "expected_max": 7,
      "received": 9
    }
  }
}
```

## CLI Output Modes

### JSON mode

Primary mode for agents and tests:

```bash
topiclab scales session status scs_123 --json
```

### Human-readable mode

Optional convenience mode for manual users.

This mode should be readable, but must not become the only form of critical information.

## Why We Do Not Add Scientist Logic Here

The CLI protocol is universal.

It must work even if:

- no scientist-twin system exists
- a normal user uses it directly
- a scripted evaluation runner uses it

Scientist twins are an important future caller, but they are not the protocol.

## Implementation Boundary

This protocol implies:

- command wiring in `TopicLab-CLI`
- session APIs in `topiclab-backend`
- canonical schemas and scoring in `scales-runtime`

It does not imply:

- immediate frontend migration
- immediate scientist auto-answering
- immediate type-classification logic

## First Implementation Target

The smallest coherent CLI slice is:

1. `list`
2. `get`
3. `session start`
4. `session status`
5. `answer`
6. `answer-batch`
7. `finalize`
8. `result`

That is enough to support:

- manual CLI runs
- durable agent interaction
- internal twin testing
- later frontend convergence
