"""Build the documented two-section Rieter R 70 configuration in metres (Blender Z up).
Run Blender in background with --factory-startup --python blender/build_rotor_spinning.py.
The construction is independent of the other equipment assets.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

library = Path(__file__).with_name('build_models.py')
exec(compile(library.read_text().split('builders=[')[0], str(library), 'exec'))
library = BLEND / 'current_extensions_v5.py'
exec(compile(library.read_text(), str(library), 'exec'))

PAGE = 'https://www.rieter.com/products/systems/rotor-spinning-machines/rotor-spinning-machine-r-70'
M['r70green'] = mat('R70 mint enamel', (.37, .63, .40), .28, .38)
M['r70deep'] = mat('R70 dark green panel', (.12, .21, .17), .36, .38)
M['r70can'] = mat('R70 sliver can', (.78, .82, .79), .18, .38)
M['r70line'] = mat('Rotor yarn in process', (.75, .47, .14), .05, .72)
M['r70blue'] = mat('Operator display', (.06, .23, .31), .12, .28)
B, C, T, P = _s3_box, _s3_cyl, _s3_torus, _s3_pipe
ROOT = e5_root('rotor_spinning', 'R 70 双面转杯纺纱机', 'Rieter', 'R 70',
    '基础机 2 节、48 纺位、2 台落筒机器人；230 mm 锭距；1 070 mm 条筒；机长 11.453 m。', PAGE)
for k,v in dict(sectionCount=2,positionCount=48,robotCount=2,gaugeMillimetres=230,
                overallLengthMetres=11.453,machineHeightMetres=2.95,sectionLengthMetres=2.82,
                canHeightMetres=1.07,independentDriveFunctionsPerPosition=5,
                actualScope='按立达技术册第 8–10 页建立基础配置。电机安装位置、外形及隐蔽传动按功能示意。').items():
    ROOT[k]=v

def tagged(obj, key, value):
    obj[key]=value
    return obj

def lathed(parent,name,profile,material,label):
    """Closed or hollow profile around Blender Y; positive face direction is outward."""
    segments=40
    verts=[(r*math.cos(2*math.pi*j/segments),y,r*math.sin(2*math.pi*j/segments))
           for y,r in profile for j in range(segments)]
    faces=[(i*segments+j,(i+1)*segments+j,(i+1)*segments+(j+1)%segments,i*segments+(j+1)%segments)
           for i in range(len(profile)-1) for j in range(segments)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.materials.append(M[material])
    for face in me.polygons:face.use_smooth=True
    return _s3_obj(name,me,(0,0,0),parent,label,'roller')

def motor(station,key,label,loc,axis,radius,length):
    """A finned cartridge or flange motor with connector, output and mounting screws."""
    g=empty('R70_'+key+'_motor',loc,station,label+'电机','motor')
    g['anchorPart']=key+'_motor';g['driveRole']='motor';g['motorDetailScope']='external_only'
    g['internalGeometryModeled']=False;g['motorLayoutEvidence']='inferred_functional_layout'
    g['description']='技术册明确该工位独立驱动。壳体比例、轴端、安装朝向和接线位置为功能示意。'
    # Native +X is the drive axis; for spin-box cartridges the operator is toward -Y.
    if axis=='y':g.rotation_euler.z=-math.pi/2
    C(g,'cartridge_body',(0,0,0),radius,length,'dark','x','电机外壳','motor',36)
    for end in [-1,1]:
        C(g,'motor_end',(end*length*.46,0,0),radius*1.08,length*.075,'steel','x','端盖止口','motor',36)
    for i in range(8):
        angle=i*math.pi/4
        fin=B(g,'body_rib',(0,radius*math.cos(angle),radius*math.sin(angle)),
              (length*.73,radius*.14,radius*.18),'r70deep','外壳纵向筋','motor',.0007)
        fin.rotation_euler.x=angle
    B(g,'cable_socket',(-length*.24,0,radius*1.03),(length*.23,radius*.73,radius*.57),'black','线缆插座','motor',.001)
    for i in range(4):
        a=math.pi*(.25+i*.5)
        C(g,'mount_screw',(length*.51,radius*.82*math.cos(a),radius*.82*math.sin(a)),
          radius*.105,length*.08,'steel','x','端盖紧固螺栓','motor',6)
    shaft=empty('R70_'+key+'_output',(length*.58,0,0),g,label+'输出端','motor',spin='x')
    shaft['anchorPart']=key+'_out';shaft['motorDetailRole']='shaft'
    C(shaft,'output_stub',(0,0,0),radius*.27,length*.26,'steel','x','外伸轴端','motor',24)
    return g

def working(station,key,label,loc,axis=None):
    node=empty('R70_'+key+'_load',loc,station,label,'roller',spin=axis)
    node['anchorPart']=key+'_load'
    return node

def station_prototype(parent):
    s=empty('R70_position',parent=parent,label='转杯纺纱位')
    # Rectangular can & folded sliver under each spinning position (220 x 920 mm).
    can=empty('R70_can',(0,-.47,0),s,'矩形条筒')
    B(can,'can_body',(0,0,.535),(.220,.920,1.050),'r70can','条筒筒身','frame',.026)
    for z in [.035,1.055]:
        B(can,'can_band',(0,0,z),(.220,.920,.030),'steel','条筒包边','frame',.012)
    B(can,'sliver_surface',(0,0,1.071),(.205,.89,.008),'cloth','盘条顶层','material',.02)
    pts=[(.076*math.sin(i*math.pi/7),-.40+i*.012,1.078) for i in range(66)]
    P(can,'sliver_coils',pts,.009,'cloth','条筒内可见棉条','material')
    P(s,'sliver_in',[(0,-.57,1.078),(.012,-.638,1.09),(.026,-.69,1.19),(.047,-.67,1.285)],
      .008,'cloth','棉条由条筒进入喂条口','material')
    # A shaped, separate front cover reveals its spin box in x-ray or exploded view.
    shield=empty('R70_spinbox_door',(0,-.725,1.49),s,'纺纱箱可开启前罩','shell',explode=[0,.07,.29])
    B(shield,'spinbox_face',(0,0,0),(.206,.034,.385),'r70green','纺纱箱前面板','shell',.017)
    for loc,r in [((-.04,-.020,.078),.040),((.047,-.022,-.092),.051)]:
        C(shield,'spinbox_access',loc,r,.014,'steel','y','纺纱箱圆形检修口','shell',36)
    B(shield,'spinbox_handle',(.083,-.036,.016),(.017,.029,.116),'dark','纺纱箱开启手柄','shell',.004)
    B(shield,'box_indicator',(-.072,-.026,.163),(.036,.014,.020),'r70blue','纺位状态指示窗','shell',.002)
    B(s,'spinbox_back',(0,-.47,1.46),(.209,.042,.39),'r70deep','纺纱箱安装背板')
    motor(s,'feed','喂条',(.045,-.584,1.285),'y',.024,.104)
    feed=working(s,'feed','喂给罗拉',(.045,-.671,1.285),'z')
    C(feed,'feed_roller',(0,0,0),.019,.064,'steel','y','喂给罗拉齿面','roller',32)
    for i in range(12):
        a=i*math.tau/12
        C(feed,'feed_flute',(.018*math.cos(a),0,.018*math.sin(a)),.0015,.060,'steel','y','喂给罗拉纵向棱','roller',6)
    B(s,'feed_table',(.045,-.675,1.260),(.063,.065,.012),'dark','给棉板','frame',.002)
    motor(s,'opening','分梳',(.047,-.565,1.390),'y',.030,.118)
    opening=working(s,'opening','针布分梳辊',(.047,-.665,1.390),'z')
    C(opening,'opening_drum',(0,0,0),.038,.061,'steel','y','分梳辊体','roller',40)
    # Toothed helices share a single mesh across all 48 heads.
    verts=[];faces=[]
    for row in range(8):
        for i in range(32):
            a=math.tau*(i+row*.32)/32;y=(row-3.5)*.007
            k=len(verts)
            for da,dy,r in [(-.055,-.002,.038),(.055,-.002,.038),(0,.002,.038),(.06,.001,.042)]:
                verts.append((r*math.cos(a+da),y+dy,r*math.sin(a+da)))
            faces.extend([(k,k+2,k+1),(k,k+1,k+3),(k+1,k+2,k+3),(k+2,k,k+3)])
    me=bpy.data.meshes.new('R70_opening_wire');me.from_pydata(verts,[],faces);me.update();me.materials.append(M['steel'])
    _s3_obj('opening_wire',me,(0,0,0),opening,'分梳辊螺旋齿列','roller')
    motor(s,'cup','转杯',(-.042,-.555,1.565),'y',.031,.146)
    cup=working(s,'cup','带凝聚槽的纺纱转杯',(-.042,-.665,1.565),'z')
    lathed(cup,'spin_cup',[(-.017,.018),(-.012,.022),(.006,.020),(.017,.009),(.017,0),(.012,0),(.002,.015),(-.010,.019),(-.017,.018)],'steel','纺纱转杯及内壁凝聚槽')
    C(cup,'cup_motion_mark',(.0188,-.016,0),.0011,.0013,'copper','y','转杯运动观察点','roller',10)
    P(s,'fibre_channel',[(.052,-.652,1.430),(.033,-.633,1.475),(-.012,-.642,1.510),(-.022,-.663,1.560)],
      .009,'r70deep','分梳辊至转杯的输纤通道','frame')
    P(s,'bypass',[(.083,-.648,1.40),(.09,-.57,1.366),(.08,-.39,1.34)],.012,'black','BYpass 排杂支路','frame')
    T(s,'nozzle',(-.042,-.704,1.565),.010,.003,'steel','y','静止引纱嘴','roller')
    draw=working(s,'delivery','引纱罗拉及压辊',(-.021,-.727,1.87),'x')
    C(draw,'delivery_roller',(0,0,0),.029,.1,'steel','x','引纱罗拉','roller',32)
    C(s,'delivery_nip',(-.021,-.773,1.873),.019,.083,'black','x','引纱压辊','roller',28)
    P(s,'yarn_lead',[(-.042,-.705,1.565),(-.042,-.765,1.60),(-.03,-.778,1.75),(-.021,-.755,1.87),(-.021,-.742,1.897)],
      .0022,'r70line','从引纱嘴至引纱罗拉的纱段','material')
    B(s,'clearer',(-.015,-.718,1.79),(.072,.034,.045),'dark','清纱检测头','frame',.005)
    motor(s,'package','卷绕',(-.078,-.603,2.20),'x',.040,.068)
    package=working(s,'package','卷绕工作辊与筒子',(.012,-.603,2.20))
    drum=empty('R70_package_drum',(0,0,0),package,'卷绕工作辊','roller',spin='x')
    C(drum,'winding_drum',(0,0,0),.057,.157,'dark','x','卷绕工作辊','roller',40)
    bob=empty('R70_package',(0,0,.181),package,'圆柱形筒子纱','material',spin='x');bob['spinSpeed']=-.35
    C(bob,'wound_yarn',(0,0,0),.124,.155,'cloth','x','纱层','material',48)
    for x in [-.089,.089]:
        C(bob,'package_cone_end',(x,0,0),.027,.022,'copper','x','纸管外伸端','material',24)
    for j in range(5):
        T(bob,'package_winding_trace',((j-2)*.029,0,0),.1238,.0009,'cloth','x','卷装纱层纹理','material')
    P(bob,'cross_wound_yarn',[(-.074+.148*i/72,.124*math.cos(i*math.pi/9),.124*math.sin(i*math.pi/9)) for i in range(73)],
      .00085,'r70line','卷装表层绕纱轨迹','material')
    for x in [-.099,.102]:
        P(s,'package_cradle',[(x,-.44,2.19),(x,-.51,2.34),(x,-.603,2.381)],.009,'r70green','卷绕摇架夹臂')
    motor(s,'guide','横动导纱',(-.074,-.654,2.047),'x',.023,.061)
    C(s,'traverse_rail',(0,-.691,2.047),.007,.193,'steel','x','横动导轨')
    guide=working(s,'guide','往复横动导纱器',(0,-.691,2.047))
    guide['travelAmplitude']=.066
    B(guide,'traverse_slide',(0,0,0),(.020,.020,.018),'r70deep','横动滑块','roller',.003)
    T(guide,'traverse_eye',(0,-.008,.012),.007,.0018,'steel','y','导纱眼','roller')
    # Unit cylinders aligned by the viewer between the nip, moving eye and drum.
    for role in ['in','out']:
        start=(-.021,-.742,1.897) if role=='in' else (0,-.699,2.059)
        end=(0,-.699,2.059) if role=='in' else (0,-.660,2.20)
        a,b=Vector(start),Vector(end);delta=b-a
        yarn=C(s,'live_yarn_'+role,tuple((a+b)/2),.0022,1.,'r70line','z','随横动导纱的纱段','material',8)
        yarn.rotation_euler=Vector((0,0,1)).rotation_difference(delta.normalized()).to_euler()
        yarn.scale.z=delta.length;yarn['travelYarn']=role
    return s

def end_panel(x,length,title,color,doors,height):
    group=empty('R70_end_housing',(x,0,0),ROOT,title,'shell')
    B(group,'cabinet_plinth',(0,0,.09),(length-.02,1.55,.18),'r70deep',title+'底座')
    B(group,'cabinet_roof',(0,0,height-.017),(length,1.62,.034),color,title+'顶板','shell')
    for edge in [-1,1]:
        B(group,'cabinet_end',(edge*(length/2-.016),0,height/2),(.032,1.62,height),color,title+'端板','shell')
        door=empty('R70_service_side',(0,edge*.81,0),group,title+'检修门','shell',explode=[0,.16,-edge*.38])
        for j in range(doors):
            xx=-length/2+(j+.5)*length/doors
            B(door,'panel_leaf',(xx,0,(height+.14)/2),(length/doors-.018,.028,height-.16),color,'分段检修门','shell',.009)
            B(door,'cabinet_latch',(xx+length/doors*.32,edge*.025,height*.54),(.020,.023,.10),'dark','门锁与把手','shell',.003)
    return group

def make_robot(side,x):
    r=empty('R70_doff_robot',(x,side*.96,0),ROOT,'自动落筒机器人')
    r['componentRole']='doff_robot';r['machineSide']='A' if side<0 else 'B'
    B(r,'robot_outer',(0,side*.16,2.13),(.67,.26,1.57),'r70green','落筒机器人外壳','shell',.04)
    B(r,'robot_service',(0,side*.298,2.12),(.20,.017,1.19),'r70deep','机器人检修盖','shell',.008)
    for z in [1.45,2.74]:
        B(r,'robot_caution',(.28,side*.302,z),(.06,.012,.11),'orange','机器人警示标志','shell',.003)
    B(r,'robot_carriage',(0,0,2.84),(.77,.51,.13),'steel','轨道行走小车','frame',.01)
    B(r,'robot_cable_cover',(0,0,2.933),(.34,.18,.034),'r70deep','机器人上部走线盖','shell',.006)
    for xx in [-.25,.25]:
        C(r,'robot_wheel',(xx,-side*.13,2.84),.047,.054,'dark','y','机器人行走轮')
    pick=tagged(empty('R70_doff_gripper',(0,-side*.10,2.34),r,'落筒夹持机构'),'driveAnchorId','R70_doffer_'+r['machineSide'])
    for xx in [-.088,.088]:
        P(pick,'gripper_finger',[(xx,0,.13),(xx,-side*.11,.04),(xx,-side*.11,-.045)],.012,'steel','落筒夹指')
    P(r,'robot_cable',[(0,0,2.83),(.13,0,2.910),(.41,0,2.921),(.65,0,2.84)],.012,'black','机器人引线')

def build():
    left=-11.453/2
    x0=left+2.211
    end_panel(left+1.057+.577,1.154,'车头控制箱','r70deep',2,1.895)
    tail=end_panel(x0+5.64+1.801,3.602,'吸风过滤车尾','r70green',4,1.895)
    for y in [-.39,.39]:
        C(tail,'filter_body',(-.64,y,1.13),.29,.88,'steel','z','过滤腔体','frame',32)
        T(tail,'filter_ring',(-.64,y,1.53),.29,.014,'dark','z','过滤器检修密封圈')
    outlet=tagged(empty('R70_filter_out',(.5,0,1.70),tail,'过滤与排风接口'),'driveAnchorId','R70_vacuum_end')
    C(outlet,'duct_socket',(0,0,0),.22,.22,'steel','z','排风连接法兰')
    B(tail,'hmi_screen',(1.20,-.836,1.40),(.33,.028,.26),'dark','整机触摸屏','frame',.014)
    B(tail,'hmi_glass',(1.20,-.854,1.40),(.28,.012,.204),'r70blue','触控显示区','frame',.007)
    for j,material in enumerate(['green','orange','r70blue','white']):
        C(tail,'signal_lamp',(1.48,-.52,1.92+j*.046),.036,.044,material,'z','机端信号灯','frame',24)
    loader=empty('R70_tube_loader',(left+.5285,0,0),ROOT,'机头双侧空管供给架')
    B(loader,'loader_base',(0,0,.80),(1.057,1.60,.15),'r70deep','供管架底梁')
    for side in [-1,1]:
        for lane in range(6):
            x=-.44+.174*lane
            B(loader,'tube_channel',(x,side*.47,1.70),(.145,.25,1.62),'r70deep','可独立启用的储管通道')
            for level in range(8):
                C(loader,'tube_sample',(x,side*.60,1.01+level*.176),.050,.19,'copper','y','在架空纱管','material',20)
        B(loader,'loader_lid',(0,side*.43,2.55),(1.046,.79,.07),'r70green','供管架顶盖','shell')
    for side in [-1,1]:
        make_robot(side,x0+(1.05 if side<0 else 4.80))
        anchor='A' if side<0 else 'B'
        belt=tagged(empty('R70_package_conveyor',(x0+2.82,side*.36,2.53),ROOT,'成筒输送带'),'driveAnchorId','R70_conveyor_'+anchor)
        B(belt,'package_belt',(0,0,0),(5.64,.30,.026),'black','成筒输送带工作面')
        for xx in [-2.77,2.77]:C(belt,'belt_end',(xx,0,-.014),.031,.30,'steel','y','成筒皮带端辊')
        B(ROOT,'gantry_rail',(x0+2.82,side*.84,2.82),(5.87,.094,.083),'steel','落筒机器人纵轨')
    proto=None
    for section in range(2):
        mid=x0+(section+.5)*2.82
        mod=empty('R70_section',(mid,0,0),ROOT,'24 纺位机节');mod['sectionIndex']=section+1
        B(mod,'suction_duct',(0,0,1.50),(2.82,.37,.36),'r70deep','机节负压总管')
        for side in [-1,1]:
            anchor='A' if side<0 else 'B'
            B(mod,'lower_beam',(0,side*.45,1.219),(2.82,.24,.088),'r70deep','机节下缘与机梁')
            B(mod,'upper_beam',(0,side*.45,2.48),(2.82,.18,.080),'r70green','卷绕与输送支承梁')
            for x in [-1.382,1.382]:
                B(mod,'leg',(x,side*.16,.61),(.052,.063,1.22),'steel','机节支腿')
                B(mod,'foot',(x,side*.16,.02),(.12,.13,.04),'dark','调平支脚')
            for j in range(12):
                local=section*12+j+1; number=local+(24 if side>0 else 0)
                xx=(j-5.5)*.230
                if proto is None:
                    s=station_prototype(mod);proto=s
                else:s=_s3_clone_tree(proto,mod,(xx,0,0),'R70_position')
                s.location=(xx,0,0);s.rotation_euler.z=math.pi if side>0 else 0
                s['positionIndex']=number;s['machineSide']=anchor;s['sectionIndex']=section+1
                s['sidePosition']=local;s.name='R70_station_'+anchor+str(local).zfill(2)
                for node in s.children_recursive:
                    if 'anchorPart' not in node:continue
                    part=node['anchorPart'];key=f'R70_{anchor}{local:02}_{part}'
                    node.name=key;node['driveAnchorId']=key
    _s3_finish(ROOT)
    # Robot tops and the dimensional drawing share the same nominal service envelope.
    ROOT['machineWidthMetres']=2.536
    return ROOT

root=build()
bpy.context.view_layer.update()
nodes=[root]+list(root.children_recursive)
assert sum(o.get('driveRole')=='motor' for o in nodes)==240
assert len({o['driveAnchorId'] for o in nodes if o.get('driveRole')=='motor'})==240
bpy.ops.object.select_all(action='DESELECT')
for o in nodes:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND/'rotor-spinning-r70.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'rotor_spinning.glb'),export_format='GLB',
    use_selection=True,export_extras=True,export_yup=True,export_apply=True,export_animations=False)
print('ROTOR_EXPORTED',len(nodes),flush=True)
