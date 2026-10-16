"""ZAR string table.
header: 'ZAR\\0' + PSP sub-header; u32 at 0x14 = B (table base, 0x80 or 0xa0 ...)
at B: u32 0, u32 total records, u32 0x20 ...; records start at B+0x20, 8 bytes each:
  (u16 flag, u16 len, u32 off)  flag==0xffff -> string (len incl. NUL, UTF-16, at B+off)
                                otherwise      -> group header (id, count, index-table offset)
"""
import struct


def base(z):
    return struct.unpack_from('<I', z, 0x14)[0]


def records(z):
    B = base(z)
    total = struct.unpack_from('<I', z, B + 4)[0]
    return B, [struct.unpack_from('<HHI', z, B + 0x20 + 8 * i) for i in range(total)]


def parse_zar(z):
    """returns (B, [(record_index, len, off, text)]) for string records"""
    assert z[:4] == b'ZAR\0'
    B, recs = records(z)
    out = []
    for i, (f, l, o) in enumerate(recs):
        if f != 0xffff: continue
        raw = z[B + o:B + o + 2 * (l - 1)]
        if len(raw) < 2 * (l - 1): raise ValueError('short')
        out.append((i, l, o, raw.decode('utf-16le')))
    return B, out


def is_ascii_table(z):
    """ZAR whose strings are 1-byte ASCII (keys like 'MG_01'); len counts bytes there."""
    B, recs = records(z)
    ss = [(l, o) for f, l, o in recs if f == 0xffff]
    if not ss: return False
    for l, o in ss:
        raw = z[B + o:B + o + l]
        if l < 2 or len(raw) < l or raw[l - 1] != 0 or not all(0x20 <= c < 0x7f for c in raw[:l - 1]):
            return False
    return True


def build_zar(z, texts, slot=0x20):
    """texts: {record_index: str} for replaced strings; returns new ZAR bytes (strings re-laid at the end)."""
    B, recs = records(z)
    tbl = B + 0x20 + 8 * len(recs)
    strs = [(i, l, o) for i, (f, l, o) in enumerate(recs) if f == 0xffff]
    offs = [B + o for i, l, o in strs if B + o >= tbl]
    start = max(min(offs) if offs else len(z), tbl)
    out = bytearray(z[:start])
    for i, l, o in strs:
        t = texts.get(i)
        if t is None: t = z[B + o:B + o + 2 * (l - 1)].decode('utf-16le')
        while (len(out) - B) % slot: out.append(0)
        no = len(out) - B
        out += t.encode('utf-16le') + b'\0\0'
        struct.pack_into('<HHI', out, B + 0x20 + 8 * i, 0xffff, len(t) + 1, no)
    return bytes(out)
