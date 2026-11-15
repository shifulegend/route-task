#!/usr/bin/env node
// cheap-llm: one-shot text job through the local OmniRoute (free/cheap models). NON-PRIVATE TEXT ONLY.
// usage: cheap-llm [--task default|fast|code|long|reason] [--system "..."] [--max 800] [--prompt "..."]   (prompt from stdin if --prompt absent)
// input over 12 KB: the long chain, max_tokens at least 12000 and a 140 s limit per model are chosen automatically
// big input that fails whole is retried in pieces of about 9 KB
// exit: 0 ok | 3 every model failed (do the job with haiku-helper) | 4 refused: input looks private
import fs from 'fs'; import os from 'os'; import path from 'path';

const CHAINS = {
  default: ['groq/openai/gpt-oss-120b', 'groq/qwen/qwen3.8-27b', 'gemini/gemini-2.5-flash-lite'],
  fast: ['groq/openai/gpt-oss-20b', 'groq/qwen/qwen3.8-27b', 'groq/openai/gpt-oss-120b'],
  code: ['mistral/codestral-latest', 'groq/openai/gpt-oss-120b', 'gemini/gemini-2.5-flash-lite'],
  long: ['gemini/gemini-2.5-flash-lite', 'openrouter/nvidia/nemotron-3-ultra-550b-a55b:free'],
  reason: ['openrouter/nvidia/nemotron-3-ultra-550b-a55b:free', 'groq/openai/gpt-oss-120b'],
};
const PRIVATE = [
  /\b[A-Z]{5}[0-9]{4}[A-Z]\b/,                       // PAN
  /\b\d{4}\s?\d{4}\s?\d{4}\b/,                       // Aadhaar-like
  /\b(?:a\/c|acct|account)\s*(?:no\.?|number|#)?\s*[:\-]?\s*\d{9,18}\b/i,
  /\b(?:IFSC|CVV|OTP|password|passwd|secret|api[_ -]?key|token)\b\s*[:=]/i,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
  /\b(?:sk-|gsk_|ghp_|AIza|xox[bp]-)[A-Za-z0-9_-]{16,}/,
  /\b(?:Form 26AS|ITR-?\d)\b/i,
];

const a = process.argv.slice(2); const opt = {};
for (let i = 0; i < a.length; i++) if (a[i].startsWith('--')) opt[a[i].slice(2)] = a[i + 1]?.startsWith('--') || a[i + 1] === undefined ? true : a[++i];
const user = typeof opt.prompt === 'string' ? opt.prompt : fs.readFileSync(0, 'utf8');
const big = user.length > 12000;   // Groq models answer http 413 above about 12 KB, so big input goes to the long chain
const task = big && (!CHAINS[opt.task] || opt.task === 'default' || opt.task === 'fast') ? 'long' : CHAINS[opt.task] ? opt.task : 'default';
if (!user.trim()) { console.error('cheap-llm: empty prompt'); process.exit(2); }
if (PRIVATE.some(r => r.test(user) || r.test(opt.system || ''))) { console.error('cheap-llm: REFUSED, input looks private. Use haiku-helper/sonnet-helper or a script.'); process.exit(4); }

const base = process.env.OMNIROUTE_BASE_URL || (process.platform === 'win32' ? 'http://127.0.0.1:39596/v1' : 'http://127.0.0.1:20128/v1');
let key = process.env.OMNIROUTE_API_KEY;
if (!key) {
  const dir = process.env.OMNIROUTE_DATA_DIR || path.join(os.homedir(), '.omniroute');
  try { key = (fs.readFileSync(path.join(dir, '.env'), 'utf8').match(/^OMNIROUTE_API_KEY=(.*)$/m) || [])[1]?.trim().replace(/^["']|["']$/g, ''); } catch {}
}
if (!key) { console.error('cheap-llm: no OmniRoute key found'); process.exit(3); }

async function ask(text, chain, isBig, cap) {
  const messages = [...(opt.system ? [{ role: 'system', content: String(opt.system) }] : []), { role: 'user', content: text }];
  for (const model of chain) {
    try {
      const r = await fetch(base + '/chat/completions', { method: 'POST', headers: { 'content-type': 'application/json', authorization: `Bearer ${key}` }, body: JSON.stringify({ model, messages, max_tokens: Math.max(Number(opt.max) || 0, cap || (isBig ? 12000 : 1500)) }), signal: AbortSignal.timeout(isBig ? 140000 : 90000) });
      const j = await r.json().catch(() => ({}));
      const c = j.choices?.[0]?.message?.content;
      const out = typeof c === 'string' ? c : Array.isArray(c) ? c.map(x => x?.text ?? '').join('') : '';
      if (r.ok && j.choices?.[0]?.finish_reason === 'length') { console.error(`cheap-llm: ${model} -> truncated, trying next`); continue; }
      if (r.ok && out.trim()) { try { fs.appendFileSync(path.join(os.homedir(), '.claude', 'routing.log'), `${new Date().toISOString()} cheap-llm model=${model} ok=true in=${text.length}B out=${out.length}B\n`); } catch {} console.error(`cheap-llm: ${model}`); return out.trim(); }
      console.error(`cheap-llm: ${model} -> http ${r.status}`);
      if (isBig && r.status === 429) return null;   // rate-limited: go straight to pieces, the slow fall-back model would eat the time
    } catch (e) { console.error(`cheap-llm: ${model} -> ${e.message.slice(0, 60)}`); }
  }
  return null;
}
let out = await ask(user, CHAINS[task], big);
if (out === null && big) {
  // Big input failed on every long-input model (usually a free-tier rate limit): cut it into pieces of about 9 KB
  // at "### " blocks or line ends and send each piece to the default chain, 2 s apart. Any piece failing = exit 3.
  const units = /\n### /.test(user) ? user.split(/\n(?=### )/) : user.split('\n'); const pieces = ['']; const sep = '\n';
  for (const u of units) { if (pieces[pieces.length - 1].length + u.length > 9000 && pieces[pieces.length - 1]) pieces.push(''); pieces[pieces.length - 1] += (pieces[pieces.length - 1] ? sep : '') + u; }
  console.error(`cheap-llm: retrying in ${pieces.length} pieces`); const parts = [];
  for (const p of pieces) { const o = p.trim() ? await ask(p, ['groq/qwen/qwen3.8-27b', 'groq/openai/gpt-oss-120b', 'gemini/gemini-2.5-flash-lite'], false, 4000) : ''; if (o === null) process.exit(3); parts.push(o); await new Promise(r => setTimeout(r, 500)); }
  out = parts.filter(Boolean).join('\n');
}
if (out === null) process.exit(3);
process.stdout.write(out + '\n'); process.exit(0);
