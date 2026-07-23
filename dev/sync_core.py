# Copy the shared material-price core out of mail.html into quote.html.
# Run again whenever mail.html's core changes: it replaces whatever sits between
# the two markers in quote.html, so it is safe to re-run.
import io, re

MAIL = 'C:/Users/info/bsmp-orders/mail.html'
QUOTE = 'C:/Users/info/bsmp-orders/quote.html'
BEGIN = '//__SHARED_PRICE_CORE__'
END = '// ── end shared price core'

mail = io.open(MAIL, encoding='utf-8').read()

def grab(start, end):
    a = mail.index(start); b = mail.index(end, a)
    return mail[a:b].rstrip() + '\n'

core = (grab('const MAT_FAMILIES=[', '// AI connection')
        + grab('function priceMatch(p,tokens){', 'function renderPrices(){'))

# these are the names quote.html leans on — fail loudly rather than ship a half copy
for name in ['MAT_FAMILIES','GAUGE_IN','UOMS','TUBE_SHAPES','matFam','parseSize','perLbCalc',
             'tubeXsec','tubeCalc','tubeLabel','tubeShape','isTube','fmtN','priceMatch',
             'mpTokens','mpExtractPrompt','mpNormalizeItems','mpParseItems','mpRecord']:
    assert re.search(r'\b(const|let|function)\s+' + name + r'\b', core), 'core is missing ' + name

quote = io.open(QUOTE, encoding='utf-8').read()
a = quote.index(BEGIN)
b = quote.index(END, a)
banner = ('// vvv GENERATED — copied from mail.html by scratchpad/sync_core.py. Do not edit here. vvv\n')
new = quote[:a] + BEGIN + '\n' + banner + core + quote[b:]
io.open(QUOTE, 'w', encoding='utf-8').write(new)
print('injected %d chars / %d lines of shared core' % (len(core), core.count('\n')))
