#!/usr/bin/env python3
"""Converte as DBs do Naruto Maniacs (Cronus/eAthena 2010) para YAML do rAthena.
Uso: python3 -I nmo2ra.py <pasta_db_cronus> <pasta_rathena> <pasta_saida>
"""
import os, re, sys, collections

SRC, RA, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
ENC = 'latin1'

def lines(path):
    with open(path, encoding=ENC, errors='replace') as f:
        for raw in f:
            l = raw.rstrip('\r\n')
            s = l.strip()
            if not s or s.startswith('//'):
                continue
            # tira comentario no fim da linha (fora de chaves)
            depth = 0; out = []
            i = 0
            while i < len(l):
                c = l[i]
                if c == '{': depth += 1
                elif c == '}': depth -= 1
                if depth == 0 and l.startswith('//', i):
                    break
                out.append(c); i += 1
            s = ''.join(out).strip()
            if s:
                yield s

# ---------- constantes de classe ----------
def load_jobs():
    txt = open(os.path.join(RA, 'src/common/mmo.hpp'), encoding='utf8').read()
    body = re.search(r'enum e_job\s*\{(.*?)\};', txt, re.S).group(1)
    jobs = {}; val = -1
    for m in re.finditer(r'(JOB_[A-Z0-9_]+)\s*(?:=\s*(\d+))?\s*,', body):
        name, v = m.group(1), m.group(2)
        val = int(v) if v else val + 1
        if name in ('JOB_MAX_BASIC', 'JOB_MAX'):
            continue
        jobs[val] = '_'.join(p.capitalize() for p in name[4:].split('_'))
    return jobs
JOBS = load_jobs()
NO_EXP = {22, 26, 27}  # wedding, xmas, summer

def jobname(i):
    return JOBS[int(i)]

# ---------- skill id -> nome ----------
def load_skill_names():
    names = {}
    cur = None
    for l in open(os.path.join(RA, 'db/pre-re/skill_db.yml'), encoding='utf8'):
        m = re.match(r'\s*- Id: (\d+)', l)
        if m: cur = int(m.group(1)); continue
        m = re.match(r'\s{4}Name: (\S+)', l)
        if m and cur is not None:
            names[cur] = m.group(1); cur = None
    return names
SKILLS = load_skill_names()
NMO_SKILL_NAME = {}
for l in lines(os.path.join(SRC, 'skill_db.txt')):
    p = l.split(',')
    if len(p) >= 16:
        NMO_SKILL_NAME[int(p[0])] = p[15].strip()

def skillname(i):
    i = int(i)
    return SKILLS.get(i) or NMO_SKILL_NAME.get(i) or str(i)

report = collections.defaultdict(list)

def hdr(t, v):
    return f"Header:\n  Type: {t}\n  Version: {v}\n\nBody:\n"

# ---------- job_exp.yml ----------
def conv_exp():
    tables = {}  # (job, type) -> (maxlv, list)
    for l in lines(os.path.join(SRC, 'exp.txt')):
        p = [x.strip() for x in l.split(',')]
        maxlv = int(p[0]); jobs = [int(j) for j in p[1].split(':') if j.strip()]
        typ = int(p[2]); vals = [int(x) for x in p[3:] if x != '']
        # replica o Cronus: le maxlv-1 valores, remove zeros finais, completa com o ultimo
        vals = vals[:maxlv - 1]
        while vals and vals[-1] <= 0: vals.pop()
        while len(vals) < maxlv - 1:
            vals.append(vals[-1] if vals else 0)
        for j in jobs:
            tables[(j, typ)] = (maxlv, vals)
    groups = collections.OrderedDict()
    for (j, typ), (maxlv, vals) in tables.items():
        if j not in JOBS: report['exp'].append(f'job {j} desconhecido'); continue
        key = (typ, maxlv, tuple(vals))
        groups.setdefault(key, []).append(j)
    out = [hdr('JOB_STATS', 4)]
    for (typ, maxlv, vals), js in groups.items():
        out.append('  - Jobs:\n' + ''.join(f'      {jobname(j)}: true\n' for j in js))
        if typ == 0:
            out.append(f'    MaxBaseLevel: {maxlv}\n    BaseExp:\n')
        else:
            out.append(f'    MaxJobLevel: {maxlv}\n    JobExp:\n')
        for lv, e in enumerate(vals, 1):
            out.append(f'      - Level: {lv}\n        Exp: {e}\n')
    open(os.path.join(OUT, 'job_exp.yml'), 'w').write(''.join(out))
    report['exp'].append(f'{len(groups)} tabelas de EXP')

# ---------- job_stats.yml (peso, HP/SP, ASPD, bonus por nivel de classe) ----------
WEAPONS = ['Fist','Dagger','1hSword','2hSword','1hSpear','2hSpear','1hAxe','2hAxe','Mace','2hMace',
           'Staff','Bow','Knuckle','Musical','Whip','Book','Katar','Revolver','Rifle','Gatling',
           'Shotgun','Grenade','Huuma','2hStaff']
STATS = ['Str','Agi','Vit','Int','Dex','Luk']
def conv_jobstats():
    j1 = {}
    for l in lines(os.path.join(SRC, 'job_db1.txt')):
        p = [x.strip() for x in l.split(',')]
        if len(p) < 29: continue
        j1[int(p[0])] = p
    j2 = {}
    for l in lines(os.path.join(SRC, 'job_db2.txt')):
        p = [x.strip() for x in l.split(',')]
        if not p[0].lstrip('-').isdigit(): continue
        j2[int(p[0])] = [int(x) for x in p[1:] if x != '']
    out = [hdr('JOB_STATS', 4)]
    for j in sorted(set(j1) | set(j2)):
        if j not in JOBS: report['stats'].append(f'job {j} desconhecido'); continue
        out.append(f'  - Jobs:\n      {jobname(j)}: true\n')
        if j in j1:
            p = j1[j]
            out.append(f'    MaxWeight: {p[1]}\n    HpFactor: {p[2]}\n    HpIncrease: {p[3]}\n'
                       f'    SpFactor: 0\n    SpIncrease: {p[4]}\n    BaseASPD:\n')
            for w, v in zip(WEAPONS, p[5:29]):
                out.append(f'      {w}: {v}\n')
        if j in j2:
            # todos os niveis explicitos (zeros incluidos) para anular o bonus padrao do rAthena
            out.append('    BonusStats:\n')
            for lv in range(1, 100):
                c = collections.Counter()
                if lv <= len(j2[j]) and 1 <= j2[j][lv-1] <= 6:
                    c[STATS[j2[j][lv-1]-1]] += 1
                out.append(f'      - Level: {lv}\n' + ''.join(f'        {k}: {c[k]}\n' for k in STATS))
    open(os.path.join(OUT, 'job_stats.yml'), 'w').write(''.join(out))
    report['stats'].append(f'{len(j1)} classes com peso/HP/ASPD, {len(j2)} com bonus')

# ---------- statpoint.yml ----------
def conv_statpoint(maxlv=int(os.environ.get("MAXLV", "400"))):
    statp = [0]; stat = 45
    for l in lines(os.path.join(SRC, 'statpoint.txt')):
        if len(statp) > maxlv: break
        stat = int(l.split()[0]); statp.append(stat)
    for i in range(len(statp), maxlv + 1):
        stat += (i + 15) // 5; statp.append(stat)
    out = [hdr('STATPOINT_DB', 2)]
    for lv in range(1, maxlv + 1):
        out.append(f'  - Level: {lv}\n    Points: {statp[lv]}\n')
    open(os.path.join(OUT, 'statpoint.yml'), 'w').write(''.join(out))
    report['statpoint'].append(f'1..{maxlv}: {statp[1]} -> {statp[maxlv]}')

# ---------- skill_tree.yml (arvore completa, sem heranca) ----------
def conv_skilltree():
    tree = collections.OrderedDict()
    for l in lines(os.path.join(SRC, 'skill_tree.txt')):
        p = [x.strip() for x in l.split(',')]
        if len(p) < 13: continue
        j, sk, mx = int(p[0]), int(p[1]), int(p[2])
        if j not in JOBS: report['tree'].append(f'job {j} desconhecido'); continue
        reqs = []
        for k in range(5):
            rid, rlv = int(p[3+k*2] or 0), int(p[4+k*2] or 0)
            if rid > 0 and rlv > 0: reqs.append((rid, rlv))
        d = tree.setdefault(j, collections.OrderedDict())
        if sk not in d:
            d[sk] = (mx, reqs)
    out = [hdr('SKILL_TREE_DB', 1)]
    for j, d in tree.items():
        out.append(f'  - Job: {jobname(j)}\n    Tree:\n')
        for sk, (mx, reqs) in d.items():
            out.append(f'      - Name: {skillname(sk)}\n        MaxLevel: {mx}\n')
            if reqs:
                out.append('        Requires:\n' + ''.join(
                    f'          - Name: {skillname(r)}\n            Level: {lv}\n' for r, lv in reqs))
    open(os.path.join(OUT, 'skill_tree.yml'), 'w').write(''.join(out))
    unk = sorted({s for d in tree.values() for s in d if skillname(s) == str(s)})
    report['tree'].append(f'{len(tree)} classes; skills sem nome: {unk}')
    return set(tree)

# ---------- itens: mapa id -> aegis ----------
def item_aegis():
    m = {}
    for f in ('item_db.txt', 'item_db2.txt'):
        for l in lines(os.path.join(SRC, f)):
            p = l.split(',')
            if p[0].strip().isdigit():
                m[int(p[0])] = p[1].strip()
    return m
ITEMS = item_aegis()

def mob_sprite():
    m = {}
    for f in ('mob_db.txt', 'mob_db2.txt'):
        for l in lines(os.path.join(SRC, f)):
            p = l.split(',')
            if p[0].strip().isdigit():
                m[int(p[0])] = p[1].strip()
    return m
MOBS = mob_sprite()

# ---------- item_group_db.yml ----------
def conv_groups():
    const = {}
    for l in lines(os.path.join(SRC, 'const.txt')):
        p = l.split()
        if len(p) >= 2 and p[0].startswith('IG_'):
            try: const[int(p[1])] = p[0][3:]
            except ValueError: pass
    files = []
    for l in lines(os.path.join(SRC, 'item_group_db.txt')):
        m = re.match(r'import:\s*(\S+)', l)
        if m: files.append(os.path.basename(m.group(1)))
    groups = collections.OrderedDict(); missing = collections.Counter()
    for f in files:
        path = os.path.join(SRC, f)
        if not os.path.exists(path): report['groups'].append(f'arquivo {f} ausente'); continue
        for l in lines(path):
            p = [x.strip() for x in l.split(',')]
            if len(p) < 2 or not p[0].isdigit(): continue
            g, it = int(p[0]), int(p[1]); rate = int(p[2]) if len(p) > 2 and p[2] else 1
            if it not in ITEMS: missing[it] += 1; continue
            name = const.get(g, f'Group{g}')
            d = groups.setdefault(name, collections.OrderedDict())
            d[ITEMS[it]] = d.get(ITEMS[it], 0) + rate
    out = [hdr('ITEM_GROUP_DB', 5)]
    for name, d in groups.items():
        out.append(f'  - Group: {name}\n    SubGroups:\n      - SubGroup: 1\n        List:\n')
        for idx, (a, r) in enumerate(d.items(), 1):
            out.append(f'          - Index: {idx}\n            Item: {a}\n            Rate: {r}\n')
    open(os.path.join(OUT, 'item_group_db.yml'), 'w').write(''.join(out))
    src_c = open(os.path.join(RA, 'src/map/itemdb.hpp'), encoding='utf8').read()
    known = {m.lower() for m in re.findall(r'\bIG_([A-Za-z0-9_]+)\s*=?', src_c)}
    newc = [n for n in groups if n.lower() not in known]
    with open(os.path.join(OUT, 'const.yml'), 'w') as o:
        o.write(hdr('CONSTANT_DB', 1))
        for k, n in enumerate(newc):
            o.write(f'  - Name: IG_{n}\n    Value: {20000 + k}\n')
    report['groups'].append(f'constantes novas: {newc}')
    report['groups'].append(f'{len(groups)} grupos; itens inexistentes: {sum(missing.values())}')

# ---------- mob_summon.yml ----------
def conv_summon():
    spec = [('mob_branch.txt', 'BLOODY_DEAD_BRANCH', 'DEAD_BRANCH'), ('mob_poring.txt', 'PORING_BOX', 'PORING'),
            ('mob_boss.txt', 'BOSS', 'PORING'), ('mob_pouch.txt', 'BUBBLE_GUM', 'PORING')]
    out = [hdr('MOB_SUMMONABLE_DB', 1)]
    # Cronus: branch = galho seco, poring = presente porin, boss = galho sangrento
    kinds = {'mob_branch.txt': ('Branch_Of_Dead_Tree', 'SCORPION'), 'mob_poring.txt': ('Poring_Box', 'PORING'),
             'mob_boss.txt': ('Bloody_Dead_Branch', 'BAPHOMET'), 'mob_pouch.txt': ('Red_Pouch_Of_Surprise', 'PORING')}
    n = 0
    for f, (grp, default) in kinds.items():
        path = os.path.join(SRC, f)
        if not os.path.exists(path): continue
        rows = []
        dflt = None  # definido pela linha de id 0
        for l in lines(path):
            p = [x.strip() for x in l.split(',')]
            if len(p) < 3: continue
            mid = int(p[0]); rate = int(p[-1] or 0)
            if mid == 0:
                dflt = MOBS.get(rate); continue
            if mid not in MOBS: report['summon'].append(f'{f}: mob {mid} inexistente'); continue
            rows.append((MOBS[mid], rate))
        if not rows: continue
        dflt = dflt or default
        out.append(f'  - Group: {grp}\n    Default: {dflt}\n    Summon:\n')
        seen = {}
        for a, r in rows:
            seen[a] = seen.get(a, 0) + r
        for a, r in seen.items():
            out.append(f'      - Mob: {a}\n        Rate: {r}\n')
        n += len(seen)
    open(os.path.join(OUT, 'mob_summon.yml'), 'w').write(''.join(out))
    report['summon'].append(f'{n} entradas')

# ---------- quest_db.yml ----------
def conv_quests():
    out = [hdr('QUEST_DB', 3)]; n = 0; seen = set()
    for l in lines(os.path.join(SRC, 'quest_db.txt')):
        p = [x.strip() for x in l.split(',')]
        if not p[0].isdigit(): continue
        qid = int(p[0])
        if qid in seen: continue
        seen.add(qid)
        title = ','.join(p[8:]).strip().strip('"') if len(p) > 8 else ''
        title = title.replace('"', "'")
        out.append(f'  - Id: {qid}\n    Title: "{title}"\n')
        t = int(p[1] or 0)
        if t > 0:
            d_, r = divmod(t, 86400); h, r = divmod(r, 3600); mn, sec = divmod(r, 60)
            tl = ''.join(f'{v}{u}' for v, u in ((d_, 'd'), (h, 'h'), (mn, 'mn'), (sec, 's')) if v)
            out.append(f'    TimeLimit: +{tl}\n')
        tg = []
        for k in range(3):
            mid, cnt = int(p[2+k*2] or 0), int(p[3+k*2] or 0)
            if mid > 0 and cnt > 0 and mid in MOBS: tg.append((MOBS[mid], cnt))
        if tg:
            out.append('    Targets:\n' + ''.join(f'      - Mob: {a}\n        Count: {c}\n' for a, c in tg))
        n += 1
    open(os.path.join(OUT, 'quest_db.yml'), 'w').write(''.join(out))
    report['quest'].append(f'{n} quests')

# ---------- mob_db.txt / item_db.txt no formato que o csv2yaml entende ----------
import unicodedata
def ascii_name(n):
    n = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode()
    n = re.sub(r'[^A-Za-z0-9_]', '_', n)
    if not n or n[0].isdigit(): n = 'N_' + n
    return n

def split_db(l):
    """separa campos simples dos scripts {...}"""
    i = l.find('{')
    head = l if i < 0 else l[:i]
    tail = '' if i < 0 else l[i:]
    return [x.strip() for x in head.split(',')], tail

AEGIS_MAP = {'item': {}, 'mob': {}}
def stock_names(files):
    m = {}; cur = None
    for f in files:
        for l in open(os.path.join(RA, f), encoding='utf8'):
            mm = re.match(r'  - Id: (\d+)', l)
            if mm: cur = int(mm.group(1)); continue
            mm = re.match(r'    AegisName: (\S+)', l)
            if mm and cur is not None: m[cur] = mm.group(1); cur = None
    return m
STOCK_ITEM = stock_names(['db/pre-re/item_db_usable.yml', 'db/pre-re/item_db_equip.yml', 'db/pre-re/item_db_etc.yml'])
STOCK_MOB = stock_names(['db/pre-re/mob_db.yml'])
STOCK_LOWER_I = {v.lower() for v in STOCK_ITEM.values()}
STOCK_LOWER_M = {v.lower() for v in STOCK_MOB.values()}
def prep_txt():
    os.makedirs(os.path.join(OUT, 'txt'), exist_ok=True)
    rows = collections.OrderedDict()
    for f in ('item_db.txt', 'item_db2.txt'):
        for l in lines(os.path.join(SRC, f)):
            p, tail = split_db(l)
            if not p[0].isdigit(): continue
            if p[0] in rows: report['items'].append(f'id {p[0]} redefinido em {f}')
            rows[p[0]] = (p, tail)
    used = set()
    with open(os.path.join(OUT, 'txt', 'item_db.txt'), 'w', encoding='utf8') as o:
        for iid, (p, tail) in rows.items():
            orig = p[1]
            a = STOCK_ITEM.get(int(iid)) or ascii_name(orig)
            if int(iid) not in STOCK_ITEM and (a.lower() in used or a.lower() in STOCK_LOWER_I): a = f'{a}_{iid}'
            used.add(a.lower()); AEGIS_MAP['item'][int(iid)] = a
            p[1] = a
            if p[3] == '4': p[3] = '5'      # eAthena 4=arma -> rAthena 5
            elif p[3] == '5': p[3] = '4'    # eAthena 5=armadura -> rAthena 4
            try:
                loc = int(p[14] or '0', 0)
            except ValueError:
                loc = 0
            if p[3] == '5' and loc and not (loc & 0x22):  # "arma" equipada na cabeca etc. -> armadura
                p[3] = '4'; report['items'].append(f'{iid}: arma em slot de armadura -> armadura')
            try:
                if p[11] and int(p[11], 0) > 0xFFFFFFFF: p[11] = '0xFFFFFFFF'
            except ValueError:
                pass
            o.write(','.join(p) + tail + '\n')
    used = set()
    with open(os.path.join(OUT, 'txt', 'mob_db.txt'), 'w', encoding='utf8') as o:
        seen = set()
        for f in ('mob_db2.txt', 'mob_db.txt'):  # mob_db2 tem prioridade
            for l in lines(os.path.join(SRC, f)):
                p = [x.strip() for x in l.split(',')]
                if not p[0].isdigit() or p[0] in seen: continue
                if len(p) > 58: p = p[:58]
                if len(p) == 56: p = p[:54] + ['0', '0'] + p[54:]  # 8 drops + carta -> 9 drops + carta
                if len(p) == 58: p = p[:31] + p[32:]
                elif len(p) < 57:
                    report['mobs'].append(f'mob {p[0]} com {len(p)} colunas (ignorado)'); continue
                seen.add(p[0])
                a = STOCK_MOB.get(int(p[0])) or ascii_name(p[1])
                if int(p[0]) not in STOCK_MOB and (a.lower() in used or a.lower() in STOCK_LOWER_M): a = f'{a}_{p[0]}'
                used.add(a.lower()); AEGIS_MAP['mob'][int(p[0])] = a
                p[1] = a
                o.write(','.join(p) + '\n')
    # mapas id->aegis para as outras DBs
    ITEMS.clear(); ITEMS.update(AEGIS_MAP['item'])
    MOBS.clear(); MOBS.update(AEGIS_MAP['mob'])
    report['items'].append(f"{len(AEGIS_MAP['item'])} itens; {len(AEGIS_MAP['mob'])} monstros")

prep_txt(); conv_exp(); conv_jobstats(); conv_statpoint(); conv_skilltree(); conv_groups(); conv_summon(); conv_quests()
for k, v in report.items():
    print(f'[{k}]', ' | '.join(v[:12]), ('... +%d' % (len(v) - 12)) if len(v) > 12 else '')
