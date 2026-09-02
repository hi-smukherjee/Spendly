# Design: Profile Page Redesign

Translates `docs/specs/profile-page-redesign.md` into concrete markup, classes, and CSS variable
values. This is the "design" step of the spec → design → tasks → build → validate flow — no code
is written yet; the **build** step implements exactly this.

## 1. New CSS variables (add to `:root` in `static/css/style.css`, after the existing block)

Bold/colorful category palette — saturated, mutually distinct hues, chosen to sit deliberately
apart from the existing muted `--accent` (forest green) / `--accent-2` (amber) pair rather than
competing with them:

```css
--cat-food:          #e8542e;  /* coral-red */
--cat-transport:     #2f6fed;  /* bold blue */
--cat-bills:         #8b5cf6;  /* violet */
--cat-health:        #10b981;  /* emerald */
--cat-entertainment: #ec4899;  /* pink */
--cat-shopping:      #f59e0b;  /* gold */
--cat-other:         #64748b;  /* slate (fallback for unknown categories) */
```

Stat-card accent bars (slot-based, not category-based — see §3):

```css
--stat-accent-1: var(--accent-2);   /* Total spent card  — amber, "money" association */
--stat-accent-2: var(--accent);     /* Expense count card — existing forest green */
/* Top-category card's accent is set inline per-row to that category's --cat-* color (§3) */
```

No existing variable is renamed or removed — this only adds to the block, per the skill's
"reuse and extend, don't introduce a parallel system" rule.

## 2. Class/container renames

| Old (borrowed from legal pages) | New                  |
|----------------------------------|----------------------|
| `.legal-section`                 | `.profile-section`   |
| `.legal-container`                | `.profile-container` |
| `.legal-card`                     | `.profile-card`      |
| `.legal-title`                    | `.profile-title`     |

Structural pattern (`*-section` > `*-container` > `*-title`/`*-card`) is copied from the existing
`.legal-*`/`.hero-*`/`.auth-*` families, just scoped to `profile-*` so the page stops borrowing
another page's semantics. Properties (padding, max-width, background, border, radius) start
identical to the `.legal-*` values they replace; only the diffs below are new.

## 3. Layout

```
.profile-section
  .profile-container (max-width: var(--max-width), wider than legal's 720px — this page
                       needs room for a 3-column stat row, not prose)
    .profile-header
      h1.profile-title  "Your Expenses"

    .stat-row                          <-- NEW, only rendered when expenses is non-empty
      .stat-card  (Total spent)   -- top accent: var(--stat-accent-1)
      .stat-card  (Expenses)      -- top accent: var(--stat-accent-2)
      .stat-card  (Top category)  -- top accent: var(--cat-<top_category slug>), set via an
                                      inline style="--stat-top-color: var(--cat-food)" (etc.)
                                      so the card visually matches the category it names

    .profile-card
      table.expense-table           <-- when expenses non-empty
        thead: Date | Category | Description | Amount
        tbody: one row per expense, each row carries a colored left-border accent:
               <tr class="category-{{ expense.category|lower }}">
      .profile-empty                <-- when expenses is empty (stat-row is NOT rendered)
```

### `.stat-card` anatomy

```
.stat-card
  .stat-value   -- large DM Serif Display number, e.g. "₹360.26" / "8" / "Food"
  .stat-label   -- small uppercase DM Sans label, ink-muted, e.g. "TOTAL SPENT"
```

- `background: var(--paper-card)`, `border: 1px solid var(--border)`, `border-radius: var(--radius-md)`
- `border-top: 4px solid <slot accent>` — the bold visual signature distinguishing this from the
  understated `.feature-card`/`.auth-card` treatments elsewhere.
- Grid: `.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }`

### Category chip + row accent

- `.expense-category` keeps its pill shape but becomes category-specific instead of one fixed
  green:
  ```css
  .category-food .expense-category { background: color-mix(in srgb, var(--cat-food) 15%, white); color: var(--cat-food); }
  ```
  (repeat per category; `--cat-other` is the fallback rule applied to any `category-*` class not
  explicitly listed, so unrecognized categories never render unstyled — satisfies TC-6.)
- Each `<tr>` also gets `border-left: 3px solid var(--cat-<category>)` for the "bold" left-accent
  look requested, applied via the same `category-{{ ... }}` row class — no per-row inline styles
  needed except the one stat card noted above.

### Empty state (`.profile-empty`)

Centered block, no illustration asset (NFR-1 — no new image/icon dependency):

```
.profile-empty
  span.profile-empty-icon   -- large glyph, e.g. "◈" (reuses the brand glyph from the navbar/footer
                                for consistency) at ~2.5rem, color: var(--ink-faint)
  h2                        -- "No expenses yet" — font-display
  p                         -- "Your expenses will show up here once you start tracking them."
                                — ink-muted, matches `.hero-subtitle` tone
```

## 4. Responsive behavior (extends existing breakpoints, does not add new ones)

- `@media (max-width: 900px)`: `.stat-row { grid-template-columns: 1fr; }` (stacks — same
  breakpoint already used to collapse `.hero`/`.features-inner` to one column).
- `@media (max-width: 600px)`: `.profile-card { padding: 1.5rem; }` and
  `.profile-section { padding: 2rem 1rem 3rem; }`, mirroring the existing `.legal-card`/
  `.legal-section` mobile rules being replaced. `.expense-table` gets a wrapping
  `.table-scroll { overflow-x: auto; }` div so a narrow viewport scrolls the table horizontally
  instead of breaking page layout (satisfies AC-8/TC-7).

## 5. Data passed from `app.py` (no new DB queries — NFR-4)

The `profile()` view computes three values in Python from the existing `get_expenses_by_user`
result before rendering:

```python
expenses = get_expenses_by_user(session["user_id"])
total_spent = sum(e["amount"] for e in expenses)
totals_by_category = {}
for e in expenses:
    totals_by_category[e["category"]] = totals_by_category.get(e["category"], 0) + e["amount"]
top_category = max(totals_by_category, key=totals_by_category.get) if expenses else None
```

Passed to the template as `expenses`, `total_spent`, `top_category` — the template itself does no
aggregation (keeps Jinja to display logic only, consistent with the rest of the app).

## 6. Out of scope (unchanged from spec)

No add/edit/delete controls, no new routes, no new DB columns/tables, no new dependencies, no date
filtering/sorting controls beyond the existing newest-first order.

## Next step

**Tasks** — break §1–§5 above into an ordered implementation checklist (CSS variables first, then
markup/class renames, then the Python aggregation, then responsive rules), per the
spec → design → **tasks** → build → validate flow.
