#!/usr/bin/env node
// cheap-llm: one-shot text job through any OpenAI-compatible backend: your OmniRoute or a provider API (free/cheap models). NON-PRIVATE TEXT ONLY.
// usage: cheap-llm [--task default|fast|code|long|reason] [--system "..."] [--max 800] [--prompt "..."]   (prompt from stdin if --prompt absent)
// input over 12 KB: the long chain, max_tokens at least 12000 and a 140 s limit per model are chosen automatically
// big input that fails whole is retried in pieces of about 9 KB
// exit: 0 ok | 3 every model failed (do the job with haiku-helper) | 4 refused: input looks private
import fs from 'fs'; import os from 'os'; import path from 'path';

// Config (optional): ~/.claude/cheap-llm.json  { "base_url", "api_key_env" | "api_key", "chains": {default,fast,code,long,reason: [model,...]}, "piece_chain": [model,...] }
// Backend = any OpenAI-compatible endpoint: your OmniRoute (its own routing/combos decide the model; use combo names here), or a provider API (Groq, Gemini, OpenRouter, Mistral, OpenAI...).
let CFG = {}; try { CFG = JSON.parse(fs.readFileSync(path.join(os.homedir(), '.claude', 'cheap-llm.json'), 'utf8')); } catch {}
const CHAINS = { default: ['auto'], ...(CFG.chains || {}) };   // 'auto' = let your OmniRoute decide (or put your combo name / provider model id)
for (const k of ['fast', 'code', 'long', 'reason']) CHAINS[k] ||= CHAINS.default;   // unset chains fall back to default
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

const base = CFG.base_url || process.env.CHEAP_LLM_BASE_URL || process.env.OMNIROUTE_BASE_URL || (process.platform === 'win32' ? 'http://127.0.0.1:39596/v1' : 'http://127.0.0.1:20128/v1');
let key = CFG.api_key || (CFG.api_key_env && process.env[CFG.api_key_env]) || process.env.CHEAP_LLM_API_KEY || process.env.OMNIROUTE_API_KEY;
if (!key) {
  const dir = process.env.OMNIROUTE_DATA_DIR || path.join(os.homedir(), '.omniroute');
  try { key = (fs.readFileSync(path.join(dir, '.env'), 'utf8').match(/^OMNIROUTE_API_KEY=(.*)$/m) || [])[1]?.trim().replace(/^["']|["']$/g, ''); } catch {}
}
if (!key) { console.error('cheap-llm: no backend configured. Set up OmniRoute (OMNIROUTE_API_KEY) or a provider API key; see config/cheap-llm.example.json and skills/route-task/reference/cheap-models.md. Falling back: use haiku-helper.'); process.exit(3); }

// Ask the backend which models it serves and skip the ones it does not list. 'auto' and unreachable lists are kept as they are.
let AVAIL = null;
try { const r = await fetch(base + '/models', { headers: { authorization: `Bearer ${key}` }, signal: AbortSignal.timeout(4000) }); const j = await r.json(); AVAIL = new Set((j.data || []).map(m => m.id)); if (!AVAIL.size) AVAIL = null; } catch {}
const usable = chain => { const ok = chain.filter(m => m === 'auto' || !AVAIL || AVAIL.has(m)); return ok.length ? ok : chain; };

async function ask(text, chain, isBig, cap) {
  chain = usable(chain);
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
  for (const p of pieces) { const o = p.trim() ? await ask(p, CFG.piece_chain || CHAINS.default, false, 4000) : ''; if (o === null) process.exit(3); parts.push(o); await new Promise(r => setTimeout(r, 500)); }
  out = parts.filter(Boolean).join('\n');
}
if (out === null) process.exit(3);
process.stdout.write(out + '\n'); process.exit(0);
