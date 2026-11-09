"""Convert the supported SPBD v0x33 aura emitters to a browser playback asset.
Input: directory from inspect-aura-effects.py. Output: JSON.
Source ETC1 textures and numeric parameters are preserved. The browser implements a
limited billboard particle interpreter; this is not the game's full shader/curve VM.
"""
import base64, hashlib, io, json, struct, sys
from pathlib import Path
from PIL import Image

mods=[[2,8,-2,-8],[5,17,-5,-17],[9,29,-9,-29],[13,42,-13,-42],[18,60,-18,-60],[24,80,-24,-80],[33,106,-33,-106],[47,183,-47,-183]]
def decode_etc1(raw,w,h):
 out=Image.new('RGB',(w,h));pix=out.load()
 def signed(v):return v-8 if v>=4 else v
 for y in range(h):
  for x in range(w):
   block=((y//8)*(w//8)+x//8)*4+(x%8//4)+(y%8//4)*2;q=int.from_bytes(raw[block*8:block*8+8],'little');diff=q>>33&1;flip=q>>32&1;xx=x%4;yy=y%4;sub=(yy>=2) if flip else (xx>=2)
   if diff:
    a=[q>>59&31,q>>51&31,q>>43&31];b=[a[0]+signed(q>>56&7),a[1]+signed(q>>48&7),a[2]+signed(q>>40&7)];rgb=[((v<<3)|(v>>2)) for v in (b if sub else a)]
   else:rgb=[(q>>(56 if sub else 60)&15)*17,(q>>(48 if sub else 52)&15)*17,(q>>(40 if sub else 44)&15)*17]
   table=q>>(34 if sub else 37)&7;bit=xx*4+yy;idx=(q>>bit&1)|((q>>(bit+16)&1)<<1);v=mods[table][idx];pix[x,h-1-y]=tuple(max(0,min(255,c+v)) for c in rgb)
 return out

FILES=['fx_e_aura_l1.ptcl','fx_e_aura_l3.ptcl','fx_c01_aura.ptcl']
def convert(path):
 b=path.read_bytes()
 def u(off):return struct.unpack_from('<I',b,off)[0]
 def f(off):return struct.unpack_from('<f',b,off)[0]
 if b[:4]!=b'SPBD' or u(4)!=0x33:raise ValueError('Unsupported particle version')
 texture_start,texture_length=u(0x14),u(0x18)
 if texture_start+texture_length>len(b):raise ValueError('Truncated textures')
 count=u(0x58);emitters=[]
 for i in range(count):
  off=u(0x64+8*i)
  if off+0x548>texture_start:raise ValueError('Emitter outside resource section')
  width,height=struct.unpack_from('<HH',b,off+0x40);size,offset=u(off+0xb0),u(off+0xb4)
  if u(off+0xac)!=0x13 or size!=width*height//2 or offset+size>texture_length:raise ValueError('Unsupported texture layout')
  raw=b[texture_start+offset:texture_start+offset+size]
  # PICA ETC1 blocks in 8x8 macrotiles. A black background is the
  # coverage channel for these native additive, monochrome effect textures.
  im=decode_etc1(raw,width,height)
  alpha=im.convert('L');im=Image.new('RGBA',(width,height),'white');im.putalpha(alpha)
  png=io.BytesIO();im.save(png,format='PNG')
  label_offset=u(0x10)+u(off+0x38);label=b[label_offset:b.find(b'\0',label_offset)].decode('ascii')
  emitters.append(dict(name=label,texture='data:image/png;base64,'+base64.b64encode(png.getvalue()).decode(),width=width,height=height,sourceOffset=off,
   spread=[f(off+0x254+j*4) for j in range(3)],origin=[f(off+0x21c+j*4) for j in range(3)],scale=[f(off+0x208+j*4) for j in range(3)],
   rate=f(off+0x2c4),startFrame=u(off+0x2c8),endFrame=u(off+0x2cc),interval=u(off+0x2d4),
   lifeFrames=u(off+0x31c),lifeVariation=u(off+0x320),velocity=[f(off+0x2d8+j*4) for j in range(3)],
   colors=[[f(off+0x430+j*16+k*4) for k in range(4)] for j in range(3)],
   sizes=[f(off+0x4e4+j*4) for j in range(4)],rotation=[f(off+0x510),f(off+0x51c)]))
 return dict(source=path.name,sha256=hashlib.sha256(b).hexdigest(),version=0x33,emitters=emitters)
if __name__=='__main__':
 result=dict(schema='denpa-native-aura/1',fps=30,limits='Decoded ETC1 sprites, colors and emitter parameters; billboard motion is an approximation, not the original SPBD curve/shader engine.',effects=[dict(id=str(i+1),label='オーラ'+str(i+1),**convert(Path(sys.argv[1])/name)) for i,name in enumerate(FILES)])
 Path(sys.argv[2]).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
 print('Converted',sum(len(x['emitters']) for x in result['effects']),'emitters from',len(FILES),'native files')
