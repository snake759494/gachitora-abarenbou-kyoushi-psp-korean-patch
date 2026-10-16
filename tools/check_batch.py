"""Validate a translated batch: python tools/check_batch.py NNN [NNN...]  (or 'all')"""
import json, re, sys, os, glob, collections
ROOT = os.path.join(os.path.dirname(__file__), '..')
CODE = re.compile(r'#c[0-9A-Fa-f]{6,8}|#[a-zA-Z]+[0-9.]+f|#[pqQ](?:cir|cro|squ|tri|lef|rig)(?:OK)?|#d|#k|#rf|#e|#n|%[0-9]*[ds]|\$[A-Za-z0-9_]+')
KANA = re.compile('[ぁ-ゖァ-ヺー々一-鿿]')


def vis_len(s):
    s = CODE.sub('', s)
    return sum(1 if ord(c) >= 0x1100 else 0.5 for c in s)


def check(jp, kr):
    errs = []
    if not isinstance(kr, str) or (jp.strip() and not kr.strip()):
        return ['empty']
    if KANA.search(kr):
        errs.append('japanese left: ' + ''.join(KANA.findall(kr))[:10])
    a = collections.Counter(CODE.findall(jp)); b = collections.Counter(CODE.findall(kr))
    if a != b:
        errs.append('codes %s -> %s' % (dict(a - b), dict(b - a)))
    jl = jp.split('\n'); kl = kr.split('\n')
    if len(kl) > len(jl):
        errs.append('lines %d>%d' % (len(kl), len(jl)))
    lim = max(vis_len(l) for l in jl)
    for l in kl:
        if vis_len(l) > lim + 3 and vis_len(l) > 4:
            errs.append('long line %.1f>%.1f+3: %s' % (vis_len(l), lim, l[:20]))
            break
    return errs


def run(n):
    src = json.load(open(f'{ROOT}/trans/batches/b{n}.json', encoding='utf-8'))
    p = f'{ROOT}/trans/out/b{n}.json'
    if not os.path.exists(p):
        print(f'b{n}: no output'); return 1
    out = json.load(open(p, encoding='utf-8'))
    bad = 0
    for e in src:
        k = str(e['id'])
        if k not in out:
            print(f'  {k}: missing'); bad += 1; continue
        er = check(e['jp'], out[k])
        if er:
            bad += 1
            print(f'  {k}: {"; ".join(er)} | {e["jp"][:30]!r} -> {out[k][:30]!r}')
    print(f'b{n}: {len(src)} strings, {bad} errors')
    return bad


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    if args == ['all']:
        args = sorted(os.path.basename(p)[1:-5] for p in glob.glob(f'{ROOT}/trans/batches/b*.json'))
    tot = sum(run(a) for a in args)
    print('total errors', tot)
