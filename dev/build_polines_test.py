# Slices the REAL purchase-line functions out of orders.html into a standalone
# test page. Run this, then open http://localhost:8123/_polinestest.html (python
# http.server from .claude/launch.json — the Browser pane refuses file:// URLs).
# Page title says "all pass" or "FAILURES"; delete _polinestest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

# the whole line model: normList / newStepLine / stepLines / ensureStepLines /
# stepLine / lineCovered / lineBuyQty / lineQtyMath / lineLabel / syncStepFromLines
block  = grab('function normList(v){', '\n// Colors are grouped')
# the Need PO pool fan-out (one card per uncovered line)
block += '\n' + grab('function npPoolItems(){', '\n// Open POs =')
# the PO -> lines walker used by ship-date / void / receive
block += '\n' + grab('function _poLines(rec, fn){', '\nwindow._polShip')

html = u'''<!doctype html><meta charset="utf-8"><title>purchase lines test</title>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));

// ── stubs: the bits of orders.html the line model leans on ──
let _n=0;
function uid(){ return 'u'+(++_n); }
function toISO(d){ return d.toISOString().slice(0,10); }
const EXTERNAL_SET=new Set(['Purchasing- Hardware','Purchasing- Material','Outsource- Plating']);
function isExternal(n){ return EXTERNAL_SET.has(n); }
function defDur(){ return 5; }
let orders=[];
function ensureSchedule(r){ return r.schedule; }
function enabledOrdered(sch){ return (sch.steps||[]).filter(s=>s.enabled); }
function computeStepDates(r){
  return (r.schedule.steps||[]).filter(s=>s.enabled).map(s=>({name:s.name,
    start:new Date('2026-09-01T00:00:00'), end:new Date('2026-09-08T00:00:00')}));
}
function _extStep(id,name){
  const r=orders.find(o=>o.id===id); if(!r) return null;
  return (r.schedule.steps||[]).find(s=>s.name===name)||null;
}
/*__BLOCK__*/

// ── fixtures ─────────────────────────────────────────────────────────────────
const mkStep=(o)=>Object.assign({name:'Purchasing- Hardware',enabled:true,duration:5,detail:''},o);
const mkOrder=(id,qty,steps)=>({id:id,qty:qty,customer:'Acme',part:'BRK-'+id,job:'J'+id,due:'2026-09-20',
  priority:2,archived:false,status:'Need Purchase Order',schedule:{steps:steps}});

// ══ 1 · legacy steps read as one line, without being written ══════════════════
{
  const s=mkStep({itemsPurchased:'14ga 304 sheet', qtyNeeded:12, vendor:'Metal Supply', vendorPO:'1100', poAt:'2026-08-01'});
  const L=stepLines(s);
  ok('legacy step reads as exactly one line', L.length===1, L.length);
  ok('legacy desc carried over', L[0].desc==='14ga 304 sheet', L[0].desc);
  ok('legacy qty carried over', L[0].qty===12, L[0].qty);
  ok('legacy vendor+PO carried over', L[0].vendor==='Metal Supply'&&L[0].vendorPO==='1100');
  ok('legacy line counts as covered', lineCovered(L[0])===true);
  ok('stepLines did NOT write s.lines', s.lines===undefined, String(s.lines));
}
{
  const s=mkStep({});   // nothing typed at all — still needs a PO
  const L=stepLines(s);
  ok('empty step still yields one uncovered line', L.length===1 && !lineCovered(L[0]));
}

// ══ 2 · RTDB shapes: object-keyed lists and null holes ════════════════════════
{
  const s=mkStep({lines:{a:{id:'l1',desc:'PEM nut',qty:100},b:null,c:{id:'l2',desc:'standoff',qty:50}}});
  const L=stepLines(s);
  ok('object-shaped lines normalize to an array', Array.isArray(L)&&L.length===2, L.length);
  ok('null holes dropped', L.every(Boolean));
  const s2=mkStep({lines:[{id:'l1',desc:'a'},null,{id:'l2',desc:'b'}]});
  ok('array with null holes normalizes', stepLines(s2).length===2);
  ensureStepLines(s2);
  ok('ensureStepLines strips the holes on the step', s2.lines.length===2);
}

// ══ 3 · buy qty + the shown math ═════════════════════════════════════════════
{
  ok('per-piece × order qty, rounded up', lineBuyQty({qtyPer:2.5,qty:''},201)===503, lineBuyQty({qtyPer:2.5,qty:''},201));
  ok('typed qty overrides the math', lineBuyQty({qtyPer:4,qty:850},200)===850);
  ok('typed zero is respected, not treated as blank', lineBuyQty({qtyPer:4,qty:0},200)===0);
  ok('no per-piece and no qty = 0', lineBuyQty({qtyPer:'',qty:''},200)===0);
  const m=lineQtyMath({qtyPer:4,qty:''},200);
  ok('math string shows its work', m==='4/pc × 200 pcs = 800', m);
  const m2=lineQtyMath({qtyPer:4,qty:850},200);
  ok('math string flags an override', m2==='4/pc × 200 pcs = 800 · buying 850', m2);
  ok('no math string without a per-piece figure', lineQtyMath({qtyPer:'',qty:500},200)==='');
}

// ══ 4 · roll-up: a step is covered only when EVERY line is ════════════════════
{
  const s=mkStep({lines:[
    {id:'l1',pn:'FH-632-2',desc:'PEM flush nut',qtyPer:4,qty:'',vendor:'Fastenal',vendorPO:'',poAt:'',sentAt:'',receivedAt:''},
    {id:'l2',pn:'',desc:'standoff',qtyPer:2,qty:'',vendor:'McMaster',vendorPO:'',poAt:'',sentAt:'',receivedAt:''}]});
  syncStepFromLines(s,200);
  ok('two vendors roll up to no single step vendor', s.vendor==='', s.vendor);
  ok('no PO yet -> step reads uncovered', s.vendorPO==='', s.vendorPO);
  ok('summary lists both items with qtys', s.itemsPurchased==='FH-632-2 — PEM flush nut ×800; standoff ×400', s.itemsPurchased);
  ok('multi-line step has no single qtyNeeded', s.qtyNeeded==='', s.qtyNeeded);

  s.lines[0].vendorPO='5001'; s.lines[0].poAt='2026-08-10'; s.lines[0].sentAt='2026-08-10';
  syncStepFromLines(s,200);
  ok('one of two on a PO -> step still uncovered', s.vendorPO==='', s.vendorPO);
  ok('partially ordered -> sentAt stays null', s.sentAt===null, String(s.sentAt));

  s.lines[1].vendorPO='5002'; s.lines[1].poAt='2026-08-12'; s.lines[1].sentAt='2026-08-14';
  syncStepFromLines(s,200);
  ok('both on POs -> step covered, both numbers listed', s.vendorPO==='5001, 5002', s.vendorPO);
  ok('poAt takes the earliest PO date', s.poAt==='2026-08-10', s.poAt);
  ok('fully ordered -> sentAt = the LAST ship date', s.sentAt==='2026-08-14', s.sentAt);
  ok('lead time anchors to the last ship date', s.start==='2026-08-14', s.start);

  s.lines[0].receivedAt='2026-08-20';
  syncStepFromLines(s,200);
  ok('one line back -> step NOT done', s.done!==true, String(s.done));
  ok('one line back -> step receivedAt cleared', s.receivedAt==='', String(s.receivedAt));
  s.lines[1].receivedAt='2026-08-25';
  syncStepFromLines(s,200);
  ok('all lines back -> step done', s.done===true);
  ok('step receivedAt = the last arrival', s.receivedAt==='2026-08-25', s.receivedAt);
}
{
  const s=mkStep({lines:[{id:'l1',pn:'',desc:'zinc plate',qtyPer:'',qty:40,vendor:'Zinc Co',vendorPO:'7001',poAt:'2026-08-02',sentAt:'2026-08-02',receivedAt:''}]});
  syncStepFromLines(s,40);
  ok('single line -> step vendor set', s.vendor==='Zinc Co', s.vendor);
  ok('single line -> plain PO number, no comma', s.vendorPO==='7001', s.vendorPO);
  ok('single line -> qtyNeeded set', s.qtyNeeded===40, s.qtyNeeded);
  ok('single line -> summary is just the item', s.itemsPurchased==='zinc plate', s.itemsPurchased);
}
{
  // a manually-completed step with no receipts must not be un-done by a later edit
  const s=mkStep({done:true,doneAt:'2026-08-01',lines:[{id:'l1',desc:'x',qty:1,vendor:'',vendorPO:'',poAt:'',sentAt:'',receivedAt:''}]});
  syncStepFromLines(s,10);
  ok('sync never clears a manual done', s.done===true);
}

// ══ 5 · Need PO fan-out: one pool card per uncovered line ════════════════════
{
  orders=[ mkOrder('o1',200,[mkStep({lines:[
      {id:'l1',pn:'FH-632-2',desc:'PEM flush nut',qtyPer:4,qty:'',vendor:'Fastenal',vendorPO:'',poAt:'',sentAt:'',receivedAt:''},
      {id:'l2',pn:'',desc:'standoff',qtyPer:2,qty:'',vendor:'McMaster',vendorPO:'',poAt:'',sentAt:'',receivedAt:''},
      {id:'l3',pn:'',desc:'rivnut',qtyPer:'',qty:60,vendor:'Fastenal',vendorPO:'9999',poAt:'2026-08-01',sentAt:'',receivedAt:''}]})]),
    mkOrder('o2',50,[mkStep({name:'Purchasing- Material',itemsPurchased:'16ga CRS',qtyNeeded:8,vendor:'Metal Supply'})]) ];
  const pool=npPoolItems();
  ok('pool has one card per UNCOVERED line', pool.length===3, pool.length);
  ok('the line already on a PO is not pooled', !pool.some(x=>x.desc==='rivnut'));
  ok('pool carries the line id', pool.every(x=>!!x.lineId));
  ok('pool vendor comes off the line', pool.filter(x=>x.vendor==='Fastenal').length===1);
  const pem=pool.find(x=>x.pn==='FH-632-2');
  ok('pool qty is the computed buy qty', pem.qty===800, pem.qty);
  ok('pool carries the qty math', pem.qtyMath==='4/pc × 200 pcs = 800', pem.qtyMath);
  ok('pool keeps the order qty for context', pem.ordQty===200, pem.ordQty);
  ok('legacy step still pools as one card', pool.filter(x=>x.orderId==='o2').length===1);

  // grouping by vendor is what makes one PO per vendor across orders
  const key=x=> x.vendor ? ('v:'+x.vendor.toLowerCase()+'|'+x.name) : ('p:'+x.name);
  const groups=new Set(pool.map(key));
  ok('three lines fall into three vendor buckets', groups.size===3, groups.size);
}
{
  // a fully-covered order contributes nothing
  orders=[ mkOrder('o3',10,[mkStep({lines:[{id:'l1',desc:'a',qty:1,vendor:'V',vendorPO:'1',poAt:'',sentAt:'',receivedAt:''}]})]) ];
  ok('fully covered order pools nothing', npPoolItems().length===0);
  orders[0].status='Confirmed';
  orders[0].schedule.steps[0].lines[0].vendorPO='';
  ok('non-"Need PO" orders never pool', npPoolItems().length===0);
}

// ══ 6 · _poLines: PO record -> the lines it actually covers ══════════════════
{
  orders=[ mkOrder('o1',200,[mkStep({lines:[
      {id:'l1',desc:'PEM nut',qty:800,vendor:'Fastenal',vendorPO:'5001',poId:'p1',poAt:'2026-08-10',sentAt:'2026-08-10',receivedAt:''},
      {id:'l2',desc:'standoff',qty:400,vendor:'McMaster',vendorPO:'5002',poId:'p2',poAt:'2026-08-11',sentAt:'2026-08-11',receivedAt:''}]})]) ];
  const rec={id:'p1',po:'5001',vendor:'Fastenal',items:[{orderId:'o1',step:'Purchasing- Hardware',lineId:'l1'}]};
  _poLines(rec,(l)=>{ l.receivedAt='2026-08-20'; });
  const st=orders[0].schedule.steps[0];
  ok('receiving PO p1 marks only its own line', st.lines[0].receivedAt==='2026-08-20' && !st.lines[1].receivedAt);
  ok('step stays open while the other vendor is out', st.done!==true, String(st.done));

  const rec2={id:'p2',po:'5002',vendor:'McMaster',items:[{orderId:'o1',step:'Purchasing- Hardware',lineId:'l2'}]};
  _poLines(rec2,(l)=>{ l.receivedAt='2026-08-22'; });
  ok('second PO in -> step completes', st.done===true);
  ok('step receivedAt = last arrival', st.receivedAt==='2026-08-22', st.receivedAt);
}
{
  // a pre-lines PO record (no lineId) still covers the whole step
  orders=[ mkOrder('o1',10,[mkStep({itemsPurchased:'sheet',qtyNeeded:4,vendor:'V',vendorPO:'3001',sentAt:'2026-08-01'})]) ];
  const rec={id:'old',po:'3001',vendor:'V',items:[{orderId:'o1',step:'Purchasing- Hardware'}]};
  _poLines(rec,(l)=>{ l.receivedAt='2026-08-09'; });
  const st=orders[0].schedule.steps[0];
  ok('legacy PO record (no lineId) receives the step', st.done===true && st.receivedAt==='2026-08-09', st.receivedAt);
}
{
  // voiding puts the line back in the pool
  orders=[ mkOrder('o1',100,[mkStep({lines:[
    {id:'l1',desc:'PEM nut',qty:400,vendor:'Fastenal',vendorPO:'5001',poId:'p1',poAt:'2026-08-10',sentAt:'2026-08-10',receivedAt:''},
    {id:'l2',desc:'standoff',qty:200,vendor:'McMaster',vendorPO:'5002',poId:'p2',poAt:'2026-08-11',sentAt:'2026-08-11',receivedAt:''}]})]) ];
  orders[0].status='Confirmed';
  const rec={id:'p1',po:'5001',vendor:'Fastenal',items:[{orderId:'o1',step:'Purchasing- Hardware',lineId:'l1'}]};
  _poLines(rec,(l)=>{ l.vendorPO=''; l.poId=''; l.poAt=''; l.sentAt=''; });
  const st=orders[0].schedule.steps[0];
  ok('void clears only the voided line', !st.lines[0].vendorPO && st.lines[1].vendorPO==='5002');
  ok('void reopens the step', st.vendorPO==='', st.vendorPO);
  orders[0].status='Need Purchase Order';
  const pool=npPoolItems();
  ok('voided line is back in the pool, alone', pool.length===1 && pool[0].lineId==='l1', pool.length);
}
{
  // _poLines tolerates RTDB object-shaped items and a deleted order
  orders=[ mkOrder('o1',10,[mkStep({lines:[{id:'l1',desc:'a',qty:1,vendor:'V',vendorPO:'1',poAt:'',sentAt:'2026-08-01',receivedAt:''}]})]) ];
  const rec={id:'p',po:'1',items:{k0:{orderId:'o1',step:'Purchasing- Hardware',lineId:'l1'},k1:null,k2:{orderId:'gone',step:'Purchasing- Hardware',lineId:'x'}}};
  let hit=0;
  _poLines(rec,()=>{ hit++; });
  ok('object-shaped items walked, holes and dead refs skipped', hit===1, hit);
}

// ══ 7 · the schedule roll-up chip ════════════════════════════════════════════
// One chip stands in for the whole line list, and its colour is the honest
// WORST case — a step that is four-fifths bought must not read as done.
{
  const L=(...ls)=>mkStep({lines:ls});
  const ln=(o)=>Object.assign({id:'l'+Math.round(Math.random()*1e6),pn:'',desc:'nut',qtyPer:'',qty:10,
    vendor:'',vendorPO:'',poAt:'',sentAt:'',receivedAt:''},o);
  const TODAY='2026-09-10';
  const roll=(step,sendBy)=>stepLineRoll(step, 100, sendBy||'', TODAY);

  let x=roll(L(ln({vendor:'Fastenal'}),ln({vendor:'McMaster'})), '2026-09-20');
  ok('counts the lines', x.n===2, x.n);
  ok('counts the distinct vendors', x.vendors===2, x.vendors);
  ok('nothing bought yet reads open', x.state==='open', x.state);
  ok('and says a PO is needed', x.progress==='needs POs', x.progress);
  ok('two vendors are summarised, not named', x.vendorTxt==='2 vendors', x.vendorTxt);

  x=roll(L(ln({vendor:'Fastenal'})), '2026-09-20');
  ok('one vendor is named outright', x.vendorTxt==='Fastenal', x.vendorTxt);
  ok('a single line says "a PO", not "POs"', x.progress==='needs a PO', x.progress);
  ok('no vendor anywhere is said out loud', roll(L(ln({})),'2026-09-20').vendorTxt==='no vendor yet');
  ok('vendor spelling/case is not double counted',
     roll(L(ln({vendor:'Fastenal'}),ln({vendor:'FASTENAL '})),'2026-09-20').vendors===1);

  // past its order-by with something still unbought = red, whatever else is true
  x=roll(L(ln({vendor:'F',vendorPO:'1'}),ln({vendor:'M'})), '2026-09-01');
  ok('unbought past the order-by date reads late', x.state==='late', x.state);
  ok('late is flagged separately too', x.late===true);
  ok('late still reports the real progress', x.progress==='1 of 2 on PO', x.progress);
  // ...but not once everything is on a PO
  x=roll(L(ln({vendor:'F',vendorPO:'1'}),ln({vendor:'M',vendorPO:'2'})), '2026-09-01');
  ok('all bought is never late, even past the date', x.state==='covered' && x.late===false, x.state);
  ok('all bought says so', x.progress==='all on PO', x.progress);

  x=roll(L(ln({vendor:'F',vendorPO:'1'}),ln({vendor:'M'})), '2026-09-20');
  ok('part bought, not yet late, reads partial', x.state==='partial', x.state);
  x=roll(L(ln({vendor:'F',vendorPO:'1',receivedAt:'2026-09-05'}),ln({vendor:'M',vendorPO:'2'})), '2026-09-20');
  ok('some back but not all is still partial', x.state==='partial', x.state);
  ok('and counts what is in', x.progress==='1 of 2 in', x.progress);
  x=roll(L(ln({vendor:'F',vendorPO:'1',receivedAt:'2026-09-05'}),ln({vendor:'M',vendorPO:'2',receivedAt:'2026-09-06'})), '2026-09-20');
  ok('everything back reads received', x.state==='received', x.state);
  ok('and says all received', x.progress==='all received', x.progress);
  ok('a received step is never late', roll(L(ln({vendorPO:'1',receivedAt:'2026-09-05'})), '2026-08-01').state==='received');
  ok('every state has a colour', ['open','late','partial','covered','received'].every(s=>!!LINE_ROLL_COLOR[s]));

  // a step nobody has typed into yet
  x=roll(L(ln({desc:'',pn:'',qty:''})), '2026-09-20');
  ok('a blank step reports nothing named', x.named===0, x.named);
  ok('but still counts as one line needing a PO', x.n===1 && x.state==='open');
  ok('a part number alone counts as named', roll(L(ln({desc:'',pn:'FH-632-2'})),'').named===1);

  // no order-by date at all (step not scheduled)
  ok('no send-by date cannot be late', roll(L(ln({})),'').late===false);

  // the hover text lists every line with its real state
  x=roll(L(ln({pn:'FH-632-2',desc:'PEM nut',qtyPer:4,qty:'',vendor:'Fastenal',vendorPO:'5001'}),
           ln({desc:'standoff',qty:200,vendor:'McMaster'})), '2026-09-20');
  ok('tip names the first line with its qty and PO',
     x.tip.indexOf('FH-632-2 — PEM nut ×400 — Fastenal — PO 5001')>=0, x.tip.split('\\n')[0]);
  ok('tip admits the unbought line', x.tip.indexOf('standoff ×200 — McMaster — no PO yet')>=0, x.tip.split('\\n')[1]);
  ok('tip has one entry per line', x.tip.split('\\n').length===2);
  ok('tip says when a line is blank', roll(L(ln({desc:'',qty:''})),'').tip.indexOf('(nothing entered)')>=0);
  ok('tip uses the per-piece math for a blank qty',
     roll(L(ln({desc:'nut',qtyPer:3,qty:''})),'').tip.indexOf('nut ×300')>=0,
     roll(L(ln({desc:'nut',qtyPer:3,qty:''})),'').tip);

  // legacy step with no lines at all still rolls up as one
  x=roll(mkStep({itemsPurchased:'16ga CRS', qtyNeeded:8, vendor:'Metal Supply', vendorPO:'1100'}), '2026-09-20');
  ok('a legacy step rolls up as a single covered line', x.n===1 && x.covered===1 && x.state==='covered', x.state);
  ok('and names its vendor', x.vendorTxt==='Metal Supply', x.vendorTxt);
}

const fails=out.filter(l=>l.startsWith('FAIL')).length;
document.getElementById('out').textContent=out.join('\\n')+'\\n\\n'+(out.length-fails)+'/'+out.length+' assertions passed';
document.title = fails ? (fails+' FAILURES') : 'all pass';
</script>'''

html = html.replace('/*__BLOCK__*/', block)
io.open('C:/Users/info/bsmp-orders/_polinestest.html', 'w', encoding='utf-8').write(html)
print('wrote _polinestest.html')
