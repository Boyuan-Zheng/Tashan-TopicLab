# Standalone Scales CLI Usage Guide

## Scope

This guide explains how to use the standalone scales CLI as a user-facing tool.

It complements:

- `scales-runtime/cli/README.md`
- `scales-runtime/docs/standalone-cli.md`

This guide focuses on:

- command surface
- arguments
- auth modes
- common workflows
- common errors

It does **not** describe the future shared `TopicLab-CLI` integration. It
describes the current standalone CLI that lives in:

- `/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py`

## Important Current Reality

Today there are two different remote access situations:

- if the portrait backend is directly reachable over HTTP/HTTPS, the CLI can
  call it directly
- if the portrait backend is only reachable on the remote server's localhost,
  an operator bridge such as SSH port forwarding is still needed

That SSH bridge is an operational workaround, not the final product design.

## Command Entry

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py --help
```

## Global Options

These options apply to all commands:

- `--state-dir <path>`
  - state directory for local sqlite + state file
  - default: `~/.topiclab-scales-runtime`
- `--auth-mode <auto|local_password|bind_key>`
  - auth provider selection
  - `auto` prefers `bind_key` if one exists in args or persisted state
- `--base-url <url>`
  - required for remote `bind_key` mode
  - also used when `local_password` should talk to a remote backend
- `--bind-key <key>`
  - required for `bind_key` mode
- `--json`
  - emit compact JSON

These global options can be placed either:

- before the subcommand
- or after the subcommand

Both forms are supported.

## Auth Modes

### `local_password`

Use this mode when:

- you want to validate the runtime independently on this machine
- you want the CLI to boot the local minimal backend harness in-process
- or you want to use `/auth/register` and `/auth/login` against a remote
  staging backend

This mode uses:

- `/auth/login`
- `/auth/register`

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --auth-mode local_password \
  auth ensure --phone 13800052001 --username demo --password password123 --json
```

Remote staging example through a temporary SSH tunnel:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --auth-mode local_password \
  --base-url http://127.0.0.1:18080 \
  auth ensure --phone 13800138001 --username stage-smoke-user --password StagePass123 --json
```

### `bind_key`

Use this mode when:

- you want to align state and auth shape with the future shared CLI
- you have a real OpenClaw bind key

This mode uses:

- `GET /api/v1/openclaw/bootstrap`
- `POST /api/v1/openclaw/session/renew`

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --auth-mode bind_key \
  --base-url https://world.tashan.chat \
  --bind-key tlos_xxx \
  auth ensure --json
```

Validated live note:

- on 2026-04-10, this auth bootstrap path was successfully run against
  `https://world.tashan.chat`
- it returned a real `access_token`, `agent_uid`, and `openclaw_agent`
- the next scale commands then returned `404 Not Found`, which shows the live
  site auth path is ready but the `/api/v1/scales/...` route family is not yet
  deployed there

## Command Reference

### `auth ensure`

Purpose:

- bootstrap authentication and persist reusable auth state

Arguments:

- `--phone`
  - local password mode only
- `--username`
  - local password mode only
- `--password`
  - local password mode only

Examples:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py auth ensure --json
```

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --auth-mode bind_key --base-url https://world.tashan.chat --bind-key tlos_xxx \
  auth ensure --json
```

### `list`

Purpose:

- list available scales

Arguments:

- no command-specific arguments

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py list --json
```

### `get <scale_id>`

Purpose:

- fetch one scale definition

Arguments:

- `scale_id`
  - one of `rcss`, `mini-ipip`, `ams`

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py get rcss --json
```

### `session start`

Purpose:

- create a new scale session

Arguments:

- `--scale <scale_id>` required
- `--actor-type <human|agent|internal>`
- `--actor-id <id>`

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  session start --scale rcss --actor-type internal --actor-id self-check --json
```

### `session status <session_id>`

Purpose:

- inspect current progress

Arguments:

- `session_id`

Returned state includes:

- session metadata
- progress
- missing question ids
- next question
- allowed actions

### `answer <session_id>`

Purpose:

- write one answer

Arguments:

- `session_id`
- `--question-id <id>` required
- `--value <number>` required

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  answer scs_123 --question-id A1 --value 6 --json
```

### `answer-batch <session_id>`

Purpose:

- write many answers in one request

Arguments:

- `session_id`
- `--answers-json <json>`
- `--answers-file <file>`

Accepted file/input shapes:

- plain answer object
  - `{"A1": 6, "A2": 5}`
- fixture object with top-level `answers`
  - `{"scale_id":"rcss","answers":{"A1":6}}`

Examples:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  answer-batch scs_123 --answers-json '{"A1":6,"A2":5}' --json
```

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  answer-batch scs_123 --answers-file /path/to/answers.json --json
```

### `finalize <session_id>`

Purpose:

- finalize scoring after all required answers are present

Arguments:

- `session_id`

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py finalize scs_123 --json
```

### `result <session_id>`

Purpose:

- fetch persisted result

Arguments:

- `session_id`

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py result scs_123 --json
```

### `sessions list`

Purpose:

- list sessions visible to the current auth user

Arguments:

- no command-specific arguments

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py sessions list --json
```

### `sessions abandon <session_id>`

Purpose:

- explicitly abandon one incomplete session

Arguments:

- `session_id`

Example:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py sessions abandon scs_123 --json
```

### `run`

Purpose:

- run a full questionnaire loop
- create or resume a session
- collect answers
- finalize
- return the result

Arguments:

- `--scale <scale_id>` required
- `--actor-type <human|agent|internal>`
- `--actor-id <id>`
- `--answers-json <json>`
- `--answers-file <file>`
- `--session-id <id>`

Behavior:

- without `--answers-json` or `--answers-file`
  - prompts interactively in the terminal
- with answers input
  - writes answers directly and finalizes

Examples:

Interactive:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py run --scale rcss
```

Fixture-driven:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  run --scale rcss --answers-file /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/fixtures/rcss-strong-integration.json --json
```

## Common Workflows

### Fast local smoke

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py auth ensure --json
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py list --json
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py run --scale rcss
```

### Live bind-key auth smoke

This validates the real OpenClaw-compatible auth path without yet assuming the
live site has deployed the new scales routes:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --auth-mode bind_key \
  --base-url https://world.tashan.chat \
  --bind-key tlos_xxx \
  auth ensure --json
```

If the live site has not yet deployed the new scale runtime routes, these
commands are expected to fail with `404 Not Found`:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --auth-mode bind_key \
  --base-url https://world.tashan.chat \
  --bind-key tlos_xxx \
  list --json
```

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --auth-mode bind_key \
  --base-url https://world.tashan.chat \
  --bind-key tlos_xxx \
  get rcss --json
```

### Resume an interrupted session

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py sessions list --json
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py session status scs_123 --json
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py run --scale rcss --session-id scs_123
```

## Common Errors

- `missing_base_url`
  - bind-key mode was selected but no base URL is available
- `missing_bind_key`
  - bind-key mode was selected but no bind key is available
- `missing_access_token`
  - auth bootstrap did not produce an access token
- `404 Not Found`
  - the selected remote base URL does not yet expose `/api/v1/scales/...`
  - this is currently the expected response from `https://world.tashan.chat`
    until the new runtime routes are deployed there
- `session_not_ready`
  - finalize was attempted before all required answers were present
- `invalid_question_id`
  - answer referenced a question that does not exist in the selected scale
- `invalid_answer_value`
  - answer value is outside the allowed numeric range

## Current Known Constraint

One `--state-dir` should be used serially.

Do not run multiple standalone CLI processes in parallel against the same state
directory, or SQLite may report:

- `database is locked`
