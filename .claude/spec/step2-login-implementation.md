# Implementation Plan — Step 2: Login Authentication

Companion to [`step2-login-specsheet`](./step2-login-specsheet). Records the approach taken and
the final state of the implementation, following the repo's spec-driven workflow (spec → design →
tasks → build → validate).

## Scope

Files changed: `app.py`, `templates/login.html`, `templates/base.html`, `static/css/style.css`.
No new files besides this pair of spec docs, no new dependencies (per spec §3, §14).

A full enterprise SRS (SQLAlchemy, Flask-Login, Flask-WTF, Flask-Mail, Postgres, RBAC, audit log,
email password reset, account lockout, remember-me) was the starting input; scope was explicitly
narrowed to core login/logout on the existing stack via a written plan reviewed and approved before
any code was written — see spec §3 for the itemized cut list and rationale.

## Design decisions

- **Secret key** is a hardcoded dev string in `app.py` with an inline comment flagging it as
  dev-only. No `.env`/`python-dotenv` exists in this project yet, and introducing one wasn't part
  of the agreed scope — the comment is the guardrail until that infra exists.
- **CSRF** is hand-rolled (`secrets.token_hex(16)` in `session`, hidden form field, equality check
  on POST) rather than Flask-WTF, per the "keep current stack" decision. A mismatched or missing
  token collapses into the same generic `"Invalid email or password."` message rather than a
  separate CSRF error, so a tampered request can't be distinguished from a bad password.
- **Session-fixation mitigation**: `session.clear()` immediately before setting the authenticated
  session keys. Flask's session is a signed cookie, not a server-side ID, so there's no session ID
  to literally regenerate — clearing and repopulating the payload is the practical equivalent
  (the signed cookie value changes because its content changed).
- **30-minute inactivity expiry** uses `PERMANENT_SESSION_LIFETIME` + `session.permanent = True`,
  relying on Flask's default `SESSION_REFRESH_EACH_REQUEST = True` to make it a sliding window
  rather than a fixed one.
- **`SESSION_COOKIE_SECURE = False`**: the dev server runs on plain HTTP
  (`http://localhost:5001`), so `Secure` would make the cookie unusable locally. Flagged in the
  spec as a pre-production flip, not deferred silently.
- **Redirect target on success is `/profile`**, even though that route still returns its Step-4
  placeholder string. The login system needed *some* real post-auth destination, and `/profile` is
  the one that already exists for that purpose — this only changes how it's reached, not its body.
- **`login_required`** is a single ~8-line decorator defined directly in `app.py` rather than a new
  `auth.py` module — the project has no blueprints/module structure yet (per `CLAUDE.md`, all
  routes live in `app.py`), so a new file for one decorator would be over-structuring at this size.
- **`/register` was left untouched.** Its form already POSTs to `/register`, but that route has no
  POST handler and wiring one up wasn't part of the login SRS — noted explicitly in spec §3 as a
  separate, pre-existing placeholder rather than silently left broken.

## Verification performed

All checks from spec §15 (Definition of Done) were run against the running dev server
(`python app.py`) using `curl` with a cookie jar:

| Check | Result |
| --- | --- |
| `demo@spendly.com` / `demo123` logs in, redirects to `/profile` (302) | ✅ |
| Wrong password → `Invalid email or password.` | ✅ |
| Unknown email → `Invalid email or password.` (same message) | ✅ |
| Empty email → `Email is required.` | ✅ |
| Empty password → `Password is required.` | ✅ |
| Tampered/missing CSRF token → rejected with the generic message | ✅ |
| `Set-Cookie` header includes `HttpOnly` and `SameSite=Lax` | ✅ |
| `GET /profile` while logged out → `302` to `/login` | ✅ |
| `GET /profile` while logged in → `200` | ✅ |
| `GET /logout` clears session; `/profile` afterward → `302` to `/login` again | ✅ |
| Nav shows "Sign in"/"Get started" logged out, name + "Log out" logged in | ✅ |
| `/`, `/register`, `/terms`, `/privacy` unaffected | ✅ (all `200`) |

## Status

Complete. Not yet committed as of this writing — see git status before committing/pushing.
