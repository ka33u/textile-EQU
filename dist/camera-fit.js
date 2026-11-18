/** Perspective framing math, independent of Three.js and the DOM. */
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const normalize=a=>{const length=Math.hypot(...a);if(length<1e-12)throw new Error('Camera direction must be non-zero');return a.map(v=>v/length)};
export function boundsCorners(bounds){
  const points=[];
  for(const x of [bounds.min[0],bounds.max[0]])for(const y of [bounds.min[1],bounds.max[1]])for(const z of [bounds.min[2],bounds.max[2]])points.push([x,y,z]);
  return points;
}
export function fitPerspectiveBounds(bounds,{direction,width,height,fov=37,padding=20,margin=1.04,minimumDistance=0}){
  if(width<=padding*2||height<=padding*2)throw new Error('Viewport has no usable framing area');
  const center=bounds.min.map((v,i)=>(v+bounds.max[i])/2);
  const outward=normalize(direction);
  let right=cross([0,1,0],outward);
  if(Math.hypot(...right)<1e-9)right=[1,0,0];else right=normalize(right);
  const up=normalize(cross(outward,right));
  const tangentY=Math.tan(fov*Math.PI/360),tangentX=tangentY*width/height;
  const safeX=1-padding*2/width,safeY=1-padding*2/height;
  let distance=minimumDistance;
  for(const corner of boundsCorners(bounds)){
    const point=corner.map((v,i)=>v-center[i]);
    const depth=dot(point,outward);
    distance=Math.max(distance,Math.abs(dot(point,right))/(tangentX*safeX)+depth,Math.abs(dot(point,up))/(tangentY*safeY)+depth);
  }
  distance=Math.max(.01,distance*margin);
  const diagonal=Math.hypot(...bounds.max.map((v,i)=>v-bounds.min[i]));
  return {center,direction:outward,distance,position:center.map((v,i)=>v+outward[i]*distance),near:Math.max(.001,Math.min(.05,diagonal/2000)),far:Math.max(100,distance+diagonal*4),safeX,safeY};
}
