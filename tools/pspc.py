"""'PSP\0' container: magic, float ver, count, flag, entries (off,size)*count, then optional names"""
import struct,sys
def parse(d,base=0,depth=0,out=None,name=''):
    if out is None: out=[]
    if d[base:base+4]!=b'PSP\0':
        out.append((depth,name,base,len(d) if False else None,d[base:base+4]));return out
    cnt,flag=struct.unpack_from('<II',d,base+8)
    ents=[struct.unpack_from('<II',d,base+16+8*i) for i in range(cnt)]
    for i,(o,s) in enumerate(ents):
        out.append((depth,f'{name}/{i}',base+o,s,d[base+o:base+o+4]))
        if d[base+o:base+o+4]==b'PSP\0': parse(d,base+o,depth+1,out,f'{name}/{i}')
    return out
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    for e in parse(d):
        print('  '*e[0],e[1],hex(e[2]),e[3] and hex(e[3]),e[4])


def _path(d,leaf,base=0,acc=None):
    """list of (container_base, entry_index) from the top container down to the leaf"""
    acc=acc or []
    cnt=struct.unpack_from('<I',d,base+8)[0]
    for i in range(cnt):
        o,s=struct.unpack_from('<II',d,base+16+8*i)
        a=base+o
        if s and a==leaf: return acc+[(base,i)]
        if s and a<leaf<a+s and d[a:a+3]==b'PSP':
            r=_path(d,leaf,a,acc+[(base,i)])
            if r: return r
    return None

GROW=0x80
def apply_mods(d,mods):
    """mods: {abs_leaf_offset: new_bytes}. Grows leaves in place (inserting GROW-aligned
    space after them) and fixes offsets/sizes in every ancestor container."""
    d=bytearray(d)
    for leaf in sorted(mods,reverse=True):
        new=mods[leaf]
        path=_path(d,leaf)
        assert path, hex(leaf)
        cb,ci=path[-1]
        old=struct.unpack_from('<I',d,cb+16+8*ci+4)[0]
        if len(new)<=old:
            d[leaf:leaf+old]=new+bytes(old-len(new))
            struct.pack_into('<I',d,cb+16+8*ci+4,len(new))
            continue
        delta=(len(new)-old+GROW-1)//GROW*GROW
        d[leaf+old:leaf+old]=bytes(delta)
        d[leaf:leaf+len(new)]=new
        for depth,(b,idx) in enumerate(path):
            cnt=struct.unpack_from('<I',d,b+8)[0]
            for i in range(cnt):
                o,s=struct.unpack_from('<II',d,b+16+8*i)
                if i==idx:
                    s = len(new) if depth==len(path)-1 else s+delta
                elif b+o>leaf: o+=delta
                struct.pack_into('<II',d,b+16+8*i,o,s)
    return bytes(d)
