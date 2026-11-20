"""Toyota RX300E with the August 2025 two-head e-draft and basket feeder layout."""
import math


RX_SECTIONS = 21
RX_PITCH = .070
RX_BLOCK = 24 * RX_PITCH
RX_WORK = RX_SECTIONS * RX_BLOCK
RX_LENGTH = 41.035
RX_SIDE_Y = .370
RX_ROLLERS = (('front', .317, 1.145), ('middle', .255, 1.179), ('back', .190, 1.217))
RX_SIDES = (('a', -1), ('b', 1))
RX_BLUE = 'rx_blue'


def rx_profile(name, profile, material, segments=24):
    parts = _drive_v4.Parts()
    parts.lathe(profile, n=segments, axis='z')
    mesh = parts.mesh(name, 'steel')
    mesh.materials.clear()
    mesh.materials.append(M[material])
    return mesh


def rx_end_units(root):
    half = RX_WORK / 2
    # OEM p.10 places the feed basket in line beyond the OE/PN1 head.
    for name, center, length, height in [('ge', -half - .325, .65, 1.705),
                                         ('oe', half + 1.32, 2.64, 1.995)]:
        casing = E('rx_' + name + '_housing', (center, 0, 0), root, '传动车头' if name == 'ge' else '吸棉及换管端', 'shell')
        for sign in (-1,1):
            B(casing, 'end_wall', (sign*(length/2-.015),0,height*.5), (.03,1.11,height-.07), 'white','端部罩板','shell',.009)
            B(casing, 'blue_cheek', (sign*(length/2-.045),0,.275), (.045,1.12,.32), RX_BLUE,'下罩蓝色端板','shell',.012)
            for panel in range(2):
                x=(panel-.5)*length/2
                enamel=RX_BLUE if name=='oe' and panel==1 else 'white'
                B(casing, 'access', (x,sign*.550,height*.49), (length*.49,.027,height*.80),enamel,'可开检修门','shell',.021)
                B(casing, 'stripe', (x,sign*.568,.36), (length*.489,.012,.18),RX_BLUE,'检修门色带','shell',.004)
                B(casing, 'latch', (x+.18,sign*.571,.91), (.027,.015,.116),'dark','门锁拉手','shell',.005)
        B(casing, 'roof', (0,0,height-.019), (length,1.13,.038),'white','顶部检修盖','shell',.022)
        for end in (-1,1):
            for sign in (-1,1):
                C(casing,'foot',(end*(length/2-.16),sign*.42,.044),.067,.088,'black','z','可调底脚','frame',18)
        B(casing,'foundation',(0,0,.115),(length-.07,1.05,.09),'dark','端部型钢底座','frame',.01)
    _s3_hmi(root,(half+1.90,-.60,1.29),'RX300 纺纱和钢领板控制面板')
    for j in range(8):
        B(root,'oe_louver',(half+1.62,-.576,1.14+j*.045),(.53,.020,.014),'dark','风箱检修百叶','shell',.004)
    end_x=RX_LENGTH-half-.65
    feeder=E('rx_basket',(end_x-.533,0,.10),root,'筐式供管单元','frame')
    for y in (-.40,.40):
        B(feeder,'hopper_wall',(0,y,.44),(1.066,.025,.79),'white','补管箱壁','shell',.016)
    for x in (-.521,.521):
        B(feeder,'hopper_end',(x,0,.44),(.024,.80,.79),'white','补管箱端壁','shell',.015)
        for y in (-.34,.34):
            C(feeder,'caster',(x*.87,y,-.036),.063,.037,'dark','y','料箱脚轮','frame',16)
    for j in range(6):
        tube=C(feeder,'empty_tube',((j-2.5)*.105,.02,.71),.014,.209,'orange','y','筒管仓内空管','material',20)
        tube.rotation_euler.z=.10*(j%3-1)
    feed_tower=E('rx_feeder_tower',(half+3.29,0,0),root,'自动给管提升站','frame')
    B(feed_tower,'tower',(0,0,.79),(.61,.81,1.56),RX_BLUE,'提升站防护侧罩','shell',.024)
    conveyor=B(feed_tower,'tube_feeder',(-.30,-.31,.68),(.92,.25,.11),'dark','储管区至输送线的倾斜给管槽','frame',.014)
    conveyor.rotation_euler.y=-.74
    B(feed_tower,'transfer_bed',(0,0,.13),(1.385,.75,.14),'steel','给管站底座','frame',.012)


def rx_drives(root):
    left = -RX_WORK/2
    right = RX_WORK/2
    motor(root,'rx_main','锭子主电机',(right+.62,0,.552),'-x',.160,.48)
    B(root,'main_plinth',(right+.62,0,.287),(.55,.36,.25),'steel','锭子主电机安装承台','frame',.015)
    drum=load(root,'rx_lineshaft','锭带纵向传动轴',(0,0,.552),'rotate:x',2.4)
    C(drum,'line_steel',(.14,0,0),.026,RX_WORK+.45,'steel','x','纵向锭带轴','roller',24)
    for index, (name,y,z) in enumerate(RX_ROLLERS):
        ends=('ge',) if name=='front' else ('ge','oe')
        for head in ends:
            tx=left-.34 if head=='ge' else right+.34
            suffix=name if name=='front' else name+'_'+head
            motor(root,'rx_'+suffix+'_motor',('前','中','后')[index]+'罗拉牵伸伺服 · '+head.upper(),(tx,-.25+index*.25,1.15),'x' if head=='ge' else '-x',.066,.17,'servo')
            drive=load(root,'rx_'+suffix+'_distribution','牵伸分配轴（连接布置推定）',(tx+(.17 if head=='ge' else -.17),0,z),'rotate:z',1.5)
            C(drive,'draft_crossfeed',(0,0,0),.012,2*y,'steel','y','牵伸分配轴','roller',20)
    motor(root,'rx_lift_motor','钢领板升降伺服',(left-.36,.125,.30),'x',.073,.22,'servo')
    shaft=load(root,'rx_lift_shaft','升降纵向传动轴',(0,.125,.30),'rotate:x',1.0)
    C(shaft,'lift_line',(0,0,0),.015,RX_WORK+.24,'steel','x','升降同步轴（布置推定）','roller',20)
    motor(root,'rx_suction_motor','PN1 吸棉风机变频电机',(right+1.32,.05,.94),'x',.114,.32)
    B(root,'fan_mount',(right+1.32,.05,.774),(.38,.30,.11),'steel','吸棉风机安装座','frame',.010)
    fan=load(root,'rx_suction_fan','断头吸棉风机叶轮',(right+1.58,.05,.94),'rotate:x',3.6)
    C(fan,'fan_hub',(0,0,0),.055,.088,'steel','x','叶轮轮毂','roller',24)
    for j in range(10):
        angle=math.tau*j/10
        blade=B(fan,'fan_blade',(0,.117*math.cos(angle),.117*math.sin(angle)),(.071,.129,.017),'steel','离心叶片','roller',.004)
        blade.rotation_euler.x=angle+.38
    for dx in (-.055,.055):
        C(root,'fan_cheek',(right+1.58+dx,.05,.94),.212,.012,RX_BLUE,'x','风机侧板','shell',36)
    P(root,'suction_elbow',[(right-.04,0,.88),(right+.48,.28,.88),(right+1.58,.28,1.07),(right+1.58,.18,1.05)],.066,'steel','单端工艺吸棉总管','frame')
    # The catalogue shows the handling cycle, but does not identify these actuators.
    wheel=load(root,'rx_tbc_wheel','空管给管轮',(right+3.29,0,.98))
    C(wheel,'tbc_dial',(0,0,0),.160,.09,'steel','x','给管机构','roller',28)
    for j in range(8):
        a=math.tau*j/8
        C(wheel,'groove',(0,.135*math.cos(a),.135*math.sin(a)),.014,.10,'dark','x','给管轮工位','roller',14)


def rx_block(root, section):
    center=-RX_WORK/2 + (section-.5)*RX_BLOCK
    base=E('rx_block_%02d' % section,(center,0,0),root,'48 锭整机节','frame')
    base['sectionIndex']=section
    for col in (-.71,0,.71):
        B(base,'cast_post',(col,0,.685),(.055,.095,1.27),'white','铸铁中墙机架','frame',.011)
        B(base,'cast_foot',(col,0,.095),(.11,.79,.095),'dark','横向机脚','frame',.015)
        B(base,'draft_stand',(col,0,1.07),(.063,.61,.09),'steel','左右一体式罗拉支架','frame',.012)
    B(base,'creel_post',(0,0,1.87),(.042,.05,1.43),'steel','粗纱架中柱','frame',.008)
    B(base,'creel_gantry',(0,0,2.619),(.048,1.20,.042),RX_BLUE,'粗纱架横梁','frame',.008)
    B(base,'fiber_duct',(0,0,.89),(RX_BLOCK,.17,.17),'white','断头吸棉风道','frame',.016)
    for row in range(4):
        for _,sign in RX_SIDES:
            B(base,'creel_bar',(0,sign*(.083+.159*row),2.57),(RX_BLOCK,.026,.034),'steel','粗纱吊锭轨道','frame',.004)
    rails={}; doffers={}
    for side,sign in RX_SIDES:
        B(base,'spindle_bed',(0,sign*RX_SIDE_Y,.491),(RX_BLOCK,.125,.048),RX_BLUE,'锭座承重梁','frame',.007)
        B(base,'pegs_track',(0,sign*.52,.191),(RX_BLOCK,.076,.035),'dark','满管及空管输送导轨','frame',.006)
        name='rx_lift_screw_%02d_%s' % (section,side)
        screw=load(base,name,'螺杆积极升降',(0,sign*.294,.656),'rotate:y',1.0)
        C(screw,'screw_surface',(0,0,0),.013,.415,'steel','z','升降丝杆','roller',24)
        for j in range(10):
            C(screw,'thread',(0,0,-.157+j*.034),.016,.006,'dark','z','外露丝杆螺纹示意','roller',16)
        C(base,'lift_guard',(0,sign*.294,.635),.024,.354,'white','z','螺杆密封防积花罩','shell',24)
        rail=load(base,'rx_rail_%02d_%s'%(section,side),'钢领板及 24 个钢领',(0,sign*RX_SIDE_Y,.765),'translate:y',.90,.073)
        B(rail,'ring_beam',(0,-sign*.043,0),(RX_BLOCK,.038,.023),'steel','钢领板纵向梁','roller',.004)
        B(rail,'rail_nut',(0,-sign*.076,-.016),(.049,.054,.048),'dark','钢领板螺母座','roller',.005)
        rails[side]=rail
        doffer=load(base,'rx_doff_%02d_%s'%(section,side),'集体落纱梁及 24 个夹持位',(0,sign*.52,.83))
        B(doffer,'doffing_bar',(0,0,0),(RX_BLOCK,.040,.039),RX_BLUE,'落纱夹持梁','roller',.005)
        for x in (-.53,.53):
            P(base,'doffing_arm',[(x,sign*.33,.43),(x+.065,sign*.49,.75),(x+.05,sign*.52,.83)],.011,'steel','落纱摆臂','roller')
        doffers[side]=doffer
        control=load(base,'rx_balloon_%02d_%s'%(section,side),'气圈控制环与导纱钩支承',(0,sign*RX_SIDE_Y,.895))
        B(control,'balloon_support',(0,-sign*.041,0),(RX_BLOCK,.022,.017),'steel','气圈环支承杆','roller',.003)
        for j in range(24):
            T(control,'balloon_limit',((j-11.5)*RX_PITCH,0,0),.025,.0017,'steel','z','气圈控制环','roller')
        for name,y,z in RX_ROLLERS:
            speed={'front':2.4,'middle':.72,'back':.62}[name]*sign
            splits=(('_ge',-.25*RX_BLOCK,12),('_oe',.25*RX_BLOCK,12)) if section==11 and name!='front' else (('',0,24),)
            for split,offset,count in splits:
                suffix='%s_%02d_%s%s'%(name,section,side,split)
                roller=load(base,'rx_'+suffix,'前罗拉' if name=='front' else '中罗拉' if name=='middle' else '后罗拉',(offset,sign*y,z),'rotate:x',speed)
                cots=load(base,'rx_cots_'+suffix,'摩擦从动上胶辊',(offset,sign*y,z+.028),'rotate:x',-speed)
                C(roller,'lower_line',(0,0,0),.0117,count*RX_PITCH,'steel','x','牵伸下罗拉轴','roller',24)
                for j in range(count):
                    xpos=(j-(count-1)/2)*RX_PITCH
                    C(roller,'flute',(xpos,0,0),.014,.043,'steel','x','罗拉握持区','roller',24)
                    C(cots,'top_cot',(xpos,0,0),.0146,.041,'black','x','上胶辊工作皮面','roller',24)
    return base,rails,doffers


def rx_tape_mesh(parent):
    s=RX_SIDE_Y
    points=[(-.035,-s-.012,0),(.035,-s-.012,0),(.044,-s-.008,0),(.047,-s,0),
            (.043,-s+.010,0),(.019,-.055,.048),(.019,.055,.048),(.043,s-.010,0),
            (.047,s,0),(.044,s+.008,0),(.035,s+.012,0),(-.035,s+.012,0),
            (-.044,s+.008,0),(-.047,s,0),(-.043,s-.010,0),(-.019,.055,-.048),
            (-.019,-.055,-.048),(-.043,-s+.010,0),(-.047,-s,0),(-.044,-s-.008,0)]
    return e5_strip(parent,'rx_tape_web',points,.007,.0017,True,'闭合四锭锭带（绕行示意）').data


def build_rx300e(root):
    M[RX_BLUE]=mat('Toyota blue panels',(.065,.27,.49),.48,.31)
    root['spindleCount']=1008
    root['sectionCount']=RX_SECTIONS
    root['spindlePitchMillimetres']=70
    root['fourSpindleTapeCount']=252
    root['machineLengthMetres']=RX_LENGTH
    rx_end_units(root)
    rx_drives(root)
    bobbin=rx_profile('rx_roving_form',[(-.203,.008),(-.203,.036),(-.164,.073),(.146,.073),(.203,.043),(.203,.009)],'cloth')
    cop=rx_profile('rx_cop_form',[(0,.005),(.013,.009),(.026,.013),(.147,.013),(.174,.0095),(.184,.005)],'cloth')
    rim=rx_profile('rx_ring_section',[(-.003,.019),(-.003,.022),(.002,.022),(.003,.021),(.002,.019)],'steel',36)
    clamp=rx_profile('rx_gripper_profile',[(-.012,.013),(-.012,.018),(.010,.017),(.013,.013)],'dark',20)
    tape_mesh=None
    for section in range(1,RX_SECTIONS+1):
        base,rails,doffers=rx_block(root,section)
        for pair in range(12):
            tape_id=(section-1)*12+pair+1
            xc=(pair-5.5)*2*RX_PITCH
            tape=load(base,'rx_tape_%03d'%tape_id,'四锭锭带组',(xc,0,.552))
            tape['tapeGroupIndex']=tape_id
            tape['drivenSpindleCount']=4
            if tape_mesh is None:
                tape_mesh=rx_tape_mesh(tape)
            else:
                _s3_obj('rx_tape_web',tape_mesh,(0,0,0),tape,'闭合四锭锭带（绕行示意）','roller')
            wheel=load(tape,'rx_drum_%03d'%tape_id,'锭带驱动盘',(0,0,0),'rotate:x',2.4)
            C(wheel,'drive_drum',(0,0,0),.052,.084,'dark','x','锭带驱动盘','roller',32)
            for side,sign in RX_SIDES:
                for slot in (1,2):
                    x=xc+(slot-1.5)*RX_PITCH
                    pos=(tape_id-1)*2+slot
                    spindle=load(base,'rx_spin_%s%03d_%d'%(side,tape_id,slot),'锭子与管纱',(x,sign*RX_SIDE_Y,.552),'rotate:y',3.25)
                    spindle['spindleIndex']=pos+(504 if side=='b' else 0)
                    spindle['machineSide']=side.upper()
                    spindle['tapeGroupIndex']=tape_id
                    C(spindle,'wharve',(0,0,0),.012,.025,'dark','z','受锭带驱动的锭盘','roller',24)
                    C(spindle,'blade',(0,0,.143),.0036,.332,'steel','z','锭杆','roller',18)
                    C(spindle,'tube',(0,0,.185),.0066,.210,'orange','z','210 mm 纱管','material',18)
                    _s3_obj('rx_wound_cop',cop,(0,0,.084),spindle,'管纱成形外轮廓','material')
                    _s3_obj('rx_ring',rim,(x,0,0),rails[side],'38 mm 钢领','roller')
                    B(rails[side],'ring_lug',(x,-sign*.027,-.001),(.035,.028,.006),'steel','钢领连接耳','roller',.0015)
                    C(rails[side],'traveller',(x+.019,0,.0027),.0013,.0035,'copper','y','钢丝圈','roller',10)
                    _s3_obj('rx_tube_grip',clamp,(x,0,-.012),doffers[side],'空管与满管夹持位','roller')
                    C(base,'tube_peg',(x,sign*.52,.226),.0062,.064,'dark','z','筒管输送锭脚','roller',14)
                    row=(pos-1)%4
                    bob_x=(math.floor((pos-1)%24/4)*4-10)*RX_PITCH
                    bob_y=sign*(.083+row*.159)
                    _s3_obj('rx_roving_package',bobbin,(bob_x,bob_y,2.275),base,'粗纱卷装','material')
                    C(base,'hanger',(bob_x,bob_y,2.519),.008,.097,'steel','z','粗纱吊锭','frame',16)
                    P(base,'rx_fibre',[(bob_x,bob_y,2.07),(x,sign*.17,1.34),(x,sign*.19,1.23)],.0017,'cloth','粗纱至后罗拉','material')
                    P(base,'rx_spun_yarn',[(x,sign*.319,1.15),(x,sign*RX_SIDE_Y,1.015),(x+.018,sign*RX_SIDE_Y,.765)],.0011,'cloth','前罗拉经导纱钩至钢领的纱段','material')
                    T(base,'lappet',(x,sign*RX_SIDE_Y,1.015),.0068,.00145,'steel','z','导纱钩','roller')
                    if slot==1:
                        arm=B(base,'weighting_arm',(xc,sign*.246,1.268),(.028,.168,.029),RX_BLUE,'双锭牵伸加压摇架','frame',.008)
                        arm.rotation_euler.x=-.40*sign
                    B(base,'double_apron',(x,sign*.264,1.198),(.040,.060,.010),'dark','双皮圈工作段','roller',.002)


BUILDERS={'toyota_rx300e':build_rx300e}
