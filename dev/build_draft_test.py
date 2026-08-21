# Slices the REAL AI-reply-drafting block out of mail.html into a standalone test page.
# Run this, then open http://localhost:8123/_drafttest.html (python http.server from
# .claude/launch.json — the Browser pane refuses file:// URLs). Page title says
# "all pass" or "FAILURES"; delete _drafttest.html when done.
import io
SRC = 'C:/Users/info/bsmp-orders/mail.html'
OUT = 'C:/Users/info/bsmp-orders/_drafttest.html'
src = io.open(SRC, encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block = grab(u'// \u2550\u2550 AI reply drafting', u'// \u2500\u2500 compose \u2500')

# the names the page leans on — fail loudly rather than test half of it
for name in ['styleClean','styleAdd','styleHarvest','styleSamples','ordLine','draftFacts',
             'draftThreadText','draftPrompt','aiDraftCall','dMoney','dDate','dRows','dRace',
             'DRAFT_SYSTEM','STYLE_CAP']:
    assert name in block, 'block is missing ' + name

html = u'''<!doctype html><meta charset="utf-8"><title>draft test</title>
<div id="reply-ai-hint"></div><textarea id="reply-body"></textarea>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const out=[]; let fails=0;
const ok=(name,cond,extra)=>{ if(!cond) fails++; out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):'')); };
const $=(id)=>document.getElementById(id);

// -- stubs: the bits of mail.html the drafting block leans on -----------------
let DB={}, WRITES=[], REMOVES=[], AICALLS=[], AIREPLY=[];
const db={};
const ref=(_d,p)=>({p:p});
const set=(r,v)=>{ WRITES.push({p:r.p,v:v}); return Promise.resolve(); };
const remove=(r)=>{ REMOVES.push(r.p); return Promise.resolve(); };
const orderByChild=(c)=>({c:c});
const equalTo=(v)=>({v:v});
const query=(r,o,e)=>({p:r.p, child:o.c, val:e.v});
function get(r){
  if(r.child!==undefined){
    const rows=DB[r.p]||{}, hit={};
    Object.keys(rows).forEach(k=>{ const row=rows[k]; if(row&&row[r.child]===r.val) hit[k]=row; });
    return Promise.resolve({val:()=>Object.keys(hit).length?hit:null});
  }
  if(r.p==='__hang__') return new Promise(()=>{});
  const parts=r.p.split('/'); let cur=DB;
  for(const seg of parts){ cur=(cur&&cur[seg]!==undefined)?cur[seg]:null; if(cur===null) break; }
  return Promise.resolve({val:()=>cur});
}
const auth={currentUser:{email:'ofc.edgar@bertsmp.com'}};
const mkey=(e)=>(e||'').toLowerCase().replace(/[.#$\\/\\[\\]]/g,'_');
const esc=(s)=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const toast=()=>{};
const expandReply=()=>{};
const autoGrowReply=()=>{};
const hasAI=()=>true;
let MAILBOXES=['info@bertsmp.com','accounting@bertsmp.com'];
const ownAddr=(a)=>MAILBOXES.some(mb=>mb.toLowerCase()===(a||'').toLowerCase());
// same shape as the real one: everything from a "On <date> ... wrote:" line down is history
function textQuoteSplit(s){
  const i=String(s||'').search(/\\nOn .*wrote:/);
  return i<0?{main:String(s||''),quoted:''}:{main:String(s).slice(0,i),quoted:String(s).slice(i)};
}
const mailPlainText=(m)=>textQuoteSplit(m.bodyText||'').main;
const sigJunk=(m,a)=>!!a.junk;
let CONTACTS={}, FLAGS={}, NOTES={}, PRICES={}, HWP={}, CURRENT=null;
const FLAG_DEFS=[{k:'won',label:'Won'},{k:'rfq',label:'RFQ'},{k:'invoice',label:'Invoice'}];
const flagOf=(t)=>((FLAGS[t.key]||{}).flag)||'';
const assignOf=(t)=>((FLAGS[t.key]||{}).assignee)||'';
const linkOf=(t)=>((FLAGS[t.key]||{}).link)||null;
const noteEntries=(k)=>Object.values(NOTES[k]||{}).filter(Boolean).sort((a,b)=>(a.at||0)-(b.at||0));
const noteAuthorName=(e)=>String(e.by||'').split('@')[0].replace(/^ofc[._-]+/,'');
const priceRecsOf=(k)=>Object.values(PRICES).filter(p=>p&&p.mailKey===k);
const hwRecsOf=(k)=>Object.values(HWP).filter(p=>p&&p.mailKey===k);
const replyToRecipient=()=>'john@acme.com';
const replyAllRecipients=()=>['john@acme.com'];
function aiCall(payload){
  AICALLS.push(payload);
  const r=AIREPLY.shift();
  return Promise.resolve({json:()=>Promise.resolve(r)});
}
window._draftTick=()=>{};
/*__BLOCK__*/

// -- fixtures ----------------------------------------------------------------
const msg=(o)=>Object.assign({id:'m1',fromName:'John',fromEmail:'john@acme.com',to:['info@bertsmp.com'],
  date:Date.parse('2026-08-18T10:00:00Z'),bodyText:'Where are we on this?',attachments:[]},o);
const thread=(o)=>Object.assign({key:'t1',subject:'PO 88231',fromName:'John Smith',fromEmail:'john@acme.com',
  mailboxes:['info@bertsmp.com'],messages:[msg({})]},o);
const reset=()=>{ DB={}; WRITES=[]; REMOVES=[]; AICALLS=[]; AIREPLY=[];
  STYLE.mine={}; STYLE.house={}; CONTACTS={}; FLAGS={}; NOTES={}; PRICES={}; HWP={};
  localStorage.removeItem('bsmp_ai_model'); };

(async function run(){
// ── styleClean ───────────────────────────────────────────────────────────────
reset();
ok('styleClean drops quoted history',
  styleClean('Sounds good, we can hold that date.\\nOn Aug 1 John wrote:\\n> old stuff')==='Sounds good, we can hold that date.');
ok('styleClean drops the signature block',
  styleClean('Thanks,\\n\\n-- \\nEdgar\\nBSMP')==='Thanks,');
ok('styleClean drops inline-image markers',
  styleClean('See the photo [image 1] on the flange plate.').indexOf('[image')<0);
ok('styleClean collapses runaway blank lines',
  styleClean('One line.\\n\\n\\n\\nAnother line.')==='One line.\\n\\nAnother line.');

// ── styleAdd ─────────────────────────────────────────────────────────────────
reset();
styleAdd('mine','too short','a@b.com','s');
ok('styleAdd rejects a sample too short to have a voice', Object.keys(STYLE.mine).length===0);
styleAdd('mine',new Array(2000).join('x'),'a@b.com','s');
ok('styleAdd rejects a sample too long to be a reply', Object.keys(STYLE.mine).length===0);
const sample='Hi John, the brackets ship Friday. I will send tracking when they leave. Thanks,';
styleAdd('mine',sample,'John@Acme.com','PO 88231','fixed1');
ok('styleAdd stores a good sample', Object.keys(STYLE.mine).length===1);
ok('styleAdd lower-cases the recipient', (STYLE.mine.fixed1||{}).to==='john@acme.com');
ok('styleAdd writes it to this user\\'s own node',
  WRITES.length===1&&WRITES[0].p==='mail/styleSamples/mine/fixed1', WRITES.length?WRITES[0].p:'none');
styleAdd('mine',sample,'john@acme.com','PO 88231','fixed1');
ok('styleAdd ignores a sample it already has', WRITES.length===1);
reset();
for(let i=0;i<STYLE_CAP+1;i++) styleAdd('mine',sample+' #'+i,'john@acme.com','s','k'+String(i).padStart(3,'0'));
ok('styleAdd keeps the corpus capped', Object.keys(STYLE.mine).length===STYLE_CAP, Object.keys(STYLE.mine).length);
ok('styleAdd prunes the oldest sample first', REMOVES.length===1&&REMOVES[0]==='mail/styleSamples/mine/k000', REMOVES[0]);
ok('styleAdd prunes one child at a time, never the whole node',
  REMOVES.every(p=>p.split('/').length===4));

// ── styleHarvest ─────────────────────────────────────────────────────────────
reset();
const long=(n)=>'Hi John, '+n+' — the parts are running now and I will confirm the ship date tomorrow. Thanks,';
const t2=thread({messages:[
  msg({id:'a',fromEmail:'john@acme.com',bodyText:long('one')}),
  msg({id:'b',fromEmail:'info@bertsmp.com',bodyText:long('two')}),
  msg({id:'c',fromEmail:'john@acme.com',bodyText:long('three')}),
  msg({id:'d',fromEmail:'accounting@bertsmp.com',bodyText:long('four')}),
  msg({id:'e',fromEmail:'info@bertsmp.com',bodyText:long('five')})]});
styleHarvest(t2);
ok('styleHarvest only takes our own messages',
  Object.keys(STYLE.house).every(k=>k==='m_d'||k==='m_e'), Object.keys(STYLE.house).join(','));
ok('styleHarvest takes the newest two only', Object.keys(STYLE.house).length===2);
ok('styleHarvest files them in the shared house corpus',
  WRITES.every(w=>w.p.indexOf('mail/styleSamples/_house/')===0));
const before=WRITES.length;
styleHarvest(t2);
ok('styleHarvest is idempotent across re-opens', WRITES.length===before);

// ── styleSamples ─────────────────────────────────────────────────────────────
reset();
STYLE.mine={a:{t:'mine-other',to:'zed@other.com',at:10}, b:{t:'mine-same',to:'john@acme.com',at:11}};
STYLE.house={c:{t:'house-same',to:'john@acme.com',at:99}, d:{t:'house-dom',to:'sue@acme.com',at:98},
             e:{t:'house-other',to:'x@nowhere.com',at:97}, f:null};
let picked=styleSamples('john@acme.com').map(s=>s.t);
ok('styleSamples puts our own writing first', picked[0]==='mine-same', picked.join(' | '));
ok('styleSamples ranks the same recipient above the same company',
  picked.indexOf('house-same')<picked.indexOf('house-dom'), picked.join(' | '));
ok('styleSamples ranks the same company above a stranger',
  picked.indexOf('house-dom')<picked.indexOf('house-other'), picked.join(' | '));
ok('styleSamples survives the null holes RTDB hands back', picked.length===5, picked.length);
STYLE.house={}; for(let i=0;i<20;i++) STYLE.house['h'+i]={t:'h'+i,to:'',at:i};
ok('styleSamples caps what goes in the prompt', styleSamples('john@acme.com').length===8);

// ── small formatters ─────────────────────────────────────────────────────────
ok('dMoney formats cents', dMoney(48.2)==='$48.20', dMoney(48.2));
ok('dMoney stays blank on a missing number', dMoney(null)===''&&dMoney(0)===''&&dMoney('')==='');
ok('dDate reads a plain YYYY-MM-DD without sliding a day',
  dDate('2026-09-04')==='Sep 4, 2026', dDate('2026-09-04'));
ok('ordLine writes the line the way the shop says it',
  ordLine({job:'4501-1',part:'B66735',qty:25,cost:48.2,due:'2026-09-04',status:'In Process',po:'88231'})
  ==='Job 4501-1 · part B66735 · qty 25 · $48.20 ea · due Sep 4, 2026 · status In Process · PO 88231',
  ordLine({job:'4501-1',part:'B66735',qty:25,cost:48.2,due:'2026-09-04',status:'In Process',po:'88231'}));
ok('ordLine leaves out what the order does not have',
  ordLine({job:'12',status:'Received'})==='Job 12 · status Received');
ok('dRows normalizes an object-shaped list with holes',
  dRows({a:{id:1},b:null,c:{id:2}}).length===2 && dRows(null).length===0);
ok('dRace gives up on a read that never comes back', (await dRace(get({p:'__hang__'}),40))===null);

// ── draftFacts ───────────────────────────────────────────────────────────────
reset();
let facts=await draftFacts(thread({}));
ok('draftFacts says nothing when there is nothing on file', facts.text===''&&facts.used.length===0, facts.text);

reset();
CONTACTS[mkey('john@acme.com')]={name:'John Smith',company:'Acme Corp',email:'john@acme.com',phone:'562-555-1212',notes:'prefers email'};
FLAGS.t1={flag:'won',assignee:'Anahi',link:{app:'orders',id:'o1'}};
DB.orders={
  o1:{id:'o1',customer:'Acme Corp',po:'88231',job:'4501-1',part:'B66735',qty:25,cost:48.2,due:'2026-09-04',status:'In Process'},
  o2:{id:'o2',customer:'Acme Corp',po:'88231',job:'4501-2',part:'B66736',qty:10,cost:12,due:'2026-09-11',status:'Received'},
  o3:{id:'o3',customer:'Other Co',po:'88231',job:'9-1',part:'ZZ',qty:1,status:'Received'},
  o4:{id:'o4',customer:'Acme Corp',po:'77000',job:'4488',part:'610-1094',qty:10,due:'2026-08-28',status:'Ready for Invoice'},
  o5:{id:'o5',customer:'Acme Corp',po:'70000',job:'4400',part:'OLD',status:'Invoiced'},
  o6:{id:'o6',customer:'Acme Corp',po:'69000',job:'4300',part:'ARCH',status:'In Process',archived:true},
  o7:null
};
PRICES.p1={mailKey:'t1',familyLabel:'304 stainless',desc:'.060 sheet 48x120',price:410,uom:'sheet',vendor:'Metal Supply'};
HWP.h1={mailKey:'t1',desc:'1/4-20 PEM stud',price:0.42,per:'each',vendor:'Fastener Co'};
NOTES.t1={n1:{by:'ofc.edgar@bertsmp.com',at:Date.parse('2026-08-18T00:00:00Z'),text:'customer wants split shipment'}};
facts=await draftFacts(thread({}));
ok('draftFacts names the flag and who owns it', /flagged: Won · assigned to Anahi/.test(facts.text), facts.text.split('\\n')[0]);
ok('draftFacts brings in the contact card', /John Smith · Acme Corp/.test(facts.text)&&/note on file: prefers email/.test(facts.text));
ok('draftFacts brings in the linked order line', /Job 4501-1 · part B66735 · qty 25 · \\$48\\.20 ea/.test(facts.text));
ok('draftFacts pulls the other lines on the same PO', /Job 4501-2/.test(facts.text));
ok('draftFacts does not drag in another customer sharing a PO number', !/Job 9-1/.test(facts.text));
ok('draftFacts lists their other open work', /Job 4488/.test(facts.text));
ok('draftFacts leaves out invoiced and archived orders', !/Job 4400/.test(facts.text)&&!/Job 4300/.test(facts.text));
ok('draftFacts includes prices saved off this conversation', /304 stainless/.test(facts.text)&&/\\$410\\.00 per sheet/.test(facts.text));
ok('draftFacts includes hardware prices too', /1\\/4-20 PEM stud · \\$0\\.42 per each/.test(facts.text));
ok('draftFacts includes team notes and marks them internal',
  /never quote them back/.test(facts.text)&&/edgar.*split shipment/i.test(facts.text));
ok('draftFacts reports what it used', facts.used.join(' · '),
  facts.used.join(' · '));
ok('draftFacts counts the order lines it found',
  facts.used.some(u=>/^2 order lines$/.test(u))&&facts.used.some(u=>/^1 other open order$/.test(u)),
  facts.used.join(' · '));

reset();
FLAGS.t1={flag:'rfq',link:{app:'quote',id:'q9'}};
DB.quotes={q9:{id:'q9',quoteNo:'1043',partNum:'B66735',revision:'6',customer:'Acme Corp',qty:25,
  pricePerPart:48.2,jobTotal:1205,material:'11ga CRS',date:'Jul 30, 2026',status:'pending',
  qtyBreaks:[{qty:50,pricePerPart:44.1},null]}};
facts=await draftFacts(thread({}));
ok('draftFacts reads the linked quote', /quote #1043/.test(facts.text)&&/\\$48\\.20 per part/.test(facts.text)&&/job total \\$1,205\\.00/.test(facts.text), facts.text);
ok('draftFacts carries the price breaks', /price break: qty 50 at \\$44\\.10 per part/.test(facts.text));
ok('draftFacts survives a null hole in the quote breaks', facts.used.indexOf('quote #1043')>=0);

reset();
FLAGS.t1={flag:'invoice',link:{app:'apar',id:'b3'}};
DB.apar={entries:{b3:{type:'ap',party:'Metal Supply',ref:'INV-771',amount:2400,issue:'2026-08-01',
  dueDate:'2026-08-31',payments:{x:{amount:400},y:null}}}};
facts=await draftFacts(thread({}));
ok('draftFacts reads the linked bill', /bill from them on this conversation: Metal Supply · ref INV-771 · \\$2,400\\.00/.test(facts.text), facts.text);
ok('draftFacts totals what has been paid against it, holes and all', /paid so far \\$400\\.00/.test(facts.text));

// ── the prompt ───────────────────────────────────────────────────────────────
reset();
const t3=thread({messages:[
  msg({id:'a',bodyText:'Can you quote 25 of these?',attachments:[{filename:'B66735.pdf'},{filename:'logo.png',junk:true}]}),
  msg({id:'b',fromEmail:'info@bertsmp.com',fromName:'Edgar',bodyText:'Quote attached.'}),
  msg({id:'c',bodyText:'What is the lead time?'})]});
let tt=draftThreadText(t3);
ok('thread text marks our own messages as ours', /FROM: US — Edgar/.test(tt), tt.split('\\n').filter(l=>/^FROM/.test(l)).join(' | '));
ok('thread text lists real attachments', /ATTACHED: B66735\\.pdf/.test(tt));
ok('thread text leaves signature-logo images out', !/logo\\.png/.test(tt));
ok('thread text keeps the newest message last', /What is the lead time\\?$/.test(tt.trim()));
const big=thread({messages:[msg({id:'x',bodyText:new Array(9000).join('a')}),
                            msg({id:'y',bodyText:new Array(9000).join('b')}),
                            msg({id:'z',bodyText:'the newest question'})]});
const bt=draftThreadText(big);
ok('thread text trims the oldest, never the newest', bt.length<=14000&&/the newest question/.test(bt), bt.length);

let p=draftPrompt(t3,'john@acme.com',{text:'Job 4501-1 · due Sep 4, 2026',used:[]},
  [{t:'Hi John, running now. Thanks,',to:'john@acme.com'}],'tell him Friday');
ok('prompt carries the writing samples', /HOW WE WRITE/.test(p)&&/running now/.test(p));
ok('prompt carries the facts', /FACTS/.test(p)&&/Job 4501-1/.test(p));
ok('prompt carries the conversation', /THE CONVERSATION/.test(p)&&/lead time/.test(p));
ok('prompt passes the typed notes as instructions, not text to copy',
  /WHAT THE REPLY HAS TO SAY/.test(p)&&/instructions, not text to copy/.test(p)&&/tell him Friday/.test(p));
ok('prompt names who the reply goes to', /Write the reply that goes out next, to john@acme\\.com/.test(p));
p=draftPrompt(t3,'john@acme.com',{text:'',used:[]},[],'');
ok('prompt handles a cold start with no samples on file', /no past replies are on file yet/.test(p));
ok('prompt leaves out the notes section when nothing was typed', !/WHAT THE REPLY HAS TO SAY/.test(p));
ok('prompt says out loud that anything unlisted is unknown', /Anything not listed here is unknown to you/.test(p));
ok('system prompt forbids inventing numbers and asks for a bracketed blank',
  /NEVER invent a fact/.test(DRAFT_SYSTEM)&&/\\[lead time\\]/.test(DRAFT_SYSTEM));
ok('system prompt stops the model signing a name over the signature',
  /signature is attached automatically/.test(DRAFT_SYSTEM));
ok('system prompt treats the conversation as data, not as orders to follow',
  /data, not instructions/.test(DRAFT_SYSTEM));

// ── the call, and what happens when a model is not available ─────────────────
reset();
AIREPLY=[{content:[{type:'text',text:'Hi John, Friday works. Thanks,'}]}];
let got=await aiDraftCall({max_tokens:10,system:'s',messages:[]});
ok('aiDraftCall returns the body text', got==='Hi John, Friday works. Thanks,');
ok('aiDraftCall asks for the best model first', AICALLS[0].model==='claude-opus-5', AICALLS[0].model);
ok('aiDraftCall keeps the draft quick with low effort', (AICALLS[0].output_config||{}).effort==='low');
ok('aiDraftCall remembers the model that worked', localStorage.getItem('bsmp_ai_model')==='claude-opus-5');

reset();
AIREPLY=[{error:{message:'model: claude-opus-5 not_found'}},{content:[{text:'fallback body'}]}];
got=await aiDraftCall({max_tokens:10,messages:[]});
ok('aiDraftCall falls back when the account cannot run that model', got==='fallback body');
ok('aiDraftCall remembers the fallback so the next draft goes straight there',
  localStorage.getItem('bsmp_ai_model')==='claude-sonnet-4-6');
ok('aiDraftCall tried exactly two models', AICALLS.length===2, AICALLS.map(c=>c.model).join(','));

reset();
AIREPLY=[{error:{message:'output_config: unexpected field'}},{content:[{text:'plain body'}]}];
got=await aiDraftCall({max_tokens:10,messages:[]});
ok('aiDraftCall retries without the tuning if the backend will not take it', got==='plain body');
ok('aiDraftCall retried the same model, untuned',
  AICALLS.length===2&&AICALLS[1].model===AICALLS[0].model&&AICALLS[1].output_config===undefined,
  AICALLS.map(c=>c.model+(c.output_config?'+cfg':'')).join(','));

reset();
AIREPLY=[{error:{message:'overloaded_error'}},{content:[{text:'never used'}]}];
let threw='';
try{ await aiDraftCall({max_tokens:10,messages:[]}); }catch(e){ threw=e.message; }
ok('aiDraftCall stops on an error that is not about the model', threw==='overloaded_error', threw);
ok('aiDraftCall does not burn a second model on a real outage', AICALLS.length===1, AICALLS.length);

document.getElementById('out').textContent=out.join('\\n')+'\\n\\n'+(fails?(fails+' FAILURES'):'all pass')+' — '+out.length+' assertions';
document.title=fails?(fails+' FAILURES'):'all pass ('+out.length+')';
})();
</script>'''

html = html.replace('/*__BLOCK__*/', block)
io.open(OUT, 'w', encoding='utf-8').write(html)
print('wrote %s  (%d chars of real code)' % (OUT, len(block)))
