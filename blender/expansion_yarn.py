"""SSM CWX-D and Rieter J 70 public-reference equipment builders.
Exec with B/C/T/P, empty, M, mat, math, bpy, Vector, motor and load supplied.
All measurements are metres, Z up. Only published configuration counts are exact;
external motor envelopes, detailed mechanisms and unmeasured dimensions are inferred.
No exports, scene resets, file access or package imports run from this module.
"""

def _ey_materials():
    for key,name,color,metal,rough in [
        ('ey_mint','J70 pale mint enamel',(.42,.64,.45),.28,.4),
        ('ey_deep','J70 dark frame enamel',(.14,.24,.19),.3,.42),
        ('ey_white','SSM light grey enclosure',(.79,.81,.79),.28,.39),
        ('ey_yarn','Visible ivory process yarn',(.88,.76,.47),0,.78),
        ('ey_yarn2','Second component yarn',(.30,.62,.75),0,.75),
        ('ey_air','Compressed air supply hose',(.03,.34,.72),.05,.48)]:
        if key not in M:M[key]=mat(name,color,metal,rough)


def _ey_tag(obj,**values):
    for key,value in values.items():obj[key]=value
    return obj


def _ey_mesh(parent,name,vertices,faces,material,label,group='frame',smooth=False):
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(vertices,[],faces);mesh.update()
    mesh.materials.append(M[material])
    for face in mesh.polygons:face.use_smooth=smooth
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.parent=parent
    _ey_tag(obj,label=label,description=label,group=group,evidenceStatus='inferred_geometry')
    if group=='shell':obj['shell']=True
    return obj


def _ey_link(parent,name,data,label,group='roller'):
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.parent=parent
    return _ey_tag(obj,label=label,description=label,group=group,evidenceStatus='inferred_geometry')


def _ey_panel_box(parent,key,loc,size,label,color='ey_mint',doors=2):
    """Hollow cabinet assembled from separately transparent panels."""
    g=empty(key,loc,parent,label,'shell');w,d,h=size
    B(g,key+'_plinth',(0,0,.09),(w,d,.18),'ey_deep',label+'底座')
    B(g,key+'_roof',(0,0,h-.022),(w,d,.044),color,label+'顶板','shell',.007)
    for xx in [-w/2+.018,w/2-.018]:
        B(g,key+'_end',(xx,0,(h+.18)/2),(.036,d,h-.18),color,label+'端板','shell',.006)
    for side in [-1,1]:
        for j in range(doors):
            xx=-w/2+(j+.5)*w/doors
            B(g,key+'_door',(xx,side*(d/2-.015),(h+.18)/2),(w/doors-.014,.03,h-.2),color,'分片检修门','shell',.006)
            B(g,key+'_latch',(xx+w/doors*.34,side*(d/2+.015),h*.52),(.016,.026,.115),'dark','门锁把手','shell',.003)
    return g


def _ey_output_support(parent,loc,label):
    x,y,z=loc
    B(parent,'drive_bracket',(x,y,z-.07),(.13,.15,.025),'steel',label+'安装托架',bevel=.003)
    B(parent,'drive_bracket_web',(x,y+.064,z-.018),(.13,.018,.13),'steel',label+'安装竖板',bevel=.003)


def _ey_grooved_drum(parent,name):
    """Actual recessed crossing grooves, shared mesh; groove pitch is illustrative."""
    key='CWXD_recessed_grooved_drum_mesh'
    mesh=bpy.data.meshes.get(key)
    if mesh is None:
        nx,na=96,64;verts=[];faces=[]
        for i in range(nx+1):
            x=-.080+.160*i/nx
            for j in range(na):
                a=math.tau*j/na;line=.075*(a/math.pi-1)
                distance=min(abs(x-line),abs(x+line))
                r=.055-.0032*max(0,1-distance/.0036)
                verts.append((x,r*math.cos(a),r*math.sin(a)))
        for i in range(nx):
            for j in range(na):
                nj=(j+1)%na;faces.append((i*na+j,(i+1)*na+j,(i+1)*na+nj,i*na+nj))
        faces.extend([tuple(reversed(range(na))),tuple(nx*na+j for j in range(na))])
        obj=_ey_mesh(parent,name,verts,faces,'steel','凹槽式往复排纱槽筒（槽形示意）','roller',True)
        obj.data.name=key
        for p in list(obj.data.polygons)[-2:]:p.use_smooth=False
        return obj
    return _ey_link(parent,name,mesh,'凹槽式往复排纱槽筒（槽形示意）')


def _ey_package(parent,key,r=.115,width=.152,material='cloth'):
    C(parent,key+'_yarn',(0,0,0),r,width,material,'x','圆柱交叉卷绕纱层','material',48)
    C(parent,key+'_tube',(0,0,0),.024,width+.035,'copper','x','筒管','material',24)
    # A fine surface trace makes the direction of rotation visible.
    P(parent,key+'_surface_trace',[(-width/2+width*i/48,r*math.cos(i*math.pi/6),r*math.sin(i*math.pi/6)) for i in range(49)],.00065,'ey_yarn','表层绕纱轨迹','material')


def _ey_cwx_position(parent,n,x,side):
    p=empty('CWXD_position_%02d'%n,(x,0,0),parent,'CWX-D 第%02d并纱位'%n)
    p.rotation_euler.z=0 if side<0 else math.pi
    _ey_tag(p,positionIndex=n,machineSide='A' if side<0 else 'B',componentRole='assembly_winding_position')
    B(p,'CWXD_unit_back',(0,-.29,1.24),(.405,.07,.58),'ey_white','并纱单元安装背板','shell',.007)
    B(p,'CWXD_unit_shelf',(0,-.44,1.352),(.37,.39,.032),'dark','槽筒及电机承台',bevel=.005)
    m=motor(p,'CWXD_wind_%02d'%n,'第%02d锭独立槽筒驱动'%n,(-.155,-.49,1.45),axis='x',radius=.040,length=.105,style='cartridge')
    _ey_tag(m,evidenceStatus='individual_drive_confirmed_layout_inferred',motorCountIsIllustrative=False)
    _ey_output_support(p,(-.155,-.49,1.45),'独立槽筒驱动')
    drum=load(p,'CWXD_drum_%02d'%n,'第%02d锭槽筒'%n,(0,-.49,1.45),motion='rotate:x',speed=.8)
    _ey_grooved_drum(drum,'CWXD_groove_%02d'%n)
    C(p,'CWXD_drum_journal',(.103,-.49,1.45),.012,.048,'steel','x','槽筒轴颈')
    B(p,'CWXD_bearing',(.116,-.49,1.45),(.025,.075,.080),'dark','槽筒轴承座',bevel=.004)
    package=load(p,'CWXD_package_%02d'%n,'第%02d锭合股筒子'%n,(0,-.49,1.620),motion='rotate:x',speed=-.38)
    _ey_package(package,'CWXD_take_up')
    for xx in [-.111,.111]:
        P(p,'CWXD_cradle',[(xx,-.31,1.40),(xx,-.36,1.55),(xx,-.49,1.62)],.009,'steel','卷装摇架与夹头')
        C(p,'CWXD_chuck',(xx,-.49,1.62),.035,.020,'dark','x','摇架筒管夹头')
    # Supply packages remain stationary: this is over-end withdrawal, not spindles.
    supply=load(p,'CWXD_supply_%02d'%n,'第%02d锭两只静止退绕供纱卷装'%n,(0,0,0))
    for j,yy in enumerate([-.56,-.90]):
        C(supply,'CWXD_supply_yarn',(0,yy,.300),.120,.260,'cloth','z','二股并纱供纱卷装','material',40)
        C(supply,'CWXD_supply_core',(0,yy,.31),.027,.315,'copper','z','退绕筒管','material',24)
        C(supply,'CWXD_package_peg',(0,yy,.138),.022,.055,'steel','z','纱架定位锭座','frame',20)
        xx=-.040 if j==0 else .040
        for zz in [.63,.93]:T(p,'CWXD_single_end_eye',(xx,-.63,zz),.009,.002,'steel','z','单根纱导纱环')
        for dx in [-.006,.006]:C(p,'CWXD_tension_disc',(xx+dx,-.63,.79),.026,.004,'steel','x','单根纱张力碟片','roller',24)
        P(p,'CWXD_tension_bracket',[(xx-.018,-.46,.765),(xx-.018,-.63,.765),(xx-.018,-.63,.79)],.004,'steel','张力器安装支杆')
        C(p,'CWXD_tension_pin',(xx-.015,-.63,.79),.004,.022,'steel','x','张力碟片支承销','frame',16)
        B(p,'CWXD_yarn_break_detector',(xx,-.606,.91),(.036,.024,.027),'dark','单根纱断纱检测器',bevel=.003)
        P(p,'CWXD_feed_yarn',[(.11,yy,.43),(xx,yy,.51),(xx,-.63,.63),(xx,-.63,.79),(xx,-.63,.93),(xx,-.63,1.028)],.0013,'ey_yarn' if j==0 else 'ey_yarn2','单根纱退绕至并纱导眼','material')
    merge=load(p,'CWXD_merge_%02d'%n,'第%02d锭两根纱并合导纱区'%n,(0,-.63,1.028))
    T(merge,'CWXD_merge_eye',(0,0,0),.013,.0025,'steel','z','并纱陶瓷导眼')
    B(p,'CWXD_combined_clearer',(0,-.615,1.17),(.055,.023,.040),'dark','合股断纱监控口',bevel=.004)
    P(p,'CWXD_assembled_yarn',[(-.040,-.63,1.028),(0,-.63,1.055),(0,-.639,1.17),(0,-.604,1.38),(0,-.5465,1.45)],.0017,'ey_yarn','合股纱至槽筒切向导入段','material')
    P(p,'CWXD_second_end_join',[(.040,-.63,1.028),(0,-.63,1.055)],.0013,'ey_yarn2','第二根纱并合段','material')
    B(p,'CWXD_station_keys',(.149,-.637,1.26),(.048,.024,.085),'dark','单锭操作键与状态灯',bevel=.004)
    for i,ma in enumerate(['green','orange']):C(p,'CWXD_key',(.149,-.653,1.24+i*.037),.009,.005,ma,'y','单锭按钮','frame',16)


def build_assembly_winding(root):
    _ey_materials()
    _ey_tag(root,equipmentId='assembly_winding',referenceManufacturer='SSM',referenceModel='CWX-D',
        referenceConfiguration='完整最小10锭；双面5+5；2股供纱；152毫米槽筒排纱',
        structuralCompleteness=False,selectedPositions=10,selectedSupplyPackages=20,
        selectedPlyCount=2,dimensionsEvidence='Photo-proportioned envelope; no manufacturer installation drawing',
        actualScope='完整10个独立并纱位；二股退绕、张力、断纱检测、槽筒排纱及接触卷绕。机体未标尺寸与电机外形按官方图推定。')
    pitch=.43;span=5*pitch
    B(root,'CWXD_spine',(0,0,.94),(span,.24,1.56),'dark','双面机身中央承重梁',bevel=.018)
    for side in [-1,1]:
        B(root,'CWXD_creel_floor',(0,side*.68,.10),(span+.06,.89,.055),'ey_white','供纱架底盘',bevel=.009)
        B(root,'CWXD_lower_beam',(0,side*.30,.32),(span,.06,.11),'steel','纱架下纵梁',bevel=.005)
        for xx in [-span/2+.035,span/2-.035]:
            B(root,'CWXD_stand',(xx,side*.32,.76),(.062,.078,1.39),'ey_white','机架立脚',bevel=.007)
            C(root,'CWXD_level_foot',(xx,side*.96,.037),.049,.074,'steel','z','可调基础脚','frame',24)
        for i in range(5):_ey_cwx_position(root,i+1+(0 if side<0 else 5),(i-2)*pitch,side)
        B(root,'CWXD_top_rail',(0,side*.38,1.91),(span+.18,.075,.055),'dark','上方防护与导纱横梁',bevel=.006)
        B(root,'CWXD_tension_shelf',(0,side*.45,.765),(span,.14,.026),'ey_white','张力器支承层',bevel=.005)
    for xx in [-span/2-.16,span/2+.16]:
        _ey_panel_box(root,'CWXD_end_cabinet',(xx,0,0),(.28,.76,1.77),'端部电控及机架侧罩','ey_white',1)
        for yy in [-.38,.38]:B(root,'CWXD_top_post',(xx,yy,1.82),(.07,.06,.21),'ey_white','顶部横梁端柱','shell')
    B(root,'CWXD_hmi',(-span/2-.309,-.22,1.40),(.025,.27,.22),'dark','整机参数面板',bevel=.008)
    B(root,'CWXD_hmi_glass',(-span/2-.325,-.22,1.40),(.008,.225,.17),'glass','操作显示屏',bevel=.003)
    C(root,'CWXD_estop',(-span/2-.33,-.22,.70),.028,.018,'orange','x','紧急停止按钮','frame',24)
    return root


def _ey_j70_can(parent,n,can_y):
    g=empty('J70_can_%02d'%n,(0,can_y,0),parent,'第%02d纺位熟条筒'%n,'material')
    _ey_tag(g,componentRole='sliver_can',positionIndex=n)
    C(g,'J70_can_body',(0,0,.537),.244,1.025,'ey_mint','z','1070毫米条筒筒体','material',40)
    for zz in [.042,1.053]:T(g,'J70_can_rim',(0,0,zz),.244,.012,'steel','z','条筒金属口圈','material')
    C(g,'J70_sliver_fill',(0,0,1.052),.230,.014,'cloth','z','筒内盘条顶面','material',40)
    for rr in [.06,.10,.14,.18,.215]:T(g,'J70_sliver_coil',(0,0,1.063),rr,.006,'cloth','z','棉条盘圈','material')
    return g


def _ey_j70_position(parent,n,x,side,can_row):
    p=empty('J70_position_%02d'%n,(x,0,0),parent,'J70 第%02d自主纺纱位'%n)
    if side>0:p.rotation_euler.z=math.pi
    _ey_tag(p,componentRole='airjet_spinning_position',positionIndex=n,machineSide='A' if side<0 else 'B')
    can_y=-.73 if can_row==0 else -1.245
    _ey_j70_can(p,n,can_y)
    B(p,'J70_unit_spine',(0,-.56,1.94),(.226,.14,1.53),'ey_deep','自主单元承重背架',bevel=.01)
    # Thin independently removable shells leave an accessible vertical process path.
    for xx in [-.102,.102]:
        for yy in [-.875,-.58]:B(p,'J70_winding_cheek',(xx,yy,2.38),(.025,.027,.45),'ey_mint','卷绕侧罩立边','shell',.008)
        B(p,'J70_winding_cheek_top',(xx,-.727,2.59),(.025,.32,.035),'ey_mint','卷绕侧罩顶边','shell',.008)
    B(p,'J70_control_face',(0,-.765,2.02),(.208,.032,.33),'ey_mint','纺位电控面板','shell',.014)
    B(p,'J70_unit_display',(.035,-.789,2.035),(.083,.012,.135),'dark','每纺位独立操作显示器',bevel=.007)
    B(p,'J70_unit_glass',(.035,-.798,2.045),(.066,.006,.103),'glass','操作显示区',bevel=.003)
    B(p,'J70_lower_housing',(0,-.615,1.43),(.225,.08,.55),'ey_deep','牵伸单元背板',bevel=.01)
    dm=motor(p,'J70_draft_%02d'%n,'第%02d纺位牵伸驱动示意'%n,(-.12,-.703,1.555),axis='x',radius=.029,length=.075,style='servo')
    _ey_tag(dm,evidenceStatus='individual_spinning_drive_confirmed_motor_allocation_inferred',motorCountIsIllustrative=True)
    B(p,'J70_draft_drive_mount',(-.13,-.65,1.555),(.04,.07,.09),'steel','牵伸驱动安装支座',bevel=.004)
    # Four nip pairs are a readable external roller-layout reconstruction; the
    # manufacturer's separate motor count and internal ratio train remain unknown.
    draft=load(p,'J70_drafting_%02d'%n,'第%02d纺位牵伸罗拉组'%n,(0,-.73,1.43))
    for k in range(4):
        z=1.285+k*.09
        rr=load(draft,'J70_draft_roller_%02d_%d'%(n,k+1),'牵伸下罗拉',(0,.027,z-1.43),motion='rotate:x',speed=.45+k*.18)
        C(rr,'J70_fluted_bottom',(0,0,0),.025,.130,'steel','x','牵伸下罗拉','roller',32)
        for angle in [j*math.tau/12 for j in range(12)]:
            C(rr,'J70_draft_flute',(0,.025*math.cos(angle),.025*math.sin(angle)),.0013,.125,'steel','x','下罗拉纵向细齿','roller',6)
        C(draft,'J70_top_cot',(0,-.048,z-1.43),.043,.125,'black','x','加压胶辊','roller',32)
        for xx in [-.078,.078]:B(draft,'J70_draft_bearing',(xx,.027,z-1.43),(.024,.074,.054),'steel','牵伸罗拉支承座',bevel=.004)
    for xx in [-.09,.09]:
        P(p,'J70_pressure_arm',[(xx,-.806,1.23),(xx,-.819,1.57),(xx,-.71,1.61)],.012,'orange','可开启加压臂')
    P(p,'J70_pressure_handle',[(-.09,-.819,1.59),(-.09,-.88,1.59),(.09,-.88,1.59),(.09,-.819,1.59)],.012,'orange','牵伸加压臂把手')
    P(p,'J70_sliver_in',[(0,can_y,1.073),(0,can_y,1.16),(0,-.73,1.24)],.005,'cloth','棉条由条筒上行喂入牵伸区','material')
    P(p,'J70_drafted_strand',[(0,-.73,1.24),(0,-.73,1.57)],.0014,'ey_yarn','穿过四组牵伸钳口的纤维束','material')
    nozzle=load(p,'J70_air_nozzle_%02d'%n,'第%02d纺位压缩空气成纱喷嘴'%n,(0,-.73,1.69))
    _ey_tag(nozzle,powerMedium='compressed_air',noMotor=True,evidenceStatus='pneumatic_process_confirmed_internal_geometry_not_replicated')
    # Split housing around an open central yarn bore, not a solid cylinder.
    for xx in [-.025,.025]:
        B(nozzle,'J70_nozzle_half',(xx,0,0),(.039,.068,.105),'steel','两片式喷嘴壳体','shell',.006)
        C(nozzle,'J70_nozzle_fastener',(xx,-.039,.026),.005,.015,'dark','y','喷嘴壳体螺钉','frame',12)
    for zz in [-.05,.05]:T(nozzle,'J70_ceramic_throat',(0,0,zz),.007,.003,'white','z','可见陶瓷入口（外观示意，非0.9毫米精密喷孔）')
    P(p,'J70_nozzle_air_hose',[(.043,-.73,1.69),(.083,-.67,1.70),(.084,-.48,1.61),(.06,-.31,1.60)],.005,'ey_air','压缩空气接入喷嘴的软管')
    P(p,'J70_fibre_to_nozzle',[(0,-.73,1.57),(0,-.73,1.64),(0,-.73,1.74)],.0014,'ey_yarn','牵伸纤维束通过气流喷嘴','material')
    # Piecing is autonomous per position; its actuators are not publicly assigned.
    piece=load(p,'J70_piecing_%02d'%n,'第%02d纺位自主接头工作口'%n,(0,-.75,1.82))
    for xx in [-.027,.027]:B(piece,'J70_piecing_jaw',(xx,0,0),(.018,.035,.045),'dark','接头工作区夹持外观',bevel=.004)
    T(piece,'J70_piece_eye',(0,-.013,.018),.008,.002,'steel','z','接头导纱口')
    delivery=load(p,'J70_delivery_%02d'%n,'第%02d纺位引纱钳口'%n,(0,-.825,2.25))
    C(delivery,'J70_delivery_bottom',(0,.026,0),.024,.12,'steel','x','引纱罗拉','roller',32)
    C(delivery,'J70_delivery_top',(0,-.026,0),.024,.12,'black','x','引纱压辊','roller',32)
    B(p,'J70_Q30A',(0,-.81,2.14),(.060,.018,.047),'dark','Q30A清纱检测头（选用）',bevel=.004)
    P(p,'J70_running_yarn',[(0,-.73,1.74),(0,-.763,1.84),(0,-.826,1.91),(0,-.826,2.14),(0,-.825,2.28)],.0013,'ey_yarn','喷嘴至接头和清纱检测、引纱的连续纱段','material')
    wm=motor(p,'J70_wind_%02d'%n,'第%02d独立卷绕单元驱动'%n,(-.13,-.66,2.47),axis='x',radius=.031,length=.074,style='cartridge')
    _ey_tag(wm,evidenceStatus='individual_winding_drive_confirmed_layout_inferred',motorCountIsIllustrative=True)
    drum=load(p,'J70_wind_drum_%02d'%n,'第%02d卷绕工作辊'%n,(.01,-.66,2.47),motion='rotate:x',speed=.85)
    C(drum,'J70_winding_drum',(0,0,0),.052,.158,'black','x','卷绕接触工作辊','roller',40)
    package=load(p,'J70_package_%02d'%n,'第%02d成纱筒子'%n,(.01,-.66,2.654),motion='rotate:x',speed=-.335)
    _ey_package(package,'J70_take_up',.132,.158)
    for xx in [-.096,.116]:
        P(p,'J70_package_cradle',[(xx,-.52,2.43),(xx,-.55,2.58),(xx,-.66,2.654)],.009,'steel','筒子夹持摇架')
        C(p,'J70_package_chuck',(xx,-.66,2.654),.032,.017,'steel','x','纱管夹头')
    guide=load(p,'J70_traverse_%02d'%n,'第%02d直线横动导纱器'%n,(0,-.827,2.365),motion='translate:x',speed=.7,amplitude=.063)
    C(p,'J70_traverse_rail',(0,-.805,2.355),.006,.185,'steel','x','直线横动导轨')
    B(guide,'J70_traverse_carriage',(0,.019,-.010),(.020,.022,.024),'dark','横动滑块',bevel=.003)
    T(guide,'J70_yarn_eye',(0,0,0),.007,.002,'steel','z','横动导纱眼')
    P(p,'J70_wind_in',[(0,-.825,2.28),(0,-.827,2.365),(.01,-.743,2.42),(.01,-.7135,2.47)],.0013,'ey_yarn','横动导眼至工作辊切向纱段','material')
    return p


def _ey_j70_robot(root,side,x):
    suffix='A' if side<0 else 'B'
    r=load(root,'J70_robot_'+suffix,suffix+'侧自动落筒机器人',(x,side*1.16,0),motion='translate:x',speed=.3,amplitude=.35)
    _ey_tag(r,componentRole='doffing_robot',machineSide=suffix)
    B(r,'J70_robot_outer',(0,0,2.27),(.61,.47,1.28),'ey_mint','落筒机器人立式机壳','shell',.026)
    B(r,'J70_robot_window',(0,side*.243,2.28),(.21,.018,1.02),'dark','落筒机器人检修窗','shell',.008)
    B(r,'J70_robot_bridge',(0,-side*.11,2.97),(.76,.64,.13),'steel','轨道小车框架',bevel=.01)
    for xx in [-.27,.27]:C(r,'J70_robot_track_wheel',(xx,-side*.27,2.96),.05,.056,'black','y','小车行走轮','roller',32)
    rm=motor(r,'J70_robot_drive_'+suffix,suffix+'侧机器人行走驱动示意',(.17,-side*.10,2.965),axis='y',radius=.048,length=.13,style='gear')
    _ey_tag(rm,evidenceStatus='travel_function_confirmed_drive_location_inferred',motorCountIsIllustrative=True)
    for xx in [-.095,.095]:P(r,'J70_robot_gripper',[(xx,-side*.20,2.64),(xx,-side*.43,2.64),(xx,-side*.43,2.51)],.012,'steel','落筒夹持臂（外观示意）')
    return r


def build_airjet_spinning(root):
    _ey_materials()
    _ey_tag(root,equipmentId='airjet_spinning',referenceManufacturer='Rieter',referenceModel='J 70',
        referenceConfiguration='40纺位，2机节，2机器人，255毫米节距；1070毫米条筒；圆柱卷装；选用Q30A',
        selectedPositions=40,selectedSections=2,selectedRobots=2,selectedCanHeightMetres=1.070,
        publicOverallLengthMetres=11.113,publicOverallWidthMetres=3.029,publicOverallHeightMetres=3.100,
        structuralCompleteness=False,motorTotalVerified=False,
        actualScope='公开基础40纺位配置及2落筒机器人、双侧物流；具体电机数量、内部分配和喷嘴微孔没有厂家装配图确认。')
    # Dimensioned total envelope; subdivisions follow the public photo, not a GA drawing.
    left=-11.113/2;active_start=left+3.03;active_length=5.370;active_mid=active_start+active_length/2
    head=_ey_panel_box(root,'J70_service_head',(left+1.515,0,0),(3.03,1.65,2.04),'吸排风与废料处理车头',doors=4)
    _ey_panel_box(root,'J70_tube_loader',(left+10.453,0,0),(1.32,1.70,3.02),'双侧空管供给箱',doors=1)
    B(root,'J70_hmi',(left+2.73,-.85,1.56),(.27,.043,.30),'dark','整机触摸控制屏',bevel=.012)
    B(root,'J70_hmi_glass',(left+2.73,-.877,1.57),(.222,.010,.25),'glass','操作屏显示区',bevel=.004)
    # Photo-visible air-exhaust chimney; no unproven internal fan motor is invented.
    exhaust=load(root,'J70_suction_system','吸排风及过滤接口',(left+.88,0,1.90))
    C(exhaust,'J70_exhaust_socket',(0,0,.21),.205,.42,'steel','z','排风接口','frame',40)
    T(exhaust,'J70_exhaust_flange',(0,0,.41),.205,.018,'dark','z','排风法兰')
    waste=load(root,'J70_waste_compactor','自动废料压实与收集系统',(left+1.84,-.18,.56))
    B(waste,'J70_compactor_housing',(0,0,.08),(.73,.66,.75),'ey_deep','压实腔外形','shell',.015)
    B(waste,'J70_waste_cart',(.15,-.69,-.22),(.64,.56,.44),'ey_white','可抽出废料收集车','frame',.025)
    for xx in [-.07,.37]:C(waste,'J70_cart_wheel',(xx,-.87,-.48),.050,.032,'black','x','废料车轮','frame',20)
    # Fully represented 660-tube storage capacity (not a claimed occupied stock).
    for side in [-1,1]:
        suffix='A' if side<0 else 'B'
        for col in range(11):
            xx=left+9.91+col*.103
            B(root,'J70_tube_loader_channel',(xx,side*.70,1.58),(.093,.055,2.58),'ey_deep','空管储存通道','frame',.004)
            for row in range(30):
                tube=empty('J70_stored_tube',(xx,side*.72,.39+row*.083),root,'空管储位')
                C(tube,'J70_empty_tube',(0,0,0),.032,.155,'copper','y','可供给空纱管','material',16)
                C(tube,'J70_tube_bore_mark',(0,side*.078,0),.023,.001,'dark','y','空管端部内孔阴影','material',16)
        B(root,'J70_robot_rail',(active_mid,side*.91,2.98),(active_length+.80,.10,.08),'steel','落筒机器人轨道',bevel=.005)
        conveyor=load(root,'J70_conveyor_'+suffix,suffix+'侧成筒输送带',(active_mid,side*.33,2.77))
        B(conveyor,'J70_package_belt',(0,0,0),(active_length+.80,.30,.022),'black','成筒输送带工作面',bevel=.003)
        for xx in [-active_length/2-.36,active_length/2+.36]:C(conveyor,'J70_conveyor_end',(xx,0,-.027),.035,.32,'steel','y','输送带端辊','roller',32)
        cm=motor(root,'J70_conveyor_drive_'+suffix,suffix+'侧成筒带驱动示意',(active_start-.36,side*.60,2.743),axis='y',radius=.047,length=.14,style='gear')
        _ey_tag(cm,evidenceStatus='conveyor_function_confirmed_drive_layout_inferred',motorCountIsIllustrative=True)
        P(root,'J70_air_main',[(active_start-.05,side*.31,1.60),(active_start+active_length+.05,side*.31,1.60)],.018,'ey_air','每侧压缩空气干管')
        _ey_j70_robot(root,side,active_start+(1.00 if side<0 else 4.25))
    for sec in range(2):
        mid=active_start+(sec+.5)*2.685
        module=empty('J70_section_%02d'%(sec+1),(mid,0,0),root,'20纺位机节')
        _ey_tag(module,sectionIndex=sec+1,selectedPositions=20)
        B(module,'J70_central_duct',(0,0,1.63),(2.685,.45,.39),'ey_deep','机节中央吸风主通道',bevel=.013)
        for side in [-1,1]:
            for zz in [1.18,2.40]:B(module,'J70_main_beam',(0,side*.51,zz),(2.685,.11,.11),'ey_mint','机节连续承重梁',bevel=.006)
            for xx in [-1.30,1.30]:B(module,'J70_support_post',(xx,side*.23,.62),(.065,.065,1.24),'steel','机节落地支柱',bevel=.005)
            for i in range(10):
                n=sec*20+(0 if side<0 else 10)+i+1
                _ey_j70_position(module,n,(i-4.5)*.255,side,i%2)
    # End supported crossbeam completes the continuous overhead robot path.
    for xx in [active_start-.34,active_start+active_length+.37]:
        for side in [-1,1]:B(root,'J70_rail_support',(xx,side*.91,2.49),(.09,.12,.94),'steel','轨道端部支承柱',bevel=.006)
    C(root,'J70_status_lamp',(left+10.88,-.45,3.06),.024,.08,'orange','z','机端状态灯','frame',24)
    return root


BUILDERS={'assembly_winding':build_assembly_winding,'airjet_spinning':build_airjet_spinning}
