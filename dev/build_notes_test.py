# Slices the REAL team-notes functions out of orders.html into a standalone test page.
# Run this, then open http://localhost:8123/_notestest.html (python http.server from
# .claude/launch.json - the Browser pane refuses file:// URLs). Page title says
# "all pass" or "FAILURES"; delete _notestest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/orders.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

# thread keys, unread bookkeeping and the button - everything above the DOM half
block = grab('// \u2500\u2500 Team notes:', 'window._openChat=')

html = u'''<!doctype html><meta charset="utf-8"><title>orders notes test</title>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
// \u2500\u2500 stubs \u2500\u2500
const INTERNAL_PROCESSES=['Inventory Check','Purchasing','Program','Laser','Shear/Sawing','De-Burr/Finish','Form','Machining','Weld','Hardware/Assembly','Inspection/First Article','Delivery'];
const EXTERNAL_PROCESSES=['Purchasing- Material','Purchasing- Hardware','Purchasing- Tooling','Outsource- Plating','Outsource- Paint','Outsource- Machining','Outsource- Other'];
const PROCESSES=[...INTERNAL_PROCESSES,...EXTERNAL_PROCESSES];
let orders=[];
let ME='uid-me';
const auth={currentUser:{uid:ME,email:'ofc.edgar@bertsmp.com'}};
const db=null;
function ref(){ return null; }
function onValue(){}
function set(){ return Promise.resolve(); }
function remove(){ return Promise.resolve(); }
function uid(){ return 'n'+Math.random().toString(36).slice(2,7); }
function esc2(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function refreshActivePage(){}
function shortProc(n){ return n; }
function ensureSchedule(r){ return r.schedule||{steps:[]}; }
function enabledOrdered(sch){ return (sch.steps||[]).filter(s=>s.enabled); }
let _DISP=[];                                   // what the Today board is showing
function dispVisibleItems(){ return _DISP.map(x=>x); }   // throws if _DISP is null - on purpose
/*__BLOCK__*/

// \u2500\u2500 fixtures \u2500\u2500
const T=Date.now();
const note=(id,who,at,text)=>({id:id,uid:who,by:who+'@x.com',at:at,text:text});
const order=(id,po,steps)=>({id:id,customer:'Acme Metals',po:po,job:'U22-'+id,part:'P'+id,
  schedule:{steps:(steps||['Laser','Form']).map(n=>({name:n,enabled:true}))}});
const o1=order('a','5001'), o2=order('b','5001'), o3=order('c','5002');
orders=[o1,o2,o3];

// 1 - keys are legal Firebase keys and stay distinct
const ILLEGAL=/[.#$\\/\\[\\]]/;
let allKeys=[], illegal=[];
PROCESSES.forEach(p=>{ const k=chatKeyStep(o1,p); allKeys.push(k); if(ILLEGAL.test(k)||/\\s/.test(k)) illegal.push(k); });
ok('every step key is a legal Firebase key', illegal.length===0, illegal.join(','));
ok('every step gets its own thread', new Set(allKeys).size===PROCESSES.length);
ok('slash in a process name is squashed', chatKeyStep(o1,'Shear/Sawing').indexOf('/')===-1, chatKeyStep(o1,'Shear/Sawing'));
ok('two lines on one PO do NOT share a step thread', chatKeyStep(o1,'Laser')!==chatKeyStep(o2,'Laser'));
ok('two lines on one PO DO share the job thread', chatKey(o1.customer,o1.po)===chatKey(o2.customer,o2.po));
ok('different POs get different job threads', chatKey(o1.customer,o1.po)!==chatKey(o3.customer,o3.po));
ok('the shop board has its own key', CHAT_SHOP_KEY==='__shop__' && !ILLEGAL.test(CHAT_SHOP_KEY));

// 2 - unread counting
const kStep=chatKeyStep(o1,'Laser'), kJob=chatKey(o1.customer,o1.po);
chats={};
chats[kStep]={n1:note('n1','uid-office',T-5000,'Deburr the long edges')};
_chatSeen={}; _chatSeenFresh=false;
ok('a note from someone else is unread', chatUnread(kStep)===1, chatUnread(kStep));
chats[kStep].n2=note('n2',ME,T-4000,'got it');
ok('your own note is never unread', chatUnread(kStep)===1, chatUnread(kStep));
markChatRead(kStep);
ok('reading the thread clears it', chatUnread(kStep)===0);
chats[kStep].n3=note('n3','uid-office',T,'one more thing');
ok('a newer note goes unread again', chatUnread(kStep)===1);
ok('an empty thread is never unread', chatUnread('nothing-here')===0);
ok('markChatRead on an empty thread is harmless', (markChatRead('nothing-here'),true));

// 3 - a fresh device starts quiet
chats={}; chats[kStep]={n1:note('n1','uid-office',T-90000,'old news')};
_chatSeen={}; _chatSeenFresh=true; primeChatSeen();
ok('first run marks existing notes as read', chatUnread(kStep)===0);
chats[kStep].n9=note('n9','uid-office',T,'new after priming');
ok('but anything after that is unread', chatUnread(kStep)===1);
_chatSeenFresh=true; primeChatSeen();
ok('priming only happens once', chatUnread(kStep)===0);

// 4 - the button
chats={}; _chatSeen={}; _chatSeenFresh=false;
chats[kJob]={n1:note('n1','uid-office',T,'PO revised to 60 pcs')};
const btn=chatBtnStep(o1,'Laser');
ok('an unread job note still raises the dot on a task row', btn.indexOf('note-btn')>-1 && btn.indexOf('unread')>-1);
ok('the task button opens the step thread', btn.indexOf("_openChat('"+kStep+"'")>-1);
ok('count shown is the step thread only', btn.indexOf('</i>0<')===-1 && btn.indexOf('</i><span class="nb-new">')>-1, btn);
chats[kStep]={n2:note('n2','uid-office',T,'two')};
ok('with step notes the count shows', chatBtnStep(o1,'Laser').indexOf('</i>1<')>-1, chatBtnStep(o1,'Laser'));
ok('the unread badge carries the number', chatBtnStep(o1,'Laser').indexOf('class="nb-new">2<')>-1, chatBtnStep(o1,'Laser'));
markChatRead(kStep); markChatRead(kJob);
ok('once read, no dot', chatBtnStep(o1,'Laser').indexOf('unread')===-1);
ok('once read, no badge either', chatBtnStep(o1,'Laser').indexOf('nb-new')===-1);
chats[kStep]={}; for(let i=0;i<12;i++) chats[kStep]['x'+i]=note('x'+i,'uid-office',T+i,'m'+i);
ok('a big pile of notes caps the badge at 9+', chatBtnStep(o1,'Laser').indexOf('class="nb-new">9+<')>-1, chatBtnStep(o1,'Laser'));
ok('job button is unchanged for callers passing 2 args', chatBtnHtml('Acme Metals','5001').indexOf("_openChat('"+kJob+"'")>-1);

// 5 - text that came from a person is escaped
chats={}; _chatSeen={};
const nasty='</button><img src=x onerror=alert(1)>';
ok('a label with quotes cannot break out', chatBtnAt('k', "O'Brien \\"Co\\"", 'id1').indexOf('onclick="event.stopPropagation();window._openChat(\\'k\\',\\'O\\\\\\'Brien &quot;Co&quot;\\',\\'id1\\')"')>-1,
   chatBtnAt('k', "O'Brien \\"Co\\"", 'id1'));
ok('author name strips the account prefix', chatAuthorName({by:'ops.mike@bertsmp.com'})==='Mike', chatAuthorName({by:'ops.mike@bertsmp.com'}));
ok('office prefix too', chatAuthorName({by:'ofc.edgar@bertsmp.com'})==='Edgar');
ok('a plain address keeps its name', chatAuthorName({by:'anahi@bertsmp.com'})==='Anahi');

// 6 - messy RTDB shapes (objects with holes)
chats={}; chats[kStep]={a:null,b:note('b','uid-x',T,'ok'),c:undefined};
let threw=null;
try{ chatEntries(kStep); }catch(e){ threw=e.message; }
ok('null holes in a thread do not throw', threw===null && chatEntries(kStep).length===1, threw);
chats={};
ok('a missing thread reads as empty', chatEntries('nope').length===0);

// 7 - a reply on a task thread still lights up the PO card it belongs to
chats={}; _chatSeen={}; _chatSeenFresh=false;
const grp={customer:'Acme Metals', po:'5001', items:[o1,o2]};
ok('stepThreadKeys covers every step on every line', stepThreadKeys(grp.items).length===4, stepThreadKeys(grp.items).length);
ok('a quiet PO card has no dot', chatBtnJob(grp).indexOf('unread')===-1);
chats[chatKeyStep(o2,'Form')]={n1:note('n1','uid-shop',T,'Ran short 2 pcs')};
ok('an operator reply on a step lights the PO card', chatBtnJob(grp).indexOf('unread')>-1);
ok('the PO card still opens the job thread', chatBtnJob(grp).indexOf("_openChat('"+chatKey('Acme Metals','5001')+"'")>-1);
ok('a multi-line PO card offers no step tabs', chatBtnJob(grp).indexOf("','')")>-1, chatBtnJob(grp));
ok('a single-line PO card passes its line id', chatBtnJob({customer:'Acme Metals',po:'5002',items:[o3]}).indexOf("','c')")>-1);
markChatRead(chatKeyStep(o2,'Form'));
ok('reading the step thread clears the card dot', chatBtnJob(grp).indexOf('unread')===-1);
ok('stepThreadKeys survives a missing items list', stepThreadKeys(undefined).length===0);

// 8 - the Today tab's own unread badge
chats={}; _chatSeen={}; _chatSeenFresh=false;
_DISP=[{r:o1,step:{name:'Laser'}},{r:o2,step:{name:'Form'}},{office:true,r:o3}];
ok('a quiet board counts nothing', dispatchUnreadCount()===0);
chats[CHAT_SHOP_KEY]={s1:note('s1','uid-office',T,'Shop closes at 3 today')};
ok('a shop note raises the tab count', dispatchUnreadCount()===1, dispatchUnreadCount());
chats[chatKeyStep(o1,'Laser')]={t1:note('t1','uid-office',T,'run 60 not 50')};
ok('a note on a task on the board counts', dispatchUnreadCount()===2, dispatchUnreadCount());
chats[chatKey(o3.customer,o3.po)]={j1:note('j1','uid-office',T,'still waiting on the PO')};
ok('an office row counts its job thread', dispatchUnreadCount()===3, dispatchUnreadCount());
chats[chatKey(o1.customer,o1.po)]={j2:note('j2','uid-office',T,'PO revised')};
ok('a job thread shared by two lines is counted once', dispatchUnreadCount()===4, dispatchUnreadCount());
chats[chatKeyStep(o1,'Laser')].mine=note('mine',ME,T+1,'on it');
ok('your own note never raises the tab badge', dispatchUnreadCount()===4, dispatchUnreadCount());
markChatRead(CHAT_SHOP_KEY); markChatRead(chatKeyStep(o1,'Laser'));
ok('reading threads drops the tab count', dispatchUnreadCount()===2, dispatchUnreadCount());
chats[chatKeyStep(o3,'Laser')]={z:note('z','uid-office',T,'not on the board')};
ok('a task the board is not showing does not count', dispatchUnreadCount()===2, dispatchUnreadCount());
_DISP=null;
ok('a broken board never breaks the nav', (function(){ try{ return dispatchUnreadCount()===0; }catch(e){ return 'threw: '+e.message; } })()===true);
_DISP=[];

const fails=out.filter(l=>l.slice(0,4)==='FAIL').length;
document.title = fails? ('FAILURES ('+fails+')') : ('all pass ('+out.length+')');
document.getElementById('out').textContent = out.join('\\n') + '\\n\\n' + (fails? (fails+' FAILURES') : 'all '+out.length+' pass');
</script>'''

html = html.replace('/*__BLOCK__*/', block)
io.open('C:/Users/info/bsmp-orders/_notestest.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _notestest.html (%d chars)' % len(html))
