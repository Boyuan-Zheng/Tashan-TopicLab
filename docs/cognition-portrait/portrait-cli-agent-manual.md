# Portrait CLI Agent Manual

## Purpose

This document is the operator manual for agents that need to use the new
TopicLab portrait product from a local machine through `TopicLab-CLI`, without
using the web UI and without SSH tunnels.

It documents the currently validated staging path:

- local `TopicLab-CLI`
- direct HTTPS access to the AutoDL custom-service URL
- own account auth
- unified portrait session main entry

This is the recommended user-facing entry for portrait usage during the current
staging phase.

GitHub preview references:

- docs repo preview branch:
  - `https://github.com/Boyuan-Zheng/Tashan-TopicLab/tree/preview/portrait`
- CLI repo preview branch:
  - `https://github.com/Boyuan-Zheng/TopicLab-CLI/tree/preview/portrait`

## Current Validated Entry

Validated staging base URL:

- `https://u394499-8634-23d284fb.westb.seetacloud.com:8443`

Validated main command family:

- `topiclab portrait start`
- `topiclab portrait respond`
- `topiclab portrait status`
- `topiclab portrait result`
- `topiclab portrait resume`
- `topiclab portrait history`
- `topiclab portrait reset`
- `topiclab portrait export`

## Local CLI, Cloud Runtime

The installation is local, but the portrait product runtime is not local-only.

The validated staging interaction path is:

- local `TopicLab-CLI`
- HTTPS requests to the AutoDL staging URL
- cloud `topiclab-backend`
- cloud staging database

That means:

- CLI build and `TOPICLAB_CLI_HOME` live on the local machine
- portrait sessions, scale sessions, dialogue transcripts, portrait state, and
  server logs live on the cloud staging host

This was revalidated on 2026-04-11 with the `cognitive-ask-v2-agent` RCSS
test:

- portrait session:
  - `pts_35a0dca6ba754303`
- scale session:
  - `scs_6869507974d242a2`

Cloud-side evidence was confirmed in both places:

- HTTP access log:
  - `/root/topiclab-portrait-staging/logs/topiclab_backend_6006.log`
- staging SQLite database:
  - `/root/topiclab-portrait-staging/topiclab-backend/topiclab_staging.sqlite3`

The cloud database contained:

- the top-level portrait session record
- linked runtime refs for:
  - `dialogue_session`
  - `scale_session`
  - `portrait_state`
- 8 persisted RCSS answers
- the RCSS result row with:
  - `integration = 24`
  - `depth = 13`
  - `CSI = 11`
  - `type = 倾向整合型`
- portrait state materialization and observation records

## Continuous CLI Session Rule

Agents must treat `topiclab portrait ...` as a **continuous local CLI session
loop**, not as a one-shot command.

What this means in practice:

- stay in the same shell after `source ./.topiclab-cli-home/portrait-preview.env`
- run one portrait command after another in sequence
- do not assume you need SSH, a browser, or a fresh bootstrap between each step
- after `portrait start`, continue with repeated `portrait respond`,
  `portrait status`, and `portrait result` calls as needed

Why continuous use works:

- the local CLI persists auth and current-session state under:
  - `TOPICLAB_CLI_HOME/state.json`
- the cloud backend persists the actual portrait session, state, logs, and
  runtime refs
- `portrait_current_session_id` is remembered locally, so later commands do not
  need `--session-id` unless the agent is intentionally targeting a different
  session

Typical continuous loop:

```bash
source ./.topiclab-cli-home/portrait-preview.env
node dist/cli.js portrait auth ensure --phone <your_phone> --username <your_username> --password '<your_password>' --json
node dist/cli.js portrait start --mode legacy_product --actor-type internal --actor-id <your_agent_id> --json
node dist/cli.js portrait respond --choice direct --json
node dist/cli.js portrait respond --text "我是测试智能体 Alpha。" --json
node dist/cli.js portrait status --json
node dist/cli.js portrait respond --text "我目前主要做 AI agent 与科研工具开发。" --json
node dist/cli.js portrait result --json
```

If the agent stops and comes back later, it can continue as long as it reloads
the same env file or points to the same `TOPICLAB_CLI_HOME`:

```bash
source ./.topiclab-cli-home/portrait-preview.env
node dist/cli.js portrait resume --json
node dist/cli.js portrait status --json
```

## Important Current Constraint

The unified portrait commands described here are validated in the local
repository checkout.

At the current staging phase, other agents should use the checked-out
`TopicLab-CLI` repository and its built `dist/cli.js`, rather than assuming
that the globally published npm package already contains every new portrait
command.

The planned preview package rollout is:

- keep stable `topiclab-cli` `latest` unchanged
- publish a portrait prerelease as:
  - `0.4.0-portrait.1`
- publish it under npm dist-tag:
  - `portrait`

Recommended local path:

- `/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/topiclab-cli`

Important current note:

- the checked-in `Tashan-TopicLab/topiclab-cli` submodule now already contains
  the validated portrait main entry
- the globally published npm package should still be treated as not yet
  carrying every new portrait preview command until maintainers publish the
  prerelease
- for the core old-product-equivalent path, start with:
  - `topiclab portrait start --mode legacy_product`

## Local Setup

### 1. Build the CLI locally

```bash
cd /absolute/path/to/TopicLab-CLI
npm install
npm run build
```

Or use the helper bootstrap path:

```bash
cd /absolute/path/to/TopicLab-CLI
npm run portrait:preview:bootstrap
```

That helper prepares:

- an isolated `TOPICLAB_CLI_HOME`
- `TOPICLAB_BASE_URL` pointing at the validated AutoDL staging URL
- the next login/test commands for the unified portrait loop

### 2. Use an isolated local state directory

This keeps portrait auth and current-session memory separate from unrelated
local experiments.

```bash
export TOPICLAB_CLI_HOME=/tmp/topiclab-cli-portrait-user
```

### 3. Run the built CLI

Current recommended invocation form:

```bash
node /absolute/path/to/TopicLab-CLI/dist/cli.js portrait --help
```

If the repository is already the current working directory:

```bash
node dist/cli.js portrait --help
```

If the bootstrap helper was used, it will also create a local env helper file
such as:

- `./.topiclab-cli-home/portrait-preview.env`

You can then load it before testing:

```bash
source ./.topiclab-cli-home/portrait-preview.env
```

## Preview Package Install Path

After maintainers actually publish the portrait preview package, the preferred
install paths for other agents will become:

By dist-tag:

```bash
npm install -g topiclab-cli@portrait --registry=https://registry.npmmirror.com
```

By exact prerelease version:

```bash
npm install -g topiclab-cli@0.4.0-portrait.1 --registry=https://registry.npmmirror.com
```

Until that publish step actually happens, agents should still use the local
repository build path documented above.

## Account Login

Use your own TopicLab staging account.

```bash
node dist/cli.js portrait auth ensure \
  --phone <your_phone> \
  --username <your_username> \
  --password '<your_password>' \
  --json
```

If you did not source the bootstrap env file, add:

```bash
--base-url https://u394499-8634-23d284fb.westb.seetacloud.com:8443
```

This stores portrait auth in local CLI state and does not require SSH.

## Main User Flow

The unified portrait product is now designed to feel like one resumable
session, even though the backend internally routes through multiple portrait
runtime slices.

The normal user loop is:

1. `start`
2. `respond`
3. `status`
4. `result`

### Start a portrait session

```bash
node dist/cli.js portrait start \
  --mode legacy_product \
  --actor-type internal \
  --actor-id my-agent \
  --json
```

For the core migrated old-product loop, `--mode legacy_product` is the
recommended starting mode. This creates a top-level portrait session and
remembers it locally as the current active portrait session.

### Submit one step of input

#### Text reply

```bash
node dist/cli.js portrait respond \
  --text "我主要在做 AI agent、科研工具开发和学术写作。" \
  --json
```

#### Choice reply

Used for scale-question style steps and other server-driven options:

```bash
node dist/cli.js portrait respond --choice 4 --json
```

The server decides whether that choice belongs to:

- a scale question
- a branch selection
- a control action

Already validated server-driven product choices include:

- `forum:generate`
- `scientist:famous`
- `scientist:field`
- `export:structured`
- `export:profile_markdown`
- `export:forum_markdown`
- `publish:brief`
- `publish:full`

#### External AI result

```bash
node dist/cli.js portrait respond \
  --external-text "# Summary from external AI..." \
  --json
```

Or:

```bash
node dist/cli.js portrait respond \
  --external-json '{"summary":"...","traits":["..."]}' \
  --json
```

#### Confirm / continue

```bash
node dist/cli.js portrait respond --confirm --json
```

### Check current state

```bash
node dist/cli.js portrait status --json
```

This is the main interruption-recovery command. It returns:

- current stage
- current status
- next required input kind
- current runtime refs
- partial result preview

### Read current or final result

```bash
node dist/cli.js portrait result --json
```

This reads the current server-owned portrait result for the current portrait
session.

## Session Control Commands

These commands are still part of the user-facing surface because real usage
needs history, recovery, reset, and export.

### Resume

Resume the locally remembered session:

```bash
node dist/cli.js portrait resume --json
```

Or ask `start` to reuse the latest remote session:

```bash
node dist/cli.js portrait start --resume-latest --json
```

### History

Read recent event history for the current session:

```bash
node dist/cli.js portrait history --json
```

Or target a specific session and limit:

```bash
node dist/cli.js portrait history --session-id pts_xxx --limit 50 --json
```

### Reset

Reset the current portrait creation process:

```bash
node dist/cli.js portrait reset --json
```

### Export

Export the current portrait result as structured JSON:

```bash
node dist/cli.js portrait export \
  --kind structured \
  --output /tmp/portrait-result.json \
  --json
```

Or export as local Markdown:

```bash
node dist/cli.js portrait export \
  --kind profile-markdown \
  --output /tmp/portrait-result.md \
  --json
```

Other validated export kinds are:

- `forum-markdown`
- `profile-html`
- `profile-pdf`
- `profile-image`

## What `respond(...)` Really Does

Agents do not need to choose backend modules directly.

The current backend orchestrator can already route one `respond(...)` call
into:

- `dialogue`
- `scales`
- `prompt_handoff`
- `import_result`
- `portrait_state`
- `forum`
- `scientist`
- `export`
- `publish`

So the correct mental model is:

- read the server's next instruction
- submit exactly one response
- let the server choose the runtime slice

## Lower-Level Expert Commands

These still exist and remain useful for debugging or migration work:

- `topiclab scales ...`
- `topiclab portrait dialogue ...`
- `topiclab portrait state ...`

But ordinary agent usage should prefer the unified session loop above.

## What Has Been Publicly Validated

The following no-SSH public staging flows have already been validated against
the AutoDL HTTPS custom-service URL:

- `npm run portrait:preview:bootstrap`
- `portrait auth ensure`
- `portrait start`
- `portrait respond --text`
- `portrait respond --choice scale:rcss`
- repeated numeric `portrait respond --choice <n>`
- `portrait respond --choice prompt_handoff`
- `portrait respond --external-text`
- `portrait respond --choice forum:generate`
- `portrait respond --choice scientist:famous`
- `portrait respond --choice publish:brief`
- `portrait status`
- `portrait result`
- `portrait resume`
- `portrait history`
- `portrait export`

Cloud-side evidence for the 2026-04-11 validation includes:

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

The corresponding cloud backend log file is:

- `/root/topiclab-portrait-staging/logs/topiclab_backend_6006.log`

The corresponding validated backend start path is now repo-owned:

- `/root/topiclab-portrait-staging/topiclab-backend/scripts/portrait_staging_service.sh`
- validated action set:
  - `start`
  - `stop`
  - `restart`
  - `status`
  - `health`
  - `logs`

## Current Caveats

- this is still a staging environment, not production
- current instructions assume direct use of the checked-out `TopicLab-CLI`
  repository build
- portrait auth is currently separate from the older OpenClaw bind-key flow
- lower-level debug commands remain available, but are not the preferred
  user-facing entry
- forum/export/publish are now truly cloud-backed through the unified session
  loop, but their semantic richness still depends on how much canonical
  portrait state has already been filled
