# Slices the REAL AI-Extract statement-mode functions out of apar.html into a standalone
# test page (the McMaster statement of 2026-09-01 as the fixture). Run this, then open
# http://localhost:8123/_stmttest.html (python http.server from .claude/launch.json — the
# Browser pane refuses file:// URLs). Page title says "all pass (N)" or "FAILURES (n)";
# delete _stmttest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/apar.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block  = grab('const fmtMoney=', '\n') + '\n'
block += grab('function fmtDate(d){', '\n') + '\n'
block += grab('const pad=n=>', '\n') + '\n'
block += grab('const toISO=d=>', '\n') + '\n'
block += grab('function addDays(iso,days){', '\n') + '\n'
block += grab('function esc(s){', '\n') + '\n'
block += grab('function vendorKey(name){', '\n') + '\n'
block += grab('const ISO_DAY=', '\n') + '\n'
block += grab('const $=id=>', '\n') + '\n'
# the whole statement-mode layer
block += grab('// ── AI Extract, statement mode', '\n// ── Auth + data wiring')

style = grab('<style>', '</style>') + '</style>'
modal = grab('<!-- AI extract modal -->', '<!-- Bulk import modal -->')

html = u'''<!doctype html><meta charset="utf-8"><title>apar stmt test</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.30.0/dist/tabler-icons.min.css">
''' + style + u'''
<style>body{background:#f4f6fa} #out{position:fixed;left:8px;bottom:8px;z-index:99;background:#fff;border:1px solid #ccc;padding:8px;max-height:38vh;overflow:auto;font:11px ui-monospace,monospace;width:520px}</style>
<pre id="out"></pre>
''' + modal + u'''
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
// ── stubs: the bits of apar.html the statement layer leans on ──
let aiType='ap', overlay={}, vendorAccounts={};
let accounts={acc1:{name:'Operating'},acc2:{name:'Utilities'}};
const DEFAULT_TERMS=30;
let ENTRIES=[];
function allEntries(){ return ENTRIES; }
function canonicalParty(p){ return p; }
function statusOf(e){ return (e.amount!=null&&e.paid>=e.amount)?'paid':'open'; }
const writes=[], patches=[], audits=[];
function writeOverlay(id,o){ overlay[id]=o; writes.push({id,o}); }
function ovlPatch(id,e,patch){ patches.push({id,patch}); }
function logAudit(a,o){ audits.push(o); }
function dbSet(){} function render(){} function closeAI(){}
window.confirm=()=>true; window.alert=m=>out.push('ALERT '+m);
/*__BLOCK__*/

// ── fixtures: what Claude returns for the McMaster statement (33 lines) + 2 edge lines ──
const V='McMaster-Carr Supply Company';
const L=(issue,po,ref,amt)=>({party:V,ref,po,amount:amt,issue,due:'',terms:30,discountTerms:'2% 10, Net 30',description:'PO '+po});
const STMT=[
 L('2026-08-31','0829EDUENEZ','71052861',112.87), L('2026-08-28','0828EDUENEZ','70996763',76.04),
 L('2026-08-26','0826EDUENEZ','70851422',34.63),  L('2026-08-25','0825EDUENEZ','70764075',235.85),
 L('2026-08-24','0824EDUENEZ','70676486',296.27), L('2026-08-24','0824EDUENEZ','70697010',38.38),
 L('2026-08-18','0818EDUENEZ','70362617',172.11), L('2026-08-17','0817EDUENEZ','70249613',59.38),
 L('2026-08-17','0817EDUENEZ','70265711',189.91), L('2026-08-14','0814BDUENEZ','70142934',116.74),
 L('2026-08-14','0814EDUENEZ','70159162',40.27),  L('2026-08-14','0814EDUENEZ','70175035',54.62),
 L('2026-08-13','0813EDUENEZ','70128965',399.07), L('2026-08-13','0813EDUENEZ','70129592',128.59),
 L('2026-08-11','0811EDUENEZ','69951120',199.00), L('2026-08-07','0807EDUENEZ','69763165',2135.72),
 L('2026-08-07','0807EDUENEZ','69774039',359.84), L('2026-08-07','0807EDUENEZ','69780758',1033.82),
 L('2026-08-05','0805EDUENEZ','69637997',256.13), L('2026-08-05','0805EDUENEZ','69643472',123.59),
 L('2026-08-03','0803EDUENEZ','69427991',196.02), L('2026-07-27','0727EDUENEZ','69003866',65.59),
 L('2026-07-24','0724EDUENEZ','68972327',118.57), L('2026-07-22','0722EDUENEZ','68813489',144.55),
 L('2026-07-20','BERT','68607304',27.25),          L('2026-07-20','0720EDUENEZ','68638026',118.40),
 L('2026-07-20','0718EDUENEZ','68650520',171.96), L('2026-07-15','0715EDUENEZ','68395293',64.29),
 L('2026-07-15','0715EDUENEZ','68425541',96.73),  L('2026-07-14','0714EDUENEZ','68328206',701.23),
 L('2026-07-13','0713EDUENEZ','68269298',92.96),  L('2026-07-10','0710EDUENEZ','68158184',450.20),
 L('2026-07-07','0707EDUENEZ','67914495',437.72),
 // edge cases the model could produce
 L('2026-08-11','0811EDUENEZ','69951120',199.00),          // the same line read twice
 Object.assign(L('2026-08-01','0801EDUENEZ','69400000',''),{amount:''}), // no amount read
];
// what the app already holds
const E=(o)=>Object.assign({type:'ap',party:'McMaster-Carr',paid:0,ref:'',account:''},o);
ENTRIES=[
  E({id:'ap_o1_x',auto:true,poRef:'PO 0829EDUENEZ',ref:'PO 0829EDUENEZ',amount:null}),      // PO bill, no amount yet -> fill
  E({id:'ap_o2_x',auto:true,poRef:'PO 0828EDUENEZ',ref:'PO 0828EDUENEZ',amount:76.04}),     // PO bill, same amount -> fill (adds inv #)
  E({id:'ap_o3_x',auto:true,poRef:'PO 0826EDUENEZ',ref:'PO 0826EDUENEZ',amount:30}),        // PO bill, different amount -> fill, unchecked
  E({id:'m_1',manual:true,ref:'70764075',amount:235.85}),                                   // already entered by invoice # -> have
  E({id:'ap_o5_x',auto:true,poRef:'PO 0824EDUENEZ',ref:'PO 0824EDUENEZ',amount:296.27,paid:100}), // has a payment -> have, locked
  E({id:'m_2',manual:true,ref:'',amount:172.11}),                                            // same amount, no ref -> possible match, unchecked
  E({id:'m_3',manual:true,party:'Grainger',ref:'70362617',amount:172.11}),                   // other vendor: must NOT match
  E({id:'m_4',manual:true,ref:'INV 68607304',amount:27.25}),                                 // prefix on the stored ref -> have
  E({id:'ap_o6_x',auto:true,poRef:'PO 0817EDUENEZ',ref:'PO 0817EDUENEZ',amount:189.91}),    // PO shipped as 2 invoices: 2nd line's amount matches
];

// ── 1. key helpers ──
ok('refKey strips PO', aiRefKey('PO 0829EDUENEZ')==='0829eduenez', aiRefKey('PO 0829EDUENEZ'));
ok('refKey strips Inv #', aiRefKey('Inv #71052861')==='71052861');
ok('refKey strips No.', aiRefKey('No. 55')==='55');
ok('refKey keeps POWER', aiRefKey('POWER123')==='power123', aiRefKey('POWER123'));
ok('refKey dash/space', aiRefKey('0829-EDUENEZ')===aiRefKey(' 0829 eduenez '));
ok('sameVendor prefix', aiSameVendor(vendorKey('McMaster-Carr Supply Company'),vendorKey('McMaster-Carr')));
ok('sameVendor exact', aiSameVendor('acme','acme'));
ok('sameVendor short no', !aiSameVendor('mcm','mcmaster'));
ok('sameVendor other no', !aiSameVendor('grainger','mcmaster_carr'));

// ── 2. statement review ──
aiStmtShow(STMT);
$('ai-modal').style.display='flex';
const R=_aiStmt.rows, byRef=r=>R.find(x=>x.ref===r);
ok('35 rows', R.length===35, R.length);
ok('vendor from lines', $('ai-s-party').value===V);
ok('terms net 30', _aiStmt.terms===30);
ok('discount carried', _aiStmt.discountTerms==='2% 10, Net 30');
let r=byRef('71052861'); ok('PO bill w/o amount -> fill, checked', r.action==='fill'&&r.sel&&r.match.id==='ap_o1_x', r.note);
r=byRef('70996763'); ok('PO bill same amt -> fill, checked', r.action==='fill'&&r.sel&&r.match.id==='ap_o2_x', r.note);
r=byRef('70851422'); ok('PO bill diff amt -> fill, unchecked', r.action==='fill'&&!r.sel&&/30\\.00/.test(r.note), r.note);
r=byRef('70764075'); ok('entered by inv # -> have, locked', r.action==='have'&&!r.sel&&r.locked, r.note);
r=byRef('70676486'); ok('paid bill -> have, locked', r.action==='have'&&!r.sel&&r.locked&&/paid/.test(r.note), r.note);
r=byRef('70362617'); ok('amount-only -> add, unchecked (not Grainger)', r.action==='add'&&!r.sel&&r.match.id==='m_2', r.note);
r=byRef('68607304'); ok('stored ref with INV prefix -> have', r.action==='have'&&r.match.id==='m_4', r.note);
ok('clean line -> add, checked', byRef('69763165').action==='add'&&byRef('69763165').sel);
r=byRef('70697010'); ok('2nd invoice on a claimed PO -> add w/ note', r.action==='add'&&r.sel&&!r.match&&/Another line/.test(r.note), r.note);
r=byRef('70265711'); ok('PO split: the amount-matching line fills', r.action==='fill'&&r.sel&&r.match.id==='ap_o6_x', r.note);
r=byRef('70249613'); ok('PO split: the other line is its own bill', r.action==='add'&&r.sel&&!r.match&&/0817EDUENEZ/.test(r.note), r.note);
ok('no _m left on rows', R.every(x=>!('_m' in x)));
const dups=R.filter(x=>x.ref==='69951120'); ok('repeated line: first add, second have', dups[0].action==='add'&&dups[0].sel&&dups[1].action==='have'&&dups[1].locked);
r=byRef('69400000'); ok('no amount -> unchecked w/ note', r.amount===null&&!r.sel&&/No amount/.test(r.note), r.note);
ok('due = issue+30', /9\\/30\\/26/.test($('ai-s-table').rows[1].cells[5].textContent), $('ai-s-table').rows[1].cells[5].textContent);
const expAdds=R.filter(x=>x.sel&&x.action==='add').length, expFills=R.filter(x=>x.sel&&x.action==='fill').length;
ok('summary counts', new RegExp('<b>'+expAdds+'</b> new · <b>'+expFills+'</b> onto').test($('ai-s-summary').innerHTML), $('ai-s-summary').textContent);
ok('button label', $('ai-add').textContent==='Add '+(expAdds+expFills)+' bills', $('ai-add').textContent);
ok('account select built', $('ai-s-account').options.length===3);
ok('table has 35 body rows', $('ai-s-table').tBodies[0].rows.length===35);

// ── 3. edits + select all / clear ──
aiStmtEdit(byRef('69400000').i,'amount','12.5'); ok('typed amount lands', byRef('69400000').amount===12.5);
aiStmtSel(byRef('69400000').i,true); ok('tick after typing', byRef('69400000').sel);
aiStmtSel(byRef('70764075').i,true); ok('locked row stays unticked', !byRef('70764075').sel);
aiStmtCheck(false); ok('clear -> none selected', R.every(x=>!x.sel));
aiStmtCheck(true); ok('select all new -> adds+fills, not have', R.filter(x=>x.sel).length===R.filter(x=>x.action!=='have'&&x.amount>0).length);
ok('select all skips have', !byRef('70764075').sel && byRef('70851422').sel);
aiStmtSel(byRef('70851422').i,false); aiStmtSel(byRef('70362617').i,false);

// ── 4. commit ──
$('ai-s-account').value='acc1';
const nAdd=R.filter(x=>x.sel&&x.action==='add').length, nFill=R.filter(x=>x.sel&&x.action==='fill').length;
aiStmtCommit();
ok('writes = selected adds', writes.length===nAdd, writes.length+' vs '+nAdd);
ok('patches = selected fills', patches.length===nFill, patches.length+' vs '+nFill);
const w0=writes.find(w=>w.o.ref==='69763165').o;
ok('new bill shape', w0.manual&&w0.type==='ap'&&w0.party===V&&w0.amount===2135.72&&w0.issue==='2026-08-07'&&w0.terms===30&&w0.discountTerms==='2% 10, Net 30'&&w0.account==='acc1'&&w0.payStatus==='open'&&w0.rel==='PO 0807EDUENEZ', JSON.stringify(w0));
const p1=patches.find(p=>p.id==='ap_o1_x').patch;
ok('fill no-amount PO bill: amount+ref+issue', p1.amount===112.87&&p1.ref==='71052861'&&p1.issue==='2026-08-31'&&p1.account==='acc1', JSON.stringify(p1));
const p2=patches.find(p=>p.id==='ap_o2_x').patch;
ok('fill same-amount PO bill: ref+issue only', p2.amount===undefined&&p2.ref==='70996763'&&p2.issue==='2026-08-28', JSON.stringify(p2));
ok('unchecked diff-amount bill untouched', !patches.find(p=>p.id==='ap_o3_x'));
ok('have rows untouched', !patches.find(p=>p.id==='m_1'||p.id==='ap_o5_x'||p.id==='m_4'));
ok('audit per write', audits.length===writes.length+patches.length, audits.length);
ok('vendor account remembered', vendorAccounts[vendorKey(V)]==='acc1');
ok('every write has a positive amount', writes.every(w=>w.o.amount>0));
ok('typed-amount line was added', !!writes.find(w=>w.o.ref==='69400000'&&w.o.amount===12.5));

// restore the pre-commit view for a screenshot
aiStmtShow(STMT); $('ai-modal').style.display='flex';
const fails=out.filter(l=>l.startsWith('FAIL')).length;
document.title=fails?('FAILURES ('+fails+')'):('all pass ('+out.length+')');
document.getElementById('out').textContent=document.title+'\\n'+out.join('\\n');
</script>
'''.replace('/*__BLOCK__*/', block)

io.open('C:/Users/info/bsmp-orders/_stmttest.html', 'w', encoding='utf-8').write(html)
print('wrote _stmttest.html')
