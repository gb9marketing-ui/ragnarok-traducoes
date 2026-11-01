import struct, zlib, sys
p = sys.argv[1]
f = open(p, 'rb'); h = f.read(46)
off, seed, nfiles, ver = struct.unpack('<IIII', h[30:46])
f.seek(off + 46)
csize, usize = struct.unpack('<II', f.read(8))
table = zlib.decompress(f.read(csize))
n = nfiles - seed - 7
pos = 0; entries = []
for _ in range(n):
    e = table.index(b'\0', pos)
    name = table[pos:e].decode('cp949', errors='replace'); pos = e + 1
    cs, cal, us, flags, o = struct.unpack('<IIIBI', table[pos:pos+17]); pos += 17
    entries.append((name, cs, cal, us, flags, o))
import pickle; pickle.dump(entries, open('/tmp/nmro_entries.pkl', 'wb'))
print(len(entries), 'arquivos; versao', hex(ver))
import collections
print(collections.Counter(e[4] for e in entries))
for want in sys.argv[2:]:
    for e in entries:
        if want.lower() in e[0].lower(): print(e)
