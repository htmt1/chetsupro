// Inserted in the renderer's closure. Uses its existing Three.js aliases.
// This is a bounded billboard interpreter, not Nintendo's entire SPBD shader VM.
function createNativeAuraPlayer(scene,camera,render,getSize) {
  let root=null,selected="none",time=0,revision=0,dead=false;
  const particles=[],emitters=[];
  const random=(seed)=>{let n=seed>>>0;return()=>{n^=n<<13;n^=n>>>17;n^=n<<5;return(n>>>0)/4294967296;};};
  function clear(){if(root){scene.remove(root);yc(root);}root=null;particles.length=emitters.length=0;}
  function reset(){time=0;for(const e of emitters){e.next=e.spec.startFrame;e.random=random(0x51a7+e.index*0x1001);for(const p of e.pool){p.live=false;p.mesh.visible=false;}}}
  async function select(id){
    const job=++revision;
    if(id==="none"){selected=id;clear();render();return;}
    const source=nativeAuraData.effects.find(e=>e.id===id);
    if(!source)throw Error("オーラが見つかりません。");
    const images=await Promise.all(source.emitters.map(e=>Uh(e.texture)));
    if(dead||job!==revision)return;
    clear();selected=id;root=new Zt();root.name="NativeAura";scene.add(root);
    const size=getSize();root.scale.set(size.scaleX,size.scaleY,size.scaleX);
    const total=source.emitters.length;
    source.emitters.forEach((spec,index)=>{
      const geometry=new hn();geometry.setAttribute("position",new Nt([-.5,-.5,0,.5,-.5,0,.5,.5,0,-.5,.5,0],3));geometry.setAttribute("uv",new Nt([0,1,1,1,1,0,0,0],2));geometry.setIndex([0,1,2,0,2,3]);geometry.computeVertexNormals();
      const map=Fh(images[index]);const pool=[];
      // Respect source rate/lifetime, bounded to keep software/mobile rendering usable.
      const expected=Math.ceil(spec.rate*Math.max(1,spec.lifeFrames+spec.lifeVariation)/Math.max(1,spec.interval));
      const count=Math.max(2,Math.min(expected+2,Math.floor(96/total)));
      for(let i=0;i<count;i++){
        const material=new Ts({map,color:16777215,emissive:16777215,emissiveMap:map,emissiveIntensity:1,transparent:true,opacity:0,alphaTest:.005,depthWrite:false,blending:2,side:Ft});
        const mesh=new St(geometry,material);mesh.name="NativeAura_"+spec.name;mesh.visible=false;root.add(mesh);
        const p={mesh,live:false};pool.push(p);particles.push(p);
      }
      emitters.push({index,spec,pool,random:random(0x51a7+index*0x1001),next:spec.startFrame});
    });
    reset();update(1/30);render();
  }
  function spawn(e,frame){
    const p=e.pool.find(p=>!p.live);if(!p)return;
    const s=e.spec,r=e.random;
    p.born=frame;p.life=Math.max(1,s.lifeFrames+(r()*2-1)*s.lifeVariation);p.live=true;
    p.xyz=s.spread.map((spread,i)=>s.origin[i]+(r()*2-1)*spread);
    p.size=[s.sizes[0]+r()*(s.sizes[1]-s.sizes[0]),s.sizes[2]+r()*(s.sizes[3]-s.sizes[2])];
    p.angle=s.rotation[0]+r()*(s.rotation[1]-s.rotation[0]);p.spec=s;
  }
  function update(dt){
    if(!root)return;
    time+=Math.max(0,Math.min(dt,1))*nativeAuraData.fps;
    for(const e of emitters){
      const s=e.spec,interval=Math.max(1,s.interval);
      while(e.next<=time&&e.next<=s.endFrame){
        for(let n=0;n<Math.max(1,Math.min(12,Math.round(s.rate)));n++)spawn(e,e.next);
        e.next+=interval;
      }
    }
    for(const p of particles){
      if(!p.live)continue;
      const age=time-p.born,t=age/p.life;
      if(t>=1){p.live=false;p.mesh.visible=false;continue;}
      const s=p.spec;p.mesh.visible=true;
      const scale=s.scale||[1,1,1];
      p.mesh.position.set((p.xyz[0]+s.velocity[0]*age)*scale[0],(p.xyz[1]+s.velocity[1]*age)*scale[1],(p.xyz[2]+s.velocity[2]*age)*scale[2]);
      p.mesh.quaternion.copy(camera.quaternion);p.mesh.rotateZ(p.angle);
      p.mesh.scale.set(Math.max(.1,Math.abs(p.size[0]*scale[0])),Math.max(.1,Math.abs(p.size[1]*scale[1])),1);
      const index=t<.5?0:1,f=t<.5?t*2:(t-.5)*2,a=s.colors[index],b=s.colors[index+1];
      const rgb=a.slice(0,3).map((v,i)=>Math.max(0,Math.min(1,v+(b[i]-v)*f)));
      p.mesh.material.color.setRGB(...rgb);p.mesh.material.emissive.setRGB(...rgb);
      // Fade the billboard envelope where the native shader/curve engine is absent.
      p.mesh.material.opacity=Math.max(0,Math.min(1,a[3]+(b[3]-a[3])*f))*Math.min(1,t*8,(1-t)*5);
    }
  }
  function resize(){if(root){const s=getSize();root.scale.set(s.scaleX,s.scaleY,s.scaleX);}}
  return {select,update,reset,resize,get selected(){return selected;},get frame(){return time;},destroy(){dead=true;revision++;clear();}};
}
