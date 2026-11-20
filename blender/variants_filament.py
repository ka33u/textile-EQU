"""Public-reference filament variants; exec with build_expansion's geometry API.

YJ1000V: complete standard 240 yarn positions, three winding decks.
eAFK HQ: complete published 12 x 48 = 576 positions, four winding decks.
eFK EvoSmart: one Smart Godet plus a separately presented EvoHeater component.
Counts are public configuration facts. Unmeasured detailed geometry, routing and
motor envelopes remain inferred. No claim of OEM CAD or complete hidden drives.
"""

def _vf_tag(o, **values):
    for k,v in values.items():o[k]=v
    return o


def _vf_materials():
    for key,name,col,metal,rough in [
        ('vf_blue','Yuejian blue frame',(.035,.25,.49),.25,.38),
        ('vf_white','Texturing warm white enamel',(.72,.76,.78),.23,.39),
        ('vf_red','Barmag DTY red packages',(.53,.035,.055),.02,.68),
        ('vf_yarn','Visible filament path',(.35,.82,.92),.08,.46),
        ('vf_cream','POY package',(.83,.80,.67),0,.78)]:
        if key not in M:M[key]=mat(name,col,metal,rough)


def _vf_merge(g):
    # Preserve semantic empty/drive anchors; only merge static direct meshes.
    for child in list(g.children):
        if child.type=='EMPTY':_vf_merge(child)
    _s3_unit_finish(g)


def _vf_clone(source,parent,oldkey,newkey,loc,index,side,section):
    mapping={}
    for old in [source,*source.children_recursive]:
        new=old.copy()
        if old.type=='MESH':new.data=old.data
        bpy.context.collection.objects.link(new);mapping[old]=new
        new.name=old.name.replace(oldkey,newkey)
        if old.get('driveAnchorId'):new['driveAnchorId']=old['driveAnchorId'].replace(oldkey,newkey)
    for old,new in mapping.items():new.parent=parent if old==source else mapping[old.parent]
    g=mapping[source];g.location=loc
    _vf_tag(g,positionIndex=index,machineSide=side,sectionIndex=section)
    return g


def _vf_motor(parent,key,label,loc,axis='x',radius=.07,length=.18,style='industrial'):
    m=motor(parent,key,label,loc,axis,radius,length,style)
    _vf_tag(m,motorLayoutEvidence='inferred_reference_layout',driveRevision='8.0')
    return m


def _vf_box_cabinet(parent,key,loc,size,color='vf_white'):
    g=E(key,loc,parent,'分片电控及传动端箱','shell');w,d,h=size
    for xx in [-w/2,w/2]:B(g,key+'_side',(xx,0,h/2),(.04,d,h),color,'端箱侧板','shell',.008)
    for yy in [-d/2,d/2]:
        for j in range(3):
            x=-w/2+w*(j+.5)/3
            B(g,key+'_door',(x,yy,h/2),(w/3-.018,.035,h-.10),color,'可开启电控柜门','shell',.008)
            B(g,key+'_handle',(x+w*.10,yy*1.02,h*.52),(.017,.024,.16),'dark','柜门把手','shell',.003)
    B(g,key+'_top',(0,0,h),(w,d,.04),color,'端柜顶板','shell',.008)
    B(g,key+'_base',(0,0,.09),(w,d,.18),'dark','端柜基础')
    B(g,key+'_HMI',(-w*.25,-d/2-.028,h*.66),(.21,.025,.28),'dark','工艺参数操作屏','frame',.006)
    B(g,key+'_screen',(-w*.25,-d/2-.043,h*.69),(.17,.012,.17),'glass','触控显示窗口','frame',.003)
    for zz,ma in [(h+.04,'orange'),(h+.10,'green')]:C(g,key+'_signal',(w*.3,0,zz),.032,.055,ma,'z','设备状态灯',n=20)
    return g


def _vf_channel(parent,key,a,b,label,width=.027,depth=.025,color='vf_white'):
    a,b=Vector(a),Vector(b);d=b-a
    g=load(parent,key,label,tuple(a))
    g.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    # An open U channel leaves the yarn axis free; a shell can be made transparent.
    # The outer cover stops short of the axis endpoints, leaving a free threading
    # mouth where consecutive channels change direction. Nominal path length stays intact.
    cover_length=max(.02,d.length-.06)
    B(g,key+'_back',(0,-depth*.55,d.length/2),(width,.004,cover_length),color,label+'背部','shell',.002)
    for xx in [-width/2,width/2]:B(g,key+'_edge',(xx,0,d.length/2),(.003,depth,cover_length),color,label+'侧壁','shell',.001)
    _vf_tag(g,componentRole='thermal_channel',nominalLength=d.length,dimensionsEvidence='inferred_unless_record_states_length')
    return g


def _vf_roller(parent,key,label,loc,r=.0375,width=.055,axis='x'):
    motion={'x':'rotate:x','y':'rotate:z','z':'rotate:y'}[axis]
    g=load(parent,key,label,loc,motion,.65)
    C(g,key+'_surface',(0,0,0),r,width,'steel',axis,label+'工作表面',n=36)
    C(g,key+'_shaft',(0,0,0),r*.24,width+.03,'dark',axis,label+'轴颈',n=20)
    return g


def _vf_wrap_between(a,b,centre,r):
    """YZ-plane external tangents and an arc; all sampled points stay outside a roller."""
    cy,cz=centre[1:];ay,az=a[1]-cy,a[2]-cz;by,bz=b[1]-cy,b[2]-cz
    da=math.hypot(ay,az);db=math.hypot(by,bz)
    if min(da,db)<=r:raise ValueError('External roller guide must lie outside its radius')
    aa=math.atan2(az,ay);bb=math.atan2(bz,by)
    candidates=[]
    for ta in [aa-math.acos(r/da),aa+math.acos(r/da)]:
        for tb in [bb-math.acos(r/db),bb+math.acos(r/db)]:
            for sign in [-1,1]:
                va=Vector((r*math.cos(ta)-ay,r*math.sin(ta)-az)).normalized()
                vb=Vector((by-r*math.cos(tb),bz-r*math.sin(tb))).normalized()
                if va.dot(Vector((-sign*math.sin(ta),sign*math.cos(ta))))<.999:continue
                if vb.dot(Vector((-sign*math.sin(tb),sign*math.cos(tb))))<.999:continue
                arc=(sign*(tb-ta))%math.tau;candidates.append((arc,ta,sign))
    arc,ta,sign=min(candidates)
    count=max(3,int(arc/.12)+1)
    return [(centre[0],cy+r*math.cos(ta+sign*arc*k/count),cz+r*math.sin(ta+sign*arc*k/count)) for k in range(count+1)]


def _vf_package(parent,key,loc,r=.125,width=.25,ma='vf_cream',moving=True):
    g=load(parent,key,'DTY卷装' if moving else '静止退绕POY卷装',loc,'rotate:x' if moving else None,-.32)
    C(g,key+'_yarn',(0,0,0),r,width,ma,'x','交叉卷绕纱层','material',40)
    C(g,key+'_tube',(0,0,0),.022,width+.028,'copper','x','卷装筒管','material',24)
    P(g,key+'_trace',[(-width/2+width*i/32,r*math.cos(i*math.pi/4),r*math.sin(i*math.pi/4)) for i in range(33)],.0007,'vf_yarn','表层纱线方向','material')
    return g


def _vf_friction(parent,key,loc,individual=False):
    g=load(parent,key,'三轴摩擦盘假捻器；盘径与盘数为结构示意',loc)
    _vf_tag(g,componentRole='friction_texturing_unit',internalTransmissionVerified=False)
    B(g,key+'_plate',(0,0,-.025),(.087,.11,.020),'dark','三轴底板',bevel=.003)
    centres=[(-.022,-.020),(.022,-.020),(0,.018)]
    for k,(x,y) in enumerate(centres):
        spindle=load(g,key+'_shaft%d'%(k+1),'假捻器第%d轴'%(k+1),(x,y,0),'rotate:y',2.1)
        C(spindle,key+'_spindle',(0,0,.065),.006,.17,'steel','z','摩擦轴',n=20)
        for level in range(3):
            z=.020+(3*level+k)*.012
            C(spindle,key+'_disc',(0,0,z),.027,.006,'orange' if level==1 else 'dark','z','错层摩擦盘','roller',32)
        C(spindle,key+'_pulley',(0,0,-.042),.012,.014,'dark','z','内部带轮示意',n=24)
    if individual:
        m=_vf_motor(parent,key+'_motor','独立摩擦器电机', (loc[0],loc[1],loc[2]-.14),'z',.027,.105,'cartridge')
        _vf_tag(m,evidenceStatus='single_driven_friction_aggregate_confirmed',motorCountIsIllustrative=False)
        # Source confirms the aggregate is single driven, not its unseen internal belt train.
    return g


def _vf_position(parent,key,index,hx,wx,deck,hq=False):
    g=E(key,(hx,0,0),parent,'完整纱路与独立卷绕位')
    _vf_tag(g,componentRole='texturing_position',positionIndex=index)
    dx=wx-hx;zpack=.60+deck*.51
    heater_a=(0,.30,3.10);heater_b=(0,1.255,4.858)
    cooler_b=(0,1.955,4.010)
    if hq:
        heater_a=(0,.35,3.32);heater_b=(0,1.28,5.08);cooler_b=(0,2.02,4.13)
    primary=_vf_channel(g,key+'_heater1',heater_a,heater_b,'第一加热器纱道')
    _vf_channel(g,key+'_cooler',heater_b,cooler_b,'冷却导轨',.021,.016,'steel')
    if not hq:primary['publishedEffectiveLength']=2.0
    fy=2.10;fz=3.71 if hq else 3.56
    _vf_friction(g,key+'_friction',(0,fy,fz),hq)
    _vf_roller(g,key+'_G1','第一喂纱辊',(0,.24,3.015))
    _vf_roller(g,key+'_G2','第二喂纱辊',(0,2.12,3.36 if hq else 3.22))
    hy=1.80;top=3.17 if hq else 3.07;bottom=top-(1.46 if not hq else 1.34)
    _vf_channel(g,key+'_heater2',(0,hy,top),(0,hy,bottom),'第二加热定型纱道')
    _vf_roller(g,key+'_G2x','第三喂纱辊',(0,2.12,bottom-.10))
    supply=_vf_package(g,key+'_supply',(dx,-.21,zpack+.03),.13,.25,'vf_cream',False)
    B(g,key+'_supply_bracket',(dx,-.23,zpack-.15),(.30,.25,.025),'vf_white','POY纱架托座（前缘留退绕净空）',bevel=.003)
    # Each process yarn is explicit; thermal channels remain open, without solid-wall crossings.
    start=(0,-.01,2.88);g2=(0,2.12,3.36 if hq else 3.22);g2x=(0,2.12,bottom-.10)
    friction_exit=(0,fy-.065,fz-.01);friction_lower_guide=(0,fy-.085,fz-.235)
    output_guide=(0,2.16,bottom-.10)
    package_entry=(dx,2.61,zpack-.055)
    # Tangential over-end withdrawal begins on the visible supply-package envelope.
    sy,sz=start[1]+.21,start[2]-(zpack+.03)
    supply_angle=math.atan2(sz,sy)-math.acos(.131/math.hypot(sy,sz))
    supply_start=(dx,-.21+.131*math.cos(supply_angle),zpack+.03+.131*math.sin(supply_angle))
    pts=[supply_start,start]
    pts+=_vf_wrap_between(start,heater_a,(0,.24,3.015),.0386)
    pts += [heater_a,heater_b,cooler_b,(0,fy-.010,fz+.19)]
    # Successive contact points follow the inner perimeter of each staggered disc.
    # Keep the strand normal to each 6 mm plate through its thickness, then change
    # direction in the clear axial gap. The exact OEM disc recipe is not asserted.
    disc_centres=[(-.022,-.020),(.022,-.020),(0,.018)]
    for plate in reversed(range(9)):
        cx,cy=disc_centres[plate%3];ll=math.hypot(cx,cy)
        px=cx*(1-.0282/ll);py=fy+cy*(1-.0282/ll);pz=fz+.020+plate*.012
        pts += [(px,py,pz+.0045),(px,py,pz-.0045)]
    pts += [friction_exit,friction_lower_guide]
    pts+=_vf_wrap_between(friction_lower_guide,(0,hy,top),g2,.0386)
    pts += [(0,hy,top),(0,hy,bottom)]
    pts+=_vf_wrap_between((0,hy,bottom),output_guide,g2x,.0386)
    pts += [output_guide]
    if not hq:
        oil_approach=(dx,2.11,zpack-.035)
        oil_centre=(dx,2.31,zpack-.055)
        _vf_roller(g,key+'_oiler','75毫米上油辊',oil_centre,.0375,.25)
        # Open oil trough below the roller; both the roller and fiber are accessible.
        B(g,key+'_oil_trough_base',(dx,2.31,zpack-.105),(.27,.13,.015),'dark','上油槽底',bevel=.003)
        for oy in [2.252,2.368]:B(g,key+'_oil_trough_wall',(dx,oy,zpack-.090),(.27,.012,.025),'vf_white','敞口油槽边壁',bevel=.002)
        pts += [(dx,2.16,zpack-.035),oil_approach]+_vf_wrap_between(oil_approach,package_entry,oil_centre,.0386)+[package_entry]
    else:
        pts += [(dx,2.16,zpack-.055),package_entry]
    # A tangent from the traverse eye terminates on the package surface, never at its centre.
    py,pz=package_entry[1]-2.77,package_entry[2]-zpack
    pa=math.atan2(pz,py)-math.acos(.126/math.hypot(py,pz))
    pts += [(dx,2.77+.126*math.cos(pa),zpack+.126*math.sin(pa))]
    yarn=load(g,key+'_thread','连续纱路；未公开走向按外观推定',(0,0,0))
    yarn['stationYarnPath']=[float(v) for p in pts for v in (p[0],p[2],-p[1])]
    P(yarn,key+'_path',pts,.00095,'vf_yarn','POY→喂纱→加热→冷却→假捻→定型→卷绕','material')
    # Contact geometry is illustrative; OEM disc recipes and contact dynamics are unverified.
    _vf_tag(yarn,routingEvidence='inferred_geometry_not_OEM_threading_chart',contactPathValidated=False)
    # Wrap the output drive drum without penetrating its cylindrical surface.
    roll=load(g,key+'_takeup','卷绕摩擦辊',(dx,2.77,zpack-.175),'rotate:x',.7)
    C(roll,key+'_takeup_roll',(0,0,0),.050,.25,'steel','x','100毫米卷绕辊' if not hq else '卷绕辊（尺寸推定）',n=40)
    pkg=_vf_package(g,key+'_package',(dx,2.77,zpack),.125,.25,'vf_red' if hq else 'vf_cream')
    guide=load(g,key+'_traverse','排纱导眼',(dx,2.61,zpack-.055),'translate:x',.7,.095)
    T(guide,key+'_eye',(0,0,0),.008,.0015,'steel','y','排纱导眼')
    for xx in [dx-.145,dx+.145]:
        P(g,key+'_cradle',[(xx,2.48,zpack-.14),(xx,2.58,zpack),(xx,2.77,zpack)],.008,'vf_white','卷装摇架')
        C(g,key+'_chuck',(xx,2.77,zpack),.03,.026,'dark','x','卷装夹头',n=20)
    for xx in [dx-.10,dx+.10]:B(g,key+'_unit_back',(xx,2.47,zpack-.07),(.10,.035,.35),'vf_white','卷绕单元安装板（中部穿纱开口）','shell',.006)
    B(g,key+'_unit_upper',(dx,2.47,zpack+.105),(.30,.035,.03),'vf_white','穿纱开口上横梁','shell',.004)
    B(g,key+'_unit_key',(dx+.108,2.506,zpack+.04),(.026,.023,.038),'green','单锭操作按钮',bevel=.003)
    if hq:
        doff=load(g,key+'_doffer','单锭自动落筒机构；动力源未公开',(dx,2.47,zpack-.18))
        C(doff,key+'_doff_pivot',(0,0,0),.016,.23,'dark','x','落筒摇臂横轴',n=20)
        for xx in [-.13,.13]:P(doff,key+'_doff_arm',[(xx,0,0),(xx,.16,-.04),(xx,.28,.02)],.009,'steel','落筒推臂')
    return g


def _vf_handling_frame(root,prefix,sections,pitch,decks,blue=False):
    color='vf_blue' if blue else 'vf_white';span=sections*pitch
    for side in [-1,1]:
        for z in [.18,.83,1.86,2.52,3.05]:B(root,prefix+'_longitudinal',(0,side*2.42,z),(span,.085,.095),color,'纵向承重梁',bevel=.006)
        B(root,prefix+'_service_deck',(0,side*2.18,3.04),(span,.72,.065),color,'上部维护走道',bevel=.006)
        for z in [3.48,3.94]:P(root,prefix+'_rail',[(-span/2,side*2.58,z),(span/2,side*2.58,z)],.018,color,'走道护栏')
        for i in range(sections+1):
            x=-span/2+i*pitch
            B(root,prefix+'_post',(x,side*2.42,1.53),(.085,.095,2.92),color,'机节承重柱',bevel=.006)
            B(root,prefix+'_upper_post',(x,side*1.25,4.08),(.065,.065,2.02),color,'上加热架支柱',bevel=.005)
            P(root,prefix+'_triangular_brace',[(x,side*.28,3.08),(x,side*1.25,5.12),(x,side*2.30,3.12)],.026,color,'V形加热器支架')
            P(root,prefix+'_guard_post',[(x,side*2.58,3.07),(x,side*2.58,3.94)],.016,color,'护栏立柱')
            C(root,prefix+'_foot',(x,side*2.42,.065),.075,.13,'dark','z','机架可调地脚',n=24)
        # Winding decks and continuous lower panel seams, not a giant common platform.
        for d in range(decks):
            B(root,prefix+'_deck',(0,side*2.67,.34+d*.51),(span,.60,.045),'vf_white','卷绕层承台',bevel=.004)
        for sec in range(sections):
            x=-span/2+(sec+.5)*pitch
            B(root,prefix+'_lower_service',(x,side*2.98,.22),(pitch-.025,.027,.29),'vf_white','下部独立检修面板','shell',.005)
        # Side maintenance ladder on the head end.
        x=-span/2-.36
        for dx in [-.23,.23]:P(root,prefix+'_ladder_side',[(x+dx,side*3.34,.12),(x+dx,side*2.65,3.08)],.023,color,'上平台检修梯扶手')
        for j in range(12):
            t=(j+.5)/12;P(root,prefix+'_ladder_rung',[(x-.23,side*(3.34-.69*t),.12+2.96*t),(x+.23,side*(3.34-.69*t),.12+2.96*t)],.018,'steel','防滑梯级')
    # Central fixed/rotary supply racks; the package count follows active positions.
    for i in range(sections+1):
        x=-span/2+i*pitch
        for y in [-.62,.62]:B(root,prefix+'_creel_post',(x,y,1.40),(.05,.05,2.72),color,'原丝架立柱',bevel=.003)
    for y in [-.62,.62]:
        for d in range(decks):B(root,prefix+'_creel_rail',(0,y,.46+d*.51),(span,.045,.045),color,'原丝架横梁',bevel=.002)
    return span


def build_yj1000v(root):
    _vf_materials();prefix='YJV';sections=10;pitch=1.440;span=_vf_handling_frame(root,prefix,sections,pitch,3,True)
    _vf_tag(root,selectedPositions=240,selectedWindingDecks=3,modelAssemblyGroups=10,officialSectionCountVerified=False,
        structuralCompleteness=False,scope='machine',routingEvidence='photo_informed_not_OEM_threading_chart',
        dimensionsEvidence='published envelope 18.780 x 6.724 x 5.250 m; detailed placement inferred')
    templates={}
    for side_index,side in enumerate(['A','B']):
        sg=E(prefix+'_side_'+side,(0,0,0),root,'YJ1000V '+side+'侧完整120位')
        if side=='B':sg.rotation_euler.z=math.pi
        sg['machineSide']=side
        for sec in range(sections):
            x=-span/2+(sec+.5)*pitch
            section=E(prefix+'_section_'+side+str(sec+1),(x,0,0),sg,'标准机节分组（按节距重建）')
            _vf_tag(section,sectionIndex=sec+1,machineSide=side)
            for d in range(3):
                for c in range(4):
                    local=d*4+c;n=side_index*120+sec*12+local+1;key='YJV_p%03d'%n
                    hx=(local-5.5)*.110;wx=(c-1.5)*.36
                    if (d,c) not in templates:
                        g=_vf_position(section,key,n,hx,wx,d,False);_vf_merge(g);templates[d,c]=(g,key)
                        _vf_tag(g,sectionIndex=sec+1,machineSide=side)
                    else:
                        source,old=templates[d,c];_vf_clone(source,section,old,key,(hx,0,0),n,side,sec+1)
        # End-drive locations are explicitly illustrative, never OEM motor count claims.
        for j,(name,z) in enumerate([('feed',2.95),('friction',3.57),('wind',.58)]):
            key='YJV_'+name+'_'+side
            m=_vf_motor(sg,key,'功能示意：'+{'feed':'喂纱','friction':'假捻','wind':'卷绕'}[name]+'组驱动',(-span/2-.60,2.15,z),'x',.11,.30)
            _vf_tag(m,evidenceStatus='inferred_functional_drive',motorCountIsIllustrative=True)
            B(sg,key+'_support',(-span/2-.60,2.15,z-.12),(.42,.28,.045),'vf_blue','示意电机承台',bevel=.004)
    _vf_box_cabinet(root,'YJV_head',(-8.28,0,0),(2.10,2.6,2.80))
    _vf_box_cabinet(root,'YJV_tail',(8.40,0,0),(1.92,2.6,2.75))
    # Nominal envelope references are metadata, not extra geometry that changes bounds.
    root['selectedMotorCountIsOEMSpecification']=False
    return root


def build_eafk_hq(root):
    _vf_materials();prefix='HQ';sections=12;pitch=2.40;span=_vf_handling_frame(root,prefix,sections,pitch,4)
    _vf_tag(root,selectedPositions=576,selectedSections=12,selectedPositionsPerSection=48,selectedWindingDecks=4,
        selectedIndependentFrictionMotors=576,scope='machine',structuralCompleteness=False,
        dimensionsEvidence='position/section counts verified; 2.40 m section pitch and detailed dimensions inferred',
        routingEvidence='photo_informed_not_OEM_threading_chart')
    templates={}
    for side_index,side in enumerate(['A','B']):
        sg=E(prefix+'_side_'+side,(0,0,0),root,'eAFK HQ '+side+'侧完整288位')
        if side=='B':sg.rotation_euler.z=math.pi
        sg['machineSide']=side
        for sec in range(sections):
            x=-span/2+(sec+.5)*pitch
            section=E(prefix+'_section_'+side+str(sec+1),(x,0,0),sg,'48位机节的单侧24位')
            _vf_tag(section,sectionIndex=sec+1,machineSide=side)
            for d in range(4):
                for c in range(6):
                    local=d*6+c;n=side_index*288+sec*24+local+1;key='HQ_p%03d'%n
                    hx=(local-11.5)*.095;wx=(c-2.5)*.39
                    if (d,c) not in templates:
                        g=_vf_position(section,key,n,hx,wx,d,True);_vf_merge(g);templates[d,c]=(g,key)
                        _vf_tag(g,sectionIndex=sec+1,machineSide=side)
                    else:
                        source,old=templates[d,c];_vf_clone(source,section,old,key,(hx,0,0),n,side,sec+1)
            # Standard Jumbo Rotary Creel: rotating carrier geometry, drive mechanism not claimed.
            creel=load(section,'HQ_creel_'+side+str(sec+1),'Jumbo Rotary Creel旋转架；容量及内部定位结构推定',(0,-.35,1.32))
            C(creel,'HQ_creel_pivot',(0,0,0),.035,2.58,'steel','z','旋转架竖轴','frame',24)
            for z in [-.80,.80]:C(creel,'HQ_creel_collar',(0,0,z),.105,.045,'dark','z','纱架定位圈','frame',24)
        # Four photographed end motors are retained without invented load assignments.
        for j,z in enumerate([3.42,4.94]):
            key='HQ_visible_end_'+side+str(j+1)
            m=_vf_motor(sg,key,'照片可见端部驱动；负载归属未公开',(-span/2-.32,1.33,z),'-x',.13,.32)
            _vf_tag(m,evidenceStatus='visible_drive_load_unassigned',motorCountIsIllustrative=True)
            B(sg,key+'_support',(-span/2-.32,1.33,z-.15),(.45,.32,.05),'vf_white','端部驱动安装支架',bevel=.005)
    _vf_box_cabinet(root,'HQ_head',(-span/2-1.02,0,0),(1.85,3.0,2.95))
    _vf_box_cabinet(root,'HQ_tail',(span/2+.57,0,0),(.98,2.5,2.95))
    return root


def build_efk_evosmart_station(root):
    _vf_materials()
    _vf_tag(root,scope='station',scopeLabel='公开工位模型',selectedSmartGodets=1,selectedEvoHeaterSamples=1,
        fullMachinePositionCountPublished=False,structuralCompleteness=False,
        actualScope='1套Smart Godet及1个独立EvoHeater插芯组件；两者并置用于技术比较，不表示真实机台位置或连接。')
    # Godet geometry is photo-proportioned, not a published dimensional drawing.
    g=E('EVS_smart_godet_station',(-.42,0,0),root,'Smart Godet公开喂纱组件')
    B(g,'EVS_stand',(0,.14,.34),(.38,.14,.68),'vf_white','教学支架（非OEM机架尺寸）',bevel=.008)
    B(g,'EVS_foot',(0,.10,.025),(.50,.42,.05),'dark','展示支架底脚',bevel=.006)
    B(g,'EVS_mount',(0,.03,.79),(.34,.075,.54),'vf_white','厚板工位安装面板',bevel=.008)
    m=_vf_motor(g,'EVS_smart_godet_motor','Smart Godet独立变频驱动',(0,.18,.75),'-y',.085,.22,'servo')
    _vf_tag(m,evidenceStatus='individual_inverter_drive_confirmed_motor_envelope_inferred',motorCountIsIllustrative=False)
    godet=load(g,'EVS_smart_godet','Smart Godet喂纱辊',(0,-.080,.75),'rotate:z',.8)
    C(godet,'EVS_godet_barrel',(0,0,0),.108,.16,'steel','y','光滑大直径喂纱工作面',n=64)
    C(godet,'EVS_godet_cap',(0,-.084,0),.103,.012,'dark','y','喂纱辊端面',n=64)
    C(godet,'EVS_axial_fastener',(0,-.092,0),.024,.009,'steel','y','端部紧固件',n=32)
    C(godet,'EVS_rear_coupling',(0,.095,0),.023,.04,'steel','y','后置轴端连接示意',n=32)
    separator=load(g,'EVS_separator','无独立电机证据的小分丝辊',(.042,-.08,.995),'rotate:z',-.9)
    C(separator,'EVS_separator_barrel',(0,0,0),.030,.16,'steel','y','小分丝辊',n=48)
    # External common tangents between the main roll and separator, advanced axially each turn.
    c1=Vector((0,.75));c2=Vector((.042,.995));delta=c2-c1
    theta=math.atan2(delta.y,delta.x);offset=math.acos((.1095-.0315)/delta.length)
    a=theta+offset;b=theta-offset;path=[]
    for turn in range(5):
        yy=-.145+turn*.025
        # Main-roll outer arc (away from separator), tangent up to separator, return tangent.
        for k in range(25):
            ang=a+(b+math.tau-a)*k/24
            path.append((c1.x+.1095*math.cos(ang),yy-.010*k/24,c1.y+.1095*math.sin(ang)))
        path.append((c2.x+.0315*math.cos(b),yy-.010,c2.y+.0315*math.sin(b)))
        for k in range(1,17):
            ang=b+(a-b)*k/16
            path.append((c2.x+.0315*math.cos(ang),yy-.010+.035*k/16,c2.y+.0315*math.sin(ang)))
        path.append((c1.x+.1095*math.cos(a),yy+.025,c1.y+.1095*math.sin(a)))
    yarn=load(g,'EVS_godet_yarn','多圈包绕与分丝路径',(0,0,0))
    yarn['stationYarnPath']=[float(v) for p in path for v in (p[0],p[2],-p[1])]
    P(yarn,'EVS_wrap',path,.00095,'vf_yarn','照片支持的多圈导丝；圈数及尺寸推定','material')
    for xx in [-.133,.133]:
        B(g,'EVS_guard',(xx,-.115,.72),(.018,.19,.27),'dark','侧边开口防护片','shell',.009)
        C(g,'EVS_mount_bolt',(xx,-.017,.55),.013,.012,'steel','y','安装板螺钉',n=6)
    C(g,'EVS_green_button',(-.06,-.016,.565),.016,.015,'green','y','绿色状态灯',n=24)
    C(g,'EVS_station_button',(.06,-.016,.565),.021,.015,'white','y','工位操作按钮',n=24)
    # Heater shown separately: no fictitious complete-machine yarn path joins the exhibits.
    heater=load(root,'EVS_evoheater','EvoHeater封闭纱道与可换插芯；单独技术组件',(.43,0,.32))
    _vf_tag(heater,componentRole='evoheater_demonstrator',componentLengthIsInferred=True,connectedToGodetInModel=False)
    B(heater,'EVS_heater_stand',(0,.02,-.17),(.30,.30,.28),'vf_white','独立组件展示支架',bevel=.006)
    # Orient upright to show the full assumed insert length while preserving an actual free bore.
    for xx in [-.040,.040]:B(heater,'EVS_heater_side',(xx,0,.43),(.012,.10,.86),'vf_white','加热器长侧壳','shell',.003)
    B(heater,'EVS_heater_back',(0,.045,.43),(.075,.012,.86),'vf_white','加热器背壳','shell',.003)
    B(heater,'EVS_heater_lid',(0,-.045,.43),(.075,.010,.86),'vf_white','封闭纱道检修盖','shell',.003)
    insert=load(heater,'EVS_heater_insert','抽出展示的可更换插芯',(.12,0,.14))
    for xx in [-.007,.007]:B(insert,'EVS_insert_rail',(xx,0,.43),(.003,.018,.86),'steel','纱道插芯槽壁',bevel=.001)
    B(insert,'EVS_insert_back',(0,.009,.43),(.016,.002,.86),'steel','插芯槽底',bevel=.001)
    B(insert,'EVS_insert_handle',(0,0,-.025),(.045,.045,.06),'dark','抽换插芯握持端',bevel=.006)
    P(heater,'EVS_heater_yarn',[(0,0,-.05),(0,0,.93)],.00095,'vf_yarn','封闭纱道轴线','material')
    for xx in [-.035,.035]:
        P(heater,'EVS_heater_hose',[(xx,.048,.06),(xx,.13,.06),(xx,.15,.18),(xx,.15,.34)],.009,'white','照片可见软管；介质流向未公开')
        C(heater,'EVS_hose_fitting',(xx,.047,.06),.015,.035,'steel','y','管路接头',n=12)
    _vf_merge(g);_vf_merge(heater)
    return root


BUILDERS={'yuejian_yj1000v':build_yj1000v,'barmag_eafk_hq':build_eafk_hq,'barmag_efk_evosmart_station':build_efk_evosmart_station}
