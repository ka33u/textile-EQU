from pathlib import Path
import bpy,math
from mathutils import Vector
source=Path(__file__).with_name('build_models.py');exec(compile(source.read_text().split('builders=[')[0],str(source),'exec'))
r=machine_calender();bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(OUT/'calender.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40;scene.render.resolution_x=1700;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.8,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for loc,energy,size in [((2,-4,8),1800,7),((-5,2,6),1500,6)]:
    bpy.ops.object.light_add(type='AREA',location=loc);bpy.context.object.data.energy=energy;bpy.context.object.data.size=size;bpy.context.object.rotation_euler=(Vector((0,0,1.4))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(8,-10,6));cam=bpy.context.object;cam.rotation_euler=(Vector((-.35,0,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=10.6;scene.camera=cam
scene.view_settings.view_transform='AgX';scene.render.filepath=str(QA/'calender-v2-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND/'calender-v2-preview.blend'));bpy.ops.render.render(write_still=True)
print('CALENDER_V2_PREVIEW_READY',len(r.children_recursive),flush=True)
