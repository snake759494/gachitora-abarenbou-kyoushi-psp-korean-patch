"""Collect every translatable string (TSB event dialogue + ZAR string tables).
writes trans/db.json   : [{"id":n,"jp":text,"src":first source}]
       work/occ.json   : occurrences for the build step
"""
import os, sys, re, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import pspc, tsb
from zar import parse_zar, is_ascii_table

ROOT = os.path.join(os.path.dirname(__file__), '..')
R = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/DATA')
JP = re.compile('[぀-ヿ一-鿿！-～、-』]')


def sources():
    ev = sorted(glob.glob(R + '/event_p/*.bin'))
    order = ['2D/CMNG.BIN', '2D/CMN.BIN']
    rest = []
    for dp, _, fs in os.walk(R):
        for f in sorted(fs):
            p = os.path.join(dp, f).replace('\\', '/')
            if '/event_p/' in p or p.endswith(('.at3', '.PMF')): continue
            rest.append(p)
    first = [R + '/' + o for o in order]
    rest = [p for p in rest if p not in first]
    return ev + first + sorted(rest)


def main():
    old = json.load(open(os.path.join(ROOT, 'trans/db.json'), encoding='utf-8')) if os.path.exists(os.path.join(ROOT, 'trans/db.json')) else []
    db = {e['jp']: e['id'] for e in old}; order = [(e['jp'], e['src']) for e in old]; occ = []
    for p in sources():
        rel = os.path.relpath(p, R).replace('\\', '/')
        d = open(p, 'rb').read()
        if d[:4] != b'PSP\0': continue
        for depth, name, off, size, magic in pspc.parse(d):
            if magic == b'TSB\0':
                t = d[off:off + size]
                for v, ps, s, e in tsb.strings(t):
                    if s not in db: db[s] = len(order); order.append((s, rel))
                    occ.append(['tsb', rel, off, v, db[s]])
            elif magic == b'ZAR\0' and size:
                z = d[off:off + size]
                try:
                    if is_ascii_table(z): continue
                    B, ss = parse_zar(z)
                except Exception as ex:
                    print('skip zar', rel, hex(off), ex); continue
                for i, l, o, s in ss:
                    if not JP.search(s) or '\0' in s: continue
                    if s not in db: db[s] = len(order); order.append((s, rel))
                    occ.append(['zar', rel, off, i, db[s]])
    os.makedirs(os.path.join(ROOT, 'trans'), exist_ok=True)
    json.dump([{'id': i, 'jp': s, 'src': r} for i, (s, r) in enumerate(order)],
              open(os.path.join(ROOT, 'trans/db.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(occ, open(os.path.join(ROOT, 'work/occ.json'), 'w'))
    print('unique', len(order), 'chars', sum(len(s) for s, _ in order), 'occurrences', len(occ))


if __name__ == '__main__':
    main()
