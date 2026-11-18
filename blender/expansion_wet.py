"""Public-reference continuous wet finishing ranges, metres / Blender Z-up.

Executed by the expansion builder with B/C/T/P, empty, M, mat, motor and load.
Manufacturer documents establish functional modules, not an OEM motor BOM.
All motor positions, mechanical couplings and un-dimensioned geometry are
explicit functional reconstructions; the complete selected modules are kept.
"""

M['wet_blue'] = mat('Wet finishing blue-grey enamel', (.16,.30,.39), .40,.34)
M['wet_grey'] = mat('Wet finishing insulated enclosure', (.63,.68,.69), .55,.38)
M['wet_water'] = mat('Visible process bath', (.13,.43,.49), .12,.26)
M['wet_felt'] = mat('Industrial felt blanket', (.59,.50,.36), .02,.87)
M['wet_fabric'] = mat('Finishing fabric path', (.77,.49,.18), .02,.78)


def _wet_node(parent, name, label, loc=(0,0,0), shell=False):
    n=empty(name,loc,parent,label,'shell' if shell else 'frame')
    n['evidenceStatus']='inferred_geometry'
    return n


def _wet_web(parent, name, points, width=1.86, material='wet_fabric', label='连续平幅布路'):
    """A broad cloth ribbon, with separate fine selvedge traces for legibility."""
    verts=[]
    for x,z in points: verts.extend([(x,-width/2,z),(x,width/2,z)])
    faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    me.materials.append(M[material])
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.parent=parent
    ob['label']=label;ob['group']='material';ob['evidenceStatus']='inferred_geometry'
    ob['materialPath']=True
    for side in [-1,1]:
        P(parent,name+'_selvedge',[(x,side*width*.5,z+.003) for x,z in points],.005,'cloth',label+'布边','material')
    return ob


def _wet_arc(x,z,r,start,end,n=12):
    return [(x+r*math.cos(start+(end-start)*i/n),z+r*math.sin(start+(end-start)*i/n)) for i in range(n+1)]


def _wet_frame(parent, key, x, length, height=1.9, width=2.28, color='wet_grey', roof=True):
    g=_wet_node(parent,key+'_frame','模块机架与密封检修罩',(x,0,0))
    for xx in [-length/2+.07,length/2-.07]:
        for yy in [-width/2,width/2]:
            B(g,'wet_column',(xx,yy,height*.5),(.075,.075,height),color,'框架立柱')
            B(g,'wet_foot',(xx,yy,.045),(.20,.19,.07),'dark','调平底脚')
            for dx in [-.06,.06]:C(g,'wet_foot_bolt',(xx+dx,yy,.09),.017,.03,'steel','z','地脚紧固螺栓','frame',6)
    for yy in [-width/2,width/2]:
        for zz in [.28,height-.10]:B(g,'wet_crossbeam',(0,yy,zz),(length,.075,.09),color,'模块纵向机梁')
    B(g,'wet_bath',(0,0,.42),(length-.08,width-.12,.20),'steel','不锈钢槽底与液体收集区')
    B(g,'wet_bath_front',(0,-width*.48,.65),(length-.12,.045,.36),color,'前下槽壁','shell')
    B(g,'wet_bath_back',(0,width*.48,height*.56),(length-.12,.045,height*.72),color,'后部保温侧板','shell')
    for xx in [-length*.34,0,length*.34]:
        B(g,'wet_inspection_rim',(xx,-width*.50,height*.61),(length*.27,.048,.48),'steel','检修窗压框','shell',.018)
        B(g,'wet_inspection_glass',(xx,-width*.515,height*.61),(length*.235,.018,.39),'glass','检修观察窗','shell',.014)
        B(g,'wet_inspection_handle',(xx+length*.105,-width*.535,height*.61),(.024,.038,.14),'dark','检查门把手','shell',.004)
    if roof:
        for xx in [-length*.25,length*.25]:
            panel=_wet_node(g,'wet_hinged_roof','分体翻起检修顶盖',(xx,0,height),True)
            panel['explode']=[0,.48,0]
            B(panel,'wet_lid',(0,0,0),(length*.49,width+.035,.045),color,'密封保温顶盖','shell')
            for yy in [-.73,.73]:P(panel,'wet_lid_handle',[(-.12,yy,.03),(-.12,yy,.08),(.12,yy,.08),(.12,yy,.03)],.013,'dark','顶盖拉手','shell')
    return g


def _wet_roller(parent, key, label, x,z,r=.115,width=2.08, material='steel',speed=1):
    a=load(parent,key,label,(x,0,z),motion='rotate:z',speed=speed)
    C(a,'wet_working_roller',(0,0,0),r,width,material,'y',label,'roller',40)
    for side in [-1,1]:
        C(a,'wet_roll_end',(0,side*(width*.5+.015),0),r*.88,.03,'steel','y','辊体端面','roller',32)
        C(a,'wet_journal',(0,side*(width*.5+.09),0),r*.25,.18,'steel','y','外置轴颈','roller',20)
        C(parent,'wet_bearing',(x,side*(width*.5+.13),z),r*.42,.065,'dark','y','湿区外置轴承座','frame',24)
    B(a,'wet_roll_motion_mark',(0,-width*.44,r*.997),(.024,.09,.006),'orange','辊面运动观察标记','roller',.001)
    return a


def _wet_drive(parent, key, label, x,z=1.65, style='gear'):
    motor(parent,key,label,(x,-1.61,z),axis='y',radius=.105,length=.28,style=style)
    gear=load(parent,key+'_gear',label+'减速输出示意',(x,-1.25,z))
    B(gear,'wet_gearbox',(0,0,0),(.28,.19,.32),'wet_blue','减速机外壳示意','transmission',.035)
    C(gear,'wet_coupling',(0,.15,0),.063,.16,'steel','y','工作轴联接示意','transmission',24)
    for xx in [-.1,.1]:
        for zz in [-.12,.12]:C(gear,'wet_case_bolt',(xx,-.11,zz),.013,.025,'steel','y','减速机盖紧固件','transmission',6)


def _wet_pump(parent,key,label,x,y=-1.72,z=.46,pipe_to=None):
    motor(parent,key,label,(x-.22,y,z),axis='x',radius=.085,length=.24,style='industrial')
    p=load(parent,key+'_pump',label+'泵头',(x+.07,y,z),motion='rotate:x',speed=1.4)
    C(p,'wet_pump_head',(0,0,0),.145,.15,'steel','x',label+'离心泵工作轴','pump',32)
    T(p,'wet_pump_flange',(.09,0,0),.118,.014,'steel','x','泵体连接法兰','pump')
    B(parent,'wet_pump_skid',(x-.04,y,z-.20),(.66,.42,.07),'wet_blue','泵组公共底座')
    q=pipe_to or (x+.08,-.50,1.45)
    P(parent,'wet_liquor_pipe',[(x+.08,y,z+.14),(x+.08,y,z+.38),(q[0],y,q[2]),q],.035,'steel',label+'循环管路','pipe')
    for zz in [z+.32]:
        C(parent,'wet_valve',(x+.08,y,zz),.068,.065,'steel','z','管路阀体（非电机）')
        T(parent,'wet_handwheel',(x+.08,y,zz+.16),.07,.009,'wet_blue','z','手动阀门手轮')


def _wet_batch(parent,key,x,roll_radius=.57,out=False):
    a=_wet_roller(parent,key+'_roll','出布卷装' if out else '进布大卷',x,.73,roll_radius,1.98,'cloth',.20)
    for side in [-1,1]:
        B(parent,'wet_batch_stand',(x,side*1.19,.36),(.12,.13,.72),'wet_blue','卷装轴承支架')
        P(parent,'wet_batch_brace',[(x-.42,side*1.19,.09),(x,side*1.19,.66),(x+.42,side*1.19,.09)],.035,'steel','三角卷架支撑')
    _wet_drive(parent,key+'_motor','出布卷绕' if out else '进布退卷',x,.73)
    return a


def _wet_control(parent,x,y=-2.05):
    B(parent,'wet_hmi_stand',(x,y,.70),(.08,.08,1.35),'steel','触控操作台立柱')
    B(parent,'wet_hmi_case',(x,y,1.48),(.58,.17,.43),'wet_grey','操作终端外壳','shell',.025)
    B(parent,'wet_hmi_glass',(x,y-.091,1.50),(.46,.015,.28),'glass','工艺参数触摸屏','frame',.014)
    C(parent,'wet_estop',(x+.20,y-.11,1.32),.035,.025,'orange','y','急停按钮','frame',24)


def _wet_open_stand(parent,x,height):
    """Bearing pedestals for exposed line-end rollers outside a wet compartment."""
    for side in [-1,1]:
        y=side*1.20
        B(parent,'wet_open_pedestal',(x,y,height*.5),(.10,.12,height),'wet_grey','外置导布辊支承立柱')
        B(parent,'wet_open_foot',(x,y,.06),(.44,.26,.10),'dark','开放辊架底脚')
        P(parent,'wet_open_brace',[(x-.22,y,.10),(x,y,height*.60),(x+.22,y,.10)],.025,'steel','辊架斜撑')
    B(parent,'wet_open_tie',(x,0,.24),(.10,2.42,.10),'wet_grey','辊架下横梁')


def _wet_extracta(parent,key,x,press=True):
    _wet_frame(parent,key,x,2.10,2.15)
    # EA single-loop selection: five complete immersion loops, not a truncated sample.
    points=[(x-1.14,1.78)]
    for n in range(5):
        xx=x-.77+n*.345
        _wet_roller(parent,f'{key}_upper_{n+1:02d}','EXTRACTA 上导布辊',xx,1.77,.10)
        _wet_roller(parent,f'{key}_lower_{n+1:02d}','EXTRACTA 浸液下辊',xx+.15,.73,.10)
        if press:_wet_roller(parent,f'{key}_press_{n+1:02d}','分格挤液压辊',xx,1.96,.085,material='black',speed=-1)
        points+=_wet_arc(xx,1.77,.105,math.pi,0,8)
        points+=_wet_arc(xx+.15,.73,.105,math.pi,2*math.pi,8)
    points.append((x+1.12,1.78))
    _wet_web(parent,key+'_fabric',points)
    for n in range(4):B(parent,'extracta_partition',(x-.50+n*.345,0,.68),(.025,2.11,.42),'steel','逆流分格隔板')
    _wet_drive(parent,key+'_motor','EXTRACTA 分段导布',x+.69,1.78)
    _wet_pump(parent,key+'_circulation','洗液循环',x-.55,pipe_to=(x-.60,-.60,1.55))
    P(parent,'extracta_counterflow',[(x+.92,1.29,.76),(x-.92,1.29,.76)],.035,'steel','逐格逆流洗液通道','pipe')


def _wet_trikoflex(parent,key,x):
    _wet_frame(parent,key,x,1.90,2.32)
    _wet_roller(parent,key+'_drum_01','TRIKOFLEX 上洗涤转鼓',x-.14,1.64,.43,2.08)
    _wet_roller(parent,key+'_drum_02','TRIKOFLEX 下洗涤转鼓',x+.13,.80,.38,2.08,speed=-1.1)
    for n,(xx,zz) in enumerate([(x-.80,.66),(x+.69,1.91),(x+.73,1.62)]):
        _wet_roller(parent,f'{key}_guide_{n+1:02d}','转鼓洗涤导布辊',xx,zz,.075)
    pts=[(x-.96,1.77),(x-.87,.66)]+_wet_arc(x+.13,.8,.39,math.pi,2*math.pi,14)
    pts+=_wet_arc(x-.14,1.64,.44,-.12*math.pi,math.pi*.95,16)+[(x+.74,1.77),(x+.98,1.78)]
    _wet_web(parent,key+'_fabric',pts)
    for z in [1.97,1.00]:
        B(parent,'triko_overflow_blade',(x-.31,0,z),(.22,2.12,.045),'steel','正反面洗涤溢流刃口','pipe')
        P(parent,'triko_supply',[(x-.31,1.25,.50),(x-.31,1.25,z),(x-.31,.6,z)],.038,'steel','转鼓喷淋供液','pipe')
    _wet_drive(parent,key+'_motor','TRIKOFLEX 转鼓导布',x-.14,1.64)
    _wet_pump(parent,key+'_circulation','转鼓洗涤循环',x+.39,pipe_to=(x-.31,-.40,1.97))


def build_washing_range(root):
    root['selectedModuleCounts']='2 TRIKOFLEX + 3 EXTRACTA EA + 1 TEMPACTA; no cylinder dryer in selected brochure combined line'
    _wet_batch(root,'WASH_entry',-11.0)
    _wet_roller(root,'WASH_inlet_pull','进布牵引辊',-9.9,2.18,.14)
    _wet_open_stand(root,-9.9,2.18)
    _wet_drive(root,'WASH_inlet_motor','进布牵引',-9.9,2.18)
    _wet_web(root,'WASH_entry_web',[(-11.0,1.31),(-9.9,2.33),(-9.55,1.78)])
    _wet_trikoflex(root,'WASH_TRIKO_01',-8.5)
    _wet_extracta(root,'WASH_EXTRACTA_01',-6.25)
    _wet_extracta(root,'WASH_EXTRACTA_02',-3.80)
    for a,b in [(-7.52,-7.39),(-5.13,-4.94),(-2.68,-2.30)]:_wet_web(root,'WASH_intermodule',[(a,1.78),(b,1.78)])
    # TEMPACTA dwell unit: full selected conveyor, entrance tower and outlet tower.
    _wet_frame(root,'WASH_TEMPACTA',.20,4.85,2.12)
    for x in [-2.05,2.45]:
        for y in [-1.12,1.12]:B(root,'tempacta_tower',(x,y,1.43),(.09,.09,2.86),'wet_grey','停留段高位进出布立架')
    _wet_roller(root,'WASH_tempacta_inlet','TEMPACTA 高位入布辊',-2.05,2.68,.13)
    _wet_roller(root,'WASH_tempacta_outlet','TEMPACTA 出布牵引辊',2.45,2.13,.13)
    dwell=load(root,'WASH_tempacta_conveyor','TEMPACTA 托布输送段',(.20,0,.80))
    B(dwell,'tempacta_belt',(0,0,0),(4.12,1.99,.035),'dark','湿布托带','roller')
    for n in range(12):_wet_roller(root,f'WASH_tempacta_support_{n+1:02d}','托布输送支承辊',-1.85+n*.37,.75,.045,1.99)
    for n,x in enumerate([-1.85,2.23]):_wet_roller(root,f'WASH_tempacta_end_{n+1:02d}','托布输送端辊',x,.78,.09)
    _wet_web(root,'WASH_tempacta_web',[(-2.30,1.78),(-2.05,2.82),(-1.84,.91)]+[(-1.84+i*.064,.91+.055*math.sin(i*math.pi/2)) for i in range(64)]+[(2.23,1.10),(2.45,2.27),(2.75,1.78)])
    for x in [-1.4,-.4,.6,1.6]:P(root,'tempacta_spray',[(x,-1.20,1.88),(x,1.20,1.88)],.022,'steel','停留段上部喷淋管','pipe')
    _wet_drive(root,'WASH_tempacta_feed_motor','停留段入布',-2.05,2.68)
    _wet_drive(root,'WASH_tempacta_transport_motor','停留段托布输送',2.23,.78)
    _wet_drive(root,'WASH_tempacta_exit_motor','停留段出布',2.45,2.13)
    _wet_pump(root,'WASH_tempacta_circulation','皂洗液循环',.20,pipe_to=(.20,-.3,1.88))
    _wet_trikoflex(root,'WASH_TRIKO_02',3.85)
    _wet_extracta(root,'WASH_EXTRACTA_03',6.10)
    _wet_web(root,'WASH_to_triko',[(2.75,1.78),(2.87,1.78)])
    _wet_web(root,'WASH_to_lastwash',[(4.83,1.78),(4.96,1.78)])
    for n,z in enumerate([1.70,1.99]):_wet_roller(root,f'WASH_final_nip_{n+1:02d}','末端轧液辊',7.70,z,.14,material='black',speed=1 if n==0 else -1)
    _wet_open_stand(root,7.70,2.08)
    _wet_drive(root,'WASH_final_motor','末端轧液',7.70,1.70)
    _wet_batch(root,'WASH_exit',9.25,out=True)
    _wet_web(root,'WASH_exit_web',[(7.22,1.78),(7.70,1.846),(8.25,2.15),(9.25,1.31)])
    _wet_control(root,8.45)


def _wet_horizontal_treatment(parent,key,x,length=3.15,label='无链浸渍辊组'):
    _wet_frame(parent,key,x,length,1.52)
    pts=[(x-length/2-.12,1.31)]
    for n in range(6):
        xx=x-length*.42+n*length*.16
        _wet_roller(parent,f'{key}_upper_{n+1:02d}',label+'上辊',xx,1.25,.17)
        _wet_roller(parent,f'{key}_lower_{n+1:02d}',label+'下辊',xx+.18,.97,.14,speed=-1.1)
        pts+=_wet_arc(xx,1.25,.174,math.pi*.88,0,9)
        pts+=_wet_arc(xx+.18,.97,.144,math.pi,math.pi*1.95,9)
    pts.append((x+length/2+.12,1.31));_wet_web(parent,key+'_web',pts)
    _wet_drive(parent,key+'_motor',label,x+length*.36,1.25)
    _wet_pump(parent,key+'_circulation',label+'碱液循环',x-.70,pipe_to=(x,-.4,1.30))


def build_mercerizing(root):
    root['selectedModuleCounts']='double impregnation, two controlled dwell fields, clip stenter, two stabilization fields, two TRIKOFLEX afterwash modules'
    _wet_batch(root,'MERC_entry',-12.0)
    _wet_roller(root,'MERC_inlet_pull','进布牵引辊',-10.8,2.18,.14)
    _wet_open_stand(root,-10.8,2.18)
    _wet_drive(root,'MERC_inlet_motor','进布牵引',-10.8,2.18)
    _wet_web(root,'MERC_entry_web',[(-12,1.31),(-10.8,2.33),(-10.2,1.31)])
    # Two compact impregnation/dwell compartments, as the brochure permits.
    _wet_horizontal_treatment(root,'MERC_impregnation_01',-8.45,label='第一浸渍停留区')
    _wet_horizontal_treatment(root,'MERC_impregnation_02',-4.95,label='第二浸渍停留区')
    _wet_web(root,'MERC_impregnation_join',[(-6.755,1.31),(-6.645,1.31)])
    for n,(xx,zz) in enumerate([(-2.95,1.30),(-2.67,1.09),(-2.39,1.30)]):_wet_roller(root,f'MERC_compensator_{n+1:02d}','浸渍后张力补偿导布辊',xx,zz,.11)
    _wet_open_stand(root,-2.95,1.30)
    _wet_open_stand(root,-2.39,1.30)
    _wet_web(root,'MERC_compensator_web',[(-3.255,1.31),(-2.95,1.41),(-2.67,.98),(-2.39,1.41),(-2.1,1.41)])
    # Integrated short clip stenter is a real part of DIMENSA, not a hot-air oven.
    _wet_frame(root,'MERC_clip',.0,4.2,1.25,roof=False)
    for side in [-1,1]:
        rail=load(root,'MERC_chain_'+('L' if side<0 else 'R'),'丝光展幅夹链轨道',(0,side*1.02,1.42))
        B(rail,'mercer_chain_rail',(0,0,0),(4.20,.11,.10),'wet_blue','左右独立夹链导轨')
        for n in range(36):
            xx=-2.04+n*.116
            B(rail,'mercer_chain_link',(xx,0,.07),(.083,.072,.035),'steel','连续夹链链节','transmission',.006)
            B(rail,'mercer_clip_jaw',(xx,-side*.052,.09),(.050,.078,.020),'dark','夹持布边钳口','transmission',.003)
        for end in [-1,1]:
            a=load(root,'MERC_chain_'+('L' if side<0 else 'R')+('_in' if end<0 else '_out'),'夹链链轮',(end*2.0,side*1.02,1.42),motion='rotate:y',speed=side)
            C(a,'mercer_chain_sprocket',(0,0,0),.13,.08,'steel','z','夹链水平链轮','transmission',32)
        motor(root,'MERC_chain_motor_'+('L' if side<0 else 'R'),'左侧夹链驱动' if side<0 else '右侧夹链驱动',(1.96,side*1.31,1.67),axis='z',radius=.09,length=.26,style='gear')
    for n,x in enumerate([-1.5,0,1.5]):
        a=load(root,f'MERC_width_screw_{n+1:02d}','夹链幅宽调节横丝杆',(x,0,1.10),motion='rotate:z',speed=.3)
        C(a,'mercer_width_screw',(0,0,0),.023,2.57,'steel','y','调幅横向丝杆','transmission',20)
        motor(root,f'MERC_width_motor_{n+1:02d}','调幅驱动示意',(x,-1.46,1.10),axis='y',radius=.055,length=.15,style='gear')
    _wet_web(root,'MERC_stenter_web',[(-2.10,1.46),(2.10,1.46)],1.94)
    for side in [-1,1]:
        section=load(root,'MERC_section_'+('L' if side<0 else 'R'),'SECTION CONTROL 布边机械伸展器',(1.65,side*.94,1.46))
        for n in range(3):C(section,'mercer_section_wheel',(-.2+n*.20,0,.04),.078,.045,'dark','z','布边局部伸展压轮','roller',24)
    # Vacuum slot is distinct from the weak-lye spraying circuit.
    vacuum=load(root,'MERC_vacuum_slot','真空抽碱狭缝',(2.28,0,1.38))
    B(vacuum,'mercer_vacuum_bar',(0,0,0),(.12,2.08,.10),'steel','全幅抽碱吸口','pipe')
    _wet_pump(root,'MERC_vacuum_motor','真空抽碱动力示意',2.42,y=-2.03,pipe_to=(2.28,-.3,1.38))
    _wet_horizontal_treatment(root,'MERC_stabilizing_01',4.15,2.95,'第一稳定水洗区')
    _wet_horizontal_treatment(root,'MERC_stabilizing_02',7.40,2.95,'第二稳定水洗区')
    _wet_web(root,'MERC_stable_join',[(5.745,1.31),(5.805,1.31)])
    _wet_web(root,'MERC_clip_exit',[(2.10,1.46),(2.28,1.44),(2.555,1.31)])
    _wet_trikoflex(root,'MERC_wash_01',10.15)
    _wet_trikoflex(root,'MERC_wash_02',12.37)
    _wet_web(root,'MERC_afterwash_entry',[(8.995,1.31),(9.19,1.77)])
    _wet_web(root,'MERC_afterwash_join',[(11.13,1.78),(11.39,1.78)])
    for n,z in enumerate([1.69,1.98]):_wet_roller(root,f'MERC_final_nip_{n+1:02d}','丝光后洗末端轧液辊',13.73,z,.14,material='black',speed=1 if n==0 else -1)
    _wet_open_stand(root,13.73,2.08)
    _wet_drive(root,'MERC_final_motor','后洗轧液',13.73,1.69)
    _wet_batch(root,'MERC_exit',15.25,out=True)
    _wet_web(root,'MERC_final_web',[(13.35,1.78),(13.73,1.835),(14.22,1.78),(15.25,1.31)])
    # Compact lye preparation below impregnation: no fictitious remote storage farm.
    B(root,'mercer_preparation_tank',(-8.45,0,.28),(1.60,1.62,.40),'steel','浸渍槽下碱液配制箱')
    for x in [-9.2,-7.7]:
        C(root,'mercer_filter',(x,-1.70,.87),.12,.45,'steel','z','碱液过滤器')
        C(root,'mercer_filter_lid',(x,-1.70,1.11),.145,.035,'steel','z','过滤器快开盖')
    _wet_control(root,-1.95)


def _wet_scray(parent,key,x):
    for y in [-1.15,1.15]:
        for xx in [x-.65,x+.65]:B(parent,'sanfor_scray_post',(xx,y,1.47),(.08,.08,2.94),'wet_grey','高位储布架立柱')
    _wet_roller(parent,key+'_top','储布架上牵引辊',x-.62,2.80,.12)
    _wet_roller(parent,key+'_bottom','气动摆辊',x+.25,1.18,.10)
    for y in [-1.16,1.16]:P(parent,'sanfor_scray_arm',[(x+.65,y,2.50),(x+.25,y,1.18)],.025,'wet_blue','摆辊摆臂（气动加载）')
    trough=[(x-.80,.92),(x-.68,.42),(x+.57,.42),(x+.78,.92)]
    _wet_web(parent,key+'_trough',trough,2.16,'steel','储布槽不锈钢曲面')
    _wet_web(parent,key+'_pile',[(x-.60+i*.04,.47+.08*math.sin(i*math.pi/2)) for i in range(30)],1.88,'wet_fabric','储布槽内连续折叠布层')
    _wet_drive(parent,key+'_motor','储布区牵引',x-.62,2.80)


def build_sanforizing(root):
    root['selectedModuleCounts']='entry scray, steamer drum, single rubber belt unit, 1500 mm felt calender, two cooling drums, exit scray and batcher; selected optional grinding dust extraction'
    _wet_batch(root,'SAN_entry',-8.40)
    _wet_scray(root,'SAN_entry_scray',-6.70)
    _wet_web(root,'SAN_entry_web',[(-8.4,1.31),(-7.32,2.93),(-7.22,.61),(-6.20,.61),(-6.45,1.29),(-5.85,2.36)])
    steam=_wet_roller(root,'SAN_steam_drum','蒸汽润湿滚筒',-5.18,1.80,.58)
    _wet_frame(root,'SAN_steamer',-5.18,1.45,2.55,roof=False)
    _wet_drive(root,'SAN_steam_motor','蒸汽滚筒输布示意',-5.18,1.80)
    P(root,'sanfor_steam_pipe',[(-5.18,1.38,.20),(-5.18,1.38,1.80),(-5.18,.8,1.80)],.06,'steel','蒸汽管与旋转接头','pipe')
    _wet_web(root,'SAN_steam_web',_wet_arc(-5.18,1.80,.586,math.pi*.92,-.14*math.pi,22)+[(-3.85,1.55)])
    _wet_frame(root,'SAN_rubber_unit',-2.20,3.05,2.45,color='wet_blue',roof=False)
    for side in [-1,1]:
        B(root,'sanfor_heavy_sideplate',(-2.20,side*1.16,1.30),(2.95,.075,1.62),'wet_blue','橡毯预缩主机厚侧板','shell',.06)
        for x in [-3.23,-1.17]:C(root,'sanfor_inspection_port',(x,side*1.208,1.56),.22,.02,'steel','y','圆形轴承检修面板','shell',40)
    _wet_roller(root,'SAN_shrink_cylinder','蒸汽加热预缩大滚筒',-2.18,1.64,.66,2.10)
    _wet_roller(root,'SAN_press_roller','橡毯压缩辊',-3.07,1.39,.27,2.10,material='black',speed=-1.8)
    _wet_roller(root,'SAN_tension_roller','橡毯张紧辊',-1.28,1.10,.26,2.10,material='black',speed=-1.7)
    _wet_roller(root,'SAN_return_roller','橡毯回程辊',-2.24,.48,.22,2.10,material='black',speed=-1.8)
    belt=load(root,'SAN_rubber_blanket','完整循环橡毯',(-2.18,0,0))
    beltpts=_wet_arc(-.89,1.39,.29,math.pi*.86,math.pi*1.65,16)+_wet_arc(-.06,.48,.24,math.pi*1.20,math.pi*1.83,12)+_wet_arc(.90,1.10,.28,-math.pi*.50,math.pi*.35,12)+_wet_arc(0,1.64,.68,-.08*math.pi,-.95*math.pi,22)
    beltpts.append(beltpts[0]);_wet_web(belt,'sanfor_rubber_blanket',beltpts,2.12,'black','预缩工作面与橡毯完整回路')
    _wet_web(root,'SAN_shrink_web',[(-3.85,1.55),(-3.30,1.65)]+_wet_arc(-2.18,1.64,.672,math.pi*.93,math.pi*1.95,28)+[(-.90,1.65)])
    _wet_drive(root,'SAN_rubber_motor','橡毯循环驱动示意',-1.28,1.10)
    _wet_drive(root,'SAN_cylinder_motor','预缩滚筒驱动示意',-2.18,1.64)
    _wet_roller(root,'SAN_grinding_roller','内置磨毯辊',-2.15,.17,.10,2.14,'dark',2.3)
    _wet_drive(root,'SAN_grinding_motor','橡毯内置磨削',-2.15,.17)
    _wet_pump(root,'SAN_cooling_pump','橡毯冷却水循环',-3.23,y=-2.01,pipe_to=(-2.25,-.20,.71))
    for x in [-2.65,-1.82]:P(root,'sanfor_cooling_spray',[(x,-1.05,.69),(x,1.05,.69)],.025,'steel','橡毯冷却喷淋管','pipe')
    # Felt calender: selected published 1500 mm cylinder option with full blanket return.
    _wet_frame(root,'SAN_felt_unit',1.42,2.80,2.72,color='wet_grey',roof=False)
    _wet_roller(root,'SAN_felt_cylinder','1500 mm 毛毯烘筒',1.40,1.64,.75,2.10)
    _wet_roller(root,'SAN_felt_tension','毛毯张紧回程辊',1.42,.46,.20,2.10)
    _wet_roller(root,'SAN_felt_entry','毛毯入口导辊',.30,1.31,.18,2.10)
    _wet_roller(root,'SAN_felt_exit','毛毯出口导辊',2.50,1.31,.18,2.10)
    felt=load(root,'SAN_felt_blanket','完整毛毯循环带',(0,0,0))
    feltpts=_wet_arc(.30,1.31,.20,math.pi*.65,math.pi*1.45,12)+_wet_arc(1.42,.46,.22,math.pi*1.13,math.pi*1.86,12)+_wet_arc(2.50,1.31,.20,math.pi*1.5,math.pi*2.35,12)+_wet_arc(1.40,1.64,.769,.0*math.pi,1.0*math.pi,30)
    feltpts.append(feltpts[0]);_wet_web(felt,'sanfor_felt_blanket',feltpts,2.13,'wet_felt','毛毯包覆烘筒及返回路径')
    _wet_web(root,'SAN_felt_web',[(-.90,1.65),(.25,1.59)]+_wet_arc(1.40,1.64,.757,math.pi,0,28)+[(2.68,1.55)])
    _wet_drive(root,'SAN_felt_motor','毛毯烘筒驱动示意',1.40,1.64)
    P(root,'sanfor_felt_steam',[(1.40,1.43,.25),(1.40,1.43,1.64),(1.40,1.14,1.64)],.06,'steel','烘筒蒸汽供给与凝水接口','pipe')
    for n,(x,z) in enumerate([(3.55,1.80),(4.45,1.22)]):
        _wet_roller(root,f'SAN_cooling_drum_{n+1:02d}','出布水冷滚筒',x,z,.38,2.10)
        _wet_open_stand(root,x,z)
    _wet_drive(root,'SAN_cooling_drive','冷却区导布驱动示意',4.45,1.22)
    _wet_web(root,'SAN_cool_web',[(2.68,1.55)]+_wet_arc(3.55,1.80,.386,math.pi,0,18)+_wet_arc(4.45,1.22,.386,math.pi,2*math.pi,18)+[(5.18,2.93)])
    _wet_scray(root,'SAN_exit_scray',5.80)
    _wet_batch(root,'SAN_exit',8.05,out=True)
    _wet_web(root,'SAN_exit_web',[(5.18,2.93),(5.26,.61),(6.35,.61),(6.05,1.29),(6.80,1.95),(8.05,1.31)])
    # Optional grinding extraction is explicitly selected, separate from production airflow.
    motor(root,'SAN_dust_motor','磨毯粉尘抽吸示意',(-.37,-2.22,.57),axis='x',radius=.12,length=.31,style='industrial')
    fan=load(root,'SAN_dust_fan','选配磨毯除尘风机',(-.05,-2.22,.57),motion='rotate:x',speed=2)
    C(fan,'sanfor_dust_fan',(0,0,0),.28,.20,'wet_blue','x','除尘风机叶轮工作区','fan',40)
    P(root,'sanfor_dust_duct',[(-2.15,-.95,.18),(-2.15,-1.93,.18),(-.05,-1.93,.57)],.09,'steel','磨毯吸屑管','pipe')
    C(root,'sanfor_filter_vessel',(.35,-2.22,1.20),.27,.86,'wet_grey','z','磨屑过滤筒','shell',40)
    _wet_control(root,-.20,-2.88)


BUILDERS={'washing_range':build_washing_range,'mercerizing':build_mercerizing,'sanforizing':build_sanforizing}
