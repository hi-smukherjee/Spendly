# Expenses Feature — Tasks

Ordered checklist implementing [`docs/design/expenses.md`](../design/expenses.md). Grouped by the
step numbers already referenced in `app.py`'s placeholder comments (Steps 4, 7, 8, 9). Work
top-to-bottom — later tasks assume earlier ones are done (e.g. templates need the category
constant; routes need the `db.py` functions).

## 0. Shared groundwork (blocks everything below)

- [ ] In `database/db.py`, add the `EXPENSE_CATEGORIES` constant (`Food`, `Transport`, `Bills`,
      `Health`, `Entertainment`, `Shopping`, `Other`).
- [ ] In `database/db.py`, add `get_expenses_by_user(user_id)`.
- [ ] In `database/db.py`, add `get_expense_by_id(expense_id, user_id)`.
- [ ] In `database/db.py`, add `add_expense(user_id, amount, category, date, description)`.
- [ ] In `database/db.py`, add `update_expense(expense_id, user_id, amount, category, date, description)`.
- [ ] In `database/db.py`, add `delete_expense(expense_id, user_id)`.
- [ ] In `app.py`, import `abort` from `flask` (not currently imported).
- [ ] In `app.py`, import the new `db.py` functions and `EXPENSE_CATEGORIES`.
- [ ] In `app.py`, add a `validate_expense_form(amount_raw, category, date_raw)` helper (returns a
      dict of field → error message).
- [ ] In `static/css/style.css`, add `.expense-table`, `.expense-row`, `.expense-amount`,
      `.expense-empty`, `.btn-danger` (reuse `--danger` / `--danger-light` tokens).

## 1. Step 4 — Profile page (view/list)

- [ ] Replace the `profile()` placeholder in `app.py`: fetch
      `get_expenses_by_user(session["user_id"])`, render `profile.html` with `expenses=expenses`.
- [ ] Create `templates/profile.html` extending `base.html`: table of date/category/description/
      amount, "Add expense" link, per-row Edit link + Delete form (POST + `confirm()`), empty
      state when there are no expenses.
- [ ] Manual check: log in as the seeded demo user (`demo@spendly.com` / `demo123`), confirm all 8
      seeded expenses render, newest date first.

## 2. Step 7 — Add expense

- [ ] Replace the `add_expense()` placeholder in `app.py` with `methods=["GET", "POST"]`:
      - GET: set fresh `session["csrf_token"]`, render `add_expense.html`.
      - POST: validate CSRF token, run `validate_expense_form`, either re-render with errors or
        call `add_expense(...)` and redirect to `/profile`.
- [ ] Create `templates/add_expense.html` extending `base.html`, following the `login.html`
      `.auth-card`/`.form-group` structure: amount, category `<select>` (looped from
      `EXPENSE_CATEGORIES`), date (defaulting to today), description, hidden `csrf_token`.
- [ ] Manual check: submit a valid expense → appears on `/profile`. Submit a negative amount, an
      invalid date, and an out-of-list category → each re-renders the form with an error and adds
      no row.

## 3. Step 8 — Edit expense

- [ ] Replace the `edit_expense(id)` placeholder in `app.py` with `methods=["GET", "POST"]`:
      - Fetch `get_expense_by_id(id, session["user_id"])` first; `abort(404)` if `None` (covers
        both GET and POST, and both "doesn't exist" and "belongs to someone else").
      - GET: render `edit_expense.html` pre-filled from the fetched row, fresh CSRF token.
      - POST: validate CSRF token, run `validate_expense_form`, either re-render with errors or
        call `update_expense(...)` and redirect to `/profile`.
- [ ] Create `templates/edit_expense.html` (same structure as `add_expense.html`, values
      pre-filled, category `<select>` pre-selected).
- [ ] Manual check: edit one of your own expenses, confirm the change shows on `/profile`. Try
      visiting `/expenses/<id>/edit` for an `id` that belongs to a different user (or doesn't
      exist) → expect a 404.

## 4. Step 9 — Delete expense

- [ ] Change the route decorator to `methods=["POST"]` only (no more implicit GET).
- [ ] Replace the `delete_expense(id)` placeholder body: validate CSRF token, call
      `delete_expense(id, session["user_id"])`, `abort(404)` if it returned `False`, otherwise
      redirect to `/profile`.
- [ ] Wire the delete `<form>` + `confirm()` on `profile.html` (may already be done in Step 1
      above — verify it points at the right action/method).
- [ ] Manual check: delete one of your own expenses, confirm it disappears from `/profile`. Try
      POSTing to `/expenses/<id>/delete` for another user's `id` (e.g. via curl) → expect 404 and
      the row still present.

## 5. Validate (cross-cutting, do last)

- [ ] Run through every test case in `docs/specs/expenses.md`'s Test Cases table (TC-1 … TC-11).
- [ ] Confirm logged-out access to all five routes redirects to `/login` (existing
      `login_required` decorator — verify it's applied to all four new/changed routes, not just
      the old placeholders).
- [ ] Confirm no route builds SQL via string interpolation (grep for `f"` / `.format(` / `%` near
      any `execute(` call in `db.py`).
- [ ] Re-read `docs/design/expenses.md`'s Open Questions section — decide if the date/timezone and
      float-amount notes need a follow-up task or are accepted as out-of-scope for this project.
