import io
src = io.open('C:/Users/info/bsmp-orders/mail.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block = (grab('const MAT_FAMILIES=[', '// AI connection')
         + grab('function mpRowData(i){', 'window.savePrices'))

style = grab('<style>', '</style>') + '</style>'

html = u'''<!doctype html><meta charset="utf-8"><title>grid test</title>
''' + style + u'''
<div style="padding:10px;background:var(--bg,#fff)"><div id="mp-rows"></div></div>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const $=(id)=>document.getElementById(id);
const esc=(s)=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const out=[];
const ok=(name,cond)=>out.push((cond?'PASS':'FAIL')+'  '+name);
/*__BLOCK__*/

// a sheet line and a tube line side by side, the way a vendor email produces them
_mpItems=[
  {form:'sheet',family:'crs',desc:'CRS 16GA 48X120',thicknessIn:.0598,gauge:16,size:'48x120',price:92,uom:'sheet',raw:'CRS 16GA 48X120 $92/SHT'},
  {form:'tube',family:'hrs',shape:'square-tube',desc:'2X2X.125 SQ TUBE',odIn:2,bIn:null,wallIn:.125,gauge:null,spec:'A500',lengthFt:24,price:3.20,uom:'ft',raw:'2X2X.125 A500 SQ TUBE $3.20/FT'}
];
renderMpRows();

// each form shows its own boxes and hides the other's
ok('sheet row has thickness + size boxes', !!$('mp-thk-0') && !!$('mp-size-0'));
ok('sheet row has no tube boxes', !$('mp-shape-0') && !$('mp-wall-0') && !$('mp-spec-0') && !$('mp-len-0'));
ok('tube row has shape/od/wall/spec/length', !!$('mp-shape-1') && !!$('mp-od-1') && !!$('mp-wall-1') && !!$('mp-spec-1') && !!$('mp-len-1'));
ok('tube row has no sheet boxes', !$('mp-thk-1') && !$('mp-size-1'));
ok('square tube shows one dim box, not two', !$('mp-b-1'));
ok('tube uom list drops per-sheet/per-sqft', [...$('mp-uom-1').options].map(o=>o.value).join(',')==='lb,cwt,ft,each');
ok('sheet uom list keeps them', [...$('mp-uom-0').options].map(o=>o.value).length===6);

// the math line under each row
out.push('  sheet math: '+$('mp-math-0').textContent);
out.push('  tube  math: '+$('mp-math-1').textContent);
ok('sheet row shows $/lb only', $('mp-math-0').textContent.indexOf('/lb')>0 && $('mp-math-0').textContent.indexOf('/ft')<0);
ok('tube row leads with $/ft then $/lb', /^≈ \\$3\\.200\\/ft · ≈ \\$1\\.003\\/lb/.test($('mp-math-1').textContent));

// switching a row to rect must reveal the B box and keep what was typed
$('mp-shape-1').value='rect-tube'; mpShape(1);
ok('rect reveals the B box', !!$('mp-b-1'));
ok('shape switch keeps OD', $('mp-od-1').value==='2');
ok('shape switch keeps wall', $('mp-wall-1').value==='0.125');
ok('shape switch keeps spec', $('mp-spec-1').value==='A500');
$('mp-b-1').value='1'; mpTouched(1);
ok('rect 2x1x.125 math appears once B is filled', $('mp-math-1').textContent.indexOf('2×1 − 1.750×0.750')>0);

// sheet -> tube on the same row: sheet fields must not linger underneath
$('mp-form-0').value='tube'; mpForm(0);
ok('switched row now has tube boxes', !!$('mp-shape-0') && !!$('mp-wall-0'));
ok('switched row dropped the sheet size', !_mpItems[0].size);
ok('switched row dropped sheet thickness', _mpItems[0].thicknessIn==null);
ok('switched row picked a sensible uom (not per-sheet)', _mpItems[0].uom==='ft');
ok('switched row kept family + vendor wording', _mpItems[0].family==='crs' && _mpItems[0].desc==='CRS 16GA 48X120');
ok('switched row kept the vendor raw line', _mpItems[0].raw.indexOf('$92/SHT')>0);

// and back again
$('mp-form-0').value='sheet'; mpForm(0);
ok('back to sheet restores sheet boxes', !!$('mp-thk-0') && !$('mp-shape-0'));
ok('back to sheet clears tube fields', !_mpItems[0].shape && _mpItems[0].odIn==null && _mpItems[0].wallIn==null);
ok('back to sheet leaves per-ft behind', _mpItems[0].uom==='sheet');

// gauge -> wall decimal, using the metal's own table (stainless 14ga = .0781)
_mpItems=[{form:'tube',family:'ss304',shape:'round-tube',desc:'',odIn:1.5,wallIn:null,gauge:null,spec:'',price:8,uom:'ft',raw:''}];
renderMpRows();
$('mp-ga-0').value='14'; mpGa(0);
ok('typing 14ga on a stainless tube fills wall .0781 (not steel .0747)', $('mp-wall-0').value==='0.0781');
$('mp-ga-0').value='16'; mpGa(0);
ok('an already-filled wall is not overwritten', $('mp-wall-0').value==='0.0781');

// a new blank row starts as sheet
mpAddRow();
ok('added row defaults to sheet', $('mp-form-1').value==='sheet');

document.getElementById('out').textContent=out.join('\\n');
document.title=out.some(l=>l.indexOf('FAIL')===0)?'FAILURES':'all pass';
</script>'''
html = html.replace('/*__BLOCK__*/', block)
io.open('C:/Users/info/bsmp-orders/_gridtest.html', 'w', encoding='utf-8').write(html)
print('built')
