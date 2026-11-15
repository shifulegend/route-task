#!/bin/sh
# SessionStart: remind about open remote sessions and the protocol.
L="$HOME/.claude/state/rs-ledger.md"
echo "Remote sessions: before create_session or remote work read ~/.claude/skills/route-task/SKILL.md (Remote-session protocol)."
if [ -f "$L" ]; then
  O=$(grep -E '\| (running|done|failed|needs-owner-archive) \|' "$L")
  [ -n "$O" ] && { echo "Open remote sessions in ledger (sweep/archive when result is saved):"; echo "$O"; }
fi
exit 0
