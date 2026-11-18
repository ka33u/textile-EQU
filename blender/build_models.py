"""Textile Atlas — original educational machinery models, Blender 5.0.
Run: Blender --background --python blender/build_models.py
No proprietary CAD, exact dimensions, or manufacturer identity is represented.
Coordinate contract: author Z-up; glTF Y-up. Extras spinAxis/explode are glTF axes.
"""
import bpy, math, json, os, sys
from mathutils import Vector
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'dist/assets/models'; OUT.mkdir(parents=True,exist_ok=True)
BLEND=BASE/'blender'; QA=BASE/'qa'; QA.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)

def mat(name, color, metal=0.0, rough=.36):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    s=m.node_tree.nodes.get('Principled BSDF'); s.inputs['Base Color'].default_value=(*color,1)
    s.inputs['Metallic'].default_value=metal; s.inputs['Roughness'].default_value=rough
    return m
M={
'white':mat('Ceramic white enamel',(.76,.82,.80),.45),
'teal':mat('Petrol blue enamel',(.025,.15,.19),.5),
'dark':mat('Graphite cast iron',(.027,.041,.05),.55),
'steel':mat('Brushed stainless steel',(.52,.62,.66),.82,.24),
'orange':mat('Drive safety ochre',(.92,.29,.055),.5),
'copper':mat('Copper winding enamel',(.68,.25,.075),.75,.24),
'cloth':mat('Cotton natural ecru',(.87,.81,.65),.0,.85),
'bluecloth':mat('Dyed cotton indigo',(.07,.27,.46),.0,.85),
'black':mat('Rubber belt and gaskets',(.014,.022,.025),.1,.64),
'green':mat('Indicator mint',(.16,.7,.5),.3),
'glass':mat('Operator display glass',(.015,.05,.065),.5,.19),
}
roots=[]; stage_counts={}
DESCRIPTIONS={
'带散热筋的铸铁机壳':'机壳支撑定子并保护内部结构；轴向散热筋增加与冷却气流的换热面积。',
'轴向散热筋':'沿机壳轴向布置，配合轴端风扇将热量传给周围空气。',
'定子叠片铁心':'由电工钢叠片组成，为旋转磁场提供磁路；叠片有助于减小涡流损耗。',
'定子端部铜绕组':'三相绕组通电后形成旋转磁场；可见铜色端部是教学结构示意。',
'槽内绕组':'绕组位于定子铁心槽内，与端部线圈连成三相电路。',
'转子叠片铁心':'在定子旋转磁场作用下与鼠笼导条共同产生电磁转矩。',
'鼠笼导条':'转子导条与两端端环相连，感应电流和磁场相互作用产生转矩。',
'输出转轴':'把转子产生的转矩传递给联轴器或带轮。',
'轴伸平键':'与联轴器或带轮轮毂键槽配合，传递转矩。',
'滚动轴承':'支承转轴并限制径向、轴向位移，使转子保持所需气隙。',
'轴承外圈':'定位于端盖轴承座内，与滚动体和内圈共同支承转轴。',
'轴承内圈':'装配在电机轴上，随轴旋转。',
'轴承滚珠':'在内外圈滚道之间滚动，降低支承摩擦。',
'轴承座端盖':'连接机壳并定位轴承，维持转子与定子的同心度。',
'轴端冷却风扇':'随转轴转动，将空气引向机壳散热筋。',
'冷却风扇叶片':'引导冷却空气流动；动画仅为结构演示。',
'风罩通风格栅':'允许冷却空气通过，同时隔离旋转风扇。',
'电机接线盒':'容纳绕组接线端子和电缆入口；具体接法按铭牌与设计确定。',
'六端子接线柱':'连接三相定子绕组引出线，示意六端子布置。',
'电缆密封接头':'固定电缆并保护接线盒进线口。',
'底脚安装座':'将电机固定到设备机架，安装时需保证轴系对中。',
'弹性联轴器':'连接电机与从动轴，传递转矩并缓冲一定冲击。',
'同步传动带':'围绕主动和从动带轮传递转矩；本模型为通用带传动构型。',
'综框开口机构':'交替升降经纱形成梭口，为纬纱通过提供空间。',
'剑杆引纬路径':'剑杆在上下经纱形成的梭口中运动，将纬纱带过幅宽。',
'连续布幅':'织造完成后形成的平幅织物；染整路线按产品要求选配。',
'经纱片':'相互平行的经纱经过浸浆、挤压、烘干后卷绕成织轴，尚未形成织物。',
'熟条筒':'存放并条输出的熟条，经导条架喂入粗纱机牵伸区。',
'上下经纱梭口':'交替经纱经过不同高度综框，在引纬区分成上下两层，并在织口汇合。'
}


def meta(o,label,group='frame',desc=None):
    o['label']=label; o['group']=group; o['description']=desc or DESCRIPTIONS.get(label,label)
    if group=='shell' or o.name.startswith(('stator_housing','cooling_fin','end_shield','terminal_lid','fan_guard','grille_')):o['shell']=True
    return o

def empty(name, loc=(0,0,0), parent=None, label=None, group='frame', explode=None, spin=None):
    o=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(o); o.location=loc; o.parent=parent
    meta(o,label or name,group)
    if explode is not None: o['explode']=explode
    if spin: o['spinAxis']=spin; o['spinSpeed']=.7
    return o

def finish(o,name,material,parent,label,group='frame',bevel=0):
    o.name=name; o.parent=parent; o.data.materials.append(M[material]); meta(o,label or name,group)
    if bevel:
        mod=o.modifiers.new('Machined edge radius','BEVEL'); mod.width=bevel; mod.segments=3
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
    if o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=False
    return o

def box(name,loc,scale,material='white',parent=None,label=None,group='frame',bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,material,parent,label,group,bevel)

def cyl(name,loc,radius,length,material='steel',parent=None,label=None,axis='x',group='roller',vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=length,location=loc)
    o=bpy.context.object
    if axis=='x': o.rotation_euler[1]=math.pi/2
    elif axis=='y': o.rotation_euler[0]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    o=finish(o,name,material,parent,label,group,0)
    ai={'x':0,'y':1,'z':2}[axis]
    for p in o.data.polygons:p.use_smooth=abs(p.normal[ai])<.999
    return o

def torus(name,loc,major,minor,material='steel',parent=None,label=None,axis='x',group='motor'):
    bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=10,location=loc,major_radius=major,minor_radius=minor)
    o=bpy.context.object
    if axis=='x':o.rotation_euler[1]=math.pi/2
    elif axis=='y':o.rotation_euler[0]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    o=finish(o,name,material,parent,label,group)
    for p in o.data.polygons:p.use_smooth=True
    return o

def tube(name,pts,radius=.025,material='steel',parent=None,label=None,group='material'):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=radius; c.bevel_resolution=1; c.resolution_u=1
    if material=='black' and len(pts)>2:
        c.resolution_u=8;c.bevel_resolution=2;spl=c.splines.new('BEZIER');spl.bezier_points.add(len(pts)-1)
        for p,xyz in zip(spl.bezier_points,pts):p.co=xyz;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    else:
        spl=c.splines.new('POLY');spl.points.add(len(pts)-1)
        for p,xyz in zip(spl.points,pts):p.co=(*xyz,1)
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.convert(target='MESH'); o=bpy.context.object; o.select_set(False)
    o=finish(o,name,material,parent,label,group)
    for p in o.data.polygons:p.use_smooth=True
    return o

def annulus(name,x1,x2,r1,r2,parent,material='teal',a0=0,a1=2*math.pi,label='定子机壳',group='motor',steps=48):
    verts=[]
    for x in (x1,x2):
        for r in (r1,r2):
            for i in range(steps+1):
                a=a0+(a1-a0)*i/steps; verts.append((x,r*math.cos(a),r*math.sin(a)))
    n=steps+1; faces=[]
    for i in range(steps):
        faces += [(i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),(i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)]
    faces.extend([(0,n,3*n,2*n),(steps,2*n+steps,3*n+steps,n+steps)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
    o=finish(o,name,material,parent,label,group)
    for i,p in enumerate(o.data.polygons):p.use_smooth=(i<steps*4 and i%4 in (2,3))
    return o

def roll(parent,name,y,z,r=.16,width=2.7,material='steel',x=0,spin=True):
    g=empty('rotate_'+name if spin else name,(x,y,z),parent,label=name,group='roller',spin='x' if spin else None)
    cyl(name+'_drum',(0,0,0),r,width,material,g,name)
    cyl(name+'_shaft',(0,0,0),r*.29,width+.35,'steel',g,'辊轴')
    for side in (-1,1):
        cyl(name+'_end',(side*(width/2+.025),0,0),r*1.06,.04,'orange',g,'辊端法兰')
    return g

def bolt(parent,loc,axis='z',r=.035,label='六角紧固螺栓'):
    return cyl('bolt',loc,r,.045,'steel',parent,label,axis,'frame',6)

def textmesh(parent,text,loc,size=.18):
    c=bpy.data.curves.new('Equipment plate','FONT');c.body=text;c.size=size;c.extrude=.001;c.align_x='CENTER'
    o=bpy.data.objects.new('Engraved '+text,c);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(math.pi/2,0,0)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False)
    finish(o,o.name,'white',parent,'设备铭牌','shell')

def base(stage,title,w=3.4,d=2.8,h=.32):
    root=empty('stage_'+stage,label=title);root['stage']=stage;root['modelType']='educational_concept';roots.append(root)
    box('base_skid',(0,0,h/2),(w,d,h),'teal',root,'设备底座',bevel=.06)
    for x in (-w/2+.2,w/2-.2):
        for y in (-d/2+.2,d/2-.2):
            cyl('leveling_foot',(x,y,.09),.11,.18,'dark',root,'调平地脚','z','frame')
            bolt(root,(x,y,h+.025))
    box('identity_plate',(0,-d/2-.012,.25),(1.2,.035,.22),'dark',root,'设备标识板',bevel=.01)
    textmesh(root,stage.upper(),(0,-d/2-.034,.20),.12)
    return root

def posts(parent,xs=(-1.4,1.4),ys=(-.9,.9),height=1.6,z=.35):
    for x in xs:
        for y in ys:
            box('frame_column',(x,y,z+height/2),(.14,.16,height),'teal',parent,'支撑机架')
    for x in xs:box('frame_longitudinal',(x,0,z+height),(.16,abs(ys[-1]-ys[0])+.15,.13),'white',parent,'机架横梁')

def console(parent,loc):
    x,y,z=loc
    box('operator_console',(x,y,z),(.5,.22,.55),'white',parent,'操作面板','shell',.04)
    box('control_display',(x,y-.12,z+.08),(.36,.025,.23),'glass',parent,'触摸控制屏','shell',.01)
    for i,ma in enumerate(('orange','green')):cyl('push_button',(x-.13+i*.24,y-.143,z-.14),.045,.03,ma,parent,'急停/运行按钮','y','shell',16)

def motor(parent,loc=(1.3,0,.8),scale=1,detail=False):
    # Main shaft aligned X. Compact motors have a full housing; detail motor is cutaway.
    g=empty('motor_assembly',loc,parent,'三相异步电动机','motor',explode=[0,.6,1.0] if not detail else None)
    g.scale=(scale,scale,scale)
    if not detail:box('motor_mounting_bracket',(0,0,-.62),(1.12,.95,.26),'white',g,'电机安装托架','frame')
    body=empty('motor_housing',parent=g,label='散热机壳与定子铁心',group='motor',explode=[0,.7,-.7] if detail else None)
    annulus('stator_housing',-.55,.55,.32,.43,body,'teal',3.65 if detail else 0,8.0 if detail else 2*math.pi,label='带散热筋的铸铁机壳')
    # axial cooling fins along casing, leaving an explanatory cutaway sector
    for i in range(20):
        a=2*math.pi*i/20
        if detail and 1.7<a<3.65:continue
        y,z=.455*math.cos(a),.455*math.sin(a)
        f=box('cooling_fin',(0,y,z),(1.05,.025,.09),'teal',body,'轴向散热筋','motor',.006)
        f.rotation_euler[0]=a-math.pi/2
    for y in (-.33,.33):
        box('motor_mounting_foot',(0,y,-.43),(.95,.22,.12),'teal',body,'底脚安装座','motor')
        for x in (-.33,.33):bolt(body,(x,y,-.355),r=.045)
    winding=empty('stator_windings',parent=g,label='定子铁心与铜绕组',group='motor',explode=[0,1.2,0] if detail else None)
    annulus('laminated_stator',-.48,.48,.26,.32,winding,'steel',3.65 if detail else 0,8.0 if detail else 2*math.pi,label='定子叠片铁心')
    for x in (-.49,.49):
        for r in (.274,.30):torus('copper_end_winding',(x,0,0),r,.025,'copper',winding,'定子端部铜绕组')
    for i in range(12):
        a=2*math.pi*i/12
        tube('copper_slot', [(-.48,.285*math.cos(a),.285*math.sin(a)),(.48,.285*math.cos(a),.285*math.sin(a))],.014,'copper',winding,'槽内绕组','motor')
    rotor=empty('rotor_unit',parent=g,label='鼠笼转子与输出轴',group='motor',explode=[2.5,0,0] if detail else None,spin='x')
    cyl('rotor_core',(0,0,0),.225,.86,'steel',rotor,'转子叠片铁心',group='motor')
    for i in range(18):
        a=i*2*math.pi/18
        tube('rotor_bar',[(-.43,.226*math.cos(a),.226*math.sin(a)),(.43,.226*math.cos(a+.12),.226*math.sin(a+.12))],.012,'copper',rotor,'鼠笼导条','motor')
    cyl('output_shaft',(.2,0,0),.075,2.1,'steel',rotor,'输出转轴',group='motor')
    box('shaft_key',(.98,0,.078),(.28,.045,.025),'steel',rotor,'轴伸平键','motor',.004)
    for s in (-1,1):
        bearing=empty(('front' if s>0 else 'rear')+'_bearing',(s*.58,0,0),g,'滚动轴承','motor',explode=[3.1 if s>0 else -1.1,.25,0] if detail else None)
        torus('bearing_outer',(0,0,0),.135,.032,'steel',bearing,'轴承外圈')
        torus('bearing_inner',(0,0,0),.087,.016,'steel',bearing,'轴承内圈')
        for i in range(8):
            a=i*math.pi/4;bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=.025,location=(0,.113*math.cos(a),.113*math.sin(a)))
            finish(bpy.context.object,'bearing_ball','steel',bearing,'轴承滚珠','motor')
        cap=empty(('front' if s>0 else 'rear')+'_end_shield',(s*.66,0,0),g,'前端盖' if s>0 else '后端盖','motor',explode=[3.7 if s>0 else -1.5,0,0] if detail else None)
        annulus('end_shield',-.055,.055,.15,.40,cap,'teal',label='轴承座端盖')
        for a in (math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4):bolt(cap,(s*.065,.335*math.cos(a),.335*math.sin(a)),'x',.04)
    fan=empty('cooling_fan',(-.80,0,0),g,'轴端冷却风扇','motor',explode=[-2.1,0,0] if detail else None,spin='x')
    cyl('fan_hub',(0,0,0),.11,.09,'orange',fan,'风扇轮毂',group='motor')
    for i in range(9):
        a=i*2*math.pi/9
        b=box('fan_blade',(0,.22*math.cos(a),.22*math.sin(a)),(.045,.24,.075),'orange',fan,'冷却风扇叶片','motor',.012);b.rotation_euler[0]=a
    hood=empty('fan_cover',(-.92,0,0),g,'风扇防护罩','motor',explode=[-2.6,0,0] if detail else None)
    annulus('fan_guard',-.05,.09,.355,.39,hood,'dark',label='风罩圆周护圈')
    # visible spokes approximate perforated rear grille
    for i in range(14):
        a=i*2*math.pi/14
        tube('grille_spoke',[(-.06,0,0),(-.06,.36*math.cos(a),.36*math.sin(a))],.012,'dark',hood,'风罩通风格栅','motor')
    for r in (.13,.24,.34):torus('grille_ring',(-.06,0,0),r,.011,'dark',hood,'风罩防护网')
    terminal=empty('terminal_box',(0,0,.56),g,'电机接线盒','motor',explode=[0,1.4,0] if detail else None)
    box('terminal_base',(0,0,0),(.47,.40,.2),'teal',terminal,'接线盒底座','motor')
    lid=box('terminal_lid',(0,0,.17),(.50,.43,.06),'dark',terminal,'接线盒盖','motor',.018)
    if detail: lid['explode']=[0,.45,0]
    for x in (-.17,.17):
        for y in (-.14,.14):bolt(terminal,(x,y,.212),r=.025)
    for x in (-.13,0,.13):
        for y in (-.075,.075):cyl('terminal_stud',(x,y,.11),.022,.08,'copper',terminal,'六端子接线柱','z','motor',10)
    cyl('cable_gland',(0,-.29,0),.065,.19,'dark',terminal,'电缆密封接头','y','motor')
    tube('motor_cable',[(0,-.38,.56),(0,-.55,.3),(.2,-.55,-.2)],.025,'black',g,'动力电缆','motor')
    if not detail:
        coupling=empty('rotate_coupling',(1.05,0,0),g,'弹性联轴器','motor',spin='x')
        cyl('coupling_front',(-.08,0,0),.15,.14,'orange',coupling,'联轴器半体',group='motor')
        cyl('coupling_elastomer',(.015,0,0),.14,.055,'black',coupling,'弹性缓冲体',group='motor')
        cyl('coupling_rear',(.10,0,0),.15,.13,'orange',coupling,'从动半联轴器',group='motor')
    return g

def yarns(parent,y1,z1,y2,z2,width=2.4,n=24,material='cloth'):
    for i in range(n):
        x=-width/2+width*i/(n-1)
        tube('warp_thread',[(x,y1,z1),(x,y2,z2)],.006,material,parent,'经纱/纤维路径','material')

def cloth(parent,pts,width=2.6,material='cloth'):
    verts=[]
    for y,z in pts:verts.extend([(-width/2,y,z),(width/2,y,z)])
    faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)]
    me=bpy.data.meshes.new('Fabric web');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('fabric_web',me);bpy.context.collection.objects.link(o)
    finish(o,'fabric_web',material,parent,'连续布幅','material');mod=o.modifiers.new('Fabric thickness','SOLIDIFY');mod.thickness=.015;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

def can(parent,x,y,z=.35,r=.40,h=.9,filled=True):
    cyl('sliver_can',(x,y,z+h/2),r,h,'white',parent,'棉条筒','z','material')
    cyl('can_rim',(x,y,z+h+.01),r*1.035,.04,'steel',parent,'条筒口圈','z','material')
    if filled:
        for j in range(4):torus('coiled_sliver',(x,y,z+h+.025+j*.007),r*(.35+j*.13),.025,'cloth',parent,'圈放棉条','z','material')

def machine_opening():
    r=base('opening','开清棉联合机',4.6,3.6);posts(r,(-2,2),(-1.3,1.3),2.2)
    for x in (-1.45,-.45,.55):box('cotton_bale',(x,-.9,.8),(.83,1,.9),'cloth',r,'压缩棉包','material',.09)
    box('travelling_plucker',(0,-.9,2.2),(3.8,.7,.48),'white',r,'往复式抓棉小车','shell',.08)
    roll(r,'抓棉打手',-.9,1.94,.18,3.5,'orange')
    box('cleaner_chamber',(0,1.0,1.3),(3.4,1.0,1.8),'white',r,'开松除杂腔','shell',.08)
    tube('pneumatic_duct',[(-1.2,-.65,2.5),(-1.2,-.65,3.0),(-1.2,1,3.0),(-1.2,1,2.2)],.18,'steel',r,'气流输棉管','frame')
    for x in (-1,0,1):box('service_door',(x,.475,1.3),(.9,.04,1.4),'teal',r,'检修门','shell')
    motor(r,(1.55,.9,2.45),.55);console(r,(2.05,-1.15,1.5));return r

def machine_carding():
    r=base('carding','梳棉机',3.9,3.7);posts(r,(-1.6,1.6),(-1.4,1.4),1.7)
    roll(r,'锡林',0,1.47,.85,2.7,'steel');roll(r,'刺辊',1.14,1.2,.28,2.7,'orange');roll(r,'道夫',-1.1,1.05,.4,2.7)
    for y in (-.55,-.35,-.15,.05,.25,.45,.65):box('revolving_flat',(0,y,2.29),(2.8,.08,.08),'teal',r,'回转盖板','roller',.012)
    shell=empty('carding_side_shell',parent=r,label='锡林侧罩',group='shell',explode=[-1.3,.4,0])
    cyl('cylinder_side',(-1.45,0,1.47),.91,.12,'white',shell,'锡林侧护罩',group='shell')
    box('feed_chute',(0,1.4,2.1),(2.7,.65,1.7),'white',r,'棉箱喂入','shell',.07)
    cloth(r,[(-1.1,1.35),(-1.7,.85)],2.1);can(r,.6,-2.0,.05,.38,.7)
    tube('sliver_delivery',[(0,-1.6,.9),(.6,-2,1.0)],.04,'cloth',r,'棉网集束成条')
    motor(r,(1.25,.45,.85),.58);console(r,(-1.85,-1.3,1.6));return r

def machine_drawing():
    r=base('drawing','并条机',4.5,4.1)
    for x in (-1.4,-.45,.5,1.45):can(r,x,1.0,.35,.37,.95)
    box('drafting_table',(0,-.35,1.55),(3.9,1.5,.35),'white',r,'并合牵伸台','shell',.08)
    for y,rr in ((.1,.13),(-.3,.13),(-.7,.16)):
        roll(r,'牵伸罗拉',y,1.84,rr,3.3)
        roll(r,'加压胶辊',y,2.09,rr*.8,3.3,'black')
    for x in (-1.4,-.45,.5,1.45):tube('sliver_in',[(x,1,1.38),(x,.3,1.86),(x*.2,-.9,1.86)],.027,'cloth',r,'多根棉条并合')
    can(r,0,-1.5,.35,.55,.85);tube('sliver_out',[(0,-.9,1.86),(0,-1.5,1.5)],.04,'cloth',r,'输出熟条')
    motor(r,(1.5,-.5,.88),.60);console(r,(-1.9,-.8,1.8));return r

def machine_combing():
    r=base('combing','精梳与成卷准备',4.4,3.2);posts(r,(-1.9,1.9),(-1.0,1.0),1.4)
    box('comber_bed',(0,0,1.25),(4,2,.5),'white',r,'精梳机台面','shell',.07)
    for x in (-1.35,-.45,.45,1.35):
        roll(r,'棉卷',.65,2.0,.36,.68,'cloth',x)
        roll(r,'精梳锡林',-.25,1.65,.22,.68,'orange',x)
        box('nipper',(x,-.15,1.91),(.72,.25,.07),'steel',r,'钳板机构','roller')
        for j in range(8):box('top_comb_tooth',(x-.3+j*.085,-.46,1.85),(.018,.035,.22),'steel',r,'顶梳针齿','roller',.002)
        tube('combed_web',[(x,.5,1.8),(x,-.6,1.55),(0,-1.1,1.45)],.025,'cloth',r,'梳理棉网')
    can(r,0,-1.7,.1,.42,.9);motor(r,(1.7,.4,.8),.57);console(r,(-1.9,-.9,1.8));return r

def spinning_family(stage,roving=False):
    r=base(stage,'粗纱机' if roving else '环锭细纱机',5.5,4.3 if roving else 2.7);posts(r,(-2.35,2.35),(-.85,.85),2.3)
    for z in (1.12,2.06,2.65):box('longitudinal_rail',(0,0,z),(5,.16,.12),'teal',r,'纵向机架梁')
    if roving:
        for j in range(5):
            can(r,-1.85+j*.92,1.45,.35,.37,.85)
        tube('sliver_guide_rail',[(-2.25,.65,2.65),(2.25,.65,2.65)],.035,'steel',r,'导条架','frame')
    for i in range(10):
        x=-2.05+i*.455
        if roving:
            tube('drawn_sliver_feed',[(round((x+1.85)/.92)*.92-1.85,1.45,1.22),(x,.65,2.65),(x,.46,2.25)],.018,'cloth',r,'熟条筒')
        else:cyl('feed_bobbin',(x,.46,2.34),.11,.55,'cloth',r,'粗纱喂入筒管','z','material')
        rotor=empty('rotate_spindle',(x,-.35,1.08),r,'锭翼/锭子','roller',spin='y')
        cyl('bobbin',(0,0,0),.105 if roving else .068,.70,'cloth',rotor,'粗纱卷装' if roving else '细纱管纱','z','material')
        cyl('spindle_shaft',(0,0,-.10),.025,1.05,'steel',rotor,'高速锭子','z')
        if roving:
            tube('flyer',[(0,0,.52),(.17,0,.45),(.17,0,-.36)],.022,'steel',rotor,'锭翼')
            tube('flyer_opposite',[(0,0,.52),(-.17,0,.45),(-.17,0,-.36)],.022,'steel',rotor,'锭翼平衡臂')
        else:torus('ring_traveler',(x,-.35,.83),.14,.015,'steel',r,'钢领与钢丝圈','z','roller')
        tube('fiber_path',[(x,.46,2.64),(x,-.08,2.08),(x,-.35,1.50)],.008,'cloth',r,'牵伸后纱线')
    for y in (-.02,.2,.42):roll(r,'牵伸罗拉',y,2.07,.075,4.8)
    box('headstock',(-2.55,0,1.32),(.5,1.8,1.9),'white',r,'传动车头','shell',.06)
    motor(r,(-1.4,.65,.77),.55);console(r,(-2.6,-.95,1.6));return r

def machine_winding():
    r=base('winding','自动络筒机',5,2.4);posts(r,(-2.1,2.1),(-.7,.7),2.1)
    box('winder_body',(0,.4,1.5),(4.6,.8,2.1),'white',r,'络筒单元背板','shell',.05)
    for i in range(6):
        x=-1.8+i*.72
        roll(r,'交叉卷绕筒子',-.25,2.05,.25,.55,'cloth',x)
        cyl('supply_cop',(x,-.55,.87),.095,.6,'cloth',r,'细纱供纱管','z','material')
        box('yarn_clearer',(x,-.5,1.4),(.25,.2,.22),'teal',r,'电子清纱器','shell')
        tube('yarn_path',[(x,-.55,1.15),(x,-.6,1.5),(x,-.3,2)],.008,'cloth',r,'络筒纱线')
    motor(r,(1.8,.1,.7),.5);console(r,(-2.25,-.7,1.65));return r

def machine_warping():
    r=base('warping','整经机与筒子架',4.4,5.8)
    for y in (.4,1.2,2.0):
        for x in (-1.65,1.65):
            box('creel_upright',(x,y,1.55),(.1,.1,2.4),'teal',r,'筒子架立柱')
            for z in (.9,1.6,2.3):cyl('creel_package',(x*.82,y,z),.18,.42,'cloth',r,'整经供纱筒子',group='material')
    box('warper_front',(0,-1.8,.7),(3.8,1.4,.7),'white',r,'整经卷绕机座','shell',.08)
    roll(r,'整经轴',-1.8,1.45,.54,2.8,'cloth')
    for x in (-1.5,1.5):cyl('beam_flange',(x,-1.8,1.45),.69,.08,'teal',r,'经轴盘片')
    box('reed_comb',(0,-.55,1.8),(3.0,.1,.22),'steel',r,'伸缩筘分纱装置')
    yarns(r,2.1,2.3,-.55,1.92,2.5,32);yarns(r,-.55,1.92,-1.8,1.98,2.5,32)
    motor(r,(1.35,-1.7,.77),.6);console(r,(-1.9,-2.2,1.6));return r

def machine_sizing():
    r=base('sizing','浆纱联合机',4.1,6.4);posts(r,(-1.7,1.7),(-2.6,2.6),1.5)
    box('size_trough',(0,1.8,.9),(3.4,1.3,1.0),'teal',r,'浆槽与浸浆装置','shell',.08)
    for y,z in ((2.2,1.5),(1.55,1.3),(1.0,1.65),(.2,1.65),(-.6,1.65),(-1.4,1.65)):
        roll(r,'上浆/烘燥辊筒',y,z,.30 if y<1.5 else .19,2.8,'steel')
    for j in range(40):
        xx=-1.3+j*2.6/39
        tube('sizing_warp_sheet',[(xx,yy,zz) for yy,zz in [(2.7,1.65),(1.8,1.1),(1,1.96),(.2,1.96),(-.6,1.96),(-1.4,1.96),(-2.5,1.3)]],.007,'cloth',r,'经纱片')
    roll(r,'织轴卷绕',-2.5,1.1,.4,2.8,'cloth')
    for x in (-1.5,1.5):cyl('weaver_beam_flange',(x,-2.5,1.1),.55,.09,'teal',r,'织轴边盘')
    motor(r,(1.25,-.6,.8),.6);console(r,(-1.8,-2.4,1.8));return r

def machine_drawing_in():
    r=base('drawing_in','穿综穿筘工作站',3.8,3.4);posts(r,(-1.5,1.5),(-1.2,1.2),2.2)
    roll(r,'待穿经轴',1.0,.95,.45,2.7,'cloth')
    for y in (-.4,0,.4):
        for z in (1.05,2.3):box('heald_frame',(0,y,z),(2.9,.06,.055),'steel',r,'综框上下横梁')
        for x in (-1.43,1.43):box('heald_frame_side',(x,y,1.67),(.05,.06,1.3),'steel',r,'综框边梁')
        for j in range(24):box('heald',(j*.112-1.29,y,1.67),(.008,.018,1.18),'steel',r,'综丝','roller',.001)
    yarns(r,1.0,1.4,-1.15,1.63,2.6,28)
    for i in range(34):box('reed_dent',(i*.081-1.34,-.9,1.65),(.009,.025,.45),'steel',r,'筘齿','roller',.001)
    box('drawing_carriage',(.65,-1.05,1.85),(.6,.42,.4),'orange',r,'自动穿经执行头','shell')
    motor(r,(1.1,.7,2.25),.38);console(r,(-1.6,-1.1,1.85));return r

def machine_weaving():
    r=base('weaving','剑杆织机',4.6,3.8);posts(r,(-1.85,1.85),(-1.5,1.5),1.6)
    for x in (-1.84,1.84):box('loom_side_frame',(x,0,1.1),(.38,3,1.5),'white',r,'织机侧机架','shell',.08)
    roll(r,'送经轴',1.15,1.0,.50,3.1,'cloth')
    for x in (-1.63,1.63):cyl('warp_beam_flange',(x,1.15,1),.59,.10,'teal',r,'经轴盘片')
    for i,y in enumerate((.05,.28,.51,.74)):
        z=1.88+(i%2)*.34
        g=empty('heald_frame_'+str(i),(0,y,z),r,'综框开口机构','roller',explode=[0,.6+i*.2,0])
        for zz in (-.4,.4):box('heald_bar',(0,0,zz),(3.2,.045,.055),'teal',g,'综框横梁')
        for xx in (-1.59,1.59):box('heald_side',(xx,0,0),(.045,.045,.8),'teal',g,'综框边梁')
        for j in range(20):box('heald_wire',(-1.43+j*.15,0,0),(.007,.016,.74),'steel',g,'综丝','roller',.001)
    for j in range(40):
        xx=-1.45+j*2.9/39; zz=2.15 if j%2 else 1.62
        tube('warp_shed_upper' if j%2 else 'warp_shed_lower',[(xx,1.15,1.50),(xx,.4,zz),(xx,-.28,zz),(xx,-.62,1.72)],.007,'cloth',r,'上下经纱梭口')
    reed=empty('reed_sley',(0,-.58,1.63),r,'筘座与打纬筘','roller',explode=[0,.1,1.0])
    box('sley_beam',(0,0,-.21),(3.35,.14,.15),'teal',reed,'打纬筘座')
    for i in range(48):box('reed_dent',(-1.48+i*.063,0,0),(.008,.032,.39),'steel',reed,'织筘筘齿','roller',.001)
    tube('rapier', [(-1.8,-.28,1.86),(1.6,-.28,1.86)],.018,'orange',r,'剑杆引纬路径','roller')
    cloth(r,[(-.6,1.72),(-1.15,1.65),(-1.55,1.05)],2.9)
    roll(r,'卷取布辊',-1.48,.85,.34,3.1,'cloth')
    box('motor_side_pedestal',(-2.65,.55,.43),(1.35,1.1,.26),'teal',r,'主电机外置支座')
    motor(r,(-2.65,.55,.78),.55);motor(r,(1.4,1.3,.67),.36)
    cyl('driven_main_shaft',(-1.55,-.35,1.40),.075,1.2,'steel',r,'织机主传动轴',group='motor')
    # Both pulleys lie in the same X plane. Small pulley aligns with motor shaft.
    for yy,zz,rr,lab in ((.55,.78,.18,'电机主动带轮'),(-.35,1.40,.37,'主轴从动带轮')):
        g=empty('rotate_drive_pulley',(-2.12,yy,zz),r,lab,'motor',spin='x')
        cyl('drive_pulley',(0,0,0),rr,.12,'orange',g,lab,group='motor')
    # A closed belt loop spans two pulley centres, including wrap arcs.
    pts=[]
    for cy,cz,rad,a0,a1 in ((.55,.78,.19,4.283,.793+2*math.pi),(-.35,1.40,.38,.793,4.283)):
        for j in range(19):
            a=a0+(a1-a0)*j/18;pts.append((-2.19,cy+rad*math.cos(a),cz+rad*math.sin(a)))
    pts.append(pts[0]);tube('drive_belt',pts,.028,'black',r,'同步传动带','motor')
    console(r,(-2.15,-1.25,1.85));return r

def machine_pretreatment():
    r=base('pretreatment','连续退煮漂水洗机',4.2,6.1);posts(r,(-1.75,1.75),(-2.5,2.5),1.7)
    for i,y in enumerate((-1.85,0,1.85)):
        box('washing_bath',(0,y,1.0),(3.6,1.65,1.35),'white',r,('退浆槽','煮练槽','漂白/水洗槽')[i],'shell',.08)
        for yy in (y-.55,y+.55):roll(r,'导布轧辊',yy,1.92,.19,3.0)
        for x in (-1.85,1.85):cyl('bath_pipe',(x,y,1.5),.07,1.3,'steel',r,'循环液管路','y','frame')
    cloth(r,[(-2.5,2.12),(-1.8,1.35),(-1.3,2.12),(-.55,2.12),(0,1.35),(.55,2.12),(1.3,2.12),(1.8,1.35),(2.5,2.12)],2.8)
    motor(r,(1.5,-1.8,.7),.6);console(r,(-1.9,-2.5,1.8));return r

def machine_dyeing():
    r=base('dyeing','平幅浸轧染色与固色水洗',4.2,7.0);posts(r,(-1.75,1.75),(-3.0,3.0),1.65)
    box('dye_pad_trough',(0,1.65,.95),(3.5,1.5,1.15),'teal',r,'染液浸轧槽','shell',.08)
    roll(r,'浸染导布辊',1.65,1.10,.22,2.9)
    roll(r,'轧液下辊',.65,1.30,.25,2.9,'black')
    roll(r,'轧液上辊',.65,1.82,.25,2.9,'steel')
    box('fixation_chamber',(0,-1.2,1.25),(3.5,2.15,1.8),'white',r,'固色/汽蒸示意箱','shell',.08)
    shell=empty('fixation_access_panel',parent=r,label='固色箱检修门',group='shell',explode=[1.1,.4,0])
    for y in (-1.75,-.65):box('chamber_side_door',(1.79,y,1.35),(.05,.93,1.25),'teal',shell,'保温检修门','shell')
    for y in (-1.8,-.7):roll(r,'箱内导布辊',y,1.6,.2,2.9)
    box('after_wash_bath',(0,-2.9,.85),(3.5,1.1,1.0),'teal',r,'固色后水洗槽','shell',.07)
    for yy in (-2.55,-3.3):roll(r,'水洗导布辊',yy,1.45,.18,2.9)
    cloth(r,[(2.4,1.7),(1.65,1.05),(.65,1.55),(-.7,1.8),(-1.8,1.8),(-2.55,1.63),(-2.9,1.0),(-3.3,1.63)],2.7,'bluecloth')
    tube('dye_circulation_pipe',[(-1.8,1.9,.6),(-1.8,1.9,1.6),(-1.8,.8,1.6)],.065,'steel',r,'染液循环管路')
    motor(r,(1.4,1.5,.8),.58);console(r,(-1.9,-2.1,1.8));return r

def machine_stenter():
    r=base('stenter','拉幅烘干与定幅机',4.3,6.2);posts(r,(-1.85,1.85),(-2.6,2.6),1.5)
    for y in (-1.5,0,1.5):
        box('thermal_chamber',(0,y,1.6),(3.7,1.35,1.6),'white',r,'拉幅烘干烘房','shell',.06)
        for x in (-1.9,1.9):box('access_panel',(x,y,1.6),(.08,1.12,1.24),'teal',r,'烘房检修面板','shell')
        tube('exhaust_stack',[(0,y,2.4),(0,y,2.85),(.65,y,2.85)],.15,'steel',r,'排湿风管')
        motor(r,(1.35,y,2.7),.43)
    for x in (-1.45,1.45):
        box('clip_chain_rail',(x,0,1.15),(.12,5.8,.15),'steel',r,'针板链条轨道')
        for j in range(30):box('chain_clip',(x,-2.8+j*.193,1.26),(.11,.08,.08),'orange',r,'布边针板/布夹','roller',.01)
    cloth(r,[(-3.1,1.23),(3.1,1.23)],2.8,'bluecloth');roll(r,'进布轧辊',-2.8,1.02,.19,3.1)
    console(r,(-1.95,-2.75,1.85));return r

def machine_calender():
    r=base('calender','轧光机（可选整理）',3.9,2.8);posts(r,(-1.6,1.6),(-.8,.8),2.5)
    for x in (-1.55,1.55):box('calender_stand',(x,0,1.65),(.35,1.2,2.5),'white',r,'高刚性轧光机架','shell',.08)
    for i in range(3):roll(r,'轧光辊',0,.95+i*.66,.31,2.8,'steel' if i%2==0 else 'black')
    for x in (-1.55,1.55):cyl('hydraulic_cylinder',(x,0,2.8),.13,.5,'orange',r,'加载油缸','z','frame')
    cloth(r,[(1.1,1.0),(.25,1.28),(-.25,1.65),(.25,1.95),(-1.1,2.25)],2.6,'bluecloth')
    motor(r,(1.3,.85,.8),.62);console(r,(-1.7,-.9,1.7));return r

def machine_inspection():
    r=base('inspection','验布与成卷',4.2,3.9);posts(r,(-1.7,1.7),(-1.5,1.5),1.4)
    table=box('inspection_light_table',(0,0,1.45),(3.3,2.2,.12),'white',r,'背光验布台','shell');table.rotation_euler[0]=-.5
    cloth(r,[(1.3,2.03),(-1.2,.88)],3,'bluecloth')
    roll(r,'放卷布轴',1.35,1.65,.37,3.2,'bluecloth');roll(r,'成品卷布轴',-1.45,.85,.42,3.2,'bluecloth')
    box('vision_crossbar',(0,.1,2.48),(3.5,.15,.15),'teal',r,'在线检测横梁')
    for x in (-1,0,1):
        box('inspection_camera',(x,.1,2.32),(.18,.22,.18),'dark',r,'视觉检测相机','shell')
        cyl('camera_lens',(x,.1,2.2),.055,.08,'glass',r,'相机镜头','z','shell')
    motor(r,(1.4,-1.2,.8),.55);console(r,(-1.9,-1.2,1.7));return r

exec(compile((BLEND/'industrial_v2.py').read_text(),str(BLEND/'industrial_v2.py'),'exec'))

exec(compile((BLEND/'motor_precision.py').read_text(),str(BLEND/'motor_precision.py'),'exec'))

# Current catalog references replace the v2 educational equipment builders.
for _module in ('current_spinning_v3.py','current_weaving_v3.py','current_finishing_v3.py'):
    exec(compile((BLEND/_module).read_text(),str(BLEND/_module),'exec'))

builders=[machine_opening,machine_carding,machine_drawing,machine_combing,lambda:spinning_family('roving',True),lambda:spinning_family('spinning'),machine_winding,machine_warping,machine_sizing,machine_drawing_in,machine_weaving,machine_pretreatment,machine_dyeing,machine_stenter,machine_calender,machine_inspection]
# Construct each machine in isolation; this avoids quadratic dependency-graph work.
source_parts=[]
for index,build in enumerate(builders+[None]):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    if build:root=build()
    else:
        root=empty('stage_motor',label='三相异步电动机结构');root['stage']='motor';root['modelType']='educational_cutaway'
        box('motor_plinth',(0,0,.15),(3.0,1.85,.3),'white',root,'电机展示底座',bevel=.06)
        motor(root,(0,0,1.0),1.4,True)
    _version=root.get('modelVersion','2.0')
    optimize_stage(root)
    root['modelVersion']=_version
    stage=root['stage'];stage_counts[stage]=len(root.children_recursive)
    bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=str(OUT/(stage+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
    tmp=BLEND/('.source-'+stage+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(tmp));source_parts.append((stage,tmp))
    print('CREATED_EXPORTED',stage,flush=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND/'.assembly-staging.blend'))
roots=[]
for stage,tmp in source_parts:
    with bpy.data.libraries.load(str(tmp),link=False) as (src,dst):dst.objects=list(src.objects)
    col=bpy.data.collections.new('MOTOR DETAIL' if stage=='motor' else stage.upper());bpy.context.scene.collection.children.link(col)
    for o in dst.objects:col.objects.link(o)
    root=bpy.data.objects.get('stage_'+stage);roots.append(root);tmp.unlink()
r=bpy.data.objects.get('stage_motor')
(BLEND/'.assembly-staging.blend').unlink()

# Authoring exhibition layout, all assets remain individually editable.
# Layout each source asset by its actual bounds, with a generous service aisle.
bpy.context.view_layer.update()
sizes=[]
for root in roots:
    points=[o.matrix_world @ Vector(c) for o in root.children_recursive if o.type=='MESH' for c in o.bound_box]
    lo=Vector(tuple(min(p[k] for p in points) for k in range(3)));hi=Vector(tuple(max(p[k] for p in points) for k in range(3)));sizes.append((lo,hi))
stepx=max(hi.x-lo.x for lo,hi in sizes)+2.5;stepy=max(hi.y-lo.y for lo,hi in sizes)+2.5
for i,root in enumerate(roots):root.location=((i%4)*stepx,(i//4)*stepy,0)
center=Vector((1.5*stepx,2*stepy,1.2))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.world.color=(.35,.35,.35)
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.75,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.object.light_add(type='AREA',location=(8,-4,18));bpy.context.object.name='Softbox key';bpy.context.object.data.energy=4500;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=14
bpy.ops.object.light_add(type='AREA',location=(18,18,15));bpy.context.object.name='Softbox fill';bpy.context.object.data.energy=3500;bpy.context.object.data.size=12
bpy.ops.object.camera_add(location=(40,-42,42));camera=bpy.context.object;camera.name='Atlas overview camera';camera.location=center+Vector((38,-58,47));direction=center-camera.location;camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=max(4*stepx,5*stepy)*1.2;scene.camera=camera
scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
# Opening viewport in material mode with complete collection visible.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_distance=45;area.spaces.active.region_3d.view_location=center
bpy.ops.object.select_all(action='DESELECT');roots[10].select_set(True);bpy.context.view_layer.objects.active=roots[10]
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND/'textile-machinery.blend'))
scene.render.filepath=str(QA/'equipment-gallery.png');bpy.ops.render.render(write_still=True)
# Save a separate motor source without other machines using a temporary scene copy.
for root in roots:
    root.hide_render=root!=r
r.location=(0,0,0)
camera.location=(4.6,-6,3.5);direction=Vector((0,0,1))-camera.location;camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=5.6
for o in bpy.data.objects:
    if o.type=='LIGHT':o.location=(2,-3,6);o.data.energy=600;o.data.size=5
# Hide other collections in viewport as well; source retains all assets only in atlas file.
for root in roots[:-1]:
    for o in [root]+list(root.children_recursive):bpy.data.objects.remove(o,do_unlink=True)
scene.render.resolution_x=1400;scene.render.resolution_y=1000
bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.context.view_layer.objects.active=r
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_location=(0,0,1)
            area.spaces.active.region_3d.view_distance=5.8
            area.spaces.active.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND/'motor-detail.blend'))
scene.render.filepath=str(BLEND/'motor-detail.png');bpy.ops.render.render(write_still=True)
# Exploded render uses extras expressed in glTF coordinates, converted back to Blender.
for o in r.children_recursive:
    if 'explode' in o:
        e=o['explode'];o.location += Vector((e[0],-e[2],e[1]))*.55
camera.data.ortho_scale=9
scene.render.filepath=str(QA/'motor-exploded.png');bpy.ops.render.render(write_still=True)
report={'blenderVersion':bpy.app.version_string,'models':[{ 'id':k,'objectCount':v,'bytes':(OUT/(k+'.glb')).stat().st_size} for k,v in stage_counts.items()], 'notes':['v3 public-source equipment references with explicit unverified configurations; standalone motor is educational; not manufacturer CAD','Blender Z-up / GLB Y-up','extras: label, description, group, explode (glTF axes), spinAxis (glTF local axis)','Main source: textile-machinery.blend; motor source: motor-detail.blend']}
(QA/'model-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('MODEL_BUILD_COMPLETE',json.dumps(report,ensure_ascii=False),flush=True)
