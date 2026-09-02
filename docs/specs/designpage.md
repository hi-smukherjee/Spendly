# Design Page (Style Guide) — Software Requirements Specification

## Overview

Spendly's CSS (`static/css/style.css`) has accumulated a set of reusable pieces — color tokens,
type scale, buttons, form inputs, cards — across the templates built so far (`landing.html`,
`login.html`, `register.html`, `terms.html`, `privacy.html`). There is no single place to see them
together. This feature adds a new page, `/design`, that renders a living catalog of every styled
element `style.css` currently defines, so that later steps (Step 4 profile, Step 7 add-expense,
Step 8 edit-expense, Step 9 delete-expense) can be built by reusing existing classes instead of
re-deriving them from scratch or drifting into inconsistent one-off styles.

This is a documentation/reference page, not a user-facing product feature — it displays static
markup only and introduces no new business logic, database access, or forms that submit data.

## Functional Requirements

- **FR-1**: A new route `GET /design` renders a page cataloging every visual component currently
  defined in `static/css/style.css`.
- **FR-2**: The page is organized into labeled sections, each showing a live rendering of the
  component plus its class name(s), in this order:
  1. Color palette — every `--*` custom property in `:root` swatched with its name and hex value.
  2. Typography — `--font-display` and `--font-body` at the sizes actually used across templates
     (hero title, section titles, body text, small/muted text).
  3. Buttons — `.btn-primary`, `.btn-ghost`, `.btn-submit`, each in its default and (where CSS
     defines one) `:hover` state.
  4. Form elements — `.form-group` / `.form-input` (text, email, password, and any other `type`
     already used in `login.html`/`register.html`), including the `::placeholder` state and the
     `.auth-error` message style.
  5. Cards — `.feature-card`, `.auth-card`, `.legal-card`, shown with representative sample
     content.
  6. Navigation & footer — the `.navbar` and `.footer` blocks, rendered as self-contained samples
     (not the page's own live nav/footer).
  7. Video modal trigger — the `#getStartedBtn` affordance and a note on how `static/js/main.js`
     wires it up (the modal itself is not opened on this page).
- **FR-3**: Every component sample is real markup using the actual CSS classes — not screenshots,
  not descriptions — so the page stays accurate as `style.css` changes.
- **FR-4**: The page is reachable by any visitor, authenticated or not (no `login_required`).
- **FR-5**: The page is not linked from `base.html`'s navbar or footer; it is reached only by
  navigating directly to `/design`.

## Non-Functional Requirements

- **NFR-1**: No new CSS framework or build step is introduced; the page reuses `style.css`
  classes as-is. Any CSS needed purely for the catalog's own layout (section spacing, swatch
  grid) is added as new, clearly-scoped rules (e.g. prefixed `.styleguide-`) so it's obviously
  separable from the reusable component styles it's documenting.
- **NFR-2**: The route performs no database access and requires no new tables or functions in
  `database/db.py`.
- **NFR-3**: The page extends `base.html` like every other template, so it inherits the real
  navbar/footer/fonts and doubles as a visual regression check for the shared layout.
- **NFR-4**: Adding a new component class to `style.css` should require only adding a markup
  sample to the design template, not touching `app.py`.

## User Stories

- As the developer (Soma) building later steps, I want to see every existing button, form field,
  and card style in one place so I can reuse the right class instead of writing new CSS.
- As a contributor picking up Step 4/7/8/9, I want a reference page so the profile and
  expense-form UI stays visually consistent with the landing/auth/legal pages already built.
- As the developer, I want the color palette and type scale listed with their token names so I
  don't hardcode raw hex values or font stacks in new templates.

## Acceptance Criteria

- **AC-1**: Given no session, visiting `/design` returns a 200 response (no redirect to `/login`).
- **AC-2**: The rendered page contains one visible swatch per `--*` custom property currently in
  `:root` (12 as of this spec: `--ink`, `--ink-soft`, `--ink-muted`, `--ink-faint`, `--paper`,
  `--paper-warm`, `--paper-card`, `--accent`, `--accent-light`, `--accent-2`, `--accent-2-light`,
  `--danger`, `--danger-light`, `--border`, `--border-soft`), each labeled with its variable name
  and hex value.
- **AC-3**: The rendered page contains a live, styled instance of `.btn-primary`, `.btn-ghost`,
  and `.btn-submit`.
- **AC-4**: The rendered page contains a live `.form-group`/`.form-input` example and a live
  `.auth-error` example.
- **AC-5**: The rendered page contains a live `.feature-card`, `.auth-card`, and `.legal-card`
  example.
- **AC-6**: `/design` does not appear as a link anywhere in `base.html`.
- **AC-7**: Editing a color value in `style.css`'s `:root` and reloading `/design` shows the
  updated color in the corresponding swatch (proves the page reads live CSS, not a hardcoded
  duplicate of values).

## API Requirements

Server-rendered only, no JSON API — consistent with every other route in the app.

| Route | Method | Auth | Description |
|---|---|---|---|
| `/design` | GET | none | Render the style guide / component catalog |

## Database Changes

None. This feature touches no tables and adds no functions to `database/db.py`.

## UI Requirements

- New template `templates/design.html`, extending `base.html`, overriding `{% block title %}`
  ("Design — Spendly") and `{% block content %}`.
- Page opens with a short heading ("Design System" or similar) and one `<section>` per catalog
  group from FR-2, each with a heading and the live samples.
- Color swatches: a grid of small blocks, each showing the swatch itself, the `--variable-name`,
  and its hex value as text (so the value is copy-pasteable).
- Every other section shows the component rendered exactly as it appears in production templates
  (e.g. the button samples use the same markup as `login.html`'s submit button), with the class
  name printed alongside (e.g. in a `<code>` tag) so it's unambiguous which class produced which
  sample.
- New styleguide-only layout CSS is added to `static/css/style.css` in its own clearly-commented
  section (e.g. `/* Style guide page */`) rather than mixed into existing component rules.

## Error Handling

- No form submissions or user input on this page, so there is no validation path.
- If a future component is added to `style.css` without a corresponding sample being added to
  `design.html`, that is a documentation gap, not a runtime error — the page simply omits it
  silently. (No automated drift-detection is in scope for this spec.)
- Standard Flask error handling applies for the route itself (e.g. a 500 if the template fails to
  render); no custom error handling is needed beyond what already exists.

## Security

- **No auth required is intentional, not an oversight**: this page contains no user data, no
  forms that write anywhere, and no session-derived content — it is safe to expose without
  `login_required`.
- **No user input is accepted**: the route takes no query parameters, form data, or URL segments,
  so there is no injection or parameter-tampering surface.
- **Not linked in navigation** (FR-5): keeps it out of the primary user journey; anyone who
  reaches it does so by knowing the URL, consistent with treating it as a developer reference
  rather than a product page. (This is obscurity, not a security boundary — the page must remain
  genuinely safe to expose even if the URL becomes known publicly.)

## Test Cases

| ID | Scenario | Expected Result |
|---|---|---|
| TC-1 | GET `/design` while logged out | 200 response, page renders |
| TC-2 | GET `/design` while logged in | 200 response, page renders (nav shows logged-in state via shared `base.html`) |
| TC-3 | Inspect rendered HTML for each `:root` variable | One swatch per variable, correct name + hex value shown |
| TC-4 | Inspect rendered HTML for buttons section | `.btn-primary`, `.btn-ghost`, `.btn-submit` each present and visually styled |
| TC-5 | Inspect rendered HTML for forms section | `.form-input` and `.auth-error` present and visually styled |
| TC-6 | Inspect rendered HTML for cards section | `.feature-card`, `.auth-card`, `.legal-card` each present |
| TC-7 | Search `templates/base.html` for `/design` or `url_for('design')` | No match — page is not linked in nav or footer |
| TC-8 | Change `--accent` in `style.css`, reload `/design` | Swatch and any accent-colored sample (e.g. `.btn-primary`) reflect the new color |
| TC-9 | GET `/design` with an active session vs. none | Identical component catalog rendered either way (no session-conditional content in the catalog itself) |
