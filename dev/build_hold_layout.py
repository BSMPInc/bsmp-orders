# Renders the REAL Today-board rows (with the new on-hold control) against fixtures so the
# grid can be eyeballed and checked for overflow at real window widths. Run this, then open
# http://localhost:8123/_holdlayout.html and resize. Delete _holdlayout.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

import re
css = '\n'.join(re.findall(r'<style>(.*?)</style>', src, re.S))   # the app has more than one style block

block  = grab("const HOLD_KEY_PO='__po__'", '\n// ══════════════ DAILY DISPATCH')
block += grab('function dispatchItems(){', "// Drag-to-reorder within a person's list")
modal = grab('<!-- Put a Today task on hold', '<script type="module">')
block += grab('// The whole-shop board:', '// \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 AI DAILY STAND-UP')
notes = grab('// \u2500\u2500 Team notes:', 'window._pp=')
chatmodal = grab('<div class="modal-bg" id="chat-modal"', '<!-- Combine multiple orders into one invoice -->')
block += grab('function enabledOrdered(sch){', '\nfunction addDays(date, n){')

html = u'''<!doctype html><html><head><meta charset="utf-8"><title>Today board \u2014 on hold layout</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>__CSS__
body{padding:14px;background:var(--bg);display:block!important}
#wlbl,#dispatch-summary,#dispatch-body{display:block;width:auto}
#wlbl{font:11px ui-monospace,monospace;color:#374151;background:#fff;border:1px dashed #c9d0da;padding:5px 8px;margin-bottom:10px}
</style></head><body>
<div id="wlbl"></div>
<div id="dispatch-shopnote"></div>
<div id="dispatch-summary"></div><div id="dispatch-body"></div>
__MODAL__
__CHATMODAL__
<script>
// stubs for the bits of orders.html the Today board leans on
const INTERNAL_PROCESSES=['Inventory Check','Purchasing','Program','Laser','Shear/Sawing','Form','Weld','Delivery'];
const EXTERNAL_PROCESSES=['Purchasing- Material','Outsource- Plating'];
const PROCESSES=[...INTERNAL_PROCESSES,...EXTERNAL_PROCESSES];
const EXTERNAL_SET=new Set(EXTERNAL_PROCESSES);
function isExternal(n){ return EXTERNAL_SET.has(n); }
const HEALTH_RANK={behind:0, today:1, soon:2, ontrack:3, none:4};
const PROCESS_COLORS={'Laser':'#2d6010','Form':'#3a6ea5','Weld':'#a8553a','Outsource- Plating':'#7a4fa3'};
const STATUS_CLASS={'Need Purchase Order':'s-need-po','Ready for Invoice':'s-ready'};
const OFFICE_ASSIGNEE='Anahi';
const OFFICE_STATUSES=['Need Purchase Order','Ready for Invoice'];
let orders=[], team=[{id:'p1',name:'Mike R.'},{id:'p2',name:'Anahi'}];
let userRole='manager', _dd=null;
function personById(id){ return team.find(p=>p.id===id)||null; }
function ensureSchedule(r){ if(!r.schedule) r.schedule={steps:[]}; return r.schedule; }
function jobHealth(r){ return r._health||{state:'ontrack',mustStart:null,slackDays:0}; }
function shortProc(n){ return n.replace(/^Outsource- /,''); }
function esc2(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtDate(d){ if(!d)return''; const p=String(d).split('-'); return p[1]+'/'+p[2]+'/'+p[0].slice(2); }
function toISO(d){ return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10); }
function fmtChatTime(ms){ return ms?new Date(ms).toLocaleDateString():''; }
function chatAuthorName(e){ return (e.by||'').split('@')[0]; }
function procIcon(n,s){ return '<i class="ti ti-tool" style="font-size:'+(s||16)+'px"></i>'; }
function drawCellHtml(r){ return '<span style="color:var(--text3);font-size:11px">-</span>'; }
function sigColor(p){ return '#3a6ea5'; }
function personInitials(n){ return (n||'?').slice(0,2).toUpperCase(); }
function assigneeOptions(step, sel){ return '<option value="">-</option>'+team.map(p=>'<option value="'+p.id+'"'+(p.id===sel?' selected':'')+'>'+p.name+'</option>').join(''); }
const HEALTH_META={behind:{color:'var(--red)',label:'behind'},today:{color:'var(--amber)',label:'start today'},soon:{color:'var(--text2)',label:'soon'},ontrack:{color:'var(--green)',label:'on track'}};
function healthBadge(h){ const m=HEALTH_META[h.state]||{color:'var(--text3)',label:h.state}; return '<span style="font-size:10.5px;font-weight:700;color:'+m.color+'">'+m.label+'</span>'; }
function renderDailyBrief(){} function renderTeamLoad(){}
function saveDB(){} function refreshActivePage(){ renderDispatch(); check(); }
const auth={currentUser:{uid:'uid-me',email:'ofc.edgar@bertsmp.com'}};
const db=null;
function ref(){ return null; } function onValue(){}
function set(){ return Promise.resolve(); } function remove(){ return Promise.resolve(); }
function uid(){ return 'n'+Math.random().toString(36).slice(2,7); }
__NOTES__
__BLOCK__

// fixtures
_dispShowHeld=true;   // harness shows held rows so both states are visible
const iso=n=>{ const d=new Date(); d.setDate(d.getDate()+n); return d.toISOString().slice(0,10); };
const step=(name,o)=>Object.assign({name:name,enabled:true,done:false},o||{});
const held=(reason,until)=>({reason:reason,until:until||'',by:'ofc.edgar@bertsmp.com',at:Date.now()});
orders=[
  {id:'1',customer:'Northrop Grumman',job:'U22-1',part:'610-1094 Rev A',due:iso(3),qty:40,status:'In Progress',
   _health:{state:'behind',mustStart:new Date(Date.now()-2*864e5),slackDays:-2},
   schedule:{steps:[step('Laser',{assignee:'p1',qtyDone:12})]}},
  {id:'2',customer:'Aerojet',job:'U41-7',part:'SPKT-2200 bracket',due:iso(9),qty:12,status:'In Progress',
   _health:{state:'today',mustStart:new Date(),slackDays:0},
   schedule:{steps:[step('Form',{assignee:'p1'})]},
   holds:{Form:held('Waiting on customer approval',iso(5))}},
  {id:'3',customer:'Curtiss-Wright Flow Control',job:'U18-3',part:'PLT-9 weldment, 0.090 5052',due:iso(14),qty:250,status:'In Progress',
   _health:{state:'soon',mustStart:new Date(Date.now()+4*864e5),slackDays:4},
   schedule:{steps:[step('Outsource- Plating',{assignee:'p1'})]},
   holds:{'Outsource- Plating':held('Waiting on vendor','')}},
  {id:'4',customer:'Moog Inc.',job:'U55-2',part:'HSG-441',due:iso(6),qty:8,status:'Need Purchase Order',
   holds:{__po__:held('Waiting on PO',iso(2))}},
  {id:'5',customer:'Parker Hannifin',job:'U60-1',part:'TUBE-77',due:iso(2),qty:60,status:'Ready for Invoice'}
];

const T=Date.now();
chats[chatKeyStep(orders[0],'Laser')]={n1:{id:'n1',uid:'uid-office',by:'ofc.anahi@bertsmp.com',at:T-60000,text:'Customer wants the long edges deburred before form.'}};
chats[chatKey(orders[2].customer,orders[2].po)]={n2:{id:'n2',uid:'uid-me',by:'ofc.edgar@bertsmp.com',at:T-30000,text:'PO revised to 250 pcs.'}};
chats[CHAT_SHOP_KEY]={n3:{id:'n3',uid:'uid-office',by:'ofc.anahi@bertsmp.com',at:T-900000,text:'No overtime Friday - shop closes at 2:30.'}};
_chatSeen={}; _chatSeenFresh=false;

function check(){
  if(!innerWidth){ document.title='waiting for a viewport'; return; }
  const rows=[...document.querySelectorAll('.disp-row')];
  const bad=[];
  rows.forEach((r,i)=>{
    const st=getComputedStyle(r);
    if(st.display!=='grid') return;                     // phone width falls back to a wrapping row
    const tracks=st.gridTemplateColumns.split(' ').length;
    if(tracks!==r.children.length) bad.push('row'+i+': '+tracks+' tracks vs '+r.children.length+' cells');
    const job=r.querySelector('.disp-job');
    const w=job?Math.round(job.getBoundingClientRect().width):999;
    if(w<110) bad.push('row'+i+' job column squeezed to '+w+'px');
  });
  document.getElementById('wlbl').textContent='viewport '+innerWidth+'px \u2014 '+(bad.length?bad.join(' | '):'grid ok across '+rows.length+' rows');
  document.title = bad.length ? ('PROBLEMS at '+innerWidth+'px') : ('ok at '+innerWidth+'px');
}
renderDispatch(); check();
if(document.fonts&&document.fonts.ready) document.fonts.ready.then(check);   // icons shift things when they land
addEventListener('load', check);
setTimeout(check,600);   // fonts.ready can fire before the glyphs actually reflow
addEventListener('resize', check);
</script></body></html>'''

html = (html.replace('__CSS__', css).replace('__BLOCK__', block).replace('__MODAL__', modal)
            .replace('__CHATMODAL__', chatmodal).replace('__NOTES__', notes))
io.open('C:/Users/info/bsmp-orders/_holdlayout.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _holdlayout.html (%d chars)' % len(html))
