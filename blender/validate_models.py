"""Validate exported artifact contracts and research-review corrections (stdlib only)."""
import json,struct,hashlib
from pathlib import Path
base=Path(__file__).resolve().parents[1]
ids='opening carding drawing combing roving spinning winding warping sizing drawing_in weaving pretreatment dyeing stenter calender inspection motor'.split()
report={'status':'passed','models':[]}
for stage in ids:
    path=base/'dist/assets/models'/f'{stage}.glb';b=path.read_bytes()
    magic,version,size=struct.unpack_from('<III',b)
    assert magic==0x46546c67 and version==2 and size==len(b),(stage,'header')
    length,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a
    data=json.loads(b[20:20+length]);nodes=data['nodes'];roots=[n for n in nodes if n['name']=='stage_'+stage]
    assert len(roots)==1,(stage,'stage root')
    assert roots[0].get('extras',{}).get('modelVersion')=='2.0',(stage,'industrial v2 version')
    assert roots[0].get('translation',[0,0,0])==[0,0,0],(stage,'root origin')
    assert all('uri' not in buffer for buffer in data.get('buffers',[])),(stage,'external dependency')
    meshes=[n for n in nodes if 'mesh' in n]
    assert all(n.get('extras',{}).get('label') and n.get('extras',{}).get('group') for n in meshes),(stage,'clickable metadata')
    motors=[n for n in nodes if n.get('extras',{}).get('group')=='motor'];assert len(motors)>50,(stage,'motor components')
    animated=[n for n in nodes if n.get('extras',{}).get('spinAxis')];assert len(animated)>=2,(stage,'drive animation')
    assert all(n['extras']['spinAxis'] in ('x','y','z') for n in animated)
    explode=[n for n in nodes if 'explode' in n.get('extras',{})];assert len(explode)>0,(stage,'exploded view')
    names=[n['name'] for n in nodes]
    if stage=='sizing':
        assert sum(n.startswith('sizing_warp_sheet') for n in names)>=24
        assert sum(n.startswith('rotate_烘干筒') for n in names)>=4
        assert not any(n.startswith('fabric_web') for n in names),'Sizing must display yarn sheet, not woven cloth'
    if stage=='roving':
        assert not any(n.startswith('feed_bobbin') for n in names),'Roving must be fed by sliver cans'
        assert sum(n.startswith('sliver_can') for n in names)==sum(n.startswith('rotate_flyer') for n in names)>=12
    if stage=='weaving':
        assert sum(n.startswith('warp_shed_upper') for n in names)>=16
        assert sum(n.startswith('warp_shed_lower') for n in names)>=16
        assert sum(n.startswith('drive_pulley') for n in names)>=2
        assert any(n.startswith('drive_belt') for n in names)
    if stage=='dyeing':assert any(n.startswith('after_wash_bath') for n in names)
    if stage=='motor':
        for prefix in ('stator_housing','distributed_double_layer_coil','stator_tooth','rotor_end_ring','rotor_core','output_shaft','bearing_ball','end_shield','curved_cooling_fan_blade','fan_cover_sheet_wall','terminal_bridge','motor_mounting_foot'):
            assert any(n.startswith(prefix) for n in names),(stage,'missing '+prefix)
        assert len(explode)>=10
        assert sum(n.startswith('distributed_double_layer_coil') for n in names)==72
        assert sum(n.startswith('curved_cooling_fan_blade') for n in names)==9
    if stage=='opening':assert any(n.startswith('cantilever_plucking_head') for n in names) and any(n.startswith('long_travel_rail') for n in names)
    if stage=='stenter':assert any(n.startswith('stenter_below_web_slot') for n in names) and any(n.startswith('stenter_above_web_slot') for n in names)
    if stage=='spinning':assert sum(n.startswith('ring_traveller') for n in names)==sum(n.startswith('spindle_cop') for n in names)>=24
    triangles=sum(data['accessors'][p['indices']]['count']//3 for m in data['meshes'] for p in m['primitives'] if 'indices' in p)
    report['models'].append({'id':stage,'bytes':len(b),'nodes':len(nodes),'uniqueMeshTriangles':triangles,'meshObjects':len(meshes),'uniqueMeshes':len(data['meshes']),'sharedGeometryInstances':roots[0]['extras'].get('sharedGeometryInstances',0),'motorNodes':len(motors),'animatedGroups':len(animated),'explodeGroups':len(explode),'sha256':hashlib.sha256(b).hexdigest()})
for name in ['textile-machinery.blend','motor-detail.blend']:
    p=base/'blender'/name
    assert p.stat().st_size>50000
    assert p.read_bytes()[:7]==b'BLENDER' or p.read_bytes()[:4]==bytes.fromhex('28b52ffd'), 'Expected Blender binary or zstd-compressed Blender file'
report['totalBytes']=sum(m['bytes'] for m in report['models'])
assert report['totalBytes']<60_000_000,'Model payload exceeds 60 MB target'
report['sourceFiles']=['blender/textile-machinery.blend','blender/motor-detail.blend','blender/build_models.py','blender/industrial_v2.py','blender/motor_precision.py']
(base/'qa/model-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
