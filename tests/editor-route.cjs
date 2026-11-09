const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');const html=fs.readFileSync('site/birth.html','utf8'),geki=fs.readFileSync('site/geki.html','utf8');
const h=html.slice(html.indexOf('function routeGekiInstructions('),html.indexOf('function routeLines('));const c={};vm.createContext(c);vm.runInContext(h,c);
const start=geki.indexOf('const GekiOperationCatalog ='),end=geki.indexOf('</script>',start),g={module:{exports:{}}};vm.createContext(g);vm.runInContext(geki.slice(start,end),g);const op=g.module.exports;
for(let n=0;n<2000;n+=2){const source={kind:'rarecatch',catch_kind:'geki',slot:3,consumption:43+n,catch_plan:{seed:3258188431,current:39,overhead:4,boxTransit:0}};const lines=c.routeGekiInstructions(source),p=op.capturePlan({target:43+n,current:39,overhead:4,boxTransit:0});const find=(prefix)=>{const s=lines.find(l=>l.startsWith(prefix));return s?Number(s.match(/[\d,]+/)[0].replaceAll(',','')):0;};assert.equal(find('出生確認')*2+find('ボックス開閉')*8+(lines.some(l=>l.startsWith('記録手帳'))?10+(lines.some(l=>l.includes('スクロール'))?find('記録手帳')*10:0):0),n);}
assert.match(c.routeGekiInstructions({kind:'rarecatch',catch_kind:'geki'})[0],/記録なし/);assert.deepEqual([...c.routeGekiInstructions({kind:'birth'})],[]);
for(const v of [2,3,4])assert.match(html,new RegExp('<option value="'+v+'">'+v+'倍'));
console.log('PASS: route instructions match 1,000 exact targets; missing records remain explicit; editor controls present');
const portrait={window:{}};vm.createContext(portrait);vm.runInContext(fs.readFileSync('site/portrait-resources.7d16985be0ee.js','utf8'),portrait);const assets=portrait.window.DenpaSharedPortrait.assets;
for(const file of ['birth.html','basic.html','geki.html']){
 const h=fs.readFileSync('site/'+file,'utf8'),a=h.indexOf('const DenpaFacePicker ='),b=h.indexOf('\n})();',a)+7,x={};vm.createContext(x);vm.runInContext(h.slice(a,b)+';this.picker=DenpaFacePicker;',x);
 const id=file==='birth.html'?'rareData':'embeddedData',data=JSON.parse(h.match(new RegExp('<script[^>]*id="'+id+'"[^>]*>([\\s\\S]*?)<\\/script>'))[1]);
 const hair=x.picker.catalog('face_variant_id',assets,data).flatMap(g=>g.ids),editor=x.picker.editorCatalog('face_variant_id',assets).flatMap(g=>g.ids);assert(!hair.includes(40));assert(editor.includes(40));assert(editor.includes(50));
 const cheeks=x.picker.editorCatalog('cheek_id',assets);assert(cheeks.some(g=>g.ids.includes(0)&&g.ids.includes(12)&&g.ids.includes(28)));
 const search=x.picker.catalog('cheek_id',assets,data);assert(!search.some((g,i)=>search.some((v,k)=>i!==k&&g.ids.some(id=>v.ids.includes(id)))));
 console.log('PASS '+file+': deduplicated search and editor groups; unused editor IDs retained');
}
