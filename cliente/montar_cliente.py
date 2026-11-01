#!/usr/bin/env python3
"""Monta o zip do cliente do Ragnaruto para os jogadores.
Uso: python3 -I montar_cliente.py <cliente_base.zip> <patch_nngo.zip> <item_db.yml> <ip> <saida.zip>
- cliente_base.zip: cliente 2025-06-04 (o mesmo do GB9 BETA PROVISORIO)
- patch_nngo.zip:   PATCH NNGO GRF SEM SENHA.zip (GRFs sem senha do NNGO)
Ordem das GRFs igual ao DATA.INI original do NNGO (so entram as que o cliente original carregava).
"""
import io, os, re, shutil, struct, sys, tempfile, zipfile, zlib

BASE, PATCH, ITEMDB, IP, OUT = sys.argv[1:6]
EXE_ORIG = '2025-06-04_Ragexe_1748494356_clientinfo.xml_patched.exe'
TOP = 'Ragnaruto/'
GRFS_NNGO = ['NNGO.grf', 'dataM.grf', 'dataS.grf', 'NNGO3.grf', 'NNGO4.grf', 'NNGO2.grf']
DATA_INI = ['NNGO.grf', 'dataM.grf', 'dataS.grf', 'NNGO3.grf', 'NNGO4.grf', 'NNGO2.grf',
            'data_gearfinder.grf', 'data_official.grf', 'data.grf']
SKIP = re.compile(r'(?i)^(savedata/|screenshot/|replay/|memo/|gearfinder offline-ro\.exe$|unins000\.dat$|data\.ini$|'
                  r'data/clientinfo\.xml$|data/sclientinfo\.xml$|systemen/iteminfo\.lua$|systemen/iteminfo_c\.lua$|'
                  r'nngo_.*\.grf$|ragnaruto\.grf$)')

def grf_entries(f):
    f.seek(0); h = f.read(46)
    off, seed, nfiles, ver = struct.unpack('<IIII', h[30:46])
    f.seek(off + 46); cs, us = struct.unpack('<II', f.read(8))
    t = zlib.decompress(f.read(cs)); n = nfiles - seed - 7; p = 0; out = {}
    for _ in range(n):
        e = t.index(b'\0', p); name = t[p:e]; p = e + 1
        c, cal, u, fl, o = struct.unpack('<IIIBI', t[p:p + 17]); p += 17
        if fl & 1: out[name.lower()] = (name, cal, u, o)
    return out

def grf_read(f, e):
    f.seek(e[3] + 46); return zlib.decompress(f.read(e[1]))[:e[2]]

def ansi(b):  # nome como o Windows (cp1252) mostra os bytes cp949 do cliente
    s = []
    for ch in b:
        try: s.append(bytes([ch]).decode('cp1252'))
        except UnicodeDecodeError: s.append(chr(ch))
    return ''.join(s)

# ---------- tabelas de itens do NNGO -> SystemEN/itemInfo_C.lua ----------
def tab(raw, keep_us=False):
    d = {}
    for l in raw.split(b'\n'):
        m = re.match(rb'^(\d+)#([^#]*)#', l.strip(b'\r'))
        if m: d[int(m.group(1))] = m.group(2).strip() if keep_us else m.group(2).replace(b'_', b' ').strip()
    return d

def desc(raw):
    d = {}; cur = None; buf = []
    for l in raw.replace(b'\r', b'').split(b'\n'):
        if cur is None:
            m = re.match(rb'^(\d+)#\s*$', l)
            if m: cur = int(m.group(1)); buf = []
        elif l.strip() == b'#': d[cur] = buf; cur = None
        elif l.endswith(b'#') and not l.startswith(b'^'): buf.append(l[:-1]); d[cur] = buf; cur = None
        else: buf.append(l)
    return d

def iteminfo(n3, up):
    def get(f, name):
        e = grf_entries(f).get(name.lower())
        return grf_read(f, e) if e else b''
    def both(name, fn):
        d = fn(get(up, name)); d.update(fn(get(n3, name))); return d  # NNGO3 vem antes de update.grf
    name = both(b'data\\idnum2itemdisplaynametable.txt', tab)
    res = both(b'data\\idnum2itemresnametable.txt', lambda r: tab(r, True))
    dsc = both(b'data\\idnum2itemdesctable.txt', desc)
    uname = both(b'data\\id2num2itemdisplaynametable.txt', tab)
    ures = tab(get(up, b'data\\num2itemresnametable.txt'), True)
    udsc = desc(get(up, b'data\\num2itemdesctable.txt'))
    slots, view, cur = {}, {}, None
    for l in open(ITEMDB, encoding='cp1252', errors='replace'):
        m = re.match(r'  - Id: (\d+)', l)
        if m: cur = int(m.group(1)); continue
        m = re.match(r'    Slots: (\d+)', l)
        if m and cur: slots[cur] = int(m.group(1))
        m = re.match(r'    View: (\d+)', l)
        if m and cur: view[cur] = int(m.group(1))
    q = lambda b: b'"' + b.replace(b'\\', b'\\\\').replace(b'"', b'\\"') + b'"'
    o = [b'-- Itens do Ragnaruto (NNGO)\r\ntbl_custom = {\r\n}\r\n\r\ntbl_override = {\r\n']
    for i in sorted(set(name) | set(dsc)):
        n = name.get(i) or b'Item %d' % i
        r = res.get(i) or ures.get(i) or b'\xbb\xe7\xb0\xfa'
        o.append(b'\t[%d] = {\r\n\t\tunidentifiedDisplayName = %s,\r\n\t\tunidentifiedResourceName = %s,\r\n' % (i, q(uname.get(i) or n), q(ures.get(i) or r)))
        o.append(b'\t\tunidentifiedDescriptionName = { ' + b', '.join(q(x) for x in (udsc.get(i) or [b''])) + b' },\r\n')
        o.append(b'\t\tidentifiedDisplayName = %s,\r\n\t\tidentifiedResourceName = %s,\r\n' % (q(n), q(r)))
        o.append(b'\t\tidentifiedDescriptionName = {\r\n' + b',\r\n'.join(b'\t\t\t' + q(x) for x in (dsc.get(i) or [b''])) + b'\r\n\t\t},\r\n')
        o.append(b'\t\tslotCount = %d,\r\n\t\tClassNum = %d,\r\n\t\tcostume = false\r\n\t},\r\n' % (slots.get(i, 0), view.get(i, 0)))
    o.append(b'}\r\n')
    return b''.join(o)

CLIENTINFO = ('<?xml version="1.0" encoding="euc-kr" ?>\r\n<clientinfo>\r\n  <servicetype>korea</servicetype>\r\n'
              '  <servertype>primary</servertype>\r\n  <connection>\r\n    <display>Ragnaruto</display>\r\n'
              '    <desc>Naruto New Generation</desc>\r\n    <address>%s</address>\r\n    <port>6900</port>\r\n'
              '    <version>55</version>\r\n    <langtype>1</langtype>\r\n    <registrationweb>http://%s/</registrationweb>\r\n'
              '    <loading>\r\n' + ''.join('      <image>nngo0%d.jpg</image>\r\n' % i for i in range(8)) +
              '    </loading>\r\n  </connection>\r\n</clientinfo>\r\n') % (IP, IP)

LEIAME = """RAGNARUTO - CLIENTE PROVISORIO
==============================

1. Extraia este zip numa pasta (ex.: C:\\Ragnaruto). Nao jogue de dentro do zip.
2. Abra o arquivo Ragnaruto.exe. Se der erro, clique com o botao direito nele
   e escolha "Executar como administrador".
3. Para criar a conta, digite no usuario o nome desejado + _M (ou _F),
   por exemplo: naruto_M, e escolha uma senha. Depois entre so com: naruto
4. No jogo, fale com a Anko para comecar.

Comandos uteis: @combate (como atacar), @treinos, @ajuda
"""

def main():
    tmp = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(OUT)))
    zb = zipfile.ZipFile(BASE); zp = zipfile.ZipFile(PATCH)
    pnames = {os.path.basename(n).lower(): n for n in zp.namelist()}
    # GRFs do NNGO que precisam ser lidas (tabelas e texturas)
    def tmpgrf(name):
        dst = os.path.join(tmp, name)
        with zp.open(pnames[name.lower()]) as s, open(dst, 'wb') as d: shutil.copyfileobj(s, d, 1 << 20)
        return open(dst, 'rb')
    n3, up, dt = tmpgrf('NNGO3.grf'), tmpgrf('update.grf'), tmpgrf('dataT.grf')
    top = zb.namelist()[0].split('/')[0] + '/'
    out = zipfile.ZipFile(OUT + '.tmp', 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
    def put(name, data):
        out.writestr(zipfile.ZipInfo(TOP + name, (2026, 11, 1, 12, 0, 0)), data, zipfile.ZIP_DEFLATED)
    def copy(src_zip, info, name, method):
        zi = zipfile.ZipInfo(TOP + name, info.date_time); zi.compress_type = method; zi.file_size = info.file_size
        with src_zip.open(info) as s, out.open(zi, 'w', force_zip64=True) as d: shutil.copyfileobj(s, d, 1 << 20)
    itemlua = None; n = 0
    for info in zb.infolist():
        if info.is_dir() or not info.filename.startswith(top): continue
        rel = info.filename[len(top):]
        if rel.lower() == 'systemen/iteminfo.lua': itemlua = zb.read(info)
        if SKIP.match(rel): continue
        if rel == EXE_ORIG: rel = 'Ragnaruto.exe'
        big = rel.lower().endswith(('.grf', '.exe', '.dll'))
        copy(zb, info, rel, zipfile.ZIP_STORED if big else zipfile.ZIP_DEFLATED); n += 1
    print('cliente base:', n, 'arquivos', flush=True)
    for g in GRFS_NNGO:
        copy(zp, zp.getinfo(pnames[g.lower()]), g, zipfile.ZIP_STORED)
    print('GRFs do NNGO ok', flush=True)
    # texturas do dataT.grf sem a interface antiga de 2008 (vao soltas na pasta data)
    UI = 'data\\texture\\유저인터페이스\\'.encode('cp949')
    KEEP = [UI + s.encode('cp949') + b'\\' for s in ('item', 'collection', 'map', 'illust')]
    k = 0
    for low, e in sorted(grf_entries(dt).items()):
        if low.startswith(UI) and not any(low.startswith(x) for x in KEEP): continue
        put(ansi(e[0]).replace('\\', '/'), grf_read(dt, e)); k += 1
    print('texturas:', k, flush=True)
    for a, b in [(b"DisplayServer = 1", b"DisplayServer = 0"), (b"DisplayItemID = 2", b"DisplayItemID = 0"),
                 (b"DisplayDatabase = true", b"DisplayDatabase = false"), (b"DisplayCustomServer = 1", b"DisplayCustomServer = 0"),
                 (b"CServerName = 'ExampleRO'", b"CServerName = 'Ragnaruto'")]:
        itemlua = itemlua.replace(a, b)
    put('SystemEN/itemInfo.lua', itemlua)
    put('SystemEN/itemInfo_C.lua', iteminfo(n3, up))
    put('DATA.ini', ('[Data]\r\n' + ''.join('%d=%s\r\n' % (i, g) for i, g in enumerate(DATA_INI))).encode())
    put('data/clientinfo.xml', CLIENTINFO.encode()); put('data/sclientinfo.xml', CLIENTINFO.encode())
    put('LEIA-ME.txt', LEIAME.replace('\n', '\r\n').encode('cp1252'))
    out.close(); os.replace(OUT + '.tmp', OUT); shutil.rmtree(tmp)
    print('pronto:', OUT, os.path.getsize(OUT) // 1048576, 'MB')

main()
