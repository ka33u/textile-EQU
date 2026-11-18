from pathlib import Path
import bpy, math, sys, json
from mathutils import Vector
source=Path(__file__).with_name('build_models.py');exec(compile(source.read_text().split('builders=[')[0],str(source),'exec'))
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['calender','carding','weaving','spinning','stenter']
export_assets='__no_export__' not in ids
ids=[x for x in ids if x!='__no_export__']
fn={k:globals()['machine_'+k] for k in ['opening','carding','drawing','combing','winding','warping','sizing','drawing_in','weaving','pretreatment','dyeing','stenter','calender','inspection']}
fn['roving']=lambda:spinning_family('roving',True);fn['spinning']=lambda:spinning_family('spinning')
(QA/'v2-model-previews').mkdir(exist_ok=True)
report=[]
for stage in ids:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    r=fn[stage]();reused=optimize_stage(r)
    bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=r
    if export_assets:bpy.ops.export_scene.gltf(filepath=str(OUT/(stage+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
    bpy.context.view_layer.update();pts=[o.matrix_world @ Vector(c) for o in r.children_recursive if o.type=='MESH' for c in o.bound_box]
    lo=Vector(tuple(min(p[k] for p in pts) for k in range(3)));hi=Vector(tuple(max(p[k] for p in pts) for k in range(3)));center=(lo+hi)/2;extent=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.73,.8,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    for off,en in [((4,-6,9),1600),((-6,3,7),1200)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(off));bpy.context.object.data.energy=en;bpy.context.object.data.size=7;bpy.context.object.rotation_euler=(center-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=center+Vector((8,-11,7)));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));uv=[((p-center).dot(right),(p-center).dot(up)) for p in pts];umin=min(a for a,b in uv);umax=max(a for a,b in uv);vmin=min(b for a,b in uv);vmax=max(b for a,b in uv);cam.location+=right*((umin+umax)/2)+up*((vmin+vmax)/2);cam.data.ortho_scale=max(umax-umin,(vmax-vmin)*1.25)*1.18;scene.camera=cam
    scene.view_settings.view_transform='AgX';scene.render.filepath=str(QA/'v2-model-previews'/(stage+'.png'));bpy.ops.render.render(write_still=True)
    report.append({'id':stage,'objects':len(r.children_recursive),'sharedMeshes':reused,'bytes':(OUT/(stage+'.glb')).stat().st_size});print('PREVIEW_READY',json.dumps(report[-1]),flush=True)
(QA/'preview-batch-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
