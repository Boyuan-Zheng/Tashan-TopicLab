# Unified Shape System (Tashan World)

Based on the UI/UX Pro Max design system, this document defines the shape (border-radius) specification for the academic research collaboration platform.

---

## 1. Design Principles

### Shape Hierarchy

- **Primary containers**: Large radius, friendly and open
- **Secondary containers**: Medium radius, clear hierarchy
- **Interactive elements**: Unified radius, easy to recognize
- **Badges/tags**: Fully rounded, prominent

### Consistency

- Reduce irregular shapes; use unified radius levels
- Avoid custom radius values (e.g. `rounded-[22px]`)
- All radii managed via CSS variables

---

## 2. Radius Level Definitions (Simplified)

**Design strategy**: Reduce radius types for consistency. Keep only **3 core radius levels**.

| Level | Tailwind Class | CSS Variable | Value | Use | Frequency |
|-------|----------------|--------------|-------|-----|------------|
| **Default** | `rounded-lg` | `--radius-md` | `12px` | **All cards, buttons, inputs, containers** | 70% |
| **Large** | `rounded-xl` | `--radius-lg` | `16px` | **Modals, dropdowns, thumbnails** | 20% |
| **Full** | `rounded-full` | `--radius-full` | `9999px` | **Avatars, chips, badges, filter buttons** | 10% |

### Deprecated Radii

| Radius | Status | Replacement | Note |
|--------|--------|-------------|------|
| `rounded-sm` (6px) | Deprecated | `rounded-lg` | Too small |
| `rounded-md` (8px) | Deprecated | `rounded-lg` | Minimal difference from 12px |
| `rounded-2xl` (20px) | Deprecated | `rounded-xl` | Over-designed; unify to 16px |

### Simplification Principles

1. **One radius for most cases**: `rounded-lg` (12px) for ~90% of scenarios
2. **Special cases**: Modals/dropdowns use `rounded-xl` (16px)
3. **Circular elements**: Avatars/chips use `rounded-full`
4. **No custom values**: Do not use `rounded-[XXpx]`

---

## 3. Component Shape Checklist

### 3.1 Primary Containers

| Component/Page | Current | Target | Priority |
|----------------|---------|--------|----------|
| `OpenClawSkillCard.tsx` | `rounded-2xl` | `rounded-2xl` | P0 |
| `TopicCard.tsx` | `rounded-lg` | `rounded-lg` | P1 |
| `SourceArticleCard.tsx` | `rounded-[22px]` | `rounded-2xl` | P0 |
| `LiteratureCard.tsx` | `rounded-[22px]` | `rounded-2xl` | P0 |
| `ExpertCard.tsx` | `rounded-lg` | `rounded-lg` | P1 |
| `SkillCard.tsx` | `rounded-lg` | `rounded-lg` | P1 |
| `MCPGrid.tsx` | `rounded-lg` | `rounded-lg` | P1 |
| `ModeratorModeGrid.tsx` | `rounded-lg` | `rounded-lg` | P1 |
| `TopicDetail.tsx` (comment container) | `rounded-[28px]` | `rounded-2xl` | P0 |
| `TopicDetail.tsx` (reply container) | `rounded-[26px]` | `rounded-2xl` | P0 |
| `TopicDetail.tsx` (inner container) | `rounded-[22px]` | `rounded-2xl` | P0 |
| `MyFavoritesPage.tsx` (empty state) | `rounded-[20px]` | `rounded-2xl` | P1 |

### 3.2 Input Fields

All inputs use `rounded-lg` (standard).

### 3.3 Buttons

| Component | Current | Target |
|-----------|---------|--------|
| Primary buttons | `rounded-lg` | `rounded-lg` |
| Chip-style filters | `rounded-full` | `rounded-full` |

### 3.4 Badges/Tags

Avatars, chips, badges: `rounded-full`.

### 3.5 Dropdowns & Modals

Modals and dropdowns: `rounded-xl` (large radius).

---

## 4. CSS Variables (Simplified)

In `frontend/src/index.css`:

```css
:root {
  --radius-sm: 12px;     /* Deprecated, maps to --radius-md */
  --radius-md: 12px;     /* Default - cards, buttons, inputs (70%) */
  --radius-lg: 16px;     /* Large - modals, dropdowns, thumbnails (20%) */
  --radius-xl: 16px;     /* Deprecated, maps to --radius-lg */
  --radius-2xl: 16px;    /* Deprecated, maps to --radius-lg */
  --radius-full: 9999px;  /* Full circle - avatars, chips, badges (10%) */
}
```

---

## 5. Usage Guide

### Correct

```tsx
<div className="rounded-lg border">Card</div>
<div className="rounded-xl shadow-xl">Modal</div>
<div className="rounded-full">Avatar</div>
```

### Avoid

```tsx
// Custom radius
<div className="rounded-[22px]"> → use `rounded-2xl`
```

---

**Document version**: 2.0 (Simplified)  
**Last updated**: 2026-03-15  
**Design system**: UI/UX Pro Max - Soft UI Evolution
