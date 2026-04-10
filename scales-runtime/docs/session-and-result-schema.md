# Scale Session And Result Schema

## Purpose

This document defines the proposed runtime objects behind the scale CLI system.

It focuses on:

- session state
- answer writes
- finalize semantics
- result payloads

The goal is to ensure the system can support multi-step interaction without ambiguity.

## Schema Philosophy

The schema should optimize for:

- resumability
- strict validation
- stable scoring
- downstream reuse

It should not optimize for one-off shortcut scripts at the cost of runtime clarity.

## Core Objects

The runtime should revolve around three core objects:

- `scale_definition`
- `scale_session`
- `scale_result`

## `scale_definition`

This is the canonical questionnaire specification.

Recommended fields:

- `scale_id`
- `name`
- `description`
- `instructions`
- `min_val`
- `max_val`
- `min_label`
- `max_label`
- `questions`
- `dimensions`
- `scoring_mode`
- `definition_version`

### Question shape

Recommended question fields:

- `id`
- `text`
- `dimension`
- `reverse`
- `required`

### Dimension shape

Recommended dimension fields:

- `id`
- `name`
- `question_ids`

## `scale_session`

This is the mutable interaction object.

It tracks:

- which scale is being answered
- who is answering
- what is already answered
- whether the session can continue or finalize

Recommended fields:

- `session_id`
- `scale_id`
- `status`
- `actor_type`
- `actor_id`
- `created_at`
- `updated_at`
- `completed_at`
- `abandoned_at`
- `answer_count`
- `required_count`
- `missing_question_ids`
- `last_answered_question_id`
- `next_question_id`
- `session_version`
- `definition_version`
- `scoring_version`

### Status enum

Recommended allowed values:

- `initialized`
- `in_progress`
- `ready_to_finalize`
- `completed`
- `abandoned`

### Meaning of each state

- `initialized`
  - session exists, no accepted answers yet
- `in_progress`
  - at least one answer accepted, but not all required items are present
- `ready_to_finalize`
  - all required items exist and scoring may run
- `completed`
  - answers are frozen and a result exists
- `abandoned`
  - session was explicitly stopped or archived

## `answer_record`

Although the CLI may send simple values, the backend should think in terms of answer records.

Recommended fields:

- `session_id`
- `question_id`
- `value`
- `answered_at`
- `source`
- `source_detail`

The first version may only need `question_id` and `value`, but the schema should leave room for future provenance.

## Single-Answer Write Contract

For `topiclab scales answer`, recommended request body:

```json
{
  "question_id": "A1",
  "value": 6
}
```

Validation rules:

- `question_id` must belong to the session scale
- `value` must be numeric and within `[min_val, max_val]`
- write is rejected if session is already `completed` or `abandoned`

Recommended response:

```json
{
  "session": {
    "session_id": "scs_123",
    "scale_id": "rcss",
    "status": "in_progress"
  },
  "accepted_answer": {
    "question_id": "A1",
    "value": 6
  },
  "progress": {
    "answered_count": 1,
    "required_count": 8,
    "remaining_count": 7,
    "missing_question_ids": ["A2", "A3", "A4", "B1", "B2", "B3", "B4"]
  },
  "next_question": {
    "id": "A2",
    "text": "..."
  },
  "allowed_actions": ["answer", "answer_batch"]
}
```

## Batch-Answer Write Contract

For `topiclab scales answer-batch`, recommended request body:

```json
{
  "answers": {
    "A1": 6,
    "A2": 5,
    "A3": 4
  }
}
```

Validation rules:

- every key must be a valid question id
- every value must be in scale range
- merge semantics should be explicit

Recommended merge rule in v1:

- last write wins within the same session

## Finalize Contract

`finalize` is where the runtime converts accepted answers into a durable scored result.

Recommended request:

```json
{}
```

The backend should infer the session target from the URL/command and should not require the caller to resubmit the full answer sheet.

### Finalize preconditions

The backend should refuse finalize when:

- required answers are missing
- session is abandoned
- session does not exist

### Finalize semantics

When finalize succeeds:

- session status becomes `completed`
- answers become frozen for that session
- canonical scoring runs
- a `scale_result` object is persisted
- the result payload is returned immediately

## `scale_result`

This is the immutable scored output for a completed session.

Recommended fields:

- `session_id`
- `scale_id`
- `completed_at`
- `definition_version`
- `scoring_version`
- `answers`
- `dimension_scores`
- `derived_scores`
- `result_summary`

### `answers`

Recommended shape:

```json
{
  "A1": 6,
  "A2": 5
}
```

### `dimension_scores`

This is the direct per-dimension output after reverse handling and aggregation.

Examples:

- `rcss`
  - `integration`
  - `depth`
- `mini-ipip`
  - `E`
  - `A`
  - `C`
  - `N`
  - `I`
- `ams`
  - `know`
  - `accomplishment`
  - `stimulation`
  - `identified`
  - `introjected`
  - `external`
  - `amotivation`

### `derived_scores`

This is where special indices live.

Examples:

#### RCSS

```json
{
  "I": 20,
  "D": 11,
  "CSI": 9,
  "type": "倾向整合型"
}
```

#### AMS

```json
{
  "intrinsicTotal": 15.25,
  "extrinsicTotal": 10.5,
  "RAI": 21.75
}
```

#### Mini-IPIP

Mini-IPIP may not need a heavy derived object in v1, but may later expose:

- optional level labels
- percentiles if norms are added

### `result_summary`

This should be compact and safe for downstream callers.

Recommended properties:

- one-line summary
- optional lightweight interpretation hints

It should not become a long LLM-generated essay in the base runtime.

## Recommended Session Status Payload

When reading a live session, recommended response shape:

```json
{
  "session": {
    "session_id": "scs_123",
    "scale_id": "rcss",
    "status": "in_progress",
    "created_at": "2026-04-10T12:00:00Z",
    "updated_at": "2026-04-10T12:03:00Z",
    "completed_at": null
  },
  "progress": {
    "answered_count": 3,
    "required_count": 8,
    "remaining_count": 5,
    "missing_question_ids": ["A4", "B1", "B2", "B3", "B4"]
  },
  "answers": {
    "A1": 6,
    "A2": 5,
    "A3": 4
  },
  "next_question": {
    "id": "A4",
    "text": "...",
    "dimension": "integration"
  },
  "allowed_actions": ["answer", "answer_batch"]
}
```

## Recommended Completed Result Payload

```json
{
  "session": {
    "session_id": "scs_123",
    "scale_id": "rcss",
    "status": "completed",
    "completed_at": "2026-04-10T12:06:00Z"
  },
  "result": {
    "definition_version": "v1",
    "scoring_version": "v1",
    "answers": {
      "A1": 6,
      "A2": 5,
      "A3": 6,
      "A4": 5,
      "B1": 3,
      "B2": 2,
      "B3": 3,
      "B4": 3
    },
    "dimension_scores": {
      "integration": 22,
      "depth": 11
    },
    "derived_scores": {
      "I": 22,
      "D": 11,
      "CSI": 11,
      "type": "倾向整合型"
    },
    "result_summary": {
      "headline": "RCSS completed",
      "short_text": "CSI=11, 倾向整合型"
    }
  },
  "allowed_actions": ["read_result"]
}
```

## Versioning Rules

The schema must support future evolution without silent breakage.

At minimum, result payloads should record:

- `definition_version`
- `scoring_version`

This makes regression testing and future migration far safer.

## Why These Objects Are Separate From Portrait Output

The portrait system may later consume scale outputs and render:

- richer natural-language analysis
- profile sections
- shareable cards

But the scale runtime should stop at structured, stable, machine-readable output.

This keeps:

- the runtime predictable
- the scoring testable
- the CLI reusable

## Initial V1 Boundary

For V1, the schema should be strict but modest.

Required:

- session states
- single answer write
- batch answer write
- finalize
- result read
- direct dimension scores
- derived scores
- version fields

Not required yet:

- percentile norms
- evidence annotations
- LLM interpretation essays
- scientist-specific provenance

## Recommended Next Step

After this schema is accepted, the next implementation doc should define:

- the backend API endpoints
- exact CLI-to-endpoint mapping
- stable error codes and exit-code policy
