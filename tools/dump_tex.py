"""Dump all MIG textures under DATA (dedup by hash) -> work/tex/<hash>.png, work/tex_index.json"""
import os, sys, json, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import pspc, mig
R = 'work/iso/PSP_GAME/USRDIR/DATA'
os.makedirs('work/tex', exist_ok=True)
idx = {}; n = 0; bad = 0
for dp, _, fs in os.walk(R):
    for f in sorted(fs):
        p = os.path.join(dp, f); rel = os.path.relpath(p, R).replace(os.sep, '/')
        if rel.startswith(('event_p/', 'sound/', 'MOVIE/')): continue
        d = open(p, 'rb').read()
        if d[:4] != b'PSP\0': continue
        for e in pspc.parse(d):
            if e[4] == b'MIG.' and e[3]:
                b = d[e[2]:e[2] + e[3]]; h = hashlib.md5(b).hexdigest()[:12]
                idx.setdefault(h, []).append([rel, e[2], e[3]])
                if len(idx[h]) > 1: continue
                try:
                    t, img = mig.read(b); img.save(f'work/tex/{h}.png'); n += 1
                except Exception as ex:
                    bad += 1
json.dump(idx, open('work/tex_index.json', 'w'), indent=0)
print('unique', len(idx), 'saved', n, 'bad', bad)
