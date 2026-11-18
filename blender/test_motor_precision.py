"""Isolated Blender check; only writes motor preview artifacts in qa/."""
from pathlib import Path
import json,math
path=Path(__file__).resolve().parent
source=(path/'build_models.py').read_text()
base_code=source.split("exec(compile((BLEND/'industrial_v2.py')",1)[0]
exec(compile(base_code,str(path/'build_models.py'),'exec'))
exec(compile((path/'industrial_v2.py').read_text(),str(path/'industrial_v2.py'),'exec'))
exec(compile((path/'motor_precision.py').read_text(),str(path/'motor_precision.py'),'exec'))
root=empty('stage_motor',label='精细三相异步电机');root['stage']='motor'
box('motor_plinth',(0,0,.15),(3.0,1.85,.3),'white',root,'电机展示底座',bevel=.06)
g=motor(root,(0,0,1.0),1.4,True)
objects=list(root.children_recursive)
coils=[o for o in objects if o.name.startswith('distributed_double_layer_coil')]
teeth=[o for o in objects if o.name.startswith('stator_tooth.') or o.name=='stator_tooth']
blades=[o for o in objects if o.name.startswith('curved_cooling_fan_blade')]
assert len(coils)==72,len(coils)
assert len(teeth)>12,len(teeth)
assert len(blades)==9,len(blades)
assert not any(o.name.startswith(('distributed_coil_end_turn','copper_slot','grille_spoke','fan_blade')) for o in objects)
assert next(o for o in objects if o.name.startswith('rotor_unit')).get('spinAxis')=='x'
assert next(o for o in objects if o.name.startswith('cooling_fan')).get('spinAxis')=='x'
# Check each two-layer copper slot radius remains within the physical slot's .266..305 radial cavity.
for r in [.274+t*.0055 for t in range(3)]+[.291+t*.0055 for t in range(3)]:
    assert .266<r-.0022 and r+.0022<.305
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(QA/'motor-v2-preview.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.67,.73,.75,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.object.light_add(type='AREA',location=(2,-4,6));bpy.context.object.data.energy=750;bpy.context.object.data.size=4
bpy.ops.object.light_add(type='AREA',location=(-4,2,4));bpy.context.object.data.energy=550;bpy.context.object.data.size=3
bpy.ops.object.camera_add(location=(4.5,-6.1,3.6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.8;scene.camera=cam
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
scene.render.filepath=str(QA/'motor-v2-preview.png');bpy.ops.render.render(write_still=True)
# An exploded preview exposes the winding's physical slots and the perforated fan cover.
for obj in objects:
    if 'explode' in obj:
        v=obj['explode'];obj.location+=Vector((v[0],-v[2],v[1]))*.55
cam.location=(6.0,-8.7,5.1);cam.rotation_euler=(Vector((.65,0,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=10.5
scene.render.filepath=str(QA/'motor-v2-exploded-preview.png');bpy.ops.render.render(write_still=True)
(QA/'motor-v2-precision-check.json').write_text(json.dumps({'coils':len(coils),'visibleCutawayTeeth':len(teeth),'curvedBlades':len(blades),'objects':len(objects),'result':'pass','previewGLB':'qa/motor-v2-preview.glb'},indent=2))
print('MOTOR_PRECISION_CHECK_PASS',len(objects),flush=True)
