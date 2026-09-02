# Spec: Profile Page Redesign

## Overview

The `/profile` route (implemented in Step 4) currently renders `templates/profile.html`: a plain
table of the logged-in user's expenses, reusing the `.legal-section`/`.legal-card` classes built
for the Terms/Privacy pages. This spec redesigns that page into a bold, colorful expense
dashboard — summary stat cards above a restyled, color-coded expense list — while keeping the
page **strictly read-only**. No add/edit/delete UI or routes are introduced here; those remain
Steps 7–9 per the placeholder comments already in `app.py` (`add_expense`, `edit_expense`,
`delete_expense`).

This spec follows the `spendly-page-redesign` skill's workflow: full project context (`base.html`,
`static/css/style.css`, the current `profile.html`) was read directly from the repo before writing
this spec — no fallback to a self-contained/guessed design system was needed.

- **Scope:** Full structural redesign (not a cosmetic-only refresh) — new dashboard-style summary
  section is added above the existing expense list.
- **Style direction:** Bold / colorful — stronger visual hierarchy and distinct, saturated
  per-category colors, layered on top of (not replacing) Spendly's existing paper/ink/serif
  design system.

## Depends on

- **Step 4 — Profile Page** (done): `/profile` route, `get_expenses_by_user(user_id)`,
  `templates/profile.html`. This spec restyles/restructures that page; it does not change auth,
  routing, or data ownership behavior.

## Functional Requirements

- FR-1: `/profile` continues to render only the logged-in user's own expenses — no change to the
  data source (`get_expenses_by_user(session["user_id"])`).
- FR-2: The page displays a **summary row** above the expense list with three stat cards:
  - Total spent (sum of all displayed expenses' `amount`)
  - Number of expenses (count of rows)
  - Top category (the category with the highest total `amount`; if there are zero expenses, the
    summary row is omitted entirely — see FR-4)
- FR-3: The expense list is restyled with a distinct color per `category` value (a colored
  left-border accent and/or colored category chip), replacing the single-accent-color pill used
  today.
- FR-4: The empty state (no expenses) is redesigned as a friendlier illustrated/iconic message,
  and the summary stat cards are **not shown** when there are zero expenses (avoids showing
  "Total spent: ₹0.00" as if it were meaningful data).
- FR-5: All Jinja logic (`{% extends %}`, `{% block %}`, `{% if %}`, `{% for %}`,
  `{{ url_for(...) }}`) and the route/view name are preserved exactly — only markup, CSS classes,
  and the additional summary data passed into the template may change.
- FR-6: Currency formatting stays as-is: `₹` prefix, amount formatted to 2 decimal places.

## Non-Functional Requirements

- NFR-1: No new dependencies (no charting library, no icon font/CDN) — icons/visuals are done with
  existing tooling (CSS, inline SVG/Unicode glyphs, or emoji), consistent with the project's
  no-build-step static assets.
- NFR-2: Responsive down to 600px, matching the existing breakpoints already defined in
  `style.css` (`@media (max-width: 900px)`, `@media (max-width: 600px)`). Stat cards stack to a
  single column on narrow screens; the table remains usable (horizontal scroll acceptable) rather
  than overflowing the viewport.
- NFR-3: All new colors are defined as CSS variables in `:root` (extending the existing variable
  block) — never hardcoded hex values in rules, per project rules.
- NFR-4: No performance regression — summary stats are computed from the same single
  `get_expenses_by_user` result already fetched; no additional database queries are introduced.

## User Stories

- US-1: As a logged-in user, I want to see my total spending and expense count at a glance when I
  open my profile, so I don't have to manually add up the table rows.
- US-2: As a logged-in user, I want expenses to be visually distinguishable by category, so I can
  quickly spot spending patterns while scanning the list.
- US-3: As a new user with no expenses yet, I want a clear, friendly empty state (not a bare table
  header or raw stat cards showing zeros), so the page doesn't look broken.

## Acceptance Criteria

- AC-1: Logging in as the seeded demo user (`demo@spendly.com` / `demo123`) and visiting
  `/profile` shows all 8 seeded expenses, newest `date` first (unchanged from Step 4).
- AC-2: The summary row shows Total spent = ₹360.26, Number of expenses = 8, and Top category =
  Food (₹101.92 across the two seeded Food rows) — verifying the aggregation logic against the
  known seed data in `database/db.py`.
- AC-3: Each of the 7 seeded categories (Food, Transport, Bills, Health, Entertainment, Shopping,
  Other) renders with a visually distinct color, driven by CSS variables, not inline hex values.
- AC-4: A user with zero expenses sees only the redesigned empty state — no summary cards, no
  empty table shell, no error/traceback.
- AC-5: Visiting `/profile` while logged out still redirects to `/login` (unchanged
  `@login_required` behavior).
- AC-6: The page renders inside `base.html` (shared nav/footer visible).
- AC-7: No add/edit/delete links, buttons, or forms are present anywhere on the page.
- AC-8: At a 375px viewport width, the summary cards stack vertically and the table does not cause
  horizontal overflow of the page body.

## API Requirements

No new routes. `GET /profile` (existing, `@login_required`) is the only route involved; its view
function gains local computation (summary stats) but keeps the same URL, method, and decorator.

## Database Changes

None. No new tables, columns, or SQL queries. Summary statistics (total, count, top category) are
computed in Python from the rows already returned by the existing `get_expenses_by_user(user_id)`
— it already returns every column needed (`amount`, `category`).

## UI Requirements

- **Summary stat cards** (new): a row of 3 cards above the expense list, shown only when
  `expenses` is non-empty.
  - Reuse existing card conventions (`var(--paper-card)` background, `var(--border)`,
    `var(--radius-md)`) so the cards feel native to the app, not bolted on.
  - Each card gets a bold accent treatment (e.g., a colored top border or icon) per the "bold /
    colorful" direction — using new CSS variables, not the existing muted `--accent`/`--accent-2`
    alone.
- **Category color coding** (new): define one CSS variable per known seed category
  (`--cat-food`, `--cat-transport`, `--cat-bills`, `--cat-health`, `--cat-entertainment`,
  `--cat-shopping`, `--cat-other`) in `:root`, each a distinct saturated hue. Apply via a
  `category-<slug>` class (lowercased category name) on the category chip and/or as a left-border
  accent on the row. Categories outside the known seed set fall back to `--cat-other`'s color so
  the page never breaks on unexpected data.
- **Empty state** (redesign): replace the plain `<p class="profile-empty">No expenses yet.</p>`
  with a centered block — heading + short supporting line — still text/CSS only, no new image
  assets.
- **Layout container**: the page may move off `.legal-section`/`.legal-container`/`.legal-card`
  (which are named for the Terms/Privacy pages) onto new, purpose-named classes (e.g.
  `.profile-section`, `.profile-container`, `.profile-card`) so the profile page has its own
  identity — per the skill's "reuse and extend existing conventions" guidance, these new classes
  should follow the same structural pattern (`*-section` > `*-container` > `*-card`) already used
  elsewhere in `style.css`, not a parallel naming scheme.
- Typography stays on the existing system: `var(--font-display)` (DM Serif Display) for headings,
  `var(--font-body)` (DM Sans) for body/table text — no new font imports.

## Error Handling

No new error paths are introduced — this is a read-only page with no user input or form
submission. Existing behavior is preserved:

- Logged-out access to `/profile` → redirect to `/login` (via `login_required`).
- Zero-expense accounts → empty state, not an exception (`get_expenses_by_user` already returns
  `[]`, never `None`, for a user with no rows).
- Unexpected/unknown `category` values → fall back to the `--cat-other` color rather than
  rendering an unstyled chip or raising a template error.

## Security

- No change to authentication or authorization: ownership scoping still relies solely on
  `session["user_id"]` passed into `get_expenses_by_user`, never a request parameter — unchanged
  from Step 4.
- No new user-controlled input is rendered — `category`, `description`, `amount`, and `date`
  values are the same fields already displayed today, still passed through Jinja's default
  autoescaping (no `|safe` filters introduced).
- No new dependencies, so no new third-party attack surface (NFR-1).

## Test Cases

- TC-1: GET `/profile` as the seeded demo user → 200, table contains 8 rows in descending `date`
  order (unchanged assertion from Step 4).
- TC-2: GET `/profile` as the seeded demo user → summary cards show Total = ₹360.26, Count = 8,
  Top category = Food.
- TC-3: GET `/profile` as a user with 0 expenses → 200, empty-state markup present, summary-card
  markup absent, no 500 error.
- TC-4: GET `/profile` without a session → 302 redirect to `/login` (unchanged).
- TC-5: Render each of the 7 seed categories → each resolves to a distinct `--cat-*` CSS variable
  (no two categories share a color, none fall through to unstyled/default browser styling).
- TC-6: Render an expense with a category not in the known set (e.g. a manually inserted "Travel"
  row) → falls back to the `--cat-other` color without a template/rendering error.
- TC-7: Viewport at 375px width → no horizontal scroll on `<body>`; stat cards stacked
  single-column (visual/manual check, no automated layout test required per project's lack of a
  frontend test setup).

## Definition of Done

- [x] Summary stat cards (Total spent, Number of expenses, Top category) render above the list,
      only when expenses exist.
- [x] All 7 seeded categories have distinct, CSS-variable-driven colors.
- [x] Empty state is redesigned and shown with no summary cards when there are zero expenses.
- [x] Page still extends `base.html`; nav/footer unchanged and visible.
- [x] No add/edit/delete links, buttons, or forms anywhere on the page.
- [x] `get_expenses_by_user` call and its `session["user_id"]`-only scoping are unchanged.
- [x] No new hardcoded hex colors — all new colors are CSS variables in `:root`.
- [x] No new dependencies added to `requirements.txt`.
- [x] Responsive at 600px and 375px widths — verified manually against the existing breakpoints.
