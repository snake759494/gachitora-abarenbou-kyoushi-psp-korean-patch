import sys;sys.path.insert(0,'tools')
from merge_pgf_fonts import PGF
from pathlib import Path
from PIL import Image
def draw(f,text,scale=3):
    W=18*len(text)+8;img=Image.new('L',(W,26),0);x=4
    for ch in text:
        i=f.glyph_index(ord(ch))
        if i is None: x+=9;continue
        g=f.glyph(i)
        for yy in range(g.height):
            for xx in range(g.width):
                v=g.pixels[yy*g.width+xx]*17
                px,py=x+g.left+xx,20-g.top+yy
                if 0<=px<W and 0<=py<26: img.putpixel((px,py),v)
        x+=g.advance[0]//64
    return img.resize((W*scale,26*scale),Image.NEAREST)
f=PGF(Path(sys.argv[1]))
ims=[draw(f,t) for t in sys.argv[3:]]
out=Image.new('L',(max(i.width for i in ims),sum(i.height for i in ims)))
y=0
for i in ims: out.paste(i,(0,y));y+=i.height
out.save(sys.argv[2])
