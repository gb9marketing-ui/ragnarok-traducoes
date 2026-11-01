import sys, re
# remove blocos de script vazios ("Script: |" sem conteudo) que o rapidyaml interpreta errado
src = open(sys.argv[1], encoding='utf8').read().split('\n')
out = []; i = 0; removed = 0
while i < len(src):
    l = src[i]
    m = re.match(r'^(\s+)(Script|EquipScript|UnEquipScript): \|$', l)
    if m:
        ind = len(m.group(1)); j = i + 1
        body = []
        while j < len(src) and (src[j].strip() == '' or len(src[j]) - len(src[j].lstrip()) > ind):
            body.append(src[j]); j += 1
        if not any(b.strip() for b in body):
            removed += 1; i = j; continue
    out.append(l); i += 1
open(sys.argv[2], 'w', encoding='utf8').write('\n'.join(out))
print('blocos vazios removidos:', removed)
