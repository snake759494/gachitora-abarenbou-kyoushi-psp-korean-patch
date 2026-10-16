"""Korean title logo: letter tiles 가/치/토/라 and the combined logo (splash + letters + subtitle).
writes work/logo/*.png (used through 'png' specs in trans/images.json)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import imgtext

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONT = os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf')
YEL = (255, 242, 0, 255); BLK = (8, 8, 8, 255); RIM = (238, 232, 205, 255)
os.makedirs(f'{ROOT}/work/logo', exist_ok=True)


def glyph(ch, size, skew=0.22, ow=6):
    f = ImageFont.truetype(FONT, size)
    pad = ow + 6
    w = int(f.getlength(ch)) + pad * 2; h = size + pad * 2
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.text((pad, pad), ch, font=f, fill=RIM, stroke_width=ow + 2, stroke_fill=RIM)
    d.text((pad, pad), ch, font=f, fill=YEL, stroke_width=ow, stroke_fill=BLK)
    lay = lay.crop(lay.getbbox())
    extra = int(skew * lay.height) + 1
    lay = lay.transform((lay.width + extra, lay.height), Image.AFFINE, (1, skew, -extra, 0, 1, 0), Image.BICUBIC)
    return lay


def fit(lay, W, H):
    s = min(W / lay.width, H / lay.height)
    return lay.resize((max(1, int(lay.width * s)), max(1, int(lay.height * s))), Image.LANCZOS)


def tile(src_hash, ch, out):
    src = Image.open(f'{ROOT}/work/tex/{src_hash}.png')
    W, H = src.size
    g = fit(glyph(ch, 120), W - 2, H - 2)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    img.alpha_composite(g, ((W - g.width) // 2, (H - g.height) // 2))
    img.save(out)


def combined():
    orig = Image.open(f'{ROOT}/work/tex/0f7a0efe43a7.png').convert('RGBA')
    splash = Image.open(f'{ROOT}/work/tex/1b04756cc0cc.png').convert('RGBA')
    W, H = orig.size
    a = np.array(orig)
    # subtitle position: template match of the subtitle texture
    sub = np.array(Image.open(f'{ROOT}/work/tex/47a83a988958.png').convert('RGBA')).astype(int)
    best = None
    for y in range(H - sub.shape[0]):
        for x in range(W - sub.shape[1]):
            blk = a[y:y + sub.shape[0], x:x + sub.shape[1]].astype(int)
            m = sub[..., 3] > 200
            e = np.abs(blk[m][:, :3] - sub[m][:, :3]).mean()
            if best is None or e < best[0]: best = (e, x, y)
    _, sx, sy = best
    print('subtitle at', sx, sy, round(best[0], 1))
    new = orig.copy()
    sp = splash.load(); npx = new.load()
    for y in range(30, 178):
        for x in range(0, 254):
            if sx - 2 <= x and sy - 2 <= y: continue          # subtitle area
            npx[x, y] = sp[x, y] if x < splash.width else (0, 0, 0, 0)
    x = 10
    for ch, w in zip('가치토라', (78, 70, 66, 86)):
        g = fit(glyph(ch, 140), w, 112)
        new.alpha_composite(g, (x, 44 + (112 - g.height) // 2)); x += w - 14
    subk = imgtext.render('47a83a988958', next(s for s in imgtext.load_specs() if s['h'] == '47a83a988958'))
    new.alpha_composite(subk, (sx, sy))
    new.save(f'{ROOT}/work/logo/combined.png')


if __name__ == '__main__':
    for h, ch in (('7245bee75c27', '가'), ('0a07db3a1b60', '치'), ('95927cd8e812', '토'), ('fb104d3b1772', '라')):
        tile(h, ch, f'{ROOT}/work/logo/{h}.png')
    combined()
