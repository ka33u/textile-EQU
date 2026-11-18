"""Assemble editable current public-reference source models; never writes dist.
Run only after all 16 v3-source/*.blend files have passed candidate review:
  Blender --background --factory-startup --python blender/assemble_current_v3.py
Optional -- --render saves one overall overview, not individual machine renders.
The motor stays the existing generic motor source; it is not relabelled v3/OEM.
"""
from pathlib import Path
import bpy, math, json, sys, time
from mathutils import Vector

BASE=Path(__file__).resolve().parents[1]
BLEND=BASE/'blender';QA=BASE/'qa'
BRANCHES_V5='--branches-v5' in sys.argv
DRIVE_V4='--drive-v4' in sys.argv or BRANCHES_V5
STAGES=[
 ('opening','开清棉'),('carding','梳棉'),('drawing','并条'),('combing','精梳'),
 ('roving','粗纱'),('spinning','细纱'),('winding','络筒'),('warping','整经'),
 ('sizing','浆纱'),('drawing_in','穿经'),('weaving','机织'),('pretreatment','前处理'),
 ('dyeing','染色'),('stenter','拉幅定形'),('calender','轧光'),('inspection','验布'),
 ('motor','通用三相异步电机结构')]
if DRIVE_V4:STAGES=[entry for entry in STAGES if entry[0]!='motor']
if BRANCHES_V5:STAGES.extend([('compact_spinning','紧密纺'),('twisting','倍捻'),('texturing','加弹')])
SOURCES={sid:(BLEND/'motor-detail.blend' if sid=='motor' else BLEND/('v4-source' if DRIVE_V4 else 'v3-source')/f'{sid}.blend') for sid,_ in STAGES}
if BRANCHES_V5:
 for sid in ['compact_spinning','twisting','texturing']:SOURCES[sid]=BLEND/'v5-source'/f'{sid}.blend'
missing=[str(p) for p in SOURCES.values() if not p.exists()]
if missing:raise FileNotFoundError('Source files missing; no assembly saved:\n'+'\n'.join(missing))

# Build in a fresh scene; every loaded machine belongs to exactly its own collection.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for col in list(bpy.data.collections):
 if col.users==0 or col.name=='Collection':bpy.data.collections.remove(col)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS';scene.unit_settings.scale_length=1.0
scene['assemblyVersion']='5.0' if BRANCHES_V5 else '4.0' if DRIVE_V4 else '3.0'
scene['sourceNote']='16台公开参考配置，电机外观与驱动工位 v4；不是OEM CAD/BOM。' if DRIVE_V4 else '16台公开参考配置 v3 + 既有通用电机；不是OEM CAD/BOM，不宣称完整隐藏结构。'
if BRANCHES_V5:scene['sourceNote']='棉纺机织染整主线与紧密纺/倍捻/加弹独立分支19台；不是单一串联生产线，非OEM CAD。'
scene['structuralCompleteness']=False
scene['motorReferenceNote']='电机仅显示外观，位置及配套型号待核实；不展示内部解剖。' if DRIVE_V4 else '电机保持既有通用教学结构与原始元数据；不升级为某厂家现款。'

# Source model files are appended, not linked: all geometry remains editable locally.
def append_root_graph(sid,path,number,title):
 started=time.perf_counter();before=set(bpy.data.objects)
 print('APPEND_PHASE',sid,'loading source collections',flush=True)
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):
  # Appending whole collections preserves their memberships in native code.
  # Avoid Object.users_collection here: its Python implementation copies/scans
  # every collection's object list for each object, becoming quadratic at 25k+.
  collection_names=list(src.collections)
  if collection_names:dst.collections=collection_names
  else:dst.objects=list(src.objects)
 loaded=set(bpy.data.objects)-before
 imported_collections=[c for c in dst.collections if c is not None] if collection_names else []
 loaded_at=time.perf_counter()
 roots=[o for o in loaded if o.get('stage')==sid and o.parent is None]
 if not roots:roots=[o for o in loaded if o.name.split('.')[0]=='stage_'+sid]
 if len(roots)!=1:raise RuntimeError(f'{sid}: expected exactly one stage root, got {len(roots)}')
 root=roots[0]
 children={}
 for o in loaded:
  if o.parent is not None:children.setdefault(o.parent,[]).append(o)
 descendants=set();stack=[root]
 while stack:
  o=stack.pop()
  if o in descendants:continue
  descendants.add(o);stack.extend(children.get(o,()))
 # In particular motor imports only stage_motor + descendants. Camera and lamp objects
 # are neither linked nor retained, even if their source names differed from known names.
 kept={o for o in descendants if o.type not in {'CAMERA','LIGHT'}}
 if any(o.parent not in kept for o in kept if o!=root):raise RuntimeError(f'{sid}: incomplete source hierarchy')
 if not kept.issubset(loaded):raise RuntimeError(f'{sid}: source graph references existing equipment')
 mesh_count=sum(o.type=='MESH' for o in kept)
 extras=loaded-kept
 if extras:bpy.data.batch_remove(ids=extras)
 col=bpy.data.collections.new(f'{number:02d} · {title} · {sid}')
 col['stage']=sid;col['sourceFile']=str(path.relative_to(BASE));col['structuralCompleteness']=False
 if imported_collections:
  # Link only source hierarchy roots, retaining nested collection organisation.
  nested={child for parent in imported_collections for child in parent.children}
  for imported in imported_collections:
   if imported not in nested:col.children.link(imported)
 else:
  # Legacy files without a collection: populate a detached collection, then
  # attach it to the scene once. No per-object membership query is required.
  for o in kept:col.objects.link(o)
 members=set(col.all_objects)
 if members!=kept:raise RuntimeError(f'{sid}: collection membership differs from complete source graph ({len(members)} vs {len(kept)})')
 if members & before:raise RuntimeError(f'{sid}: collection contains another equipment asset')
 if sum(o.type=='MESH' for o in members)!=mesh_count:raise RuntimeError(f'{sid}: mesh object lost during collection append')
 if any(o.library is not None for o in kept):raise RuntimeError(f'{sid}: object remained library-linked instead of editable')
 scene.collection.children.link(col)
 linked_at=time.perf_counter()
 root.location=(0,0,0)
 # Root transforms other than location are preserved; source internal coordinates are not normalized.
 bpy.context.view_layer.update()
 pts=[o.matrix_world@Vector(c) for o in kept if o.type=='MESH' for c in o.bound_box]
 if not pts:raise RuntimeError(f'{sid}: no mesh bounds')
 lo=Vector(tuple(min(p[k] for p in pts) for k in range(3)))
 hi=Vector(tuple(max(p[k] for p in pts) for k in range(3)))
 if sid!='motor' and root.get('modelVersion')!='3.0':raise RuntimeError(f'{sid}: source is not v3')
 root['assemblySource']=str(path.relative_to(BASE))
 elapsed={'loadSeconds':loaded_at-started,'graphAndLinkSeconds':linked_at-loaded_at,'updateAndBoundsSeconds':time.perf_counter()-linked_at}
 print('APPEND_TIMINGS',sid,json.dumps(elapsed),flush=True)
 return {'id':sid,'title':title,'root':root,'collection':col,'lo':lo,'hi':hi,'size':hi-lo,'objects':len(kept),'kept':tuple(kept),'meshObjects':mesh_count,'appendTimings':elapsed}

entries=[]
for number,(sid,title) in enumerate(STAGES,1):
 entry=append_root_graph(sid,SOURCES[sid],number,title);entries.append(entry)
 print('APPENDED_EDITABLE',sid,entry['objects'],list(entry['size']),flush=True)

# Column and row dimensions come from actual bounds, keeping every machine in metres.
# No stage is rescaled to match another. Aisles are added around full model envelopes.
columns=4;rows=math.ceil(len(entries)/columns);aisle=3.0
column_widths=[max((e['size'].x for i,e in enumerate(entries) if i%columns==c),default=0) for c in range(columns)]
row_depths=[max((e['size'].y for i,e in enumerate(entries) if i//columns==r),default=0) for r in range(rows)]
col_x=[sum(column_widths[:c])+aisle*c for c in range(columns)]
row_y=[sum(row_depths[:r])+aisle*r for r in range(rows)]
for i,e in enumerate(entries):
 c=i%columns;r=i//columns
 # Center within its cell and put the actual lowest point on the common Z=0 floor.
 x=col_x[c]+(column_widths[c]-e['size'].x)/2-e['lo'].x
 y=row_y[r]+(row_depths[r]-e['size'].y)/2-e['lo'].y
 e['root'].location=(x,y,-e['lo'].z)
 e['collection']['gridColumn']=c;e['collection']['gridRow']=r
 e['root']['assemblyGridColumn']=c;e['root']['assemblyGridRow']=r
bpy.context.view_layer.update()
points=[o.matrix_world@Vector(c) for e in entries for o in e['kept'] if o.type=='MESH' for c in o.bound_box]
lo=Vector(tuple(min(p[k] for p in points) for k in range(3)))
hi=Vector(tuple(max(p[k] for p in points) for k in range(3)));center=(lo+hi)/2
extent=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)

# Camera and lights live in a separate presentation collection, not any equipment collection.
presentation=bpy.data.collections.new('00 · 总装相机与照明');scene.collection.children.link(presentation)
def link_presentation(obj):
 for col in list(obj.users_collection):col.objects.unlink(obj)
 presentation.objects.link(obj)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.73,.77,.82,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
for name,offset,power in [('总装主光',(.35,-.6,.9),1500),('总装补光',(-.6,.4,.8),1000)]:
 ld=bpy.data.lights.new(name,'AREA');ld.energy=power*max(extent/6,1)**2;ld.shape='DISK';ld.size=max(extent*.60,5)
 o=bpy.data.objects.new(name,ld);presentation.objects.link(o)
 o.location=center+Vector(offset)*max(extent,8);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('自适应总装正交相机');camera=bpy.data.objects.new('自适应总装正交相机',camdata);presentation.objects.link(camera)
direction=Vector((.72,-1.0,.95)).normalized()
camera.location=center+direction*max(extent*2.5,12)
camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
camdata.type='ORTHO';camdata.clip_start=.05;camdata.clip_end=max(extent*12,1000)
resolution=(2400,1600);aspect=resolution[0]/resolution[1]
q=camera.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0))
uv=[((p-center).dot(right),(p-center).dot(up)) for p in points]
minu=min(u for u,v in uv);maxu=max(u for u,v in uv);minv=min(v for u,v in uv);maxv=max(v for u,v in uv)
camera.location+=right*((minu+maxu)/2)+up*((minv+maxv)/2)
camdata.ortho_scale=max(maxu-minu,(maxv-minv)*aspect)*1.12
scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=resolution;scene.render.resolution_percentage=100
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.view_settings.view_transform='AgX'
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL'
   area.spaces.active.region_3d.view_location=center
   area.spaces.active.region_3d.view_distance=max(extent*1.3,10)
   area.spaces.active.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
   area.spaces.active.clip_end=max(extent*12,1000)
bpy.ops.object.select_all(action='DESELECT')
entries[10]['root'].select_set(True);bpy.context.view_layer.objects.active=entries[10]['root']
QA.mkdir(exist_ok=True)
out=BLEND/('textile-machinery-v5.blend' if BRANCHES_V5 else 'textile-machinery-v4.blend' if DRIVE_V4 else 'textile-machinery-v3.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'assemblyFile':str(out.relative_to(BASE)),'modelVersion':'3.0','structuralCompleteness':False,'units':'metres','allEditable':True,'sourceStageCount':16,'genericMotorCount':1,'equipmentCollections':len(entries),'bounds':{'min':list(lo),'max':list(hi)},'grid':{'columns':columns,'rows':rows,'aisleM':aisle,'columnWidthsM':column_widths,'rowDepthsM':row_depths},'items':[{'id':e['id'],'source':str(SOURCES[e['id']].relative_to(BASE)),'collection':e['collection'].name,'objectCount':e['objects'],'boundsSizeM':list(e['size']),'assemblyLocation':list(e['root'].location),'referenceModel':e['root'].get('referenceModel'),'modelVersion':e['root'].get('modelVersion')} for e in entries]}
if DRIVE_V4:report.update(assemblyVersion='4.0',genericMotorCount=0,motorDetailScope='external_only')
if BRANCHES_V5:report.update(assemblyVersion='5.0',sourceStageCount=19,routeScope='16 main-route stages plus 3 independent or alternative branches')
(QA/('v5-assembly-report.json' if BRANCHES_V5 else 'v4-assembly-report.json' if DRIVE_V4 else 'v3-assembly-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('ASSEMBLY_SAVED',str(out),flush=True)
if '--render' in sys.argv:
 scene.render.filepath=str(QA/('v5-equipment-gallery.png' if BRANCHES_V5 else 'v4-equipment-gallery.png' if DRIVE_V4 else 'v3-equipment-gallery.png'));bpy.ops.render.render(write_still=True)
 print('ASSEMBLY_OVERVIEW_RENDERED',scene.render.filepath,flush=True)
