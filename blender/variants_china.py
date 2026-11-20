"""Independent Chinese equipment reconstructions, checked 2026-11-20.
Uses the common expansion geometry/drive interface. No export side effects.
Public dimensions and selected configurations are recorded in variants-china.json.
"""

def _vc_materials():
    for k,c,m,r in [('vc_white',(.76,.79,.78),.2,.42),('vc_green',(.25,.55,.12),.2,.40),('vc_blue',(.02,.36,.55),.32,.34),('vc_navy',(.12,.25,.31),.3,.40),('vc_steel',(.60,.65,.67),.8,.28),('vc_dark',(.035,.045,.05),.25,.4),('vc_can',(.69,.77,.79),.22,.43),('vc_sliver',(.89,.86,.72),0,.9),('vc_yarn',(.75,.48,.13),0,.8),('vc_screen',(.025,.12,.16),.1,.3),('vc_brass',(.56,.42,.19),.62,.3)]:
        if k not in M:M[k]=mat(k,c,m,r)

def _vc_mesh(parent,name,vs,fs,ma,label,group='frame'):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(M[ma])
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.parent=parent;o['label']=label;o['group']=group
    return o

def _vc_beam(parent,name,a,b,w=.035,ma='vc_steel',label='结构支承'):
    a,b=Vector(a),Vector(b);o=B(parent,name,tuple((a+b)/2),(w,w,(b-a).length),ma,label,'frame',w*.12)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def _vc_belt(parent,id,a,b,r=.06,width=.018):
    # Equal-radius visible belt loop; sizes are selected geometry, not a tooth specification.
    g=load(parent,id,'闭合带传动区段',(0,0,0));ax,y,az=a;bx,_,bz=b;theta=math.atan2(bz-az,bx-ax)
    pts=[]
    for x,z,start in [(ax,az,theta+math.pi/2),(bx,bz,theta-math.pi/2)]:
        for j in range(25):
            t=start+j*math.pi/24;pts.append((x+r*math.cos(t),y,z+r*math.sin(t)))
    vs=[(x,yy+d,z) for x,yy,z in pts for d in (-width/2,width/2)]
    fs=[(2*j,2*j+1,2*((j+1)%len(pts))+1,2*((j+1)%len(pts))) for j in range(len(pts))]
    _vc_mesh(g,id+'_web',vs,fs,'vc_dark','闭合传动带','roller')
    for x,yy,z in [a,b]:C(g,id+'_pulley',(x,yy,z),r,.025,'vc_steel','y','带轮外形','roller',40)
    return g

def _vc_cabinet(parent,name,loc,size,ma='vc_white'):
    x,y,z=loc;sx,sy,sz=size;g=empty(name,loc,parent,'分板式电气/驱动机箱','shell')
    B(g,name+'_base',(0,0,.055),(sx,sy,.11),'vc_navy','机箱底座','frame',.012)
    B(g,name+'_top',(0,0,sz-.02),(sx,sy,.04),ma,'机箱顶板','shell',.018)
    for side in (-1,1):
        B(g,name+'_end',(side*(sx/2-.018),0,sz/2),(.036,sy,sz),ma,'端部面板','shell',.012)
        door=empty(name+'_door',(0,side*sy/2,sz/2),g,'可拆侧门','shell',explode=[0,side*.18,0])
        B(door,name+'_door_panel',(0,0,0),(sx-.04,.025,sz-.13),ma,'机箱检修门','shell',.01)
        B(door,name+'_latch',(sx*.31,side*.018,0),(.022,.027,.12),'vc_dark','门锁','frame',.004)
        for j in range(8):B(door,name+'_vent',(-sx*.20+j*sx*.035,side*.018,-sz*.26),(.014,.010,sz*.16),'vc_dark','通风百叶','frame',.002)
    return g

def _vc_can(parent,name,loc,r=.25,h=1.1):
    g=empty(name,loc,parent,'棉条筒','material')
    C(g,name+'_body',(0,0,h/2),r,h,'vc_can','z','条筒筒壁','material',48)
    for z in (.03,h-.02):T(g,name+'_rim',(0,0,z),r,.012,'vc_steel','z','条筒金属包边','material')
    C(g,name+'_sliver_top',(0,0,h+.002),r*.91,.006,'vc_sliver','z','棉条筒内棉条','material',48)
    for j in range(5):T(g,name+'_sliver_coil',(0,0,h+.007),r*(.16+j*.16),.004,'vc_sliver','z','盘条表层','material')
    return g

def _vc_rotor_cup(parent,name,r=.019):
    profile=[(-.017,.003),(-.014,r*.72),(-.010,r),(.008,r),(.010,r*.88),(-.007,r*.85),(-.010,.005)]
    vs=[(rr*math.cos(j*math.tau/40),-y,rr*math.sin(j*math.tau/40)) for y,rr in profile for j in range(40)]
    fs=[(k*40+j,k*40+(j+1)%40,(k+1)*40+(j+1)%40,(k+1)*40+j) for k in range(len(profile)-1) for j in range(40)]
    o=_vc_mesh(parent,name,vs,fs,'vc_steel','转杯内壁与凝聚槽','roller')
    for p in o.data.polygons:p.use_smooth=True

def _vc_fan(parent,id,loc,r=.16):
    x,y,z=loc
    motor(parent,id+'_motor','清洁吸风电机',(x,y+.30,z),axis='-y',radius=.075,length=.23)
    g=load(parent,id+'_impeller','离心清洁风机叶轮',(x,y,z),'rotate:z',1.4)
    C(g,id+'_disc',(0,0,0),r,.018,'vc_steel','y','风机轮盘','roller',40)
    for j in range(10):
        t=j*math.tau/10;o=B(g,id+'_blade',(r*.56*math.cos(t),-.025,r*.56*math.sin(t)),(r*.7,.065,.012),'vc_steel','离心叶片','roller',.002);o.rotation_euler.y=-t+.35
    shell=empty(id+'_shell',loc,parent,'吸风蜗壳','shell',explode=[0,-.15,0])
    C(shell,id+'_housing',(0,0,0),r*1.15,.19,'vc_navy','y','风机蜗壳','shell',48)
    B(shell,id+'_outlet',(r*.75,0,r*.65),(r*.8,.19,r*.7),'vc_navy','切向风口','shell',.012)
    C(parent,id+'_shaft',(x,y+.17,z),.018,.27,'vc_steel','y','风机轴端连接','frame',24)
    B(parent,id+'_mount',(x,y+.15,z-.105),(.30,.55,.04),'vc_navy','电机与风机共用托座','frame',.006)

def build_jingwei_jwf1366pro(root):
    _vc_materials();root['selectedFeedEnds']=6;root['selectedDeliveryHeads']=1
    # Six complete input cans and active creel, distinct from the Rieter sloped layout.
    for j in range(6):
        x=1.80+(j//2)*.64;y=(-1 if j%2==0 else 1)*.35
        _vc_can(root,'JW1366_feed_can_%02d'%(j+1),(x,y,0),.25,1.1)
        P(root,'JW1366_feed_sliver',[(x,y,1.10),(x,y,1.60),(x,0,1.65),(.73,(j-2.5)*.022,1.52)],.008,'vc_sliver','六根喂入棉条','material')
    for x in (1.55,3.47):
        B(root,'JW1366_creel_post',(x,0,.79),(.075,.075,1.58),'vc_dark','导条架支柱','frame',.007)
        B(root,'JW1366_creel_foot',(x,0,.035),(.37,.28,.07),'vc_dark','导条架底脚','frame',.008)
    B(root,'JW1366_creel_beam',(2.5,0,1.61),(2.05,.08,.08),'vc_steel','积极导条架横梁','frame',.006)
    for j,x in enumerate((1.80,2.44,3.08),1):
        roll=load(root,'JW1366_creel_roll_%02d'%j,'积极导条罗拉',(x,0,1.65),'rotate:z',1)
        C(roll,'JW1366_creel_roller',(0,0,0),.040,.73,'vc_steel','y','两侧导条罗拉','roller',40)
        for y in (-.29,.29):C(root,'JW1366_creel_press',(x,y,1.72),.027,.10,'vc_dark','y','喂入压辊','frame',32)
    _vc_cabinet(root,'JW1366_drive_body',(.35,0,0),(1.22,.94,1.40))
    # Arched forward hood and side green accents reproduce the observed overall massing.
    hood=empty('JW1366_draft_hood',(0,0,0),root,'圆弧牵伸罩','shell',explode=[0,0,.32])
    section=[(-.74+1.55*j/32,1.35+.40*math.sin(math.pi*j/32)**.25) for j in range(33)]
    vs=[(x,y,z) for x,z in section for y in (-.49,.49)];fs=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(section)-1)]
    top=_vc_mesh(hood,'JW1366_curved_cover',vs,fs,'vc_white','圆弧牵伸工作罩','shell')
    for polygon in top.data.polygons:polygon.use_smooth=True
    for y in (-.49,.49):
        side=[(x,y,z) for x,z in section]+[(.81,y,1.31),(-.74,y,1.31)]
        _vc_mesh(hood,'JW1366_hood_side',side,[tuple(range(len(side)))],'vc_white','圆弧罩侧板','shell')
    for y in (-.50,.50):B(hood,'JW1366_green_accent',(-.05,y,1.61),(.80,.018,.11),'vc_green','两侧绿色标识带','shell',.02)
    for j,(x,r) in enumerate([(.46,.015),(.30,.015),(.14,.020)],1):
        id='JW1366_'+['rear','middle','front'][j-1]
        g=load(root,id+'_roller','第%d下罗拉'%j,(x,0,1.47),'rotate:z',1.0+j*.5)
        C(g,id+'_steel',(0,0,0),r,.30,'vc_steel','y','牵伸下罗拉','roller',40)
        for k in range(20):
            a=k*math.tau/20;C(g,id+'_flute',(r*math.cos(a),0,r*math.sin(a)),.0006,.29,'vc_steel','y','罗拉细槽','roller',5)
        C(root,id+'_top',(x,0,1.47+r+.019),.019,.28,'vc_dark','y','弹簧加压上皮辊','frame',40)
        for yy in (-.18,.18):B(root,id+'_bearing',(x,yy,1.47),(.055,.055,.07),'vc_navy','罗拉轴承支座','frame',.006)
    C(root,'JW1366_guiding_top',(.06,0,1.49),.019,.25,'vc_dark','y','额外导向上皮辊','frame',32)
    B(root,'JW1366_pressure_bar',(.23,0,1.491),(.008,.28,.012),'vc_steel','8×12mm压力棒','frame',.001)
    detector=load(root,'JW1366_detecting_pair','喂入凹凸检测罗拉',(.70,0,1.51),'rotate:z',.6)
    for x in (-.024,.024):C(detector,'JW1366_measure_roll',(x,0,0),.03,.17,'vc_steel','y','检测凹凸罗拉','roller',40)
    delivery=load(root,'JW1366_delivery_nip','输出压辊',(-.09,0,1.465),'rotate:z',1.8)
    for x in (-.028,.028):C(delivery,'JW1366_delivery_roll',(x,0,0),.027,.13,'vc_steel','y','条子压实辊','roller',32)
    P(root,'JW1366_joined_sliver',[(.73,0,1.532),(.46,0,1.486),(.30,0,1.486),(.14,0,1.491),(-.09,0,1.492),(-.47,0,1.43)],.007,'vc_sliver','合并牵伸后的连续棉条','material')
    motor(root,'JW1366_main_motor','主电机 XYT112M30P4-5.5 / 5.5kW',(.15,-.30,.72),axis='y',radius=.12,length=.29)
    _vc_belt(root,'JW1366_main_belt',(.15,-.12,.72),(.14,-.12,1.47),.06)
    motor(root,'JW1366_servo_motor','匀整伺服电机 LTM-080 / 1.34kW',(.63,-.36,1.08),axis='y',radius=.055,length=.19,style='servo')
    diff=load(root,'JW1366_differential','主速度与匀整补偿的差速箱',(.63,-.12,1.08))
    B(diff,'JW1366_diff_housing',(0,0,0),(.20,.20,.18),'vc_steel','差速箱外壳','frame',.015)
    _vc_belt(root,'JW1366_level_belt',(.63,.025,1.08),(.46,.025,1.47),.055)
    # Two different disc motors: top coiler and can turntable, fully independent.
    motor(root,'JW1366_top_coil_motor','上圈条直驱盘式永磁同步电机 ANB3.3-T / 3.3kW',(-.55,0,1.50),axis='-z',radius=.145,length=.075)
    coil=load(root,'JW1366_top_coiler','上圈条盘',(-.55,0,1.43),'rotate:y',1.2)
    C(coil,'JW1366_coiler_disc',(0,0,0),.21,.035,'vc_steel','z','上圈条盘','roller',64)
    P(coil,'JW1366_eccentric_guide',[(0,0,.02),(.11,0,-.005),(.15,.015,-.06)],.014,'vc_steel','偏心圈条导管','roller')
    motor(root,'JW1366_bottom_coil_motor','下圈条直驱盘式电机 ANB0.1-D / 0.1kW',(-.55,0,.065),axis='z',radius=.14,length=.055)
    turn=load(root,'JW1366_can_turntable','下圈条筒盘',(-.55,0,.14),'rotate:y',.13)
    C(turn,'JW1366_table_disc',(0,0,0),.28,.035,'vc_dark','z','下筒盘','roller',64)
    C(root,'JW1366_lower_coil_joint',(-.55,0,.115),.022,.04,'vc_steel','z','下圈条同轴接口','frame',28)
    _vc_can(turn,'JW1366_active_can',(0,0,.03),.25,1.1)
    _vc_can(root,'JW1366_spare_can',(-.55,.65,.17),.25,1.1)
    for y in (-.34,.99):B(root,'JW1366_can_slide',(-.55,y,.09),(.65,.06,.08),'vc_dark','换筒滑轨','frame',.008)
    changer=load(root,'JW1366_pneumatic_change','气动换筒推杆',(-.55,.35,.20),'translate:z',.14,.30)
    C(changer,'JW1366_change_rod',(0,0,0),.014,.61,'vc_steel','y','气动换筒推杆','roller',24)
    B(changer,'JW1366_pusher',(0,-.32,0),(.45,.05,.16),'vc_dark','换筒推板','roller',.006)
    _vc_fan(root,'JW1366_fan',(.38,-.05,.54),.16)
    for x in (.12,.47):P(root,'JW1366_cleaning_duct',[(x,.21,1.44),(x,.28,1.20),(.38,-.05,.66)],.043,'vc_navy','上下吸棉支路')
    B(root,'JW1366_panel_arm',(.55,-.54,1.47),(.055,.21,.055),'vc_steel','控制屏横向支臂','frame',.005)
    B(root,'JW1366_panel_post',(.55,-.62,1.65),(.045,.045,.45),'vc_steel','显示器支臂','frame',.005)
    B(root,'JW1366_hmi',(.55,-.62,1.91),(.28,.06,.20),'vc_white','控制屏外框','frame',.012)
    B(root,'JW1366_screen',(.55,-.657,1.91),(.24,.008,.16),'vc_screen','匀整参数显示','frame',.005)
    return root

def _vc_k90_station(root):
    g=empty('K90_position_001',(0,0,0),root,'完整转杯纺工位 001');g['positionIndex']=1
    B(g,'K90_spinbox_back',(0,.005,1.40),(.215,.10,.47),'vc_navy','纺纱器安装背板','frame',.012)
    door=empty('K90_front_door',(0,-.18,1.43),g,'可开启纺纱箱前罩','shell',explode=[0,-.12,.05])
    B(door,'K90_spinbox_face',(0,0,0),(.209,.038,.36),'vc_white','独立纺位前罩','shell',.014)
    B(door,'K90_green_latch',(.074,-.027,.025),(.026,.025,.11),'vc_green','纺纱箱锁扣','frame',.004)
    B(door,'K90_yellow_service',(.015,-.03,-.14),(.13,.018,.033),'vc_brass','纺位维护拨片','frame',.004)
    motor(g,'K90_001_rotor_motor','单锭高速转杯电机',( -.045,-.055,1.48),axis='-y',radius=.029,length=.13,style='cartridge')
    cup=load(g,'K90_001_rotor','独立转杯',(-.045,-.168,1.48),'rotate:z',2.6);_vc_rotor_cup(cup,'K90_rotor_cup',.019)
    motor(g,'K90_001_feed_motor','步进喂给电机',(.060,-.05,1.28),axis='-y',radius=.024,length=.10,style='cartridge')
    feed=load(g,'K90_001_feed','给棉罗拉',(.060,-.145,1.28),'rotate:z',.35)
    C(feed,'K90_feed_roll',(0,0,0),.015,.044,'vc_steel','y','喂给罗拉','roller',28)
    B(g,'K90_feed_plate',(.06,-.145,1.258),(.045,.056,.007),'vc_steel','给棉板','frame',.001)
    opening=load(g,'K90_001_opening','分梳辊',(.045,-.15,1.365),'rotate:z',1.8)
    C(opening,'K90_opening_drum',(0,0,0),.027,.052,'vc_navy','y','分梳针布辊','roller',40)
    for i in range(24):
        a=i*math.tau/24;C(opening,'K90_opening_tooth',(.028*math.cos(a),0,.028*math.sin(a)),.0018,.055,'vc_steel','y','分梳针布齿列','roller',5)
    P(g,'K90_transfer_channel',[(.045,-.16,1.385),(.01,-.13,1.42),(-.04,-.16,1.46)],.008,'vc_navy','分梳至转杯输纤通道')
    C(g,'K90_draw_nozzle',(-.045,-.198,1.48),.006,.028,'vc_steel','y','静止引纱嘴','frame',20)
    # Independent delivery is described publicly; its motor packaging remains inferred.
    motor(g,'K90_001_delivery_motor','单锭引纱驱动；型式/位置推定',(-.102,-.13,1.82),axis='x',radius=.025,length=.065,style='cartridge')
    draw=load(g,'K90_001_delivery','单锭引纱罗拉',(0,-.13,1.82),'rotate:x',1.2)
    C(draw,'K90_delivery_roll',(0,0,0),.026,.12,'vc_steel','x','引纱罗拉','roller',32)
    C(g,'K90_delivery_press',(0,-.179,1.82),.021,.10,'vc_dark','x','引纱压辊','frame',28)
    wind=load(g,'K90_001_winding','卷绕接触辊',(0,-.13,1.99),'rotate:x',.8)
    C(wind,'K90_winding_drum',(0,0,0),.050,.16,'vc_dark','x','卷绕工作辊','roller',40)
    package=load(g,'K90_001_package','筒子纱',(0,-.13,2.185),'rotate:x',-.28)
    C(package,'K90_yarn_package',(0,0,0),.145,.15,'vc_sliver','x','所选成品卷装','material',48)
    for x in (-.084,.084):C(package,'K90_package_tube',(x,0,0),.025,.024,'vc_brass','x','筒管端部','material',24)
    for x in (-.097,.097):P(g,'K90_package_cradle',[(x,.02,2.00),(x,-.005,2.18),(x,-.13,2.185)],.008,'vc_navy','筒子摇架')
    guide=load(g,'K90_001_traverse','横动导纱工作位',(0,-.235,1.98),'translate:x',.7,.06)
    T(guide,'K90_traverse_eye',(0,0,0),.006,.0018,'vc_steel','y','横动导纱眼','roller')
    P(g,'K90_yarn_path',[(-.045,-.213,1.48),(-.045,-.23,1.62),(0,-.23,1.80),(0,-.183,1.82),(0,-.235,1.98),(0,-.180,1.99)],.0013,'vc_yarn','转杯至引纱和卷绕纱路','material')
    _vc_can(g,'K90_sliver_can',(0,-.80,0),.225,.90)
    P(g,'K90_feed_sliver',[(0,-.80,.90),(.02,-.54,1.15),(.06,-.18,1.26)],.006,'vc_sliver','由条筒至步进给棉口','material')
    B(g,'K90_green_status',(0,-.027,1.73),(.20,.02,.04),'vc_green','单锭状态横条','frame',.004)
    return g

def _vc_clone_station(template,parent,number,loc,side):
    originals=[template,*template.children_recursive];mapping={}
    for src in originals:
        o=src.copy();o.name=src.name.replace('001',f'{number:03d}',1) if '001' in src.name else src.name
        bpy.context.collection.objects.link(o);mapping[src]=o
        if o.get('driveAnchorId'):o['driveAnchorId']=o['driveAnchorId'].replace('001',f'{number:03d}',1)
    for src,o in mapping.items():o.parent=mapping.get(src.parent,parent)
    out=mapping[template];out.location=loc;out['positionIndex']=number;out['machineSide']=side
    if side=='B':out.rotation_euler.z=math.pi
    # Two staggered can rows, 460mm within each row, retain every 450mm can.
    if number%2==0:
        for o in out.children:
            if o.name.startswith('K90_sliver_can'):o.location.y=-1.30
            if o.name.startswith('K90_feed_sliver'):bpy.data.objects.remove(o,do_unlink=True)
        P(out,'K90_feed_sliver_far',[(0,-1.30,.90),(.02,-.59,1.16),(.06,-.18,1.26)],.006,'vc_sliver','外排条筒至给棉口棉条','material')
    return out

def build_titan_tqf_k90(root):
    _vc_materials();root['selectedPositions']=200;root['selectedSections']=10;root['gaugeMetres']=.23
    for j in range(10):
        x=(j-4.5)*2.30
        for y in (-.33,.33):
            B(root,'K90_section_sill',(x,y,.24),(2.29,.08,.13),'vc_navy','20头分节纵梁','frame',.009)
            B(root,'K90_section_upper',(x,y,1.74),(2.29,.09,.08),'vc_green','分节上梁','frame',.008)
            for xx in (x-1.10,x+1.10):
                B(root,'K90_section_post',(xx,y,1.02),(.07,.08,1.64),'vc_white','分节立柱','frame',.008)
                B(root,'K90_foot',(xx,y,.075),(.16,.25,.15),'vc_navy','机脚','frame',.01)
    for x,sx in [(-12.2,1.4),(12.1,1.2)]:
        _vc_cabinet(root,'K90_end_cabinet',(x,0,0),(sx,1.02,2.38))
        B(root,'K90_end_green_strip',(x,-.526,2.08),(sx-.06,.02,.055),'vc_green','机头绿色横线','shell',.006)
    B(root,'K90_operator_screen',(-12.24,-.531,1.87),(.47,.025,.36),'vc_screen','双屏控制面板','frame',.012)
    B(root,'K90_secondary_screen',(-12.24,-.533,1.52),(.40,.025,.20),'vc_screen','纺纱工艺显示','frame',.008)
    template=_vc_k90_station(root)
    for n in range(2,201):
        side='A' if n<=100 else 'B';j=(n-1)%100
        _vc_clone_station(template,root,n,((j-49.5)*.23,-.35 if side=='A' else .35,0),side)
    template.location=(-11.385,-.35,0);template['machineSide']='A'
    for side,sign in [('A',-1),('B',1)]:
        motor(root,'K90_opening_'+side+'_motor','该侧分梳共用驱动功能位置；数量/传动待核',(-12.1,sign*.25,1.34),axis='y' if sign<0 else '-y',radius=.12,length=.28)
        motor(root,'K90_winding_'+side+'_motor','该侧卷绕/横动共用驱动功能位置；未获BOM',(-12.1,sign*.25,1.95),axis='y' if sign<0 else '-y',radius=.11,length=.26)
        drive=load(root,'K90_winding_'+side+'_shaft','卷绕侧向分配轴接口；具体联接待核',(0,sign*.22,1.99))
        C(drive,'K90_long_distribution',(0,0,0),.018,22.96,'vc_steel','x','共用传动轴功能表达','frame',32)
        _vc_fan(root,'K90_suction_'+side,(11.84 if side=='A' else 12.30,-.12,.65 if side=='A' else 1.30),.20)
        B(root,'K90_negative_pressure_duct',(0,sign*.12,.60),(22.95,.15,.18),'vc_navy','纺纱负压总管','frame',.012)
    return root

def _vc_warp_mesh(parent,name,start,end,count=480,width=1.70):
    vs=[];fs=[]
    for i in range(count):
        x=-width/2+i*width/(count-1);k=len(vs)
        for y,z in [start,end]:
            for dx,dz in [(-.0007,0),(.0007,0),(.0007,.0014),(-.0007,.0014)]:vs.append((x+dx,y,z+dz))
        fs.extend([(k,k+1,k+5,k+4),(k+1,k+2,k+6,k+5),(k+2,k+3,k+7,k+6)])
    return _vc_mesh(parent,name,vs,fs,'vc_yarn','完整480根选定经纱','material')

def build_titan_tt868(root):
    _vc_materials();root['selectedReedWidthMetres']=1.70;root['selectedHealdFrames']=6;root['selectedWeftColors']=4
    for x in (-1.13,1.13):
        for y in (-.52,.65):B(root,'TT868_base_foot',(x,y,.08),(.30,.28,.16),'vc_navy','铸造底脚','frame',.018)
        B(root,'TT868_side_frame',(x,.03,.64),(.22,1.52,1.12),'vc_navy','厚壁整体侧机架','frame',.045)
        B(root,'TT868_side_cap',(x,.03,1.22),(.32,1.56,.06),'vc_steel','侧机架顶面','frame',.018)
        cover=empty('TT868_side_access',(x,0,0),root,'可拆侧传动罩','shell',explode=[x*.22,0,.08])
        B(cover,'TT868_panel',(0,-.10,.75),(.25,1.20,.80),'vc_white','剑轮箱外罩','shell',.035)
    for z in (.22,.64):B(root,'TT868_cross_member',(0,.31,z),(2.27,.14,.15),'vc_navy','跨幅机架横梁','frame',.012)
    # Current model uses a direct motor, not a belt main drive.
    motor(root,'TT868_main_motor','电子控制变速直驱主电机',(-1.38,-.44,.56),axis='x',radius=.15,length=.29)
    B(root,'TT868_main_mount',(-1.40,-.44,.38),(.50,.37,.06),'vc_navy','主电机安装托座','frame',.009)
    shaft=load(root,'TT868_main_shaft','主轴及打纬凸轮输入',(-1.02,-.44,.56),'rotate:x',1.0)
    C(shaft,'TT868_main_coupling',(0,0,0),.055,.36,'vc_steel','x','直驱联接轴','roller',40)
    reed=load(root,'TT868_reed_sley','筘座打纬工作组',(0,-.47,1.02),'oscillate:x',1.0,.045)
    for z in (0,.19):B(reed,'TT868_reed_beam',(0,0,z),(1.86,.045,.045),'vc_steel','钢筘横梁','roller',.004)
    # 480 model warp ends and 480 reed dents, explicit selected fabric construction.
    for i in range(480):B(reed,'TT868_reed_dent',(-.85+i*1.70/479,0,.095),(.0012,.013,.17),'vc_steel','筘齿','roller',.0002)
    for side,x in [('L',-1.02),('R',1.02)]:
        screw=load(root,'TT868_'+side+'_screw_drive','变距螺杆引纬机构外部工作位',(x,-.23,.93),'rotate:z',1.0)
        C(screw,'TT868_screw_body',(0,0,0),.052,.20,'vc_steel','y','引纬螺杆工作轴外形','roller',40)
        P(screw,'TT868_variable_pitch_trace',[(.055*math.cos(j*math.tau/24),-.085+.17*(j/95)**1.2,.055*math.sin(j*math.tau/24)) for j in range(96)],.006,'vc_brass','变距螺旋示意；非厂家齿形','roller')
        rapier=load(root,'TT868_'+side+'_rapier','左送纬剑' if side=='L' else '右接纬剑',(-.53 if side=='L' else .53,-.37,1.13),'translate:x',1.0,.34)
        B(rapier,'TT868_rapier_band',(0,0,0),(.86,.014,.008),'vc_dark','柔性剑带','roller',.001)
        B(rapier,'TT868_rapier_head',(.43 if side=='L' else -.43,0,.002),(.055,.030,.016),'vc_steel','剑头夹纱钳','roller',.003)
    # Electronic dobby is a selectable working system; no invented servo per frame.
    dobby=load(root,'TT868_dobby','六片电子多臂开口工作箱',(-1.65,.13,.90))
    B(dobby,'TT868_dobby_housing',(0,0,0),(.56,.65,.72),'vc_dark','电子多臂机箱','shell',.025)
    for y in (-.10,.36):B(root,'TT868_dobby_stand',(-1.65,y,.29),(.40,.09,.58),'vc_navy','多臂机承座','frame',.009)
    for j in range(6):
        y=-.03+j*.07;g=load(root,'TT868_heald_%02d'%(j+1),'第%d综框'%(j+1),(0,y,1.06),'translate:y',1.0,.035)
        for z in (-.14,.14):B(g,'TT868_heald_beam',(0,0,z),(1.88,.020,.025),'vc_steel','综框横梁','roller',.003)
        for x in (-.92,.92):B(g,'TT868_heald_side',(x,0,0),(.025,.02,.28),'vc_steel','综框侧档','roller',.003)
        for i in range(80):
            x=-.85+(i*6+j)*1.70/479;C(g,'TT868_heald_wire',(x,0,0),.0009,.27,'vc_steel','z','钢丝综','roller',5)
        P(root,'TT868_heald_link',[(-1.65,.13,.68),(-1.02,y,.65),(-.91,y,.88)],.009,'vc_steel','多臂至综框提综连杆；布局推定')
    motor(root,'TT868_letoff_servo','经轴电子送经伺服电机',(1.31,.78,.58),axis='-x',radius=.095,length=.23,style='servo')
    interface=load(root,'TT868_letoff_interface','送经轴端连接',(1.105,.78,.58),'rotate:x',.12)
    C(interface,'TT868_letoff_joint',(0,0,0),.032,.23,'vc_steel','x','送经联接轴端','roller',32)
    B(root,'TT868_letoff_mount',(1.28,.78,.43),(.42,.30,.08),'vc_navy','送经伺服安装座','frame',.008)
    warp=load(root,'TT868_warp_beam','φ800单经轴',(0,.78,.58),'rotate:x',.12)
    C(warp,'TT868_warp_package',(0,0,0),.36,1.78,'vc_yarn','x','经纱卷装','material',64)
    for x in (-.95,.95):C(warp,'TT868_beam_flange',(x,0,0),.40,.035,'vc_steel','x','φ800经轴盘片','roller',64)
    for x in (-1.01,1.01):C(root,'TT868_beam_bearing',(x,.78,.58),.08,.12,'vc_navy','x','经轴轴承座','frame',40)
    C(root,'TT868_backrest',(0,.68,1.20),.055,1.96,'vc_steel','x','单后梁张力导辊','frame',48)
    _vc_warp_mesh(root,'TT868_warp_back',(.80,.96),(.68,1.255))
    _vc_warp_mesh(root,'TT868_warp_to_heald',(.68,1.255),(.32,1.065))
    _vc_warp_mesh(root,'TT868_shed_to_reed',(.32,1.065),(-.47,1.12))
    motor(root,'TT868_takeup_servo','电子卷取伺服电机',(1.29,-.57,.74),axis='-x',radius=.085,length=.22,style='servo')
    interface=load(root,'TT868_takeup_interface','卷取轴端连接',(1.06,-.57,.74),'rotate:x',.18)
    C(interface,'TT868_takeup_joint',(0,0,0),.030,.28,'vc_steel','x','卷取联接轴端','roller',32)
    B(root,'TT868_takeup_mount',(1.28,-.57,.60),(.42,.30,.08),'vc_navy','卷取伺服安装座','frame',.008)
    take=load(root,'TT868_takeup','织物牵引卷取辊',(0,-.57,.74),'rotate:x',.18)
    C(take,'TT868_takeup_roll',(0,0,0),.085,1.87,'vc_dark','x','牵引卷取辊','roller',48)
    cloth=load(root,'TT868_cloth_roll','最大φ550卷布工作位',(0,-.45,.36),'rotate:x',.10)
    C(cloth,'TT868_woven_roll',(0,0,0),.25,1.78,'vc_sliver','x','织物卷装','material',64)
    _vc_mesh(root,'TT868_woven_web',[(-.85,-.47,1.12),(.85,-.47,1.12),(-.85,-.65,.79),(.85,-.65,.79),(-.85,-.70,.36),(.85,-.70,.36)],[(0,1,3,2),(2,3,5,4)],'vc_sliver','成布至卷取连续布幅','material')
    B(root,'TT868_blue_front',(0,-.66,1.24),(2.17,.15,.13),'vc_blue','蓝色前保护横梁','shell',.025)
    B(root,'TT868_hmi',(1.05,-.66,1.36),(.24,.10,.18),'vc_screen','机台操作屏','frame',.01)
    for side,x in [('L',-.92),('R',.92)]:
        motor(root,'TT868_leno_'+side+'_step','步进电机驱动电子绞边器',(x,-.12,1.34),axis='-y',radius=.032,length=.085,style='cartridge')
        leno=load(root,'TT868_leno_'+side,'电子绞边工作盘',(x,-.20,1.34),'rotate:z',1)
        C(leno,'TT868_leno_disc',(0,0,0),.045,.016,'vc_steel','y','绞边工作盘','roller',32)
        for xx in (-.024,.024):T(leno,'TT868_leno_eye',(xx,-.012,0),.006,.002,'vc_brass','y','绞边导纱眼','roller')
    for j in range(4):
        z=1.10+(j//2)*.44;y=-.20+(j%2)*.45
        B(root,'TT868_creel_support',(-2.28,y,z-.16),(.08,.08,.35),'vc_navy','四色纬纱架支柱','frame',.008)
        C(root,'TT868_weft_package',(-2.28,y,z),.13,.23,'vc_sliver','y','纬纱筒子','material',40)
        feeder=load(root,'TT868_weft_feeder_%02d'%(j+1),'第%d储纬工位'%(j+1),(-1.82,y,1.62+(j//2)*.15))
        C(feeder,'TT868_storage_drum',(0,0,0),.075,.14,'vc_steel','y','储纬鼓；独立驱动未核','roller',40)
        B(root,'TT868_feeder_bracket',(-2.05,y+.08,1.62+(j//2)*.15),(.51,.04,.045),'vc_navy','储纬器至筒架横支臂','frame',.004)
        B(feeder,'TT868_feeder_mount',(0,.08,0),(.10,.05,.14),'vc_navy','储纬器后安装板','frame',.005)
        P(root,'TT868_weft_path',[(-2.28,y-.13,z),(-1.82,y-.08,1.62+(j//2)*.15),(-1.00,-.36,1.19),(-.85,-.37,1.13)],.0014,'vc_yarn','四色独立纬纱路径','material')
    for y in (-.20,.25):
        _vc_beam(root,'TT868_weft_creel_column',(-2.28,y,.04),(-2.28,y,1.90),.05,'vc_navy','储纬与筒架立柱')
        B(root,'TT868_creel_foot',(-2.28,y,.035),(.38,.26,.07),'vc_navy','纬纱架底脚','frame',.008)
    selector=load(root,'TT868_weft_selector','四色电子选纬工作组',(-.99,-.34,1.25))
    for j in range(4):C(selector,'TT868_weft_needle',((j-1.5)*.022,0,0),.003,.18,'vc_steel','z','选纬导纱针','roller',12)
    cutter=load(root,'TT868_mechanical_scissor','标准机械纬剪',(-.88,-.48,1.12),'oscillate:z',1,.14)
    for sign in (-1,1):B(cutter,'TT868_scissor_blade',(sign*.009,0,0),(.01,.07,.006),'vc_steel','标准纬剪刀片','roller',.001)
    return root

BUILDERS={'jingwei_jwf1366pro':build_jingwei_jwf1366pro,'titan_tqf_k90':build_titan_tqf_k90,'titan_tt868':build_titan_tt868}
