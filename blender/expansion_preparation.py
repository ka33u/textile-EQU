"""TIEPRO/TPF and Super Singe; public-reference reconstruction, not OEM CAD.

Injected dependencies: B/C/T/P, empty/E, M/mat, bpy, math, Vector, motor/load.
Dimensions absent from the brochures are explicitly selected demonstration values.
"""

def _prep_materials():
    for key,col,metal,rough in [
        ('prep_teal',(.08,.61,.57),.3,.32),('prep_blue',(.15,.29,.64),.25,.36),
        ('prep_steel',(.64,.69,.71),.8,.27),('prep_dark',(.04,.055,.065),.4,.38),
        ('prep_cloth',(.87,.85,.70),0,.9),('prep_yarn',(.82,.65,.27),0,.8),
        ('prep_ceramic',(.69,.55,.34),0,.8),('prep_gas',(.92,.55,.04),.2,.4),
        ('prep_water',(.08,.32,.70),.3,.36),('prep_screen',(.02,.10,.15),.1,.26),
        ('prep_sensor',(.44,.12,.14),.3,.32),('prep_white',(.76,.79,.77),.2,.4)]:
        if key not in M:M[key]=mat(key,col,metal,rough)

def _prep_mesh(parent,name,verts,faces,material,label,group='frame'):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();mesh.materials.append(M[material])
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.parent=parent
    obj['label']=label;obj['group']=group;obj['evidenceStatus']='inferred_geometry'
    return obj

def _prep_beam(parent,name,a,b,w=.035,d=.035,ma='prep_steel',label='结构支承'):
    a,b=Vector(a),Vector(b);o=B(parent,name,tuple((a+b)/2),(w,d,(b-a).length),ma,label,'frame',min(w,d)*.12)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def _prep_bearing(parent,name,loc,axis='y',r=.045):
    x,y,z=loc
    if axis=='y':
        B(parent,name+'_foot',(x,y,z-r*.85),(r*3.6,r*1.9,r*.60),'prep_blue','轴承座底脚','frame',.006)
        C(parent,name+'_seat',loc,r*1.5,r*1.30,'prep_blue','y','剖分轴承座','frame',32)
        C(parent,name+'_seal',(x,y-r*.70,z),r*.92,r*.14,'prep_dark','y','轴承密封圈','frame',32)
    else:
        C(parent,name+'_seat',loc,r*1.5,r*1.3,'prep_steel',axis,'轴承座','frame',32)

def _prep_roller(parent,id,label,x,z,r=.07,width=2.0,drive=False,ma='prep_steel'):
    g=load(parent,id,label,(x,0,z),'rotate:z' if drive else None,1.3)
    C(g,id+'_body',(0,0,0),r,width,ma,'y',label,'roller',48)
    C(g,id+'_shaft',(0,0,0),r*.28,width+.22,'prep_steel','y','贯通辊轴','roller',24)
    for y in (-width/2-.075,width/2+.075):_prep_bearing(parent,id+'_bearing',(x,y,z),r=r*.60)
    return g

def _prep_sheet(parent,name,points,width=1.8):
    verts=[(x,y,z) for x,z in points for y in (-width/2,width/2)]
    faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)]
    obj=_prep_mesh(parent,name,verts,faces,'prep_cloth','连续平幅织物','material')
    obj['processPath']=True;obj['physicalSimulation']=False
    for side in (-1,1):P(parent,name+'_selvedge',[(x,side*width/2,z+.001) for x,z in points],.002,'prep_yarn','连续布边','material')
    return obj

def _prep_tangent_path(disks):
    """Short circular wraps joined by exact signed-circle common tangents (XZ)."""
    incoming={};outgoing={}
    for i in range(len(disks)-1):
        x,z,r,s=disks[i];xx,zz,rr,ss=disks[i+1];dx,dz=xx-x,zz-z;distance=math.hypot(dx,dz)
        a=(s*r-ss*rr)/distance;assert abs(a)<1
        nx=a*dx/distance-math.sqrt(1-a*a)*dz/distance
        nz=a*dz/distance+math.sqrt(1-a*a)*dx/distance
        outgoing[i]=(x+s*r*nx,z+s*r*nz);incoming[i+1]=(xx+ss*rr*nx,zz+ss*rr*nz)
    result=[outgoing[0]]
    for i in range(1,len(disks)-1):
        x,z,r,s=disks[i];p=incoming[i];q=outgoing[i]
        result.append(p);a=math.atan2(p[1]-z,p[0]-x);b=math.atan2(q[1]-z,q[0]-x)
        delta=(b-a+math.pi)%math.tau-math.pi
        for j in range(1,19):
            t=a+delta*j/18;result.append((x+r*math.cos(t),z+r*math.sin(t)))
    result.append(incoming[len(disks)-1]);return result

def _prep_parallel_yarns(parent,name,y_start,y_end,z_start,z_end,count=480):
    # Complete selected warp sheet; one mesh retains every end without 960 objects.
    verts=[];faces=[]
    for i in range(count):
        x=-1.08+i*2.16/(count-1);a=Vector((x,y_start,z_start));b=Vector((x,y_end,z_end));v=(b-a).normalized()
        u=v.cross(Vector((1,0,0))).normalized();w=v.cross(u).normalized();k=len(verts)
        for q in (a,b):
            for j in range(5):verts.append(tuple(q+.00065*(u*math.cos(j*math.tau/5)+w*math.sin(j*math.tau/5))))
        for j in range(5):faces.append((k+j,k+(j+1)%5,k+5+(j+1)%5,k+5+j))
    obj=_prep_mesh(parent,name,verts,faces,'prep_yarn','480根完整选定经纱；非厂家额定容量','material');obj['selectedEndCount']=count

def build_warp_tying(root):
    _prep_materials()
    root['selectedWarpEndsPerSheet']=480;root['selectedKnottingWidthMetres']=2.16
    root['structuralCompleteness']=False
    # TPF: narrow wheeled frame, telescopic posts and two aligned clamping systems.
    for x in (-1.27,1.27):
        B(root,'TPF_cast_base',(x,0,.16),(.20,.76,.07),'prep_steel','铸造脚座','frame',.026)
        for y in (-.29,.29):
            C(root,'TPF_castor',(x,y,.075),.065,.032,'prep_dark','x','脚轮','frame',32)
            for dx in (-.025,.025):B(root,'TPF_wheel_fork',(x+dx,y,.122),(.009,.09,.10),'prep_steel','脚轮支叉','frame',.004)
            C(root,'TPF_swivel_stem',(x,y,.17),.018,.08,'prep_steel','z','转向脚轮轴','frame',20)
        C(root,'TPF_outer_column',(x,0,.55),.033,.70,'prep_steel','z','升降立柱套管','frame',32)
        C(root,'TPF_inner_column',(x,0,.90),.026,.48,'prep_steel','z','伸缩立柱','frame',32)
        B(root,'TPF_height_clamp',(x,0,.81),(.12,.10,.07),'prep_dark','高度锁紧夹','frame',.009)
    C(root,'TPF_lower_crossbar',(0,0,.24),.027,2.56,'prep_steel','x','底部横撑','frame',32)
    for y in (-.28,.28):
        B(root,'TPF_longitudinal_rail',(0,y,1.13),(2.62,.052,.07),'prep_steel','夹纱架纵梁','frame',.006)
        for x in (-1.27,1.27):_prep_beam(root,'TPF_post_bracket',(x,0,1.01),(x,y,1.13),.04,.04)
    for y,z in [(-.24,1.19),(.24,1.24)]:
        B(root,'TPF_clamping_lip',(0,y,z),(2.28,.035,.030),'prep_dark','A式平直夹纱口','frame',.004)
        B(root,'TPF_pressure_bar',(0,y+.025,z+.025),(2.28,.026,.022),'prep_steel','夹紧压条','frame',.003)
        for x in (-1.10,0,1.10):
            C(root,'TPF_clamp_pivot',(x,y,z+.05),.011,.055,'prep_steel','y','夹纱杠杆枢轴','frame',16)
            P(root,'TPF_clamp_lever',[(x,y,z+.05),(x,y-.065,z+.07),(x,y-.085,z+.12)],.006,'prep_dark','手动夹纱杠杆')
    _prep_parallel_yarns(root,'TPF_old_warp',-.52,-.035,1.19,1.205)
    _prep_parallel_yarns(root,'TPF_new_warp',.52,.035,1.24,1.235)
    for x in (-.85,.85):
        P(root,'TPF_reed_support',[(x,-.28,1.10),(x,-.36,.91),(x,-.48,.91)],.012,'prep_dark','停经片/钢筘托钩')
    C(root,'TPF_traverse_rail',(0,.36,1.26),.018,2.66,'prep_steel','x','结经头行走导轨','frame',32)
    # Mechanism housing follows the observed TIEPRO photo, not an invented gear cutaway.
    head=load(root,'TIEPRO_carriage','TIEPRO移动结经头',(0,0,1.21),'translate:x',.055,.76)
    head['description']='沿经纱幅宽进给；实际驱动数量及传动未公开，移动仅功能示意。'
    for x in (-.145,.145):
        B(head,'TIEPRO_carriage_saddle',(x,.28,.07),(.055,.20,.07),'prep_steel','结经头后部导轨承托架','frame',.006)
        C(head,'TIEPRO_carriage_roller',(x,.36,.09),.022,.040,'prep_dark','y','沿TPF导轨运行的承重轮；布置推定','frame',32)
        C(head,'TIEPRO_carriage_axle',(x,.36,.09),.006,.075,'prep_steel','y','承重轮轴','frame',20)
    B(head,'TIEPRO_lower_body',(0,.075,.23),(.39,.37,.42),'prep_steel','结经头折弯钣金机体','shell',.025)
    B(head,'TIEPRO_upper_turquoise',(0,.045,.485),(.47,.46,.15),'prep_teal','TIEPRO青绿上盖','shell',.031)
    B(head,'TIEPRO_roof_lid',(0,.045,.566),(.405,.39,.012),'prep_teal','顶部检修盖','shell',.009)
    for x in (-.19,.19):P(head,'TIEPRO_carry_handle',[(x,.15,.56),(x,.15,.65),(x,-.02,.65)],.011,'prep_steel','携带提手')
    B(head,'TIEPRO_display',(0,-.035,.575),(.14,.095,.009),'prep_screen','操作屏幕；非电机','frame',.006)
    for x in (-.041,0,.041):B(head,'TIEPRO_ui_button',(x,-.06,.581),(.025,.024,.004),'prep_gas','操作按键','frame',.002)
    C(head,'TIEPRO_side_handwheel',(.247,.035,.48),.046,.016,'prep_steel','x','侧面调整轮','frame',40)
    B(head,'TIEPRO_front_mount',(0,-.150,.22),(.32,.055,.25),'prep_dark','前部机构安装面','frame',.01)
    B(head,'TIEPRO_lower_yarn_plate',(0,-.205,.008),(.32,.20,.014),'prep_gas','前端导纱底板','frame',.009)
    for x in (-.13,-.07,.07,.13):B(head,'TIEPRO_guide_slot',(x,-.26,.018),(.012,.062,.008),'prep_dark','导纱板槽口','frame',.002)
    # One functional source represents undisclosed internal distribution, not a measured motor count.
    motor(head,'TIEPRO_main_motor','结经头主驱动功能定位；数量/型式待核',(.005,.19,.285),axis='-y',radius=.042,length=.13,style='cartridge')
    drive=load(head,'TIEPRO_main_interface','内部主轴接口；具体分配未公开',(0,.075,.285))
    C(drive,'TIEPRO_interface_shaft',(0,0,0),.012,.13,'prep_steel','y','主轴功能接口','roller',24)
    for code,x,z in [('upper',-.060,.24),('lower',.060,.13)]:
        cone=load(head,'TIEPRO_'+code+'_separator',('上层' if code=='upper' else '下层')+'锥形分纱器',(x,-.205,z),'rotate:z',1.1)
        # Lathed cone with narrow tip, matching public spindle-cone principle.
        profile=[(-.052,.005),(-.040,.012),(-.012,.027),(.030,.034),(.047,.026)]
        vs=[(rr*math.cos(j*math.tau/40),yy,rr*math.sin(j*math.tau/40)) for yy,rr in profile for j in range(40)]
        fs=[(k*40+j,k*40+(j+1)%40,(k+1)*40+(j+1)%40,(k+1)*40+j) for k in range(4) for j in range(40)]
        _prep_mesh(cone,'TIEPRO_'+code+'_cone',vs,fs,'prep_steel','锥形分纱工作表面','roller')
        C(head,'TIEPRO_cone_mount',(x,-.14,z),.040,.026,'prep_dark','y','分纱轴承座','frame',32)
    knotter=load(head,'TIEPRO_knotter','打结工作区；内部机构未公开',(0,-.222,.065),'oscillate:z',1.1,.08)
    C(knotter,'TIEPRO_hook_hub',(0,0,0),.022,.022,'prep_steel','y','打结工作区轮毂外形','roller',28)
    P(knotter,'TIEPRO_hook',[(0,-.016,0),(.025,-.023,.012),(.028,-.024,.030),(.016,-.025,.036)],.003,'prep_steel','打结抓纱钩功能外形','roller')
    cutter=load(head,'TIEPRO_cutter','配对确认后的切纱执行',(0,-.18,.045),'translate:y',1.0,.006)
    B(cutter,'TIEPRO_cutting_blade',(0,0,0),(.092,.012,.008),'prep_steel','切纱刀片外形','roller',.001)
    detector=load(head,'TIEPRO_double_end_sensor','电子双纱检测；传感而非驱动',(.095,-.210,.205))
    B(detector,'TIEPRO_sensor_body',(0,0,0),(.039,.024,.052),'prep_sensor','双纱检测器外观位置推定','frame',.005)
    C(detector,'TIEPRO_sensor_window',(0,-.014,0),.009,.003,'prep_screen','y','检测窗口','frame',20)
    P(head,'TIEPRO_sensor_cable',[(.095,-.19,.22),(.14,-.10,.32),(.13,.15,.38)],.004,'prep_dark','传感器线束')
    for side in (-1,1):
        for z in (.08,.32):C(head,'TIEPRO_face_fastener',(side*.14,-.182,z),.007,.007,'prep_steel','y','机体紧固件','frame',6)
    P(root,'TPF_power_cable',[(0,.23,1.55),(.28,.40,1.20),(.70,.40,.85),(1.27,.10,.85),(1.27,.12,.28)],.008,'prep_dark','结经头供电软缆；预留拖动长度')
    return root

def _prep_fan(parent,id,label,x,y,z,r=.30,material='prep_blue'):
    # Volute + circular inlet + impeller, independent of motor housing.
    housing=empty(id+'_housing',(x,y,z),parent,label+'蜗壳','shell')
    C(housing,id+'_volute',(0,0,0),r,.25,material,'y',label+'圆形蜗壳','shell',64)
    B(housing,id+'_outlet',(r*.60,0,r*.70),(r*.8,.25,r*.65),material,label+'切向出风口','shell',.025)
    C(housing,id+'_inlet',(0,-.145,0),r*.53,.07,'prep_dark','y','风机吸入口','frame',40)
    T(housing,id+'_inlet_ring',(0,-.18,0),r*.54,.012,'prep_steel','y','风机进风法兰','frame')
    imp=load(parent,id+'_impeller',label+'叶轮',(x,y,z),'rotate:z',1.5)
    C(imp,id+'_backplate',(0,0,0),r*.79,.015,'prep_steel','y','叶轮背盘','roller',48)
    for i in range(12):
        a=i*math.tau/12
        blade=B(imp,id+'_blade',(r*.48*math.cos(a),-.045,r*.48*math.sin(a)),(r*.52,.085,.018),'prep_steel','离心叶片','roller',.002)
        blade.rotation_euler.y=-a+.40
    motor(parent,id+'_motor',label+'驱动电机；类型/安装推定',(x,y+.40,z),axis='-y',radius=r*.31,length=.25)
    C(parent,id+'_shaft',(x,y+.20,z),.027,.27,'prep_steel','y','风机同轴连接示意','frame',24)
    B(parent,id+'_mount',(x,y+.25,z-r*.31-.025),(.34,.70,.05),'prep_blue','风机电机托座','frame',.009)
    return imp

def build_singeing(root):
    _prep_materials();root['structuralCompleteness']=False
    root['selectedFabricWidthMetres']=1.8;root['selectedRollerFaceMetres']=2.0
    # Complete selected standalone dry singeing module; optional wet desizing omitted by choice.
    for x in (-3.35,-2.58,-1.25,1.25,2.55,3.35):
        for y in (-1.13,1.13):
            B(root,'SSG_frame_column',(x,y,1.43),(.10,.10,2.76),'prep_blue','落地框架立柱','frame',.012)
            B(root,'SSG_foot',(x,y,.055),(.26,.25,.11),'prep_blue','设备基础底脚','frame',.015)
            for dx in (-.075,.075):C(root,'SSG_anchor_bolt',(x+dx,y,.12),.013,.035,'prep_steel','z','地脚紧固件','frame',6)
        B(root,'SSG_cross_top',(x,0,2.80),(.105,2.38,.10),'prep_blue','顶部跨幅梁','frame',.01)
    for y in (-1.13,1.13):
        B(root,'SSG_upper_stringer',(0,y,2.20),(6.85,.10,.12),'prep_blue','纵向机架梁','frame',.009)
        B(root,'SSG_lower_stringer',(0,y,.24),(6.85,.09,.12),'prep_blue','底部纵梁','frame',.009)
    # Two cleaning heads, each with two direct-driven brush rollers.
    for tag,x in [('pre',-2.52),('post',1.965)]:
        B(root,'SSG_'+tag+'_brush_back',(x,.99,2.40),(.66,.035,.62),'prep_blue','刷毛吸尘箱背板','shell',.014)
        for offset in (-.22,.22):
            B(root,'SSG_'+tag+'_brush_roof',(x+offset,0,2.73),(.22,2.08,.035),'prep_blue','刷毛箱顶板；保留进出布槽','shell',.01)
            B(root,'SSG_'+tag+'_dust_hopper',(x+offset,0,1.98),(.22,2.02,.18),'prep_blue','两侧吸尘斗；中央布槽贯通','shell',.025)
        for j,(dx,dz) in enumerate([(-.09,-.10),(.09,.10)],1):
            bx,bz=x+dx,2.38+dz;id='SSG_'+tag+'_brush_'+str(j)
            brush=_prep_roller(root,id,'前刷毛辊' if tag=='pre' else '后刷毛辊',bx,bz,.088,2.0,True,'prep_dark')
            for row in range(16):
                a=row*math.tau/16
                pts=[(.091*math.cos(a+k*.12),-.99+k*.044,.091*math.sin(a+k*.12)) for k in range(46)]
                P(brush,id+'_bristle_helix',pts,.007,'prep_ceramic','刷毛螺旋毛束','roller')
            motor(root,id+'_motor','交流电机直联刷毛辊',(bx,-1.38,bz),axis='y',radius=.075,length=.26)
            coupling=load(root,id+'_coupling','刷辊同轴直联接口',(bx,-1.17,bz),'rotate:z',1.3)
            C(coupling,id+'_joint',(0,0,0),.025,.12,'prep_steel','y','刷辊直联轴端','roller',28)
            B(root,id+'_motor_shelf',(bx,-1.36,bz-.11),(.28,.38,.07),'prep_blue','刷辊电机固定托座','frame',.009)
            _prep_beam(root,id+'_shelf_strut',(bx,-1.13,bz-.30),(bx,-1.43,bz-.13),.045,.045,'prep_blue','电机托架斜撑')
    # Thermal chamber: two opposite slit burners and four water-cooled guide rolls.
    for y in (-1.15,1.15):
        B(root,'SSG_chamber_lower_side',(0,y,.42),(2.38,.045,.65),'prep_blue','燃烧箱下侧壁','shell',.015)
        B(root,'SSG_chamber_upper_side',(0,y,1.94),(2.38,.045,.52),'prep_blue','燃烧箱上侧壁','shell',.015)
        for x in (-.78,.78):
            door=empty('SSG_chamber_access',(x,y,1.13),root,'燃烧器检修门','shell',explode=[0,-y*.3,0])
            B(door,'SSG_access_panel',(0,0,0),(.68,.032,.68),'prep_blue','带观察孔检修门','shell',.015)
            C(door,'SSG_view_window',(0,-.023 if y<0 else .023,.10),.095,.02,'prep_screen','y','观察窗口','shell',40)
            P(door,'SSG_door_handle',[(.22,-.04,-.07),(.22,-.07,-.07),(.22,-.07,.10),(.22,-.04,.10)],.008,'prep_steel','检修门把手')
    for k,(x,z) in enumerate([(-.29,1.68),(-.29,.84),(.29,1.68),(.29,.84)],1):
        _prep_roller(root,'SSG_water_cooled_roll_'+str(k),'水冷导布辊',x,z,.075,2.0)
        P(root,'SSG_roll_water_branch',[(x,1.13,z),(x,1.31,z),(x,1.31,.45)],.012,'prep_water','水冷辊旋转接头与支管')
    for k,x in enumerate((-.74,.74),1):
        side=1 if x<0 else -1
        burner=load(root,'SSG_burner_'+str(k),'狭缝燃烧器与失电退避工作位',(x,0,1.23))
        C(burner,'SSG_mixing_chamber',(0,0,0),.092,2.05,'prep_blue','y','气体均压混合腔','frame',48)
        B(burner,'SSG_water_jacket',(side*.09,0,0),(.10,2.04,.18),'prep_steel','水冷夹套','frame',.008)
        B(burner,'SSG_refractory',(side*.15,0,0),(.065,2.00,.13),'prep_ceramic','耐火砖狭缝喷口','frame',.005)
        B(burner,'SSG_burner_slit',(side*.188,0,0),(.003,1.92,.008),'prep_dark','连续狭缝；非电机负载','frame',.001)
        for yy in (-1.06,1.06):
            _prep_beam(root,'SSG_burner_pivot_arm',(x,yy,.30),(x,yy,1.23),.055,.045,'prep_blue','燃烧器退避支臂')
            C(root,'SSG_pivot_pin',(x,yy,.30),.028,.10,'prep_steel','y','退避转轴','frame',24)
        P(root,'SSG_burner_gas_branch',[(x,-1.07,1.23),(x,-1.38,1.23),(x,-1.42,.60)],.035,'prep_gas','燃烧器气体支管')
        P(root,'SSG_burner_cooling',[(x,1.05,1.23),(x,1.42,1.23),(x,1.42,.50)],.014,'prep_water','燃烧器水冷回路')
        ign=load(root,'SSG_igniter_'+str(k),'高压点火电极；非旋转电机',(x+side*.19,-1.005,1.26))
        C(ign,'SSG_ignition_ceramic',(0,0,0),.008,.08,'prep_ceramic','y','点火绝缘瓷管','frame',16)
        P(ign,'SSG_ignition_electrode',[(0,-.03,0),(0,.07,0),(side*.008,.08,-.018)],.002,'prep_steel','火花点火杆')
    # Tapered exhaust hood rather than a solid block through the web path.
    v=[(x,y,z) for z,l,w in [(2.20,1.16,1.11),(2.66,.30,.29)] for x,y in [(-l,-w),(l,-w),(l,w),(-l,w)]]
    _prep_mesh(root,'SSG_tapered_hood',v,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'prep_blue','燃烧废气集气罩','shell')
    _prep_fan(root,'SSG_exhaust','燃烧废气排风',.32,0,3.05,.37)
    B(root,'SSG_exhaust_neck',(.32,0,2.73),(.44,.40,.25),'prep_blue','排风连接短管','shell',.012)
    _prep_fan(root,'SSG_combustion_air','助燃空气',-.65,0,2.95,.27)
    P(root,'SSG_air_manifold',[(-.47,-.03,3.15),(-.45,-1.42,3.15),(-.45,-1.42,.60),(.74,-1.42,.60)],.055,'prep_gas','助燃空气/混合供气总管')
    _prep_fan(root,'SSG_dust_suction','独立刷毛吸尘',-2.55,1.70,.72,.31)
    for x in (-2.52,1.965):P(root,'SSG_brush_dust_duct',[(x,.80,1.97),(x,1.68,1.97),(-2.55,1.68,1.45),(-2.55,1.55,.72)],.10,'prep_steel','刷毛吸尘支管；不混入燃烧废气')
    B(root,'SSG_dust_filter_box',(-2.55,2.18,.68),(.90,.62,1.22),'prep_white','独立绒尘收集箱','shell',.025)
    for x in (-2.82,-2.28):C(root,'SSG_filter_cage',(x,2.18,1.40),.16,.45,'prep_white','z','过滤筒外罩','shell',32)
    # Main web transport is a selected functional drive; no OEM motor type claim.
    _prep_roller(root,'SSG_exit_pull','出口牵引辊',3.25,1.46,.11,2.0,True,'prep_dark')
    _prep_roller(root,'SSG_exit_pressure','牵引压辊',3.25,1.67,.095,2.0,False,'prep_dark')
    motor(root,'SSG_transport_motor','牵引驱动功能位置；型号未公开',(3.25,-1.39,1.46),axis='y',radius=.10,length=.30,style='gear')
    joint=load(root,'SSG_transport_coupling','牵引辊联接接口',(3.25,-1.17,1.46),'rotate:z',1.0)
    C(joint,'SSG_transport_join',(0,0,0),.036,.14,'prep_steel','y','牵引联接外形','roller',32)
    B(root,'SSG_transport_mount',(3.25,-1.37,1.30),(.42,.44,.09),'prep_blue','牵引驱动安装座','frame',.01)
    # Steam quench selected instead of optional chemical impregnation vat.
    quench=load(root,'SSG_steam_quench','蒸汽灭火管；外部蒸汽供给',(1.45,0,1.86))
    C(quench,'SSG_quench_header',(0,0,0),.025,2.02,'prep_steel','y','蒸汽灭火喷管','frame',32)
    for j in range(32):C(quench,'SSG_quench_port',(0,-.93+j*.06,.023),.003,.010,'prep_dark','z','蒸汽喷孔','frame',8)
    P(root,'SSG_steam_supply',[(1.45,1.02,1.86),(1.45,1.45,1.86),(1.45,1.45,.24)],.025,'prep_steel','外接蒸汽管')
    # Passive rollers complete the selected actual web path.
    disks=[(-3.65,1.50,.055,1),(-3.32,2.82,.055,1),(-2.92,2.82,.055,-1),(-2.58,.46,.06,-1),(-2.58,2.79,.06,-1),(-1.31,2.79,.06,-1),(-1.31,.42,.06,-1),(-.62,.42,.05,1),(-.29,1.68,.078,1),(-.29,.84,.078,-1),(.29,1.68,.078,1),(.29,.84,.078,-1),(1.28,1.96,.055,1),(1.91,1.96,.055,-1),(1.91,2.80,.055,-1),(2.62,2.80,.055,1),(3.25,1.46,.113,-1),(3.70,1.46,.05,1)]
    for k,(x,z,r,side) in enumerate(disks):
        if k not in (8,9,10,11,16):_prep_roller(root,'SSG_passive_guide_'+str(k),'被动导布辊',x,z,r-.003,2.0)
    _prep_sheet(root,'SSG_complete_web',_prep_tangent_path(disks),1.8)
    # Controls and gas/water instrumentation are distinctly non-motor.
    B(root,'SSG_control_cabinet',(-1.40,-1.72,.86),(.46,.45,1.62),'prep_white','独立电气控制柜','shell',.025)
    B(root,'SSG_operator_screen',(-1.40,-1.952,1.38),(.30,.015,.23),'prep_screen','工艺控制显示器','frame',.008)
    for i in range(5):C(root,'SSG_pushbutton',(-1.55+i*.075,-1.965,1.15),.019,.014,'prep_gas' if i==0 else 'prep_dark','y','按钮/急停','frame',20)
    for k,x in enumerate((-.74,.74),1):
        C(root,'SSG_gas_gauge',(x,-1.49,.89),.06,.035,'prep_steel','y','燃气压力表；非电机','frame',40)
        C(root,'SSG_gauge_face',(x,-1.513,.89),.052,.006,'prep_white','y','压力表盘','frame',40)
        P(root,'SSG_pressure_pickup',[(x,-1.42,.60),(x,-1.42,.89)],.008,'prep_gas','压力取样管')
        for z in (.45,.66):B(root,'SSG_valve_body',(x,-1.42,z),(.13,.13,.10),'prep_steel','气路阀组','frame',.008)
    return root

BUILDERS={'warp_tying':build_warp_tying,'singeing':build_singeing}
