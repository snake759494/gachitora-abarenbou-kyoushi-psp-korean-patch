"""Redraw Japanese text in UI textures with Korean.
Spec file trans/images.json : list of
  {"h": "<12-hex md5 prefix>", "boxes": [ {"box":[x,y,w,h], "erase":"row"|"clear"|"col"|"none",
     "text":"...", "font":"eHv", "size":18, "fill":"#RRGGBB", "outline":"#RRGGBB", "ow":2,
     "align":"c"|"l"|"r", "dx":0, "dy":0, "sx":1.0 (horizontal squeeze/stretch), "skew":0.0, "shadow":null} ]}
python tools/imgtext.py preview  -> work/img_prev/<h>.png (before | after, 3x)
"""
import os, sys, json, glob, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import mig, pspc

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONTS = {'aLt': 'NanumSquareNeo-aLt.ttf', 'bRg': 'NanumSquareNeo-bRg.ttf', 'cBd': 'NanumSquareNeo-cBd.ttf',
         'dEb': 'NanumSquareNeo-dEb.ttf', 'eHv': 'NanumSquareNeo-eHv.ttf',
         'SB': 'SeoulHangangB.ttf', 'SEB': 'SeoulHangangEB.ttf', 'SM': 'SeoulHangangM.ttf', 'SL': 'SeoulHangangL.ttf'}


def rgb(s):
    s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + ((int(s[6:8], 16),) if len(s) == 8 else (255,))


def erase(img, box, mode):
    x0, y0, w, h = box; x1, y1 = x0 + w, y0 + h
    px = img.load(); W, H = img.size
    if mode == 'clear':
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)): px[x, y] = (0, 0, 0, 0)
    elif mode == 'row':
        for y in range(max(0, y0), min(H, y1)):
            l = px[x0 - 1, y] if x0 > 0 else (0, 0, 0, 0)
            r = px[x1, y] if x1 < W else l
            if x0 <= 0: l = r
            for x in range(max(0, x0), min(W, x1)):
                t = (x - x0 + 0.5) / w
                px[x, y] = tuple(int(l[i] * (1 - t) + r[i] * t) for i in range(4))
    elif mode == 'band':
        # horizontal banner: rebuild its top/bottom edges by interpolating the edge rows
        # found just outside the box, fill inside with the opaque row colour.
        def edges(x):
            ys = [y for y in range(H) if px[x, y][3] > 128]
            return (ys[0], ys[-1]) if ys else (None, None)
        xl, xr = max(0, x0 - 1), min(W - 1, x1)
        tl, bl = edges(xl); tr, br = edges(xr)
        if tl is None: tl, bl = tr, br
        if tr is None: tr, br = tl, bl
        clear = px[xl, 0]
        for y in range(max(0, y0), min(H, y1)):
            L, Rr = px[xl, y], px[xr, y]
            band = L if L[3] >= Rr[3] else Rr
            for x in range(max(0, x0), min(W, x1)):
                t = (x - xl) / max(1, xr - xl)
                top = tl + (tr - tl) * t; bot = bl + (br - bl) * t
                px[x, y] = band if top - 0.5 <= y <= bot + 0.5 else clear
    elif mode == 'col':
        for x in range(max(0, x0), min(W, x1)):
            u = px[x, y0 - 1] if y0 > 0 else (0, 0, 0, 0)
            d = px[x, y1] if y1 < H else u
            if y0 <= 0: u = d
            for y in range(max(0, y0), min(H, y1)):
                t = (y - y0 + 0.5) / h
                px[x, y] = tuple(int(u[i] * (1 - t) + d[i] * t) for i in range(4))
    elif isinstance(mode, str) and mode.startswith('#'):
        c = rgb(mode)
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)): px[x, y] = c


def draw_text(img, b):
    x0, y0, w, h = b['box']
    text = b['text']
    if w <= 0 or h <= 0: return
    font = ImageFont.truetype(os.path.join(ROOT, FONTS[b.get('font', 'eHv')]), b.get('size', h))
    ow = b.get('ow', 0)
    lines = text.split('\n')
    lh = b.get('lh', b.get('size', h) + 2)
    # render big then fit
    pad = ow + 4
    tw = max(int(font.getlength(l)) for l in lines) + pad * 2
    th = lh * len(lines) + pad * 2
    layer = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    asc = font.getmetrics()[0]
    for i, l in enumerate(lines):
        lx = pad + (tw - pad * 2 - font.getlength(l)) / 2 if b.get('align', 'c') == 'c' else pad
        ly = pad + i * lh
        if b.get('shadow'):
            sx, sy, sc = b['shadow']
            d.text((lx + sx, ly + sy), l, font=font, fill=rgb(sc), stroke_width=ow, stroke_fill=rgb(sc))
        d.text((lx, ly), l, font=font, fill=rgb(b.get('fill', '#ffffff')),
               stroke_width=ow, stroke_fill=rgb(b.get('outline', '#000000')) if ow else None)
    bb = layer.getbbox()
    if not bb: return
    layer = layer.crop(bb)
    sx = b.get('sx', 1.0)
    if b.get('skew'):
        k = b['skew']; extra = int(abs(k) * layer.height) + 1
        layer = layer.transform((layer.width + extra, layer.height), Image.AFFINE,
                                (1, k, -extra if k > 0 else 0, 0, 1, 0), Image.BICUBIC)
    nw = max(1, int(layer.width * sx)); nh = max(1, layer.height)
    if nw > w: nh = max(1, int(nh * w / nw)); nw = max(1, w)          # fit width
    if nh > h: nw = max(1, int(nw * h / nh)); nh = max(1, h)
    if (nw, nh) != layer.size: layer = layer.resize((nw, nh), Image.LANCZOS)
    al = b.get('align', 'c')
    px = x0 + (w - nw) // 2 if al == 'c' else (x0 if al == 'l' else x0 + w - nw)
    py = y0 + (h - nh) // 2
    img.alpha_composite(layer, (px + b.get('dx', 0), py + b.get('dy', 0)))


def render(h, spec):
    if spec.get('png'):
        return Image.open(os.path.join(ROOT, spec['png'])).convert('RGBA')
    src = glob.glob(f'{ROOT}/work/tex/{h}*.png')[0]
    img = Image.open(src).convert('RGBA')
    for b in spec['boxes']:
        if b.get('erase', 'row') != 'none': erase(img, b['box'], b.get('erase', 'row'))
    for b in spec['boxes']:
        if b.get('text'): draw_text(img, b)
    return img


def load_specs():
    out = []
    for p in [f'{ROOT}/trans/images.json'] + sorted(glob.glob(f'{ROOT}/trans/images/*.json')):
        if os.path.exists(p): out += json.load(open(p, encoding='utf-8'))
    return out


def apply_to_file(d, specs_by_hash, cache):
    """Replace every MIG leaf whose md5 prefix has a spec (same size, in place)."""
    d = bytearray(d)
    for e in pspc.parse(bytes(d)):
        if e[4] != b'MIG.' or not e[3]: continue
        blob = bytes(d[e[2]:e[2] + e[3]])
        h = hashlib.md5(blob).hexdigest()[:12]
        if h not in specs_by_hash: continue
        if h not in cache: cache[h] = mig.write(blob, render(h, specs_by_hash[h]))
        d[e[2]:e[2] + e[3]] = cache[h]
    return bytes(d)


if __name__ == '__main__':
    os.makedirs(f'{ROOT}/work/img_prev', exist_ok=True)
    only = sys.argv[2:] if len(sys.argv) > 2 else None
    for s in load_specs():
        h = s['h']
        if only and not any(h.startswith(o) for o in only): continue
        a = Image.open(glob.glob(f'{ROOT}/work/tex/{h}*.png')[0]).convert('RGBA')
        b = render(h, s)
        # show through the real encoder (palette quantisation) too
        blob = None
        W, H = a.size
        o = Image.new('RGBA', (W * 3 * 2 + 8, H * 3), (0, 120, 120, 255))
        o.alpha_composite(a.resize((W * 3, H * 3), Image.NEAREST), (0, 0))
        o.alpha_composite(b.resize((W * 3, H * 3), Image.NEAREST), (W * 3 + 8, 0))
        o.save(f'{ROOT}/work/img_prev/{h}.png')
    print('ok')


def apply_scan(d, specs_by_hash, cache):
    """Same as apply_to_file but finds MIG textures by signature (for INSTMP stage files)."""
    import re, struct
    d = bytearray(d)
    for m in re.finditer(re.escape(b'MIG.00.1PSP\0'), bytes(d)):
        o = m.start(); s = 16 + struct.unpack_from('<I', d, o + 0x14)[0]
        blob = bytes(d[o:o + s]); h = hashlib.md5(blob).hexdigest()[:12]
        if h not in specs_by_hash: continue
        if h not in cache: cache[h] = mig.write(blob, render(h, specs_by_hash[h]))
        d[o:o + s] = cache[h]
    return bytes(d)
