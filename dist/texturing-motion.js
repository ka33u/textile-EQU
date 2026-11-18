import * as THREE from 'three';
import {motorDriveRoutes,driveObjectContext} from './drive-view.js?v=20261119-stations';

export const TEXTURING_PHASES=Object.freeze([
  {id:'poy',label:'POY退绕'},{id:'g1',label:'G1喂入'},{id:'primary',label:'一次加热'},
  {id:'cooling',label:'冷却轨'},{id:'friction',label:'摩擦假捻'},{id:'g2',label:'G2牵伸'},
  {id:'secondary',label:'二次加热'},{id:'w3',label:'W3喂纱'},{id:'oiling',label:'上油'},
  {id:'takeup',label:'横动卷绕'}
]);
const AXES={x:new THREE.Vector3(1,0,0),y:new THREE.Vector3(0,1,0),z:new THREE.Vector3(0,0,1)};
const identityRotation=new THREE.Quaternion();
const mod=(v,n)=>((v%n)+n)%n;
const stem=node=>node.name.replace(/\d+$/,'');
const isName=(node,name)=>node.name===name||node.name.startsWith(name+'.')||new RegExp('^'+name+'\\d+$').test(node.name);
const clampIndex=value=>THREE.MathUtils.clamp(Math.trunc(Number(value)||1),1,384);
const center=node=>new THREE.Box3().setFromObject(node).getCenter(new THREE.Vector3());

/** Recover the actual tube rings exported by Blender, verifying the export contract.
 * Averaging is permitted only after each five-vertex ring passes a diameter check.
 * This prevents accidentally treating a reordered arbitrary mesh as a yarn path. */
export function extractYarnCenterline(geometry){
  const a=geometry.getAttribute('position');
  if(!a||a.count%5)throw new Error('Texturing yarn is not a five-sided continuous tube');
  const points=[],rings=[];
  for(let i=0;i<a.count;i+=5){
    const p=new THREE.Vector3();for(let j=0;j<5;j++)p.add(new THREE.Vector3().fromBufferAttribute(a,i+j));p.multiplyScalar(.2);
    for(let j=0;j<5;j++)if(new THREE.Vector3().fromBufferAttribute(a,i+j).distanceTo(p)>.00101)throw new Error('Texturing yarn vertex order changed');
    points.push(p);rings.push([i,i+1,i+2,i+3,i+4]);
  }
  if(points.length<20)throw new Error('Incomplete texturing yarn path');
  return {points,rings};
}
export function measurePolyline(points){
  const lengths=new Float64Array(points.length);for(let i=1;i<points.length;i++)lengths[i]=lengths[i-1]+points[i].distanceTo(points[i-1]);
  return {points,lengths,total:lengths.at(-1)||0};
}
export function samplePolyline(path,fraction,target=new THREE.Vector3()){
  if(!path.points.length)return target.set(0,0,0);
  const d=THREE.MathUtils.clamp(fraction,0,1)*path.total;let lo=0,hi=path.lengths.length-1;
  while(lo+1<hi){const mid=(lo+hi)>>1;if(path.lengths[mid]<d)lo=mid;else hi=mid}
  const span=path.lengths[hi]-path.lengths[lo];return target.copy(path.points[lo]).lerp(path.points[hi],span>1e-10?(d-path.lengths[lo])/span:0);
}
function nearestProgress(path,p){
  let result=0,best=Infinity;const direction=new THREE.Vector3(),offset=new THREE.Vector3();
  for(let i=1;i<path.points.length;i++){
    const a=path.points[i-1],d=direction.subVectors(path.points[i],a),den=d.lengthSq();
    offset.subVectors(p,a);
    const t=den?THREE.MathUtils.clamp(offset.dot(d)/den,0,1):0;
    const distance=offset.addScaledVector(d,-t).lengthSq();
    if(distance<best){best=distance;result=(path.lengths[i-1]+Math.sqrt(den)*t)/path.total}
  }
  return result;
}
function rotationKind(node){
  if(node.userData.motorDetailRole==='shaft')return 'motor';
  if(node.name.startsWith('efk_friction_shaft_'))return 'friction';
  if(node.name.startsWith('EFK_G1_godet_rotation'))return 'g1';
  if(node.name.startsWith('EFK_G2_godet_rotation'))return 'g2';
  if(isName(node,'EFK_W3_section_shaft'))return 'w3';
  if(isName(node,'EFK_camshaft_section'))return 'camshaft';
  if(isName(node,'EFK_take_up_drum'))return 'drum';
  if(node.userData.componentRole==='dty_package')return 'package';
  return null; // POY, oil wheels, housings, guards and support frames remain still.
}
const RATES={motor:2.6,friction:5.2,g1:1.8,g2:2.1,w3:1.8,camshaft:2.2,drum:2.2,package:-1.01};

/** Illustrative motion, never an OEM timing/drive-ratio simulation.
 * update receives cumulative played seconds (including the UI speed factor).
 * Repeating elapsed is a true pause. A decrease rewinds all managed transforms.
 * Call markDirty after normalization/explosion; camera movement needs no rebuild.
 * No model material is touched. highlightedObjects() integrates with existing UI.
 */
export class TexturingMotion {
  constructor(root,scene,{routes=[]}={}){
    this.root=root;this.scene=scene;this.routes=routes;this.disposed=false;this.visible=true;this.lastElapsed=0;this.time=0;
    this.selection={mode:'process',yarnMode:'single',stationIndex:1,side:'A',routeId:null,motorIndex:0,running:true};
    this.stations=new Map();this.rotors=[];this.guides=[];this.batches=[];this.managedNodes=new Set();this._highlights=new Set();this._active=new Set();this._affected=new Set();
    this.group=new THREE.Group();this.group.name='texturing_motion_overlay';scene.add(this.group);
    this.animationBounds=new THREE.Box3();this.geometryDirty=true;this.overlayDirty=true;
    root.updateWorldMatrix(true,true);
    root.traverse(node=>{
      if(node.userData.componentRole==='texturing_position')this.stations.set(node.userData.positionIndex,{index:node.userData.positionIndex,node,side:node.userData.machineSide,section:node.userData.sectionIndex,localPosition:(node.userData.positionIndex-1)%192+1,sectionPosition:node.userData.sectionPosition});
      const kind=rotationKind(node);
      if(kind&&AXES[node.userData.spinAxis]){this.rotors.push({node,kind,base:node.quaternion.clone(),angle:0});this.managedNodes.add(node)}
    });
    if(this.stations.size!==384)throw new Error('TexturingMotion requires all 384 actual eFK positions');
    const geometryCache=new Map(),batchMap=new Map();
    for(const station of this.stations.values()){
      const children=[];station.node.traverse(node=>children.push(node));station.children=children;
      station.yarn=children.find(node=>node.isMesh&&node.userData.componentRole==='continuous_yarn_path');
      station.guide=children.find(node=>isName(node,'EFK_traverse_guide'));
      station.winder=children.find(node=>node.userData.componentRole==='takeup_position');
      if(!station.yarn||!station.guide||!station.winder)throw new Error('Incomplete dynamic station '+station.index);
      const original=station.yarn.geometry;if(!geometryCache.has(original))geometryCache.set(original,extractYarnCenterline(original));
      const key=original.uuid+station.side;let batch=batchMap.get(key);
      if(!batch){
        const source=geometryCache.get(original);batch={original,geometry:original.clone(),rings:source.rings,basePoints:source.points.map(p=>p.clone()),points:source.points.map(p=>p.clone()),stations:[],phase:0,started:false};
        batch.geometry.getAttribute('position').setUsage(THREE.DynamicDrawUsage);batch.geometry.getAttribute('normal')?.setUsage(THREE.DynamicDrawUsage);
        batchMap.set(key,batch);this.batches.push(batch);
      }
      station.originalGeometry=original;station.yarn.geometry=batch.geometry;station.batch=batch;batch.stations.push(station);
      station.guideBase=station.guide.position.clone();this.guides.push(station);this.managedNodes.add(station.guide);
    }
    // One batched line and one instanced marker draw for all 384 paths, never one
    // WebGL object per flow particle. Source machinery stays fully present.
    this.lines=new THREE.LineSegments(new THREE.BufferGeometry(),new THREE.LineBasicMaterial({color:0x087680,transparent:true,opacity:.9,depthTest:false,depthWrite:false}));this.lines.frustumCulled=false;this.lines.renderOrder=35;this.group.add(this.lines);
    this.particles=new THREE.InstancedMesh(new THREE.SphereGeometry(1,6,4),new THREE.MeshBasicMaterial({color:0x31c9c0,depthTest:false,depthWrite:false}),384*4+20);
    this.particles.instanceMatrix.setUsage(THREE.DynamicDrawUsage);this.particles.frustumCulled=false;this.particles.renderOrder=36;this.group.add(this.particles);
    this.rotationMarkers=new THREE.InstancedMesh(new THREE.SphereGeometry(1,6,4),new THREE.MeshBasicMaterial({color:0xe28b31,depthTest:false,depthWrite:false}),32);
    this.rotationMarkers.instanceMatrix.setUsage(THREE.DynamicDrawUsage);this.rotationMarkers.frustumCulled=false;this.rotationMarkers.renderOrder=37;this.group.add(this.rotationMarkers);
    this._markerLocal=new WeakMap();
    this._matrix=new THREE.Matrix4();this._point=new THREE.Vector3();this._quat=new THREE.Quaternion();this._scale=new THREE.Vector3();
    this.setSelection({});this.rebuildPaths();this.update(0);
  }
  setSelection(change={}){
    if(this.disposed)return;
    const previous=this.selection;this.selection={...previous,...change};
    const s=this.selection;s.mode=s.mode==='motor'?'motor':'process';s.yarnMode=['single','all','off'].includes(s.yarnMode)?s.yarnMode:'single';
    if(change.side&&change.stationIndex===undefined)s.stationIndex=(clampIndex(s.stationIndex)-1)%192+1+(change.side==='B'?192:0);
    s.stationIndex=clampIndex(s.stationIndex);s.side=s.stationIndex>192?'B':'A';
    if(this.activeRoutes&&['mode','yarnMode','stationIndex','routeId','motorIndex','motorAnchorId','motor'].every(key=>previous[key]===s[key]))return this.getState();
    const route=this.routes.find(route=>route.id===s.routeId);
    this.selectedMotor=change.motor||s.motor||(s.motorAnchorId?this.routes.flatMap(r=>r.motors).find(m=>m.userData.driveAnchorId===s.motorAnchorId):null)||route?.motors[THREE.MathUtils.clamp(Number(s.motorIndex)||0,0,Math.max(0,(route?.motors.length||0)-1))]||null;
    this.activeRoutes=s.mode==='motor'?motorDriveRoutes(this.routes,this.selectedMotor):this.routes;
    this._active.clear();this._highlights.clear();this._affected.clear();
    if(s.mode==='process'){
      for(const item of this.rotors)this._active.add(item.node);for(const item of this.guides)this._active.add(item.guide);
      for(const index of this.stations.keys())this._affected.add(index);
    }else{
      for(const scoped of this.activeRoutes)for(const step of scoped.steps)for(const object of step.objects){
        this._highlights.add(object);
        object.traverse(node=>{
          // Pump-to-oil-contact is a fluid relation; only its real output shaft rotates.
          if(scoped.id!=='oiling'||node.userData.motorDetailRole==='shaft')this._active.add(node);
          const index=driveObjectContext(node).positionIndex;if(index)this._affected.add(index);
        });
        const context=driveObjectContext(object);
        if(context.sectionIndex&&!context.positionIndex)for(const station of this.stations.values())if(station.section===context.sectionIndex&&station.side===context.machineSide)this._affected.add(station.index);
      }
      if(this.selectedMotor)this._highlights.add(this.selectedMotor);
    }
    this.markerRotors=this.rotors.filter(({node})=>{
      if(!this._active.has(node))return false;
      const context=driveObjectContext(node);
      return context.positionIndex===s.stationIndex||context.motor===this.selectedMotor;
    });
    this.overlayDirty=true;return this.getState();
  }
  setVisible(visible){if(this.visible!==Boolean(visible))this.overlayDirty=true;this.visible=Boolean(visible);this.group.visible=this.visible}
  highlightedObjects(){return new Set(this._highlights)}
  getStationObjects(index=this.selection.stationIndex){const station=this.stations.get(clampIndex(index));return station?[station.node]:[]}
  getStationBounds(index=this.selection.stationIndex){
    const station=this.stations.get(clampIndex(index)),bounds=new THREE.Box3();if(!station)return bounds;
    station.node.updateWorldMatrix(true,true);bounds.setFromObject(station.node);
    for(const point of station.path?.points||[])bounds.expandByPoint(point);
    // Full illustrative traverse envelope, including the guide outside the package.
    for(const z of [-.108,.108])bounds.expandByPoint(station.winder.localToWorld(new THREE.Vector3(.06,.15,z)));
    return bounds;
  }
  markDirty(){this.geometryDirty=true;this.overlayDirty=true}
  rebuildPaths(){
    this.root.updateWorldMatrix(true,true);this.animationBounds.makeEmpty();
    for(const station of this.stations.values()){
      station.path=measurePolyline(station.batch.points.map(p=>p.clone().applyMatrix4(station.yarn.matrixWorld)));
      for(const p of station.path.points)this.animationBounds.expandByPoint(p);
      if(!station.phaseProgress){
      const phaseObjects=[
        station.children.find(o=>o.userData.componentRole==='EFK_active_POY_package'),station.children.find(o=>o.userData.componentRole==='G1_godet'),
        station.children.find(o=>o.userData.componentRole==='primary_channel'),station.children.find(o=>o.userData.componentRole==='cooling_channel'),
        station.children.find(o=>o.userData.componentRole==='friction_unit'),station.children.find(o=>o.userData.componentRole==='G2_godet'),
        station.children.find(o=>o.userData.componentRole==='secondary_channel'),null,null,station.winder];
      // W3/oil belong to the section, shared across its twelve yarns.
      const sectionObjects=station.node.parent.children;
      phaseObjects[7]=sectionObjects.find(o=>isName(o,'EFK_W3_section_shaft'));
      const stationCenter=center(station.node);let nearestOil=Infinity;
      for(const o of sectionObjects.filter(o=>isName(o,'EFK_oil_contact'))){const d=center(o).distanceToSquared(stationCenter);if(d<nearestOil){nearestOil=d;phaseObjects[8]=o}}
        let previous=0;station.phaseProgress=phaseObjects.map((o,i)=>{let p=i===0?0:i===9?1:o?nearestProgress(station.path,center(o)):previous;p=Math.max(previous,p);previous=p;return p});
      }
    }
    this.geometryDirty=false;this.overlayDirty=true;return this.animationBounds;
  }
  _rewind(){
    this.time=0;
    for(const rotor of this.rotors){rotor.angle=0;rotor.node.quaternion.copy(rotor.base)}
    for(const station of this.guides)station.guide.position.copy(station.guideBase);
    for(const batch of this.batches){batch.phase=0;batch.started=false;batch.points=batch.basePoints.map(p=>p.clone());batch.geometry.getAttribute('position').array.set(batch.original.getAttribute('position').array);batch.geometry.getAttribute('position').needsUpdate=true;const n=batch.geometry.getAttribute('normal');if(n){n.array.set(batch.original.getAttribute('normal').array);n.needsUpdate=true}}
    this.markDirty();
  }
  _updateTraverse(batch,delta){
    const station=batch.stations[0];if(!this._active.has(station.guide)||delta===0)return false;
    batch.started=true;batch.phase+=delta*2.2;
    const offset=.095*Math.sin(batch.phase+(station.winder.userData.windingDeck-1)*Math.PI*2/3);
    for(const item of batch.stations)item.guide.position.set(.06,.15,offset);
    station.winder.updateWorldMatrix(true,false);station.yarn.updateWorldMatrix(true,false);
    const transform=station.yarn.matrixWorld.clone().invert().multiply(station.winder.matrixWorld);
    const radius=.1214,gx=.06,gy=.15,angle=Math.atan2(gy,gx)+Math.acos(radius/Math.hypot(gx,gy));
    const tx=radius*Math.cos(angle),ty=radius*Math.sin(angle);
    const tail=[[gx,gy,.23],[gx,gy,offset+.012],[gx,gy,offset],[gx,gy,offset-.012],[(gx+tx)*.5,(gy+ty)*.5,offset-.012],[tx,ty,offset-.012],[tx,ty,offset-.020]];
    const start=batch.points.length-tail.length;
    for(let j=0;j<tail.length;j++)batch.points[start+j].set(...tail[j]).applyMatrix4(transform);
    const positions=batch.geometry.getAttribute('position'),normals=batch.geometry.getAttribute('normal');
    for(let i=start-1;i<batch.points.length;i++){
      const p=batch.points[i],t=batch.points[Math.min(i+1,batch.points.length-1)].clone().sub(batch.points[Math.max(i-1,0)]).normalize();
      let a=t.clone().cross(AXES.x);if(a.lengthSq()<1e-6)a=t.clone().cross(AXES.y);a.normalize();const b=t.clone().cross(a).normalize();
      batch.rings[i].forEach((index,j)=>{const normal=a.clone().multiplyScalar(Math.cos(j*Math.PI*2/5)).addScaledVector(b,Math.sin(j*Math.PI*2/5));positions.setXYZ(index,p.x+.0007*normal.x,p.y+.0007*normal.y,p.z+.0007*normal.z);normals?.setXYZ(index,normal.x,normal.y,normal.z)});
    }
    positions.needsUpdate=true;if(normals)normals.needsUpdate=true;batch.geometry.boundingSphere=null;batch.geometry.boundingBox=null;return true;
  }
  _updateWorldTails(){
    // Only seven tail rings change. Preserve all cached thermal/godet path points.
    for(const station of this.stations.values()){
      const start=station.batch.points.length-7;station.yarn.updateWorldMatrix(true,false);
      for(let i=start;i<station.path.points.length;i++)station.path.points[i].copy(station.batch.points[i]).applyMatrix4(station.yarn.matrixWorld);
      for(let i=start;i<station.path.points.length;i++)station.path.lengths[i]=station.path.lengths[i-1]+station.path.points[i].distanceTo(station.path.points[i-1]);
      station.path.total=station.path.lengths.at(-1);
    }
  }
  _displayStations(){return this.selection.yarnMode==='off'?[]:this.selection.yarnMode==='all'?[...this.stations.values()]:[this.stations.get(this.selection.stationIndex)]}
  _lineGeometry(stations,tailsOnly=false){
    const count=stations.reduce((sum,s)=>sum+(s.path.points.length-1)*2,0);let attr=this.lines.geometry.getAttribute('position');
    if(!attr||attr.count!==count){attr=new THREE.BufferAttribute(new Float32Array(count*3),3);attr.setUsage(THREE.DynamicDrawUsage);this.lines.geometry.setAttribute('position',attr);tailsOnly=false}
    let offset=0;for(const station of stations){
      const start=tailsOnly?Math.max(1,station.path.points.length-7):1;let index=offset+(start-1)*6;
      for(let i=start;i<station.path.points.length;i++){station.path.points[i-1].toArray(attr.array,index);index+=3;station.path.points[i].toArray(attr.array,index);index+=3}
      offset+=(station.path.points.length-1)*6;
    }
    attr.needsUpdate=true;this.lines.material.opacity=this.selection.yarnMode==='all'?.23:.85;this.lines.visible=count>0;
  }
  update(elapsed=0){
    if(this.disposed)return;elapsed=Math.max(0,Number(elapsed)||0);
    if(elapsed<this.lastElapsed-1e-8)this._rewind();
    const delta=this.selection.running===false?0:Math.max(0,elapsed-this.lastElapsed);this.lastElapsed=elapsed;this.time+=delta;
    if(!delta&&!this.geometryDirty&&!this.overlayDirty)return;
    if(delta)for(const rotor of this.rotors)if(this._active.has(rotor.node)){rotor.angle+=delta*RATES[rotor.kind];rotor.node.quaternion.copy(rotor.base).multiply(this._quat.setFromAxisAngle(AXES[rotor.node.userData.spinAxis],rotor.angle))}
    let tailChanged=false;for(const batch of this.batches)tailChanged=this._updateTraverse(batch,delta)||tailChanged;
    if(this.geometryDirty)this.rebuildPaths();else if(tailChanged)this._updateWorldTails();
    const stations=this._displayStations();if(this.overlayDirty||tailChanged){this._lineGeometry(stations,!this.overlayDirty);this.overlayDirty=false}
    let count=0;const process=this.selection.mode==='process',routes=new Set(this.activeRoutes.map(r=>r.id));
    const phaseId=routes.has('false_twist')?'friction':routes.has('w3')?'w3':routes.has('camshaft_traverse')||routes.has('takeup')?'takeup':null;
    const frameScale=this.root.getWorldScale(new THREE.Vector3()).length()/Math.sqrt(3),dotRadius=Math.max(.0015,frameScale*(this.selection.yarnMode==='single'?.045:.009));
    for(const station of stations){
      if(!process&&(!phaseId||!this._affected.has(station.index)))continue;
      const n=this.selection.yarnMode==='single'?18:4,phaseIndex=TEXTURING_PHASES.findIndex(p=>p.id===phaseId),mid=station.phaseProgress[phaseIndex]??1;
      for(let i=0;i<n;i++){
        const progress=process?mod(this.time/12+i/n,1):THREE.MathUtils.clamp(mid-.018+mod(this.time*.45+i/n,1)*.036,0,1);
        samplePolyline(station.path,progress,this._point);this._scale.setScalar(dotRadius*(station.index===this.selection.stationIndex?1.5:1));
        this._matrix.compose(this._point,identityRotation,this._scale);this.particles.setMatrixAt(count++,this._matrix);
      }
    }
    this.particles.count=count;this.particles.visible=count>0;this.particles.instanceMatrix.needsUpdate=true;this.group.visible=this.visible;
    // A tiny contrasting surface marker makes smooth cylinders visibly rotate.
    // Only the current yarn station and selected motor receive these markers.
    let markers=0;
    for(const rotor of this.markerRotors){
      if(!this._markerLocal.has(rotor.node)){
        rotor.node.updateWorldMatrix(true,true);const inverse=rotor.node.matrixWorld.clone().invert(),bounds=new THREE.Box3();
        rotor.node.traverse(o=>{if(!o.isMesh)return;o.geometry.computeBoundingBox();const b=o.geometry.boundingBox.clone().applyMatrix4(inverse.clone().multiply(o.matrixWorld));bounds.union(b)});
        const axis=rotor.node.userData.spinAxis,radial=axis==='x'?'y':'x',p=bounds.getCenter(new THREE.Vector3());p[radial]=bounds.max[radial]*.77;p[axis]=bounds.max[axis]+.001;
        this._markerLocal.set(rotor.node,p);
      }
      rotor.node.updateWorldMatrix(true,false);this._point.copy(this._markerLocal.get(rotor.node)).applyMatrix4(rotor.node.matrixWorld);
      this._scale.setScalar(frameScale*.006);this._matrix.compose(this._point,identityRotation,this._scale);this.rotationMarkers.setMatrixAt(markers++,this._matrix);
      if(markers===32)break;
    }
    this.rotationMarkers.count=markers;this.rotationMarkers.instanceMatrix.needsUpdate=true;
  }
  getState(){
    const station=this.stations.get(this.selection.stationIndex),progress=mod(this.time/12,1);let phaseIndex=0;
    if(station?.phaseProgress)for(let i=1;i<station.phaseProgress.length;i++)if(progress>=(station.phaseProgress[i-1]+station.phaseProgress[i])*.5)phaseIndex=i;
    const routeIds=new Set((this.activeRoutes||[]).map(r=>r.id));
    if(this.selection.mode==='motor')phaseIndex=routeIds.has('false_twist')?4:routeIds.has('w3')?7:routeIds.has('oiling')?8:routeIds.has('camshaft_traverse')||routeIds.has('takeup')?9:-1;
    const phaseLabel=this.selection.mode==='motor'?(phaseIndex===8?'油剂供给 · 纱线停留':phaseIndex>=0?TEXTURING_PHASES[phaseIndex].label+' · 局部运动':'选择已建模动力源'):TEXTURING_PHASES[phaseIndex].label;
    return {stationIndex:station?.index,side:station?.side,section:station?.section,localPosition:station?.localPosition,sectionPosition:station?.sectionPosition,
      phaseIndex,phaseLabel,progress:this.selection.mode==='process'?progress:0,visibleYarnCount:this._displayStations().length,affectedPositionCount:this._affected.size,
      selectedMotor:this.selectedMotor?.userData.driveAnchorId||null,mode:this.selection.mode,yarnMode:this.selection.yarnMode,
      motionNote:'运动速度、横动行程与阶段用时为教学示意；未知动力连接没有补造电机。',
      phasePoints:station?.phaseProgress?.map((p,i)=>({id:TEXTURING_PHASES[i].id,label:TEXTURING_PHASES[i].label,progress:p,point:samplePolyline(station.path,p)}))||[]};
  }
  dispose(){
    if(this.disposed)return;this.disposed=true;
    for(const rotor of this.rotors)rotor.node.quaternion.copy(rotor.base);
    for(const station of this.stations.values()){station.guide.position.copy(station.guideBase);station.yarn.geometry=station.originalGeometry}
    for(const batch of this.batches)batch.geometry.dispose();
    this.lines.geometry.dispose();this.lines.material.dispose();this.particles.dispose();this.particles.geometry.dispose();this.particles.material.dispose();this.rotationMarkers.dispose();this.rotationMarkers.geometry.dispose();this.rotationMarkers.material.dispose();this.group.removeFromParent();this.group.clear();
  }
}
