#!/usr/bin/env node
// agy-ask: send one text task to Google's official Antigravity CLI (agy -p) and print the answer. NON-PRIVATE TEXT ONLY.
// usage: agy-ask [--model gemini-3.8-flash-high|gemini-3.8-flash-medium|gemini-3.8-flash-low|claude-sonnet-4-6|claude-opus-4-6-thinking|gpt-oss-120b-medium] [--prompt "..."]   (stdin if no --prompt)
// exit: 0 ok | 3 failed or limit reached (use cheap-llm / haiku-helper instead) | 4 refused: input looks private
// Safety: runs in an empty temp dir (headless agy auto-denies any tool that needs permission), min 10 s between calls, max 30 calls/day (personal account: keep use low).
import fs from 'fs'; import os from 'os'; import path from 'path'; import { spawnSync } from 'child_process';

const PRIVATE = [
  /\b[A-Z]{5}[0-9]{4}[A-Z]\b/, /\b\d{4}\s?\d{4}\s?\d{4}\b/,
  /\b(?:a\/c|acct|account)\s*(?:no\.?|number|#)?\s*[:\-]?\s*\d{9,18}\b/i,
  /\b(?:IFSC|CVV|OTP|password|passwd|secret|api[_ -]?key|token)\b\s*[:=]/i,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/, /\b(?:sk-|gsk_|ghp_|AIza|xox[bp]-)[A-Za-z0-9_-]{16,}/,
  /\b(?:Form 26AS|ITR-?\d)\b/i,
];
const a = process.argv.slice(2); const opt = {};
for (let i = 0; i < a.length; i++) if (a[i].startsWith('--')) opt[a[i].slice(2)] = a[i + 1]?.startsWith('--') || a[i + 1] === undefined ? true : a[++i];
const MODELS = ['gemini-3.8-flash-high', 'gemini-3.8-flash-medium', 'gemini-3.8-flash-low', 'claude-sonnet-4-6', 'claude-opus-4-6-thinking', 'gpt-oss-120b-medium'];
const model = MODELS.includes(opt.model) ? opt.model : 'gemini-3.8-flash-high';
const prompt = typeof opt.prompt === 'string' ? opt.prompt : fs.readFileSync(0, 'utf8');
if (!prompt.trim()) { console.error('agy-ask: empty prompt'); process.exit(2); }
if (PRIVATE.some(r => r.test(prompt))) { console.error('agy-ask: REFUSED, input looks private (it would go to Google). Use haiku-helper/sonnet-helper or a script.'); process.exit(4); }

const home = os.homedir(); const stateFile = path.join(home, '.claude', 'agy-ask-state.json'); const logFile = path.join(home, '.claude', 'routing.log');
let st = {}; try { st = JSON.parse(fs.readFileSync(stateFile, 'utf8')); } catch {}
const today = new Date().toISOString().slice(0, 10);
if (st.date !== today) st = { date: today, count: 0, last: 0 };
if (st.count >= 30) { console.error('agy-ask: daily limit (30) reached'); process.exit(3); }
// Memory guard: agy starts a heavy background process. Refuse when this host is short of RAM (a small server can be OOM-killed).
const minFreeMb = Number(process.env.AGY_MIN_FREE_MB) || 450; const freeMb = Math.round(os.freemem() / 1048576);
if (freeMb < minFreeMb) { console.error(`agy-ask: only ${freeMb} MB free (< ${minFreeMb} MB), refusing so the host does not run out of memory`); process.exit(3); }
// One agy-ask at a time per host (stale lock after 5 min).
const lockFile = path.join(home, '.claude', 'agy-ask.lock');
try { if (Date.now() - fs.statSync(lockFile).mtimeMs > 300000) fs.unlinkSync(lockFile); } catch {}
try { fs.closeSync(fs.openSync(lockFile, 'wx')); } catch { console.error('agy-ask: another agy-ask is running on this host'); process.exit(3); }
process.on('exit', () => { try { fs.unlinkSync(lockFile); } catch {} });
const wait = 10000 - (Date.now() - st.last); if (wait > 0) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, wait);
st.count++; st.last = Date.now(); fs.writeFileSync(stateFile, JSON.stringify(st));

const bin = process.platform === 'win32' ? path.join(process.env.LOCALAPPDATA, 'agy', 'bin', 'agy.exe') : path.join(home, '.local', 'bin', 'agy');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'agy-ask-'));
const t0 = Date.now();
const r = spawnSync(bin, ['-p', prompt, '--model', model, '--print-timeout', '120s'], { cwd: dir, encoding: 'utf8', timeout: 150000 });
try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
const out = (r.stdout || '').replace(/\r/g, '').trim();
const ok = r.status === 0 && out && !/Please sign in|Error:/.test(out.slice(0, 200));
fs.appendFileSync(logFile, `${new Date().toISOString()} agy-ask model=${model} ok=${ok} in=${prompt.length}B out=${out.length}B ${((Date.now() - t0) / 1000).toFixed(0)}s\n`);
if (ok) { process.stdout.write(out + '\n'); console.error(`agy-ask: ${model}`); process.exit(0); }
console.error('agy-ask: failed ' + (r.stderr || out).slice(0, 150)); process.exit(3);
