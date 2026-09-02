# Expenses Feature — Software Requirements Specification

## Overview

Spendly's core value proposition is tracking personal expenses. This feature covers the full
CRUD lifecycle for an authenticated user's expenses: viewing them on the profile page, adding new
ones, editing existing ones, and deleting them. It replaces the placeholder routes currently in
`app.py` (`profile` — Step 4, `add_expense` — Step 7, `edit_expense` — Step 8, `delete_expense` —
Step 9) with working implementations backed by the existing `expenses` table in
`database/db.py`.

Every expense belongs to exactly one user (`expenses.user_id`), and a user may only ever view,
edit, or delete their own expenses.

## Functional Requirements

- **FR-1**: An authenticated user can view a list of all their own expenses on the profile page
  (`/profile`), ordered by `date` descending (most recent first).
- **FR-2**: An authenticated user can add a new expense via `/expenses/add`, supplying amount,
  category, date, and an optional description.
- **FR-3**: An authenticated user can edit one of their own existing expenses via
  `/expenses/<id>/edit`, changing any of amount, category, date, or description.
- **FR-4**: An authenticated user can delete one of their own existing expenses via
  `/expenses/<id>/delete`, after confirming the action.
- **FR-5**: Category is restricted to a fixed set of values, matching the values already used by
  `seed_db()`: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`.
- **FR-6**: A user attempting to view, edit, or delete an expense that does not belong to them (or
  does not exist) is rejected — see Security section.
- **FR-7**: All three mutating routes (`add`, `edit`, `delete`) are only reachable by an
  authenticated user, enforced by the existing `login_required` decorator.

## Non-Functional Requirements

- **NFR-1**: Every expense-list read (`profile`) issues a single query, filtered by
  `user_id = ?`; no N+1 query patterns per row.
- **NFR-2**: All database access goes through `database/db.py` using parameterized queries — no
  string-interpolated SQL, consistent with `get_user_by_email`'s existing pattern.
- **NFR-3**: Pages render within the existing `base.html` layout/nav and reuse
  `static/css/style.css` conventions (no new CSS framework introduced).
- **NFR-4**: Amounts are stored as `REAL` (existing schema) and displayed formatted to 2 decimal
  places with a `₹` prefix, consistent with the footer tagline ("Track every rupee").

## User Stories

- As a logged-in user, I want to see all my expenses in one place so I can review my spending.
- As a logged-in user, I want to add a new expense so I can keep my records up to date.
- As a logged-in user, I want to correct a mistake in an existing expense so my records stay
  accurate.
- As a logged-in user, I want to delete an expense I entered by mistake so it stops affecting my
  totals.
- As a logged-in user, I want to be sure no one else can see, change, or delete my expenses.

## Acceptance Criteria

- **AC-1**: Given a logged-in user with N expenses, visiting `/profile` displays exactly those N
  expenses (amount, category, date, description) and no other user's expenses.
- **AC-2**: Given a logged-in user on `/expenses/add`, submitting a valid form creates one new row
  in `expenses` with `user_id` set to the current session user, then redirects to `/profile`.
- **AC-3**: Given a logged-in user on `/expenses/add`, submitting an invalid form (see Error
  Handling) re-renders the form with the entered values preserved and inline error messages; no
  row is created.
- **AC-4**: Given a logged-in user editing their own expense via `/expenses/<id>/edit`, submitting
  valid changes updates that row only, then redirects to `/profile`.
- **AC-5**: Given a logged-in user attempting `/expenses/<id>/edit` or `/expenses/<id>/delete` for
  an `id` belonging to another user (or a non-existent `id`), the app responds with 404 and makes
  no database change.
- **AC-6**: Given a logged-in user deleting their own expense, after confirming, the row is
  removed from `expenses` and no longer appears on `/profile`.

## API Requirements

All routes are server-rendered (form POST + redirect), no JSON API, matching the existing
`login`/`register` pattern.

| Route | Method(s) | Auth | Description |
|---|---|---|---|
| `/profile` | GET | required | List current user's expenses |
| `/expenses/add` | GET | required | Render empty add-expense form |
| `/expenses/add` | POST | required | Validate and insert a new expense; redirect to `/profile` |
| `/expenses/<int:id>/edit` | GET | required | Render edit form pre-filled with the expense (404 if not owned) |
| `/expenses/<int:id>/edit` | POST | required | Validate and update the expense (404 if not owned); redirect to `/profile` |
| `/expenses/<int:id>/delete` | POST | required | Delete the expense (404 if not owned); redirect to `/profile` |

`/expenses/<id>/delete` moves from `GET` to `POST` (a destructive action must not be triggerable
by a plain link/GET request — see Security).

## Database Changes

None required — the existing `expenses` table already supports this feature:

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users (id),
    amount      REAL NOT NULL,
    category    TEXT NOT NULL,
    date        TEXT NOT NULL,
    description TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
```

New functions to add to `database/db.py` (naming follows the existing `get_user_by_email`
convention):

- `get_expenses_by_user(user_id)` — all expenses for a user, ordered by `date DESC`.
- `get_expense_by_id(expense_id, user_id)` — single expense, scoped to the owning user (returns
  `None` if missing or not owned — this is what backs the 404 checks in AC-5).
- `add_expense(user_id, amount, category, date, description)` — insert.
- `update_expense(expense_id, user_id, amount, category, date, description)` — update, scoped by
  both `id` and `user_id` in the `WHERE` clause.
- `delete_expense(expense_id, user_id)` — delete, scoped by both `id` and `user_id`.

## UI Requirements

- **Profile page (`/profile`)**: extends `base.html`. A table or card list of expenses (date,
  category, description, amount), an "Add expense" link/button per row with "Edit" and "Delete"
  actions, and an empty state ("No expenses yet — add your first one") when the list is empty.
- **Add/Edit expense form**: extends `base.html`, styled consistently with `login.html` /
  `register.html` form patterns already in the codebase. Fields: amount (number input), category
  (`<select>` populated from the fixed category list), date (date input, defaulting to today on
  add), description (optional text input).
- **Delete confirmation**: a confirmation step before the delete POST fires (e.g. a JS `confirm()`
  or a dedicated confirm page) so a misclick can't silently destroy data.
- Category `<select>` order matches FR-5's list.

## Error Handling

- **Validation errors** (add/edit): amount must be present and a positive number; category must
  be one of the fixed set; date must be present and a valid `YYYY-MM-DD` date. On failure,
  re-render the form with the submitted values and a per-field or summary error message (same
  pattern as `login`'s `error` variable) — no partial writes.
- **Not found / not owned** (edit/delete): return a 404 response rather than leaking whether the
  `id` exists under another account.
- **Unauthenticated access**: any of the five routes redirect to `/login` via the existing
  `login_required` decorator.
- **Database errors**: unexpected `sqlite3` exceptions are not swallowed silently; they surface as
  a generic 500 rather than a partially-applied change (rely on SQLite's implicit per-statement
  transaction; do not commit on the write path if the insert/update raises).

## Security

- **Ownership enforcement**: every read/update/delete query filters by `user_id = ?` using the
  session's `user_id`, never a value taken from the request — the `<id>` in the URL only selects
  *which* expense, never *whose*.
- **CSRF protection**: add/edit/delete forms include the same `csrf_token` session-bound pattern
  already used by `login`, validated server-side before any write.
- **Destructive action via POST only**: `/expenses/<id>/delete` must not be a `GET`-triggerable
  link, preventing accidental deletion via prefetching, crawlers, or CSRF via `<img>`-style GET
  abuse.
- **Parameterized SQL**: all new `database/db.py` functions use `?` placeholders, no string
  formatting into SQL.
- **Authorization, not just authentication**: `login_required` alone is insufficient — it proves
  *a* user is logged in, not that they own the specific expense `id` in the URL; ownership checks
  in Database Changes (`get_expense_by_id`, `update_expense`, `delete_expense`) are mandatory on
  every mutating route.

## Test Cases

| ID | Scenario | Expected Result |
|---|---|---|
| TC-1 | Logged-in user visits `/profile` with 3 existing expenses | All 3 render, newest date first |
| TC-2 | Logged-in user visits `/profile` with 0 expenses | Empty-state message shown, no error |
| TC-3 | POST valid data to `/expenses/add` | New row inserted with correct `user_id`; redirect to `/profile` |
| TC-4 | POST `/expenses/add` with negative or non-numeric amount | Form re-rendered with error; no row inserted |
| TC-5 | POST `/expenses/add` with a category not in the fixed set | Form re-rendered with error; no row inserted |
| TC-6 | GET `/expenses/<id>/edit` for an expense owned by another user | 404 response |
| TC-7 | POST `/expenses/<id>/edit` with valid changes, owned expense | Row updated; redirect to `/profile` |
| TC-8 | POST `/expenses/<id>/delete` for an owned expense | Row removed; no longer listed on `/profile` |
| TC-9 | POST `/expenses/<id>/delete` for another user's expense id | 404 response; row NOT removed |
| TC-10 | GET any of the 5 routes while logged out | Redirect to `/login` |
| TC-11 | POST `/expenses/add` missing CSRF token / stale token | Rejected with error; no row inserted |
