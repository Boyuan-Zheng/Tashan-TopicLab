# Portrait CLI Test Agent Skill

This is now the **single canonical document** for external agents.

If you are onboarding another agent, send **only this file**.

## Purpose

This is the **shareable skill text** for any agent that needs to test the new
TopicLab portrait product through local `TopicLab-CLI` against the cloud
staging runtime.

Unlike the local Codex skill installed on one machine, this file is meant to be
copied or referenced directly when onboarding other agents.

## Trigger

Use this skill when the task is:

- test the new TopicLab portrait product through CLI
- validate the unified portrait session flow
- use a personal staging account instead of the web UI
- run portrait CLI smoke / operator testing without SSH tunnels

## Single Source Rule

This file is self-contained.

Do not require the testing agent to read extra portrait CLI docs first.

If the local file path is unavailable, use the GitHub preview copy of this same
file:

- `https://github.com/Boyuan-Zheng/Tashan-TopicLab/blob/preview/portrait/docs/cognition-portrait/portrait-cli-test-agent-skill.md`
- exact preview tag:
  - `tashan-topiclab-portrait-preview-2026.04.11.2`

If you only read one rule from this skill, read this:

- `topiclab portrait ...` is a **continuous CLI interaction loop**
- you should keep using the CLI repeatedly in the same local shell or with the
  same `TOPICLAB_CLI_HOME`
- after `start`, continue with more `respond`, `status`, `result`, `resume`,
  `history`, and `reset` calls as needed
- do not assume the test ends after one command

## Fastest Working Path Right Now

If you want the shortest path that works today, do exactly this:

```bash
git clone --branch preview/portrait https://github.com/Boyuan-Zheng/TopicLab-CLI.git
cd TopicLab-CLI
npm install
npm run portrait:preview:bootstrap
source ./.topiclab-cli-home/portrait-preview.env
node dist/cli.js portrait auth ensure --phone <your_phone> --username <your_username> --password '<your_password>' --json
node dist/cli.js portrait start --mode legacy_product --actor-type internal --actor-id <your_agent_id> --json
node dist/cli.js portrait respond --choice direct --json
node dist/cli.js portrait respond --text "我是测试智能体 Alpha。" --json
node dist/cli.js portrait status --json
node dist/cli.js portrait respond --text "我目前主要做 AI agent 与科研工具开发。" --json
node dist/cli.js portrait result --json
```

Use this GitHub source-install path until the npm prerelease is actually
published.

## Core Rule

Prefer the unified portrait session surface.

Main user-facing loop:

1. `topiclab portrait auth ensure`
2. `topiclab portrait start`
3. `topiclab portrait respond`
4. `topiclab portrait status`
5. `topiclab portrait result`

Session-control commands:

- `topiclab portrait resume`
- `topiclab portrait history`
- `topiclab portrait reset`
- `topiclab portrait export`

Only use lower-level commands when debugging:

- `topiclab scales ...`
- `topiclab portrait dialogue ...`
- `topiclab portrait state ...`

## Current Runtime Target

Validated staging base URL:

- `https://u394499-8634-23d284fb.westb.seetacloud.com:8443`

Current account type:

- staging/test account
- not production account

## Install And Bootstrap Rule

At the current stage, the preferred install path is:

1. clone the preview branch from GitHub
2. build the CLI locally
3. source the bootstrap env file
4. login with a staging account
5. keep using the CLI continuously against the cloud staging backend

Recommended source install path:

```bash
git clone --branch preview/portrait https://github.com/Boyuan-Zheng/TopicLab-CLI.git
cd TopicLab-CLI
npm install
npm run portrait:preview:bootstrap
source ./.topiclab-cli-home/portrait-preview.env
```

Exact preview source tag, if a pinned ref is required:

- `topiclab-cli-v0.4.0-portrait.1`

After the npm prerelease is actually published, an alternative install path is:

```bash
npm install -g topiclab-cli@portrait --registry=https://registry.npmmirror.com
topiclab portrait auth ensure --base-url https://u394499-8634-23d284fb.westb.seetacloud.com:8443 --phone <your_phone> --username <your_username> --password '<your_password>' --json
```

Until that prerelease really exists, prefer the GitHub source-install path.

Preferred bootstrap:

```bash
cd /absolute/path/to/TopicLab-CLI
npm run portrait:preview:bootstrap
source ./.topiclab-cli-home/portrait-preview.env
```

If needed, the manual build path is:

```bash
cd /absolute/path/to/TopicLab-CLI
npm install
npm run build
export TOPICLAB_CLI_HOME=/tmp/topiclab-cli-portrait-user
export TOPICLAB_BASE_URL=https://u394499-8634-23d284fb.westb.seetacloud.com:8443
```

## Login Rule

Use a staging/test account, not a production account.

If the account is not already registered on staging, the CLI may auto-register
it when the backend allows that path.

Operational shortcut:

- treat `portrait auth ensure` as the register-or-login command
- if it succeeds, continue immediately with `start` and `respond`

Canonical login command:

```bash
node dist/cli.js portrait auth ensure \
  --phone <your_phone> \
  --username <your_username> \
  --password '<your_password>' \
  --json
```

## Continuous Use Rule

After login, continue using the same CLI environment.

Important mental model:

- local CLI state is stored in `TOPICLAB_CLI_HOME/state.json`
- the current portrait session id is remembered there
- the real conversation and portrait state live on the cloud staging backend
- therefore the agent should run several CLI commands in sequence, not stop
  after the first successful response

The minimum continuous interaction pattern is:

```bash
node dist/cli.js portrait start --mode legacy_product --actor-type internal --actor-id <your_agent_id> --json
node dist/cli.js portrait respond --choice direct --json
node dist/cli.js portrait respond --text "我是测试智能体 Alpha。" --json
node dist/cli.js portrait status --json
node dist/cli.js portrait respond --text "我目前主要做 AI agent 与科研工具开发。" --json
node dist/cli.js portrait result --json
```

If the agent pauses and later comes back, it should continue with:

```bash
source ./.topiclab-cli-home/portrait-preview.env
node dist/cli.js portrait resume --json
node dist/cli.js portrait status --json
```

## Input Rule For `respond`

Use exactly one input family per call:

- `--choice`
- `--text` or `--text-file`
- `--external-text` or `--external-text-file`
- `--external-json` or `--external-json-file`
- `--confirm`

Do not make the agent choose backend runtime slices manually unless the task is
explicitly about debugging.

## Minimum Test Flow

Run at least this closure:

1. login with own staging account
2. `portrait start --mode legacy_product`
3. `portrait respond --choice direct`
4. `portrait respond --text ...`
5. `portrait status`
6. `portrait result`

If asked to do a fuller validation, also test:

7. one or more additional `portrait respond --text ...` calls to prove
   continuous CLI interaction
8. `portrait resume`
9. `portrait history`
10. `portrait export`
11. `portrait reset`

## Reporting Rule

Report back with:

1. whether clone/install/bootstrap succeeded
2. whether login/register succeeded
3. which portrait commands were executed in sequence
4. whether continuous CLI interaction worked across multiple commands
5. whether the cloud staging runtime returned valid results
6. exact failures, if any

## Ready-To-Forward Prompt

If you want to hand this task to another agent, you can send only the text
below together with the path or URL of this file:

```text
请作为 TopicLab Portrait CLI 测试智能体，阅读这份唯一 skill 文档并严格按它执行：

/Users/boyuan/aiwork/0310_huaxiang/项目群/github_refs/Tashan-TopicLab/docs/cognition-portrait/portrait-cli-test-agent-skill.md

如果本地路径不可用，就读：
https://github.com/Boyuan-Zheng/Tashan-TopicLab/blob/preview/portrait/docs/cognition-portrait/portrait-cli-test-agent-skill.md

你的目标是：
1. 通过网络下载或进入已有的 TopicLab-CLI preview/portrait 分支
2. 在本地安装并 bootstrap CLI
3. 用你自己的 staging/test 账号执行 portrait auth ensure
4. 连续执行 topiclab portrait start / respond / status / result
5. 必要时继续执行 resume / history / export / reset
6. 汇报是否证明了“本地 CLI -> 云端 staging”闭环可用

注意：
- 不要默认使用生产账号
- 不要把 CLI 当成一次性命令
- 除非主入口失败，不要优先使用底层调试命令
```
