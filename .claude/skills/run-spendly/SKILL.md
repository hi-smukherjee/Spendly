---
name: run-spendly
description: Build, run, and drive Spendly (the Flask expense tracker). Use when asked to start Spendly, run the app, smoke-test a route (login, profile, edit expense), or verify a Flask/template change actually works end-to-end rather than just reading the diff.
---

Spendly is a single-file Flask app (`app.py`, Werkzeug dev server, `sqlite3` stdlib
storage, no build step, no JS framework). There's no meaningful GUI surface to click
through with a browser driver — drive it with
`.claude/skills/run-spendly/smoke.sh`, a `curl`-based smoke test that logs in as
the seeded demo user and walks a full request/response flow (session cookie +
CSRF token included).

All paths below are relative to the repo root (`expense-tracker/`).

## Prerequisites

This project is developed on Windows (see `CLAUDE.md`). You need:

- Python 3.11 on `PATH`
- Git Bash (ships with Git for Windows) — the driver is a bash script, run it
  through the `Bash` tool, not PowerShell

No OS packages are required — Flask + Werkzeug + stdlib `sqlite3`, nothing native.

## Setup

```bash
python -m venv venv
venv/Scripts/python.exe -m pip install -r requirements.txt
```

The driver does this automatically on first run if `venv/Scripts/python.exe`
is missing, so you normally don't need to run it by hand.

No env vars needed — `app.secret_key` is a hardcoded dev key
(`app.py:21`), and `init_db()` / `seed_db()` run automatically at import
time, so `expense_tracker.db` is created and seeded with a demo user the
first time anything imports `app.py`.

## Run (agent path)

```bash
bash .claude/skills/run-spendly/smoke.sh
```

This is a full round-trip smoke test, not just a liveness check:

1. Creates the venv if missing, then starts `venv/Scripts/python.exe app.py`
   on port 5001 in the background and polls until it responds.
2. Logs in as the seeded demo user (`demo@spendly.com` / `demo123`),
   handling the login form's CSRF token.
3. Reads `/profile`, takes the first expense row's `/expenses/<id>/edit`
   link, and GETs the edit form (checks it's pre-filled correctly).
4. POSTs an updated amount + description, follows the redirect to
   `/profile`, and confirms the new values actually appear in the table.
5. POSTs a non-numeric amount and confirms the server rejects it with a
   validation error instead of saving.
6. Reverts the row to its original values (so re-running the smoke test,
   or a human poking at `/profile` afterwards, sees the original demo
   data) and confirms the revert took.
7. Stops the server (see Gotchas — this needs `taskkill /T` because of the
   Werkzeug reloader).

Prints `[smoke] PASS` and exits 0 on success; on any failed check it prints
`[smoke] FAIL: <what>`, continues (so later steps still run/report), and
exits non-zero. Intermediate HTML/headers for each step are kept in a
`mktemp -d` workdir whose path is echoed alongside any failure — read those
files instead of re-running with extra debug output.

Pass `--keep-up` to leave the server running afterward instead of stopping
it (e.g. to keep poking `http://localhost:5001` by hand or with more
`curl` afterward):

```bash
bash .claude/skills/run-spendly/smoke.sh --keep-up
```

When you're done, stop it yourself (see Gotchas for why a plain `kill`
isn't enough):

```bash
PID=$(netstat -ano | grep ":5001" | grep LISTENING | awk '{print $5}' | head -1)
taskkill //PID "$PID" //F //T
```

### Driving other routes/flows

For anything beyond the built-in Edit Expense check — a new route, a
different form — copy the pattern from `smoke.sh` rather than writing curl
from scratch: get the page first to pull `csrf_token` out of the hidden
input (every POST-handling form in this app requires it, checked against
`session["csrf_token"]`), keep using the same `-c "$JAR" -b "$JAR"` cookie
jar across requests, and check the `Location` header / re-fetch the page to
confirm the change actually landed instead of trusting a 200/302 alone.

## Run (human path)

```
venv\Scripts\activate
python app.py
```

Opens on `http://localhost:5001`, `debug=True` (auto-reloads on file save).
Ctrl-C to stop — reliable in an interactive terminal; only the backgrounded
case needs the `taskkill /T` dance below.

## Test

No test suite exists yet (`pytest`/`pytest-flask` are in `requirements.txt`
for when one's added — see `CLAUDE.md`). `smoke.sh` is the closest thing to
one right now.

---

## Gotchas

- **Stopping the server needs the whole process tree, not just the PID you
  launched.** `app.run(debug=True, ...)` starts the Werkzeug reloader,
  which forks a child process that does the actual serving — the PID you
  get back from `"$PY" app.py &` is the parent, and a plain `kill`/
  `taskkill` on it leaves an orphaned child still listening on the port.
  Find the PID actually holding the port instead, and kill its tree:
  `netstat -ano | grep ":5001" | grep LISTENING | awk '{print $5}'` then
  `taskkill //PID "$pid" //F //T`.
- **`taskkill //PID`, not `/PID`.** Under Git Bash (MSYS), a bare `/PID`
  gets rewritten as a Windows path before `taskkill` ever sees it, and the
  command silently does the wrong thing. Doubling the slash (`//PID`,
  `//F`, `//T`) stops MSYS's path-conversion from touching it.
- **A backgrounded server outlives the bash command that started it.**
  Launching `"$PY" app.py &` inside a script, then letting that script's
  process exit, does *not* kill the server on this setup — it keeps
  listening on the port after the launching shell is gone. Convenient
  (nothing to keep the tool call open for), but it means you must
  explicitly stop it (see above) or it'll sit there for the rest of the
  session.
- **Every POST route on a form checks CSRF, and it's per-session, not
  per-page.** `session["csrf_token"]` is (re)issued on the matching GET
  (`/login`, `/expenses/<id>/edit`). Reusing a token from an earlier GET,
  or skipping the initial GET and just POSTing, gets you a silent-looking
  validation error (`error = "..."`) on a `200`, not an HTTP-level
  rejection — check the response body, not just the status code.
- **The category `<select>`'s selected option isn't a plain `value="..."`
  match.** Jinja renders it as `<option value="Food"\n    selected>` (the
  attribute and the `selected` keyword are on different lines from the
  `{% if %}` block's whitespace) — grepping for `value="..."` on its own
  will just grab the *first* `<option>` in the list (`Food`), not
  necessarily the expense's real category. Match the option that also
  contains `selected`, as `smoke.sh`'s `extract` helper does.

## Troubleshooting

- **`curl` loop in `smoke.sh` never breaks / times out around 15s**: check
  the log file path the script printed after "starting app.py" — usually
  a stale `expense_tracker.db` schema mismatch or a port already in use
  from a prior unstopped run (`netstat -ano | grep ":5001"`).
- **`[smoke] FAIL: login or profile load failed`**: almost always a stale
  or missing seeded user. Delete `expense_tracker.db` and re-run — `app.py`
  recreates and reseeds it (demo user `demo@spendly.com` / `demo123`) on
  next import.
