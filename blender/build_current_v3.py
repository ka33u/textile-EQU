"""Build review candidates without overwriting the running local release.
Blender --background --factory-startup --python blender/build_current_v3.py -- <stage...>
"""
from pathlib import Path
import sys, json, math, hashlib, struct
import bpy
from mathutils import Vector
source=Path(__file__).with_name('build_models.py')
exec(compile(source.read_text().split('builders=[')[0],str(source),'exec'))

CANDIDATE=QA/'v3-candidates';CANDIDATE.mkdir(exist_ok=True)
OUT=CANDIDATE/'models';OUT.mkdir(exist_ok=True)
PREV=QA/'v3-model-previews';PREV.mkdir(exist_ok=True)
SRC=BLEND/'v3-source';SRC.mkdir(exist_ok=True)
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['opening','carding','drawing','combing','roving','spinning','winding','warping','sizing','drawing_in','weaving','pretreatment','dyeing','stenter','calender','inspection']
render='__no_render__' not in ids;ids=[i for i in ids if i!='__no_render__']
fn={k:globals()['machine_'+k] for k in ['opening','carding','drawing','combing','winding','warping','sizing','drawing_in','weaving','pretreatment','dyeing','stenter','calender','inspection']}
fn['roving']=lambda:spinning_family('roving',True);fn['spinning']=lambda:spinning_family('spinning')

def share_exact_geometry(root):
    seen={};shared={};reused=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        me=o.data;keyptr=me.as_pointer()
        if keyptr in seen:
            o.data=seen[keyptr];reused+=1;continue
        h=hashlib.sha256();h.update('|'.join(m.name for m in me.materials).encode())
        for v in me.vertices:h.update(struct.pack('<fff',*v.co))
        for p in me.polygons:
            h.update(struct.pack('<I?',len(p.vertices),p.use_smooth));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
        key=h.digest()
        if key in shared:o.data=shared[key];reused+=1
        else:shared[key]=me
        seen[keyptr]=o.data
    root['sharedGeometryInstances']=reused
    return reused

for stage in ids:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    print('BUILD_START',stage,flush=True)
    root=fn[stage]()
    if root.get('modelVersion')!='3.0':raise RuntimeError(stage+' has no current-generation builder')
    reused=share_exact_geometry(root)
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(c) for o in root.children_recursive if o.type=='MESH' for c in o.bound_box]
    lo=Vector(tuple(min(p[k] for p in pts) for k in range(3)));hi=Vector(tuple(max(p[k] for p in pts) for k in range(3)))
    center=(lo+hi)/2
    bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=str(OUT/(stage+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/(stage+'.blend')))
    report={'id':stage,'objects':len(root.children_recursive),'sharedMeshes':reused,'bytes':(OUT/(stage+'.glb')).stat().st_size,'sha256':hashlib.sha256((OUT/(stage+'.glb')).read_bytes()).hexdigest(),'boundsMetres':{'min':list(lo),'max':list(hi)},'referenceModel':root.get('referenceModel'),'structuralCompleteness':False}
    (CANDIDATE/(stage+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('CANDIDATE_EXPORTED',json.dumps(report,ensure_ascii=False),flush=True)
    if not render:continue
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
    scene.render.resolution_x=1440;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.73,.77,.82,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    extent=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)
    for off,energy in [((.35,-.65,1),1300),((-.7,.4,.8),900)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(off)*max(extent,5));o=bpy.context.object;o.data.energy=energy*max(extent/6,1)**2;o.data.size=max(extent*.6,4);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    direction=Vector((8,-11,8))
    bpy.ops.object.camera_add(location=center+direction.normalized()*max(extent*2,12));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO'
    q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));uv=[((p-center).dot(right),(p-center).dot(up)) for p in pts]
    umin=min(a for a,b in uv);umax=max(a for a,b in uv);vmin=min(b for a,b in uv);vmax=max(b for a,b in uv)
    cam.location+=right*((umin+umax)/2)+up*((vmin+vmax)/2);cam.data.ortho_scale=max(umax-umin,(vmax-vmin)*1.6)*1.13;cam.data.clip_end=max(extent*10,1000);scene.camera=cam
    scene.view_settings.view_transform='AgX';scene.render.filepath=str(PREV/(stage+'.png'));bpy.ops.render.render(write_still=True)
    print('PREVIEW_READY',stage,flush=True)
