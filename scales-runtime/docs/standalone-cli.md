# Standalone Scales CLI

## Purpose

This document records the validated standalone CLI path for the new scale
runtime.

This is not the shared `TopicLab-CLI` integration yet.

This is the independent scale-domain CLI that proves a real end-to-end loop can
already run locally:

1. show usage
2. bootstrap auth
3. list definitions
4. start or resume a session
5. answer questions from the terminal
6. finalize
7. fetch result later in a separate invocation

## Location

- CLI entrypoint:
  - `/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py`
- CLI README:
  - `/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/README.md`

## Runtime Model

The CLI boots the minimal local backend harness in-process on every invocation.

It reuses the already-validated backend runtime:

- `topiclab-backend/app/api/scales.py`
- `topiclab-backend/app/services/scales_service.py`
- `topiclab-backend/app/services/scales_scoring.py`

It persists local state under one state directory:

- SQLite database
- auth session file
- last known local user context

The auth layer now uses a dual-provider structure:

- `local_password`
  - current validated standalone mode
  - local harness or remote HTTP + `/auth/login` / `/auth/register`
- `bind_key`
  - migration-aligned mode
  - remote/base-url transport + `/api/v1/openclaw/bootstrap` / `/api/v1/openclaw/session/renew`

By default the state directory is:

- `~/.topiclab-scales-runtime`

During validation, the commands below were run with:

- `/tmp/topiclab-scales-runtime-check`

## Validated Commands

The following commands were actually executed on 2026-04-10.

### 1. Show usage

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py --help
```

This returned the expected command surface:

- `auth`
- `list`
- `get`
- `session`
- `answer`
- `answer-batch`
- `finalize`
- `result`
- `sessions`
- `run`

### 2. Bootstrap local auth

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py --json --state-dir /tmp/topiclab-scales-runtime-check auth ensure
```

This created or refreshed a reusable local auth session and returned a token.

### 3. List available scales

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py --json --state-dir /tmp/topiclab-scales-runtime-check list
```

Validated result:

- `rcss`
- `mini-ipip`
- `ams`

### 4. Run one full interactive RCSS loop

The validated run used piped terminal answers:

```bash
printf '7\n7\n7\n7\n1\n1\n1\n1\n' | \
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --state-dir /tmp/topiclab-scales-runtime-check \
  run --scale rcss --actor-type internal --actor-id self-check
```

This prompted for all 8 RCSS questions and returned:

- a real `session_id`
- finalized session payload
- persisted result payload

Validated result values:

- `integration = 28.0`
- `depth = 4.0`
- `CSI = 24.0`
- `type = 强整合型`

### 5. Re-read the same result in a later invocation

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json --state-dir /tmp/topiclab-scales-runtime-check \
  result scs_d82fd24141f24376
```

This returned the persisted result object successfully in a new CLI process.

### 6. List historical sessions

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json --state-dir /tmp/topiclab-scales-runtime-check \
  sessions list
```

This returned the completed RCSS session with:

- `status = completed`
- `remaining_count = 0`
- `allowed_actions = ["read_result"]`

## Real Constraints Found

### 1. One state directory should be used serially

The standalone CLI uses one SQLite file per state directory.

When two CLI processes were intentionally launched in parallel against the same
state directory, SQLite reported `database is locked`.

This is acceptable for the current validation target:

- one human user
- one agent session
- one serial local loop

For now, the documented rule is:

- do not run multiple standalone CLI commands in parallel against the same
  `--state-dir`

### 2. Global flags now work even after the subcommand

During the first validation pass, `--json` only worked before the subcommand.

The CLI was then adjusted so:

- `--json`
- `--state-dir`

are normalized as global options even if they appear later in the argv list.

### 3. Bind-key mode is now auth-validated against the live site, but scale routes are not deployed there yet

The standalone CLI now supports a `bind_key` auth provider so its auth/state
shape can converge toward `TopicLab-CLI` before migration.

What has been validated locally:

- auth mode resolution
- provider switching
- remote/base-url transport wiring
- machine-readable guardrails such as missing `--bind-key`

What was then validated on 2026-04-10 against the live public site:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --state-dir /tmp/topiclab-scales-runtime-bindkey \
  --auth-mode bind_key \
  --base-url https://world.tashan.chat \
  --bind-key tlos_xxx \
  auth ensure
```

This succeeded and returned:

- `auth_mode = bind_key`
- `base_url = https://world.tashan.chat`
- a real `access_token`
- a real `agent_uid`
- a real `openclaw_agent`

This proves that:

- the bind-key auth provider works
- remote bootstrap works
- the local state model is already compatible with a future `TopicLab-CLI`
  migration path

What was attempted immediately after that:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --state-dir /tmp/topiclab-scales-runtime-bindkey \
  --auth-mode bind_key \
  --base-url https://world.tashan.chat \
  --bind-key tlos_xxx \
  list
```

and:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --state-dir /tmp/topiclab-scales-runtime-bindkey \
  --auth-mode bind_key \
  --base-url https://world.tashan.chat \
  --bind-key tlos_xxx \
  get rcss
```

Both returned `404 Not Found` from:

- `/api/v1/scales`
- `/api/v1/scales/rcss`

This means the current blocker is not auth and not the standalone CLI.

The current blocker is:

- the live `world.tashan.chat` deployment does not yet expose the new
  `/api/v1/scales/...` route family

### 4. Remote local-password mode is now validated through a tunnel-backed staging loop

On 2026-04-10, the standalone CLI was also validated against a remote staging
backend using:

- local CLI process
- SSH local port forwarding as a temporary transport bridge
- remote HTTP runtime on the staging host

Validated local tunnel shape:

```bash
ssh -N -L 18080:127.0.0.1:18000 -p <staging-ssh-port> root@<staging-host>
```

Validated auth command shape:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --auth-mode local_password \
  --base-url http://127.0.0.1:18080 \
  --state-dir /tmp/topiclab-standalone-remote-cli \
  auth ensure \
  --phone 13800138001 \
  --username stage-smoke-user \
  --password StagePass123
```

Validated full run shape:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --auth-mode local_password \
  --base-url http://127.0.0.1:18080 \
  --state-dir /tmp/topiclab-standalone-remote-cli \
  run --scale rcss \
  --actor-type internal \
  --actor-id remote-cli-proof \
  --answers-file /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/fixtures/rcss-strong-integration.json
```

Observed result:

- remote auth succeeded
- remote scale listing succeeded
- remote RCSS run succeeded
- returned result still matched expectation:
  - `CSI = 24.0`
  - `type = 强整合型`

Important interpretation:

- this proves the CLI contract can already drive a remote staging runtime
- but the SSH tunnel is still an operator bridge, not the final product path
- the long-term target remains:
  - local CLI
  - directly reachable remote portrait runtime
  - no manual SSH requirement for normal usage

### 5. Direct no-SSH public access was tested separately and is not yet available on the current test host

On the same day, the remote staging process was rebound from:

- `127.0.0.1:18000`

to:

- `0.0.0.0:18000`

This removed the application-level localhost-only limitation, but it did **not**
yet make the runtime directly usable from arbitrary external clients.

Observed direct public results:

- `http://connect.westb.seetacloud.com:18000/health`
  - remote end closed without a usable HTTP response
- `http://connect.westb.seetacloud.com/health`
  - remote end closed without a usable HTTP response
- `https://connect.westb.seetacloud.com/health`
  - TLS/HTTP handshake still failed
- `http://116.172.93.108:18000/health`
  - `503 Service Unavailable`
- `http://116.172.93.108/health`
  - `503 Service Unavailable`

Validated no-SSH CLI probe:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --auth-mode local_password \
  --base-url http://116.172.93.108:18000 \
  --state-dir /tmp/topiclab-standalone-no-ssh \
  list
```

Observed result:

- `{"ok": false, "status_code": 503, "detail": "Service Unavailable"}`

Current interpretation:

- the portrait runtime itself is healthy
- the standalone CLI remote mode itself is healthy
- the remaining blocker is the public ingress / provider exposure path of the
  current test platform
- until that ingress layer is solved, the currently validated remote product
  path remains:
  - local CLI
  - SSH tunnel or equivalent public tunnel bridge
  - remote portrait runtime

### 6. Direct no-SSH public closure succeeded once the AutoDL custom-service URL was used

Later on the same staging host, the platform UI confirmed that the host was an
AutoDL instance with a mapped custom-service URL for:

- `http://127.0.0.1:6006`

mapped to:

- `https://u394499-8634-23d284fb.westb.seetacloud.com:8443`

The portrait runtime was then started directly on:

- `127.0.0.1:6006`

and the public URL was probed successfully:

```bash
python3 - <<'PY'
import ssl, urllib.request
with urllib.request.urlopen(
    'https://u394499-8634-23d284fb.westb.seetacloud.com:8443/health',
    timeout=20,
    context=ssl.create_default_context(),
) as r:
    print(r.status)
    print(r.read().decode('utf-8'))
PY
```

Observed result:

- `200`
- `{"status":"ok","service":"topiclab-backend"}`

Validated direct CLI auth shape:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --auth-mode local_password \
  --base-url 'https://u394499-8634-23d284fb.westb.seetacloud.com:8443' \
  --state-dir /tmp/topiclab-standalone-autodl \
  auth ensure \
  --phone 13800138002 \
  --username autodl-stage-user \
  --password '<redacted>'
```

Validated direct CLI run shape:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --auth-mode local_password \
  --base-url 'https://u394499-8634-23d284fb.westb.seetacloud.com:8443' \
  --state-dir /tmp/topiclab-standalone-autodl \
  run --scale rcss \
  --actor-type internal \
  --actor-id autodl-direct-cli \
  --answers-file /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/fixtures/rcss-strong-integration.json
```

Validated separate result re-read:

```bash
python3 /Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/scales-runtime/cli/standalone_scales_cli.py \
  --json \
  --auth-mode local_password \
  --base-url 'https://u394499-8634-23d284fb.westb.seetacloud.com:8443' \
  --state-dir /tmp/topiclab-standalone-autodl \
  result scs_853a2a796fa94d74
```

Observed direct-public result:

- scale listing succeeded
- auth succeeded
- RCSS run succeeded
- separate result re-read succeeded
- returned:
  - `CSI = 24.0`
  - `type = 强整合型`

Updated interpretation:

- direct no-SSH public closure is now proven on a non-production host
- the correct public entry on AutoDL is the platform-provided custom-service
  HTTPS URL, not the raw public IP or raw custom port
- SSH is still useful for deployment and debugging, but it is no longer needed
  for normal CLI usage once that public URL exists

## Closure Status

The standalone local CLI is now sufficient to claim a real local closure:

- usage is visible
- answering can happen in the terminal
- session state persists across invocations
- scoring is canonical and server-side
- finalized results can be re-read later

This means the next migration step can now be treated as an adapter problem:

- expand the initial thin `TopicLab-CLI` adapter toward fuller parity
- keep backend truth unchanged

For the live public site, one deployment step is still required before the same
remote closure can succeed:

- deploy the new `/api/v1/scales/...` routes behind the existing OpenClaw auth
  path
