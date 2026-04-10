# Standalone Scales CLI

This directory contains the standalone local CLI for the scales runtime.

It exists for one reason:

- prove that the scales domain can already run as a real command-line workflow
- before the same command surface is migrated into `TopicLab-CLI`

## Why It Lives Here

This CLI is scale-domain-specific.

It is intentionally kept out of the shared `TopicLab-CLI` repository for now so
that:

- the runtime can be validated independently
- the command surface can settle before migration
- portrait / scale work stays decoupled from other teams' active CLI changes

## Entry Point

- `standalone_scales_cli.py`

The script boots the minimal local TopicLab backend harness in-process, stores a
persistent SQLite database under a state directory, and reuses the same backend
`/api/v1/scales/...` contract that the future shared CLI will call.

It now has a dual-provider auth shape:

- `local_password`
  - validated local harness mode
  - uses `/auth/login` and `/auth/register`
- `bind_key`
  - migration-aligned mode for future TopicLab-CLI convergence
  - uses `/api/v1/openclaw/bootstrap` and `/api/v1/openclaw/session/renew`

It can also now use `local_password` against a remote backend when `--base-url`
is provided.

That means there are currently two practical validation shapes:

- local harness mode
- local CLI talking to a remote staging backend over HTTP

## Supported Commands

- `auth ensure`
- `list`
- `get <scale_id>`
- `session start`
- `session status`
- `answer`
- `answer-batch`
- `finalize`
- `result`
- `sessions list`
- `sessions abandon`
- `run`

## Default State Directory

By default the CLI persists its local state under:

- `~/.topiclab-scales-runtime`

You can override this with:

- `--state-dir /path/to/state`

The local state file is intentionally moving closer to `TopicLab-CLI` naming.
It may contain fields such as:

- `auth_mode`
- `base_url`
- `bind_key`
- `access_token`
- `token_type`
- `agent_uid`
- `openclaw_agent`
- `phone`
- `username`
- `password`
- `last_session_id`

## Validation Status

This CLI is expected to support a real end-to-end loop:

1. show help
2. bootstrap auth
3. list/get scale definitions
4. create a session
5. submit answers
6. finalize
7. fetch result

Actual validated command examples should be recorded in:

- `../docs/standalone-cli.md`
- `../docs/cli-usage-guide.md`
