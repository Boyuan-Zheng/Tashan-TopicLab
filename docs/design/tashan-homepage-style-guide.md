# Tashan Homepage UI Single-File Specification

This document contains the **minimal specification set** for replicating the Tashan homepage visual and interaction style: design tokens, key CSS classes, component behavior contracts, content data schema, and page templates. Implementation does not require the original project source.

---

## 0. Quick Reference

- **Visual style**: Light, academic/innovative; primary colors "light blue + light green" gradient; card-based information structure; large titles/numbers use gradient text.
- **Layout skeleton** (fixed per page): `page-wrapper` → `page-header` (unified header image) → content `section` + `container`.
- **Interaction**: Clickable elements hover with slight lift (`y:-2~5`) + light scale (`scale:1.02`) + enhanced shadow.
- **Animation**: Fade-in on viewport entry (e.g. Framer Motion); avoid exaggeration; unified easing `cubic-bezier(0.4,0,0.2,1)`.
- **Component language**: Fixed header + scroll frosted state + dropdown; dark footer; content as cards/carousel/list.

---

## 1. Design Tokens (CSS Variables)

Copy these `:root` variables to global CSS (e.g. `App.css` / `global.css`) to align ~80% of the visual style.

```css
:root {
  /* Brand (light blue + light green) */
  --color-primary: #5B9BD5;
  --color-secondary: #9FD4C4;
  --color-accent: #6BC5D6;
  --color-accent-light: #B5E5C8;

  /* Neutrals */
  --color-dark: #0E2E4F;
  --color-darker: #0A1F35;
  --color-light: #FFFFFF;
  --color-gray: #6C757D;
  --color-gray-light: #E9ECEF;
  --color-gray-dark: #495057;

  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #5B9BD5 0%, #9FD4C4 100%);
  --gradient-secondary: linear-gradient(135deg, #6BC5D6 0%, #B5E5C8 100%);
  --gradient-accent: linear-gradient(135deg, #5B9BD5 0%, #B5E5C8 100%);
  --gradient-dark: linear-gradient(135deg, #0E2E4F 0%, #0A1F35 100%);
  --gradient-banner: linear-gradient(135deg, #5B9BD5 0%, #B5E5C8 100%);

  /* Shadows */
  --shadow-sm: 0 2px 8px rgba(15, 46, 79, 0.08);
  --shadow-md: 0 4px 16px rgba(15, 46, 79, 0.12);
  --shadow-lg: 0 8px 32px rgba(15, 46, 79, 0.15);
  --shadow-accent: 0 4px 16px rgba(107, 197, 214, 0.25);

  /* Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-xl: 32px;

  /* Transitions */
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## 2. Key CSS Classes

These are the minimal necessary classes for consistent layout and visual syntax.

```css
/* Layout skeleton */
.page-wrapper { width: 100%; min-height: calc(100vh - 400px); }
.container { max-width: 1200px; width: 100%; margin: 0 auto; padding: 0 24px; }
section { padding: 100px 0; position: relative; width: 100%; }

/* Page header (unified background) */
.page-header {
  background-image: url('/media/bg_horizontal.webp');
  background-size: cover;
  background-position: center;
  padding: 120px 0 80px;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-md);
}
.page-title {
  font-size: 56px;
  font-weight: 800;
  margin-bottom: 16px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.page-subtitle { font-size: 20px; color: var(--color-gray); font-weight: 500; }

/* Section headers */
.section-title {
  font-size: 48px; font-weight: 700; margin-bottom: 16px;
  background: var(--gradient-primary);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Buttons */
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 14px 32px; border-radius: var(--radius-lg); font-size: 16px; font-weight: 600; text-decoration: none; cursor: pointer; transition: var(--transition); border: none; }
.btn-primary { background: var(--gradient-primary); color: #fff; box-shadow: var(--shadow-md); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); background: var(--gradient-accent); }
.btn-secondary { background: #fff; color: var(--color-primary); border: 2px solid var(--color-primary); }
.btn-secondary:hover { background: var(--color-primary); color: #fff; }

/* Cards */
.card {
  background: #fff;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
  border: 1px solid var(--color-gray-light);
}
.card:hover { box-shadow: var(--shadow-md); border-color: rgba(91, 155, 213, 0.35); transform: translateY(-2px); }

@media (max-width: 768px) {
  .container { padding: 0 16px; }
  .page-title { font-size: 40px; }
  .page-subtitle { font-size: 16px; }
  .page-header { padding: 100px 0 60px; }
  section { padding: 60px 0; }
}
```

---

## 3. Component Specifications

### 3.1 Header (Fixed + Scroll Frosted + Dropdown)

- **Fixed**: Always at top; initially transparent.
- **On scroll (>50px)**: Semi-transparent white + blur + `shadow-sm`.
- **Links**: Hover shows gradient underline; active uses primary color.
- **Mobile (≤768px)**: Hamburger opens full-width panel.

### 3.2 Footer (Dark + Links + Social)

- Background: `--color-dark`; text in white/gray layers; links brighten on hover.
- Social icons: Square/rounded buttons; default semi-transparent white, hover primary.

### 3.3 Carousel

- **Input**: `items[]`; show controls only when length > 1.
- **Autoplay**: 5s per slide.
- **Transition**: Slide + opacity + light scale (0.98→1).
- **Controls**: Circular prev/next; dots; active dot elongates (8px → 24px).

### 3.4 Content Card (Left Text + Right Media)

Unified layout: **left** (title/description/bullets) + **right** (video/image/link list).

---

## 4. Content Schema

### ContentCardItem

- **Required**: `title`, `description`
- **Optional**: `stats`, `details[]`, `tags[]`, `videos[]`, `linkList[]`, `image`, `videoLink`, `link`

### CarouselItem

- **Optional**: `title`, `description`, `date`, `location`, `images[]`, `link`

---

## 5. Acceptance Checklist

- [ ] All tokens (color/gradient/shadow/radius/transition) from this spec
- [ ] `page-header` with unified header image and gradient title
- [ ] Cards: large radius, soft shadow, hover lift + shadow
- [ ] Animations: first-screen fade-in + viewport fade-in
- [ ] Mobile: ≤768px padding 16px, smaller titles, reduced section padding
