# -*- coding: utf-8 -*-
# Quote history merge-down (quoteSnaps). What has to be proven: pulling from the cloud
# only ever ADDS or brings a genuinely newer edit, never removes, never resurrects a
# deleted quote, and never "updates" a quote just because RTDB dropped its empty arrays.
# Writes _quotesync_test.html; serve the repo on :8123 and read the page title.
import io
src = io.open('C:/Users/info/bsmp-orders/quote.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block = grab('// \u2500\u2500 Quote history merge-down', 'let _qHistListening = false;')

html = u'''<!doctype html><meta charset="utf-8"><title>quote sync test</title>
<div id="q-syncall-status"></div>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
// this page shares localhost:8123 storage with a real signed-in copy of the app: back up, clear, restore at the end
const _KEYS=['bsmp_quote_tombstones','bsmp_quote_snapped','bsmp_customers'];
const _SAVED={}; _KEYS.forEach(k=>{ _SAVED[k]=localStorage.getItem(k); localStorage.removeItem(k); });
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
// stubs for what the real block expects from the page / module
let HISTORY=[]; let persists=0, renders=0, toasts=[];
let CUSTOMERS=[{name:'Acme',markup:18,finance:7}]; let custRenders=0;
function populateCustomerSelect(){ custRenders++; }
function persistHistory(){ persists++; }
function renderHistory(){ renders++; }
function showToast(o){ toasts.push(o.sub); }
const _qSynced=new Set(); function _qSaveSynced(){}
function _qLocalQuotes(){ return HISTORY; }
const $q=id=>document.getElementById(id);
const db={}; const ref=(d,p)=>p; let setCalls=[]; let failSet=false;
async function set(p,v){ if(failSet) throw new Error('PERMISSION_DENIED'); setCalls.push([p,v]); }
/*__BLOCK__*/
const reset=list=>{ HISTORY=JSON.parse(JSON.stringify(list)); persists=0; renders=0; toasts=[]; };
const byId=id=>HISTORY.find(q=>String(q.id)===String(id));
const full=(id,extra)=>Object.assign({id, date:'Sep 24, 2026', status:'pending', partNum:'P'+id, revision:'A', customer:'Acme', qty:2,
  material:'0.060 thk CRS', pricePerPart:10, laborLines:[{op:'602 Form- Level 1',mins:'1'}], hwLines:[], outLines:[], qtyBreaks:[], notes:'', img:'data:x'}, extra||{});
// what RTDB hands back: no img, empty arrays and empty strings gone
const cloud=q=>{ const c=JSON.parse(JSON.stringify(q)); delete c.img; Object.keys(c).forEach(k=>{ if(c[k]==='' || (Array.isArray(c[k])&&!c[k].length)) delete c[k]; }); return c; };

// 1. a quote made in another browser appears here, fully shaped
reset([full(1)]);
_qMergeDown({2: cloud(full(2,{savedAt:5}))}, null);
ok('add: new cloud quote is added', !!byId(2));
ok('add: empty arrays restored after RTDB dropped them', Array.isArray(byId(2).hwLines) && Array.isArray(byId(2).qtyBreaks));
ok('add: saved + re-rendered once', persists===1 && renders===1, persists+'/'+renders);
ok('add: toast says 1 added', toasts[0]==='1 quote added from the cloud', toasts[0]);
ok('add: newest id first', HISTORY[0].id===2 && HISTORY[1].id===1);
ok('add: local quote untouched (img kept)', byId(1).img==='data:x');

// 2. nothing new -> nothing written
reset([full(1,{savedAt:5})]);
_qMergeDown({1: cloud(full(1,{savedAt:5}))}, {});
ok('no-op: identical copy writes nothing', persists===0 && renders===0 && !toasts.length);

// 3. RTDB-dropped empties are NOT a change, even if the cloud copy is "newer"
reset([full(1)]);
_qMergeDown({1: cloud(full(1,{savedAt:9}))}, null);
ok('no-op: dropped empty arrays/strings are not an edit', persists===0);
ok('no-op: local quote adopts the cloud savedAt', byId(1).savedAt===9);
ok('no-op: local img survives', byId(1).img==='data:x');

// 4. a real, newer edit from another browser replaces the local copy (keeping the thumbnail)
reset([full(1,{savedAt:5})]);
_qMergeDown({1: cloud(full(1,{savedAt:8, status:'accepted', pricePerPart:12}))}, null);
ok('update: newer edit wins', byId(1).status==='accepted' && byId(1).pricePerPart===12);
ok('update: thumbnail kept from the local copy', byId(1).img==='data:x');
ok('update: toast says 1 updated', toasts[0]==='1 updated from the cloud', toasts[0]);

// 5. an OLDER cloud copy (stale browser re-synced) never overwrites a newer local edit
reset([full(1,{savedAt:8, status:'accepted'})]);
_qMergeDown({1: cloud(full(1,{savedAt:5, status:'pending'}))}, null);
ok('stale: older cloud copy ignored', byId(1).status==='accepted' && persists===0);
reset([full(1,{savedAt:8, status:'accepted'})]);
_qMergeDown({1: cloud(full(1,{status:'pending'}))}, null);
ok('stale: cloud copy with no savedAt ignored', byId(1).status==='accepted');

// 6. additive only: quotes missing from the cloud stay put, an empty/failed read changes nothing
reset([full(1), full(2)]);
_qMergeDown({}, {});
ok('additive: empty cloud removes nothing', HISTORY.length===2 && persists===0);
_qMergeDown(null, null);
ok('additive: null read removes nothing', HISTORY.length===2);

// 7. deleted here -> the cloud cannot bring it back
reset([full(1)]);
window._qTombstone([3]);
_qMergeDown({3: cloud(full(3,{savedAt:9}))}, {3:{id:3, partNum:'P3'}});
ok('tombstone: deleted quote not resurrected', !byId(3) && persists===0);
ok('tombstone: remembered across reloads', JSON.parse(localStorage.getItem('bsmp_quote_tombstones')).includes('3'));

// 8. a trimmed Order-Tracker copy with no full copy is still listed
reset([full(1)]);
_qMergeDown({}, {4:{id:4, partNum:'', customer:'Beta', qty:5, pricePerPart:3, laborLines:[{op:'x',mins:'1'}]}});
ok('lite: trimmed-only quote added', !!byId(4) && byId(4)._cloudLite===true);
ok('lite: blanks shown as dashes like normal quotes', byId(4).partNum==='\u2014' && byId(4).revision==='\u2014' && byId(4).material==='\u2014');
ok('lite: status defaults to pending', byId(4).status==='pending');
ok('lite: arrays present', Array.isArray(byId(4).outLines) && byId(4).laborLines.length===1);

// 9. a full copy beats the trimmed one for the same id, and upgrades a lite local copy
reset([full(1)]);
_qMergeDown({5: cloud(full(5,{savedAt:1, notes:'full'}))}, {5:{id:5, partNum:'P5'}});
ok('full-over-lite: full copy used', byId(5).notes==='full' && !byId(5)._cloudLite);
reset([Object.assign(full(6),{_cloudLite:true, img:null})]);
_qMergeDown({6: cloud(full(6,{notes:'now full'}))}, null);
ok('upgrade: lite local copy replaced by full copy even without savedAt', byId(6).notes==='now full' && !byId(6)._cloudLite);

// 10. RTDB sometimes returns an array as an object {0:..,1:..}
reset([]);
const odd=cloud(full(7,{savedAt:1})); odd.laborLines={0:{op:'a',mins:'1'},1:{op:'b',mins:'2'}};
_qMergeDown({7: odd}, null);
ok('shape: object-shaped array normalised', Array.isArray(byId(7).laborLines) && byId(7).laborLines.length===2);

// 10b. customers this browser has never seen are added (defaults), known ones untouched
reset([]); CUSTOMERS=[{name:'Acme',markup:18,finance:7}]; custRenders=0;
_qMergeDown({20: cloud(full(20,{customer:'New Co'})), 21: cloud(full(21,{customer:'acme'}))}, {22:{id:22, customer:''}});
ok('customers: unknown customer added with 30/7', CUSTOMERS.some(c=>c.name==='New Co' && c.markup===30 && c.finance===7), JSON.stringify(CUSTOMERS));
ok('customers: known customer (any case) not duplicated, markup kept', CUSTOMERS.filter(c=>/^acme$/i.test(c.name)).length===1 && CUSTOMERS[0].markup===18);
ok('customers: blank / dash customer never added', CUSTOMERS.length===2);
ok('customers: saved + dropdown refreshed', JSON.parse(localStorage.getItem('bsmp_customers')).length===2 && custRenders===1);

// 11. the full copy never carries the drawing thumbnail
ok('snap: img stripped', !('img' in _qSnapOf(full(8))) && _qSnapOf(full(8)).partNum==='P8');

// 12. pushing full copies; a missing rule stops the backfill after ONE failure and says so
(async()=>{
  setCalls=[]; failSet=false; reset([full(10), full(11)]);
  await _qSnapBackfill();
  ok('backfill: every local quote gets a full copy', setCalls.length===2 && setCalls[0][0]==='quoteSnaps/10', setCalls.length);
  setCalls=[]; await _qSnapBackfill();
  ok('backfill: already-copied quotes are not re-sent', setCalls.length===0, setCalls.length);
  window._qTombstone([12]); HISTORY.push(full(12)); setCalls=[]; await _qSnapBackfill();
  ok('backfill: tombstoned quotes skipped', setCalls.length===0);
  HISTORY.push(Object.assign(full(15),{_cloudLite:true})); setCalls=[]; await _qSnapBackfill();
  ok('backfill: trimmed-only copies are never pushed as full copies', setCalls.length===0, setCalls.length);
  _qMergeDown({16: cloud(full(16,{savedAt:3}))}, null); setCalls=[]; await _qSnapBackfill();
  ok('backfill: quotes pulled from the cloud are not sent back', setCalls.length===0, setCalls.length);
  HISTORY.push(full(13), full(14)); failSet=true; setCalls=[];
  await _qSnapBackfill();
  ok('blocked: stops after the first refusal', _qSnapBlocked===true);
  ok('blocked: tells the owner the rule is missing', /quoteSnaps/.test(document.getElementById('q-syncall-status').textContent));
  _KEYS.forEach(k=>{ if(_SAVED[k]===null) localStorage.removeItem(k); else localStorage.setItem(k,_SAVED[k]); });
  const fails=out.filter(l=>l.startsWith('FAIL')).length;
  document.getElementById('out').textContent=out.join('\\n');
  document.title = fails ? ('FAILURES ('+fails+')') : ('all pass ('+out.length+')');
})();
</script>
'''
io.open('C:/Users/info/bsmp-orders/_quotesync_test.html', 'w', encoding='utf-8').write(html.replace('/*__BLOCK__*/', block))
print('wrote _quotesync_test.html,', len(block), 'chars of real code')
