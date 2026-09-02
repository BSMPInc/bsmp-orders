# Slices the REAL on-hold + Today-board functions out of orders.html into a standalone
# test page. Run this, then open http://localhost:8123/_holdtest.html (python http.server
# from .claude/launch.json — the Browser pane refuses file:// URLs). Page title says
# "all pass" or "FAILURES"; delete _holdtest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

# the hold engine (pure helpers only — the modal/window bits need a DOM)
block  = grab("const HOLD_KEY_PO='__po__'", '// Show/hide held tasks on the Today board')
# the Today item set, grouping, visibility filter and sort
block += grab('function dispatchItems(){', "// Drag-to-reorder within a person's list")
# step ordering + team load
block += grab('function enabledOrdered(sch){', '\nfunction addDays(date, n){')
block += grab('function teamLoad(){', 'function renderTeamLoad(){')

html = u'''<!doctype html><meta charset="utf-8"><title>orders hold test</title>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
// ── stubs: the bits of orders.html the hold layer leans on ───────────────────
const INTERNAL_PROCESSES=['Inventory Check','Purchasing','Program','Laser','Shear/Sawing','De-Burr/Finish','Form','Machining','Weld','Hardware/Assembly','Inspection/First Article','Delivery'];
const EXTERNAL_PROCESSES=['Purchasing- Material','Purchasing- Hardware','Outsource- Plating'];
const PROCESSES=[...INTERNAL_PROCESSES,...EXTERNAL_PROCESSES];
const EXTERNAL_SET=new Set(EXTERNAL_PROCESSES);
function isExternal(n){ return EXTERNAL_SET.has(n); }
const HEALTH_RANK={behind:0, today:1, soon:2, ontrack:3, none:4};
const OFFICE_ASSIGNEE='Anahi';
const OFFICE_STATUSES=['Need Purchase Order','Ready for Invoice'];
let orders=[], team=[{id:'p1',name:'Mike'},{id:'p2',name:'Anahi'}];
let userRole='manager';
let _dispShowHeld=false;
function personById(id){ return team.find(p=>p.id===id)||null; }
function ensureSchedule(r){ if(!r.schedule) r.schedule={steps:[]}; return r.schedule; }
function jobHealth(r){ return r._health||{state:'ontrack',mustStart:null,slackDays:0}; }
function shortProc(n){ return n; }
function esc2(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function fmtDate(d){ if(!d)return''; const p=String(d).split('-'); return p[1]+'/'+p[2]+'/'+p[0].slice(2); }
function fmtChatTime(ms){ return ms?new Date(ms).toLocaleDateString():''; }
function chatAuthorName(e){ return (e.by||'').split('@')[0]; }
/*__BLOCK__*/

// ── fixtures ─────────────────────────────────────────────────────────────────
const iso=n=>{ const d=new Date(); d.setDate(d.getDate()+n); return d.toISOString().slice(0,10); };
const TODAY=iso(0), TOMORROW=iso(1), YESTERDAY=iso(-1);
const step=(name,o)=>Object.assign({name:name,enabled:true,done:false},o||{});
const order=(id,steps,o)=>Object.assign({id:id,customer:'Acme',job:'J'+id,status:'In Progress',schedule:{steps:steps}},o||{});
const held=(reason,until)=>({reason:reason,until:until||'',by:'ofc.edgar@bertsmp.com',at:Date.now()});
const ids=arr=>arr.map(i=>i.r.id).join(',');

// 1 — slot encoding: Firebase keys can't hold "/" "." "#" "$" "[" "]"
ok('holdSlot swaps out /', holdSlot('Shear/Sawing')==='Shear_Sawing', holdSlot('Shear/Sawing'));
ok('holdSlot leaves plain names alone', holdSlot('Laser')==='Laser');
ok('holdSlot slots are unique across every process', new Set(PROCESSES.map(holdSlot)).size===PROCESSES.length);

// 2 — a hold on the current step takes the job off the Today board
orders=[ order('a',[step('Laser')], {holds:{Laser:held('Waiting on material','')}}),
         order('b',[step('Form')]) ];
_dispShowHeld=false;
ok('held task is hidden from Today', ids(dispVisibleItems())==='b', ids(dispVisibleItems()));
_dispShowHeld=true;
ok('"show on hold" reveals it', dispVisibleItems().length===2);
ok('held item carries its record', !!dispatchAllItems().find(i=>i.r.id==='a').hold);
ok('live item has no hold', !dispatchAllItems().find(i=>i.r.id==='b').hold);
_dispShowHeld=false;

// 3 — the "until" date releases the hold on its own
orders=[ order('c',[step('Laser')], {holds:{Laser:held('Pushed out',TOMORROW)}}) ];
ok('hold with a future date still holds', dispVisibleItems().length===0);
orders=[ order('c',[step('Laser')], {holds:{Laser:held('Pushed out',TODAY)}}) ];
ok('hold ending today is over', dispVisibleItems().length===1);
orders=[ order('c',[step('Laser')], {holds:{Laser:held('Pushed out',YESTERDAY)}}) ];
ok('hold with a past date is over', dispVisibleItems().length===1);
orders=[ order('c',[step('Laser')], {holds:{Laser:held('No date','')}}) ];
ok('blank date holds indefinitely', dispVisibleItems().length===0);

// 4 — the hold follows the STEP, not the job
orders=[ order('d',[step('Laser'),step('Form')], {holds:{Form:held('Waiting on vendor','')}}) ];
ok('hold on a later step leaves Today alone', dispVisibleItems().length===1);
ok('currentStepHold ignores a later step', currentStepHold(orders[0])===null);
orders=[ order('e',[step('Laser',{done:true}),step('Form')], {holds:{Laser:held('stale','')}}) ];
ok('hold on a finished step is ignored', dispVisibleItems().length===1);
orders=[ order('f',[step('Shear/Sawing')], {holds:{'Shear_Sawing':held('saw down','')}}) ];
ok('a slash-named step holds through its slot', dispVisibleItems().length===0);

// 5 — office tasks (Get PO / Invoice) hold too
orders=[ order('g',[], {status:'Need Purchase Order', holds:{__po__:held('waiting on customer','')}}),
         order('h',[], {status:'Ready for Invoice'}) ];
ok('held office task is hidden', ids(dispVisibleItems())==='h', ids(dispVisibleItems()));
ok('office hold uses the PO slot', !!dispatchAllItems().find(i=>i.r.id==='g').hold);
orders=[ order('i',[], {status:'Ready for Invoice', holds:{__invoice__:held('customer disputes','')}}) ];
ok('held invoice task is hidden', dispVisibleItems().length===0);

// 6 — held rows sort below live work even when someone dragged them up
_dispShowHeld=true;
orders=[ order('j',[step('Laser',{assignee:'p1'})], {holds:{Laser:held('parked','')}, daySeq:1, daySeqDate:TODAY}),
         order('k',[step('Laser',{assignee:'p1'})], {daySeq:2, daySeqDate:TODAY}) ];
ok('held rows sink to the bottom of a person list', ids(dispGroupsSorted().get('p1'))==='k,j', ids(dispGroupsSorted().get('p1')));
_dispShowHeld=false;
ok('and are gone entirely when hidden', ids(dispGroupsSorted().get('p1'))==='k');

// 7 — team load ignores parked work
orders=[ order('l',[step('Laser',{assignee:'p1'})], {holds:{Laser:held('parked','')}}),
         order('m',[step('Form',{assignee:'p1'})]) ];
ok('team load counts only live tasks', teamLoad().load.get('p1').today===1, teamLoad().load.get('p1').today);

// 8 — messy Firebase shapes must not throw (RTDB hands back objects with holes)
const messy=[ order('n',[step('Laser')], {holds:null}),
              order('o',[step('Laser')], {holds:[]}),
              order('p',[step('Laser')], {holds:'nope'}),
              order('q',[step('Laser')], {holds:{Laser:'not an object'}}),
              order('r',[step('Laser')], {holds:{Laser:null}}) ];
let threw='';
try{ orders=messy; ok('messy holds shapes all read as live', dispVisibleItems().length===5, dispVisibleItems().length); }
catch(err){ threw=err.message; ok('messy holds shapes all read as live', false, threw); }

// 9 — the chip escapes whatever someone typed
const chip=holdChipHtml(held('<img src=x onerror=alert(1)>',TOMORROW));
ok('reason is HTML-escaped', chip.indexOf('<img')===-1 && chip.indexOf('&lt;img')>-1);
ok('chip shows the until date', chip.indexOf(fmtDate(TOMORROW))>-1);
ok('chip says "no end date" when open-ended', holdChipHtml(held('x','')).indexOf('no end date')>-1);
ok('no record, no chip', holdChipHtml(null)==='');

// 10 — the button reflects state and survives an apostrophe in a name
ok('idle hold button', dispHoldBtn('id1','Laser',null).indexOf('class="disp-hold-btn"')>-1);
ok('active hold button is flagged', dispHoldBtn('id1','Laser',held('x','')).indexOf('disp-hold-btn on')>-1);

const fails=out.filter(l=>l.slice(0,4)==='FAIL').length;
document.title = fails? ('FAILURES ('+fails+')') : ('all pass ('+out.length+')');
document.getElementById('out').textContent = out.join('\\n') + '\\n\\n' + (fails? (fails+' FAILURES') : 'all '+out.length+' pass');
</script>'''

html = html.replace('/*__BLOCK__*/', block)
io.open('C:/Users/info/bsmp-orders/_holdtest.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _holdtest.html (%d chars)' % len(html))
