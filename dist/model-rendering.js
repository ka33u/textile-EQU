import * as THREE from 'three';

// Keep the original mesh as the unit of selection, drive assignment and measurement.
// Only the draw submission for repeated opaque geometry moves to an instance batch.
export const PICK_LAYER=1;
const reflection=new THREE.Matrix4().makeScale(-1,1,1);
const motorColor=new THREE.Color(0xd96827);
const WIREFRAME=1,HIGHLIGHT=2,MOTOR_TINT=4,XRAY_SHELL=8;
const contextMaterials=new WeakSet();
function supportsInstanceNormals(matrix){
  // Three's instance-normal transform supports nonuniform scale, but not shear.
  const m=matrix.elements;
  for(const [a,b] of [[0,4],[0,8],[4,8]]){
    const dot=m[a]*m[b]+m[a+1]*m[b+1]+m[a+2]*m[b+2];
    const lengthA=m[a]**2+m[a+1]**2+m[a+2]**2,lengthB=m[b]**2+m[b+1]**2+m[b+2]**2;
    if(dot*dot>1e-12*lengthA*lengthB)return false;
  }
  return true;
}

export class ModelMaterials {
  constructor(meshes){
    this.meshes=meshes;
    this.original=new Map(meshes.map(mesh=>[mesh,mesh.material]));
    this.variants=new Map();
    this.arrays=new WeakMap();
  }
  material(base,style){
    if(!style)return base;
    const variants=Array.isArray(base)?this.arrays:this.variants;
    if(!variants.has(base))variants.set(base,new Map());
    const cache=variants.get(base);
    if(cache.has(style))return cache.get(style);
    if(Array.isArray(base)){
      const array=base.map(material=>this.material(material,style));cache.set(style,array);return array;
    }
    const material=base.clone();
    if(style&WIREFRAME)material.wireframe=true;
    if(style&MOTOR_TINT)material.color?.lerp(motorColor,.85);
    if((style&HIGHLIGHT)&&material.emissive){material.emissive.set(0xda643b);material.emissiveIntensity=.45}
    const opacity=(style>>4)/100;
    if(opacity){material.transparent=true;material.depthWrite=false;material.opacity=style&XRAY_SHELL?opacity:Math.min(base.opacity,opacity)}
    if([6,9,14,20].includes(style>>4)){
      // Context fades keep both faces of a two-sided surface in one submission.
      material.forceSinglePass=true;contextMaterials.add(material);
    }
    cache.set(style,material);return material;
  }
  apply({wire,xray,motorTint,dimMotor,dimYarn,selected,highlighted,yarns,shells}){
    let changed=false;
    for(const mesh of this.meshes){
      let marked=false,onYarn=false;
      if(selected||highlighted.size||dimYarn){
        for(let p=mesh;p;p=p.parent){
          if(p===selected||highlighted.has(p))marked=true;
          if(dimYarn&&yarns.has(p))onYarn=true;
        }
      }
      const shell=shells.has(mesh);
      let percent=xray&&shell?17:0;
      if(dimMotor&&!marked)percent=shell?9:20;
      if(dimYarn&&!onYarn)percent=shell?6:14;
      if(xray&&shell&&marked)percent=60;
      const orange=motorTint&&marked;
      // There are only a handful of combinations per view. Each source material
      // gets one immutable variant per combination, shared across all stations.
      const style=(wire?WIREFRAME:0)|(marked?HIGHLIGHT:0)|(orange?MOTOR_TINT:0)|(xray&&shell?XRAY_SHELL:0)|(percent<<4);
      const next=this.material(this.original.get(mesh),style);
      if(mesh.material!==next){mesh.material=next;changed=true}
    }
    return changed;
  }
  restore(){
    for(const [mesh,material] of this.original)mesh.material=material;
  }
  dispose(){
    this.restore();
    for(const cache of this.variants.values())for(const material of cache.values())material.dispose();
    this.variants.clear();this.arrays=new WeakMap();
  }
}

export class ModelBatches {
  constructor(scene,root,meshes,moving){
    this.group=new THREE.Group();scene.add(this.group);
    this.root=root;this.meshes=meshes;this.dynamic=new Set();
    this.members=[];this.batches=[];this.matrix=new THREE.Matrix4();this.regions=new Map();this.blocks=new Map();
    this.direction=new THREE.Vector3();this.sortDirection=new THREE.Vector3();
    this.point=new THREE.Vector3();
    for(const mesh of meshes){
      let side,section;
      for(let p=mesh;p;p=p.parent){
        if(moving.has(p))this.dynamic.add(mesh);
        side??=p.userData.machineSide;section??=p.userData.sectionIndex;
      }
      this.regions.set(mesh,[side,section].join('/'));
      this.blocks.set(mesh,section===undefined?'':Math.floor((section-1)/4));
    }
    this.rebuild();
  }
  clear(){
    for(const mesh of this.members)mesh.layers.set(0);
    for(const {draw} of this.batches)draw.dispose();
    this.group.clear();this.members=[];this.batches=[];this.sorted=[];
  }
  rebuild(){
    this.clear();this.root.updateWorldMatrix(true,true);
    const groups=new Map();
    for(const mesh of this.meshes){
      const material=mesh.material;
      // Original glass and fabric retain Three's per-object transparency sorting.
      const contextFade=contextMaterials.has(material);
      if(mesh.layers.mask!==1||!mesh.visible||mesh.isSkinnedMesh||mesh.morphTargetInfluences||Array.isArray(material)||(material.transparent&&!contextFade))continue;
      const matrix=mesh.matrixWorld,det=matrix.determinant();
      if(!det||!supportsInstanceNormals(matrix))continue;
      const key=[mesh.geometry.id,material.id,mesh.castShadow,mesh.receiveShadow,mesh.renderOrder,det<0,contextFade?this.regions.get(mesh):this.blocks.get(mesh)].join('/');
      if(!groups.has(key))groups.set(key,[]);
      groups.get(key).push(mesh);
    }
    for(const nodes of groups.values()){
      if(nodes.length<(contextMaterials.has(nodes[0].material)?2:4))continue;
      const first=nodes[0],mirrored=first.matrixWorld.determinant()<0;
      const draw=new THREE.InstancedMesh(first.geometry,first.material,nodes.length);
      draw.castShadow=first.castShadow;draw.receiveShadow=first.receiveShadow;draw.renderOrder=first.renderOrder;
      if(mirrored)draw.scale.x=-1;
      this.group.add(draw);
      const dynamic=[];
      nodes.forEach((mesh,index)=>{
        mesh.layers.set(PICK_LAYER);this.members.push(mesh);
        if(this.dynamic.has(mesh))dynamic.push(index);
      });
      if(dynamic.length)draw.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      // Moving shafts and deforming yarn can leave their rest bounds. Static
      // sections can be culled in close-ups, with fresh bounds after an explosion.
      draw.frustumCulled=!dynamic.length&&first.geometry.attributes.position.usage!==THREE.DynamicDrawUsage;
      const batch={nodes,draw,mirrored,dynamic};this.batches.push(batch);
      if(contextMaterials.has(first.material)){
        // Native transparent sorting compares object centres. Limit each batch to
        // one machine section and side, then depth-sort its members within it.
        batch.order=nodes.map((_,i)=>i);batch.depth=new Float64Array(nodes.length);
        batch.resort=true;this.sorted.push(batch);
      }
      this.write(batch,true);
      if(batch.order||draw.frustumCulled)draw.computeBoundingSphere();
    }
  }
  write(batch,full){
    const {nodes,draw,mirrored,dynamic,order}=batch;
    if(order&&!full){if(dynamic.length)batch.resort=true;return}
    const count=full?nodes.length:dynamic.length;
    for(let i=0;i<count;i++){
      const slot=full?i:dynamic[i],world=nodes[order?order[slot]:slot].matrixWorld;
      draw.setMatrixAt(slot,mirrored?this.matrix.multiplyMatrices(reflection,world):world);
    }
    if(count)draw.instanceMatrix.needsUpdate=true;
  }
  update(full=false){
    this.root.updateWorldMatrix(true,true);
    for(const batch of this.batches){
      this.write(batch,full);
      if(full){
        if(batch.order)batch.resort=true;
        if(batch.order||batch.draw.frustumCulled)batch.draw.computeBoundingSphere();
      }
    }
  }
  sortFades(camera){
    if(!this.sorted.length)return;
    const matrix=camera.matrixWorldInverse.elements;
    this.direction.set(matrix[2],matrix[6],matrix[10]);
    const viewChanged=!this.direction.equals(this.sortDirection);
    for(const batch of this.sorted){
      if(!viewChanged&&!batch.resort)continue;
      const {nodes,order,depth}=batch;
      const geometry=batch.draw.geometry;
      if(!geometry.boundingSphere)geometry.computeBoundingSphere();
      for(let i=0;i<nodes.length;i++){
        depth[i]=this.point.copy(geometry.boundingSphere.center).applyMatrix4(nodes[i].matrixWorld).dot(this.direction);
      }
      order.sort((a,b)=>depth[a]-depth[b]||a-b);
      this.write(batch,true);batch.resort=false;
    }
    this.sortDirection.copy(this.direction);
  }
  dispose(){this.clear();this.group.removeFromParent()}
}
