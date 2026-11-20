import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {registerHooks} from 'node:module';
import {machineHash, parseMachineHash, filterModels} from '../dist/model-library.js';

const vendor = new URL('../dist/vendor/three.module.js', import.meta.url).href;
registerHooks({resolve(name, context, next) {
  return name === 'three' ? {url:vendor, shortCircuit:true} : next(name, context);
}});
const THREE = await import('../dist/vendor/three.module.js');
const {GLTFLoader} = await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {resolveDriveRoutes, scopeDriveRoute, buildDriveBranches} = await import('../dist/drive-view.js');
const {StationYarn}=await import('../dist/station-yarn.js');
const {StationMotion} = await import('../dist/station-motion.js');
const {normalizeImportedModel, worldModelBounds} = await import('../dist/scene-geometry.js');
const {fitPerspectiveBounds, boundsCorners} = await import('../dist/camera-fit.js');
const read = async file => JSON.parse(await fs.readFile(file, 'utf8'));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const catalog = await read('dist/model-variants.json');
const {stages} = await read('dist/process-data.json');
const baseline = await read('dist/equipment-provenance.json');
const study = await read('dist/motor-applications.json');
const studyHTML = await fs.readFile('dist/motor-applications.html', 'utf8');
const sources = (await fs.readdir('research')).filter(name => /^variants-.*\.json$/.test(name));
const originals = (await Promise.all(sources.map(name => read(path.join('research', name))))).flat();
const added = catalog.models.filter(m => m.id !== m.stageId);
const indexed = new Set(catalog.models.map(m => m.id));
assert.equal(indexed.size, catalog.models.length);
assert.deepEqual(new Set(added.map(m => m.id)), new Set(originals.map(r => r.id)));
assert.deepEqual(new Set(catalog.models.filter(m => m.id === m.stageId).map(m => m.id)), new Set(stages.map(s => s.id)));
const makers = new Set(added.map(m => m.makerKey));
for (const key of ['jingwei','titan','yuejian','saurer','rieter','barmag']) assert(makers.has(key),key);
assert(added.some(m => m.scope === 'station') && added.some(m => m.scope === 'machine'));
assert(filterModels(catalog.models,'','drawing','立达 RSB-D27').some(m => m.id === 'rieter_rsb_d27'));
assert(filterModels(catalog.models,'saurer','rotor_spinning').length >= 2);
const ringMachines = filterModels(catalog.models,'','spinning');
for (const key of ['rieter','jingwei','saurer','marzoli','toyota']) assert(ringMachines.some(model=>model.makerKey===key),key);
const configuredLengths={jingwei_jwf1590a:60.125,marzoli_mds2_384:19.988,toyota_rx300e:41.035,saurer_zinser_51_ring:18.460};
assert.equal(filterModels(catalog.models,'titan','drawing').length,0);
assert.deepEqual(parseMachineHash('#drawing/motor',stages),{current:'drawing',mode:'drive',variant:null});
assert.equal(parseMachineHash('#%ZZ',stages),null);
assert.equal(parseMachineHash('#bogus',stages),null);
for (const m of catalog.models) {
  for (const mode of ['drive','machine']) {
    const hash = machineHash(m.stageId, m.id, mode);
    assert.deepEqual(parseMachineHash(hash,stages),{current:m.stageId,mode,variant:m.id === m.stageId ? null : m.id});
  }
}
const seenAssets = new Set(Object.values(baseline.assets).map(asset => asset.sha256));
const meshesSeen = new Set();
const projections = [[790,465],[370,440],[1140,390]];
const directions = [[1,.64,1],[0,0,1],[0,0,-1],[1,0,0],[-1,0,0],[0,1,.00001],[0,-1,-.00001]];
const report = {classes:stages.length,models:catalog.models.length,manufacturers:catalog.makers.length,variants:[],projectionCases:0,motorAssociations:0};
const loader = new GLTFLoader();
for (const machine of added) {
  const key = machine.id, title = machine.model;
  const base = path.join('dist/assets/variants',key);
  const [bytes, sidecar, blend] = await Promise.all([fs.readFile(base+'.glb'),fs.readFile(base+'.json'),fs.stat(path.join('blender/variants',key+'.blend'))]);
  assert(blend.size > 10000);
  assert.equal(digest(bytes),machine.sha256);
  assert.equal(digest(sidecar),machine.detailHash);
  assert(!seenAssets.has(machine.sha256)); seenAssets.add(machine.sha256);
  const detail = JSON.parse(sidecar), original = originals.find(x => x.id === key);
  assert.equal(detail.id,key);assert.equal(detail.stageId,machine.stageId);
  assert.equal(detail.provenance.referenceManufacturer,machine.maker);
  assert.equal(detail.provenance.referenceModel,title);
  assert.equal(detail.provenance.currentFinding,original.dating);
  const geometryOffset = 20 + bytes.readUInt32LE(12) + 8;
  const geometryID = digest(bytes.subarray(geometryOffset));
  assert(!meshesSeen.has(geometryID),key+' reused geometry');meshesSeen.add(geometryID);
  const {scene} = await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.length),'');
  const container = new THREE.Group();
  const {rawBounds} = normalizeImportedModel(scene,container);
  const nodes=[], anchors=new Map(); scene.traverse(n => {
    nodes.push(n);
    if (n.userData.driveAnchorId) {assert(!anchors.has(n.userData.driveAnchorId));anchors.set(n.userData.driveAnchorId,n);}
  });
  const assembly = nodes.filter(n => n.userData.equipmentId === key);
  assert.equal(assembly.length,1,key);const identity=assembly[0].userData;
  assert.equal(identity.stageId,machine.stageId); assert.equal(identity.makerKey,machine.makerKey);
  assert.equal(identity.referenceModel,title);assert.equal(identity.referenceManufacturer,machine.maker);
  if(machine.stageId==='texturing'){
    const flow=new StationYarn(scene,new THREE.Group());
    const expected=machine.scope==='station'?1:identity.selectedPositions;
    assert.equal(flow.paths.length,expected,key+' exported continuous threads');
    assert(flow.paths.every(p=>p.xyz.length>=6 && p.xyz.every(Number.isFinite)));
    for(const index of new Set([0,flow.paths.length-1])){
      flow.select(index);const start=flow.dots.instanceMatrix.array.slice();
      flow.update(.35);assert.notDeepEqual(flow.dots.instanceMatrix.array,start,key+' yarn should move');
      const paused=flow.dots.instanceMatrix.array.slice();flow.update(0);assert.deepEqual(flow.dots.instanceMatrix.array,paused);
    }
    flow.dispose();
  }
  const routes=resolveDriveRoutes(scene,detail.drive.routes), motion=new StationMotion(scene);
  motion.setRoutes(routes);
  const mapped = new Set();
  const spindleDrives = new Map();
  const studyRows=study.stages.find(s=>s.id===machine.stageId).rows.filter(row=>row.modelAssetId===key);
  assert.equal(studyRows.length,routes.length);
  assert(studyHTML.includes('./index.html'+machineHash(machine.stageId,key,'drive')),key+' missing study link');
  for (const route of routes) {
    assert.equal(route.graph.association,'explicit_motor_groups',key);
    assert(route.evidence.sources.length);
    assert(studyRows.some(row => row.routeId===route.id && row.refs.every(ref=>study.sources[ref])));
    for (const step of route.steps) assert.deepEqual(new Set(step.objects.map(n=>n.userData.driveAnchorId)),new Set(step.anchorIds),key+' '+route.id);
    const actualEdges = buildDriveBranches(route);
    assert.equal(actualEdges.length,route.graph.links.length,key+' '+route.id);
    if(machine.stageId==='spinning'&&route.motors.length>1){
      assert.deepEqual(new Set(Object.keys(route.motorLabels)),new Set(route.motors.map(node=>node.userData.driveAnchorId)));
      assert.equal(new Set(Object.values(route.motorLabels)).size,route.motors.length,key+' distinguish each motor');
    }
    for (const motor of route.motors) {
      assert.equal(motor.userData.motorDetailScope,'external_only');assert.equal(motor.userData.internalGeometryModeled,false);
      const id=motor.userData.driveAnchorId; mapped.add(id);
      const scopes=scopeDriveRoute(route,motor);
      for (let i=0;i<route.steps.length;i++) {
        const expected=route.steps[i].motorScopes[id];
        assert.deepEqual(new Set(scopes.steps[i].objects.map(n=>n.userData.driveAnchorId)),new Set(expected),key+' '+id);
      }
      const working=scopes.steps.at(-1).objects;assert.equal(working.length===0,Boolean(route.loadUnassigned));
      if (machine.stageId==='spinning') {
        for (const spindle of working.filter(n=>n.userData.spindleIndex!==undefined)) {
          const number=spindle.userData.spindleIndex;
          if (!spindleDrives.has(number)) spindleDrives.set(number,new Set());
          spindleDrives.get(number).add(id);
        }
      }
      motion.select([scopes]);
      if(route.loadUnassigned)assert.equal(motion.active.length,0);
      else assert(motion.active.length>0 && motion.active.some(e=>e.node===anchors.get(id+'_out')),id);
      const selected=new Set(scopes.steps.flatMap(step=>step.objects));
      for (const e of motion.active) {
        let owner=e.node;
        while(owner&&!selected.has(owner))owner=owner.parent;
        assert(owner,key+' unrelated moving station');
      }
      report.motorAssociations++;
    }
    if (route.operation==='doffing') {
      for (const motor of route.motors) {
        const shaft=anchors.get(motor.userData.driveAnchorId+'_out');
        assert(!motion.production.some(entry=>entry.node===shaft),key+' doffing motor runs during spinning');
      }
    }
    if (route.evidence.status==='not_modeled'&&!route.loadUnassigned) {assert.equal(route.motors.length,0);motion.select([route]);assert.equal(motion.active.length,0);}
  }
  assert.deepEqual(mapped,new Set([...anchors].filter(([,n])=>n.userData.driveRole==='motor').map(([id])=>id)));
  assert.equal(mapped.size,machine.motors);assert.equal(identity.modeledMotorCount,mapped.size);
  assert.equal(routes.length,machine.routes);
  let ringFacts;
  if (machine.stageId==='spinning') {
    if(key in configuredLengths){
      const length=rawBounds.max.x-rawBounds.min.x;
      assert(Math.abs(length-configuredLengths[key])<.03,key+' total length including end equipment');
    }
    const count=identity.spindleCount;
    const spindles=nodes.map(node=>node.userData).filter(data=>Number.isInteger(data.spindleIndex));
    assert(Number.isInteger(count) && count>0 && count%2===0,key+' configuration spindle count');
    assert.deepEqual(spindles.map(p=>p.spindleIndex).sort((a,b)=>a-b),Array.from({length:count},(_,i)=>i+1),key+' every physical spindle');
    const sides=new Map(), perMotor=new Map();
    for (const spindle of spindles) {
      assert(spindle.machineSide && spindle.driveAnchorId && spindle.stationMotion?.startsWith('rotate:'),key+' indexed rotating spindle');
      sides.set(spindle.machineSide,(sides.get(spindle.machineSide)||0)+1);
      const drives=spindleDrives.get(spindle.spindleIndex);
      assert.equal(drives?.size,1,key+' exact power source for spindle '+spindle.spindleIndex);
      const [id]=drives;
      if(spindle.spindleMotorAnchor)assert.equal(id,spindle.spindleMotorAnchor,key+' motor on the physical spindle');
      perMotor.set(id,(perMotor.get(id)||0)+1);
    }
    assert.deepEqual([...sides.values()].sort((a,b)=>a-b),[count/2,count/2],key+' both sides complete');
    if(key==='marzoli_mds2_384') {
      assert.deepEqual([...perMotor.values()],[192,192],key+' independent drives');
      const turn=worldModelBounds(anchors.get('MDS_tray_return'));
      for(const side of ['A','B'])
        assert(turn.intersectsBox(worldModelBounds(anchors.get('MDS_tray_track_'+side))),key+' connected tray track '+side);
    }
    if(key==='toyota_rx300e') {
      assert.deepEqual([...perMotor.values()],[1008]);
      const tapes=nodes.filter(n=>n.userData.drivenSpindleCount===4);
      assert.equal(tapes.length,252);
      const main=routes.find(r=>r.id==='rx_spindles');
      const edges=new Map();
      for(const [from,to] of main.graph.links) {
        if(!edges.has(from))edges.set(from,[]);
        edges.get(from).push(to);
      }
      for(const tape of tapes) {
        const outputs=edges.get(tape.userData.driveAnchorId);
        assert.equal(outputs?.length,4);
        assert(outputs.every(id=>anchors.get(id).userData.tapeGroupIndex===tape.userData.tapeGroupIndex));
      }
      for(const name of ['middle','back']) {
        const route=routes.find(r=>r.id==='rx_'+name+'_draft');
        const [ge,oe]=route.motors.map(m=>new Set(scopeDriveRoute(route,m).steps.at(-1).objects));
        assert(ge.size===oe.size && [...ge].every(node=>!oe.has(node)),key+' two independent '+name+' roller sections');
      }
    }
    ringFacts={spindles:count,perSide:count/2,spindlesPerMainMotor:Object.fromEntries(perMotor)};
  }
  for (const phase of [0,.73]) {
    motion.select(null);motion.update(phase);
    const box=worldModelBounds(container),bounds={min:box.min.toArray(),max:box.max.toArray()};
    for(const [width,height] of projections)for(const direction of directions){
      const fit=fitPerspectiveBounds(bounds,{direction,width,height,padding:20});
      const camera=new THREE.PerspectiveCamera(37,width/height,fit.near,fit.far);
      camera.position.fromArray(fit.position);camera.lookAt(...fit.center);camera.updateMatrixWorld(true);
      for(const corner of boundsCorners(bounds)){
        const p=new THREE.Vector3(...corner).project(camera);
        assert(Math.abs(p.x)<=fit.safeX+1e-7 && Math.abs(p.y)<=fit.safeY+1e-7 && p.z>=-1 && p.z<=1,key+' clipped');
      }
      report.projectionCases++;
    }
  }
  motion.dispose();container.clear();
  report.variants.push({id:key,stage:machine.stageId,model:title,scope:machine.scope,
    routes:routes.length,motors:mapped.size,...ringFacts,meshes:nodes.filter(n=>n.isMesh).length,bytes:bytes.length,
    boundsMetres:rawBounds.getSize(new THREE.Vector3()).toArray().map(n=>Number(n.toFixed(3))),sha256:machine.sha256});
  console.log(key,mapped.size+' motor locations',routes.length+' routes');
}
report.status='pass';
await fs.writeFile('qa/model-variants-validation.json',JSON.stringify(report,null,2)+'\n');
console.log(report.models+' model entries, '+report.motorAssociations+' motor/route assignments, '+report.projectionCases+' framing checks.');
