#!/bin/sh
# Install route-task into ~/.claude (copies; backs up files it would overwrite). Review config/ before merging.
set -e
D="$HOME/.claude"; B="$D/backups/route-task-$(date +%Y%m%d-%H%M%S)"; H=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$D/skills" "$D/agents" "$D/bin" "$D/state" "$B"
for p in skills/route-task skills/skill-optimizer; do [ -e "$D/$p" ] && cp -r "$D/$p" "$B/" && rm -rf "$D/$p"; cp -r "$H/$p" "$D/$p"; done
for f in agents/*.md bin/*; do [ -e "$D/$f" ] && cp "$D/$f" "$B/"; cp "$H/$f" "$D/$f"; done
chmod +x "$D"/bin/*
[ -f "$D/state/rs-ledger.md" ] || printf '# Remote-session ledger\n# format: <session_id> | <name prefix> | <purpose> | <status> | <result location>\n' > "$D/state/rs-ledger.md"
echo "Installed. Now: (1) append config/CLAUDE.routing.md to ~/.claude/CLAUDE.md, (2) merge config/settings.hooks.example.json into ~/.claude/settings.json, (3) copy config/rs-cloud-envs.example.json to ~/.claude/state/rs-cloud-envs.json with your ids. Backups: $B"
