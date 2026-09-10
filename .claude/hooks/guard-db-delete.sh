#!/usr/bin/env bash
# PreToolUse hook: block any Bash/PowerShell command that would delete expense_tracker.db.
input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty')
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')

case "$tool" in
  Bash|PowerShell) ;;
  *) exit 0 ;;
esac

# Only look at commands that reference the db file at all.
if ! printf '%s' "$cmd" | grep -qiE 'expense_tracker\.db'; then
  exit 0
fi

# Block if a deletion verb appears as its own command/token in the same line
# (rm, del, erase, unlink, rd, rmdir, Remove-Item/ri, git rm).
if printf '%s' "$cmd" | grep -qiE '(^|[;&|(]|[[:space:]])(rm|del|erase|unlink|rd|rmdir|remove-item|ri|git[[:space:]]+rm)([[:space:]]|$)'; then
  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked by protective hook: deleting expense_tracker.db is not allowed."}}
EOF
fi

exit 0
