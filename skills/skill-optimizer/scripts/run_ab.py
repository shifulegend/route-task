#!/usr/bin/env python3
"""A/B runner: every scenario with and without a skill, via `claude -p` (stream-json).
Usage: run_ab.py SCENARIOS.json OUTDIR --skill NAME [--only ID,ID] [--model M] [--arms with,without,rules]
                 [--repeat N] [--budget USD] [--claude-args "..."] [--work-root DIR]
Writes OUTDIR/runs/<id>-<arm>.json (repeat 2 and up: <id>-<arm>.r2.json) and the raw stream next to it
(<tag>.raw.jsonl.gz). Resumable: finished runs are skipped.
Work folders live under --work-root (default: the system temp folder), never under ~/.claude and never in a path
holding the skill name, so a skill-less arm cannot find the skill through a parent folder.
Scenario field allow_if {"LABEL": "regex"}: in plan mode a forbidden route is accepted when every ROUTE line of that
label matches the regex (for example an outside benchmark that says it uses made-up data).
Arms: 'without' = isolated config dir holding only the credentials link (no skill, no CLAUDE.md, no helper agents);
      'rules'   = + CLAUDE.md and helper agents, no skill (shows what the skill itself adds);
      'with'    = + the skill.
Each record holds tokens and cost per model, helper-agent calls, and free-model calls read from ~/.claude/routing.log.
cost_norm = billed cost with later-turn cache misses of the main model re-priced as hits (removes cache luck between runs).
--budget stops before a run once the cost of all runs in OUTDIR reaches it.
Runs one at a time (host has about 1.9 GB RAM)."""
import argparse, gzip, hashlib, json, os, pathlib, re, shlex, shutil, subprocess, tempfile, time

HOME = pathlib.Path.home()
ap = argparse.ArgumentParser()
ap.add_argument("scenarios"); ap.add_argument("outdir")
ap.add_argument("--skill", required=True)
ap.add_argument("--only", default="")
ap.add_argument("--model", default="claude-sonnet-5-5")
ap.add_argument("--arms", default="with,without")
ap.add_argument("--repeat", type=int, default=1)
ap.add_argument("--budget", type=float, default=0)
ap.add_argument("--claude-args", default="")
ap.add_argument("--work-root", default="")
a = ap.parse_args()

out = pathlib.Path(a.outdir).resolve(); runs = out / "runs"; runs.mkdir(parents=True, exist_ok=True)
S = json.load(open(a.scenarios))
fixtures = pathlib.Path(S["fixtures"]).expanduser()
suffix = S["plan_suffix"]
LOG = HOME / ".claude/routing.log"
skill_dir = HOME / ".claude/skills" / a.skill
stamp = hashlib.sha1((skill_dir / "SKILL.md").read_bytes() + (HOME / ".claude/CLAUDE.md").read_bytes()).hexdigest()[:8]
fresh = set()
work_root = pathlib.Path(a.work_root or tempfile.gettempdir()).resolve() / ("ab-work-" + hashlib.sha1(str(out).encode()).hexdigest()[:8])
assert a.skill not in str(work_root) and not str(work_root).startswith(str(HOME / ".claude")), "work root must be outside ~/.claude and must not name the skill"


def make_cfg(arm):
    """Rebuilt once per invocation so an edited skill is always the one tested."""
    d = out / f"cfg-{arm}"
    if arm in fresh:
        return d
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    os.symlink(HOME / ".claude/.credentials.json", d / ".credentials.json")
    json.dump({"hasCompletedOnboarding": True}, open(d / ".claude.json", "w"))
    # syncClaudeAiSkills off: the background download of the account's claude.ai skills lands in a random turn of a
    # random run and adds about 3,200 tokens there (measured 2026-11-13), which is luck, not the skill under test.
    json.dump({"permissions": {"defaultMode": "bypassPermissions"}, "skipDangerousModePermissionPrompt": True,
               "syncClaudeAiSkills": False}, open(d / "settings.json", "w"))
    if arm in ("with", "rules"):
        shutil.copy(HOME / ".claude/CLAUDE.md", d / "CLAUDE.md")
        shutil.copytree(HOME / ".claude/agents", d / "agents")
    if arm == "with":
        shutil.copytree(skill_dir, d / "skills" / a.skill)
    fresh.add(arm)
    return d


def labels_from_tools(events):
    found, skill_used, tools, helpers = set(), False, 0, {}
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []):
            if c.get("type") != "tool_use":
                continue
            n, i = c.get("name", ""), c.get("input", {})
            tools += 1
            if n == "Skill":
                sk = str(i.get("skill", ""))
                skill_used = skill_used or sk == a.skill or sk.endswith(":" + a.skill)
            elif n == "Read" and f"skills/{a.skill}/" in i.get("file_path", ""):
                skill_used = True
            elif n in ("Agent", "Task"):
                st = i.get("subagent_type", "") or "other"
                helpers[st] = helpers.get(st, 0) + 1
                found.add({"haiku-helper": "HAIKU", "sonnet-helper": "SONNET"}.get(st, "AGENT"))
            elif n == "Bash":
                cmd = i.get("command", "")
                skill_used = skill_used or f"skills/{a.skill}/" in cmd
                found.add("CHEAP" if "cheap-llm" in cmd else "AGY" if "agy-ask" in cmd
                          else "COLAB" if "colab " in cmd else "SCRIPT")
            elif "create_session" in n:
                found.add("CLOUD")
            elif "Team" in n:
                found.add("TEAM")
    if not found & {"CHEAP", "AGY", "HAIKU", "SONNET", "AGENT", "CLOUD", "COLAB", "TEAM"}:
        found.add("ME")
    return found, skill_used, tools, helpers


def labels_from_plan(text):
    return set(re.findall(r"^ROUTE\s+([A-Z]+)\s*\|", text or "", re.M))


def grade(sc, found, text=""):
    ok_expect = all(any(alt in found for alt in need.split("|")) for need in sc.get("expect", []))
    bad = set(sc.get("forbid", [])) & found
    for lab, rx in (sc.get("allow_if") or {}).items():
        lines = re.findall(rf"^ROUTE\s+{lab}\s*\|.*$", text or "", re.M)
        if lab in bad and lines and all(re.search(rx, ln, re.I) for ln in lines):
            bad.discard(lab)
    return ok_expect and not bad


def log_lines():
    return LOG.read_text().splitlines() if LOG.exists() else []


def free_calls(new):
    """Free-model work (cost counted as 0): calls and sizes, from the routing log lines added during the run."""
    f = {"calls": 0, "cheap": 0, "agy": 0, "in_bytes": 0, "out_bytes": 0, "models": []}
    for ln in new:
        m = re.search(r"(cheap-llm|agy-ask) model=(\S+) ok=true in=(\d+)B out=(\d+)B", ln)
        if m:
            f["calls"] += 1; f["cheap" if m[1] == "cheap-llm" else "agy"] += 1
            f["in_bytes"] += int(m[3]); f["out_bytes"] += int(m[4]); f["models"].append(m[2])
    return f


def spent():
    t = 0.0
    for f in runs.glob("*.json"):
        try:
            t += json.load(open(f)).get("cost_usd") or 0
        except ValueError:
            pass
    return t


only = set(filter(None, a.only.split(",")))
for sc in S["scenarios"]:
    if only and sc["id"] not in only:
        continue
    for arm in a.arms.split(","):
        for rep in range(1, a.repeat + 1):
            tag = f"{sc['id']}-{arm}" + (f".r{rep}" if rep > 1 else "")
            rf = runs / f"{tag}.json"
            if rf.exists():
                continue
            if a.budget and spent() >= a.budget:
                print(f"BUDGET STOP: ${spent():.2f} spent, limit ${a.budget:.2f}", flush=True)
                raise SystemExit(3)
            cfg = make_cfg(arm)
            work = work_root / tag
            shutil.rmtree(work, ignore_errors=True)
            if "files" in sc:      # copy only what the task needs
                work.mkdir(parents=True)
                for name in sc["files"]:
                    src = fixtures / name
                    (shutil.copytree if src.is_dir() else shutil.copy)(src, work / name)
            else:
                shutil.copytree(fixtures, work)
            plan = sc["mode"] == "plan"
            prompt = sc["prompt"] + ("\n\n" + suffix if plan else "")
            cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", a.model,
                   "--permission-mode", "bypassPermissions", "--no-session-persistence",
                   "--max-budget-usd", str(sc.get("cap", 0.30 if plan else 1.50)),
                   "--disallowed-tools", "mcp__claude-code-remote__create_session"] + shlex.split(a.claude_args)
            if arm != "with":      # a skill-less arm must not find the skill by browsing the real home folder
                cmd += ["--disallowed-tools", f"Read(//{str(HOME).lstrip('/')}/.claude/skills/**)"]
            env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg))
            before = len(log_lines())
            t0 = time.time()
            try:
                p = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=sc.get("timeout", 900))
                raw = p.stdout
            except subprocess.TimeoutExpired as ex:
                raw = (ex.stdout or b"").decode() if isinstance(ex.stdout, bytes) else (ex.stdout or "")
            free = free_calls(log_lines()[before:])
            with gzip.open(runs / f"{tag}.raw.jsonl.gz", "wt") as fh:
                fh.write(raw)
            events = []
            for line in raw.splitlines():
                try:
                    events.append(json.loads(line))
                except ValueError:
                    pass
            res = next((e for e in reversed(events) if e.get("type") == "result"), {})
            mu = res.get("modelUsage") or {}
            models = {m: {"in": v.get("inputTokens", 0), "out": v.get("outputTokens", 0),
                          "cache_read": v.get("cacheReadInputTokens", 0), "cache_write": v.get("cacheCreationInputTokens", 0),
                          "cost": v.get("costUSD", 0)} for m, v in mu.items()}
            if mu:
                tokens = sum(v["in"] + v["out"] + v["cache_read"] + v["cache_write"] for v in models.values())
            else:
                u = res.get("usage", {})
                tokens = sum(u.get(k, 0) for k in ("input_tokens", "output_tokens",
                                                   "cache_read_input_tokens", "cache_creation_input_tokens"))
            # Cache-neutral cost: a cache miss on a later main-model call is luck, not routing, so re-price it as a hit.
            seen, calls = set(), []
            for e in events:
                m = e.get("message", {})
                if e.get("type") == "assistant" and not e.get("parent_tool_use_id") and m.get("id") not in seen:
                    seen.add(m.get("id")); u = m.get("usage", {})
                    cw = u.get("cache_creation_input_tokens", 0)
                    calls.append((u.get("input_tokens", 0) + cw + u.get("cache_read_input_tokens", 0), cw))
            excess = sum(max(0, cw - max(0, c - calls[i][0])) for i, (c, cw) in enumerate(calls[1:]))
            mm = models.get(next((m for m in models if m.startswith(a.model)), ""), None)
            cost_norm = res.get("total_cost_usd")
            if mm and cost_norm is not None:
                unit = mm["cost"] / max(1, mm["in"] + 1.25 * mm["cache_write"] + 0.1 * mm["cache_read"] + 5 * mm["out"])
                cost_norm = round(cost_norm - excess * 1.15 * unit, 6)
            found, skill_used, tools, helpers = labels_from_tools(events)
            init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
            skill_listed = any(str(x) == a.skill or str(x).endswith(":" + a.skill) for x in init.get("skills", []))
            if plan:
                found = labels_from_plan(res.get("result", ""))
            out_ok, note = None, ""
            if sc.get("verify") and not plan:
                v = subprocess.run(["bash", "-c", sc["verify"]], cwd=work, capture_output=True, text=True)
                out_ok, note = v.returncode == 0, (v.stdout or v.stderr).strip()[-200:]
            rec = {"id": sc["id"], "arm": arm, "rep": rep, "group": sc["group"], "mode": sc["mode"],
                   "scorecard": sc.get("scorecard"), "kind": sc.get("kind"), "size": sc.get("size"),
                   "prompt": sc["prompt"], "expected": sc.get("expect", []), "forbid": sc.get("forbid", []),
                   "routes": sorted(found), "route_ok": grade(sc, found, res.get("result", "") if plan else ""), "output_ok": out_ok, "verify_note": note,
                   "skill_used": skill_used, "skill_listed": skill_listed, "tool_calls": tools, "helpers": helpers, "free": free,
                   "tokens": tokens, "models": models, "cost_usd": res.get("total_cost_usd"), "cost_norm": cost_norm,
                   "main_calls": len(calls), "cache_miss_tokens": excess, "turns": res.get("num_turns"),
                   "seconds": round(time.time() - t0, 1), "is_error": res.get("is_error", True), "stamp": stamp,
                   "answer": (res.get("result") or "")[:1500]}
            json.dump(rec, open(rf, "w"), indent=1)
            if plan or sc.get("drop_work"):
                shutil.rmtree(work, ignore_errors=True)
            print(f"{tag:14} routes={sorted(found)} route_ok={rec['route_ok']} out_ok={out_ok} skill={skill_used} "
                  f"helpers={helpers} free={free['calls']} tokens={tokens} cost={rec['cost_usd']} norm={cost_norm} {rec['seconds']}s", flush=True)
