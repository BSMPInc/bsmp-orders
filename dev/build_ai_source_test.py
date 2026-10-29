# Slices the REAL AI Extract modal (HTML + CSS + JS) out of orders.html into a
# standalone test page with Firebase, the mail worker and the AI worker stubbed,
# plus a 2-page sample PO PDF. Run this, then open
#   http://localhost:8123/_aisrctest.html            (hand upload / mail hand-off buttons)
# (python http.server from .claude/launch.json — the Browser pane refuses file:// URLs).
# Page title says "all pass" or "FAILURES" after "Run checks"; delete _aisrctest.html
# and _aisrc_po.pdf when done.
import io, re
ROOT = 'C:/Users/info/bsmp-orders/'
src = io.open(ROOT + 'orders.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

head = src[:src.index('</head>')]
links = '\n'.join(re.findall(r'<link[^>]+>', head))
styles = '\n'.join(re.findall(r'<style[\s\S]*?</style>', head))
modal = grab('<!-- AI Modal -->', '<!-- Add/Edit Customer Modal -->')
js = grab("window.closeModal=(id)=>", "\nwindow.exportCSV")
fmt = grab('function fmtMoney(v){', '\n')
esc = grab('function esc2(s){', '\n')

# ── a tiny 2-page PDF (hand-written objects, xref offsets computed) ──
def pdf(pages):
    objs = ['<< /Type /Catalog /Pages 2 0 R >>',
            '<< /Type /Pages /Kids [%s] /Count %d >>' % (' '.join('%d 0 R' % (4 + 2*i) for i in range(len(pages))), len(pages)),
            '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    for lines in pages:
        body = 'BT /F1 13 Tf 60 740 Td 18 TL ' + ' '.join('(%s) Tj T*' % l for l in lines) + ' ET'
        objs.append('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>' % (5 + 2*(len(objs)-3)//2))
        objs.append('<< /Length %d >>\nstream\n%s\nendstream' % (len(body), body))
    out = '%PDF-1.4\n'; offs = []
    for i, o in enumerate(objs):
        offs.append(len(out)); out += '%d 0 obj\n%s\nendobj\n' % (i + 1, o)
    x = len(out)
    out += 'xref\n0 %d\n0000000000 65535 f \n' % (len(objs) + 1) + ''.join('%010d 00000 n \n' % o for o in offs)
    out += 'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objs) + 1, x)
    return out.encode('latin-1')

io.open(ROOT + '_aisrc_po.pdf', 'wb').write(pdf([
    ['ACME FABRICATION INC.  PURCHASE ORDER 45110', 'Vendor: Bert\'s Sheet Metal Products', '',
     'Line 1   BRK-2201 Rev C   14ga 304 SS bracket   Qty 50   Unit 12.40', 'Line 2   PNL-88 Rev A   .080 5052 panel   Qty 12   Unit 48.00',
     '', 'Page 1 of 2'],
    ['ACME FABRICATION INC.  PO 45110 (continued)', '', 'Line 3   CVR-17   11ga CRS cover   Qty 6   Unit 95.00', 'Required date: 2026-11-20', '', 'Page 2 of 2']]))

html = u'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI source pane test</title>
%s
%s
<style>body{background:var(--bg);font-family:'Hanken Grotesk',sans-serif;margin:0;padding:12px}#tb{display:flex;gap:6px;flex-wrap:wrap}#log{font:11px ui-monospace,monospace;white-space:pre-wrap}</style>
</head><body>
<div id="tb">
<button class="btn" onclick="openAI()">Open AI Extract (empty)</button>
<button class="btn" onclick="tMail(true,true)">Mail hand-off: PDF + email</button>
<button class="btn" onclick="tMail(false,true)">Mail hand-off: email body only</button>
<button class="btn" onclick="tMail(true,true,true)">Mail hand-off: one bad attachment</button>
<button class="btn" onclick="tUpload()">Hand upload PDF</button>
<button class="btn" onclick="runChecks()">Run checks</button>
</div>
<pre id="log"></pre>
%s
<script>
%s
%s
// ── stubs: the bits of orders.html the AI modal leans on ──
const STATUSES=['Received','In Progress','Complete'];
let orders=[], expanded=new Set(), aiParsed=[], _n=0;
function uid(){ return 'o'+(++_n); }
function suggestJobNumber(c,p){ return 'J'+(2700+_n); }
function maybeAdvanceCounter(){} function autoIndexCustomer(){} function revealNewOrder(){} function render(){} function showPage(){}
function saveDB(){ window._saved=JSON.parse(JSON.stringify(orders)); }
const db={}; const ref=(d,p)=>p;
const get=async p=>({val:()=>({proxyUrl:location.origin+'/_fakeproxy/'})});
const update=async(p,v)=>{ window._linked={p,v}; };
const auth={currentUser:{getIdToken:async()=>'tok'}};
const AI_ROWS=[{customer:'Acme Fabrication Inc.',po:'45110',job:'',part:'BRK-2201 Rev C',desc:'14ga 304 SS',qty:50,cost:12.4,due:'2026-11-20',status:'',poNotes:''},
  {customer:'Acme Fabrication Inc.',po:'45110',job:'',part:'PNL-88 Rev A',desc:'.080 5052',qty:12,cost:48,due:'2026-11-20',status:'',poNotes:''},
  {customer:'Acme Fabrication Inc.',po:'45110',job:'',part:'',desc:'11ga CRS',qty:'6',cost:'$95.00',due:'Nov 20',status:'',poNotes:'Cust Job 8111'}];
const realFetch=window.fetch.bind(window); window._aiReq=null; window._attFail=false;
window.fetch=async(url,opt)=>{
  url=String(url);
  if(url.includes('/_fakeproxy/attachment')){
    if(window._attFail && url.includes('id=a2')) return new Response('nope',{status:502});
    const b=await (await realFetch('_aisrc_po.pdf')).blob();
    return new Response(b,{status:200,headers:{'Content-Type':'application/octet-stream'}});
  }
  if(url.includes('bsmp-ai-extract')){
    window._aiReq=JSON.parse(opt.body);
    await new Promise(r=>setTimeout(r,500));
    return new Response(JSON.stringify({content:[{type:'text',text:'```json\\n'+JSON.stringify(AI_ROWS)+'\\n```'}]}));
  }
  return realFetch(url,opt);
};
const EMAIL='FROM: Dana Ruiz <dana@acmefab.example>  DATE: 10/29/2026\\nHi Bert\\'s,\\n\\nPlease see attached PO 45110 for 3 parts. Need them by 11/20.\\n\\nThanks,\\nDana\\n\\n----\\n\\nFROM: Edgar <ofc.edgar@bertsmp.com>  DATE: 10/22/2026\\nQuote attached: BRK-2201 $12.40, PNL-88 $48.00, CVR-17 $95.00.\\n';
function tMail(withPdf, withText, oneBad){
  window._attFail=!!oneBad;
  const atts=withPdf?[{b:'box1',m:'m1',a:'a1',t:'application/octet-stream',n:'PO_45110.pdf'}].concat(oneBad?[{b:'box1',m:'m1',a:'a2',t:'application/pdf',n:'drawing.pdf'}]:[]):[];
  localStorage.setItem('bsmp_poMailText',JSON.stringify({key:'thr1',at:Date.now(),text:withText?EMAIL:''}));
  history.replaceState(null,'','?fromMail=thr1&cust='+encodeURIComponent('Dana Ruiz')+'&subj='+encodeURIComponent('PO 45110')+(atts.length?'&atts='+encodeURIComponent(JSON.stringify(atts)):''));
  _mailParamsDone=false; handleMailParams();
}
async function tUpload(){
  const b=await (await realFetch('_aisrc_po.pdf')).blob();
  _fromMailKey=''; _fromMailText=''; openAI();
  await aiReadUpload(new File([b],'Acme PO 45110.pdf',{type:'application/pdf'}));
}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function runChecks(){
  const out=[]; const ok=(n,c,x)=>out.push((c?'PASS':'FAIL')+'  '+n+(x!=null?'   ['+x+']':''));
  const $=id=>document.getElementById(id);
  // 1 · mail hand-off with a PDF and the email text
  orders=[]; tMail(true,true); await wait(1500);
  const req=window._aiReq, c=req&&req.messages[0].content;
  ok('modal split open', $('ai-modal-box').classList.contains('has-src'));
  ok('stale email text removed from localStorage', localStorage.getItem('bsmp_poMailText')===null);
  ok('AI got the PDF document', c&&c[0].type==='document'&&c[0].source.media_type==='application/pdf');
  ok('AI got the email text', c&&/EMAIL:\\n[\\s\\S]*PO 45110/.test(c[c.length-1].text));
  ok('prompt ends with the JSON rule', c&&/Return ONLY valid JSON, no markdown\\.$/.test(c[c.length-1].text));
  ok('two source tabs (PDF + email)', document.querySelectorAll('#mp-src-tabs .mp-src-tab').length===2);
  ok('PDF iframe shown first', !!document.querySelector('#mp-src-body iframe'));
  ok('octet-stream became a PDF blob', _aiSrc.docs[0].file.type==='application/pdf', _aiSrc.docs[0].file.type);
  ok('3 editable rows', document.querySelectorAll('#ai-rows .ai-row').length===3);
  ok('header customer/PO filled', $('ai-cust').value==='Acme Fabrication Inc.'&&$('ai-po').value==='45110');
  ok('non-ISO due left blank', aiParsed[2].due==='');
  ok('missing part flagged', document.querySelectorAll('#ai-rows .ai-row')[2].querySelector('input.miss')!=null);
  ok('import button counts lines', /Import 3 orders/.test($('ai-import-btn').textContent), $('ai-import-btn').textContent.trim());
  // edit: fix the missing part, change a qty, rename the PO in the header
  const r3=document.querySelectorAll('#ai-rows .ai-row')[2].querySelectorAll('.ai-grid input');
  r3[0].value='CVR-17'; r3[0].dispatchEvent(new Event('input'));
  ok('fixing the part clears the flag', !r3[0].classList.contains('miss'));
  const r1=document.querySelectorAll('#ai-rows .ai-row')[0].querySelectorAll('.ai-grid input');
  r1[1].value='55'; r1[1].dispatchEvent(new Event('input'));
  ok('line total updates', /55 × \\$12.4 = \\$682.00/.test($('ai-tot-0').textContent), $('ai-tot-0').textContent);
  $('ai-po').value='45110-A'; $('ai-po').dispatchEvent(new Event('input'));
  aiAddRow(); ok('add line', aiParsed.length===4&&aiParsed[3].po==='45110-A');
  aiDelRow(3); ok('remove line', aiParsed.length===3);
  importAIOrders();
  const s=window._saved||[];
  ok('3 orders saved', s.length===3, s.length);
  ok('edited qty saved', s.some(o=>o.part==='BRK-2201 Rev C'&&o.qty===55&&o.total===55*12.4));
  ok('header PO applied to every line', s.every(o=>o.po==='45110-A'));
  ok('$95.00 parsed as 95', s.some(o=>o.part==='CVR-17'&&o.cost===95));
  ok('mailKey stamped', s.every(o=>o.mailKey==='thr1'));
  ok('mail thread linked back', window._linked&&window._linked.p==='mail/threads/thr1');
  ok('modal closed after import', $('ai-modal').style.display==='none');
  // 2 · email body only (no attachment)
  orders=[]; window._aiReq=null; tMail(false,true); await wait(1200);
  const c2=window._aiReq&&window._aiReq.messages[0].content;
  ok('body-only: AI read text only', c2&&c2.length===1&&/There is no attached document/.test(c2[0].text));
  ok('body-only: email tab shown', $('mp-src-body').querySelector('.mp-src-text')!=null&&/Dana/.test($('mp-src-body').textContent));
  // 3 · one attachment fails to load
  window._aiReq=null; tMail(true,true,true); await wait(1500);
  const c3=window._aiReq&&window._aiReq.messages[0].content;
  ok('bad attachment: the good PDF still sent', c3&&c3.filter(x=>x.type==='document').length===1);
  ok('bad attachment: noted in status', /Couldn’t load drawing\\.pdf/.test($('ai-status').textContent), $('ai-status').textContent);
  aiSrcTab(1); ok('bad attachment: error note in its tab', /Couldn’t load drawing\\.pdf/.test($('mp-src-body').textContent));
  // 4 · hand upload
  window._aiReq=null; await tUpload(); await wait(200);
  ok('upload: no email tab', document.querySelectorAll('#mp-src-tabs .mp-src-tab').length===1);
  ok('upload: no mailKey link armed', _fromMailKey==='');
  closeAI();
  $('log').textContent=out.join('\\n');
  document.title=out.some(l=>l.startsWith('FAIL'))?'FAILURES':'all pass';
}
</script></body></html>''' % (links, styles, modal, esc, fmt + '\n' + js)

io.open(ROOT + '_aisrctest.html', 'w', encoding='utf-8').write(html)
print('wrote _aisrctest.html + _aisrc_po.pdf')
