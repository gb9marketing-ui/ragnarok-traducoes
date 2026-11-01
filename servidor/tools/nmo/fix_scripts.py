#!/usr/bin/env python3
"""Ajustes de texto nos scripts do Naruto Maniacs para o rAthena (arquivos em cp1252, mantidos assim).
Uso: python3 -I fix_scripts.py <rathena>
"""
import os, re, sys, collections
RA = sys.argv[1]
EQI = {'EQI_HEAD_TOP': 1, 'EQI_ARMOR': 2, 'EQI_HAND_L': 3, 'EQI_HAND_R': 4, 'EQI_GARMENT': 5,
       'EQI_SHOES': 6, 'EQI_ACC_L': 7, 'EQI_ACC_R': 8, 'EQI_HEAD_MID': 9, 'EQI_HEAD_LOW': 10}
stats = collections.Counter()

def fix(text, is_yaml=False):
    # slots de equipamento: valores antigos (o rAthena foi ajustado para essa numeracao)
    def eqi(m):
        stats['EQI'] += 1
        return str(EQI[m.group(0)])
    text = re.sub(r'\bEQI_(HEAD_TOP|ARMOR|HAND_L|HAND_R|GARMENT|SHOES|ACC_L|ACC_R|HEAD_MID|HEAD_LOW)\b', eqi, text)
    # GetCastleData <mapa>,0,<evento>;  ->  GetCastleData <mapa>,0; donpcevent <evento>;
    def gcd(m):
        stats['GetCastleData'] += 1
        return f'{m.group(1)}GetCastleData {m.group(2)},0; donpcevent {m.group(3)};'
    text = re.sub(r'(?i)()GetCastleData\s+([^,;\n]+?)\s*,\s*0\s*,\s*([^;\n]+?)\s*;', gcd, text)
    text = re.sub(r'guildopenstorage\(\s*0\s*\)', 'guildopenstorage()', text)
    if is_yaml:
        # restos de chaves quebradas vindas do item_db original
        n0 = len(text)
        text = re.sub(r'(?m)^(\s+)\},\{\s*$', r'\1', text)
        if len(text) != n0: stats['chaves'] += 1
        # chaves fechando a mais no fim de uma linha de script
        def bal(m):
            line = m.group(0); extra = line.count('}') - line.count('{')
            while extra > 0 and line.rstrip().endswith('}'):
                line = line.rstrip()[:-1]; extra -= 1; stats['chave extra'] += 1
            return line
        text = re.sub(r'(?m)^      [^\n]*\}[ \t]*$', bal, text)
    return text

files = []
for root, _, fs in os.walk(os.path.join(RA, 'npc', os.environ.get('KIT', 'nmo'))):
    files += [os.path.join(root, f) for f in fs if f.endswith('.txt')]
files.append(os.path.join(RA, 'db', os.environ.get('KIT', 'nmo'), 'item_db.yml'))
for p in files:
    raw = open(p, 'rb').read().decode('cp1252', errors='surrogateescape')
    new = fix(raw, p.endswith('.yml'))
    if new != raw:
        open(p, 'wb').write(new.encode('cp1252', errors='surrogateescape'))
        stats['arquivos'] += 1
print(dict(stats))

# NNGO: racas "chefe"/"nao chefe" do eAthena (RC_Boss=10, RC_NonBoss=11) viraram classes no rAthena
BOSS = {'RC_Boss': 'Class_Boss', '10': 'Class_Boss', 'RC_NonBoss': 'Class_Normal', '11': 'Class_Normal'}
RULES = [  # (padrao antigo, novo bonus)
    (r'bonus2 bAddRace,(RC_Boss|RC_NonBoss|10|11),', 'bonus2 bAddClass,{c},'),
    (r'bonus2 bSubRace,(RC_Boss|RC_NonBoss|10|11),', 'bonus2 bSubClass,{c},'),
    (r'bonus2 bMagicAddRace,(RC_Boss|RC_NonBoss|10|11),', 'bonus2 bMagicAddClass,{c},'),
    (r'bonus2 bWeaponComaRace,(RC_Boss|RC_NonBoss|10|11),', 'bonus2 bWeaponComaClass,{c},'),
    (r'bonus bDefRatioAtkRace,(RC_Boss|RC_NonBoss|10|11)\b', 'bonus bDefRatioAtkClass,{c}'),
    (r'bonus bIgnoreDefRace,(RC_Boss|RC_NonBoss|10|11)\b', 'bonus bIgnoreDefClass,{c}'),
    (r'bonus bIgnoreMDefRace,(RC_Boss|RC_NonBoss|10|11)\b', 'bonus2 bIgnoreMdefClassRate,{c},100'),
    (r'bonus2 bIgnoreMdefRate,(RC_Boss|RC_NonBoss|10|11),', 'bonus2 bIgnoreMdefClassRate,{c},'),
    (r'bonus2 bIgnoreDefRate,(RC_Boss|RC_NonBoss|10|11),', 'bonus2 bIgnoreDefClassRate,{c},'),
    (r'bonus2 bIgnoreMdefRate,', 'bonus2 bIgnoreMdefRaceRate,'),
    (r'bonus2 bIgnoreDefRate,', 'bonus2 bIgnoreDefRaceRate,'),
]
stats2 = collections.Counter()
for p in files:
    raw = open(p, 'rb').read().decode('cp1252', errors='surrogateescape')
    new = raw
    for pat, rep in RULES:
        def sub(m, rep=rep):
            stats2[rep.split(',')[0]] += 1
            return rep.format(c=BOSS.get(m.group(1), '')) if m.groups() else rep
        new = re.sub(pat, sub, new, flags=re.I)
    if new != raw:
        open(p, 'wb').write(new.encode('cp1252', errors='surrogateescape'))
print('racas chefe/nao chefe:', dict(stats2))

# NNGO: funcoes globais com o mesmo nome de variaveis (no rAthena o nome da funcao vira palavra reservada)
fn_names = set()
texts = {p: open(p, 'rb').read().decode('cp1252', errors='surrogateescape') for p in files if p.endswith('.txt')}
for t in texts.values():
    fn_names |= set(re.findall(r'(?m)^function\s+script\s+([A-Za-z_]\w*)\s*\{', t))
clash = set()
for n in fn_names:
    pat = re.compile(r'(?<![\w"])' + re.escape(n) + r'\s*(?:[=!<>]=?|,|\))|set\s+' + re.escape(n) + r'\b', re.I)
    if any(pat.search(re.sub(r'"[^"\n]*"', '""', t)) for t in texts.values()):
        clash.add(n)
ren = 0
for p, t in texts.items():
    new = t
    for n in clash:
        new = re.sub(r'(?m)^(function\s+script\s+)' + re.escape(n) + r'(\s*\{)', r'\1fn_' + n + r'\2', new)
        new = re.sub(r'(callfunc\s*\(?\s*")' + re.escape(n) + r'"', r'\1fn_' + n + '"', new, flags=re.I)
    if new != t:
        ren += 1
        open(p, 'wb').write(new.encode('cp1252', errors='surrogateescape'))
print('funcoes renomeadas:', sorted(clash), 'arquivos:', ren)
