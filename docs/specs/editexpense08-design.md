# Design: Edit Expense (Step 8)

Translates `docs/specs/editexpense08.md` into concrete routes, functions, markup, and classes.
This is the "design" step of the spec → design → tasks → **build** → validate flow — no code is
written yet; the **build** step implements exactly this.

## 1. `database/db.py` — two new functions

Placed after `get_expenses_by_user`, following the file's existing connection-per-call style
(fresh `get_db()`, explicit `conn.close()`, parameterized SQL only):

```python
def get_expense_by_id(id, user_id):
    """Return the expense row matching id and owned by user_id, or None."""
    conn = get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?", (id, user_id)
    ).fetchone()
    conn.close()
    return expense


def update_expense(id, user_id, amount, category, date, description):
    """Update an expense in place. Scoped by user_id; a no-op if the id/user_id pair doesn't
    match any row (defense in depth — the view already checks ownership first)."""
    conn = get_db()
    conn.execute(
        """
        UPDATE expenses
        SET amount = ?, category = ?, date = ?, description = ?
        WHERE id = ? AND user_id = ?
        """,
        (amount, category, date, description, id, user_id),
    )
    conn.commit()
    conn.close()
```

Both take `user_id` as an explicit parameter rather than relying on the caller to filter — the
`WHERE ... AND user_id = ?` clause is what makes IDOR (spec AC-6/AC-12, Security) structurally
impossible rather than dependent on the view remembering to check.

## 2. `app.py` — route

Replace the placeholder:

```python
@app.route("/expenses/<int:id>/edit")
@login_required
def edit_expense(id):
    return "Edit expense — coming in Step 8"
```

with a `GET`+`POST` view, mirroring the existing `/login` view's shape (token issuance on `GET`,
validation block on `POST`, re-render with `error` on failure):

```python
EXPENSE_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method == "GET":
        session["csrf_token"] = secrets.token_hex(16)
        return render_template(
            "edit_expense.html", expense=expense, categories=EXPENSE_CATEGORIES,
            csrf_token=session["csrf_token"],
        )

    form = {
        "amount": request.form.get("amount", "").strip(),
        "category": request.form.get("category", "").strip(),
        "date": request.form.get("date", "").strip(),
        "description": request.form.get("description", "").strip(),
    }
    submitted_token = request.form.get("csrf_token", "")

    error = None
    amount_value = None
    if not submitted_token or submitted_token != session.get("csrf_token"):
        error = "Something went wrong. Please try again."
    elif not form["date"]:
        error = "Date is required."
    elif form["category"] not in EXPENSE_CATEGORIES:
        error = "Please choose a valid category."
    else:
        try:
            amount_value = float(form["amount"])
            if amount_value <= 0:
                error = "Amount must be greater than zero."
        except ValueError:
            error = "Amount must be a number."

    if error:
        session["csrf_token"] = secrets.token_hex(16)
        return render_template(
            "edit_expense.html", expense=expense, categories=EXPENSE_CATEGORIES,
            csrf_token=session["csrf_token"], error=error, form=form,
        )

    update_expense(
        id, session["user_id"], amount_value, form["category"], form["date"],
        form["description"] or None,
    )
    return redirect(url_for("profile"))
```

Notes:

- `abort(404)` runs **before** the CSRF/validation block on both methods (a `GET` for a
  not-owned/nonexistent `id` also 404s) — satisfies FR-1/FR-4/AC-6/TC-2/TC-3/TC-12.
- `EXPENSE_CATEGORIES` is the single source of truth for the fixed category set, used both to
  populate the `<select>` and to validate the `POST` body server-side (Security — a `<select>` is
  a UI hint, not a guarantee).
- `abort` and `secrets` need importing/already imported — `secrets` is already imported at the top
  of `app.py`; `abort` needs adding to the `from flask import ...` line.
- New imports needed in `app.py`: `get_expense_by_id`, `update_expense` added to the existing
  `from database.db import ...` line.
- On validation failure, the raw `form` dict (submitted values) is passed back so the template can
  re-populate fields with what the user actually typed, not the stale DB values — matches FR-3's
  "submitted values retained."

## 3. `templates/edit_expense.html` — new template

Structure copied from `login.html`/`register.html`'s `.auth-section` > `.auth-container` >
`.auth-card` pattern (per spec UI Requirements), not a new container family — this is a single
form page like login/register, not a dashboard like profile:

```
{% extends "base.html" %}
{% block title %}Edit expense — Spendly{% endblock %}
{% block content %}

<section class="auth-section">
  <div class="auth-container">

    <div class="auth-header">
      <h1 class="auth-title">Edit expense</h1>
      <p class="auth-subtitle">Update the details below</p>
    </div>

    <div class="auth-card">
      {% if error %}
      <div class="auth-error">{{ error }}</div>
      {% endif %}

      <form method="POST" action="{{ url_for('edit_expense', id=expense['id']) }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

        <div class="form-group">
          <label for="amount">Amount</label>
          <input type="number" id="amount" name="amount" class="form-input"
                 step="0.01" min="0.01"
                 value="{{ form.amount if form else '%.2f'|format(expense['amount']) }}"
                 required autofocus>
        </div>

        <div class="form-group">
          <label for="category">Category</label>
          <select id="category" name="category" class="form-input" required>
            {% for c in categories %}
            <option value="{{ c }}"
                {% if (form.category if form else expense['category']) == c %}selected{% endif %}>
              {{ c }}
            </option>
            {% endfor %}
          </select>
        </div>

        <div class="form-group">
          <label for="date">Date</label>
          <input type="date" id="date" name="date" class="form-input"
                 value="{{ form.date if form else expense['date'] }}" required>
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <input type="text" id="description" name="description" class="form-input"
                 placeholder="Optional note"
                 value="{{ form.description if form else (expense['description'] or '') }}">
        </div>

        <button type="submit" class="btn-submit">Save changes</button>
      </form>
    </div>

    <p class="auth-switch">
      <a href="{{ url_for('profile') }}">Cancel</a>
    </p>

  </div>
</section>

{% endblock %}
```

- Reuses `.auth-*`/`.form-*`/`.btn-submit`/`.auth-error` wholesale — **no new CSS classes or
  variables are needed for this page** (NFR-4 satisfied by reuse, not new rules).
- The `form.amount if form else ...` / `form.category if form else ...` ternaries are how "retain
  submitted values on error, else show the DB values" (FR-3, AC-3/AC-4) is expressed without two
  separate templates: `form` is only passed in on a failed `POST` re-render.

## 4. `templates/profile.html` — actions column

Add a 5th column to the existing table, and one `.btn-ghost` link per row:

```
<thead>
    <tr>
        <th>Date</th>
        <th>Category</th>
        <th>Description</th>
        <th>Amount</th>
        <th>Actions</th>              <!-- NEW -->
    </tr>
</thead>
<tbody>
    {% for expense in expenses %}
    <tr class="category-{{ expense['category']|lower }}">
        <td>{{ expense["date"] }}</td>
        <td><span class="expense-category">{{ expense["category"] }}</span></td>
        <td>{{ expense["description"] or "—" }}</td>
        <td class="expense-amount">₹{{ "%.2f"|format(expense["amount"]) }}</td>
        <td>
            <a href="{{ url_for('edit_expense', id=expense['id']) }}"
               class="btn-ghost btn-table-action">Edit</a>   <!-- NEW -->
        </td>
    </tr>
    {% endfor %}
</tbody>
```

`.btn-ghost` already exists and is already used for the "Analytics" link in `.profile-header` —
reused as-is for visual consistency. One new small modifier class, `.btn-table-action`, tightens
its padding/font-size so it fits inside a table cell without inflating row height:

```css
.btn-table-action {
    padding: 0.3rem 0.85rem;
    font-size: 0.8rem;
}
```

This is the **one** new CSS rule this whole feature needs — everything else (form page, stat
cards, category colors) reuses what already exists in `style.css`.

## 5. Responsive behavior (extends existing breakpoints, adds none)

- The edit form page needs no new responsive rules — `.auth-section`/`.auth-card`/`.form-input`
  already behave correctly at all widths (proven by `login.html`/`register.html`).
- The profile table's new "Actions" column sits inside the existing `.table-scroll { overflow-x:
  auto }` wrapper — at 375px the table scrolls horizontally as a whole (unchanged mechanism from
  the profile redesign), so the extra column doesn't force new mobile-specific rules
  (NFR-3/TC-14 region).

## 6. Out of scope (unchanged from spec)

No flash/success message system, no Add or Delete UI/routes, no schema changes, no new
dependencies, no change to `/expenses/add` or `/expenses/<id>/delete` placeholders.

## Next step

**Tasks** — break §1–§4 above into an ordered implementation checklist (DB functions first, then
the route, then the new template, then the profile table edit), per the
spec → design → **tasks** → build → validate flow.
