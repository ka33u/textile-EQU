"""Additional complete selected compact-spinning and two-for-one machines.

Executed after build_models.py's definitions. Uses the shared v3 geometry
helpers and v4 exterior motor library. Public dimensions/counts are distinguished
from inferred enclosure, drive-layout and yarn-path geometry. Not OEM CAD.
"""
import math
from mathutils import Vector, Matrix

K48_URL='https://www.rieter.com/products/systems/compact-spinning-machines/compact-spinning-machine-k-48'
K48_PDF='https://www.rieter.com/fileadmin/user_upload/products/documents/systems/end-spinning/rieter-k-48-compact-spinning-machine-brochure-3237-v6-95005-en.pdf'
TWISTER_URL='https://saurer.com/en/products/machines/twisting-and-cabling/staple/compacttwister'

def e5_root(stage,title,manufacturer,model,configuration,url):
    r=empty('stage_'+stage,label=title);roots.append(r)
    props={'stage':stage,'equipmentId':stage,'modelVersion':'3.0','driveRevision':'5.0',
        'motorDetailScope':'external_only','referenceManufacturer':manufacturer,
        'referenceModel':model,'referenceConfiguration':configuration,'referenceUrl':url,
        'fidelityStatus':'partial_public_reference','referenceStatus':'partial_public_reference',
        'structuralCompleteness':False,'capacityMatchedLine':False,
        'modelType':'public_configuration_reconstruction','dimensionsUnit':'metres',
        'hiddenOEMGeometryVerified':False,'motorLayoutEvidence':'inferred_functional_layout'}
    for k,v in props.items():r[k]=v
    return r

def e5_motor(parent,name,loc,size,style='induction',axis='x',shaft_end=None):
    g=empty(name,loc,parent,'精细外观电机：'+name,'motor')
    g['description']='功能驱动位置示意；电机型号、安装尺寸及隐蔽传动未获厂家CAD/BOM核实。'
    g['evidenceStatus']='drive_function_reference_layout_inferred'
    w,d,h=size
    rot=Matrix.Identity(3) if axis=='x' else Matrix.Rotation(-math.pi/2,3,'Y') if axis=='z' else Matrix.Rotation(math.pi/2,3,'Z')
    # Rotate the complete assembly so anchor-local +X remains the shaft axis.
    g.rotation_euler=rot.to_euler()
    foot=-h/2-.03 if style=='induction' else None
    _drive_v4.add_exterior(g,style,size,shaft_end if shaft_end is not None else w/2+.12,foot)
    g['driveRevision']='5.0';g['driveAnchorId']=name;g['motorLayoutEvidence']='inferred_new_reference_layout'
    if style=='induction' and axis=='x':
        bottom=loc[2]+foot
        if bottom>.18:
            _s3_box(parent,name+'_pedestal',(loc[0],loc[1],(.18+bottom)/2),(w*.96,d*.93,bottom-.18),'steel','电机承台：与机座连续','frame',.008)
    return g

def e5_shaft(parent,name,a,b,r=.016,label='传动轴',spin=True):
    a=Vector(a);b=Vector(b);delta=b-a;g=empty(name,tuple((a+b)/2),parent,label,'motor',spin='x' if spin else None)
    g.rotation_euler=Vector((1,0,0)).rotation_difference(delta.normalized()).to_euler()
    _s3_cyl(g,name+'_surface',(0,0,0),r,delta.length,'steel','x',label,'motor',24)
    g['driveRole']='transmission';g['transmissionEvidence']='functional_layout_inferred'
    return g

def e5_coupling(parent,name,loc,r=.045,length=.13,axis='x'):
    g=empty(name,loc,parent,'外部轴联接：'+name,'motor',spin={'x':'x','y':'z','z':'y'}[axis])
    for off in (-length*.30,length*.30):
        p=[0,0,0];p[{'x':0,'y':1,'z':2}[axis]]=off
        _s3_cyl(g,'coupling_half',p,r,length*.44,'orange',axis,'联轴器半体','motor',32)
    _s3_cyl(g,'coupling_flexible_center',(0,0,0),r*.91,length*.12,'black',axis,'弹性连接片','motor',32)
    g['driveRole']='transmission';g['transmissionEvidence']='functional_layout_inferred';return g

def e5_strip(parent,name,path,width=.01,thickness=.003,vertical=True,label='闭合传动带'):
    # A finite rectangular ribbon along a closed 3D loop. Strip orientation is
    # illustrative when a belt changes plane; no manufacturer's routing is claimed.
    points=[Vector(p) for p in path]
    if (points[-1]-points[0]).length>1e-7:points.append(points[0])
    verts=[]
    for i,p in enumerate(points):
        tangent=(points[(i+1)%(len(points)-1)]-points[(i-1)%(len(points)-1)]).normalized()
        side=Vector((0,0,1)) if vertical else Vector((1,0,0))
        normal=tangent.cross(side).normalized()
        if normal.length<.1:normal=Vector((0,1,0))
        for a,b in ((-1,-1),(1,-1),(1,1),(-1,1)):verts.append(tuple(p+side*a*width/2+normal*b*thickness/2))
    faces=[]
    for i in range(len(points)-1):
        for j in range(4):faces.append((4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.materials.append(M['black'])
    o=_s3_obj(name,me,(0,0,0),parent,label,'motor');o['driveRole']='transmission';o['transmissionEvidence']='functional_layout_inferred';return o

def e5_fibre_ribbon(parent,name,path,widths):
    verts=[]
    for (y,z),w in zip(path,widths):verts.extend([(-w/2,y,z),(w/2,y,z)])
    faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(path)-1)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.materials.append(M['cloth'])
    return _s3_obj(name,me,(0,0,0),parent,'纤维束由宽到窄的气流集聚路径','material')

def e5_k48_position(parent):
    g=empty('K48_compact_position',parent=parent,label='K48完整紧密纺锭位',group='roller')
    g['compactUnitCount']=1;g['modelledPrinciple']='sieve_drum_pneumatic_compacting'
    draft=empty('K48_drafting_rollers',parent=g,label='牵伸罗拉、胶辊与皮圈工作组',group='roller');draft['componentRole']='drafting_working_set'
    ringwork=empty('K48_ringrail_working_set',parent=g,label='钢领梁上的钢领及钢丝圈',group='roller');ringwork['componentRole']='ringrail_working_set'
    doffer=empty('K48_doff_gripper_set',parent=g,label='独立落纱夹爪与连接臂',group='frame');doffer['componentRole']='doffer_working_set'
    suction=empty('K48_compacting_suction_branch_group',parent=g,label='独立集聚抽吸接口及支管',group='frame');suction['componentRole']='compacting_suction_branch'
    # Three roller apron drafting followed by a separate perforated sieve drum.
    for j,(yy,zz) in enumerate(((.20,1.20),(.14,1.185),(.08,1.17))):
        _s3_cyl(draft,'K48_drafting_bottom',(0,yy,zz),.014,.060,'steel','x','牵伸下罗拉 '+str(j+1))
        _s3_cyl(draft,'K48_drafting_top',(0,yy,zz+.029),.014,.052,'black','x','牵伸上胶辊 '+str(j+1))
    _s3_box(draft,'K48_drafting_apron',(0,.14,1.209),(.044,.086,.011),'black','双皮圈主牵伸区；不是集聚皮圈','roller',.003)
    _s3_box(draft,'K48_pressure_arm',(0,.155,1.25),(.015,.155,.022),'teal','牵伸加压摇架','roller',.004)
    drum=empty('K48_perforated_compacting_drum',(0,.020,1.150),g,'多孔集聚滚筒','roller',spin='x')
    parts=_drive_v4.Parts()
    # Visible actual perforations; their pitch/number are explanatory, not OEM tolerances.
    for j in range(7):parts.ring(-.026+j*.0084,-.0243+j*.0084,.0167,.0185,n=32)
    for j in range(24):
        a=j*math.pi/12;parts.ring(-.026,.026,.0167,.0185,n=1,a0=a-.022,a1=a+.022)
    me=parts.mesh('K48_sieve_surface_shared','steel')
    o=_s3_obj('K48_sieve_surface',me,(0,0,0),drum,'多孔筛筒表面；孔型与尺寸为示意','roller');o['perforationGeometryVerified']=False
    _s3_cyl(drum,'K48_sieve_shaft',(0,0,0),.005,.068,'steel','x','集聚滚筒驱动轴','motor',20)
    detect=empty('K48_Detect_air_guide',(0,.022,1.184),g,'Detect导流及集聚监测元件','roller')
    _s3_box(detect,'Detect_air_guide_body',(0,0,0),(.032,.034,.013),'teal','导流元件外部形体','roller',.003)
    _s3_box(detect,'Detect_monitor_tip',(.014,-.01,.001),(.006,.009,.006),'orange','集聚监测位置','frame',.001)
    _s3_box(suction,'K48_suction_insert_envelope',(0,.020,1.128),(.048,.037,.017),'dark','筛筒下部抽吸接口外形','frame',.003)
    _s3_pipe(suction,'K48_compacting_suction_branch',[(0,.020,1.119),(0,.020,1.06),(0,.17,1.06)],.0075,'steel','集聚负压支路至单吸风总管')
    _s3_cyl(g,'K48_delivery_pressure_roller',(0,-.001,1.177),.011,.043,'black','x','集聚末端输出压辊')
    pp=[(.20,1.215),(.14,1.200),(.08,1.185),(.020,1.169)]
    pp +=[(.020+.019*math.cos(a),1.150+.019*math.sin(a)) for a in [math.pi/2+i*math.pi/2/8 for i in range(1,9)]]
    e5_fibre_ribbon(g,'K48_compacting_fibre_band',pp,[.008,.008,.007,.006]+[.006-.0045*(i+1)/8 for i in range(8)])
    spindle=empty('rotate_K48_LENA28_spindle',(0,0,.68),g,'LENA28锭子与紧密纱管纱','roller',spin='y')
    _s3_cyl(spindle,'K48_DUI16_tube',(0,0,.085),.008,.210,'orange','z','DUI16纱管；选定210mm管长','material',24)
    _s3_cyl(spindle,'K48_cop_yarn',(0,0,.085),.0125,.184,'cloth','z','紧密纱管纱','material',32)
    _s3_cyl(spindle,'K48_spindle_blade',(0,0,-.015),.006,.45,'steel','z','锭杆','roller',24)
    _s3_cyl(spindle,'K48_spindle_whorl',(0,0,-.18),.012,.022,'orange','z','锭带盘','motor',24)
    _s3_torus(ringwork,'K48_ring_34mm',(0,0,.70),.017,.002,'steel','z','34mm钢领')
    _s3_torus(ringwork,'K48_traveller',(0,.017,.70),.0032,.0008,'copper','x','钢丝圈')
    _s3_torus(g,'K48_lappet',(0,0,1.025),.007,.0015,'steel','z','短气圈导纱钩')
    _s3_pipe(g,'K48_compact_yarn_path',[(0,.001,1.15),(0,0,1.025),(.010,.011,.90),(0,.017,.70),(0,.0125,.74)],.00115,'cloth','集聚输出—导纱钩—钢丝圈—管纱','material')
    _s3_box(g,'K48_ISM_premium',(0,-.045,.59),(.030,.016,.023),'dark','ISM premium逐锭监测','frame',.002)
    _s3_box(g,'K48_partition',(.034,0,.86),(.001,.115,.29),'steel','相邻锭位隔纱板','frame',0)
    _s3_cyl(g,'K48_SERVOdisc_tray',(0,-.135,.20),.024,.012,'dark','z','SERVOdisc管纱输送托盘','roller',24)
    _s3_cyl(g,'K48_empty_tube',(0,-.135,.30),.008,.210,'orange','z','全锭位自动换管空管','material',24)
    _s3_torus(doffer,'K48_doffer_gripper',(0,-.175,.84),.022,.005,'black','z','自动落纱夹持器')
    _s3_box(doffer,'K48_doffer_arm',(0,-.115,.84),(.025,.10,.025),'steel','落纱夹爪连接臂')
    _s3_unit_finish(draft)
    return _s3_unit_finish(g)

def machine_compact_spinning():
    r=e5_root('compact_spinning','K48 288锭紧密纺机','Rieter','K 48',
        '288锭/6节×48；70mm节距；14.260m直联型C3；单端吸风、无IMD；High-Speed Package 34mm钢领/DUI16/LENA28；公开配置重建，非OEM装配',K48_URL)
    for k,v in {'spindleCount':288,'sectionCount':6,'spindleGaugeMillimetres':70,'machineLengthMetres':14.260,
        'selectedCompactingUnits':288,'selectedFourSpindleTapeGroups':72,'selectedRingDiameterMillimetres':34,
        'selectedTubeLengthMillimetres':210,'singleSuction':True,'intermediateDriveSelected':False,
        'roboSpinSelected':False,'automaticDoffingSelected':True,'specificationSource':K48_PDF}.items():r[k]=v
    work=10.080
    _s3_module(r,'K48_electronic_headstock',(-6.140,0,0),(2.155,1.64,1.80),'K48电子传动封闭车头',3)
    _s3_module(r,'K48_single_suction_end',(6.030,0,0),(1.935,1.64,1.80),'K48单通道吸风及SERVOdisc输出车尾',3)
    for sec in range(6):
        xx=-work/2+(sec+.5)*1.680
        module=empty('K48_48_spindle_section',(xx,0,0),r,'K48完整48锭节段','frame');module['sectionIndex']=sec+1;module['spindlesPerSection']=48
        _s3_module(module,'K48_section_sill',(0,0,0),(1.635,.48,.47),'紧密纺节段中墙下机座',2)
        for side in (-1,1):
            for zz,yy,sz,lab in ((.70,.330,.024,'钢领升降梁'),(.46,.330,.075,'锭子承重梁'),(.84,.505,.035,'自动落纱梁'),(.19,.465,.04,'SERVOdisc输送轨')):
                _s3_box(module,'K48_'+lab,(0,side*yy,zz),(1.680,.075,sz),'teal' if zz<.8 else 'steel',lab)
        for yy in (-.525,-.315,-.105,.105,.315,.525):_s3_box(module,'K48_creel_longrail',(0,yy,2.07),(1.680,.035,.04),'steel','多列粗纱吊锭纵轨')
        _s3_box(module,'K48_creel_crossbeam',(0,0,2.07),(.04,1.22,.045),'steel','粗纱架横梁')
        for xx2 in (-.82,.82):_s3_box(module,'K48_creel_column',(xx2,0,1.13),(.04,.045,1.88),'white','中墙与粗纱架立柱')
    first=e5_k48_position(r)
    for side in (-1,1):
        for i in range(144):
            xx=-work/2+(i+.5)*.070;index=(0 if side<0 else 144)+i+1
            if index==1:g=first;g.location=(xx,side*.330,0);g['positionIndex']=index
            else:g=_s3_clone_tree(first,r,(xx,side*.330,0),'K48_compact_position',index)
            g['machineSide']='front' if side<0 else 'rear'
            if side>0:g.rotation_euler[2]=math.pi
            cx=-work/2+((i//3)*3+1.5)*.070;cy=side*(.105+(i%3)*.210)
            _s3_cyl(r,'K48_roving_package',(cx,cy,1.74),.076,.406,'cloth','z','完整粗纱喂入卷装 '+str(index),'material',32)
            _s3_cyl(r,'K48_roving_hanger',(cx,cy,2.005),.010,.125,'steel','z','粗纱吊锭','frame',16)
            _s3_pipe(r,'K48_roving_feed',[(cx,cy,1.537),(xx,side*.13,1.33),(xx,side*.13,1.215)],.0016,'cloth','粗纱至牵伸头 '+str(index),'material')
    main=e5_motor(r,'K48_main_spindle_motor',(-6.35,0,1.02),(.62,.40,.40))
    main['label']='主锭子电机：功能据样本，外形/布置推定'
    e5_shaft(r,'K48_main_tinroller_shaft',(-5.92,0,.50),(5.04,0,.50),.022,'主电机至全机四锭锭带的纵向传动轴')
    # Manufacturer brochure p12: parallel-axis motor/belt stage before the long shaft.
    for name,zz,rr in (('motor',1.02,.100),('lineshaft',.50,.180)):
        pg=empty('rotate_K48_main_'+name+'_pulley',(-5.90,0,zz),r,'主传动'+name+'带轮','motor',spin='x')
        _s3_cyl(pg,'K48_main_belt_pulley',(0,0,0),rr,.032,'dark','x','主传动带轮','motor',48)
        for xx in (-.018,.018):_s3_cyl(pg,'K48_pulley_flange',(xx,0,0),rr+.007,.006,'steel','x','带轮挡边','motor',48)
        pg['driveRole']='transmission';pg['evidenceStatus']='belt_stage_verified_dimensions_inferred'
    right=-math.pi/2+math.acos((.104-.184)/.52);left=math.pi-right
    belt=[]
    for j in range(17):
        a=right+(left-right)*j/16;belt.append((-5.90,.104*math.cos(a),1.02+.104*math.sin(a)))
    for j in range(25):
        a=left+(right+2*math.pi-left)*j/24;belt.append((-5.90,.184*math.cos(a),.50+.184*math.sin(a)))
    e5_strip(r,'K48_main_motor_belt',belt,.024,.004,False,'原厂图示主电机—大带轮—纵向轴；轮径布局示意')
    e5_coupling(r,'K48_main_external_coupling',(-5.68,0,.50),.052,.15)
    for j in range(72):
        xx=-work/2+(j+.5)*.140;g=empty('K48_four_spindle_tape_group',(xx,0,.50),r,'完整四锭锭带组 '+str(j+1),'motor');g['tapeGroupIndex']=j+1;g['drivenSpindleCount']=4;g['driveGeometryVerified']=False
        rotor=empty('rotate_K48_tape_drum',parent=g,label='四锭锭带驱动滚轮',group='motor',spin='x')
        _s3_cyl(rotor,'K48_tape_drive_drum',(0,0,0),.055,.10,'dark','x','纵向轴上的锭带驱动滚轮','motor',32)
        e5_strip(g,'K48_four_spindle_tape',[(-.035,-.342,0),(.035,-.342,0),(.047,-.320,0),(.020,-.055,.045),(.020,.055,.045),(.047,.320,0),(.035,.342,0),(-.035,.342,0),(-.047,.320,0),(-.020,.055,-.045),(-.020,-.055,-.045),(-.047,-.320,0)],.007,.0017,True,'四锭锭带闭合空间路径；安装细节示意')
    for side in (-1,1):
        y=side*.20
        mo=e5_motor(r,'K48_drafting_drive_'+('front' if side<0 else 'rear'),(-5.65,y,1.20),(.38,.24,.24),'servo');mo['label']='电子牵伸/集聚传动功能电机；具体数量与布置推定'
        _s3_box(r,'K48_draft_distribution_cover',(-5.20,y,1.20),(.26,.31,.19),'teal','牵伸与集聚分配传动外罩；内部未建','shell',.018)
        e5_coupling(r,'K48_draft_coupling',(-5.31,y,1.20),.033,.12)
        for yy,zz in ((.20,1.20),(.14,1.185),(.08,1.17),(.020,1.15)):
            e5_shaft(r,'K48_draft_compact_lineshaft',(-5.08,side*(.330-yy),zz),(5.04,side*(.330-yy),zz),.005,'连续牵伸/集聚辊轴')
        _s3_pipe(r,'K48_one_duct_suction_branch',[(-5.05,side*.16,1.06),(5.12,side*.16,1.06),(5.75,0,.87),(6.45,.05,.79)],.045,'steel','集聚与断头共用的单通道抽吸支路')
    rail=e5_motor(r,'K48_ringrail_motor',(-6.40,.13,.30),(.34,.23,.23),'servo');rail['label']='钢领升降驱动外观（样本1.75kW功能）'
    e5_shaft(r,'K48_ringrail_transmission',(-6.11,.13,.30),(5.04,.13,.30),.014,'钢领板纵向传动轴；连杆布置推定')
    for xx in (-4.2,-2.52,-.84,.84,2.52,4.2):
        for side in (-1,1):
            _s3_pipe(r,'K48_ringrail_lift_link',[(xx,.13,.30),(xx,side*.33,.70)],.010,'steel','传动轴至钢领梁的升降连杆')
            _s3_pipe(r,'K48_doffer_link',[(xx,side*.20,.48),(xx+.20,side*.505,.84)],.012,'steel','集体落纱升降摆臂')
    fan=e5_motor(r,'K48_single_suction_motor',(6.0,.05,.55),(.50,.38,.38));fan['label']='单侧吸风电机外观（288锭6.5kW功能）'
    _s3_cyl(r,'K48_suction_scroll',(6.45,.05,.55),.25,.15,'teal','x','单通道吸风机外部蜗壳','frame',48)
    e5_coupling(r,'K48_fan_coupling',(6.35,.05,.55),.040,.10)
    _s3_pipe(r,'K48_exhaust',[(6.45,.05,.79),(6.45,.05,1.95),(6.45,.75,2.10)],.13,'steel','单端排风接口')
    for yy in (-.465,.465):_s3_box(r,'K48_link_delivery_track',(6.03,yy,.19),(1.98,.07,.04),'teal','SERVOdisc直联输送接口；产能未匹配')
    _s3_hmi(r,(-6.75,-.84,1.55),'K48电子牵伸、ISM及集聚监测操作屏')
    r['selectedMotorAnchors']=5
    return _s3_finish(r)

def e5_twister_position(parent):
    g=empty('CompactTwister_position',parent=parent,label='CompactTwister完整倍捻工位',group='roller')
    g['principle']='one_hollow_spindle_two_twists_per_revolution';g['twistsPerSpindleRevolution']=2
    g['internalThreadPathEvidence']='two_for_one_principle_schematic_not_OEM_passage_CAD'
    pot=empty('CT_stationary_pot',parent=g,label='静止筒罐及合股喂入卷装',group='shell')
    p=_drive_v4.Parts();p.ring(-.1225,.1225,.086,.090,loc=(0,0,.6325),axis='z',n=48)
    shell=_s3_obj('CT_stationary_pot_wall',p.mesh('CT_stationary_pot_shared','steel'),(0,0,0),pot,'静止罐壁；外径为布局推定','shell');shell['shell']=True
    floor=_drive_v4.Parts();floor.ring(-.006,.006,.014,.086,loc=(0,0,.514),axis='z',n=48)
    _s3_obj('CT_stationary_pot_floor',floor.mesh('CT_pot_floor_shared','steel'),(0,0,0),pot,'带中心通道的静止筒罐底座','frame')
    _s3_torus(pot,'CT_stationary_pot_rim',(0,0,.755),.088,.003,'dark','z','筒罐口圈','shell')
    feed=_drive_v4.Parts();feed.ring(-.1025,.1025,.012,.080,loc=(0,0,.6375),axis='z',n=48)
    feedme=feed.mesh('CT_annular_feed_package_shared','steel');feedme.materials.clear();feedme.materials.append(M['cloth'])
    _s3_obj('CT_feed_package',feedme,(0,0,0),pot,'预先并合的喂入卷装：选定160mm直径','material')
    tube=_drive_v4.Parts();tube.ring(-.115,.115,.010,.012,loc=(0,0,.642),axis='z',n=24)
    _s3_obj('CT_feed_tube',tube.mesh('CT_feed_tube_shared','orange'),(0,0,0),pot,'中空喂入筒管','material')
    # Stationary tension head above the package; hollow spindle passage is a schematic.
    for name,z,rad,h,ma,lab in [('CT_yarn_brake_housing',.795,.015,.065,'dark','带中心过纱孔的张力器外壳'),('CT_yarn_inlet',.842,.008,.035,'steel','中空纱线入口管')]:
        pp=_drive_v4.Parts();pp.ring(-h/2,h/2,.003,rad,loc=(0,0,z),axis='z',n=24)
        _s3_obj(name,pp.mesh(name+'_shared',ma),(0,0,0),g,lab,'roller')
    _s3_pipe(g,'CT_unwinding_yarn',[(.070,0,.740),(.050,0,.790),(0,0,.860)],.0012,'cloth','合股卷装至入口制动器','material')
    rotor=empty('rotate_CT_storage_disc',(0,0,.485),g,'旋转空心锭与储纱盘','roller',spin='y')
    disc=_drive_v4.Parts();disc.ring(-.007,.007,.009,.094,axis='z',n=48)
    disc_object=_s3_obj('CT_storage_disc',disc.mesh('CT_storage_disc_shared','steel'),(0,0,0),rotor,'留径向过纱通道的储纱盘；孔径布局示意','roller')
    hub=_drive_v4.Parts();hub.ring(-.0435,-.007,.005,.023,axis='z',n=32)
    _s3_obj('CT_rotor_hub',hub.mesh('CT_rotor_hub_shared','steel'),(0,0,0),rotor,'中空旋转锭盘轮毂','roller')
    _s3_cyl(rotor,'CT_spindle_whorl',(0,0,-.045),.025,.022,'orange','z','切向锭带驱动盘','motor',32)
    hollow=_drive_v4.Parts();hollow.ring(-.05,.26,.005,.009,axis='z',n=24)
    hollow_object=_s3_obj('CT_hollow_spindle_passage',hollow.mesh('CT_hollow_spindle_shared','steel'),(0,0,0),rotor,'空心锭外壁与中心通道示意','roller')
    # A real transverse bore joins the axial passage to the radial exit. This is
    # constructed once and shared by all twenty stations, rather than yarn drawn
    # through an opaque solid storage disc.
    cutter=_s3_cyl(rotor,'temporary_radial_bore',(.055,0,0),.0045,.110,'dark','x','临时径向孔布尔刀具','frame',24)
    bpy.context.view_layer.update()
    for target in (disc_object,hollow_object):
        modifier=target.modifiers.new('Radial yarn passage','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
        bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    outlet=_drive_v4.Parts();outlet.ring(.009,.094,.002,.004,n=24)
    _s3_obj('CT_radial_exit_guide',outlet.mesh('CT_radial_exit_guide_shared','dark'),(0,0,0),rotor,'中空径向出纱导管','roller')
    first_twist=_s3_pipe(rotor,'CT_first_twist_yarn',[(0,0,.375),(0,0,0),(.095,0,0)],.0012,'cloth','第一捻区：张力器至旋转盘出口','material');first_twist['twistZone']=1
    balloon=[]
    for j in range(41):
        t=j/40;z=.485+.495*t
        radius=.095 if z<.79 else .095*max(0,(.980-z)/.190)
        theta=.60*math.pi*t
        balloon.append((radius*math.cos(theta),radius*math.sin(theta),z-.485))
    air=_s3_pipe(rotor,'CT_second_twist_balloon',balloon,.0013,'cloth','第二捻区：旋转盘外气圈至固定导纱眼','material');air['twistZone']=2
    _s3_torus(g,'CT_balloon_guide',(0,0,.980),.006,.0018,'steel','z','固定气圈导纱眼')
    _s3_box(g,'CT_yarn_stop_sensor',(.022,.005,1.000),(.025,.025,.028),'dark','断纱自停检测位置','frame',.003)
    # Every station includes its actual local overfeed/deflection/winding functions.
    cap=empty('rotate_CT_overfeed',(0,-.035,1.13),g,'超喂轮','roller',spin='x')
    _s3_cyl(cap,'CT_overfeed_roller',(0,0,0),.035,.050,'dark','x','超喂轮表面','roller',40)
    _s3_cyl(cap,'CT_overfeed_hub',(.030,0,0),.016,.020,'steel','x','超喂轮轴头','roller',24)
    for xx in (-.030,.030):_s3_cyl(g,'CT_overfeed_bearing',(xx,-.035,1.13),.019,.014,'teal','x','超喂轮外部轴座','frame',24)
    _s3_cyl(g,'CT_deflection_roller',(0,-.120,1.225),.012,.036,'steel','x','可调导纱轮','roller',24)
    _s3_box(g,'CT_deflection_slide',(.029,-.120,1.225),(.018,.035,.07),'teal','导纱轮调节滑座','frame',.003)
    _s3_pipe(g,'CT_guide_support',[(.029,-.120,1.225),(.029,.07,1.225)],.009,'steel','导纱轮支承臂')
    _s3_torus(g,'CT_traverse_eye',(0,-.145,1.255),.005,.0015,'steel','y','横动导纱眼')
    _s3_box(g,'CT_traverse_slider',(0,-.14,1.246),(.024,.018,.014),'orange','机械横动导纱滑块','roller',.002)
    # Tangent-connected yarn from the balloon guide over the overfeed and deflector.
    start=(0,.980);c1=(-.035,1.13);c2=(-.120,1.225);r1=.0356;r2=.0126;exit=(-.145,1.255)
    entry=math.atan2(start[1]-c1[1],start[0]-c1[0])+math.acos(r1/math.dist(start,c1))
    common=math.atan2(c2[1]-c1[1],c2[0]-c1[0])-math.acos((r1-r2)/math.dist(c1,c2))
    leaving=math.atan2(exit[1]-c2[1],exit[0]-c2[0])-math.acos(r2/math.dist(exit,c2))
    pts=[(0,*start)]
    for c,rad,a,b in ((c1,r1,entry,common),(c2,r2,common,leaving)):
        while b<a:b+=2*math.pi
        pts.extend((0,c[0]+rad*math.cos(a+(b-a)*j/16),c[1]+rad*math.sin(a+(b-a)*j/16)) for j in range(17))
    pts.extend([(0,*exit),(0,-.040+.1107*math.cos(5*math.pi/4),1.395+.1107*math.sin(5*math.pi/4))])
    _s3_pipe(g,'CT_overfeed_winding_yarn',pts,.0011,'cloth','气圈眼—超喂轮—导轮—横动—交叉卷绕的连续纱路','material')
    friction=empty('rotate_CT_friction_roller',(0,-.040,1.25),g,'卷绕摩擦辊','roller',spin='x')
    _s3_cyl(friction,'CT_friction_surface',(0,0,0),.035,.172,'dark','x','摩擦卷绕辊','roller',40)
    package=empty('rotate_CT_delivery_package',(0,-.040,1.395),g,'交叉卷绕成品筒子','material',spin='x')
    _s3_cyl(package,'CT_delivery_package',(0,0,0),.110,.170,'cloth','x','选定220mm交叉卷绕筒子','material',48)
    _s3_cyl(package,'CT_delivery_tube',(0,0,0),.025,.195,'orange','x','交叉卷绕筒管','material',32)
    for hand in (-1,1):
        path=[]
        for j in range(161):
            x=-.084+.168*j/160;a=hand*j*8*math.pi/160
            path.append((x,.1108*math.cos(a),.1108*math.sin(a)))
        _s3_pipe(package,'CT_cross_wind_surface_trace',path,.00065,'cloth','交叉卷绕表面纱线示意','material')
    for side in (-1,1):
        _s3_pipe(g,'CT_package_cradle',[(side*.098,.050,1.24),(side*.098,-.040,1.395)],.008,'steel','筒子摇架')
        _s3_cyl(g,'CT_centring_disc',(side*.098,-.040,1.395),.036,.014,'steel','x','筒子夹持盘','frame',32)
    _s3_box(g,'CT_separator',(.102,0,.77),(.0015,.230,.63),'white','锭位隔板','shell',0)
    _s3_box(g,'CT_brake_pedal',(0,-.120,.075),(.045,.065,.018),'orange','锭子制动及Volcojet脚踏板','frame',.005)
    _s3_pipe(g,'CT_brake_link',[(0,-.120,.084),(0,-.070,.24),(0,0,.42)],.006,'steel','脚踏制动连杆')
    _s3_pipe(g,'CT_Volcojet_air_branch',[(.035,.10,.15),(.035,.06,.40),(0,0,.45)],.0035,'black','Volcojet穿纱气路支管')
    return _s3_unit_finish(g)

def machine_twisting():
    r=e5_root('twisting','CompactTwister系列8机械控制20锭倍捻机','Saurer / Volkmann','CompactTwister series 8',
        '机械控制；VTS-07；1节20锭（双面10+10），207mm锭距；长4.895m/宽0.620m；机械分配传动，非电子伺服版',TWISTER_URL)
    for k,v in {'spindleCount':20,'sectionCount':1,'spindleGaugeMillimetres':207,'machineLengthMetres':4.895,
        'machineWidthMetres':.620,'sectionHeightMetres':1.601,'controlVariant':'mechanical',
        'spindleType':'VTS-07','selectedStationaryPots':20,'selectedStorageDiscs':20,
        'twistsPerSpindleRevolution':2,'selectedFeedPackageDiameterMillimetres':160,
        'selectedDeliveryPackageDiameterMillimetres':220,'electronicServoControlSelected':False,
        'packageConveyorSelected':False,'optionalBalloonLimiterSelected':False}.items():r[k]=v
    # Official p18 overall chain: 2167 head + 2100 section + 628 end = 4895 mm.
    _s3_module(r,'CompactTwister_mechanical_head',(-2.1335,0,0),(2.122,.525,1.54),'机械调节与主传动车头',3)
    _s3_module(r,'CompactTwister_endstock',(1.364,0,0),(.583,.525,1.40),'机械控制型车尾',1)
    sec=empty('CompactTwister_twenty_spindle_section',parent=r,label='完整20锭机节：两侧各10锭',group='frame');sec['sectionIndex']=1;sec['spindlesPerSection']=20
    for yy in (-.275,.275):
        _s3_box(sec,'CT_base_longitudinal',(0,yy,.21),(2.100,.055,.17),'teal','节段落地纵梁')
        for xx in (-1.02,0,1.02):
            _s3_box(sec,'CT_station_frame_upright',(xx,yy,.80),(.045,.045,1.50),'white','机节承重立柱')
            _s3_cyl(sec,'CT_level_foot',(xx,yy,.035),.035,.07,'dark','z','调平地脚','frame',24)
    for zz in (.435,1.13,1.25,1.58):_s3_box(sec,'CT_central_crosshead',(0,0,zz),(2.100,.065,.042),'teal','连续中墙承梁')
    for yy in (-.155,.155):
        _s3_box(sec,'CT_spindle_support_rail',(0,yy,.40),(2.100,.12,.055),'white','锭子支承梁')
        _s3_box(sec,'CT_lower_transmission_cover',(0,yy*1.85,.30),(2.100,.025,.18),'white','切向传动区域检修护板','shell',.008)
    first=e5_twister_position(r)
    for side in (-1,1):
        for j in range(10):
            index=(0 if side<0 else 10)+j+1;xx=-1.035+(j+.5)*.207
            if index==1:g=first;g.location=(xx,side*.155,0);g['positionIndex']=index
            else:g=_s3_clone_tree(first,r,(xx,side*.155,0),'CompactTwister_position',index)
            g['machineSide']='front' if side<0 else 'rear'
            if side>0:g.rotation_euler[2]=math.pi
    # A single functional main motor, since the selected minimum machine is mechanical.
    main=e5_motor(r,'CT_mechanical_main_motor',(-1.24,-.090,.18),(.28,.30,.30),'compact','z',.26)
    main['label']='机械控制型主电机；位置和功率未获装配图核实'
    _s3_box(r,'CT_main_motor_mount',(-1.24,-.090,.347),(.38,.36,.035),'steel','立式主电机承重法兰托板')
    e5_coupling(r,'CT_main_drive_coupling',(-1.24,-.090,.412),.040,.07,'z')
    # Closed tangential belt contacts the inner side of every 25mm-radius spindle whorl.
    belt=[];corners=[(-1.24,-.090,-math.pi,-math.pi/2),(1.15,-.090,-math.pi/2,0),(1.15,.090,0,math.pi/2),(-1.24,.090,math.pi/2,math.pi)]
    for j,(x,y,a,b) in enumerate(corners):
        pg=empty('rotate_CT_main_pulley' if j==0 else 'rotate_CT_belt_guide_'+str(j),(x,y,.440),r,'主带轮' if j==0 else '切向锭带导轮','motor',spin='y')
        _s3_cyl(pg,'CT_belt_pulley',(0,0,0),.040,.024,'dark','z','切向锭带轮','motor',40)
        for zz in (-.014,.014):_s3_cyl(pg,'CT_pulley_flange',(0,0,zz),.045,.005,'steel','z','带轮挡边','motor',40)
        pg['driveRole']='transmission';pg['transmissionEvidence']='tangential_belt_verified_routing_inferred'
        if j>0:_s3_box(r,'CT_idler_support',(x,y,.315),(.08,.08,.23),'teal','导轮承座')
        for k in range(13):
            aa=a+(b-a)*k/12;belt.append((x+.040*math.cos(aa),y+.040*math.sin(aa),.440))
    e5_strip(r,'CT_twenty_spindle_tangential_belt',belt,.018,.002,True,'闭合切向锭带：全部20锭接触，具体布置推定')
    # Main speed is distributed mechanically to overfeed, winding and traverse;
    # do not invent a servo variant on this 20-spindle machine.
    e5_shaft(r,'CT_vertical_mechanical_input',(-1.24,-.09,.44),(-1.24,-.09,1.25),.018,'主传动至机械分配箱立轴')
    _s3_box(r,'CT_mechanical_distribution_guard',(-1.24,0,1.20),(.21,.48,.27),'teal','机械变速/分配传动外罩；未复刻隐藏齿轮','shell',.016)
    e5_shaft(r,'CT_mechanical_crossshaft',(-1.24,-.20,1.25),(-1.24,.20,1.25),.014,'两侧卷绕机械分配横轴')
    for side in (-1,1):
        e5_shaft(r,'CT_friction_lineshaft_'+('front' if side<0 else 'rear'),(-1.24,side*.195,1.25),(1.08,side*.195,1.25),.009,'全10工位卷绕摩擦辊连续传动轴')
        e5_shaft(r,'CT_overfeed_lineshaft_'+('front' if side<0 else 'rear'),(-1.24,side*.190,1.13),(1.08,side*.190,1.13),.008,'全10工位超喂轮连续机械传动轴')
        _s3_box(r,'CT_traverse_motion_rod',(0,side*.295,1.246),(2.10,.010,.012),'steel','机械横动联动杆','motor',.002)
        _s3_pipe(r,'CT_Volcojet_air_main',[(-1.23,side*.055,.15),(1.08,side*.055,.15)],.010,'steel','Volcojet穿纱压缩空气总管')
    # Mechanical adjustment, switching and belt access remain visible on the headstock.
    _s3_box(r,'CT_mechanical_setting_panel',(-2.18,-.280,1.12),(.64,.025,.30),'dark','机械捻度/速度调节面板','shell',.012)
    for xx in (-2.40,-2.18,-1.96):
        _s3_cyl(r,'CT_setting_handwheel',(xx,-.2975,1.12),.045,.025,'steel','y','机械调整手轮','frame',32)
    _s3_cyl(r,'CT_emergency_stop',(-2.91,-.2975,.90),.030,.025,'orange','y','急停开关','shell',24)
    r['selectedMotorAnchors']=1
    return _s3_finish(r)
