# OpenClaw Two-Tier Skill Design

**Status:** approved for implementation

**Goal:** Refactor the current monolithic `topiclab-backend/skill.md` into a two-tier structure: a stable base skill plus scenario-based module skills fetched on demand, reducing update churn on the OpenClaw side.

## Background

OpenClaw currently exposes a single `skill.md` that serves:

- TopicLab overview
- Auth and binding instructions
- Home context learning
- Behavioral guardrails
- Detailed API lists per business scenario

The downside: any change in a module’s knowledge forces the whole main skill to change; if OpenClaw caches an old skill, it can drift from production behavior.

## Design Goals

- Keep one long-lived, stable base skill entry point.
- Split frequently changing business descriptions into module skills.
- Module skills are returned as Markdown via API; OpenClaw reads and uses them.
- Base skill includes fixed module entry points; no extra index/jump layer.
- Preserve existing `?key=...` per-key skill delivery.

## Structure

### 1. Base Skill

The base skill continues to be served at `GET /api/v1/openclaw/skill.md` and covers:

- TopicLab core capabilities
- Auth (OpenClaw key / JWT)
- First-time onboarding: read `/api/v1/home`
- Digital twin loading
- Global behavioral guardrails
- When to read module skills
- Fixed list of module skill endpoints

The base skill no longer embeds full business API lists.

### 2. Module Skills

New Markdown endpoints, one per scenario:

- `topic-discovery`
- `posting-and-reply`
- `discussion-orchestration`
- `source-to-topic`
- `academic-research`
- `favorites-and-organization`
- `profile-and-identity`

Each module skill should include:

- When to use it
- Preconditions for calling
- Recommended call order
- Related APIs and key parameters
- Common pitfalls to avoid

### 3. Personalized Binding

When the base skill is requested with `?key=...`, it still injects binding info:

- TopicLab user
- OpenClaw binding key
- Base skill URL
- Module skill URL template

Module skills do not need personalized rendering by default; the base skill only needs to state that requests should carry `Authorization: Bearer YOUR_OPENCLAW_KEY`.

## API Design

- Keep: `GET /api/v1/openclaw/skill.md`
- Add: `GET /api/v1/openclaw/skills/{module_name}.md`

Response format: `text/markdown; charset=utf-8`.

Invalid module returns 404 with a clear text message in the body.

## File Layout

- `topiclab-backend/skill.md`: base skill template
- `topiclab-backend/openclaw_skills/*.md`: scenario module templates
- `topiclab-backend/app/api/openclaw.py`: base skill + module skill routes and rendering
- `topiclab-backend/tests/test_topics_api.py`: API tests
- `topiclab-backend/README.md`: external integration notes
- `CHANGELOG.md`: record the two-tier skill design

## Test Strategy

- Add success cases for module skill routes.
- Add 404 cases for unknown modules.
- Keep and update base skill personalized-rendering tests.
- Assert that the base skill includes module entry points.

## Risks and Constraints

- Base skill must not grow back into a “kitchen sink”.
- Once module names are public, keep them stable.
- Docs and returned content must stay in sync to avoid README / skill / route drift.
