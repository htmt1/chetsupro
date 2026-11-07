const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const portrait={window:{}};vm.createContext(portrait);vm.runInContext(fs.readFileSync(process.argv[2]+'/portrait-resources.7d16985be0ee.js','utf8'),portrait);
for(const file of ['geki.html','basic.html']){
 const html=fs.readFileSync(process.argv[2]+'/'+file,'utf8'), data=JSON.parse(html.match(/<script id="embeddedData"[^>]*>([\s\S]*?)<\/script>/)[1]);
 const ctx={module:{exports:{}}};vm.createContext(ctx);
 let a=html.indexOf('const DenpaFacePicker = '),b=html.indexOf('\n"use strict";',a);vm.runInContext(html.slice(a,b)+';this.picker=DenpaFacePicker;',ctx);
 const assets=portrait.window.DenpaSharedPortrait.assets;
 for(const key of ctx.picker.keys){
  const groups=ctx.picker.catalog(key,assets,data),ids=groups.flatMap(g=>g.ids),visuals=groups.map(g=>{const x=assets.layers[key]?.[g.id];return x?JSON.stringify([x.empty,x.colors?.[0]||x.src,x.box]):JSON.stringify((key==='face_color_id'?assets.skinColors:assets.hairColors)[g.id]);});
  assert.equal(new Set(ids).size,ids.length);assert.equal(new Set(visuals).size,visuals.length);
 }
 const hair=ctx.picker.catalog('face_variant_id',assets,data);assert(hair.some(g=>g.ids.includes(32)));assert(!hair.some(g=>g.ids.includes(40)));assert(!hair.some(g=>g.ids.includes(48)));
 a=html.lastIndexOf('const DenpaTraits = ');b=html.indexOf('if (typeof module !== "undefined") module.exports = DenpaTraits;',a);vm.runInContext(html.slice(a,b)+';this.traits=DenpaTraits;',ctx);
 const t=ctx.traits;
 for(const excluded of [false,true])for(const id of [0,1,32,39]){
  const filter={face_variant_id:[32,39],...(excluded?{_exclude:['face_variant_id']}:{})};const v={face_variant_id:id};assert.equal(t.matches(v,filter),excluded?![32,39].includes(id):[32,39].includes(id));assert.equal(t.compile(filter)(v),t.matches(v,filter));
 }
 // Multiple included/excluded colors; unordered colors inspect either slot.
 for(const [filter,yes,no] of [
  [{color1_ids:[3,6],color_order:'either'}, {color1_id:9,color2_id:6},{color1_id:9,color2_id:12}],
  [{color1_ids:[3,6],_exclude:['color1_id'],color_order:'either'},{color1_id:9,color2_id:12},{color1_id:9,color2_id:6}],
  [{color1_ids:[3,6],color2_ids:[9,12],_exclude:['color2_id'],color_order:'either'},{color1_id:3,color2_id:0},{color1_id:3,color2_id:9}]
 ])for(const v of [yes,no]){assert.equal(t.matches(v,filter),v===yes);assert.equal(t.compile(filter)(v),v===yes);}
 console.log('PASS '+file+': valid distinct face candidates and multiple include/exclude predicates');
}
