"""Build only the two additional equipment candidates, never the release assets."""
from pathlib import Path
import sys,json,hashlib,struct,math
import bpy
from mathutils import Vector

source=Path(__file__).with_name('build_models.py')
exec(compile(source.read_text().split('builders=[')[0],str(source),'exec'))
source=BLEND/'current_extensions_v5.py'
exec(compile(source.read_text(),str(source),'exec'))
DEST=QA/'v5-candidates';OUT=DEST/'models';SAVE=BLEND/'v5-source';PREVIEW=DEST/'previews'
for p in (DEST,OUT,SAVE,PREVIEW):p.mkdir(parents=True,exist_ok=True)

def share_geometry(root):
    seen={};meshes={};reuse=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        me=o.data;ptr=me.as_pointer()
        if ptr in seen:o.data=seen[ptr];reuse+=1;continue
        h=hashlib.sha256();h.update('|'.join(m.name for m in me.materials).encode())
        for v in me.vertices:h.update(struct.pack('<fff',*v.co))
        for p in me.polygons:h.update(struct.pack('<I?',len(p.vertices),p.use_smooth));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
        key=h.digest()
        if key in meshes:o.data=meshes[key];reuse+=1
        else:meshes[key]=me
        seen[ptr]=o.data
    return reuse

def render_selection(root,objects,path,full=True):
    members=set(objects)
    for o in bpy.context.scene.objects:o.hide_render=o not in members
    points=[o.matrix_world@Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
    low=Vector(tuple(min(p[k] for p in points) for k in range(3)));high=Vector(tuple(max(p[k] for p in points) for k in range(3)));center=(low+high)/2;extent=max(high-low)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
    scene.render.resolution_x=1600 if full else 1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.68,.73,.78,1);bg.inputs[1].default_value=.70
    for offset,energy in [((.3,-.6,1.1),1100),((-.6,.4,.8),800)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(offset)*max(extent,3));o=bpy.context.object;o.data.energy=energy*max(extent/6,1)**2;o.data.size=max(extent*.6,3);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    direction=Vector((.6,-1.2,.67) if full else (.7,-1.5,.7)).normalized()
    bpy.ops.object.camera_add(location=center+direction*max(extent*2,5));cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO'
    q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));uv=[((p-center).dot(right),(p-center).dot(up)) for p in points]
    umin=min(a for a,b in uv);umax=max(a for a,b in uv);vmin=min(b for a,b in uv);vmax=max(b for a,b in uv)
    aspect=scene.render.resolution_x/scene.render.resolution_y;cam.location+=right*((umin+umax)/2)+up*((vmin+vmax)/2)
    cam.data.ortho_scale=max(umax-umin,(vmax-vmin)*aspect)*1.12;cam.data.clip_end=1000;scene.camera=cam
    scene.view_settings.view_transform='AgX';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def build(stage):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    root=globals()['machine_'+stage]();reuse=share_geometry(root);bpy.context.view_layer.update()
    nodes=list(root.children_recursive);motors=[o for o in nodes if o.get('driveRole')=='motor']
    for m in motors:
        assert m.get('motorDetailScope')=='external_only'
        assert not any(any(x in c.name.lower() for x in ('rotor_core','stator','winding','bearing')) for c in m.children_recursive)
    if stage=='compact_spinning':
        positions=[o for o in nodes if o.name.startswith('K48_compact_position') and o.type=='EMPTY']
        assert len(positions)==288 and sorted(o['positionIndex'] for o in positions)==list(range(1,289))
        assert sum(o.name.startswith('K48_perforated_compacting_drum') for o in nodes)==288
        assert sum(o.name.startswith('K48_Detect_air_guide') and o.type=='EMPTY' for o in nodes)==288
        assert sum(o.name.startswith('K48_four_spindle_tape_group') for o in nodes)==72
        assert sum(o.name.startswith('K48_48_spindle_section') for o in nodes)==6
        expected={'spindles':288,'compactingUnits':288,'DetectGuides':288,'sections':6,'fourSpindleTapeGroups':72,'motorAnchors':5}
    else:
        positions=[o for o in nodes if o.name.startswith('CompactTwister_position') and o.type=='EMPTY']
        assert len(positions)==20 and sorted(o['positionIndex'] for o in positions)==list(range(1,21))
        assert sum(o.name.startswith('CT_stationary_pot') and o.type=='EMPTY' for o in nodes)==20
        assert sum(o.name.startswith('rotate_CT_storage_disc') for o in nodes)==20
        expected={'spindles':20,'stationaryPots':20,'storageDiscs':20,'sections':1,'motorAnchors':len(motors)}
    assert len(motors)==expected['motorAnchors']
    bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
    for o in nodes:o.select_set(True)
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'{stage}.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(SAVE/f'{stage}.blend'))
    points=[o.matrix_world@Vector(c) for o in nodes if o.type=='MESH' for c in o.bound_box]
    report={'id':stage,'status':'pass','validationScope':'selected counts, finite geometry, exterior motor semantics; not full OEM structure',
       'modelVersion':root['modelVersion'],'driveRevision':root['driveRevision'],'referenceModel':root['referenceModel'],
       'structuralCompleteness':False,'counts':expected,'objects':len(nodes),'sharedMeshInstances':reuse,
       'boundsMetres':{'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)]},
       'bytes':(OUT/f'{stage}.glb').stat().st_size,'sha256':hashlib.sha256((OUT/f'{stage}.glb').read_bytes()).hexdigest(),
       'motors':[{'anchorId':m['driveAnchorId'],'name':m.name,'label':m.get('label'),'position':list(m.matrix_world.translation),'layoutEvidence':m.get('motorLayoutEvidence')} for m in motors]}
    (DEST/f'{stage}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('EXTENSION_EXPORTED',json.dumps(report,ensure_ascii=False),flush=True)
    render_selection(root,nodes,PREVIEW/f'{stage}-full.png')
    selected=[g for g in positions if g.get('positionIndex') in ((70,71,72) if stage=='compact_spinning' else (4,5))]
    render_selection(root,[o for g in selected for o in [g]+list(g.children_recursive)],PREVIEW/f'{stage}-process-detail.png',False)

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['compact_spinning','twisting']
for stage in args:build(stage)
