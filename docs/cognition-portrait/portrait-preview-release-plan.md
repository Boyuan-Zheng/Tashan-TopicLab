# Portrait Preview Release Plan

## Purpose

This document defines the recommended public-preview release path for the new
portrait product during the current staging phase.

The goal is not to expose production directly. The goal is to let more humans
and agents validate the new portrait loop in a controlled way:

- code can be fetched from GitHub
- the CLI can be installed either from npm prerelease or from source
- testers can talk to the cloud staging backend over HTTPS
- stable users on `latest` stay unaffected

## Release Goal

Use one coordinated preview surface made of three layers:

1. GitHub preview branch and preview tags
2. npm prerelease package for `topiclab-cli`
3. a tester-facing install and verification guide

At the current phase, the recommended public testing topology is:

- testers install the CLI locally
- testers authenticate with their own staging account
- testers connect to the hosted AutoDL staging backend
- testers do **not** self-host the backend by default

This is the fastest path to broader validation because it avoids asking every
tester to provision AI keys, database state, and backend runtime themselves.

## Current Recommended Public Entry

- staging base URL:
  - `https://u394499-8634-23d284fb.westb.seetacloud.com:8443`
- core product mode:
  - `topiclab portrait start --mode legacy_product`
- current local bootstrap helper:
  - `topiclab-cli/scripts/portrait-preview-bootstrap.mjs`
- current staging backend service script:
  - `topiclab-backend/scripts/portrait_staging_service.sh`

## Recommended Repository Strategy

Use two public-facing stability lanes:

- `main`
  - stable branch
  - only carries behavior already acceptable for the normal release train
- `preview/portrait`
  - integration branch for the new portrait runtime, CLI entry, staging docs,
    and preview-only operator workflow

Recommended working model:

1. feature work lands on short-lived branches
2. preview-ready work merges into `preview/portrait`
3. validated preview snapshots receive tags and GitHub Releases
4. once the preview lane is accepted, changes are merged from
   `preview/portrait` into `main`

Why this shape is recommended:

- it keeps preview churn away from `main`
- it gives testers one stable branch name
- it maps naturally to npm prerelease publishing

## Recommended Tagging Scheme

### CLI repo

Use the npm version as the Git tag:

- `topiclab-cli-v0.4.0-portrait.1`
- `topiclab-cli-v0.4.0-portrait.2`

### Backend repo

Because the backend is not currently packaged on npm, use a date-based preview
tag:

- `topiclab-backend-portrait-preview-2026.04.11.1`
- `topiclab-backend-portrait-preview-2026.04.12.1`

### GitHub Release body should always include

- what changed
- the exact CLI tag
- the exact backend tag
- the validated staging URL
- the smoke commands that were actually run
- known caveats

## Recommended npm Strategy

The stable npm lane must remain unchanged:

- stable version line stays on `latest`

The portrait preview lane should use:

- version example:
  - `0.4.0-portrait.1`
- npm dist-tag:
  - `portrait`

This gives two install modes:

- stable users:
  - `npm install -g topiclab-cli@latest`
- preview testers:
  - `npm install -g topiclab-cli@portrait`

Recommended publish rule:

- every preview publish must come from the `preview/portrait` branch or from a
  tag created from that branch

## Release Sequence

### Phase A. Prepare the preview snapshot

In `topiclab-cli`:

1. confirm the preview branch is green
2. run:
   - `npm run build`
   - `npm test`
3. confirm the bootstrap helper still prints the correct staging URL and next
   commands

In `topiclab-backend`:

1. confirm the staging script still works:
   - `status`
   - `restart`
   - `health`
2. confirm the public staging path still works through the CLI:
   - `portrait auth ensure`
   - `portrait start --mode legacy_product`
   - `portrait respond`
   - `portrait status`

### Phase B. Create preview tags

Recommended order:

1. tag backend snapshot
2. tag CLI snapshot
3. draft the GitHub Release notes

### Phase C. Publish npm prerelease

Recommended CLI release commands:

```bash
cd topiclab-cli
npm version 0.4.0-portrait.1 --no-git-tag-version
npm run build
npm test
npm publish --tag portrait
```

After publishing, verify:

```bash
npm view topiclab-cli dist-tags
npm view topiclab-cli versions --json
```

Expected result:

- `latest` still points to the stable line
- `portrait` points to `0.4.0-portrait.1`

### Phase D. Publish tester instructions

The tester-facing announcement should always include:

- GitHub repository URL
- preview branch or release tag
- npm install command
- source-install fallback command
- staging base URL
- minimal validation commands
- where to report:
  - session id
  - command used
  - result
  - error payload

## Tester Install Guide

There should be two official tester paths.

### Path 1. npm prerelease install

Use this after the preview package is published:

```bash
npm install -g topiclab-cli@portrait --registry=https://registry.npmmirror.com
topiclab portrait auth ensure --base-url https://u394499-8634-23d284fb.westb.seetacloud.com:8443 --phone <your_phone> --username <your_username> --password '<your_password>' --json
topiclab portrait start --mode legacy_product --actor-type internal --actor-id <your_agent_id> --json
topiclab portrait respond --choice direct --json
topiclab portrait status --json
```

Use this as the default path for external testers once the prerelease exists.

### Path 2. GitHub source install

Use this before the npm prerelease is published, or when debugging the exact
preview branch code:

```bash
git clone <repo_url>
cd topiclab-cli
git checkout preview/portrait
npm install
npm run portrait:preview:bootstrap
source ./.topiclab-cli-home/portrait-preview.env
node dist/cli.js portrait auth ensure --phone <your_phone> --username <your_username> --password '<your_password>' --json
node dist/cli.js portrait start --mode legacy_product --actor-type internal --actor-id <your_agent_id> --json
node dist/cli.js portrait respond --choice direct --json
node dist/cli.js portrait status --json
```

Use this as the current default path until npm preview publishing is actually
done.

## What Should Be Public Now vs Later

### Good to expose now

- `topiclab-cli` preview source
- preview release notes
- local bootstrap helper
- cloud staging URL
- tester operator manual

### Should not be exposed in the public repo

- real API keys
- real production credentials
- staging passwords
- `.env` files with secrets
- private datasets or logs that include sensitive user content

Before opening the repo more broadly, make sure the public-facing repositories
contain:

- `.env.example`
- no hard-coded secrets
- no private test accounts
- no internal-only hostnames that are not meant to be shared

## Recommended Reporting Template For Testers

Ask every tester to return:

1. install path used:
   - `npm`
   - `git clone`
2. CLI version:
   - `topiclab --version`
3. first successful session id
4. the exact command that failed, if any
5. the JSON error payload, if any
6. whether the issue is:
   - install problem
   - auth problem
   - session orchestration problem
   - staging service problem
   - result-quality problem

## Current Recommendation

For the next round, the most suitable rollout is:

1. keep `main` untouched
2. treat `preview/portrait` as the external-testing branch
3. publish `topiclab-cli@0.4.0-portrait.1` with npm dist-tag `portrait`
4. let testers use the hosted AutoDL staging backend instead of self-hosting
5. collect feedback until the CLI loop and legacy-product-equivalent core are
   stable enough to merge toward the normal release line

This gives the broadest testing surface with the lowest operational load.
