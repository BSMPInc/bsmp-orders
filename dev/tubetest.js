// pull the real price-book functions out of mail.html and exercise them
const fs=require('fs');
const src=fs.readFileSync('C:/Users/info/bsmp-orders/mail.html','utf8');
const grab=(startMark,endMark)=>{
  const a=src.indexOf(startMark); const b=src.indexOf(endMark,a);
  if(a<0||b<0) throw new Error('cannot find '+startMark);
  return src.slice(a,b);
};
const block=grab('const MAT_FAMILIES=[','// AI connection')
  +grab('function priceMatch(p,tokens){','function renderPrices(){');
const esc=s=>String(s);
eval(block);

const t=(name,got,want,tol)=>{
  const ok=Math.abs(got-want)<=tol;
  console.log((ok?'PASS':'FAIL')+'  '+name+'  got '+(Math.round(got*1000)/1000)+' want ~'+want);
};

// 2x2x.125 A500 square tube, HRS. Mill table says 3.05 lb/ft (design wall .116);
// square-corner nominal math should land a few % high, not wildly off.
let sq={form:'tube',family:'hrs',shape:'square-tube',odIn:2,bIn:null,wallIn:.125,price:3.20,uom:'ft'};
let c=tubeCalc(sq);
t('square 2x2x.125 lb/ft', c.lbPerFt, 3.19, .02);
t('square 2x2x.125 $/ft (quoted per ft)', c.perFt, 3.20, .001);
t('square 2x2x.125 $/lb derived', c.perLb, 3.20/3.19, .01);
console.log('   math: '+c.math+'\n');

// round 1.5 OD x .120 wall
let rd={form:'tube',family:'hrs',shape:'round-tube',odIn:1.5,wallIn:.120,price:1.80,uom:'lb'};
c=tubeCalc(rd);
t('round 1.5od x .120 lb/ft', c.lbPerFt, 1.771, .02);  // π/4(1.5²-1.26²)=0.5203 in² ×12×.2836
t('round quoted per lb -> $/ft', c.perFt, 1.80*1.771, .05);
t('round quoted per lb -> $/lb', c.perLb, 1.80, .001);
console.log('   math: '+c.math+'\n');

// rect 2x1x.120, priced per 24 ft stick
let rc={form:'tube',family:'hrs',shape:'rect-tube',odIn:2,bIn:1,wallIn:.120,price:48,uom:'each',lengthFt:24};
c=tubeCalc(rc);
// 2-.24=1.76, 1-.24=.76 -> 2 - 1.3376 = .6624 in² -> x12x.2836 = 2.254 lb/ft
t('rect 2x1x.120 lb/ft', c.lbPerFt, 2.254, .02);
t('rect per-stick -> $/ft', c.perFt, 2.0, .001);
t('rect per-stick -> $/lb', c.perLb, 2.0/2.254, .01);
console.log('   math: '+c.math+'\n');

// cwt on aluminum round bar
let ab={form:'tube',family:'al6061',shape:'round-bar',odIn:1,price:325,uom:'cwt'};
c=tubeCalc(ab);
t('al 1in round bar lb/ft', c.lbPerFt, .919, .01);   // π/4 ×1 =.7854 ×12×.0975
t('cwt -> $/lb', c.perLb, 3.25, .001);
t('cwt -> $/ft', c.perFt, 3.25*.919, .02);
console.log('   math: '+c.math+'\n');

// sheet still works (no regression)
let sh={form:'sheet',family:'crs',thicknessIn:.0598,size:'48x120',price:92,uom:'sheet'};
const s=perLbCalc(sh);
t('sheet 16ga CRS 48x120 $/lb', s.v, 92/(48*120*.0598*.2836), .001);
console.log('   math: '+s.math+'\n');

// Guards. A half-described tube must never invent a weight — but a price the
// vendor actually quoted per foot still stands on its own, so $/ft survives and
// only the weight-derived numbers go null.
const g=(name,rec)=>{
  const r=tubeCalc(rec);
  const bad=r&&((r.lbPerFt!=null&&!(r.lbPerFt>0))||(r.perFt!=null&&!(r.perFt>0))||(r.perLb!=null&&!(r.perLb>0)));
  console.log((bad?'FAIL':'PASS')+'  guard '+name+' -> '+JSON.stringify(r&&{perFt:r.perFt,perLb:r.perLb,lbPerFt:r.lbPerFt}));
};
g('no wall on a tube (keeps quoted $/ft, no weight)', {form:'tube',family:'hrs',shape:'square-tube',odIn:2,price:3,uom:'ft'});
g('rect missing B', {form:'tube',family:'hrs',shape:'rect-tube',odIn:2,wallIn:.12,price:3,uom:'ft'});
g('wall >= half the size (no negative metal)', {form:'tube',family:'hrs',shape:'square-tube',odIn:2,wallIn:1,price:3,uom:'ft'});
g('per-stick with no length (nothing to divide by)', {form:'tube',family:'hrs',shape:'square-tube',odIn:2,wallIn:.125,price:60,uom:'each'});
g('sqft on a tube (meaningless)', {form:'tube',family:'hrs',shape:'square-tube',odIn:2,wallIn:.125,price:3,uom:'sqft'});
g('family with no density', {form:'tube',family:'other',shape:'square-tube',odIn:2,wallIn:.125,price:3.2,uom:'ft'});
g('no price at all', {form:'tube',family:'hrs',shape:'square-tube',odIn:2,wallIn:.125,uom:'ft'});
console.log('');

// ── search ────────────────────────────────────────────────────────────────
const tok=(q)=>q.toLowerCase()
  .replace(/(\d)\s+(ga(uge)?)\b/g,'$1ga')
  .replace(/(\d)\s*"?\s+(od|wall)\b/g,'$1$2')
  .replace(/\b(od|wall)\s+(\.?\d)/g,'$1$2')
  .split(/[\s,]+/).filter(Boolean);
const recSq=Object.assign({},sq,{spec:'A500',desc:'2X2X.125 SQ TUBE A500',raw:'2X2X.125 SQ TUBE A500 $3.20/FT',vendor:'Metals Co'});
const recRd=Object.assign({},rd,{spec:'DOM',desc:'1.5 OD X .120 WALL DOM',raw:'',vendor:'Metals Co'});
const recRc=Object.assign({},rc,{spec:'A513',gauge:11,desc:'2X1 RECT 11GA',raw:'',vendor:'Metals Co'});
const recSh=Object.assign({},sh,{desc:'CRS 16GA 48X120',raw:'',vendor:'Steel Supply'});
const RECS={'sq tube':recSq,'rd tube':recRd,'rc tube':recRc,'sheet':recSh};
const m=(label,q,want)=>{
  const got=priceMatch(RECS[label],tok(q));
  console.log((got===want?'PASS':'FAIL')+'  "'+q+'" vs '+label+' -> '+got+(want?'':' (should not match)'));
};
m('sq tube','2x2x.125',true);
m('sq tube','2x2',true);
m('sq tube','a500 tube',true);
m('sq tube','2x2x.125 a500',true);
m('sq tube','.125 wall',true);
m('sq tube','wall .125',true);
m('sq tube','2x2x11ga',false);          // wrong wall gauge
m('sq tube','3x3x.125',false);
m('rd tube','1.5 od',true);
m('rd tube','od 1.5',true);
m('rd tube','1.5od .120wall',true);
m('rd tube','dom round',true);
m('rd tube','2 od',false);
m('rc tube','2x1x11ga',true);           // gauge form of the wall
m('rc tube','1x2x11ga',true);           // said backwards
m('rc tube','2x1',true);
m('rc tube','2x1x14ga',false);
m('rc tube','a513',true);
m('sheet','16ga',true);                 // gauge<->decimal still works
m('sheet','.0598',true);
m('sheet','48x120',true);
m('sheet','crs 16ga 48x120',true);
m('sheet','2x2x.125',false);            // a tube search must not drag in sheet
m('sheet','a500',false);
m('sq tube','48x120',false);
