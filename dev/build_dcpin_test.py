# Drawing Check pin view — test harness.
# Builds dev/_dcpin/: two sample drawings (customer + ours, PNG and a 2-page PDF of the
# customer's), and qc_test.html = qc.html with the Firebase module swapped for an
# in-memory stub (fake manager sign-in, RTDB writes logged to window.__writes, uploads
# return the served sample URLs) and the AI call replaced by a fed-in result.
# Serve the repo (launch config "bsmp-apps", port 8123) and open
#   http://localhost:8123/dev/_dcpin/qc_test.html
# then call  dcTestLive()  (compare two picked files) or  dcTestSaved('pdf'|'png'|'bad').
# dev/_dcpin/ is scratch — don't commit it.
import io, os, re, json
from PIL import Image, ImageDraw, ImageFont

ROOT = 'C:/Users/info/bsmp-orders/'
OUT = ROOT + 'dev/_dcpin/'
os.makedirs(OUT, exist_ok=True)
W, H = 1700, 1100
F = lambda n: ImageFont.truetype('C:/Windows/Fonts/arial.ttf', n)
FB = lambda n: ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', n)

def sheet(title_lines, dims, cols=8, rows=4):
    im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
    m = 34
    d.rectangle([m, m, W - m, H - m], outline='black', width=3)
    d.rectangle([12, 12, W - 12, H - 12], outline='black', width=1)
    # border grid: numbers right-to-left (1 at the right), letters bottom-to-top (A at the bottom) — ASME style
    for c in range(cols):
        x = m + (W - 2 * m) * (c + 0.5) / cols; n = str(cols - c)
        d.text((x, 23), n, font=F(16), fill='black', anchor='mm'); d.text((x, H - 23), n, font=F(16), fill='black', anchor='mm')
        if c: xx = m + (W - 2 * m) * c / cols; d.line([xx, 12, xx, m], fill='black'); d.line([xx, H - m, xx, H - 12], fill='black')
    for r in range(rows):
        y = m + (H - 2 * m) * (r + 0.5) / rows; L = chr(65 + rows - 1 - r)
        d.text((23, y), L, font=F(16), fill='black', anchor='mm'); d.text((W - 23, y), L, font=F(16), fill='black', anchor='mm')
        if r: yy = m + (H - 2 * m) * r / rows; d.line([12, yy, m, yy], fill='black'); d.line([W - m, yy, W - 12, yy], fill='black')
    # the part: a plate with 4 holes, one radiused corner
    px0, py0, px1, py1 = 300, 300, 1150, 760
    d.rectangle([px0, py0, px1, py1], outline='black', width=3)
    for hx, hy in [(380, 380), (1070, 380), (380, 680), (1070, 680)]:
        d.ellipse([hx - 16, hy - 16, hx + 16, hy + 16], outline='black', width=2)
    # dimension lines
    d.line([px0, 230, px1, 230], fill='black', width=1); d.line([px0, 220, px0, py0], fill='black'); d.line([px1, 220, px1, py0], fill='black')
    d.line([220, py0, 220, py1], fill='black', width=1); d.line([210, py0, px0, py0], fill='black'); d.line([210, py1, px0, py1], fill='black')
    # title block
    tb = [1220, 820, W - m, H - m]; d.rectangle(tb, outline='black', width=2)
    y = 832
    for ln in title_lines:
        d.text((1235, y), ln, font=F(17), fill='black'); y += 26
    for txt, (x, y), size in dims:
        d.text((x, y), txt, font=FB(size), fill='black', anchor='mm')
    return im

cust_dims = [('12.000', (725, 215), 22), ('6.500', (190, 530), 22), ('Ø.250 THRU 4X', (470, 360), 18),
             ('R.125', (1180, 790), 18), ('BEND UP 90°', (725, 820), 18), ('.80 TYP', (440, 900), 18)]
mine_dims = [('12.006', (735, 210), 22), ('6.500', (185, 535), 22), ('Ø.250 THRU 4X', (480, 355), 18),
             ('BEND UP 90°', (735, 815), 18)]
cust = sheet(['PART NO. 10-4471', 'REV B', 'MATERIAL: 16 GA 304 SS', 'FINISH: #4 BRUSH', 'UNLESS OTHERWISE SPECIFIED:',
              '.XX ±.020  .XXX ±.005  ANG ±1°'], cust_dims)
mine = sheet(['PART NO. 10-4471', 'REV B', 'MATERIAL: 16 GA 304', 'FINISH: #4 BRUSH', 'BSMP  —  JOB 2617'], mine_dims)
cust.save(OUT + 'cust.png'); mine.save(OUT + 'mine.png')
notes = Image.new('RGB', (W, H), 'white'); dn = ImageDraw.Draw(notes)
dn.rectangle([34, 34, W - 34, H - 34], outline='black', width=3)
dn.text((120, 140), 'NOTES:', font=FB(26), fill='black')
dn.text((120, 190), '1. DEBURR ALL EDGES.', font=F(22), fill='black')
dn.text((120, 230), '2. HARDWARE PER BOM — SEE SHEET 3 (NOT PROVIDED).', font=FB(22), fill='black')
cust.save(OUT + 'cust.pdf', save_all=True, append_images=[notes], resolution=150)

fx = lambda x: round(x / W, 4); fy = lambda y: round(y / H, 4)
# The fed-in AI reply: locations deliberately a bit off on two rows (to drag), null on two (zone fallback / none).
AI = {
  'custTitleBlock': {'stated': True, 'frac': None, 'p2': 0.020, 'p3': 0.005, 'ang': 1},
  'custGrid': {'cols': 8, 'rows': 4, 'numbers': 'right-to-left', 'letters': 'bottom-to-top'},
  'mineGrid': {'cols': 8, 'rows': 4, 'numbers': 'right-to-left', 'letters': 'bottom-to-top'},
  'rows': [
    {'feature': 'Overall length', 'kind': 'dim', 'cust': '12.000', 'mine': '12.006', 'zone': 'D5', 'mineZone': 'D5',
     'custAt': {'page': 1, 'x': fx(725), 'y': fy(215)}, 'mineAt': {'page': 1, 'x': fx(735), 'y': fy(210)}, 'note': ''},
    {'feature': 'Overall height', 'kind': 'dim', 'cust': '6.500', 'mine': '6.500', 'zone': 'C8', 'mineZone': 'C8',
     'custAt': {'page': 1, 'x': fx(190), 'y': fy(530)}, 'mineAt': {'page': 1, 'x': fx(185), 'y': fy(535)}, 'note': ''},
    {'feature': 'Hole size', 'kind': 'hole', 'cust': 'Ø.250 THRU 4X', 'mine': 'Ø.250 THRU 4X', 'zone': 'D7', 'mineZone': 'D7',
     'custAt': {'page': 1, 'x': fx(470), 'y': fy(360)}, 'mineAt': {'page': 1, 'x': fx(560), 'y': fy(420)}, 'note': ''},
    {'feature': 'Corner radius', 'kind': 'dim', 'cust': 'R.125', 'mine': '', 'zone': 'B4', 'mineZone': '',
     'custAt': None, 'mineAt': None, 'note': ''},
    {'feature': 'Bend angle', 'kind': 'angle', 'cust': 'BEND UP 90°', 'mine': 'BEND UP 90°', 'zone': 'B5', 'mineZone': 'B5',
     'custAt': {'page': 1, 'x': fx(725), 'y': fy(820)}, 'mineAt': {'page': 1, 'x': fx(735), 'y': fy(815)}, 'note': ''},
    {'feature': 'Material', 'kind': 'material', 'cust': '16 GA 304 SS', 'mine': '16 GA 304', 'zone': 'A2', 'mineZone': 'A2',
     'custAt': {'page': 1, 'x': fx(1330), 'y': fy(895)}, 'mineAt': {'page': 1, 'x': fx(1330), 'y': fy(895)}, 'note': ''},
    {'feature': 'Part number', 'kind': 'part', 'cust': '10-4471', 'mine': '10-4471', 'zone': 'A2', 'mineZone': 'A2',
     'custAt': {'page': 1, 'x': fx(1310), 'y': fy(843)}, 'mineAt': {'page': 1, 'x': fx(1310), 'y': fy(843)}, 'note': ''},
    {'feature': 'Revision', 'kind': 'rev', 'cust': 'REV B', 'mine': 'REV B', 'zone': 'A2', 'mineZone': 'A2',
     'custAt': {'page': 1, 'x': fx(1265), 'y': fy(868)}, 'mineAt': {'page': 1, 'x': fx(1265), 'y': fy(868)}, 'note': ''},
    {'feature': 'Hole edge distance', 'kind': 'dim', 'cust': '.80 TYP', 'mine': '', 'zone': 'A7', 'mineZone': '',
     'custAt': {'page': 1, 'x': fx(440), 'y': fy(900)}, 'mineAt': None, 'note': ''},
    {'feature': 'Job number', 'kind': 'note', 'cust': '', 'mine': 'BSMP — JOB 2617', 'zone': '', 'mineZone': 'A2',
     'custAt': None, 'mineAt': {'page': 1, 'x': fx(1320), 'y': fy(947)}, 'note': ''},
  ],
  'questions': [
    {'topic': 'Hardware', 'detail': 'Note 2 calls for hardware per BOM on sheet 3, which was not sent — ask for the BOM.', 'zone': '',
     'custAt': {'page': 2, 'x': fx(500), 'y': fy(242)}},
    {'topic': 'Bend direction', 'detail': '"BEND UP" has no view showing which face is up.', 'zone': 'B5', 'custAt': None},
  ],
  'summary': 'Our length is .006 long and the R.125 corner and .80 edge distance are missing on ours.'
}

src = io.open(ROOT + 'qc.html', encoding='utf-8').read()
stub = '''<script>
/* ---- test stub for the Firebase module ---- */
window.__writes=[]; window.__db={};
const __clone=(v)=>v==null?v:JSON.parse(JSON.stringify(v));
function __get(path){ return path.split('/').reduce((o,k)=>o==null?o:o[k], window.__db); }
function __put(path,val){ const ks=path.split('/'); let o=window.__db; ks.slice(0,-1).forEach(k=>{ if(o[k]==null||typeof o[k]!=='object') o[k]={}; o=o[k]; }); if(val==null) delete o[ks[ks.length-1]]; else o[ks[ks.length-1]]=__clone(val); }
function __tick(){ setTimeout(()=>window.qcOnData('drawingChecks', __clone(__get('qc/drawingChecks'))||{}), 30); }
window.qcSet=async (p,v)=>{ window.__writes.push({op:'set',path:p,val:__clone(v)}); __put(p,v); __tick(); };
window.qcUpdate=async (p,v)=>{ window.__writes.push({op:'update',path:p,val:__clone(v)}); Object.keys(v).forEach(k=>__put(p+'/'+k,v[k])); __tick(); };
window.qcRemove=async (p)=>{ window.__writes.push({op:'remove',path:p}); __put(p,null); __tick(); };
window.qcUpload=async (file,prefix)=>'/dev/_dcpin/'+(/mine/.test(file.name)?'mine.png':(/pdf$/i.test(file.name)?'cust.pdf':'cust.png'));
window.__AI=%s;
const __SAVED=(id,cu,mi)=>({id, createdAt:Date.now()-86400000, createdBy:'ofc.edgar@bertsmp.com', partNum:'10-4471', customer:'Test Co', rev:'B',
  custDrawing:{name:cu.split('/').pop(), url:cu, type:/pdf$/.test(cu)?'application/pdf':'image/png'}, myDrawing:{name:mi.split('/').pop(), url:mi, type:'image/png'}});
window.addEventListener('load', ()=>{
  window.hasAIConnection=()=>true;
  window.callAIJsonContent=async ()=>{ await new Promise(r=>setTimeout(r,200)); return __clone(window.__AI); };
  const lg=document.getElementById('qc-login'); if(lg) lg.style.display='none';
  window.qcOnAuth({email:'ofc.edgar@bertsmp.com'}, 'manager');
  showPage('drawcheck');
});
// live: put the two sample files on the form and run the (stubbed) AI compare
window.dcTestLive=async (custFile)=>{
  const get=async (u,n,tp)=>new File([await (await fetch(u)).blob()], n, {type:tp});
  _pendingFiles['dccust']=[await get('/dev/_dcpin/'+(custFile||'cust.png'), custFile||'cust.png', /pdf$/.test(custFile||'')?'application/pdf':'image/png')];
  _pendingFiles['dcmine']=[await get('/dev/_dcpin/mine.png','mine.png','image/png')];
  await qcDrawCompare();
};
// saved: build a record the way qcSaveDrawCheck would and open it
window.dcTestSaved=async (kind)=>{
  const cu=kind==='bad'?'https://firebasestorage.googleapis.com/v0/b/x/o/nope.pdf?alt=media':(kind==='pdf'?'/dev/_dcpin/cust.pdf':'/dev/_dcpin/cust.png');
  const mi=kind==='bad'?'https://example.invalid/nope.png':'/dev/_dcpin/mine.png';
  _pendingFiles['dccust']=[]; _pendingFiles['dcmine']=[];
  const a=__clone(window.__AI), tol=dcTolDefaults(a.custTitleBlock);
  const rows=dcComputeRows(a.rows, tol.defaults).sort((x,y)=>(DC_ORDER[x.status]-DC_ORDER[y.status]));
  const rec=Object.assign(__SAVED('dchk_'+kind, cu, mi), dcRecomputeVerdict({ranAt:Date.now(), rows, questions:a.questions.map(q=>Object.assign({},q,{custAt:dcAt(q.custAt)})),
    custGrid:dcGrid(a.custGrid), mineGrid:dcGrid(a.mineGrid), tolDefaults:tol.defaults, tolFromCustomer:tol.fromCustomer, summary:a.summary}));
  __put('qc/drawingChecks/'+rec.id, rec); window.qcOnData('drawingChecks', __clone(__get('qc/drawingChecks')));
  qcDrawCheckOpen(rec.id);
};
</script>''' % json.dumps(AI, ensure_ascii=False)
out = re.sub(r'<script type="module">.*?</script>', lambda m: stub, src, count=1, flags=re.S)
assert out != src
io.open(OUT + 'qc_test.html', 'w', encoding='utf-8', newline='').write(out)
print('built', OUT)
