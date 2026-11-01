#!/usr/bin/env python3
"""Instala as DBs convertidas do Naruto Maniacs dentro do rAthena.
Uso: python3 -I apply_db.py <out/db> <rathena> <cronus/db> <cronus/conf>
"""
import os, re, sys, shutil

OUT, RA, CDB, CCONF = sys.argv[1:5]
KIT = os.environ.get('KIT', 'nmo')
NMO = os.path.join(RA, 'db', KIT)
os.makedirs(NMO, exist_ok=True)

# 1) YAMLs convertidos. item/mob em cp1252 (o cliente BR mostra os nomes nessa codificacao)
for f in ['item_db', 'mob_db', 'skill_tree', 'quest_db', 'item_group_db', 'mob_summon', 'statpoint', 'job_exp', 'job_stats', 'skill_db', 'const']:
    src = os.path.join(OUT, f + '.yml')
    txt = open(src, encoding='utf8').read()
    hdr = f'# Naruto Maniacs (convertido do Cronus) - nao editar o original do rAthena, editar aqui\n'
    with open(os.path.join(NMO, f + '.yml'), 'w', encoding='cp1252', errors='replace') as o:
        o.write(hdr + txt)

# 2) Substitui o arquivo pre-re pelo do NMO nas DBs que o NMO define por completo
def swap_footer(dbfile, nmofile):
    p = os.path.join(RA, 'db', dbfile)
    s = open(p, encoding='utf8').read()
    if 'db/' + KIT + '/' + nmofile in s: return
    new = re.sub(r'(- Path: )db/pre-re/' + re.escape(dbfile), r'\1db/' + KIT + '/' + nmofile, s)
    assert new != s, dbfile
    open(p, 'w', encoding='utf8').write(new)
for f in ['item_db.yml', 'mob_db.yml', 'skill_tree.yml', 'quest_db.yml', 'item_group_db.yml', 'mob_summon.yml', 'statpoint.yml']:
    swap_footer(f, f)

# item_combos: o NMO nao tinha combos; esvazia a lista padrao para nao criar bonus novos
p = os.path.join(RA, 'db', 'item_combos.yml')
s = open(p, encoding='utf8').read()
s2 = re.sub(r'\n\s*- Path: db/pre-re/item_combos.yml\n\s*Mode: Prerenewal', '', s)
open(p, 'w', encoding='utf8').write(s2)

# 3) job_stats: tabelas do NMO carregadas depois das padrao (sobrescrevem por classe)
p = os.path.join(RA, 'db', 'job_stats.yml')
s = open(p, encoding='utf8').read()
if 'db/' + KIT + '/' not in s:
    s = s.replace('  - Path: db/import/job_stats.yml',
                  '  - Path: db/' + KIT + '/job_stats.yml\n    Mode: Prerenewal\n  - Path: db/' + KIT + '/job_exp.yml\n    Mode: Prerenewal\n\n  - Path: db/import/job_stats.yml')
    open(p, 'w', encoding='utf8').write(s)

# 3b) skills (diferencas do NMO por cima do pre-re) e constantes novas
def add_after(dbfile, after, newpath):
    p = os.path.join(RA, 'db', dbfile)
    s = open(p, encoding='utf8').read()
    if newpath in s: return
    s = s.replace(after, after + '\n  - Path: ' + newpath + '\n    Mode: Prerenewal', 1) if 'Mode: Prerenewal' in after else s.replace(after, after + '\n  - Path: ' + newpath, 1)
    open(p, 'w', encoding='utf8').write(s)
add_after('skill_db.yml', '  - Path: db/pre-re/skill_db.yml\n    Mode: Prerenewal', 'db/' + KIT + '/skill_db.yml')
add_after('const.yml', '  Imports:', 'db/' + KIT + '/const.yml')

# 4) habilidades dos monstros (txt, mesmo formato do Cronus)
with open(os.path.join(RA, 'db', 'pre-re', 'mob_skill_db.txt'), 'wb') as o:
    o.write(b'// Naruto Maniacs: mob_skill_db.txt + mob_skill_db2.txt do Cronus\n')
    for f in ('mob_skill_db.txt', 'mob_skill_db2.txt'):
        o.write(open(os.path.join(CDB, f), 'rb').read().replace(b'\r\n', b'\n') + b'\n')

# 5) item_noequip (mesmo formato)
src = os.path.join(CDB, 'item_noequip.txt')
if os.path.exists(src):
    shutil.copy(src, os.path.join(RA, 'db', 'import', 'item_noequip.txt'))

# 6) mapas: indice extra + lista de mapas do NMO
ra_idx = set()
for l in open(os.path.join(RA, 'db', 'map_index.txt'), encoding='latin1'):
    l = l.strip()
    if l and not l.startswith('//'): ra_idx.add(l.split()[0].lower())
maps = []
for l in open(os.path.join(CCONF, 'maps_athena.conf'), encoding='latin1'):
    m = re.match(r'^map:\s*(\S+)', l.strip())
    if m:
        n = re.sub(r'\.gat$', '', m.group(1))
        if n not in maps: maps.append(n)
extra = [m for m in maps if m.lower() not in ra_idx]
with open(os.path.join(RA, 'db', 'import', 'map_index.txt'), 'w') as o:
    o.write('// Mapas do Naruto Maniacs que nao existem no rAthena\n' + ''.join(m + '\n' for m in extra))
with open(os.path.join(RA, 'conf', 'maps_athena.conf'), 'w') as o:
    o.write('// Lista de mapas do Naruto Maniacs (vinda do Cronus)\n' + ''.join(f'map: {m}\n' for m in maps))
print(f'{len(maps)} mapas, {len(extra)} novos no indice: {extra}')
