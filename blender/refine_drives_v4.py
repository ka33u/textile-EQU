"""Exterior-only drive refinement of saved v3 equipment.

Run Blender --background --factory-startup --python blender/refine_drives_v4.py
  -- <stage...> [--preview]
No OEM motor identity is implied. Existing station anchors, selected equipment
quantities, loads and transmission geometry are preserved. This module can also
be imported by motor_precision.py to construct exterior-only generic motors.
"""
from pathlib import Path
import bpy, bmesh, math, json, sys, hashlib, struct
from mathutils import Vector, Matrix

BASE = Path(__file__).resolve().parents[1]
STAGES = ['opening','carding','drawing','combing','roving','spinning','winding','warping','sizing','drawing_in','weaving','pretreatment','dyeing','stenter','calender','inspection']
_CACHE = {}
_MATERIALS = {}

def _material(key):
    if key in _MATERIALS and _MATERIALS[key].name in bpy.data.materials:
        return _MATERIALS[key]
    specs = {'paint': ((.045,.115,.135),.45,.34),
             'steel': ((.49,.55,.57),.78,.30),
             'dark': ((.026,.034,.038),.35,.43),
             'rubber': ((.013,.018,.021),0,.66),
             'orange': ((.77,.27,.045),.35,.39)}
    col,metal,rough = specs[key]
    m=bpy.data.materials.new('V4 exterior '+key);m.diffuse_color=(*col,1);m.use_nodes=True
    shader=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value=(*col,1)
    shader.inputs['Metallic'].default_value=metal;shader.inputs['Roughness'].default_value=rough
    _MATERIALS[key]=m
    return m

class Parts:
    """Batched primitive surfaces; separate round walls and flat end normals."""
    def __init__(self): self.v=[];self.f=[];self.s=[]
    def append(self,vertices,faces,smooth=False,matrix=None):
        n=len(self.v)
        self.v.extend(tuple(matrix@Vector(v)) if matrix else tuple(v) for v in vertices)
        self.f.extend(tuple(n+i for i in face) for face in faces)
        self.s.extend(smooth if isinstance(smooth,list) else [smooth]*len(faces))
    def box(self,loc,size,bevel=0,rotation=None):
        bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
        for v in bm.verts:v.co=Vector(tuple(v.co[i]*size[i] for i in range(3)))
        if bevel:
            bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(size)*.23),segments=2,affect='EDGES')
        bm.verts.ensure_lookup_table();bm.verts.index_update()
        mat=Matrix.Translation(Vector(loc))
        if rotation:mat=mat@rotation.to_4x4()
        self.append([v.co[:] for v in bm.verts],[[v.index for v in f.verts] for f in bm.faces],False,mat)
        bm.free()
    def lathe(self,profile,loc=(0,0,0),n=48,a0=0,a1=2*math.pi,axis='x'):
        # Profile traverses a closed axial/radial section; all surfaces have finite thickness.
        v=[];f=[];sm=[];segments=n+1
        for x,r in profile:
            v.extend((x,r*math.cos(a0+(a1-a0)*j/n),r*math.sin(a0+(a1-a0)*j/n)) for j in range(segments))
        for i in range(len(profile)):
            k=(i+1)%len(profile)
            for j in range(n):
                f.append((i*segments+j,i*segments+j+1,k*segments+j+1,k*segments+j))
                sm.append(abs(profile[i][0]-profile[k][0])>1e-9)
        if a1-a0<2*math.pi-1e-7:
            f.extend([tuple(i*segments for i in range(len(profile)-1,-1,-1)),tuple(i*segments+n for i in range(len(profile)))])
            sm.extend([False,False])
        mat=Matrix.Translation(Vector(loc))
        if axis=='y':mat=mat@Matrix.Rotation(math.pi/2,4,'Z')
        elif axis=='z':mat=mat@Matrix.Rotation(-math.pi/2,4,'Y')
        self.append(v,f,sm,mat)
    def cyl(self,loc,r,length,n=48,axis='x',chamfer=0):
        c=min(chamfer,length*.2,r*.2);a=-length/2;b=length/2
        profile=[(a,0),(a,max(0,r-c)),(a+c,r),(b-c,r),(b,max(0,r-c)),(b,0)] if c else [(a,0),(a,r),(b,r),(b,0)]
        self.lathe(profile,loc,n,axis=axis)
    def ring(self,x1,x2,r1,r2,loc=(0,0,0),n=48,a0=0,a1=2*math.pi,axis='x'):
        self.lathe([(x1,r1),(x1,r2),(x2,r2),(x2,r1)],loc,n,a0,a1,axis)
    def mesh(self,name,material):
        me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
        for p,s in zip(me.polygons,self.s):p.use_smooth=s
        me.materials.append(_material(material));return me

def _bolt(parts,loc,r,length,axis='x'):
    parts.cyl(loc,r*1.25,length*.30,n=24,axis=axis)
    offset=Vector(loc);offset[{'x':0,'y':1,'z':2}[axis]]+=length*.35
    parts.cyl(offset,r,length*.65,n=6,axis=axis,chamfer=r*.08)

def exterior_meshes(style,size,shaft_end=None,foot_bottom=None,generic=False):
    """One shared mesh per semantic exterior component, 8 parts per drive."""
    w,d,h=(float(q) for q in size)
    key=(style,tuple(round(q,6) for q in size),None if shaft_end is None else round(shaft_end,6),None if foot_bottom is None else round(foot_bottom,6),generic)
    if key in _CACHE and all(me.name in bpy.data.meshes for _,me,_,_ in _CACHE[key]):return _CACHE[key]
    housing=Parts();end=Parts();fan=Parts();terminal=Parts();bolts=Parts();rubber=Parts();shaft=Parts();coupling=Parts();mount=Parts()
    r=h*.5
    if style=='servo':
        housing.box((0,0,0),(w*.88,d*.94,h*.94),min(w,d,h)*.06)
        # Shallow extruded cooling ribs and a machined square mounting flange.
        for side in (-1,1):
            for j in range(5):
                z=-h*.32+j*h*.16
                housing.box((0,side*d*.485,z),(w*.72,d*.045,h*.045),h*.006)
        mount.box((w*.465,0,0),(w*.075,d*1.08,h*1.08),min(d,h)*.045)
        end.cyl((w*.51,0,0),min(d,h)*.31,w*.035,chamfer=h*.012)
        fan.box((-w*.465,0,0),(w*.07,d*.90,h*.90),min(d,h)*.065)
        # Separate power/encoder connectors; no assumed internal electronics.
        for xx,rr in ((-w*.23,h*.085),(w*.12,h*.066)):
            terminal.cyl((xx,0,h*.51),rr,h*.12,n=24,axis='z',chamfer=rr*.1)
            bolts.cyl((xx,0,h*.58),rr*.88,h*.06,n=6,axis='z')
            rubber.cyl((xx,0,h*.64),rr*.66,h*.08,n=24,axis='z')
        for yy in (-d*.40,d*.40):
            for zz in (-h*.40,h*.40):_bolt(bolts,(w*.51,yy,zz),min(d,h)*.035,w*.04)
    else:
        housing.cyl((w*.025,0,0),r*.90,w*.76,chamfer=h*.025)
        for j in range(24):
            a=j*2*math.pi/24
            if foot_bottom is not None and math.sin(a)<-.80:continue
            housing.box((w*.025,r*1.01*math.cos(a),r*1.01*math.sin(a)),(w*.70,h*.024,h*.13),h*.004,Matrix.Rotation(a-math.pi/2,3,'X'))
        for sign in (-1,1):
            xx=w*(.42 if sign>0 else -.36)
            end.cyl((xx,0,0),r*.96,w*.085,chamfer=h*.024)
            if sign>0:
                end.cyl((w*.48,0,0),r*.65,w*.08,chamfer=h*.024)
                end.cyl((w*.525,0,0),r*.29,w*.025,chamfer=h*.012)
            for j in range(8):
                a=(j+.5)*math.pi/4
                end.box((xx+sign*w*.045,r*.67*math.cos(a),r*.67*math.sin(a)),(w*.035,h*.035,h*.24),h*.005,Matrix.Rotation(a-math.pi/2,3,'X'))
            for j in range(4):
                a=math.pi/4+j*math.pi/2
                _bolt(bolts,(xx+sign*w*.053,r*.79*math.cos(a),r*.79*math.sin(a)),h*.035,w*.035)
        # A thin hood with genuine open rear slots, not an opaque disk with painted lines.
        fan.ring(-w*.50,-w*.345,r*.935,r*.98)
        for a,b in ((0,.22),(.29,.42),(.49,.62),(.69,.82),(.89,.98)):
            fan.ring(-w*.506,-w*.485,r*a,r*b)
        for j in range(12):
            aa=j*math.pi/6
            fan.ring(-w*.506,-w*.485,r*.18,r*.965,n=2,a0=aa-.023,a1=aa+.023)
        for j in range(3):
            a=j*2*math.pi/3
            _bolt(bolts,(-w*.512,r*.87*math.cos(a),r*.87*math.sin(a)),h*.024,w*.026)
        terminal.box((-w*.04,0,h*.625),(w*.42,d*.49,h*.23),h*.025)
        terminal.box((-w*.04,0,h*.757),(w*.45,d*.53,h*.042),h*.012)
        rubber.box((-w*.04,0,h*.730),(w*.435,d*.515,h*.012),h*.004)
        for xx in (-w*.205,w*.125):
            for yy in (-d*.19,d*.19):_bolt(bolts,(xx,yy,h*.789),h*.024,h*.025,'z')
        # Gland ends at an inlet stub; no invented external cable routing.
        terminal.cyl((-w*.04,-d*.29,h*.625),h*.07,d*.12,n=24,axis='y')
        bolts.cyl((-w*.04,-d*.35,h*.625),h*.072,d*.05,n=6,axis='y')
        rubber.cyl((-w*.04,-d*.40,h*.625),h*.047,d*.08,n=24,axis='y')
        end.box((w*.02,-r*.94,h*.14),(w*.36,h*.016,h*.19),h*.008)
        if foot_bottom is not None:
            t=h*.105
            for yy in (-d*.32,d*.32):
                mount.box((0,yy,foot_bottom+t/2),(w*.82,d*.22,t),h*.018)
                mount.box((0,yy*.88,(foot_bottom+t-h*.24)/2),(w*.56,d*.13,max(h*.08,-h*.24-foot_bottom-t)),h*.012)
                for xx in (-w*.29,w*.29):_bolt(bolts,(xx,yy,foot_bottom+t+h*.02),h*.045,h*.05,'z')
    if shaft_end is not None and shaft_end>w*.51:
        start=w*.49;rr=min(d,h)*.10
        shaft.cyl(((start+shaft_end)/2,0,0),rr,shaft_end-start,chamfer=rr*.10)
        if shaft_end-start>rr*2:
            shaft.box(((start+shaft_end)/2,0,rr),((shaft_end-start)*.55,rr*.50,rr*.24),rr*.05)
        if generic:
            # Exact former generic coupling envelope; its counterpart outside the motor stays untouched.
            for xx,rr,ll in ((.97,.15,.14),(1.15,.15,.13)):coupling.cyl((xx,0,0),rr,ll,chamfer=.008)
            rubber.cyl((1.065,0,0),.14,.055)
            for j in range(6):
                a=j*math.pi/3
                _bolt(bolts,(1.22,.108*math.cos(a),.108*math.sin(a)),.018,.025)
    items=[('housing_and_fins',housing,'paint','机壳与轴向散热筋'),('end_shields',end,'steel','端盖法兰与机壳铭牌座'),('ventilated_fan_cover',fan,'dark','有开孔的风罩或编码器端罩'),('terminal_and_gland',terminal,'paint','接线盒与电缆入口'),('fasteners',bolts,'steel','外部紧固件'),('gaskets',rubber,'rubber','密封垫与电缆入口套'),('mounting_feet_flange',mount,'steel','安装底脚或端面安装法兰'),('output_shaft',shaft,'steel','外伸输出轴与平键'),('external_coupling',coupling,'orange','原接口弹性联轴器外形')]
    result=[(name,part.mesh('v4_'+name,ma),label,name in ('output_shaft','external_coupling')) for name,part,ma,label in items if part.f]
    _CACHE[key]=result;return result

def add_exterior(anchor,style,size,shaft_end=None,foot_bottom=None,generic=False,rotation=None):
    for name,me,label,spin in exterior_meshes(style,size,shaft_end,foot_bottom,generic):
        o=bpy.data.objects.new('v4_'+name,me);bpy.context.collection.objects.link(o);o.parent=anchor
        if rotation:o.rotation_euler=rotation.to_euler()
        o['label']=label;o['group']='motor';o['exteriorPart']=True
        o['motorDetailRole']={'housing_and_fins':'housing','end_shields':'end_cover','ventilated_fan_cover':'encoder_cover' if style=='servo' else 'fan_guard','terminal_and_gland':'terminal_box','fasteners':'fastener','gaskets':'seal','mounting_feet_flange':'mount','output_shaft':'shaft','external_coupling':'coupling'}[name]
        o['description']='通用外观构件；不表示已核实的厂家电机型号或隐藏内部。'
        if name in ('housing_and_fins','end_shields','ventilated_fan_cover','terminal_and_gland'):o['shell']=True
        if spin:o['spinAxis']='x';o['spinSpeed']=.7
    anchor['driveRole']='motor';anchor['driveAnchorId']=anchor.name
    anchor['motorDetailScope']='external_only';anchor['driveRevision']='4.0'
    anchor['internalGeometryModeled']=False;anchor['oemMotorModelVerified']=False
    anchor['motorAppearanceEvidence']='generic_exterior_reference'
    anchor['motorLayoutEvidence']='inferred_existing_v3_layout'
    anchor['externalDetails']=list(dict.fromkeys(c['motorDetailRole'] for c in anchor.children if c.get('motorDetailRole')))

def create_generic_motor(parent,loc=(1.3,0,.8),scale=1,detail=False):
    """Drop-in exterior-only replacement for the previous generic motor()."""
    g=bpy.data.objects.new('motor_assembly',None);bpy.context.collection.objects.link(g);g.parent=parent;g.location=loc;g.scale=(scale,)*3
    g['label']='三相异步电动机';g['group']='motor';g['description']='外部构型示意；型号和布局未获厂家图纸核实。'
    add_exterior(g,'induction',(1.1,.86,.86),1.25,-.49,True)
    p=Parts();p.box((0,0,-.62),(1.12,.95,.26),.02)
    o=bpy.data.objects.new('motor_mounting_bracket',p.mesh('v4_mounting_bracket','steel'));bpy.context.collection.objects.link(o);o.parent=g;o['label']='电机安装托架';o['group']='frame'
    return g

def _known_motor(o):
    if o.type=='EMPTY':
        return o.name.startswith(('motor_assembly','f3_external_drive')) or any(c.name.startswith(('servo_body','industrial_drive_housing')) for c in o.children)
    return o.type=='MESH' and o.name.startswith(('X6_unit_motor','pressure_servo','feeder_motor','integrated_axis_motor'))

def _mesh_signature(me):
    h=hashlib.sha256()
    for v in me.vertices:h.update(struct.pack('<fff',*v.co))
    for p in me.polygons:
        h.update(struct.pack('<I?I',len(p.vertices),p.use_smooth,p.material_index));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    for mat in me.materials:h.update((mat.name if mat else '').encode())
    return h.hexdigest()

def _fingerprints(objects):
    meshes={};result={}
    for o in objects:
        item={'type':o.type,'parent':o.parent.name if o.parent else None,'matrixLocal':[v for row in o.matrix_local for v in row]}
        if o.type=='MESH':
            ptr=o.data.as_pointer()
            if ptr not in meshes:meshes[ptr]=_mesh_signature(o.data)
            item['mesh']=meshes[ptr]
        result[o.name]=item
    return result

def _settings(o):
    if o.name.startswith('motor_assembly'):return ('induction',(1.1,.86,.86),1.25,-.49,True,None)
    if o.name.startswith('f3_external_drive'):return ('induction',(.36,.28,.28),.33,-.175,False,None)
    child=next((c for c in o.children if c.name.startswith(('servo_body','industrial_drive_housing'))),None)
    if child:
        dims=tuple(float(v) for v in child.dimensions);servo=child.name.startswith('servo_body')
        return ('servo' if servo else 'induction',dims,dims[0]/2+.10,None if servo else -dims[2]/2-.03,False,None)
    dims=tuple(float(v) for v in o.dimensions)
    if o.name.startswith('pressure_servo'):
        return ('servo',(dims[1],dims[0],dims[2]),dims[1]*.55,None,False,Matrix.Rotation(-math.pi/2,3,'Z'))
    if o.name.startswith('integrated_axis_motor'):
        rot=Matrix.Rotation(math.pi,3,'Z') if o.location.x>0 else None
        return ('compact',dims,dims[0]/2+.06,None,False,rot)
    if o.name.startswith('feeder_motor'):return ('compact',dims,dims[0]/2+.015,None,False,None)
    # X6 motor location and output direction are not confirmed by a source drawing.
    # Keep this envelope without inventing a shaft to a displaced winding roller.
    return ('servo',dims,None,None,False,None)

def refine_stage(stage,preview=False):
    src=BASE/'blender/v3-source'/f'{stage}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(src));_CACHE.clear();_MATERIALS.clear()
    root=bpy.data.objects.get('stage_'+stage)
    if root is None:raise ValueError('Missing root '+stage)
    old_root_props={k:root[k] for k in root.keys()}
    anchors=sorted([o for o in root.children_recursive if _known_motor(o)],key=lambda o:o.name)
    # Old generic supporting bracket is not a motor exterior. Retain the exact object/mesh.
    retained={o for g in anchors for o in g.children_recursive if o.name.startswith('motor_mounting_bracket')}
    removed={o for g in anchors for o in g.children_recursive if o not in retained}
    leaf={o for o in anchors if o.type=='MESH'}
    before_count=len(root.children_recursive)
    untouched=[o for o in root.children_recursive if o not in removed and o not in leaf and o not in anchors]
    before=_fingerprints(untouched);records=[]
    for old in anchors:
        name=old.name;settings=_settings(old);matrix=[v for row in old.matrix_world for v in row]
        rec={'originalName':name,'anchorId':name,'label':old.get('label'),'parent':old.parent.name if old.parent else None,'originalWorldMatrix':matrix,'localPosition':list(old.location),'oldSubtreeObjects':len(old.children_recursive)+(1 if old.type=='MESH' else 0),'style':settings[0],'bodySizeMetres':list(settings[1]),'motorLayoutEvidence':'inferred_existing_v3_layout','oemMotorModelVerified':False,'externalConnectionScope':'existing_axis_and_external_load_geometry_preserved; hidden_train_unverified'}
        if old.type=='MESH':
            props={k:old[k] for k in old.keys()};par=old.parent;local=old.matrix_local.copy()
            bpy.data.objects.remove(old,do_unlink=True)
            g=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(g);g.parent=par;g.matrix_local=local
            for k,v in props.items():g[k]=v
        else:
            g=old
            for c in list(g.children_recursive):
                if c not in retained and c.name in bpy.data.objects:bpy.data.objects.remove(c,do_unlink=True)
        add_exterior(g,*settings)
        rec['newAnchorName']=g.name;rec['newSubtreeObjects']=len(g.children_recursive);rec['newMeshObjects']=sum(c.type=='MESH' for c in g.children_recursive)
        rec['outputAxisLocal']=list(settings[-1]@Vector((1,0,0))) if settings[-1] else [1,0,0]
        rec['hasExposedOutputShaft']=settings[2] is not None
        records.append(rec)
    bpy.context.view_layer.update()
    after=_fingerprints([bpy.data.objects[n] for n in before])
    if before!=after:raise AssertionError('Non-motor geometry/transform changed: '+stage)
    for k,v in old_root_props.items():
        if root[k]!=v:raise AssertionError('Root property changed: '+k)
    root['driveRevision']='4.0';root['motorDetailScope']='external_only';root['refinedMotorCount']=len(anchors)
    out=BASE/'qa/v4-candidates/models';out.mkdir(parents=True,exist_ok=True)
    save=BASE/'blender/v4-source';save.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
    for o in root.children_recursive:o.select_set(True)
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=str(out/f'{stage}.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(save/f'{stage}.blend'))
    report={'stage':stage,'source':str(src.relative_to(BASE)),'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'modelVersion':root.get('modelVersion'),'driveRevision':'4.0','motorDetailScope':'external_only','structuralCompleteness':False,'oemMotorModelsVerified':False,'replacedMotorCount':len(anchors),'objectsBefore':before_count,'objectsAfter':len(root.children_recursive),'unchangedNonMotorObjects':len(before),'nonMotorFingerprintSHA256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'nonMotorObjectsTransformsMeshesUnchanged':True,'rootOriginalMetadataUnchanged':True,'glbBytes':(out/f'{stage}.glb').stat().st_size,'glbSHA256':hashlib.sha256((out/f'{stage}.glb').read_bytes()).hexdigest(),'motors':records}
    (out.parent/f'{stage}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('DRIVE_REFINED',stage,len(anchors),report['glbBytes'],flush=True)
    if preview and anchors:
        anchor=bpy.data.objects.get(records[0]['newAnchorName']);render_closeup(anchor,BASE/'qa/v4-candidates'/f'{stage}-motor-closeup.png')
    return report

def render_closeup(anchor,path,view_direction=(1.8,-2.7,1.6)):
    """Isolated exterior review, without changing saved scene geometry."""
    visible={anchor,*anchor.children_recursive}
    for o in bpy.context.scene.objects:o.hide_render=o not in visible
    pts=[o.matrix_world@Vector(c) for o in anchor.children_recursive if o.type=='MESH' for c in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));center=(lo+hi)/2;extent=max(hi-lo)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48
    scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.55,.61,.67,1);bg.inputs[1].default_value=.55
    for off,energy in [((1,-2,2.8),110),((-2,1,1.3),80)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(off)*extent);o=bpy.context.object;o.data.energy=energy*extent**2;o.data.size=extent*2;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    direction=anchor.matrix_world.to_3x3()@Vector(view_direction);direction.normalize()
    bpy.ops.object.camera_add(location=center+direction*extent*4);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.5;cam.data.clip_end=1000;scene.camera=cam
    scene.view_settings.view_transform='AgX';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    preview='--preview' in args;stages=[x for x in args if not x.startswith('--')] or STAGES
    reports=[refine_stage(stage,preview) for stage in stages]
    folder=BASE/'qa/v4-candidates'
    existing=[]
    for stage in STAGES:
        p=folder/f'{stage}.json'
        if p.exists():existing.append(json.loads(p.read_text()))
    manifest={'revision':'4.0','scope':'exterior-only motor refinement; existing equipment and transmissions retained','structuralCompleteness':False,'oemMotorModelsVerified':False,'stages':existing,'totalReplacedMotors':sum(x['replacedMotorCount'] for x in existing),'totalGLBBytes':sum(x['glbBytes'] for x in existing)}
    (folder/'drive-refinement-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
