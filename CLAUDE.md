# Portfolio Website

Static developer portfolio hosted on GitHub Pages.

## Stack

- Pure HTML/CSS/JS — no build step, no framework
- GitHub Pages deployment (push to main = deploy)
- No backend, no database

## Project Structure

```
index.html          ← Single-page site
style.css           ← Styles (separate file for maintainability)
assets/             ← Images, favicons
```

## Design System

See `DESIGN.md` for the full UX guide — Scandic developer aesthetic.

## Conventions

- No build tools, no npm, no bundlers
- Mobile-first responsive design
- Semantic HTML5 (`<header>`, `<main>`, `<section>`, `<article>`, `<footer>`)
- CSS custom properties for all design tokens (colors, spacing, typography)
- No JavaScript unless strictly necessary (prefer CSS animations)
- Accessibility: WCAG AA minimum, keyboard navigable, screen reader friendly

## Testing

- Open `index.html` in browser: `open index.html`
- Mobile preview: browser DevTools responsive mode
- Lighthouse audit for performance/accessibility

## Deployment

Push to main → GitHub Pages auto-deploys.
URL: `https://tomashermansen-lang.github.io/portfolio`

## Related Projects

- [dotfiles](https://github.com/tomashermansen-lang/dotfiles) — CLI pipeline (source of truth for dev workflow)
- [dashboard](https://github.com/tomashermansen-lang/claude-agent-dashboard) — Autopilot monitoring
