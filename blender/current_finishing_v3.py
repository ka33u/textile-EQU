"""Current-catalog finishing references. Public geometry, not manufacturer CAD.
Every root carries its chosen configuration and unresolved evidence status.
No claim of hidden-component completeness is made by the model or its metadata.
"""
M['v3_blue']=mat('Current equipment blue',(.022,.075,.24),.35,.32)
M['v3_red']=mat('Optical equipment red',(.62,.018,.035),.20,.31)
M['v3_silver']=mat('Brushed enclosure aluminium',(.55,.59,.61),.65,.30)
M['v3_white']=mat('Industrial light grey enamel',(.74,.77,.78),.22,.37)

def f3_root(stage,title,maker,model,configuration):
    r=empty('stage_'+stage,label=title)
    r['stage']=stage;r['equipmentId']=stage;r['modelVersion']='3.0';r['modelType']='current_public_reference'
    r['referenceStatus']='structure_unverified'
    r['referenceManufacturer']=maker;r['referenceModel']=model;r['referenceConfiguration']=configuration
    r['fidelityStatus']='partial_public_reference';r['structuralCompleteness']=False
    r['evidenceFile']='research/config-finishing-v3.json';r['coordinateUnit']='metre'
    return r

def f3_foot(r,x,y,z=.12):
    box('f3_sole',(x,y,.045),(.28,.30,.09),'steel',r,'独立安装底板',bevel=.012)
    cyl('f3_jackscrew',(x,y,z/2+.045),.035,z,'steel',r,'调平螺杆','z','frame',16)
    for dx in (-.09,.09):bolt(r,(x+dx,y,.10),'z',.023)

def f3_beam(r,name,loc,dims,material='v3_blue'):
    return box('f3_frame',loc,dims,material,r,name,'frame',.012)

def f3_case(r,name,loc,size,color='v3_white',explosion=(0,.6,0),through_z=None,open_top=False):
    x,y,z=loc;w,d,h=size
    g=empty('f3_case',parent=r,label=name,group='shell',explode=list(explosion))
    for xx in (-w/2,w/2):box('f3_case_wall',(x+xx,y,z),(.035,d,h),color,g,name+'侧壁','shell',.008)
    if not open_top:box('f3_case_top',(x,y,z+h/2),(w,d,.035),color,g,name+'顶板','shell',.008)
    if through_z is None:
        box('f3_case_rear',(x,y+d/2,z),(w,.035,h),color,g,name+'背板','shell',.008)
    else:
        low=z-h/2;high=z+h/2;gap=.13
        for yy in (y-d/2,y+d/2):
            for a,b in ((low,through_z-gap/2),(through_z+gap/2,high)):
                if b>a:box('f3_case_end_opening',(x,yy,(a+b)/2),(w,.035,b-a),color,g,name+'进出布槽端板','shell',.006)
    box('f3_case_floor',(x,y,z-h/2),(w,d,.035),'steel',g,name+'底板','shell',.008)
    return g

def f3_front_door(r,x,y,z,w,h,name,color='v3_white'):
    box('f3_door_gasket',(x,y,z),(w+.012,.028,h+.012),'black',r,'检修门密封','shell',.005)
    box('f3_door',(x,y-.019,z),(w,.025,h),color,r,name,'shell',.008)
    handle(r,(x+w*.37,y-.05,z),.12)
    for zz in (z-h*.32,z+h*.32):box('f3_door_hinge',(x-w*.45,y-.045,zz),(.025,.025,.09),'steel',r,'检修门铰链','shell',.003)

def f3_roller(r,name,y,z,radius,width,color='steel',x=0):
    g=roll(r,name,y,z,radius,width,color,x)
    for side in (-1,1):
        xx=x+side*(width/2+.09)
        cyl('f3_bearing',(xx,y,z),radius*.45,.11,'v3_blue',r,'导辊轴承座','x','frame',32)
        box('f3_bearing_foot',(xx,y,z-radius*.35),(.15,radius*.75,.07),'steel',r,'轴承座安装脚','frame',.008)
    return g

def f3_pipe(r,name,points,radius=.035,color='steel'):
    o=tube('f3_pipe',points,radius,color,r,name,'frame')
    o['evidenceStatus']='layout_inferred';return o

def f3_thin_cloth(parent,points,width,material='bluecloth'):
    # A submillimetre web avoids the old 15 mm teaching sheet intersecting narrow nips.
    verts=[(x,y,z) for y,z in points for x in (-width/2,width/2)]
    faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)]
    me=bpy.data.meshes.new('CPB fabric web');me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new('fabric_web',me);bpy.context.collection.objects.link(o)
    finish(o,'fabric_web',material,parent,'连续布幅','material')
    mod=o.modifiers.new('Display cloth thickness','SOLIDIFY');mod.thickness=.0006
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    o['thicknessStatus']='0.6mm display selection; actual fabric specification unverified'
    return o

def f3_drive(r,loc,label='驱动装置外部形体'):
    # Housing only: the motor type and hidden winding are not inferred from a generic cutaway.
    x,y,z=loc;g=empty('f3_external_drive',loc,r,label,'motor')
    g['description']='公开照片可见的驱动外部形体；具体电机型号、绕组及减速内部待厂家资料核实。'
    cyl('f3_drive_shell',(0,0,0),.14,.36,'v3_silver',g,label,'x','motor',32)
    for k in range(8):
        a=2*math.pi*k/8
        box('f3_drive_fin',(0,.14*math.cos(a),.14*math.sin(a)),(.30,.025,.025),'v3_silver',g,'外部散热筋','motor',.004)
    box('f3_drive_terminal',(-.02,0,.17),(.16,.15,.09),'v3_silver',g,'驱动接线壳','shell',.01)
    box('f3_drive_foot',(0,0,-.15),(.30,.30,.05),'steel',g,'驱动安装脚','frame',.005)
    cyl('f3_drive_shaft',(.25,0,0),.035,.16,'steel',g,'外伸轴','x','motor',24)
    f3_beam(r,'驱动承座',(x,y,z-.26),(.45,.38,.17))
    return g

def f3_panel_bank(r,x,y,number=4):
    for i in range(number):
        xx=x+i*.55
        g=f3_case(r,'分区电控柜',(xx,y,1.12),(.53,.48,1.88))
        f3_front_door(g,xx,y-.25,1.12,.49,1.80,'电控柜检修门')
        f3_foot(r,xx,y-.13);f3_foot(r,xx,y+.13)
        f3_pipe(r,'柜底电缆出口',[(xx,y,.18),(xx,y+.35,.13),(xx+.23,y+.35,.13)],.025,'black')

def machine_inspection():
    r=f3_root('inspection','Fabriq Vision 2 检测单元','Uster','Fabriq Vision 2','2250 mm检测幅宽；3000×2150×680 mm闭合检测单元；独立控制台')
    r['verifiedWidthMetres']=3.0;r['verifiedHeightMetres']=2.15;r['verifiedDepthMetres']=.68
    for x in (-1.44,1.44):
        for y in (-.27,.27):
            f3_foot(r,x,y,.12);f3_beam(r,'检测机架立柱',(x,y,1.12),(.09,.09,2.02),'v3_silver')
    for z in (.20,.48,2.11):
        for y in (-.28,.28):f3_beam(r,'检测单元横梁',(0,y,z),(2.96,.07,.07),'v3_silver')
    g=f3_case(r,'检测光学腔',(0,0,1.31),(2.95,.64,1.61),explosion=(0,.6,0))
    for i in range(4):
        x=-1.095+i*.73
        f3_front_door(g,x,-.339,1.12,.709,1.13,'光学腔检修门')
        f3_front_door(g,x,-.339,1.925,.709,.40,'相机上部检修盖','v3_red' if i>0 else 'v3_white')
    for y,z in ((-.23,.355),(.23,.355)):
        f3_roller(r,'检测单元导布辊',y,z,.05,2.44,'dark')
    # Actual camera quantity depends on the ordered optical configuration; do not invent it.
    inner=box('f3_optical_mount',(0,.06,1.66),(2.62,.08,.08),'dark',r,'SVC3光学安装梁（相机配置待核实）','frame',.005)
    inner['description']='SVC3检测平台已在厂家资料确认；相机数量、镜头与安装位置需要该幅宽订单的光学配置图，当前未虚构相机阵列。'
    for z in (.68,1.45):box('f3_illumination',(0,.11,z),(2.45,.09,.035),'white',r,'检测照明组件','frame',.003)
    cloth(r,[(.65,.412),(.23,.412),(-.23,.412),(-.65,.412)],2.20,'bluecloth')
    for side in (-1,1):
        cyl('f3_encoder',(side*1.28,.23,.355),.07,.06,'dark',r,'计长编码器安装端','x','frame',24)
    # Published console envelope: W650/H1550/D440 mm.
    x=-2.15;y=-.12
    c=f3_case(r,'独立检测控制台',(x,y,.795),(.65,.44,1.51),explosion=(-.4,0,0))
    f3_front_door(c,x,y-.235,.56,.60,1.00,'控制台下检修门','v3_red')
    box('f3_vision_hmi',(x,y-.245,1.32),(.55,.035,.34),'glass',c,'21.5英寸触摸屏','shell',.01)
    box('f3_keyboard_shelf',(x,y-.35,1.08),(.56,.22,.035),'v3_silver',c,'键盘操作台','shell',.008)
    box('f3_keyboard',(x,y-.36,1.105),(.40,.12,.012),'dark',c,'键盘','shell',.003)
    f3_foot(r,x-.24,y);f3_foot(r,x+.24,y)
    f3_pipe(r,'控制台至检测柜线缆',[(x+.32,y,.2),(-1.75,.45,.18),(-1.4,.45,.18),(-1.4,.25,.8)],.025,'black')
    # The review workstation is included in the technical delivery list, independent of the machine console.
    table=empty('f3_review_station',(-2.35,1.25,0),r,'Album复核工作站','frame')
    for xx in (-.4,.4):f3_beam(table,'工作站台脚',(xx,0,.43),(.06,.48,.86),'steel')
    box('f3_review_table',(0,0,.88),(1.0,.65,.045),'v3_white',table,'复核工作台','frame',.01)
    box('f3_review_pc',(0,.1,1.18),(.59,.06,.36),'dark',table,'复核一体机','shell',.012)
    box('f3_review_pc_stand',(0,.13,.98),(.08,.08,.2),'steel',table,'工作站显示器支架','frame',.005)
    r['unresolved']='内部相机/镜头配置、全部柜内零件与配套放卷收卷设备未取得完整资料；本模型仅对应检测系统，不冒称完整验布卷装线。'
    return r

def machine_calender():
    r=f3_root('calender','teXcal s-roll 双辊轧光机','ANDRITZ','teXcal s-roll','双辊构型；2200 mm辊面为所选配置；外形按当前产品册p14')
    width=2.2
    for side in (-1,1):
        x=side*1.37
        f3_beam(r,'轧光机承压底座',(x,.12,.16),(.42,1.55,.22),'v3_silver')
        for y in (-.45,.70):f3_foot(r,x,y)
        f3_beam(r,'深截面承压侧机架',(x,.32,1.30),(.30,.58,2.25),'dark')
        for z in (.55,2.28):f3_beam(r,'承压机架横向支座',(x,-.05,z),(.34,1.15,.18),'v3_blue')
        for y in (-.25,.30):f3_beam(r,'轴承滑座导向',(x,y,1.48),(.11,.065,1.3),'steel')
        for z in (1.46,1.99):bearing_block(r,(side*1.24,0,z),.17,side,'轧光辊支承轴承箱')
        hydraulic_cylinder(r,(x,0,.66),.35,.10,.23)
    f3_roller(r,'s-roll复合工作辊',0,1.46,.255,width,'rubber')
    f3_roller(r,'镀铬加热钢辊',0,1.99,.245,width,'steel')
    for y,z,rr in ((-.65,1.55,.065),(-.88,.39,.07),(.70,1.70,.065)):
        f3_roller(r,'全幅导布辊',y,z,rr,width)
        for side in (-1,1):f3_beam(r,'导布辊支架',(side*1.25,y,z/2),(.075,.08,z),'v3_silver')
    sh=f3_case(r,'左侧控制与主传动封闭柜',(-1.78,.13,1.25),(.60,1.35,2.2))
    f3_front_door(sh,-1.78,-.57,1.25,.56,2.10,'主机全高控制柜门')
    box('f3_calender_hmi',(-1.78,-.61,1.83),(.37,.025,.30),'glass',sh,'轧光操作触摸屏','shell',.01)
    for z in (.98,1.10):cyl('f3_calender_button',(-1.78,-.64,z),.027,.03,'green' if z<1 else 'red',sh,'操作按钮','y','shell',16)
    f3_beam(r,'整体顶部横梁',(-.12,.30,2.40),(3.62,.45,.11),'v3_white')
    right=f3_case(r,'右侧辊端保护罩',(1.58,.30,1.13),(.22,.84,1.55),'dark',explosion=(.5,.2,0))
    f3_front_door(right,1.58,-.14,1.13,.19,1.44,'辊端维护盖','dark')
    for zz in (1.46,1.99):
        cyl('f3_rotary_union',(1.52,0,zz),.085,.22,'steel',r,'辊端旋转接头','x','frame',32)
        f3_pipe(r,'旋转接头介质软管',[(1.63,0,zz),(1.82,.15,zz),(1.85,.65,zz-.2),(1.85,1.05,.55)],.025,'black')
    box('f3_utility_interface',(1.85,1.11,.55),(.20,.12,.26),'steel',r,'外接介质接口（外围温控系统待配置图）','frame',.008)
    f3_pipe(r,'安全拉绳',[(-1.22,-.73,1.29),(1.22,-.73,1.29)],.009,'red')
    # Preserve a continuous sheet through the nip; no crossing of the roll centre.
    cloth(r,[(1.05,1.78),(.70,1.773),(.35,1.73),(-.35,1.73),(-.65,1.623),(-.88,.463),(-1.12,.32)],2.05,'bluecloth')
    oil=f3_case(r,'独立油站',(-1.65,1.40,.55),(.85,.72,.85))
    f3_front_door(oil,-1.65,1.02,.55,.78,.76,'油站维护门')
    f3_drive(r,(-1.65,1.4,1.13),'油站泵驱动外壳');gauge(r,(-1.28,1.05,.95))
    f3_pipe(r,'油站至主机压力回路',[(-1.30,1.4,.8),(-1.1,1.0,.8),(1.35,1.0,.8),(1.35,.20,.8)],.022,'black')
    r['unresolved']='所选辊面宽在公开范围内；外包络比例及管线走向按照片推定。内部s-roll支承、完整液压及驱动BOM待核实。'
    return r

def f3_wash_web_path(y,length=1.65,through_z=1.67):
    """Tangent web around the four EXISTING wash rolls, in +Y to -Y order.

    This checks the selected model geometry, not an unpublished OEM wet path.
    The 22 mm radial offset clears the one-sided 15 mm display sheet. Horizontal
    leads cross the 130 mm end-wall slots before turning inside the tank.
    """
    radius=.09+.022
    circles=[(y-length*.35+j*length*.70/3,1.45 if j%2==0 else .62)
             for j in reversed(range(4))]
    entry=(y+length/2-.060,through_z)
    exit_point=(y-length/2+.060,through_z)
    incoming=[0.0]*4;outgoing=[0.0]*4
    def point_tangents(point,center):
        dy,dz=point[0]-center[0],point[1]-center[1]
        distance=math.hypot(dy,dz)
        if distance<=radius:raise ValueError('Wash web anchor lies inside a roll')
        phi=math.atan2(dz,dy);a=math.acos(radius/distance)
        return (phi-a,phi+a)
    incoming[0]=max(point_tangents(entry,circles[0]),key=math.cos)
    outgoing[-1]=max(point_tangents(exit_point,circles[-1]),key=math.sin)
    for i in range(3):
        dy=circles[i+1][0]-circles[i][0];dz=circles[i+1][1]-circles[i][1]
        phi=math.atan2(dz,dy);a=math.acos(2*radius/math.hypot(dy,dz))
        # Opposite normals give an internal common tangent: below each low
        # roll and above each high roll, with no straight segment through iron.
        side=-1 if circles[i][1]<1.0 else 1
        angle=max((phi-a,phi+a),key=lambda t:side*math.sin(t))
        outgoing[i]=angle;incoming[i+1]=angle+math.pi
    path=[(y+length/2+.05,through_z),entry]
    for i,(cy,cz) in enumerate(circles):
        start,end=incoming[i],outgoing[i]
        if cz<1.0:
            while end>start:end-=2*math.pi
        else:
            while end<start:end+=2*math.pi
        steps=max(2,math.ceil(abs(end-start)/(math.pi/36)))
        path.extend((cy+radius*math.cos(start+(end-start)*j/steps),
                     cz+radius*math.sin(start+(end-start)*j/steps))
                    for j in range(steps+1))
    path.extend([exit_point,(y-length/2-.05,through_z)])
    return path

def f3_wash_module(r,y,name,width=2.4,length=1.65,height=1.75):
    g=f3_case(r,name,(0,y,height/2+.22),(width+.50,length,height),through_z=1.67)
    for side in (-1,1):panel(g,(side*(width/2+.27),y,height/2+.22),(length-.08,height-.09),side='side',label=name+'侧面维护门',color='v3_silver')
    for side in (-1,1):
        for dy in (-length*.34,length*.34):f3_foot(r,side*(width/2+.12),y+dy)
    for j in range(4):
        yy=y-length*.35+j*length*.70/3
        f3_roller(r,name+'导布辊',yy,1.45 if j%2==0 else .62,.09,width)
    # Separate feed and return manifolds and service ports.
    for z in (.40,1.20):
        f3_pipe(r,name+'配液主管',[(width/2+.38,y-.65,z),(width/2+.38,y+.65,z)],.04)
    valve(r,(width/2+.38,y,.55));gauge(r,(width/2+.4,y-.7,1.2))
    f3_drive(r,(width/2+.55,y,1.45),name+'牵引驱动外壳')
    return g

def machine_pretreatment():
    r=f3_root('pretreatment','BEN-BLEACH 退煮漂模块线','Benninger','BEN-BLEACH / REACTA','INJECTA预处理—EXTRACTA洗涤—IMPACTA浸渍—REACTA—EXTRACTA后洗；模块顺序依据官网，数量为待确认配置')
    width=2.4
    for yy,name in ((7.8,'INJECTA预溶胀'),(5.8,'EXTRACTA预洗'),(3.8,'IMPACTA浸渍'),(-3.8,'EXTRACTA后洗一'),(-5.8,'EXTRACTA后洗二'),(-7.8,'EXTRACTA后洗三')):
        f3_wash_module(r,yy,name,width)
    # Elevated REACTA housing keeps the real high/low line silhouette.
    steam=f3_case(r,'REACTA汽蒸反应箱',(0,0,3.62),(2.95,5.25,2.55),explosion=(0,1.1,0),through_z=4.43)
    for side in (-1,1):
        for yy in (-2.25,0,2.25):
            f3_beam(r,'反应箱承重柱',(side*1.4,yy,1.28),(.16,.18,2.50),'v3_silver');f3_foot(r,side*1.4,yy)
        for yy in (-2.25,-1.5,-.75,0,.75,1.5,2.25):
            for z in (3.00,4.32):
                cyl('f3_steamer_bearing_cover',(side*1.51,yy,z),.095,.055,'v3_blue',r,'汽蒸箱辊端检修盖','x','frame',32)
        for yy in (-1.75,0,1.75):panel(steam,(side*1.50,yy,3.60),(1.65,2.36),side='side',label='反应箱保温检修门',color='v3_silver')
    for yy in (-2.25,-1.5,-.75,0,.75,1.5,2.25):
        for z in (3.00,4.32):f3_roller(r,'反应箱布路导辊',yy,z,.095,width)
    for yy in (-2.25,2.25):f3_beam(r,'上部反应箱横向托梁',(0,yy,2.32),(3.2,.20,.25),'v3_blue')
    for xx in (-1.82,1.82):
        rail_platform(r,(xx,0,2.28),(.60,5.8),1.0)
        for yy in (-2.6,0,2.6):f3_beam(r,'检修平台支柱',(xx,yy,1.15),(.10,.10,2.24),'v3_silver')
    for j in range(10):
        yy=-3.95+j*.23;zz=.20+j*.22
        box('f3_stair',(-1.85,yy,zz),(.68,.27,.055),'steel',r,'检修楼梯踏步','frame',.006)
    f3_pipe(r,'楼梯扶手',[(-2.2,-4.05,1.15),(-2.2,-1.65,3.25)],.025)
    f3_pipe(r,'蒸汽供给总管',[(2.1,-8.5,.4),(2.1,0,.4),(2.1,0,4.7),(1.5,0,4.7)],.06)
    for yy in (-7.8,-5.8,-3.8,0,3.8,5.8,7.8):
        f3_pipe(r,'模块循环/排液接口',[(1.6,yy,.4),(2.10,yy,.4)],.04);valve(r,(2.1,yy,.52))
    for yy in (-1.3,1.3):f3_pipe(r,'反应箱排汽风道',[(0,yy,4.91),(0,yy,5.25),(.7,yy,5.42)],.18)
    # One continuous sheet replaces the former straight strips through all
    # six tanks. Only the existing four rolls in each wash module are wrapped.
    web_path=[(9.0,1.67)]
    for yy in (7.8,5.8,3.8):web_path.extend(f3_wash_web_path(yy))
    # The elevated REACTA transit is explicitly schematic. Do not invent an
    # internal storage/roll-bed configuration without the customer's GA.
    web_path.extend([(2.85,1.67),(2.85,4.43),(2.25,4.43),
                     (-2.25,4.43),(-2.85,4.43),(-2.85,1.67)])
    for yy in (-3.8,-5.8,-7.8):web_path.extend(f3_wash_web_path(yy))
    web_path.append((-9.0,1.67))
    web=cloth(r,web_path,2.20,'cloth')
    web['label']='六洗槽相切包辊布路；REACTA段为示意'
    web['description']='洗槽段按当前四辊几何作相切包覆并经端壁槽口连续连接；REACTA内部储布和单/双辊床路线未获总图，仅显示进出位置与高位通行。'
    web['processPathVerified']=False
    f3_panel_bank(r,2.9,4.7,5);console(r,(2.9,2.8,1.55))
    r['unresolved']='指定订单模块数、REACTA单/双辊床配置及内部布路未获得总图；此整线为公开模块的选定布局，不能作为无遗漏整机。'
    return r

def machine_dyeing():
    r=f3_root('dyeing','Küsters DyePad 冷轧堆染色单元','Benninger','Küsters DyePad / CPB','2200 mm展示幅宽；高进布架、双泳动辊、配液、卷装堆置；水洗为堆置后的独立步骤')
    width=2.2
    for side in (-1,1):
        xx=side*1.38
        f3_beam(r,'轧车整体侧承座',(xx,0,.98),(.38,.88,1.80),'v3_silver')
        for y in (-.30,.30):f3_foot(r,xx,y)
        f3_beam(r,'高进布架立柱',(xx,.55,1.85),(.13,.16,3.35),'v3_silver')
        for zz in (1.02,1.54):bearing_block(r,(side*1.23,0,zz),.16,side,'DyePad泳动辊端支承')
    for y,z,rad in ((1.10,3.45,.08),(.20,3.45,.08),(.45,2.82,.065)):
        f3_roller(r,'高进布/展幅导辊',y,z,rad,width)
        for side in (-1,1):f3_beam(r,'高架悬臂梁',(side*1.38,.6,z),(.13,1.45,.12),'v3_silver')
    for z in (1.02,1.54):f3_roller(r,'DyePad泳动工作辊',0,z,.25,width,'rubber' if z<1.3 else 'steel')
    trough=f3_case(r,'低浴比浸液槽',(0,.63,.80),(2.32,.58,.42),'v3_silver',explosion=(0,-.5,0),open_top=True)
    box('f3_trough_front',(0,.34,.80),(2.32,.035,.42),'v3_silver',trough,'浸液槽前壁','shell',.008)
    f3_roller(r,'浸液导辊',.63,.77,.11,width)
    for x in (-1.12,1.12):
        box('f3_liquor_lid',(x,.63,1.02),(.08,.58,.024),'v3_silver',trough,'浸液槽侧部检修盖','shell',.006)
    f3_beam(r,'下部联接横梁',(0,.15,.30),(2.95,.28,.20),'v3_silver')
    for y in (-.40,.42):
        for z in (1.15,1.44):
            box('f3_nip_guard',(0,y,z),(2.3,.025,.10),'v3_silver',r,'留有穿布口的轧点防护板','shell',.008)
            for j in range(30):box('f3_guard_slot',(-1.09+j*.075,y-.018,z),(.036,.008,.055),'dark',r,'防护板通风孔','shell',.002)
    for side in (-1,1):
        hydraulic_cylinder(r,(side*1.35,0,2.04),.30,.085,.18)
        f3_pipe(r,'泳动辊压力软管',[(side*1.4,.05,1.55),(side*1.60,.22,1.65),(side*1.62,.45,.5)],.026,'black')
    f3_drive(r,(-1.75,0,1.02),'轧辊主驱动外部形体')
    console(r,(1.70,-.55,1.70))
    # Separate mixing / dosing skid, with traceable physical connections.
    skid=empty('f3_liquor_skid',(2.6,1.2,0),r,'染液配制与计量单元','frame')
    f3_beam(skid,'配液单元底架',(0,0,.12),(1.25,1.25,.16),'v3_silver')
    for xx in (-.35,.35):
        cyl('f3_mix_tank',(xx,.15,.70),.24,1.0,'steel',skid,'配液储罐','z','frame',48)
        cyl('f3_mix_lid',(xx,.15,1.22),.25,.04,'steel',skid,'储罐顶盖','z','frame',48)
        f3_pipe(skid,'计量支路',[(xx,.15,.25),(xx,-.45,.25),(xx,-.45,.9)],.025);valve(skid,(xx,-.45,.55))
    f3_pipe(r,'配液至浸槽供液管',[(2.6,.75,.6),(1.85,.75,.6),(1.85,.63,.85),(1.18,.63,.85)],.03)
    # Batch cart is downstream; it is not connected directly to a steam fixation box.
    cart=empty('f3_cpb_batch_cart',(0,-2.6,0),r,'冷轧堆卷装及堆置小车','frame')
    f3_beam(cart,'卷装小车底梁',(0,0,.19),(2.7,1.0,.16),'v3_blue')
    for side in (-1,1):
        f3_beam(cart,'卷装轴支座',(side*1.25,0,.62),(.16,.60,.75),'v3_blue')
        for yy in (-.38,.38):cyl('f3_batch_wheel',(side*1.15,yy,.11),.10,.07,'dark',cart,'堆置车脚轮','x','frame',24)
    f3_roller(cart,'染色卷装',0,.92,.57,width,'bluecloth')
    f3_drive(cart,(1.63,0,.92),'堆置慢转驱动外壳')
    def arc(c,r,a,b,n=24):return [(c[0]+r*math.cos(a+(b-a)*j/n),c[1]+r*math.sin(a+(b-a)*j/n)) for j in range(n+1)]
    c1=(.20,3.45);c2=(.45,2.82);c3=(.63,.77);r1=.081;r2=.066;r3=.123
    # Opposite side tangent from the upper roll to the lower high-frame guide.
    phi=math.atan2(c2[1]-c1[1],c2[0]-c1[0])-math.acos((r1+r2)/math.dist(c1,c2))
    first=arc(c1,r1,math.pi/2,phi+2*math.pi)
    psi=math.atan2(c3[1]-c2[1],c3[0]-c2[0])+math.acos((r2-r3)/math.dist(c2,c3))
    second=arc(c2,r2,phi+math.pi,psi)
    out=(.30,1.28)
    end=math.atan2(out[1]-c3[1],out[0]-c3[0])+math.acos(r3/math.dist(out,c3))-2*math.pi
    dip=arc(c3,r3,psi,end)
    f3_thin_cloth(r,[(1.12,3.531)]+first+second+dip+[out,(-.30,1.28),(-1.4,1.28),(-2.6,1.50)],2.08)
    f3_panel_bank(r,2.50,-1.55,2)
    r['unresolved']='泳动辊内部、压力回路、实际计量配方单元与选定堆置/后洗订单未完整公开；辅助模块外形为布置推定，不宣称厂家完整成套线。'
    return r

def machine_stenter():
    r=f3_root('stenter','MONTEX 六烘房全电拉幅线','Monforts','MONTEX — AEI 2026 reference','6烘房、3.2 m工作幅宽、全电加热、延长进布臂及热回收；依据2026-11-09案例')
    r['verifiedChamberCount']=6;r['verifiedWorkingWidthMetres']=3.2
    width=3.2;outer=4.25;spacing=3.0
    # All six chambers retained. Section length is an estimate until the order GA is available.
    for i in range(6):
        yy=i*spacing;sec=empty('f3_stenter_chamber',parent=r,label='第%d烘房'%(i+1),group='frame')
        sec['chamberIndex']=i+1
        sh=f3_case(sec,'第%d烘房保温箱'%(i+1),(0,yy,1.62),(outer,2.98,2.50),explosion=(0,.9,0),through_z=1.60)
        for side in (-1,1):
            # Broad flush enclosure doors and bottom technical boxes follow the actual installation photos.
            for dy in (-.72,.72):panel(sh,(side*(outer/2+.02),yy+dy,1.62),(1.38,2.35),side='side',label='烘房整高检修门',color='v3_white')
            for dy in (-.90,.90):
                f3_foot(sec,side*1.95,yy+dy)
                f3_beam(sec,'烘房纵向底梁',(side*1.95,yy,.24),(.19,2.95,.22),'v3_silver')
            box('f3_bottom_duct',(side*2.35,yy,.55),(.40,2.25,.60),'v3_silver',sec,'侧下部风路/维护箱','shell',.02)
            f3_drive(sec,(side*2.20,yy,2.48),'循环风机外部驱动')
            cyl('f3_fan_housing',(side*1.93,yy,2.48),.31,.18,'v3_silver',sec,'循环风机检修盖','x','shell',48)
        for z in (1.11,1.96):
            box('f3_air_plenum',(0,yy,z),(3.50,2.75,.18),'v3_silver',sec,'上下循环风分配箱','shell',.02)
            for j in range(9):box('f3_nozzle_rail',(0,yy-1.16+j*.29,z+(.13 if z<1.5 else -.13)),(3.3,.075,.10),'steel',sec,'横向热风喷嘴排（位置待总图核实）','frame',.006)
        f3_pipe(sec,'烘房顶部排湿接口',[(.7,yy,2.90),(.7,yy,3.55)],.19)
    # Extended inlet, pinning point and width-adjustable full chain return.
    y0=-8.0;y1=17.5
    for side in (-1,1):
        x=side*1.64
        for z in (1.52,.99):f3_beam(r,'连续针链工作/回程导轨',(x,(y0+y1)/2,z),(.10,y1-y0,.09),'steel')
        for i in range(256):
            yy=y0+(y1-y0)*i/255
            box('f3_chain_clip',(x,yy,1.58),(.08,.065,.045),'dark',r,'针板链工作段','roller',.004)
            box('f3_chain_return',(x,yy,.99),(.08,.065,.045),'dark',r,'针链下部回程','roller',.004)
        for yy in (y0,y1):
            cyl('f3_chain_sprocket',(x,yy,1.27),.27,.075,'v3_blue',r,'针链端部链轮','x','roller',48)
            f3_beam(r,'链轮轴承支座',(x,yy,.65),(.20,.34,1.0),'v3_blue');f3_foot(r,x,yy)
        for yy in (-6.5,-4.6,-2.6,0,3,6,9,12,15,17.0):
            f3_beam(r,'链轨调幅支座',(x,yy,.80),(.21,.23,.30),'v3_blue')
        for yy in (-6.5,-4.6,-2.6):
            cyl('f3_overfeed_wheel',(x,yy,1.68),.09,.065,'dark',r,'超喂/上针压轮','x','roller',32)
            box('f3_edge_sensor',(x+side*.16,yy,1.76),(.10,.16,.13),'v3_blue',r,'布边跟踪传感头','frame',.006)
    for yy in (-6.5,-4.6,-2.6,0,3,6,9,12,15,17.0):cyl('f3_width_screw',(0,yy,.83),.025,3.8,'steel',r,'横向调幅丝杆','x','frame',24)
    for yy in (-9.8,-8.9):
        f3_roller(r,'入口展幅/牵引辊',yy,1.66,.095,3.35)
        for side in (-1,1):f3_beam(r,'进布架侧柱',(side*1.84,yy,.88),(.18,.19,1.6),'v3_silver');f3_foot(r,side*1.84,yy)
    for zz in (1.63,2.05):f3_roller(r,'入口轧液辊',-10.8,zz,.205,3.35,'rubber')
    for side in (-1,1):
        pad=f3_case(r,'轧车侧箱',(side*1.97,-10.8,1.21),(.42,1.0,2.10))
        f3_foot(r,side*1.97,-11.12);f3_foot(r,side*1.97,-10.47)
        for z in (1.63,2.05):bearing_block(r,(side*1.78,-10.8,z),.15,side,'入口轧辊轴承箱')
    for yy in (18.5,19.3):
        f3_roller(r,'出布冷却导辊',yy,1.55,.12,3.35)
        for side in (-1,1):f3_beam(r,'出布架支撑',(side*1.82,yy,.85),(.14,.16,1.55),'v3_silver');f3_foot(r,side*1.82,yy)
    cloth(r,[(-11.7,1.84),(-11.0,1.84),(-10.6,1.84),(-9.8,1.76),(-8.9,1.76),(-8,1.60),(17.5,1.60),(18.5,1.68),(19.3,1.68),(20,1.0)],3.18,'bluecloth')
    # Six-room air collection to an independently supported heat-recovery unit.
    f3_pipe(r,'排湿汇总风道',[(.7,-1.0,3.55),(.7,16.0,3.55),(3.2,16.0,3.55),(3.2,16.0,2.75)],.25)
    hx=f3_case(r,'集成热回收模块',(3.25,15.7,1.50),(1.55,2.0,2.65),'v3_silver')
    for x in (2.70,3.80):
        for y in (15.0,16.4):f3_foot(r,x,y)
    for j in range(3):f3_front_door(hx,2.75+j*.5,14.68,1.5,.47,2.5,'热回收器检修门','v3_silver')
    f3_panel_bank(r,3.0,-5.5,6);console(r,(2.35,-9.0,1.65))
    # The floor-level yellow maintenance aisle follows the current AEI photo.
    for side in (-1,1):
        box('f3_service_aisle',(side*2.90,7.5,.14),(.65,18.5,.12),'yellow',r,'连续侧面检修走道','frame',.012)
        for yy in (-1.5,1.5,4.5,7.5,10.5,13.5,16.5):f3_pipe(r,'走道栏杆立柱',[(side*3.20,yy,.2),(side*3.20,yy,1.15)],.022)
        f3_pipe(r,'走道连续扶手',[(side*3.20,-1.5,1.15),(side*3.20,16.5,1.15)],.025)
    r['unresolved']='六房、3.2m、全电、长入口与热回收有案例依据；房长、风机/喷嘴/针链节距及实际电控内部未获厂家总图，几何布置仍需核验。'
    return r
