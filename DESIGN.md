# Design System: Scandic Developer

A blend of Anthropic's Claude pages (clean, generous whitespace, warm
intelligence) and the menu card at a natural wine bar in Copenhagen
(organic textures, earthy muted palette, handcrafted feel, understated
elegance).

Quiet confidence. No flashy gradients. No tech-bro aesthetic.

## Principles

1. **Restraint over decoration** — every element earns its place
2. **Typography is the design** — type hierarchy does the heavy lifting
3. **Warmth over sterility** — off-whites, not pure white; charcoal, not black
4. **Texture over flatness** — subtle grain, paper-like quality
5. **Space is content** — generous margins signal confidence

## Color Palette

```css
:root {
  /* Backgrounds */
  --bg-primary: #FAF8F5;        /* Warm cream — like unbleached paper */
  --bg-secondary: #F2EDE8;      /* Slightly darker — card backgrounds */
  --bg-accent: #EBE4DB;         /* Subtle dividers, hover states */

  /* Text */
  --text-primary: #2C2825;      /* Dark charcoal — warm, not pure black */
  --text-secondary: #6B6560;    /* Muted — secondary info, metadata */
  --text-tertiary: #9C9590;     /* Subtle — timestamps, labels */

  /* Accents */
  --accent-terracotta: #C4755B; /* Primary accent — links, highlights */
  --accent-clay: #A8634E;       /* Darker terracotta — hover states */
  --accent-sage: #7A8B6F;       /* Secondary accent — tags, badges */
  --accent-stone: #8C8478;      /* Neutral accent — borders */

  /* Functional */
  --border: #E0D8CF;            /* Subtle borders */
  --shadow: rgba(44, 40, 37, 0.06); /* Barely-there shadows */
}
```

### Dark Mode (optional, later)

If implemented, invert warmth — dark backgrounds should feel like a
candlelit wine bar, not a code editor. Rich dark browns, not grays.

## Typography

Two typefaces, maximum:

1. **Headings:** A refined serif with editorial character
   - **Primary choice:** `'Playfair Display', Georgia, serif`
   - **Alternative:** `'DM Serif Display', Georgia, serif`
   - Weight: 400–700
   - Letter-spacing: -0.02em (tight, editorial)

2. **Body & UI:** Clean, modern sans-serif
   - **Primary choice:** `'Inter', -apple-system, sans-serif`
   - **Alternative:** `'DM Sans', -apple-system, sans-serif`
   - Weight: 300–600
   - Letter-spacing: 0 (default)

3. **Code/technical:** Monospace for tech stack tags, metadata
   - `'JetBrains Mono', 'SF Mono', monospace`
   - Weight: 400
   - Font-size: 0.85em relative to body

### Type Scale

```css
--text-xs: 0.75rem;    /* 12px — metadata, labels */
--text-sm: 0.875rem;   /* 14px — secondary text, tags */
--text-base: 1.0625rem;/* 17px — body text (slightly larger than default) */
--text-lg: 1.25rem;    /* 20px — lead paragraphs */
--text-xl: 1.5rem;     /* 24px — section headers */
--text-2xl: 2rem;      /* 32px — page titles */
--text-3xl: 2.75rem;   /* 44px — hero heading */
--text-4xl: 3.5rem;    /* 56px — hero heading (desktop) */
```

### Line Heights

- Headings: 1.1–1.2 (tight)
- Body: 1.6–1.7 (generous, readable)
- UI elements: 1.4

## Spacing

8px base grid:

```css
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;       /* 16px */
--space-lg: 1.5rem;     /* 24px */
--space-xl: 2.5rem;     /* 40px */
--space-2xl: 4rem;      /* 64px */
--space-3xl: 6rem;      /* 96px */
--space-4xl: 8rem;      /* 128px */
```

Section padding: `var(--space-3xl) 0` (96px vertical).
Max content width: `720px` (body text), `1080px` (card grid).

## Layout

### Hero

- Full viewport height minus a subtle hint to scroll
- Name in serif, large (3xl–4xl)
- One-line positioning underneath in sans-serif, secondary color
- No image, no illustration — typography only
- Subtle scroll indicator (thin line or arrow, animated)

### Sections

- Clear vertical rhythm with generous section spacing
- Section titles: serif, left-aligned, with a thin rule beneath
- Content follows immediately — no unnecessary subheadings

### Project Cards

- 2-column grid on desktop, single column on mobile
- Card has: subtle border (not shadow), slight background shift on hover
- Content: title (serif), one-line description (sans), tech stack tags (mono, small)
- Hover: gentle background warm-up, border darkens slightly
- Link: entire card is clickable, arrow indicator on hover

```
┌─────────────────────────────────────────┐
│                                         │
│  Project Title                    →     │
│  One-line description of what it does   │
│                                         │
│  python  typescript  react  fastapi     │
│                                         │
└─────────────────────────────────────────┘
```

### Tech Stack Tags

- Pill-shaped, small, monospace font
- Background: `--bg-accent`
- Text: `--text-secondary`
- No icons — text only, lowercase

## Interactions

- **Links:** Terracotta color, no underline by default. Underline on hover
  with a subtle transition (0.2s ease).
- **Cards:** `transition: background-color 0.2s ease, border-color 0.2s ease`
  — no transform/scale effects (too flashy).
- **Scroll:** Smooth scroll for anchor links (`scroll-behavior: smooth`).
- **No animations on load.** Content is simply there. The only motion is
  the scroll indicator and hover transitions.

## Texture

- Subtle CSS noise/grain overlay on `--bg-primary` (optional, via SVG filter
  or pseudo-element with noise PNG at very low opacity: 0.02–0.04).
- This gives the "unbleached paper" feel without loading heavy assets.

```css
body::before {
  content: '';
  position: fixed;
  inset: 0;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,..."); /* tiny noise pattern */
  pointer-events: none;
  z-index: 9999;
}
```

## Content Sections

1. **Hero** — Name + positioning
2. **About** — 2-3 paragraphs, what I do, my approach
3. **Projects** — Card grid (easy to add new cards)
4. **Writing** — Placeholder for LinkedIn posts / blog (can start empty)
5. **Contact** — LinkedIn, GitHub, email — minimal, just links

## Responsive Breakpoints

```css
/* Mobile-first */
@media (min-width: 640px)  { /* sm — tablets */ }
@media (min-width: 1024px) { /* lg — desktop */ }
@media (min-width: 1280px) { /* xl — wide desktop */ }
```

- Hero text scales down smoothly (clamp or media queries)
- Cards go from 1-col to 2-col at `lg`
- Max-width containers prevent ultra-wide line lengths

## Accessibility

- Color contrast: AA minimum (4.5:1 for body text, 3:1 for large text)
- `--accent-terracotta` on `--bg-primary`: ratio ~4.7:1 (passes AA)
- All interactive elements keyboard-focusable with visible focus ring
- Semantic HTML landmarks (`<nav>`, `<main>`, `<section>`, `<footer>`)
- `prefers-reduced-motion`: disable scroll indicator animation
- `prefers-color-scheme`: respect system dark mode (if implemented)

## Fonts Loading

Use Google Fonts with `display=swap` to prevent FOIT:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
```

## Reference Aesthetic

Think of these touchpoints:
- **Anthropic.com** — the warmth, the whitespace, the confident simplicity
- **A natural wine list** — organic typography, no logos, just curated names and descriptions
- **A Copenhagen design studio** — restrained Scandi minimalism, nothing unnecessary
- **A well-typeset book** — generous margins, careful leading, content that breathes
