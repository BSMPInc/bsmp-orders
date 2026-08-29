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
      POST /send   reply: {replyAs, box, id, ids, body, all?, cc?, attachments?, tables?}
                   new:   {replyAs, to, subject, body, cc?, attachments?, tables?}
                   all: reply-all — cc everyone on the email except our boxes
                   to: one address or a comma-joined list; cc: array or comma
                   list, merged on top of reply-all's, deduped against To:.
                   Both are re-validated here — a caller cannot smuggle a header
                   attachments: [{name, mime, data(base64)}] — ~18 MB total
                   (Gmail rejects a message over 25 MB after base64 +33%)
                   tables: [{title?, header?, rows:[[cells…]]}] — appended after
                   the body (before the signature) as real HTML tables; the
                   plain-text alternative gets padded-column versions
                   sigLogo: {data(base64), mime, width} — signature logo,
                   embedded inline (cid) under the signature text
                   inline: [{marker, name, mime, data(base64)}] — images pasted
                   into the body; each one replaces its "[image N]" marker in
                   the HTML as an embedded (cid) picture, so it shows exactly
                   where it was pasted — never a blocked remote image
      POST /trash   {ids:{box:threadId}} move to Gmail trash in every box
      POST /untrash {ids:{box:threadId}} restore from trash (the undo)
*/

const GMAIL_SCOPES = 'https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.send';
const ALLOWED_ORIGINS = ['https://bsmpinc.github.io', 'http://localhost:8742', 'http://127.0.0.1:8742',
                         'https://bertsmp.com', 'https://www.bertsmp.com', 'http://localhost:8791'];

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
      // ---- public: quote request from bertsmp.com -----------------------
      // Handled BEFORE the sign-in gate below, because website visitors have
      // no Firebase account. Everything here is untrusted input: it is length
      // capped, stripped of CR/LF so no extra mail headers can be injected,
      // and only ever mailed to our own mailbox -- never to an address the
      // sender picks.
      if (new URL(request.url).pathname === '/quote' && request.method === 'POST') {
        const q = await request.json().catch(() => null);
        if (!q) return json({ error: 'bad request' }, 400);

        // Honeypot: bots fill the hidden "website" field, people never see it.
        // Answer 200 so the bot believes it worked and does not retry.
        if (String(q.website || '').trim()) return json({ ok: true });

        const one = (v, n) => String(v == null ? '' : v).replace(/[\r\n]+/g, ' ').trim().slice(0, n);
        const name    = one(q.name, 120);
        const email   = one(q.email, 160);
        const company = one(q.company, 120);
        const phone   = one(q.phone, 40);
        const message = String(q.message == null ? '' : q.message).trim().slice(0, 4000);

        if (!name || !email || !message) return json({ error: 'name, email and message are required' }, 400);
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: 'that email address is not valid' }, 400);

        const qBoxes = (env.MAILBOXES || '').split(',').map(x => x.trim()).filter(Boolean);
        if (!qBoxes.length) return json({ error: 'MAILBOXES not configured' }, 500);
        const qBox = qBoxes[0];

        // Optional rate limit -- active only if a KV namespace called QUOTE_KV
        // is bound to the worker. Without it the honeypot carries the load.
        if (env.QUOTE_KV) {
          const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
          const n = parseInt(await env.QUOTE_KV.get('q:' + ip) || '0', 10);
          if (n >= 5) return json({ error: 'too many requests -- please call us at 818.775.0104' }, 429);
          await env.QUOTE_KV.put('q:' + ip, String(n + 1), { expirationTtl: 3600 });
        }

        const qBody =
          'New quote request from bertsmp.com\n' +
          '--------------------------------------------\n' +
          'Name:    ' + name + '\n' +
          (company ? 'Company: ' + company + '\n' : '') +
          'Email:   ' + email + '\n' +
          (phone ? 'Phone:   ' + phone + '\n' : '') +
          '--------------------------------------------\n\n' +
          message + '\n\n' +
          '--------------------------------------------\n' +
          'Hit Reply to answer ' + name + ' directly.\n';

        await sendMail(env, qBoxes, {
          replyAs: qBox,
          to: qBox,
          subject: 'Quote request -- ' + (company || name),
          replyTo: email,
          body: qBody,
        });
        return json({ ok: true });
      }

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
        // q → search the ENTIRE mailbox history; tokens → page further back
        let tokens = {};
        try { tokens = JSON.parse(url.searchParams.get('tokens') || '{}'); } catch { /* fresh load */ }
        return json(await listThreads(env, mailboxes, url.searchParams.get('q') || '', tokens));
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
      if ((url.pathname === '/trash' || url.pathname === '/untrash') && request.method === 'POST') {
        const { ids } = await request.json();
        const op = url.pathname.slice(1);   // Gmail's threads/<id>/trash | /untrash
        await Promise.all(Object.entries(ids || {}).map(([box, tid]) =>
          mailboxes.includes(box)
            ? gmail(env, box, `threads/${encodeURIComponent(tid)}/${op}`, 'POST').catch(() => null)
            : null));
        return json({ ok: true });
      }
      if (url.pathname === '/attachment' && request.method === 'GET') {
        const box = url.searchParams.get('box'), msg = url.searchParams.get('msg'), id = url.searchParams.get('id');
        const mime = url.searchParams.get('mime') || 'application/octet-stream';
        const name = (url.searchParams.get('name') || 'attachment').replace(/["\r\n]/g, '');
        if (!mailboxes.includes(box) || !msg || !id) return json({ error: 'bad params' }, 400);
        const att = await gmail(env, box, `messages/${encodeURIComponent(msg)}/attachments/${encodeURIComponent(id)}`);
        const bytes = b64urlToBytes(att.data || '');
        return new Response(bytes, { headers: { ...cors, 'Content-Type': mime,
          'Content-Disposition': `inline; filename="${name}"`, 'Cache-Control': 'private, max-age=3600' } });
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
// EVERYTHING except spam/trash comes through — the app's shared mute list
// (mail/muted) is what keeps unwanted senders out of view, not Gmail's
// category guesses (which were hiding real customer mail).
async function listThreads(env, mailboxes, q, tokens) {
  const query = (q ? q + ' ' : '') + '-in:spam -in:trash';
  const paging = tokens && Object.keys(tokens).length > 0;
  const next = {};
  const perBox = await Promise.all(mailboxes.map(async (box) => {
    if (paging && !tokens[box]) return { box, threads: [] };   // this box is exhausted
    const pt = paging ? '&pageToken=' + encodeURIComponent(tokens[box]) : '';
    const list = await gmail(env, box, 'threads?maxResults=100&q=' + encodeURIComponent(query) + pt);
    if (list.nextPageToken) next[box] = list.nextPageToken;
    const metas = await gmailBatch(env, box, (list.threads || []).map(t =>
      `threads/${t.id}?format=metadata&metadataHeaders=From&metadataHeaders=To&metadataHeaders=Subject&metadataHeaders=Message-ID&metadataHeaders=Date`));
    return { box, threads: metas.filter(Boolean) };
  }));

  const ours = (a) => mailboxes.some(mb => mb.toLowerCase() === (a || '').toLowerCase());
  const merged = new Map();
  for (const { box, threads } of perBox) {
    for (const t of threads) {
      const msgs = t.messages || [];
      if (!msgs.length) continue;
      const first = msgs[0], last = msgs[msgs.length - 1];
      const h = (m, n) => ((m.payload && m.payload.headers || []).find(x => x.name.toLowerCase() === n.toLowerCase()) || {}).value || '';
      const mid = h(first, 'Message-ID') || (box + ':' + t.id);
      const key = mid.replace(/[.#$\/\[\]\s<>]/g, '_').slice(0, 200);
      // the card shows the OTHER party — replying must not flip the sender
      // column to our own address. Walk back to the newest outside sender;
      // if the whole thread is ours, show who we wrote to.
      let from = null;
      for (let i = msgs.length - 1; i >= 0; i--) {
        const f = parseAddr(h(msgs[i], 'From'));
        if (f.email && !ours(f.email)) { from = f; break; }
      }
      if (!from) {
        const toA = (h(last, 'To') || '').split(',').map(s => parseAddr(s)).find(x => x.email && !ours(x.email));
        from = toA ? { name: 'To: ' + (toA.name || toA.email), email: toA.email } : parseAddr(h(last, 'From'));
      }
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
  return { threads, next };
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
      bodyText: extractText(m.payload), bodyHtml: sanitizeHtml(extractHtml(m.payload)),
      attachments: listAttachments(m.payload),
    };
  });
  return { messages };
}

// ── /send: reply into a thread, or brand-new mail ───────────────────────────
async function sendMail(env, mailboxes, p) {
  const from = p.replyAs;
  const ours = (a) => mailboxes.some(mb => mb.toLowerCase() === (a || '').toLowerCase());
  let to = p.to, subject = p.subject || '', headers = '', threadId = null, cc = [];

  if (p.box && p.id) {  // reply — pull headers from the original thread
    const t = await gmail(env, p.box, `threads/${encodeURIComponent(p.id)}?format=metadata&metadataHeaders=From&metadataHeaders=To&metadataHeaders=Cc&metadataHeaders=Reply-To&metadataHeaders=Subject&metadataHeaders=Message-ID&metadataHeaders=References`);
    const msgs = t.messages || [];
    const last = msgs[msgs.length - 1];
    const h = (m, n) => ((m.payload && m.payload.headers || []).find(x => x.name.toLowerCase() === n.toLowerCase()) || {}).value || '';
    // reply to the other party, not ourselves — if the last message in the
    // thread is our own, walk back to the most recent outside sender
    let src = null, replyTo = '';
    for (let i = msgs.length - 1; i >= 0; i--) {
      const fromAddr = parseAddr(h(msgs[i], 'From')).email;
      if (fromAddr && !ours(fromAddr)) { src = msgs[i]; replyTo = h(src, 'Reply-To') || h(src, 'From'); break; }
    }
    // whole thread is ours (we wrote first, no answer yet) — reply to whoever we wrote to
    if (!replyTo) { src = last; replyTo = splitAddrs(h(last, 'To')).find(a => !ours(a)) || ''; }
    to = to || parseAddr(replyTo).email;
    if (p.all && src) {  // reply-all: cc everyone else on that email, minus our own boxes
      const seen = new Set([(to || '').toLowerCase()]);
      for (const a of splitAddrs(h(src, 'To') + ',' + h(src, 'Cc'))) {
        const l = a.toLowerCase();
        if (!a || ours(a) || seen.has(l)) continue;
        seen.add(l); cc.push(a);
      }
    }
    subject = subject || h(msgs[0], 'Subject');
    if (!/^re:/i.test(subject)) subject = 'Re: ' + subject;
    const lastMid = h(last, 'Message-ID');
    const refs = (h(last, 'References') + ' ' + lastMid).trim();
    if (lastMid) headers = `In-Reply-To: ${lastMid}\r\nReferences: ${refs}\r\n`;
    // if the sending mailbox has this thread too, keep Gmail's own threading
    if (p.ids && p.ids[from]) threadId = p.ids[from];
  }
  if (!to) throw new Error('no recipient');

  // Client-supplied Cc (the order-confirmation picker sends one). Reply-all
  // fills `cc` from the thread above instead; anything passed in is merged on
  // top of that. Both To: and Cc: are written straight into the header block,
  // so every address is stripped of CR/LF and re-validated here — a caller must
  // never be able to smuggle in an extra header or a hidden Bcc.
  const addrOk = (a) => /^[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+$/.test(a);
  const cleanAddr = (raw) => {
    const s = String(raw == null ? '' : raw).replace(/[\r\n]/g, ' ');
    const a = (parseAddr(s).email || s).trim().replace(/[<>,;]/g, '');
    return addrOk(a) ? a : '';
  };
  const toList = splitAddrs(String(to)).map(cleanAddr).filter(Boolean);
  if (!toList.length) throw new Error('no valid recipient');
  to = toList.join(', ');
  const seenCc = new Set(toList.map(a => a.toLowerCase()).concat(cc.map(a => a.toLowerCase())));
  for (const raw of (Array.isArray(p.cc) ? p.cc : String(p.cc || '').split(','))) {
    const a = cleanAddr(raw);
    if (!a) continue;
    const l = a.toLowerCase();
    if (seenCc.has(l)) continue;   // already on To:, or already cc'd by reply-all
    seenCc.add(l); cc.push(a);
  }

  const atts = (Array.isArray(p.attachments) ? p.attachments : []).filter(a => a && a.data && a.name);
  // images pasted into the body — embedded inline (cid) where their [image N]
  // marker sits in the text; any without a marker land after the body instead
  const inline = (Array.isArray(p.inline) ? p.inline : []).slice(0, 12)
    .filter(a => a && typeof a.data === 'string' && /^image\//.test(a.mime || ''))
    .map((a, i) => ({
      cid: 'bsmpinl' + (i + 1),
      marker: String(a.marker || ''),
      name: String(a.name || 'image' + (i + 1)).replace(/["\r\n]/g, '').slice(0, 120),
      mime: String(a.mime).replace(/[\r\n";]/g, ''),
      data: a.data.replace(/[^A-Za-z0-9+/=]/g, '') }))
    .filter(a => a.data.length);
  const attBytes = atts.reduce((s, a) => s + String(a.data).length * 0.75, 0)
    + inline.reduce((s, a) => s + a.data.length * 0.75, 0);
  if (attBytes > 20 * 1024 * 1024) throw new Error('attachments too large — keep an email under ~18 MB total');

  // optional tables: sent as structured rows, rendered as real HTML tables.
  // With tables (or a signature logo) the email goes out multipart/alternative
  // (plain + HTML) so old mail programs still get a readable text version.
  const tables = (Array.isArray(p.tables) ? p.tables : []).filter(t => t && Array.isArray(t.rows))
    .map(t => ({ title: String(t.title || ''), header: !!t.header,
      rows: t.rows.slice(0, 30).map(r => (Array.isArray(r) ? r : [r]).slice(0, 10).map(c => String(c == null ? '' : c))) }))
    .filter(t => t.rows.length && t.rows.some(r => r.some(c => c.trim())));
  // optional signature logo: small base64 image, embedded inline (cid) so it
  // shows without the recipient clicking "load remote images"
  const logo = (p.sigLogo && typeof p.sigLogo.data === 'string' && p.sigLogo.data.length < 700000
      && /^image\//.test(p.sigLogo.mime || ''))
    ? { data: p.sigLogo.data.replace(/[^A-Za-z0-9+/=]/g, ''),
        mime: String(p.sigLogo.mime).replace(/[\r\n";]/g, ''),
        width: Math.max(40, Math.min(600, parseInt(p.sigLogo.width) || 160)) }
    : null;
  const wantHtml = tables.length > 0 || !!logo || inline.length > 0;
  let main = p.body || '', sig = '';
  if (wantHtml) {   // tables go after the text but the signature stays last
    const si = main.lastIndexOf('\n\n-- \n');
    if (si >= 0) { sig = main.slice(si); main = main.slice(0, si); }
    else if (/^-- \n/.test(main)) { sig = '\n\n' + main; main = ''; }
  }
  const mid = tables.map(tableText).join('\n\n');
  const plain = wantHtml ? main + (mid ? (main ? '\n\n' : '') + mid : '') + sig : main;
  // pasted images: swap each [image N] marker for its embedded picture — the
  // markers pass through escHtml untouched, so a plain string replace is safe.
  // The plain-text alternative keeps the "[image N]" text as its stand-in.
  const inlineTag = (im) => `<img src="cid:${im.cid}" style="max-width:100%;height:auto;border:0" alt="${escHtml(im.name)}">`;
  let mainHtml = textToHtml(main), loose = '';
  for (const im of inline) {
    if (im.marker && mainHtml.includes(im.marker)) mainHtml = mainHtml.replace(im.marker, () => inlineTag(im));
    else loose += `<div style="margin:10px 0">${inlineTag(im)}</div>`;
  }
  const html = wantHtml
    ? '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.5;color:#111">' +
      mainHtml + tables.map(tableHtml).join('') + loose + textToHtml(sig) +
      (logo ? `<div style="margin-top:10px"><img src="cid:bsmpsiglogo" width="${logo.width}" style="display:block;max-width:100%;height:auto;border:0" alt=""></div>` : '') +
      '</div>'
    : '';

  // Reply-To -- set by the public /quote endpoint so that hitting Reply in
  // Gmail answers the customer rather than our own mailbox.
  if (p.replyTo) headers += 'Reply-To: ' + String(p.replyTo).replace(/[\r\n<>,]/g, '') + '\r\n';
  const ccLine = cc.length ? `Cc: ${cc.join(', ')}\r\n` : '';
  const top = `From: ${from}\r\nTo: ${to}\r\n${ccLine}Subject: ${encodeHeader(subject)}\r\n${headers}MIME-Version: 1.0\r\n`;
  const utf8 = (s) => unescape(encodeURIComponent(s));   // text → binary string for btoa
  let cType = 'text/plain; charset=UTF-8', content = plain;
  if (html) {
    // HTML side: plain text/html, or multipart/related when pictures are
    // embedded (pasted body images and/or the signature logo)
    const relParts = inline.map(im => ({ cid: im.cid, mime: im.mime, name: im.name, data: im.data }));
    if (logo) relParts.push({ cid: 'bsmpsiglogo', mime: logo.mime, name: 'logo', data: logo.data });
    let htmlSection;
    if (relParts.length) {
      const rel = 'rel_bsmp_' + Math.random().toString(36).slice(2);
      htmlSection = `Content-Type: multipart/related; boundary="${rel}"\r\n\r\n` +
        `--${rel}\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n${html}\r\n\r\n` +
        relParts.map(pt => `--${rel}\r\nContent-Type: ${pt.mime}\r\nContent-Transfer-Encoding: base64\r\nContent-ID: <${pt.cid}>\r\nContent-Disposition: inline; filename="${pt.name}"\r\n\r\n${pt.data.replace(/(.{76})/g, '$1\r\n')}\r\n`).join('') +
        `--${rel}--`;
    } else {
      htmlSection = `Content-Type: text/html; charset=UTF-8\r\n\r\n${html}`;
    }
    const alt = 'alt_bsmp_' + Math.random().toString(36).slice(2);
    cType = `multipart/alternative; boundary="${alt}"`;
    content = `--${alt}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n${plain}\r\n\r\n` +
              `--${alt}\r\n${htmlSection}\r\n\r\n--${alt}--`;
  }
  let bin;   // full MIME message as a binary string
  if (atts.length) {
    const bnd = 'mime_bsmp_' + Math.random().toString(36).slice(2);
    bin = utf8(top + `Content-Type: multipart/mixed; boundary="${bnd}"\r\n\r\n` +
      `--${bnd}\r\nContent-Type: ${cType}\r\n\r\n${content}`);
    for (const a of atts) {
      const name = encodeHeader(String(a.name || 'file').replace(/["\r\n]/g, '').slice(0, 180));
      const type = String(a.mime || 'application/octet-stream').replace(/[\r\n"]/g, '');
      // base64 payload is already ASCII — append it untouched (utf8() over
      // megabytes of it would burn the worker's CPU budget for nothing)
      const b64 = String(a.data).replace(/[^A-Za-z0-9+/=]/g, '').replace(/(.{76})/g, '$1\r\n');
      bin += `\r\n\r\n--${bnd}\r\n` + utf8(`Content-Type: ${type}; name="${name}"\r\nContent-Disposition: attachment; filename="${name}"\r\nContent-Transfer-Encoding: base64\r\n\r\n`) + b64;
    }
    bin += `\r\n--${bnd}--`;
  } else {
    bin = utf8(top + `Content-Type: ${cType}\r\n\r\n${content}`);
  }
  const body = { raw: btoa(bin).replace(/\+/g, '-').replace(/\//g, '_') };
  if (threadId) body.threadId = threadId;
  const sent = await gmail(env, from, 'messages/send', 'POST', body);
  return { ok: true, id: sent.id };
}
function encodeHeader(s) { return /[^\x20-\x7e]/.test(s) ? '=?UTF-8?B?' + btoa(unescape(encodeURIComponent(s))) + '?=' : s; }

// ── outgoing tables: one structured table → padded text + inline-styled HTML ──
function escHtml(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function textToHtml(s) { return s ? escHtml(s).replace(/\r?\n/g, '<br>') : ''; }
function tableText(t) {
  const w = [];
  t.rows.forEach(r => r.forEach((c, i) => { w[i] = Math.max(w[i] || 0, c.length); }));
  const line = (r) => r.map((c, i) => c.padEnd(w[i])).join('   ').trimEnd();
  const out = t.rows.map(line);
  if (t.header && out.length > 1) out.splice(1, 0, w.map(x => '-'.repeat(x)).join('   '));
  return (t.title ? t.title + '\n' : '') + out.join('\n');
}
function tableHtml(t) {
  const cell = 'border:1px solid #b9c0c9;padding:5px 10px;font-size:13px;text-align:left';
  const rows = t.rows.map((r, i) => '<tr>' + r.map(c =>
    (t.header && i === 0)
      ? `<th style="${cell};background:#eef1f5">${escHtml(c)}</th>`
      : `<td style="${cell}">${escHtml(c)}</td>`).join('') + '</tr>').join('');
  return (t.title ? `<div style="font-weight:700;margin:14px 0 6px">${escHtml(t.title)}</div>` : '') +
    `<table style="border-collapse:collapse;margin:8px 0 14px" cellspacing="0">${rows}</table>`;
}

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
  if (payload.filename) {
    const ph = (n) => (((payload.headers || []).find(x => x.name.toLowerCase() === n)) || {}).value || '';
    out.push({
      filename: payload.filename,
      size: (payload.body && payload.body.size) || 0,
      mime: payload.mimeType || 'application/octet-stream',
      id: (payload.body && payload.body.attachmentId) || '',
      // inline signature images reference these by <img src="cid:..."> — the
      // app uses this to render them in place and keep them out of the
      // attachment chip list (like Gmail does)
      cid: ph('content-id').replace(/[<>]/g, ''),
      inline: /^inline/i.test(ph('content-disposition')),
    });
  }
  (payload.parts || []).forEach(p => listAttachments(p, out));
  return out;
}
function extractHtml(payload) {
  if (!payload) return '';
  if (payload.mimeType === 'text/html' && payload.body && payload.body.data) return b64urlDecode(payload.body.data);
  if (payload.parts) {
    for (const p of payload.parts) { const h = extractHtml(p); if (h) return h; }
  }
  return '';
}
function sanitizeHtml(h) {
  if (!h) return '';
  return h
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<meta[^>]*http-equiv[^>]*>/gi, '')
    .replace(/\son\w+\s*=\s*"[^"]*"/gi, '')
    .replace(/\son\w+\s*=\s*'[^']*'/gi, '')
    .replace(/\son\w+\s*=\s*[^\s>]+/gi, '')
    .replace(/javascript:/gi, '');
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
function b64urlToBytes(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  const b = atob(s);
  const a = new Uint8Array(b.length);
  for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
  return a;
}
function b64urlDecode(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  try { return decodeURIComponent(escape(atob(s))); } catch { try { return atob(s); } catch { return ''; } }
}
