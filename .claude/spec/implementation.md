# Implementation Plan — Step 1: Database Setup

Companion to [`specsheet`](./specsheet). Records the approach taken to satisfy that spec and the
final state of the implementation, following the repo's spec-driven workflow (spec → design →
tasks → build → validate).

## Scope

Files changed: `database/db.py`, `app.py`. No new files, no new dependencies (per spec §7–9).

## Design decisions

- **Schema** follows the spec's column list/types exactly (§4). One open point the spec left
  unspecified — `ON DELETE` behavior on `expenses.user_id`'s FK — was resolved by dropping any
  `ON DELETE` clause, matching the spec literally rather than adding undocumented cascade behavior.
- **`get_db()`** resolves `expense_tracker.db` to the project root regardless of working directory
  (`os.path.dirname` walked up from `database/db.py`'s own location), sets `row_factory = sqlite3.Row`
  and `PRAGMA foreign_keys = ON` per connection, per spec §5A.
- **`init_db()`** uses a single `executescript()` with `CREATE TABLE IF NOT EXISTS` for both tables —
  safe to call repeatedly, per spec §5B.
- **`seed_db()`** guards on "does `users` have any row at all" (not a specific email) before
  inserting, so it's safe to call on every app startup without duplicating data, per spec §5C/§11.
  Seeds exactly one demo user and 8 expenses spanning all 7 fixed categories (Food ×2, one each of
  Transport/Bills/Health/Entertainment/Shopping/Other), dates `2026-08-01`–`2026-08-18`.
- **`app.py` startup wiring**: `init_db()`/`seed_db()` run inside `app.app_context()` at *module
  level* (right after `app = Flask(__name__)`), not inside `if __name__ == "__main__":`. This
  guarantees the DB is ready whenever `app` is imported — by `flask run`, a future test suite via
  `pytest-flask`, or a WSGI server — not only when run directly via `python app.py`. Both functions
  are idempotent, so the Werkzeug debug reloader executing this twice on startup is harmless.
- The pre-existing `if __name__ == "__main__":` block in `database/db.py` (a `python -m database.db`
  convenience for resetting/inspecting the DB standalone) was kept — it's guarded and doesn't
  conflict with `app.py`'s own startup call.

## Verification performed

All checks from spec §12–14 (Definition of Done) were run against a freshly rebuilt
`expense_tracker.db`:

| Check | Result |
| --- | --- |
| `PRAGMA table_info` on both tables matches spec column types/nullability | ✅ |
| `users` has exactly 1 row, `email = demo@spendly.com` | ✅ |
| `expenses` has exactly 8 rows, all 7 categories represented | ✅ |
| `check_password_hash(hash, "demo123")` → `True` | ✅ |
| Calling `seed_db()` a second time does not add rows | ✅ |
| Insert with a nonexistent `user_id` raises `IntegrityError` (FK enforced) | ✅ |
| Insert with a duplicate `email` raises `IntegrityError` (UNIQUE enforced) | ✅ |
| `python app.py` starts cleanly; `GET /` → `200` | ✅ |

## Status

Complete. Committed on `feature/database-setup` (schema/seed corrections + `app.py` wiring not yet
committed as of this writing — see git status before merging).
