"""TSB event script: UTF-16 strings that are targets of 4-byte pointers (relative to TSB start)."""
import struct,re
KANA=re.compile('[\u3041-\u30fa\u30fc]')
OK=re.compile('^[\u0020-\u007e\n\u3000-\u30ff\u4e00-\u9fff\uff01-\uff9f\u2010-\u203b\u2190-\u21ff\u2460-\u24ff\u25a0-\u266f\u00a0-\u00ff\u0391-\u03c9\u0401-\u044f\u2200-\u22ff]+$')
def ascii_pair(c):
    o=ord(c); a,b=o&0xff,o>>8
    return 0x20<=a<0x7f and 0x20<=b<0x7f
def good(s):
    if not OK.match(s): return False
    if not KANA.search(s) and not re.search('[、。！？…「」]',s): return False
    cjk=[c for c in s if ord(c)>=0x3000]
    if not cjk: return False
    han=[c for c in cjk if 0x4e00<=ord(c)<=0x9fff]
    ap=sum(ascii_pair(c) for c in han)
    if han and ap*2>len(han) and len(han)*2>len(cjk): return False
    if len(s)<2: return False
    return True
def strings(t):
    n=len(t)
    ptrs={}
    for p in range(0,n-3,4):
        v=struct.unpack_from('<I',t,p)[0]
        if 0x40<=v<n and v%2==0: ptrs.setdefault(v,[]).append(p)
    out=[]
    for v,ps in sorted(ptrs.items()):
        e=v
        while e+1<n and (t[e]|t[e+1]): e+=2
        if e==v: continue
        try: s=t[v:e].decode('utf-16le')
        except: continue
        if good(s) and not re.search(rb'[Nn]ode[0-9]',t[max(0,v-6):e+4]) : out.append((v,ps,s,e))
    # drop strings that are suffixes inside another accepted string
    starts=[(v,e) for v,_,_,e in out]
    res=[]
    for x in out:
        if any(v<x[0]<e for v,e in starts): continue
        res.append(x)
    return res

def patch_tsb(t, repl):
    """repl: {string_offset: new_text}. In place when it fits the original slot,
    else appended at the end of the TSB and every pointer to it is redirected."""
    t=bytearray(t)
    found={v:(ps,e) for v,ps,s,e in strings(bytes(t))}
    tail=bytearray()
    base=len(t)
    while base%4: base+=1; 
    for v,new in sorted(repl.items()):
        ps,e=found[v]
        cap=(e+2+3)//4*4-v
        b=new.encode('utf-16le')+b'\0\0'
        if len(b)<=cap:
            t[v:v+cap]=b+bytes(cap-len(b))
        else:
            t[v:e+2]=bytes(e+2-v)
            while len(tail)%4: tail.append(0)
            nv=base+len(tail)
            tail+=b
            for p in ps: struct.pack_into('<I',t,p,nv)
    if tail:
        t+=bytes(base-len(t))+tail
        while len(t)%0x10: t.append(0)
    return bytes(t)
