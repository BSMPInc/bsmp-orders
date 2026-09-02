# Renders the REAL schedule-step row markup (internal + external, held and not) with the
# real CSS, so the new on-hold control can be checked against the step grid. Run this, then
# open http://localhost:8123/_holdsteprow.html. Delete _holdsteprow.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

css = grab('<style>', '</style>').replace('<style>', '')
block = grab("const HOLD_KEY_PO='__po__'", '// Show/hide held tasks on the Today board')
# the row builder itself, lifted out of detailInner
rowsrc = grab('    const pJs=p.replace', '  };\n  const rowsOf =')

html = u'''<!doctype html><html><head><meta charset="utf-8"><title>schedule step row \u2014 on hold</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>__CSS__
body{padding:14px;background:var(--bg);display:block!important}
#wlbl{font:11px ui-monospace,monospace;color:#374151;background:#fff;border:1px dashed #c9d0da;padding:5px 8px;margin-bottom:10px}
.host{max-width:820px}
</style></head><body>
<div id="wlbl"></div>
<div class="host">
  <div class="sched-grp-label ext">Outsourced steps \u2014 vendor coordination</div>
  <div class="sched-steps grp-ext" id="ext"></div>
  <div class="sched-grp-label">Internal steps</div>
  <div class="sched-steps grp-int" id="int"></div>
</div>
<script>
let userRole='manager', team=[{id:'p1',name:'Mike R.'}];
const PROCESS_COLORS={'Laser':'#2d6010','Outsource- Plating':'#7a4fa3'};
function esc2(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtDate(d){ if(!d)return''; const p=String(d).split('-'); return p[1]+'/'+p[2]+'/'+p[0].slice(2); }
function fmtChatTime(ms){ return ms?new Date(ms).toLocaleDateString():''; }
function chatAuthorName(e){ return (e.by||'').split('@')[0]; }
function shortProc(n){ return n; }
function _todayStr(){ return new Date().toISOString().slice(0,10); }
function procIcon(n,s){ return '<i class="ti ti-tool" style="font-size:'+(s||16)+'px"></i>'; }
function assigneeOptions(p,sel){ return '<option>-</option><option selected>Mike R.</option>'; }
function defDur(p){ return 3; }
function isExternal(n){ return n.indexOf('Outsource-')===0 || n.indexOf('Purchasing-')===0; }
function extKind(p){ return {group: p.indexOf('Outsource-')===0?'outsource':'buy'}; }
function slIsOpen(){ return false; }
function stepLines(){ return []; }
function lineQtyMath(){ return {}; }
function stepLineRoll(){ return null; }
function toISO(d){ return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10); }
const LINE_ROLL_COLOR={open:'#888',received:'#2d6010'};
const cd=null;
function ensureSchedule(r){ return r.schedule; }
function enabledOrdered(){ return []; }
__BLOCK__

function renderRow(r, step, idx, ord){
  const p=step.name, ext=isExternal(p), done=!!step.done;
  const qtyNeeded=r.qty||0;
  const anchorIcon='';
  const dateLabel = done ? 'done 09/01/26' : '<span style="color:var(--text2)">start by 09/05/26</span>';
__ROWSRC__
}
const held=(reason,until)=>({reason:reason,until:until||'',by:'ofc.edgar@bertsmp.com',at:Date.now()});
const order=(holds)=>({id:'o1',qty:40,holds:holds||{}});
const st=(name,o)=>Object.assign({name:name,enabled:true,done:false,duration:3},o||{});

const rInt=order({Laser:held('Waiting on customer approval','2026-09-07')});
const rExt=order({'Outsource- Plating':held('Waiting on vendor','')});
document.getElementById('int').innerHTML =
  renderRow(order({}), st('Laser',{qtyDone:12}), 0, [1,2]) +
  renderRow(rInt, st('Laser',{qtyDone:12}), 1, [1,2]);
document.getElementById('ext').innerHTML =
  renderRow(order({}), st('Outsource- Plating'), 0, [1,2]) +
  renderRow(rExt, st('Outsource- Plating'), 1, [1,2]);

const bad=[];
[...document.querySelectorAll('.sched-step')].forEach((row,i)=>{
  const tracks=getComputedStyle(row).gridTemplateColumns.split(' ').length;
  if(tracks!==row.children.length) bad.push('row'+i+': '+tracks+' tracks vs '+row.children.length+' cells');
  const btn=row.querySelector('.ss-hold');
  if(btn){
    const b=btn.getBoundingClientRect(), rr=row.getBoundingClientRect();
    if(b.width<8||b.height<8) bad.push('row'+i+': hold button collapsed');
    if(b.right>rr.right+1||b.left<rr.left-1) bad.push('row'+i+': hold button clipped by the row');
  }
});
document.getElementById('wlbl').textContent = bad.length? bad.join(' | ') : 'step rows ok \u2014 hold control visible and inside every row';
document.title = bad.length? 'PROBLEMS' : 'step rows ok';
</script></body></html>'''

html = html.replace('__CSS__', css).replace('__BLOCK__', block).replace('__ROWSRC__', rowsrc)
io.open('C:/Users/info/bsmp-orders/_holdsteprow.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _holdsteprow.html (%d chars)' % len(html))
