const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=process.argv[2]||'site';
const index=fs.readFileSync(path.join(root,'index.html'),'utf8');
const resourceName=index.match(/portrait-resources\.[a-f0-9]{12}\.js/)[0];
const shared=JSON.parse(fs.readFileSync(path.join(root,resourceName),'utf8').replace(/^window.DenpaSharedPortrait=/,'').trim().replace(/;$/,''));
const birth=fs.readFileSync(path.join(root,'birth.html'),'utf8');
const model=fs.readFileSync(path.join(root,birth.match(/model3d\.[a-f0-9]{12}\.js/)[0]),'utf8');new vm.Script(model);
const start=model.indexOf('const antennaLifts='),end=model.indexOf('function vc(',start);assert(start>=0&&end>start);
class Group{constructor(){this.children=[];this.position={x:0,y:0,z:0,fromArray(v){[this.x,this.y,this.z]=v;}};this.scale={set(){},setScalar(){}};this.rotation={set(){}};}add(o){this.children.push(o);}updateMatrixWorld(){}bind(){}normalizeSkinWeights(){}}
const texture={clone(){return {needsUpdate:false}}};
const ctx={Zt:Group,Wi:Group,ys:Group,St:Group,vs:class{},Po(){},Lo(){},Nh:async()=>texture};vm.createContext(ctx);vm.runInContext(model.slice(start,end)+';this.build=Wg;',ctx);
const data={bones:[],bodyColors:[],patterns:[0],body:[{}],heads:shared.assets.heads.map(()=>[]),faceMeshes:[],antennas:Array.from({length:134},()=>({meshes:[]})),anchors:shared.details.anchors};
(async()=>{
 let pairs=0;
 for(const page of ['birth.html','basic.html','geki.html']){
  const html=fs.readFileSync(path.join(root,page),'utf8');const a=html.indexOf('const DenpaPortrait = (() => {'),b=html.indexOf('})();',a);assert(a>=0&&b>a);
  const env={parent:{DenpaSharedPortrait:shared},console};vm.createContext(env);vm.runInContext(html.slice(a,b+5)+';this.portrait=DenpaPortrait;',env);
  const portrait=env.portrait,group=shared.details.groups.length;
  for(const [asset,mask] of Object.entries(shared.details.variants)){
   if(mask.empty)continue;const [modelID,icon]=asset.split(':').map(Number),stage={model:modelID,icon,asset,level:1};shared.details.groups[group]=[stage];
   for(let head=0;head<40;head++){
    const traits={head_id:head,body_id:0,pattern_id:0,color1_id:3,color2_id:3,face_id:0,face_variant_id:0,brow_id:0,eye_id:0,nose_id:0,mouth_id:0,cheek_id:0,face_color_id:0,hair_color_id:0,antenna_group_id:group,level:1};
    const svg=decodeURIComponent(portrait.imageSync(traits,{fit:true}).split(',').slice(1).join(','));
    const match=svg.match(/data-game-antenna="\d+" data-antenna-icon="\d+" transform="translate\(([^ ]+) ([^)]+)\)"/);assert(match,asset);
    const frame=shared.assets.frame,anchor=data.anchors[head],svgLift=frame.center[1]-Number(match[2])/frame.scale-anchor[1];
    if(page==='birth.html'){
     const object=await ctx.build(data,traits,{scaleX:1,scaleY:1,headScale:1},stage),headGroup=object.children.find(x=>x.name==='Head'),antenna=headGroup.children.find(x=>x.name==='Antenna');
     assert(antenna);assert(Math.abs(antenna.position.y-anchor[1]-svgLift)<1e-8,asset+' head '+head);pairs++;
    }
    const box=svg.match(/viewBox="([^\"]+)"/)[1].split(' ').map(Number),[x,y,w,h]=mask.box,dy=Number(match[2]);
    assert(y+dy>=box[1]-.01 && y+dy+h<=box[1]+box[3]+.01,'antenna cropped in '+page);
   }
  }
 }
 assert.equal(pairs,7040);assert(shared.details.antennaLift['0:34']['27']>10);assert.equal(shared.details.antennaLift['0:34']['0'],undefined);
 console.log('PASS 7,040 shared 2D/3D placements; fitted portraits in all three pages retain the complete antenna; round-head placement unchanged.');
})().catch(e=>{console.error(e.message);process.exit(1)});
