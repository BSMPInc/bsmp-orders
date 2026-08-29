# Slices the REAL AP-derivation functions out of apar.html into a standalone test page.
# Run this, then open http://localhost:8123/_apartest.html (python http.server from
# .claude/launch.json — the Browser pane refuses file:// URLs). Page title says
# "all pass" or "FAILURES"; delete _apartest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/apar.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block  = grab('function hash(s){', '\n') + '\n'
block += grab('const fmtMoney=', '\n') + '\n'
block += grab('function fmtDate(d){', '\n') + '\n'
block += grab('function esc(s){', '\n') + '\n'
block += grab('function vendorKey(name){', '\n') + '\n'
# the PO-invoice index + matcher + the whole AP derivation
block += grab('// -- Vendor-invoice totals from the Need PO pipeline', '\n// merge derived + overlay')
# the merge that decides which amount actually wins
block += grab('function allEntriesRaw(){', '\n// Active entries:')
# the two show-your-work helpers
block += grab('// Hover text for a bill whose amount', '\nfunction entryRow(')

html = u'''<!doctype html><meta charset="utf-8"><title>apar PO test</title>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
// ── stubs: the bits of apar.html the AP layer leans on ──
let orders={}, poRecs={}, apSplit={}, overlay={};
const DEFAULT_TERMS=30;
let AR_STUB=[];
function deriveAR(){ return AR_STUB.slice(); }
function canonicalParty(p){ return p; }
function addDays(iso,n){ const d=new Date(iso+'T00:00:00'); d.setDate(d.getDate()+n); return d.toISOString().slice(0,10); }
/*__BLOCK__*/

// ── fixtures ─────────────────────────────────────────────────────────────────
const step=(o)=>Object.assign({name:'Outsource- Process',vendor:'',vendorPO:'',sentAt:'2026-08-01',detail:''},o);
const order=(id,part,steps)=>({id:id,customer:'Acme',part:part,schedule:{steps:steps}});
const poRec=(id,po,vendor,info)=>({id:id,po:po,vendor:vendor,status:'received',receivedAt:'2026-08-05',invoiceInfo:info});

orders={
  o1:order('o1','BRK-1',[step({name:'Outsource- Anodize',vendor:'Anodize Inc.',vendorPO:'8891'})]),
  o2:order('o2','BRK-2',[step({name:'Outsource- Zinc',vendor:'Zinc Co',vendorPO:'9002'})]),
  o3:order('o3','PL-1',[step({name:'Outsource- Grind',vendor:'Plate Works',vendorPO:'7700'})]),
  o4:order('o4','PL-2',[step({name:'Outsource- Plate',vendor:'Plate Works',vendorPO:'7700'})]),
  o5:order('o5','SP-1',[step({name:'Outsource- Plating',vendor:'PLATING  co.',vendorPO:'6001'})]),
  o6:order('o6','GR-1',[step({name:'Outsource- Blanchard',vendor:'Bobs Grinding',vendorPO:'5500'})]),
  o7:order('o7','AM-1',[step({name:'Outsource- Heat treat',vendor:'Vendor C',vendorPO:'4400'})]),
  o8:order('o8','AM-2',[step({name:'Outsource- Temper',vendor:'Vendor A',vendorPO:'4400'})]),
  o9:order('o9','NT-1',[step({name:'Outsource- Paint',vendor:'Paint Pros',vendorPO:'3300'})]),
  o10:order('o10','WS-1',[step({name:'Outsource- Laser',vendor:'Laser LLC',vendorPO:' 2200 '})]),
  o11:order('o11','ST-1',[step({name:'Purchasing- Steel',vendor:'Metal Supply',vendorPO:'1100'})]),
  o12:order('o12','AR-1',[]),
  o13:order('o13','NN-1',[step({name:'Outsource- Deburr',vendor:'No Number Co',vendorPO:'9900'})]),
  o14:order('o14','BD-1',[step({name:'Outsource- Bend',vendor:'Bad Date Co',vendorPO:'9910'})]),
};
poRecs={
  p1:poRec('p1','8891','Anodize Inc.',{no:'A-77',date:'2026-08-05',total:1234.56,extracted:'ai'}),
  p3:poRec('p3','7700','Plate Works',{no:'PW-9',date:'2026-08-04',total:2500,extracted:'ai',
      invoiceGrandTotal:2575,
      lines:[{desc:'Grind',qty:'10',amount:1500,sel:true},null,
             {desc:'Plate',qty:'10',amount:1000,sel:true},
             {desc:'Freight',qty:'1',amount:75,sel:false}]}),
  p5:poRec('p5','6001','Plating Co',{no:'PC-1',date:'2026-08-03',total:410.10,extracted:'manual'}),
  p6:poRec('p6','5500','Robert Grinding LLC',{no:'RG-4',date:'2026-08-02',total:88.25,extracted:'manual'}),
  p7:poRec('p7','4400','Vendor A',{no:'VA-1',date:'2026-08-02',total:700,extracted:'manual'}),
  p8:poRec('p8','4400','Vendor B',{no:'VB-1',date:'2026-08-02',total:900,extracted:'manual'}),
  p9:poRec('p9','3300','Paint Pros',{no:'PP-1',date:'2026-08-02',total:null,extracted:'manual'}),
  p10:poRec('p10','2200','Laser LLC',{no:'L-1',date:'2026-08-02',total:'999.99',extracted:'ai'}),
  p11:poRec('p11','1100','Metal Supply',{no:'MS-1',date:'2026-08-01',total:3050,extracted:'ai'}),
  p12:poRec('p12','9900','No Number Co',{no:'',date:'2026-08-06',total:250,extracted:'manual'}),
  p13:poRec('p13','9910','Bad Date Co',{no:'BD-1',date:'08/12/2026',total:100,extracted:'ai'}),
  hole:null,                                              // RTDB null hole
  nopo:poRec('nopo','','No PO Vendor',{no:'x',total:5}),   // record with no PO number
  noinfo:{id:'ni',po:'1100',vendor:'Metal Supply'},        // issued, not yet received
};
AR_STUB=[{id:'ar_x',type:'ar',party:'Customer Co',ref:'Inv 5001',rel:'',amount:4200,issue:'2026-08-01',auto:true}];

const byRef=(r)=>allEntriesRaw().filter(e=>e.ref===r||e.poRef===r);
const one=(r)=>byRef(r)[0];

// ── 1 · the bug being fixed: a received PO carries its invoice amount over ───
let e=one('PO 8891');
ok('single-step PO takes the vendor-invoice total', e && e.amount===1234.56, e&&e.amount);
ok('single-step PO is flagged as auto-filled', !!(e&&e.amountFromPO));
ok('the source invoice rides along', !!(e&&e.poInv&&e.poInv.no==='A-77'));
ok('bill is still a payable', e&&e.type==='ap');

// ── 2 · no PO record / no invoice yet -> unchanged blank behavior ────────────
e=one('PO 9002');
ok('PO with no record stays blank', e && e.amount===null, e&&e.amount);
ok('blank PO is not flagged auto-filled', e && e.amountFromPO===false);
e=one('PO 3300');
ok('received with no total stays blank', e && e.amount===null, e&&e.amount);
e=one('PO 1100');
ok('an un-received duplicate record cannot blank a good one', e && e.amount===3050, e&&e.amount);

// ── 3 · combined PO (two steps, one vendor invoice) ─────────────────────────
e=one('PO 7700');
ok('two steps on one PO combine into one bill', byRef('PO 7700').length===1, byRef('PO 7700').length);
ok('combined bill takes the invoice total', e && e.amount===2500, e&&e.amount);
ok('combined bill still knows its 2 items', e && e.comboCount===2 && e.lineItems.length===2);

// ── 4 · hand-entered numbers always beat the derived one ────────────────────
const idA=one('PO 8891').id, idC=one('PO 7700').id;
overlay={};
overlay[idA]={amount:1300};
e=one('PO 8891');
ok('typed amount overrides the invoice', e && e.amount===1300, e&&e.amount);
ok('overridden bill drops the auto-filled flag', e && e.amountFromPO===false);
ok('overridden bill still shows the invoice for reference', !!(e&&e.poInv));
overlay={};
overlay[idC]={lineItems:[{part:'Grind',total:1400},{part:'Plate',total:900}]};
e=one('PO 7700');
ok('combined line amounts override the invoice', e && e.amount===2300, e&&e.amount);
ok('line-driven bill drops the auto-filled flag', e && e.amountFromPO===false);
overlay={};

// ── 5 · matching when the vendor name was typed differently ────────────────
e=one('PO 6001');
ok('vendor name normalizes ("PLATING  co." = "Plating Co")', e && e.amount===410.10, e&&e.amount);
e=one('PO 5500');
ok('different vendor name, unique PO -> falls back to the PO number', e && e.amount===88.25, e&&e.amount);

// ── 6 · the same PO number used by two vendors must not cross-post ─────────
e=one('PO 4400') && byRef('PO 4400').filter(x=>x.party==='Vendor C')[0];
ok('unknown vendor on a shared PO number stays blank', e && e.amount===null, e&&e.amount);
e=byRef('PO 4400').filter(x=>x.party==='Vendor A')[0];
ok('exact vendor match still wins on a shared PO number', e && e.amount===700, e&&e.amount);

// ── 7 · messy real-world data ──────────────────────────────────────────────
e=one('PO 2200');
ok('PO number whitespace is ignored', e && e.amount===999.99, e&&e.amount);
ok('a numeric string total becomes a number', e && typeof e.amount==='number');
ok('null holes in the pos node do not throw', allEntriesRaw().length>0);

// ── 8 · receivables untouched ──────────────────────────────────────────────
e=one('Inv 5001');
ok('AR entries still derive', e && e.amount===4200 && e.type==='ar');
ok('AR is never flagged as PO-auto-filled', e && !e.amountFromPO);

// ── 9 · show-your-work note + hover text ───────────────────────────────────
let note=poInvNote(one('PO 7700'));
ok('note names the invoice', note.indexOf('PW-9')>=0);
ok('note shows the ticked-line math', note.indexOf('$1,500.00 + $1,000.00 = ')>=0);
ok('note says a line was left off', note.indexOf('1 line')>=0 && note.indexOf('$2,575.00')>=0);
ok('note skips null line holes', note.indexOf('undefined')<0);
note=poInvNote(one('PO 8891'));
ok('note says when the AI read the PDF', note.indexOf('read off the invoice PDF')>=0);
overlay={}; overlay[idA]={amount:1300};
ok('note admits when it has been overridden', poInvNote(one('PO 8891')).indexOf('here for reference')>=0);
overlay={};
ok('blank bill gets no note', poInvNote(one('PO 9002'))==='');
const tip=poInvTip(one('PO 8891'));
ok('hover text names invoice + PO', tip.indexOf('#A-77')>=0 && tip.indexOf('PO 8891')>=0);
ok('hover text is a safe attribute', tip.indexOf(' title="')===0 && tip.lastIndexOf('"')===tip.length-1);
ok('no hover text on a blank bill', poInvTip(one('PO 9002'))==='');

// ── 10 · index internals ───────────────────────────────────────────────────
const idx=poInvoiceIndex();
ok('records without a total are not indexed', !poInvoiceFor(idx,'Paint Pros','3300'));
ok('records without a PO number are not indexed', !poInvoiceFor(idx,'No PO Vendor',''));
ok('unknown PO returns null, not a throw', poInvoiceFor(idx,'Nobody','0000')===null);

// -- 11 - the vendor's own invoice date and number ------------------------
e=one('PO 8891');
ok('bill is referenced by the vendor invoice number', e && e.ref==='Inv A-77', e&&e.ref);
ok('the PO number is kept as poRef', e && e.poRef==='PO 8891', e&&e.poRef);
ok('bill is dated the invoice date, not the PO send date', e && e.issue==='2026-08-05', e&&e.issue);
ok('terms count from the invoice date', e && e.due==='2026-09-04', e&&e.due);
ok('flagged as invoice-dated / invoice-numbered', e && e.issueFromPO===true && e.refFromPO===true);
e=one('PO 7700');
ok('combined bill takes the invoice date over the earliest PO', e && e.issue==='2026-08-04', e&&e.issue);
ok('combined bill takes the invoice number', e && e.ref==='Inv PW-9', e&&e.ref);
e=one('PO 9002');
ok('no PO record -> still reads PO number', e && e.ref==='PO 9002', e&&e.ref);
ok('no PO record -> still dated the PO send date', e && e.issue==='2026-08-01', e&&e.issue);
ok('no PO record -> neither flag set', e && e.refFromPO===false && e.issueFromPO===false);
ok('no PO record -> no hover text for a PO', refTip(e)==='');
e=one('PO 9900');
ok('invoice with no number keeps the PO as the reference', e && e.ref==='PO 9900', e&&e.ref);
ok('invoice with no number still supplies date + amount', e && e.issue==='2026-08-06' && e.amount===250, e&&e.issue);
ok('invoice with no number is not flagged invoice-numbered', e && e.refFromPO===false);
e=one('PO 9910');
ok('a non-ISO invoice date is refused', e && e.issue==='2026-08-01', e&&e.issue);
ok('refused date is not flagged invoice-dated', e && e.issueFromPO===false);
ok('a bad date does not block the number or amount', e && e.ref==='Inv BD-1' && e.amount===100);
ok('hover text carries the PO number', refTip(one('PO 8891')).indexOf('PO 8891')>=0);

// typed values still win, echoed-back derived values do not
const id8=one('PO 8891').id;
overlay={}; overlay[id8]={ref:'MY-REF',issue:'2026-09-01'};
e=one('PO 8891');
ok('a typed reference beats the invoice number', e && e.ref==='MY-REF', e&&e.ref);
ok('a typed issue date beats the invoice date', e && e.issue==='2026-09-01', e&&e.issue);
ok('typed values drop both flags', e && e.refFromPO===false && e.issueFromPO===false);
ok('the invoice is still there for reference', !!(e&&e.poInv));
overlay={}; overlay[id8]={ref:'PO 8891',issue:'2026-08-01'};   // what old saves stored
e=one('PO 8891');
ok('an old stored "PO 1234" reference is not an override', e && e.ref==='Inv A-77', e&&e.ref);
ok('an old stored PO-send issue date is not an override', e && e.issue==='2026-08-05', e&&e.issue);
ok('and the flags survive it', e && e.refFromPO===true && e.issueFromPO===true);
overlay={};
ok('AR entries have no PO reference', one('Inv 5001').poRef===undefined);
overlay={ar_x:{ref:'Custom AR'}};
ok('an AR reference override still works', one('Custom AR')&&one('Custom AR').amount===4200);
overlay={};

// the note explains the date and the number too
note=poInvNote(one('PO 8891'));
ok('note says the due date counts from the invoice date', note.indexOf('due date counts from there')>=0);
ok('note names the invoice number it filed under', note.indexOf('A-77')>=0 && note.indexOf('invoice number')>=0);
ok('note still names the PO the bill came from', note.indexOf('PO 8891')>=0);
overlay={}; overlay[id8]={issue:'2026-09-01'};
ok('note admits the date was overridden', poInvNote(one('PO 8891')).indexOf('your own issue date')>=0);
overlay={};
ok('a refused invoice date is never claimed in the note', poInvNote(one('PO 9910')).indexOf('due date counts from there')<0);

// ── 12 · purchase lines: one step bought from two vendors = two bills ────────
// The step's roll-up vendor is blank and its vendorPO is "5001, 5002" - reading
// those instead of the lines would invent one bogus bill for a vendor that
// doesn't exist, and neither real invoice would ever match.
{
  const savedO=orders, savedP=poRecs, savedS=apSplit;
  const hwStep=(lines)=>({name:'Purchasing- Hardware',enabled:true,detail:'hardware',
    vendor:'',vendorPO:'5001, 5002',sentAt:'2026-08-10',lines:lines});
  orders={ h1:{id:'h1',customer:'Acme',part:'BRK-1',schedule:{steps:[hwStep([
      {id:'l1',desc:'PEM nut',qty:800,vendor:'Fastenal',vendorPO:'5001',sentAt:'2026-08-10'},
      {id:'l2',desc:'standoff',qty:400,vendor:'McMaster',vendorPO:'5002',sentAt:'2026-08-11'}])]}} };
  poRecs={ q1:poRec('q1','5001','Fastenal',{no:'F-1',date:'2026-08-12',total:168,extracted:'ai'}),
           q2:poRec('q2','5002','McMaster',{no:'M-1',date:'2026-08-13',total:96,extracted:'ai'}) };
  apSplit={};
  const aps=allEntriesRaw().filter(e=>e.type==='ap');
  ok('a two-vendor step derives two bills', aps.length===2, aps.length);
  ok('no bogus merged "5001, 5002" bill', !aps.some(e=>String(e.poRef||'').indexOf(',')>=0),
     aps.map(e=>e.poRef).join(' / '));
  ok('no "(vendor)" placeholder bill', !aps.some(e=>e.party==='(vendor)'), aps.map(e=>e.party).join(' / '));
  const f=aps.find(e=>e.party==='Fastenal'), m=aps.find(e=>e.party==='McMaster');
  ok('each vendor gets its own invoice amount', f&&f.amount===168 && m&&m.amount===96, (f&&f.amount)+' / '+(m&&m.amount));
  ok('each bill is referenced by its own invoice number', f&&f.ref==='Inv F-1' && m&&m.ref==='Inv M-1');
  ok('each bill dates from its own invoice', f&&f.issue==='2026-08-12' && m&&m.issue==='2026-08-13');

  // object-shaped lines with a null hole (how RTDB hands lists back)
  orders={ h2:{id:'h2',customer:'Acme',part:'BRK-2',schedule:{steps:[hwStep(
    {a:{id:'l1',desc:'PEM nut',qty:800,vendor:'Fastenal',vendorPO:'5001',sentAt:'2026-08-10'},
     b:null,
     c:{id:'l2',desc:'standoff',qty:400,vendor:'McMaster',vendorPO:'5002',sentAt:'2026-08-11'}})]}} };
  ok('object-shaped lines with holes still derive two bills',
     allEntriesRaw().filter(e=>e.type==='ap').length===2);

  // a line not yet on a PO is not a bill
  orders={ h3:{id:'h3',customer:'Acme',part:'BRK-3',schedule:{steps:[Object.assign(hwStep([
      {id:'l1',desc:'PEM nut',qty:800,vendor:'Fastenal',vendorPO:'5001',sentAt:'2026-08-10'},
      {id:'l2',desc:'standoff',qty:400,vendor:'McMaster',vendorPO:'',sentAt:''}]),{vendorPO:''})]}} };
  const partial=allEntriesRaw().filter(e=>e.type==='ap');
  ok('a line still waiting on a PO is not a bill', partial.length===1 && partial[0].party==='Fastenal', partial.length);

  // legacy step (no lines at all) is unchanged
  orders={ h4:{id:'h4',customer:'Acme',part:'BRK-4',schedule:{steps:[
    {name:'Outsource- Plating',enabled:true,vendor:'Fastenal',vendorPO:'5001',sentAt:'2026-08-10',detail:''}]}} };
  const legacy=allEntriesRaw().filter(e=>e.type==='ap');
  ok('a step with no lines still derives its one bill', legacy.length===1 && legacy[0].amount===168, legacy.length);

  orders=savedO; poRecs=savedP; apSplit=savedS;
}

const fails=out.filter(l=>l.indexOf('FAIL')===0).length;
document.getElementById('out').textContent=out.join('\\n')+'\\n\\n'+(out.length-fails)+' / '+out.length+' assertions';
document.title=fails?('FAILURES ('+fails+')'):'all pass';
</script>'''

io.open('C:/Users/info/bsmp-orders/_apartest.html', 'w', encoding='utf-8', newline='').write(
    html.replace('/*__BLOCK__*/', block))
print('wrote _apartest.html (%d chars of sliced source)' % len(block))

# ── second page: the new UI bits under the real stylesheet, at laptop width ──
# The note is rendered by the REAL poInvNote() so this page cannot drift from the code.
style = grab('<style>', '</style>') + '</style>'
view = u'''<!doctype html><meta charset="utf-8"><title>apar PO note view</title>
__STYLE__
<div style="width:700px;padding:14px;background:var(--bg,#fff)">
  <div class="erow ap" style="cursor:default">
    <span class="er-party">Plate Works</span>
    <span class="er-ref" title="PO 7700">Inv PW-9<span class="er-auto">auto</span></span>
    <span class="er-due">09/03/26 (16d)</span>
    <span class="er-amt" title="Amount from vendor invoice #PW-9">$2,500.00<span class="inv-src">inv</span></span>
    <span class="pill open er-pill">Open</span>
  </div>
  <div id="note"></div>
  <div id="note2" style="margin-top:14px"></div>
</div>
<script>
let orders={},poRecs={},apSplit={},overlay={};const DEFAULT_TERMS=30;
function deriveAR(){return[]}function canonicalParty(p){return p}
function addDays(iso,n){const d=new Date(iso+'T00:00:00');d.setDate(d.getDate()+n);return d.toISOString().slice(0,10)}
/*__BLOCK__*/
const inv={total:2500,no:'PW-9',date:'2026-08-04',extracted:'ai',po:'7700',
  grandTotal:2575,lines:[{desc:'Grind',amount:1500,sel:true},{desc:'Plate',amount:1000,sel:true},
                         {desc:'Freight',amount:75,sel:false}]};
document.getElementById('note').innerHTML =
  poInvNote({poInv:inv,amountFromPO:true,issueFromPO:true,refFromPO:true,combined:true});
document.getElementById('note2').innerHTML =
  poInvNote({poInv:inv,amountFromPO:false,issueFromPO:false,refFromPO:false,combined:false});
</script>'''
io.open('C:/Users/info/bsmp-orders/_apartest_view.html','w',encoding='utf-8',newline='').write(
    view.replace('__STYLE__', style).replace('/*__BLOCK__*/', block))
print('wrote _apartest_view.html')
