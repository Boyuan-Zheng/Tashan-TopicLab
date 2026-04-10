# Unified Portrait Interaction Architecture

## Why This Document Exists

TopicLab is not being redefined into a portrait-only product.

TopicLab already has many existing features. What is happening here is that a
new portrait capability is being added into the same larger product, using the
same overall frontend while introducing new pages and flows.

Within that larger product, the portrait capability already has multiple
interaction surfaces:

1. users can directly complete the three portrait scales
2. users can talk to a lightweight in-product agent
3. the system can generate a prompt for an external AI platform
4. users can paste the external AI output back into TopicLab
5. TopicLab can then parse that material and return a structured portrait

Historically, these flows were designed around human interaction.

The current architectural goal is to upgrade that same portrait capability so
both of these callers can use it:

- human users
- agents operating through CLI or other machine interfaces

This document records that unifying view so the system does not accidentally
split into one "human portrait feature set" and one separate "agent portrait
tool."

## Core Position

The correct abstraction is:

- one larger TopicLab product
- one portrait business domain inside it
- one runtime truth
- multiple interaction adapters

The standalone CLI and future `topiclab-cli` integration are therefore not new
products.

They are additional adapters for the same portrait runtime inside TopicLab.

## Operational Path Versus Product Path

These two paths must stay conceptually separate.

### Operational path

This is the engineering path used to ship and validate the system:

- SSH
- staging server access
- dependency installation
- process startup
- deployment and rollback

This path is necessary for building and operating the portrait system, but it
is **not** the intended end-user or end-agent interaction model.

### Product path

This is the interaction model the portrait system should eventually expose:

- a local CLI adapter
- machine-readable auth/session handling
- remote HTTP calls into the deployed portrait runtime
- resumable interactions without manual SSH usage

So the target loop is:

- local human or local agent runs CLI
- CLI talks to remote TopicLab portrait runtime
- remote runtime persists state and returns structured results

SSH should remain an operator tool, not the normal product entry point.

## What Already Exists

The current portrait business domain already has three real interaction modes.

### A. Direct scale testing

Users can answer the three portrait scales directly.

Current reference assets include:

- `frontend/src/modules/profile-helper/data/scales.ts`
- `frontend/src/modules/profile-helper/utils/scoring.ts`
- `frontend/src/modules/profile-helper/pages/ScaleTestPage.tsx`

### B. Lightweight in-product portrait dialogue

Users can interact with the existing profile-helper conversation flow and
gradually build portrait material through guided exchange.

This is already a separate interaction surface from direct questionnaire
answering.

### C. External-AI prompt handoff and return

The product can also guide users into a deeper portrait flow by:

1. providing a prompt
2. asking the user to run that prompt on another AI platform
3. asking the user to paste the result back
4. parsing the returned text into a fuller portrait

That means the portrait capability is already more than a single questionnaire
page.

It is already a layered portrait subsystem inside TopicLab.

## Architectural Upgrade Now Underway

The new requirement is not "build an agent-only side system."

The new requirement is:

- keep the existing TopicLab product and existing human-facing portrait paths
- let agents also interact with the same portrait runtime through CLI

The important change is therefore at the interaction layer, not at the product
identity layer.

## The Correct System Shape

The system should be treated as four layers.

### 1. Portrait runtime

This is the domain truth.

It should own:

- canonical scale definitions
- canonical scoring
- session lifecycle
- answer persistence
- result materialization
- structured portrait outputs

This is what `scales-runtime/` and the new backend `scales` modules are trying
to establish.

### 2. Portrait orchestration

This layer coordinates portrait workflows inside TopicLab that are larger than
one form:

- lightweight portrait dialogue
- prompt generation for external AI
- pasted-result ingestion
- future orchestration across scales + dialogue + imported outputs

This layer should consume the runtime truth, not create a second truth.

### 3. Interaction adapters

This layer is how callers talk to the system.

Examples:

- Web UI
- standalone CLI
- future `topiclab-cli`
- internal test harnesses
- future agent runners

These adapters should stay thin.

They should not become a second place that owns:

- question text
- scoring logic
- portrait interpretation rules

### 4. Callers

These are the actual users or agents of the system.

Examples:

- a human user on the web
- a human user in a terminal
- an internal scientist twin
- a lightweight built-in agent
- a future external agent using CLI

These callers can differ, but they should still enter the same portrait runtime.

## Key Principle: Human And Agent Must Share The Same Contract

The architecture should converge toward one session contract that works for both
human and agent callers.

For scale testing, that means:

- a human can answer one question at a time
- an agent can answer one question at a time
- a human can resume a session later
- an agent can resume a session later
- both go through the same finalize path
- both get results from the same canonical scoring engine

This is why the new scale runtime is modeled as a state machine instead of a
one-shot submit endpoint.

## Why CLI Is An Adapter, Not A Side System

The CLI work should not produce a parallel portrait implementation.

The CLI is only valuable if it proves that the same portrait capability inside
TopicLab can be used in a machine-readable, resumable way.

So the right mental model is:

- Web UI = one adapter
- standalone CLI = one adapter
- future `topiclab-cli` = one adapter

Not:

- Web portrait product
- CLI portrait product
- agent portrait product

Those would drift apart and create multiple truths inside the same product.

## Why Standalone First Was The Right Step

The standalone CLI was intentionally built before changing `TopicLab-CLI`
because the runtime needed to be proven independently first.

That step has now established:

- canonical scale definitions under `scales-runtime/definitions/`
- backend-owned scoring and result persistence
- a resumable scale session loop
- a local standalone CLI that can really complete the loop
- a migration-compatible `bind_key` auth shape

This means the next `TopicLab-CLI` work can stay thin.

It does not need to invent a new portrait runtime.

It only needs to adopt it.

## Near-Term Boundary

For now, this unified architecture is only fully implemented for the direct
scale-testing part of the portrait business domain.

That is intentional.

The current rollout order is:

1. make the three direct scales runtime-grade and CLI-usable
2. let humans and agents share that runtime
3. later extend the same runtime thinking to:
   - lightweight portrait dialogue
   - external prompt handoff
   - returned-result ingestion

So today, "unified portrait interaction architecture" is a design truth for the
portrait business domain inside TopicLab, but the concrete implementation is
currently deepest in the scales domain.

## Migration Implication

Because TopicLab is one larger product and portrait is one business domain with
multiple adapters, future migration should follow this order:

1. prove runtime truth in the dedicated scale domain
2. expose that truth through the standalone CLI
3. migrate the same command surface into `TopicLab-CLI`
4. let the web layer gradually consume the same runtime
5. let internal twins and future agents use the same session protocol

This order minimizes coupling and prevents early shared-infrastructure churn.

## Practical Design Rules

### Rule 1. Runtime truth must stay backend-owned

Scoring, completion, and result materialization should stay server-side.

### Rule 2. Adapters must stay thin

CLI and web should call the runtime; they should not re-implement it.

### Rule 3. Human-first and agent-first are both wrong

The correct target is caller-agnostic runtime design.

### Rule 4. External-AI prompt flows are part of the same portrait domain

Prompt generation and pasted-result return should eventually be modeled as
runtime-supported portrait interactions, not forever as ad hoc UI glue.

### Rule 5. Internal scientist twins are test callers, not a separate product

The 120 scientist twins are useful because they can exercise the same
interaction contract, but they should not force the runtime to become
scientist-specific.

### Rule 6. Important portrait data must be server-owned and durable

No important portrait interaction should exist only in:

- browser local storage
- local CLI state
- backend process memory
- temporary filesystem working caches

Local state is acceptable as cache or recovery aid, but not as long-term truth.

The portrait application should eventually persist all important interaction
data on the server or in the database, including:

- scale sessions, answers, and results
- portrait dialogue transcripts
- prompt handoff records
- pasted external-AI outputs
- portrait update history
- agent execution logs and runtime traces

## Current Proven Facts

As of 2026-04-10, the following path has been proven in files and execution:

- scale definitions are normalized under `scales-runtime/definitions/`
- backend scale routes exist locally under `/api/v1/scales/...`
- standalone CLI can complete a local scale loop end-to-end
- standalone CLI `bind_key` auth can bootstrap successfully against the live
  public site
- the current live blocker is route deployment, not the adapter shape

This means the unification strategy is no longer theoretical.

It already has a validated first slice.

## What This Document Does Not Claim

This document does not claim that the whole TopicLab product is already unified
around portrait.

It only claims:

- the correct architecture is now clear
- the first runtime slice is already real
- future CLI and agent work should extend the same application, not fork it
- important portrait-domain data should progressively move away from local-only
  state and into durable server-owned persistence
