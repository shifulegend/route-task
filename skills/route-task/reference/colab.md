# Colab (GPU / long CPU)

Source: your own infrastructure notes on Colab sessions. Read them before use. Never paste `~/.config/colab-cli/sessions.json` (holds tokens). Last check: no sessions active.

## Tools on the server
- Official `colab` CLI (v0.6.0): `colab new`, `colab sessions`, `colab status -s NAME`, `colab upload|download`, `colab install`, `colab exec -s NAME -f file.py --timeout N` (default 30 s), `colab run` (one script on a fresh VM, then releases it), `colab stop -s NAME`.
- `~/bin/colab-sessions.sh`: `-m cpu|gpu|both|all`, `-g T4,L4,G4,H100,A100`, `-p PREFIX`, `-d` Drive, `-n` dry run.
- PM2 `colab-keepalive` guard: restarts missing keep-alive processes; never creates or stops sessions.

## Use Colab when
1. A GPU is needed (CUDA kernel tests, GPU inference or benchmarks on T4/L4/G4/A100/H100): the Claude cloud VMs have no GPU (FulllAccess: 4 CPU, 16 GB).
2. A job outlasts a Claude cloud session or this host: several hours up to Colab's own limit (about 12 h free, 24 h paid).
3. Large model or dataset work needs about 100 GB of scratch disk and fast downloads (disk ~108-113 GB, wiped at session end; save results first).
4. Parallel comparisons across hardware (same script on T4 vs L4 vs A100), one prefixed session each.
5. A clean, quiet machine is needed for a repeatable CPU or GPU benchmark when the shared VMs are noisy.
6. A single throwaway Python script: `colab run`.
7. Project-zero model-load or tokens-per-second checks at sizes that do not fit in this host's 1.9 GB RAM.

## Do NOT use Colab when
- The data is private (bank, tax, ERP, personal mail, credentials): it runs on the owner's Google account and leaves the machine.
- The job needs a Claude agent, git pushes, or the repo's own secrets: Colab only runs code. Use a cloud session for the agent and Colab only for the compute.
- A plain build or test fits GitHub CI or the FulllAccess cloud VM (cheaper, no compute units).
- It needs a long-lived service, root-level system changes, or anything that must survive the session.

## Rules
- Name sessions `RS-<task>-<date>` (prefix `-p`); log each in `~/.claude/state/rs-ledger.md` as kind `colab` with its result location.
- Ask or check the compute-unit cost first; every running session spends units. Dry run with `-n` before creating GPU sessions.
- The keep-alive guard is why sessions do not end by themselves. Finish in this order: `colab download` the result to the server, verify it (hash or test), `colab stop -s NAME`, mark the ledger line archived. Only stop sessions this task created.
- Drive mounting needs a browser consent link per session: avoid it for unattended work; use `upload`/`download`.
- Colab sessions fall under the same max-4 limit as children.
- Not yet exercised by a real task: the first use must record a line in lessons.md (what worked, cost, what broke).
