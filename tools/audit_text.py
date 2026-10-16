"""Find UTF-16 Japanese strings in DATA files that the extractor does not cover."""
import os, sys, re, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import pspc, tsb
from zar import parse_zar, is_ascii_table

R = 'work/iso/PSP_GAME/USRDIR/DATA'
JPR = re.compile('[ぁ-んァ-ン]{2}|[一-鿿]{2}')
out = []
for dp, _, fs in os.walk(R):
    for f in fs:
        if f.endswith(('.at3', '.PMF')): continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, R).replace(os.sep, '/')
        d = open(p, 'rb').read()
        cov = []
        if d[:4] == b'PSP\0':
            for e in pspc.parse(d):
                if not e[3]: continue
                if e[4] == b'ZAR\0':
                    cov.append((e[2], e[2] + e[3]))          # whole ZAR handled (strings or keys)
                elif e[4] == b'TSB\0':
                    t = d[e[2]:e[2] + e[3]]
                    for v, ps, s, en in tsb.strings(t): cov.append((e[2] + v, e[2] + en))
                elif e[4] == b'MIG.':
                    cov.append((e[2], e[2] + e[3]))
        cov.sort()
        def covered(o):
            for a, b in cov:
                if a <= o < b: return True
            return False
        i = 0; n = len(d)
        while i < n - 2:
            if d[i] == 0 and d[i + 1] == 0: i += 2; continue
            j = i
            while j < n - 1 and (d[j] or d[j + 1]): j += 2
            try:
                s = d[i:j].decode('utf-16le')
                if tsb.OK.match(s) and JPR.search(s) and len(s) >= 2 and not covered(i):
                    out.append((rel, i, s))
            except Exception:
                pass
            i = j + 2
c = collections.Counter(r for r, _, _ in out)
print(len(out)); print(c.most_common(30))
json.dump(out, open('work/audit_text.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
