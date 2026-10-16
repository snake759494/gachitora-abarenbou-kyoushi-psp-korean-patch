"""Contact sheet of textures from one DATA file: python tools/sheet.py 2D/TITLE.BIN out.png [maxw]"""
import sys, json
from PIL import Image, ImageDraw
idx = json.load(open('work/tex_index.json'))
src = sys.argv[1]; out = sys.argv[2]; W = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
hs = []
if src.startswith('@'):
    sel = [l.strip() for l in open(src[1:]) if l.strip()]
    a, b = (int(x) for x in sys.argv[4].split(':')) if len(sys.argv) > 4 else (0, len(sel))
    hs = list(enumerate(sel[a:b]))
else:
  for h, occ in idx.items():
    if any(o[0] == src for o in occ): hs.append((min(o[1] for o in occ if o[0] == src), h))
hs.sort()
ims = []
for _, h in hs:
    im = Image.open(f'work/tex/{h}.png').convert('RGBA')
    if im.width < 16 and im.height < 16: continue
    sc = min(1.0, 300 / max(im.width, im.height))
    if sc < 1: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))))
    ims.append((h, im))
x = y = rowh = 0; pos = []
for h, im in ims:
    if x + im.width > W: x = 0; y += rowh + 14; rowh = 0
    pos.append((h, im, x, y)); x += im.width + 6; rowh = max(rowh, im.height)
H = y + rowh + 14
sheet = Image.new('RGBA', (W, max(H, 20)), (60, 60, 90, 255))
d = ImageDraw.Draw(sheet)
for h, im, x, y in pos:
    bg = Image.new('RGBA', im.size, (40, 40, 40, 255)); bg.alpha_composite(im)
    sheet.paste(bg, (x, y + 12)); d.text((x, y), h[:6], fill=(255, 255, 0, 255))
sheet.save(out)
print(len(pos), sheet.size)
