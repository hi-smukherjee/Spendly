# Expenses Feature — Design

Follows [`docs/specs/expenses.md`](../specs/expenses.md). This document translates that spec into
concrete routes, database functions, templates, and validation logic, matching the conventions
already established by `login`/`register` in `app.py` and `get_user_by_email` in `database/db.py`.
No code is written here — this is the "design" step; "tasks" and "build" come after.

## Architecture Summary

No new architectural pattern is introduced. Same single-file Flask app, same raw-SQLite-via-
`database/db.py` approach, same server-rendered form+redirect flow as `login`. Five routes change
from placeholder strings to real implementations:

```
GET  /profile                  → profile()       (Step 4)
GET  /expenses/add             → add_expense()    (Step 7, render form)
POST /expenses/add             → add_expense()    (Step 7, handle submit)
GET  /expenses/<id>/edit       → edit_expense(id)  (Step 8, render form)
POST /expenses/<id>/edit       → edit_expense(id)  (Step 8, handle submit)
POST /expenses/<id>/delete     → delete_expense(id) (Step 9)
```

`add_expense` and `edit_expense` each become a single view function handling both GET and POST
(`methods=["GET", "POST"]`), mirroring how `login` already does it — not split into separate
functions.

## Data Flow

```
Browser                    Flask (app.py)                 database/db.py            SQLite
   |                             |                              |                      |
   |-- GET /profile ----------->|                              |                      |
   |                             |-- get_expenses_by_user(uid)->|-- SELECT ... ------->|
   |                             |<---------------- rows -------|<-------- rows -------|
   |<--- render profile.html ---|                              |                      |
   |                             |                              |                      |
   |-- POST /expenses/add ----->|-- validate form ------------>|                      |
   |    (amount, category,      |   (server-side, see below)   |                      |
   |     date, description)     |-- add_expense(uid, ...) ---->|-- INSERT ----------->|
   |<--- redirect /profile -----|                              |                      |
```

Edit follows the same shape as add, but every read/write is additionally scoped by `user_id` (see
Security in the spec) via `get_expense_by_id(id, uid)` / `update_expense(id, uid, ...)`. Delete is
the same scoping applied to a `DELETE`.

## Database Layer Design (`database/db.py`)

All five functions follow the existing style: open connection, execute parameterized query, close
connection, return `sqlite3.Row` / list of rows / `None`.

```python
def get_expenses_by_user(user_id):
    """Return all expenses for a user, most recent first."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_expense_by_id(expense_id, user_id):
    """Return one expense iff it belongs to user_id, else None."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    ).fetchone()
    conn.close()
    return row


def add_expense(user_id, amount, category, date, description):
    """Insert a new expense, return its new id."""
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def update_expense(expense_id, user_id, amount, category, date, description):
    """Update an expense iff it belongs to user_id. Returns True if a row changed."""
    conn = get_db()
    cursor = conn.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? "
        "WHERE id = ? AND user_id = ?",
        (amount, category, date, description, expense_id, user_id),
    )
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed


def delete_expense(expense_id, user_id):
    """Delete an expense iff it belongs to user_id. Returns True if a row was removed."""
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
```

The `WHERE id = ? AND user_id = ?` clause is what makes ownership structurally impossible to skip
— there is no code path in `update_expense`/`delete_expense` that can touch another user's row,
even if a caller forgot to check ownership first. `cursor.rowcount` doubles as the "not found or
not owned" signal that routes use to decide 404 vs. success.

A module-level constant is added for the fixed category list, imported by `app.py` for both
server-side validation and to populate the `<select>`:

```python
EXPENSE_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
```

## Route Design (`app.py`)

### `profile()` — GET `/profile`

```
expenses = get_expenses_by_user(session["user_id"])
render profile.html with expenses=expenses
```

### `add_expense()` — GET/POST `/expenses/add`

```
GET:
    session["csrf_token"] = new token
    render add_expense.html with csrf_token, categories=EXPENSE_CATEGORIES, form={} , error=None

POST:
    validate csrf_token (same pattern as login)
    read amount, category, date, description from request.form
    errors = validate(amount, category, date)     # see Form Validation below
    if errors:
        re-render add_expense.html with entered values + errors, fresh csrf_token
    else:
        add_expense(session["user_id"], amount, category, date, description)
        redirect to /profile
```

### `edit_expense(id)` — GET/POST `/expenses/<int:id>/edit`

```
expense = get_expense_by_id(id, session["user_id"])
if expense is None:
    abort(404)

GET:
    render edit_expense.html pre-filled from expense, fresh csrf_token

POST:
    validate csrf_token
    errors = validate(amount, category, date)
    if errors:
        re-render edit_expense.html with entered values + errors
    else:
        update_expense(id, session["user_id"], amount, category, date, description)
        redirect to /profile
```

Fetching `expense` before branching on method means the 404 check happens once, for both GET and
POST, before any form logic runs.

### `delete_expense(id)` — POST only, `/expenses/<int:id>/delete`

```
validate csrf_token
deleted = delete_expense(id, session["user_id"])
if not deleted:
    abort(404)
redirect to /profile
```

Route decorator changes from `@app.route("/expenses/<int:id>/delete")` (implicit GET) to
`@app.route("/expenses/<int:id>/delete", methods=["POST"])` — this is the fix called out in the
spec's Security section.

## Form Validation Design

A single helper, colocated with the routes, used by both add and edit:

```python
def validate_expense_form(amount_raw, category, date_raw):
    """Return a dict of field_name -> error message; empty dict means valid."""
    errors = {}

    try:
        amount = float(amount_raw)
        if amount <= 0:
            errors["amount"] = "Amount must be greater than zero."
    except (TypeError, ValueError):
        errors["amount"] = "Enter a valid amount."

    if category not in EXPENSE_CATEGORIES:
        errors["category"] = "Choose a valid category."

    try:
        datetime.strptime(date_raw, "%Y-%m-%d")
    except (TypeError, ValueError):
        errors["date"] = "Enter a valid date."

    return errors
```

`description` has no validation — optional free text, stored as-is (empty string or `None`).

## CSRF Design

Reuses the exact `login` pattern rather than introducing a new mechanism:

- A fresh `session["csrf_token"]` is set on every GET that renders a form (add, edit).
- Each form includes `<input type="hidden" name="csrf_token" value="{{ csrf_token }}">`.
- Each POST handler compares `request.form["csrf_token"]` against `session["csrf_token"]` before
  doing anything else; mismatch → treat like a validation error (re-render with a generic error,
  no partial write).
- The delete action needs a token too, so it can't be a bare link — it's implemented as a small
  `<form method="POST">` with a submit button (styled to look like a link/icon if desired), not an
  `<a href="...">`.

## UI / Template Design

Three new templates, all extending `base.html` like every existing page.

**`templates/profile.html`**

```
+--------------------------------------------------------------+
| [nav from base.html]                                          |
+--------------------------------------------------------------+
|  Your expenses                          [+ Add expense] ---->|  (link to /expenses/add)
+--------------------------------------------------------------+
|  Date        Category      Description        Amount         |
|  --------------------------------------------------------    |
|  2026-08-18  Food          Dinner out          ₹47.60  [Edit] [Delete]
|  2026-08-16  Other         Miscellaneous       ₹15.75  [Edit] [Delete]
|  ...                                                          |
+--------------------------------------------------------------+
```

- Empty state (no rows): a centered message "No expenses yet — add your first one" plus the same
  "Add expense" link, reusing `.auth-subtitle`-style typography.
- Each row's `[Delete]` is its own `<form method="POST" action="/expenses/<id>/delete">` with a
  JS `onsubmit="return confirm('Delete this expense?')"` — satisfies the spec's confirmation
  requirement without a separate confirm page.
- New CSS needed in `static/css/style.css`: `.expense-table`, `.expense-row`, `.expense-amount`,
  `.expense-empty`, `.btn-danger` (using the existing `--danger` / `--danger-light` tokens, which
  are defined but currently unused).

**`templates/add_expense.html`** / **`templates/edit_expense.html`**

Same `.auth-card` / `.form-group` / `.form-input` / `.btn-submit` structure as `login.html`
(shown in full in the spec's UI Requirements), so they inherit existing styling for free:

```
+-----------------------------+
|   Add an expense            |
|   ------------------------  |
|   Amount        [________]  |
|   Category      [Food ▾]    |
|   Date          [2026-09-02]|
|   Description   [________]  |
|                              |
|        [ Save expense ]     |
+-----------------------------+
```

Category `<select>` options are rendered from `EXPENSE_CATEGORIES` (Jinja `{% for %}`), so the
fixed set lives in exactly one place (`db.py`) and both the form and server-side validation read
from it — no duplicated string list.

## File Change List

| File | Change |
|---|---|
| `database/db.py` | Add `EXPENSE_CATEGORIES`, `get_expenses_by_user`, `get_expense_by_id`, `add_expense`, `update_expense`, `delete_expense` |
| `app.py` | Replace placeholder `profile`, `add_expense`, `edit_expense`, `delete_expense` bodies; add `validate_expense_form` helper; import new `db.py` functions + `EXPENSE_CATEGORIES`; add `from datetime import datetime` (already imports `timedelta` from `datetime`) |
| `templates/profile.html` | New |
| `templates/add_expense.html` | New |
| `templates/edit_expense.html` | New |
| `static/css/style.css` | Add `.expense-table`, `.expense-row`, `.expense-amount`, `.expense-empty`, `.btn-danger` |

No changes to `templates/base.html` or the `users` table.

## Open Questions / Risks

- **Timezone/"today" for the date default**: `datetime.strptime`/`date.today()` uses the server's
  local time; fine for a single-user learning app, worth a comment if this ever runs across
  timezones.
- **`abort(404)` import**: `app.py` doesn't currently import `abort` from `flask` — needs adding.
- **Amount precision**: stored as `REAL` (float); acceptable for this learning project's scope,
  but a production app would use integer cents or `Decimal` to avoid float rounding — out of scope
  per the spec's "keep it minimal" answer.
