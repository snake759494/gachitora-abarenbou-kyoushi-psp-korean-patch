"""Build the Korean ISO.
  python tools/build.py [--out PATH]
Reads trans/db.json + trans/out/*.json, patches TSB event scripts and ZAR string tables,
EBOOT (font from disc), FONT.PGF (jpn0 + Hangul), PARAM.SFO, image overrides, and writes the ISO."""
import os, sys, json, glob, struct, argparse, collections, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import pspc, tsb, isobuild, eboot_patch, imgtext
from zar import parse_zar, build_zar

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ISO = os.path.join(ROOT, 'Gachitora! Abarenbou Kyoushi in High School (Japan).iso')
OUT = os.path.join(ROOT, 'Gachitora! Abarenbou Kyoushi in High School (Korean).iso')
DATA = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/DATA')


def load_trans():
    db = json.load(open(f'{ROOT}/trans/db.json', encoding='utf-8'))
    tr = {}
    for p in sorted(glob.glob(f'{ROOT}/trans/out/b*.json')):
        for k, v in json.load(open(p, encoding='utf-8')).items():
            tr[int(k)] = v
    fix = f'{ROOT}/trans/fix.json'          # manual overrides {jp: kr}
    over = json.load(open(fix, encoding='utf-8')) if os.path.exists(fix) else {}
    out = {}
    for e in db:
        v = over.get(e['jp'], tr.get(e['id']))
        if v is not None: out[e['id']] = v
    return db, out


def patch_files(db, tr):
    occ = json.load(open(f'{ROOT}/work/occ.json'))
    per = collections.defaultdict(lambda: collections.defaultdict(dict))
    for kind, rel, leaf, key, sid in occ:
        if sid in tr: per[rel][(kind, leaf)][key] = tr[sid]
    res = {}
    for rel, leaves in per.items():
        d = open(f'{DATA}/{rel}', 'rb').read()
        size = {e[2]: e[3] for e in pspc.parse(d) if e[3]}
        mods = {}
        for (kind, leaf), rep in leaves.items():
            blob = d[leaf:leaf + size[leaf]]
            if kind == 'tsb':
                mods[leaf] = tsb.patch_tsb(blob, rep)
            else:
                mods[leaf] = build_zar(blob, rep)
        res[rel] = pspc.apply_mods(d, mods)
    return res


def param_sfo(d):
    d = bytearray(d)
    kt, dt, n = struct.unpack_from('<III', d, 8)
    for i in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', d, 0x14 + 16 * i)
        key = d[kt + ko:d.index(b'\0', kt + ko)]
        if key == b'TITLE':
            t = '가치토라! ~폭주 교사 in High School~'.encode('utf-8') + b'\0'
            assert len(t) <= mx
            d[dt + do:dt + do + mx] = t + bytes(mx - len(t))
            struct.pack_into('<I', d, 0x14 + 16 * i + 4, len(t))
    return bytes(d)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    db, tr = load_trans()
    print('translated', len(tr), '/', len(db))
    files = patch_files(db, tr)
    used = ''.join(tr.values()) + ''.join(json.load(open(f'{ROOT}/trans/eboot_kr.json', encoding='utf-8')).values()) + ''.join(c for c in eboot_patch.INLINE.values() if isinstance(c, str))
    txt = f'{ROOT}/work/used_chars.txt'
    open(txt, 'w', encoding='utf-8').write(used)
    font = f'{ROOT}/work/FONT.PGF'
    subprocess.run([sys.executable, f'{ROOT}/tools/build_font.py', txt, font, 'NanumSquareNeo-cBd.ttf', '18'], check=True)
    if os.path.exists(a.out): os.remove(a.out)
    iso = isobuild.Iso(ISO, a.out)
    st = collections.Counter()
    specs = {sp['h']: sp for sp in imgtext.load_specs()}
    idx = json.load(open(f'{ROOT}/work/tex_index.json'))
    imgfiles = {o[0] for h in specs if h in idx for o in idx[h] if not o[0].startswith('INSTMP/')}
    cache = {}
    for rel in sorted(imgfiles):
        d = files.get(rel) or open(f'{DATA}/{rel}', 'rb').read()
        files[rel] = imgtext.apply_to_file(d, specs, cache)
    print('textures', len(cache), 'in', len(imgfiles), 'files')
    stgfiles = sorted({o[0] for h in specs if h in idx for o in idx[h] if o[0].startswith('INSTMP/')})
    for rel in stgfiles:
        d = open(f'{ROOT}/work/instmp/' + rel[7:], 'rb').read()
        st[iso.replace('/PSP_GAME/USRDIR/' + rel, imgtext.apply_scan(d, specs, cache))] += 1
    print('stage files', len(stgfiles))
    for rel, d in sorted(files.items()):
        st[iso.replace('/PSP_GAME/USRDIR/DATA/' + rel, d)] += 1
    elf = eboot_patch.patch(open(f'{ROOT}/work/eboot_dec.elf', 'rb').read())
    elf, bad = eboot_patch.patch_text(elf, json.load(open(f'{ROOT}/work/eboot_u16.json', encoding='utf-8')),
                                      json.load(open(f'{ROOT}/trans/eboot_kr.json', encoding='utf-8')))
    if bad: print('EBOOT text too long:', len(bad))
    elf = eboot_patch.patch_inline(elf)
    elf = eboot_patch.patch_paths(elf)
    iso.replace('/PSP_GAME/SYSDIR/EBOOT.BIN', elf)
    iso.replace('/PSP_GAME/SYSDIR/BOOT.BIN', elf)
    iso.replace('/PSP_GAME/PARAM.SFO', param_sfo(open(f'{ROOT}/work/iso/PSP_GAME/PARAM.SFO', 'rb').read()))
    iso.add('/PSP_GAME/USRDIR', 'FONT.PGF', open(font, 'rb').read())
    iso.close()
    print('files', dict(st), '->', a.out, os.path.getsize(a.out))


if __name__ == '__main__':
    main()
