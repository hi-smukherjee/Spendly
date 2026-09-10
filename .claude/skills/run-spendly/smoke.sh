#!/usr/bin/env bash
# Smoke-test for Spendly (Flask app).
#
# Starts the dev server, logs in as the seeded demo user, drives the Edit
# Expense flow end-to-end (load form -> submit change -> verify on
# /profile -> revert), checks a validation error path, then shuts the
# server down. Prints PASS/FAIL and exits non-zero on failure.
#
# Run from anywhere; it cd's to the repo root itself. Requires Git Bash
# (this repo is developed on Windows — see .claude/skills/run-spendly/SKILL.md).
#
# Usage:
#   bash .claude/skills/run-spendly/smoke.sh            # full smoke test, stops server after
#   bash .claude/skills/run-spendly/smoke.sh --keep-up   # leaves the server running afterwards
set -uo pipefail

KEEP_UP=0
[ "${1:-}" = "--keep-up" ] && KEEP_UP=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT" || exit 1

PORT=5001
BASE="http://localhost:$PORT"
LOG="$(mktemp -d)/spendly_run.log"
JAR="$(mktemp -d)/cookies.txt"
WORKDIR="$(mktemp -d)"
STATUS=0

log()  { echo "[smoke] $*"; }
fail() { echo "[smoke] FAIL: $*"; STATUS=1; }

# --- helpers: pull one attribute value out of an HTML file with the venv's
# python (more reliable than multiline grep -P for this). ------------------
extract() {  # extract <file> <name-attr-regex>
  "$PY" - "$1" "$2" <<'EOF'
import re, sys
html = open(sys.argv[1], encoding="utf-8").read()
m = re.search(sys.argv[2], html)
print(m.group(1) if m else "")
EOF
}

stop_server() {
  local pid
  pid=$(netstat -ano | grep ":$PORT" | grep LISTENING | awk '{print $5}' | head -1)
  if [ -n "${pid:-}" ]; then
    log "stopping server (PID $pid, and its reloader children)"
    # Flask's debug-mode reloader forks a child process; taskkill's /T walks
    # the whole tree. NOTE the "//" — Git Bash rewrites a lone "/PID" as a
    # path, which breaks taskkill's argument parsing.
    taskkill //PID "$pid" //F //T >/dev/null 2>&1
  fi
}

# --- 1. venv -----------------------------------------------------------------
if [ ! -x "venv/Scripts/python.exe" ]; then
  log "no venv found — creating one and installing requirements"
  python -m venv venv || { echo "[smoke] FAIL: python not on PATH"; exit 1; }
  venv/Scripts/python.exe -m pip install -q -r requirements.txt
fi
PY="venv/Scripts/python.exe"

# --- 2. launch -----------------------------------------------------------------
log "starting app.py on :$PORT (log: $LOG)"
"$PY" app.py > "$LOG" 2>&1 &
up=0
for _ in $(seq 1 30); do
  if curl -s -o /dev/null "$BASE/"; then up=1; break; fi
  sleep 0.5
done
if [ "$up" -ne 1 ]; then
  fail "server never came up on :$PORT — log follows"
  cat "$LOG"
  exit 1
fi
log "server is up"

# --- 3. log in as the seeded demo user ----------------------------------------
curl -s -c "$JAR" -b "$JAR" "$BASE/login" -o "$WORKDIR/login.html"
TOKEN=$(extract "$WORKDIR/login.html" 'name="csrf_token" value="([^"]+)"')
curl -s -c "$JAR" -b "$JAR" -o "$WORKDIR/login_post.html" "$BASE/login" \
  --data-urlencode "email=demo@spendly.com" \
  --data-urlencode "password=demo123" \
  --data-urlencode "csrf_token=$TOKEN"
curl -s -c "$JAR" -b "$JAR" "$BASE/profile" -o "$WORKDIR/profile_before.html"
if grep -q "expense-amount" "$WORKDIR/profile_before.html"; then
  log "login OK, profile loaded"
else
  fail "login or profile load failed (check $WORKDIR/profile_before.html)"
fi

# --- 4. drive the Edit Expense flow on the first row --------------------------
EXPENSE_HREF=$(extract "$WORKDIR/profile_before.html" 'href="(/expenses/[0-9]+/edit)"')
if [ -z "$EXPENSE_HREF" ]; then
  fail "no expense rows found on /profile — nothing to edit"
else
  log "editing $EXPENSE_HREF"
  curl -s -c "$JAR" -b "$JAR" "$BASE$EXPENSE_HREF" -o "$WORKDIR/edit_get.html"

  ORIG_AMOUNT=$(extract "$WORKDIR/edit_get.html" 'name="amount"[^>]*value="([^"]+)"')
  ORIG_DATE=$(extract "$WORKDIR/edit_get.html" 'name="date"[^>]*value="([^"]+)"')
  ORIG_DESC=$(extract "$WORKDIR/edit_get.html" 'name="description"[^>]*value="([^"]*)"')
  # category isn't a plain value= match — it's whichever <option value="X" ...>
  # also carries the "selected" attribute:
  ORIG_CATEGORY=$("$PY" - "$WORKDIR/edit_get.html" <<'EOF'
import re, sys
html = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'<option value="([^"]+)"\s*\n?\s*selected>', html)
print(m.group(1) if m else "")
EOF
)
  EDIT_TOKEN=$(extract "$WORKDIR/edit_get.html" 'name="csrf_token" value="([^"]+)"')

  if [ -z "$ORIG_AMOUNT" ] || [ -z "$EDIT_TOKEN" ] || [ -z "$ORIG_CATEGORY" ]; then
    fail "could not parse the edit form (amount='$ORIG_AMOUNT' category='$ORIG_CATEGORY' token='$EDIT_TOKEN')"
  else
    log "original values: amount=$ORIG_AMOUNT category=$ORIG_CATEGORY date=$ORIG_DATE description='$ORIG_DESC'"

    NEW_AMOUNT="99.99"
    NEW_DESC="$ORIG_DESC (smoke-tested)"
    curl -s -c "$JAR" -b "$JAR" -o "$WORKDIR/edit_post.html" -D "$WORKDIR/edit_post_headers.txt" \
      "$BASE$EXPENSE_HREF" \
      --data-urlencode "amount=$NEW_AMOUNT" \
      --data-urlencode "category=$ORIG_CATEGORY" \
      --data-urlencode "date=$ORIG_DATE" \
      --data-urlencode "description=$NEW_DESC" \
      --data-urlencode "csrf_token=$EDIT_TOKEN"

    if grep -q "^HTTP.*302" "$WORKDIR/edit_post_headers.txt" && grep -qi "profile" "$WORKDIR/edit_post_headers.txt"; then
      log "edit POST redirected to /profile as expected"
    else
      fail "edit POST did not redirect to /profile — see $WORKDIR/edit_post_headers.txt"
    fi

    curl -s -c "$JAR" -b "$JAR" "$BASE/profile" -o "$WORKDIR/profile_after.html"
    if grep -qF "$NEW_AMOUNT" "$WORKDIR/profile_after.html" && grep -qF "$NEW_DESC" "$WORKDIR/profile_after.html"; then
      log "profile page reflects the edit (amount + description updated)"
    else
      fail "profile page does not show the updated amount/description"
    fi

    # --- 5. validation: a bad amount should re-render the form, not save ------
    curl -s -c "$JAR" -b "$JAR" "$BASE$EXPENSE_HREF" -o "$WORKDIR/edit_get2.html"
    TOKEN2=$(extract "$WORKDIR/edit_get2.html" 'name="csrf_token" value="([^"]+)"')
    curl -s -c "$JAR" -b "$JAR" "$BASE$EXPENSE_HREF" -o "$WORKDIR/edit_invalid.html" \
      --data-urlencode "amount=not-a-number" \
      --data-urlencode "category=$ORIG_CATEGORY" \
      --data-urlencode "date=$ORIG_DATE" \
      --data-urlencode "description=should not save" \
      --data-urlencode "csrf_token=$TOKEN2"
    if grep -qi "Amount must be a number" "$WORKDIR/edit_invalid.html"; then
      log "validation error path OK (non-numeric amount rejected)"
    else
      fail "invalid amount did not produce the expected validation error"
    fi

    # --- 6. revert the row back to its original values -------------------------
    curl -s -c "$JAR" -b "$JAR" "$BASE$EXPENSE_HREF" -o "$WORKDIR/edit_get3.html"
    TOKEN3=$(extract "$WORKDIR/edit_get3.html" 'name="csrf_token" value="([^"]+)"')
    curl -s -c "$JAR" -b "$JAR" -o /dev/null "$BASE$EXPENSE_HREF" \
      --data-urlencode "amount=$ORIG_AMOUNT" \
      --data-urlencode "category=$ORIG_CATEGORY" \
      --data-urlencode "date=$ORIG_DATE" \
      --data-urlencode "description=$ORIG_DESC" \
      --data-urlencode "csrf_token=$TOKEN3"
    curl -s -c "$JAR" -b "$JAR" "$BASE/profile" -o "$WORKDIR/profile_reverted.html"
    if grep -qF "$ORIG_AMOUNT" "$WORKDIR/profile_reverted.html"; then
      log "reverted the row back to its original values"
    else
      fail "revert did not take — check the demo data by hand"
    fi
  fi
fi

# --- 7. stop -------------------------------------------------------------------
if [ "$KEEP_UP" -eq 1 ]; then
  log "--keep-up passed: leaving the server running at $BASE"
else
  stop_server
fi

if [ "$STATUS" -eq 0 ]; then
  echo "[smoke] PASS"
else
  echo "[smoke] one or more checks FAILED — see above and $WORKDIR"
fi
exit "$STATUS"
