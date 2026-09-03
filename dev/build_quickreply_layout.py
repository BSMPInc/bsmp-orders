# Renders the REAL reply box and the REAL quick-reply editor with the REAL mail.html CSS,
# so the chip row can be checked for fit and overflow. Run this, then open
# http://localhost:8123/_quicklayout.html - the title says "all pass" or "FAILURES".
# Delete _quicklayout.html when done.
import io, re
src = io.open('C:/Users/info/bsmp-orders/mail.html', encoding='utf-8').read()

def grab(start, end, inclusive_end=True):
    a = src.index(start); b = src.index(end, a)
    return src[a:b+(len(end) if inclusive_end else 0)]

css   = '\n'.join(re.findall(r'<style>(.*?)</style>', src, re.S))
reply = grab('<div class="reply" id="reply-box">', '<div class="hint" id="reply-sig-hint"></div>') + '</div>'
modal = grab('<!-- quick replies: the chips above the reply box -->', '<!-- material price capture -->', False)
compose = grab('<div class="modal-bg" id="compose-modal">', '<!-- quick replies: the chips above the reply box -->', False)
block = grab(u'// \u2500\u2500 quick replies (shared', u'// \u2500\u2500 outgoing attachments', False)

html = u'''<!doctype html><html><head><meta charset="utf-8"><title>quick reply layout</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>__CSS__
body{padding:14px;background:var(--bg)}
#out{font:12px ui-monospace,monospace;white-space:pre-wrap;background:#fff;border:1px dashed #c9d0da;padding:8px;margin-bottom:12px}
.host{max-width:900px;background:var(--card);border:1px solid var(--border)}
/* the modals are real modals - show them in place so they can be measured */
#quick-modal,#compose-modal{position:static;display:block!important;background:none;padding:0;margin-top:16px}
</style></head><body>
<div id="out"></div>
<div class="host">__REPLY__</div>
__COMPOSE__
__MODAL__
<script>
function $(id){ return document.getElementById(id); }
const esc=(s)=>(s==null?'':String(s)).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
function toast(){}
let QUICK={}, CURRENT={messages:[{from:'Jane Smith', fromEmail:'jane@acme.com'}]};
let SETTINGS={mailboxes:['info@bertsmp.com']};
const ownAddr=(a)=>(SETTINGS.mailboxes||[]).some(mb=>mb.toLowerCase()===(a||'').toLowerCase());
function replyToRecipient(){ return 'jane@acme.com'; }
const auth={currentUser:{uid:'me', email:'ofc.edgar@bertsmp.com'}};
function autoGrowReply(ta){ ta.style.height='auto'; ta.style.height=Math.min(ta.scrollHeight+2,220)+'px'; }
window._draftTick=()=>{};
const db=null;
function ref(_d,path){ return {path:path}; }
function set(){ return Promise.resolve(); }
function remove(){ return Promise.resolve(); }
function renderSigHints(){}
let CONTACTS={};
const mkey=(e)=>(e||'').toLowerCase().replace(/[.#$\\/\\[\\]]/g,'_');
function acInput(){}
function acKey(){}
function closeCompose(){}
function sendCompose(){}
function renderOutAtts(){}
function toggleReplyAll(){}
function aiDraftReply(){}
function pickAtt(){}
function openTable(){}
function sendReply(){}
function collapseReply(){}
function expandReply(){}
/*__BLOCK__*/

$('reply-box').classList.add('open');
$('cp-to').value='ben.walker@acme.com';
renderQuickRow();
_qrEdit=quickList().slice(0,3).map(q=>({id:q.id,label:q.label,text:q.text}));
renderQuickEdit();

const out=[]; const ok=(n,c,x)=>out.push((c?'PASS':'FAIL')+'  '+n+(x!=null?('   ['+x+']'):''));
function check(){
  if(!innerWidth) return;                       // the Browser pane runs hidden pages at width 0
  out.length=0;
  const row=$('quick-row'), chips=[...row.querySelectorAll('.qr-chip')];
  const rr=row.getBoundingClientRect();
  ok('the chip row is showing when the reply box is open', getComputedStyle(row).display==='flex');
  ok('a chip per starter, plus Edit', chips.length===8, chips.length);
  ok('the chips sit on one line', new Set(chips.map(c=>Math.round(c.getBoundingClientRect().top))).size===1,
     chips.map(c=>Math.round(c.getBoundingClientRect().top)).join(','));
  ok('the row never gets taller than one chip', rr.height<=44, Math.round(rr.height));
  ok('overflowing chips scroll sideways instead of being cut off',
     getComputedStyle(row).overflowX==='auto' && row.scrollWidth>=Math.round(rr.width)-1,
     Math.round(row.scrollWidth)+' in '+Math.round(rr.width));
  const first=chips[0].getBoundingClientRect();
  ok('the first chip is visible in the row', first.width>0 && first.left>=rr.left-0.5 && first.top>=rr.top-0.5);
  ok('the Edit chip is reachable', chips[chips.length-1].textContent.indexOf('Edit')>-1);
  const btm=$('reply-body').getBoundingClientRect();
  ok('the chips sit above the text box, not over it', rr.bottom<=btm.top+0.5, Math.round(rr.bottom)+' vs '+Math.round(btm.top));
  // the editor
  const erows=[...document.querySelectorAll('#qr-rows .qr-row')];
  ok('the editor draws a row per chip', erows.length===3, erows.length);
  const f=erows[0].querySelector('.qr-label').getBoundingClientRect();
  const t=erows[0].querySelector('.qr-text').getBoundingClientRect();
  const acts=erows[0].querySelector('.qr-acts').getBoundingClientRect();
  const er=erows[0].getBoundingClientRect();
  ok('label and text stack, both full width', Math.abs(f.width-t.width)<1 && t.top>=f.bottom-0.5, Math.round(f.width)+'/'+Math.round(t.width));
  ok('the fields do not run under the buttons', f.right<=acts.left+0.5, Math.round(f.right)+' vs '+Math.round(acts.left));
  ok('the buttons stay inside the row', acts.right<=er.right+0.5 && acts.top>=er.top-0.5);
  ok('all three row buttons are there', erows[0].querySelectorAll('.icon-btn').length===3);
  ok('the message box is not the tall compose one', t.height<90, Math.round(t.height));
  // squeeze it: on a narrow panel the chips must scroll, never wrap or clip
  const host=document.querySelector('.host'), was=host.style.maxWidth;
  host.style.maxWidth='420px';
  const row2=$('quick-row'), chips2=[...row2.querySelectorAll('.qr-chip')];
  const rr2=row2.getBoundingClientRect();
  ok('squeezed narrow, the chips still sit on one line',
     new Set(chips2.map(c=>Math.round(c.getBoundingClientRect().top))).size===1);
  ok('squeezed narrow, the row is still one chip tall', rr2.height<=44, Math.round(rr2.height));
  ok('squeezed narrow, the row scrolls', row2.scrollWidth>row2.clientWidth+1,
     row2.scrollWidth+' > '+row2.clientWidth);
  row2.scrollLeft=row2.scrollWidth;
  ok('scrolling reaches the Edit chip at the end', row2.scrollLeft>0);
  row2.scrollLeft=0; host.style.maxWidth=was;
  // the same row inside the new-email window
  const crow=$('quick-row-cp'), cchips=[...crow.querySelectorAll('.qr-chip')];
  const cr=crow.getBoundingClientRect(), cb=$('cp-body').getBoundingClientRect();
  const cmodal=document.querySelector('#compose-modal .modal').getBoundingClientRect();
  ok('the compose window shows the chips', getComputedStyle(crow).display==='flex' && cchips.length===8, cchips.length);
  ok('compose chips sit on one line', new Set(cchips.map(c=>Math.round(c.getBoundingClientRect().top))).size===1);
  ok('the compose row is one chip tall', cr.height<=44, Math.round(cr.height));
  ok('the compose chips sit above the message box', cr.bottom<=cb.top+0.5, Math.round(cr.bottom)+' vs '+Math.round(cb.top));
  ok('the compose row stays inside the window', cr.left>=cmodal.left-0.5 && cr.right<=cmodal.right+0.5);
  ok('the compose row scrolls rather than clipping',
     getComputedStyle(crow).overflowX==='auto' && crow.scrollWidth>crow.clientWidth+1,
     crow.scrollWidth+' > '+crow.clientWidth);
  ok('a compose chip is aimed at the compose box', crow.innerHTML.indexOf("'compose'")>-1);
  const fails=out.filter(l=>l.slice(0,4)==='FAIL').length;
  document.title = fails? ('FAILURES ('+fails+')') : ('all pass ('+out.length+')');
  $('out').textContent='viewport '+innerWidth+'px\\n'+out.join('\\n');
}
check();
addEventListener('resize', check);
</script></body></html>'''

html = (html.replace('__CSS__', css).replace('__REPLY__', reply).replace('__MODAL__', modal)
            .replace('__COMPOSE__', compose).replace('/*__BLOCK__*/', block))
io.open('C:/Users/info/bsmp-orders/_quicklayout.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _quicklayout.html (%d chars)' % len(html))
