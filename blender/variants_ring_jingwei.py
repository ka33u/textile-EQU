"""JWF1590A 1440-spindle original public-reference reconstruction.
Only definitions. Common expansion helpers injected by build_expansion.py.
The exact functional motor partition is inferred, not an OEM electrical BOM.
"""

def _jr_materials():
    for k,c,m,r in [('jr_white',(.78,.81,.80),.2,.4),('jr_grey',(.22,.29,.31),.4,.4),('jr_blue',(.03,.28,.52),.25,.33),('jr_green',(.25,.57,.10),.1,.44),('jr_red',(.66,.10,.10),.2,.35),('jr_dark',(.028,.036,.044),.22,.4),('jr_steel',(.64,.68,.70),.8,.27),('jr_yarn',(.84,.80,.68),0,.86),('jr_copper',(.62,.35,.12),.65,.33),('jr_screen',(.015,.08,.12),.05,.3)]:
        if k not in M:M[k]=mat(k,c,m,r)

def _jr_mesh(parent,name,vs,fs,ma,label,group='frame'):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(M[ma])
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.parent=parent;o['label']=label;o['group']=group;return o

def _jr_cabinet(parent,name,x,length,height=2.488,width=1.52):
    g=empty(name,(x,0,0),parent,'分板式端部机箱','shell',explode=[0,.30,.28])
    B(g,name+'_base',(0,0,.13),(length,width,.26),'jr_grey','整体底座','frame',.025)
    B(g,name+'_top',(0,0,height-.025),(length,width,.05),'jr_white','顶罩','shell',.015)
    for xx in (-length/2,length/2):B(g,name+'_end',(xx,0,height/2),(.035,width,height),'jr_white','分板端面','shell',.01)
    for s in (-1,1):
        for j in range(2):
            z=.27+(height-.27)*(j+.5)/2
            B(g,name+'_door',(0,s*(width/2),z),(length-.04,.035,(height-.27)/2-.025),'jr_white','上下检修门','shell',.012)
            B(g,name+'_handle',(.30,s*(width/2+.026),z),(.025,.027,.15),'jr_dark','门把手','shell',.003)
        B(g,name+'_line',(0,s*(width/2+.02),1.45),(length-.12,.012,.035),'jr_green','细绿色标识带','shell',.004)
        for q in range(12):B(g,name+'_vent',(-length*.32+q*length*.035,s*(width/2+.02),1.68),(.016,.01,.16),'jr_grey','通风百叶','shell',.001)
    return g

def _jr_spindle_x(j):
    # 720 positions on each side. The 2010mm central module is inferred from
    # the brochure's 52410mm L minus 720*70mm, and explicitly disclosed.
    return -26.205+(j+.5)*.07 if j<360 else 1.005+(j-360+.5)*.07

def _jr_station(root):
    g=empty('JW1590A_station_0001',parent=root,label='环锭工位 0001',group='frame');g['machineSide']='A';g['positionIndex']=1
    rotor=load(g,'JW1590A_spindle_0001','锭子 0001 / A侧',(0,-.625,.64),'rotate:y',2.2)
    rotor['spindleIndex']=1;rotor['machineSide']='A'
    C(rotor,'JW1590A_wharve',(0,0,0),.0095,.025,'jr_steel','z','φ19锭盘','roller',24)
    C(rotor,'JW1590A_spindle_blade',(0,0,.13),.004,.34,'jr_steel','z','旋转锭杆','roller',20)
    C(rotor,'JW1590A_green_tube',(0,0,.145),.0075,.20,'jr_green','z','选定200mm纱管','material',20)
    # Original lathed U-shaped cop envelope; not an OEM winding simulation.
    prof=[(.055,.009),(.064,.014),(.085,.016),(.18,.016),(.225,.009),(.235,.0075)]
    vs=[(r*math.cos(k*math.tau/24),r*math.sin(k*math.tau/24),z) for z,r in prof for k in range(24)]
    fs=[(i*24+k,i*24+(k+1)%24,(i+1)*24+(k+1)%24,(i+1)*24+k) for i in range(len(prof)-1) for k in range(24)]
    cop=_jr_mesh(rotor,'JW1590A_U_cop',vs,fs,'jr_yarn','U型成形管纱','material')
    for p in cop.data.polygons:p.use_smooth=True
    C(g,'JW1590A_bolster',(0,-.625,.57),.016,.095,'jr_grey','z','固定锭胆座','frame',24)
    B(g,'JW1590A_brake',(0,-.655,.56),(.023,.035,.07),'jr_dark','锭子制动工作片','frame',.004)
    # One feed roving per spindle; alternated into two creel rows by clone.
    rov=empty('JW1590A_roving_0001',(0,-.44,2.045),g,'在用粗纱筒 0001','material')
    C(rov,'JW1590A_roving_body',(0,0,0),.052,.25,'jr_yarn','z','粗纱卷装','material',32)
    for z in (-.145,.145):C(rov,'JW1590A_blue_end',(0,0,z),.017,.035,'jr_blue','z','粗纱管蓝色端部','material',20)
    C(rov,'JW1590A_hanger',(0,0,.205),.006,.10,'jr_steel','z','粗纱吊锭','frame',16)
    # All three top roller pairs and aprons remain visible at every spindle.
    for j,(yy,zz) in enumerate([(-.43,1.34),(-.50,1.30),(-.57,1.26)]):
        C(g,'JW1590A_top_cot',(0,yy,zz+.029),.0155,.047,'jr_dark','x','第%d上胶辊'%(j+1),'roller',24)
        C(g,'JW1590A_top_axle',(0,yy,zz+.029),.004,.062,'jr_steel','x','胶辊轴端','frame',16)
    B(g,'JW1590A_apron',(0,-.514,1.322),(.044,.068,.009),'jr_dark','上短下长双皮圈区','roller',.003)
    B(g,'JW1590A_weight_arm',(0,-.49,1.405),(.016,.19,.025),'jr_steel','YJ系列弹簧加压摇架','frame',.004)
    B(g,'JW1590A_weight_handle',(0,-.58,1.43),(.024,.04,.035),'jr_blue','摇架操作柄','frame',.004)
    P(g,'JW1590A_roving_path',[(0,-.44,1.90),(0,-.40,1.61),(0,-.43,1.355),(0,-.50,1.315),(0,-.57,1.275)],.0016,'jr_yarn','粗纱至三罗拉牵伸的连续纤维束','material')
    T(g,'JW1590A_lappet',(0,-.625,1.08),.006,.0011,'jr_steel','z','导纱钩','frame')
    P(g,'JW1590A_yarn_path',[(0,-.57,1.275),(0,-.625,1.08),(.011,-.634,.93),(0,-.644,.76),(0,-.64,.78)],.0008,'jr_yarn','牵伸输出—导纱钩—钢丝圈—管纱','material')
    B(g,'JW1590A_separator',(.0345,-.625,.91),(.001,.11,.28),'jr_steel','逐锭隔纱板','frame',0)
    noz=load(g,'JW1590A_nozzle_0001','单吸嘴 0001',(0,-.595,1.212))
    P(noz,'JW1590A_suction_branch',[(0,0,0),(0,.015,-.02),(0,.325,-.10)],.006,'jr_grey','单吸嘴至负压总管','frame')
    B(noz,'JW1590A_mouth',(0,0,0),(.035,.016,.014),'jr_dark','吸棉口','frame',.002)
    sensor=empty('JW1590A_detect_0001',(0,-.665,.69),g,'可选单锭检测；传感器不是电机','frame')
    B(sensor,'JW1590A_detect_body',(0,0,0),(.025,.012,.020),'jr_dark','单锭传感外形','frame',.002)
    return g

def _jr_clone(template,root,number,side,j):
    originals=[template,*template.children_recursive];mapping={}
    for src in originals:
        o=src.copy();o.name=src.name.replace('0001',f'{number:04d}',1);bpy.context.collection.objects.link(o);mapping[src]=o
        if o.get('driveAnchorId'):o['driveAnchorId']=o['driveAnchorId'].replace('0001',f'{number:04d}',1)
        if o.get('spindleIndex'):
            o['spindleIndex']=number;o['machineSide']=side;o['label']=f'锭子 {number:04d} / {side}侧'
    for src,o in mapping.items():o.parent=mapping.get(src.parent,root)
    g=mapping[template];g.location=(_jr_spindle_x(j),0,0);g['machineSide']=side;g['positionIndex']=number;g['label']=f'完整环锭工位 {number:04d} / {side}侧'
    if side=='B':g.rotation_euler.z=math.pi
    if j%2:
        for o in g.children:
            if o.name.startswith('JW1590A_roving_'):o.location.y=-.66
            if o.name.startswith('JW1590A_roving_path'):bpy.data.objects.remove(o,do_unlink=True)
        P(g,'JW1590A_outer_roving_path',[(0,-.66,1.90),(0,-.40,1.61),(0,-.43,1.355),(0,-.50,1.315),(0,-.57,1.275)],.0016,'jr_yarn','外排粗纱的连续喂入束','material')
    return g

def _jr_tape(parent,id,x):
    g=load(parent,id,'四锭一组闭合锭带',(x,0,.64))
    # Contact layout: two wharves on each side. Ribbon orientation rotates from
    # vertical on wharves to axial on the horizontal tin pulley.
    p=[(-.035,-.6345,0),(.035,-.6345,0),(.0445,-.625,0),(.035,-.6155,0),(.025,-.10,.06633),(.025,0,.12),(.025,.10,.06633),(.035,.6155,0),(.0445,.625,0),(.035,.6345,0),(-.035,.6345,0),(-.0445,.625,0),(-.035,.6155,0),(-.025,.10,-.06633),(-.025,0,-.12),(-.025,-.10,-.06633),(-.035,-.6155,0),(-.0445,-.625,0)]
    vs=[]
    for a,b,c in p:
        v=Vector((max(0,1-abs(b)/.3),0,min(1,abs(b)/.3))).normalized()*.0035
        vs.extend([tuple(Vector((a,b,c))-v),tuple(Vector((a,b,c))+v)])
    fs=[(2*i,2*i+1,2*((i+1)%len(p))+1,2*((i+1)%len(p))) for i in range(len(p))]
    _jr_mesh(g,id+'_surface',vs,fs,'jr_dark','带宽/扭转空间为重建，非原厂装配尺寸','roller');return g

def _jr_fan(root,end,x):
    axis='x' if end=='head' else '-x';sgn=1 if end=='head' else -1
    motor(root,'JW1590A_fan_'+end,'机头吸棉风机' if end=='head' else '机尾吸棉风机',(x-sgn*.36,0,1.87),axis=axis,radius=.12,length=.36)
    f=load(root,'JW1590A_fan_'+end+'_impeller','工艺吸棉叶轮',(x,0,1.87),'rotate:x',1.5)
    C(f,'JW1590A_fan_disc',(0,0,0),.22,.025,'jr_steel','x','离心叶轮轮盘','roller',40)
    for k in range(10):
        a=k*math.tau/10;o=B(f,'JW1590A_fan_blade',(0,.13*math.cos(a),.13*math.sin(a)),(.11,.12,.015),'jr_steel','叶片','roller',.002);o.rotation_euler.x=a+.3
    sh=empty('JW1590A_fan_'+end+'_shell',(x,0,1.87),root,'风机壳体','shell',explode=[0,.28,0])
    C(sh,'JW1590A_fan_housing',(0,0,0),.26,.23,'jr_grey','x','蜗壳','shell',48)
    B(root,'JW1590A_fan_pedestal',(x-sgn*.3,0,1.66),(.62,.40,.12),'jr_grey','风机与电机共用托座','frame',.01)
    C(root,'JW1590A_fan_joint',(x-sgn*.14,0,1.87),.033,.13,'jr_steel','x','风机联轴接口','frame',28)
    for y in (-.27,.27):P(root,'JW1590A_fan_duct',[(x,0,1.82),(x,y,1.4),(x+sgn*.40,y,1.112)],.060,'jr_grey','双风道工艺吸风接口','frame')

def build_jingwei_jwf1590a(root):
    _jr_materials()
    for k,v in dict(spindleCount=1440,spindleGaugeMillimetres=70,spindlesPerSide=720,mainLengthMetres=52.410,installedLengthMetres=60.125,referenceConfigurationRevision='official_joint_brochure_2026_download',draftingRollerPieceSpindles=8,selectedRovingPackages=1440,selectedFourSpindleTapes=360,modeledAuxiliaryMotorCountsVerified=False).items():root[k]=v
    _jr_cabinet(root,'JW1590A_head',-27.3325,2.255)
    _jr_cabinet(root,'JW1590A_tail',27.885,3.36)
    _jr_cabinet(root,'JW1590A_centre',0,2.01,1.732,1.18)
    B(root,'JW1590A_HMI',(-26.85,-.79,1.25),(.30,.08,.43),'jr_screen','触控工艺操作终端','frame',.012)
    # Thirty complete structural modules, every one carrying 24 positions/side.
    for m in range(30):
        j=m*24;x=sum(_jr_spindle_x(j+k) for k in range(24))/24
        mod=empty('JW1590A_module_%02d'%(m+1),(x,0,0),root,'整节装配机架模块 %02d'%(m+1),'frame')
        for y in (-.625,.625):
            B(mod,'JW1590A_spindle_rail',(0,y,.55),(1.68,.085,.075),'jr_grey','锭子龙筋','frame',.006)
            B(mod,'JW1590A_lower_sill',(0,y,.12),(1.68,.13,.16),'jr_grey','下纵梁','frame',.008)
        for xlocal in (-.78,.78):
            B(mod,'JW1590A_midwall',(xlocal,0,.72),(.07,.70,1.30),'jr_white','整体中墙板','frame',.014)
            for y in (-.58,.58):B(mod,'JW1590A_foot',(xlocal,y,.045),(.15,.33,.09),'jr_grey','调平底脚','frame',.01)
        C(mod,'JW1590A_round_crossbeam',(0,0,1.19),.075,1.66,'jr_steel','x','圆机梁','frame',32)
        B(mod,'JW1590A_creel_post',(0,0,1.85),(.045,.045,1.24),'jr_steel','上部粗纱架立柱','frame',.004)
        B(mod,'JW1590A_creel_cross',(0,0,2.40),(.07,1.50,.05),'jr_steel','双排粗纱吊架横梁','frame',.005)
        for y in (-.44,-.66,.44,.66):B(mod,'JW1590A_roving_rail',(0,y,2.30),(1.68,.035,.035),'jr_steel','连续粗纱吊锭轨','frame',.003)
        # Segmented ring and doffer rails: precise functional scope per lift screw.
        for side,sgn in [('A',-1),('B',1)]:
            ring=load(root,f'JW1590A_ringrail_{side}_{m+1:02d}','24锭钢领板工作段',(x,sgn*.625,.76),'translate:y',.20,.08)
            B(ring,'JW1590A_ring_rail',(0,0,-.015),(1.68,.07,.018),'jr_red','钢领板','roller',.002)
            doff=load(root,f'JW1590A_doffrail_{side}_{m+1:02d}','24位集体落纱梁',(x,sgn*.84,.69),'translate:y',.14,.22)
            B(doff,'JW1590A_doff_rail',(0,0,0),(1.68,.032,.032),'jr_steel','钢带式集落夹持梁','roller',.003)
            for k in range(24):
                dx=(k-11.5)*.07
                T(ring,'JW1590A_ring',(dx,0,0),.019,.0018,'jr_steel','z','所选φ38钢领','roller')
                T(ring,'JW1590A_traveller',(dx,sgn*.019,0),.0027,.0006,'jr_copper','x','钢丝圈','roller')
                T(doff,'JW1590A_gripper',(dx,0,0),.012,.003,'jr_dark','z','逐锭落纱夹持器','roller')
                B(doff,'JW1590A_gripper_arm',(dx,-sgn*.055,0),(.015,.11,.018),'jr_steel','夹持臂','roller',.002)
            screw=load(root,f'JW1590A_liftscrew_{side}_{m+1:02d}','钢领板螺杆升降工作位',(x,sgn*.735,.69),'rotate:y',.35)
            C(screw,'JW1590A_lift_screw',(0,0,0),.009,.42,'jr_steel','z','升降螺杆；螺距未公开','roller',24)
            for zz in (-.23,.23):B(root,'JW1590A_lift_support',(x,sgn*.735,.69+zz),(.06,.06,.04),'jr_grey','螺杆轴承支座','frame',.004)
            B(ring,'JW1590A_lift_nut',(0,sgn*.11,-.01),(.055,.05,.06),'jr_grey','随钢领板升降的螺母座','roller',.003)
            C(root,'JW1590A_doff_pivot',(x,sgn*.73,.25),.028,.14,'jr_steel','x','集落平行四杆支点','frame',24)
            P(root,'JW1590A_doff_link',[(x,sgn*.73,.25),(x,sgn*.82,.47),(x,sgn*.84,.69)],.015,'jr_grey','集落提升连杆；布置推定','frame')
    template=_jr_station(root)
    for number in range(2,1441):
        side='A' if number<=720 else 'B';j=(number-1)%720
        _jr_clone(template,root,number,side,j)
    template.location=(_jr_spindle_x(0),0,0)
    print('JW1590A_ALL_1440_STATIONS',flush=True)
    # All 540 8-spindle bottom-roller pieces; no half-length showcase reduction.
    for side,sgn in [('A',-1),('B',1)]:
        for row,yy,zz in [('rear',.43,1.34),('middle',.50,1.30),('front',.57,1.26)]:
            for n in range(90):
                x=sum(_jr_spindle_x(n*8+k) for k in range(8))/8
                r=load(root,f'JW1590A_draft_{side}_{row}_{n+1:02d}','8锭一节下罗拉',(x,sgn*yy,zz),'rotate:x',.45 if row=='rear' else .7 if row=='middle' else 1.8)
                C(r,'JW1590A_bottom_roller',(0,0,0),.0135,.56,'jr_steel','x','φ27下罗拉','roller',28)
                for xlocal in (-.27,.27):C(root,'JW1590A_roller_seat',(x+xlocal,sgn*yy,zz),.021,.024,'jr_grey','x','罗拉轴承座','frame',20)
        for z,xx in [(1,-26.57),(2,0),(3,26.57)]:
            for ri,row in enumerate(('rear','middle','front')):
                mid=f'JW1590A_draftmotor_{side}_{z}_{row}';zz=.74+ri*.25;axis='-x' if z==3 else 'x'
                motor(root,mid,f'{side}侧第{z}牵伸功能区 {row} 伺服（布局/台数推定）',(xx,sgn*.20,zz),axis=axis,radius=.065,length=.22,style='servo')
                B(root,'JW1590A_servo_mount',(xx,sgn*.20,zz-.08),(.30,.22,.035),'jr_grey','牵伸伺服安装托座','frame',.005)
                interface=load(root,mid+'_distribution','牵伸分段传动箱工作接口',(xx+(-.20 if z==3 else .20),sgn*.20,zz))
                B(interface,'JW1590A_draft_gearbox',(0,0,0),(.14,.25,.20),'jr_steel','模块化分配箱；隐蔽齿轮不复刻','frame',.008)
    # Two inferred end main drives. The verified four-spindle mechanical grouping is complete.
    for half,x,axis,start,stop in [('head',-27.38,'x',-26.205,-1.005),('tail',27.38,'-x',1.005,26.205)]:
        motor(root,'JW1590A_main_'+half,'变频主驱功能工位；两端分区台数推定',(x,0,.62),axis=axis,radius=.21,length=.54)
        B(root,'JW1590A_main_mount',(x,0,.34),(.80,.60,.12),'jr_grey','主电机连续基座','frame',.014)
        gear=load(root,'JW1590A_oilcase_'+half,'油浴式主传动箱',(x+(.55 if half=='head' else -.55),0,.64))
        B(gear,'JW1590A_oilcase_body',(0,0,0),(.44,.58,.48),'jr_grey','油浴传动箱外壳','shell',.025)
        shaft=load(root,'JW1590A_lineshaft_'+half,'碳纤滚盘主轴',((start+stop)/2,0,.64),'rotate:x',1.7)
        C(shaft,'JW1590A_mainshaft',(0,0,0),.027,stop-start,'jr_steel','x','高精度主轴','roller',32)
        C(root,'JW1590A_main_output_joint',(-26.40 if half=='head' else 26.40,0,.64),.034,.45,'jr_steel','x','油浴传动箱至主轴的联接段','frame',28)
    for n in range(360):
        x=(_jr_spindle_x(2*n)+_jr_spindle_x(2*n+1))/2
        drum=load(root,f'JW1590A_tin_{n+1:03d}','四锭一组碳纤滚盘',(x,0,.64),'rotate:x',1.7)
        C(drum,'JW1590A_tin_surface',(0,0,0),.12,.062,'jr_dark','x','碳纤滚盘外形','roller',40)
        _jr_tape(root,f'JW1590A_tape_{n+1:03d}',x)
    print('JW1590A_ALL_360_TAPES',flush=True)
    # Central ring-rail / doffer functions are separate, as shown in A-series brochure.
    for role,loc in [('ringlift',(0,-.25,.32)),('dofflift',(0,.25,1.10))]:
        motor(root,'JW1590A_'+role,'居中钢领板升降驱动' if role=='ringlift' else '居中集落升降驱动',loc,axis='x',radius=.11,length=.28,style='servo')
        g=load(root,'JW1590A_'+role+'_gearbox','居中双侧分配传动箱',(.33,loc[1],loc[2]))
        B(g,'JW1590A_centre_gearcase',(0,0,0),(.25,.30,.27),'jr_grey','升降分配箱外壳；齿轮未获图','frame',.015)
        B(root,'JW1590A_centre_mount',(0,loc[1],loc[2]-.16),(.64,.40,.06),'jr_grey','中央电机安装平台','frame',.008)
        for side,sgn in [('A',-1),('B',1)]:
            q=load(root,'JW1590A_'+role+'_line_'+side,'升降纵向分配轴',(0,sgn*(.735 if role=='ringlift' else .73),.43 if role=='ringlift' else .25),'rotate:x',.35)
            C(q,'JW1590A_lift_lineshaft',(0,0,0),.014,52.41,'jr_steel','x','沿全车机械分配轴；布置推定','roller',24)
    # Two complete steel-tape delivery loops and 1440 pins/empty tubes.
    for side,sgn in [('A',-1),('B',1)]:
        motor(root,'JW1590A_transport_'+side,'钢带走管功能驱动 '+side,(28.80,sgn*.65,.30),axis='y' if sgn>0 else '-y',radius=.075,length=.20,style='gear')
        C(root,'JW1590A_transport_joint',(28.80,sgn*.81,.30),.018,.11,'jr_steel','y','钢带驱动轮同轴联接','frame',24)
        drive=load(root,'JW1590A_transport_'+side+'_pulley','钢带输送端轮',(28.80,sgn*.84,.30),'rotate:z',.25)
        C(drive,'JW1590A_transport_pulley',(0,0,0),.08,.035,'jr_steel','y','钢带端部驱动轮','roller',40)
        tape=load(root,'JW1590A_transport_'+side+'_belt','全车钢带管纱输送线',(0,sgn*.84,.30))
        B(tape,'JW1590A_tape_upper',(1.2,0,.08),(55.2,.034,.003),'jr_steel','钢带承载段','roller',.001)
        B(tape,'JW1590A_tape_return',(1.2,0,-.08),(55.2,.034,.003),'jr_steel','钢带返回段','roller',.001)
        for x in (-26.40,28.80):
            pts=[(x+.08*math.cos(a),0,.08*math.sin(a)) for a in [math.pi/2+k*math.pi/16 for k in range(17)]]
            if x>0:pts=[(x+.08*math.cos(a),0,.08*math.sin(a)) for a in [-math.pi/2+k*math.pi/16 for k in range(17)]]
            P(tape,'JW1590A_tape_endturn',pts,.004,'jr_steel','钢带回转端段','roller')
        for j in range(720):
            x=_jr_spindle_x(j)
            C(tape,'JW1590A_delivery_pin',(x,0,.10),.005,.045,'jr_steel','z','逐锭走管销','roller',12)
            C(tape,'JW1590A_empty_tube',(x,0,.205),.008,.20,'jr_green','z','完整1440只空纱管','material',16)
        for m in range(30):
            x=sum(_jr_spindle_x(m*24+k) for k in range(24))/24
            B(root,'JW1590A_transport_support',(x,sgn*.84,.20),(1.68,.06,.035),'jr_grey','钢带输送支承','frame',.004)
    # Two ends of the process suction system, with every modeled branch assigned.
    _jr_fan(root,'head',-26.66);_jr_fan(root,'tail',26.66)
    for half,a,b in [('head',-26.205,-1.005),('tail',1.005,26.205)]:
        for side,sgn in [('A',-1),('B',1)]:
            d=load(root,'JW1590A_duct_'+half+'_'+side,'双风道负压主管',((a+b)/2,sgn*.27,1.112))
            C(d,'JW1590A_suction_main',(0,0,0),.065,b-a,'jr_grey','x','沿车双负压风道','frame',32)
    # Automatic tube orienter at the public 2100mm end length; internal counts inferred.
    sorter=empty('JW1590A_auto_tube_sorter',(30.615,0,0),root,'自动理管机','frame')
    B(sorter,'JW1590A_sorter_base',(0,0,.10),(2.10,1.20,.20),'jr_grey','理管机机座','frame',.02)
    for s in (-1,1):B(sorter,'JW1590A_sorter_side',(.40,s*.57,.72),(1.22,.035,1.20),'jr_white','理管斗侧板','shell',.015)
    B(sorter,'JW1590A_hopper_floor',(.40,0,.48),(1.22,1.12,.035),'jr_steel','空管储料斗底板','frame',.005)
    B(sorter,'JW1590A_hopper_end',(.99,0,.72),(.04,1.16,1.20),'jr_white','储料斗尾板','shell',.012)
    for i in range(18):C(sorter,'JW1590A_hopper_tube',(.05+(i%6)*.14,-.32+(i//6)*.31,.55),.008,.20,'jr_green','y','料斗展示空管；非容量上限','material',16)
    motor(root,'JW1590A_sorter_elevator','理管提升功能工位；配置推定',(30.0,-.48,.40),axis='y',radius=.085,length=.24,style='gear')
    elev=load(root,'JW1590A_sorter_elevator_load','自动理管斜升输送工作组',(30.1,0,1.0))
    for y in (-.35,.35):P(elev,'JW1590A_elevator_frame',[(.38,y,-.50),(-.38,y,.83)],.035,'jr_grey','斜提升框架','frame')
    for k in range(12):B(elev,'JW1590A_elevator_flight',(.35-k*.065,0,-.45+k*.112),(.07,.66,.04),'jr_steel','提升托条；节数为外形选定','roller',.004)
    motor(root,'JW1590A_sorter_orient','理管方向整理功能工位；配置推定',(29.72,-.43,1.78),axis='y',radius=.06,length=.20,style='servo')
    orient=load(root,'JW1590A_sorter_orient_load','理管滚筒与分流口',(29.72,0,1.78),'rotate:z',.30)
    C(orient,'JW1590A_sorter_drum',(0,0,0),.11,.60,'jr_dark','y','定向滚筒外形；槽数未复制','roller',40)
    P(root,'JW1590A_sorter_outlet',[(29.72,0,1.68),(29.40,0,1.35),(29.1,0,.62)],.09,'jr_grey','定向后至钢带装管位的输送通道','frame')
    B(root,'JW1590A_sorter_screen',(29.63,-.64,1.35),(.035,.08,.28),'jr_screen','自动理管操作屏','frame',.006)
    print('JW1590A_BUILD_COMPLETE',flush=True)
    return root

BUILDERS={'jingwei_jwf1590a':build_jingwei_jwf1590a}
