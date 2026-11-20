"""Current OEM comparison variants; external motor housings, no motor internals.
Position counts match the selected minimum complete configuration. Unknown drive
locations remain illustrative and are declared in variants-spinning.json.
"""

def _vs_materials():
    for key,col in [('vs_red',(.64,.025,.036)),('vs_mint',(.42,.70,.61)),('vs_shell',(.79,.83,.83)),('vs_yarn',(.90,.82,.57))]:
        if key not in M:M[key]=mat(key,col,0.12,.43)


def _vs_cab(root,name,x,length,height=2.1,color='white',doors=3,width=1.35,open_end=False):
    n=E(name,(x,0,0),root,name,'frame')
    B(n,name+'_base',(0,0,.13),(length,width+.07,.24),'dark',group='frame')
    B(n,name+'_roof',(0,0,height+.105),(length,width,.045),color,group='frame',bevel=.015)
    for sx in [-1,1]:
        if sx<0 and open_end:continue
        B(n,name+'_end_wall',(sx*(length/2-.018),0,height/2+.12),(.036,width,height),color,group='frame',bevel=.012)
    for sy in [-1,1]:
        for j in range(doors):
            cx=-length/2+(j+.5)*length/doors
            B(n,'cabinet_door',(cx,sy*(width/2+.012),height/2+.15),(length/doors-.025,.025,height-.13),color,group='guard',bevel=.008)
            B(n,'door_handle',(cx+length/doors*.37,sy*(width/2+.04),height*.55),(.025,.025,.17),'dark',group='guard',bevel=.006)
            for k in range(5):B(n,'vent_slot',(cx,sy*(width/2+.031),.30+k*.035),(length/doors*.62,.015,.013),'dark',group='guard',bevel=.002)
        for z in [.40,height-.15]:
            for cx in [-length/2+.06,length/2-.06]:B(n,'hinge',(cx,sy*(width/2+.032),z),(.03,.025,.055),'steel',group='guard')
    return n


def _vs_can(unit,rect=True,low=False):
    h=.915 if low else 1.07
    cy=(-.005 if int(unit.get('spinningPosition',1))%2==0 else -.405) if low else -.41
    if rect:
        B(unit,'sliver_can',(0,cy,h/2),(.216,.965,h),'vs_shell','条筒','material',.035)
        B(unit,'can_fibre_top',(0,cy,h+.006),(.191,.93,.014),'cloth','筒内纤维条','material',.025)
        for yy in [cy-.46,cy+.46]:B(unit,'can_rim',(0,yy,h),(.216,.018,.027),'steel',group='material')
    else:
        C(unit,'round_can',(0,cy,h/2),.195,h,'vs_shell','z','圆条筒','material',28)
        C(unit,'can_fibre_top',(0,cy,h+.004),.185,.014,'cloth','z','筒内纤维条','material',28)
        T(unit,'can_rim',(0,cy,h),.19,.009,'steel','z',group='material')
    for xx in [-.07,.07]:C(unit,'can_castor',(xx,cy,.035),.024,.028,'black','x',group='material',n=12)
    return h,cy


def _vs_package(unit,pre,z,individual=True,low=False):
    py=-.47 if low else -.69
    pkg=load(unit,pre+'_package','交叉卷绕筒子',(0,py,z),'rotate:x',.8)
    C(pkg,'yarn_package',(0,0,0),.126,.158,'cloth','x','纱线卷装','material',40)
    C(pkg,'tube_bore',(0,0,0),.027,.18,'copper','x','筒管','material',24)
    for x in [-.089,.089]:
        B(unit,'package_arm',(x,py+.035,z-.07),(.017,.045,.21),'white','筒子摇架','frame',.006)
        C(unit,'package_hub',(x,py,z),.037,.018,'steel','x',group='frame',n=20)
    if individual:
        motor(unit,pre+'_wind_m','独立卷绕电机',(-.07,py+.15,z-.075),'x',.043,.092,'servo')
    guide=load(unit,pre+'_guide','横动导纱器',(0,py-.105,z-.20),'translate:x',1.1,.067)
    T(guide,'guide_eye',(0,0,0),.009,.003,'steel','y',group='yarn')
    B(unit,'guide_track',(0,py-.082,z-.20),(.194,.025,.019),'steel',group='frame')
    if individual:motor(unit,pre+'_guide_m','独立导纱电机',(-.072,py+.03,z-.20),'x',.027,.070,'cartridge')
    return py


def _vs_unit(root,prefix,idx,x,side,kind):
    pre=f'{prefix}_{idx:02d}'
    u=E(pre+'_unit',(x,side*(.22 if kind=='r37' else .32),0),root,f'{idx:02d} 号纺纱工位','frame')
    if side>0:u.rotation_euler.z=math.pi
    u['spinningPosition']=idx
    low=kind=='r37'; air=kind=='airo'; auto=kind=='coro'
    h,cy=_vs_can(u,rect=not low,low=low)
    sz=1.18 if low else 1.40
    pz=1.72 if low else 2.12
    B(u,'unit_support',(0,-.23,sz+.15),(.211,.30,.84 if not low else .65),'vs_mint' if low else 'white','工位支架','frame',.016)
    face=B(u,'spin_face',(0,-.47,sz),(.205,.10,.28),'dark','纺纱箱前盖','guard',.018)
    face.rotation_euler.x=math.radians(12 if air else 7)
    for xx in [-.085,.085]:C(u,'cover_screw',(xx,-.527,sz+.105),.006,.009,'steel','y',group='guard',n=8)
    B(u,'release_handle',(0,-.55,sz-.07),(.11,.026,.028),'vs_red','纺纱箱开盖手柄','guard',.008)
    py=_vs_package(u,pre,pz,individual=(auto or air),low=low)
    # Feeder and its short duct are represented on every rotor station.
    if not air:
        feed=load(u,pre+'_feed','喂条罗拉',(0,-.43,sz-.19),'rotate:x',.45)
        C(feed,'feed_roll',(0,0,0),.025,.13,'steel','x',group='roller',n=20)
        motor(u,pre+'_feed_m','单工位喂条电机',(-.065,-.30,sz-.19),'x',.030,.080,'cartridge')
        opening=load(u,pre+'_opening','分梳辊',(-.042,-.31,sz+.015),'rotate:z',2.2)
        C(opening,'opening_roller',(0,0,0),.032,.05,'steel','y',group='roller',n=24)
        for j in range(16):
            a=j*math.tau/16
            C(opening,'opening_tooth',(.034*math.cos(a),-.026,.034*math.sin(a)),.0022,.012,'steel','y',group='roller',n=6)
        rot=load(u,pre+'_rotor','纺纱转杯',(.043,-.30,sz+.08),'rotate:z',4.0)
        C(rot,'rotor_cup',(0,0,0),.026,.030,'steel','y',group='roller',n=32)
        T(rot,'rotor_lip',(0,-.019,0),.026,.004,'steel','y',group='roller')
        if auto:
            motor(u,pre+'_opening_m','分梳辊独立电机',(-.042,-.13,sz+.015),'-y',.035,.10,'cartridge')
            motor(u,pre+'_rotor_m','转杯独立电机',(.043,-.12,sz+.08),'-y',.032,.12,'cartridge')
        P(u,'sliver_path',[(0,cy,h+.015),(0,cy,h+.14),(0,-.52,sz-.22),(0,-.43,sz-.19)],.009,'vs_yarn','纤维条喂入路径','yarn')
        P(u,'fibre_transport',[(0,-.43,sz-.19),(-.042,-.31,sz+.015),(.043,-.30,sz+.08)],.006,'vs_yarn','分梳与纤维输送示意','yarn')
        outlet=(.043,-.55,sz+.17)
        delivery=load(u,pre+'_delivery','引纱罗拉',(0,-.57,sz+.28),'rotate:x',.8)
        C(delivery,'takeoff_roll',(0,0,0),.025,.12,'steel','x',group='roller',n=20)
        C(u,'pressure_roll',(0,-.57,sz+.325),.021,.12,'black','x',group='roller',n=20)
        if low:motor(u,pre+'_delivery_m','AMIspin-Pro 单工位引纱电机',(-.06,-.39,sz+.28),'x',.03,.08,'cartridge')
        else:
            piecer=load(u,pre+'_piecer','接头及引纱机构：轴数未披露',(0,-.42,sz+.27),'rotate:x',.8)
            C(piecer,'piecing_disc',(0,0,0),.024,.09,'dark','x',group='roller',n=20)
        if low:
            B(u,'q30_sensor',(.045,-.62,sz+.22),(.045,.045,.055),'white','Q30清纱检测头','frame',.006)
            wax=load(u,pre+'_wax','上蜡盘',(0,-.58,sz+.43),'rotate:z',.25)
            C(wax,'wax_roll',(0,0,0),.018,.035,'cloth','y',group='roller',n=20)
            motor(u,pre+'_wax_m','单工位上蜡电机',(0,-.43,sz+.43),'-y',.022,.065,'cartridge')
            P(u,'vacuum_loop',[(.025,-.59,sz+.28),(.035,-.61,sz+.16),(.065,-.60,sz+.30)],.008,'dark','真空储纱补偿管','frame')
        else:load(u,pre+'_lift','机械筒子抬起与制动',(0,py+.04,pz-.12))
        P(u,'yarn_process_path',[outlet,(0,-.60,sz+.28),(0,py-.10,pz-.20),(0,py-.126,pz)],.0035,'vs_yarn','引纱、检测与卷绕路径','yarn')
    else:
        # Four pairs are a visual interpretation of the product photograph, not OEM axis count.
        drafting=load(u,pre+'_draft','牵伸罗拉组',(0,-.50,1.37))
        for j in range(4):
            yy=-.12+j*.073;zz=-.14+j*.055
            roller=load(drafting,pre+f'_draft_{j+1}','牵伸罗拉对',(0,yy,zz),'rotate:x',.45+j*.35)
            for dz in [-.018,.018]:C(roller,'draft_roll',(0,0,dz),.017,.16,'steel' if dz<0 else 'black','x',group='roller',n=20)
        motor(u,pre+'_draft_m','牵伸驱动功能位置（轴数未披露）',(-.067,-.25,1.40),'x',.032,.092,'servo')
        nozzle=load(u,pre+'_nozzle','气流纺纱喷嘴',(0,-.55,1.57))
        C(nozzle,'nozzle_shell',(0,0,0),.026,.10,'steel','z','纺纱喷嘴外壳','frame',24)
        C(nozzle,'air_coupling',(.034,0,0),.010,.05,'copper','x',group='frame',n=12)
        P(u,'air_branch',[(.056,-.55,1.57),(.085,-.28,1.57),(.085,-.15,1.30)],.008,'teal','压缩空气支管','frame')
        piecer=load(u,pre+'_piecer','数字接头机构：独立轴数未披露',(0,-.49,1.72),'rotate:x',.7)
        C(piecer,'piecing_roll',(0,0,0),.023,.115,'steel','x',group='roller',n=20)
        B(u,'airo_quality',(0,-.57,1.82),(.07,.05,.08),'white','Airolab 清纱头','frame',.009)
        P(u,'yarn_process_path',[(0,cy,h+.01),(0,-.65,1.23),(0,-.55,1.52),(0,-.55,1.62),(0,-.59,1.82),(0,py-.10,pz-.20),(0,py-.126,pz)],.004,'vs_yarn','条子、牵伸、气流成纱及卷绕路径','yarn')
    B(u,'status_display',(0,-.53,pz-.32),(.13,.025,.085),'vs_red' if not low else 'dark','工位状态操作面板','frame',.012)
    B(u,'status_light',(0,-.547,pz-.34),(.045,.008,.014),'green',group='frame',bevel=.003)
    return u


def _vs_tubemag(root,prefix,x):
    rack=load(root,prefix+'_tube_mag','空管库：12 排 × 36 支',(x,0,0))
    B(rack,'magazine_back',(.64,0,1.30),(.025,.70,1.43),'dark','空管库背板','frame')
    for j in range(13):B(rack,'tube_shelf',(0,0,.60+j*.107),(1.30,.70,.014),'steel','管排支架','frame',.003)
    # 12 vertical rows, 6 across × 6 deep per row = 432 tubes; packing is illustrative.
    for row in range(12):
        for across in range(6):
            for deep in range(6):
                C(rack,'empty_tube',(-.49+across*.193,-.28+deep*.112,.65+row*.107),.027,.17,'copper' if row%2 else 'cloth','x','432 支配置空管','material',12)
    for sy in [-1,1]:
        B(rack,'mag_guard',(0,sy*.37,1.3),(1.32,.028,1.45),'glass','管库检查窗','guard')
    motor(root,prefix+'_tube_m','管库输送驱动功能位置',(x+.48,.31,.47),'x',.065,.19,'gear')


def _vs_doffers(root,prefix,start,span,clean=False):
    for side in [-1,1]:
        B(root,'doffer_rail',(start+span/2,side*.92,2.51),(span+1.0,.08,.11),'steel','自动落筒轨道','frame')
        n=1 if side<0 else 2
        travel=load(root,prefix+f'_robot_{n}','落筒清洁单元沿机面行走',(start+span*(.30 if side<0 else .70),side*.99,0),'translate:x',.20,.72)
        B(travel,'robot_shell',(0,0,2.14),(.62,.42,.90),'white','落筒单元机壳','guard',.055)
        B(travel,'robot_face',(0,side*.225,2.16),(.48,.028,.73),'dark',group='guard',bevel=.04)
        for xx in [-.20,.20]:B(travel,'robot_accent',(xx,side*.244,2.17),(.05,.015,.70),'vs_red' if not clean else 'steel',group='guard')
        B(travel,'robot_window',(0,side*.246,2.02),(.25,.012,.24),'glass','作业检查窗','guard',.015)
        motor(travel,prefix+f'_robot_m_{n}','落筒单元行走驱动（安装推定）',(0,0,2.48),'x',.055,.16,'gear')
        arm=load(travel,prefix+f'_doff_arm_{n}','落筒夹持机构',(0,side*.12,1.73),'translate:y',.20,.08)
        for xx in [-.1,.1]:B(arm,'gripper_finger',(xx,0,0),(.03,.21,.07),'steel',group='frame')
        if clean:
            m=motor(travel,prefix+f'_clean_m_{n}','转杯清洁直线电机：外形示意',(-.17,0,1.90),'z',.037,.15,'servo')
            brush=load(travel,prefix+f'_clean_tool_{n}','转杯清洁头',(0,side*.15,1.68),'translate:y',.8,.065)
            C(brush,'cleaning_probe',(0,0,0),.014,.15,'steel','z',group='frame',n=16)
            m['linearMotorHousing']=True
            for child in m.children:
                if child.get('driveAnchorId')==prefix+f'_clean_m_{n}_out':
                    child['stationMotion']='translate:y';child['motionAmplitude']=.018
                    if 'spinAxis' in child:del child['spinAxis']
        P(travel,'clean_hose',[(.19,0,2.3),(.23,0,1.82),(0,side*.12,1.75)],.015,'black',group='frame')
        C(travel,'beacon_pole',(0,0,2.69),.012,.17,'steel','z',group='frame',n=12)
        C(travel,'beacon',(0,0,2.79),.028,.05,'orange','z',group='frame',n=16)


def _vs_common(root,prefix,kind):
    _vs_materials()
    r=kind=='r37'; auto=kind in ['coro','airo']; air=kind=='airo'
    section=2.35 if r else 2.812;half=10 if r else 12;span=2*section
    front=2.615 if r else (.896 if kind=='bd' else (1.417 if air else 1.418))
    rear=2.75 if r else (4.18 if kind=='bd' else 4.134)
    length=front+span+rear;start=-length/2+front;end=start+span
    root['selectedSpinningPositions']=half*4
    root['oemSectionCount']=2
    root['motorPlacementScope']='功能对应已核查；未公开的安装细节为推定'
    B(root,'foundation',(0,0,.055),(length,1.42 if r else 1.57,.10),'dark','整机底座','frame')
    for side in [-1,1]:
        for z in ([.16,.96,1.51] if r else [.17,1.18,1.91]):B(root,'longitudinal_frame',(start+span/2,side*.36,z),(span,.09,.10),'vs_mint' if r else 'white','纵向机架','frame')
        for k in range(3):B(root,'section_post',(start+k*section,side*.32,.82),(.06,.08,1.49),'steel','机节立柱','frame')
        airpipe=load(root,prefix+('_air_' if air else '_vacuum_')+str(1 if side<0 else 2),'压缩空气母管' if air else '纺纱工艺与排杂风道',(start+span/2,side*.15,1.13 if not r else .86))
        C(airpipe,'main_duct',(0,0,0),.065 if air else .11,span,'teal' if air else 'dark','x',group='frame',n=24)
    for side in [-1,1]:
        for sec in range(2):
            for j in range(half):
                i=(0 if side<0 else half*2)+sec*half+j+1
                px=start+sec*section+(section-(half-1)*.23)/2+j*.23
                _vs_unit(root,prefix,i,px,side,kind)
    head=_vs_cab(root,prefix+'_head',-length/2+front/2,front,1.76 if r else (1.64 if kind=='bd' else 2.12),'vs_mint' if r else 'white',doors=2,open_end=auto)
    B(head,'hmi_frame',(-front*.24,-.697,1.28),(.40,.04,.28),'dark','参数操作屏','frame',.02)
    B(head,'hmi_screen',(-front*.24,-.724,1.28),(.33,.018,.20),'glass',group='frame',bevel=.01)
    B(head,'brand_strip',(0,-.704,1.56 if r else 1.72),(front*.80,.016,.045),'vs_mint' if r else 'vs_red',group='frame')
    for side in [-1,1]:
        C(head,'e_stop',(-front*.24+.26,side*.71,1.22),.023,.025,'vs_red','y','急停按钮','frame',16)
    tail=_vs_cab(root,prefix+'_tail',end+rear/2,rear,1.76 if r else 1.88,'vs_mint' if r else 'white',doors=4)
    chambers=2 if air else (2 if r else 3)
    for k in range(chambers):
        xx=end+.28+(k+.5)*(rear-.56)/chambers
        for side in [-1,1]:
            B(root,'waste_chamber_door',(xx,side*.70,1.13),((rear-.6)/chambers-.055,.04,.67),'dark','分区废料过滤门','guard',.022)
            B(root,'waste_observation',(xx,side*.727,1.24),(.24,.012,.23),'glass','过滤腔观察窗','guard',.01)
    # Visible fan motors are functional representatives: supplier motor BOM unavailable.
    fan=load(root,prefix+'_fan','工艺吸风叶轮',(end+rear*.76,0,.58),'rotate:x',1.3)
    C(fan,'fan_wheel',(0,0,0),.24,.13,'dark','x','风机叶轮','roller',32)
    for j in range(9):
        a=math.tau*j/9
        b=B(fan,'fan_blade',(0,.14*math.cos(a),.14*math.sin(a)),(.12,.16,.027),'steel',group='roller');b.rotation_euler.x=a
    motor(root,prefix+'_fan_m','机尾工艺吸风驱动（数量及安装推定）',(end+rear*.76-.32,0,.58),'x',.13,.40,'industrial')
    if auto:
        _vs_tubemag(root,prefix,-length/2+front/2)
        _vs_doffers(root,prefix,start,span,clean=kind=='coro')
    # Conveyors: Autoairo selects documented optional belts; others standard.
    for side in [-1,1]:
        sn=1 if side<0 else 2
        belt=load(root,prefix+f'_conveyor_{sn}','筒子输送带',(start+span/2,side*.30,2.20 if auto else (1.80 if r else 2.16)),'translate:x',.24,.05)
        B(belt,'transport_belt',(0,0,0),(span+.5,.25,.027),'dark',group='roller')
        for xx in [-span/2,span/2]:C(belt,'conveyor_drum',(xx,0,0),.045,.27,'steel','y',group='roller',n=20)
    if kind=='bd':motor(root,prefix+'_transport_m','双面筒带中央驱动（安装推定）',(end+.17,0,1.8),'y',.07,.23,'gear')
    else:
        for side in [-1,1]:motor(root,prefix+f'_transport_m_{1 if side<0 else 2}','筒带驱动（数量和安装推定）',(end+.17,side*.30,1.84 if auto else 1.50),'x',.062,.20,'gear')
    if not auto:
        # Shared drive categories with conservative inferred architecture.
        for side in [-1,1]:
            sn=1 if side<0 else 2
            for system,z in [('rotor',1.28 if not r else 1.25),('opening',1.10 if not r else 1.15),('winding',1.94 if not r else 1.59),('traverse',1.80 if not r else 1.48)]:
                tr=load(root,prefix+f'_{system}_trans_{sn}',system+' 机面传动',(start+span/2,side*.20,z),'rotate:x',.8)
                if system=='rotor':
                    for yy in [-.028,.028]:B(tr,'tangential_belt',(0,yy,0),(span+.12,.015,.034),'black','切向带示意','roller')
                    for xx in [-span/2,span/2]:C(tr,'drive_pulley',(xx,0,0),.05,.06,'steel','z',group='roller',n=20)
                else:C(tr,'shared_shaft',(0,0,0),.016,span+.1,'steel','x','共用传动轴示意','roller',16)
                motor(root,prefix+f'_{system}_m_{sn}','机面 '+str(sn)+' '+system+' 功能驱动位置',(end+.22+(.30 if system=='opening' else 0),side*.25,z),'x',.073 if system=='rotor' else .055,.22,'industrial')
    return root


def build_saurer_autocoro_11(root):return _vs_common(root,'AC11','coro')
def build_saurer_bd_8(root):return _vs_common(root,'BD8','bd')
def build_saurer_autoairo(root):return _vs_common(root,'AA','airo')
def build_rieter_r_37(root):return _vs_common(root,'R37','r37')

BUILDERS={'saurer_autocoro_11':build_saurer_autocoro_11,'saurer_bd_8':build_saurer_bd_8,'saurer_autoairo':build_saurer_autoairo,'rieter_r_37':build_rieter_r_37}
