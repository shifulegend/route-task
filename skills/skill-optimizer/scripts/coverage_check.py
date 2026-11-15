#!/usr/bin/env python3
"""Check a skill rewrite lost nothing. Usage: coverage_check.py OLD_FILE SKILL_DIR
Every backticked token and number in OLD_FILE must appear somewhere in SKILL_DIR/SKILL.md + SKILL_DIR/**/*.md.
Also prints sizes and the description length. Exit 1 if any token or number is missing."""
import re, sys, pathlib

old_path, skill_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
old = old_path.read_text()
files = [skill_dir / "SKILL.md"] + sorted(p for p in skill_dir.rglob("*.md") if p.name != "SKILL.md")
new = "\n".join(p.read_text() for p in files)
norm = lambda s: re.sub(r"\s+", " ", s.lower())
N = norm(new)

ticks = sorted(set(re.findall(r"`([^`\n]+)`", old)))
miss = [t for t in ticks if norm(t) not in N]
nums = sorted(set(re.findall(r"(?<![\w.])\d[\d.,:-]*\d|\b\d\b", old)))
nmiss = [n for n in nums if n not in new]
print(f"backticked tokens: {len(ticks)}, missing: {len(miss)}")
for m in miss:
    print("  MISSING", m)
print(f"numbers: {len(nums)}, missing: {len(nmiss)}", nmiss)
ow = set(re.findall(r"[a-z][a-z_-]{5,}", old.lower()))
nw = set(re.findall(r"[a-z][a-z_-]{5,}", new.lower()))
print("distinct words only in old (review by hand):", " ".join(sorted(ow - nw)))
print()
for p in files:
    t = p.read_text()
    print(f"{str(p.relative_to(skill_dir)):36} lines {len(t.splitlines()):4} words {len(t.split()):5} ~tokens {len(t)//4:5}")
print(f"{'OLD':36} lines {len(old.splitlines()):4} words {len(old.split()):5} ~tokens {len(old)//4:5}")
d = re.search(r"^description: (.*)$", (skill_dir / "SKILL.md").read_text(), re.M)
print("description chars:", len(d.group(1)) if d else "MISSING")
sys.exit(1 if miss or nmiss else 0)
