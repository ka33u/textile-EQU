"""JWF1217 card and two-head RSB-D 27 draw frame. Dimensions in metres, Blender Z up."""
def panel(root, name, contour, y, thickness, color, label):
    vertices=[(x, y+offset, z) for offset in (-thickness/2,thickness/2) for x,z in contour]
    n=len(contour)
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.materials.append(M[color])
    return _s3_obj(name,mesh,(0,0,0),root,label,'shell')


def roll(root, ident, label, center, radius, width, speed, color='steel',bands=3):
    hub=load(root,ident,label,center,'rotate:z',-speed)
    C(hub,ident+'_drum',(0,0,0),radius,width,color,'y',label,'roller',64)
    C(hub,'axle',(0,0,0),radius*.24,width+.12,'steel','y','辊端轴','roller',36)
    for j in range(bands):
        y=width*((j+.5)/bands-.5)
        T(hub,'clothing_band',(0,y,0),radius,.0035,'steel','y','辊体表面环','roller')
    for sy in (-1,1):
        C(hub,'hub_face',(0,sy*(width/2+.011),0),radius*.64,.019,'dark','y','轴端盖','roller',36)
        for j in range(4):
            a=j*math.pi/2
            C(hub,'hub_stud',(radius*.44*math.cos(a),sy*(width/2+.025),radius*.44*math.sin(a)),
              max(.004,radius*.035),.012,'steel','y','辊端紧固件','roller',8)
    return hub


def turntable(root,ident,label,x,y,z,r,speed):
    node=load(root,ident,label,(x,y,z),'rotate:y',speed)
    C(node,'table',(0,0,0),r,.052,'steel','z',label,'roller',48)
    T(node,'lip',(0,0,.025),r*.92,.013,'dark','z','转盘外缘','roller')
    C(node,'outlet',(r*.42,0,-.031),r*.14,.015,'dark','z','偏心位置标记','roller')
    return node


def cabinet_faces(root,name,x1,x2,y,height,label):
    for side in (-1,1):
        yy=side*y
        for i in range(3):
            xx=x1+(x2-x1)*(i+.5)/3
            B(root,name+'_hatch',(xx,yy,height/2+.15),((x2-x1)/3-.016,.024,height-.16),'white',label,'shell',.02)
            B(root,name+'_handle',(xx+(x2-x1)/9,yy+side*.024,height*.56),(.028,.030,.14),'dark','检修把手','shell',.009)
            for j in range(4):
                B(root,name+'_vent',(xx,yy+side*.014,.31+.043*j),((x2-x1)*.16,.009,.013),'dark','通风槽','shell',.003)


def jingwei_card(root):
    M['jw_green']=mat('JWF enamel green',(.15,.43,.12),.2)
    for y in (-.89,.89):
        B(root,'long_sill',(-.63,y,.14),(3.73,.14,.22),'dark','纵向底梁','frame')
        for x in (-2.37,-1.39,-.04,1.05):C(root,'foot',(x,y,.045),.075,.09,'black','z','调平支脚','frame')
    # The chute, inclined nose and free-standing coiler define the visible outline.
    _s3_module(root,'chute',(-1.93,0,.18),(.77,1.72,3.035),'喂棉箱',2)
    B(root,'chute_green',(-1.93,-.882,2.47),(.74,.029,.63),'jw_green','棉箱上部门板','shell')
    B(root,'chute_window',(-1.93,-.906,2.47),(.54,.014,.32),'glass','储棉观察窗','shell')
    C(root,'feed_duct',(-1.93,0,3.432),.205,.426,'steel','z','输棉接口','frame')
    roll(root,'chute_feed','棉箱给棉罗拉',(-1.88,0,2.23),.086,1.21,.52)
    motor(root,'chute_feed_m','棉箱匀整给棉驱动',(-1.88,-.75,2.23),'y',.071,.21)
    roll(root,'opener','棉箱开松辊',(-2.02,0,1.93),.146,1.21,1.9,'dark')
    roll(root,'chute_out','棉箱输出罗拉',(-1.89,0,.78),.078,1.21,.62)
    B(root,'chute_plate',(-1.78,0,2.19),(.027,1.21,.22),'steel','棉箱弹簧加压给棉板')
    B(root,'lower_chute',(-1.92,.61,1.37),(.43,.045,.77),'steel','下棉箱排风壁')
    blower=load(root,'chute_fan','棉箱循环风轮',(-1.95,.44,2.75),'rotate:z',2.8)
    for j in range(12):
        a=math.tau*j/12
        b=B(blower,'chute_fan_blade',(.143*math.cos(a),0,.143*math.sin(a)),(.092,.094,.019),'steel','循环风机叶片','roller',.003)
        b.rotation_euler.y=-a+.36
    T(root,'chute_fan_ring',(-1.95,.44,2.75),.203,.027,'dark','y','循环风机蜗壳','shell')
    motor(root,'chute_fan_m','棉箱循环风机示意电机',(-1.95,.72,2.75),'-y',.081,.21)
    contour=[(-1.54,.23),(1.19,.23),(1.23,.77),(.61,1.88),(-.10,2.26),(-1.47,2.26)]
    for sign in (-1,1):
        y=sign*1.045
        panel(root,'card_side',contour,y,.039,'white','梳理机侧护罩')
        panel(root,'green_inset',[(-1.47,1.06),(.95,1.06),(.54,1.79),(-.14,2.12),(-1.47,2.12)],y+sign*.026,.014,'jw_green','绿色检修盖板带')
        for x in (-1.12,-.54,.07,.66):
            B(root,'door_gap',(x,y+sign*.044,.66),(.011,.011,.82),'dark','门板接缝','shell')
            B(root,'recessed_handle',(x+.11,y+sign*.052,.85),(.066,.023,.033),'dark','嵌入式拉手','shell')
        for j in range(9):B(root,'inlet_slot',(-1.40,y+sign*.04,.35+j*.055),(.20,.009,.017),'dark','门板格栅','shell')
    for (x1,z1),(x2,z2) in zip(contour[3:],contour[4:]):
        p=B(root,'hood',((x1+x2)/2,0,(z1+z2)/2),(math.hypot(x2-x1,z2-z1),2.10,.041),'white','检修顶罩','shell')
        p.rotation_euler.y=-math.atan2(z2-z1,x2-x1)
    p=B(root,'front_hood',(.915,0,1.325),(1.27,2.10,.045),'dark','倾斜前罩','shell')
    p.rotation_euler.y=math.radians(61)
    rolls=[('cyl','锡林',-.30,1.20,.644,3.0,'dark'),('lick','刺辊',-1.004,.84,.125,5.,'dark'),
           ('feed','给棉罗拉',-1.27,.91,.067,.60,'steel'),('doff','道夫',.54,.65,.353,.80,'teal'),
           ('cal','大压辊',1.15,.94,.084,.9,'steel'),('web1','棉网第一输出辊',.864,.87,.050,1.2,'steel'),
           ('web2','棉网第二输出辊',.921,.943,.042,-1.2,'black'),('web3','棉网第三输出辊',1.00,.896,.041,1.2,'steel')]
    for ident,label,x,z,r,spd,color in rolls:roll(root,ident,label,(x,0,z),r,1.28,spd,color,8 if ident=='cyl' else 3)
    for ident,label,x,z,r in [('cyl','锡林直联永磁同步电机',-.30,1.20,.24),('lick','刺辊变频电机',-1.00,.84,.10),
                               ('feed','给棉伺服电机',-1.27,.91,.062),('doff','道夫伺服电机',.54,.65,.10),
                               ('cal','大压辊伺服电机',1.15,.94,.065),('web','三罗拉伺服电机',.93,.94,.052)]:
        yy=.85 if ident in ('lick','web') else -.85
        motor(root,ident+'_m',label,(x,yy,z),'-y' if yy>0 else 'y',r,.26,'industrial' if ident in ('cyl','lick') else 'servo')
    # Closed revolving-flat circuit, 38 bars in work over the cylinder, 70 on the return.
    arc=[(-.30+.694*math.cos(a),1.20+.694*math.sin(a)) for a in [math.radians(26+i*128/37) for i in range(38)]]
    end=arc[-1];start=arc[0]
    path=[end,(end[0]-.10,end[1]+.12),(end[0]-.08,2.06),(start[0]+.03,2.06),(start[0]+.11,start[1]+.12),start]
    lengths=[math.dist(a,b) for a,b in zip(path,path[1:])]
    def on_return(distance):
        for a,b,length in zip(path,path[1:],lengths):
            if distance<=length:
                fraction=distance/length
                return tuple(x+(y-x)*fraction for x,y in zip(a,b))
            distance-=length
        return path[-1]
    for i,(x,z) in enumerate(arc+[on_return(sum(lengths)*(j+.5)/70) for j in range(70)]):
        B(root,'working_flat' if i<38 else 'return_flat',(x,0,z),(.027,1.31,.022),'steel','工作盖板' if i<38 else '回程盖板','roller',.002)
    for y in (-.665,.665):
        for i in range(len(path)-1):P(root,'guide_rail',[(path[i][0],y,path[i][1]),(path[i+1][0],y,path[i+1][1])],.016,'dark','盖板回程导轨')
    roll(root,'flat_wheel','回转盖板传动轮',(.36,-.68,1.56),.096,.094,.7,'dark')
    motor(root,'flat_m','盖板变频电机',(.36,-.86,1.56),'y',.076,.23)
    for side in (-1,1):
        for i in range(10):
            a=math.radians(4+i*2.0 if side>0 else 158+i*2.0)
            B(root,'fixed_flat',(-.30+.683*math.cos(a),0,1.20+.683*math.sin(a)),(.017,1.28,.022),'dark','固定盖板','roller',.002)
        for j in range(3):
            x=-.30+side*(.48+.09*j)
            P(root,'web_cleaner',[(x,-.67,1.68-.10*j),(x,.67,1.68-.10*j)],.019,'steel','棉网清洁器')
    for j in range(2):
        B(root,'lick_plate',(-1.08+j*.10,0,.69),(.06,1.28,.018),'steel','刺辊分梳板','roller')
        B(root,'trash_knife',(-1.12+j*.14,0,.72),(.016,1.28,.030),'dark','刺辊除尘刀','roller')
    P(root,'suction_trunk',[(-2.10,.77,.28),(1.10,.77,.28)],.094,'steel','吸落棉总管')
    suction=[('前车肚吸口',.65,.32),('锡林漏底吸口',-.32,.50),('刺辊第二落杂区吸口',-.98,.65),
        ('刺辊第一落杂区吸口',-1.12,.67),('刺辊放气罩吸口',-1.10,1.04),('后下清洁器吸口',-.89,1.46),
        ('后上清洁器吸口',-.74,1.68),('后盖板杂质吸口',-.99,1.56),('盖板花吸口',-.53,1.96),
        ('盖板飞花吸口',-.20,2.04),('前盖板杂质吸口',.28,1.69),('前上清洁器吸口',.11,1.70),
        ('前下清洁器吸口',.34,1.52),('三罗拉清洁吸口',.90,1.05),('喇叭口吸口',1.11,1.03),
        ('圈条器吸口',1.87,1.28),('盖板传动吸口',.36,1.58)]
    for label,x,z in suction+[(label,x,z) for label,x,z in (suction[j] for j in (0,1,3,8,13))]:
        yy=-.67 if any(o.get('label')==label for o in root.children) else .67
        P(root,'suction_tap',[(x,yy,z),(x,yy+.085,z),(x+.06,yy+.085,z-.06)],.018,'steel',label)
    for name,x,z,r in [('锡林漏底',-.30,1.20,.68),('道夫漏底',.54,.65,.38)]:
        for j in range(9):
            theta=math.radians(216+j*10)
            b=B(root,'undercase',(x+r*math.cos(theta),0,z+r*math.sin(theta)),(r*.18,1.33,.014),'dark',name,'shell',.002)
            b.rotation_euler.y=-(theta+math.pi/2)
    B(root,'apron',(1.27,0,.94),(.26,.51,.027),'black','皮圈导棉装置','roller')
    for x,z,label in [(-1.27,.99,'棉层厚度检测'),(1.30,1.01,'生条重量检测')]:
        B(root,'transducer',(x,-.18,z),(.07,.06,.044),'dark',label)
    P(root,'output_bridge',[(1.15,0,.94),(1.46,0,1.35),(1.94,0,1.35)],.022,'cloth','输出生条','material')
    for y in (-.62,.62):B(root,'coiler_upright',(1.86,y,.73),(.10,.09,1.41),'white','圈条支架')
    B(root,'coiler_cover',(2.10,0,1.49),(.99,1.37,.17),'white','圈条器顶罩','shell')
    turntable(root,'coil','圈条盘',2.16,0,1.374,.45,1.1)
    motor(root,'coil_m','圈条伺服电机',(1.87,.46,1.31),'z',.080,.18,'servo')
    _s3_can(root,(2.16,0,0),1.00,1.19,'直径 1000 mm 生条筒')
    _s3_can(root,(2.16,1.045,0),1.00,1.19,'换筒待用条筒')
    for x in (1.65,2.67):B(root,'can_track',(x,.49,.04),(.038,2.14,.041),'steel','直线换筒导轨')
    pusher=load(root,'card_pusher','直线换筒推送件',(2.16,.52,.10),'translate:z',.62,.16)
    B(pusher,'can_pusher',(0,0,0),(.90,.055,.091),'steel','推筒横杆','roller')
    cutter=load(root,'card_cutter','机外切条部件',(1.85,-.12,1.34))
    B(cutter,'cutter_jaw',(0,0,0),(.13,.066,.056),'steel','机外切条夹口','roller')
    _s3_hmi(root,(.78,-1.10,1.51),'梳棉操作屏')


def rieter_drawing(root):
    M['rieter_mint']=mat('Rieter light green enamel',(.37,.61,.49),.23)
    # Two 3 × 2 can banks feed independently levelled heads from the power creel.
    for i,sy in enumerate((-1,1),1):
        y=.82*sy; head=E('delivery_'+str(i),(0,y,0),root,f'第 {i} 眼独立并条单元','frame')
        ident=lambda key: key+str(i)
        for j in range(3):
            x=-5.26+j*1.20
            for t in (-1,1):
                yy=t*.33
                _s3_can(head,(x,yy,0),.60,1.00,'600 mm 喂入条筒')
                P(head,'input_sliver',[(x,yy,1.06),(x+.06,yy,1.52),(x+.16,yy*.64,1.57),(-1.18,yy*.26+j*.033,1.49)],.013,'cloth','喂入纤维条','material')
                T(head,'guide_eye',(x+.16,yy*.64,1.57),.027,.006,'steel','x','导条眼','frame')
            B(head,'creel_post',(x,0,.79),(.064,.060,1.55),'dark','高架导条支柱')
            B(head,'creel_crossbar',(x,0,1.52),(.10,.91,.051),'steel','喂入横梁')
        B(head,'creel_spine',(-3.10,0,1.61),(4.32,.070,.062),'rieter_mint','主动导条架')
        B(head,'draft_base',(0,0,.18),(2.198,1.55,.30),'dark','牵伸机座')
        for yy in (-.73,.73):
            B(head,'side_base',(0,yy,.36),(2.14,.055,.15),'rieter_mint','机身下缘')
            for xx in (-.97,.97):B(head,'frame_post',(xx,yy,.86),(.082,.074,1.10),'steel','支承立柱')
        cabinet_faces(head,'service',-1.08,1.08,.771,1.21,'并条机侧门')
        for yy in (-.69,.69):
            panel(head,'draft_profile',[(-1.10,1.37),(-.76,1.91),(.28,1.91),(.76,1.56),(1.08,1.46),(1.08,1.34)],yy,.035,'rieter_mint','牵伸整流罩')
        roof=B(head,'draft_top',(-.22,0,1.92),(1.15,1.42,.047),'white','牵伸室顶盖','shell')
        hood=B(head,'angled_hood',(.54,0,1.74),(.62,1.42,.044),'rieter_mint','牵伸观察盖','shell')
        hood.rotation_euler.y=.57
        for j in range(3):
            roll(head,ident('lower'+str(j)+'_'),'下牵伸罗拉',(-.59+j*.20,0,1.43),.066,.67,1.0+j*.35)
        for j in range(4):
            roll(head,ident('upper'+str(j)+'_'),'上牵伸胶辊',(-.68+j*.20,0,1.528),.065,.66,-1.0-j*.27,'black')
        roll(head,ident('feed'),'喂入测量罗拉',(-.96,0,1.46),.052,.60,.7)
        motor(head,ident('main_m'),'牵伸主电机 3.90 kW',(-.19,-.51,1.40),'y',.115,.24)
        motor(head,ident('feed_m'),'喂入电机 3.90 kW',(-.93,.52,1.44),'-y',.112,.24)
        B(head,'pressure_arm',(-.28,.38,1.67),(.84,.088,.075),'steel','摇架加压臂')
        B(head,'trumpet',(.21,0,1.44),(.20,.24,.07),'white','集束喇叭口','roller')
        P(head,'out_sliver',[(.13,0,1.44),(.47,0,1.40),(.83,0,1.32)],.017,'cloth','输出熟条','material')
        turntable(head,ident('coil'),'偏心圈条盘',.88,0,1.26,.285,1.4)
        motor(head,ident('coil_m'),'圈条电机 1.10 kW',(.64,.40,1.17),'z',.085,.19)
        turntable(head,ident('table'),'条筒底盘',.88,0,.087,.30,.43)
        motor(head,ident('table_m'),'条筒底盘电机',(.62,.39,.18),'z',.067,.14,'gear')
        for x in (.88,1.61):_s3_can(head,(x,0,.13),.60,1.00,'600 mm 输出换筒位')
        slide=load(head,ident('pusher'),'自动换筒推杆',(1.22,.36,.20),'translate:x',.65,.20)
        B(slide,'pusher',(0,0,0),(.15,.55,.09),'steel','换筒推杆','roller')
        motor(head,ident('change_m'),'换筒驱动 0.12 kW',(1.01,.49,.28),'x',.056,.14,'gear')
        for yy in (-.38,.38):B(head,'can_rail',(1.65,yy,.08),(1.32,.039,.065),'steel','换筒导轨')
        P(head,'suction_branch',[(-.33,.45,1.37),(-.46,.45,1.00),(-.54,-y*.75,.76)],.072,'steel','牵伸区吸风支管')
    fan=load(root,'fan','共用吸风叶轮',(-.59,0,.75),'rotate:x',2.7)
    for j in range(11):
        a=j*math.tau/11
        blade=B(fan,'fan_blade',(0,.145*math.cos(a),.145*math.sin(a)),(.095,.085,.026),'steel','风机叶片','roller',.006)
        blade.rotation_euler.x=a+.39
    T(root,'fan_ring',(-.58,0,.75),.21,.025,'rieter_mint','x','吸风机壳','shell')
    motor(root,'fan_m','共用吸风电机 1.50 kW',(-.84,0,.75),'x',.098,.24)
    _s3_hmi(root,(.52,-1.56,1.73),'双眼并条操作屏')


BUILDERS={'jingwei_jwf1217':jingwei_card,'rieter_rsb_d27':rieter_drawing}
