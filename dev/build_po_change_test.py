# PO change mode test: slices the REAL AI Extract modal (HTML + CSS + JS) out of
# orders.html into a standalone page with Firebase stubbed and a board that already
# holds Fluid Line PO 36241 (a plain line, a part split into two runs, an invoiced
# line, a line the revision drops) plus another customer's PO 36241.
# Run this, then open http://localhost:8123/_pochgtest.html and press "Run checks"
# (title says "all pass" or "FAILURES"). Delete _pochgtest.html when done.
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
helpers = '\n'.join([grab('function fmtMoney(v){', '\n'), grab('function esc2(s){', '\n'), grab('function fmtDate(d){', '\n'),
                     grab('const podKey = ', '\n'), grab('const podHit = ', '\n')])

html = u'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>PO change test</title>
%s
%s
<style>body{background:var(--bg);font-family:'Hanken Grotesk',sans-serif;margin:0;padding:12px}#tb{display:flex;gap:6px;flex-wrap:wrap}#log{font:11px ui-monospace,monospace;white-space:pre-wrap}</style>
</head><body>
<div id="tb">
<button class="btn" onclick="tOpen()">Open revised PO 36241</button>
<button class="btn" onclick="runChecks()">Run checks</button>
</div>
<pre id="log"></pre>
%s
<script>
%s
// ── stubs: the bits of orders.html the AI modal leans on ──
const STATUSES=['Received','Confirmed','In Progress','Need Purchase Order','Completed','Ready for Invoice','Invoiced'];
let orders=[], expanded=new Set(), aiParsed=[], _n=0;
function uid(){ return 'n'+(++_n); }
function suggestJobNumber(c,p){ return '2701-'+(orders.filter(o=>o.po===p).length+1); }
function maybeAdvanceCounter(){} function autoIndexCustomer(){} function revealNewOrder(){} function render(){} function showPage(){}
function saveDB(){ window._saved=JSON.parse(JSON.stringify(orders)); }
window._deleted=[]; window._trash={};
function deleteDB(id){ window._deleted.push(id); }
const db={}; const ref=(d,p)=>p;
const set=async(p,v)=>{ window._trash[p]=v; };
const get=async p=>({val:()=>({proxyUrl:location.origin+'/_fakeproxy/'})});
const update=async(p,v)=>{ window._linked={p,v}; };
const auth={currentUser:{getIdToken:async()=>'tok'}};
window._showConfirmation=()=>{};
function board(){
  return [
    {id:'o1',customer:'Fluid Line',po:'36241',job:'2701',part:'FA-0322-01',rev:'A',desc:'7ga 316L',qty:10,cost:30,total:300,due:'2026-11-20',status:'In Progress',notes:'keep me',schedule:{steps:['Laser']}},
    {id:'o2',customer:'Fluid Line',po:'36241',job:'2701-2',part:'GA-0311',rev:'',desc:'',qty:2,cost:500,total:1000,due:'2026-11-20',status:'Received',notes:'',splitFrom:'o3',splitOf:5,splitMode:'production'},
    {id:'o3',customer:'Fluid Line',po:'36241',job:'2701-3',part:'GA-0311',rev:'',desc:'',qty:3,cost:500,total:1500,due:'2026-12-01',status:'Received',notes:''},
    {id:'o4',customer:'Fluid Line',po:'36241',job:'2701-4',part:'XX-100',rev:'',desc:'',qty:4,cost:12,total:48,due:'2026-11-20',status:'Received',notes:''},
    {id:'o5',customer:'Fluid Line',po:'36241',job:'2701-5',part:'INV-9',rev:'',desc:'',qty:1,cost:80,total:80,due:'2026-11-01',status:'Invoiced',notes:''},
    {id:'a1',customer:'Acme Fab',po:'36241',job:'2650',part:'FA-0322-01',rev:'',desc:'',qty:99,cost:1,total:99,due:'',status:'Received',notes:''},
    {id:'z1',customer:'Fluid Line',po:'36241',job:'2600',part:'OLD-1',qty:1,cost:1,status:'Invoiced',archived:true}];
}
const AI_ROWS=[{customer:'Fluid Line Products, Inc.',po:'36241',part:'FA-0322-01',rev:'B',desc:'7ga 316L',qty:15,cost:30,due:'2026-12-04',poNotes:'Change order 1: qty 10 -> 15'},
  {customer:'Fluid Line Products, Inc.',po:'36241',part:'GA-0311',rev:'',desc:'',qty:6,cost:520,due:'',poNotes:''},
  {customer:'Fluid Line Products, Inc.',po:'36241',part:'INV-9',rev:'',desc:'',qty:2,cost:80,due:'',poNotes:''},
  {customer:'Fluid Line Products, Inc.',po:'36241',part:'NEW-77',rev:'',desc:'.125 304',qty:8,cost:9.5,due:'2026-12-04',poNotes:''}];
function tOpen(){ orders=board(); openAI(); aiSetRows(JSON.parse(JSON.stringify(AI_ROWS))); }
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function runChecks(){
  const out=[]; const ok=(n,c,x)=>out.push((c?'PASS':'FAIL')+'  '+n+(x!=null?'   ['+x+']':''));
  const $=id=>document.getElementById(id);
  const tag=i=>($('ai-mtag-'+i)||{}).textContent||'';
  const diff=i=>($('ai-diff-'+i)||{}).textContent||'';
  // 1 · detection + review
  tOpen();
  ok('banner shown for the PO on the board', $('ai-chg').style.display==='block' && /PO 36241/.test($('ai-chg').textContent), $('ai-chg').textContent.slice(0,90));
  ok('customer matched despite "Products, Inc."', _aiChg && _aiChg.cust==='Fluid Line');
  ok('other customer + archived lines left out', _aiChg && _aiChg.lines.length===5 && !_aiChg.lines.some(o=>o.id==='a1'||o.id==='z1'));
  ok('line 1 tagged Changes', /Changes/.test(tag(0)), tag(0));
  ok('line 1 shows qty, due and rev', /Qty 10 → 15/.test(diff(0)) && /Due 11\\/20\\/26 → 12\\/04\\/26/.test(diff(0)) && /Rev A → B/.test(diff(0)), diff(0));
  ok('split line: qty shown, not applied', /Qty 5 → 6 · split line/.test(diff(1)), diff(1));
  ok('split line: price applied to both runs', /Unit \\$ \\$500\\.00 → \\$520\\.00/.test(diff(1)) && !/Unit[^·]*already/.test(diff(1)));
  ok('invoiced line: not changed', /No change/.test(tag(2)) && /already invoiced/.test(diff(2)), diff(2));
  ok('new part tagged New line', /New line/.test(tag(3)), tag(3));
  ok('dropped line listed with a tick box', /XX-100/.test($('ai-chg').textContent) && document.querySelectorAll('#ai-chg input[type=checkbox]').length===1);
  ok('button says Apply changes', /Apply changes to PO 36241/.test($('ai-import-btn').textContent), $('ai-import-btn').textContent.trim());
  // 2 · typing updates the old → new live
  const q1=document.querySelectorAll('#ai-rows .ai-row')[0].querySelectorAll('.ai-grid input')[2];
  q1.value='10'; q1.dispatchEvent(new Event('input'));
  ok('qty back to 10 drops the qty change', !/Qty/.test(diff(0)) && /Due/.test(diff(0)), diff(0));
  q1.value='15'; q1.dispatchEvent(new Event('input'));
  // 3 · mode toggle and header PO change
  aiChgMode('new');
  ok('import-as-new mode: plain import button', /Import 4 orders/.test($('ai-import-btn').textContent) && !$('ai-diff-0'));
  aiChgMode('change');
  $('ai-po').value='99999'; $('ai-po').dispatchEvent(new Event('input'));
  ok('unknown PO: banner hidden', $('ai-chg').style.display==='none' && /Import 4 orders/.test($('ai-import-btn').textContent));
  $('ai-po').value='36241'; $('ai-po').dispatchEvent(new Event('input'));
  ok('PO typed back: banner returns', $('ai-chg').style.display==='block');
  // 4 · re-pair: point NEW-77 at the dropped XX-100 line, then back
  aiChgPick(3,'id:o4');
  ok('re-paired line leaves the dropped list', !/tick to delete/.test($('ai-chg').textContent));
  aiChgPick(3,'new');
  document.querySelector('#ai-chg input[type=checkbox]').click();
  ok('ticked line struck through', document.querySelector('#ai-chg label.on')!=null && /1 to delete/.test($('ai-chg').textContent));
  // 5 · apply
  importAIOrders();
  const s=window._saved||[], g=id=>s.find(o=>o.id===id)||{};
  ok('line 1 updated in place', g('o1').qty===15 && g('o1').total===450 && g('o1').due==='2026-12-04' && g('o1').rev==='B', JSON.stringify(g('o1')).slice(0,160));
  ok('line 1 keeps job, status, schedule, notes', g('o1').job==='2701' && g('o1').status==='In Progress' && g('o1').schedule && /^keep me\\nPO change \\d\\d\\/\\d\\d\\/\\d\\d: Qty 10 → 15; Due 11\\/20\\/26 → 12\\/04\\/26; Rev A → B$/.test(g('o1').notes), g('o1').notes);
  ok('split runs: price changed, qty and dates kept', g('o2').cost===520 && g('o3').cost===520 && g('o2').qty===2 && g('o3').qty===3 && g('o2').total===1040 && g('o3').due==='2026-12-01');
  ok('invoiced line untouched', g('o5').qty===1 && !g('o5').notes);
  const nw=s.find(o=>o.part==='NEW-77')||{};
  ok('new line added under the board spelling', nw.customer==='Fluid Line' && nw.po==='36241' && nw.qty===8 && /Added on PO change/.test(nw.notes), JSON.stringify(nw).slice(0,140));
  ok('ticked line deleted to Recently Deleted', !s.some(o=>o.id==='o4') && window._deleted.includes('o4') && window._trash['trash/o4'] && /Not on PO change/.test(window._trash['trash/o4'].deletedWhy));
  ok('other customer untouched', g('a1').qty===99 && s.length===7, s.length);
  ok('modal closed', $('ai-modal').style.display==='none');
  ok('toast sums it up', /PO 36241 updated: 2 changed · 1 added · 1 deleted/.test(($('next-toast')||{}).textContent||''), ($('next-toast')||{}).textContent);
  // 6 · plain import still works when the PO is new
  orders=[]; window._saved=null; openAI(); aiSetRows(JSON.parse(JSON.stringify(AI_ROWS)));
  ok('new PO: no banner', $('ai-chg').style.display==='none');
  importAIOrders();
  ok('new PO: 4 orders imported', (window._saved||[]).length===4);
  $('log').textContent=out.join('\\n');
  document.title=out.some(l=>l.startsWith('FAIL'))?'FAILURES':'all pass';
}
</script></body></html>''' % (links, styles, modal, helpers + '\n' + js)

io.open(ROOT + '_pochgtest.html', 'w', encoding='utf-8').write(html)
print('wrote _pochgtest.html')
