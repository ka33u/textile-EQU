import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
const directory=process.cwd();
registerHooks({resolve(specifier,context,next){if(specifier==='three')return {url:pathToFileURL(directory+'/dist/vendor/three.module.js').href,shortCircuit:true};return next(specifier,context)}});
const THREE=await import(pathToFileURL(directory+'/dist/vendor/three.module.js'));
const {GLTFLoader}=await import(pathToFileURL(directory+'/dist/vendor/addons/loaders/GLTFLoader.js'));
const app=await fs.readFile('dist/app.js','utf8');
const identities=app.slice(app.indexOf('function readModelIdentity('),app.indexOf('const provenanceItem='));
const semantics=app.slice(app.indexOf('function inheritedData('),app.indexOf('function applyMaterials('));
const env={content:null};
const api=vm.runInNewContext(identities+'\n'+semantics+';({readModelIdentity,resolveModelIdentity,labeledPart,semanticPartKey,semanticPartRepresentative})',env);
const provenance=JSON.parse(await fs.readFile('dist/equipment-provenance.json','utf8'));
const processData=JSON.parse(await fs.readFile('dist/process-data.json','utf8'));
assert.deepEqual(new Set(Object.keys(provenance.assets)),new Set([...processData.stages.map(item=>item.id),'motor']),'Manifest covers each catalog equipment');
const refs=new Map(provenance.items.map(i=>[i.id,i]));
const report={testedAt:new Date().toISOString(),assetVersion:provenance.assetVersion,identityCases:0,raycastSelectionCases:0,configurationRecords:0,models:[],regressions:[],manufacturerCompletenessVerified:false};
const loader=new GLTFLoader();
for(const [id,asset] of Object.entries(provenance.assets)){
 const bytes=await fs.readFile(`dist/assets/models/${id}.glb`),hash=createHash('sha256').update(bytes).digest('hex');assert.equal(hash,asset.sha256,id);
 const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 env.content=new THREE.Group();env.content.add(gltf.scene);
 const metadata=api.readModelIdentity(gltf.scene),identity=api.resolveModelIdentity(metadata,refs.get(id));
 assert.equal(String(metadata.modelVersion),String(asset.modelVersion),id);
 if(id!=='motor'){assert.equal(identity.hasReference,true);assert.equal(identity.model,refs.get(id).referenceModel);assert.equal(identity.manufacturer,refs.get(id).referenceManufacturer);assert.equal(metadata.structuralCompleteness,false)}
 else{assert.equal(identity.hasReference,false);assert.equal(identity.manufacturer,'');assert.equal(identity.model,'结构教学模型')}
 report.identityCases++;
 const groups=new Map(),meshes=[];
 gltf.scene.traverse(object=>{
  if(object.isMesh)meshes.push(object);
  if(!object.userData.label)return;
  const key=api.semanticPartKey(object),parent=api.labeledPart(object.parent);
  if(parent&&api.semanticPartKey(parent)===key)return;
  if(!groups.has(key))groups.set(key,[]);
  groups.get(key).push(object);
 });
 for(const mesh of meshes){const representative=api.semanticPartRepresentative(mesh),group=groups.get(api.semanticPartKey(representative));assert.ok(group?.includes(representative),`${id}: selected mesh absent from semantic group ${mesh.name}`);report.raycastSelectionCases++}
 assert.ok(groups.size<200,`${id}: uncollapsed semantic labels (${groups.size})`);
 if(id==='weaving')assert.equal(groups.get('经纱').length,2880);
 if(id==='drawing_in'){assert.equal(groups.get('穿经后经片').length,2880);assert.ok([...groups.entries()].some(([key,objects])=>key!=='穿经后经片'&&objects.length===2880))}
 if(id==='warping')assert.equal(groups.get('筒子架锭位').length,480);
 if(id==='spinning')assert.equal(groups.get('G38独立完整纺纱锭位').length,288);
 report.models.push({id,sha256:hash,modelVersion:String(metadata.modelVersion),referenceModel:metadata.referenceModel||null,meshNodes:meshes.length,semanticTypes:groups.size,members:[...groups.values()].reduce((n,v)=>n+v.length,0),largestGroups:[...groups.entries()].map(([label,objects])=>({label,members:objects.length})).sort((a,b)=>b.members-a.members).slice(0,5)});
 console.log(`${id}: identity + ${groups.size} semantic types + ${meshes.length} mesh selections pass`);
}
const old=api.resolveModelIdentity({modelVersion:'2.0',referenceModel:'New catalog name'},refs.get('weaving'));assert.equal(old.hasReference,false);assert.equal(old.model,'结构教学模型');
assert.equal(api.resolveModelIdentity({modelVersion:'3.0'},refs.get('weaving')).hasReference,false);
assert.equal(api.semanticPartKey({name:'card',userData:{label:'C 81'}}),'C 81');
assert.equal(api.semanticPartKey({name:'yarn',userData:{label:'经纱 2000/2880'}}),'经纱');
assert.equal(api.semanticPartKey({name:'can',userData:{label:'F40喂条筒 72'}}),'F40喂条筒');
report.regressions=['v2 catalog-rename isolation','v3 missing model name fallback','motor remains generic','model numbers preserved','n/total yarn labels consolidated','ordinal can labels consolidated','every raycast mesh maps to a selectable semantic member'];
let configurationSourceRecords=0;
for(const source of ['research/config-spinning-v3.json','research/config-weaving-v3.json','research/config-finishing-v3.json','research/config-extensions-v5.json','research/config-rotor.json']){
 const cfg=JSON.parse(await fs.readFile(source,'utf8'));
 configurationSourceRecords+=cfg.items.length;
 for(const x of cfg.items){const i=refs.get(x.id||x.equipmentId);assert.equal(i.referenceModel,x.referenceModel);assert.equal(i.referenceManufacturer,x.referenceManufacturer||x.manufacturer);for(const field of ['verified','inferred','missing'])assert.equal(i[field].length,x[field].length,`${i.id}: ${field}`);if(x.selectedCounts)assert.deepEqual(Object.values(i.selectedCounts),Object.values(x.selectedCounts),i.id);report.configurationRecords++}
}
for(const file of provenance.configurationFiles.filter(s=>s.startsWith('research/expansion-'))){
 const records=JSON.parse(await fs.readFile(file,'utf8'));configurationSourceRecords+=records.length;
 for(const rec of records){
  const ref=refs.get(rec.id);assert.equal(ref.referenceModel,rec.model);assert.equal(ref.referenceManufacturer,rec.maker);
  assert.deepEqual(ref.selectedCounts,rec.counts);
  for(const field of ['verified','inferred','missing'])assert.deepEqual(ref[field],rec[field]);
  report.configurationRecords++;
 }
}
assert.equal(report.configurationRecords,configurationSourceRecords);assert.equal(report.configurationRecords,processData.stages.length);assert.equal(report.identityCases,Object.keys(provenance.assets).length);
for(const item of processData.stages){assert.ok(refs.has(item.id),`${item.id}: missing provenance record`);assert.ok(report.models.some(model=>model.id===item.id),`${item.id}: model identity not tested`)}
report.result='pass';
await fs.writeFile('qa/frontend-validation.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({result:report.result,identityCases:report.identityCases,configurationRecords:report.configurationRecords,raycastSelectionCases:report.raycastSelectionCases}));
