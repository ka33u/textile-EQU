"""Reference-informed industrial geometry upgrade. All forms are original, not OEM CAD."""
M['steel'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.29
M['white'].node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.18
M['white'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.62,.68,.67,1)
M['teal'].node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.28
M['yellow']=mat('Industrial warning yellow',(.95,.63,.045),.12,.4)
M['red']=mat('Emergency stop red',(.7,.025,.015),.1,.35)
M['rubber']=mat('Composite calender roll',(.09,.10,.12),.15,.38)

old_base=base

def base(stage,title,w=3.4,d=2.8,h=.32):
    # Foundation plinth is thinner; the machinery bears its own industrial structure.
    r=old_base(stage,title,w,d,.18);r['modelVersion']='2.0';r['modelType']='reference_informed_industrial';return r

def plate_profile(name, yz, x, depth, parent, material='white', label='重型铸造机架', group='frame', bevel=.035):
    n=len(yz);vs=[(xx,y,z) for xx in (x-depth/2,x+depth/2) for y,z in yz]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    return finish(o,name,material,parent,label,group,bevel)

def handle(parent,loc,width=.22,axis='y'):
    x,y,z=loc
    pts=[(x-width/2,y,z),(x-width/2,y-.06,z),(x+width/2,y-.06,z),(x+width/2,y,z)] if axis=='y' else [(x,y-width/2,z),(x+.06,y-width/2,z),(x+.06,y+width/2,z),(x,y+width/2,z)]
    return tube('service_handle',pts,.018,'dark',parent,'检修门把手','shell')

def panel(parent,loc,size,side='front',label='分段检修门',vents=False,color='white'):
    x,y,z=loc;w,h=size
    if side=='front':
        box('panel_gasket',(x,y,z),(w+.025,.035,h+.025),'black',parent,'检修门密封缝','shell',.008)
        box('panel_skin',(x,y-.025,z),(w,.035,h),color,parent,label,'shell',.015)
        handle(parent,(x+w*.32,y-.05,z))
        for zz in (z-h*.32,z+h*.32):box('hinge',(x-w*.46,y-.06,zz),(.04,.04,.12),'steel',parent,'门铰链','shell',.006)
        if vents:
            for j in range(8):box('louver_slot',(x,y-.047,z-h*.25+j*.04),(w*.65,.012,.015),'dark',parent,'散热百叶','shell',.004)
    else:
        box('panel_gasket',(x,y,z),(.035,w+.025,h+.025),'black',parent,'检修门密封缝','shell',.008)
        box('panel_skin',(x+.025,y,z),(.035,w,h),color,parent,label,'shell',.015)
        handle(parent,(x+.05,y+w*.32,z),axis='x')
        if vents:
            for j in range(8):box('louver_slot',(x+.047,y,z-h*.25+j*.04),(.012,w*.65,.015),'dark',parent,'散热百叶','shell',.004)

def cabinet(parent,loc=(0,0,1.1),size=(.8,.7,1.8),label='变频电控柜'):
    x,y,z=loc;w,d,h=size
    g=empty('electrical_cabinet',loc,parent,label,'shell',explode=[0,.3,-.6])
    box('cabinet_shell',(0,0,0),(w,d,h),'white',g,label,'shell',.035)
    panel(g,(0,-d/2-.015,0),(w*.9,h*.9),label='电控柜门',vents=True)
    box('cabinet_plinth',(0,0,-h/2-.06),(w*.94,d*.94,.14),'dark',g,'柜体踢脚底座','frame')
    for xx in (-w*.25,w*.25):tube('cabinet_cable',[(xx,d/2,-h*.3),(xx,d/2+.12,-h*.3),(xx,d/2+.12,-h*.65)],.027,'black',g,'电缆与线槽','frame')
    return g

def bearing_block(parent,loc,r=.24,side=1,label='分体式辊端轴承箱'):
    x,y,z=loc
    g=empty('bearing_housing',loc,parent,label,'roller')
    box('bearing_lower',(0,0,-r*.32),(.30,r*2.8,r*1.55),'teal',g,label,'roller',.035)
    box('bearing_cap',(0,0,r*.46),(.31,r*2.65,r*1.12),'teal',g,'轴承箱上盖','roller',.05)
    box('bearing_split',(side*.158,0,.04),(.008,r*2.6,.013),'black',g,'轴承箱水平分合面','roller',.001)
    cyl('bearing_flange',(side*.19,0,0),r*1.03,.09,'steel',g,'轴承端盖','x','roller',64)
    torus('bearing_seal',(side*.24,0,0),r*.66,.026,'black',g,'轴封与防尘圈','x','roller')
    cyl('bearing_shaft',(side*.25,0,0),r*.5,.28,'steel',g,'辊端轴伸','x','roller',48)
    for yy in (-r*.95,r*.95):
        bolt(g,(0,yy,r*1.12),'z',.045)
        for zz in (-r*.65,r*.65):bolt(g,(side*.21,yy,zz),'x',.028)
    cyl('grease_nipple',(0,0,r*1.1),.028,.10,'steel',g,'润滑注油嘴','z','roller',12)
    return g

def hydraulic_cylinder(parent,loc,length=.72,r=.17,stroke=.32):
    x,y,z=loc
    g=empty('hydraulic_pressure_cylinder',loc,parent,'液压压紧缸','roller')
    cyl('cylinder_barrel',(0,0,0),r,length,'teal',g,'液压缸筒','z','roller',64)
    for zz in (-length/2,length/2):
        box('cylinder_flange',(0,0,zz),(r*2.7,r*2.7,.11),'steel',g,'液压缸端法兰','roller',.018)
    for xx in (-r*.95,r*.95):
        for yy in (-r*.95,r*.95):cyl('tie_rod',(xx,yy,0),.023,length+.15,'steel',g,'液压缸拉杆','z','roller',12)
    cyl('piston_rod',(0,0,-length/2-stroke/2),r*.50,stroke,'steel',g,'镀铬活塞杆','z','roller',48)
    for zz in (-length*.28,length*.28):
        cyl('hydraulic_port',(0,r+.04,zz),.043,.14,'steel',g,'高压油口','y','roller',12)
    return g

def gauge(parent,loc,reading=.55):
    x,y,z=loc
    cyl('gauge_body',loc,.105,.06,'steel',parent,'液压压力表','y','frame',48)
    cyl('gauge_face',(x,y-.035,z),.087,.006,'white',parent,'压力表刻度盘','y','frame',48)
    for j in range(9):
        a=.25+2.65*j/8
        tube('gauge_tick',[(x+.072*math.cos(a),y-.041,z+.072*math.sin(a)),(x+.058*math.cos(a),y-.041,z+.058*math.sin(a))],.003,'dark',parent,'压力刻度','frame')
    a=.25+2.65*reading;tube('gauge_needle',[(x,y-.045,z),(x+.065*math.cos(a),y-.045,z+.065*math.sin(a))],.004,'red',parent,'压力表指针','frame')

def valve(parent,loc,axis='z'):
    x,y,z=loc
    cyl('valve_body',loc,.075,.2,'steel',parent,'管路截止阀',axis,'frame',16)
    cyl('valve_stem',(x,y,z+.12),.022,.18,'steel',parent,'阀杆','z','frame',12)
    torus('valve_handwheel',(x,y,z+.23),.095,.012,'red',parent,'阀门手轮','z','frame')
    for a in (0,math.pi/2):tube('valve_spoke',[(x-.09*math.cos(a),y-.09*math.sin(a),z+.23),(x+.09*math.cos(a),y+.09*math.sin(a),z+.23)],.008,'red',parent,'手轮辐条','frame')

def rail_platform(parent,loc,size=(1.2,2.4),height=.55):
    x,y,z=loc;w,d=size
    box('service_platform',(x,y,z),(w,d,.10),'dark',parent,'防滑维护平台','frame',.012)
    for j in range(int(w/.08)):box('grating_bar',(x-w/2+j*.08,y,z+.058),(.025,d,.018),'steel',parent,'平台格栅','frame',.002)
    for yy in (-d/2,d/2):
        for xx in (-w/2,w/2):
            tube('guardrail_upright',[(x+xx,y+yy,z),(x+xx,y+yy,z+height)],.024,'yellow',parent,'平台栏杆','frame')
    for zz in (height*.52,height):tube('guardrail',[(x-w/2,y-d/2,z+zz),(x-w/2,y+d/2,z+zz),(x+w/2,y+d/2,z+zz)],.025,'yellow',parent,'维护护栏','frame')

def reducer(parent,loc):
    x,y,z=loc;g=empty('helical_gear_reducer',loc,parent,'斜齿轮减速箱','motor',explode=[-.5,.15,0])
    box('gearbox_foot',(0,0,-.34),(.76,.83,.14),'teal',g,'减速箱安装脚','motor')
    box('gearbox_cast_case',(0,0,0),(.7,.72,.67),'teal',g,'带加强筋减速机壳','motor',.065)
    for j in range(6):box('gearbox_rib',(-.23+j*.09,0,.36),(.025,.64,.065),'teal',g,'齿轮箱加强筋','motor',.008)
    for side in (-1,1):
        cyl('gearbox_bearing_cover',(side*.37,0,0),.25,.065,'teal',g,'减速箱轴承盖','x','motor',48)
        for j in range(8):
            a=j*math.pi/4;bolt(g,(side*.42,.2*math.cos(a),.2*math.sin(a)),'x',.023)
        cyl('gearbox_shaft',(side*.51,0,0),.085,.3,'steel',g,'减速机输入/输出轴','x','motor')
    cyl('oil_filler',(0,0,.43),.05,.08,'steel',g,'减速机油塞','z','motor',12)
    return g

def console(parent,loc):
    x,y,z=loc
    box('hmi_column',(x,y,z*.46),(.14,.14,z*.92),'teal',parent,'独立HMI支柱','frame')
    box('hmi_base',(x,y,.23),(.55,.48,.1),'teal',parent,'控制台底脚','frame')
    g=empty('operator_hmi',loc,parent,'人机界面操作台','shell')
    b=box('operator_console',(0,0,0),(.69,.25,.55),'white',g,'倾斜控制台','shell',.04);b.rotation_euler[0]=-.14
    box('control_display',(0,-.145,.05),(.50,.018,.30),'glass',g,'触摸屏','shell',.015)
    for j in range(4):box('screen_line',(-.15+j*.1,-.157,.05),(.065,.004,.10+j*.025),'green',g,'显示界面图形','shell',.001)
    for xx,ma in ((-.23,'red'),(.23,'green')):cyl('push_button',(xx,-.16,-.17),.038,.035,ma,g,'急停/运行按钮','y','shell',24)
    tube('hmi_cable',[(x,y+.12,z-.2),(x,y+.18,.4),(x+.35,y+.18,.3)],.023,'black',parent,'控制台线缆','frame')

def machine_calender():
    r=base('calender','重型液压轧光机',7.4,5.1)
    # Separate cast C-stands carry pressure through the rear spine and foundation.
    profile=[(-.90,.22),(.95,.22),(.95,3.32),(-.80,3.32),(-.80,2.96),(.42,2.96),(.42,.66),(-.90,.66)]
    for side in (-1,1):
        xx=side*2.18
        plate_profile('cast_C_stand',profile,xx,.48,r,'white','整体铸造C形承压机架',bevel=.055)
        box('foundation_soleplate',(xx,0,.29),(.9,2.25,.22),'teal',r,'机架基础承压底板','frame',.035)
        for yy in (-.85,.85):
            for dx in (-.28,.28):bolt(r,(xx+dx,yy,.43),'z',.065)
        for yy in (-.43,.43):box('vertical_guideway',(xx,yy,1.85),(.17,.09,2.1),'steel',r,'轴承箱精磨滑动导轨','roller',.012)
        hydraulic_cylinder(r,(xx,0,3.40),.62,.19,.40)
        for zz in (1.57,2.55):bearing_block(r,(side*1.99,0,zz),.29,side)
        # Cast relief ribs are functional section stiffeners, not applied decoration.
        for zz in (.82,2.83):box('cast_cross_rib',(xx,.69,zz),(.58,.3,.15),'teal',r,'机架横向加强肋','frame',.025)
    box('rear_tie_beam',(0,.8,.62),(4.5,.25,.3),'teal',r,'机架下联梁')
    box('top_tie_beam',(0,.7,3.15),(4.6,.25,.22),'white',r,'机架上联梁')
    roll(r,'下复合轧光辊',0,1.57,.52,3.64,'rubber')
    roll(r,'上镀铬加热辊',0,2.55,.44,3.64,'steel')
    # Rotary unions and connected thermal-fluid hoses on the non-drive side.
    for zz in (2.55,):
        cyl('rotary_union',(2.43,0,zz),.14,.36,'steel',r,'辊端旋转接头','x','roller',48)
        tube('thermal_oil_hose',[(2.6,0,zz),(2.78,.1,zz),(2.8,.7,zz+.12),(2.8,1.15,.75)],.035,'black',r,'加热辊导热油软管','frame')
    # Transmission: motor -> flexible coupling -> helical reducer -> lower roll shaft.
    box('drive_subframe',(-2.95,0,1.0675),(1.8,1.35,.12),'teal',r,'主传动承重平台','frame')
    for xx in (-3.7,-2.2):
        for yy in (-.5,.5):box('drive_support_leg',(xx,yy,.59375),(.14,.14,.8275),'teal',r,'传动平台承重立柱')
    box('reducer_mount_pad',(-2.7,0,1.14375),(.8,.8,.0325),'steel',r,'减速机找平垫板')
    reducer(r,(-2.70,0,1.57));motor(r,(-3.68,0,1.57),.59)
    coupling=empty('calender_coupling',(-2.12,0,1.57),r,'辊轴联轴器','motor',spin='x')
    cyl('coupling',(-.06,0,0),.18,.20,'steel',coupling,'减速机输出联轴器','x','motor')
    # Sheet-metal drive enclosure has removable doors for the x-ray interaction.
    sh=empty('drive_enclosure',parent=r,label='主传动检修护罩',group='shell',explode=[-1,.25,0])
    box('guard_top',(-3.1,0,2.17),(2.15,1.15,.065),'white',sh,'传动罩顶板','shell',.025)
    panel(sh,(-3.1,.60,1.37),(2.1,1.52),label='传动后检修门',vents=True)
    panel(sh,(-3.1,-.60,.94),(2.1,.7),label='下部传动检修门',vents=True)
    # Inlet and outlet frames have supported, bearing-mounted web guides.
    for yy,zz,rad in ((2.15,.93,.16),(1.25,2.05,.13),(-1.25,2.05,.13),(-2.15,.93,.16)):
        roll(r,'展幅导布辊',yy,zz,rad,3.64)
        for side in (-1,1):
            box('guide_roll_post',(side*1.99,yy,(zz+.28)/2),(.12,.15,zz-.28),'teal',r,'进出布架立柱')
            bearing_block(r,(side*1.94,yy,zz),.115,side,'导布辊带座轴承')
    arc=[(-1.25+.14*math.cos(a),2.05+.14*math.sin(a)) for a in [1.457+(2.444-1.457)*j/12 for j in range(13)]]
    out=arc+[(-2.280,1.039),(-2.55,.703)]
    cloth(r,[(-y,z) for y,z in reversed(out)]+[(.45,2.10),(-.45,2.10)]+out,3.34,'bluecloth')
    # Nip guard is narrow and above the web so the process rolls remain inspectable.
    for yy in (-.72,.72):
        tube('nip_guard_rail',[(-1.85,yy,2.31),(1.85,yy,2.31)],.035,'yellow',r,'轧点防护横杆','frame')
        for xx in (-1.85,1.85):box('safety_sensor',(xx,yy,2.18),(.065,.08,.30),'dark',r,'安全光电检测器','frame',.01)
    # Independent hydraulic unit and routed pressure/return lines.
    box('hydraulic_reservoir',(2.9,1.45,.6),(1.05,.85,.75),'white',r,'液压油站储油箱','frame',.045)
    motor(r,(2.7,1.43,1.23),.36)
    for k in range(3):
        box('hydraulic_valve_block',(3.15,1.17,.98+k*.08),(.22,.25,.055),'steel',r,'液压阀组','frame',.01)
    for side in (-1,1):
        for j in range(2):
            tube('pressure_oil_line',[(3.15,1.2,1.0+j*.08),(3.15,.95,1.15+j*.08),(side*2.18,.95,1.15+j*.08),(side*2.18,.95,3.25+j*.3),(side*2.18,.24,3.25+j*.3)],.022,'black',r,'压紧缸高压油管','frame')
    gauge(r,(2.91,.99,1.08));valve(r,(3.14,1.48,1.06))
    cabinet(r,(-2.96,1.55,1.40),(1.05,.75,2.3),'轧光机变频与液压控制柜')
    console(r,(2.65,-1.73,1.63))
    return r

# Motor geometry: retain the proven assembly hierarchy while rebuilding its electromagnetic parts.
_motor_v1=motor

def motor(parent,loc=(1.3,0,.8),scale=1,detail=False):
    g=_motor_v1(parent,loc,scale,detail)
    winding=next(o for o in g.children if o.name.startswith('stator_windings'))
    rotor=next(o for o in g.children if o.name.startswith('rotor_unit'))
    for o in list(winding.children):
        if o.name.startswith(('copper_end_winding','copper_slot')):bpy.data.objects.remove(o,do_unlink=True)
    # Each distributed coil occupies two separated slots and returns through curved end turns.
    for coil in range(12):
        a0=coil*math.pi/6;a1=a0+math.pi/2
        for turn in range(3 if detail else 1):
            rr=.282+turn*.009;pts=[]
            pts.extend([(-.45,rr*math.cos(a0),rr*math.sin(a0)),(.45,rr*math.cos(a0),rr*math.sin(a0))])
            for j in range(1,15):
                t=j/14;a=a0+(a1-a0)*t;rad=rr+.035*math.sin(math.pi*t)
                pts.append((.45+(.17+turn*.008)*math.sin(math.pi*t),rad*math.cos(a),rad*math.sin(a)))
            pts.append((-.45,rr*math.cos(a1),rr*math.sin(a1)))
            for j in range(1,15):
                t=j/14;a=a1-(a1-a0)*t;rad=rr+.035*math.sin(math.pi*t)
                pts.append((-.45-(.17+turn*.008)*math.sin(math.pi*t),rad*math.cos(a),rad*math.sin(a)))
            tube('distributed_coil_end_turn',pts,.0065,'copper',winding,'分布式绕组及跨槽端部线圈','motor')
    # Insulated slots and axial lamination seams remain visible in the cutaway.
    for i in range(24):
        a=2*math.pi*i/24
        b=box('stator_slot_liner',(0,.272*math.cos(a),.272*math.sin(a)),(.88,.018,.012),'black',winding,'定子槽口绝缘衬垫','motor',.002);b.rotation_euler[0]=a
    if detail:
        for i in range(14):
            annulus('stator_lamination_seam',-.44+i*.066,-.438+i*.066,.262,.322,winding,'dark',3.65,8.0,label='定子叠片层间纹理',steps=48)
    for x in (-.44,.44):torus('rotor_end_ring',(x,0,0),.224,.022,'copper',rotor,'鼠笼转子短路端环','x','motor')
    for o in list(g.children):
        if o.name.startswith(('front_end_shield','rear_end_shield')):
            side=1 if 'front' in o.name else -1
            for i in range(8):
                a=i*math.pi/4
                b=box('endshield_cast_rib',(side*.075,.26*math.cos(a),.26*math.sin(a)),(.06,.16,.032),'teal',o,'端盖径向加强筋','motor',.008);b.rotation_euler[0]=a
            torus('endshield_dust_seal',(side*.09,0,0),.12,.024,'black',o,'轴承防尘密封圈','x','motor')
    terminal=next(o for o in g.children if o.name.startswith('terminal_box'))
    for o in list(terminal.children):
        if o.name.startswith('terminal_base'):bpy.data.objects.remove(o,do_unlink=True)
    box('terminal_bottom',(0,0,-.08),(.47,.4,.04),'teal',terminal,'接线盒底板','motor')
    for yy in (-.18,.18):box('terminal_wall',(0,yy,.015),(.47,.04,.20),'teal',terminal,'接线盒壁','motor',.012)
    for xx in (-.215,.215):box('terminal_wall',(xx,0,.015),(.04,.32,.20),'teal',terminal,'接线盒壁','motor',.012)
    box('terminal_insulator',(0,0,.015),(.37,.26,.055),'black',terminal,'六端子绝缘座','motor',.01)
    for xx in (-.13,0,.13):box('terminal_bridge',(xx,0,.10),(.035,.19,.012),'copper',terminal,'端子铜连接片','motor',.003)
    # Add threaded lifting eye and a recessed nameplate on the casing.
    body=next(o for o in g.children if o.name.startswith('motor_housing'))
    torus('motor_lifting_eye',(-.28,0,.55),.055,.014,'steel',body,'电机吊环','y','motor')
    box('motor_nameplate',(.15,-.437,-.05),(.33,.012,.13),'steel',body,'电机铭牌','motor',.004)
    for j in range(4):box('nameplate_engraving',(.15,-.445,-.09+j*.025),(.26,.004,.006),'dark',body,'铭牌刻线','motor',0)
    return g

_opening_v1=machine_opening
_drawing_v1=machine_drawing
_combing_v1=machine_combing
_winding_v1=machine_winding
_warping_v1=machine_warping
_sizing_v1=machine_sizing
_drawing_in_v1=machine_drawing_in
_pretreatment_v1=machine_pretreatment
_dyeing_v1=machine_dyeing
_inspection_v1=machine_inspection

def remove_named(root,prefixes):
    doomed=set()
    for o in list(root.children_recursive):
        if o.name.startswith(tuple(prefixes)):doomed.update([o.name]+[c.name for c in o.children_recursive])
    for name in doomed:
        if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)

def enclosure_sides(r,width,depth,height,z0=.25,segments=3):
    # Thin, split removable shell panels preserve internal mechanisms for x-ray inspection.
    for side in (-1,1):
        sh=empty('segmented_side_enclosure',parent=r,label='分层机身检修外罩',group='shell',explode=[side*.9,.15,0])
        for j in range(segments):
            yy=-depth/2+(j+.5)*depth/segments
            panel(sh,(side*width/2,yy,z0+height/2),(depth/segments-.035,height),side='side',vents=j==segments-1)
    box('machine_lower_sill',(0,0,z0+.13),(width,depth,.22),'teal',r,'整体机身下裙座','shell',.04)

def machine_opening():
    r=_opening_v1()
    # Cleaner housings and flanged conveying trunk are industrial-scale sheet-metal modules.
    enclosure_sides(r,4.2,2.65,1.7,.32,3)
    for x in (-1.25,0,1.25):panel(r,(x,.44,1.32),(1.16,1.50),label='开清棉分段检修门',vents=True)
    for y in (-1.3,1.3):box('travelling_carriage_rail',(0,y,2.55),(4.3,.13,.14),'steel',r,'抓棉小车直线轨道')
    for x in (-1.6,1.6):
        for y in (-1.3,1.3):cyl('carriage_wheel',(x,y,2.62),.1,.09,'dark',r,'行走小车轨道轮','y','roller')
    tube('large_conveying_elbow',[(-1.2,1,2.2),(-1.2,1,2.8),(-.8,1,3.15),(.3,1,3.15)],.22,'steel',r,'开松输棉主风管','frame')
    for xx in (-.6,0):torus('duct_flange',(xx,1,3.15),.24,.025,'steel',r,'输棉风管法兰','x','frame')
    cabinet(r,(2.45,.5,1.18),(.65,.8,1.75));return r

def machine_carding():
    r=base('carding','包壳式高产梳棉机',6.25,5.5)
    roll(r,'主锡林',0,1.45,.92,2.75,'steel');roll(r,'刺辊',1.2,1.18,.27,2.75,'steel');roll(r,'道夫',-1.22,1.12,.43,2.75,'steel')
    # Parallel fine card-clothing ribs and a true curved revolving-flat path.
    for xx in [-1.34+j*.11 for j in range(25)]:
        torus('cylinder_card_clothing',(xx,0,1.45),.922,.006,'dark',r,'锡林针布纹理','x','roller')
    for i in range(33):
        a=.05+(math.pi-.1)*i/32;y=1.06*math.cos(a);z=1.45+1.06*math.sin(a)
        b=box('revolving_flat_bar',(0,y,z),(2.87,.09,.065),'teal',r,'沿锡林弧面运动的盖板条','roller',.008);b.rotation_euler[0]=a-math.pi/2
    for side in (-1,1):
        xx=side*1.65
        yz=[(-1.9,.25),(1.8,.25),(1.8,1.65),(1.1,2.30),(.4,2.65),(-.6,2.55),(-1.5,1.8),(-1.9,1.15)]
        sh=empty('carder_side_body',parent=r,label='分段梳棉主机罩',group='shell',explode=[side*.9,.25,0])
        plate_profile('contoured_carder_casing',yz,xx,.25,sh,'white','贴合锡林轮廓的梳棉机侧罩','shell',.045)
        for y in (-1.15,0,1.15):panel(sh,(side*1.80,y,1.14),(.92,1.45),side='side',label='侧检修罩板',vents=y>1)
        for y,z,rad in ((0,1.45,.31),(-1.22,1.12,.21),(1.2,1.18,.16)):bearing_block(r,(side*1.48,y,z),rad,side)
    box('feed_chute',(0,1.65,2.06),(2.95,.80,2.9),'white',r,'高位棉箱喂入','shell',.06)
    for j in range(3):panel(r,(-.96+j*.96,1.23,2.1),(.9,2.45),label='棉箱喂入检修门')
    tube('feed_air_duct',[(0,1.65,3.51),(0,1.65,3.85),(.8,1.65,3.85)],.20,'steel',r,'气流喂棉接口','frame')
    roll(r,'剥取与压棉罗拉',-2.05,.95,.10,2.6)
    arc=[(-1.22+.44*math.cos(a),1.12+.44*math.sin(a)) for a in [1.57+.63*j/12 for j in range(13)]]
    cloth(r,arc+[(-2.05,1.06)],2.5)
    cover=empty('carder_upper_cover',parent=r,label='可开启上检修罩',group='shell',explode=[0,.85,0])
    box('carder_top_panel',(0,.1,2.6),(2.9,1.2,.07),'white',cover,'锡林与盖板上护罩','shell',.025)
    can(r,.35,-2.7,.18,.46,.86)
    tube('condensed_sliver',[(0,-2.05,1.06),(0,-2.35,1.22),(.35,-2.7,1.17)],.033,'cloth',r,'棉网集束出条')
    drive=motor(r,(2.65,.2,.82),.56);drive.rotation_euler[2]=math.pi
    box('carder_drive_pedestal',(2.65,.2,.29),(1.0,.85,.22),'teal',r,'外置主电机承重支座')
    cyl('cylinder_drive_extension',(1.83,0,1.45),.085,.68,'steel',r,'锡林轴外伸传动轴','x','motor')
    belt_drive(r,2.15,(.2,.82),.12,(0,1.45),.32)
    console(r,(-1.95,-1.95,1.65));return r

def machine_drawing():
    r=_drawing_v1();enclosure_sides(r,4.0,1.85,1.3,.3,2)
    sh=empty('drafting_cover',parent=r,label='可掀式牵伸罩',group='shell',explode=[0,.8,0])
    for x in (-1.8,1.8):plate_profile('drafting_end_casing',[(-1.1,.4),(.45,.4),(.45,2.35),(-.65,2.35),(-1.1,1.85)],x,.24,sh,'white','牵伸单元端部壳体','shell')
    for y in (.1,-.3,-.7):
        for x in (-1.76,1.76):bearing_block(r,(x,y,1.84),.12,1 if x>0 else -1,'牵伸罗拉轴承座')
    box('pressure_arm_crossbar',(0,-.2,2.3),(3.4,.15,.12),'teal',r,'摇架加压横梁')
    for x in (-1.76,1.76):
        for yy in (.1,-.3,-.7):bearing_block(r,(x,yy,2.09),.09,1 if x>0 else -1,'上胶辊轴承加压座')
        tube('drafting_pressure_rocker',[(x,.28,2.30),(x,-.1,2.36),(x,-.7,2.22)],.035,'teal',r,'上胶辊弹簧加压摇架','frame')
        cyl('drafting_spring',(x,.22,2.36),.045,.12,'steel',r,'摇架加压弹簧','z','frame')
    cyl('coiler_head',(0,-1.5,1.54),.35,.18,'teal',r,'圈条器盘头','z','roller')
    return r

def machine_combing():
    r=_combing_v1();enclosure_sides(r,4.15,2.25,1.1,.25,3)
    for x in (-1.5,-.5,.5,1.5):panel(r,(x,-1.04,.82),(.94,.92),label='精梳传动检修门')
    for x in (-1.35,-.45,.45,1.35):
        for xx in (x-.35,x+.35):box('lap_support_arm',(xx,.62,1.82),(.07,.6,.68),'teal',r,'棉卷托持摇臂')
        box('nipper_spring_arm',(x,-.12,2.12),(.55,.08,.13),'steel',r,'钳板加压与摆动连杆')
        cyl('combing_gear',(x+.36,-.25,1.65),.19,.05,'orange',r,'精梳头传动齿轮','x','roller',48)
    tube('comber_extraction',[(0,1.2,.6),(0,1.6,.6),(1.6,1.6,.6)],.1,'steel',r,'落棉负压吸风管','frame');return r

def spinning_family(stage,roving=False):
    r=base(stage,'双面环锭细纱机' if not roving else '熟条喂入粗纱机',10.4,4.4 if roving else 3.6)
    # Tall closed headstock, long dense spinning zone and a distinct tailstock.
    for xx,w,h in ((-4.65,1.1,2.9),(4.65,.65,2.55)):
        sh=empty('headstock_enclosure',(xx,0,.18),r,'封闭式传动车头' if xx<0 else '车尾传动箱','shell',explode=[-.6 if xx<0 else .6,.2,0])
        box('headstock_body',(0,0,h/2),(w,2.65,h),'white',sh,'整流线型车头机箱','shell',.09)
        panel(sh,(0,-1.35,h/2),(w*.88,h*.90),label='车头传动检修门',vents=True)
        for y in (-.65,.65):panel(sh,(w/2+.015,y,h/2),(1.16,h*.9),side='side',vents=True)
    for side in (-1,1):
        yy=side*.95
        box('continuous_rail',(0,yy,.77),(8.35,.45,.18),'teal',r,'连续钢领板/锭翼升降梁')
        box('machine_sill',(0,side*.55,.44),(8.4,.52,.45),'white',r,'纵向承载机身与吸风槽','shell',.035)
        for x in (-3.6,-2.4,-1.2,0,1.2,2.4,3.6):
            box('intermediate_frame',(x,side*.55,1.80),(.09,.18,3.12),'teal',r,'中墙板与上部支撑')
        for z in (2.37,3.3):box('upper_longitudinal_girder',(0,side*.65,z),(8.4,.12,.12),'steel',r,'粗纱架与牵伸纵梁')
        for yoff in (-.13,0,.13):roll(r,'牵伸罗拉',yy+yoff,2.27,.055,8.25)
        for i in range(18 if not roving else 12):
            count=18 if not roving else 12;xx=-3.85+i*7.7/(count-1)
            if not roving:
                cyl('roving_package',(xx,side*.66,3.02),.095,.52,'cloth',r,'高位粗纱喂入卷装','z','material')
                tube('thread_path',[(xx,side*.66,2.75),(xx,yy,2.33),(xx,yy,2.02),(xx,yy+.11,1.45),(xx,yy+.092,.92),(xx,yy+.058,1.1)],.005,'cloth',r,'粗纱至牵伸与锭子纱路')
                sp=empty('rotate_spindle',(xx,yy,1.2),r,'环锭纺纱锭位','roller',spin='y')
                cyl('spindle_cop',(0,0,0),.058,.61,'cloth',sp,'纱管与细纱卷装','z','material')
                cyl('spindle_blade',(0,0,-.12),.018,.97,'steel',sp,'锭杆','z','roller')
                torus('spinning_ring',(xx,yy,.92),.092,.012,'steel',r,'钢领与钢丝圈','z','roller')
                torus('yarn_guide_eye',(xx,yy,2.02),.024,.005,'steel',r,'导纱钩','z','roller')
                torus('ring_traveller',(xx,yy+.092,.92),.012,.004,'steel',r,'钢丝圈','y','roller')
                box('spindle_separator',(xx+.18,yy,1.28),(.012,.39,.72),'steel',r,'薄片锭位隔纱板','frame',.003)
            elif side<0:
                sp=empty('rotate_flyer',(xx,yy,1.15),r,'粗纱锭翼','roller',spin='y')
                cyl('roving_bobbin',(0,0,0),.13,.70,'cloth',sp,'粗纱卷装','z','material')
                tube('flyer_leg',[(0,0,.55),(.2,0,.46),(.2,0,-.36)],.026,'steel',sp,'锭翼与压掌','roller')
                tube('flyer_balance',[(0,0,.55),(-.2,0,.46),(-.2,0,-.36)],.026,'steel',sp,'锭翼平衡臂','roller')
                tube('drafted_roving',[(xx,.7,2.75),(xx,yy,2.28),(xx,yy,1.7)],.009,'cloth',r,'牵伸后粗纱路径')
    if roving:
        for i in range(12):
            xx=-3.85+i*7.7/11;can(r,xx,1.55,.18,.31,.95)
            tube('drawn_sliver_feed',[(xx,1.55,1.16),(xx,.7,2.75)],.021,'cloth',r,'熟条筒导条架喂入')
    tube('pneumatic_suction_duct',[(-4.1,0,.55),(4.1,0,.55)],.13,'steel',r,'机底中央吸棉风道','frame')
    motor(r,(-4.5,.3,.85),.6)
    for z,ma in ((3.18,'red'),(3.29,'yellow'),(3.40,'green')):cyl('tower_signal',(-4.65,0,z),.055,.1,ma,r,'设备状态灯','z','shell',24)
    console(r,(-4.6,-1.55,1.7));return r

_weaving_v1=machine_weaving

def machine_weaving():
    r=_weaving_v1()
    remove_named(r,['loom_side_frame','frame_column','frame_longitudinal','fabric_web'])
    a=math.atan2(.82,.33)+math.acos(.35/math.hypot(.33,.82))
    cloth(r,[(-.6,1.72),(-1.15,1.67),(-1.48+.35*math.cos(a),.85+.35*math.sin(a))],2.9)
    for side in (-1,1):
        sh=empty('loom_side_body',parent=r,label='厚壁整体织机侧箱',group='shell',explode=[side*.8,.1,0])
        yz=[(-1.65,.25),(1.55,.25),(1.55,1.75),(.85,2.18),(-.6,2.18),(-1.65,1.7)]
        plate_profile('cast_loom_side',yz,side*1.95,.55,sh,'white','织机整体铸造侧机架','shell',.065)
        for y in (-.9,.35,1.15):panel(sh,(side*2.25,y,1.06),(.65,1.3),side='side',label='侧传动检修门')
        bearing_block(r,(side*1.7,1.15,1.0),.22,side,'送经轴承座')
        bearing_block(r,(side*1.7,-1.48,.85),.19,side,'卷取轴承座')
    box('front_loom_breast_beam',(0,-1.0,1.54),(3.5,.22,.22),'teal',r,'连续胸梁与前面板','shell',.045)
    roll(r,'送经张力后梁',1.55,1.70,.105,3.05)
    for xx in (-1.55,1.55):
        tube('backrest_rocker',[(xx,1.2,1.1),(xx,1.55,1.7)],.045,'steel',r,'送经张力后梁摆臂','frame')
        cyl('backrest_sensor',(xx,1.55,1.7),.13,.08,'dark',r,'经纱张力检测器','x','roller')
    remove_named(r,['warp_shed_upper','warp_shed_lower'])
    for j in range(40):
        xx=-1.45+j*2.9/39;zz=2.15 if j%2 else 1.62
        theta=math.atan2(zz-1.7,.4-1.55)
        if theta<0:theta+=2*math.pi
        end=theta-math.acos(.115/math.hypot(.4-1.55,zz-1.7))
        arc=[(xx,1.55+.115*math.cos(a),1.7+.115*math.sin(a)) for a in [-.007+(end+.007)*k/14 for k in range(15)]]
        tube('warp_shed_upper' if j%2 else 'warp_shed_lower',[(xx,1.66,.996)]+arc+[(xx,.4,zz),(xx,-.28,zz),(xx,-.62,1.72)],.007,'cloth',r,'经轴—张力后梁—综框—织口连续经纱')
    # Independent weft creel and stationary yarn accumulators, characteristic of rapier looms.
    for xx in (-3.5,-2.9):
        box('creel_soleplate',(xx,-.2,.1),(.45,.65,.2),'teal',r,'独立纬纱架落地底脚')
        tube('weft_creel_upright',[(xx,-.2,.2),(xx,-.2,2.8)],.035,'teal',r,'纬纱筒子架','frame')
    for z in (.75,1.4,2.05,2.7):
        tube('weft_creel_crossbar',[(-3.6,-.2,z),(-2.8,-.2,z)],.028,'steel',r,'纬纱架横梁','frame')
        cyl('weft_cone',(-3.25,-.2,z),.17,.36,'cloth',r,'纬纱供纱筒子','x','material')
    tube('accumulator_support',[(-2.5,.1,.18),(-2.5,.1,2.65),(-2.5,-.45,2.65)],.05,'teal',r,'储纬器独立承重支架','frame')
    box('accumulator_bracket',(-2.5,-.45,2.54),(.85,.25,.13),'steel',r,'储纬器安装横板')
    for j in range(3):
        x=-2.7+j*.22;z=2.705
        cyl('weft_accumulator',(x,-.55,z),.10,.28,'steel',r,'电子储纬器','y','roller')
        tube('weft_yarn',[(-3.2,-.2,2.05),(x,-.7,z),(-1.9,-.28,1.86)],.005,'cloth',r,'纬纱至剑杆引纬纱路')
    cabinet(r,(2.65,.65,1.15),(.67,1.4,1.85),'开口与主驱动侧柜')
    return r

def machine_winding():
    r=_winding_v1();enclosure_sides(r,4.65,1.55,1.55,.22,3)
    for i in range(6):
        xx=-1.8+i*.72
        sh=empty('winding_unit_casing',parent=r,label='独立自动络筒单元',group='shell',explode=[0,.3,.5])
        plate_profile('winding_unit_cheek',[(-.8,.3),(.3,.3),(.3,2.48),(-.25,2.48),(-.67,1.85)],xx+.32,.07,sh,'white','单锭络筒机壳','shell',.018)
        box('splicing_chamber',(xx,-.65,1.44),(.36,.34,.30),'white',r,'空气捻接器模块','shell',.025)
        cyl('tension_disc',(xx,-.85,1.22),.073,.055,'steel',r,'纱线张力盘','y','roller')
        for z in (.65,.86):cyl('reserve_bobbin',(xx,.07,z),.10,.5,'cloth',r,'自动换管后备管纱','z','material')
        tube('suction_arm',[(xx,-.35,2.1),(xx-.2,-.5,1.93),(xx-.2,-.7,1.62)],.032,'dark',r,'接头寻纱吸嘴','frame')
        box('unit_status_led',(xx,-.67,1.64),(.12,.02,.025),'green',r,'锭位状态指示','shell',.005)
    tube('winder_extraction_main',[(-2.3,.7,2.55),(2.3,.7,2.55)],.13,'steel',r,'络筒中央吸风总管','frame')
    box('tube_conveyor',(0,-.5,.43),(4.45,.32,.13),'dark',r,'管纱输送通道','frame')
    cabinet(r,(-2.7,.2,1.32),(.65,1.5,2.2),'络筒机车头控制柜');return r

def machine_warping():
    r=_warping_v1()
    for m in list(r.children):
        if m.name.startswith('motor_assembly'):remove_named(r,[m.name])
    box('warper_drive_foundation',(2.7,-1.8,.09),(1.25,1.1,.18),'teal',r,'整经轴驱动基础')
    box('warper_drive_bed',(2.7,-1.8,.59),(1.05,.85,.82),'teal',r,'整经主电机承重台')
    drive=motor(r,(2.7,-1.8,1.45),.6);drive.rotation_euler[2]=math.pi
    cyl('warper_axis_extension',(1.87,-1.8,1.45),.08,.6,'steel',r,'经轴外伸驱动联接轴','x','motor')
    for side in (-1,1):
        sh=empty('warper_side_cabinet',parent=r,label='整经机侧箱与制动模块',group='shell',explode=[side*.8,.15,0])
        plate_profile('warper_side_cheek',[(-2.7,.20),(-.9,.20),(-.9,2.20),(-1.35,2.65),(-2.7,2.15)],side*1.83,.55,sh,'white','整经卷绕主机侧箱','shell',.055)
        panel(sh,(side*2.12,-1.8,1.24),(1.5,1.82),side='side',label='整经传动制动检修门')
        bearing_block(r,(side*1.57,-1.8,1.45),.28,side,'整经轴承支座')
        box('beam_lifting_arm',(side*1.52,-1.9,.95),(.14,.95,.16),'teal',r,'经轴装卸升降托臂')
    # Hinged guard framing, open wire screen leaves warp visible.
    for xx in (-1.5,1.5):tube('safety_guard_frame',[(xx,-2.5,.5),(xx,-2.5,2.0),(xx,-.7,2.5)],.035,'steel',r,'翻转式经纱安全罩框','shell')
    for zz in (.7,1.15,1.6,2.05):tube('guard_mesh_crossbar',[(-1.5,-2.5,zz),(1.5,-2.5,zz)],.008,'dark',r,'安全罩防护网','shell')
    for j in range(21):tube('guard_mesh_upright',[(-1.5+j*.15,-2.5,.5),(-1.5+j*.15,-2.5,2.05)],.006,'dark',r,'安全罩防护网','shell')
    for yy in (.4,1.2,2.0):
        for side in (-1,1):
            for zz in (.9,1.6,2.3):
                box('creel_tensioner',(side*1.2,yy-.22,zz),(.10,.08,.12),'dark',r,'筒子架张力器','frame',.012)
                tube('creel_yarn',[(side*1.35,yy,zz),(side*1.2,yy-.25,zz),(side*1.05,-.55,1.92)],.004,'cloth',r,'筒子经纱导引')
    roll(r,'压纱辊',-1.40,2.03,.12,2.85);return r

def machine_sizing():
    r=_sizing_v1();enclosure_sides(r,3.65,5.45,1.55,.25,4)
    # Separate squeeze nip, insulated dryer section and woven-beam take-up.
    for side in (-1,1):
        for yy in (2.2,1.55,1.0,.2,-.6,-1.4,-2.5):bearing_block(r,(side*1.53,yy,1.65 if yy<1.5 else 1.5),.13,side,'浆纱辊轴承座')
        box('size_squeeze_upright',(side*1.6,1.05,1.58),(.26,.42,1.7),'teal',r,'浸轧压力机架')
        hydraulic_cylinder(r,(side*1.6,1.05,2.28),.35,.10,.18)
    hood=empty('dryer_fume_hood',parent=r,label='烘燥排湿罩',group='shell',explode=[0,1.2,0])
    # Sloping hood roof is a closed frustum rather than a floating rectangular slab.
    vs=[(-1.7,-1.8,2.35),(1.7,-1.8,2.35),(1.7,.75,2.35),(-1.7,.75,2.35),(-.6,-.9,3.05),(.6,-.9,3.05),(.6,-.15,3.05),(-.6,-.15,3.05)]
    me=bpy.data.meshes.new('Fume hood');me.from_pydata(vs,[],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]);me.update();o=bpy.data.objects.new('sloped_extraction_hood',me);bpy.context.collection.objects.link(o);finish(o,o.name,'steel',hood,'渐缩排湿罩','shell',.015)
    tube('exhaust_main',[(0,-.5,3.05),(0,-.5,3.42),(.5,-.5,3.7),(1.4,-.5,3.7)],.18,'steel',r,'烘筒排湿风道','frame')
    for yy in (0,-.6,-1.2):
        tube('steam_header',[(1.9,yy,.75),(1.9,yy,1.6),(1.55,yy,1.6)],.04,'steel',r,'烘筒蒸汽与冷凝水接口','frame')
        valve(r,(1.9,yy,1.0))
    cabinet(r,(-2.2,1.6,1.3),(.6,1,2.0));return r

def machine_drawing_in():
    r=_drawing_in_v1();remove_named(r,['frame_column','frame_longitudinal','drawing_carriage'])
    box('drawing_tower',(1.35,.35,1.95),(.65,.65,3.5),'white',r,'自动穿经主塔','shell',.07)
    panel(r,(1.35,-.0,1.95),(.54,3.2),label='穿经主塔检修门',vents=True)
    box('traverse_bridge',(0,.35,3.55),(3.5,.45,.38),'teal',r,'高速穿经横移桥架')
    for xx in (-1.4,1.4):cyl('vertical_linear_guide',(xx,.0,2.65),.035,1.9,'steel',r,'穿经头精密直线导轨','z','frame')
    box('drawing_head',(.6,-.25,2.65),(.55,.55,.75),'teal',r,'综丝停经片选取与穿经头','shell',.045)
    tube('cable_drag_chain',[(.55,.55,2.6),(.55,.7,3.1),(-.5,.7,3.25),(-1.3,.7,3.25)],.055,'black',r,'穿经头拖链与信号束','frame')
    for y in (-1.25,1.25):box('rail_bed',(0,y,.38),(3.6,.13,.14),'steel',r,'经纱车与综框支撑导轨')
    for x in (-1.5,1.5):
        for y in (-1.25,1.25):cyl('transport_wheel',(x,y,.23),.12,.07,'dark',r,'经纱车脚轮','y','frame')
    for y in (-1.4,1.4):tube('operator_guard',[(-1.65,y,.35),(-1.65,y,1.2),(1.65,y,1.2),(1.65,y,.35)],.025,'yellow',r,'穿经工位防护栏','frame')
    return r

def machine_pretreatment():
    r=_pretreatment_v1();remove_named(r,['fabric_web'])
    for yy in (-1.85,1.85):
        for side in (-1,1):
            panel(r,(side*1.84,yy,1.1),(1.5,1.35),side='side',label='水洗箱保温检修门')
            for z in (.6,1.3):tube('washing_manifold',[(side*1.95,yy-.6,z),(side*1.95,yy+.6,z)],.055,'steel',r,'逆流水洗配液管','frame')
    chamber=empty('steaming_tower',parent=r,label='退煮漂汽蒸反应箱',group='shell',explode=[0,1.1,0])
    box('steamer_body',(0,0,2.3),(3.55,1.25,2.15),'white',chamber,'保温汽蒸箱','shell',.055)
    for xx in (-1.15,0,1.15):panel(chamber,(xx,-.65,2.3),(1.08,1.9),label='汽蒸箱分段检修门')
    for yy in (-.45,.45):roll(r,'高位导布辊',yy,3.0,.16,2.95)
    cloth(r,[(2.5,2.12),(1.8,1.35),(1.3,2.12),(.45,3.17),(-.45,3.17),(-1.3,2.12),(-1.8,1.35),(-2.5,2.12)],2.8)
    tube('steam_feed',[(1.95,-2.4,.5),(1.95,0,.5),(1.95,0,2.8),(1.7,0,2.8)],.07,'steel',r,'工艺蒸汽总管','frame')
    for yy in (-1.85,0,1.85):valve(r,(1.95,yy,.62))
    rail_platform(r,(2.5,0,1.15),(.75,3.7),.95)
    for j in range(5):box('service_stair_tread',(2.5,-2.6+j*.2,.25+j*.2),(.75,.28,.08),'dark',r,'维护平台楼梯','frame')
    for yy in (-1.3,1.3):box('platform_column',(2.5,yy,.64),(.12,.12,1.0),'steel',r,'维护平台支柱')
    cabinet(r,(-2.2,-.8,1.22),(.65,1.2,1.9));return r

def machine_dyeing():
    r=_dyeing_v1();remove_named(r,['fabric_web']);enclosure_sides(r,3.7,6.2,1.15,.25,4)
    for side in (-1,1):
        box('padder_side_frame',(side*1.65,.7,1.38),(.38,.85,2.0),'white',r,'浸轧机重型侧架','shell',.05)
        for zz in (1.3,1.82):bearing_block(r,(side*1.5,.65,zz),.18,side,'浸轧辊端轴承箱')
        hydraulic_cylinder(r,(side*1.65,.65,2.28),.4,.12,.24)
    imm=[(1.65+.23*math.cos(a),1.10+.23*math.sin(a)) for a in [-.654+(-2.270+.654)*k/20 for k in range(21)]]
    nip=[(.65+.26*math.cos(a),1.30+.26*math.sin(a)) for a in [.871+(math.pi/2-.871)*k/12 for k in range(13)]]
    cloth(r,[(2.4,1.7)]+imm+nip+[(.25,1.56),(-.7,1.82),(-1.8,1.82),(-2.55,1.64),(-3.45,1.64)],2.7,'bluecloth')
    box('dye_liquor_supply_tank',(2.18,1.7,.78),(.7,1.05,1.15),'steel',r,'染液循环配液槽','frame',.03)
    for yy in (1.35,1.85):
        tube('dye_pipe_loop',[(2.25,yy,.4),(2.45,yy,.4),(2.45,yy,1.75),(1.65,yy,1.75)],.04,'steel',r,'染液供回流管路','frame')
        valve(r,(2.45,yy,1.1))
    gauge(r,(2.48,1.0,1.45))
    for x in (-1.15,0,1.15):panel(r,(x,-.1,1.45),(1.08,1.6),label='固色箱入口罩板')
    for yy in (-1.8,-.7):
        tube('fixation_exhaust',[(0,yy,2.2),(0,yy,2.65),(.5,yy,2.85)],.13,'steel',r,'固色箱排湿风道','frame')
    for side in (-1,1):bearing_block(r,(side*1.55,-3.3,1.45),.14,side,'末道水洗出布辊轴承')
    cabinet(r,(-2.25,1.3,1.18),(.65,1.0,1.85));return r

def machine_stenter():
    r=base('stenter','拉幅烘干定幅联合机',5.5,10.3)
    for yy in (0,1.7,3.4):
        sh=empty('stenter_chamber_section',parent=r,label='模块化热风烘房',group='shell',explode=[0,1.0,0])
        for xx in (-1.86,1.86):box('stenter_side_wall',(xx,yy,1.7),(.08,1.65,1.85),'white',sh,'烘房保温侧板','shell',.015)
        for zz in (.815,2.585):box('stenter_roof_floor',(0,yy,zz),(3.8,1.65,.08),'white',sh,'烘房顶底保温板','shell',.015)
        for yend in (yy-.825,yy+.825):
            box('stenter_below_web_slot',(0,yend,1.1225),(3.8,.08,.695),'white',sh,'进出布槽下门板','shell',.015)
            box('stenter_above_web_slot',(0,yend,2.1275),(3.8,.08,.995),'white',sh,'进出布槽上门板','shell',.015)
        box('chamber_undercarriage',(0,yy,.52),(3.6,1.50,.55),'teal',r,'烘房支撑底座')
        for side in (-1,1):
            for dy in (-.4,.4):panel(sh,(side*1.93,yy+dy,1.7),(.73,1.62),side='side',label='烘房保温门')
        # A blower scroll and shaft support, not a motor dropped onto a flat roof.
        box('blower_mount',(0,yy,2.68),(1.5,.78,.14),'teal',r,'循环风机法兰支架')
        cyl('blower_scroll',(.05,yy,3.0),.32,.36,'steel',r,'热风循环风机蜗壳','x','frame',64)
        box('blower_outlet',(.05,yy+.32,3.0),(.35,.4,.26),'steel',r,'蜗壳切向出口','frame',.03)
        motor(r,(-.62,yy,3.0),.36)
        tube('chamber_exhaust',[(.7,yy,2.7),(.7,yy,3.35),(.7,yy+.45,3.6)],.15,'steel',r,'烘房排湿风管','frame')
        for zz in (1.1,1.85):roll(r,'烘房循环导布辊',yy,zz,.11,2.9)
    # Long level entry section links the heavy padder to the chain rails.
    for side in (-1,1):
        x=side*1.48
        box('pin_chain_rail',(x,.2,1.43),(.13,8.65,.15),'steel',r,'贯通针板链轨','frame')
        for j in range(44):box('stenter_chain_link',(x,-4.0+j*.195,1.54),(.11,.075,.055),'orange',r,'针板链节与布夹','roller',.007)
        for yy in (-2.75,-1.75):
            cyl('width_adjusting_screw',(0,yy,1.1),.035,3.8,'steel',r,'横向调幅丝杆','x','roller',32)
            box('width_adjustment_nut',(x,yy,1.1),(.22,.24,.18),'teal',r,'链轨调幅滑块')
            cyl('edge_sensor_wheel',(x,yy,1.66),.065,.035,'dark',r,'布边光电与探边轮','y','roller')
    for side in (-1,1):
        sh=empty('padder_side_pod',parent=r,label='进布轧车侧机座',group='shell',explode=[side*.6,.1,0])
        box('entry_padder_pod',(side*1.95,-3.75,1.23),(.73,1.6,2.1),'white',sh,'入口轧车整体侧箱','shell',.07)
        panel(sh,(side*2.33,-3.75,1.2),(1.4,1.8),side='side',label='轧车检修门')
        for zz in (1.19,1.70):bearing_block(r,(side*1.58,-3.75,zz),.19,side,'入口轧辊轴承座')
        hydraulic_cylinder(r,(side*1.8,-3.75,2.40),.42,.12,.22)
    roll(r,'进布轧液下辊',-3.75,1.19,.245,3.1,'rubber');roll(r,'进布轧液上辊',-3.75,1.70,.245,3.1,'steel')
    roll(r,'进布展幅辊',-4.65,1.43,.12,3.1)
    cloth(r,[(-4.95,1.56),(-4.65,1.56),(-4.05,1.445),(-3.45,1.445),(-2.9,1.55),(4.4,1.55)],2.82,'bluecloth')
    rail_platform(r,(0,-4.95,.32),(3.5,.55),.5)
    tube('overhead_safety_rail',[(-2.5,-2.8,.25),(-2.5,-2.8,2.7),(2.5,-2.8,2.7),(2.5,-2.8,.25)],.045,'yellow',r,'入口安全与检修框架','frame')
    motor(r,(-1.25,-3.75,.76),.52);console(r,(-2.60,-3.5,1.85));cabinet(r,(2.45,-1.8,1.2),(.65,1.1,1.9));return r

def machine_inspection():
    r=_inspection_v1();remove_named(r,['fabric_web'])
    table=next(o for o in r.children_recursive if o.name.startswith('inspection_light_table'))
    table.rotation_euler=(0,0,0);table.dimensions=(3.3,2.85,.12);table.location=(0,-.075,1.595);table.rotation_euler[0]=math.atan(.75/2.75)
    cloth(r,[(1.3,2.03),(-1.45,1.28)],3,'bluecloth')
    for side in (-1,1):
        sh=empty('inspection_side_case',parent=r,label='验布机侧传动机壳',group='shell',explode=[side*.7,.1,0])
        yz=[(-1.8,.22),(1.8,.22),(1.8,2.13),(.9,2.13),(-1.8,.95)]
        plate_profile('inspection_case',yz,side*1.78,.35,sh,'white','斜面验布机整体侧机架','shell',.05)
        panel(sh,(side*1.98,-.6,.73),(1.9,.76),side='side',label='卷取传动检修门',vents=True)
        for y,z in ((1.35,1.65),(-1.45,.85)):bearing_block(r,(side*1.65,y,z),.17,side,'验布收放卷轴承座')
    for xx in (-1.45,1.45):
        tube('inspection_light_arm',[(xx,1.3,1.7),(xx,1.3,2.8),(xx,-.5,2.8)],.045,'teal',r,'顶光检查灯支臂','frame')
    box('inspection_lamp',(0,-.5,2.8),(3.1,.13,.12),'white',r,'连续验布照明灯','shell',.025)
    box('operator_worktop',(-2.25,-.5,1.1),(.65,.9,.12),'white',r,'验布记录操作台','frame')
    for m in list(r.children):
        if m.name.startswith('motor_assembly'):remove_named(r,[m.name])
    box('inspection_drive_foundation',(3.0,-1.45,.09),(2.25,1.15,.18),'teal',r,'验布卷取外置驱动基础')
    box('inspection_drive_bed',(2.85,-1.45,.31),(2.0,.9,.26),'teal',r,'电机与减速箱共用找平机座')
    drive=motor(r,(3.25,-1.45,.85),.55);drive.rotation_euler[2]=math.pi
    reducer(r,(2.1,-1.45,.85))
    cyl('inspection_roll_coupling',(1.72,-1.45,.85),.075,.4,'steel',r,'卷取辊与减速器同轴联接','x','motor')
    tube('inspection_cable_tray',[(1.9,1.3,.5),(1.9,-1.3,.5)],.045,'dark',r,'检测与驱动电缆线槽','frame')
    return r

# Exact geometry sharing reduces buffers and preserves independently clickable object nodes.
def optimize_stage(root):
    import hashlib,struct
    shared={}; reused=0
    for o in root.children_recursive:
        if o.type!='MESH':continue
        me=o.data;h=hashlib.sha1()
        h.update('|'.join(m.name for m in me.materials).encode())
        for v in me.vertices:h.update(struct.pack('<fff',*v.co))
        for p in me.polygons:
            h.update(struct.pack('<I?',len(p.vertices),p.use_smooth));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
        key=h.digest()
        if key in shared:o.data=shared[key];reused+=1
        else:shared[key]=me
    root['sharedGeometryInstances']=reused
    root['modelVersion']='2.0'
    return reused

# Geometrically tangent external belt, used by the outboard carder drive.
def belt_drive(parent,x,c1,r1,c2,r2):
    d=math.hypot(c2[0]-c1[0],c2[1]-c1[1]);theta=math.atan2(c2[1]-c1[1],c2[0]-c1[0]);alpha=math.acos((r1-r2)/d)
    a=theta-alpha;b=theta+alpha
    for (cy,cz),rad in ((c1,r1),(c2,r2)):
        g=empty('belt_drive_pulley',(x,cy,cz),parent,'带传动主/从动轮','motor',spin='x');cyl('drive_pulley',(0,0,0),rad,.10,'orange',g,'传动带轮','x','motor')
    pts=[]
    for center,rad,start,end in ((c1,r1,b,a+2*math.pi),(c2,r2,a,b)):
        for j in range(20):
            q=start+(end-start)*j/19;pts.append((x+.065,center[0]+rad*math.cos(q),center[1]+rad*math.sin(q)))
    pts.append(pts[0]);tube('tangent_drive_belt',pts,.018,'black',parent,'双轮切线传动带','motor')

def machine_opening():
    r=base('opening','移动塔式抓棉与开清棉',8.4,5.6)
    # Long centre-track and single travelling tower with a one-sided extracting cantilever.
    for yy in (-.38,.38):
        box('long_travel_rail',(0,yy,.27),(7.9,.11,.16),'steel',r,'抓棉机长行走轨道')
        for xx in (-3.6,-2.4,-1.2,0,1.2,2.4,3.6):box('rail_sleeper',(xx,yy,.20),(.23,.28,.08),'teal',r,'轨道安装压板')
    for side in (-1,1):
        for j in range(6):
            xx=-2.9+j*1.08;yy=side*1.65
            box('pressed_cotton_bale',(xx,yy,.72),(.98,1.5,1.08),'cloth',r,'排列待抓取棉包','material',.055)
            for k in range(6):box('cotton_bale_top_layer',(xx-.44+k*.17,yy,1.27+.018*(k%3)),(.16,1.47,.09),'cloth',r,'棉包松散纤维层','material',.04)
    cart=empty('travelling_tower_carriage',(-.45,0,0),r,'往复式抓棉移动塔','frame')
    box('carriage_chassis',(0,0,.45),(1.22,1.05,.32),'teal',cart,'轨道小车底盘')
    for xx in (-.42,.42):
        for yy in (-.39,.39):cyl('rail_rolling_wheel',(xx,yy,.37),.12,.075,'dark',cart,'轨道轮','y','roller')
    sh=empty('tower_enclosure',parent=cart,label='移动塔驱动检修罩',group='shell',explode=[.7,.25,0])
    box('tower_column',(0,0,2.03),(.96,.92,2.90),'white',sh,'抓棉升降塔机身','shell',.09)
    panel(sh,(0,-.48,2.12),(.80,2.55),label='升降传动检修门',vents=True)
    for xx in (-.39,.39):box('vertical_head_guide',(xx,-.52,2.1),(.08,.07,2.5),'steel',cart,'抓棉臂升降导轨')
    arm=empty('cantilever_plucking_head',parent=cart,label='单侧悬臂抓棉头',group='shell',explode=[0,.45,.5])
    box('cantilever_box_beam',(0,-1.45,1.59),(.91,2.35,.46),'white',arm,'悬臂式抓棉头壳体','shell',.055)
    panel(arm,(0,-2.64,1.59),(.80,.35),label='抓棉头端部检修门',vents=True)
    rotor=empty('rotate_plucking_beater',(0,-1.5,1.285),cart,'抓棉打手','roller',spin='z')
    cyl('plucking_beater',(0,0,0),.085,1.95,'steel',rotor,'抓棉辊轴','y','roller')
    for k in range(10):
        a=k*math.pi/5
        tube('beater_tooth_strip',[(.11*math.cos(a),-.94,.11*math.sin(a)),(.11*math.cos(a),.94,.11*math.sin(a))],.012,'steel',rotor,'抓棉打手齿列','roller')
    box('plucker_internal_motor_bed',(0,-.17,.805),(.50,.55,.39),'teal',cart,'抓棉头内置电机承重台')
    drive=motor(cart,(0,-.17,1.285),.38);drive.rotation_euler[2]=-math.pi/2
    tube('tower_suction_duct',[(0,0,3.5),(0,0,3.85),(.5,0,4.1),(1.9,0,4.1)],.20,'steel',cart,'抓棉负压输送主管','frame')
    for xx in (.7,1.5):torus('conveying_duct_flange',(xx,0,4.1),.22,.02,'steel',cart,'输棉管连接法兰','x','frame')
    console(r,(-3.7,-.7,1.55));return r

def machine_sizing():
    r=base('sizing','浸轧—多烘筒—卷绕浆纱机',6.5,6.8)
    box('size_trough',(0,1.85,.77),(3.5,1.6,1.1),'teal',r,'浆槽与循环上浆系统','shell',.045)
    roll(r,'浸浆导纱辊',1.85,1.15,.20,2.95)
    for yy in (1.05,.25,-.55,-1.35):roll(r,'烘干筒',yy,1.65,.30,2.95)
    roll(r,'轧浆上辊',1.05,2.27,.30,2.95,'rubber')
    roll(r,'织轴卷绕',-2.5,1.1,.40,2.95,'cloth')
    for side in (-1,1):
        cyl('weaver_beam_flange',(side*1.58,-2.5,1.1),.54,.10,'teal',r,'浆纱织轴盘片','x','roller')
        for yy,zz,rr in ((1.85,1.15,.13),(1.05,1.65,.16),(1.05,2.27,.16),(.25,1.65,.16),(-.55,1.65,.16),(-1.35,1.65,.16),(-2.5,1.1,.21)):
            bearing_block(r,(side*1.58,yy,zz),rr,side,'浆纱辊轴承支座')
        box('sizing_side_rail',(side*1.75,-.25,.65),(.25,5.7,.5),'teal',r,'浆纱主机纵向承重梁')
        box('squeeze_side_upright',(side*1.7,1.05,1.65),(.3,.42,2.9),'white',r,'轧浆压力侧机架')
        hydraulic_cylinder(r,(side*1.7,1.05,2.98),.4,.12,.2)
    # A continuous warp sheet has real alternating dryer wraps and a tangent beam entry.
    path=[(2.70,1.70)]
    path += [(1.85+.21*math.cos(a),1.15+.21*math.sin(a)) for a in [-.788+(-2.713+.788)*j/18 for j in range(19)]]
    for yy,start,end in ((1.05,.429,2.458),(.25,5.6,3.826),(-.55,.684,2.458),(-1.35,5.6,5.237)):
        path += [(yy+.31*math.cos(a),1.65+.31*math.sin(a)) for a in [start+(end-start)*j/18 for j in range(19)]]
    path.append((-2.5+.41*math.cos(5.237),1.1+.41*math.sin(5.237)))
    for j in range(40):tube('sizing_warp_sheet',[( -1.35+j*2.7/39,y,z) for y,z in path],.006,'cloth',r,'浸浆—轧浆—交替包覆烘筒—织轴连续经纱片')
    enclosure_sides(r,3.95,5.85,1.75,.20,4)
    hood=empty('sizing_dryer_hood',parent=r,label='可开启烘筒排湿罩',group='shell',explode=[0,1.1,0])
    box('dryer_hood_roof',(0,-.55,2.43),(3.8,2.65,.07),'white',hood,'烘筒上部排湿罩','shell',.02)
    tube('dryer_exhaust',[(0,-.5,2.46),(0,-.5,3.0),(.55,-.5,3.35),(1.5,-.5,3.35)],.19,'steel',r,'排湿风管','frame')
    for yy in (.25,-.55,-1.35):
        tube('dryer_rotary_union',[(1.8,yy,1.65),(2.05,yy,1.65),(2.05,yy,.7)],.035,'steel',r,'烘筒蒸汽旋转接头与回水','frame')
        valve(r,(2.05,yy,.85))
    box('sizing_drive_pedestal',(2.6,-2.5,.4525),(1.1,.9,.545),'teal',r,'织轴电机外置承重机座')
    drive=motor(r,(2.6,-2.5,1.1),.5);drive.rotation_euler[2]=math.pi
    cyl('weaver_beam_coupling_shaft',(1.85,-2.5,1.1),.075,.45,'steel',r,'织轴驱动同轴联接轴','x','motor')
    console(r,(-2.1,-2.55,1.7));return r
