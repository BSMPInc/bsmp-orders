# Inspection photo viewer + drawing-over-photo overlay — test harness.
# Builds dev/_ovtest/: a sample drawing (PNG + 2-page PDF) of a 4-hole plate, a fake
# "photo" of that plate (turned, scaled, on a dark bench), and qc_test.html = qc.html with
# the Firebase module swapped for an in-memory stub (fake manager sign-in, RTDB writes
# logged to window.__writes and fed back through qcOnData like the real listeners,
# uploads become blob: URLs) plus a saved self-check and first article that use them.
# Serve the repo (launch config "bsmp-apps", port 8123) and open
#   http://localhost:8123/dev/_ovtest/qc_test.html
# dev/_ovtest/ is scratch — don't commit it.
import io, os, re, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = 'C:/Users/info/bsmp-orders/'
OUT = ROOT + 'dev/_ovtest/'
os.makedirs(OUT, exist_ok=True)
W, H = 1700, 1100
F = lambda n: ImageFont.truetype('C:/Windows/Fonts/arial.ttf', n)
FB = lambda n: ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', n)
PX0, PY0, PX1, PY1 = 300, 300, 1150, 760
HOLES = [(380, 380), (1070, 380), (380, 680), (1070, 680), (725, 530)]

dw = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(dw)
d.rectangle([34, 34, W - 34, H - 34], outline='black', width=3)
d.rectangle([PX0, PY0, PX1, PY1], outline='black', width=3)
for hx, hy in HOLES:
    r = 30 if (hx, hy) == (725, 530) else 16
    d.ellipse([hx - r, hy - r, hx + r, hy + r], outline='black', width=2)
d.line([PX0, 230, PX1, 230], fill='black'); d.text((725, 215), '12.000', font=FB(22), fill='black', anchor='mm')
d.line([220, PY0, 220, PY1], fill='black'); d.text((190, 530), '6.500', font=FB(22), fill='black', anchor='mm')
d.text((470, 360), 'Ø.250 THRU 4X', font=FB(18), fill='black', anchor='mm')
d.rectangle([1220, 820, W - 34, H - 34], outline='black', width=2)
for i, ln in enumerate(['PART NO. 10-4471', 'REV B', 'MATERIAL: 16 GA 304 SS']):
    d.text((1235, 832 + 26 * i), ln, font=F(17), fill='black')
dw.save(OUT + 'drawing.png')
notes = Image.new('RGB', (W, H), 'white'); ImageDraw.Draw(notes).text((120, 140), 'NOTES: DEBURR ALL EDGES.', font=FB(26), fill='black')
dw.save(OUT + 'drawing.pdf', save_all=True, append_images=[notes], resolution=150)

# the "photo": the plate turned 7°, about 1.9x, offset, on a dark bench (a 3000x2250 camera shot)
PW, PH = 3000, 2250
ph = Image.new('RGB', (PW, PH), (52, 48, 44))
plate = Image.new('RGBA', (PX1 - PX0, PY1 - PY0), (186, 190, 194, 255)); pd = ImageDraw.Draw(plate)
for hx, hy in HOLES:
    r = 30 if (hx, hy) == (725, 530) else 16
    pd.ellipse([hx - PX0 - r, hy - PY0 - r, hx - PX0 + r, hy - PY0 + r], fill=(30, 28, 26, 255))
k = 1.9
plate = plate.resize((int(plate.width * k), int(plate.height * k)), Image.LANCZOS).rotate(-7, expand=True, resample=Image.BICUBIC)
ph.paste(plate, (PW // 2 - plate.width // 2 + 120, PH // 2 - plate.height // 2 - 60), plate)
ph = ph.filter(ImageFilter.GaussianBlur(1.2))
ph.save(OUT + 'photo1.jpg', quality=88)
ph.rotate(180).save(OUT + 'photo2.jpg', quality=88)

src = io.open(ROOT + 'qc.html', encoding='utf-8').read()
stub = '''<script>
/* ---- test stub for the Firebase module ---- */
window.__writes=[]; window.__db={qc:{inspections:{}, audit:{}, drawings:{}}};
const __clone=(v)=>v==null?v:JSON.parse(JSON.stringify(v));
function __get(path){ return path.split('/').reduce((o,k)=>o==null?o:o[k], window.__db); }
function __put(path,val){ const ks=path.split('/'); let o=window.__db; ks.slice(0,-1).forEach(k=>{ if(o[k]==null||typeof o[k]!=='object') o[k]={}; o=o[k]; }); if(val==null) delete o[ks[ks.length-1]]; else o[ks[ks.length-1]]=__clone(val); }
function __tick(){ setTimeout(()=>{ ['inspections','audit','drawings'].forEach(n=>window.qcOnData(n, __clone(__get('qc/'+n))||{})); }, 30); }
window.qcSet=async (p,v)=>{ window.__writes.push({op:'set',path:p,val:__clone(v)}); __put(p,v); __tick(); };
window.qcUpdate=async (p,v)=>{ window.__writes.push({op:'update',path:p,val:__clone(v)}); Object.keys(v).forEach(k=>__put(p+'/'+k,v[k])); __tick(); };
window.qcRemove=async (p)=>{ window.__writes.push({op:'remove',path:p}); __put(p,null); __tick(); };
window.__uploads=[];
window.qcUpload=async (file,prefix)=>{ window.__uploads.push({name:file.name, type:file.type, size:file.size, prefix}); return URL.createObjectURL(file); };
const B='/dev/_ovtest/';
// messy shapes on purpose: photos as an object with a null hole, drawings missing on the FAR
__put('qc/inspections/insp_t1', {id:'insp_t1', type:'self', createdAt:Date.now()-3600e3, createdBy:'ops.luis@bertsmp.com', partNum:'10-4471', customer:'Test Co', job:'2617', rev:'B', qty:'10', result:'Pass', status:'Logged',
  photos:{0:{name:'photo1.jpg', url:B+'photo1.jpg', type:'image/jpeg'}, 1:null, 2:{name:'photo2.jpg', url:B+'photo2.jpg', type:'image/jpeg'}},
  drawing:{name:'drawing.pdf', url:B+'drawing.pdf', type:'application/pdf'}, drawings:[{name:'drawing.pdf', url:B+'drawing.pdf', type:'application/pdf'}], notes:'saved notes'});
__put('qc/inspections/fair_t2', {id:'fair_t2', type:'fair', mode:'simple', createdAt:Date.now()-7200e3, createdBy:'ofc.edgar@bertsmp.com', partNum:'10-4471', customer:'Test Co', rev:'B', fairStatus:'Draft',
  photos:[{name:'photo1.jpg', url:B+'photo1.jpg', type:'image/jpeg'}], characteristics:[]});
__put('qc/inspections/insp_t3', {id:'insp_t3', type:'self', createdAt:Date.now()-60e3, createdBy:'ops.luis@bertsmp.com', partNum:'99-0001', customer:'No Photo Co', result:'Pass', status:'Logged'});
__put('qc/drawings/drw_1', {id:'drw_1', name:'10-4471 flat.png', url:B+'drawing.png', type:'image/png', partNum:'10-4471', rev:'B', customer:'Test Co', createdAt:Date.now()-86400e3});
__put('qc/drawings/drw_2', {id:'drw_2', name:'10-4471.DXF', url:B+'x.dxf', type:'', partNum:'10-4471', createdAt:Date.now()-86400e3});
window.addEventListener('load', ()=>{
  const lg=document.getElementById('qc-login'); if(lg) lg.style.display='none';
  window.qcOnAuth({email:'ofc.edgar@bertsmp.com'}, 'manager');
  __tick();
  setTimeout(()=>showPage('inspections'), 80);
});
window.__file=async (n,tp)=>new File([await (await fetch(B+n)).blob()], n, {type:tp});
</script>'''
out = re.sub(r'<script type="module">.*?</script>', lambda m: stub, src, count=1, flags=re.S)
assert out != src
io.open(OUT + 'qc_test.html', 'w', encoding='utf-8', newline='').write(out)
print('built', OUT)
