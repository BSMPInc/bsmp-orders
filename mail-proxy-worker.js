/*  BSMP Mail Proxy — Cloudflare Worker
    ─────────────────────────────────────────────────────────────────────────
    Sits between mail.html and the Gmail API. The browser never sees Google
    credentials; this worker holds them and only answers signed-in BSMP users.

    NOT served by GitHub Pages — deploy to Cloudflare (dash.cloudflare.com →
    Workers → Create → paste this file), then set these secrets/variables:

      GOOGLE_SA_KEY     (secret)  full JSON of the service-account key that has
                                  domain-wide delegation for the Gmail scopes
      MAILBOXES         (var)     comma list: info@bertsmp.com,sales@bertsmp.com
      FIREBASE_API_KEY  (var)     the Firebase web API key (same one in the apps)

    Endpoints (all require Authorization: Bearer <Firebase ID token>):
      GET  /threads                     merged, deduped thread list, both boxes
      GET  /thread?box=…&id=…           full messages of one thread
      POST /read   {ids:{box:threadId}} clear UNREAD in every box that has it
      POST /send   reply: {replyAs, box, id, ids, body}
                   new:   {replyAs, to, subject, body}
*/

const GMAIL_SCOPES = 'https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.send';
const ALLOWED_ORIGINS = ['https://bsmpinc.github.io', 'http://localhost:8742', 'http://127.0.0.1:8742'];

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Vary': 'Origin',
    };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    const json = (obj, status = 200) =>
      new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', ...cors } });

    try {
      // ── gate: caller must be a signed-in, non-operator BSMP user ──────────
      const idToken = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
      if (!idToken) return json({ error: 'missing token' }, 401);
      const who = await verifyFirebaseToken(idToken, env);
      if (!who) return json({ error: 'invalid token' }, 401);
      if (isOperatorEmail(who)) return json({ error: 'managers only' }, 403);

      const url = new URL(request.url);
      const mailboxes = (env.MAILBOXES || '').split(',').map(s => s.trim()).filter(Boolean);
      if (!mailboxes.length) return json({ error: 'MAILBOXES not configured' }, 500);

      if (url.pathname === '/threads' && request.method === 'GET') {
        // no q → recent working set (6 months); q → search the ENTIRE mailbox history
        return json(await listThreads(env, mailboxes, url.searchParams.get('q') || ''));
      }
      if (url.pathname === '/thread' && request.method === 'GET') {
        const box = url.searchParams.get('box'), id = url.searchParams.get('id');
        if (!mailboxes.includes(box) || !id) return json({ error: 'bad box/id' }, 400);
        return json(await getThread(env, box, id));
      }
      if (url.pathname === '/read' && request.method === 'POST') {
        const { ids } = await request.json();
        await Promise.all(Object.entries(ids || {}).map(([box, tid]) =>
          mailboxes.includes(box)
            ? gmail(env, box, `threads/${encodeURIComponent(tid)}/modify`, 'POST', { removeLabelIds: ['UNREAD'] }).catch(() => null)
            : null));
        return json({ ok: true });
      }
      if (url.pathname === '/send' && request.method === 'POST') {
        const p = await request.json();
        if (!mailboxes.includes(p.replyAs)) return json({ error: 'bad replyAs' }, 400);
        return json(await sendMail(env, mailboxes, p));
      }
      return json({ error: 'not found' }, 404);
    } catch (e) {
      return json({ error: String(e && e.message || e) }, 500);
    }
  },
};

// ── Firebase ID-token check (identitytoolkit lookup — simple and robust) ────
async function verifyFirebaseToken(idToken, env) {
  const r = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=${env.FIREBASE_API_KEY}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ idToken }),
  });
  if (!r.ok) return null;
  const d = await r.json();
  return d.users && d.users[0] && d.users[0].email || null;
}
function isOperatorEmail(email) {
  email = (email || '').toLowerCase();
  const local = email.split('@')[0] || '';
  if (local === 'ops' || /^ops[._-]/.test(local)) return true;
  return local.startsWith('operator');
}

// ── Google service-account auth (domain-wide delegation per mailbox) ────────
const _tokCache = {};   // mailbox → {tok, exp}
async function gToken(env, mailbox) {
  const c = _tokCache[mailbox];
  if (c && c.exp > Date.now() + 60000) return c.tok;
  const sa = JSON.parse(env.GOOGLE_SA_KEY);
  const now = Math.floor(Date.now() / 1000);
  const enc = (o) => b64url(new TextEncoder().encode(JSON.stringify(o)));
  const unsigned = enc({ alg: 'RS256', typ: 'JWT' }) + '.' + enc({
    iss: sa.client_email, sub: mailbox, scope: GMAIL_SCOPES,
    aud: 'https://oauth2.googleapis.com/token', iat: now, exp: now + 3600,
  });
  const key = await crypto.subtle.importKey('pkcs8', pemToBuf(sa.private_key),
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(unsigned));
  const jwt = unsigned + '.' + b64url(new Uint8Array(sig));
  const r = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=${encodeURIComponent('urn:ietf:params:oauth:grant-type:jwt-bearer')}&assertion=${jwt}`,
  });
  const d = await r.json();
  if (!d.access_token) throw new Error('Google auth failed for ' + mailbox + ': ' + JSON.stringify(d).slice(0, 200));
  _tokCache[mailbox] = { tok: d.access_token, exp: Date.now() + (d.expires_in - 120) * 1000 };
  return d.access_token;
}
function pemToBuf(pem) {
  const b = atob(pem.replace(/-----[^-]+-----/g, '').replace(/\s/g, ''));
  const a = new Uint8Array(b.length);
  for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
  return a.buffer;
}
function b64url(bytes) {
  let s = ''; bytes.forEach ? bytes.forEach(x => s += String.fromCharCode(x)) : (s = bytes);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function gmail(env, mailbox, path, method = 'GET', body = null) {
  const tok = await gToken(env, mailbox);
  const r = await fetch(`https://gmail.googleapis.com/gmail/v1/users/${encodeURIComponent(mailbox)}/${path}`, {
    method, headers: { Authorization: 'Bearer ' + tok, ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : null,
  });
  if (!r.ok) throw new Error(`Gmail ${method} ${path} → ${r.status}: ${(await r.text()).slice(0, 200)}`);
  return r.json();
}

// ── Gmail batch endpoint: up to 100 thread fetches in ONE HTTP call ─────────
// (keeps us far under Cloudflare's subrequest cap and makes refreshes fast)
async function gmailBatch(env, mailbox, paths) {
  if (!paths.length) return [];
  const tok = await gToken(env, mailbox);
  const boundary = 'batch_bsmp_' + Math.random().toString(36).slice(2);
  const body = paths.map((p, i) =>
    `--${boundary}\r\nContent-Type: application/http\r\nContent-ID: <item${i}>\r\n\r\nGET /gmail/v1/users/${encodeURIComponent(mailbox)}/${p} HTTP/1.1\r\n\r\n`
  ).join('') + `--${boundary}--`;
  const r = await fetch('https://gmail.googleapis.com/batch/gmail/v1', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'multipart/mixed; boundary=' + boundary },
    body,
  });
  if (!r.ok) throw new Error('Gmail batch → ' + r.status + ': ' + (await r.text()).slice(0, 200));
  const ctBoundary = (/boundary=("?)([^";]+)\1/.exec(r.headers.get('Content-Type') || '') || [])[2];
  if (!ctBoundary) throw new Error('Gmail batch: missing response boundary');
  const out = new Array(paths.length).fill(null);
  for (const part of (await r.text()).split('--' + ctBoundary).slice(1, -1)) {
    const idm = /Content-ID:\s*<?response-item(\d+)/i.exec(part);
    const start = part.indexOf('{');
    if (!idm || start < 0) continue;
    try { out[Number(idm[1])] = JSON.parse(part.slice(start, part.lastIndexOf('}') + 1)); } catch { /* skip bad part */ }
  }
  return out;
}

// ── /threads: recent mail from every box (or full-history search), deduped ──
// The default inbox view skips Gmail's promotional/social/forum categories;
// an explicit search (q) still looks through EVERYTHING.
async function listThreads(env, mailboxes, q) {
  const query = q
    ? q + ' -in:spam -in:trash'
    : '-in:spam -in:trash -category:promotions -category:social -category:forums newer_than:180d';
  const perBox = await Promise.all(mailboxes.map(async (box) => {
    const list = await gmail(env, box, 'threads?maxResults=100&q=' + encodeURIComponent(query));
    const metas = await gmailBatch(env, box, (list.threads || []).map(t =>
      `threads/${t.id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Message-ID&metadataHeaders=Date`));
    return { box, threads: metas.filter(Boolean) };
  }));

  const merged = new Map();
  for (const { box, threads } of perBox) {
    for (const t of threads) {
      const msgs = t.messages || [];
      if (!msgs.length) continue;
      const first = msgs[0], last = msgs[msgs.length - 1];
      const h = (m, n) => ((m.payload && m.payload.headers || []).find(x => x.name.toLowerCase() === n.toLowerCase()) || {}).value || '';
      const mid = h(first, 'Message-ID') || (box + ':' + t.id);
      const key = mid.replace(/[.#$\/\[\]\s<>]/g, '_').slice(0, 200);
      const from = parseAddr(h(last, 'From'));
      const entry = merged.get(key) || {
        key, subject: h(first, 'Subject'), fromName: from.name, fromEmail: from.email,
        snippet: decodeEntities(last.snippet || ''), date: Number(last.internalDate || 0),
        unread: false, hasAttach: false, mailboxes: [], ids: {},
      };
      entry.mailboxes.push(box);
      entry.ids[box] = t.id;
      entry.unread = entry.unread || msgs.some(m => (m.labelIds || []).includes('UNREAD'));
      entry.hasAttach = entry.hasAttach || msgs.some(m => hasAttachment(m.payload));
      if (Number(last.internalDate || 0) > entry.date) {
        entry.date = Number(last.internalDate || 0);
        entry.snippet = decodeEntities(last.snippet || '');
      }
      merged.set(key, entry);
    }
  }
  const threads = [...merged.values()].sort((a, b) => b.date - a.date);
  return { threads };
}

// ── /thread: full conversation from one mailbox ─────────────────────────────
async function getThread(env, box, id) {
  const t = await gmail(env, box, `threads/${encodeURIComponent(id)}?format=full`);
  const messages = (t.messages || []).map(m => {
    const h = (n) => ((m.payload && m.payload.headers || []).find(x => x.name.toLowerCase() === n.toLowerCase()) || {}).value || '';
    const from = parseAddr(h('From'));
    return {
      id: m.id, fromName: from.name, fromEmail: from.email,
      to: splitAddrs(h('To')).concat(splitAddrs(h('Cc'))),
      date: Number(m.internalDate || 0), snippet: decodeEntities(m.snippet || ''),
      bodyText: extractText(m.payload), attachments: listAttachments(m.payload),
    };
  });
  return { messages };
}

// ── /send: reply into a thread, or brand-new mail ───────────────────────────
async function sendMail(env, mailboxes, p) {
  const from = p.replyAs;
  let to = p.to, subject = p.subject || '', headers = '', threadId = null;

  if (p.box && p.id) {  // reply — pull headers from the original thread
    const t = await gmail(env, p.box, `threads/${encodeURIComponent(p.id)}?format=metadata&metadataHeaders=From&metadataHeaders=Reply-To&metadataHeaders=Subject&metadataHeaders=Message-ID&metadataHeaders=References`);
    const msgs = t.messages || [];
    const last = msgs[msgs.length - 1];
    const h = (m, n) => ((m.payload && m.payload.headers || []).find(x => x.name.toLowerCase() === n.toLowerCase()) || {}).value || '';
    const replyTo = h(last, 'Reply-To') || h(last, 'From');
    to = to || parseAddr(replyTo).email;
    subject = subject || h(msgs[0], 'Subject');
    if (!/^re:/i.test(subject)) subject = 'Re: ' + subject;
    const lastMid = h(last, 'Message-ID');
    const refs = (h(last, 'References') + ' ' + lastMid).trim();
    if (lastMid) headers = `In-Reply-To: ${lastMid}\r\nReferences: ${refs}\r\n`;
    // if the sending mailbox has this thread too, keep Gmail's own threading
    if (p.ids && p.ids[from]) threadId = p.ids[from];
  }
  if (!to) throw new Error('no recipient');

  const body = { raw: btoa(unescape(encodeURIComponent(
    `From: ${from}\r\nTo: ${to}\r\nSubject: ${encodeHeader(subject)}\r\n${headers}MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n${p.body || ''}`
  ))).replace(/\+/g, '-').replace(/\//g, '_') };
  if (threadId) body.threadId = threadId;
  const sent = await gmail(env, from, 'messages/send', 'POST', body);
  return { ok: true, id: sent.id };
}
function encodeHeader(s) { return /[^\x20-\x7e]/.test(s) ? '=?UTF-8?B?' + btoa(unescape(encodeURIComponent(s))) + '?=' : s; }

// ── MIME helpers ─────────────────────────────────────────────────────────────
function parseAddr(s) {
  const m = /^\s*"?([^"<]*)"?\s*<([^>]+)>/.exec(s || '');
  if (m) return { name: m[1].trim(), email: m[2].trim() };
  return { name: '', email: (s || '').trim() };
}
function splitAddrs(s) { return (s || '').split(',').map(x => parseAddr(x).email).filter(Boolean); }
function decodeEntities(s) {
  return (s || '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#39;/g, "'").replace(/&quot;/g, '"');
}
function hasAttachment(payload) {
  if (!payload) return false;
  if (payload.filename) return true;
  return (payload.parts || []).some(hasAttachment);
}
function listAttachments(payload, out) {
  out = out || [];
  if (!payload) return out;
  if (payload.filename) out.push({ filename: payload.filename, size: (payload.body && payload.body.size) || 0 });
  (payload.parts || []).forEach(p => listAttachments(p, out));
  return out;
}
function extractText(payload) {
  if (!payload) return '';
  if (payload.mimeType === 'text/plain' && payload.body && payload.body.data) return b64urlDecode(payload.body.data);
  if (payload.parts) {
    for (const p of payload.parts) { const t = extractText(p); if (t) return t; }
  }
  if (payload.mimeType === 'text/html' && payload.body && payload.body.data) {
    return b64urlDecode(payload.body.data)
      .replace(/<style[\s\S]*?<\/style>/gi, '').replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>/gi, '\n\n').replace(/<[^>]+>/g, '')
      .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
      .replace(/\n{3,}/g, '\n\n').trim();
  }
  return '';
}
function b64urlDecode(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  try { return decodeURIComponent(escape(atob(s))); } catch { try { return atob(s); } catch { return ''; } }
}
