import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';

const threeURL=new URL('../dist/vendor/three.module.js',import.meta.url);
registerHooks({resolve(specifier,context,next){
  return specifier==='three'?{url:threeURL.href,shortCircuit:true}:next(specifier,context);
}});
const THREE=await import(threeURL);
const {GLTFLoader}=await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {DriveView,buildDriveBranches,driveObjectContext,resolveDriveRoutes,scopeDriveRoute}=await import('../dist/drive-view.js');
const {RotorMotion}=await import('../dist/rotor-motion.js');
const bytes=await fs.readFile('dist/assets/models/rotor_spinning.glb');
const {scene}=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
scene.updateMatrixWorld(true);
const size=new THREE.Box3().setFromObject(scene,true).getSize(new THREE.Vector3());
const close=(a,b,tolerance,description)=>assert.ok(Math.abs(a-b)<=tolerance,description+' ('+a+' / '+b+')');
close(size.x,11.453,.002,'Machine length in metres');
close(size.y,2.950,.002,'Machine height');
close(size.z,2.536,.004,'Maximum width across the two robot housings');

const nodes=[];
scene.traverse(node=>nodes.push(node));
const stations=nodes.filter(n=>n.userData.sidePosition);
assert.equal(stations.length,48);
assert.equal(nodes.filter(n=>n.userData.componentRole==='doff_robot').length,2);
assert.equal(nodes.filter(n=>/^R70_conveyor_[AB]$/.test(n.userData.driveAnchorId)).length,2);
for(const side of ['A','B'])for(const section of [1,2]){
  const heads=stations.filter(n=>n.userData.machineSide===side&&n.userData.sectionIndex===section)
    .sort((a,b)=>a.userData.sidePosition-b.userData.sidePosition);
  assert.equal(heads.length,12);
  for(let i=1;i<heads.length;i++)close(heads[i].position.x-heads[i-1].position.x,.230,1e-6,'Same-side station pitch');
}
const data=JSON.parse(await fs.readFile('dist/drive-chains.json','utf8')).items.find(item=>item.id==='rotor_spinning');
const routes=resolveDriveRoutes(scene,data.routes);
const motorRoutes=routes.filter(r=>r.motors.length);
assert.deepEqual(motorRoutes.map(r=>r.id),['feed','opening','cup','package','guide']);
const anchors=new Set();
for(const route of motorRoutes){
  assert.equal(route.motors.length,48);
  for(const [i,motor] of route.motors.entries()){
    const key='R70_'+(i<24?'A':'B')+String(i%24+1).padStart(2,'0')+'_'+route.id;
    assert.equal(motor.userData.driveAnchorId,key+'_motor');
    assert.equal(motor.userData.internalGeometryModeled,false);
    const scoped=scopeDriveRoute(route,motor);
    assert.deepEqual(scoped.steps.map(s=>s.objects.map(o=>o.userData.driveAnchorId)),[['_motor'],['_out'],['_load']].map(([suffix])=>[key+suffix]));
    anchors.add(key);
  }
  const edges=buildDriveBranches(route);assert.equal(edges.length,96);
  for(const edge of edges)assert.equal(driveObjectContext(edge.from).positionIndex,driveObjectContext(edge.to).positionIndex);
}
assert.equal(anchors.size,240);
const unassigned=routes.filter(r=>!r.motors.length);
assert.deepEqual(unassigned.map(r=>[r.id,r.steps.at(-1).objects.length]),[['delivery',48],['vacuum',1],['convey',2],['doff',2]]);
for(const route of unassigned)assert.equal(buildDriveBranches(route).length,0);

const motion=new RotorMotion(scene);
const guideRoute=routes.find(r=>r.id==='guide');
guideRoute.motorIndex=47;motion.select(guideRoute);
assert.equal(motion.activeGuides.length,1);assert.equal(motion.activeGuides[0].position,48);
const moving=motion.activeGuides[0];
const other=motion.guides.find(g=>g.position===47);
const yarnEnds=mesh=>{
  const axis=new THREE.Vector3(0,1,0).applyQuaternion(mesh.quaternion).multiplyScalar(.5*mesh.scale.y);
  return [mesh.position.clone().sub(axis),mesh.position.clone().add(axis)];
};
const incoming=moving.yarn.find(l=>l.mesh.userData.travelYarn==='in');
const outgoing=moving.yarn.find(l=>l.mesh.userData.travelYarn==='out');
const fixedNip=yarnEnds(incoming.mesh)[0];
const eye=moving.guide.children.find(n=>n.userData.label==='导纱眼');
assert.ok(eye);
const hiddenLink=buildDriveBranches(scopeDriveRoute(guideRoute,47)).find(e=>e.unmodeled);
const center=n=>new THREE.Box3().setFromObject(n).getCenter(new THREE.Vector3());
const start=center(hiddenLink.from);
const lineGeometry=new THREE.BufferGeometry().setFromPoints([start,center(hiddenLink.to)]);
const lines=new THREE.LineSegments(lineGeometry,new THREE.LineDashedMaterial());
lines.computeLineDistances();
const batches={branchBatches:[{route:guideRoute,unmodeled:true,lines,visibleEdges:[hiddenLink]}]};
for(let frame=0;frame<64;frame++){
  motion.update(1/30);
  const [nip,inEnd]=yarnEnds(incoming.mesh),[outStart]=yarnEnds(outgoing.mesh);
  const eyePosition=eye.position.clone().add(moving.guide.position);
  assert.ok(nip.distanceTo(fixedNip)<1e-6);
  assert.ok(inEnd.distanceTo(outStart)<1e-6&&inEnd.distanceTo(eyePosition)<1e-6,'Both strands stay inside the moving eye');
  assert.equal(other.guide.position.x,other.rest);
  moving.guide.updateWorldMatrix(true,true);
  DriveView.prototype.updateTraverseEndpoints.call(batches);
  const end=new THREE.Vector3().fromBufferAttribute(lineGeometry.attributes.position,1);
  assert.ok(end.distanceTo(center(moving.guide))<1e-6,'Displayed drive endpoint follows the actual B-side guide');
  close(lineGeometry.attributes.lineDistance.getX(1),start.distanceTo(end),1e-6,'Dashed link length');
}
assert.ok(Math.abs(moving.guide.position.x-moving.rest)>.01);
const atPause=moving.guide.position.x;motion.update(0);assert.equal(moving.guide.position.x,atPause);
const cup=routes.find(r=>r.id==='cup');cup.motorIndex=47;motion.select(cup);
assert.equal(motion.activeGuides.length,0);assert.ok(motion.activeRotors.every(p=>p.position===48&&p.kind==='cup'));
assert.ok(motion.activeRotors.some(p=>p.node.userData.anchorPart==='cup_load'));
motion.update(.25);
assert.equal(moving.guide.position.x,atPause);
for(const entry of motion.activeRotors)assert.ok(entry.rest.angleTo(entry.node.quaternion)>.01);
motion.select(unassigned[0]);assert.equal(motion.activeRotors.length,0);assert.equal(motion.activeGuides.length,0);
motion.select(null);assert.equal(motion.activeGuides.length,48);
motion.dispose();
assert.equal(moving.guide.position.x,moving.rest);
for(const l of moving.yarn){assert.ok(l.mesh.position.equals(l.position));assert.ok(l.mesh.quaternion.equals(l.quaternion));assert.ok(l.mesh.scale.equals(l.scale))}
console.log(JSON.stringify({result:'pass',positions:stations.length,positionMotors:anchors.size,unassignedLoads:4,
  checkedYarnFrames:64,dimensionsMetres:{length:size.x,height:size.y,width:size.z}}));
