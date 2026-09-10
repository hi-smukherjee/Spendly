# Spec: Edit Expense (Step 8)

## Overview

`app.py` currently has a placeholder route, `GET /expenses/<int:id>/edit`, that returns the plain
string `"Edit expense — coming in Step 8"`. This spec implements that route for real: a form to
edit an existing expense's `amount`, `category`, `date`, and `description`, scoped so a user can
only edit their own expenses.

This is a **build** step per the project's spec → design → tasks → build → validate workflow — it
follows Step 4 (Profile Page) and precedes Step 9 (Delete Expense). Step 7 (Add Expense) is a
sibling placeholder (`/expenses/add`) and is **not** implemented by this spec; no shared
"expense form" helper is assumed to exist yet, though a future Add Expense spec may choose to
reuse the template/markup introduced here.

- **Category input:** a fixed `<select>` limited to the 7 known seed categories (Food, Transport,
  Bills, Health, Entertainment, Shopping, Other) — the same set already wired to `--cat-*` CSS
  variables in `static/css/style.css`. This keeps every editable expense compatible with the
  existing color-coding; free-text categories are out of scope.
- **Entry point:** `templates/profile.html`'s expense table gains a per-row "Edit" link pointing
  at `/expenses/<id>/edit`, reversing the Step 4 redesign's "no add/edit/delete links" constraint
  for the Edit case only (Add and Delete links remain out of scope, per Steps 7 and 9).
- **Post-save behavior:** a successful `POST` redirects to `GET /profile` with no flash/success
  message, consistent with the codebase's current lack of a flash-messaging system.

## Depends on

- **Step 1 — Database Setup** (done): `get_db()`, `init_db()`, `expenses` table.
- **Step 4 — Profile Page** (done): `/profile` route, `get_expenses_by_user(user_id)`,
  `templates/profile.html`, `--cat-*` / `category-<slug>` color-coding conventions.
- Login's CSRF pattern (`session["csrf_token"]`, hidden `csrf_token` form field, regenerated on
  every `GET` of the form) is reused as-is for this form.

## Functional Requirements

- FR-1: `GET /expenses/<int:id>/edit` (login required) loads the expense matching `id`, verifies
  it belongs to `session["user_id"]`, and renders a pre-filled edit form. If no such expense
  exists for this user (wrong id, or another user's expense), respond `404` rather than revealing
  whether the id belongs to someone else.
- FR-2: The edit form has four fields, matching the `expenses` table columns:
  - **Amount** — numeric, required, > 0.
  - **Category** — `<select>` of the 7 fixed categories, required, pre-selected to the expense's
    current value.
  - **Date** — date, required, pre-filled with the expense's current value (`YYYY-MM-DD`).
  - **Description** — free text, optional (matches the nullable `description` column).
- FR-3: `POST /expenses/<int:id>/edit` (same URL, login required) validates the submitted fields
  and the CSRF token, then:
  - On validation success: updates the expense row in place (same `id`, same `user_id`, unchanged
    `created_at`) and redirects (`302`) to `GET /profile`.
  - On validation failure: re-renders the edit form with the submitted values retained, a new CSRF
    token, and an inline error message — no partial database write occurs.
- FR-4: Ownership scoping is enforced identically on both `GET` and `POST` — a user can never view
  or modify an expense whose `user_id` does not match `session["user_id"]`, regardless of what
  `id` is in the URL.
- FR-5: `templates/profile.html`'s expense table adds an actions column with an "Edit" link
  (`href="{{ url_for('edit_expense', id=expense['id']) }}"`) on every row. No Add or Delete UI is
  introduced.
- FR-6: All existing Jinja/`url_for` conventions and the unrelated placeholder routes
  (`/expenses/add`, `/expenses/<id>/delete`) are left untouched.

## Non-Functional Requirements

- NFR-1: No new dependencies — form handling, validation, and the date input use plain
  Flask/Jinja/HTML5, consistent with the project's no-build-step, stdlib-`sqlite3` approach.
- NFR-2: New `database/db.py` functions (`get_expense_by_id`, `update_expense`) follow the
  existing style: a fresh `get_db()` connection per call, explicit `conn.close()`, parameterized
  SQL only (no string-formatted queries).
- NFR-3: The edit page and the updated profile table remain responsive at the same breakpoints
  already defined in `style.css` (900px, 600px) — the new actions column must not force horizontal
  overflow at 375px width.
- NFR-4: The edit form reuses existing `.auth-card`/`.form-group`/`.form-input`/`.btn-submit`
  conventions (or a purpose-named equivalent following the same structural pattern) rather than
  inventing an unrelated styling system.

## User Stories

- US-1: As a logged-in user, I want to correct a mistake in an expense I already logged (wrong
  amount, category, date, or note), so my totals and category breakdown on the profile page stay
  accurate.
- US-2: As a logged-in user, I want to be blocked (with a 404, not a confusing form) from editing
  an expense that isn't mine, even if I guess or manipulate the URL's id.
- US-3: As a logged-in user, I want an "Edit" link right on my expense list, so I don't have to
  know or construct the `/expenses/<id>/edit` URL myself.

## Acceptance Criteria

- AC-1: Logging in as the seeded demo user and clicking "Edit" on any row navigates to
  `/expenses/<id>/edit` with the form pre-filled with that row's exact `amount`, `category`,
  `date`, and `description`.
- AC-2: Submitting the form with a changed `amount` and `category` redirects to `/profile`, and
  the updated values (and updated stat cards / category color) are immediately visible — no
  server restart or manual refresh workaround needed.
- AC-3: Submitting with `amount` set to `0`, a negative number, or non-numeric text re-renders the
  form with an inline error and the user's other submitted values retained; the database row is
  unchanged.
- AC-4: Submitting with `date` or `category` empty re-renders the form with an inline error; the
  database row is unchanged.
- AC-5: Submitting with `description` empty is accepted (description is optional) — the row's
  `description` becomes `NULL`/empty, matching how new rows already allow it.
- AC-6: Visiting `/expenses/<id>/edit` for an `id` that doesn't exist, or that belongs to a
  different user, returns `404` — not a redirect, not the other user's data.
- AC-7: Visiting `/expenses/<id>/edit` (GET or POST) while logged out redirects to `/login`
  (unchanged `@login_required` behavior).
- AC-8: Submitting the form without a valid CSRF token (or with a stale/mismatched one) is
  rejected with an inline error and no database write — same behavior class as the login form.
- AC-9: `expenses/add` and `expenses/<id>/delete` still return their original Step 7 / Step 9
  placeholder strings, unaffected by this change.

## API Requirements

- `GET /expenses/<int:id>/edit` — login required (`@login_required`). Returns the edit form for
  the caller's own expense, or `404` if it doesn't exist or belongs to another user.
- `POST /expenses/<int:id>/edit` — login required (`@login_required`), same URL/view function as
  the `GET` (mirrors the existing `/login` GET+POST pattern). Form-encoded body:
  `amount`, `category`, `date`, `description` (optional), `csrf_token`. On success: `302` to
  `/profile`. On validation failure: `200` with the form re-rendered and an `error` message. On
  ownership failure: `404`.

## Database Changes

No schema changes — no new tables or columns. Two new functions in `database/db.py`, following
the existing connection-per-call style:

- `get_expense_by_id(id, user_id)` — `SELECT * FROM expenses WHERE id = ? AND user_id = ?`,
  returns the row or `None`. The `user_id` filter is what makes ownership enforcement (FR-1, FR-4)
  a single query rather than a fetch-then-check-in-Python step that could be bypassed.
- `update_expense(id, user_id, amount, category, date, description)` — parameterized
  `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND
  user_id = ?`. The `user_id` clause is a defense-in-depth second check even though the view
  already verified ownership via `get_expense_by_id`.

## UI Requirements

- **Edit form page** (new template, e.g. `templates/edit_expense.html`): extends `base.html`,
  reuses the `auth-section`/`auth-container`/`auth-card` structural pattern (or a purpose-named
  `expense-form-*` equivalent following the same `*-section` > `*-container` > `*-card` nesting
  already used elsewhere), with:
  - Amount: `<input type="number" step="0.01" min="0.01">`.
  - Category: `<select>` with exactly the 7 fixed options, current value pre-selected via Jinja
    (`{{ "selected" if expense["category"] == "Food" }}` or equivalent loop).
  - Date: `<input type="date">`, value pre-filled from the expense's stored `YYYY-MM-DD` string.
  - Description: `<input type="text">` or `<textarea>`, optional, pre-filled.
  - Submit button (e.g. "Save changes") and a "Cancel" link back to `/profile`.
  - Inline error rendering via the same `.auth-error`-style block used by `login.html` when
    validation fails.
- **Profile table actions column** (`templates/profile.html` edit): one new `<th>Actions</th>` /
  `<td>` pair per row, containing the "Edit" link. Style with the existing `.btn-ghost` link
  treatment (already used for the "Analytics" link) rather than introducing a new button class.
- No new icon fonts, images, or JS — an "Edit" text label (optionally alongside the existing ◈
  glyph convention or a simple ✎ character) is sufficient.

## Error Handling

- Nonexistent or not-owned `id` → `404` (Flask's default `abort(404)`), for both `GET` and `POST`.
- Invalid `amount` (non-numeric, ≤ 0) → re-render form, `200`, inline error, no write.
- Missing `category` or `date`, or a `category` outside the fixed 7-value set (e.g. a tampered
  form submission) → re-render form, `200`, inline error, no write.
- Missing/invalid CSRF token → re-render form, `200`, inline error, no write — matches the login
  form's existing `"Invalid email or password."`-style generic rejection rather than leaking which
  check failed.
- Logged-out access → `302` redirect to `/login` (unchanged `@login_required`), before any
  ownership or validation logic runs.
- Any of the above must not raise an unhandled exception or expose a stack trace (Flask
  `debug=True` is dev-only per `app.py`, but production correctness is still the goal).

## Security

- **Ownership (IDOR prevention):** `get_expense_by_id(id, user_id)` filters by both `id` and
  `session["user_id"]` in the SQL itself, and `update_expense` repeats the `user_id` filter in its
  `WHERE` clause — a user can never view or overwrite another user's row by editing the URL's
  `id`, even if the ownership check in the view were accidentally skipped.
- **CSRF:** reuses the existing `session["csrf_token"]` pattern from `/login` — a fresh token is
  issued on every `GET` of the form and compared on `POST`; mismatches are rejected before any
  validation or database write.
- **SQL injection:** all new queries are parameterized (`?` placeholders), no f-string/`.format()`
  SQL construction — matches every existing query in `database/db.py`.
- **Input trust:** `category` is validated server-side against the fixed 7-value allowlist even
  though the form renders a `<select>` — a `<select>`'s options are a UI hint, not a server-side
  guarantee, since a POST body can be crafted directly.
- **XSS:** all displayed values (pre-filled form fields, error messages) go through Jinja's
  default autoescaping — no `|safe` filters are introduced.
- **Authorization ordering:** `@login_required` (session check) runs before the ownership check,
  which runs before validation — an anonymous request never reaches the database, and a
  wrong-owner request never reaches validation logic that might otherwise leak field-level detail.

## Test Cases

- TC-1: `GET /expenses/<id>/edit` for the demo user's own expense → `200`, form fields pre-filled
  with that expense's exact stored values.
- TC-2: `GET /expenses/<id>/edit` for an `id` belonging to a different user → `404`.
- TC-3: `GET /expenses/<id>/edit` for a nonexistent `id` → `404`.
- TC-4: `GET /expenses/<id>/edit` while logged out → `302` to `/login`.
- TC-5: `POST /expenses/<id>/edit` with valid data (new amount, category, date, description) and a
  correct CSRF token → `302` to `/profile`; re-fetching the expense shows the updated values;
  `user_id` and `created_at` unchanged.
- TC-6: `POST /expenses/<id>/edit` with `amount = "0"` → `200`, inline error, row unchanged in DB.
- TC-7: `POST /expenses/<id>/edit` with `amount = "-5"` → `200`, inline error, row unchanged.
- TC-8: `POST /expenses/<id>/edit` with `amount = "abc"` → `200`, inline error, row unchanged.
- TC-9: `POST /expenses/<id>/edit` with empty `date` → `200`, inline error, row unchanged.
- TC-10: `POST /expenses/<id>/edit` with `category = "NotARealCategory"` (bypassing the `<select>`
  via a raw request) → `200`, inline error, row unchanged.
- TC-11: `POST /expenses/<id>/edit` with empty `description` → `302` to `/profile`; row updated
  with `description` empty/`NULL`.
- TC-12: `POST /expenses/<id>/edit` for another user's `id` (crafted request, valid session for a
  *different* user) → `404`; the other user's row is unchanged in the database.
- TC-13: `POST /expenses/<id>/edit` with a missing or mismatched `csrf_token` → `200`, inline
  error, row unchanged.
- TC-14: `GET /profile` as the demo user → each expense row shows an "Edit" link whose `href`
  matches `/expenses/<that row's id>/edit`.
- TC-15: `GET /expenses/add` and `GET /expenses/<id>/delete` still return their original Step 7 /
  Step 9 placeholder strings (regression check — this spec must not touch those routes).

## Definition of Done

- [ ] `database/db.py` has `get_expense_by_id(id, user_id)` and
      `update_expense(id, user_id, amount, category, date, description)`, both parameterized and
      scoped by `user_id`.
- [ ] `GET /expenses/<int:id>/edit` renders a pre-filled form for the caller's own expense, `404`
      otherwise.
- [ ] `POST /expenses/<int:id>/edit` validates amount/category/date/CSRF, updates the row on
      success, redirects to `/profile`, and re-renders with an inline error (no write) on failure.
- [ ] `templates/edit_expense.html` created, extending `base.html`, following existing form/card
      conventions.
- [ ] `templates/profile.html` gains a per-row "Edit" link; no Add/Delete UI added.
- [ ] Category `<select>` is limited to the 7 fixed values, validated server-side too.
- [ ] Ownership is enforced on both `GET` and `POST`, at the SQL layer, not just in Python.
- [ ] CSRF token issued and checked, following the `/login` pattern.
- [ ] No new hardcoded hex colors; no new dependencies added to `requirements.txt`.
- [ ] `/expenses/add` and `/expenses/<id>/delete` placeholders remain unchanged.
- [ ] Responsive at 600px and 375px widths — actions column does not force table overflow.
