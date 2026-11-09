const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const files=fs.readdirSync('site'),birth=fs.readFileSync('site/birth.html','utf8'),name=birth.match(/model3d\.[a-f0-9]{12}\.js/)[0],code=fs.readFileSync('site/'+name,'utf8');new vm.Script(code);
const start=code.indexOf('const nativeAuraData='),end=code.indexOf('async function Xg(',start);assert(start>=0&&end>start);
class Object3D{constructor(){this.children=[];this.scale={set:(...v)=>{this.scales=v;}};this.position={set:(...v)=>{this.positions=v;}};this.quaternion={copy(){}};}add(x){this.children.push(x);}remove(x){this.children=this.children.filter(c=>c!==x);}rotateZ(){}setAttribute(){return this;}setIndex(){}computeVertexNormals(){}}
class Material{constructor(x){Object.assign(this,x);this.color={setRGB:(...c)=>this.rgb=c};this.emissive={setRGB(){}};}}
class Mesh extends Object3D{constructor(g,m){super();this.geometry=g;this.material=m;}}
const ctx={Zt:Object3D,hn:Object3D,Nt:class{},St:Mesh,Ts:Material,Ft:2,Uh:async src=>({src}),Fh:image=>({image}),yc:()=>{},console};vm.createContext(ctx);vm.runInContext(code.slice(start,end)+';this.data=nativeAuraData;this.create=createNativeAuraPlayer;',ctx);
(async()=>{const scene=new Object3D(),player=ctx.create(scene,{quaternion:{}},()=>{},()=>({scaleX:1,scaleY:1}));
 assert.equal(ctx.data.effects.length,3);
 for(const effect of ctx.data.effects){assert.match(effect.sha256,/^[a-f0-9]{64}$/);assert(effect.emitters.every(e=>e.texture.startsWith('data:image/png;base64,')));
  await player.select(effect.id);for(let i=0;i<90;i++)player.update(1/30);
  assert.equal(scene.children.length,1);const live=scene.children[0].children.filter(c=>c.visible);assert(live.length>0);assert(scene.children[0].children.length<=96);
  for(const m of live){assert(m.positions.every(Number.isFinite));assert(m.scales.every(Number.isFinite));assert(m.material.opacity>=0&&m.material.opacity<=1);assert(m.material.rgb.every(v=>v>=0&&v<=1));}
 }
 player.reset();player.update(.4);assert.equal(player.frame,12);
 await player.select('none');assert.equal(scene.children.length,0);
 const a=player.select('1'),b=player.select('3');await Promise.all([a,b]);assert.equal(player.selected,'3');assert.equal(scene.children.length,1);
 player.destroy();assert.equal(scene.children.length,0);console.log('PASS: three native effects emit bounded finite sprites; switching, off, racing selections and disposal');
})();
