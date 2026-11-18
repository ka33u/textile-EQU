import * as THREE from 'three';
/** Measure the imported scene before parenting: previous normalization must not leak into it. */
export function normalizeImportedModel(root,container,targetExtent=7.2,restBounds){
  root.removeFromParent();
  root.updateWorldMatrix(true,true);
  const rawBounds=restBounds||new THREE.Box3().setFromObject(root,true);
  if(rawBounds.isEmpty())throw new Error('Model has no visible geometry');
  const size=rawBounds.getSize(new THREE.Vector3());
  const extent=Math.max(size.x,size.y,size.z);
  if(!Number.isFinite(extent)||extent<=0)throw new Error('Invalid model bounds');
  const center=rawBounds.getCenter(new THREE.Vector3()),scale=targetExtent/extent;
  container.scale.setScalar(scale);
  container.position.set(-center.x*scale,-rawBounds.min.y*scale,-center.z*scale);
  container.add(root);
  container.updateWorldMatrix(true,true);
  return {scale,height:size.y*scale,rawBounds};
}
export function worldModelBounds(root){
  root.updateWorldMatrix(true,true);
  return new THREE.Box3().setFromObject(root);
}
