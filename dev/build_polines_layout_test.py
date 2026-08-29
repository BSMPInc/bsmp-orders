# Slices the REAL <style> block out of orders.html and renders the purchase-line
# rows (order-card step editor + Need PO pool card) at the owner's 700px panel
# width, asserting nothing scrolls sideways. Run this, then open
# http://localhost:8123/_polinelayout.html; title says "all pass"/"FAILURES".
# Delete _polinelayout.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()

a = src.index('<style>'); b = src.index('</style>', a)
css = src[a+len('<style>'):b]

page = u'''<!doctype html><meta charset="utf-8"><title>purchase line layout</title>
<style>__CSS__</style>
<style>
  /* the app's own shell rules (body{display:flex}, zero-width html/body) would
     squeeze the harness to nothing — neutralize them, then pin the panel to the
     owner's 700px working width */
  html,body{display:block!important;width:auto!important;height:auto!important;margin:0;background:#fff;overflow:visible!important}
  .panel{width:700px!important;max-width:700px!important;flex:none!important;overflow-x:auto;border:1px solid #ccc;box-sizing:border-box}
  #out{font:12px ui-monospace,monospace;white-space:pre;padding:8px}
</style>
<div class="panel" id="panel">
  <!-- order-card step editor: one external step carrying three purchase lines -->
  <div class="sched-steps grp-ext">
    <div class="sched-step ss-on"><span class="ss-seq">1</span><span class="ss-name">Purchasing- Hardware</span></div>
  </div>
  <!-- collapsed: the roll-up chip stands in for the whole line list -->
  <div class="ss-vwrap" id="vwrap-closed">
    <div class="ss-vrow">
      <button type="button" class="slc" id="chip-late" style="color:#A32D2D;border-color:#A32D2D44;background:#A32D2D12">
        <i class="ti ti-chevron-right"></i>
        <b>4 items</b><span class="slc-sep">·</span><span>2 vendors</span>
        <span class="slc-sep">·</span><span class="slc-prog">1 of 4 on PO</span>
        <span class="slc-due late">order by 8/12</span>
      </button>
      <input class="ss-vin grow" placeholder="Process / details — e.g. Type II black">
    </div>
  </div>
  <div class="ss-vwrap" id="vwrap-green">
    <div class="ss-vrow">
      <button type="button" class="slc" id="chip-recv" style="color:#2f8f6b;border-color:#2f8f6b44;background:#2f8f6b12">
        <i class="ti ti-chevron-right"></i>
        <b>4 items</b><span class="slc-sep">·</span><span>Fastenal Industrial Supply</span>
        <span class="slc-sep">·</span><span class="slc-prog">all received</span>
      </button>
      <input class="ss-vin grow" placeholder="Process / details — e.g. Type II black">
    </div>
  </div>
  <!-- expanded: chip stays, list and Add item appear under it -->
  <div class="ss-vwrap" id="vwrap">
    <div class="ss-vrow">
      <button type="button" class="slc open" id="chip-open" style="color:#BA7517;border-color:#BA751744;background:#BA751712">
        <i class="ti ti-chevron-down"></i>
        <b>3 items</b><span class="slc-sep">·</span><span>2 vendors</span>
        <span class="slc-sep">·</span><span class="slc-prog">1 of 3 on PO</span>
        <span class="slc-due">order by 9/03</span>
      </button>
      <input class="ss-vin grow" placeholder="Process / details — e.g. Type II black">
      <button type="button" class="ss-lnadd"><i class="ti ti-plus"></i> Add item</button>
    </div>
    <div class="ss-lines">
      <div class="ss-line">
        <input class="ss-vin ss-pn" placeholder="Part #" value="FH-632-2">
        <input class="ss-vin grow" placeholder="What to buy" value="PEM flush nut 6-32 zinc">
        <input class="ss-vin ss-per" type="number" placeholder="/pc" value="4">
        <input class="ss-vin ss-qty" type="number" placeholder="Qty" value="850">
        <select class="ss-vin"><option>Fastenal Industrial Supply</option></select>
        <span class="ss-vpo">PO 5001</span>
        <span class="ss-lnmath">4/pc × 200 pcs = 800 · buying 850</span>
      </div>
      <div class="ss-line">
        <input class="ss-vin ss-pn" placeholder="Part #">
        <input class="ss-vin grow" placeholder="What to buy" value="Aluminum standoff .250 hex">
        <input class="ss-vin ss-per" type="number" placeholder="/pc" value="2">
        <input class="ss-vin ss-qty" type="number" placeholder="Qty">
        <select class="ss-vin"><option>McMaster-Carr</option></select>
        <i class="ti ti-x ss-lnrm"></i>
        <span class="ss-lnmath">2/pc × 200 pcs = 400</span>
      </div>
      <div class="ss-line">
        <input class="ss-vin ss-pn" placeholder="Part #">
        <input class="ss-vin grow" placeholder="What to buy">
        <input class="ss-vin ss-per" type="number" placeholder="/pc">
        <input class="ss-vin ss-qty" type="number" placeholder="Qty">
        <select class="ss-vin"><option>— vendor —</option></select>
        <i class="ti ti-x ss-lnrm"></i>
      </div>
    </div>
  </div>

  <!-- Need PO pool card: a vendor bucket with two line cards -->
  <div class="npv-card" id="npvcard">
    <div class="npv-head">
      <span class="npv-vendor">Fastenal Industrial Supply</span>
      <span class="npv-procbadge">Hardware</span>
      <span class="npv-count">2 items</span>
      <span class="npv-needby" style="margin-left:auto">PO needed by <b>Sep 3</b></span>
    </div>
    <div class="npv-rows">
      <div class="npv-row">
        <input type="checkbox" class="npv-pick" checked>
        <span class="npv-main">
          <span class="npv-l1">BRK-1042 <small>· Acme Aerospace · J-8891 · due Sep 20</small></span>
          <span class="npv-inrow">
            <input class="npq-in npq-pn" placeholder="Part #" value="FH-632-2">
            <input class="npq-in npq-item" placeholder="What to buy" value="PEM flush nut 6-32 zinc">
            <input class="npq-in npq-per" type="number" placeholder="/pc" value="4">
            <input class="npq-in npq-qty" type="number" placeholder="Buy qty" value="850">
            <input class="npq-in npq-detail" placeholder="Process / spec">
          </span>
          <span class="npv-math">4/pc × 200 pcs = 800 · buying 850</span>
        </span>
        <span class="npv-nums"><span class="npv-num"><small>order</small><b>200</b></span></span>
        <span class="npv-due">Sep 3 → Sep 10</span>
      </div>
      <div class="npv-row">
        <input type="checkbox" class="npv-pick" checked>
        <span class="npv-main">
          <span class="npv-l1">PLT-9 <small>· Northrop · J-8902</small></span>
          <span class="npv-inrow">
            <input class="npq-in npq-pn" placeholder="Part #">
            <input class="npq-in npq-item" placeholder="What to buy" value="Rivnut 1/4-20 steel">
            <input class="npq-in npq-per" type="number" placeholder="/pc">
            <input class="npq-in npq-qty" type="number" placeholder="Buy qty" value="60">
            <input class="npq-in npq-detail" placeholder="Process / spec">
          </span>
        </span>
        <span class="npv-nums"><span class="npv-num"><small>order</small><b>30</b></span></span>
        <span class="npv-due over">Aug 28 → Sep 4</span>
      </div>
    </div>
  </div>

  <!-- step-detail modal: the read-only line list a multi-line step shows -->
  <div class="iod-lines" id="iodlines">
    <div class="iod-line"><span class="il-d">FH-632-2 — PEM flush nut 6-32 zinc <b>×850</b></span><span class="il-v">Fastenal Industrial Supply</span><span class="il-s">PO 5001</span></div>
    <div class="iod-line"><span class="il-d">Aluminum standoff .250 hex <b>×400</b></span><span class="il-v">McMaster-Carr</span><span class="il-s">needs a PO</span></div>
  </div>
</div>
<pre id="out"></pre>
<script>
const out=[];
const ok=(n,c,e)=>out.push((c?'PASS':'FAIL')+'  '+n+(e!=null?('   ['+e+']'):''));
const R=id=>document.getElementById(id).getBoundingClientRect();
const panel=document.getElementById('panel');

ok('panel does not scroll sideways at 700px', panel.scrollWidth<=panel.clientWidth+1,
   panel.scrollWidth+' vs '+panel.clientWidth);

// every control stays inside the panel
const pr=panel.getBoundingClientRect();
let esc=[];
document.querySelectorAll('#panel input, #panel select, #panel button, #panel .ss-vpo, #panel .npv-due, #panel .il-s').forEach(el=>{
  const r=el.getBoundingClientRect();
  if(r.right>pr.right+1||r.left<pr.left-1) esc.push((el.className||el.tagName)+' @'+Math.round(r.left)+'-'+Math.round(r.right));
});
ok('no control overflows the panel', esc.length===0, esc.join(' | '));

// ── the roll-up chip ────────────────────────────────────────────────────────
{
  const chip=document.getElementById('chip-late').getBoundingClientRect();
  ok('the collapsed chip fits on one row', chip.height<=34, Math.round(chip.height));
  ok('the chip leaves room for the details box beside it',
     document.querySelector('#vwrap-closed .ss-vin.grow').getBoundingClientRect().width>=150,
     Math.round(document.querySelector('#vwrap-closed .ss-vin.grow').getBoundingClientRect().width));
  ok('a collapsed step shows no line rows', document.querySelectorAll('#vwrap-closed .ss-line').length===0);
  ok('a collapsed step offers no Add item', document.querySelectorAll('#vwrap-closed .ss-lnadd').length===0);
  ok('an expanded step keeps its chip', !!document.getElementById('chip-open'));
  ok('an expanded step shows Add item', document.querySelectorAll('#vwrap .ss-lnadd').length===1);
  // the state colour has to actually reach the text, not just the border
  const cs=getComputedStyle(document.getElementById('chip-late'));
  ok('a late chip is red', cs.color==='rgb(163, 45, 45)', cs.color);
  ok('a received chip is green', getComputedStyle(document.getElementById('chip-recv')).color==='rgb(47, 143, 107)',
     getComputedStyle(document.getElementById('chip-recv')).color);
  ok('the due date is underlined only when late',
     getComputedStyle(document.querySelector('#chip-late .slc-due')).textDecorationLine==='underline'
     && getComputedStyle(document.querySelector('#chip-open .slc-due')).textDecorationLine==='none');
  // a long vendor name must not push the chip out of the panel
  const g=document.getElementById('chip-recv').getBoundingClientRect(), pw=panel.getBoundingClientRect();
  ok('a long vendor name keeps the chip inside the panel', g.right<=pw.right+1, Math.round(g.right)+' vs '+Math.round(pw.right));
}

// the three-line step editor should stack, not squeeze onto one row
const lines=[...document.querySelectorAll('#vwrap .ss-line')].map(e=>e.getBoundingClientRect());
ok('three purchase lines render', lines.length===3, lines.length);
ok('purchase lines stack vertically', lines[1].top>=lines[0].bottom-1 && lines[2].top>=lines[1].bottom-1);
ok('a purchase line stays a sensible height', lines[0].height>=24 && lines[0].height<=140, Math.round(lines[0].height));

// the desc box must not collapse to nothing once five controls share the row
const desc=document.querySelector('#vwrap .ss-line .ss-vin.grow').getBoundingClientRect();
ok('item description box keeps usable width', desc.width>=110, Math.round(desc.width));
const pn=document.querySelector('#vwrap .ss-line .ss-pn').getBoundingClientRect();
ok('part # box keeps its width', pn.width>=70, Math.round(pn.width));

// Need PO card
const rows=[...document.querySelectorAll('#npvcard .npv-row')].map(e=>e.getBoundingClientRect());
ok('two pool rows render', rows.length===2);
ok('pool rows stack', rows[1].top>=rows[0].bottom-1);
const pdesc=document.querySelector('#npvcard .npq-item').getBoundingClientRect();
ok('pool item box keeps usable width', pdesc.width>=140, Math.round(pdesc.width));
const math=document.querySelector('#npvcard .npv-math').getBoundingClientRect();
ok('qty math sits on its own line under the inputs', math.width>60 && math.height>0, Math.round(math.width));

// modal line list
const il=[...document.querySelectorAll('#iodlines .iod-line')].map(e=>e.getBoundingClientRect());
ok('modal line list stacks', il.length===2 && il[1].top>=il[0].bottom-1);
const st=document.querySelector('#iodlines .il-s').getBoundingClientRect();
ok('modal PO/status column is right-aligned', st.right>R('iodlines').right-40, Math.round(R('iodlines').right-st.right));

const fails=out.filter(l=>l.startsWith('FAIL')).length;
document.getElementById('out').textContent=out.join('\\n')+'\\n\\n'+(out.length-fails)+'/'+out.length+' assertions passed';
document.title=fails?(fails+' FAILURES'):'all pass';
</script>'''

page = page.replace('__CSS__', css)
io.open('C:/Users/info/bsmp-orders/_polinelayout.html', 'w', encoding='utf-8').write(page)
print('wrote _polinelayout.html')
