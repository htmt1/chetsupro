"""Rebuild pattern masks using the native BCH Maya UV transform.
Usage: python build-pattern-portraits.py MODEL_JSON SHARED_PORTRAITS_JS OUTPUT_DIRECTORY
All nine patterned head masks are rebuilt; face assets are preserved. Requires numpy and Pillow.
"""
from pathlib import Path
import json,base64,io,math,sys,hashlib
import numpy as np
from PIL import Image
j=json.loads(Path(sys.argv[1]).read_text());shared=Path(sys.argv[2]).read_text().strip();res=json.loads(shared[len('window.DenpaSharedPortrait='):].rstrip(';'))
scale=res['assets']['frame']['scale'];cx,cy=res['assets']['frame']['center'];overrides={}
def project(meshes,asset,tex):
 x,y,w,h=asset['box'];ss=3;W,H=w*ss,h*ss;depth=np.full((H,W),-np.inf);value=np.zeros((H,W));coverage=np.zeros((H,W),bool)
 for mesh in meshes:
  v=np.array(mesh['vertices']);px=(128+(v[:,0]-cx)*scale-x)*ss;py=(128-(v[:,1]-cy)*scale-y)*ss;uv=v[:,3:5].copy();co=mesh.get('coord',[1,1,0,0,0]);ca,sa=math.cos(co[2]),math.sin(co[2]);uu,vv=uv[:,0].copy(),uv[:,1].copy();uv[:,0]=co[0]*(uu*ca-vv*sa+.5*sa-.5*ca+.5-co[3]);uv[:,1]=co[1]*(uu*sa+vv*ca-.5*sa-.5*ca+.5-co[4])
  for a,b,c in np.array(mesh['indices']).reshape(-1,3):
   left=max(0,int(np.floor(min(px[[a,b,c]]))));right=min(W,int(np.ceil(max(px[[a,b,c]]))));top=max(0,int(np.floor(min(py[[a,b,c]]))));bottom=min(H,int(np.ceil(max(py[[a,b,c]]))))
   if right<=left or bottom<=top:continue
   den=(py[b]-py[c])*(px[a]-px[c])+(px[c]-px[b])*(py[a]-py[c])
   if abs(den)<1e-10:continue
   Y,X=np.mgrid[top:bottom,left:right];X=X+.5;Y=Y+.5;u=((py[b]-py[c])*(X-px[c])+(px[c]-px[b])*(Y-py[c]))/den;q=((py[c]-py[a])*(X-px[c])+(px[a]-px[c])*(Y-py[c]))/den;r=1-u-q;z=u*v[a,2]+q*v[b,2]+r*v[c,2];good=(u>=0)&(q>=0)&(r>=0)&(z>depth[top:bottom,left:right]);U=(u*uv[a,0]+q*uv[b,0]+r*uv[c,0])*tex.shape[1]-.5;V=(u*uv[a,1]+q*uv[b,1]+r*uv[c,1])*tex.shape[0]-.5;ix=np.floor(U).astype(int);iy=np.floor(V).astype(int);fx=U-ix;fy=V-iy;sample=sum(tex[(iy+dy)%tex.shape[0],(ix+dx)%tex.shape[1]]*(fx if dx else 1-fx)*(fy if dy else 1-fy) for dx,dy in [(0,0),(1,0),(0,1),(1,1)])
   depth[top:bottom,left:right][good]=z[good];value[top:bottom,left:right][good]=sample[good];coverage[top:bottom,left:right][good]=True
 # White is color1, alpha is its exact bilinear weight; do not threshold stripes.
 alpha=Image.fromarray(np.uint8(np.clip(value,0,1)*255)).resize((w,h),Image.Resampling.LANCZOS);im=Image.new('RGBA',(w,h),'white');im.putalpha(alpha);b=io.BytesIO();im.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

output=Path(sys.argv[3]);output.mkdir(parents=True,exist_ok=True);(output/'portrait-images').mkdir(exist_ok=True);written=set()
def save_asset(meshes,box,tex):
 a={'box':box};raw=project(meshes,a,tex);im=Image.open(io.BytesIO(base64.b64decode(raw.split(',')[1])));im.putalpha(im.getchannel('A').point(lambda n:round(n/17)*17));im=im.quantize(colors=16,method=Image.Quantize.FASTOCTREE);buf=io.BytesIO();im.save(buf,format='PNG',optimize=True);raw=buf.getvalue();name='portrait-images/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';(output/name).write_bytes(raw);written.add(name);return {'src':name,'box':box}
for pattern in range(1,10):
 tex=np.asarray(Image.open(io.BytesIO(base64.b64decode(j['patterns'][pattern].split(',')[1]))).convert('L'))/255
 for head,meshes in enumerate(j['heads'][:40]):
  if meshes:res['details']['patterns'][head][pattern]=save_asset(meshes,res['assets']['heads'][head]['box'],tex)
 if pattern==7:res['details']['body']['patterns'][7]=save_asset(j['body'],res['details']['body']['silhouette']['box'],tex)
res['details']['sources'].pop('tigerBoundary',None);res['details']['sources']['patternProjection']='BCH Maya scale/rotation/translation matrix; bilinear repeat sampling and front depth.'
content='window.DenpaSharedPortrait='+json.dumps(res,separators=(',',':'))+';\n';name='portrait-resources.'+hashlib.sha256(content.encode()).hexdigest()[:12]+'.js';(output/name).write_text(content);written.add(name);(output/'pattern-build-files.json').write_text(json.dumps(sorted(written)));print(name,len(written))
