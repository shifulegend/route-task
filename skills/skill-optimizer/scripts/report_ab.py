#!/usr/bin/env python3
"""Report from run_ab.py output, one scorecard per skill function.
Usage: report_ab.py OUTDIR "Title" [--baseline OLDDIR] [--notes FILE]
 baseline = earlier results whose 'without' arm is reused for plan scenarios (only where the prompt is the same);
 notes = text file, one caveat or finding per line, printed at the end of both reports. Arms that were not run are left out.
Scorecards: 1 model routing (the ONLY gain %, on cost_norm above the same arm's empty-task cost; free-model work counted as 0),
 2 privacy, 3 compute placement, 4 session rules, 5 split and categorise (pass/fail grids),
 6 overhead: what the always-on rules plus the skill listing add to an empty session, and whether the skill stays unloaded on light work.
Writes OUTDIR/report.md and OUTDIR/report.html."""
import json, glob, html, pathlib, sys, collections, statistics as st

a = sys.argv[1:]; out = pathlib.Path(a[0]); title = a[1]
base = pathlib.Path(a[a.index("--baseline") + 1]) if "--baseline" in a else None
notes = [l.strip() for l in open(a[a.index("--notes") + 1]) if l.strip()] if "--notes" in a else []
E = html.escape
def load(d):
    R = collections.defaultdict(lambda: collections.defaultdict(list))
    for f in sorted(glob.glob(str(d / "runs/*.json"))):
        r = json.load(open(f)); R[r["id"]][r["arm"]].append(r)
    return R
R = load(out); B = load(base) if base else {}
mean = lambda xs: sum(xs) / len(xs) if xs else None
cn = lambda r: r["cost_norm"] if r.get("cost_norm") is not None else (r.get("cost_usd") or 0)
def model_split(r):
    """(main-model cost, haiku cost) from per-model usage; everything else counted as main."""
    h = sum(v["cost"] for m, v in r["models"].items() if "haiku" in m)
    return cn(r) - h, h
ARMS = [arm for arm in ("without", "rules", "with") if any(arm in v for v in R.values())]
# ---- scorecard 6 / empty task
empty = collections.defaultdict(lambda: None, {arm: mean([cn(r) for r in R.get("Z0", {}).get(arm, [])]) for arm in ARMS})
empty_tok = collections.defaultdict(lambda: None, {arm: mean([r["tokens"] for r in R.get("Z0", {}).get(arm, [])]) for arm in ARMS})
# ---- scorecard 1
sc1 = [i for i in R if any(r.get("scorecard") == 1 for rs in R[i].values() for r in rs)]
order = {"small": 0, "medium": 1, "large": 2}
def key1(i):
    r = next(iter(R[i].values()))[0]; return (r["kind"], order.get(r["size"], 9))
sc1.sort(key=key1)
rows1 = []
for i in sc1:
    row = dict(id=i)
    for arm in ARMS:
        rs = R[i].get(arm, [])
        if not rs: continue
        first = rs[0]; row.update(kind=first["kind"], size=first["size"], prompt=first["prompt"])
        ex = mean([cn(r) for r in rs]) - (empty.get(arm) or 0)
        main, hk = zip(*[model_split(r) for r in rs])
        row[arm] = dict(n=len(rs), cost=mean([cn(r) for r in rs]), billed=mean([r["cost_usd"] or 0 for r in rs]), excess=max(ex, 0),
                        main=mean(main), haiku=mean(hk), free=mean([r["free"]["calls"] for r in rs]),
                        free_kb=mean([r["free"]["in_bytes"] + r["free"]["out_bytes"] for r in rs]) / 1000,
                        ok=sum(1 for r in rs if r["output_ok"]), routes=sorted({x for r in rs for x in r["routes"]}),
                        skill=sum(1 for r in rs if r["skill_used"]), tokens=mean([r["tokens"] for r in rs]),
                        turns=mean([r.get("main_calls") or r.get("turns") or 0 for r in rs]))
    rows1.append(row)
def gain(row, arm="with"):
    w, o = row.get(arm), row.get("without")
    if not (w and o) or o["excess"] < 0.003: return None
    return round((o["excess"] - w["excess"]) / o["excess"] * 100, 1)
def size_gain(sz):
    o = sum(r["without"]["excess"] for r in rows1 if r.get("size") == sz and "with" in r and "without" in r)
    w = sum(r["with"]["excess"] for r in rows1 if r.get("size") == sz and "with" in r and "without" in r)
    return None if o < 0.003 else round((o - w) / o * 100, 1)
# ---- scorecards 2-5: plan and session scenarios, with-arm now, baseline without-arm from older results
def grid(sc):
    g = []
    for i, arms in sorted(R.items(), key=lambda kv: (kv[0][0], int(kv[0][1:]) if kv[0][1:].isdigit() else 0)):
        rs = arms.get("with", [])
        if not rs or rs[0].get("scorecard") != sc: continue
        old = next((r for r in B.get(i, {}).get("without", []) + arms.get("without", []) if r["prompt"] == rs[0]["prompt"]), None)
        g.append(dict(id=i, prompt=rs[0]["prompt"], exp=" + ".join(rs[0]["expected"]), forbid=",".join(rs[0]["forbid"]),
                      now=rs[0]["route_ok"], routes=",".join(rs[0]["routes"]), old=None if old is None else old["route_ok"],
                      out=rs[0]["output_ok"], leak=bool(rs[0]["free"]["calls"]) if sc == 2 else None))
    return g
G = {sc: grid(sc) for sc in (2, 3, 4, 5)}
# privacy: also a leak if a free model was called in an executed private scenario
priv_fail = [g["id"] for g in G[2] if (not g["now"]) or g["leak"]]
# overhead and loading. Light work is meant to run on the always-on rules, so the skill should NOT load there (target 0).
light = [r for i in sc1 for r in R[i].get("with", [])]
light_loads = (sum(1 for r in light if r["skill_used"]), len(light))
heavy = [r for sc in (3, 4) for i, arms in R.items() for r in arms.get("with", []) if r.get("scorecard") == sc]
heavy_loads = (sum(1 for r in heavy if r["skill_used"]), len(heavy))
dirty = [r["id"] for arms in R.values() for r in arms.get("without", []) if r.get("skill_listed") or r.get("skill_used")]
ov = None if empty["with"] is None or empty["without"] is None else empty["with"] - empty["without"]
ov_tok = None if empty_tok["with"] is None or empty_tok["without"] is None else empty_tok["with"] - empty_tok["without"]
pair = [r for r in rows1 if "with" in r and "without" in r]
raw = {arm: sum(r[arm]["billed"] for r in pair) for arm in ("without", "with")}
raw_gain = None if not raw["without"] else round((raw["without"] - raw["with"]) / raw["without"] * 100, 1)
def raw_size(sz):
    o = sum(r["without"]["billed"] for r in pair if r.get("size") == sz); w = sum(r["with"]["billed"] for r in pair if r.get("size") == sz)
    return None if not o else round((o - w) / o * 100, 1)
mark = lambda b: "n/a" if b is None else ("PASS" if b else "FAIL")
f = lambda x, n=3: "–" if x is None else f"{x:.{n}f}"
# targets
mid = [gain(r) for r in rows1 if r.get("size") in ("medium", "large") and r.get("kind") != "reshape" and gain(r) is not None]
t1 = size_gain("medium"), size_gain("large"), size_gain("small")
ok_all = all(r["with"]["ok"] == r["with"]["n"] for r in rows1 if "with" in r)

arm_cols = [x for x in ARMS]
md = [f"# {title}", "", "Gain % exists only in scorecard 1 and is worked out on the cost above the empty-task cost of the same arm, on cache-neutral cost (`cost_norm`). Free-model work (OmniRoute, agy) is counted as 0.", "",
      "## 1. Model routing (light, not private)", "",
      "Empty-task cost (fixed start-up): " + ", ".join(f"{x} ${f(empty[x],4)}" for x in ARMS) + ".",
      f"Gain on cost above empty task: small {t1[2]}%, medium {t1[0]}%, large {t1[1]}%. Output checks in the with arm: {'all pass' if ok_all else 'SOME FAIL'}.",
      f"Raw billed totals over the {len(pair)} tasks run in both arms, start-up cost included: without ${f(raw['without'])}, with ${f(raw['with'])} ({raw_gain}%). By size: small {raw_size('small')}%, medium {raw_size('medium')}%, large {raw_size('large')}%.", "",
      "| ID | Kind | Size | Runs | Task | " + " | ".join(f"Cost over empty {x} $" for x in arm_cols) + " | Gain % | Billed without $ / with $ | Main turns without / with | Main $ / Haiku $ (with) | Free calls / KB (with) | Output ok (with / without) | Routes (with) | Routes (without) | Skill loaded |",
      "|---|---|---|---|---|" + "---|" * len(arm_cols) + "---|---|---|---|---|---|---|---|---|"]
for r in rows1:
    w, o = r.get("with"), r.get("without")
    md.append(f"| {r['id']} | {r.get('kind')} | {r.get('size')} | {w and w['n']} | {r.get('prompt','').replace('|','/')[:140]} | " + " | ".join(f(r.get(x) and r[x]['excess']) for x in arm_cols) + f" | {gain(r)} | "
              f"{f(o and o['billed'])} / {f(w and w['billed'])} | {f(o and o['turns'],1)} / {f(w and w['turns'],1)} | "
              f"{f(w and w['main'])} / {f(w and w['haiku'])} | {f(w and w['free'],1)} / {f(w and w['free_kb'],1)} | "
              f"{w and str(w['ok'])+'/'+str(w['n'])} / {o and str(o['ok'])+'/'+str(o['n'])} | {','.join(w['routes']) if w else ''} | {','.join(o['routes']) if o else ''} | {w and str(w['skill'])+'/'+str(w['n'])} |")
for sc, name in ((2, "Privacy (one leak fails the whole test)"), (3, "Compute placement (tokens for information only)"),
                 (4, "Remote-session rules"), (5, "Split and categorise")):
    md += ["", f"## {sc}. {name}", "", f"With the rules and skill: pass {sum(1 for g in G[sc] if g['now'])}/{len(G[sc])}; baseline without them (same prompt, where one exists): pass {sum(1 for g in G[sc] if g['old'])}/{sum(1 for g in G[sc] if g['old'] is not None)}.", "",
          "| ID | Task | Expected | Forbidden | Routes chosen | With | Baseline |", "|---|---|---|---|---|---|---|"]
    md += [f"| {g['id']} | {g['prompt'].replace('|','/')[:140]} | {g['exp']} | {g['forbid']} | {g['routes']} | {mark(g['now'])} | {mark(g['old'])} |" for g in G[sc]]
sec6 = [f"Empty task: " + ", ".join(f"{x} {f(empty_tok[x],0)} tokens / ${f(empty[x],4)}" for x in ARMS) + f". The always-on rules, helper descriptions and skill listing add {f(ov_tok,0)} tokens, ${f(ov,4)} per session.",
        f"Skill loaded on light tasks: {light_loads[0]}/{light_loads[1]} (target 0: light work runs on the always-on rules, loading the skill there only costs).",
        f"Skill loaded in placement and session scenarios: {heavy_loads[0]}/{heavy_loads[1]} (for information; the pass marks above are what counts).",
        "Baseline arm clean (skill neither listed nor loaded in any 'without' run): " + ("yes" if not dirty else "NO: " + ", ".join(dirty)),
        "Privacy leaks: " + (", ".join(priv_fail) if priv_fail else "none")]
md += ["", "## 6. Overhead", ""] + [f"- {x}" for x in sec6]
if notes:
    md += ["", "## Notes and limits", ""] + [f"- {x}" for x in notes]
(out / "report.md").write_text("\n".join(md))

# ---------- infographic ----------
def bars(items, w=480):
    """items: (label, main, haiku, gain_text); stacked main + haiku per arm pair not needed: one bar per arm."""
    mx = max([max(a, b) for _, a, b, _ in items] + [1e-9]); h = 28 * len(items) + 8; s = [f'<svg viewBox="0 0 {w+250} {h}" role="img" class="chart">']
    for k, (lab, a, b, g) in enumerate(items):
        y = 4 + k * 28
        s.append(f'<text x="0" y="{y+14}" class="lab">{E(lab)}</text>')
        s.append(f'<rect x="130" y="{y}" width="{max(1, b/mx*w):.0f}" height="11" class="bo"/>')
        s.append(f'<rect x="130" y="{y+12}" width="{max(1, a/mx*w):.0f}" height="11" class="bw"/>')
        s.append(f'<text x="{136+w}" y="{y+20}" class="lab">{E(g)}</text>')
    return "".join(s) + "</svg>"
items = [(f"{r['id']} {r.get('kind')} {r.get('size')}", r["with"]["excess"], r["without"]["excess"], f"{gain(r)}%" if gain(r) is not None else "–")
         for r in rows1 if "with" in r and "without" in r]
def gridhtml(sc):
    return "".join(f'<tr><td>{g["id"]}</td><td class="p">{E(g["prompt"][:100])}</td><td>{E(g["routes"])}</td>'
                   f'<td class="{"good" if g["now"] else "bad"}">{mark(g["now"])}</td><td class="{"good" if g["old"] else "bad"}">{mark(g["old"])}</td></tr>' for g in G[sc])
kpi = lambda v, l: f'<div class="kpi"><b>{v}</b><span>{l}</span></div>'
pc = lambda sc: f'{sum(1 for g in G[sc] if g["now"])}/{len(G[sc])}'
tbl = lambda sc, name: f'<h2>{sc}. {name}</h2><div class="card"><table><tr><th>ID</th><th>Task</th><th>Routes chosen</th><th>With</th><th>Baseline</th></tr>{gridhtml(sc)}</table></div>'
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill A/B Test Report</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--line:#e4e4de;--w:#2a7f62;--o:#c9a227;--good:#1f7a4d;--bad:#b3261e}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161614;--fg:#ecece6;--mut:#9a9a92;--card:#1f1f1c;--line:#34342f;--w:#4fb893;--o:#d9b84a;--good:#5fcf97;--bad:#f2766e}}}}
:root[data-theme="dark"]{{--bg:#161614;--fg:#ecece6;--mut:#9a9a92;--card:#1f1f1c;--line:#34342f;--w:#4fb893;--o:#d9b84a;--good:#5fcf97;--bad:#f2766e}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;padding:24px 16px}}
main{{max-width:980px;margin:auto}}h1{{font-size:26px;margin:0 0 4px}}h2{{font-size:18px;margin:32px 0 8px}}p.s{{color:var(--mut);margin:0 0 18px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}}
.kpi b{{display:block;font-size:24px}}.kpi span{{color:var(--mut);font-size:13px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;overflow-x:auto}}svg.chart{{width:100%;min-width:600px;height:auto}}
.lab{{fill:var(--fg);font-size:12px}}.bw{{fill:var(--w)}}.bo{{fill:var(--o)}}.key i{{display:inline-block;width:12px;height:12px;margin:0 6px 0 14px;border-radius:2px;vertical-align:-1px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}td.p{{min-width:220px}}ul{{margin:0;padding-left:18px}}li{{margin:4px 0}}.good{{color:var(--good);font-weight:600}}.bad{{color:var(--bad);font-weight:600}}
</style></head><body><main>
<h1>{E(title)}</h1><p class="s">One scorecard per skill function. Gain % only for model routing, on cost above the empty task; free models count as 0. A positive gain means cheaper with the rules and skill.</p>
<div class="kpis">{kpi(f"{t1[0]}% / {t1[1]}%","routing gain, medium / large")}{kpi(f"{t1[2]}%","routing gain, small (noise ±15%)")}
{kpi(f"{raw_gain}%","all tasks, raw billed cost")}{kpi(pc(2),"privacy pass")}{kpi(pc(3),"placement pass")}{kpi(pc(4),"session rules pass")}{kpi(pc(5),"split and categorise pass")}{kpi(f"${f(ov,3)}","always-on rules, per session")}{kpi(f"{light_loads[0]}/{light_loads[1]}","skill loads on light work (target 0)")}</div>
<h2>1. Model routing: Claude cost above the empty task</h2><div class="card"><div class="key"><i style="background:var(--w)"></i>with rules and skill<i style="background:var(--o)"></i>without</div>{bars(items)}</div>
{tbl(2,"Privacy")}{tbl(3,"Compute placement")}{tbl(4,"Remote-session rules")}{tbl(5,"Split and categorise")}
<h2>6. Overhead</h2><div class="card"><ul>{"".join(f"<li>{E(x)}</li>" for x in sec6)}</ul></div>
{('<h2>Notes and limits</h2><div class="card"><ul>' + "".join(f"<li>{E(x)}</li>" for x in notes) + '</ul></div>') if notes else ""}
<p class="s">Full prompts and per-run numbers are in report.md.</p></main></body></html>"""
(out / "report.html").write_text(page)
print(f"scorecard1 tasks {len(rows1)}; wrote {out/'report.md'} and {out/'report.html'}")
