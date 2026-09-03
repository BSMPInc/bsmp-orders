# Slices the REAL price-break check out of quote.html into a standalone test page,
# including the rising-cost/part diagnosis. Run this, then open
# http://localhost:8123/_qbchecktest.html (python http.server from .claude/launch.json -
# the Browser pane refuses file:// URLs). Title says "all pass" or "FAILURES";
# delete _qbchecktest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/quote.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

sheets = grab('// Sheets are bought and billed in eighths', 'function saveMinSheet()')
check  = grab('// The largest quantity that still fits inside', '\nfunction copyQtyBreaks()')

html = u'''<!doctype html><meta charset="utf-8"><title>price-break check test</title>
<pre id="out" style="font:12px ui-monospace,monospace;white-space:pre-wrap"></pre>
<input id="scrap-allowance" type="number" value="0">
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+String(extra).slice(0,300)+']'):''));
// \u2500\u2500 stubs \u2500\u2500
let MIN_SHEET=0.125;
let matMode='sheet';
let BANDS=[];        // markup tiers the cliff half of the check probes
let BREAKS={};       // qty -> {jobTotal, markup}
function markupTierBands(){ return BANDS; }
function calcBreakForQty(q){ return BREAKS[q]||{jobTotal:0,markup:0}; }
/*__SHEETS__*/
/*__CHECK__*/

// \u2500\u2500 the real quote that started this: 619 parts/sheet, ~$920 a sheet \u2500\u2500
const real=[
  {qty:200, pps:619, sheetsReq:0.375, matCostPart:1.73, totalCostPart:3.74, jobTotal:1100, markup:0.45},
  {qty:250, pps:619, sheetsReq:0.5,   matCostPart:1.84, totalCostPart:3.82, jobTotal:1400, markup:0.44},
  {qty:300, pps:619, sheetsReq:0.5,   matCostPart:1.53, totalCostPart:3.49, jobTotal:1500, markup:0.43},
  {qty:600, pps:619, sheetsReq:1,     matCostPart:1.53, totalCostPart:3.44, jobTotal:2940, markup:0.42},
];
const clone=(rows)=>rows.map(r=>Object.assign({},r));

// 1 \u2500 the sheet-boundary diagnosis
let h=qbCliffCheckHtml(clone(real));
ok('the rising cost/part is caught at all', h.indexOf('Cost/part rises with quantity')>-1, h);
ok('it names the two quantities', h.indexOf('250 pcs costs $3.82/part but 200 pcs costs $3.74')>-1, h);
ok('it blames the 1/8 rounding', h.indexOf('billed in 1/8ths')>-1, h);
ok('it shows what is actually used', h.indexOf('0.5 sheets (0.404 actually used)')>-1, h);
ok('it shows the material step', h.indexOf('$1.73 \\u2192 $1.84/part')>-1, h);
ok('it suggests the quantity that reuses the smaller break\\u2019s sheet', h.indexOf('<strong>232</strong>')>-1, h);
ok('with the price it would carry', h.indexOf('232</strong> (the same 0.375 sheets the 200 break already buys \\u2014 $1.49/part)')>-1, h);
ok('it suggests filling the sheet it is already billing', h.indexOf('<strong>309</strong>')>-1, h);
ok('with that price too', h.indexOf('309</strong> (fills the 0.5 sheets you are billing at 250 \\u2014 $1.49/part)')>-1, h);
ok('it does not blame something else', h.indexOf('Material is not the cause')===-1, h);
ok('it does not claim a totals cliff', h.indexOf('a buyer pays less')===-1, h);

// 2 \u2500 fixing the quantity clears it
const fixed=[
  {qty:200, pps:619, sheetsReq:0.375, matCostPart:1.73, totalCostPart:3.74, jobTotal:1100, markup:0.45},
  {qty:232, pps:619, sheetsReq:0.375, matCostPart:1.49, totalCostPart:3.47, jobTotal:1345, markup:0.45},
  {qty:309, pps:619, sheetsReq:0.5,   matCostPart:1.49, totalCostPart:3.45, jobTotal:1700, markup:0.45},
];
h=qbCliffCheckHtml(fixed);
ok('a clean schedule goes green', h.indexOf('\\u2713')>-1 && h.indexOf('Cost/part rises')===-1, h);
ok('the all-clear mentions cost/part too', h.indexOf('Cost/part falls as quantity rises')>-1, h);

// 3 \u2500 a rise that is NOT the material says so
const setupRows=[
  {qty:200, pps:619, sheetsReq:0.375, matCostPart:1.73, totalCostPart:3.74, jobTotal:1100, markup:0.45},
  {qty:250, pps:619, sheetsReq:0.375, matCostPart:1.73, totalCostPart:3.90, jobTotal:1500, markup:0.45},
];
h=qbCliffCheckHtml(setupRows);
ok('a non-material rise is still reported', h.indexOf('Cost/part rises with quantity')>-1, h);
ok('and is not blamed on the sheets', h.indexOf('Material is not the cause')>-1 && h.indexOf('billed in 1/8ths')===-1, h);

// 4 \u2500 material rose but sheets-per-part did not (a price break, say)
const priceRows=[
  {qty:200, pps:619, sheetsReq:0.375, matCostPart:1.73, totalCostPart:3.74, jobTotal:1100, markup:0.45},
  {qty:400, pps:619, sheetsReq:0.75,  matCostPart:1.99, totalCostPart:4.10, jobTotal:2400, markup:0.45},
];
h=qbCliffCheckHtml(priceRows);
ok('same sheets-per-part is not called a rounding problem', h.indexOf('Material is not the cause')>-1, h);

// 5 \u2500 bar stock talks about bars
matMode='bar';
h=qbCliffCheckHtml([
  {qty:100, pps:20, sheetsReq:5, matCostPart:1.00, totalCostPart:3.00, jobTotal:400, markup:0.45},
  {qty:110, pps:20, sheetsReq:6, matCostPart:1.09, totalCostPart:3.09, jobTotal:460, markup:0.45},
]);
ok('bar mode says bars, not sheets', h.indexOf('bars are billed')>-1 && h.indexOf('sheets are billed')===-1, h);
ok('bar mode still suggests a quantity', h.indexOf('<strong>120</strong>')>-1, h);
matMode='sheet';

// 6 \u2500 a scrap allowance shrinks the suggestion
document.getElementById('scrap-allowance').value='5';
h=qbCliffCheckHtml(clone(real));
ok('scrap allowance is taken off the suggested quantity', h.indexOf('<strong>221</strong>')>-1, h);
ok('and off the used figure', h.indexOf('(0.424 actually used)')>-1, h);
document.getElementById('scrap-allowance').value='0';

// 7 \u2500 the markup-cliff half still works, and both can show at once
BANDS=[{max:200}];
BREAKS={200:{jobTotal:1100,markup:0.45}, 201:{jobTotal:1085.40,markup:0.44}};
h=qbCliffCheckHtml(clone(real));
ok('the markup cliff is still caught', h.indexOf('a buyer pays less by ordering more')>-1, h);
ok('both faults show together', h.indexOf('Cost/part rises with quantity')>-1 && h.indexOf('<hr')>-1, h);
ok('each fault keeps its own fix line',
   h.indexOf('cannot use \\u2014 moving the quantity')>-1 && h.indexOf("keep the % flat")>-1, h);
ok('only one heading', (h.match(/Price-break check/g)||[]).length===1, h);
BANDS=[]; BREAKS={};

// 8 \u2500 a bigger order totalling less is still caught on its own
h=qbCliffCheckHtml([
  {qty:200, pps:619, sheetsReq:0.375, matCostPart:1.73, totalCostPart:3.74, jobTotal:1100, markup:0.45},
  {qty:300, pps:619, sheetsReq:0.5,   matCostPart:1.53, totalCostPart:3.49, jobTotal:1000, markup:0.30},
]);
ok('a smaller total at a bigger qty is caught', h.indexOf('less than $1,100.00 for 200 pcs')>-1, h);

// 9 \u2500 nothing to check, and rubbish input, must not throw
let threw=null;
try{ qbCliffCheckHtml([real[0]]); }catch(e){ threw=e.message; }
ok('a single break does not throw', threw===null, threw);
try{ h=qbCliffCheckHtml([
  {qty:200, pps:0, sheetsReq:0, matCostPart:1.73, totalCostPart:3.74, jobTotal:1100, markup:0.45},
  {qty:250, pps:0, sheetsReq:0, matCostPart:1.84, totalCostPart:3.82, jobTotal:1400, markup:0.44},
]); }catch(e){ threw=e.message; }
ok('no parts-per-sheet does not throw', threw===null && h.indexOf('Cost/part rises')>-1, threw||h);
ok('and makes no suggestion it cannot stand behind', h.indexOf('instead, and the curve falls')===-1, h);

// 10 \u2500 the helper on its own
ok('maxQtyForSheets fills an eighth exactly', maxQtyForSheets(0.375,619,1)===232, maxQtyForSheets(0.375,619,1));
ok('and a half', maxQtyForSheets(0.5,619,1)===309, maxQtyForSheets(0.5,619,1));
ok('and a whole sheet', maxQtyForSheets(1,619,1)===619, maxQtyForSheets(1,619,1));
ok('what it returns really does bill that many sheets',
   billableSheets(232/619)===0.375 && billableSheets(309/619)===0.5 && billableSheets(619/619)===1);
ok('one more part tips it over the boundary', billableSheets(233/619)===0.5 && billableSheets(310/619)===0.625,
   billableSheets(233/619)+'/'+billableSheets(310/619));
ok('it refuses nonsense', maxQtyForSheets(0,619,1)===0 && maxQtyForSheets(0.5,0,1)===0 && maxQtyForSheets(0.5,619,0)===0);

const fails=out.filter(l=>l.slice(0,4)==='FAIL').length;
document.title = fails? ('FAILURES ('+fails+')') : ('all pass ('+out.length+')');
document.getElementById('out').textContent = out.join('\\n') + '\\n\\n' + (fails? (fails+' FAILURES') : 'all '+out.length+' pass');
</script>'''

html = html.replace('/*__SHEETS__*/', sheets).replace('/*__CHECK__*/', check)
io.open('C:/Users/info/bsmp-orders/_qbchecktest.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _qbchecktest.html (%d chars)' % len(html))
