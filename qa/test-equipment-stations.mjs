import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
const vendor=new URL('../dist/vendor/three.module.js',import.meta.url).href;
registerHooks({resolve(s,c,next){return s==='three'?{url:vendor,shortCircuit:true}:next(s,c)}});
const {GLTFLoader}=await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {StationMotion}=await import('../dist/station-motion.js');
const {resolveDriveRoutes,scopeDriveRoute,motorDriveRoutes,buildDriveBranches}=await import('../dist/drive-view.js');
const json=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const refs=await json('dist/equipment-provenance.json'),chains=await json('dist/drive-chains.json');
const equipment=await json('dist/process-data.json'),applications=await json('dist/motor-applications.json');
const sources=refs.configurationFiles.filter(f=>f.startsWith('research/expansion-'));
const records=(await Promise.all(sources.map(json))).flat();
assert.equal(records.length,7);assert.equal(equipment.stages.length,27);
const summary=[];
for(const rec of records){
  const bytes=await fs.readFile('dist/assets/models/'+rec.id+'.glb');
  const asset=refs.assets[rec.id];
  assert.equal(createHash('sha256').update(bytes).digest('hex'),asset.sha256);
  const {scene}=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  scene.updateMatrixWorld(true);
  const nodes=[];scene.traverse(n=>nodes.push(n));
  const byId=new Map(nodes.filter(n=>n.userData.driveAnchorId).map(n=>[n.userData.driveAnchorId,n]));
  assert.equal(byId.size,nodes.filter(n=>n.userData.driveAnchorId).length);
  const identity=nodes.find(n=>n.userData.equipmentId===rec.id);
  assert.equal(identity.userData.referenceModel,rec.model);
  const routes=resolveDriveRoutes(scene,chains.items.find(r=>r.id===rec.id).routes);
  const indexed=applications.stages.find(s=>s.id===rec.id).rows;
  const motion=new StationMotion(scene),allMotors=new Set(),states={confirmed:new Set(),inferred:new Set()};
  motion.setRoutes(routes);
  const posed=()=>motion.entries.map(e=>[...e.node.position.toArray(),...e.node.quaternion.toArray()]);
  const rest=posed();
  for(const spec of rec.routes){
    const route=routes.find(r=>r.id===spec.id);assert.ok(route);
    assert.ok(indexed.some(row=>row.electric===spec.electric&&row.refs.length));
    const groups=spec.groups.flatMap(g=>{
      const format=(s,n)=>s?.replace(/\{n(?::0(\d+)d)?\}/g,(_,width)=>String(n).padStart(Number(width)||0,'0'));
      if(!g.repeat)return [g];
      return Array.from({length:g.repeat},(_,i)=>{const n=i+(g.start??1);
        return {motor:format(g.motor,n),via:g.via.map(s=>format(s,n)),loads:g.loads.map(s=>format(s,n))};
      });
    });
    assert.deepEqual(route.motors.map(m=>m.userData.driveAnchorId),groups.filter(g=>g.motor).map(g=>g.motor));
    const expectedEdges=new Set();
    for(const group of groups){
      if(!group.motor)continue;
      const sequence=[group.motor,group.motor+'_out',...group.via.filter(v=>v!==group.motor+'_out')];
      for(let i=1;i<sequence.length;i++)expectedEdges.add(sequence[i-1]+'>'+sequence[i]);
      for(const target of group.loads)expectedEdges.add(sequence.at(-1)+'>'+target);
      const motor=byId.get(group.motor);allMotors.add(motor);states[spec.status].add(motor);
      const scoped=scopeDriveRoute(route,motor);
      assert.deepEqual(new Set(scoped.steps.at(-1).objects.map(o=>o.userData.driveAnchorId)),new Set(group.loads));
      assert.equal(motor.userData.internalGeometryModeled,false);
      const active=motorDriveRoutes(routes,motor);
      motion.select(active);assert.ok(motion.active.length,'Motor includes a moving output');
      const allowed=new Set(active.flatMap(s=>s.steps.flatMap(step=>step.objects)));
      for(const entry of motion.active){
        let owner=entry.node;while(owner&&!allowed.has(owner))owner=owner.parent;
        assert.ok(owner,'No unrelated mechanism in selected scope');
      }
      const before=posed();motion.update(.2);const after=posed();
      assert.ok(after.some((a,i)=>a.some((v,j)=>v!==before[i][j])));
      const activeEntries=new Set(motion.active);
      motion.entries.forEach((e,i)=>{if(!activeEntries.has(e))assert.deepEqual(after[i],before[i])});
      motion.update(0);assert.deepEqual(posed(),after);
    }
    assert.deepEqual(new Set(buildDriveBranches(route).map(e=>e.from.userData.driveAnchorId+'>'+e.to.userData.driveAnchorId)),expectedEdges);
    if(spec.status==='unassigned'){
      assert.equal(route.motors.length,0);motion.select([route]);assert.equal(motion.active.length,0);
    }
  }
  assert.equal(allMotors.size,identity.userData.modeledMotorCount);
  motion.select(null);
  for(const route of routes.filter(r=>r.operation==='maintenance')){
    for(const motor of route.motors)assert.ok(!(motion.byOwner.get(motor)||[]).some(e=>motion.active.includes(e)));
  }
  assert.ok(motion.active.length>0);motion.dispose();assert.deepEqual(posed(),rest);
  summary.push({id:rec.id,manufacturer:rec.maker,model:rec.model,routes:routes.length,motors:allMotors.size,
    confirmed:states.confirmed.size,inferred:[...states.inferred].filter(m=>!states.confirmed.has(m)).length,
    unassignedRoutes:routes.filter(r=>!r.motors.length).length,movingParts:motion.entries.length,bytes:asset.bytes,sha256:asset.sha256});
}
assert.deepEqual(new Set(equipment.coverageReview.modeled.map(s=>s.id)),new Set(records.map(s=>s.id)));
const report={status:'pass',equipment:27,newModels:summary};
await fs.writeFile('qa/equipment-stations-validation.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
