# Model Check re-compare — test harness.
# Builds dev/_mcrc/: qc_test.html = qc.html with the Firebase module swapped for an
# in-memory stub (fake manager sign-in, RTDB writes logged to window.__writes, uploads
# return served sample URLs) and the SolidWorks helper (mcFetch) replaced by two canned
# runs: RUN1 = first compare, RUN2 = after "fixing" our model (one piece gone, one
# changed, one new, two unchanged).
# Serve the repo (launch config "bsmp-apps", port 8123) and open
#   http://localhost:8123/dev/_mcrc/qc_test.html
# then call  mcTestLive()  (run 1 on the live form), sign rows off, mcTestFix() (helper
# now answers RUN2) and press Re-compare; or  mcTestSaved()  for a saved check.
# dev/_mcrc/ is scratch — don't commit it.
import io, os, re, json, base64
from PIL import Image

ROOT = 'C:/Users/info/bsmp-orders/'
OUT = ROOT + 'dev/_mcrc/'
os.makedirs(OUT, exist_ok=True)

def jpg(color):
    b = io.BytesIO(); Image.new('RGB', (320, 220), color).save(b, 'JPEG'); return base64.b64encode(b.getvalue()).decode()
for n in ('cust.step', 'mine.SLDPRT', 'mine_v2.SLDPRT'):
    io.open(OUT + n, 'w').write('fake model ' + n)

def geo(findings, pics):
    return {'ok': True, 'ours': {'title': 'TEST-PART', 'size': [12, 6.5, 1], 'volume': 9.8, 'area': 200, 'bodies': 1, 'config': 'Default'},
            'theirs': {'title': 'CUST', 'size': [12, 6.5, 1], 'volume': 9.81, 'area': 201, 'bodies': 1, 'config': 'Default'},
            'holesOurs': 4, 'holesTheirs': 4, 'rotation': [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 'shift': [0, 0, 0], 'planeDeltas': [],
            'diffVol': {'ours': .3, 'theirs': .01}, 'slivers': {'ours': {'count': 2, 'vol': 1e-5}, 'theirs': {'count': 1, 'vol': 1e-6}},
            'limits': {'minVol': 1e-7, 'thinAvg': .003, 'maskThk': .01}, 'findings': findings, 'pictures': pics}

relief = {'side': 'ours', 'count': 4, 'vol': .0005, 'size': [.25, .06, .06], 'avgThk': .02, 'at': [[1, 1, 0], [11, 1, 0], [1, 5.5, 0], [11, 5.5, 0]]}
disc = {'side': 'theirs', 'count': 1, 'vol': .0022, 'size': [.75, .75, .005], 'avgThk': .005, 'at': [[6, 3.25, 1]], 'suggest': 'masking', 'why': 'customer-only pad .005 thick'}
block = {'side': 'ours', 'count': 1, 'vol': .3, 'size': [.25, .69, .69], 'avgThk': .2, 'at': [[11.9, 3.2, .5]]}
tab = {'side': 'theirs', 'count': 2, 'vol': .01, 'size': [.5, .25, .06], 'avgThk': .05, 'at': [[3, 6.4, 0], [9, 6.4, 0]]}
tab2 = dict(tab, vol=.004, size=[.5, .1, .06], at=[[3.01, 6.41, 0], [9.01, 6.41, 0]])
newp = {'side': 'ours', 'count': 1, 'vol': .001, 'size': [.1, .1, .1], 'avgThk': .03, 'at': [[8, 8, 0]]}
P1 = {k: jpg(c) for k, c in (('iso', '#ccd'), ('top', '#cdc'), ('front', '#dcc'), ('diffs', '#ddc'))}
P2 = {k: jpg(c) for k, c in (('iso', '#99a'), ('top', '#9a9'), ('front', '#a99'), ('diffs', '#aa9'))}
RUN1 = geo([relief, disc, block, tab], P1)
RUN2 = geo([dict(relief), dict(disc), tab2, newp], P2)

src = io.open(ROOT + 'qc.html', encoding='utf-8').read()
stub = '''<script>
/* ---- test stub for the Firebase module ---- */
window.__writes=[]; window.__db={}; window.__checks=[];
const __clone=(v)=>v==null?v:JSON.parse(JSON.stringify(v));
function __get(path){ return path.split('/').reduce((o,k)=>o==null?o:o[k], window.__db); }
function __put(path,val){ const ks=path.split('/'); let o=window.__db; ks.slice(0,-1).forEach(k=>{ if(o[k]==null||typeof o[k]!=='object') o[k]={}; o=o[k]; }); if(val==null) delete o[ks[ks.length-1]]; else o[ks[ks.length-1]]=__clone(val); }
function __tick(){ setTimeout(()=>window.qcOnData('drawingChecks', __clone(__get('qc/drawingChecks'))||{}), 30); }
window.qcSet=async (p,v)=>{ window.__writes.push({op:'set',path:p,val:__clone(v)}); __put(p,v); __tick(); };
window.qcUpdate=async (p,v)=>{ window.__writes.push({op:'update',path:p,val:__clone(v)}); Object.keys(v).forEach(k=>__put(p+'/'+k,v[k])); __tick(); };
window.qcRemove=async (p)=>{ window.__writes.push({op:'remove',path:p}); __put(p,null); __tick(); };
window.qcUpload=async (file,prefix)=>/\\.jpg$/.test(file.name)?('data:image/jpeg;base64,'+(await toBase64(file))):('/dev/_mcrc/'+file.name);
window.__RUN1=%s; window.__RUN2=%s; window.__run=1;
window.addEventListener('load', ()=>{
  window.mcFetch=async (path,opts)=>{
    if(path==='/status') return {ok:true, solidworks:true, version:1};
    if(path==='/parts') return {ok:true, parts:[{title:'TEST-PART.SLDPRT', path:'C:\\\\Parts\\\\TEST-PART.SLDPRT'},{title:'CUST.SLDPRT', path:'C:\\\\Parts\\\\CUST.SLDPRT'}]};
    if(path==='/check'){ const b=JSON.parse(opts.body); window.__checks.push({ours:b.ours.path||b.ours.name, theirs:b.theirs.path||b.theirs.name, b64:!!(b.ours.b64||b.theirs.b64)});
      await new Promise(r=>setTimeout(r,600)); if(window.__fail) return {ok:false, error:'SolidWorks said no'}; return __clone(window.__run===1?window.__RUN1:window.__RUN2); }
  };
  const lg=document.getElementById('qc-login'); if(lg) lg.style.display='none';
  window.qcOnAuth({email:'ofc.edgar@bertsmp.com'}, 'manager');
  showPage('modelcheck');
});
window.mcTestLive=async ()=>{ window.__run=1; mcPickOurs('C:\\\\Parts\\\\TEST-PART.SLDPRT'); _mc.theirsFile=new File([await (await fetch('/dev/_mcrc/cust.step')).blob()],'cust.step'); _mc.f.part='TEST-1'; await mcRun(); };
window.mcTestFix=()=>{ window.__run=2; };
window.mcTestFixFile=async ()=>new File([await (await fetch('/dev/_mcrc/mine_v2.SLDPRT')).blob()], 'mine_v2.SLDPRT');
// a saved check made from run 1, rows 0 and 1 signed off, uploaded models on file
window.mcTestSaved=()=>{
  window.__run=1;
  const g=__clone(window.__RUN1); delete g.pictures; delete g.ok;
  const res=mcRecompute({ranAt:Date.now()-86400000, by:'ofc.edgar@bertsmp.com', geo:g, rows:mcRowsFrom(g.findings), oursName:'mine.SLDPRT', oursPath:'', theirsName:'cust.step', theirsPath:''});
  res.rows[0].accepted=true; res.rows[0].acceptWhy='clearance'; res.rows[0].acceptBy='ofc.edgar@bertsmp.com'; res.rows[0].acceptAt=Date.now()-86000000;
  res.rows[1].accepted=true; res.rows[1].acceptWhy='masking'; res.rows[1].acceptBy='ofc.edgar@bertsmp.com'; res.rows[1].acceptAt=Date.now()-86000000;
  mcRecompute(res);
  const rec=Object.assign(res, {id:'mchk_t1', kind:'model', createdAt:Date.now()-86400000, createdBy:'ofc.edgar@bertsmp.com', partNum:'TEST-1', customer:'Test Co',
    custModel:{name:'cust.step', url:'/dev/_mcrc/cust.step'}, myModel:{name:'mine.SLDPRT', url:'/dev/_mcrc/mine.SLDPRT'},
    pictures:{iso:{name:'iso.jpg', url:'data:image/jpeg;base64,'+window.__RUN1.pictures.iso}, diffs:{name:'d.jpg', url:'data:image/jpeg;base64,'+window.__RUN1.pictures.diffs}}});
  __put('qc/drawingChecks/'+rec.id, rec); window.qcOnData('drawingChecks', __clone(__get('qc/drawingChecks')));
  mcOpen(rec.id);
};
</script>''' % (json.dumps(RUN1), json.dumps(RUN2))
out = re.sub(r'<script type="module">.*?</script>', lambda m: stub, src, count=1, flags=re.S)
assert out != src
io.open(OUT + 'qc_test.html', 'w', encoding='utf-8', newline='').write(out)
print('built', OUT)
