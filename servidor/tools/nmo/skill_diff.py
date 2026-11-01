#!/usr/bin/env python3
"""Gera db/import/skill_db.yml com as diferencas de skills do Naruto Maniacs (Cronus) em relacao ao rAthena.
Uso: python3 -I skill_diff.py <cronus/db> <rathena> <saida.yml> <item_db_nmo.yml>
"""
import os, re, sys, collections, yaml
CDB, RA, OUT, ITEMYML = sys.argv[1:5]
MAXL = 100
try:
    Loader = yaml.CSafeLoader
except AttributeError:
    Loader = yaml.SafeLoader

def fill(vals, n=MAXL):
    """mesmo algoritmo do skill_split_atoi (Cronus) / SkillDatabase::parseNode (rAthena)"""
    v = list(vals)
    i = len(v)
    if i == 0: return [0] * n
    v += [0] * (n - i)
    if i == 1:
        return [v[0]] * n
    for step in range(1, i // 2 + 1):
        diff = v[i-1] - v[i-step-1]
        ok = all(v[j] - v[j-step] == diff for j in range(i-1, step-1, -1))
        if not ok: continue
        k = i
        while k < n:
            v[k] = v[k-step] + diff
            if v[k] < 1 and v[k-1] >= 0:
                v[k] = 1; diff = 0; step = 1
            k += 1
        return v
    for k in range(i, n): v[k] = v[i-1]
    return v

def split_lv(s):
    return fill([int(x or '0', 0) if re.match(r'^-?(0x[0-9a-fA-F]+|\d+)$', (x or '0').strip()) else 0 for x in str(s).split(':')])

def nmo_lines(f):
    for l in open(os.path.join(CDB, f), encoding='latin1'):
        l = l.split('//')[0].strip()
        if l: yield [x.strip() for x in l.split(',')]

ELEM = ['Neutral', 'Water', 'Earth', 'Fire', 'Wind', 'Poison', 'Holy', 'Dark', 'Ghost', 'Undead']
ELEM_SP = {-1: 'Weapon', -2: 'Endowed', -3: 'Random'}
def elem_name(v):
    return ELEM[v] if 0 <= v < len(ELEM) else ELEM_SP.get(v, 'Neutral')

# ---------- NMO ----------
nmo = {}
for p in nmo_lines('skill_db.txt'):
    sid = int(p[0])
    nmo[sid] = {'max': int(p[7]), 'Range': split_lv(p[1]), 'Element': split_lv(p[4]),
                'SplashArea': split_lv(p[6]), 'HitCount': split_lv(p[8]),
                'ActiveInstance': split_lv(p[12]), 'Knockback': split_lv(p[14])}
for p in nmo_lines('skill_require_db.txt'):
    sid = int(p[0])
    if sid not in nmo or len(p) < 12: continue
    d = nmo[sid]
    d['HpCost'] = split_lv(p[1]); d['MaxHpTrigger'] = split_lv(p[2]); d['SpCost'] = split_lv(p[3])
    d['HpRateCost'] = split_lv(p[4]); d['SpRateCost'] = split_lv(p[5]); d['ZenyCost'] = split_lv(p[6])
    d['SpiritSphereCost'] = split_lv(p[11])
    items = []
    for k in range(10):
        if 12 + k*2 + 1 < len(p):
            iid, amt = int(p[12+k*2] or 0), int(p[13+k*2] or 0)
            if iid > 0 and amt > 0: items.append((iid, amt))
    d['items'] = items
for p in nmo_lines('skill_cast_db.txt'):
    sid = int(p[0])
    if sid not in nmo or len(p) < 6: continue
    d = nmo[sid]
    d['CastTime'] = split_lv(p[1]); d['AfterCastActDelay'] = split_lv(p[2]); d['AfterCastWalkDelay'] = split_lv(p[3])
    d['Duration1'] = split_lv(p[4]); d['Duration2'] = split_lv(p[5])

# nivel maximo efetivo: arvore de skills e skills de monstros
need = collections.defaultdict(int)
for p in nmo_lines('skill_tree.txt'):
    if len(p) >= 13: need[int(p[1])] = max(need[int(p[1])], int(p[2]))
for f in ('mob_skill_db.txt', 'mob_skill_db2.txt'):
    for p in nmo_lines(f):
        if len(p) > 4 and p[3].lstrip('-').isdigit():
            need[int(p[3])] = max(need[int(p[3])], int(p[4] or 0))

# itens: id -> aegis (nomes usados no item_db do NMO convertido)
aegis = {}; cur = None
for l in open(ITEMYML, encoding='utf8', errors='replace'):
    m = re.match(r'  - Id: (\d+)', l)
    if m: cur = int(m.group(1)); continue
    m = re.match(r'    AegisName: (\S+)', l)
    if m and cur is not None: aegis[cur] = m.group(1); cur = None

# ---------- rAthena ----------
ra = {s['Id']: s for s in yaml.load(open(os.path.join(RA, 'db/pre-re/skill_db.yml'), encoding='utf8'), Loader=Loader)['Body']}
# skills que so existem no kit (geradas por gen_custom_skills.py) entram como base da comparacao
if os.environ.get('EXTRA_SKILL_YML'):
    for s_ in yaml.load(open(os.environ['EXTRA_SKILL_YML'], encoding='utf8'), Loader=Loader)['Body']:
        ra[s_['Id']] = s_
cooldown = {}
if os.environ.get('COOLDOWN_DB') and os.path.exists(os.environ['COOLDOWN_DB']):
    for l in open(os.environ['COOLDOWN_DB'], encoding='latin1'):
        l = l.split('//')[0].strip()
        if l and l.split(',')[0].strip().isdigit():
            a, b = l.split(',')[:2]
            cooldown[int(a)] = int(b)
SUB = {'Range': 'Size', 'HitCount': 'Count', 'SplashArea': 'Area', 'ActiveInstance': 'Max', 'Knockback': 'Amount',
       'CastTime': 'Time', 'AfterCastActDelay': 'Time', 'AfterCastWalkDelay': 'Time', 'Duration1': 'Time', 'Duration2': 'Time',
       'HpCost': 'Amount', 'MaxHpTrigger': 'Amount', 'SpCost': 'Amount', 'HpRateCost': 'Amount', 'SpRateCost': 'Amount',
       'ZenyCost': 'Amount', 'SpiritSphereCost': 'Amount'}
REQ = {'HpCost', 'MaxHpTrigger', 'SpCost', 'HpRateCost', 'SpRateCost', 'ZenyCost', 'SpiritSphereCost'}

def ra_arr(node, field):
    dflt = 'Neutral' if field == 'Element' else 0
    if node is None: return [dflt] * MAXL
    v = node.get(field)
    if v is None: return [dflt] * MAXL
    if isinstance(v, list):
        if field == 'Element':
            vals = {}
            for e in v: vals[e['Level']] = e['Element']
            mx = max(vals); return [vals.get(i, 'Neutral') for i in range(1, mx + 1)] + [vals[mx]] * (MAXL - mx)
        vals = {e['Level']: e.get(SUB[field], 0) for e in v}
        mx = max(vals)
        return fill([vals.get(i, 0) for i in range(1, mx + 1)])
    return [v] * MAXL

out = ['Header:\n  Type: SKILL_DB\n  Version: 4\n\nBody:\n']
stats = collections.Counter(); changed = []
for sid, d in sorted(nmo.items()):
    s = ra.get(sid)
    if s is None:
        stats['skill so no Cronus'] += 1; continue
    L = min(MAXL, max(d['max'], need.get(sid, 0)))
    if L < 1: continue
    lines = []
    if L != s.get('MaxLevel'):
        lines.append(f'    MaxLevel: {L}\n'); stats['MaxLevel'] += 1
    req = []
    for field in SUB:
        if field not in d: continue
        a = d[field][:L]
        b = ra_arr(s.get('Requires') if field in REQ else s, field)[:L]
        if a == b: continue
        stats[field] += 1
        block = [f'{"      " if field in REQ else "    "}{field}:\n']
        ind = '        ' if field in REQ else '      '
        for lv in range(1, L + 1):
            block.append(f'{ind}- Level: {lv}\n{ind}  {SUB[field]}: {a[lv-1]}\n')
        (req if field in REQ else lines).extend(block)
    a = [elem_name(x) for x in d['Element'][:L]]
    b = ra_arr(s, 'Element')[:L]
    if [x.lower() for x in a] != [str(x).lower() for x in b]:
        stats['Element'] += 1
        lines.append('    Element:\n' + ''.join(f'      - Level: {lv}\n        Element: {a[lv-1]}\n' for lv in range(1, L + 1)))
    # itens consumidos
    ra_items = sorted((it['Item'].lower(), it.get('Amount', 1)) for it in (s.get('Requires', {}) or {}).get('ItemCost', []) or [] if 'Level' not in it)
    nm_items = sorted((aegis.get(i, str(i)).lower(), a_) for i, a_ in d.get('items', []))
    if 'items' in d and nm_items != ra_items and all(i in aegis for i, _ in d['items']):
        stats['ItemCost'] += 1
        req.append('      ItemCost:\n' + ''.join(f'        - Item: {aegis[i]}\n          Amount: {a_}\n' for i, a_ in d['items']))
    if sid in cooldown and cooldown[sid] > 0:
        lines.append(f'    Cooldown: {cooldown[sid]}\n'); stats['Cooldown'] += 1
    if req:
        lines.append('    Requires:\n' + ''.join(req))
    if lines:
        out.append(f'  - Id: {sid}\n    Name: {s["Name"]}\n' + ''.join(lines))
        changed.append(s['Name'])
open(OUT, 'w').write(''.join(out))
print(f'{len(changed)} skills com diferencas;', dict(stats))
