import io
src = io.open('C:/Users/info/bsmp-orders/quote.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

# the shared core + the quote-side lookup layer, straight out of the real file
block = grab('const MAT_FAMILIES=[', '// ── end shared price core')
block += grab('let MPRICES = {};', 'let PRICE_INDEX =')
# the price-break loader, so its tier logic is tested too
block += grab('function loadPriceBreaksFromIndex(){', '\n// ===================== SLIDING MARKUP TIERS')

html = u'''<!doctype html><meta charset="utf-8"><title>quote price test</title>
<input id="material" value=""><select id="sheetsize"><option value="48x120">48x120</option><option value="48x144">48x144</option><option value="custom">custom</option></select>
<input id="custom-sheet-w" value="48"><input id="custom-sheet-l" value="120">
<input id="costsheet" value="0"><div id="costsheet-src"></div>
<div id="matbreaks-rows"></div><input type="checkbox" id="matbreaks-enabled"><div id="matbreaks-section"></div>
<div id="matbreaks-label"></div><div id="matbreaks-dot"></div><div id="matbreaks-active-price"></div>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
const near=(a,b,tol)=>a!=null&&Math.abs(a-b)<=tol;
// stubs for the bits of the page the pricing layer touches
let calcCalls=0; function calculate(){calcCalls++;}
const alerts=[]; window.alert=(m)=>alerts.push(m);
let matBreakRowCount=0; const breakRows=[];
function addMatBreakRow(min,price){ matBreakRowCount++; breakRows.push({min:min,price:price}); }
function toggleMatBreaks(){ document.getElementById('matbreaks-enabled').checked=true; }
/*__BLOCK__*/

// ── a price book like the real one: same metal, quoted four different ways ──
const REC = (o) => Object.assign({id:'x'+Math.random(), form:'sheet', at:Date.parse('2026-07-01')}, o);
MPRICES = {
  // 16ga CRS = .0598. 48x120 sheet weighs 48*120*.0598*.2836 = 97.68 lb
  a: REC({id:'a', family:'crs', familyLabel:'CRS (cold rolled)', desc:'CRS 16GA 48X120', thicknessIn:.0598, gauge:16,
          size:'48x120', price:92, uom:'sheet', pricePerLb:0.9418, vendor:'Sheet Co', emailDate:Date.parse('2026-07-01')}),
  // same material from another vendor, quoted per lb — must convert
  b: REC({id:'b', family:'crs', familyLabel:'CRS (cold rolled)', desc:'CR 1008 .060', thicknessIn:.0598, gauge:null,
          size:'', price:0.85, uom:'lb', pricePerLb:0.85, vendor:'Pound Co', emailDate:Date.parse('2026-07-02')}),
  // 304 16ga = .0625 (NOT .0598) — the per-metal table matters
  c: REC({id:'c', family:'ss304', familyLabel:'304 Stainless', desc:'T304 2B 16GA 48X120', thicknessIn:.0625, gauge:16,
          size:'48x120', price:310, uom:'sheet', pricePerLb:1.7787, vendor:'Stainless Co', emailDate:Date.parse('2026-07-03')}),
  // a tube must never price a sheet
  d: REC({id:'d', form:'tube', family:'hrs', familyLabel:'HRS (hot rolled)', shape:'square-tube', desc:'2X2X.125 A500',
          odIn:2, wallIn:.125, spec:'A500', price:3.20, uom:'ft', pricePerFt:3.2, pricePerLb:1.003, vendor:'Tube Co'}),
};

// ── reading the quote form's material string ──
ok('family: "0.0598 thk CRS" -> crs', qFamilyOf('0.0598 thk CRS')==='crs');
ok('family: "0.0625 thk 304 SS" -> ss304', qFamilyOf('0.0625 thk 304 SS')==='ss304');
ok('family: "0.125 thk Alu-5052" -> al5052', qFamilyOf('0.125 thk 5052')==='al5052');
ok('family: bare "stainless" -> 304 (shop default)', qFamilyOf('.060 thk stainless')==='ss304');
ok('family: nonsense -> null', qFamilyOf('unobtainium')===null);
ok('thickness: decimal read straight', near(qThickOf('0.0598 thk CRS','crs'),.0598,.0001));
ok('thickness: "16ga CRS" uses the STEEL table', near(qThickOf('16ga CRS','crs'),.0598,.0001));
ok('thickness: "16ga 304" uses the STAINLESS table', near(qThickOf('16ga 304','ss304'),.0625,.0001));

// ── the money question: what does one sheet cost ──
let hit = qBestPrice('0.0598 thk CRS');
ok('CRS 16ga finds a price', !!hit, hit && hit.p.id);
ok('CRS 16ga prefers the exact-size sheet quote over the per-lb one', hit && hit.p.id==='a', hit && hit.p.id);
ok('CRS 16ga 48x120 = $92 as quoted', hit && near(hit.c.v,92,.01), hit && hit.c.v);
out.push('   math: '+(hit?hit.c.math:''));

// per-lb quote converted onto a real sheet: 97.68 lb x $0.85 = $83.03
delete MPRICES.a;
hit = qBestPrice('0.0598 thk CRS');
ok('per-lb quote converts to a per-sheet cost', hit && near(hit.c.v,83.03,.05), hit && hit.c.v.toFixed(2));
out.push('   math: '+(hit?hit.c.math:''));

// a bigger sheet costs proportionally more off the same per-lb price
document.getElementById('sheetsize').value='48x144';
hit = qBestPrice('0.0598 thk CRS');
ok('48x144 off the same $/lb = 1.2x the 48x120 cost', hit && near(hit.c.v,83.03*1.2,.06), hit && hit.c.v.toFixed(2));
document.getElementById('sheetsize').value='48x120';

// the bug this fixes: a per-lb price must NOT land in the box as-is
ok('per-lb price never lands raw in the cost-per-sheet box', hit && hit.c.v > 50, hit && hit.c.v.toFixed(2));

// ── things that must NOT match ──
ok('304 does not price CRS', qBestPrice('0.0598 thk CRS').p.family==='crs');
ok('16ga 304 finds the stainless sheet, not the steel one', qBestPrice('16ga 304 SS').p.id==='c');
ok('a thickness nobody quoted finds nothing', qBestPrice('0.250 thk CRS')===null);
ok('a metal nobody quoted finds nothing', qBestPrice('0.0598 thk brass')===null);
ok('tube never prices a sheet', qBestPrice('0.125 thk HRS')===null);
ok('material with no thickness finds nothing', qBestPrice('CRS')===null);

// ── the cost box + its provenance line ──
document.getElementById('material').value='16ga 304 SS';
const v = applyIndexPrice('16ga 304 SS');
ok('applyIndexPrice fills the box', document.getElementById('costsheet').value==='310.00', document.getElementById('costsheet').value);
ok('applyIndexPrice says which vendor it came from', document.getElementById('costsheet-src').innerHTML.indexOf('Stainless Co')>0);
ok('applyIndexPrice shows the arithmetic', document.getElementById('costsheet-src').innerHTML.indexOf('quoted')>0);
const v2 = applyIndexPrice('0.250 thk CRS');
ok('no match -> returns null and hides the note', v2===null && document.getElementById('costsheet-src').style.display==='none');

// ── quantity breaks off the shared book ──
MPRICES.e = REC({id:'e', family:'crs', familyLabel:'CRS', desc:'CRS 16GA 48X120 10+', thicknessIn:.0598, gauge:16,
                 size:'48x120', price:88, uom:'sheet', qty:10, vendor:'Sheet Co'});
MPRICES.f = REC({id:'f', family:'crs', familyLabel:'CRS', desc:'CRS 16GA 48X120 1-9', thicknessIn:.0598, gauge:16,
                 size:'48x120', price:92, uom:'sheet', qty:1, vendor:'Sheet Co'});
MPRICES.g = REC({id:'g', family:'crs', familyLabel:'CRS', desc:'CRS 16GA same break, dearer', thicknessIn:.0598, gauge:16,
                 size:'48x120', price:95, uom:'sheet', qty:10, vendor:'Pricey Co'});
window._qPricesReady = true;
document.getElementById('material').value='0.0598 thk CRS';
breakRows.length=0; matBreakRowCount=0;
loadPriceBreaksFromIndex();
// four matching records collapse to two tiers: qty 1 (the $92 break and the
// per-lb line both land there, cheaper wins) and qty 10 ($88 beats $95)
ok('breaks: one tier per break quantity, not per record', breakRows.length===2, JSON.stringify(breakRows));
ok('breaks: tiers come out lowest-first', breakRows[0].min===1 && breakRows[1].min===10);
ok('breaks: cheaper vendor wins a tied break qty', breakRows[1].price==='88.00', breakRows[1].price);
ok('breaks: cheapest qty-1 wins — the converted per-lb line beats the $92 sheet', breakRows[0].price==='83.03', breakRows[0].price);

alerts.length=0; breakRows.length=0;
document.getElementById('material').value='0.250 thk brass';
loadPriceBreaksFromIndex();
ok('breaks: nothing matching -> tells you, adds no tiers', breakRows.length===0 && alerts.length===1, alerts[0]);

document.getElementById('out').textContent=out.join('\\n');
document.title=out.some(l=>l.indexOf('FAIL')===0)?'FAILURES':'all pass';
</script>'''
html = html.replace('/*__BLOCK__*/', block)
io.open('C:/Users/info/bsmp-orders/_quotetest.html', 'w', encoding='utf-8').write(html)
print('built')
