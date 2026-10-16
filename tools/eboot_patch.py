"""Make the game load its font from disc instead of flash0 jpn0.pgf.
sceFontOpen(lib, 0, mode, &err) -> sceFontOpenUserFile(lib, "disc0:/PSP_GAME/USRDIR/FONT.PGF", mode, &err)
The lui/addiu at 0x21af78/0x21af80 carry HI16/LO16 relocations, so the new code keeps
a lui/addiu pair at exactly those addresses and only rewrites their immediates/registers."""
import struct
OFF=0xa0                      # file offset of vaddr 0
PATH=b'disc0:/PSP_GAME/USRDIR/FONT.PGF\0'
STR_VA=0x2aa5d8               # "sceFontDoneLib() Error : 0x%x" + following error strings (56 bytes)
def ins(d,va,w): struct.pack_into('<I',d,OFF+va,w)
def patch(d):
    d=bytearray(d)
    assert struct.unpack_from('<I',d,OFF+0x21af5c)[0]==0x0c000000|(0x287510>>2)
    # NID table entry for the stub at 0x287510 (7th import of sceLibFont)
    nid_off=0x287e3c+OFF+6*4
    assert struct.unpack_from('<I',d,nid_off)[0]==0xA834319D
    struct.pack_into('<I',d,nid_off,0x57FCB733)
    assert d[OFF+STR_VA:OFF+STR_VA+14]==b'sceFontDoneLib'
    d[OFF+STR_VA:OFF+STR_VA+len(PATH)]=PATH
    hi=(STR_VA+0x8000)>>16; lo=(STR_VA-(hi<<16))&0xffff
    orig_hi=struct.unpack_from('<I',d,OFF+0x21af78)[0]
    assert orig_hi==0x3c04002b, hex(orig_hi)
    # 0x21af5c/0x21af7c carry R_MIPS_26 relocs (keep j/jal there), 0x21af78/80 HI16/LO16.
    assert struct.unpack_from('<I',d,OFF+0x21af50)[0]>>16==0x1225   # beq s1,a1,0x21afb8
    code={0x21af50:0x16250009,   # bne  s1,a1,0x21af78 (valid slot -> set up path)
          0x21af54:0x02403025,   # move a2,s2          (delay slot)
          0x21af58:0,            # nop (only reached when no free slot)
          #  0x21af5c jal stub / 0x21af60 move a3,sp / 0x64-0x6c unchanged
          0x21af70:0x10000006,   # b    0x21af8c       (skip error path)
          #  0x21af74 sw v0,8(s2) unchanged (delay slot)
          0x21af78:0x3c050000|hi,          # lui  a1,hi     (reloc HI16)
          0x21af7c:0x08000000|(0x21af5c>>2),# j    0x21af5c  (reloc R26)
          0x21af80:0x24a50000|lo}          # addiu a1,a1,lo (reloc LO16, delay slot)
    for va,w in code.items(): ins(d,va,w)
    return bytes(d)
if __name__=='__main__':
    import sys
    open(sys.argv[2],'wb').write(patch(open(sys.argv[1],'rb').read()))


def patch_text(d, entries, kr):
    """entries: [{'off','jp','cap'}] (file offsets); writes Korean UTF-16 in place when it fits."""
    d = bytearray(d); bad = []
    for e in entries:
        t = kr.get(e['jp'])
        if not t: continue
        if len(t) > e['cap']:
            bad.append((e['jp'], t, e['cap'])); continue
        o = e['off']
        d[o:o + 2 * (e['cap'] + 1)] = t.encode('utf-16le') + bytes(2 * (e['cap'] + 1 - len(t)))
    return bytes(d), bad


# Inline UTF-16 strings that the code builds on the stack with "ori rX,zero,char" + "sh".
# value 0 = string terminator (shortens the string).  Registers are reused between strings,
# so every replacement below was chosen to read correctly in all strings sharing it.
INLINE = {
    # fishing stats: 飛距離 / 安定性 / 飛距離補正 / 巻取り速度 / ％
    0xa1c8: '비', 0xa1cc: '거', 0xa1d4: '리', 0xa1e0: '안', 0xa1e8: '정', 0xa1f0: '성',
    0xa208: '보', 0xa210: '정', 0xa21c: '감', 0xa224: '기', 0xa22c: '속', 0xa234: '도', 0xa23c: 0,
    0x149c14: '비', 0x149c18: '거', 0x149c20: '리', 0x149c2c: '안', 0x149c34: '정', 0x149c3c: '성',
    0x149c48: '감', 0x149c50: '기', 0x149c58: '속', 0x149c60: '도', 0x149c68: 0,
    0x149c74: '길', 0x149c7c: '이', 0x149c88: '무', 0x149c90: '게',
    # 校門 / 飛び降りて
    0xd1b20: '교', 0xd1b24: '문', 0xd1b30: '뛰', 0xd1b38: '어', 0xd1b40: '내', 0xd1b48: '려', 0xd1b50: 0,
    0xee1b0: '회', 0xf44ac: '엔', 0x135de0: '엔', 0x167b18: '엔',
    0x125b24: '특', 0x125b2c: '별', 0x125b34: '수', 0x125b3c: '당',
    # 話 / ～ / 最終(話)
    0x12f2a8: '화', 0x12f2bc: '최', 0x12f2c4: '종',
    # 融資可能金額 / 今回の利息金額 / 借入れ金額 / 月の利息金額
    0x152068: '대', 0x15206c: '출', 0x152074: '가', 0x15207c: '능', 0x152084: '금', 0x15208c: '액',
    0x1520a0: '이', 0x1520a8: '번', 0x1520b0: ' ', 0x1520b8: '이', 0x1520c0: '자',
    0x1520d4: '차', 0x1520dc: '입', 0x1520e4: ' ', 0x1520f8: '월',
    # 名前 / 性別 / 年齢 / 職業, 男 / 女
    0x15bef0: '이', 0x15bef4: '름', 0x15bf00: '성', 0x15bf08: '별', 0x15bf14: '나', 0x15bf1c: '이',
    0x15bf28: '직', 0x15bf30: '업', 0x15c8c4: '남', 0x15c8cc: '여',
    # 着信: / 通話中:
    0x1614cc: '수', 0x1614d0: '신', 0x161664: '통', 0x161668: '화', 0x161670: '중',
    # PV 喧嘩番長5 / PV 侍道4
    0x16a9bc: '켄', 0x16a9c4: '카', 0x16a9cc: '반', 0x16a9d4: '초', 0x16aa20: 'S', 0x16aa28: 'D',
    0x17e224: '수', 0x17e228: '락', 0x17e230: '중',
}


def patch_inline(d):
    d = bytearray(d)
    for va, ch in INLINE.items():
        w = struct.unpack_from('<I', d, OFF + va)[0]
        assert w >> 26 == 0x0d and (w >> 21) & 31 == 0, hex(va)
        v = ord(ch) if isinstance(ch, str) else ch
        struct.pack_into('<I', d, OFF + va, (w & 0xffff0000) | v)
    return bytes(d)


def patch_paths(d):
    """Read the plain INSTMP copies instead of the PGD-encrypted INSDIR files (same length)."""
    return d.replace(b'INSDIR/', b'INSTMP/')
