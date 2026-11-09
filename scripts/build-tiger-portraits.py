"""Rebuild tiger masks with the same reflected UV boundary as the renderer.
Usage: python build-tiger-portraits.py MODEL_JSON SHARED_PORTRAITS_JS OUTPUT_JS
Other patterns and face assets are preserved. Requires numpy and Pillow.
"""
from pathlib import Path
import json,base64,io,math,sys,hashlib
import numpy as np
from PIL import Image
j=json.loads(Path(sys.argv[1]).read_text());shared=Path(sys.argv[2]).read_text().strip();res=json.loads(shared[len('window.DenpaSharedPortrait='):].rstrip(';'));tex=np.array(Image.open(io.BytesIO(base64.b64decode(j['patterns'][7].split(',')[1]))).convert('L'))/255
scale=res['assets']['frame']['scale'];cx,cy=res['assets']['frame']['center'];overrides={}
def mirror(i,n):
 v=i%(2*n);return np.where(v<n,v,2*n-1-v)
def project(meshes,asset):
 x,y,w,h=asset['box'];ss=3;W,H=w*ss,h*ss;depth=np.full((H,W),-np.inf);value=np.zeros((H,W));coverage=np.zeros((H,W),bool)
 for mesh in meshes:
  v=np.array(mesh['vertices']);px=(128+(v[:,0]-cx)*scale-x)*ss;py=(128-(v[:,1]-cy)*scale-y)*ss;uv=v[:,3:5].copy();co=mesh.get('coord',[1,1,0,0,0]);uv*=co[:2];rot=np.array([[math.cos(co[2]),-math.sin(co[2])],[math.sin(co[2]),math.cos(co[2])]]);uv=uv@rot.T+co[3:5]
  for a,b,c in np.array(mesh['indices']).reshape(-1,3):
   left=max(0,int(np.floor(min(px[[a,b,c]]))));right=min(W,int(np.ceil(max(px[[a,b,c]]))));top=max(0,int(np.floor(min(py[[a,b,c]]))));bottom=min(H,int(np.ceil(max(py[[a,b,c]]))))
   if right<=left or bottom<=top:continue
   den=(py[b]-py[c])*(px[a]-px[c])+(px[c]-px[b])*(py[a]-py[c])
   if abs(den)<1e-10:continue
   Y,X=np.mgrid[top:bottom,left:right];X=X+.5;Y=Y+.5;u=((py[b]-py[c])*(X-px[c])+(px[c]-px[b])*(Y-py[c]))/den;q=((py[c]-py[a])*(X-px[c])+(px[a]-px[c])*(Y-py[c]))/den;r=1-u-q;z=u*v[a,2]+q*v[b,2]+r*v[c,2];good=(u>=0)&(q>=0)&(r>=0)&(z>depth[top:bottom,left:right]);U=(u*uv[a,0]+q*uv[b,0]+r*uv[c,0])*tex.shape[1]-.5;V=(u*uv[a,1]+q*uv[b,1]+r*uv[c,1])*tex.shape[0]-.5;ix=np.floor(U).astype(int);iy=np.floor(V).astype(int);fx=U-ix;fy=V-iy;sample=sum(tex[mirror(iy+dy,tex.shape[0]),mirror(ix+dx,tex.shape[1])]*(fx if dx else 1-fx)*(fy if dy else 1-fy) for dx,dy in [(0,0),(1,0),(0,1),(1,1)])
   depth[top:bottom,left:right][good]=z[good];value[top:bottom,left:right][good]=sample[good];coverage[top:bottom,left:right][good]=True
 # White is color1, alpha is its exact bilinear weight; do not threshold stripes.
 alpha=Image.fromarray(np.uint8(np.clip(value,0,1)*255)).resize((w,h),Image.Resampling.LANCZOS);im=Image.new('RGBA',(w,h),'white');im.putalpha(alpha);b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()
for idx,meshes in enumerate(j['heads'][:40]):
 if not meshes:continue
 asset=res['details']['patterns'][idx][7];overrides[str(idx)]={**asset,'src':project(meshes,asset)}
b=res['details']['body']['patterns'][7];body={**b,'src':project(j['body'],b)}
for a in [*overrides.values(),body]:
 im=Image.open(io.BytesIO(base64.b64decode(a['src'].split(',')[1])));im.putalpha(im.getchannel('A').point(lambda x:round(x/17)*17));im=im.quantize(colors=16,method=Image.Quantize.FASTOCTREE);buf=io.BytesIO();im.save(buf,format='PNG',optimize=True);a['src']='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
for id,mask in overrides.items():res['details']['patterns'][int(id)][7]=mask
res['details']['body']['patterns'][7]=body
res['details']['sources']['tigerBoundary']='Reflected repeat at UV tile boundaries, shared with the 3D and software renderers.'
Path(sys.argv[3]).write_text('window.DenpaSharedPortrait='+json.dumps(res,separators=(',',':'))+';\n')
print('Projected tiger masks:',len(overrides),'heads + body')
