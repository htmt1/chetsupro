const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(process.argv[2]||'site/birth.html','utf8');
const code=html.slice(html.indexOf('const DenpaParentLoadGate ='),html.indexOf('const DenpaSavedParentsUI ='));
class Element { constructor(){this.children=[];this.disabled=false;} append(...x){this.children.push(...x);} prepend(x){this.children.unshift(x);} setAttribute(){} remove(){this.removed=true;} showModal(){this.open=true;} close(){this.open=false;} focus(){} }
async function test(mode,fail=false){
 const made=[],main=new Element(),body=new Element(),status=new Element();let opened=0,cleared=[],resolved=false;
 const context={make:(tag,cls,text)=>{const e=new Element();e.textContent=text;made.push(e);return e;},document:{querySelector:()=>main,body},$ :()=>status,indexedDB:{open(...args){opened++;assert.deepEqual(args,['denpa-saved-parent-groups']);const request={};queueMicrotask(()=>{request.result={objectStoreNames:{contains:()=>true},close(){},transaction(names,kind){assert.deepEqual([...names],['groups','poolChunks']);assert.equal(kind,'readwrite');const tx={objectStore:name=>({clear(){cleared.push(name);}})};queueMicrotask(()=>fail?tx.onabort():tx.oncomplete());return tx;}};request.onsuccess();});return request;}}};
 vm.createContext(context);vm.runInContext(code+'\nthis.gate=DenpaParentLoadGate;',context);context.gate.ready.then(()=>resolved=true);
 const get=id=>made.find(e=>e.id===id);
 await Promise.resolve();assert.equal(opened,0);assert.equal(resolved,false);
 get('clearParentsBeforeRead').onclick();assert.equal(opened,0);assert.equal(get('clearParentsDialog').open,true);
 made.find(e=>e.textContent==='キャンセル').onclick();assert.equal(opened,0);assert.equal(resolved,false);
 if(mode==='load'){get('loadParentsBeforeRead').onclick();await Promise.resolve();assert.equal(opened,0);assert.equal(resolved,true);return;}
 await get('confirmClearParents').onclick();await Promise.resolve();assert.deepEqual(cleared,['groups','poolChunks']);assert.equal(resolved,!fail);
 if(fail){assert.equal(get('loadParentsBeforeRead').disabled,false);assert.match(made.find(e=>e.children.length===0&&e.textContent?.startsWith('削除できませんでした：')).textContent,/削除/);}
}
(async()=>{await test('load');await test('clear');await test('clear',true);assert.match(html,/async function restore\(\{ force = false \} = \{\}\) \{\s*await DenpaParentLoadGate.ready;/);for(const script of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)){if(script[1].trim()&&!script[0].includes('type="application/json"'))new vm.Script(script[1]);}console.log('PASS: no reads before choice; cancel, load, atomic clear and retry after failure.');})();
