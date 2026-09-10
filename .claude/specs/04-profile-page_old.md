# Spec: Profile Page

## Overview

The `/profile` route currently returns the placeholder string `"Profile page — coming in Step 4"`
(`app.py`). This step replaces it with a real page that shows the logged-in user's expenses: a
read-only list, ordered most-recent-first, scoped strictly to that user. It is the first screen
where `expenses` table data actually reaches the UI. Adding, editing, and deleting expenses stay
out of scope here — those are Steps 7, 8, and 9 per the placeholder comments already in `app.py`
(`add_expense`, `edit_expense`, `delete_expense`). Note: `docs/specs/expenses.md` already
specifies the full CRUD lifecycle (including this same profile listing as its FR-1/AC-1) — this
spec narrows that down to only the Step 4 slice so the branch stays small and reviewable; the
add/edit/delete portions of that broader doc still apply to their respective later steps and
should not be re-implemented here.

## Depends on

- **Step 1 — Database Setup**: `expenses` table, `get_db()`/`init_db()`/`seed_db()` — done
  (`database/db.py` is implemented, not the empty scaffold its header comment still describes).
- **Step 2 — Login Authentication**: session-based auth and the `login_required` decorator — done
  (`app.py`), and already applied to the `/profile` route.

## Routes

- `GET /profile` — render the current user's expenses, newest `date` first — logged-in only
  (already decorated with `@login_required`; no change to the decorator needed).

No new routes are added.

## Database changes

No new tables, columns, or constraints — `expenses` already has everything needed
(`user_id`, `amount`, `category`, `date`, `description`), confirmed against `database/db.py`.

One new function is needed in `database/db.py`, following the existing `get_user_by_email`
convention (parameterized query, connection opened/closed within the function):

- `get_expenses_by_user(user_id)` — `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC`,
  returns all matching rows (empty list if none).

## Templates

- **Create:** `templates/profile.html` — extends `base.html`; overrides `{% block title %}`
  ("Profile — Spendly") and `{% block content %}`. Renders a table/list of expenses (date,
  category, description, amount) and an empty-state message ("No expenses yet") when the list is
  empty. No add/edit/delete controls yet — this page is read-only until Steps 7–9 land.
- **Modify:** none. `base.html` nav/footer already work for a logged-in session
  (`session.user_name`, logout link).

## Files to change

- `app.py` — implement the `profile()` view: call `get_expenses_by_user(session["user_id"])` and
  `render_template("profile.html", expenses=...)` in place of the placeholder string.
- `database/db.py` — add `get_expenses_by_user(user_id)`.

## Files to create

- `templates/profile.html`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug. *(No password handling in this step — carried over as a
  standing project rule.)*
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- `get_expenses_by_user` filters by `user_id = ?` using the session's `user_id` only — never a
  value taken from the request — consistent with the ownership-enforcement pattern in
  `docs/specs/expenses.md`.
- No add/edit/delete UI or routes in this step — keep the page strictly read-only so it doesn't
  encroach on Steps 7–9's scope.
- Amounts display formatted to 2 decimal places, consistent with `expenses` being stored as
  `REAL`.

## Definition of done

- [ ] Logging in as the seeded demo user (`demo@spendly.com` / `demo123`) and visiting `/profile`
      shows all 8 seeded expenses, ordered newest `date` first.
- [ ] Visiting `/profile` while logged out redirects to `/login`.
- [ ] A user with zero expenses sees the empty-state message and no error/traceback.
- [ ] Each row shows date, category, description, and amount (2 decimal places).
- [ ] Only the logged-in user's own expenses ever appear — verified by checking the `WHERE
      user_id = ?` clause in `get_expenses_by_user` uses the session value, not a request
      parameter.
- [ ] The page renders inside `base.html` (shared nav/footer visible) and uses only existing
      `style.css` classes/variables — no new hardcoded colors.
- [ ] No add/edit/delete links or forms are present on the page.
