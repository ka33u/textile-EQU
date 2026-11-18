import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
registerHooks({resolve(specifier,context,next){
  if(specifier==='three')return {url:pathToFileURL(process.cwd()+'/dist/vendor/three.module.js').href,shortCircuit:true};
  return next(specifier,context);
}});
const THREE=await import('../dist/vendor/three.module.js');
const {GLTFLoader}=await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {DriveView,resolveDriveRoutes,scopeDriveRoute,motorDriveRoutes,uniqueDriveMotors,driveObjectContext,buildDriveBranches,layoutDriveMarkers}=await import('../dist/drive-view.js');
const {fitPerspectiveBounds}=await import('../dist/camera-fit.js');
class Element{
  constructor(){this.children=[];this.style={};this.dataset={};this.attributes={};this.events={};this.classList={add(){},toggle(){}}}
  append(child){this.children.push(child);child.parent=this}
  setAttribute(key,value){this.attributes[key]=String(value)}
  addEventListener(key,value){this.events[key]=value}
  remove(){if(this.parent)this.parent.children=this.parent.children.filter(item=>item!==this)}
}
globalThis.document={createElement:()=>new Element(),createElementNS:()=>new Element()};
const data=JSON.parse(await fs.readFile('dist/drive-chains.json','utf8'));
const record=data.items.find(item=>item.id==='texturing');
const bytes=await fs.readFile('dist/assets/models/texturing.glb');
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
gltf.scene.updateMatrixWorld(true);
const routes=resolveDriveRoutes(gltf.scene,record.routes),motors=uniqueDriveMotors(routes);
assert.deepEqual(motors.map(({anchorId})=>anchorId),[
  'EFK_friction_drive_A','EFK_friction_drive_B','EFK_W3_drive_A','EFK_W3_drive_B',
  'EFK_camshaft_drive_A','EFK_camshaft_drive_B','EFK_oil_circulation_drive'
]);
const expected={false_twist:[1,1,16,576],w3:[1,1,16],camshaft_traverse:[1,1,48,192],takeup:[1,1,0,192,192],oiling:[1,1,0,2,384]};
const counts=[];
for(const entry of motors){
  const scoped=motorDriveRoutes(routes,entry.motor),side=entry.anchorId.match(/_([AB])$/)?.[1];
  assert.equal(scoped.length,entry.anchorId.includes('camshaft')?2:1);
  for(const route of scoped){
    const actual=route.steps.map(step=>step.objects.length);
    if(expected[route.id])assert.deepEqual(actual,expected[route.id],`${entry.anchorId}/${route.id}: complete selected station scope`);
    for(const step of route.steps)for(const object of step.objects){
      const context=driveObjectContext(object);
      if(side)assert.equal(context.machineSide,side,`${object.name}: opposite/unknown side must not enter motor scope`);
    }
    const edges=buildDriveBranches(route);
    for(const edge of edges){
      const from=driveObjectContext(edge.from),to=driveObjectContext(edge.to);
      if(from.machineSide!==undefined&&to.machineSide!==undefined)assert.equal(from.machineSide,to.machineSide);
      if(from.sectionIndex!==undefined&&to.sectionIndex!==undefined)assert.equal(from.sectionIndex,to.sectionIndex);
      assert.equal(edge.unmodeled,route.steps[edge.stepIndex].connectionStatus==='unmodeled');
    }
    for(let i=1;i<route.steps.length;i++){
      if(!route.steps[i-1].objects.length||!route.steps[i].objects.length)assert.ok(!edges.some(edge=>edge.stepIndex===i),'No bridge across empty step');
    }
    counts.push({motor:entry.anchorId,route:route.id,stepCounts:actual,edges:edges.length});
  }
}
const scene=new THREE.Scene();scene.add(gltf.scene);const events=[];
const view=new DriveView(scene,new Element(),(...args)=>events.push(args));view.setModel(gltf.scene,record);view.setVisible(true);
assert.equal(view.markers.length,7);assert.equal(view.stationDots.length,0);
assert.deepEqual(view.markers.map(marker=>marker.button.textContent),['M1','M2','M3','M4','M5','M6','M7']);
view.markers[4].button.events.click();assert.equal(events.at(-1)[2].motor,true);assert.equal(view.activeMotor.userData.driveAnchorId,'EFK_camshaft_drive_A');
assert.deepEqual(view.selectedMotorRoutes().map(route=>route.id),['camshaft_traverse','takeup']);
assert.equal(view.highlightedObjects().size,1+1+48+192+192+192,'Same-motor camshaft and takeup loads highlighted, shared motor/shaft counted once');
assert.ok([...view.highlightedObjects()].every(object=>driveObjectContext(object).machineSide==='A'));
view.setActiveMotor('false_twist',1);
assert.equal(view.highlightedObjects().size,1+1+16+576,'All 576 selected-side shafts, not one nearest shaft');
assert.ok([...view.highlightedObjects()].every(object=>driveObjectContext(object).machineSide==='B'));
view.setActive('feed_g1');assert.equal(view.highlightedObjects().size,384,'Unknown motor does not hide known load objects or substitute a motor');
view.setActiveMotor('takeup',0);
const camera=new THREE.PerspectiveCamera(40,1,.01,500);camera.position.set(20,20,30);camera.lookAt(0,2,0);camera.updateMatrixWorld(true);
view.update(camera,800,800,0);
const versions=()=>view.branchBatches.map(batch=>[batch.lines.geometry.attributes.position.version,batch.heads?.instanceMatrix.version,batch.lines.geometry.drawRange.count,batch.heads?.count]);
const initialVersions=versions();const transforms=motors.map(({motor})=>motor.matrixWorld.toArray());
for(let frame=1;frame<=120;frame++)view.update(camera,800,800,frame/60);
assert.deepEqual(versions(),initialVersions,'120 animation frames must not upload branch vertices or instance matrices');
assert.deepEqual(motors.map(({motor})=>motor.matrixWorld.toArray()),transforms,'Drive overlays do not rotate or move motor housings');
for(const batch of view.branchBatches){
  if(batch.unmodeled){assert.ok(batch.lines.material.isLineDashedMaterial);assert.equal(batch.heads,null);assert.equal(batch.lines.material.uniforms,undefined)}
  else{
    assert.equal(batch.lines.material.uniforms.elapsed.value,2);
    assert.equal(batch.lines.material.uniforms.pulseEnabled.value,1);
    assert.match(batch.lines.material.fragmentShader,/vProgress-elapsed\*\.48/,'Pulse travels from upstream progress 0 to downstream 1');
  }
}
view.update(camera,800,800,2);assert.deepEqual(versions(),initialVersions,'Paused time does not rebuild');
view.setActive(null);view.update(camera,800,800,2);
for(const batch of view.branchBatches)if(!batch.unmodeled)assert.ok(batch.lines.material.uniforms.opacity.value<=.15,'All-machine overlay remains subdued');
view.setActiveMotor('false_twist',0);view.update(camera,800,800,2);
for(const batch of view.branchBatches)if(batch.lines.visible){
  assert.equal(batch.route.id,'false_twist');
  assert.ok(batch.visibleEdges.every(edge=>driveObjectContext(edge.from).machineSide==='A'&&driveObjectContext(edge.to).machineSide==='A'));
}
const emptyFixture={id:'empty',motors:[],motorIndex:0,steps:[{role:'motor',objects:[]},{role:'transmission',objects:[]},{role:'load',objects:[motors[0].motor]}]};
assert.equal(buildDriveBranches(emptyFixture).length,0);
assert.equal(scopeDriveRoute(emptyFixture).motors.length,0);
assert.deepEqual(motorDriveRoutes(routes,null),[]);
const assertLayout=(positions,width,height)=>{
  for(let i=0;i<positions.length;i++){
    const p=positions[i];
    assert.ok(p.x-p.width/2>=7.99&&p.x+p.width/2<=width-7.99,'Label stays inside horizontal canvas edges');
    assert.ok(p.y-p.height/2>=7.99&&p.y+p.height/2<=height-7.99,'Label stays inside vertical canvas edges');
    for(let j=0;j<i;j++){
      const q=positions[j];
      assert.ok(Math.abs(p.x-q.x)>=(p.width+q.width)/2+6.99||Math.abs(p.y-q.y)>=(p.height+q.height)/2+6.99,'Every label pair retains a visible gap');
    }
  }
};
let labelLayouts=0;
for(const [width,height] of [[320,300],[390,340],[960,600],[1440,900]]){
  // All seven labels collide at each corner and at center before placement.
  for(const [x,y] of [[0,0],[width,0],[0,height],[width,height],[width/2,height/2]]){
    const labels=Array.from({length:7},(_,index)=>({x,y,width:index%2?36:45,height:32}));
    assertLayout(layoutDriveMarkers(labels,width,height),width,height);labelLayouts++;
  }
  const bounds=new THREE.Box3().setFromObject(gltf.scene);
  const directions=[[.73,.47,.82],[1,0,0],[-1,0,0],[0,0,1],[0,0,-1],[0,1,.001],[.8,.4,-.7]];
  view.setActive(null);
  for(const direction of directions){
    const fit=fitPerspectiveBounds({min:bounds.min.toArray(),max:bounds.max.toArray()},{direction,width,height,padding:24});
    const cam=new THREE.PerspectiveCamera(37,width/height,fit.near,fit.far);cam.position.fromArray(fit.position);cam.lookAt(...fit.center);cam.updateMatrixWorld(true);
    view.update(cam,width,height,2);
    const positions=view.markers.map(({button,line})=>{
      assert.equal(button.hidden,false,'All seven eFK labels remain available in fitted views');
      const match=button.style.transform.match(/^translate\(([-\d.e]+)px,([-\d.e]+)px\)/);
      assert.ok(match);const x=Number(match[1]),y=Number(match[2]);
      assert.equal(Number(line.attributes.x2),x);assert.equal(Number(line.attributes.y2),y);
      assert.ok(Number.isFinite(Number(line.attributes.x1))&&Number.isFinite(Number(line.attributes.y1)),'Leader retains motor anchor');
      return {x,y,width:36,height:32};
    });
    assertLayout(positions,width,height);labelLayouts++;
  }
}
view.clear();assert.equal(view.markers.length,0);assert.equal(view.branchBatches.length,0);
// Preserve the equipment catalog contract, including old three-argument updates,
// unknown motors, independently clickable repeated stations and complete graphs.
let legacyModels=0,legacyBranches=0;
for(const item of data.items){
  const modelBytes=await fs.readFile(`dist/assets/models/${item.id}.glb`);
  const model=await new GLTFLoader().parseAsync(modelBytes.buffer.slice(modelBytes.byteOffset,modelBytes.byteOffset+modelBytes.byteLength),'');
  model.scene.updateMatrixWorld(true);
  const legacyView=new DriveView(new THREE.Scene(),new Element(),()=>{});legacyView.setModel(model.scene,item);legacyView.setVisible(true);legacyView.update(camera,800,800);
  if(item.id==='sizing')assert.equal(legacyView.stationDots.length,12);
  if(item.id==='winding')assert.equal(legacyView.stationDots.length,96);
  if(item.id==='inspection')assert.equal(uniqueDriveMotors(legacyView.routes).length,0);
  for(const route of legacyView.routes){
    const edges=buildDriveBranches(route);legacyBranches+=edges.length;
    for(let i=1;i<route.steps.length;i++){
      const from=route.steps[i-1].objects,to=route.steps[i].objects,segment=edges.filter(edge=>edge.stepIndex===i);
      if(!from.length||!to.length){assert.equal(segment.length,0);continue}
      assert.deepEqual(new Set(segment.map(edge=>edge.from)),new Set(from),`${item.id}/${route.id}: every upstream object retained`);
      assert.deepEqual(new Set(segment.map(edge=>edge.to)),new Set(to),`${item.id}/${route.id}: every downstream object retained`);
    }
  }
  for(const batch of legacyView.branchBatches)if(!batch.unmodeled)assert.equal(batch.lines.material.uniforms.pulseEnabled.value,0,'Legacy static update remains static');
  legacyView.clear();legacyModels++;
  model.scene.traverse(node=>{node.geometry?.dispose();for(const material of (Array.isArray(node.material)?node.material:[node.material]))material?.dispose()});
}
assert.equal(legacyModels,JSON.parse(await fs.readFile('dist/process-data.json','utf8')).stages.length);
console.log(JSON.stringify({result:'pass',motors:7,scopedRoutes:counts,legacyModels,legacyBranches,labelLayouts,animationFrames:120,vertexAndMatrixReuploads:0,unknownConnections:'dashed; empty steps never bridged'},null,2));
