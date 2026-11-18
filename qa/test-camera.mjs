import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {registerHooks} from 'node:module';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const directory=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
registerHooks({resolve(specifier,context,next){if(specifier==='three')return {url:new URL('../dist/vendor/three.module.js',import.meta.url).href,shortCircuit:true};return next(specifier,context)}});
const THREE=await import('../dist/vendor/three.module.js');
const {GLTFLoader}=await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {fitPerspectiveBounds,boundsCorners}=await import('../dist/camera-fit.js');
const {normalizeImportedModel,worldModelBounds}=await import('../dist/scene-geometry.js');
const filenames=(await fs.readdir(path.join(directory,'dist/assets/models'))).filter(f=>f.endsWith('.glb')).sort();
const processData=JSON.parse(await fs.readFile(path.join(directory,'dist/process-data.json'),'utf8'));
const expectedFiles=[...processData.stages.map(stage=>`${stage.id}.glb`),'motor.glb'].sort();
assert.deepEqual(filenames,expectedFiles,'Expected a separate model for every catalog equipment plus the archived motor');
const sources=new Map(),report={testedAt:new Date().toISOString(),models:[],normalizationCases:0,projectionCases:0,groundClearanceCases:0,minimumDynamicGroundClearance:null,originalGroundConflicts:[],viewports:[[800,500],[390,380],[330,480],[1200,400]],azimuths:24,elevations:[-60,0,35,75,89.99],explode:[0,.5,1],animationPhases:[0,Math.PI/3,Math.PI*1.1],failures:[]};
const loader=new GLTFLoader();
for(const filename of filenames){
  const bytes=await fs.readFile(path.join(directory,'dist/assets/models',filename));
  const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  sources.set(filename,gltf.scene);
  report.models.push({file:filename,sha256:createHash('sha256').update(bytes).digest('hex'),meshes:0});
  gltf.scene.traverse(node=>{if(node.isMesh)report.models.at(-1).meshes++});
}
// Reproduce the bug: retain a previous model's parent/world transform, then switch repeatedly.
const container=new THREE.Group();
container.position.set(14,-8,23);container.scale.setScalar(6);container.updateMatrixWorld(true);
const sequence=[...filenames,...filenames.toReversed(),...filenames.flatMap(f=>['motor.glb',f])];
for(const filename of sequence){
  container.clear();const root=sources.get(filename).clone(true);
  normalizeImportedModel(root,container);
  const bounds=worldModelBounds(container),size=bounds.getSize(new THREE.Vector3());
  assert.ok(Math.abs(bounds.min.y)<1e-6,`${filename}: floor height ${bounds.min.y}`);
  assert.ok(Math.abs(Math.max(size.x,size.y,size.z)-7.2)<1e-6,`${filename}: normalized extent ${size.toArray()}`);
  assert.ok(Math.abs((bounds.min.x+bounds.max.x)/2)<1e-6&&Math.abs((bounds.min.z+bounds.max.z)/2)<1e-6,`${filename}: scene not centered`);
  report.normalizationCases++;
}
const directions=[];
for(let az=0;az<24;az++)for(const elevation of report.elevations){
  const angle=az/24*Math.PI*2,phi=elevation*Math.PI/180;
  directions.push([Math.cos(phi)*Math.sin(angle),Math.sin(phi),Math.cos(phi)*Math.cos(angle)]);
}
directions.push([0,1,1e-6],[0,-1,-1e-6]);
for(const filename of filenames){
  container.clear();const root=sources.get(filename).clone(true);normalizeImportedModel(root,container);
  const animated=[],exploded=[];
  root.traverse(object=>{
    if(object.userData.explode)exploded.push({object,position:object.position.clone()});
    if(['x','y','z'].includes(object.userData.spinAxis))animated.push({object,rotation:object.rotation.clone()});
  });
  for(const amount of report.explode)for(const phase of report.animationPhases){
    for(const {object,position} of exploded)object.position.copy(position).addScaledVector(new THREE.Vector3(...object.userData.explode),amount);
    for(const {object,rotation} of animated){object.rotation.copy(rotation);object.rotation[object.userData.spinAxis]+=phase}
    const bounds=worldModelBounds(container),plain={min:bounds.min.toArray(),max:bounds.max.toArray()};
    // Precise vertex bounds independently check the dynamic ground against the conservative scene bounds.
    const vertexBounds=new THREE.Box3().setFromObject(container,true);
    const dynamicFloor=bounds.min.y-.035,clearance=vertexBounds.min.y-dynamicFloor;
    assert.ok(clearance>=.034999,`${filename}: dynamic floor intersects geometry after explode=${amount}, phase=${phase}`);
    report.minimumDynamicGroundClearance=Math.min(report.minimumDynamicGroundClearance??Infinity,clearance);
    report.groundClearanceCases++;
    if(vertexBounds.min.y<-.035)report.originalGroundConflicts.push({file:filename,explode:amount,phase,minimumY:vertexBounds.min.y});
    for(const [width,height] of report.viewports)for(const direction of directions){
      const fit=fitPerspectiveBounds(plain,{direction,width,height,padding:20});
      // Independent projection through the actual Three.js camera, not the fitter's inverse equations.
      const camera=new THREE.PerspectiveCamera(37,width/height,fit.near,fit.far);
      camera.position.fromArray(fit.position);camera.lookAt(...fit.center);camera.updateMatrixWorld(true);
      for(const point of boundsCorners(plain)){
        const projected=new THREE.Vector3(...point).project(camera);
        if(Math.abs(projected.x)>fit.safeX+1e-7||Math.abs(projected.y)>fit.safeY+1e-7||projected.z < -1||projected.z>1){
          throw new Error(`${filename} clipped: explode=${amount} phase=${phase} viewport=${width}x${height} direction=${direction} projection=${projected.toArray()}`);
        }
      }
      report.projectionCases++;
    }
  }
  console.log(`${filename}: normalization and full-angle bounds pass`);
}
report.result='pass';
await fs.writeFile(path.join(directory,'qa/camera-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({result:report.result,models:report.models.length,normalizationCases:report.normalizationCases,projectionCases:report.projectionCases,groundClearanceCases:report.groundClearanceCases,oldGroundConflicts:report.originalGroundConflicts.length}));
