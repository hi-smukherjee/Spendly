# Tasks: Edit Expense (Step 8)

Ordered implementation checklist for `docs/specs/editexpense08.md` /
`docs/specs/editexpense08-design.md`. This is the **tasks** step of
spec → design → tasks → **build** → validate — build should follow this order so each task is
independently testable before the next depends on it.

## 1. Database layer (`database/db.py`)

- [ ] 1.1 Add `get_expense_by_id(id, user_id)` per design §1 — `SELECT * ... WHERE id = ? AND
      user_id = ?`, returns the row or `None`.
- [ ] 1.2 Add `update_expense(id, user_id, amount, category, date, description)` per design §1 —
      parameterized `UPDATE ... WHERE id = ? AND user_id = ?`.
- [ ] 1.3 Manually verify both against the seeded demo data: `get_expense_by_id` returns `None`
      for a made-up id, and returns the row for a real id owned by the demo user.

## 2. Route (`app.py`)

- [ ] 2.1 Add `abort` to the `from flask import ...` line; add `get_expense_by_id`,
      `update_expense` to the `from database.db import ...` line.
- [ ] 2.2 Define the `EXPENSE_CATEGORIES` list (module-level constant) per design §2.
- [ ] 2.3 Replace the placeholder `edit_expense` view with the `GET`/`POST` implementation from
      design §2: `methods=["GET", "POST"]`, ownership check + `abort(404)` before anything else,
      CSRF issuance on `GET`.
- [ ] 2.4 Implement the `POST` validation block in order: CSRF check → date required → category
      in `EXPENSE_CATEGORIES` → amount numeric and > 0 — matching the order in design §2 so error
      precedence is deterministic.
- [ ] 2.5 On validation failure, re-render `edit_expense.html` with `expense`, `categories`, a
      fresh `csrf_token`, the `error` string, and the submitted `form` dict — no database write.
- [ ] 2.6 On success, call `update_expense(...)` and `redirect(url_for("profile"))`.
- [ ] 2.7 Confirm `/expenses/add` and `/expenses/<id>/delete` view functions are untouched.

## 3. Template (`templates/edit_expense.html`)

- [ ] 3.1 Create the file extending `base.html`, using the `.auth-section`/`.auth-container`/
      `.auth-card` structure per design §3 (copied from `login.html`).
- [ ] 3.2 Add the four form fields (amount/category/date/description) with the
      `form.x if form else expense['x']` fallback pattern so submitted values survive a
      validation error (FR-3).
- [ ] 3.3 Amount field: `type="number" step="0.01" min="0.01"`, pre-filled to 2 decimal places
      from `expense['amount']` when there's no `form` (i.e. first load).
- [ ] 3.4 Category field: `<select>` looping over `categories`, pre-selecting the current value.
- [ ] 3.5 Date field: `type="date"`, pre-filled from the stored `YYYY-MM-DD` string.
- [ ] 3.6 Description field: plain text input, optional, pre-filled or empty.
- [ ] 3.7 Hidden `csrf_token` field; `{% if error %}` block using `.auth-error`, matching
      `login.html`'s pattern exactly.
- [ ] 3.8 "Save changes" submit button (`.btn-submit`) and a "Cancel" link back to `/profile`.

## 4. Profile table actions column (`templates/profile.html` + `static/css/style.css`)

- [ ] 4.1 Add the `<th>Actions</th>` header cell.
- [ ] 4.2 Add the per-row `<td>` with an "Edit" link (`.btn-ghost btn-table-action`) pointing at
      `url_for('edit_expense', id=expense['id'])`, per design §4.
- [ ] 4.3 Add the `.btn-table-action` CSS rule (design §4) — the one new rule this feature
      introduces.
- [ ] 4.4 Confirm the new column sits inside the existing `.table-scroll` wrapper and doesn't need
      its own responsive rule.

## 5. Validate against spec

- [ ] 5.1 AC-1: "Edit" link on any row opens a form pre-filled with that exact row's values.
- [ ] 5.2 AC-2: valid edit → redirect to `/profile`, updated values and category color visible
      immediately.
- [ ] 5.3 AC-3: `amount` = `0`, negative, or non-numeric → inline error, row unchanged in DB.
- [ ] 5.4 AC-4: empty `date` or `category` → inline error, row unchanged.
- [ ] 5.5 AC-5: empty `description` → accepted, saved as empty/`NULL`.
- [ ] 5.6 AC-6: nonexistent or not-owned `id` (try editing another seeded/test user's expense id)
      → `404`.
- [ ] 5.7 AC-7: logged-out `GET`/`POST` to `/expenses/<id>/edit` → redirect to `/login`.
- [ ] 5.8 AC-8: missing/mismatched `csrf_token` → inline error, row unchanged.
- [ ] 5.9 AC-9: `/expenses/add` and `/expenses/<id>/delete` still return their original
      placeholder strings (regression check).
- [ ] 5.10 Tamper-test: submit a `category` value not in `EXPENSE_CATEGORIES` via a raw request
      (not through the `<select>`) → inline error, row unchanged (spec TC-10 / Security note on
      not trusting the `<select>` alone).
- [ ] 5.11 Confirm no new hardcoded hex colors were added (the only new CSS, `.btn-table-action`,
      uses no color values at all).
- [ ] 5.12 Confirm `requirements.txt` is untouched (NFR-1 — no new dependencies).
- [ ] 5.13 At 375px width, the profile table (now 5 columns) still scrolls inside
      `.table-scroll` rather than breaking page layout; the edit form page renders correctly at
      the same width.

## Next step

**Build** — implement tasks 1–4 in order, then run through the validation checklist in §5.
