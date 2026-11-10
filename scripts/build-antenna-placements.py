"""Keep the visible antenna above the head silhouette in the shared camera.

Usage: python build-antenna-placements.py SITE_DIRECTORY
Requires Pillow. Reads the existing transparent native-model portraits; does not
alter their pixels, meshes, textures, animations, or original attachment anchors.
The part below the antenna's local root is intentionally allowed into the head.
"""
from pathlib import Path
from PIL import Image
import hashlib,json,math,re,sys

def content_name(prefix,text):
    return prefix+'.'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.js'

def column_edges(root,asset,bottom=False,above_root=False):
    x,y,w,h=asset['box'];alpha=Image.open(root/asset['src']).convert('RGBA').getchannel('A')
    result={}
    for col in range(w):
        rows=[row for row in range(h) if alpha.getpixel((col,row))>=64 and (not above_root or y+row+.5<=128)]
        if rows:result[x+col]=y+(rows[-1] if bottom else rows[0])+.5
    return result

def main(root):
    index=(root/'index.html').read_text()
    old_resource=re.search(r'portrait-resources\.[a-f0-9]{12}\.js',index)[0]
    raw=(root/old_resource).read_text();resource=json.loads(raw[len('window.DenpaSharedPortrait='):].rstrip(';\n'))
    assets,details=resource['assets'],resource['details'];scale=assets['frame']['scale'];cy=assets['frame']['center'][1]
    birth=(root/'birth.html').read_text()
    base_match=re.search(r'\[0\.6473, 0\.579[^\]]+\]\[p.head_id\]',birth)
    if not base_match:raise ValueError('Expected original antenna placement table')
    base_expr=base_match[0];base=json.loads(base_expr.split('][p.head_id]')[0]+']')
    heads=[column_edges(root,head) if head else {} for head in assets['heads']]
    lifts={};checked=0
    for key,asset in details['variants'].items():
        if asset.get('empty'):continue
        edges=column_edges(root,asset,bottom=True,above_root=True);overrides={}
        for head,top in enumerate(heads):
            anchor=details['anchors'][head] if head<len(details['anchors']) else None
            if not anchor:continue
            checked+=1;required=base[head];dx=anchor[0]*scale
            for col,bottom in edges.items():
                target=col+dx
                columns=range(math.ceil(target-.51),math.floor(target+.51)+1)
                ceilings=[top[c] for c in columns if c in top]
                if ceilings:required=max(required,(bottom-min(ceilings)+.6)/scale-anchor[1]+cy)
            if required>base[head]+.0001:overrides[str(head)]=math.ceil(required*10000)/10000
        if overrides:lifts[key]=overrides
    details['antennaLift']=lifts
    details['sources']['antennaPlacement']='Native alpha silhouettes; lift only when the visible part above the antenna root is occluded. Root and hanging parts retain their original placement.'
    output='window.DenpaSharedPortrait='+json.dumps(resource,separators=(',',':'))+';\n'
    resource_name=content_name('portrait-resources',output);(root/resource_name).write_text(output)
    lookup='(details.antennaLift?.[stage.asset || (stage.model+":"+(stage.icon||0))]?.[p.head_id] ?? '+base_expr+')'
    for name in ['birth.html','basic.html','geki.html']:
        text=(root/name).read_text();assert text.count(base_expr)==2,name
        (root/name).write_text(text.replace(base_expr,lookup))
    birth=(root/'birth.html').read_text();old_model=re.search(r'model3d\.[a-f0-9]{12}\.js',birth)[0];code=(root/old_model).read_text()
    old3d=base_expr.replace('[p.head_id]','[e.head_id]')+'||0'
    assert code.count(old3d)==1
    code=code.replace('async function Wg(', 'const antennaLifts='+json.dumps(lifts,separators=(',',':'))+';\nasync function Wg(',1)
    code=code.replace(old3d,'(antennaLifts[n.model+":"+(n.icon||0)]?.[e.head_id] ?? '+old3d.replace('||0',' ?? 0')+')',1)
    model_name=content_name('model3d',code);(root/model_name).write_text(code)
    (root/'birth.html').write_text(birth.replace(old_model,model_name))
    (root/'index.html').write_text(index.replace(old_resource,resource_name).replace('1.0.7','1.0.8'))
    print(json.dumps({'checked':checked,'adjusted':sum(len(v) for v in lifts.values()),'resource':resource_name,'model':model_name}))

if __name__=='__main__':main(Path(sys.argv[1]))
