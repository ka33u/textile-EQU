"""Zinser 51 conventional ring spinning, 6 x 48 selected complete positions.
Sources and reconstruction boundaries: research/variants-ring-zinser.json.
All moving spindle nodes carry a unique spindleIndex and explicit machineSide.
"""

def _zr_materials():
    for key,color in [('zr_white',(.78,.83,.86)),('zr_blue',(.025,.20,.43)),('zr_red',(.62,.025,.035)),('zr_cot',(.66,.47,.64)),('zr_yarn',(.93,.79,.41))]:
        if key not in M:M[key]=mat(key,color,.08,.40)


def _zr_lathe(parent,name,loc,profile,ma,label,group='material',n=24):
    key=('ZR_LATHE',tuple(profile),ma,n)
    if not hasattr(_zr_lathe,'cache'):_zr_lathe.cache={}
    mesh=_zr_lathe.cache.get(key)
    if mesh is None:
        verts=[(r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n),z) for z,r in profile for j in range(n)]
        faces=[]
        for k in range(len(profile)-1):
            for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
        faces.extend([tuple(reversed(range(n))),tuple((len(profile)-1)*n+j for j in range(n))])
        mesh=bpy.data.meshes.new(name+'_shared');mesh.from_pydata(verts,[],faces);mesh.materials.append(M[ma]);mesh.update()
        for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
        _zr_lathe.cache[key]=mesh
    return _s3_obj(name,mesh,loc,parent,label,group)


def _zr_separator(parent,loc):
    if not hasattr(_zr_separator,'mesh'):
        yz=[(-.052,.59),(.045,.59),(.045,1.035),(-.052,.985)]
        vv=[(xx,yy,zz) for xx in [-.0012,.0012] for yy,zz in yz]
        ff=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        m=bpy.data.meshes.new('ZR51_separator_shared');m.from_pydata(vv,[],ff);m.materials.append(M['zr_white']);m.update();_zr_separator.mesh=m
    return _s3_obj('ZR51_separator',_zr_separator.mesh,loc,parent,'斜顶隔纱板','guard')


def _zr_cabinet(root,name,xc,length):
    g=E(name,(xc,0,0),root,name,'frame')
    B(g,'cabinet_base',(0,0,.20),(length,1.16,.39),'dark',group='frame',bevel=.022)
    B(g,'cabinet_roof',(0,0,1.70),(length,1.12,.065),'dark',group='guard',bevel=.018)
    for sx in [-1,1]:B(g,'cabinet_end',(sx*(length/2-.025),0,.96),(.05,1.12,1.47),'dark',group='guard')
    for side in [-1,1]:
        B(g,'top_door_header',(0,side*.565,1.62),(length-.03,.045,.11),'dark','检修门上框','guard',.006)
        for col in range(3):
            xx=-length/2+(col+.5)*length/3
            for row in range(2):
                zz=.64+row*.62
                B(g,'access_door',(xx,side*.567,zz),(length/3-.028,.035,.60),'zr_white','双层检修门','guard',.008)
                B(g,'door_handle',(xx+length/3*.31,side*.594,zz),(.027,.024,.12),'dark',group='guard',bevel=.006)
                if row==0:
                    for j in range(4):B(g,'vent_slot',(xx-.16,side*.589,zz-.13+j*.035),(.14,.008,.013),'dark',group='guard',bevel=.001)
        B(g,'inspection_window',(.12,side*.593,1.25),(.29,.012,.36),'glass','驱动区检查窗','guard',.012)
        B(g,'red_brand_strip',(-length*.30,side*.59,1.51),(.43,.012,.039),'zr_red',group='guard')
    for x in [-length*.4,length*.4]:
        for y in [-.46,.46]:C(g,'level_foot',(x,y,.025),.06,.04,'steel','z','可调机脚','frame',16)
    return g


def _zr_unit(root,idx,x,side,ringrail,doffrail):
    sid='A' if side<0 else 'B';pre=f'ZR51_{idx:03d}'
    u=E(pre+'_position',(x,side*.395,0),root,f'{sid}面 {idx:03d} 锭','frame')
    if side>0:u.rotation_euler.z=math.pi
    u['spinningPosition']=idx;u['machineSide']=sid
    spindle=load(u,pre+'_spindle','锭子、锭盘与管纱',(0,0,.54),'rotate:y',2.5)
    spindle['spindleIndex']=idx;spindle['machineSide']=sid;spindle['drivenByTangentialBelt']=True
    C(spindle,'spindle_blade',(0,0,.22),.004,.49,'steel','z','钢锭杆','roller',20)
    C(spindle,'spindle_whorl',(0,0,0),.013,.027,'dark','z','切向锭带接触锭盘','roller',24)
    C(spindle,'spinnfinity',(0,0,.038),.017,.029,'zr_blue','z','Spinnfinity 零卷绕组件','roller',24)
    C(spindle,'red_tube',(0,0,.19),.007,.23,'zr_red','z','230 mm 细纱管','material',20)
    _zr_lathe(spindle,'yarn_cop',(0,0,.18),[(-.086,.018),(-.06,.016),(.055,.011),(.083,.007)],'cloth','成形管纱',n=24)
    C(u,'spindle_bolster',(0,0,.405),.014,.23,'steel','z','锭脚轴承座外壳','frame',20)
    B(u,'spindle_brake',(0,-.035,.46),(.035,.025,.085),'dark','脚踏锭子制动位置','frame',.007)
    _zr_separator(u,(.034375,0,0))
    C(u,'lappet_support',(0,.045,1.105),.006,.11,'steel','y','导纱钩座','frame',16)
    T(u,'lappet',(0,0,1.105),.007,.0017,'steel','z','导纱钩','yarn')
    # A conventional three-line apron draft, without the fourth compacting line.
    for key,yy,zz,rb,rt,spd in [('front',.12,1.25,.0135,.015,1.15),('middle',.197,1.285,.01525,.0125,.40),('back',.269,1.318,.0135,.015,.23)]:
        bot=load(u,pre+'_'+key+'_bot',key+' 下罗拉',(0,yy,zz),'rotate:x',spd)
        C(bot,'bottom_roller',(0,0,0),rb,.062,'steel','x','牵伸下罗拉','roller',24)
        top=load(u,pre+'_'+key+'_top',key+' 上胶辊',(0,yy,zz+rb+rt),'rotate:x',-spd)
        C(top,'top_cot',(0,0,0),rt,.045,'zr_cot' if key=='front' else 'dark','x','摩擦随动上胶辊','roller',24)
        C(u,'roller_bearing',(0,yy,zz),.009,.068,'steel','x','罗拉轴颈','frame',16)
    B(u,'lower_apron',(0,.165,1.296),(.042,.091,.007),'dark','中区下皮圈','roller',.003)
    B(u,'upper_apron',(0,.165,1.313),(.041,.087,.007),'dark','中区上皮圈','roller',.003)
    # One active roving package per spindle, staggered on two creel rows per side.
    ry=.10 if idx%2 else -.15
    roving=load(u,pre+'_roving','被牵伸系统牵引退绕的粗纱',(0,ry,2.07),'rotate:y',.10)
    _zr_lathe(roving,'roving_package',(0,0,0),[(-.16,.017),(-.13,.058),(.12,.058),(.16,.017)],'cloth','粗纱卷装',n=24)
    C(roving,'roving_tube',(0,0,0),.013,.37,'zr_red','z','悬挂粗纱筒管','material',16)
    C(u,'bobbin_hanger',(0,ry,2.29),.014,.10,'steel','z','粗纱吊锭','frame',16)
    T(u,'roving_guide',(0,.269,1.62),.009,.002,'steel','x','粗纱导条器','yarn')
    fibre=load(u,pre+'_fibre','单根粗纱至管纱路径',(0,0,0))
    P(fibre,'material_path',[(0,ry,1.89),(0,.269,1.62),(0,.269,1.351),(0,.197,1.313),(0,.12,1.28),(0,0,1.105),(.020,0,.755),(.012,0,.79)],.0018,'zr_yarn','粗纱—三罗拉牵伸—导纱钩—钢丝圈—管纱','yarn')
    P(u,'suction_flute',[(0,.095,1.21),(0,.15,1.15),(0,.27,1.15)],.007,'zr_white','吸棉笛管','frame')
    # The lifting ring rail belongs to the whole side, not to an electric spindle.
    localx=x-ringrail.location.x
    ring=load(ringrail,pre+'_ring','40 mm 钢领',(localx,0,0))
    T(ring,'spinning_ring',(0,0,0),.020,.0026,'steel','z','40 mm钢领','roller')
    traveller=load(ring,pre+'_traveller','由纱线拖动的钢丝圈',(0,0,0),'rotate:y',2.25)
    T(traveller,'traveller',(0,.020,.001),.0035,.001,'copper','x','钢丝圈','roller')
    grip=load(doffrail,pre+'_grip','Cowemat 真空夹持头',(x-doffrail.location.x,0,0))
    T(grip,'vacuum_gripper',(0,0,0),.010,.0035,'dark','z','真空管纱夹持口','frame')
    C(grip,'gripper_head',(0,0,.016),.016,.025,'zr_white','z','可释放落纱夹持头','frame',16)
    tray=load(root,pre+'_tray','Bobbintray 管纱承载盘',(x,side*.525,.205),'translate:x',.15,.025)
    C(tray,'tray_disc',(0,0,0),.026,.016,'dark','z','承载盘','roller',20)
    C(tray,'tray_peg',(0,0,.036),.005,.065,'steel','z','定位柱','roller',12)
    C(tray,'empty_tube',(0,0,.125),.007,.23,'zr_red','z','待换空管','material',16)


def _zr_fan(root,pre,loc,label,r=.18):
    fan=load(root,pre+'_wheel',label+'叶轮',loc,'rotate:x',1.5)
    C(fan,'fan_disc',(0,0,0),r,.07,'dark','x',label,'roller',32)
    for j in range(10):
        a=j*math.tau/10;b=B(fan,'fan_blade',(0,r*.60*math.cos(a),r*.60*math.sin(a)),(.10,r*.58,.022),'steel',group='roller');b.rotation_euler.x=a
    motor(root,pre+'_motor',label+'电机（外形重建）',(loc[0]-.24,loc[1],loc[2]),'x',r*.56,.26,'industrial')
    C(root,'fan_scroll',(loc[0]+.025,loc[1],loc[2]),r*1.15,.16,'zr_white','x',label+'蜗壳','guard',32)


def build_saurer_zinser_51_ring(root):
    _zr_materials();_zr_units=[];length=18.460;span=9.9;start=-6.307;end=start+span;cx=(start+end)/2
    root['spindleCount']=288;root['selectedSectionCount']=6;root['spindleGaugeMillimetres']=68.75
    root['conventionalRingOnly']=True;root['compactAttachmentSelected']=False;root['siroSelected']=False
    root['machineLengthMetres']=length;root['configurationEvidence']='6节由原厂48锭/节模块表选定，非厂家公开最小机型'
    B(root,'long_foundation',(0,0,.045),(length,1.164,.08),'dark','整机底架','frame')
    head=_zr_cabinet(root,'ZR51_suction_head',-length/2+2.923/2,2.923)
    tail=_zr_cabinet(root,'ZR51_drive_end',end+1.49,2.98)
    B(tail,'hmi_arm',(1.05,-.70,1.34),(.045,.30,.045),'steel','Easyspin 屏支架','frame')
    B(tail,'hmi_frame',(1.05,-.86,1.40),(.47,.10,.32),'dark','Easyspin 操作屏','frame',.015)
    B(tail,'hmi_screen',(1.05,-.917,1.40),(.38,.012,.23),'glass',group='frame',bevel=.008)
    C(tail,'emergency_stop',(1.27,-.927,1.37),.024,.025,'zr_red','y','急停按钮','frame',16)
    for side,sid in [(-1,'A'),(1,'B')]:
        for z,w in [(.12,.12),(.405,.09),(.94,.045)]:B(root,'longitudinal_rail',(cx,side*.30,z),(span,w,.07),'zr_white','机面纵向承梁','frame')
        B(root,'spindle_bearing_rail',(cx,side*.395,.46),(span,.075,.07),'zr_white','连续锭脚梁','frame')
        B(root,'bobbintray_track',(cx,side*.525,.18),(span+.50,.082,.04),'dark','Bobbintray 输送轨道','frame')
        ringrail=load(root,'ZR51_ringrail_'+sid,'整面钢领板升降',(cx,side*.395,.755),'translate:y',.30,.075)
        B(ringrail,'ring_rail',(0,0,-.014),(span,.065,.018),'zr_white','连续钢领板','roller')
        doffrail=load(root,'ZR51_doffrail_'+sid,'Cowemat 整面落纱梁',(cx,side*.565,.45),'translate:y',.18,.26)
        B(doffrail,'doffer_beam',(0,0,0),(span,.045,.045),'zr_white','集体落纱夹持梁','frame')
        suction=load(root,'ZR51_suction_duct_'+sid,'本机面吸棉风道',(cx,side*.13,1.13))
        C(suction,'suction_duct',(0,0,0),.055,span,'dark','x','工艺吸棉主管','frame',24)
        for sec in range(6):
            sx=start+(sec+.5)*1.65
            if side<0:B(root,'section_frame',(sx,0,.65),(1.60,.43,.18),'dark','机节中部脊梁','frame')
            for xx in [sx-.74,sx+.74]:
                B(root,'frame_upright',(xx,side*.24,.65),(.045,.06,1.19),'zr_white','机节立柱','frame')
                C(root,'building_lift_rod',(xx,side*.32,.64),.008,.57,'steel','z','钢领板升降连杆示意','frame',12)
            for sign in [-1,1]:
                bar=B(root,'cowemat_scissor',(sx,side*.54,.25),(1.57,.032,.026),'steel','Cowemat 下部连杆','frame',.005);bar.rotation_euler.y=sign*.11
            for j in range(24):
                idx=(0 if side<0 else 144)+sec*24+j+1;x=start+sec*1.65+(j+.5)*.06875
                _zr_units.append((root,idx,x,side,ringrail,doffrail))
            # Mechanical weighting arms support two neighbouring spindle positions.
            for pair in range(12):
                x=start+sec*1.65+(2*pair+1)*.06875
                arm=E('ZR51_pressure_arm',(x,side*.395,0),root,'双锭机械加压摇架','frame')
                if side>0:arm.rotation_euler.z=math.pi
                lever=B(arm,'blue_loading_lever',(0,.201,1.405),(.023,.20,.039),'zr_blue','机械加压手柄','frame',.008);lever.rotation_euler.x=.44
                C(arm,'arm_hinge',(0,.276,1.36),.025,.047,'steel','x','摇架铰轴','frame',20)
                for yy,zz in [(.12,1.279),(.197,1.313),(.269,1.346)]:C(arm,'paired_top_roller_axle',(0,yy,zz),.006,.13,'steel','x','双锭上罗拉轴','frame',12)
        # Continuous bottom shafts join all 144 spindles on one side.
        for key,yy,zz in [('front',.275,1.25),('middle',.198,1.285),('back',.126,1.318)]:
            tr=load(root,'ZR51_'+key+'_shaft_'+sid,key+' 罗拉传动轴',(cx,side*yy,zz),'rotate:x',1.0)
            C(tr,'draft_shaft',(0,0,0),.008,span+.30,'steel','x','纵向牵伸罗拉轴','roller',16)
        belt=load(root,'ZR51_tangent_belt_'+sid,'切向锭带回路',(cx,side*.336,.54))
        for dy in [-.046,.046]:B(belt,'tangential_strand',(0,dy,0),(span+.90,.009,.025),'black','连续切向锭带','roller',.002)
        for xx in [-span/2-.45,span/2+.45]:
            pulley=load(belt,'ZR51_belt_pulley_'+sid+('_head' if xx<0 else '_tail'),'锭带轮',(xx,0,0),'rotate:y',1.4)
            C(pulley,'belt_wheel',(0,0,0),.047,.037,'steel','z','锭带驱动/回转带轮','roller',24)
        motor(root,'ZR51_spindle_motor_'+sid,'切向带主驱功能位置（轴数待核）',(start-.45,side*.336,.27),'z',.12,.30,'industrial')
        motor(root,'ZR51_doff_motor_'+sid,'Cowemat 升降功能驱动（推定）',(end+.32,side*.42,.37),'x',.075,.22,'gear')
        motor(root,'ZR51_tray_motor_'+sid,'Bobbintray 精密输送驱动（推定）',(end+.34,side*.50,.15),'x',.060,.18,'gear')
    # NSD-i: one large motor and four servos follow the brochure assembly photo.
    drive=load(root,'ZR51_draft_transfer','NSD-i 公共传动箱',(end+.55,0,1.20))
    B(drive,'nsdi_gearcase',(0,0,0),(.38,.50,.38),'dark','NSD-i 传动箱外壳','frame',.025)
    motor(root,'ZR51_draft_front_motor','NSD-i 大电机：前罗拉分配为推定',(end+1.10,0,1.17),'-x',.14,.37,'industrial')
    C(drive,'front_input_coupling',(.25,0,-.03),.035,.19,'steel','x','NSD-i 输入轴联接示意','frame',24)
    for sy in [-1,1]:C(drive,'front_output_coupling',(-.30,sy*.275,.05),.018,.30,'steel','x','前罗拉输出轴示意','frame',20)
    B(root,'nsdi_mounting_deck',(end+.80,0,1.09),(1.10,.83,.055),'steel','NSD-i 安装托板','frame')
    for side,sid in [(-1,'A'),(1,'B')]:
        for key,x,z in [('middle',end+.73,1.49),('back',end+1.12,1.49)]:
            motor(root,'ZR51_draft_'+key+'_motor_'+sid,'NSD-i 伺服：'+sid+key+' 分配为推定',(x,side*.35,z),'-x',.050,.16,'servo')
            link=load(root,'ZR51_draft_'+key+'_coupling_'+sid,'NSD-i 带传动与联轴功能位置',(x-.20,side*.35,z),'rotate:x',.65)
            C(link,'draft_coupling',(0,0,0),.040,.060,'steel','x','驱动联轴器','roller',20)
            targetz=1.285 if key=='middle' else 1.318
            targety=.198 if key=='middle' else .126
            C(root,'servo_input_shaft',(x-.135,side*.35,z),.008,.075,'steel','x','伺服轴联接示意','frame',16)
            C(root,'servo_lower_pulley',(x-.20,side*.35,targetz),.040,.060,'steel','x','NSD-i 从动带轮示意','frame',24)
            P(root,'nsdi_local_belt',[(x-.20,side*.35-.04,z),(x-.20,side*.35-.04,targetz),(x-.20,side*.35+.04,targetz),(x-.20,side*.35+.04,z),(x-.20,side*.35-.04,z)],.008,'dark','NSD-i局部传动带示意','frame')
            B(root,'servo_mounting_bracket',(x+.02,side*.35,1.275),(.06,.13,.33),'steel','伺服安装支架','frame',.005)
            B(root,'roller_transfer_housing',(x-.20,side*(.35+targety)/2,targetz),(.11,.35-targety+.07,.095),'dark','罗拉偏置联接功能示意','frame',.012)
            dx=(x-.20)-(end+.15)
            C(root,'draft_extension_shaft',(end+.15+dx/2,side*targety,targetz),.009,dx,'steel','x','罗拉延伸联接轴示意','frame',16)
    # Building and technological suction are distinct from the drafting drive.
    motor(root,'ZR51_building_motor','钢领板升降驱动功能位置（推定）',(end+.68,0,.62),'x',.085,.24,'gear')
    building=load(root,'ZR51_building_link','钢领板公共升降传力位置',(cx,0,.55),'rotate:x',.20)
    C(building,'building_shaft',(0,0,0),.019,span+.65,'steel','x','升降传力轴示意','roller',20)
    _zr_fan(root,'ZR51_suction_head', (start-1.47,0,.89),'Optisuction 机头吸风',.24)
    _zr_fan(root,'ZR51_suction_tail', (end+2.28,0,.88),'Optisuction 机尾吸风',.24)
    _zr_fan(root,'ZR51_doff_vacuum',(end+1.45,0,.42),'Cowemat 独立真空供给',.11)
    for side,sid in [(-1,'A'),(1,'B')]:
        manifold=load(root,'ZR51_vacuum_manifold_'+sid,'Cowemat 真空分配管',(cx,side*.565,.49))
        C(manifold,'vacuum_manifold',(0,0,0),.012,span,'dark','x','夹持真空分配管','frame',16)
    # Full four-row creel, 288 active roving packages; no paired/siro feeding.
    for yy in [-.545,-.295,.295,.545]:B(root,'roving_creel_rail',(cx,yy,2.34),(span+.35,.034,.034),'steel','粗纱吊锭纵轨','frame')
    for sec in range(7):
        x=start+sec*1.65
        B(root,'creel_column',(x,0,1.70),(.055,.065,1.33),'dark','粗纱架中央立柱','frame')
        B(root,'creel_crossarm',(x,0,2.34),(.045,1.43,.035),'steel','粗纱架横梁','frame')
    # Cowefeed standalone hopper, elevator and sorting station occupy the full rear envelope.
    hx=length/2-.73
    hopper=load(root,'ZR51_cowefeed_hopper','Cowefeed 空管投料仓',(hx,0,.49))
    B(hopper,'hopper_floor',(0,0,0),(1.40,.92,.10),'zr_white','空管仓底','frame')
    for sy in [-1,1]:B(hopper,'hopper_side',(0,sy*.45,.31),(1.40,.04,.62),'zr_white','投料仓侧壁','guard')
    B(hopper,'hopper_rear',(.68,0,.31),(.04,.92,.62),'zr_white','投料仓端壁','guard')
    for i in range(24):
        C(hopper,'loose_empty_tube',(-.56+(i%8)*.15,-.28+(i//8)*.26,.13+(i%3)*.014),.008,.23,'zr_red','y','投料空管示意（仓容量未披露）','material',12)
    elevator=load(root,'ZR51_cowefeed_elevator','Cowefeed 提升输送带',(end+4.02,0,1.00))
    ramp=B(elevator,'elevator_belt',(0,0,0),(2.04,.40,.035),'dark','空管提升带','roller');ramp.rotation_euler.y=.45
    for j in range(16):
        u=-.92+j*.12
        b=B(elevator,'elevator_flight',(u*math.cos(.45),0,-u*math.sin(.45)+.033),(.025,.40,.055),'zr_white','提升带横挡','roller');b.rotation_euler.y=.45
    motor(root,'ZR51_cowefeed_lift_motor','Cowefeed 提升功能驱动（推定）',(end+3.10,-.29,1.41),'y',.065,.19,'gear')
    sorter=load(root,'ZR51_cowefeed_sorter','Cowefeed 空管定向机构',(end+3.04,0,1.32),'rotate:y',.35)
    C(sorter,'sorting_wheel',(0,0,0),.18,.12,'steel','z','定向机构示意','roller',24)
    motor(root,'ZR51_cowefeed_sort_motor','Cowefeed 分选功能驱动（推定）',(end+3.04,0,1.03),'z',.065,.19,'gear')
    B(root,'sorter_guard',(end+3.04,0,1.46),(.51,.52,.04),'glass','分选区检查窗','guard')
    for side in [-1,1]:P(root,'tube_feed_chute',[(end+3.04,side*.16,1.3),(end+2.85,side*.42,.98),(end+2.70,side*.525,.22),(end+.35,side*.525,.22)],.025,'zr_white','空管输出通道示意','frame')
    # The cleaner visible in the current OEM photographs is selected as an accessory.
    B(root,'cleaner_top_rail',(cx,0,2.66),(span+4.0,.065,.075),'steel','巡回清洁器轨道','frame')
    cleaner=load(root,'ZR51_cleaner','巡回吹吸清洁器',(cx-1.0,0,0),'translate:x',.12,1.0)
    B(cleaner,'cleaner_case',(0,0,2.78),(.55,.43,.25),'zr_white','巡回清洁器机壳','guard',.035)
    motor(cleaner,'ZR51_cleaner_travel_motor','清洁器行走驱动（推定）',(.20,.14,2.61),'x',.048,.14,'gear')
    _zr_fan(cleaner,'ZR51_cleaner_blower',(0,0,2.78),'巡回吹吸风',.10)
    for side in [-1,1]:
        P(cleaner,'cleaner_hose',[(0,side*.15,2.89),(.12,side*.72,2.82),(.15,side*.84,1.55),(.15,side*.81,.26)],.037,'dark','巡回清洁吸吹管','frame')
        B(cleaner,'cleaner_nozzle',(.15,side*.81,.22),(.16,.10,.08),'dark','近地吸尘口','frame')
    for args in _zr_units:_zr_unit(*args)
    root['modeledRovingPackageCount']=288;root['modeledWeightingArmCount']=144
    return root

BUILDERS={'saurer_zinser_51_ring':build_saurer_zinser_51_ring}
