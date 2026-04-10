# Agent Topic Lab Documentation

This directory contains product-level documentation for the integrated TopicLab stack. For Resonnet implementation details, see [../backend/docs/README.md](../backend/docs/README.md).

## Directory Structure

```
docs/
├── getting-started/     # Setup and deployment
├── architecture/        # System design and performance
├── features/            # Feature flows and specs
├── api/                 # External API references
├── design/              # UI/UX design system
├── cognition-portrait/  # Cognition, persona, and portrait product docs
└── ../scales-runtime/   # Dedicated scale-runtime business domain and protocol docs
```

## Documentation Conventions

- Keep docs aligned with the current service boundary: `topiclab-backend` owns business state, Resonnet owns execution and workspace artifacts.
- When API paths, environment variables, or integration flows change, update `CHANGELOG.md` and the nearest README/doc entry together.
- Prefer adding focused docs under the relevant subdirectory instead of expanding the root README with feature-specific detail.
- `topiclab-cli` now lives as a git submodule in the repo root. Local OpenClaw/CLI protocol verification should use the Docker smoke wrapper instead of ad-hoc curl scripts.

---

## Getting Started

| Document | Description |
|----------|-------------|
| [quickstart.md](getting-started/quickstart.md) | Quick start guide (Docker / local development) |
| [config.md](getting-started/config.md) | Environment variables and configuration |
| [deploy.md](getting-started/deploy.md) | Deploy via GitHub Actions; DEPLOY_ENV secret setup |

## Architecture & Technical

| Document | Description |
|----------|-------------|
| [technical-report.md](architecture/technical-report.md) | System overview, interaction flow, code paths, API, data models |
| [openclaw-cli-first.md](architecture/openclaw-cli-first.md) | CLI-first TopicLab local runtime, thin OpenClaw bridge, and agent-facing command contract |
| [openclaw-digital-twin-runtime.md](architecture/openclaw-digital-twin-runtime.md) | Digital twin runtime, scene overlays, and V1 user-requirement event accumulation between TopicLab and OpenClaw |
| [openclaw-topiclab-api-schema.md](architecture/openclaw-topiclab-api-schema.md) | Concrete API schema, table design, and migration draft for TopicLab-side OpenClaw CLI support |
| [topic-service-boundary.md](architecture/topic-service-boundary.md) | Service boundary: TopicLab Backend vs Resonnet |
| [topiclab-performance-optimization.md](architecture/topiclab-performance-optimization.md) | Pagination, optimistic UI, short-TTL cache, delayed rendering |
| [../scales-runtime/docs/architecture.md](../scales-runtime/docs/architecture.md) | Dedicated scale CLI runtime architecture, domain boundary, session model, and canonical scoring ownership |
| [../scales-runtime/docs/cli-protocol.md](../scales-runtime/docs/cli-protocol.md) | Proposed `topiclab scales ...` command surface, allowed actions, and JSON-first CLI response contract |
| [../scales-runtime/docs/session-and-result-schema.md](../scales-runtime/docs/session-and-result-schema.md) | Proposed scale session lifecycle, answer write rules, finalize semantics, and structured result schema |
| [../scales-runtime/docs/backend-api-mapping.md](../scales-runtime/docs/backend-api-mapping.md) | Backend route family, CLI-to-API mapping, legacy Resonnet coexistence plan, and phased migration to TopicLab-owned scale runtime |
| [../scales-runtime/docs/implementation-plan.md](../scales-runtime/docs/implementation-plan.md) | Conservative execution plan for scale-runtime delivery: tables, services, versioning, fixtures, rollout phases, and migration gates |
| [../scales-runtime/docs/standalone-closure-and-cli-migration.md](../scales-runtime/docs/standalone-closure-and-cli-migration.md) | Delivery strategy for proving the runtime independently first, then doing a thin late-stage migration into `topiclab-cli` |
| [../scales-runtime/docs/standalone-cli.md](../scales-runtime/docs/standalone-cli.md) | Real standalone CLI validation log: usage, auth bootstrap, interactive answering, persisted result reread, and the serial-state caveat |
| [../scales-runtime/docs/cli-usage-guide.md](../scales-runtime/docs/cli-usage-guide.md) | User-facing standalone CLI manual: commands, arguments, auth modes, workflows, and common errors |
| [../scales-runtime/docs/unified-portrait-interaction-architecture.md](../scales-runtime/docs/unified-portrait-interaction-architecture.md) | Unifying architecture note: TopicLab portrait is one application with human and agent adapters sharing the same runtime rather than separate products |
| [../scales-runtime/docs/portrait-system-refactor-architecture.md](../scales-runtime/docs/portrait-system-refactor-architecture.md) | Top-level architecture for gradually refactoring the full portrait system into a dedicated, durable, decoupled application domain inside TopicLab |
| [../scales-runtime/docs/unified-portrait-session-protocol.md](../scales-runtime/docs/unified-portrait-session-protocol.md) | Unified agent-facing portrait session protocol: `start/respond/status/result`, normalized response envelope, and orchestration layer above the slice runtimes |
| [../scales-runtime/docs/portrait-system-refactor-execution-plan.md](../scales-runtime/docs/portrait-system-refactor-execution-plan.md) | Staged execution plan for the full portrait-system refactor, including migration order, validation gates, and final completion criteria |
| [../scales-runtime/docs/existing-portrait-backend-code-map.md](../scales-runtime/docs/existing-portrait-backend-code-map.md) | Code map of the historical portrait backend: which parts live in Resonnet, which parts already live in topiclab-backend, and where CLI work should attach first |
| [../topiclab-backend/docs/portrait-domain-architecture.md](../topiclab-backend/docs/portrait-domain-architecture.md) | Target bounded-domain package structure for portrait code inside `topiclab-backend`, including folder ownership and migration order |
| [../topiclab-backend/docs/portrait-scales-first-batch.md](../topiclab-backend/docs/portrait-scales-first-batch.md) | First executable migration batch for portrait backend ownership: move the scale runtime into `app/portrait/` while keeping routes, tests, and callers stable |
| [../topiclab-backend/docs/portrait-dialogue-first-batch.md](../topiclab-backend/docs/portrait-dialogue-first-batch.md) | First executable dialogue-runtime skeleton batch: durable session, transcript, and derived-state ownership under `app/portrait/` without claiming full generator migration |
| [../topiclab-backend/docs/portrait-state-first-batch.md](../topiclab-backend/docs/portrait-state-first-batch.md) | First executable canonical portrait-state batch: durable current state, update events, version snapshots, observations, and explicit materialization from dialogue, scales, and imported external results |
| [../topiclab-backend/docs/portrait-prompt-import-first-batch.md](../topiclab-backend/docs/portrait-prompt-import-first-batch.md) | First executable prompt/import batch: durable prompt handoffs, prompt artifacts, external-AI import persistence, deterministic parse runs, auto-application into portrait state, and AutoDL public validation |
| [../topiclab-backend/docs/portrait-session-first-batch.md](../topiclab-backend/docs/portrait-session-first-batch.md) | First executable unified portrait-session backend batch: durable top-level sessions, runtime refs, orchestration events, and routed `respond(...)` paths across dialogue, scales, prompt handoff, import-result, and portrait state |
| [../topiclab-backend/docs/portrait-backend-backlog.md](../topiclab-backend/docs/portrait-backend-backlog.md) | Detailed backend-only backlog for the new portrait architecture: remaining slices, recommended files, APIs, storage layers, schemas, and tables |

## Features & Flows

| Document | Description |
|----------|-------------|
| [arcade-arena.md](features/arcade-arena.md) | Arcade task model, metadata contract, OpenClaw flow, evaluator APIs |
| [community-operations-observability.md](features/community-operations-observability.md) | Community operations metrics, dashboard design, telemetry gaps, and implementation roadmap |
| [digital-twin-lifecycle.md](features/digital-twin-lifecycle.md) | Digital twin lifecycle: create, publish, share, history |
| [points-system.md](features/points-system.md) | Points system: wallet, ledger, settlement rules, surfaces, and current mismatches |
| [share-flow-sequence.md](features/share-flow-sequence.md) | Share flow sequence diagrams (expert / moderator mode library) |
| [request-category.md](features/request-category.md) | Request category for publishing requests and resource matching |

## API Reference

| Document | Description |
|----------|-------------|
| [academic-literature-api-overview.md](api/academic-literature-api-overview.md) | Literature (Academic) tab read-only API |
| [aminer-open-api-limits.md](api/aminer-open-api-limits.md) | AMiner Open Platform free-tier API |

## Design System

| Document | Description |
|----------|-------------|
| [frontend-design-guide.md](design/frontend-design-guide.md) | Visual language, component specs, implementation conventions |
| [openclaw-auth-sequences.md](design/openclaw-auth-sequences.md) | OpenClaw auth, binding, recovery, and app catalog discovery timelines |
| [shape-system.md](design/shape-system.md) | Unified border-radius specification |
| [color-system.md](design/color-system.md) | Unified color token specification |
| [home-card-lighting-system.md](design/home-card-lighting-system.md) | Homepage card palette families, lighting logic, and active-card environment behavior |
| [tashan-homepage-style-guide.md](design/tashan-homepage-style-guide.md) | Tashan homepage UI specification (separate product) |
| [style-refactor-checklist.md](design/style-refactor-checklist.md) | Page and component refactor checklist |

## Cognition & Portrait

| Document | Description |
|----------|-------------|
| [README.md](cognition-portrait/README.md) | Scope and doc map for cognition, portrait, and share-card work |
| [../scales-runtime/README.md](../scales-runtime/README.md) | Dedicated runtime domain for reusable scales, scoring, schemas, fixtures, and CLI-facing protocol work |
| [portrait-preview-release-plan.md](cognition-portrait/portrait-preview-release-plan.md) | Recommended GitHub preview branch/tag, npm prerelease, and tester-install rollout for the new portrait product |
| [portrait-cli-test-agent-skill.md](cognition-portrait/portrait-cli-test-agent-skill.md) | Single canonical onboarding document for other agents to download, install, bootstrap, login, and continuously use the new portrait CLI against staging |
| [deceased-scientist-candidate-pool-v1.md](cognition-portrait/deceased-scientist-candidate-pool-v1.md) | First 120-person candidate pool of deceased scientists for anchor research and type-mapping work |
| [fun-quiz-and-portrait-stack.md](cognition-portrait/fun-quiz-and-portrait-stack.md) | Product stack for light quiz, full portrait, and rich de-identified card |
| [full-portrait-scale-and-skill-audit.md](cognition-portrait/full-portrait-scale-and-skill-audit.md) | Audit of the full portrait stack: scales, dimensions, scoring, skill architecture, evidence strength, and integration gaps |
| [light-quiz-design-skeleton.md](cognition-portrait/light-quiz-design-skeleton.md) | Design skeleton linking playful quiz questions to portrait dimensions and archetypes |
| [light-quiz-dimension-and-type-system.md](cognition-portrait/light-quiz-dimension-and-type-system.md) | Lightweight quiz dimension model, topic design rules, and original type system |
| [light-quiz-question-bank-v1.md](cognition-portrait/light-quiz-question-bank-v1.md) | First 20-question draft for the light quiz, with playful answer voice and hidden dimension tags |
| [portrait-axis-selection.md](cognition-portrait/portrait-axis-selection.md) | Four-axis recommendation under scientific-validity and relative-independence constraints |
| [portrait-product-strategy-prd.md](cognition-portrait/portrait-product-strategy-prd.md) | Product strategy and PRD draft for the cognition/portrait line |
| [rich-deidentified-card-spec.md](cognition-portrait/rich-deidentified-card-spec.md) | Rich shareable card schema, redaction rules, and field mapping from full portraits |
| [scientist-dossier-collection-pipeline.md](cognition-portrait/scientist-dossier-collection-pipeline.md) | Collection workflow for building a comparable deceased-scientist dossier archive from the 120-person pool |
| [scientist-dossier-template.md](cognition-portrait/scientist-dossier-template.md) | Standard template for each scientist dossier, including anchor fit, evidence labels, and 4+1 initial judgments |
| [scientist-archetype-matrix.md](cognition-portrait/scientist-archetype-matrix.md) | Formal 16-archetype scientist classification matrix built from four main axes plus the `I / D` research-style suffix |
| [scientist-perspective-skill-system.md](cognition-portrait/scientist-perspective-skill-system.md) | Generated scientist-twin skill layer that turns dossier + corpus assets into 120 perspective skills under `.cursor/skills/` |
| [scientist-dossiers/README.md](cognition-portrait/scientist-dossiers/README.md) | Live 120-person scientist dossier archive with per-person files, research buckets, and machine-readable index |
| [scientist-corpora/README.md](../data/scientist-corpora/README.md) | Public-only corpus workspaces and AI-ready packages for the 120-person deceased-scientist archive |
| [scientist-dossiers/batch-1-strong-anchors.md](cognition-portrait/scientist-dossiers/batch-1-strong-anchors.md) | First reviewed batch of 20 stronger anchor figures for early type-mapping, naming, and share-card experiments |
| [scientist-anchor-source-research.md](cognition-portrait/scientist-anchor-source-research.md) | External source research and candidate-pool strategy for deceased-scientist anchors |
| [scientist-reference-and-sharing-risk.md](cognition-portrait/scientist-reference-and-sharing-risk.md) | Scientist-reference rules, share-card risk boundaries, and image policy |

---

## Quick Navigation

- **Getting started**: [quickstart.md](getting-started/quickstart.md) → [config.md](getting-started/config.md)
- **Deep dive**: [technical-report.md](architecture/technical-report.md)
- **OpenClaw CLI proposal**: [openclaw-cli-first.md](architecture/openclaw-cli-first.md)
- **Scale runtime domain**: [../scales-runtime/README.md](../scales-runtime/README.md)
- **Digital twin runtime and requirement events**: [openclaw-digital-twin-runtime.md](architecture/openclaw-digital-twin-runtime.md)
- **API schema draft**: [openclaw-topiclab-api-schema.md](architecture/openclaw-topiclab-api-schema.md)
- **Performance**: [topiclab-performance-optimization.md](architecture/topiclab-performance-optimization.md)
- **Arcade**: [arcade-arena.md](features/arcade-arena.md)
- **Community ops and observability**: [community-operations-observability.md](features/community-operations-observability.md)
- **Digital twin**: [digital-twin-lifecycle.md](features/digital-twin-lifecycle.md)
- **Cognition & portrait stack**: [fun-quiz-and-portrait-stack.md](cognition-portrait/fun-quiz-and-portrait-stack.md)
- **Portrait preview release plan**: [portrait-preview-release-plan.md](cognition-portrait/portrait-preview-release-plan.md)
- **Portrait CLI test-agent skill**: [portrait-cli-test-agent-skill.md](cognition-portrait/portrait-cli-test-agent-skill.md)
- **Deceased scientist candidate pool V1**: [deceased-scientist-candidate-pool-v1.md](cognition-portrait/deceased-scientist-candidate-pool-v1.md)
- **Full portrait scale / skill audit**: [full-portrait-scale-and-skill-audit.md](cognition-portrait/full-portrait-scale-and-skill-audit.md)
- **Light quiz design skeleton**: [light-quiz-design-skeleton.md](cognition-portrait/light-quiz-design-skeleton.md)
- **Light quiz dimensions / type system**: [light-quiz-dimension-and-type-system.md](cognition-portrait/light-quiz-dimension-and-type-system.md)
- **Light quiz question bank V1**: [light-quiz-question-bank-v1.md](cognition-portrait/light-quiz-question-bank-v1.md)
- **Portrait axis selection**: [portrait-axis-selection.md](cognition-portrait/portrait-axis-selection.md)
- **Portrait product strategy / PRD**: [portrait-product-strategy-prd.md](cognition-portrait/portrait-product-strategy-prd.md)
- **Rich de-identified card spec**: [rich-deidentified-card-spec.md](cognition-portrait/rich-deidentified-card-spec.md)
- **Scientist dossier collection pipeline**: [scientist-dossier-collection-pipeline.md](cognition-portrait/scientist-dossier-collection-pipeline.md)
- **Scientist dossier template**: [scientist-dossier-template.md](cognition-portrait/scientist-dossier-template.md)
- **Scientist archetype matrix**: [scientist-archetype-matrix.md](cognition-portrait/scientist-archetype-matrix.md)
- **Scientist perspective skill system**: [scientist-perspective-skill-system.md](cognition-portrait/scientist-perspective-skill-system.md)
- **Scientist corpora root**: [scientist-corpora/README.md](../data/scientist-corpora/README.md)
- **Scientist dossiers archive**: [scientist-dossiers/README.md](cognition-portrait/scientist-dossiers/README.md)
- **Batch 1 strong anchors**: [scientist-dossiers/batch-1-strong-anchors.md](cognition-portrait/scientist-dossiers/batch-1-strong-anchors.md)
- **Scientist anchor source research**: [scientist-anchor-source-research.md](cognition-portrait/scientist-anchor-source-research.md)
- **Scientist reference risk boundary**: [scientist-reference-and-sharing-risk.md](cognition-portrait/scientist-reference-and-sharing-risk.md)
- **Points system**: [points-system.md](features/points-system.md)
- **Deploy**: [deploy.md](getting-started/deploy.md)
- **Backend API**: [backend/docs/api-reference.md](../backend/docs/api-reference.md) | [Resonnet](https://github.com/TashanGKD/Resonnet)
- **TopicLab backend**: [topiclab-backend/README.md](../topiclab-backend/README.md)
