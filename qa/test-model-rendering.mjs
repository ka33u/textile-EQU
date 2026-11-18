import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';

registerHooks({resolve(specifier,context,next){
  if(specifier==='three')return {url:new URL('../dist/vendor/three.module.js',import.meta.url).href,shortCircuit:true};
  return next(specifier,context);
}});
const THREE=await import('three');
const {GLTFLoader}=await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {ModelBatches,ModelMaterials,PICK_LAYER}=await import('../dist/model-rendering.js');
const {normalizeImportedModel}=await import('../dist/scene-geometry.js');
const {TexturingMotion}=await import('../dist/texturing-motion.js');
const {resolveDriveRoutes}=await import('../dist/drive-view.js');
const rootURL=new URL('../dist/',import.meta.url),modelsURL=new URL('assets/models/',rootURL);
const records=JSON.parse(await fs.readFile(new URL('drive-chains.json',rootURL))).items;
const camera=new THREE.PerspectiveCamera(),raycaster=new THREE.Raycaster();
const local=new THREE.Matrix4(),world=new THREE.Matrix4(),sphere=new THREE.Sphere();
let modelCount=0,instances=0,mirrors=0;

function checkDraws(batches,meshes){
  batches.group.updateWorldMatrix(true,true);
  const represented=new Set(meshes.filter(mesh=>camera.layers.test(mesh.layers)));
  for(const {draw,nodes,order,mirrored} of batches.batches){
    for(let slot=0;slot<draw.count;slot++){
      const mesh=nodes[order?order[slot]:slot];
      assert.equal(represented.has(mesh),false,'A component has multiple draw submissions');
      represented.add(mesh);assert.equal(draw.geometry,mesh.geometry);assert.equal(draw.material,mesh.material);
      draw.getMatrixAt(slot,local);world.multiplyMatrices(draw.matrixWorld,local);
      assert.ok(local.determinant()>0,'Reflections must be on the batch, not in its instances');
      assert.ok(world.elements.every((v,i)=>Math.abs(mesh.matrixWorld.elements[i]-v)<2e-5),'Wrong placement: '+mesh.name);
      if(draw.frustumCulled){
        sphere.copy(draw.geometry.boundingSphere).applyMatrix4(local);
        assert.ok(draw.boundingSphere.center.distanceTo(sphere.center)+sphere.radius<=draw.boundingSphere.radius+2e-5,'Culling could hide '+mesh.name);
      }
      instances++;if(mirrored)mirrors++;
    }
  }
  assert.equal(represented.size,meshes.length,'Missing source components');
}
for(const name of await fs.readdir(modelsURL)){
  if(!name.endsWith('.glb'))continue;
  const bytes=await fs.readFile(new URL(name,modelsURL));
  const {scene:root}=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  const scene=new THREE.Scene(),content=new THREE.Group();scene.add(content);normalizeImportedModel(root,content);
  const meshes=[],moving=new Set(),explode=[],shells=new Set();
  root.traverse(node=>{
    if(node.isMesh)meshes.push(node);
    if(node.userData.spinAxis)moving.add(node);
    if(Array.isArray(node.userData.explode))explode.push(node);
    if(node.userData.shell||node.userData.group==='shell')shells.add(node);
  });
  const isEFK=name==='texturing.glb',drive=records.find(item=>item.id==='texturing');
  let motion;
  if(isEFK)motion=new TexturingMotion(root,scene,{routes:resolveDriveRoutes(root,drive.routes)});
  const probe=meshes.find(mesh=>mesh.geometry.getAttribute('position').count>4);
  if(!probe.geometry.boundingSphere)probe.geometry.computeBoundingSphere();
  const center=probe.geometry.boundingSphere.center.clone().applyMatrix4(probe.matrixWorld);
  raycaster.set(center.clone().add(new THREE.Vector3(0,0,20)),new THREE.Vector3(0,0,-1));
  raycaster.layers.set(0);
  const referenceHit=raycaster.intersectObjects(meshes,false)[0]?.object;
  const materials=new ModelMaterials(meshes),base=meshes.map(mesh=>mesh.material);
  const batches=new ModelBatches(scene,root,meshes,motion?.managedNodes||moving);
  raycaster.layers.enable(PICK_LAYER);
  assert.equal(raycaster.intersectObjects(meshes,false)[0]?.object,referenceHit,'Picking changed under instancing');
  checkDraws(batches,meshes);
  if(isEFK){
    motion.update(.3);batches.update();checkDraws(batches,meshes);
    const motor=motion.routes.flatMap(route=>route.motors).find(m=>m.userData.driveAnchorId==='EFK_friction_drive_B');
    motion.setSelection({mode:'motor',motorAnchorId:motor.userData.driveAnchorId,stationIndex:384});
    const state={wire:false,xray:false,motorTint:true,dimMotor:true,dimYarn:false,selected:motor,highlighted:motion.highlightedObjects(),yarns:new Set(),shells};
    assert.ok(materials.apply(state));assert.equal(materials.apply(state),false,'Unchanged selection should reuse materials');
    assert.ok(meshes.some(mesh=>mesh.material.transparent));assert.ok(batches.dynamic.size>0);
    batches.rebuild();assert.ok(batches.sorted.length>0);
    for(const x of [-1,1]){
      camera.position.set(x,1,1);camera.lookAt(0,0,0);camera.updateMatrixWorld();
      batches.sortFades(camera);checkDraws(batches,meshes);
      for(const {order,depth} of batches.sorted)assert.ok(order.every((n,i)=>!i||depth[order[i-1]]<=depth[n]),'Faded surfaces must be depth-sorted');
    }
    assert.equal(motion.getState().affectedPositionCount,192);
    assert.equal(motion.getState().stationIndex,384);
    assert.ok(materials.apply({...state,xray:true,wire:true}));
    batches.rebuild();
  }
  for(const node of explode)node.position.addScaledVector(new THREE.Vector3(...node.userData.explode),1);
  batches.update(true);batches.sortFades(camera);checkDraws(batches,meshes);
  batches.dispose();materials.dispose();motion?.dispose();
  meshes.forEach((mesh,i)=>{assert.equal(mesh.layers.mask,1);assert.equal(mesh.material,base[i])});
  assert.equal(scene.children.length,1,'Rendering resources retained after detach');
  modelCount++;
}
assert.ok(mirrors>0);
console.log(JSON.stringify({modelCount,instancePlacements:instances,mirroredPlacements:mirrors,result:'pass'}));
