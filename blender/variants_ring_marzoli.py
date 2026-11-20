"""Marzoli Galileo MDS2: complete selected 384-spindle conventional ring frame.
Public configuration: 8 x 48, 70 mm, two multi-tangential-belt drive zones,
one-sided suction and automatic tube loader. See variants-ring-marzoli.json.
All spindle anchors are unique. Dimensional detail and routing are not OEM CAD.
"""

def _mr_tag(o,**values):
    for k,v in values.items():o[k]=v
    return o


def _mr_materials():
    for key,col,metal,rough in [('mr_cyan',(.16,.61,.62),.22,.37),('mr_white',(.77,.81,.81),.2,.40),('mr_yellow',(.93,.72,.06),0,.5),('mr_cot',(.47,.29,.42),.03,.58),('mr_yarn',(.92,.79,.40),0,.65)]:
        if key not in M:M[key]=mat(key,col,metal,rough)


def _mr_lathe(parent,key,loc,profile,ma,label,n=28):
    cache=getattr(_mr_lathe,'cache',{});_mr_lathe.cache=cache;tag=(tuple(profile),ma,n)
    if tag not in cache:
        verts=[(r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n),z) for z,r in profile for j in range(n)]
        faces=[(k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for k in range(len(profile)-1) for j in range(n)]
        faces += [tuple(reversed(range(n))),tuple((len(profile)-1)*n+j for j in range(n))]
        me=bpy.data.meshes.new(key+'_shared');me.from_pydata(verts,[],faces);me.materials.append(M[ma]);me.update()
        for f in me.polygons:f.use_smooth=len(f.vertices)==4
        cache[tag]=me
    return _s3_obj(key,cache[tag],loc,parent,label,'material')


def _mr_motor(parent,key,label,loc,axis='x',r=.095,length=.28,style='industrial'):
    m=motor(parent,key,label,loc,axis,r,length,style)
    _mr_tag(m,motorLayoutEvidence='inferred_reference_layout',driveRevision='8.0')
    return m


def _mr_merge(g):
    for c in list(g.children):
        if c.type=='EMPTY':_mr_merge(c)
    _s3_unit_finish(g)


def _mr_clone(source,parent,oldkey,key,loc,index,side):
    mapping={}
    for old in [source,*source.children_recursive]:
        new=old.copy();new.data=old.data if old.type=='MESH' else None
        new.name=old.name.replace(oldkey,key);bpy.context.collection.objects.link(new);mapping[old]=new
        if old.get('driveAnchorId'):new['driveAnchorId']=old['driveAnchorId'].replace(oldkey,key)
        if 'spindleIndex' in old:
            new['spindleIndex']=index;new['machineSide']=side;new['spindleMotorAnchor']='MDS_spindle_motor_'+str(1 if (index-1)%192<96 else 2)
    for old,new in mapping.items():new.parent=parent if old==source else mapping[old.parent]
    g=mapping[source];g.location=loc;g['positionIndex']=index;g['machineSide']=side
    return g


def _mr_cabinet(root,key,xc,length,height,end_grille=False):
    g=E(key,(xc,0,0),root,'MDS2分层封闭机箱','shell')
    B(g,key+'_base',(0,0,.15),(length,1.05,.30),'dark','机箱基础及承台',bevel=.012)
    B(g,key+'_roof',(0,0,height-.025),(length,1.10,.05),'mr_white','白色顶罩','shell',.010)
    for sign in [-1,1]:
        for j in range(max(1,int(length/.75))):
            cols=max(1,int(length/.75));xx=-length/2+(j+.5)*length/cols
            B(g,key+'_door',(xx,sign*.545,height*.49),(length/cols-.018,.035,height*.83),'mr_cyan','青色独立检修门','shell',.008)
            B(g,key+'_upper_white',(xx,sign*.545,height*.93),(length/cols-.018,.036,height*.13),'mr_white','上部白色罩面','shell',.007)
            B(g,key+'_handle',(xx+length/cols*.31,sign*.568,height*.52),(.018,.025,.145),'dark','门锁与检修把手','shell',.003)
            for z in [.32,height-.28]:B(g,key+'_hinge',(xx-length/cols*.41,sign*.568,z),(.026,.019,.055),'steel','门铰链','shell',.002)
    for sx in [-1,1]:
        x=sx*(length/2-.022)
        if end_grille and sx==1:
            # Actual open grid, not a dark solid rectangle covering the fan.
            for j in range(18):B(g,key+'_grille_vertical',(x,-.48+j*.056,height*.54),(.038,.007,height*.84),'mr_white','机头端面通风格栅','shell',.001)
            for j in range(30):B(g,key+'_grille_horizontal',(x,0,.22+j*(height-.38)/29),(.038,1.0,.007),'mr_white','端面通风格栅横筋','shell',.001)
        else:B(g,key+'_end',(x,0,height/2),(.044,1.08,height-.07),'mr_white','端箱立面','shell',.008)
    for x in [-length*.38,length*.38]:
        for y in [-.45,.45]:C(g,key+'_foot',(x,y,.035),.07,.07,'steel','z','调平底脚','frame',24)
    return g


def _mr_belt_loop(parent,key,points,width=.024,thickness=.0025,label='闭合传动带'):
    g=load(parent,key,label,(0,0,0));e5_strip(g,key+'_ribbon',points,width,thickness,True,label)
    _mr_tag(g,driveRole='transmission',transmissionEvidence='functional_geometry_reference_inferred_dimensions')
    return g


def _mr_round_rectangle(x0,x1,y0,y1,r,z):
    result=[]
    for cx,cy,start in [(x1-r,y1-r,0),(x0+r,y1-r,math.pi/2),(x0+r,y0+r,math.pi),(x1-r,y0+r,3*math.pi/2)]:
        for j in range(9):
            a=start+j*math.pi/16;result.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
    return result


def _mr_planar_belt(parent,key,c1,c2,r1,r2,z,width=.018):
    # External tangents between two parallel vertical shafts.
    dx,dy=c2[0]-c1[0],c2[1]-c1[1];angle=math.atan2(dy,dx);d=math.hypot(dx,dy)
    off=math.acos((r1-r2)/d);a=angle+off;b=angle-off
    pts=[]
    for j in range(25):
        t=a+(b+math.tau-a)*j/24;pts.append((c1[0]+r1*math.cos(t),c1[1]+r1*math.sin(t),z))
    for j in range(25):
        t=b+(a-b)*j/24;pts.append((c2[0]+r2*math.cos(t),c2[1]+r2*math.sin(t),z))
    return _mr_belt_loop(parent,key,pts,width,.002,'电机至切向带轮的局部同步带（结构推定）')


def _mr_spinning_position(parent,key,index,side):
    g=E(key,parent=parent,label='MDS2常规环锭完整锭位')
    _mr_tag(g,positionIndex=index,machineSide=side,componentRole='ring_spinning_position')
    spindle=load(g,key+'_spindle','旋转锭子、锭盘与管纱',(0,0,.58),'rotate:y',2.4)
    _mr_tag(spindle,spindleIndex=index,machineSide=side,drivenByTangentialBelt=True,
        spindleMotorAnchor='MDS_spindle_motor_'+str(1 if (index-1)%192<96 else 2))
    C(spindle,key+'_blade',(0,0,.16),.0045,.52,'steel','z','锭杆','roller',24)
    C(spindle,key+'_whorl',(0,0,0),.013,.027,'dark','z','切向带接触锭盘','roller',32)
    C(spindle,key+'_tube',(0,0,.25),.0065,.230,'mr_yellow','z','选定230毫米筒管','material',24)
    _mr_lathe(spindle,key+'_cop',(0,0,.245),[(-.10,.009),(-.08,.016),(.055,.015),(.102,.0065)],'cloth','常规环锭管纱')
    C(g,key+'_bolster',(0,0,.415),.014,.24,'steel','z','锭脚轴承座外形','frame',24)
    B(g,key+'_brake',(0,-.032,.43),(.031,.022,.075),'dark','锭脚制动踏片',bevel=.004)
    B(g,key+'_partition',(.034,0,.91),(.0015,.10,.34),'mr_white','逐锭隔纱板',bevel=.0005)
    T(g,key+'_lappet',(0,0,1.145),.006,.0014,'steel','z','导纱钩','frame')
    P(g,key+'_lappet_support',[(0,.050,1.17),(0,.05,1.145),(0,.006,1.145)],.0035,'steel','导纱钩支承')
    for name,yy,zz,r,spd in [('front',.085,1.32,.0135,1.15),('middle',.145,1.36,.015,.40),('back',.205,1.40,.0135,.21)]:
        lower=load(g,key+'_'+name,'牵伸'+name+'下罗拉',(0,yy,zz),'rotate:x',spd)
        C(lower,key+'_'+name+'_surface',(0,0,0),r,.062,'steel','x','下罗拉工作面','roller',24)
        C(lower,key+'_'+name+'_neck',(0,0,0),.007,.070,'steel','x','连续罗拉轴颈','roller',20)
        top=load(g,key+'_'+name+'_top','牵伸'+name+'摩擦随动胶辊',(0,yy,zz+r+.015),'rotate:x',-spd)
        C(top,key+'_cot',(0,0,0),.015,.046,'mr_cot','x','上胶辊工作面','roller',24)
    # A short double apron follows the slope between middle and front nips.
    for zoff in [-.004,.010]:
        o=B(g,key+'_apron',(0,.126,1.369+zoff),(.043,.065,.005),'black','双皮圈牵伸区','roller',.002);o.rotation_euler.x=.42
    suction=load(g,key+'_flute','单大风道对应本锭吸棉笛口',(0,0,0))
    P(suction,key+'_flute_pipe',[(0,.065,1.29),(0,.10,1.23),(0,.28,1.19)],.0065,'mr_white','断头吸棉笛管')
    _mr_merge(g)
    return g


def _mr_stage_spindles(root,start,span):
    rings={};doffs={};trays={};proto=None;oldkey='MDS_p001'
    for side,sid in [(-1,'A'),(1,'B')]:
        rr=load(root,'MDS_ringrail_'+sid,'全侧钢领板升降',(0,side*.385,.82),'translate:y',.30,.065)
        B(rr,'MDS_ringrail_surface',(0,0,-.014),(span,.067,.020),'mr_cyan','连续钢领板','roller',.004);rings[sid]=rr
        dr=load(root,'MDS_doffrail_'+sid,'全侧自动落纱夹持梁',(0,side*.525,.42),'translate:y',.15,.32)
        B(dr,'MDS_doffer_beam',(0,0,0),(span,.040,.040),'mr_white','连续落纱梁','frame',.004);doffs[sid]=dr
        tray=load(root,'MDS_tray_track_'+sid,'管纱托盘输送链与托盘',(0,side*.505,.16),'translate:x',.10,.020)
        B(tray,'MDS_chain_rail',(0,0,0),(span+.10,.045,.027),'dark','管纱托盘输送轨','roller',.003);trays[sid]=tray
        B(root,'MDS_parking_rail',(0,side*.46,.32),(span,.035,.026),'mr_white','空管停车轨；与管纱托盘分开',bevel=.003)
        for i in range(192):
            idx=i+1+(0 if side<0 else 192);key='MDS_p%03d'%idx;x=start+(i+.5)*.070
            if proto is None:
                g=_mr_spinning_position(root,key,idx,sid);proto=g;g.location=(x,side*.385,0)
            else:g=_mr_clone(proto,root,oldkey,key,(x,side*.385,0),idx,sid)
            if side>0:g.rotation_euler.z=math.pi
            g['sectionIndex']=i//24+1
            ring=load(rr,key+'_ring','44毫米钢领',(x,0,0))
            T(ring,key+'_ring_surface',(0,0,0),.022,.0024,'steel','z','44毫米钢领','roller')
            tv=load(ring,key+'_traveller','纱线拖动的钢丝圈',(0,0,0),'rotate:y',2.0)
            T(tv,key+'_traveller_surface',(0,-side*.022,0),.0029,.0008,'copper','x','钢丝圈','roller')
            grip=load(dr,key+'_grip','落纱夹持器',(x,0,0))
            T(grip,key+'_grip_ring',(0,0,.025),.011,.003,'black','z','夹持口','frame')
            C(grip,key+'_grip_head',(0,0,.045),.016,.026,'mr_white','z','夹持头外壳','frame',20)
            C(tray,key+'_tray_disc',(x,0,.018),.026,.014,'dark','z','管纱托盘','roller',24)
            C(tray,key+'_tray_peg',(x,0,.058),.0045,.073,'steel','z','托盘定位销','roller',16)
            C(root,key+'_parking_tube',(x,side*.46,.45),.0065,.230,'mr_yellow','z','停车轨待换空管','material',20)
            C(root,key+'_parking_peg',(x,side*.46,.355),.004,.06,'steel','z','停车轨管座','frame',16)
            # Three staggered creel rows per side allow full-size coarse roving packages.
            cx=start+((i//3)*3+1.5)*.070;cy=side*(.10+(i%3)*.20)
            supply=load(root,key+'_roving','本锭悬挂粗纱卷装',(cx,cy,2.13))
            _mr_lathe(supply,key+'_roving_yarn',(0,0,0),[(-.21,.018),(-.17,.074),(.16,.074),(.21,.018)],'cloth','悬挂粗纱卷装')
            C(supply,key+'_roving_tube',(0,0,0),.012,.47,'mr_yellow','z','粗纱筒管','material',20)
            C(root,key+'_roving_hanger',(cx,cy,2.43),.011,.16,'steel','z','粗纱吊锭','frame',16)
            # Coordinates are in root space; local Three-Y is Blender-Z.
            yy=lambda v:side*(.385-v)
            fibre=[(cx,cy,1.907),(x,yy(.205),1.67),(x,yy(.205),1.4145),(x,yy(.145),1.376),
                   (x,yy(.085),1.3345),(x,side*.385,1.145),(x+.024,side*.392,1.02),
                   (x,side*(.385+.022),.82),(x,side*(.385+.015),.85)]
            yarn=load(root,key+'_yarn','粗纱—牵伸—钢丝圈—管纱连续路径',(0,0,0))
            yarn['stationYarnPath']=[float(v) for p in fibre for v in (p[0],p[2],-p[1])]
            P(yarn,key+'_thread',fibre,.00075,'mr_yarn','逐锭纱路；精确OEM穿纱尺寸未公开','material')
        for pair in range(96):
            x=start+(pair*2+1)*.070;arm=E('MDS_MT1_weighting_arm',(x,side*.385,0),root,'MT1常规双锭加压摇架')
            if side>0:arm.rotation_euler.z=math.pi
            C(arm,'MDS_arm_hinge',(0,.224,1.466),.019,.052,'steel','x','加压臂铰轴','frame',24)
            lever=B(arm,'MDS_loading_arm',(0,.15,1.47),(.024,.195,.032),'mr_cyan','机械加压摇架手柄',bevel=.006);lever.rotation_euler.x=.30
            for yy,zz in [(.085,1.3485),(.145,1.39),(.205,1.4285)]:C(arm,'MDS_double_cot_axle',(0,yy,zz),.006,.132,'steel','x','双锭上罗拉轴','frame',16)
    return rings,doffs,trays


def _mr_tangential_zone(root,zone,x0,x1):
    prefix='MDS_zone%d'%zone;y=.3705;corner=.025;z=.58
    anchor=_mr_belt_loop(root,prefix+'_tangential_belt',_mr_round_rectangle(x0,x1,-y,y,corner,z),.023,.0028,'独立192锭区闭合切向带')
    _mr_tag(anchor,drivenSpindleCount=192,driveZoneIndex=zone,layoutEvidence='inferred_96_A_plus_96_B_partition')
    for k,(x,yy) in enumerate([(x0+corner,-y+corner),(x0+corner,y-corner),(x1-corner,y-corner),(x1-corner,-y+corner)]):
        g=load(root,prefix+'_corner%d'%(k+1),'切向带转向轮',(x,yy,z),'rotate:y',1.5)
        C(g,prefix+'_wheel',(0,0,0),corner,.032,'dark','z','切向带转向轮；尺寸推定','roller',40)
    # Central motor is below the spindle bed; the local transfer is explicitly inferred.
    mx=x0+corner;my=0
    m=_mr_motor(root,'MDS_spindle_motor_%d'%zone,'多切向带第%d驱动：7.5kW档，每电机192锭'%zone,(mx,my,.29),'z',.115,.30)
    _mr_tag(m,publishedCapacitySpindles=192,publishedPowerKilowatts=7.5,modeledDrivenSpindles=192,
        sharedInverterGroup='MDS_spindle_inverter',scopeEvidence='192_capacity_confirmed_partition_inferred')
    B(root,prefix+'_motor_bridge',(mx,0,.11),(.38,.65,.055),'mr_white','分布式锭子电机承台',bevel=.006)
    for yy in [-.27,.27]:B(root,prefix+'_bridge_leg',(mx,yy,.21),(.045,.045,.24),'mr_white','电机平台支撑',bevel=.004)
    for name,yy,rr in [('input',0,.09),('output',-y+corner,.035)]:
        pg=load(root,prefix+'_'+name+'_pulley','局部传动带轮',(mx,yy,.515),'rotate:y',1.5)
        C(pg,prefix+'_pulley_surface',(0,0,0),rr,.025,'dark','z','局部传动轮；轮径及比值推定','roller',40)
        C(pg,prefix+'_vertical_shaft',(0,0,.030),.009,.105,'steel','z','上下轮轴连接','roller',24)
    _mr_planar_belt(root,prefix+'_transfer_belt',(mx,0),(mx,-y+corner),.0915,.0365,.515)
    return anchor


def _mr_draft_drive(root,end,span):
    # One common front drive and one common middle/rear drive: brochure <=576 diagram.
    _mr_motor(root,'MDS_front_draft_motor','前罗拉独立变频驱动',(end+.67,-.20,1.34),'-x',.12,.32)
    _mr_motor(root,'MDS_middle_rear_motor','中后罗拉独立无刷驱动',(end+.67,.20,1.48),'-x',.09,.28,'servo')
    for key,x,z in [('front',end+.38,1.34),('middle_rear',end+.38,1.48)]:
        tr=load(root,'MDS_'+key+'_distribution','双面牵伸同步带分配组件',(x,0,z))
        for yy in [-.30,0,.30]:C(tr,'MDS_draft_pulley',(0,yy,0),.045,.026,'dark','x','牵伸分配同步带轮','roller',32)
        # Open visible twin-side belt plane, no gear teeth claimed for belt-linked rear rollers.
        P(tr,'MDS_timing_loop',[(0,-.30,-.046),(0,.30,-.046),(0,.345,0),(0,.30,.046),(0,-.30,.046),(0,-.345,0),(0,-.30,-.046)],.005,'black','头端同步带功能分配（精确绕法推定）','motor')
    for side,sid in [(-1,'A'),(1,'B')]:
        for key,off,z in [('front',.085,1.32),('middle',.145,1.36),('back',.205,1.40)]:
            yy=side*(.385-off)
            shaft=load(root,'MDS_'+key+'_shaft_'+sid,'全侧'+key+'罗拉轴',(0,yy,z),'rotate:x',1.0)
            C(shaft,'MDS_draft_lineshaft',(0,0,0),.007,span+.35,'steel','x','贯通短罗拉连接轴','roller',20)
            P(root,'MDS_end_draft_support',[(end+.05,yy,z-.10),(end+.05,yy,z)],.012,'mr_white','牵伸轴端支架')
        midback=load(root,'MDS_middle_back_timing_'+sid,'中后罗拉同步带连接',(end+.16,0,0))
        pts=[(0,side*.24,1.36),(0,side*.18,1.40),(0,side*.15,1.40),(0,side*.21,1.36),(0,side*.24,1.36)]
        P(midback,'MDS_mid_back_belt',pts,.004,'black','中后罗拉同步带；非齿轮传动','motor')


def build_marzoli_mds2_384(root):
    _mr_materials();span=13.440;start=-span/2;end=span/2
    _mr_tag(root,spindleCount=384,selectedSpindleCount=384,selectedSectionCount=8,spindlesPerSection=48,
        spindleGaugeMillimetres=70,selectedRingDiameterMillimetres=44,selectedTubeLengthMillimetres=230,
        machineLengthMetres=19.988,selectedSuction='single',selectedDoffing='automatic_with_tube_loader',
        conventionalRingOnly=True,compactAttachmentSelected=False,capacityMatchedLine=False,
        structuralCompleteness=False,scope='machine',selectedTangentialBelts=2,
        actualScope='384个完整常规环锭位；两电机各192锭。具体纵向分区各96A+96B为重建推定，非OEM锭号表。')
    tail=_mr_cabinet(root,'MDS_tail',start-.525,1.050,1.887)
    head=_mr_cabinet(root,'MDS_head',end+1.608,3.216,2.110,True)
    # Exact published envelope segments: 1.050 + 13.440 + 3.216 + 2.282.
    B(root,'MDS_HMI',(end+2.65,-.578,1.53),(.31,.045,.39),'dark','机头触控屏与驱动参数',bevel=.012)
    B(root,'MDS_HMI_glass',(end+2.65,-.605,1.56),(.255,.012,.28),'glass','参数与配方显示屏',bevel=.006)
    C(root,'MDS_emergency_stop',(end+2.89,-.61,1.34),.035,.030,'orange','y','急停旋钮','frame',24)
    for side in [-1,1]:
        for y,z,w,h in [(.385,.46,.070,.070),(.21,.19,.075,.08),(.25,1.18,.055,.055)]:B(root,'MDS_long_beam',(0,side*y,z),(span,w,h),'mr_white','机身纵向承梁',bevel=.006)
        B(root,'MDS_low_skirt',(0,side*.54,.09),(span,.035,.12),'mr_white','沿机身底部检修裙板','shell',.004)
    for sec in range(8):
        x=start+(sec+.5)*1.680
        for xx in [x-.81,x+.81]:
            B(root,'MDS_section_leg',(xx,0,.62),(.055,.36,1.20),'mr_white','中墙机节承重立柱',bevel=.006)
            B(root,'MDS_cross_foot',(xx,0,.065),(.15,1.06,.12),'mr_white','横向机脚',bevel=.007)
            for sy in [-.48,.48]:C(root,'MDS_adjustable_pad',(xx,sy,.023),.055,.046,'steel','z','地脚调平垫','frame',24)
        B(root,'MDS_creel_column',(x,0,1.88),(.05,.07,1.32),'mr_white','粗纱架独立支柱',bevel=.004)
        B(root,'MDS_creel_crossarm',(x,0,2.51),(.045,1.12,.045),'steel','粗纱吊架横梁',bevel=.003)
        for yy in [-.50,-.30,-.10,.10,.30,.50]:B(root,'MDS_creel_longrail',(x,yy,2.51),(1.680,.032,.035),'steel','六列粗纱吊轨',bevel=.003)
    rings,doffs,trays=_mr_stage_spindles(root,start,span)
    for zone in [1,2]:_mr_tangential_zone(root,zone,start+(zone-1)*span/2+.001,start+zone*span/2-.001)
    _mr_draft_drive(root,end,span)
    # Ring-rail motion is independent of the automatic-doffer mechanism.
    _mr_motor(root,'MDS_ringrail_motor','钢领板独立无配重升降驱动；功率未绑定',(end+.77,-.16,.58),'-x',.085,.25,'gear')
    buildshaft=load(root,'MDS_ringrail_transfer','钢领板公共升降传力轴',(0,-.14,.33),'rotate:x',.25)
    C(buildshaft,'MDS_building_shaft',(0,0,0),.017,span+.50,'steel','x','钢领板传力轴；机构尺寸推定','roller',24)
    _mr_motor(root,'MDS_doffer_motor','自动落纱升降功能驱动；数量及机构推定',(end+1.43,.22,.38),'-x',.085,.25,'gear')
    doffshaft=load(root,'MDS_doff_transfer','自动落纱纵向传力机构',(0,.16,.22),'rotate:x',.20)
    C(doffshaft,'MDS_doff_shaft',(0,0,0),.019,span+.45,'steel','x','自动落纱传力轴示意','roller',24)
    for sec in range(8):
        x=start+(sec+.5)*1.68
        for side in [-1,1]:
            P(root,'MDS_ring_lift_link',[(x,-.14,.33),(x,side*.32,.48),(x,side*.385,.79)],.008,'steel','钢领板无配重升降连杆示意')
            for direction in [-1,1]:P(root,'MDS_doff_parallel_link',[(x-direction*.58,side*.48,.18),(x+direction*.55,side*.525,.40)],.011,'mr_white','照片中落纱平行连杆')
    # One large broken-end suction duct, not two small side ducts or MAC3000 vacuum.
    duct=load(root,'MDS_single_suction_duct','单根大截面断头抽吸总管',(0,0,1.16))
    C(duct,'MDS_duct_wall',(0,0,0),.115,span+.60,'mr_cyan','x','单大风道外壳','shell',40)
    _mr_motor(root,'MDS_suction_motor','单侧抽吸风机：384锭档4kW / 50Hz',(end+2.14,0,.91),'x',.14,.38)
    fan=load(root,'MDS_suction_fan','断头吸棉风机叶轮',(end+2.47,0,.91),'rotate:x',1.8)
    C(fan,'MDS_fan_hub',(0,0,0),.07,.12,'steel','x','抽吸风机轮毂','roller',32)
    for j in range(12):
        a=j*math.tau/12;b=B(fan,'MDS_fan_blade',(0,.17*math.cos(a),.17*math.sin(a)),(.11,.17,.018),'steel','抽吸叶片','roller',.004);b.rotation_euler.x=a
    C(root,'MDS_fan_scroll',(end+2.47,0,.91),.29,.18,'mr_cyan','x','单吸风机蜗壳','shell',48)
    P(root,'MDS_main_suction_connection',[(end+.20,0,1.16),(end+1.90,0,1.16),(end+2.47,0,1.16)],.11,'mr_cyan','单风道至过滤与风机接口','shell')
    P(root,'MDS_exhaust',[(end+2.47,0,1.16),(end+2.47,0,1.86),(end+2.47,.45,1.86)],.095,'mr_white','排风接口；厂房管网未建','shell')
    # Complete 384-position peg-tray/parking-rail system, and selected tube-loader envelope.
    _mr_motor(root,'MDS_tray_motor','管纱托盘输送功能驱动（推定）',(end+.52,.35,.19),'-x',.055,.18,'gear')
    chain=load(root,'MDS_tray_return','双侧托盘回转输送',(end+1.46,0,.16))
    P(chain,'MDS_head_return',[(-1.46,-.505,0),(1.44,-.505,0),(1.56,0,0),(1.44,.505,0),(-1.46,.505,0)],.018,'dark','头端托盘链回转连接')
    lx=end+3.216;loader=_mr_cabinet(root,'MDS_tube_loader',lx+1.141,2.282,1.605)
    # Open intake front, visible inclined cleated chain and upper sorter.
    hopper=load(root,'MDS_loader_hopper','自动管纱装载器料斗',(lx+1.70,0,.65))
    B(hopper,'MDS_hopper_bottom',(0,0,0),(.90,.75,.05),'mr_cyan','空管料斗底',bevel=.008)
    for side in [-1,1]:B(hopper,'MDS_hopper_side',(0,side*.38,.27),(.90,.035,.54),'mr_cyan','空管料斗侧壁','shell',.008)
    elevator=load(root,'MDS_loader_elevator','自动空管提升链',(0,0,0))
    ep=[(lx+.25,-.40,.18),(lx+.75,-.40,.32),(lx+1.12,-.40,1.30),(lx+1.63,-.40,1.39)]
    for shift in [0,.12]:P(elevator,'MDS_elevator_chain',[(x,y+shift,z) for x,y,z in ep],.014,'dark','倾斜空管提升链','roller')
    for j in range(22):
        t=j/21;x=lx+.75+.37*t;z=.32+.98*t
        C(elevator,'MDS_loader_peg',(x,-.34,z),.005,.070,'steel','y','提升链管纱定位销','roller',16)
    _mr_motor(root,'MDS_loader_motor','空管提升链驱动（功能推定）',(lx+1.10,-.15,1.27),'-y',.065,.20,'gear')
    sorter=load(root,'MDS_loader_sorter','空管定向与上盘机构',(lx+.61,0,1.20),'rotate:y',.30)
    C(sorter,'MDS_loader_starwheel',(0,0,0),.17,.06,'steel','z','定向星轮示意','roller',32)
    for j in range(8):
        a=j*math.tau/8;C(sorter,'MDS_sorter_finger',(.14*math.cos(a),.14*math.sin(a),.055),.008,.07,'dark','z','定向指爪示意','roller',16)
    _mr_motor(root,'MDS_sorter_motor','空管定向上盘驱动（功能推定）',(lx+.61,0,.91),'z',.06,.20,'gear')
    for side in [-1,1]:P(root,'MDS_loader_chute',[(lx+.61,side*.13,1.22),(lx+.24,side*.40,.97),(lx+.13,side*.505,.18),(end+2.80,side*.505,.18)],.019,'mr_white','空管至托盘输出通道示意')
    for motor_obj in [o for o in root.children_recursive if o.get('driveRole')=='motor']:_mr_merge(motor_obj)
    _mr_tag(root,selectedMotorAnchors=10,modeledRovingPackages=384,modeledParkingTubes=384,
        modeledPegTrays=384,modeledWeightingArms=192,exactOEMMotorBOMVerified=False)
    return root


BUILDERS={'marzoli_mds2_384':build_marzoli_mds2_384}
