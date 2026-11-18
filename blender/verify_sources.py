"""Open both delivered .blend files and inspect actual saved scene contents."""
import bpy,json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
expected=set('opening carding drawing combing roving spinning winding warping sizing drawing_in weaving pretreatment dyeing stenter calender inspection motor'.split())
results=[]
for filename,stages in [('textile-machinery.blend',expected),('motor-detail.blend',{'motor'})]:
    bpy.ops.wm.open_mainfile(filepath=str(base/'blender'/filename))
    roots=[o for o in bpy.data.objects if o.name.startswith('stage_')]
    assert {o['stage'] for o in roots}==stages,(filename,'stage inventory')
    assert bpy.context.scene.camera is not None
    assert all(o.type=='MESH' for root in roots for o in root.children_recursive if o.type!='EMPTY')
    results.append({'file':filename,'verifiedBy':'Blender reopen','stages':sorted(stages),'objects':len(bpy.data.objects),'meshObjects':sum(o.type=='MESH' for o in bpy.data.objects),'materials':len(bpy.data.materials)})
(base/'qa/source-validation.json').write_text(json.dumps({'status':'passed','sources':results},ensure_ascii=False,indent=2))
print('SOURCE_VALIDATION_PASSED',json.dumps(results,ensure_ascii=False))
