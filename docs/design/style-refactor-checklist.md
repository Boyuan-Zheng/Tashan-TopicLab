# Page and Component Space Checklist (Tashan World)

This document lists all pages and components for unified color and style refactoring.

---

## 1. Global Layer

| File | Description | Status |
|------|-------------|--------|
| `src/index.css` | Global styles, CSS variables, animations | Done |
| `src/App.tsx` | App entry, routing | Done |
| `src/components/TopNav.tsx` | Top navigation | Done |
| `src/components/Footer.tsx` | Footer | Done |
| `src/components/AppErrorBoundary.tsx` | Error boundary | Done |
| `tailwind.config.js` | Tailwind config | Done |

---

## 2. Pages

### 2.1 Topic-Related

| File | Route | Description | Status |
|------|-------|-------------|--------|
| `src/pages/TopicList.tsx` | `/` | Topic list home | Pending |
| `src/pages/TopicDetail.tsx` | `/topics/:id` | Topic detail | Pending |
| `src/pages/CreateTopic.tsx` | `/topics/new` | Create topic | Pending |

### 2.2 Source Feed

| File | Route | Description | Status |
|------|-------|-------------|--------|
| `src/pages/SourceFeedPage.tsx` | `/source-feed/:section` | Source feed | Pending |

### 2.3 Library

| File | Route | Description | Status |
|------|-------|-------------|--------|
| `src/pages/LibraryPage.tsx` | `/library/:section` | Library (unified entry) | Pending |
| `src/pages/ExpertList.tsx` | - | Expert list | Pending |
| `src/pages/ExpertEdit.tsx` | `/experts/:name/edit` | Expert edit | Pending |
| `src/pages/SkillLibrary.tsx` | - | Skill library | Pending |
| `src/pages/MCPLibrary.tsx` | - | MCP library | Pending |
| `src/pages/ModeratorModeLibrary.tsx` | - | Moderator mode library | Pending |

### 2.4 Agent Links

| File | Route | Description | Status |
|------|-------|-------------|--------|
| `src/pages/AgentLinkLibraryPage.tsx` | `/agent-links` | Agent Link library | Pending |
| `src/pages/AgentLinkChatPage.tsx` | `/agent-links/:slug` | Agent Link chat | Pending |

### 2.5 User

| File | Route | Description | Status |
|------|-------|-------------|--------|
| `src/pages/Login.tsx` | `/login` | Login | Pending |
| `src/pages/Register.tsx` | `/register` | Register | Pending |
| `src/pages/MyFavoritesPage.tsx` | `/favorites` | My favorites | Pending |

### 2.6 Profile Helper

| File | Route | Description | Status |
|------|-------|-------------|--------|
| `src/pages/ProfileHelperPage.tsx` | `/profile-helper/*` | Digital persona home | Pending |

---

## 3. Components

### 3.1 Layout

| File | Description | Status |
|------|-------------|--------|
| `src/components/LibraryPageLayout.tsx` | Library layout | Done |
| `src/components/TabPanel.tsx` | Tab panel | Pending |
| `src/components/ResizableToc.tsx` | Resizable TOC | Pending |

### 3.2 Cards

| File | Description | Status |
|------|-------------|--------|
| `src/components/TopicCard.tsx` | Topic card | Pending |
| `src/components/ExpertCard.tsx` | Expert card | Pending |
| `src/components/SkillCard.tsx` | Skill card | Pending |
| `src/components/MCPCard.tsx` | MCP card | Pending |
| `src/components/OpenClawSkillCard.tsx` | OpenClaw skill card (home top) | Pending |
| `src/components/ModeratorModeCard.tsx` | Moderator mode card | Pending |
| `src/components/SourceArticleCard.tsx` | Source article card | Pending |
| `src/components/SourceArticlePreviewCard.tsx` | Source article preview | Pending |
| `src/components/LiteratureCard.tsx` | Literature card | Pending |

### 3.3 Grids

| File | Description | Status |
|------|-------------|--------|
| `src/components/ExpertGrid.tsx` | Expert grid | Pending |
| `src/components/SkillGrid.tsx` | Skill grid | Pending |
| `src/components/MCPGrid.tsx` | MCP grid | Pending |
| `src/components/ModeratorModeGrid.tsx` | Moderator mode grid | Pending |

### 3.4 Modals

| File | Description | Status |
|------|-------------|--------|
| `src/components/ExpertDetailModal.tsx` | Expert detail | Pending |
| `src/components/SkillDetailModal.tsx` | Skill detail | Pending |
| `src/components/MCPDetailModal.tsx` | MCP detail | Pending |
| `src/components/ModeratorModeDetailModal.tsx` | Moderator mode detail | Pending |
| `src/components/ResourceDetailModal.tsx` | Resource detail | Pending |

### 3.5 Selectors

| File | Description | Status |
|------|-------------|--------|
| `src/components/ExpertSelector.tsx` | Expert selector | Pending |
| `src/components/SkillSelector.tsx` | Skill selector | Pending |
| `src/components/MCPServerSelector.tsx` | MCP selector | Pending |
| `src/components/ModeratorModeSelector.tsx` | Moderator mode selector | Pending |
| `src/components/FavoriteCategoryPicker.tsx` | Favorite category picker | Pending |

---

## 4. Refactor Priority

### P0 - Core Pages

1. `TopicList.tsx` - Home
2. `TopNav.tsx` - Navigation (done)
3. `Footer.tsx` - Footer (done)
4. `OpenClawSkillCard.tsx` - Home top card

### P1 - Main Feature Pages

1. `TopicDetail.tsx` - Topic detail
2. `SourceFeedPage.tsx` - Source feed
3. `LibraryPage.tsx` + library pages
4. `Login.tsx` / `Register.tsx`

### P2 - Cards and Lists

1. Card components
2. Grid components
3. Modal components

### P3 - Selectors and Helpers

1. Selector components
2. Form-related components

### P4 - Modules

1. Profile Helper module
2. Agent Links module

---

## 5. Design Spec Summary

### Color System

- **Primary**: `--color-primary: #5B9BD5` (light blue)
- **Secondary**: `--color-secondary: #9FD4C4` (light green)
- **Accent**: `--color-accent: #6BC5D6`
- **Dark**: `--color-dark: #0E2E4F`
- **Darker**: `--color-darker: #0A1F35`

### Backgrounds

- **Page**: `#F8FAFB` + subtle gradient
- **Card**: `#FFFFFF`
- **Footer**: `--gradient-dark`

### Buttons

- **Primary**: `--color-dark` (solid, not gradient)
- **Secondary**: Border style
- **Hover**: Slight lift + enhanced shadow

### Typography

- **Brand**: Sans-serif + letter-spacing
- **Body**: Serif (Noto Serif SC)
- **Headings**: Dark color; avoid highlight gradients

---

*Last updated: 2026-03-15*
