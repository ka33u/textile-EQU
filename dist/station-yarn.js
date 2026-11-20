import * as THREE from 'three';
import {measurePolyline, samplePolyline} from './texturing-motion.js?v=20261119-stations';

// Coordinates on each yarn anchor are the centreline used to build its visible thread.
// Only the selected polyline and three direction markers are submitted to the GPU.
export class StationYarn {
  constructor(root, scene) {
    this.paths = [];
    this.index = -1;
    this.elapsed = 0;
    root.traverse(node => {
      const xyz = node.userData.stationYarnPath;
      if (!Array.isArray(xyz) || xyz.length < 6 || xyz.length % 3) return;
      let unit = node;
      while (unit.parent && unit.userData.positionIndex === undefined) unit = unit.parent;
      this.paths.push({node,xyz,number:unit.userData.positionIndex || 1,side:unit.userData.machineSide || ''});
    });
    this.paths.sort((a,b) => a.number-b.number);
    if (!this.paths.length) return;
    this.overlay = new THREE.Group();
    this.overlay.matrixAutoUpdate = false;
    this.overlay.name = 'selected_yarn_flow';
    scene.add(this.overlay);
    this.line = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({
      color:0x007f87,transparent:true,opacity:.9,depthTest:false,depthWrite:false
    }));
    this.line.renderOrder=35;
    this.dots = new THREE.InstancedMesh(new THREE.SphereGeometry(1,10,6),
      new THREE.MeshBasicMaterial({color:0x09bcc3,depthTest:false,depthWrite:false}),3);
    this.dots.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.dots.renderOrder=36;this.dots.frustumCulled=false;
    this.overlay.add(this.line,this.dots);
    this.pose = new THREE.Object3D();
    this.select(0);
  }

  select(index) {
    if (!this.paths[index]) return;
    this.index = index;this.elapsed=0;
    const xyz=this.paths[index].xyz, points=[];
    for(let i=0;i<xyz.length;i+=3) points.push(new THREE.Vector3(xyz[i],xyz[i+1],xyz[i+2]));
    this.path = measurePolyline(points);
    this.line.geometry.dispose();
    this.line.geometry=new THREE.BufferGeometry().setFromPoints(points);
    this.pose.scale.setScalar(THREE.MathUtils.clamp(this.path.total*.0031,.005,.027));
    this.update(0);
  }

  update(delta) {
    if (!this.overlay?.visible) return;
    const anchor=this.paths[this.index].node;
    anchor.updateWorldMatrix(true,false);
    this.overlay.matrix.copy(anchor.matrixWorld);
    this.overlay.matrixWorldNeedsUpdate=true;
    this.elapsed=(this.elapsed+delta*.16)%1;
    for(let i=0;i<this.dots.count;i++){
      samplePolyline(this.path,(this.elapsed+i/this.dots.count)%1,this.pose.position);
      this.pose.updateMatrix();this.dots.setMatrixAt(i,this.pose.matrix);
    }
    this.dots.instanceMatrix.needsUpdate=true;
  }

  dispose() {
    if (!this.overlay) return;
    this.overlay.removeFromParent();
    this.line.geometry.dispose();this.line.material.dispose();
    this.dots.geometry.dispose();this.dots.material.dispose();this.dots.dispose();
  }
}
