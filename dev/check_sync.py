# The whole point of the unification is that both apps normalize prices the SAME
# way. Prove the shared core in quote.html is byte-identical to mail.html's, and
# that no stale reference to the old local index survives in the pricing path.
import io, re

mail = io.open('C:/Users/info/bsmp-orders/mail.html', encoding='utf-8').read()
quote = io.open('C:/Users/info/bsmp-orders/quote.html', encoding='utf-8').read()

def grab(src, start, end):
    a = src.index(start); b = src.index(end, a)
    return src[a:b].rstrip() + '\n'

core_mail = (grab(mail, 'const MAT_FAMILIES=[', '// AI connection')
             + grab(mail, 'function priceMatch(p,tokens){', 'function renderPrices(){'))
a = quote.index('//__SHARED_PRICE_CORE__')
b = quote.index('// ── end shared price core', a)
core_quote = quote[a:b]
core_quote = core_quote[core_quote.index('const MAT_FAMILIES=['):]

ok = True
if core_quote.strip() == core_mail.strip():
    print('PASS  shared core is byte-identical in both apps (%d lines)' % core_mail.count('\n'))
else:
    ok = False
    print('FAIL  shared core DIFFERS between mail.html and quote.html')
    ml, ql = core_mail.strip().split('\n'), core_quote.strip().split('\n')
    for i in range(max(len(ml), len(ql))):
        m = ml[i] if i < len(ml) else '<missing>'
        q = ql[i] if i < len(ql) else '<missing>'
        if m != q:
            print('   first diff at line %d:\n     mail : %s\n     quote: %s' % (i+1, m[:110], q[:110]))
            break

# nothing in the quoting path may still read the retired local list
pricing_path = quote[quote.index('//__SHARED_PRICE_CORE__'):]
stale = [m.start() for m in re.finditer(r'PRICE_INDEX', pricing_path)]
allowed = pricing_path.count("localStorage.getItem('bsmp_prices')")   # the legacy read, kept for backups
for i in stale:
    line = pricing_path[pricing_path.rfind('\n', 0, i)+1 : pricing_path.find('\n', i)].strip()
    if 'bsmp_prices' in line or 'legacy' in line.lower():
        continue
    ok = False
    print('FAIL  live PRICE_INDEX use still in the pricing path: ' + line[:110])

# and the functions quote.html calls must actually exist in it
for name in ['qBestPrice','qSheetCost','qFamilyOf','qThickOf','qSheetSize','applyIndexPrice',
             'mpList','piRowData','piSync','piTouched','mpRecord','mpExtractPrompt','priceMatch','mpTokens']:
    if not re.search(r'\bfunction\s+' + name + r'\b|\b(const|let)\s+' + name + r'\s*=', quote):
        ok = False
        print('FAIL  quote.html is missing ' + name)

# dead code should be gone
for gone in ['function getPriceFromIndex', 'function getBarPriceFromIndex', 'function clearPriceIndex', 'clearPriceIndex()']:
    if gone in quote:
        ok = False
        print('FAIL  leftover: ' + gone)

print('PASS  no stale references' if ok else 'FAILURES ABOVE')
