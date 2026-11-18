import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {createHash} from 'node:crypto';
registerHooks({resolve(specifier,context,next){if(specifier==='three')return {url:new URL('../dist/vendor/three.module.js',import.meta.url).href,shortCircuit:true};return next(specifier,context)}});
const THREE=await import('../dist/vendor/three.module.js');
const {GLTFLoader}=await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {resolveDriveRoutes,driveObjectContext}=await import('../dist/drive-view.js?v=20261118-v6-motion');
const {normalizeImportedModel}=await import('../dist/scene-geometry.js');
const {TexturingMotion,TEXTURING_PHASES,extractYarnCenterline,samplePolyline}=await import('../dist/texturing-motion.js');
const bytes=await fs.readFile('dist/assets/models/texturing.glb'),sha256=createHash('sha256').update(bytes).digest('hex');
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
const scene=new THREE.Scene(),container=new THREE.Group();scene.add(container);normalizeImportedModel(gltf.scene,container);
const data=JSON.parse(await fs.readFile('dist/drive-chains.json','utf8')).items.find(i=>i.id==='texturing');
const routes=resolveDriveRoutes(gltf.scene,data.routes),original=new Map();
gltf.scene.traverse(node=>original.set(node,{position:node.position.clone(),quaternion:node.quaternion.clone(),geometry:node.geometry}));
const start=performance.now(),motion=new TexturingMotion(gltf.scene,scene,{routes}),constructionMs=performance.now()-start;
assert.equal(motion.stations.size,384);assert.equal(motion.batches.length,24);assert.equal(TEXTURING_PHASES.length,10);
assert.equal(motion.getState().visibleYarnCount,1);
assert.equal(motion.getState().progress,0,'first frame progress is finite without requiring rewind');
assert.ok(Array.from(motion.particles.instanceMatrix.array.slice(0,motion.particles.count*16)).every(Number.isFinite),'first-frame marker transforms');
for(const station of motion.stations.values()){
  assert.equal(extractYarnCenterline(station.originalGeometry).points.length,131);
  assert.ok(station.path.total>0);assert.ok(station.path.points.every(p=>p.toArray().every(Number.isFinite)));
}
// The visible pulse follows the actual tube, including the godet wraps and V path.
const first=motion.stations.get(1),p=new THREE.Vector3();samplePolyline(first.path,.5,p);assert.ok(p.distanceTo(first.path.points[0])>.1);
motion.setSelection({mode:'process',yarnMode:'all',stationIndex:1});motion.update(.7);container.updateMatrixWorld(true);
assert.equal(motion.getState().visibleYarnCount,384);assert.equal(motion.particles.count,1536);
assert.equal(motion.getState().affectedPositionCount,384);
assert.ok(Number.isFinite(motion.getState().progress));assert.ok(Array.from(motion.particles.instanceMatrix.array.slice(0,motion.particles.count*16)).every(Number.isFinite),'first-play marker transforms');
for(const rotor of motion.rotors)assert.ok(rotor.node.quaternion.angleTo(rotor.base)>1e-5,rotor.node.name);
for(const [node,base] of original)if(!motion.managedNodes.has(node)){
  assert.ok(node.position.distanceTo(base.position)<1e-9,node.name+' stationary translation');
  assert.ok(node.quaternion.angleTo(base.quaternion)<1e-7,node.name+' stationary rotation');
}
const paused=new Map(motion.rotors.map(r=>[r.node,r.node.quaternion.clone()]));const guidePaused=first.guide.position.clone();motion.update(.7);
for(const [node,q] of paused)assert.ok(q.angleTo(node.quaternion)<1e-7);assert.ok(first.guide.position.equals(guidePaused));
const pausedProgress=motion.getState().progress;motion.setSelection({running:false});motion.update(.9);assert.equal(motion.getState().progress,pausedProgress);assert.ok(first.guide.position.equals(guidePaused));motion.setSelection({running:true});
// Camshaft A owns both all 192 A-side traverses and their 192 take-up packages.
motion.setSelection({mode:'motor',motorAnchorId:'EFK_camshaft_drive_A',routeId:'camshaft_traverse',stationIndex:1,yarnMode:'single'});
const before=new Map(motion.rotors.map(r=>[r.node,r.node.quaternion.clone()]));motion.update(1.2);container.updateMatrixWorld(true);
assert.deepEqual(new Set(motion.activeRoutes.map(r=>r.id)),new Set(['camshaft_traverse','takeup']));assert.equal(motion.getState().affectedPositionCount,192);
let changedA=0,changedB=0;
for(const rotor of motion.rotors){const changed=rotor.node.quaternion.angleTo(before.get(rotor.node))>1e-6,context=driveObjectContext(rotor.node);if(changed&&context.machineSide==='A')changedA++;if(changed&&context.machineSide==='B')changedB++}
assert.ok(changedA>=384);assert.equal(changedB,0);
assert.equal(motion.highlightedObjects().size,1+1+48+192+192+192); // motor, shaft, cams, guides, drums, packages
// An oil pump never turns oil wheels or implies continuous yarn production.
motion.setSelection({mode:'motor',routeId:'oiling',motorAnchorId:'EFK_oil_circulation_drive'});
const oilBefore=new Map(motion.rotors.map(r=>[r.node,r.node.quaternion.clone()]));motion.update(1.8);
const oilChanged=motion.rotors.filter(r=>r.node.quaternion.angleTo(oilBefore.get(r.node))>1e-6);
assert.equal(oilChanged.length,1);assert.equal(oilChanged[0].kind,'motor');assert.equal(motion.particles.count,0);assert.match(motion.getState().phaseLabel,/停留/);
motion.setSelection({mode:'motor',routeId:'feed_g1',motorAnchorId:null});motion.update(2.0);assert.equal(motion.activeRoutes.length,0);assert.equal(motion.highlightedObjects().size,0);
// Station/side mapping and pause-safe restart.
motion.setSelection({mode:'process',side:'B',stationIndex:384,yarnMode:'single'});assert.equal(motion.getState().localPosition,192);assert.equal(motion.getState().section,16);
motion.update(0);for(const rotor of motion.rotors)assert.ok(rotor.node.quaternion.angleTo(rotor.base)<1e-7);
assert.ok(motion.stations.get(384).guide.position.equals(motion.stations.get(384).guideBase));
// Twelve actual yarn variants, both mirrored sides, every sampled stroke phase.
// Check guide radial envelope and the dynamic tail against the DTY package cylinder
// analytically, then actual triangles for the remaining selected station hardware.
motion.setSelection({mode:'process',yarnMode:'single'});
let samples=0,minimumGuideClearance=Infinity,minimumPackageClearance=Infinity;
const crossings=[];const ray=new THREE.Raycaster();
const sectionMeshes=new Map();
for(let phase=1;phase<=12;phase++){
  motion.update(phase*.241);container.updateMatrixWorld(true);
  for(const index of [...Array.from({length:12},(_,i)=>i+1),...Array.from({length:12},(_,i)=>193+i)]){
    const station=motion.stations.get(index),guide=station.guide.position;
    minimumGuideClearance=Math.min(minimumGuideClearance,Math.hypot(guide.x,guide.y)-.12-.0065);
    assert.ok(Math.abs(guide.z)<=.095001);
    const inverse=station.winder.matrixWorld.clone().invert(),tail=station.path.points.slice(-7).map(p=>p.clone().applyMatrix4(inverse));
    for(let j=1;j<tail.length;j++)for(let k=0;k<=20;k++){
      const point=tail[j-1].clone().lerp(tail[j],k/20);
      if(Math.abs(point.z)<=.1266)minimumPackageClearance=Math.min(minimumPackageClearance,Math.hypot(point.x,point.y)-.12-.0007);
    }
    if(index>12)continue; // mirror already analytically checked; exact source triangles below.
    if(!sectionMeshes.has(station.node.parent)){const objects=[];station.node.parent.traverse(o=>{if(o.isMesh&&o.userData.componentRole!=='continuous_yarn_path')objects.push(o)});sectionMeshes.set(station.node.parent,objects)}
    const meshes=sectionMeshes.get(station.node.parent),world=station.path.points.slice(-8);
    for(let j=1;j<world.length;j++){
      const d=world[j].clone().sub(world[j-1]),length=d.length();if(length<1e-7)continue;
      ray.set(world[j-1].clone().addScaledVector(d,1e-5/length),d.normalize());ray.far=length-2e-5;
      const hit=ray.intersectObjects(meshes,false)[0];if(hit)crossings.push({index,phase,segment:j,name:hit.object.name});samples++;
      ray.set(world[j].clone().addScaledVector(d,-1e-5),d.clone().negate());const reverse=ray.intersectObjects(meshes,false)[0];if(reverse)crossings.push({index,phase,segment:j,name:reverse.object.name,reverse:true});samples++;
    }
  }
}
assert.ok(minimumGuideClearance>.02);assert.ok(minimumPackageClearance>0);assert.deepEqual(crossings,[]);
// Rebuild world paths after normalization / explosion without altering local shape.
const beforePoint=first.path.points[0].clone();container.position.x+=.4;motion.markDirty();motion.update(2.892);
assert.ok(first.path.points[0].x-beforePoint.x>.39999);assert.ok(!motion.getStationBounds(1).isEmpty());
const timers=[];motion.setSelection({mode:'process',yarnMode:'all'});
for(let i=0;i<20;i++){const t=performance.now();motion.update(3+i*.016);timers.push(performance.now()-t)}
const report={testedAt:new Date().toISOString(),sha256,result:'pass',stations:384,sharedDynamicGeometries:24,actualTubeRings:131,phaseCount:10,constructionMs,meanCpuUpdateMs:timers.reduce((a,b)=>a+b,0)/timers.length,guideSamples:12*24,triangleSegmentChecks:samples,minimumGuideClearanceMetres:minimumGuideClearance,minimumDynamicYarnPackageClearanceMetres:minimumPackageClearance,crossings,regressions:['pause','rewind','all_384_paths','exact_motor_side','camshaft_and_takeup','oil_fluid_not_rotation','unknown_motor_no_fallback','station_384','world_transform_dirty','dispose_restoration']};
motion.dispose();motion.dispose();
for(const [node,base] of original){assert.ok(node.position.distanceTo(base.position)<1e-9);assert.ok(node.quaternion.angleTo(base.quaternion)<1e-7);assert.equal(node.geometry,base.geometry)}
assert.equal(scene.children.includes(motion.group),false);
await fs.writeFile('qa/texturing-motion-validation.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
