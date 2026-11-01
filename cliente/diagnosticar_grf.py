#!/usr/bin/env python3
"""Diagnostico das entradas de uma GRF que nao abrem com zlib (formato/compressao).
Uso: python3 -I diagnosticar_grf.py <arquivo.grf> <saida.txt>"""
import collections, lzma, struct, sys, zlib
f = open(sys.argv[1], 'rb'); h = f.read(46)
off, seed, nfiles, ver = struct.unpack('<IIII', h[30:46])
f.seek(off + 46); cs, us = struct.unpack('<II', f.read(8))
t = zlib.decompress(f.read(cs)); n = nfiles - seed - 7; pos = 0
out = ['header=%r key=%s ver=0x%x tabela_comp=%d tabela=%d' % (h[:16], h[16:30].hex(), ver, cs, us)]
heads = collections.Counter(); fl_bad = collections.Counter(); fl_ok = collections.Counter()
ext_bad = collections.Counter(); ext_ok = collections.Counter(); dir_bad = collections.Counter(); dir_ok = collections.Counter()
alt = collections.Counter(); examples = []
for _ in range(n):
    e = t.index(b'\0', pos); name = t[pos:e]; pos = e + 1
    c, cal, u, fl, o = struct.unpack('<IIIBI', t[pos:pos + 17]); pos += 17
    if not fl & 1: continue
    f.seek(o + 46); d = f.read(cal)
    ext = name.rsplit(b'.', 1)[-1].lower().decode('ascii', 'replace')
    top = b'\\'.join(name.split(b'\\')[:2]).decode('cp949', 'replace')
    try:
        zlib.decompress(d); fl_ok[fl] += 1; ext_ok[ext] += 1; dir_ok[top] += 1; continue
    except Exception: pass
    fl_bad[fl] += 1; ext_bad[ext] += 1; dir_bad[top] += 1; heads[d[:2].hex()] += 1
    kind = 'nenhum'
    for nm, fn in (('deflate_cru', lambda x: zlib.decompress(x, -15)), ('lzma', lambda x: lzma.decompress(x)),
                   ('lzma_alone', lambda x: lzma.decompress(x, format=lzma.FORMAT_ALONE)),
                   ('zlib_+1', lambda x: zlib.decompress(x[1:])), ('cru', lambda x: x if len(x) == u else 1 / 0)):
        try:
            r = fn(d)
            if len(r) >= u * 0.9: kind = nm; break
        except Exception: pass
    alt[kind] += 1
    if len(examples) < 25: examples.append('%s c=%d cal=%d u=%d fl=%d head=%s' % (name.decode('cp949', 'replace'), c, cal, u, fl, d[:12].hex()))
out += ['flags OK: %s' % dict(fl_ok), 'flags RUINS: %s' % dict(fl_bad), 'inicio dos ruins: %s' % heads.most_common(10),
        'outros formatos: %s' % dict(alt), 'ext ruins: %s' % ext_bad.most_common(15), 'ext ok: %s' % ext_ok.most_common(15),
        'pastas ruins: %s' % dir_bad.most_common(15), 'pastas ok: %s' % dir_ok.most_common(15), 'exemplos:'] + examples
open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
