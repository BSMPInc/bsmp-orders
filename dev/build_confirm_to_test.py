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

# the picker: RE_EMAIL / ctoParse / ctoAdd / the handlers / _ctoRender
block  = grab('const RE_EMAIL=', '\nwindow.emailConfirmation=')
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
  #panel{width:520px!important;max-width:520px!important;flex:none!important;overflow-x:auto;border:1px solid #ccc;box-sizing:border-box;padding:14px}
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
            {email:'purchasing@northrop-grumman-aerostructures.com',name:'Bob Buyer',company:'Northrop'}];
  _ctoTo=[{email:'jane@acme.com',name:'Jane Machinist'},
          {email:'purchasing@northrop-grumman-aerostructures.com',name:''},
          {email:'shipping@acme.com',name:'Shipping Dept'}];
  _ctoRender();
  const chips=[...document.querySelectorAll('#panel .cto-chip')];
  ok('one chip per recipient', chips.length===3, chips.length);
  ok('the send button counts them', (document.getElementById('cto-go').textContent||'').indexOf('Send to 3')>=0,
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
  ok('send counts the To recipients', (document.getElementById('cto-go').textContent||'').indexOf('Send to 2')>=0,
     document.getElementById('cto-go').textContent.trim());
  _ctoCcOn=true; _ctoCc=[{email:'qa@acme.com',name:'QA'}]; _ctoRender();
  ok('Cc row renders when opened', !!document.getElementById('cto-in-cc'));
  ok('the "+ Cc" link goes away once the row is open', !document.querySelector('#panel .cto-cclink'));
  ok('Cc chips render', document.querySelectorAll('#panel .cto-box')[1].querySelectorAll('.cto-chip').length===1);
  ok('send counts To + Cc', (document.getElementById('cto-go').textContent||'').indexOf('Send to 3')>=0,
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

const fails=out.filter(l=>l.indexOf('FAIL')===0).length;
document.getElementById('out').textContent=out.join('\\n')+'\\n\\n'+(out.length-fails)+'/'+out.length+' assertions passed';
document.title=fails?(fails+' FAILURES'):'all pass';
</script>'''

html = html.replace('__CSS__', css).replace('/*__BLOCK__*/', block).replace('/*__MERGE__*/', merge).replace('/*__WORKER__*/', worker)
io.open('C:/Users/info/bsmp-orders/_confirmtotest.html', 'w', encoding='utf-8').write(html)
print('wrote _confirmtotest.html')
