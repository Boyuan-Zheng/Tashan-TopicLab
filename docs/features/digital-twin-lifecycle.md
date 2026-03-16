# Digital Twin End-to-End Lifecycle (Create / Publish / Share / History)

## Table of Contents

- [1. Goals and Scope](#1-goals-and-scope)
- [2. Roles and Components](#2-roles-and-components)
- [3. End-to-End Primary Flow](#3-end-to-end-primary-flow)
- [4. Key Sequence Diagrams](#4-key-sequence-diagrams)
- [5. State Transition Diagram](#5-state-transition-diagram)
- [6. History List and Detail View Flow](#6-history-list-and-detail-view-flow)
- [7. Data Model Mapping](#7-data-model-mapping)
- [8. API Inventory](#8-api-inventory)
- [9. Lifecycle Timeline](#9-lifecycle-timeline)
- [10. Failure and Fallback Strategy](#10-failure-and-fallback-strategy)
- [11. Import into Topic Experts (Private Masking)](#11-import-into-topic-experts-private-masking)

---

## 1. Goals and Scope

This document describes the complete digital twin loop:
creation, publication, persistence, sharing state, and history review.

| Capability | Description |
|---|---|
| Twin creation | Build profile and forum profile from chat collection and scale tests |
| Twin publishing | Set `display_name`, `visibility`, and `exposure` in "My Twin" |
| Persistence | Optionally sync to account service `digital_twins` after publish |
| Share state | Use `visibility=public/private` to control sharing |
| History review | Show twin history list and record detail on demand |

---

## 2. Roles and Components

```mermaid
flowchart LR
    U[User]
    F[Frontend<br/>Profile Helper]
    R[Resonnet Backend<br/>/profile-helper/*]
    FS[(User Workspace Files)]
    T[TopicLab Auth Backend<br/>/auth/*]
    DB[(PostgreSQL<br/>digital_twins)]

    U --> F
    F --> R
    R --> FS
    R --> T
    T --> DB
    F --> T
```

Responsibilities:

- Frontend: hosts "My Twin", publish form, history list, and detail panel.
- Resonnet backend: generates twin content and executes publish flow; optionally syncs to account service.
- TopicLab auth backend: handles identity and twin persistence in `digital_twins`.
- PostgreSQL: stores twin records and optional detail payload (`role_content`).

---

## 3. End-to-End Primary Flow

```mermaid
flowchart TD
    A[Open chat collection] --> B[Create or reuse session]
    B --> C[Collect profile context by multi-turn chat]
    C --> D[Generate profile and forum profile]
    D --> E[Optional: complete scales and save]
    E --> F[Open My Twin page]
    F --> G[Set publish params<br/>display_name / visibility / exposure]
    G --> H[Call publish-to-library]
    H --> I[Resonnet writes to workspace]
    I --> J{ACCOUNT_SYNC_ENABLED?}
    J -- Yes --> K[Sync to account service digital_twins]
    J -- No --> L[Skip sync and return]
    K --> M[Frontend refreshes history]
    L --> M
    M --> N[User opens history detail]
```

---

## 4. Key Sequence Diagrams

### 4.1 Create and Publish

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend ProfilePage
    participant RH as Resonnet /profile-helper
    participant FS as User Workspace
    participant AH as TopicLab /auth
    participant DB as PostgreSQL

    User->>FE: Open "My Twin" after chat/scales
    FE->>RH: GET /profile-helper/profile/{session_id}
    RH->>FS: Read profile.md / forum_profile.md / scales.json
    RH-->>FE: Return twin content

    User->>FE: Click "Rename and publish to website"
    FE->>RH: POST /profile-helper/publish-to-library
    RH->>FS: Write users/{uid}/agents/my_twin/role.md + meta.json
    opt ACCOUNT_SYNC_ENABLED=true
      RH->>AH: POST /auth/digital-twins/upsert (Bearer token)
      AH->>DB: UPSERT digital_twins
      DB-->>AH: OK
      AH-->>RH: OK
    end
    RH-->>FE: Publish success (display_name/visibility/exposure)
```

### 4.2 History List and Detail

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend ProfilePage
    participant AH as TopicLab /auth
    participant DB as PostgreSQL

    FE->>AH: GET /auth/digital-twins
    AH->>DB: SELECT by user_id ORDER BY updated_at DESC
    DB-->>AH: rows
    AH-->>FE: digital_twins[]
    FE-->>User: Render history list with visibility state

    User->>FE: Click one history item
    FE->>AH: GET /auth/digital-twins/{agent_name}
    AH->>DB: SELECT one record
    DB-->>AH: detail row
    AH-->>FE: digital_twin(role_content...)
    FE-->>User: Render record detail
```

---

## 5. State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> Draft: Collection in progress
    Draft --> Generated: Twin content generated
    Generated --> PublishedPrivate: Publish (visibility=private)
    Generated --> PublishedShared: Publish (visibility=public)
    PublishedPrivate --> PublishedShared: Republish as shared
    PublishedShared --> PublishedPrivate: Republish as private
    PublishedPrivate --> HistoryVisible: Visible in history list
    PublishedShared --> HistoryVisible: Visible in history list
    HistoryVisible --> DetailViewed: User opens record detail
```

Notes:

- "Private" and "Shared" are visibility states of the same twin model.
- Published records are shown in `updated_at` descending order.

---

## 6. History List and Detail View Flow

```mermaid
flowchart TD
    A[Page load] --> B[Request digital_twins list]
    B --> C{Has records?}
    C -- No --> D[Show empty state]
    C -- Yes --> E[Render list and status badges]
    E --> F[Select first or last selected record]
    F --> G[Request detail by agent_name]
    G --> H{Detail success?}
    H -- No --> I[Show load-failed hint]
    H -- Yes --> J[Render role_content and metadata]
```

UI highlights:

- List badges: `Shared (public)` / `Private (private)`.
- Detail panel: name, visibility, exposure, updated time, and content text.

---

## 7. Data Model Mapping

### 7.1 Frontend List Record (Summary)

| Field | Meaning |
|---|---|
| `agent_name` | Internal unique twin key |
| `display_name` | User-visible twin name |
| `visibility` | `private` / `public` |
| `exposure` | `brief` / `full` |
| `updated_at` | Last update timestamp |
| `has_role_content` | Whether detail content exists |

### 7.2 Frontend Detail Record (Summary)

| Field | Meaning |
|---|---|
| `role_content` | Twin detail text rendered in detail panel |
| Other fields | Same as list payload (state and timestamps) |

### 7.3 Account DB `digital_twins` Key Fields

| Field | Meaning |
|---|---|
| `user_id` | User ID |
| `agent_name` | Twin key (unique within user scope) |
| `display_name` | Twin display name |
| `visibility` | Private/shared visibility |
| `exposure` | Published content scope |
| `role_content` | Twin detail payload |
| `created_at` / `updated_at` | Creation/update timestamps |

---

## 8. API Inventory

| Service | Endpoint | Purpose |
|---|---|---|
| Resonnet | `POST /profile-helper/publish-to-library` | Publish twin and optionally trigger sync |
| TopicLab Auth | `POST /auth/digital-twins/upsert` | Create/update twin record |
| TopicLab Auth | `GET /auth/digital-twins` | List twin history |
| TopicLab Auth | `GET /auth/digital-twins/{agent_name}` | Get one twin detail |

---

## 9. Lifecycle Timeline

```mermaid
timeline
    title Digital Twin Lifecycle
    section Creation
      Chat collection : Create session and collect context
      Scale collection : Save scale results to workspace
      Content generation : Build profile and forum_profile
    section Publish
      Parameter setup : Set display_name / visibility / exposure
      Publish action : Call publish-to-library
      Account sync : Upsert into digital_twins
    section Review
      History list : Fetch all records
      Detail open : Fetch by agent_name
      State check : Distinguish private and shared
```

---

## 10. Failure and Fallback Strategy

| Scenario | Symptom | Handling |
|---|---|---|
| `AUTH_MODE=jwt` with missing/expired token | List/detail calls fail | Prompt user to re-login |
| Account service is temporarily unavailable | Publish succeeds but sync fails | Return `sync_status=failed`, prompt retry |
| One record has no `role_content` | Empty detail panel | Show "No detail content available" |
| History is empty | No selectable item | Show empty state and guide user to publish first |

---

## 11. Import into Topic Experts (Private Masking)

In topic expert configuration, users can import their twin as a discussion expert:

- `visibility=public`: import full `role_content`.
- `visibility=private`: import masked content; backend `GET /topics/{topic_id}/experts/{expert_name}/content` returns `masked=true` to avoid exposing original private text.

This keeps private source data protected while still allowing discussion participation.
