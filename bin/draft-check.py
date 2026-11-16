#!/usr/bin/env python3
"""draft-check: cheap check for drafted text, one item per line as `key<TAB>text`.
usage: draft-check.py FILE [--max-chars 160] [--expect N]
A script finds the obvious faults (missing, empty, duplicate, too long, only repeats the key, filler phrases).
It then prints at most 3 lines for the main model to skim: flagged lines first, then lines spread across the file.
exit 0 = no faults, skim the 3 lines;  exit 1 = too many faults, redo the whole batch one rung up (never patch single items)."""
import sys, re
a = sys.argv[1:]
if not a: sys.exit(__doc__)
path = a[0]; mx = int(a[a.index('--max-chars') + 1]) if '--max-chars' in a else 160
expect = int(a[a.index('--expect') + 1]) if '--expect' in a else None
FILLER = re.compile(r"\b(as an ai|i cannot|i can't|sorry|todo|tbd|lorem|placeholder|here is|here's)\b", re.I)
rows = [l.rstrip('\n').split('\t', 1) for l in open(path, encoding='utf8', errors='replace') if l.strip()]
bad, seen = {}, {}
for n, r in enumerate(rows):
    k, t = (r[0], r[1].strip()) if len(r) == 2 else (r[0], '')
    why = []
    if not t: why.append('empty')
    if len(t) > mx: why.append('too long')
    if t and re.sub(r'\W+', '', t.lower()) == re.sub(r'\W+', '', k.lower().split(':')[-1]): why.append('repeats key')
    if FILLER.search(t): why.append('filler')
    if t and t.lower() in seen: why.append('duplicate of ' + seen[t.lower()])
    seen.setdefault(t.lower(), k)
    if why: bad[n] = why
missing = (expect - len(rows)) if expect is not None and len(rows) != expect else 0
picks = list(bad)[:3]
for i in (len(rows) // 2, 0, len(rows) - 1):          # then spread: middle, first, last
    if len(picks) < 3 and rows and i not in picks: picks.append(i)
print(f"items={len(rows)} flagged={len(bad)} missing={abs(missing)}")
for n in sorted(picks):
    print(f"SKIM {n + 1}: {'\t'.join(rows[n])[:240]}" + (f"   <- {', '.join(bad[n])}" if n in bad else ''))
sys.exit(1 if missing or len(bad) > max(1, len(rows) // 10) else 0)
