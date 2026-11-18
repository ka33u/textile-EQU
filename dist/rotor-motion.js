import * as THREE from 'three';

const up=new THREE.Vector3(0,1,0);
const speeds={cup:7,opening:3.8,feed:.8,package:1.6,guide:1.3,delivery:1.4};

function restYarn(mesh){
  const direction=up.clone().applyQuaternion(mesh.quaternion).multiplyScalar(mesh.scale.y*.5);
  return {mesh,start:mesh.position.clone().sub(direction),end:mesh.position.clone().add(direction),
    position:mesh.position.clone(),quaternion:mesh.quaternion.clone(),scale:mesh.scale.clone()};
}

/** One motion scope per physical R 70 motor; frame rates are for visual observation. */
export class RotorMotion{
  constructor(root){
    this.managedNodes=new Set();this.rotors=[];this.guides=[];
    this.direction=new THREE.Vector3();this.start=new THREE.Vector3();this.end=new THREE.Vector3();
    root.traverse(station=>{
      if(!station.userData.sidePosition)return;
      const position=station.userData.positionIndex;
      const guide=station.children.find(node=>node.userData.anchorPart==='guide_load');
      const yarn=station.children.filter(node=>node.userData.travelYarn).map(restYarn);
      if(!guide||yarn.length!==2)throw new Error('Incomplete R 70 yarn traverse at position '+position);
      this.guides.push({position,guide,rest:guide.position.x,yarn,phase:0});
      this.managedNodes.add(guide);for(const {mesh} of yarn)this.managedNodes.add(mesh);
      station.traverse(node=>{
        if(!node.userData.spinAxis)return;
        let owner=node;
        while(owner&&!owner.userData.anchorPart)owner=owner.parent;
        if(!owner)throw new Error('Unmapped R 70 motion: '+node.name);
        const kind=owner.userData.anchorPart.split('_')[0];
        this.managedNodes.add(node);
        this.rotors.push({node,position,kind,axis:node.userData.spinAxis,
          speed:(speeds[kind]||1)*(node.userData.spinSpeed??.7),rest:node.quaternion.clone()});
      });
    });
    this.select(null);
  }
  select(route){
    const motor=route?.motors[route.motorIndex];
    const stationID=motor?.parent.userData.positionIndex;
    const accepts=(kind,position)=>!route||(motor&&route.id===kind&&position===stationID);
    this.activeRotors=this.rotors.filter(item=>accepts(item.kind,item.position));
    this.activeGuides=this.guides.filter(item=>accepts('guide',item.position));
  }
  update(delta){
    for(const {node,axis,speed} of this.activeRotors)node.rotation[axis]+=delta*speed;
    for(const item of this.activeGuides){
      item.phase+=delta*2.2;
      const x=Math.sin(item.phase)*item.guide.userData.travelAmplitude;
      item.guide.position.x=item.rest+x;
      for(const line of item.yarn){
        const {mesh}=line;
        this.start.copy(line.start);this.end.copy(line.end);
        // The two yarn segments share the moving eye. The winding contact follows
        // it across the package while the upstream delivery nip stays fixed.
        if(mesh.userData.travelYarn==='out')this.start.x+=x;
        this.end.x+=x;
        const length=this.direction.subVectors(this.end,this.start).length();
        mesh.position.addVectors(this.start,this.end).multiplyScalar(.5);
        mesh.quaternion.setFromUnitVectors(up,this.direction.multiplyScalar(1/length));
        mesh.scale.y=length;
      }
    }
  }
  dispose(){
    for(const {node,rest} of this.rotors)node.quaternion.copy(rest);
    for(const {guide,rest,yarn} of this.guides){
      guide.position.x=rest;
      for(const l of yarn){l.mesh.position.copy(l.position);l.mesh.quaternion.copy(l.quaternion);l.mesh.scale.copy(l.scale)}
    }
  }
}
