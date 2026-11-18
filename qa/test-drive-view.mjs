import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
registerHooks({resolve(specifier,context,next){if(specifier==='three')return {url:pathToFileURL(process.cwd()+'/dist/vendor/three.module.js').href,shortCircuit:true};return next(specifier,context)}});
const THREE=await import('../dist/vendor/three.module.js');
const {GLTFLoader}=await import('../dist/vendor/addons/loaders/GLTFLoader.js');
const {resolveDriveRoutes,driveRoutePoints,buildDriveBranches,exteriorDriveDirection,DriveView}=await import('../dist/drive-view.js');
const {normalizeImportedModel,worldModelBounds}=await import('../dist/scene-geometry.js');
const data=JSON.parse(await fs.readFile('dist/drive-chains.json','utf8'));
const provenance=JSON.parse(await fs.readFile('dist/equipment-provenance.json','utf8'));
const processData=JSON.parse(await fs.readFile('dist/process-data.json','utf8'));
assert.deepEqual(new Set(data.items.map(item=>item.id)),new Set(processData.stages.map(item=>item.id)),'Every catalog equipment has its own drive record');
const report={testedAt:new Date().toISOString(),assetVersion:provenance.assetVersion,modelCases:[],routeCases:0,stepCases:0,emptySteps:0,motorStations:0,finitePathPositions:0,branchEdges:0,unmodeledEdges:0,regressions:[],failures:[]};
class Element {
 constructor(){this.children=[];this.style={};this.dataset={};this.attributes={};this.events={};this.hidden=false;this.classList={add:()=>{},toggle:()=>{}}}
 append(child){this.children.push(child);child.parent=this}
 setAttribute(key,value){this.attributes[key]=String(value)}
 addEventListener(event,listener){this.events[event]=listener}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(child=>child!==this)}
}
globalThis.document={createElement:()=>new Element(),createElementNS:()=>new Element()};
const {fitPerspectiveBounds}=await import('../dist/camera-fit.js');
const loader=new GLTFLoader();
for(const item of data.items){
 const bytes=await fs.readFile(`dist/assets/models/${item.id}.glb`),sha256=createHash('sha256').update(bytes).digest('hex');
 assert.equal(sha256,provenance.assets[item.id].sha256,item.id);
 const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 const parent=new THREE.Group();normalizeImportedModel(gltf.scene,parent);parent.updateMatrixWorld(true);
 const routes=resolveDriveRoutes(gltf.scene,item.routes),allMotors=[];gltf.scene.traverse(node=>{if(node.userData.driveRole==='motor')allMotors.push(node)});
 const resolvedMotors=new Set(routes.flatMap(route=>route.motors));
 assert.deepEqual(new Set(allMotors),resolvedMotors,`${item.id}: every actual motor assembly belongs to a route`);
 for(const route of routes){
  report.routeCases++;
  const branches=buildDriveBranches(route);report.branchEdges+=branches.length;report.unmodeledEdges+=branches.filter(edge=>edge.unmodeled).length;
  for(let i=1;i<route.steps.length;i++){
   const from=route.steps[i-1],to=route.steps[i],edges=branches.filter(edge=>edge.stepIndex===i);
   if(!from.objects.length||!to.objects.length){assert.equal(edges.length,0);continue}
   assert.deepEqual(new Set(edges.map(edge=>edge.from)),new Set(from.objects),`${item.id}/${route.id}: upstream branch omitted`);
   assert.deepEqual(new Set(edges.map(edge=>edge.to)),new Set(to.objects),`${item.id}/${route.id}: downstream branch omitted`);
   assert.ok(edges.every(edge=>edge.unmodeled===(to.connectionStatus==='unmodeled')));
  }
  for(const step of route.steps){
   report.stepCases++;
   if(step.anchorIds?.length){
    assert.equal(step.objects.length,step.anchorIds.length,`${item.id}/${route.id}: exact anchor count`);
    for(const id of step.anchorIds)assert.ok(step.objects.some(node=>node.userData.driveAnchorId===id||node.name===id||node.name===THREE.PropertyBinding.sanitizeNodeName(id)),`${item.id}/${route.id}: ${id}`);
   } else if(step.match?.length)assert.ok(step.objects.length,`${item.id}/${route.id}: selector missing`);
   else{assert.equal(step.objects.length,0);report.emptySteps++}
  }
  const visited=new Set();
  for(let i=0;i<Math.max(1,route.motors.length);i++){
   route.motorIndex=i;const points=driveRoutePoints(route);
   for(const point of points){if(point.object){assert.ok(point.point.toArray().every(Number.isFinite));report.finitePathPositions++}else assert.equal(point.point,null)}
   if(route.motors.length){visited.add(points.find(x=>x.step.role==='motor'&&x.object)?.object)}
  }
  assert.equal(visited.size,route.motors.length,`${item.id}/${route.id}: each repeated motor is individually addressable`);
  const fixture={selectedRoute:()=>route,geometryDirty:false};
  route.motorIndex=0;DriveView.prototype.moveStation.call(fixture,-1);assert.equal(route.motorIndex,Math.max(0,route.motors.length-1));DriveView.prototype.moveStation.call(fixture,1);assert.equal(route.motorIndex,0);
 }
 // Run the actual overlay renderer with DOM primitives; each physical station remains clickable.
 const sceneForDrive=new THREE.Scene();sceneForDrive.add(parent);let clicked;
 const view=new DriveView(sceneForDrive,new Element(),(id,index)=>{clicked={id,index}});
 view.setModel(gltf.scene,item);view.setVisible(true);
 const boundsForDrive=worldModelBounds(parent),fit=fitPerspectiveBounds({min:boundsForDrive.min.toArray(),max:boundsForDrive.max.toArray()},{direction:[.73,.47,.82],width:390,height:340,padding:20});
 const cam=new THREE.PerspectiveCamera(37,390/340,fit.near,fit.far);cam.position.fromArray(fit.position);cam.lookAt(...fit.center);cam.updateMatrixWorld(true);
 view.update(cam,390,340);
 for(const {route,index,button} of view.stationDots){
  assert.equal(button.hidden,false,`${item.id}: repeated motor ${index} marker visible in fitted mobile view`);
  assert.ok(button.attributes['aria-label'].includes(`${index+1}/${route.motors.length}`));
  button.events.click();assert.equal(clicked.id,route.id);assert.equal(clicked.index,index);
 }
 for(const marker of view.markers.filter(marker=>!marker.route.motors.length))assert.equal(marker.button.hidden,true,'Unknown motors have no invented spatial label');
 if(item.id==='sizing')assert.equal(view.stationDots.length,12);
 if(item.id==='winding')assert.equal(view.stationDots.length,96);
 view.clear();assert.equal(view.stationDots.length,0);
 const before=worldModelBounds(parent).clone();
 // Route resolution and arrows use a sibling group, so machine framing is independent of overlays.
 const scene=new THREE.Scene();scene.add(parent);const overlay=new THREE.Group();scene.add(overlay);overlay.position.set(10000,10000,10000);
 assert.ok(worldModelBounds(parent).equals(before));
 if(item.id==='sizing'){
  const dryer=routes.find(route=>route.motors.length===12);assert.ok(dryer,'12 dryer motors have a route');assert.ok(!dryer.motors.some(node=>node.userData.driveAnchorId==='motor_assembly.012'));
  assert.ok(routes.some(route=>route.motors.length===1&&route.motors[0].userData.driveAnchorId==='motor_assembly.012'));
  const motor=dryer.motors[1],motorBounds=worldModelBounds(motor),direction=exteriorDriveDirection(before,motorBounds);
  assert.ok(direction.x<-.9,'Sizing dryer motor must be viewed from the outside left face');
  const fit=fitPerspectiveBounds({min:motorBounds.min.toArray(),max:motorBounds.max.toArray()},{direction:direction.toArray(),width:800,height:450,padding:67.5});
  const target=new THREE.Vector3(...fit.center),origin=new THREE.Vector3(...fit.position).sub(target).multiplyScalar(1.22).add(target),ray=new THREE.Raycaster(origin,target.clone().sub(origin).normalize());
  const first=ray.intersectObject(gltf.scene,true)[0]?.object;let ancestor=first,isMotor=false;while(ancestor){if(ancestor===motor)isMotor=true;ancestor=ancestor.parent}
  assert.ok(isMotor,'Sizing dryer motor center must not be hidden behind a roll at exterior focus');
 }
 if(item.id==='inspection')assert.equal(resolvedMotors.size,0,'Inspection-only system must not invent a motor');
 report.motorStations+=resolvedMotors.size;report.modelCases.push({id:item.id,sha256,routes:routes.length,motors:resolvedMotors.size});
 gltf.scene.traverse(node=>{node.geometry?.dispose();if(node.material)for(const material of Array.isArray(node.material)?node.material:[node.material])material.dispose()});
 console.log(`${item.id}: ${routes.length} routes / ${resolvedMotors.size} motors / exact selectors pass`);
}
// Exact IDs dominate even if a broad match would otherwise find a different motor.
const fixture=new THREE.Group(),motor=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial());motor.name='motor_assembly';motor.userData.driveAnchorId='motor_assembly';fixture.add(motor);fixture.updateMatrixWorld(true);
const [unknown]=resolveDriveRoutes(fixture,[{id:'unknown',steps:[{role:'motor',anchorIds:['absent'],match:['motor_assembly']},{role:'transmission',match:[]},{role:'load',match:[]}]}]);
assert.equal(unknown.motors.length,0);assert.ok(driveRoutePoints(unknown).every(item=>item.point===null));
const [known]=resolveDriveRoutes(fixture,[{id:'known',steps:[{role:'motor',anchorIds:['motor_assembly']}]}]);const first=driveRoutePoints(known)[0].point.clone();motor.position.x=3;fixture.updateMatrixWorld(true);assert.equal(driveRoutePoints(known)[0].point.x-first.x,3);
const app=await fs.readFile('dist/app.js','utf8'),html=await fs.readFile('dist/index.html','utf8');
const readHash=app.slice(app.indexOf('function readHashRoute(){'),app.indexOf('async function syncHashRoute(){'));
const env={state:{data:{stages:data.items}},location:{hash:''}};const parse=vm.runInNewContext(readHash+';readHashRoute',env);
for(const suffix of ['/motor','/drive','']){env.location.hash='#sizing'+suffix;assert.equal(parse().current,'sizing');assert.equal(parse().mode,suffix?'drive':'machine')}
env.location.hash='#invalid/drive';assert.equal(parse(),null);
assert.ok(app.includes('const modelID = () => state.current;'),'Both modes load equipment only');
assert.ok(!html.includes('电机解剖'));assert.ok(html.includes('data-mode="drive"'));
report.regressions=['exact anchor IDs dominate broad fragments','empty/unknown steps never substitute a motor','all actual motor assemblies assigned to their own drive records','each repeated motor independently addressable and wraps','12 dryer motors exclude beam motor 13','inspection has no invented motor','functional anchors follow object transform','overlays excluded from equipment fit','legacy motor hash maps to whole-equipment drive mode','every repeated motor has a visible, accessible, directly clickable spatial dot in fitted mobile projection','all mapped upstream/downstream objects participate in cached branch topology','unmodeled connections use dashed batches','sizing motor exterior focus is unoccluded by raycast'];
assert.equal(report.modelCases.length,processData.stages.length);assert.equal(report.routeCases,data.items.reduce((sum,item)=>sum+item.routes.length,0));assert.ok(report.motorStations>0);
report.result='pass';await fs.writeFile('qa/drive-view-validation.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({result:report.result,routes:report.routeCases,steps:report.stepCases,empty:report.emptySteps,motorStations:report.motorStations,branchEdges:report.branchEdges,unmodeledEdges:report.unmodeledEdges}));
