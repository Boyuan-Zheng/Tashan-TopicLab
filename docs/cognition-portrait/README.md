# Cognition & Portrait Docs

This directory stores product and policy documents for TopicLab's cognition, persona, and portrait experiences.

Implementation-heavy scale-runtime protocol work is intentionally separated into [../../scales-runtime/README.md](../../scales-runtime/README.md), especially the runtime, session, backend-mapping, and unified human/agent interaction architecture documents, so portrait business assets stay decoupled from generic CLI infrastructure.

It is the preferred place to document work related to:

- playful persona quizzes and shareable result cards
- research-profile generation and full digital-twin portraits
- de-identification and safe-to-share portrait surfaces
- scientist-reference usage rules, image-source policy, and legal-risk boundaries

## Current Focus

The current direction is not a single portrait product. It is a layered stack:

1. `Light quiz`: interesting questions, low-friction entry, fun share card
2. `Full portrait`: user can continue with a deeper AI-assisted portrait flow
3. `Rich de-identified card`: more informative than the light card, but safe to share

## Document Map

| Document | Purpose |
|---|---|
| [fun-quiz-and-portrait-stack.md](fun-quiz-and-portrait-stack.md) | Defines the product stack, user journey, card layers, field design, and staged rollout |
| [portrait-preview-release-plan.md](portrait-preview-release-plan.md) | Recommended public-preview rollout for the new portrait product across GitHub preview branch/tagging, npm prerelease, and tester installation paths |
| [deceased-scientist-candidate-pool-v1.md](deceased-scientist-candidate-pool-v1.md) | First 120-person candidate pool of deceased scientists for future type anchors, naming work, and share-card references |
| [full-portrait-scale-and-skill-audit.md](full-portrait-scale-and-skill-audit.md) | Audit of the full portrait stack: three scales, dimensions, scoring, skill architecture, evidence strength, and current integration gaps |
| [portrait-cli-test-agent-skill.md](portrait-cli-test-agent-skill.md) | Single canonical onboarding document for any external testing agent, including install, bootstrap, login, continuous CLI use, reporting, and a ready-to-forward prompt |
| [light-quiz-design-skeleton.md](light-quiz-design-skeleton.md) | Design skeleton for turning playful research-life questions into stable dimension sampling and recognizable portrait archetypes |
| [light-quiz-dimension-and-type-system.md](light-quiz-dimension-and-type-system.md) | Defines the lightweight quiz dimensions, question principles, and original type-system design |
| [light-quiz-question-bank-v1.md](light-quiz-question-bank-v1.md) | First 20-question draft with research-life scenarios, playful answer voice, and hidden dimension tags |
| [portrait-axis-selection.md](portrait-axis-selection.md) | Recommends which four axes should define the main type system under scientific-validity and relative-independence constraints |
| [portrait-product-strategy-prd.md](portrait-product-strategy-prd.md) | Product-manager view of the portrait line: users, JTBD, funnel, MVP, metrics, and roadmap |
| [rich-deidentified-card-spec.md](rich-deidentified-card-spec.md) | Defines the rich shareable card schema, content layers, de-identification rules, and field mapping |
| [scientist-dossier-collection-pipeline.md](scientist-dossier-collection-pipeline.md) | Collection workflow for turning the 120-person deceased-scientist pool into a structured, comparable dossier archive |
| [scientist-dossier-template.md](scientist-dossier-template.md) | Standard per-scientist dossier template for future archive files, anchor summaries, and type-mapping work |
| [scientist-archetype-matrix.md](scientist-archetype-matrix.md) | Formal 16-archetype scientist classification matrix based on four main axes plus the `I / D` research-style suffix |
| [scientist-perspective-skill-system.md](scientist-perspective-skill-system.md) | Explains the generated scientist-twin skill layer that turns dossier + corpus assets into 120 perspective skills under `.cursor/skills/` |
| [../../data/scientist-corpora/README.md](../../data/scientist-corpora/README.md) | Public-only corpus workspaces and AI-ready packages for the 120-person deceased-scientist archive |
| [scientist-dossiers/README.md](scientist-dossiers/README.md) | Live archive root for the 120-person deceased-scientist dossier library, with per-person dossier files and research buckets |
| [scientist-dossiers/batch-1-strong-anchors.md](scientist-dossiers/batch-1-strong-anchors.md) | First reviewed batch of 20 stronger anchor figures selected for early type-mapping and naming work |
| [scientist-anchor-source-research.md](scientist-anchor-source-research.md) | External research on source systems, rankings, biography archives, and candidate-building strategy for deceased-scientist anchor pools |
| [scientist-reference-and-sharing-risk.md](scientist-reference-and-sharing-risk.md) | Defines legal-risk boundaries, scientist-reference rules, image policy, and de-identification guidance |

## Writing Rules For This Folder

- Prefer recording product decisions, constraints, and verified risk boundaries.
- Keep legal content framed as product guidance unless reviewed by counsel.
- When new portrait surfaces are added, document:
  - what is private
  - what is shareable
  - what is derived
  - what must be de-identified
- If the implementation path changes, update this directory together with the relevant feature/design docs.
