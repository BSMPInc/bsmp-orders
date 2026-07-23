import io, re
src = io.open('C:/Users/info/bsmp-orders/mail.html', encoding='utf-8').read()

def grab(start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b]

block = grab('const MAT_FAMILIES=[', '// AI connection') + grab('function priceMatch(p,tokens){', 'function renderPrices(){')
tests = io.open('C:/Users/info/bsmp-orders/dev/tubetest.js', encoding='utf-8').read()
# strip the node-only header (everything up to the eval of the extracted block)
tests = tests[tests.index('const t=(name,got,want,tol)=>'):]

html = u'''<!doctype html><meta charset="utf-8"><title>tube math test</title>
<pre id="out" style="font:12px ui-monospace,monospace"></pre>
<script>
const esc=s=>String(s);
const out=[];
console.log=(...a)=>out.push(a.join(' '));
%s
%s
document.getElementById('out').textContent=out.join('\\n');
document.title=out.some(l=>l.indexOf('FAIL')===0)?'FAILURES':'all pass';
</script>''' % (block, tests)
io.open('C:/Users/info/bsmp-orders/_tubetest.html', 'w', encoding='utf-8').write(html)
print('built, block chars:', len(block))
