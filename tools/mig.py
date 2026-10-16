"""MIG (= GIM, magic 'MIG.00.1PSP') texture read/write for all common formats.
read(blob) -> Tex (rgba PIL image + layout info);  write(blob, tex, PIL rgba image) -> new blob (same size)
Formats: 0 RGBA5650, 1 RGBA5551, 2 RGBA4444, 3 RGBA8888, 4 INDEX4, 5 INDEX8 (palette 0-3)."""
import struct
from dataclasses import dataclass
from PIL import Image

MAGIC = b'MIG.00.1PSP\0'
BPP = {0: 16, 1: 16, 2: 16, 3: 32, 4: 4, 5: 8}


def chunks(b, start, end):
    p = start
    while p + 16 <= end:
        t, _, size, nxt, data = struct.unpack_from('<HHIII', b, p)
        yield t, p, size, nxt, data
        if t in (2, 3): yield from chunks(b, p + data, p + size)
        p += nxt if nxt else size
        if not nxt and not size: break


def find(b, kind):
    for t, p, size, nxt, data in chunks(b, 16, len(b)):
        if t == kind: return p, size, data
    return None


@dataclass
class Tex:
    fmt: int; order: int; w: int; h: int; pitch: int; rows: int
    pix_off: int; pal_fmt: int; pal_off: int; pal_n: int


def _unswz(d, pitch, rows):
    out = bytearray(pitch * rows); bw = pitch // 16; i = 0
    for by in range(0, rows, 8):
        for bx in range(bw):
            for y in range(8):
                if by + y < rows:
                    o = (by + y) * pitch + bx * 16
                    out[o:o + 16] = d[i:i + 16]
                i += 16
    return out


def _swz(d, pitch, rows):
    out = bytearray(pitch * rows); bw = pitch // 16; i = 0
    for by in range(0, rows, 8):
        for bx in range(bw):
            for y in range(8):
                if by + y < rows:
                    o = (by + y) * pitch + bx * 16
                    out[i:i + 16] = d[o:o + 16]
                i += 16
    return out


def _dec(fmt, v):
    if fmt == 0: return ((v & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v >> 11 & 31) * 255 // 31, 255)
    if fmt == 1: return ((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31, 255 if v >> 15 else 0)
    if fmt == 2: return ((v & 15) * 17, (v >> 4 & 15) * 17, (v >> 8 & 15) * 17, (v >> 12 & 15) * 17)
    return (v & 255, v >> 8 & 255, v >> 16 & 255, v >> 24 & 255)


def _enc(fmt, c):
    r, g, b, a = c
    if fmt == 0: return (r * 31 + 127) // 255 | (g * 63 + 127) // 255 << 5 | (b * 31 + 127) // 255 << 11
    if fmt == 1: return (r * 31 + 127) // 255 | (g * 31 + 127) // 255 << 5 | (b * 31 + 127) // 255 << 10 | (1 << 15 if a >= 128 else 0)
    if fmt == 2: return (r * 15 + 127) // 255 | (g * 15 + 127) // 255 << 4 | (b * 15 + 127) // 255 << 8 | (a * 15 + 127) // 255 << 12
    return r | g << 8 | b << 16 | a << 24


def info(b):
    ip, isz, idat = find(b, 4)
    h = ip + 16
    hs, _, fmt, order, w, hh, bpp, pa, ha = struct.unpack_from('<HHHHHHHHH', b, h)
    if fmt not in BPP: raise ValueError('fmt %d' % fmt)
    bpp = BPP[fmt]
    pitch = (w * bpp // 8 + pa - 1) // pa * pa
    rows = (hh + ha - 1) // ha * ha
    pix = ip + idat + struct.unpack_from('<I', b, h + 0x1C)[0]
    pf = po = pn = 0
    pc = find(b, 5)
    if pc:
        pp, psz, pdat = pc
        ph = pp + 16
        pf = struct.unpack_from('<H', b, ph + 4)[0]
        pn = struct.unpack_from('<H', b, ph + 8)[0]
        po = pp + pdat + struct.unpack_from('<I', b, ph + 0x1C)[0]
    return Tex(fmt, order, w, hh, pitch, rows, pix, pf, po, pn)


def palette(b, t):
    if not t.pal_off: return []
    sz = 4 if t.pal_fmt == 3 else 2
    return [_dec(t.pal_fmt, int.from_bytes(b[t.pal_off + i * sz:t.pal_off + i * sz + sz], 'little')) for i in range(t.pal_n)]


def read(b):
    t = info(b)
    raw = b[t.pix_off:t.pix_off + t.pitch * t.rows]
    if t.order: raw = _unswz(raw, t.pitch, t.rows)
    img = Image.new('RGBA', (t.w, t.h))
    px = img.load()
    if t.fmt in (4, 5):
        pal = palette(b, t)
        for y in range(t.h):
            row = raw[y * t.pitch:]
            for x in range(t.w):
                i = (row[x >> 1] >> (4 * (x & 1)) & 15) if t.fmt == 4 else row[x]
                px[x, y] = pal[i] if i < len(pal) else (0, 0, 0, 0)
    else:
        sz = BPP[t.fmt] // 8
        for y in range(t.h):
            for x in range(t.w):
                o = y * t.pitch + x * sz
                px[x, y] = _dec(t.fmt, int.from_bytes(raw[o:o + sz], 'little'))
    return t, img


def write(b, img, keep_palette=True):
    """Encode RGBA image back into the same texture slot (same size/format).
    Index formats are matched to the existing palette (nearest colour, alpha-weighted)."""
    t = info(b)
    img = img.convert('RGBA')
    assert img.size == (t.w, t.h), (img.size, t.w, t.h)
    px = img.load()
    raw = bytearray(t.pitch * t.rows)
    if t.fmt in (4, 5):
        pal = palette(b, t)
        cache = {}
        def near(c):
            if c in cache: return cache[c]
            best = min(range(len(pal)), key=lambda i: (pal[i][0] - c[0]) ** 2 * (c[3] + 1) + (pal[i][1] - c[1]) ** 2 * (c[3] + 1)
                       + (pal[i][2] - c[2]) ** 2 * (c[3] + 1) + (pal[i][3] - c[3]) ** 2 * 300)
            cache[c] = best; return best
        for y in range(t.h):
            for x in range(t.w):
                i = near(px[x, y])
                if t.fmt == 4: raw[y * t.pitch + (x >> 1)] |= i << (4 * (x & 1))
                else: raw[y * t.pitch + x] = i
    else:
        sz = BPP[t.fmt] // 8
        for y in range(t.h):
            for x in range(t.w):
                o = y * t.pitch + x * sz
                raw[o:o + sz] = _enc(t.fmt, px[x, y]).to_bytes(sz, 'little')
    if t.order: raw = _swz(raw, t.pitch, t.rows)
    b = bytearray(b)
    b[t.pix_off:t.pix_off + len(raw)] = raw
    return bytes(b)
