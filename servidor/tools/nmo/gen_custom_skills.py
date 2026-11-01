#!/usr/bin/env python3
"""Gera entradas completas (skill_db.yml) para skills que so existem no emulador antigo.
Uso: python3 -I gen_custom_skills.py <cronus/db> <lista id nome> <saida.yml> <rathena>
Tambem renumera no db/pre-re/skill_db.yml do rAthena as skills de monstro movidas para 9000+.
"""
import os, re, sys
CDB, LIST, OUT, RA = sys.argv[1:5]
ids = {int(l.split()[0]): l.split()[1] for l in open(LIST) if l.strip()}

TARGET = {0: 'Passive', 1: 'Attack', 2: 'Ground', 4: 'Self', 16: 'Support', 32: 'Trap'}
NK = {0x1: 'NoDamage', 0x2: 'Splash', 0x4: 'SplashSplit', 0x8: 'IgnoreAtkCard', 0x10: 'IgnoreElement',
      0x20: 'IgnoreDefense', 0x40: 'IgnoreFlee', 0x80: 'IgnoreDefCard'}
INF2 = {0x1: 'IsQuest', 0x2: 'IsNpc', 0x4: 'IsWedding', 0x8: 'IsSpirit', 0x10: 'IsGuild', 0x20: 'IsSong',
        0x40: 'IsEnsemble', 0x80: 'IsTrap', 0x100: 'TargetSelf', 0x200: 'NoTargetSelf', 0x400: 'PartyOnly',
        0x800: 'GuildOnly', 0x1000: 'NoTargetEnemy'}
TYPE = {'weapon': 'Weapon', 'magic': 'Magic', 'misc': 'Misc', 'none': 'None'}

def num(x):
    x = (x or '0').strip()
    try: return int(x, 0)
    except ValueError: return 0

out = ['Header:\n  Type: SKILL_DB\n  Version: 4\n\nBody:\n']
for l in open(os.path.join(CDB, 'skill_db.txt'), encoding='latin1'):
    l = l.split('//')[0].strip()
    if not l: continue
    p = [x.strip() for x in l.split(',')]
    if len(p) < 17 or not p[0].isdigit() or int(p[0]) not in ids: continue
    sid = int(p[0]); name = ids[sid]
    e = [f'  - Id: {sid}\n    Name: {name}\n    Description: {p[16] or name}\n    MaxLevel: {max(1, num(p[7]))}\n']
    t = TYPE.get(p[13].lower(), 'None')
    if t != 'None': e.append(f'    Type: {t}\n')
    inf = num(p[3])
    if inf in TARGET and inf: e.append(f'    TargetType: {TARGET[inf]}\n')
    nk = num(p[5]); fl = [v for k, v in NK.items() if nk & k]
    if fl: e.append('    DamageFlags:\n' + ''.join(f'      {f}: true\n' for f in fl))
    inf2 = num(p[11]); fl = [v for k, v in INF2.items() if inf2 & k]
    if fl: e.append('    Flags:\n' + ''.join(f'      {f}: true\n' for f in fl))
    hit = num(p[2])
    if hit in (6, 8): e.append(f'    Hit: {"Multi_Hit" if hit == 8 else "Single"}\n')
    if p[9].lower() == 'no': e.append('    CastCancel: false\n')
    if num(p[10]): e.append(f'    CastDefenseReduction: {num(p[10])}\n')
    out.append(''.join(e))
open(OUT, 'w').write(''.join(out))
print(len(out) - 1, 'skills geradas')

# renumera as skills de monstro do rAthena que estavam nos IDs do NNGO
hpp = open(os.path.join(RA, 'src/map/skill.hpp'), encoding='utf8').read()
body = re.search(r'enum e_skill\s*\{(.*?)\n\};', hpp, re.S).group(1)
val = -1; names = {}
for m in re.finditer(r'^\s*([A-Z][A-Z0-9_]*)\s*(?:=\s*(0x[0-9a-fA-F]+|\d+))?\s*,', body, re.M):
    val = int(m.group(2), 0) if m.group(2) else val + 1
    names[m.group(1)] = val
p = os.path.join(RA, 'db/pre-re/skill_db.yml')
s = open(p, encoding='utf8').read()
def fix(m):
    sid, nm = int(m.group(1)), m.group(2)
    new = names.get(nm)
    return f'  - Id: {new}\n    Name: {nm}\n' if new is not None and new != sid else m.group(0)
s2, n = re.subn(r'  - Id: (\d+)\n    Name: (\S+)\n', fix, s)
moved = sum(1 for a, b in zip(re.findall(r'  - Id: (\d+)', s), re.findall(r'  - Id: (\d+)', s2)) if a != b)
open(p, 'w', encoding='utf8').write(s2)
print('skills do rAthena renumeradas:', moved)
