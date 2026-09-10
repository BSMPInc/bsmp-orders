# Slices the REAL inbox-load / search functions (loadThreads, searchAll,
# searchInput, leaveSearch, loadOlder, refreshOnReturn) out of mail.html into a
# standalone test page with a fake mail proxy, and replays the race conditions
# that made emails vanish or a refresh look dead.
# Run this, then open http://localhost:8123/_mailrefreshtest.html (python
# http.server from .claude/launch.json - the Browser pane refuses file:// URLs).
# Page title says "all pass" or "FAILURES"; delete _mailrefreshtest.html when done.
import io
src = io.open('C:/Users/info/bsmp-orders/mail.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block = grab(u'let NEXT={};       // per-mailbox Gmail page tokens', u'// \u2500\u2500 rendering \u2500')

html = u'''<!doctype html><meta charset="utf-8"><title>mail refresh test</title>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<button id="refresh-btn"><i class="ti ti-refresh"></i></button>
<input id="search">
<div id="connect-banner" style="display:none"></div>
<script>
const out=[];
const ok=(name,cond,extra)=>out.push((cond?'PASS':'FAIL')+'  '+name+(extra!=null?('   ['+extra+']'):''));
// \u2500\u2500 stubs for the bits of the real page these functions touch \u2500\u2500
function $(id){ return document.getElementById(id); }
const esc=(s)=>(s==null?'':String(s)).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
let TOASTS=[]; function toast(m,err){ TOASTS.push({m:m,err:!!err}); }
let LIVE={}; function setLive(state,txt){ LIVE={state:state,txt:txt}; }
let RENDERS=0; window.renderList=()=>{ RENDERS++; };
function renderNavCounts(){} function backfillFlagMeta(){} function maybeOpenDeep(){} function prefetchThreads(){}
let CACHE_SAVES=0; function saveInboxCache(){ CACHE_SAVES++; }
function boxTag(addr){ return (addr||'').split('@')[0].toUpperCase(); }
let SETTINGS={proxyUrl:'https://fake', mailboxes:['info@bertsmp.com','sales@bertsmp.com']};
let THREADS=[]; let _pollTimer=null;
// fake proxy: every call parks a deferred we resolve by hand, in any order
const PENDING=[];
function api(path,opts){ return new Promise((res,rej)=>PENDING.push({path:path,res:res,rej:rej})); }
const T=(k,d)=>({key:k, subject:k, date:d, mailboxes:['info@bertsmp.com'], ids:{'info@bertsmp.com':k}});
const keys=()=>THREADS.map(t=>t.key).sort().join(',');
const tick=()=>new Promise(r=>setTimeout(r,0));
</script>
<script>
''' + block + u'''
</script>
<script>
(async()=>{
  // A. a poll went out, then the user clicked Refresh; the poll's (older)
  //    answer lands LAST and must not overwrite the newer list
  THREADS=[T('t1',10)];
  loadThreads(false); loadThreads(true);
  ok('A: two loads in flight', PENDING.length===2, PENDING.length);
  ok('A: refresh button spins while loading', $('refresh-btn').disabled && $('refresh-btn').innerHTML.includes('nt-spin'));
  PENDING[1].res({threads:[T('t1',10),T('t2',20)], next:{}, failed:[]}); await tick(); await tick();
  ok('A: newer answer painted', keys()==='t1,t2', keys());
  ok('A: button back to normal', !$('refresh-btn').disabled && $('refresh-btn').innerHTML.includes('ti-refresh'));
  ok('A: "Mail refreshed" toast once', TOASTS.filter(x=>x.m==='Mail refreshed').length===1);
  PENDING[0].res({threads:[T('t1',10)], next:{}, failed:[]}); await tick(); await tick();
  ok('A: late older answer ignored', keys()==='t1,t2', keys());
  ok('A: live = Live', LIVE.state==='ok', LIVE.txt);
  PENDING.length=0; TOASTS.length=0;

  // B. search, then clear the box BEFORE the search answers
  $('search').value='foo'; searchAll();
  ok('B: search mode on', _searchQ==='foo');
  ok('B: searching bar renders', _loadingQ==='foo');
  $('search').value=''; searchInput();
  ok('B: inbox back instantly on clear', keys()==='t1,t2' && _searchQ==='', keys());
  ok('B: inbox reload requested', PENDING.length===2 && PENDING[1].path==='/threads', PENDING.map(p=>p.path).join(' '));
  PENDING[0].res({threads:[T('s1',5)], next:{}, failed:[]}); await tick(); await tick();
  ok('B: late search answer discarded', keys()==='t1,t2', keys());
  PENDING[1].res({threads:[T('t3',30)], next:{}, failed:[]}); await tick(); await tick();
  ok('B: reload merged on top (never wipes)', keys()==='t1,t2,t3', keys());
  PENDING.length=0;

  // C. a finished search, then clear - the inbox must come back even when the
  //    reload behind it fails
  NEXT={'info@bertsmp.com':'pageX'};
  $('search').value='bar'; searchAll();
  PENDING[0].res({threads:[T('s1',5),T('s2',6)], next:{'info@bertsmp.com':'srchPage'}, failed:[]}); await tick(); await tick();
  ok('C: search results shown', keys()==='s1,s2', keys());
  ok('C: search finished toast', TOASTS.some(x=>x.m==='Search finished'));
  $('search').value=''; searchInput();
  ok('C: inbox restored', keys()==='t1,t2,t3', keys());
  ok('C: Load-older tokens restored', NEXT['info@bertsmp.com']==='pageX', JSON.stringify(NEXT));
  PENDING[1].rej(new Error('Mail proxy error 502')); await tick(); await tick();
  ok('C: inbox survives a failed reload', keys()==='t1,t2,t3', keys());
  ok('C: status says offline', LIVE.state==='err' && LIVE.txt==='Mail offline', LIVE.txt);
  ok('C: button re-enabled after failure', !$('refresh-btn').disabled);
  PENDING.length=0; TOASTS.length=0; CACHE_SAVES=0;

  // D. one mailbox didn't answer - keep what we had, say which box, no cache save
  loadThreads(true);
  PENDING[0].res({threads:[T('t4',40)], next:{}, failed:['sales@bertsmp.com']}); await tick(); await tick();
  ok('D: new mail from the good box merged', keys()==='t1,t2,t3,t4', keys());
  ok('D: status names the box', LIVE.state==='err' && LIVE.txt.includes('SALES'), LIVE.txt);
  ok('D: warning toast', TOASTS.some(x=>x.err && x.m.includes('SALES')));
  ok('D: partial load not cached', CACHE_SAVES===0, CACHE_SAVES);
  PENDING.length=0; TOASTS.length=0;

  // E. typing filters after a pause, not per keystroke
  RENDERS=0; $('search').value='t'; searchInput(); $('search').value='t1'; searchInput(); $('search').value='t12'; searchInput();
  ok('E: no render yet while typing', RENDERS===0, RENDERS);
  await new Promise(r=>setTimeout(r,150));
  ok('E: one render after the pause', RENDERS===1, RENDERS);
  $('search').value='';

  // F. coming back to the tab after a while triggers a check; not while one is in flight
  _lastLoadAt=Date.now()-60000; refreshOnReturn();
  ok('F: refresh on return', PENDING.length===1, PENDING.length);
  refreshOnReturn();
  ok('F: not twice while in flight', PENDING.length===1, PENDING.length);
  PENDING[0].res({threads:[], next:{}, failed:[]}); await tick(); await tick();
  refreshOnReturn();
  ok('F: not again right after a fresh load', PENDING.length===1, PENDING.length);
  ok('F: empty answer never wipes the list', keys()==='t1,t2,t3,t4', keys());

  const fails=out.filter(l=>l.slice(0,4)==='FAIL').length;
  document.title=fails?('FAILURES: '+fails):'all pass';
  $('out').textContent=out.join('\\n')+'\\n\\n'+document.title;
})();
</script>
'''
io.open('C:/Users/info/bsmp-orders/_mailrefreshtest.html', 'w', encoding='utf-8').write(html)
print('wrote _mailrefreshtest.html')
