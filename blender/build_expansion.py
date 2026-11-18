"""Export one current-reference machine and its editable assembly.

Blender -b --factory-startup --python-exit-code 1 --python blender/build_expansion.py -- <equipment_id>
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

source_dir = Path(__file__).resolve().parent
library_file = source_dir / 'build_models.py'
exec(compile(library_file.read_text().split('builders=[')[0], str(library_file), 'exec'))
library_file = source_dir / 'current_extensions_v5.py'
exec(compile(library_file.read_text(), str(library_file), 'exec'))
B, C, T, P, E = _s3_box, _s3_cyl, _s3_torus, _s3_pipe, empty


def load(parent, id, label, loc, motion=None, speed=1.0, amplitude=0.0):
    node = empty(id, loc, parent, label, 'roller')
    node['driveAnchorId'] = id
    if motion:
        kind, axis = motion.split(':')
        if kind not in ('rotate', 'translate', 'oscillate') or axis not in ('x', 'y', 'z'):
            raise ValueError(f'Unsupported motion {motion} for {id}')
        node['stationMotion'] = motion
        node['motionSpeed'] = float(speed)
        node['motionAmplitude'] = float(amplitude)
        if kind == 'rotate':
            node['spinAxis'] = axis
            node['spinSpeed'] = float(speed)
    return node


def motor(parent, id, label, loc, axis='x', radius=.10, length=.26, style='industrial'):
    """Model the visible housing, mount, connections and output. The axis is Blender-local."""
    facing = {'x':(0,0,0), '-x':(0,0,math.pi), 'y':(0,0,math.pi/2),
              '-y':(0,0,-math.pi/2), 'z':(0,-math.pi/2,0), '-z':(0,math.pi/2,0)}
    node = empty(id, loc, parent, label, 'motor')
    node.rotation_euler = facing[axis.lstrip('+')]
    for field, value in dict(driveAnchorId=id, driveRole='motor', motorDetailScope='external_only',
                             internalGeometryModeled=False, motorLayoutEvidence='inferred_functional_layout').items():
        node[field] = value
    r, l = radius, length
    cartridge = style == 'cartridge'
    square = style in ('servo','gear')
    color = 'dark' if cartridge or style == 'servo' else 'teal'
    if style == 'servo':
        B(node, 'servo_body', (0,0,0), (l,1.79*r,1.79*r), color, '方形电机壳体', 'motor', r*.16)
    else:
        C(node, 'drive_case', (0,0,0), r,l,color,'x','电机机壳','motor',36)
    fin_count = 8 if cartridge or square else 14
    for j in range(fin_count):
        angle=math.tau*j/fin_count
        fin=B(node,'case_rib',(0,.98*r*math.cos(angle),.98*r*math.sin(angle)),
              (.72*l,.17*r,.105*r),color,'机壳纵筋','motor',.015*r)
        fin.rotation_euler.x=angle
    C(node,'rear_cover',(-.49*l,0,0),1.035*r,l*.14,color,'x','电机后端罩','motor',40)
    C(node,'rear_lip',(-.565*l,0,0),.91*r,l*.03,'steel','x','后罩边缘','motor',36)
    if square:
        B(node,'flange_plate',(.47*l,0,0),(.13*l,2.06*r,2.06*r),'steel','安装法兰','motor',.09*r)
    else:
        C(node,'flange_face',(.485*l,0,0),1.12*r,.12*l,'steel','x','安装法兰','motor',40)
    for angle in [math.pi/4+i*math.pi/2 for i in range(4)]:
        y=.87*r*math.cos(angle); z=.87*r*math.sin(angle)
        C(node,'flange_fastener',(.555*l,y,z),.093*r,.057*l,'steel','x','法兰紧固螺栓','motor',6)
    if not cartridge:
        B(node,'cable_box',(-.14*l,0,1.03*r),(.36*l,.84*r,.43*r),color,'电机接线盒','motor',.055*r)
        B(node,'cable_lid',(-.14*l,0,1.25*r),(.375*l,.90*r,.055*r),'dark','接线盒盖','motor',.02*r)
        C(node,'cable_gland',(-.14*l,-.49*r,1.05*r),.12*r,.18*r,'dark','y','电缆密封接头','motor',12)
        if style!='servo':
            for side in [-1,1]:
                B(node,'mounting_foot',(0,.70*r*side,-.86*r),(.72*l,.38*r,.25*r),color,'安装底脚','motor',.035*r)
    else:
        C(node,'plug',(-.30*l,0,r),.18*r,.37*r,'black','z','电机插头','motor',16)
    C(node,'flange_register',(.56*l,0,0),.56*r,.10*l,'steel','x','定位止口','motor',32)
    shaft=load(node,id+'_out','外伸输出轴',(.65*l,0,0),'rotate:x',1.8)
    shaft['motorDetailRole']='shaft'
    C(shaft,'output_stub',(0,0,0),.255*r,.22*l,'steel','x','输出轴端','motor',28)
    B(shaft,'shaft_key',(0,0,.244*r),(.16*l,.091*r,.054*r),'dark','外伸轴键','motor',.008*r)
    return node


if '--' not in sys.argv or len(sys.argv[sys.argv.index('--')+1:])!=1:
    raise SystemExit('Pass one equipment ID after --')
equipment_id=sys.argv[-1]
families={'yarn':('assembly_winding','airjet_spinning'), 'preparation':('warp_tying','singeing'),
          'wet':('washing_range','mercerizing','sanforizing')}
family=next(k for k,ids in families.items() if equipment_id in ids)
reference_file=BASE/'research'/('expansion-'+family+'.json')
reference=next(row for row in json.loads(reference_file.read_text()) if row['id']==equipment_id)
equipment_file=source_dir/('expansion_'+family+'.py')
exec(compile(equipment_file.read_text(),str(equipment_file),'exec'))
root=e5_root(equipment_id,reference['equipment'],reference['maker'],reference['model'],
             reference['configuration'],reference['sources'][0]['url'])
root['driveRevision']='7.0'
root['stationDriveModel']=True
root['actualScope']='工位与传动的资料依据分别列在路线详情中。电机外观及安装尺寸按公开外形和工位功能重建。'
BUILDERS[equipment_id](root)
_s3_finish(root)
nodes=[root,*root.children_recursive]
anchor_ids=[n['driveAnchorId'] for n in nodes if n.get('driveAnchorId')]
assert len(anchor_ids)==len(set(anchor_ids)), 'Duplicate anchors for '+equipment_id
assert any(n.type=='MESH' for n in nodes)
root['modeledMotorCount']=sum(n.get('driveRole')=='motor' for n in nodes)
bpy.ops.object.select_all(action='DESELECT')
for obj in nodes:obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(source_dir/(equipment_id+'.blend')),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/(equipment_id+'.glb')),export_format='GLB',use_selection=True,
                          export_extras=True,export_yup=True,export_apply=True,export_animations=False)
print('EXPORTED',equipment_id,len(nodes),len(anchor_ids),root['modeledMotorCount'],flush=True)
