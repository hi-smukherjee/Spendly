# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Spendly — a Flask expense tracker, structured as a step-by-step learning project. Comments like
`# Students will write this file in Step 1 — Database Setup` and routes returning
`"Logout — coming in Step 3"` mark intentionally unimplemented pieces; don't "fix" these into dead
ends without checking whether the placeholder is deliberate scaffolding for a later step.

## Commands

Windows, run from this directory (`expense-tracker/`):

```
venv\Scripts\activate
python app.py            # runs on http://localhost:5001, debug=True
pip install -r requirements.txt
```

There is no test suite yet, though `pytest` and `pytest-flask` are already in `requirements.txt` for
when one is added.

## Architecture

- **`app.py`** — single-file Flask app; all routes live here (no blueprints). Implemented routes
  (`/`, `/register`, `/login`, `/terms`, `/privacy`) render templates directly with no logic yet.
  Placeholder routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`,
  `/expenses/<id>/delete`) return plain strings and are expected to be built out in later steps.
- **`database/db.py`** — currently empty; intended to hold `get_db()` (SQLite connection with
  `row_factory` and foreign keys enabled), `init_db()` (create tables `IF NOT EXISTS`), and
  `seed_db()` (sample data). No ORM — raw SQLite via the stdlib `sqlite3` module is the intended
  approach.
- **Templates** (`templates/`) use Jinja2 inheritance from `base.html`, which defines the shared
  nav, footer, and a video modal (`#videoModal`) driven by `static/js/main.js` and opened via the
  `#getStartedBtn` nav link. Page templates override `{% block title %}` / `{% block content %}`.
- **Static assets** are plain CSS/JS, no build step or bundler — `static/css/style.css` and
  `static/js/main.js` are edited directly and referenced via `url_for('static', ...)`.

## Spec-driven development

Work through each step in this order: **spec → design → tasks → build → validate**. Don't jump
ahead to build before the spec and task breakdown for that step are settled.
