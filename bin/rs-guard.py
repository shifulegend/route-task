#!/usr/bin/env python3
"""PreToolUse guard for mcp__claude-code-remote__create_session (route-task skill, Remote-session protocol).
Blocks (exit 2, reason on stderr) unless the request follows the owner's rules."""
import json, sys, os, re
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # never block on a parse problem
i = d.get("tool_input") or {}
errs = []
title = i.get("title") or ""
tags = i.get("tags") or []
prompt = i.get("prompt") or ""
if not title.startswith("RS/"):
    errs.append("title must start with 'RS/<area>/<task>/<YYYY-MM-DD>'")
# Allowed cloud environments: {environment_id: name}. Put yours in ~/.claude/state/rs-cloud-envs.json (see config/rs-cloud-envs.example.json)
try:
    CLOUD = json.load(open(os.path.expanduser("~/.claude/state/rs-cloud-envs.json")))
except Exception:
    CLOUD = {}
if i.get("environment_id") not in CLOUD and "rs-local" not in tags:
    errs.append("environment_id must be a cloud environment (one listed in ~/.claude/state/rs-cloud-envs.json): the default 'bridge' environment runs on THIS machine and offloads nothing. Tag 'rs-local' only for light jobs that must use this host")
if "rs-managed" not in tags:
    errs.append("tags must include 'rs-managed'")
if i.get("permission_mode") != "auto":
    errs.append("set permission_mode to 'auto' (a bare child runs in default mode and raises approval cards)")
if not re.search(r"deadline", prompt, re.I) or not re.search(r"(hard stop|no extra runs|stop after)", prompt, re.I):
    errs.append("prompt must state a deadline and a hard stop ('no extra runs')")
if len(prompt.split()) > 600:
    errs.append("prompt over 600 words: point to files instead of pasting content")
led = os.path.expanduser("~/.claude/state/rs-ledger.md")
try:
    running = [l for l in open(led) if "| running |" in l]
    if len(running) >= 4:
        errs.append("4 children already running per ledger: finish/archive one first")
except OSError:
    pass
if errs:
    sys.stderr.write("route-task protocol (Remote-session protocol) blocked create_session:\n- " + "\n- ".join(errs) +
                     "\nAlso run get_session with no argument first: if permission_mode is plan, ask the owner to re-select Auto in the app.\n")
    sys.exit(2)
sys.exit(0)
