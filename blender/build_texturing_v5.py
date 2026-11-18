"""Export the selected current eFK standard configuration, without touching dist."""
from pathlib import Path
import bpy,math,sys,json,hashlib
from mathutils import Vector
source=Path(__file__).with_name('build_models.py')
exec(compile(source.read_text().split('builders=[')[0],str(source),'exec'))
module=Path(__file__).with_name('current_texturing_v5.py')
exec(compile(module.read_text(),str(module),'exec'))
root=machine_texturing()
bpy.context.view_layer.update()
nodes=list(root.children_recursive)
positions=[o for o in nodes if o.get('componentRole')=='texturing_position']
counts={'positions':len(positions),'activePOYPackages':sum(o.name.startswith('EFK_active_POY_package') and o.type=='EMPTY' for o in nodes),'DTYPackages':sum(o.get('componentRole')=='dty_package' for o in nodes),'continuousYarnPaths':sum(o.get('componentRole')=='continuous_yarn_path' for o in nodes),'frictionUnits':sum(o.get('componentRole')=='friction_unit' for o in nodes),'frictionShafts':sum(o.name.startswith('efk_friction_shaft_') and o.type=='EMPTY' for o in nodes),'G1':sum(o.get('componentRole')=='G1_godet' for o in nodes),'G2':sum(o.get('componentRole')=='G2_godet' for o in nodes),'takeupPositions':sum(o.get('componentRole')=='takeup_position' for o in nodes),'oilWheels':sum(o.name.startswith('EFK_oil_contact') and o.type=='EMPTY' for o in nodes),'traverseGuides':sum(o.name.startswith('EFK_traverse_guide') and o.type=='EMPTY' for o in nodes)}
assert sorted(o['positionIndex'] for o in positions)==list(range(1,385)), '384 unique consecutive position indices required'
for k,n in counts.items():assert n==(1152 if k=='frictionShafts' else 384),(k,n)
thermal=[]
for role,length in [('primary_channel',2.0),('cooling_channel',1.1),('secondary_channel',1.46)]:
 channels=[o for o in nodes if o.get('componentRole')==role and o.type=='EMPTY']
 assert len(channels)==384,(role,len(channels))
 errors=[]
 for o in channels:
  rails=[c for c in o.children if '_rail' in c.name]
  assert len(rails)==1,(o.name,len(rails))
  rail=rails[0];localzs=[v.co.z for v in rail.data.vertices]
  actual=(max(localzs)-min(localzs))*(rail.matrix_world.to_3x3()@Vector((0,0,1))).length
  errors.append(abs(actual-length))
 assert max(errors)<1e-5,(role,max(errors))
 thermal.append({'role':role,'count':len(channels),'expectedMetres':length,'maximumActualGeometryErrorMetres':max(errors)})
anchors=[{'name':o.name,'label':o.get('label'),'anchorId':o.get('driveAnchorId'),'locationMetres':list(o.matrix_world.translation)} for o in nodes if o.get('driveRole')=='motor']
assert len(anchors)==7 and all(a['name']==a['anchorId'] for a in anchors)
# Ray tests use actual generated surfaces, not matching counts or metadata.
# All twelve deck/column variants of a complete side-section are checked.
from mathutils.bvhtree import BVHTree
section=next(o for o in root.children if o.name.startswith('EFK_section_side'))
vs=[];fs=[];face_objects=[]
for o in section.children_recursive:
 if o.type!='MESH' or o.get('componentRole')=='continuous_yarn_path':continue
 offset=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices)
 for p in o.data.polygons:fs.append(tuple(offset+i for i in p.vertices));face_objects.append(o.name)
bvh=BVHTree.FromPolygons(vs,fs,all_triangles=False,epsilon=0)
yarn_hits=[];segments=0
for o in section.children_recursive:
 if o.get('componentRole')!='continuous_yarn_path':continue
 v=list(o.data.vertices);points=[o.matrix_world@(sum((x.co for x in v[i:i+5]),Vector())/5) for i in range(0,len(v),5)]
 for j,(a,b) in enumerate(zip(points,points[1:])):
  delta=b-a;length=delta.length
  if length<1e-7:continue
  segments+=1;hit,normal,index,distance=bvh.ray_cast(a+delta.normalized()*1e-5,delta.normalized(),max(0,length-2e-5))
  if hit is not None:yarn_hits.append({'positionIndex':o.parent.get('positionIndex'),'segment':j,'surface':face_objects[index],'point':list(hit)})
print('TEXTURING_YARN_SURFACE_CHECK',segments,'segments,',len(yarn_hits),'surface crossings',flush=True)
assert not yarn_hits, 'Generated yarn centerlines cross selected section surfaces: '+str(yarn_hits[:4])
print('TEXTURING_STRUCTURE_PASS',json.dumps(counts),flush=True)
out=QA/'v5-candidates/models';out.mkdir(parents=True,exist_ok=True)
src=BLEND/'v5-source';src.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(out/'texturing.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(src/'texturing.blend'))
pts=[o.matrix_world@Vector(c) for o in root.children_recursive if o.type=='MESH' for c in o.bound_box]
lo=Vector(tuple(min(p[k] for p in pts) for k in range(3)));hi=Vector(tuple(max(p[k] for p in pts) for k in range(3)))
report={'id':'texturing','objects':len(root.children_recursive),'meshNodes':sum(o.type=='MESH' for o in nodes),'uniqueSharedMeshes':len({o.data.name for o in nodes if o.type=='MESH'}),'bytes':(out/'texturing.glb').stat().st_size,'sha256':hashlib.sha256((out/'texturing.glb').read_bytes()).hexdigest(),'boundsMetres':{'min':list(lo),'max':list(hi)},'referenceModel':root.get('referenceModel'),'structuralCompleteness':False,'selectedCounts':dict(root.get('selectedCounts',{})),'actualCounts':counts,'thermalGeometryChecks':thermal,'motorAnchors':anchors,'yarnSurfaceChecks':{'testedVariants':12,'testedSegments':segments,'crossings':yarn_hits},'configurationCrossSectionInspected':False,'status':'pass_selected_population_and_thermal_geometry','evidenceLimit':'2023 official indexed full configuration plus historical manufacturer V-layout text and current component photographs; exact section installation drawing unavailable; local coordinates and common-drive placement inferred.'}
(QA/'v5-candidates/texturing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('TEXTURING_EXPORTED',json.dumps(report,ensure_ascii=False),flush=True)
if '--no-render' not in sys.argv:
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
 scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
 scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.73,.77,.82,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
 center=(lo+hi)/2;extent=max(hi-lo)
 for off,power in [((.35,-.65,1),1300),((-.7,.4,.8),900)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(off)*max(extent,5));o=bpy.context.object;o.data.energy=power*max(extent/6,1)**2;o.data.size=max(extent*.6,4);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
 direction=Vector((10,-16,13))
 bpy.ops.object.camera_add(location=center+direction.normalized()*extent*2.5);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.clip_end=1000
 q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));uv=[((p-center).dot(right),(p-center).dot(up)) for p in pts]
 umin=min(a for a,b in uv);umax=max(a for a,b in uv);vmin=min(b for a,b in uv);vmax=max(b for a,b in uv)
 cam.location+=right*((umin+umax)/2)+up*((vmin+vmax)/2);cam.data.ortho_scale=max(umax-umin,(vmax-vmin)*1.6)*1.12;scene.camera=cam
 scene.view_settings.view_transform='AgX';scene.render.filepath=str(QA/'v5-candidates/texturing-overview.png');bpy.ops.render.render(write_still=True)
 # Section close-up with full height, retaining actual neighboring components.
 target=Vector((-4.32,-1.70,2.85));cam.location=target+Vector((.65,-12,5.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=7.5
 scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.cycles.samples=24
 scene.render.filepath=str(QA/'v5-candidates/texturing-section.png');bpy.ops.render.render(write_still=True)
 target=Vector((-3.99,-1.55,3.08));cam.location=target+Vector((.15,.75,.32));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.85
 scene.render.resolution_x=1400;scene.render.resolution_y=1000
 scene.render.filepath=str(QA/'v5-candidates/texturing-friction.png');bpy.ops.render.render(write_still=True)
 # Explicit QA sectional view: isolate a complete two-sided section in the image
 # only. The already-exported GLB and saved blend retain all sixteen sections.
 selected=[o for o in root.children if o.name.startswith('EFK_section_side') and o.get('sectionIndex')==8]
 keep={o for s in selected for o in [s]+list(s.children_recursive)}
 for o in nodes:
  if o.type=='MESH':o.hide_render=o not in keep
 target=Vector((-.72,0,2.84));cam.location=target+Vector((-13,-1.8,1.4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.3
 scene.render.resolution_x=1600;scene.render.resolution_y=1100
 scene.render.filepath=str(QA/'v5-candidates/texturing-cross-section.png');bpy.ops.render.render(write_still=True)
 for o in nodes:
  if o.type=='MESH':o.hide_render=False
 print('TEXTURING_RENDERED overview / section / friction / isolated complete section',flush=True)
