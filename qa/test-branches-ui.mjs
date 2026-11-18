import fs from 'node:fs/promises';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fallbackData,branchConnections} from '../dist/ui-data.js';
const app=await fs.readFile('dist/app.js','utf8'),html=await fs.readFile('dist/index.html','utf8');
const source=JSON.parse(await fs.readFile('dist/process-data.json','utf8'));
const mergeCode=app.slice(app.indexOf('function mergeProcessData('),app.indexOf('async function getData('));
const env={fallbackData,toArray:value=>Array.isArray(value)?value:value?[value]:[]};
const merge=vm.runInNewContext(mergeCode+';mergeProcessData',env);
const legacy=source.stages.filter(stage=>!branchConnections[stage.id]),merged=merge({...source,stages:legacy});
assert.equal(legacy.length,16,'The original cotton route remains intact');
assert.equal(merged.stages.length,27,'An old snapshot must retain the complete live catalog');
assert.deepEqual(Array.from(merged.stages.slice(0,16),stage=>stage.id),fallbackData.stages.slice(0,16).map(stage=>stage.id));
for(const [id,branch] of Object.entries(branchConnections)){
 const stage=merged.stages.find(stage=>stage.id===id);assert.ok(['yarn_processing','weaving','finishing'].includes(stage.section));assert.match(branch.code,/^[A-K]$/);
 for(const link of branch.links)assert.ok(merged.stages.some(stage=>stage.id===link.id),`${id}: dangling related equipment`);
}
assert.equal(branchConnections.compact_spinning.kind,'替代分支');assert.equal(branchConnections.twisting.kind,'选配分支');assert.equal(branchConnections.texturing.kind,'独立路线');
assert.equal(branchConnections.rotor_spinning.kind,'替代分支');assert.deepEqual(branchConnections.rotor_spinning.links.map(item=>item.id),['drawing','warping','spinning']);
const filterCode=app.slice(app.indexOf('function matchesProcessFilter('),app.indexOf('function renderNavigation('));
const matchesFilter=vm.runInNewContext(filterCode+';matchesProcessFilter',{branchConnections});
assert.deepEqual(Object.keys(branchConnections).filter(id=>matchesFilter(merged.stages.find(s=>s.id===id),'spinning')),['compact_spinning','rotor_spinning','airjet_spinning']);
const future=merge({...source,stages:[...source.stages,{id:'future_equipment',name:'后续设备',section:'yarn_processing'}]});assert.equal(future.stages.length,merged.stages.length+1,'Catalog size can grow');
assert.throws(()=>merge({stages:[{id:'spinning'},{id:'spinning'}]}));
const hashCode=app.slice(app.indexOf('function readHashRoute(){'),app.indexOf('async function syncHashRoute(){'));
const hashEnv={state:{data:merged},location:{hash:''}},readHash=vm.runInNewContext(hashCode+';readHashRoute',hashEnv);
for(const id of Object.keys(branchConnections))for(const suffix of ['','/drive','/motor']){hashEnv.location.hash=`#${id}${suffix}`;const route=readHash();assert.equal(route.current,id);assert.equal(route.mode,suffix?'drive':'machine')}
assert.ok(!app.includes('stages.length!==16'));assert.ok(!app.includes('if(index<15)'));
assert.ok(app.includes('state.data.stages.length-1'));
assert.ok(app.includes("if(modelRoot)modelRoot.visible=false;"),'Do not show the previous device while a different model is unavailable');
assert.ok(app.includes("metadata.equipmentId!==loadedID"),'Do not relabel a wrong equipment model');
assert.ok(html.includes('纱线加工'));assert.ok(html.includes('浏览系统设备 · 不代表必经顺序'));
assert.ok(!html.includes('下一工序'));
const stenter=fallbackData.stages.find(stage=>stage.id==='stenter');assert.ok(stenter.name.includes('热定型'));assert.ok(stenter.equipment.includes('兼烘干'));assert.ok(stenter.summary.includes('全棉')&&stenter.summary.includes('热塑性'));
assert.equal(new Set(Object.values(branchConnections).map(branch=>branch.code)).size,11);
const report={testedAt:new Date().toISOString(),result:'pass',legacyEquipment:16,catalogEquipment:merged.stages.length,branchIDs:Object.keys(branchConnections),hashCases:Object.keys(branchConnections).length*3,dynamicFutureCount:future.stages.length};
await fs.writeFile('qa/branches-ui-validation.json',JSON.stringify(report,null,2)+'\n');console.log(report);
