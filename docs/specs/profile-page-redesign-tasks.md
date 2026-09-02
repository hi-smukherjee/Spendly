# Tasks: Profile Page Redesign

Ordered implementation checklist for `docs/specs/profile-page-redesign.md` /
`docs/specs/profile-page-redesign-design.md`. This is the **tasks** step of
spec → design → tasks → **build** → validate — build should follow this order so each task is
independently testable before the next depends on it.

## 1. Backend aggregation (`app.py`)

- [x] 1.1 In `profile()`, after `expenses = get_expenses_by_user(session["user_id"])`, compute
      `total_spent` (sum of `amount`) and `top_category` (category with the highest summed
      `amount`; `None` when `expenses` is empty) per design §5.
- [x] 1.2 Pass `total_spent` and `top_category` into `render_template("profile.html", ...)`
      alongside the existing `expenses`.
- [x] 1.3 Manually verify against seed data (`database/db.py`): `total_spent == 360.26`,
      `top_category == "Food"` for the demo user — matches spec AC-2.

## 2. CSS variables (`static/css/style.css`)

- [x] 2.1 Add the 7 `--cat-*` variables and 2 `--stat-accent-*` variables to the existing `:root`
      block (design §1) — append only, no edits to existing variables.

## 3. Container/class renames (`static/css/style.css` + `templates/profile.html`)

- [x] 3.1 Add new rules `.profile-section`, `.profile-container`, `.profile-title` (copy current
      `.legal-section`/`.legal-container`/`.legal-title` property values as the starting point,
      per design §2), with `.profile-container` at `var(--max-width)` instead of 720px.
- [x] 3.2 Update `templates/profile.html` to use `.profile-section`/`.profile-container`/
      `.profile-title` in place of the `.legal-*` classes it currently borrows.
- [x] 3.3 Do **not** delete `.legal-*` rules from `style.css` — `terms.html`/`privacy.html` still
      depend on them.

## 4. Stat row markup + styles

- [x] 4.1 Add `.stat-row`, `.stat-card`, `.stat-value`, `.stat-label` rules per design §3
      (grid layout, card chrome matching `.profile-card`/`.paper-card` conventions, 4px top-accent
      border).
- [x] 4.2 Add the `.stat-row` markup to `profile.html` inside `{% if expenses %}`, rendering three
      `.stat-card`s: Total spent (`--stat-accent-1`), Expense count (`--stat-accent-2`), Top
      category (inline `style` pointing at `var(--cat-<slug>)` for the actual top category).
- [x] 4.3 Confirm the stat row is entirely absent (not just empty) when `expenses` is falsy —
      satisfies spec FR-4.

## 5. Category color coding (table)

- [x] 5.1 Add per-category chip rules (`.category-food .expense-category`, etc.) and the
      `--cat-other` fallback rule, per design §3.
- [x] 5.2 Add the `category-{{ expense.category|lower }}` class to each `<tr>` in `profile.html`,
      plus the `border-left: 3px solid var(--cat-*)` row-accent rule.
- [x] 5.3 Verify an out-of-set category (e.g. temporarily insert a test row with category
      `"Travel"`) falls back to `--cat-other` styling without a template error — spec TC-6.

## 6. Empty state redesign

- [x] 6.1 Replace the current `<p class="profile-empty">` markup with the icon/heading/subtext
      structure from design §3 (`.profile-empty-icon`, heading, supporting copy).
- [x] 6.2 Style `.profile-empty` as a centered block; no new image assets (NFR-1).

## 7. Responsive rules

- [x] 7.1 Add `.stat-row { grid-template-columns: 1fr; }` under the existing
      `@media (max-width: 900px)` block.
- [x] 7.2 Add `.profile-card`/`.profile-section` mobile padding under the existing
      `@media (max-width: 600px)` block (mirroring the `.legal-card`/`.legal-section` rules there).
- [x] 7.3 Wrap `<table class="expense-table">` in a `<div class="table-scroll">` and add
      `.table-scroll { overflow-x: auto; }`.

## 8. Validate against spec

- [x] 8.1 AC-1: demo user sees all 8 seeded expenses, newest-first — unchanged.
- [x] 8.2 AC-2: stat row shows the exact seed-data numbers from task 1.3.
- [x] 8.3 AC-3: all 7 seeded categories render with visually distinct colors.
- [x] 8.4 AC-4: zero-expense account shows only the empty state — no stat row, no table shell.
- [x] 8.5 AC-5: logged-out `/profile` still redirects to `/login`.
- [x] 8.6 AC-6: nav/footer from `base.html` still visible.
- [x] 8.7 AC-7: no add/edit/delete links, buttons, or forms anywhere on the page.
- [x] 8.8 AC-8: at 375px width, stat cards stack and the table scrolls inside `.table-scroll`
      rather than overflowing `<body>`.
- [x] 8.9 Confirm no new hardcoded hex colors were added outside the `:root` block (grep
      `style.css` for stray `#`/`rgb(` in the new rules).
- [x] 8.10 Confirm `requirements.txt` is untouched (NFR-1 — no new dependencies).

## Next step

**Build** — implement tasks 1–7 in order, then run through the validation checklist in §8.
