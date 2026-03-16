# Unified Color System (Tashan World)

Based on the UI/UX Pro Max design system, this document defines the color specification for the academic research collaboration platform.

---

## 1. Color System Overview

### Design Principles

- **Academic and professional**: Calm, trustworthy tones
- **Soft and comfortable**: Easy on the eyes for long reading
- **Clear hierarchy**: Distinct information levels
- **Accessible**: WCAG AA+ contrast standards

### Style

**Soft UI Evolution** — Evolved soft UI with better contrast, modern aesthetics, subtle depth

---

## 2. Core Color Definitions

### 2.1 Brand Colors

| Name | Value | Use | CSS Variable |
|------|-------|-----|--------------|
| **Primary** | `#3B82F6` | Brand, logo, brand elements | `--brand-primary` |
| **Dark** | `#1E40AF` | Dark variant, footer background | `--brand-dark` |
| **Light** | `#DBEAFE` | Light background, tag background | `--brand-light` |

### 2.2 Accent Colors

| Name | Value | Use | CSS Variable |
|------|-------|-----|--------------|
| **Accent** | `#0EA5E9` | Links, focus, selected state | `--accent-primary` |
| **Success** | `#10B981` | Success, create button, positive feedback | `--accent-success` |
| **Warning** | `#F59E0B` | Warning, pending | `--accent-warning` |
| **Error** | `#EF4444` | Error, delete button, negative feedback | `--accent-error` |
| **Info** | `#3B82F6` | Info, help | `--accent-info` |

### 2.3 Background Colors

| Name | Value | Use | CSS Variable |
|------|-------|-----|--------------|
| **Page** | `#F8FAFC` | Global page background | `--bg-page` |
| **Container** | `#FFFFFF` | Cards, panels, modals | `--bg-container` |
| **Secondary** | `#F1F5F9` | Secondary areas, table stripes | `--bg-secondary` |
| **Hover** | `#F1F5F9` | Hover state | `--bg-hover` |
| **Selected** | `#E0F2FE` | Selected item background | `--bg-selected` |
| **Disabled** | `#E2E8F0` | Disabled state | `--bg-disabled` |
| **Footer** | `#0E2E4F` | Footer dark background | `--bg-footer` |

### 2.4 Text Colors

| Name | Value | Use | CSS Variable |
|------|-------|-----|--------------|
| **Primary** | `#1E293B` | Headings, body, important | `--text-primary` |
| **Secondary** | `#475569` | Descriptions, metadata | `--text-secondary` |
| **Tertiary** | `#94A3B8` | Placeholders, hints | `--text-tertiary` |
| **Disabled** | `#CBD5E1` | Disabled text | `--text-disabled` |
| **Inverse** | `#FFFFFF` | Text on dark backgrounds | `--text-inverse` |

### 2.5 Border Colors

| Name | Value | Use | CSS Variable |
|------|-------|-----|--------------|
| **Default** | `#E2E8F0` | Borders, dividers | `--border-default` |
| **Hover** | `#CBD5E1` | Hover border | `--border-hover` |
| **Focus** | `#3B82F6` | Input focus | `--border-focus` |
| **Active** | `#0EA5E9` | Selected, active | `--border-active` |

---

## 3. CSS Variable Definitions

Add to `src/index.css` `:root`:

```css
:root {
  --brand-primary: #3B82F6;
  --brand-dark: #1E40AF;
  --brand-light: #DBEAFE;

  --accent-primary: #0EA5E9;
  --accent-success: #10B981;
  --accent-warning: #F59E0B;
  --accent-error: #EF4444;
  --accent-info: #3B82F6;

  --bg-page: #F8FAFC;
  --bg-container: #FFFFFF;
  --bg-secondary: #F1F5F9;
  --bg-hover: #F1F5F9;
  --bg-selected: #E0F2FE;
  --bg-disabled: #E2E8F0;

  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-tertiary: #94A3B8;
  --text-disabled: #CBD5E1;
  --text-inverse: #FFFFFF;

  --border-default: #E2E8F0;
  --border-hover: #CBD5E1;
  --border-focus: #3B82F6;
  --border-active: #0EA5E9;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-xl: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
}
```

---

## 4. Migration Guide

### Old → New Variable Mapping

| Old | New | Note |
|-----|-----|------|
| `--color-primary` | `--brand-primary` | Brand primary |
| `--color-secondary` | `--accent-primary` | Accent |
| `--color-dark` | `--text-primary` | Primary text |
| `--color-gray` | `--text-secondary` | Secondary text |
| `--color-gray-light` | `--border-default` | Border |
| `--gradient-primary` | Remove | No longer use gradients |
| `--gradient-dark` | `--brand-dark` | Footer uses solid color |

---

*Last updated: 2026-03-15*
