# -*- coding: utf-8 -*-
# Eight markup bands instead of five. The two things worth proving: the shipped
# defaults still price EXACTLY as the old five-tier ladder did, and a band that
# was left blank is skipped rather than priced at 0%.
import io
src = io.open('C:/Users/info/bsmp-orders/quote.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

# the real tier machinery, straight out of the page
block  = grab('// Eight bands: seven editable', '(function(){\n  function buildTierRows()')
block += grab('function getAsmMarkupForQty(qty){', "// Find a part's cost-per-part")
# the cliff check, so we can prove it probes every band and not just four
block += grab('function qbCliffCheckHtml(results){', 'function copyQtyBreaks(){')

html = u'''<!doctype html><meta charset="utf-8"><title>markup tier test</title>
<div id="markup-tiers-row"></div>
<div id="asm-markup-tiers-row"></div>
<input id="markup" value="30"><input id="asm-markup" value="30">
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
let partCalcs=0, asmCalcs=0;
function calcQtyBreaks(){partCalcs++;}
function calcAsmQtyBreaks(){asmCalcs++;}
// stub priced job, used only by the cliff check
let CLIFF_AT=null;
function calcBreakForQty(q){
  // job total falls off a cliff just past CLIFF_AT, so the check has something to find
  const total=(CLIFF_AT!=null && q>CLIFF_AT) ? 100 : 1000;
  return {qty:q, jobTotal:total, markup:getMarkupForQty(q)};
}
/*__BLOCK__*/
const V=(id,v)=>{document.getElementById(id).value=v;};
const G=id=>document.getElementById(id);
const mk=q=>getMarkupForQty(q);

buildMarkupTierRow('mt-', 'calcQtyBreaks', 'resetMarkupTiers');
buildMarkupTierRow('asm-mt-', 'calcAsmQtyBreaks', 'resetAsmMarkupTiers');

// -- the row the owner sees --
ok('build: seven editable threshold boxes', document.querySelectorAll('#markup-tiers-row input[id^="mt-thresh-"]').length===7);
ok('build: seven % boxes plus the above rate', document.querySelectorAll('#markup-tiers-row input[id^="mt-markup-"]').length===8);
// the old row numbered the above rate "5"; slot 5 is now a real band and the
// above rate is named, so nothing can confuse the two
ok('build: the above rate is named, not numbered', !!G('mt-markup-above') && !G('mt-markup-8') && !G('mt-thresh-above'));
ok('build: reset button kept', document.querySelectorAll('#markup-tiers-row button').length===1);
ok('build: assembly card gets its own row, same shape', document.querySelectorAll('#asm-markup-tiers-row input[id^="asm-mt-thresh-"]').length===7);
ok('build: assembly reset calls the assembly recalc', document.querySelector('#asm-markup-tiers-row button').getAttribute('onclick')==='resetAsmMarkupTiers()');
ok('build: assembly inputs recalc the assembly card', G('asm-mt-thresh-1').getAttribute('onchange')==='calcAsmQtyBreaks()');

// -- defaults must price byte-identically to the old five-tier ladder --
ok('defaults: bands 1-4 filled, 5-7 blank', [1,2,3,4].every(i=>G('mt-thresh-'+i).value!=='') && [5,6,7].every(i=>G('mt-thresh-'+i).value===''));
ok('defaults: above = 20%', G('mt-markup-above').value==='20');
const LADDER=[[1,.35],[50,.35],[51,.30],[200,.30],[201,.25],[500,.25],[501,.22],[999,.22],[1000,.20],[100000,.20]];
LADDER.forEach(function(p){ ok('ladder: qty '+p[0]+' -> '+(p[1]*100)+'%', Math.abs(mk(p[0])-p[1])<1e-9, mk(p[0])); });
ok('ladder: assembly reads its own boxes, same answer', Math.abs(getAsmMarkupForQty(300)-.25)<1e-9);

// -- a blank band is SKIPPED, not a 0% tier --
V('mt-thresh-5',2000);                     // threshold typed, % still blank
ok('blank %: band ignored, above rate still wins', Math.abs(mk(1500)-.20)<1e-9, mk(1500));
V('mt-markup-5',18);
ok('band 5 filled: 1500 pcs now takes it', Math.abs(mk(1500)-.18)<1e-9);
ok('band 5 filled: 999 pcs unaffected', Math.abs(mk(999)-.22)<1e-9);
ok('band 5 filled: past it, above rate', Math.abs(mk(2001)-.20)<1e-9);
V('mt-thresh-5','');
ok('blank threshold: a stray % does not become a band', Math.abs(mk(1500)-.20)<1e-9);
V('mt-markup-5','');

// zero is a real number -- only BLANK is skipped
V('mt-thresh-6',2000); V('mt-markup-6',0);
ok('0% is a real band, not a blank one', mk(1500)===0);
V('mt-thresh-6',''); V('mt-markup-6','');

// -- bands typed out of order still ladder correctly --
V('mt-thresh-7',2000); V('mt-markup-7',18);
V('mt-thresh-5',5000); V('mt-markup-5',15);
ok('out of order: 1500 pcs takes the 2000 band', Math.abs(mk(1500)-.18)<1e-9);
ok('out of order: 3000 pcs takes the 5000 band', Math.abs(mk(3000)-.15)<1e-9);
ok('out of order: 5001 pcs takes the above rate', Math.abs(mk(5001)-.20)<1e-9);
ok('out of order: bands come back sorted', markupTierBands('mt-').map(b=>b.max).join(',')==='50,200,500,999,2000,5000');
V('mt-thresh-7',''); V('mt-markup-7',''); V('mt-thresh-5',''); V('mt-markup-5','');

// -- junk in a threshold box --
V('mt-thresh-5',0); V('mt-markup-5',18);
ok('threshold of 0 is not a band', Math.abs(mk(1500)-.20)<1e-9);
V('mt-thresh-5',-5);
ok('negative threshold is not a band', Math.abs(mk(1500)-.20)<1e-9);
V('mt-thresh-5',''); V('mt-markup-5','');

// -- the fallbacks below the ladder --
V('mt-markup-above','');
ok('above blank: falls back to the markup field', Math.abs(mk(5000)-.30)<1e-9, mk(5000));
V('markup','');
ok('above and markup both blank: 30% floor', Math.abs(mk(5000)-.30)<1e-9);
V('markup','12');
ok('markup field honoured when the ladder runs out', Math.abs(mk(5000)-.12)<1e-9);
V('markup','30'); V('mt-markup-above',20);
ok('below the ladder the bands still win over the markup field', Math.abs(mk(100)-.30)<1e-9);

// -- the two cards do not read each other --
V('mt-markup-1',99);
ok('cards are independent: assembly unchanged by a part edit', Math.abs(getAsmMarkupForQty(10)-.35)<1e-9);
ok('cards are independent: part edit took', Math.abs(mk(10)-.99)<1e-9);

// -- reset --
partCalcs=0; resetMarkupTiers();
ok('reset: band 1 back to 50 @ 35%', G('mt-thresh-1').value==='50' && G('mt-markup-1').value==='35');
ok('reset: bands 5-7 blanked, not zeroed', [5,6,7].every(i=>G('mt-thresh-'+i).value==='' && G('mt-markup-'+i).value===''));
ok('reset: above back to 20', G('mt-markup-above').value==='20');
ok('reset: recalculates once', partCalcs===1, partCalcs);
asmCalcs=0; V('asm-mt-markup-1',99); resetAsmMarkupTiers();
ok('reset: assembly resets its own row and recalcs', G('asm-mt-markup-1').value==='35' && asmCalcs===1);

// -- the cliff check has to probe all seven bands, not the first four --
// a band above 999 is exactly what the old hard-coded list could not see
V('mt-thresh-5',2000); V('mt-markup-5',18);
CLIFF_AT=2000;
let h=qbCliffCheckHtml([{qty:1000,jobTotal:1000},{qty:3000,jobTotal:1000}]);
ok('cliff check: sees a cliff on band 5', h.indexOf('2001 pcs')>-1, h.replace(/<[^>]*>/g,' ').slice(0,120));
CLIFF_AT=null;
h=qbCliffCheckHtml([{qty:1000,jobTotal:1000},{qty:3000,jobTotal:1000}]);
ok('cliff check: clean ladder reports green', h.indexOf('\\u2713')>-1);
// out-of-range boundaries are still left alone
CLIFF_AT=50;
h=qbCliffCheckHtml([{qty:1000,jobTotal:1000},{qty:3000,jobTotal:1000}]);
ok('cliff check: boundary outside the quoted range is not probed', h.indexOf('51 pcs')===-1);
V('mt-thresh-5',''); V('mt-markup-5','');

// -- what the AI review is told --
CLIFF_AT=null;
const aiTiers=markupTierBands('mt-').map(b=>'up to '+b.max+': '+b.pct+'% markup');
ok('AI prompt: four bands listed by default, not seven', aiTiers.length===4, aiTiers.length);
V('mt-thresh-5',2000); V('mt-markup-5',18);
ok('AI prompt: a filled fifth band is listed', markupTierBands('mt-').length===5);

document.getElementById('out').textContent=out.join('\\n');
document.title=out.some(l=>l.indexOf('FAIL')===0)?('FAILURES ('+out.filter(l=>l.indexOf('FAIL')===0).length+')'):('all pass ('+out.length+')');
</script>'''
html = html.replace('/*__BLOCK__*/', block)
io.open('C:/Users/info/bsmp-orders/_mtiertest.html', 'w', encoding='utf-8').write(html)
print('built')
