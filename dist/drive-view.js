import * as THREE from 'three';

const normalized=(value)=>String(value||'').normalize('NFKC').toLowerCase();
const localCenters=new WeakMap();
const movingCenters=new WeakMap();
function hasMovingCenter(object){
  if(movingCenters.has(object))return movingCenters.get(object);
  let result=false;
  for(let node=object;node;node=node.parent){
    const motion=node.userData.stationMotion;
    if(motion&&(motion.startsWith('translate:')||motion.startsWith('oscillate:'))){result=true;break}
  }
  movingCenters.set(object,result);return result;
}
const centerOf=(object)=>{
  if(!localCenters.has(object)){
    object.updateWorldMatrix(true,true);
    const bounds=new THREE.Box3().setFromObject(object);
    localCenters.set(object,bounds.isEmpty()?new THREE.Vector3():object.worldToLocal(bounds.getCenter(new THREE.Vector3())));
  }
  return localCenters.get(object).clone().applyMatrix4(object.matrixWorld);
};

const motorKey=(motor)=>String(motor?.userData.driveAnchorId||motor?.name||'');
const sameMotor=(a,b)=>Boolean(a&&b&&(a===b||(motorKey(a)&&motorKey(a)===motorKey(b))));
function anchorNames(ids){
  const names=new Set(ids);
  for(const id of ids)names.add(THREE.PropertyBinding.sanitizeNodeName(id));
  return names;
}
const scopeCache=new WeakMap();
const contextCache=new WeakMap();
/** Published model's station identity; inherited IDs, never inferred from distance. */
export function driveObjectContext(object){
  if(contextCache.has(object))return contextCache.get(object);
  const context={};
  for(let node=object;node;node=node.parent){
    for(const key of ['machineSide','sectionIndex','positionIndex','sidePosition'])if(context[key]===undefined&&node.userData[key]!==undefined)context[key]=node.userData[key];
    if(node.userData.driveRole==='motor'&&!context.motor){
      context.motor=node;
      const side=motorKey(node).match(/^EFK_(?:friction|W3|camshaft)_drive_([AB])$/)?.[1];
      if(side)context.machineSide=side;
    }
  }
  contextCache.set(object,context);return context;
}

/** A motor scope retains every mapped working part, not one nearest point per step.
 * Explicit per-motor anchor lists take precedence. Older records use their existing
 * spatial association policy; this is a functional association, not an OEM claim.
 */
export function scopeDriveRoute(route,motorOrIndex=route.motorIndex){
  const motor=typeof motorOrIndex==='number'?route.motors[motorOrIndex]:motorOrIndex;
  if(!motor||!route.motors.some(item=>sameMotor(item,motor)))return {...route,steps:route.steps.map(step=>({...step,objects:[]})),motors:[],motorIndex:0};
  let cache=scopeCache.get(route);if(!cache){cache=new Map();scopeCache.set(route,cache)}
  const key=motorKey(motor);if(cache.has(key))return cache.get(key);
  let positions;
  const selected=route.motors.findIndex(item=>sameMotor(item,motor));
  const exactSide=key.match(/^EFK_(?:friction|W3|camshaft)_drive_([AB])$/)?.[1];
  const steps=route.steps.map(step=>{
    const explicit=step.motorScopes?.[key];
    let objects;
    if(step.role==='motor')objects=step.objects.filter(item=>sameMotor(item,motor));
    else if(Array.isArray(explicit)){
      const ids=new Set(explicit),names=anchorNames(explicit);
      objects=step.objects.filter(item=>ids.has(item.userData.driveAnchorId)||names.has(item.name));
    }
    else if(step.motorScopes)objects=[]; // Incomplete explicit data never silently guesses.
    else if(exactSide)objects=step.objects.filter(item=>{
      const context=driveObjectContext(item);
      return context.motor?sameMotor(context.motor,motor):context.machineSide===exactSide;
    });
    else if(route.motors.length===1)objects=step.objects;
    else objects=step.objects.filter(item=>{
      for(let p=item;p;p=p.parent){const index=route.motors.indexOf(p);if(index!==-1)return index===selected}
      if(step.objects.length===1)return true; // A shared mapped mechanism remains shared.
      const point=centerOf(item);let nearest=0,distance=Infinity;
      positions??=route.motors.map(centerOf);
      positions.forEach((position,index)=>{const d=position.distanceToSquared(point);if(d<distance){nearest=index;distance=d}});
      return nearest===selected;
    });
    return {...step,objects};
  });
  const scoped={...route,steps,motors:[motor],motorIndex:0,sourceRoute:route,selectedMotor:motor};
  cache.set(key,scoped);return scoped;
}

/** All functional routes served by the same concrete motor, with exact station scope. */
export function motorDriveRoutes(routes,motor){
  if(!motor)return [];
  return routes.filter(route=>route.motors.some(item=>sameMotor(item,motor))).map(route=>scopeDriveRoute(route,motor));
}

/** Stable catalog order: repeated anchors (e.g. camshaft/takeup) appear only once. */
export function uniqueDriveMotors(routes){
  const seen=new Set(),motors=[];
  for(const route of routes)route.motors.forEach((motor,index)=>{
    const key=motorKey(motor);if(seen.has(key))return;seen.add(key);motors.push({motor,route,index,anchorId:key});
  });
  return motors;
}

/** Resolve only the route's own matches. An unknown motor never falls back to another drive. */
export function resolveDriveRoutes(root,routes=[]){
  const nodes=[],anchorIndex=new Map(),nameIndex=new Map(),searchText=new Map(),order=new Map();
  root.traverse(node=>{
    order.set(node,nodes.length);nodes.push(node);
    const anchor=node.userData.driveAnchorId,index=anchor?anchorIndex:nameIndex,key=String(anchor||node.name);
    if(!index.has(key))index.set(key,[]);
    index.get(key).push(node);
  });
  return routes.map((route,index)=>{
    const steps=(route.steps||[]).map(step=>{
      const exact=(step.anchorIds||[]).map(String),terms=(step.match||[]).flatMap(value=>[normalized(value),normalized(THREE.PropertyBinding.sanitizeNodeName(String(value)))]).filter(Boolean);
      let objects=[];
      if(exact.length){
        const found=new Set();
        for(const id of exact)for(const node of anchorIndex.get(id)||[])found.add(node);
        for(const name of anchorNames(exact))for(const node of nameIndex.get(name)||[])found.add(node);
        objects=[...found].sort((a,b)=>order.get(a)-order.get(b));
      }else if(terms.length){
        objects=nodes.filter(node=>{
          if(!searchText.has(node))searchText.set(node,[normalized(node.name),normalized(node.userData.label)]);
          const [name,label]=searchText.get(node);
          return terms.some(term=>name.includes(term)||label.includes(term));
        });
      }
      // A matched motor group owns its visible casing parts; count the assembly once.
      if (route.graph?.association!=='explicit_motor_groups' || !exact.length) {
        const candidates=new Set(objects);
        objects=objects.filter(node=>{let p=node.parent;while(p&&p!==root.parent){if(candidates.has(p))return false;p=p.parent}return true});
      }
      return {...step,objects};
    });
    const motors=[...new Set(steps.filter(step=>step.role==='motor').flatMap(step=>step.objects))];
    if(route.graph?.association==='same_spinning_position')motors.sort((a,b)=>driveObjectContext(a).positionIndex-driveObjectContext(b).positionIndex);
    if(route.graph?.association==='explicit_motor_groups'){
      const rank=new Map(steps[0].anchorIds.map((id,i)=>[id,i]));
      motors.sort((a,b)=>rank.get(motorKey(a))-rank.get(motorKey(b)));
    }
    return {...route,index,steps,motors,motorIndex:0};
  });
}

/** Select a concrete repeated station and the nearest matching mechanism at each next step. */
export function driveRoutePoints(route){
  let previous=null;
  const motor=route.motors[route.motorIndex%Math.max(1,route.motors.length)]||null;
  if(motor)previous=centerOf(motor);
  return route.steps.map(step=>{
    let object=step.role==='motor'&&motor&&step.objects.includes(motor)?motor:null;
    if(!object&&step.objects.length){
      object=step.objects[0];
      if(previous){let nearest=Infinity;for(const item of step.objects){const distance=centerOf(item).distanceToSquared(previous);if(distance<nearest){nearest=distance;object=item}}}
    }
    if(!object)return {step,object:null,point:null};
    const point=centerOf(object);previous=point;
    return {step,object,point};
  });
}

// One shader uniform advances all directional pulses. Geometry and arrow matrices
// are uploaded only after selection/explosion changes, never on animation ticks.
function pulseMaterial(settings){
  return new THREE.ShaderMaterial({
    transparent:true,depthTest:false,depthWrite:false,toneMapped:false,
    uniforms:{color:{value:new THREE.Color(settings.color)},opacity:{value:settings.opacity},elapsed:{value:0},pulseEnabled:{value:0},pulseStrength:{value:.4}},
    vertexShader:`attribute float routeProgress; varying float vProgress;
      void main(){vProgress=routeProgress;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader:`uniform vec3 color;uniform float opacity;uniform float elapsed;
      uniform float pulseEnabled;uniform float pulseStrength;varying float vProgress;
      void main(){
        float phase=fract(vProgress-elapsed*.48);
        float pulse=(1.0-smoothstep(.025,.12,abs(phase-.5)))*pulseEnabled;
        gl_FragColor=vec4(mix(color,vec3(1.0,.63,.24),pulse*.85),min(1.0,opacity+pulse*pulseStrength));
        #include <colorspace_fragment>
      }`
  });
}

/** Cache the full functional branch topology. Every mapped node is retained. */
export function buildDriveBranches(route){
  if(route.graph?.association==='explicit_motor_groups'){
    const steps=route.steps.map(step=>new Map(step.objects.map(o=>[o.userData.driveAnchorId,o])));
    const edges=[];
    for(const [fromId,toId,stepIndex] of route.graph.links){
      const from=steps[stepIndex-1].get(fromId),to=steps[stepIndex].get(toId);
      if(from&&to)edges.push({from,to,stepIndex,unmodeled:route.steps[stepIndex].connectionStatus==='unmodeled'});
    }
    return edges;
  }
  const edges=[];
  for(let index=1;index<route.steps.length;index++){
    const upstream=route.steps[index-1].objects,downstream=route.steps[index].objects;
    if(!upstream.length||!downstream.length)continue; // Never bridge an unmodeled stage.
    const a=upstream.map(centerOf),b=downstream.map(centerOf),usedA=new Set(),pairs=new Set();
    const candidates=objects=>{
      const contexts=objects.map(driveObjectContext),cache=new Map();
      return other=>{
        const {machineSide,sectionIndex,positionIndex}=driveObjectContext(other);
        const station=route.graph?.association==='same_spinning_position'?positionIndex:undefined;
        const key=JSON.stringify([machineSide,sectionIndex,station]);
        if(!cache.has(key)){
          const indices=[];
          contexts.forEach((value,i)=>{
            if(machineSide!==undefined&&value.machineSide!==undefined&&machineSide!==value.machineSide)return;
            if(sectionIndex!==undefined&&value.sectionIndex!==undefined&&sectionIndex!==value.sectionIndex)return;
            if(station!==undefined&&station!==value.positionIndex)return;
            indices.push(i);
          });
          cache.set(key,indices);
        }
        return cache.get(key);
      };
    };
    const upstreamFor=candidates(upstream),downstreamFor=candidates(downstream);
    const add=(i,j)=>{const key=`${i}:${j}`;if(pairs.has(key))return;pairs.add(key);usedA.add(i);edges.push({from:upstream[i],to:downstream[j],stepIndex:index,unmodeled:route.steps[index].connectionStatus==='unmodeled'})};
    for(let j=0;j<b.length;j++){
      let closest=-1,distance=Infinity;for(const i of upstreamFor(downstream[j])){const d=a[i].distanceToSquared(b[j]);if(d<distance){distance=d;closest=i}}
      if(closest!==-1)add(closest,j);
    }
    // Also retain upstream branches that merge into fewer downstream groups.
    for(let i=0;i<a.length;i++)if(!usedA.has(i)){
      let closest=-1,distance=Infinity;for(const j of downstreamFor(upstream[i])){const d=a[i].distanceToSquared(b[j]);if(d<distance){distance=d;closest=j}}
      if(closest!==-1)add(i,closest);
    }
  }
  return edges;
}

/** Approach a drive from the outside face of the machine, not from its work envelope. */
export function exteriorDriveDirection(machineBounds,motorBounds){
  const center=motorBounds.getCenter(new THREE.Vector3()),mid=machineBounds.getCenter(new THREE.Vector3()),size=machineBounds.getSize(new THREE.Vector3());
  const offset=center.sub(mid),x=Math.abs(offset.x)/Math.max(size.x*.5,.0001),z=Math.abs(offset.z)/Math.max(size.z*.5,.0001);
  const axis=Math.max(x,z)<.05?(size.x<size.z?'x':'z'):(x>=z?'x':'z');
  const direction=new THREE.Vector3(0,.32,0);
  direction[axis]=Math.sign(offset[axis])||1;direction[axis==='x'?'z':'x']=(Math.sign(offset[axis==='x'?'z':'x'])||1)*.16;
  return direction.normalize();
}

/** Place screen-space labels inside the canvas, preferring the closest free cell.
 * Search both axes instead of repeatedly clamping a vertical displacement at an
 * edge. Inputs/outputs use label centers; dimensions include the actual button.
 */
export function layoutDriveMarkers(entries,width,height){
  const margin=8,gap=7,placed=[],rings=Math.max(3,Math.ceil(Math.sqrt(entries.length))+1);
  const stepX=Math.max(45,...entries.map(item=>item.width+gap)),stepY=Math.max(36,...entries.map(item=>item.height+gap));
  for(const entry of entries){
    const halfW=entry.width/2,halfH=entry.height/2;
    const minX=Math.min(width/2,margin+halfW),maxX=Math.max(width/2,width-margin-halfW);
    const minY=Math.min(height/2,margin+halfH),maxY=Math.max(height/2,height-margin-halfH);
    const desiredX=entry.x,desiredY=entry.y-21,xs=new Set([minX,maxX]),ys=new Set([minY,maxY]);
    for(let i=-rings;i<=rings;i++){
      xs.add(THREE.MathUtils.clamp(desiredX+i*stepX,minX,maxX));
      ys.add(THREE.MathUtils.clamp(desiredY+i*stepY,minY,maxY));
    }
    let best=null;
    for(const x of xs)for(const y of ys){
      let overlaps=0,area=0;
      for(const other of placed){
        const dx=(entry.width+other.width)/2+gap-Math.abs(x-other.x),dy=(entry.height+other.height)/2+gap-Math.abs(y-other.y);
        if(dx>0&&dy>0){overlaps++;area+=dx*dy}
      }
      const distance=(x-desiredX)**2+(y-desiredY)**2;
      if(!best||overlaps<best.overlaps||(overlaps===best.overlaps&&(area<best.area||(area===best.area&&distance<best.distance))))best={...entry,x,y,overlaps,area,distance};
    }
    placed.push(best);
  }
  return placed;
}

export class DriveView {
  constructor(scene,container,onSelect){
    this.scene=scene;this.container=container;this.onSelect=onSelect;
    this.group=new THREE.Group();this.group.name='functional_drive_routes';scene.add(this.group);
    this.lastView=new THREE.Matrix4();this.lastProjection=new THREE.Matrix4();
    this.arrowPose=new THREE.Object3D();this.edgeStart=new THREE.Vector3();this.edgeEnd=new THREE.Vector3();this.edgeDirection=new THREE.Vector3();
    this.routes=[];this.activeId=null;this.activeMotor=null;this.visible=false;this.markers=[];this.stationDots=[];this.branchBatches=[];this.geometryDirty=true;this.motorMarkers=false;
    this.leaders=document.createElementNS('http://www.w3.org/2000/svg','svg');this.leaders.classList.add('drive-leaders');this.leaders.setAttribute('aria-hidden','true');container.append(this.leaders);
  }
  clear(){
    const geometries=new Set(),materials=new Set();this.group.traverse(node=>{if(node.geometry)geometries.add(node.geometry);if(node.material)materials.add(node.material)});
    for(const child of this.group.children)if(child.isInstancedMesh)child.dispose();
    this.group.clear();geometries.forEach(item=>item.dispose());materials.forEach(item=>item.dispose());
    this.markers.forEach(({button,line})=>{button.remove();line.remove()});this.markers=[];this.branchBatches=[];
    this.stationDots.forEach(({button})=>button.remove());this.stationDots=[];this.activeMotor=null;
  }
  setModel(root,data){
    this.clear();this.routes=resolveDriveRoutes(root,data?.routes||[]);this.activeId=null;
    this.motorMarkers=data?.id==='texturing';
    const markerEntries=this.motorMarkers?uniqueDriveMotors(this.routes):this.routes.map(route=>({route}));
    markerEntries.forEach(({route,motor,index},ordinal)=>{
      const button=document.createElement('button');button.type='button';button.className='drive-marker';button.textContent=motor?`M${ordinal+1}`:String(route.index+1).padStart(2,'0');
      const title=motor?`${button.textContent} · ${motor.userData.label||motor.name}`:`${route.label}${route.motors.length>1?` · 同类 ${route.motors.length} 处`:''}`;
      button.setAttribute('aria-label',motor?title:`驱动工位 ${route.index+1}：${title}`);button.title=title;
      if(!motor&&route.motors.length>1){const count=document.createElement('span');count.className='drive-marker-count';count.textContent=`×${route.motors.length}`;button.append(count)}
      button.addEventListener('click',()=>{
        if(motor)this.setActiveMotor(route.id,index);
        this.onSelect(route.id,index,motor?{motor:true,anchorId:motorKey(motor)}:undefined);
      });this.container.append(button);
      const line=document.createElementNS('http://www.w3.org/2000/svg','line');this.leaders.append(line);this.markers.push({route,motor,index,button,line});
    });
    for(const route of this.routes){
      // Every repeated motor has a direct spatial target; only one carries the text label.
      if(!this.motorMarkers&&!['same_spinning_position','explicit_motor_groups'].includes(route.graph?.association)&&route.motors.length>1)route.motors.forEach((motor,index)=>{
        const dot=document.createElement('button');dot.type='button';dot.className='drive-station-dot';
        dot.dataset.driveMotorIndex=String(index);dot.dataset.driveRoute=route.id;
        dot.setAttribute('aria-label',`${route.label} · 电机 ${index+1}/${route.motors.length}`);
        dot.title=`${route.label} · 第 ${index+1} 处 / 共 ${route.motors.length} 处`;
        dot.addEventListener('click',()=>this.onSelect(route.id,index));this.container.append(dot);this.stationDots.push({route,index,button:dot});
      });
      route.branches=buildDriveBranches(route);
      for(const unmodeled of [false,true]){
        const edges=route.branches.filter(edge=>edge.unmodeled===unmodeled);if(!edges.length)continue;
        const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(new Float32Array(edges.length*6),3));
        const progress=new Float32Array(edges.length*2);for(let i=0;i<edges.length;i++)progress[i*2+1]=1;
        geometry.setAttribute('routeProgress',new THREE.BufferAttribute(progress,1));
        const settings={color:unmodeled?0xa38869:0xc96337,transparent:true,opacity:.6,depthTest:false,depthWrite:false};
        const material=unmodeled?new THREE.LineDashedMaterial({...settings,dashSize:.025,gapSize:.018}):pulseMaterial(settings);
        const lines=new THREE.LineSegments(geometry,material);lines.renderOrder=20;lines.frustumCulled=false;this.group.add(lines);
        let heads=null;
        if(!unmodeled){heads=new THREE.InstancedMesh(new THREE.ConeGeometry(1,1,5),new THREE.MeshBasicMaterial(settings),edges.length);heads.instanceMatrix.setUsage(THREE.DynamicDrawUsage);heads.frustumCulled=false;heads.renderOrder=21;this.group.add(heads)}
        this.branchBatches.push({route,edges,lines,heads,unmodeled});
      }
    }
    this.geometryDirty=true;this.setVisible(this.visible);
  }
  setVisible(visible){if(this.visible!==visible)this.geometryDirty=true;this.visible=visible;this.group.visible=visible;this.container.hidden=!visible}
  setActive(id){this.activeId=id||null;this.activeMotor=null;this.geometryDirty=true}
  setActiveMotor(id,index=0){
    this.setActive(id);const route=this.selectedRoute();if(!route?.motors.length)return;
    route.motorIndex=THREE.MathUtils.clamp(index,0,route.motors.length-1);this.activeMotor=route.motors[route.motorIndex];this.geometryDirty=true;
  }
  selectedRoute(){return this.routes.find(route=>route.id===this.activeId)||null}
  selectedMotorRoutes(){
    if(this.activeMotor)return motorDriveRoutes(this.routes,this.activeMotor);
    const route=this.selectedRoute();return route?[route.motors.length?scopeDriveRoute(route):route]:[];
  }
  moveStation(direction){const route=this.selectedRoute();if(!route?.motors.length)return;route.motorIndex=(route.motorIndex+direction+route.motors.length)%route.motors.length;if(this.activeMotor)this.activeMotor=route.motors[route.motorIndex];this.geometryDirty=true}
  markDirty(){this.geometryDirty=true}
  updateMovingEndpoints(){
    for(const {lines,heads,unmodeled,visibleEdges,movingEdges} of this.branchBatches){
      if(!lines.visible||!movingEdges?.length)continue;
      const {position,lineDistance}=lines.geometry.attributes;
      for(const i of movingEdges){
        const edge=visibleEdges[i],start=i*2;
        const a=centerOf(edge.from),b=centerOf(edge.to);
        position.setXYZ(start,a.x,a.y,a.z);position.setXYZ(start+1,b.x,b.y,b.z);
        if(heads){
          const direction=this.edgeDirection.subVectors(b,a).normalize();
          const length=Math.min(.045,a.distanceTo(b)*.2);
          this.arrowPose.position.copy(b).addScaledVector(direction,-length*.5);
          this.arrowPose.quaternion.setFromUnitVectors(this.arrowPose.up,direction);
          this.arrowPose.scale.set(length*.38,length,length*.38);this.arrowPose.updateMatrix();
          heads.setMatrixAt(i,this.arrowPose.matrix);
        }
      }
      if(unmodeled){
        let distance=0;
        for(let i=0;i<visibleEdges.length;i++){
          this.edgeStart.fromBufferAttribute(position,i*2);this.edgeEnd.fromBufferAttribute(position,i*2+1);
          lineDistance.setX(i*2,distance);distance+=this.edgeStart.distanceTo(this.edgeEnd);lineDistance.setX(i*2+1,distance);
        }
        lineDistance.needsUpdate=true;
      }
      position.needsUpdate=true;if(heads)heads.instanceMatrix.needsUpdate=true;
    }
  }
  updateTraverseEndpoints(){
    const batch=this.branchBatches.find(item=>item.route.id==='guide'&&item.unmodeled&&item.lines.visible);
    if(!batch?.visibleEdges?.length)return;
    const {position,lineDistance}=batch.lines.geometry.attributes;
    let distance=0;
    for(const [i,edge] of batch.visibleEdges.entries()){
      const start=i*2,end=start+1;
      const target=centerOf(edge.to);
      position.setXYZ(end,target.x,target.y,target.z);
      lineDistance.setX(start,distance);
      distance+=Math.hypot(target.x-position.getX(start),target.y-position.getY(start),target.z-position.getZ(start));
      lineDistance.setX(end,distance);
    }
    position.needsUpdate=true;lineDistance.needsUpdate=true;
  }
  highlightedObjects(){
    return new Set(this.activeId?this.selectedMotorRoutes().flatMap(route=>route.steps.flatMap(step=>step.objects)):this.routes.flatMap(route=>route.motors));
  }
  // elapsedSeconds is application-owned playback time (already speed-scaled).
  // Pause by passing the same time; the legacy three-argument API stays static.
  update(camera,width,height,elapsedSeconds){
    if(!this.visible)return;
    const layoutDirty=this.geometryDirty||width!==this.lastWidth||height!==this.lastHeight||!this.lastView.equals(camera.matrixWorld)||!this.lastProjection.equals(camera.projectionMatrix);
    if(this.geometryDirty){
      for(const route of this.routes){route.points=driveRoutePoints(route);route.stationPoints=route.motors.map(centerOf);route.markerPoint=route.stationPoints[route.motorIndex]||null}
      const scopedRoutes=new Map(this.selectedMotorRoutes().map(route=>[route.id,route]));
      const selectedBranches=new Map();
      for(const [id,route] of scopedRoutes)selectedBranches.set(id,buildDriveBranches(route));
      this.visibleRouteIds=this.activeId?new Set(scopedRoutes.keys()):new Set(this.routes.map(route=>route.id));
      const centerCache=new Map(),center=node=>{if(!centerCache.has(node))centerCache.set(node,centerOf(node));return centerCache.get(node)};
      const matrix=new THREE.Matrix4(),orientation=new THREE.Quaternion(),up=new THREE.Vector3(0,1,0),scale=new THREE.Vector3();
      const usedEdges=new Map();
      for(const batch of this.branchBatches){
        const {route,lines,heads,unmodeled}=batch;
        const visible=this.visibleRouteIds.has(route.id);lines.visible=visible;if(heads)heads.visible=visible;if(!visible)continue;
        const edges=(this.activeId?selectedBranches.get(route.id):batch.edges).filter(edge=>edge.unmodeled===unmodeled).filter(edge=>{
          // Shared motor/shaft paths belonging to two routes need one visible line.
          let targets=usedEdges.get(edge.from);if(!targets){targets=new Set();usedEdges.set(edge.from,targets)}
          const key=`${edge.to.uuid}:${unmodeled}`;if(targets.has(key))return false;targets.add(key);return true;
        });
        batch.visibleEdges=edges;lines.geometry.setDrawRange(0,edges.length*2);if(heads)heads.count=edges.length;
        if(route.graph?.association==='explicit_motor_groups'){
          batch.movingEdges=[];edges.forEach((edge,i)=>{if(hasMovingCenter(edge.from)||hasMovingCenter(edge.to))batch.movingEdges.push(i)});
        }
        const vertices=lines.geometry.attributes.position.array;
        edges.forEach((edge,index)=>{
          const a=center(edge.from),b=center(edge.to);a.toArray(vertices,index*6);b.toArray(vertices,index*6+3);
          if(heads){
            const direction=b.clone().sub(a),length=direction.length(),headLength=Math.min(.045,length*.2);
            orientation.setFromUnitVectors(up,length>0?direction.normalize():up);
            const position=b.clone().addScaledVector(direction,-headLength*.5);scale.set(headLength*.38,headLength,headLength*.38);
            matrix.compose(position,orientation,scale);heads.setMatrixAt(index,matrix);
          }
        });
        lines.geometry.attributes.position.needsUpdate=true;if(unmodeled)lines.computeLineDistances();
        const opacity=this.activeId ? .62 : this.motorMarkers ? .10 : .35;
        if(unmodeled)lines.material.opacity=opacity;
        else{lines.material.uniforms.opacity.value=opacity;lines.material.uniforms.pulseStrength.value=this.activeId ? .34 : this.motorMarkers ? .18 : .32}
        if(heads){heads.instanceMatrix.needsUpdate=true;heads.material.opacity=this.activeId ? .72 : this.motorMarkers ? .16 : .42}
      }
      this.geometryDirty=false;
    }
    if(Number.isFinite(elapsedSeconds))for(const {route,lines,unmodeled} of this.branchBatches)if(!unmodeled){
      lines.material.uniforms.elapsed.value=elapsedSeconds;
      lines.material.uniforms.pulseEnabled.value=route.operation==='maintenance'&&this.activeId!==route.id?0:1;
    }
    if(!layoutDirty)return;
    this.lastView.copy(camera.matrixWorld);this.lastProjection.copy(camera.projectionMatrix);this.lastWidth=width;this.lastHeight=height;
    for(const {route,index,button} of this.stationDots){
      const point=route.stationPoints[index]?.clone().project(camera);
      const show=point&&point.z>=-1&&point.z<=1&&Math.abs(point.x)<.99&&Math.abs(point.y)<.99&&(!this.activeId||this.activeId===route.id);
      button.hidden=!show;if(!show)continue;
      const active=this.activeId===route.id&&route.motorIndex===index;
      button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));
      button.style.transform=`translate(${(point.x+1)*width/2}px,${(1-point.y)*height/2}px) translate(-50%,-50%)`;
    }
    const projected=[];this.leaders.setAttribute('viewBox',`0 0 ${width} ${height}`);
    for(const marker of this.markers){
      const {route,motor,index,button,line}=marker;
      const point=(motor?route.stationPoints[index]:route.markerPoint)?.clone().project(camera),show=point&&point.z>=-1&&point.z<=1&&Math.abs(point.x)<=1.08&&Math.abs(point.y)<=1.08&&(this.motorMarkers||!this.activeId||this.activeId===route.id);
      button.hidden=!show;line.style.display=show?'':'none';if(!show)continue;
      projected.push({marker,x:(point.x+1)*width/2,y:(1-point.y)*height/2});
    }
    // Measure all visible labels before writing their positions to avoid repeated
    // forced layouts. The fallback also keeps headless tests deterministic.
    const entries=projected.map(item=>({...item,width:item.marker.button.offsetWidth||36,height:item.marker.button.offsetHeight||32}));
    const positions=layoutDriveMarkers(entries,width,height);
    for(let i=0;i<positions.length;i++){
      const {marker,x:left,y:top}=positions[i],{route,motor,index,button,line}=marker,{x,y}=projected[i];
      button.style.transform=`translate(${left}px,${top}px) translate(-50%,-50%)`;
      const active=motor?(this.activeMotor?sameMotor(this.activeMotor,motor):this.activeId===route.id&&route.motorIndex===index):this.activeId===route.id;
      button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));
      line.setAttribute('x1',x);line.setAttribute('y1',y);line.setAttribute('x2',left);line.setAttribute('y2',top);
    }
  }
}
