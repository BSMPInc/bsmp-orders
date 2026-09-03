# Renders the REAL Today row + the REAL sidebar/dock Today tab with the REAL CSS, so the
# unread-notes badge can be checked for clipping and placement. Run this, then open
# http://localhost:8123/_notebadge.html - the title says "all pass" or "FAILURES".
# Delete _notebadge.html when done.
import io, re
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

css   = '\n'.join(re.findall(r'<style>(.*?)</style>', src, re.S))
notes = grab('// \u2500\u2500 Team notes:', 'window._openChat=')
row   = grab('function dispatchRow(it, idx, total){', 'function officeDispatchRow')
navit = grab('<div class="nav-item" id="nav-dispatch"', '</div>') + '</div>'
dock  = grab('<button class="dock-tab" id="dock-dispatch"', '</button>') + '</button>'
badges = grab('function updateNavBadges(){', '\nlet _dashBrief=')
# updateNavBadges touches half the app - keep only the part this page can answer for
badges = 'function updateNavBadges(){\n  const msgs=dispatchUnreadCount();\n' + badges[badges.index('  const mtxt='):]

html = u'''<!doctype html><html><head><meta charset="utf-8"><title>note badge layout</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
<style>__CSS__
body{padding:14px;background:var(--bg);display:block!important}
#out{font:12px ui-monospace,monospace;white-space:pre-wrap;background:#fff;border:1px dashed #c9d0da;padding:8px;margin-bottom:12px}
.host{max-width:980px;background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.navhost{width:230px;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:8px;margin-top:14px}
.dockhost{width:300px;background:var(--card);border:1px solid var(--border);border-radius:12px;margin-top:14px;display:flex}
</style></head><body>
<div id="out"></div>
<div class="host" id="rows"></div>
<div class="navhost">__NAVIT__</div>
<div class="dockhost">__DOCK__</div>
<script>
let userRole='manager', team=[{id:'p1',name:'Mike R.'}];
const PROCESS_COLORS={'Laser':'#2d6010','Form':'#185FA5'};
function esc2(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtDate(d){ if(!d)return''; const p=String(d).split('-'); return p[1]+'/'+p[2]+'/'+p[0].slice(2); }
function toISO(d){ return new Date(d).toISOString().slice(0,10); }
function fmtChatTime(ms){ return ms?new Date(ms).toLocaleTimeString():''; }
function shortProc(n){ return n; }
function procIcon(n,s){ return '<i class="ti ti-tool" style="font-size:'+(s||16)+'px"></i>'; }
function healthBadge(h){ return '<span class="health-badge behind">behind</span>'; }
function drawCellHtml(r){ return '<span style="color:#9aa3af">\u2014</span>'; }
function assigneeOptions(p,sel){ return '<option>-</option><option selected>Mike R.</option>'; }
function dispHoldBtn(){ return '<span></span>'; }
function holdChipHtml(h){ return ''; }
function dispSeqBadge(i){ return '<span class="disp-seq">'+(i+1)+'</span>'; }
function dispMoveCtl(){ return '<span class="disp-grip"><i class="ti ti-grip-vertical"></i></span>'; }
function isExternal(n){ return n.indexOf('Outsource-')===0 || n.indexOf('Purchasing-')===0; }
function ensureSchedule(r){ return r.schedule||{steps:[]}; }
function enabledOrdered(sch){ return (sch.steps||[]).filter(s=>s.enabled); }
function refreshActivePage(){}
function officeDispatchRow(){ return ''; }
function dispVisibleItems(){ return _DISP.map(x=>x); }
let _DISP=[];
const auth={currentUser:{uid:'uid-me',email:'ofc.edgar@bertsmp.com'}};
const db=null; function ref(){return null;} function onValue(){} function set(){return Promise.resolve();}
function remove(){return Promise.resolve();} function uid(){return 'n1';}
/*__NOTES__*/
/*__ROW__*/
/*__BADGES__*/

// fixtures: one very long part name - the worst case for a clipped badge
const T=Date.now();
const note=(id,who,at,text)=>({id:id,uid:who,by:who+'@x.com',at:at,text:text});
const mk=(id,po,part)=>({id:id,customer:'Sierra Aerospace Structures',po:po,job:'U22-'+id,part:part,due:'2026-09-11',
  schedule:{steps:[{name:'Laser',enabled:true,assignee:'p1'},{name:'Form',enabled:true}]}});
const o1=mk('a','5001','BRACKET ASSY 4130 .125 LONG PART NAME THAT RUNS ON AND ON'), o2=mk('b','5002','SHIM');
orders=[o1,o2];
const kStep=chatKeyStep(o1,'Laser');
chats={}; _chatSeen={}; _chatSeenFresh=false;
chats[kStep]={};
for(let i=0;i<3;i++) chats[kStep]['n'+i]=note('n'+i,'uid-office',T-i*1000,'message '+i);
chats[chatKeyStep(o2,'Laser')]={q:note('q','uid-me',T,'mine only')};
chats[CHAT_SHOP_KEY]={s:note('s','uid-office',T,'Shop closes at 3 today')};
const items=[{r:o1,step:o1.schedule.steps[0],health:{state:'behind',mustStart:new Date()},ext:false,hold:null},
             {r:o2,step:o2.schedule.steps[0],health:{state:'today',mustStart:new Date()},ext:false,hold:null}];
_DISP=items;
document.getElementById('rows').innerHTML=items.map((it,i)=>dispatchRow(it,i,items.length)).join('');
updateNavBadges();

const out=[]; const ok=(n,c,x)=>out.push((c?'PASS':'FAIL')+'  '+n+(x!=null?('   ['+x+']'):''));
function check(){
  if(!innerWidth) return;                        // the Browser pane runs hidden pages at width 0
  out.length=0;
  const rows=[...document.querySelectorAll('.disp-row')];
  const b1=rows[0].querySelector('.nb-new'), b2=rows[1].querySelector('.nb-new');
  ok('the unread row has a badge', !!b1);
  ok('a row with only your own notes has none', !b2);
  ok('the badge reads the unread count', b1 && b1.textContent==='3', b1&&b1.textContent);
  if(b1){
    const br=b1.getBoundingClientRect();
    const job=rows[0].querySelector('.disp-job').getBoundingClientRect();
    const btn=rows[0].querySelector('.note-btn').getBoundingClientRect();
    ok('badge is actually visible', br.width>0 && br.height>0, Math.round(br.width)+'x'+Math.round(br.height));
    ok('badge is not clipped by the job cell', br.left>=job.left-0.5 && br.right<=job.right+0.5,
       'badge '+Math.round(br.left)+'-'+Math.round(br.right)+' vs cell '+Math.round(job.left)+'-'+Math.round(job.right));
    ok('badge sits inside its button', br.top>=btn.top-0.5 && br.bottom<=btn.bottom+0.5);
    ok('the job text truncates instead of pushing the button out', btn.right <= job.right+0.5);
  }
  const nb=document.getElementById('badge-dispatch-msg');
  ok('the sidebar Today tab shows a badge', nb && nb.style.display!=='none' && nb.textContent==='4', nb&&nb.textContent);
  const nr=nb.getBoundingClientRect(), navr=document.getElementById('nav-dispatch').getBoundingClientRect();
  ok('sidebar badge is inside the nav row', nr.width>0 && nr.right<=navr.right+0.5 && nr.top>=navr.top-0.5, Math.round(nr.width)+'px');
  const dk=document.getElementById('dock-badge-dispatch');
  const dr=dk.getBoundingClientRect(), tabr=document.getElementById('dock-dispatch').getBoundingClientRect();
  ok('the dock Today tab shows a badge', dk.style.display!=='none' && dr.width>0 && dk.textContent==='4', dk.textContent);
  ok('dock badge sits over the tab', dr.left>=tabr.left-0.5 && dr.right<=tabr.right+0.5 && dr.top>=tabr.top-0.5);
  Object.keys(chats).forEach(k=>markChatRead(k));
  updateNavBadges();
  ok('reading everything hides both tab badges',
     document.getElementById('badge-dispatch-msg').style.display==='none' && document.getElementById('dock-badge-dispatch').style.display==='none');
  const fails=out.filter(l=>l.slice(0,4)==='FAIL').length;
  document.title = fails? ('FAILURES ('+fails+')') : ('all pass ('+out.length+')');
  document.getElementById('out').textContent='viewport '+innerWidth+'px\\n'+out.join('\\n');
}
check();
addEventListener('resize', ()=>{ _chatSeen={}; updateNavBadges(); check(); });
</script></body></html>'''

html = (html.replace('__CSS__', css).replace('__NAVIT__', navit).replace('__DOCK__', dock)
            .replace('/*__NOTES__*/', notes).replace('/*__ROW__*/', row).replace('/*__BADGES__*/', badges))
io.open('C:/Users/info/bsmp-orders/_notebadge.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _notebadge.html (%d chars)' % len(html))
