import struct, zlib, sys, os, pickle
def index(p):
    f = open(p, 'rb'); h = f.read(46)
    if h[:15] != b'Master of Magic': return None
    off, seed, nfiles, ver = struct.unpack('<IIII', h[30:46])
    if ver != 0x200: return ('ver', hex(ver))
    f.seek(off + 46); cs, us = struct.unpack('<II', f.read(8))
    t = zlib.decompress(f.read(cs)); n = nfiles - seed - 7; pos = 0; out = {}
    for _ in range(n):
        e = t.index(b'\0', pos); name = t[pos:e].decode('cp949', errors='replace').lower(); pos = e + 1
        c, ca, u, fl, o = struct.unpack('<IIIBI', t[pos:pos+17]); pos += 17
        out[name] = (c, ca, u, fl, o)
    return out
res = {}
for p in sys.argv[2:]:
    r = index(p); res[p] = r
    print(os.path.basename(p), 'erro' if not isinstance(r, dict) else len(r), r if not isinstance(r, dict) else '')
pickle.dump(res, open(sys.argv[1], 'wb'))
