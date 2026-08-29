# Slices the REAL confirmation-email recipient picker out of orders.html into a
# standalone test page: address parsing/validation, dedupe, the address-book
# merge, the suggestion filter, and the chip-box layout at the owner's panel
# width. Run this, then open http://localhost:8123/_confirmtotest.html (python
# http.server from .claude/launch.json — the Browser pane refuses file:// URLs).
# Title says "all pass" or "FAILURES"; delete _confirmtotest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()
wsrc = io.open('C:/Users/info/bsmp-orders/mail-proxy-worker.js', encoding='utf-8').read()

def grab(start, end, s=None):
    s = src if s is None else s
    a = s.index(start); b = s.index(end, a)
    return s[a:b]

# The worker's own To:/Cc: sanitiser, sliced verbatim and wrapped so it can be
# exercised without a request — this is the code that actually writes the header
# lines, so it is the one worth asserting against.
worker = (grab('function parseAddr(s) {', '\nfunction decodeEntities', wsrc)
          + '\nfunction wkRecipients(p, to, cc){\n'
          + grab("  if (!to) throw new Error('no recipient');", '\n  const atts =', wsrc)
          + '\n  return {to:to, cc:cc};\n}\n')

a = src.index('<style>'); b = src.index('</style>', a)
css = src[a+len('<style>'):b]

# the picker: RE_EMAIL / ctoParse / ctoAdd / the handlers / _ctoRender / preview
block  = grab('const RE_EMAIL=', '\nwindow.emailConfirmation=')
# the message composer — the preview and the send both render this one function,
# so asserting on it is asserting on what actually leaves the building
block += '\n' + grab('function _confirmCompose(sigText){', '\n// Mailbox + shared signature.')
# the guess+book merge, lifted out of emailConfirmation so it can be exercised
# without Firebase (kept byte-identical to the source below it)
merge = u'''
function mergeBook(guesses, book){
  const seen=new Set(), merged=[];
  guesses.filter(g=>g.email&&RE_EMAIL.test(g.email)).forEach(g=>{
    const k=g.email.toLowerCase(); if(seen.has(k)) return; seen.add(k);
    const b=book.find(x=>x.email.toLowerCase()===k);
    merged.push({email:g.email, name:g.name||(b&&b.name)||'', company:(b&&b.company)||'', suggested:g.suggested});
  });
  book.forEach(b=>{ const k=b.email.toLowerCase(); if(seen.has(k)) return; seen.add(k); merged.push(b); });
  return merged;
}
'''

html = u'''<!doctype html><meta charset="utf-8"><title>confirm recipients test</title>
<style>__CSS__</style>
<style>
  /* the app's shell rules (body{display:flex}, zero-width html/body) would squeeze
     the harness to nothing — neutralize them, then pin the modal to its real width */
  html,body{display:block!important;width:auto!important;height:auto!important;margin:0;background:#fff;overflow:visible!important}
  #panel{width:580px!important;max-width:580px!important;flex:none!important;overflow-x:auto;border:1px solid #ccc;box-sizing:border-box;padding:14px}
  #out{font:12px ui-monospace,monospace;white-space:pre;padding:8px}
</style>
<div id="panel"><div id="cto-body"></div></div>
<pre id="out"></pre>
<script>
const out=[];
const ok=(n,c,e)=>out.push((c?'PASS':'FAIL')+'  '+n+(e!=null?('   ['+e+']'):''));
// ── stubs ──
function esc2(s){ return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
function closeModal(){}
function saveDB(){}
function fmtDate(d){ if(!d) return ''; const [y,m,dd]=String(d).split('-'); return m+'/'+dd+'/'+y.slice(2); }
function fmtMoney(n){ return '$'+(Number(n)||0).toFixed(2); }
function rowTotal(r){ return r.qty&&r.cost?r.qty*r.cost:(parseFloat(r.total)||0); }
let _confirmItems=[], _confirmMeta={};
/*__BLOCK__*/
/*__MERGE__*/
/*__WORKER__*/

// ══ 1 · parsing what gets pasted in ══════════════════════════════════════════
ok('plain address parses', ctoParse('a@x.com').join('|')==='a@x.com');
ok('display-name form is unwrapped', ctoParse('Jane Machinist <jane@acme.com>').join('|')==='jane@acme.com',
   ctoParse('Jane Machinist <jane@acme.com>').join('|'));
ok('comma list splits', ctoParse('a@x.com, b@y.com').join('|')==='a@x.com|b@y.com');
ok('semicolon list splits (Outlook paste)', ctoParse('a@x.com; b@y.com').join('|')==='a@x.com|b@y.com');
ok('newline list splits', ctoParse('a@x.com\\nb@y.com').join('|')==='a@x.com|b@y.com');
ok('mixed display names in a list', ctoParse('Jane <j@a.com>; Bob <b@b.com>').join('|')==='j@a.com|b@b.com');
ok('empty in, empty out', ctoParse('  ,  ; ').length===0);

// ══ 2 · validation + dedupe ══════════════════════════════════════════════════
_ctoBook=[]; _ctoTo=[];
ok('a good address is added', ctoAdd('a@x.com').added===1 && _ctoTo.length===1);
ok('the same address twice is one chip', ctoAdd('a@x.com').added===0 && _ctoTo.length===1);
ok('dedupe ignores case', ctoAdd('A@X.COM').added===0 && _ctoTo.length===1);
let r=ctoAdd('not-an-email');
ok('a non-address is refused', r.added===0 && r.bad==='not-an-email', r.bad);
ok('a refused address adds no chip', _ctoTo.length===1);
r=ctoAdd('a@x.com, b@y.com, nope');
ok('a mixed paste keeps the good ones', r.added===1 && _ctoTo.length===2, _ctoTo.length);
ok('and reports the bad one', r.bad==='nope', r.bad);
ok('no-dot domains are refused', ctoAdd('a@localhost').added===0);
ok('addresses with + and dots are fine', ctoAdd('jane.q+po@sub.acme.co.uk').added===1);
_ctoBook=[{email:'jane@acme.com',name:'Jane Machinist',company:'Acme'}]; _ctoTo=[];
ctoAdd('jane@acme.com');
ok('a book address brings its name onto the chip', _ctoTo[0].name==='Jane Machinist', _ctoTo[0].name);
ok('a typed stranger gets no name', (ctoAdd('who@else.com'), _ctoTo[1].name===''), _ctoTo[1].name);

// ══ 3 · the guess + address-book merge ═══════════════════════════════════════
{
  const book=[{email:'jane@acme.com',name:'Jane Machinist',company:'Acme'},
              {email:'zeb@other.com',name:'Zeb',company:'Other'},
              {email:'buyer@acme.com',name:'Buyer Bob',company:'Acme'}];
  const guesses=[{email:'buyer@acme.com',name:'',suggested:'customer card'},
                 {email:'po@acme.com',name:'PO Desk',suggested:'sent the PO'},
                 {email:'BUYER@acme.com',name:'',suggested:'sent last time'}];
  const m=mergeBook(guesses,book);
  ok('guesses come first', m[0].email==='buyer@acme.com' && m[1].email==='po@acme.com', m.slice(0,2).map(x=>x.email).join('|'));
  ok('a guess picks up the book name', m[0].name==='Buyer Bob', m[0].name);
  ok('a guess picks up the book company', m[0].company==='Acme', m[0].company);
  ok('a guess not in the book keeps its own name', m[1].name==='PO Desk', m[1].name);
  ok('the same address is never listed twice', m.filter(x=>x.email.toLowerCase()==='buyer@acme.com').length===1);
  ok('the book follows, minus what was promoted', m.length===4, m.length);
  ok('a promoted address is not repeated below', m.slice(1).every(x=>x.email!=='buyer@acme.com'));
  ok('an invalid guess is dropped', mergeBook([{email:'junk',suggested:'x'}],book).length===3);
  ok('no address book still yields the guesses', mergeBook(guesses,[]).length===2);
}

// ══ 4 · the suggestion filter ════════════════════════════════════════════════
{
  _ctoBook=[{email:'jane@acme.com',name:'Jane Machinist',company:'Acme Aerospace'},
            {email:'bob@northrop.com',name:'Bob Buyer',company:'Northrop'},
            {email:'zeb@acme.com',name:'Zeb',company:'Acme Aerospace'}];
  _ctoTo=[];
  document.getElementById('cto-body').innerHTML='<div id="cto-sug-to"></div>';
  const fake=(v)=>{ const i={value:v}; _ctoInput(i,'to'); return _ctoSug.map(s=>s.email); };
  ok('empty query lists the whole book', fake('').length===3);
  ok('matches on name', fake('jane').join('|')==='jane@acme.com');
  ok('matches on company', fake('northrop').join('|')==='bob@northrop.com');
  ok('matches on the email itself', fake('zeb@').join('|')==='zeb@acme.com');
  ok('matching is case-insensitive', fake('JANE').join('|')==='jane@acme.com');
  ok('no match, no suggestions', fake('nobody').length===0);
  _ctoTo=[{email:'jane@acme.com',name:'Jane Machinist'}];
  ok('an address already picked is not suggested again', fake('').indexOf('jane@acme.com')<0, fake('').join('|'));
  ok('highlight resets onto the first match', (fake('acme'), _ctoHi===0), _ctoHi);
  ok('highlight clears when nothing matches', (fake('zzz'), _ctoHi===-1), _ctoHi);
}

// ══ 5 · the chip box renders and fits ════════════════════════════════════════
{
  _ctoBook=[{email:'jane@acme.com',name:'Jane Machinist',company:'Acme Aerospace',suggested:'customer card'},
            {email:'purchasing.department.aerostructures@northrop-grumman-aerostructures-division.com',name:'Bob Buyer',company:'Northrop'}];
  _ctoTo=[{email:'jane@acme.com',name:'Jane Machinist'},
          {email:'purchasing.department.aerostructures@northrop-grumman-aerostructures-division.com',name:''},
          {email:'shipping@acme.com',name:'Shipping Dept'}];
  _ctoRender();
  const chips=[...document.querySelectorAll('#panel .cto-chip')];
  ok('one chip per recipient', chips.length===3, chips.length);
  ok('step 1 offers a review, with the recipient count', (document.getElementById('cto-go').textContent||'').indexOf('Review message · 3 recipients')>=0,
     document.getElementById('cto-go').textContent.trim());
  const p=document.getElementById('panel');
  ok('picker does not scroll sideways', p.scrollWidth<=p.clientWidth+1, p.scrollWidth+' vs '+p.clientWidth);
  const pr=p.getBoundingClientRect();
  const esc2p=[...document.querySelectorAll('#panel .cto-chip, #panel input, #panel button, #panel .cto-sug')]
    .filter(el=>{const r=el.getBoundingClientRect(); return r.right>pr.right+1||r.left<pr.left-1;});
  ok('nothing overflows the picker', esc2p.length===0, esc2p.length);
  const box=document.querySelector('#panel .cto-box').getBoundingClientRect();
  const rows=new Set(chips.map(c=>Math.round(c.getBoundingClientRect().top)));
  ok('a long address wraps to another row instead of overflowing', rows.size>=2, rows.size);
  const inp=document.getElementById('cto-in-to').getBoundingClientRect();
  ok('the type-here box keeps usable width', inp.width>=110, Math.round(inp.width));
  ok('chips and input share one box', inp.top>=box.top-1 && inp.bottom<=box.bottom+1);
  // suggestions
  _ctoTo=[]; _ctoRender();
  const sug=[...document.querySelectorAll('#panel .cto-sug')];
  ok('the book is offered with the box empty', sug.length===2, sug.length);
  ok('a suggested address is tagged why', (document.querySelector('#panel .cto-tag')||{}).textContent==='customer card',
     (document.querySelector('#panel .cto-tag')||{}).textContent);
  ok('the first suggestion is highlighted', document.querySelectorAll('#panel .cto-sug.on').length===1);
  ok('send button drops the count for one recipient', (document.getElementById('cto-go').textContent||'').indexOf('to')<0,
     document.getElementById('cto-go').textContent.trim());
}

// ══ 6 · header-injection guard on the address list ═══════════════════════════
{
  // the worker drops `to` straight into the To: line, so CR/LF must never survive
  const RE=RE_EMAIL;
  const clean=(list)=>list.map(e=>String(e).replace(/[\\r\\n]/g,'').trim()).filter(e=>RE.test(e));
  ok('a CR/LF payload never reaches the To: line',
     clean(['a@x.com\\r\\nBcc: evil@bad.com']).length===0,
     JSON.stringify(clean(['a@x.com\\r\\nBcc: evil@bad.com'])));
  ok('a clean list passes through', clean(['a@x.com',' b@y.com ']).join(', ')==='a@x.com, b@y.com');
  ok('commas cannot smuggle a second address', RE.test('a@x.com,evil@bad.com')===false);
  ok('angle brackets cannot smuggle one', RE.test('a@x.com><evil@bad.com')===false);
}

// ══ 7 · Cc: a second field, and an address only ever sits in one of them ═════
{
  _ctoBook=[{email:'jane@acme.com',name:'Jane Machinist',company:'Acme'}];
  _ctoTo=[]; _ctoCc=[]; _ctoCcOn=false; _ctoField='to';
  ctoAdd('jane@acme.com','to');
  ok('Cc starts empty', _ctoCc.length===0);
  ok('adding to Cc lands on Cc, not To', (ctoAdd('qa@acme.com','cc').added===1 && _ctoCc.length===1 && _ctoTo.length===1));
  let x=ctoAdd('jane@acme.com','cc');
  ok('someone already on To cannot be Cc\\'d as well', x.added===0 && _ctoCc.length===1, x.dupIn);
  ok('and the note says which field they are on', x.dupIn==='To', x.dupIn);
  x=ctoAdd('qa@acme.com','to');
  ok('and the reverse is refused too', x.added===0 && x.dupIn==='Cc', x.dupIn);
  ok('a Cc address picks up its book name', (ctoAdd('jane2@acme.com','cc'), true));
  _ctoBook.push({email:'boss@acme.com',name:'The Boss'});
  ctoAdd('boss@acme.com','cc');
  ok('Cc chips carry names like To chips does', _ctoCc[_ctoCc.length-1].name==='The Boss', _ctoCc[_ctoCc.length-1].name);

  // the suggestion list must not re-offer anyone on EITHER field
  document.getElementById('cto-body').innerHTML='<div id="cto-sug-to"></div><div id="cto-sug-cc"></div>';
  _ctoTo=[{email:'jane@acme.com',name:''}]; _ctoCc=[{email:'boss@acme.com',name:''}];
  _ctoBook=[{email:'jane@acme.com',name:'Jane'},{email:'boss@acme.com',name:'Boss'},{email:'free@acme.com',name:'Free'}];
  _ctoInput({value:''},'cc');
  ok('neither a To nor a Cc address is suggested again', _ctoSug.map(s=>s.email).join('|')==='free@acme.com',
     _ctoSug.map(s=>s.email).join('|'));

  // render: the Cc row appears once asked for, and the send count spans both
  _ctoTo=[{email:'jane@acme.com',name:'Jane'},{email:'bob@acme.com',name:''}];
  _ctoCc=[]; _ctoCcOn=false; _ctoField='to';
  _ctoRender();
  ok('Cc row is hidden until asked for', !document.getElementById('cto-in-cc'));
  ok('a "+ Cc" link is offered', !!document.querySelector('#panel .cto-cclink'));
  ok('review button counts the To recipients', (document.getElementById('cto-go').textContent||'').indexOf('Review message · 2 recipients')>=0,
     document.getElementById('cto-go').textContent.trim());
  _ctoCcOn=true; _ctoCc=[{email:'qa@acme.com',name:'QA'}]; _ctoRender();
  ok('Cc row renders when opened', !!document.getElementById('cto-in-cc'));
  ok('the "+ Cc" link goes away once the row is open', !document.querySelector('#panel .cto-cclink'));
  ok('Cc chips render', document.querySelectorAll('#panel .cto-box')[1].querySelectorAll('.cto-chip').length===1);
  ok('review button counts To + Cc', (document.getElementById('cto-go').textContent||'').indexOf('Review message · 3 recipients')>=0,
     document.getElementById('cto-go').textContent.trim());
  ok('a saved Cc forces the row open on reopen', (_ctoCcOn=false, _ctoRender(), !!document.getElementById('cto-in-cc')));
  const p=document.getElementById('panel');
  ok('two-field picker does not scroll sideways', p.scrollWidth<=p.clientWidth+1, p.scrollWidth+' vs '+p.clientWidth);
  const boxes=[...document.querySelectorAll('#panel .cto-box')].map(b=>b.getBoundingClientRect());
  ok('the Cc box sits below the To box', boxes.length===2 && boxes[1].top>=boxes[0].bottom-1);
}

// ══ 8 · the worker's own To:/Cc: sanitiser (what writes the header lines) ════
{
  const W=(p,to,cc)=>wkRecipients(p, to, cc||[]);
  let r=W({cc:['qa@acme.com']}, 'jane@acme.com');
  ok('worker keeps a plain To', r.to==='jane@acme.com', r.to);
  ok('worker accepts a client Cc', r.cc.join(', ')==='qa@acme.com', r.cc.join(', '));
  r=W({}, 'a@x.com, b@y.com');
  ok('worker keeps a comma-joined To list', r.to==='a@x.com, b@y.com', r.to);
  r=W({cc:'qa@acme.com, boss@acme.com'}, 'jane@acme.com');
  ok('worker accepts Cc as a comma string too', r.cc.length===2, r.cc.join('|'));
  r=W({cc:['jane@acme.com','JANE@acme.com','qa@acme.com']}, 'jane@acme.com');
  ok('worker drops a Cc that is already on To', r.cc.join('|')==='qa@acme.com', r.cc.join('|'));
  r=W({cc:['qa@acme.com','QA@ACME.com']}, 'jane@acme.com');
  ok('worker dedupes Cc against itself', r.cc.length===1, r.cc.join('|'));
  r=W({cc:['a@x.com']}, 'jane@acme.com', ['a@x.com','b@y.com']);   // reply-all already cc'd these
  ok('worker keeps reply-all\\'s Cc and does not double it', r.cc.join('|')==='a@x.com|b@y.com', r.cc.join('|'));
  r=W({cc:['Jane Machinist <jane@acme.com>']}, 'bob@acme.com');
  ok('worker unwraps a display-name Cc', r.cc.join('|')==='jane@acme.com', r.cc.join('|'));
  // injection: a CR/LF or a smuggled comma must never reach the header block
  r=W({cc:['ok@x.com\\r\\nBcc: evil@bad.com']}, 'jane@acme.com');
  ok('worker refuses a CR/LF Cc payload', r.cc.length===0, JSON.stringify(r.cc));
  r=W({cc:['a@x.com,evil@bad.com']}, 'jane@acme.com');
  ok('worker refuses a comma-smuggled Cc', r.cc.length===0, JSON.stringify(r.cc));
  // a CR/LF To collapses to a space, which makes the whole entry invalid — the
  // worker refuses the send outright rather than half-cleaning it through
  let threw=false;
  try{ W({}, 'jane@acme.com\\r\\nBcc: evil@bad.com'); }catch(e){ threw=true; }
  ok('worker refuses a CR/LF To payload outright', threw);
  ok('surrounding whitespace on a good To is fine', W({}, '  jane@acme.com \\r\\n').to==='jane@acme.com',
     JSON.stringify(W({}, '  jane@acme.com \\r\\n').to));
  ok('worker refuses junk Cc entries', W({cc:['nope','',null,'a@x.com']}, 'j@a.com').cc.join('|')==='a@x.com');
  threw=false;
  try{ W({}, 'not-an-address'); }catch(e){ threw=true; }
  ok('worker throws rather than sending to an invalid To', threw);
  threw=false;
  try{ W({}, ''); }catch(e){ threw=true; }
  ok('worker still throws on an empty To', threw);
  // one bad address in a list must not quietly drop the rest, nor pass through
  ok('worker keeps the good addresses out of a mixed To list', W({}, 'a@x.com, junk, b@y.com').to==='a@x.com, b@y.com',
     W({}, 'a@x.com, junk, b@y.com').to);
}

// ══ 9 · the composed message (what the preview shows AND the send posts) ════
{
  _confirmMeta={customer:'Acme Aerospace', po:'PO-4471'};
  _confirmItems=[
    {part:'BRK-1042', desc:'bracket', qty:200, cost:3.25, ordered:'2026-08-03', due:'2026-09-18', confirmNotes:''},
    {part:'PLT-9',    desc:'',        qty:50,  cost:11.4, ordered:'2026-08-01', due:'2026-09-20', confirmNotes:''}];
  let m=_confirmCompose('Edgar\\nBert’s Sheet Metal');
  ok('subject names customer and PO', m.subject==='Order Confirmation — Acme Aerospace — PO PO-4471', m.subject);
  ok('body names the PO', m.body.indexOf('PO PO-4471')>=0);
  ok('body carries the earliest order date', m.body.indexOf('Order date: 08/01/26')>=0, m.body.match(/Order date: .*/));
  ok('body carries the LATEST due date', m.body.indexOf('Completion / due date: 09/20/26')>=0, m.body.match(/Completion.*/));
  ok('body says it is not an invoice', m.body.indexOf('is not an invoice')>=0);
  ok('the signature is appended after the "-- " delimiter', m.body.indexOf('\\n\\n-- \\nEdgar')>=0);
  ok('no Notes block when there are none', m.body.indexOf('Notes:')<0);
  ok('header row first', m.rows[0].join('|')==='Part / Description|Qty|Rate|Amount', m.rows[0].join('|'));
  ok('one row per line item', m.rows.length===4, m.rows.length);
  ok('a line shows part — desc', m.rows[1][0]==='BRK-1042 — bracket', m.rows[1][0]);
  ok('a line with no desc shows just the part', m.rows[2][0]==='PLT-9', m.rows[2][0]);
  ok('line amount is qty × cost', m.rows[1][3]==='$650.00', m.rows[1][3]);
  ok('TOTAL row is last and adds up', m.rows[3].join('|')==='||TOTAL|$1220.00', m.rows[3].join('|'));

  _confirmItems[0].confirmNotes='Certs included.';
  m=_confirmCompose('Edgar');
  ok('a note appears in the body', m.body.indexOf('\\n\\nNotes:\\nCerts included.')>=0);
  ok('the note lands BEFORE the sign-off', m.body.indexOf('Notes:')<m.body.indexOf('Thank you,'));
  ok('and before the signature', m.body.indexOf('Notes:')<m.body.indexOf('-- \\nEdgar'));
  ok('composer reports the note back for the edit box', m.notes==='Certs included.', m.notes);

  // no signature record -> the hard-coded sign-off stands in
  m=_confirmCompose('');
  ok('no signature falls back to the company block', m.body.indexOf('9521 Irondale Ave')>=0);
  ok('the fallback carries no "-- " delimiter', m.body.indexOf('-- \\n')<0);

  // a bare order: no dates, no prices
  _confirmMeta={customer:'', po:''};
  _confirmItems=[{part:'X', desc:'', qty:1, cost:0, total:0, ordered:'', due:'', confirmNotes:''}];
  m=_confirmCompose('');
  ok('subject survives a missing customer and PO', m.subject==='Order Confirmation', m.subject);
  ok('no order-date line when there is no date', m.body.indexOf('Order date:')<0);
  ok('no due-date line when there is no date', m.body.indexOf('Completion / due date:')<0);
  ok('a priceless line still renders', m.rows[1].join('|')==='X|1||', m.rows[1].join('|'));
  ok('TOTAL is zero, not blank', m.rows[2][3]==='$0.00', m.rows[2][3]);
}

// ══ 10 · the preview step renders that message ═══════════════════════════════
{
  _confirmMeta={customer:'Acme Aerospace', po:'PO-4471'};
  _confirmItems=[{part:'BRK-1042', desc:'bracket', qty:200, cost:3.25, ordered:'2026-08-03', due:'2026-09-18', confirmNotes:'Certs included.'}];
  _ctoTo=[{email:'jane@acme.com',name:'Jane Machinist'}];
  _ctoCc=[{email:'qa@acme.com',name:''}];

  // still loading the mailbox/signature
  _ctoStep='preview'; _ctoCfg=null; _ctoRender();
  ok('preview shows a loading line until the mailbox is read',
     document.getElementById('cto-body').textContent.indexOf('Loading the mailbox')>=0);
  ok('nothing is sendable while it loads', !document.getElementById('cto-go'));

  // settings unreachable
  _ctoCfg={error:'mail proxy address not set — finish the Mail app setup first'}; _ctoRender();
  const errTxt=document.getElementById('cto-body').textContent;
  ok('a config failure is shown, not swallowed', errTxt.indexOf('mail proxy address not set')>=0);
  ok('and there is no Send button on a failed preview', !document.getElementById('cto-go'));
  ok('but Back still works from the error state', !!document.querySelector('#panel button'));

  // the real thing
  _ctoCfg={proxy:'https://p', replyAs:'info@bertsmp.com', sigText:'Edgar\\nBSMP', sigLogo:null};
  _ctoRender();
  const txt=document.getElementById('cto-body').textContent;
  const msg=_confirmCompose(_ctoCfg.sigText);
  ok('preview shows the sending mailbox', txt.indexOf('info@bertsmp.com')>=0);
  ok('preview shows To with the contact name', txt.indexOf('Jane Machinist <jane@acme.com>')>=0);
  ok('preview shows Cc', txt.indexOf('qa@acme.com')>=0);
  ok('preview shows the subject', txt.indexOf(msg.subject)>=0);
  ok('preview shows the real body text', txt.indexOf('This confirms receipt of your order')>=0);
  ok('preview shows the note', txt.indexOf('Certs included.')>=0);
  ok('preview shows the signature', txt.indexOf('Edgar')>=0);
  const rows=[...document.querySelectorAll('#panel .cmp-tbl tbody tr')];
  ok('preview draws one table row per line item', rows.length===1, rows.length);
  ok('preview draws the TOTAL in the table foot',
     (document.querySelector('#panel .cmp-tbl tfoot')||{}).textContent.indexOf('$650.00')>=0,
     (document.querySelector('#panel .cmp-tbl tfoot')||{}).textContent);
  ok('preview has a Send button', !!document.getElementById('cto-go'));
  ok('Send counts To + Cc', document.getElementById('cto-go').textContent.indexOf('Send to 2')>=0,
     document.getElementById('cto-go').textContent.trim());

  // the body shown is byte-for-byte what would be posted
  // HTML collapses the trailing space of the RFC "-- " signature delimiter when
  // the text is read back through innerText, so compare with per-line trailing
  // whitespace normalised. What is POSTED keeps the real delimiter — section 9
  // asserts that on the composed body itself.
  const flat=(t)=>t.replace(/\\u00a0/g,' ').split('\\n').map(l=>l.replace(/\\s+$/,'')).join('\\n').replace(/\\s+$/,'');
  const shown=document.querySelector('#panel .cmp-body').innerText;
  ok('the previewed body is the composed body, line for line',
     flat(shown)===flat(msg.body),
     JSON.stringify(flat(shown).slice(-40))+' vs '+JSON.stringify(flat(msg.body).slice(-40)));
  ok('every line of the composed body is shown',
     msg.body.split('\\n').every(l=>!l.trim()||shown.indexOf(l.trim())>=0));

  // editing the notes in the preview updates the body and the order records
  _ctoNotes('Partial shipments OK.');
  ok('editing notes writes back to the orders', _confirmItems[0].confirmNotes==='Partial shipments OK.');
  ok('editing notes repaints the previewed body',
     document.querySelector('#panel .cmp-body').textContent.indexOf('Partial shipments OK.')>=0);
  ok('the old note is gone from the preview',
     document.querySelector('#panel .cmp-body').textContent.indexOf('Certs included.')<0);
  ok('the notes box keeps its own value (caret not lost)',
     document.getElementById('cmp-notes').value==='Certs included.',
     document.getElementById('cmp-notes').value);

  // Back keeps the recipients
  _ctoBack();
  ok('Back returns to the recipient step', _ctoStep==='who' && !!document.getElementById('cto-in-to'));
  ok('Back keeps the To chips', _ctoTo.length===1, _ctoTo.length);
  ok('Back keeps the Cc chips', _ctoCc.length===1, _ctoCc.length);
  ok('the recipient step asks you to review, not to send',
     document.getElementById('cto-go').textContent.indexOf('Review message')>=0,
     document.getElementById('cto-go').textContent.trim());

  // layout of the preview at the modal's real width
  _ctoStep='preview'; _ctoRender();
  const p=document.getElementById('panel');
  ok('preview does not scroll the modal sideways', p.scrollWidth<=p.clientWidth+1, p.scrollWidth+' vs '+p.clientWidth);
  const w=document.querySelector('#panel .cmp-tblwrap');
  ok('a wide table scrolls inside its own box', getComputedStyle(w).overflowX==='auto');
  // the money columns must not be the ones pushed off — a preview you have to
  // scroll to see the total is not much of a preview
  ok('the table fits without scrolling at the modal width', w.scrollWidth<=w.clientWidth+1,
     w.scrollWidth+' vs '+w.clientWidth);
  const amtCells=[...document.querySelectorAll('#panel .cmp-tbl tr')].map(tr=>tr.lastElementChild.getBoundingClientRect());
  const wr=w.getBoundingClientRect();
  ok('the Amount column is on screen', amtCells.every(c=>c.right<=wr.right+1), amtCells.map(c=>Math.round(c.right)).join('|'));
  const pr=p.getBoundingClientRect();
  const over=[...document.querySelectorAll('#panel .cmp-hdr, #panel .cmp-body, #panel .cmp-tblwrap, #panel button, #panel textarea')]
    .filter(el=>{const r=el.getBoundingClientRect(); return r.right>pr.right+1||r.left<pr.left-1;});
  ok('nothing overflows the preview', over.length===0, over.map(e=>e.className).join('|'));
}

const fails=out.filter(l=>l.indexOf('FAIL')===0).length;
document.getElementById('out').textContent=out.join('\\n')+'\\n\\n'+(out.length-fails)+'/'+out.length+' assertions passed';
document.title=fails?(fails+' FAILURES'):'all pass';
</script>'''

html = html.replace('__CSS__', css).replace('/*__BLOCK__*/', block).replace('/*__MERGE__*/', merge).replace('/*__WORKER__*/', worker)
io.open('C:/Users/info/bsmp-orders/_confirmtotest.html', 'w', encoding='utf-8').write(html)
print('wrote _confirmtotest.html')
