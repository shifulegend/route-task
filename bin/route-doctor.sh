#!/bin/sh
# route-doctor: check every dependency of route-task and say how to fix what is missing. Read-only. Exit 0 always.
H="$HOME/.claude"; ok(){ printf '  [ok]      %s\n' "$1"; }; no(){ printf '  [MISSING] %s\n            fix: %s\n' "$1" "$2"; }; opt(){ printf '  [optional] %s\n             %s\n' "$1" "$2"; }
echo "REQUIRED"
command -v node >/dev/null && ok "node $(node -v) (cheap-llm, agy-ask)" || no "node 18+" "install Node.js from nodejs.org or your package manager"
command -v python3 >/dev/null && ok "python3 (rs-guard, test harness)" || no "python3" "install Python 3"
command -v claude >/dev/null && ok "claude CLI" || no "claude CLI" "install Claude Code: https://claude.com/claude-code"
for f in skills/route-task/SKILL.md agents/haiku-helper.md agents/sonnet-helper.md bin/cheap-llm.mjs bin/rs-guard.py; do [ -e "$H/$f" ] && ok "~/.claude/$f" || no "~/.claude/$f" "run: sh install.sh from the repo"; done
grep -q "Model routing" "$H/CLAUDE.md" 2>/dev/null && ok "routing rules in ~/.claude/CLAUDE.md" || no "always-on routing rules" "append config/CLAUDE.routing.md to ~/.claude/CLAUDE.md"
grep -q "rs-guard" "$H/settings.json" 2>/dev/null && ok "rs-guard hook in settings.json" || no "rs-guard / rs-start hooks" "merge config/settings.hooks.example.json into ~/.claude/settings.json (use the update-config skill)"
[ -s "$H/state/rs-cloud-envs.json" ] && ok "cloud environments listed (rs-cloud-envs.json)" || no "cloud environment ids" "copy config/rs-cloud-envs.example.json to ~/.claude/state/rs-cloud-envs.json and put your own ids (list them with the list_environments tool in Claude Code)"
echo "FREE-MODEL BACKEND (D1; without it the skill uses Haiku, saving less)"
B=none; [ -f "$H/cheap-llm.json" ] && B=config
if [ "$B" = config ] || [ -n "$OMNIROUTE_API_KEY$CHEAP_LLM_API_KEY" ] || [ -f "$HOME/.omniroute/.env" ]; then
  U=$(node -e 'try{const c=JSON.parse(require("fs").readFileSync(process.env.HOME+"/.claude/cheap-llm.json","utf8"));console.log(c.base_url||"")}catch{console.log("")}' 2>/dev/null); U=${U:-${OMNIROUTE_BASE_URL:-http://127.0.0.1:20128/v1}}
  if command -v curl >/dev/null && curl -s -m 4 -o /dev/null "$U/models"; then ok "backend answers at $U"; else no "backend not reachable at $U" "start OmniRoute, or fix base_url in ~/.claude/cheap-llm.json"; fi
else no "no free-model backend configured" "choose one: (1) install OmniRoute and set OMNIROUTE_API_KEY, or (2) copy config/cheap-llm.example.json to ~/.claude/cheap-llm.json with a provider base_url, api_key_env and model ids (Groq, Gemini, OpenRouter, Mistral, OpenAI...). Or skip: Haiku helper is used instead"; fi
echo "OPTIONAL"
command -v gh >/dev/null && ok "gh (GitHub CI, R1)" || opt "gh not found" "needed only to run builds/tests on GitHub Actions: https://cli.github.com then gh auth login"
command -v agy >/dev/null && ok "agy (stronger non-private model via agy-ask)" || opt "agy not found" "Google Antigravity CLI; needs your own Google account. Skip if you do not use it"
command -v colab >/dev/null && ok "colab CLI (R3: GPU / multi-hour jobs)" || opt "colab CLI not found" "needed only for GPU or multi-hour jobs; install the official Colab CLI and sign in"
{ [ "$CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" = 1 ] || grep -q EXPERIMENTAL_AGENT_TEAMS "$H/settings.json" 2>/dev/null; } && ok "agent teams enabled" || opt "agent teams off" "needed only for parallel cross-checking workers: set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 in settings.json env"
echo; echo "Fix the MISSING lines, then run this again. Optional lines only unlock extra routes."
