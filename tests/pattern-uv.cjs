const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const h=fs.readFileSync('site/birth.html','utf8'),name=h.match(/model3d\.[a-f0-9]{12}\.js/)[0],code=fs.readFileSync('site/'+name,'utf8');new vm.Script(code);
class Geometry{constructor(){this.attributes={};}setAttribute(k,v){this.attributes[k]=v;return this;}setIndex(){}computeVertexNormals(){}}
class Attribute{constructor(array,size){this.array=array;this.itemSize=size;}}
const c={hn:Geometry,Nt:Attribute,si:Attribute};vm.createContext(c);let a=code.indexOf('function Po('),b=code.indexOf('function Lo(',a);vm.runInContext(code.slice(a,b),c);
const point=(u,v,s,o)=>c.Po({vertices:[[0,0,0,u,v]],indices:[0],coord:s},o).attributes.uv.array,near=(a,b)=>assert(Math.abs(a-b)<1e-6);
let uv=point(.468859,.438949,[2,3,0,.22,.005]);near(uv[0],.497718);near(uv[1],1.301847);
uv=point(.5,.25,[2,3,Math.PI/2,.22,.005]);near(uv[0],1.06);near(uv[1],1.485);
uv=point(.3,.7,[1,1,0,0,0],[.125,-.25]);near(uv[0],.425);near(uv[1],.45);
assert(!code.includes('function denpaPatternTexture'));
const model=JSON.parse(fs.readFileSync('site/model-data.5a514a7bb403.json','utf8'));
for(const head of model.heads.filter(Boolean))for(const mesh of head){const got=c.Po(mesh).attributes.uv.array;for(let i=0;i<mesh.vertices.length;i++){near(got[i*2],(mesh.vertices[i][3]-.22)*2);near(got[i*2+1],(mesh.vertices[i][4]-.005)*3);}}
console.log('PASS native UV matrix: all source heads, rotation, unchanged atlas offsets and removal of reflected tiger override');
