#!/usr/bin/env python3
"""Lista uma GRF (nome em hex | tamanho real | abre com zlib? S/N) num .txt.gz, para comparar com outras GRFs.
Uso: python3 -I listar_grf.py <arquivo.grf> <saida.txt.gz>"""
import gzip, struct, sys, zlib
f = open(sys.argv[1], 'rb'); h = f.read(46)
off, seed, nfiles, ver = struct.unpack('<IIII', h[30:46])
f.seek(off + 46); cs, us = struct.unpack('<II', f.read(8))
t = zlib.decompress(f.read(cs)); n = nfiles - seed - 7; pos = 0; out = ['#ver=0x%x key=%s' % (ver, h[16:30].hex())]
for _ in range(n):
    e = t.index(b'\0', pos); name = t[pos:e]; pos = e + 1
    c, cal, u, fl, o = struct.unpack('<IIIBI', t[pos:pos + 17]); pos += 17
    ok = '-'
    if fl & 1:
        f.seek(o + 46)
        try: ok = 'S' if len(zlib.decompress(f.read(cal))) >= u else 'N'
        except Exception: ok = 'N'
    out.append('%s|%d|%d|%s' % (name.hex(), u, fl, ok))
open(sys.argv[2], 'wb').write(gzip.compress('\n'.join(out).encode()))
print(len(out) - 1, 'arquivos;', sum(1 for l in out if l.endswith('|N')), 'nao abrem')
