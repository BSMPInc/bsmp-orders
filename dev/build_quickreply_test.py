# Slices the REAL quick-reply functions out of mail.html into a standalone test page.
# Run this, then open http://localhost:8123/_quicktest.html (python http.server from
# .claude/launch.json - the Browser pane refuses file:// URLs). Page title says
# "all pass" or "FAILURES"; delete _quicktest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/mail.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block = grab(u'// \u2500\u2500 quick replies (shared', u'// \u2500\u2500 outgoing attachments')

html = u'''<!doctype html><meta charset="utf-8"><title>mail quick-reply test</title>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<!-- the bits of the real page these functions touch -->
<div class="reply open" id="reply-box"><div class="quick-row" id="quick-row"></div>
<textarea id="reply-body"></textarea></div>
<div id="quick-modal" style="display:none"><div id="qr-rows"></div></div>
<div id="compose-modal" style="display:none"><input id="cp-to">
<div class="quick-row" id="quick-row-cp"></div><textarea id="cp-body"></textarea></div>
<div id="toast"></div>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
// \u2500\u2500 stubs \u2500\u2500
function $(id){ return document.getElementById(id); }
const esc=(s)=>(s==null?'':String(s)).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
let TOASTS=[];
function toast(m,err){ TOASTS.push({m:m,err:!!err}); }
let QUICK={};
let CURRENT=null;
let SETTINGS={mailboxes:['info@bertsmp.com','sales@bertsmp.com']};
const ownAddr=(a)=>(SETTINGS.mailboxes||[]).some(mb=>mb.toLowerCase()===(a||'').toLowerCase());
function replyToRecipient(){
  const msgs=(CURRENT&&CURRENT.messages)||[];
  for(let i=msgs.length-1;i>=0;i--){ if(msgs[i]&&msgs[i].fromEmail&&!ownAddr(msgs[i].fromEmail)) return msgs[i].fromEmail; }
  return '';
}
const auth={currentUser:{uid:'uid-me', email:'ofc.edgar@bertsmp.com'}};
let CONTACTS={};
const mkey=(e)=>(e||'').toLowerCase().replace(/[.#$\\/\\[\\]]/g,'_');
let GROWN=0, TICKS=0, LASTCTX='';
function autoGrowReply(){ GROWN++; }
window._draftTick=(ctx)=>{ TICKS++; LASTCTX=ctx; };
// every write the module makes, in order
let WRITES=[];
const db=null;
function ref(_d,path){ return {path:path}; }
function set(r,val){ WRITES.push({op:'set', path:r.path, val:val}); return Promise.resolve(); }
function remove(r){ WRITES.push({op:'remove', path:r.path}); return Promise.resolve(); }
/*__BLOCK__*/

// \u2500\u2500 fixtures \u2500\u2500
const msg=(from,email)=>({from:from, fromEmail:email, body:''});
const thread=(msgs)=>({key:'t1', messages:msgs});
const ta=$('reply-body');
const rowsHtml=()=>$('quick-row').innerHTML;

// 1 \u2500 the starter set until the office saves its own
QUICK={};
ok('starters show when nothing is saved', quickList().length===7, quickList().length);
ok('every starter has a label and text', quickList().every(q=>q.label&&q.text));
ok('starters are flagged built-in', quickList().every(q=>q.builtin===true));
QUICK={ b:{id:'b',label:'Bee',text:'second',seq:1}, a:{id:'a',label:'Ay',text:'first',seq:0} };
ok('saved chips replace the starters', quickList().length===2 && !quickList()[0].builtin);
ok('saved chips come back in saved order', quickList().map(q=>q.id).join(',')==='a,b', quickList().map(q=>q.id).join(','));
QUICK={ a:null, b:{id:'b',label:'Bee',text:'second'}, c:undefined, d:{} };
let threw=null; try{ quickList(); }catch(e){ threw=e.message; }
ok('null holes in the RTDB node do not throw', threw===null && quickList().length===1, threw);

// 2 \u2500 whose name goes in {first}
QUICK={};
CURRENT=thread([msg('Jane Smith','jane@acme.com')]);
ok('display name gives the first name', qrFirstName()==='Jane', qrFirstName());
CURRENT=thread([msg('Smith, Jane','jane@acme.com')]);
ok('"Last, First" is read the right way round', qrFirstName()==='Jane', qrFirstName());
CURRENT=thread([msg('jane.smith@acme.com','jane.smith@acme.com')]);
ok('no display name falls back to the address', qrFirstName()==='Jane', qrFirstName());
CURRENT=thread([msg('ANGELA MACLEOD','a@x.com')]);
ok('a SHOUTED name is tidied', qrFirstName()==='Angela', qrFirstName());
CURRENT=thread([msg('Ian MacLeod','i@x.com')]);
ok('a name that is already mixed case is left alone', qrFirstName()==='Ian', qrFirstName());
CURRENT=thread([msg('Jane Smith','jane@acme.com'), msg('BSMP','info@bertsmp.com')]);
ok('our own last reply is skipped', qrFirstName()==='Jane', qrFirstName());
CURRENT=thread([msg('','')]);
ok('nothing to go on gives an empty name', qrFirstName()==='', qrFirstName());
CURRENT=null;
ok('no open conversation is harmless', qrFirstName()==='');
ok('{me} strips the ofc. prefix', qrMyName()==='Edgar', qrMyName());

// 3 \u2500 placeholders
CURRENT=thread([msg('Jane Smith','jane@acme.com')]);
ok('{first} fills in', qrExpand('Hi {first}, thanks.')==='Hi Jane, thanks.', qrExpand('Hi {first}, thanks.'));
ok('{me} fills in', qrExpand('\u2014 {me}')==='\u2014 Edgar', qrExpand('\u2014 {me}'));
ok('a placeholder can repeat', qrExpand('{first} {first}')==='Jane Jane');
ok('case does not matter', qrExpand('{First}')==='Jane', qrExpand('{First}'));
CURRENT=thread([msg('','')]);
ok('an unknown name leaves no stray space before the comma', qrExpand('Hi {first}, thanks.')==='Hi, thanks.', qrExpand('Hi {first}, thanks.'));
ok('plain text is untouched', qrExpand('Got it \u2014 thank you.')==='Got it \u2014 thank you.');

// 4 \u2500 inserting into the reply box
CURRENT=thread([msg('Jane Smith','jane@acme.com')]);
QUICK={ q1:{id:'q1',label:'Got it',text:'Got it \u2014 thank you.',seq:0}, q2:{id:'q2',label:'Hi',text:'Hi {first},',seq:1} };
ta.value=''; TICKS=0; GROWN=0;
qrInsert('q1');
ok('a chip writes into an empty box', ta.value==='Got it \u2014 thank you.', JSON.stringify(ta.value));
ok('inserting saves the draft', TICKS===1 && GROWN===1, TICKS+'/'+GROWN);
qrInsert('q2');
ok('a second chip lands under the first, blank line between',
   ta.value==='Got it \u2014 thank you.\\n\\nHi Jane,', JSON.stringify(ta.value));
ta.value='Dear Jane,\\n\\nRegards'; ta.focus(); ta.setSelectionRange(11,11);
qrInsert('q1');
ok('it goes in at the cursor, not the end',
   ta.value==='Dear Jane,\\nGot it \u2014 thank you.\\nRegards', JSON.stringify(ta.value));
ok('nothing already typed is lost', ta.value.indexOf('Dear Jane,')===0 && ta.value.indexOf('Regards')>-1);
ta.value='one two'; ta.focus(); ta.setSelectionRange(3,3);
qrInsert('q1');
ok('dropped mid-line it opens its own blank lines',
   ta.value==='one\\n\\nGot it \u2014 thank you.\\n\\n two', JSON.stringify(ta.value));
ta.value='replace me'; ta.focus(); ta.setSelectionRange(0,10);
qrInsert('q1');
ok('a chip replaces text you had selected', ta.value==='Got it \u2014 thank you.', JSON.stringify(ta.value));
ta.value='typed'; ta.blur();
qrInsert('q1');
ok('with the box unfocused it appends at the end', ta.value.indexOf('typed')===0 && ta.value.indexOf('Got it')>0, JSON.stringify(ta.value));
const before=ta.value; qrInsert('nope');
ok('an unknown chip does nothing', ta.value===before);
QUICK={ blank:{id:'blank',label:'Blank',text:'   ',seq:0} };
ta.value='keep'; qrInsert('blank');
ok('an empty chip cannot wipe the box', ta.value==='keep');

// 5 \u2500 the chip row
QUICK={ q1:{id:'q1',label:'Got it',text:'Hi {first}',seq:0} };
renderQuickRow();
ok('a chip is drawn for each quick reply', (rowsHtml().match(/qr-chip/g)||[]).length===2, rowsHtml());
ok('the row always offers the editor', rowsHtml().indexOf('openQuick()')>-1);
ok('the tooltip previews the filled-in text', rowsHtml().indexOf('title="Hi Jane"')>-1, rowsHtml());
QUICK={ x:{id:'x',label:'<img src=x onerror=alert(1)>',text:'"quoted" <b>',seq:0} };
renderQuickRow();
ok('a label written by a person cannot inject markup', rowsHtml().indexOf('<img')===-1 && rowsHtml().indexOf('&lt;img')>-1, rowsHtml());
ok('quotes in the text cannot break the tooltip attribute', rowsHtml().indexOf('title="&quot;quoted&quot; &lt;b&gt;"')>-1, rowsHtml());

// 6 \u2500 the editor
QUICK={ q1:{id:'q1',label:'One',text:'first line',seq:0}, q2:{id:'q2',label:'Two',text:'second line',seq:1} };
openQuick();
ok('the editor opens with the saved chips', document.querySelectorAll('#qr-rows .qr-row').length===2);
ok('the editor is showing', $('quick-modal').style.display==='flex');
document.querySelectorAll('#qr-rows .qr-label')[0].value='One edited';
qrAdd();
ok('adding a row keeps what was just typed', _qrEdit[0].label==='One edited', _qrEdit[0].label);
ok('the new row is empty and last', _qrEdit.length===3 && !_qrEdit[2].label && !_qrEdit[2].text);
document.querySelectorAll('#qr-rows .qr-label')[2].value='Three';
document.querySelectorAll('#qr-rows .qr-text')[2].value='third line';
qrMove(2,-1);
ok('moving a row keeps its text', _qrEdit[1].label==='Three' && _qrEdit[1].text==='third line', JSON.stringify(_qrEdit[1]));
ok('the row it swapped with moved down', _qrEdit[2].label==='Two');
qrMove(0,-1);
ok('the top row cannot move off the top', _qrEdit[0].label==='One edited');
qrMove(2,1);
ok('the bottom row cannot move off the bottom', _qrEdit[2].label==='Two' && _qrEdit.length===3);
qrDel(0);
ok('deleting a row drops it', _qrEdit.length===2 && _qrEdit[0].label==='Three');

// 7 \u2500 saving
WRITES=[]; TOASTS=[];
QUICK={ q1:{id:'q1',label:'One',text:'first line',seq:0}, q2:{id:'q2',label:'Two',text:'second line',seq:1} };
openQuick();                                   // rows: One, Two
document.querySelectorAll('#qr-rows .qr-text')[1].value='second line, revised';
saveQuick();
ok('an unchanged chip is not rewritten', WRITES.filter(w=>w.path.indexOf('q1')>-1).length===0, JSON.stringify(WRITES));
ok('the edited chip is written on its own', WRITES.some(w=>w.op==='set'&&w.path==='mail/quickReplies/q2'&&w.val.text==='second line, revised'), JSON.stringify(WRITES));
ok('the whole node is never set at once', WRITES.every(w=>w.path!=='mail/quickReplies'), JSON.stringify(WRITES));
ok('saving closes the editor', $('quick-modal').style.display==='none');
ok('the chips redraw after saving', rowsHtml().indexOf('Two')>-1);
WRITES=[];
QUICK={ q1:{id:'q1',label:'One',text:'first line',seq:0}, q2:{id:'q2',label:'Two',text:'second line',seq:1} };
openQuick(); qrDel(1); saveQuick();
ok('a deleted chip is removed from the database', WRITES.some(w=>w.op==='remove'&&w.path==='mail/quickReplies/q2'), JSON.stringify(WRITES));
ok('the one that stayed is left alone', !WRITES.some(w=>w.op==='set'&&w.path==='mail/quickReplies/q1'), JSON.stringify(WRITES));
WRITES=[]; TOASTS=[];
QUICK={ q1:{id:'q1',label:'One',text:'first line',seq:0} };
openQuick(); qrAdd();
document.querySelectorAll('#qr-rows .qr-label')[1].value='Label only';
saveQuick();
ok('a chip with no text is refused', WRITES.length===0 && TOASTS.length===1 && TOASTS[0].err, JSON.stringify(TOASTS));
ok('the editor stays open so it can be fixed', $('quick-modal').style.display==='flex');
document.querySelectorAll('#qr-rows .qr-text')[1].value='now it has text';
saveQuick();
ok('once fixed it saves', WRITES.some(w=>w.op==='set'&&w.val.text==='now it has text'));
WRITES=[]; QUICK={};
openQuick();                                   // pre-filled with the starters
ok('the editor adopts the starters', _qrEdit.length===7 && _qrEdit.every(r=>r.id.charAt(0)==='q'), _qrEdit.length);
saveQuick();
ok('saving the starters writes them as real chips', WRITES.filter(w=>w.op==='set').length===7, WRITES.length);
ok('they are numbered in order', WRITES.filter(w=>w.op==='set').every((w,i)=>w.val.seq===i));
ok('every saved chip carries who and when', WRITES.filter(w=>w.op==='set').every(w=>w.val.by==='ofc.edgar@bertsmp.com'&&w.val.at>0));
WRITES=[];
QUICK={};
openQuick(); _qrEdit=[{id:'z1',label:'',text:'a line with no label at all, quite a long one'}]; renderQuickEdit();
saveQuick();
ok('a chip with text but no label gets one', WRITES[0].val.label.length<=25 && WRITES[0].val.label.indexOf('a line')===0, WRITES[0].val.label);
openQuick(); closeQuick();
ok('cancelling throws the edits away', _qrEdit===null && $('quick-modal').style.display==='none');

// 8 ─ the same chips in the new-email window
const cto=$('cp-to'), cbody=$('cp-body');
CURRENT=thread([msg('Jane Smith','jane@acme.com')]);      // an open conversation must NOT leak in
CONTACTS={};
cto.value='ben.walker@acme.com';
ok('composing, {first} comes off the To box, not the open thread', qrFirstName('compose')==='Ben', qrFirstName('compose'));
cto.value='Ruth Alvarez <ruth@acme.com>';
ok('a "Name <email>" recipient is read', qrFirstName('compose')==='Ruth', qrFirstName('compose'));
cto.value='ruth@acme.com';
CONTACTS[mkey('ruth@acme.com')]={email:'ruth@acme.com', name:'Ruth Alvarez'};
ok('the address book names a bare address', qrFirstName('compose')==='Ruth', qrFirstName('compose'));
cto.value='ruth@acme.com, sam@acme.com';
ok('with several recipients the first one wins', qrFirstName('compose')==='Ruth', qrFirstName('compose'));
cto.value='';
ok('an empty To box gives no name', qrFirstName('compose')==='', qrFirstName('compose'));
ok('the reply side is unaffected', qrFirstName()==='Jane', qrFirstName());
cto.value='ben.walker@acme.com';
ok('placeholders expand against the compose context', qrExpand('Hi {first},','compose')==='Hi Ben,', qrExpand('Hi {first},','compose'));
ok('the same chip expands differently in a reply', qrExpand('Hi {first},')==='Hi Jane,', qrExpand('Hi {first},'));

QUICK={ q1:{id:'q1',label:'Hi',text:'Hi {first},',seq:0} };
renderQuickRow();
const cpHtml=$('quick-row-cp').innerHTML;
ok('the compose row gets the same chips', (cpHtml.match(/qr-chip/g)||[]).length===2, cpHtml);
ok('compose chips insert into the compose box', cpHtml.indexOf("qrInsert('q1','compose')")>-1, cpHtml);
ok('reply chips still say reply', $('quick-row').innerHTML.indexOf("qrInsert('q1','reply')")>-1);
ok('each row previews its own recipient',
   cpHtml.indexOf('title="Hi Ben,"')>-1 && $('quick-row').innerHTML.indexOf('title="Hi Jane,"')>-1, cpHtml);

ta.value='reply stays put'; cbody.value=''; TICKS=0; GROWN=0; LASTCTX='';
qrInsert('q1','compose');
ok('a compose chip writes into the compose box', cbody.value==='Hi Ben,', JSON.stringify(cbody.value));
ok('it leaves the reply box alone', ta.value==='reply stays put');
ok('it saves the compose draft, not the reply one', TICKS===1 && LASTCTX==='compose', TICKS+'/'+LASTCTX);
ok('the compose box is not auto-grown', GROWN===0, GROWN);
cbody.value='Dear Ben,'; cbody.focus(); cbody.setSelectionRange(9,9);
qrInsert('q1','compose');
ok('the cursor rules apply there too', cbody.value==='Dear Ben,\\n\\nHi Ben,', JSON.stringify(cbody.value));
ta.value=''; qrInsert('q1');
ok('no context still means the reply box', ta.value==='Hi Jane,' && LASTCTX==='reply', JSON.stringify(ta.value));
ta.value=''; qrInsert('q1','nonsense');
ok('an unknown context falls back to the reply box', ta.value==='Hi Jane,', JSON.stringify(ta.value));

const fails=out.filter(l=>l.slice(0,4)==='FAIL').length;
document.title = fails? ('FAILURES ('+fails+')') : ('all pass ('+out.length+')');
document.getElementById('out').textContent = out.join('\\n') + '\\n\\n' + (fails? (fails+' FAILURES') : 'all '+out.length+' pass');
</script>'''

html = html.replace('/*__BLOCK__*/', block)
io.open('C:/Users/info/bsmp-orders/_quicktest.html', 'w', encoding='utf-8', newline='').write(html)
print('wrote _quicktest.html (%d chars)' % len(html))
