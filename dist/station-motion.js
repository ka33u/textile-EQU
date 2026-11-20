import * as THREE from 'three';

const axes={x:new THREE.Vector3(1,0,0),y:new THREE.Vector3(0,1,0),z:new THREE.Vector3(0,0,1)};

/** Animate exported mechanisms in the coordinate frame in which the builder placed them. */
export class StationMotion {
  constructor(root){
    this.entries=[];this.byOwner=new Map();this.managedNodes=new Set();this.turn=new THREE.Quaternion();
    root.traverse(node=>{
      if(!node.userData.stationMotion)return;
      const [kind,axis]=node.userData.stationMotion.split(':');
      const entry={node,kind,axis,speed:node.userData.motionSpeed,amplitude:node.userData.motionAmplitude,
        phase:0,rest:node.position.clone(),rotation:node.quaternion.clone()};
      this.entries.push(entry);this.managedNodes.add(node);
      for(let owner=node;owner;owner=owner.parent){
        if(!owner.userData.driveAnchorId)continue;
        if(!this.byOwner.has(owner))this.byOwner.set(owner,[]);
        this.byOwner.get(owner).push(entry);
      }
    });
    this.production=this.entries;this.select(null);
  }
  setRoutes(routes){
    const maintenance=new Set(),production=new Set();
    for(const route of routes){
      const target=route.operation==='maintenance'||route.loadUnassigned?maintenance:production;
      for(const step of route.steps)for(const object of step.objects){
        for(const entry of this.byOwner.get(object)||[])target.add(entry);
      }
    }
    this.production=this.entries.filter(e=>!maintenance.has(e)||production.has(e));
    this.select(null);
  }
  select(scopes){
    if(scopes===null){this.active=this.production;return}
    const entries=new Set();
    for(const route of scopes){
      if(route.loadUnassigned)continue;
      if(!route.motors.length&&!(route.actuation==='pneumatic'&&route.evidence.status==='public_confirmed'))continue;
      for(const step of route.steps)for(const node of step.objects){
        for(const entry of this.byOwner.get(node)||[])entries.add(entry);
      }
    }
    this.active=[...entries];
  }
  update(delta){
    if(!delta)return;
    for(const e of this.active){
      e.phase=(e.phase+delta*e.speed)%(2*Math.PI);
      if(e.kind==='translate')e.node.position[e.axis]=e.rest[e.axis]+e.amplitude*Math.sin(e.phase);
      else {
        const angle=e.kind==='oscillate'?e.amplitude*Math.sin(e.phase):e.phase;
        e.node.quaternion.copy(e.rotation).multiply(this.turn.setFromAxisAngle(axes[e.axis],angle));
      }
    }
  }
  dispose(){
    for(const e of this.entries){e.node.position.copy(e.rest);e.node.quaternion.copy(e.rotation)}
  }
}
