# Figma ↔ Spendly Design System Rules

Reference doc for translating Figma designs into this codebase (and vice versa). Spendly is a
**server-rendered Flask app with no component framework, no CSS-in-JS, and no build step** — every
rule below reflects that; don't propose React/Vue components, CSS Modules, or a bundler pipeline,
they don't apply here.

## 1. Token Definitions

All design tokens live as **CSS custom properties** in a single `:root` block at the top of
`static/css/style.css:5-42`. There is no token-transformation system (no Style Dictionary, no
Tailwind config, no JS token file) — the CSS variables *are* the source of truth, referenced
directly by every stylesheet rule and occasionally inlined in templates via `style="--stat-top-color: ...`
(see `templates/profile.html:17`).

```css
:root {
    /* Ink / text scale */
    --ink: #0f0f0f;
    --ink-soft: #2d2d2d;
    --ink-muted: #6b6b6b;
    --ink-faint: #a0a0a0;

    /* Surface scale */
    --paper: #f7f6f3;
    --paper-warm: #f0ede6;
    --paper-card: #ffffff;

    /* Brand */
    --accent: #1a472a;        /* deep green */
    --accent-light: #e8f0eb;
    --accent-2: #c17f24;      /* ochre */
    --accent-2-light: #fdf3e3;

    /* Semantic */
    --danger: #c0392b;
    --danger-light: #fdecea;

    /* Borders */
    --border: #e4e1da;
    --border-soft: #eeebe4;

    /* Type */
    --font-display: 'DM Serif Display', Georgia, serif;
    --font-body: 'DM Sans', system-ui, sans-serif;

    /* Layout */
    --max-width: 1200px;
    --auth-width: 440px;

    /* Radius scale */
    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-lg: 20px;

    /* Expense category colors (data-viz, not brand) */
    --cat-food: #e8542e;
    --cat-transport: #2f6fed;
    --cat-bills: #8b5cf6;
    --cat-health: #10b981;
    --cat-entertainment: #ec4899;
    --cat-shopping: #f59e0b;
    --cat-other: #64748b;

    /* Derived/semantic aliases */
    --stat-accent-1: var(--accent-2);
    --stat-accent-2: var(--accent);
}
```

**When mapping Figma variables → code:** map Figma color/number variables 1:1 onto these custom
properties by name (strip the `--`). If a Figma design introduces a new color that isn't one of
these, don't invent a new ad-hoc hex — check whether it should be a new named token in this block
first (e.g. a new `--cat-*` for a new expense category, or a genuinely new semantic color).

There are only two font families (`--font-display` for headings/serif moments, `--font-body` for
everything else) and three border-radius steps — treat these as closed sets, not a starting point
for arbitrary values.

## 2. Component Library

**There is no component library, no Storybook, and no JS component framework.** "Components" are
CSS class conventions applied to plain HTML in Jinja2 templates. The closest thing to a component
inventory is the class list in `static/css/style.css`, organized in commented sections:

- Navbar (`.navbar`, `.nav-inner`, `.nav-brand`, `.nav-links`, `.nav-cta`)
- Buttons (`.btn-primary`, `.btn-ghost`, `.btn-submit`)
- Cards (`.feature-card`, `.auth-card`, `.legal-card`, `.profile-card`, `.stat-card`)
- Forms (`.form-group`, `.form-input`, `.auth-error`)
- Footer (`.footer`, `.footer-inner`, `.footer-links`)
- Page-specific sections (`.hero-*`, `.auth-*`, `.legal-*`, `.profile-*`, `.coming-soon-*`)
- Video modal (`.video-modal*`)

When a Figma frame maps to a recurring UI pattern (a card, a button, a stat tile), reuse the
existing class rather than authoring new component-scoped CSS — e.g. any new "small pill of color
text" should extend `.expense-category`, not become a new one-off class.

## 3. Frameworks & Libraries

- **Backend/rendering**: Flask 3.1 (`app.py`, single file, no blueprints) rendering Jinja2
  templates server-side. There is no client-side framework — no React, Vue, Svelte, Alpine, or
  htmx.
- **Styling**: plain hand-written CSS in one file, no preprocessor (no Sass/Less/PostCSS), no
  utility framework (no Tailwind, Bootstrap).
- **JS**: plain vanilla JS in `static/js/main.js`, IIFE style, no imports/exports, no npm
  dependencies at all for the frontend.
- **Build system**: none. No `package.json`, no bundler, no transpiler. Files are served as-is via
  Flask's static handler (`url_for('static', filename=...)`). Any Figma-to-code output must be
  hand-authored HTML/CSS/JS that runs unmodified in the browser — no JSX, no build-time imports.

## 4. Asset Management

- Assets live under `static/images/` (currently just `hero-illustration.svg`) and are referenced
  with `url_for('static', filename='images/...')` in templates, matching CSS/JS references.
- No image optimization pipeline, no responsive `srcset` generation, no CDN — everything is served
  directly by Flask from disk. Keep new assets as hand-optimized SVG where possible (the existing
  hero image is inline-optimizable SVG, not a raster export).
- Google Fonts are loaded via `<link>` tags in `templates/base.html:7-9` (preconnect + stylesheet),
  not self-hosted.

## 5. Icon System

There is no icon library (no Font Awesome, no Lucide/Heroicons, no SVG sprite sheet). Icons seen in
the UI today are either:
- A single **Unicode glyph** used as the brand mark: `◈` (see `.brand-icon` in
  `templates/base.html:18` and `templates/profile.html:58`), styled purely with CSS `color`/
  `font-size`.
- Plain **text/emoji-less glyphs** inline in markup (e.g. `&times;` for the modal close button in
  `templates/base.html:53`).

When a Figma design specifies an icon, prefer either reusing `◈` where a "Spendly mark" is called
for, or inlining a minimal hand-written `<svg>` directly in the template (matching the
`hero-illustration.svg` pattern) — don't introduce an icon-font or npm icon package dependency.

## 6. Styling Approach

- **Methodology**: plain global CSS with descriptive, page/section-prefixed class names (e.g.
  `.profile-header`, `.auth-card`, `.legal-title`) — not BEM, not CSS Modules, not scoped styles.
  One global stylesheet (`static/css/style.css`), organized top-to-bottom by page/section with
  `/* ---- */` banner comments; keep new rules in the matching section rather than appending at the
  end.
- **Global styles**: a `*, *::before, *::after` box-sizing reset and base `html`/`body`/`a` rules
  sit right after the `:root` token block (`static/css/style.css:44-65`).
- **State via modifier classes**, not inline style attributes — except for genuinely
  per-instance/dynamic values, which are set as CSS custom-property overrides inline (e.g.
  `style="--stat-top-color: var(--stat-accent-1);"` in `templates/profile.html:17`, or
  category-color mixing via `color-mix(in srgb, var(--cat-food) 15%, white)` at
  `static/css/style.css:647-652`). Follow this pattern for any new per-row/per-item dynamic
  coloring rather than generating classes server-side.
- **Responsive design**: two breakpoints only, `max-width: 900px` and `max-width: 600px`, defined
  in one consolidated block at the bottom of the stylesheet (`static/css/style.css:797-832`) rather
  than interleaved per-component. Add new responsive overrides there, grouped by the same
  breakpoint.

## 7. Project Structure

```
app.py                     # single-file Flask app — all routes here, no blueprints
database/
  db.py                    # get_db() / init_db() / seed_db() — raw sqlite3, no ORM
templates/
  base.html                # layout: nav, footer, video modal; {% block title/content/scripts %}
  landing.html, login.html, register.html, terms.html, privacy.html, profile.html, coming_soon.html
static/
  css/style.css            # single global stylesheet, tokens + all component/page styles
  js/main.js               # single global script, vanilla JS, IIFE-wrapped features
  images/                  # SVG/static assets
```

There is no feature-folder or domain-based organization — pages are flat under `templates/`, and
all backend logic (however much exists per step) lives directly in `app.py`. This project is built
incrementally as a step-by-step learning exercise (see root `CLAUDE.md`): some routes are
deliberate placeholders (`/logout`, `/expenses/add`, etc., returning plain strings) rather than
missing functionality. When implementing a Figma design for one of these routes, build the real
template/route, but don't assume adjacent placeholder routes are bugs to "fix" — check
`CLAUDE.md` and the current step's spec under `docs/specs/` first.

## Practical checklist for Figma → Spendly code

1. Map every Figma color/type/spacing variable to an existing `:root` token in
   `static/css/style.css` by name before introducing a new one.
2. Reuse an existing class pattern (`.stat-card`, `.btn-primary`, `.form-input`, …) for any
   recurring shape instead of writing new one-off CSS.
3. Author plain HTML in a Jinja2 template extending `base.html`, with `{% block title %}` and
   `{% block content %}` — no JSX/component files.
4. Add new CSS to the matching commented section of `static/css/style.css`; add new responsive
   overrides to the existing breakpoint block at the bottom.
5. New icons: inline SVG or the `◈` glyph — no icon package.
6. New images: drop an optimized SVG/asset into `static/images/`, reference via `url_for`.
7. Any interactivity: vanilla JS appended to `static/js/main.js` following the existing
   IIFE + `getElementById` pattern — no framework, no build step.
