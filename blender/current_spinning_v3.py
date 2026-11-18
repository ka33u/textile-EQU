"""Current-reference cotton preparation and spinning assets.
Exec after industrial_v2.py and motor_precision.py. Definitions only; no export.
Public configuration facts are in research/config-spinning-v3.json.
This is a partial public-reference reconstruction, not OEM CAD/BOM.
"""
import math
from mathutils import Vector, Matrix

_S3_GEOMETRY = {}
_S3_URL = 'https://www.rieter.com/products/systems/'

def _s3_obj(name, data, loc, parent, label, group='frame'):
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o)
    o.parent=parent;o.location=loc;meta(o,label,group)
    o['evidenceStatus']='inferred_geometry';return o

def _s3_box(parent,name,loc,size,ma='white',label=None,group='frame',bevel=.012):
    key=('b',tuple(round(float(v),5) for v in size),ma,bevel)
    if key not in _S3_GEOMETRY or _S3_GEOMETRY[key].name not in bpy.data.meshes:
        o=box(name,(0,0,0),size,ma,None,label or name,group,bevel)
        _S3_GEOMETRY[key]=o.data;bpy.data.objects.remove(o,do_unlink=True)
    return _s3_obj(name,_S3_GEOMETRY[key],loc,parent,label or name,group)

def _s3_cyl(parent,name,loc,r,length,ma='steel',axis='x',label=None,group='roller',n=32):
    key=('c',round(r,6),round(length,6),ma,axis,n)
    if key not in _S3_GEOMETRY or _S3_GEOMETRY[key].name not in bpy.data.meshes:
        o=cyl(name,(0,0,0),r,length,ma,None,label or name,axis,group,n)
        _S3_GEOMETRY[key]=o.data;bpy.data.objects.remove(o,do_unlink=True)
    return _s3_obj(name,_S3_GEOMETRY[key],loc,parent,label or name,group)

def _s3_torus(parent,name,loc,r,t,ma='steel',axis='z',label=None,group='roller'):
    key=('t',round(r,6),round(t,6),ma,axis)
    if key not in _S3_GEOMETRY or _S3_GEOMETRY[key].name not in bpy.data.meshes:
        o=torus(name,(0,0,0),r,t,ma,None,label or name,axis,group)
        _S3_GEOMETRY[key]=o.data;bpy.data.objects.remove(o,do_unlink=True)
    return _s3_obj(name,_S3_GEOMETRY[key],loc,parent,label or name,group)

def _s3_pipe(parent,name,points,r=.018,ma='steel',label=None,group='frame'):
    # Local centered paths permit mesh reuse for repeated yarn and mechanical units.
    org=Vector(points[0]);pts=[tuple(Vector(p)-org) for p in points]
    key=('p',tuple(tuple(round(v,5) for v in p) for p in pts),r,ma)
    if key not in _S3_GEOMETRY or _S3_GEOMETRY[key].name not in bpy.data.meshes:
        o=tube(name,pts,r,ma,None,label or name,group)
        _S3_GEOMETRY[key]=o.data;bpy.data.objects.remove(o,do_unlink=True)
    return _s3_obj(name,_S3_GEOMETRY[key],tuple(org),parent,label or name,group)

def _s3_root(stage,title,model,configuration,url):
    r=empty('stage_'+stage,label=title);roots.append(r)
    for k,v in {'stage':stage,'equipmentId':stage,'modelVersion':'3.0','referenceManufacturer':'Rieter','referenceModel':model,'referenceConfiguration':configuration,'referenceStatus':'partial_public_reference','fidelityStatus':'partial_public_reference','structuralCompleteness':False,'referenceUrl':url,'modelType':'public_configuration_reconstruction','dimensionsUnit':'metres','capacityMatchedLine':False}.items():r[k]=v
    return r

def _s3_finish(r):
    # Ground all components and centre individual assets; preserve engineering dimensions.
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(c) for o in r.children_recursive if o.type=='MESH' for c in o.bound_box]
    if pts:
        lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
        shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
        for o in r.children:o.location+=shift
    return r

def _s3_module(parent,name,loc,size,label,doors=2,color='white'):
    g=empty(name,loc,parent,label,'shell',explode=[0,.4,.55])
    w,d,h=size
    # Separate panels reveal actual contents under x-ray, unlike a solid cabinet block.
    for xx in (-w/2,w/2):_s3_box(g,name+'_end',(xx,0,h/2),(.045,d,h),color,label,'shell')
    _s3_box(g,name+'_roof',(0,0,h),(w,d,.045),color,label+'顶罩','shell')
    _s3_box(g,name+'_rear',(0,d/2,h/2),(w,.04,h),color,label+'后板','shell')
    _s3_box(g,name+'_sill',(0,0,.10),(w,d,.15),'teal',label+'机座')
    for j in range(doors):
        x=-w/2+(j+.5)*w/doors;ww=w/doors-.018
        _s3_box(g,name+'_door',(x,-d/2,h/2),(ww,.035,h-.15),color,label+'检修门','shell')
        _s3_box(g,name+'_handle',(x+ww*.35,-d/2-.035,h*.53),(.018,.025,.16),'dark','门把手','shell',.004)
        for z in (.2,h-.2):_s3_box(g,name+'_hinge',(x-ww*.45,-d/2-.024,z),(.026,.018,.07),'steel','门铰链','shell',.002)
    for x in (-w*.43,w*.43):
        for y in (-d*.4,d*.4):_s3_cyl(g,'level_foot',(x,y,.025),.055,.05,'black','z','调平底脚','frame',24)
    return g

def _s3_drive(parent,name,loc,size=(.32,.24,.24),kind='servo'):
    g=empty(name,loc,parent,'独立'+('伺服驱动外壳' if kind=='servo' else '电动机外壳'),'motor')
    g['evidenceStatus']='drive_function_verified_envelope_inferred';g['internalGeometryVerified']=False
    w,d,h=size
    if kind=='servo':
        _s3_box(g,'servo_body',(0,0,0),size,'dark','伺服电机外壳','motor')
        _s3_box(g,'servo_flange',(w/2,0,0),(.025,d*1.12,h*1.12),'steel','安装法兰','motor')
        _s3_box(g,'encoder_cap',(-w/2-.025,0,0),(.05,d*.9,h*.9),'black','编码器端罩','motor')
    else:
        _s3_cyl(g,'industrial_drive_housing',(0,0,0),h*.5,w,'teal','x','工艺电机壳体','motor')
        for j in range(12):
            a=j*math.pi/6
            f=_s3_box(g,'drive_fin',(0,h*.52*math.cos(a),h*.52*math.sin(a)),(w*.9,.012,h*.15),'teal','电机散热筋','motor',.002);f.rotation_euler[0]=a
        _s3_box(g,'terminal_box',(0,0,h*.64),(w*.4,d*.6,h*.28),'teal','接线盒','motor')
        for yy in (-d*.35,d*.35):_s3_box(g,'drive_foot',(0,yy,-h*.5),(w*.8,.055,.06),'steel','电机底脚','motor',.006)
    axis=empty('rotate_'+name,(w/2+.04,0,0),g,'驱动轴','motor',spin='x')
    _s3_cyl(axis,'drive_shaft',(0,0,0),min(d,h)*.1,.12,'steel','x','输出轴','motor')
    return g

def _s3_can(parent,loc,d=.6,h=1.2,label='条筒'):
    g=empty('sliver_can',loc,parent,label,'material')
    _s3_cyl(g,'can_body',(0,0,h/2+.035),d/2,h,'white','z',label,'material')
    for z in (.08,h+.04):_s3_torus(g,'can_rim',(0,0,z),d/2,.014,'steel','z','条筒口圈','material')
    _s3_cyl(g,'sliver_surface',(0,0,h+.045),d*.46,.018,'cloth','z','筒内棉条','material')
    for a in (0,math.pi/2,math.pi,math.pi*1.5):_s3_cyl(g,'can_castor',(d*.29*math.cos(a),d*.29*math.sin(a),.035),.035,.03,'black','x','条筒脚轮','frame',16)
    return g

def _s3_hmi(parent,loc,label):
    x,y,z=loc
    _s3_box(parent,'hmi_pedestal',(x,y,z-.18),(.035,.035,.4),'steel','HMI安装支杆')
    _s3_box(parent,'hmi_display',loc,(.28,.055,.22),'dark',label,'shell')
    _s3_box(parent,'hmi_glass',(x,y-.03,z),(.235,.006,.17),'glass','操作触屏','shell',.003)
    _s3_cyl(parent,'emergency_stop',(x+.20,y-.03,z-.14),.025,.025,'red','y','急停按钮','shell',24)

def _s3_roll(parent,name,loc,r,length,ma='steel',axis='x'):
    g=empty('rotate_'+name,loc,parent,name,'roller',spin={'x':'x','y':'z','z':'y'}[axis])
    _s3_cyl(g,name+'_surface',(0,0,0),r,length,ma,axis,name)
    _s3_cyl(g,name+'_axle',(0,0,0),r*.23,length+.14,'steel',axis,'辊端轴伸')
    return g

def machine_opening():
    r=_s3_root('opening','A12与VARIOline开清棉配置','UNIfloc A 12 + UNIclean B 12 + UNImix B 72 + UNIstore A 79','单侧取棉；棉清理模块与A49重物分离、A21输送接口；厂房布局推定',_S3_URL+'fiber-preparation/blowroom-line-varioline')
    # Bale laydown is site equipment, not a shortened version of a fixed machine.
    for y in (-.37,.37):_s3_box(r,'A12_travel_rail',(-5.5,y,.09),(12,.10,.13),'steel','A12行走轨道')
    for j in range(10):
        for side in (-1,1):_s3_box(r,'cotton_bale',(-10.5+j*1.05,side*1.75,.62),(.96,1.4,1.2),'cloth','配棉场棉包','material',.04)
    cart=empty('A12_travelling_tower',(-5.5,0,0),r,'A12移动塔')
    _s3_module(cart,'A12_tower',(0,0,.15),(1.05,1.10,3.25),'抓棉塔机身',2)
    for x in (-.42,.42):
        for y in (-.40,.40):_s3_cyl(cart,'A12_wheel',(x,y,.18),.15,.09,'dark','y','行走轮')
    for x in (-.44,.44):_s3_box(cart,'lift_guide',(x,-.57,1.85),(.06,.06,3.05),'steel','抓棉臂升降直线导轨')
    arm=_s3_module(cart,'A12_plucking_arm',(0,-1.55,1.38),(.92,2.30,.48),'单侧抓棉头',1)
    _s3_roll(cart,'A12抓棉辊',(0,-1.55,1.39),.095,2.08,'steel','y')
    for j in range(32):
        _s3_cyl(cart,'plucking_disc',(0,-2.53+j*.064,1.39),.122,.012,'steel','y','抓棉辊盘；盘形由公开外观推定',n=24)
    drive=_s3_drive(cart,'A12_torque_direct_drive',(0,-.35,1.39),(.28,.28,.28));drive.rotation_euler[2]=-math.pi/2
    _s3_drive(cart,'A12_lift_drive',(.26,.25,.64),(.3,.23,.23))
    _s3_pipe(cart,'A12_fiber_suction',[(0,0,3.43),(0,0,3.8),(1.3,0,4.0),(2.2,0,4.0)],.19,'steel','吸棉主管')
    _s3_hmi(cart,(.65,-.63,1.55),'A12操作屏')
    # Each linked machine remains independently labelled and explodable.
    b12=_s3_module(r,'B12',(-.4,0,0),(2.227,1.04,2.020),'UNIclean B12预清棉机',2)
    _s3_roll(b12,'B12清棉辊',(0,0,1.0),.375,1.6)
    _s3_box(b12,'waste_chute',(0,0,.26),(1.70,.8,.23),'dark','落杂收集腔')
    b72=_s3_module(r,'B72',(3.0,0,0),(3.7,2.15,3.6),'UNImix B72混棉机',6)
    for i in range(6):
        _s3_box(b72,'mixing_chamber_divider',(-1.55+i*.62,0,2.05),(.028,2.0,2.8),'steel','混棉仓隔板')
        _s3_roll(b72,'混棉输出罗拉',(-1.55+i*.62,0,.60),.11,1.85,axis='y')
    a79=_s3_module(r,'A79',(6.45,0,0),(1.80,1.35,3.0),'UNIstore A79储棉精开松机',2)
    _s3_roll(a79,'A79开松辊',(0,0,1.20),.25,1.25)
    a49=_s3_module(r,'A49',(-2.25,3.20,0),(.85,.90,1.90),'A49重物分离器',1)
    for a,b in [((-3.3,0,4),(-2.25,3.20,2.10)),((-2.25,3.20,2.10),(-.4,0,2.25)),((-.4,0,2.25),(3,0,3.85)),((4.8,0,3.85),(6.45,0,3.25))]:
        _s3_pipe(r,'intermachine_tuft_duct',[a,(a[0],a[1],4.35),(b[0],b[1],4.35),b],.17,'steel','机间纤维输送管；厂房管线推定')
    condenser=_s3_module(r,'A21',(8.4,0,1.8),(1.1,1.05,1.0),'A21凝棉器接口',1)
    _s3_pipe(r,'A79_A21_duct',[(6.45,0,3.25),(8.4,0,3.25),(8.4,0,2.8)],.17,'steel','末端凝棉输送')
    for x in (8.0,8.8):_s3_box(r,'condenser_support',(x,0,.9),(.10,.9,1.8),'teal','凝棉器支承')
    _s3_drive(r,'transport_fan_drive',(8.4,.85,2.23),(.45,.38,.38),'induction')
    _s3_pipe(r,'waste_air_header',[(-.4,.8,.3),(3,.8,.3),(6.45,.8,.3),(7.3,2.2,.3)],.10,'dark','落杂吸排总管；外部过滤机组为未核定接口')
    return _s3_finish(r)

def machine_carding():
    r=_s3_root('carding','C81高产梳棉机','C 81','40个工作盖板；CGC/TLM/IGS功能位置；单眼圈条，未配置RSB-Module 55',_S3_URL+'fiber-preparation/card-c-81')
    _s3_module(r,'C81_main',(0,0,0),(2.35,3.5,1.80),'C81主机分段检修外罩',4)
    _s3_module(r,'C81_feed_chute',(0,2.1,0),(1.75,.8,3.28),'C81气流喂棉箱',2)
    _s3_roll(r,'C81主锡林',(0,0,1.04),.60,1.50)
    _s3_roll(r,'C81刺辊',(0,1.05,.80),.17,1.50)
    _s3_roll(r,'C81道夫',(0,-.91,.82),.30,1.50)
    # Exactly forty working flats. Return path is separately identified as inferred.
    for i in range(40):
        a=.12+(math.pi-.24)*i/39
        o=_s3_box(r,'C81_working_flat',(0,.665*math.cos(a),1.04+.665*math.sin(a)),(1.55,.038,.028),'teal','C81工作盖板 '+str(i+1),'roller',.003);o.rotation_euler[0]=a-math.pi/2;o['evidenceStatus']='verified_count_inferred_geometry'
    for i in range(40):
        _s3_box(r,'C81_return_flat',(0,-.66+i*1.32/39,1.83),(1.55,.027,.028),'dark','盖板回程；返回段数量/链距未有BOM','roller',.002)
    for x in (-.80,.80):
        _s3_pipe(r,'C81_flat_chain',[(x,-.69,1.13),(x,-.69,1.8),(x,.69,1.8),(x,.69,1.13)],.018,'steel','回转盖板链路；外形推定')
        for y in (-.69,.69):_s3_cyl(r,'C81_chain_sprocket',(x,y,1.72),.09,.045,'steel','x','盖板回程导轮')
    for x in (-.84,.84):_s3_box(r,'CGC_sensor',(x,.35,1.60),(.07,.10,.10),'orange','CGC梳理间隙检测/调节位置','roller',.004)
    _s3_box(r,'TLM_module',(.90,1.05,.90),(.16,.20,.12),'orange','TLM落杂监测功能位置','roller')
    _s3_pipe(r,'IGS_traverse',[(-.82,-.18,1.63),(.82,-.18,1.63)],.026,'steel','IGS磨针横移装置位置')
    _s3_roll(r,'剥网辊',(0,-1.40,.75),.07,1.50)
    _s3_pipe(r,'card_sliver',[(0,-1.45,.83),(0,-1.85,.92),(0,-2.35,1.38)],.022,'cloth','棉网集束输送','material')
    _s3_module(r,'C81_coiler',(0,-2.25,.92),(1.35,.85,.58),'圈条器独立机头',2)
    _s3_cyl(r,'C81_coiler_disc',(0,-2.25,1.15),.30,.12,'teal','z','圈条盘')
    _s3_can(r,(0,-2.25,0),.90,1.05);_s3_can(r,(1.05,-2.25,0),.90,1.05,'备用条筒')
    _s3_drive(r,'C81_cylinder_drive',(.94,.30,.65),(.40,.30,.30),'induction')
    for y in (-1.1,.2,1.1):_s3_pipe(r,'C81_suction_branch',[(.80,y,.45),(1.0,y,.30),(1.0,1.65,.30)],.045,'dark','锡林/刺辊/道夫吸排支管')
    _s3_pipe(r,'C81_suction_main',[(1,1.65,.3),(1,2.6,.3),(1,2.6,3.25)],.12,'steel','梳棉主吸风接口')
    _s3_hmi(r,(-1.12,-1.70,1.65),'C81操作屏');return _s3_finish(r)

def machine_drawing():
    r=_s3_root('drawing','RSB-D55单眼自调匀整并条机','RSB-D 55','8并合；单眼；RQM与CLEANtube；输出筒600mm，换筒结构公开外观重建',_S3_URL+'spinning-preparation/draw-frame-rsb-dsb-d-55')
    _s3_module(r,'RSBD55_main',(0,0,0),(1.55,1.60,1.45),'D55紧凑牵伸机体',2)
    cap=_s3_box(r,'RSBD55_drafting_hood',(0,0,1.58),(1.45,.94,.24),'teal','可开启牵伸区上罩','shell',.05)
    _s3_box(r,'RSBD55_head_frame',(0,0,1.29),(1.25,.80,.14),'steel','牵伸头承载架')
    for k,y in enumerate((.30,0,-.30)):
        _s3_roll(r,'D55下牵伸罗拉'+str(k),(0,y,1.40),.050,.48)
        _s3_roll(r,'D55上胶辊'+str(k),(0,y,1.49),.040,.48,'black')
    _s3_box(r,'RSB_scanning_pair',(0,.58,1.43),(.31,.12,.10),'orange','自调匀整喂入检测位置','roller')
    _s3_drive(r,'RSB_autolevel_servo',(.48,.15,1.30),(.26,.20,.20))
    _s3_drive(r,'D55_main_drive',(-.45,.25,.55),(.40,.29,.29),'induction')
    _s3_drive(r,'CLEANtube_coiler_drive',(.40,-.80,1.30),(.23,.17,.17))
    _s3_box(r,'coiler_bridge',(0,-1.05,1.29),(1.30,1.2,.16),'white','圈条与换筒桥架','shell')
    for x in (-.52,.52):_s3_box(r,'coiler_leg',(x,-1.30,.64),(.10,.10,1.28),'teal','圈条机脚')
    _s3_cyl(r,'coiler_rotating_disc',(0,-1.15,1.25),.27,.10,'steel','z','圈条盘')
    for y in (-1.15,-1.88,-2.61):_s3_can(r,(0,y,0),.6,1.15,'输出/换筒队列')
    for x in (-.40,.40):_s3_box(r,'can_change_guide',(x,-1.85,.10),(.06,2.10,.08),'steel','自动换筒地面导轨')
    for i in range(8):
        x=(-.65 if i%2==0 else .65);y=1.50+(i//2)*.75
        _s3_can(r,(x,y,0),.6,1.15,'喂入棉条筒 '+str(i+1))
        _s3_pipe(r,'draw_feed_sliver',[(x,y,1.22),(x*.65,y,1.82),(x*.65,.90,1.82),(0,.58,1.46)],.010,'cloth','第'+str(i+1)+'根并合喂条','material')
        _s3_cyl(r,'creel_feed_roller',(x*.65,y,1.80),.034,.16,'black','x','导条架主动喂入轮')
    for y in (1.45,2.95,4.1):
        for x in (-.48,.48):_s3_box(r,'power_creel_post',(x,y,.92),(.06,.06,1.84),'teal','动力导条架立柱')
        _s3_box(r,'power_creel_crossbar',(0,y,1.80),(1.10,.06,.07),'steel','导条架横梁')
    _s3_pipe(r,'drawframe_exhaust',[(.60,.3,.45),(.75,.3,.45),(.75,.85,.45)],.08,'steel','牵伸吸风与清洁接口')
    _s3_hmi(r,(-.55,-.55,1.85),'D55/RQM操作屏');return _s3_finish(r)

def machine_combing():
    r=_s3_root('combing','E90八头精梳与E40成卷准备','E 90 + OMEGAlap E 40 + SERVOlap E 26','E90八头/300mm棉卷/ROBOlap；E40完整28筒600mm；自动棉卷运输；非产能配套验算',_S3_URL+'spinning-preparation/comber-e-90')
    # E90 main body: complete eight-head row, individual lap supports and delivery table.
    _s3_module(r,'E90_bed',(1.65,0,0),(5.15,1.32,.88),'E90精梳主机',8)
    _s3_module(r,'E90_delivery_head',(-1.45,0,0),(1.10,1.45,1.50),'E90牵伸圈条车头',2)
    for i in range(8):
        x=-.58+i*.59
        g=empty('E90_combing_head',(x,0,0),r,'E90精梳头 '+str(i+1),'roller');g['headIndex']=i+1
        _s3_roll(g,'E90喂入棉卷',(0,.42,1.25),.275,.300,'cloth')
        for xx in (-.19,.19):_s3_box(g,'lap_cradle',(xx,.42,1.03),(.055,.55,.4),'teal','棉卷支承臂')
        _s3_roll(g,'RiQ圆梳',(0,-.04,.84),.12,.300,'orange')
        for yy in (-.20,-.29):_s3_roll(g,'分离罗拉',(0,yy,1.0),.036,.30)
        _s3_box(g,'nipper_top',(0,-.03,1.04),(.32,.12,.025),'steel','钳板夹持组件','roller',.003)
        _s3_box(g,'top_comb_bar',(0,-.17,1.08),(.30,.022,.045),'steel','顶梳座；针齿密度未有工程数据','roller',.002)
        _s3_pipe(g,'lap_sheet',[(0,.42,.97),(0,.12,1.06),(0,-.22,1.04),(0,-.48,1.0)],.023,'cloth','棉卷喂给与精梳棉网','material')
        _s3_pipe(r,'combed_sliver_delivery',[(x,-.48,1.0),(x,-.58,1.15),(-1.15,-.58,1.15)],.008,'cloth','精梳头集条输送','material')
        _s3_box(g,'ROBOlap_feed_apron',(0,.70,1.02),(.40,.22,.05),'dark','ROBOlap棉卷自动接续工作位','roller')
    _s3_box(r,'E90_sliver_table',(1.55,-.58,1.10),(5.15,.17,.05),'steel','八头集条台')
    for j in range(3):_s3_roll(r,'E90下牵伸辊',(-1.45,-.15+j*.13,1.35),.037,.36)
    for j in range(4):_s3_roll(r,'E90上胶辊',(-1.45,-.20+j*.11,1.415),.028,.36,'black')
    _s3_can(r,(-1.45,-1.25,0),.6,1.2);_s3_can(r,(-1.45,-1.95,0),.6,1.2,'备用输出筒')
    _s3_pipe(r,'E90_noil_duct',[(-1.8,.8,.25),(4,.8,.25),(4,.8,2.4)],.09,'steel','落棉中央吸风管')
    _s3_drive(r,'E90_main_drive',(-1.45,.20,.55),(.40,.30,.30),'induction')
    _s3_hmi(r,(-1.70,-.6,1.75),'E90/RQM屏')
    # E40 is separate machinery rather than a label attached to the comber.
    e40=empty('OMEGAlap_E40',(-.3,4.2,0),r,'OMEGAlap E40成卷准备');e40['referenceModel']='OMEGAlap E 40'
    _s3_module(e40,'E40_main',(-2.3,0,0),(1.48,2.10,1.80),'E40条并卷主机',2)
    for side in (-1,1):
        for row in range(7):
            for col in range(2):
                i=(side+1)//2*14+row*2+col;x=-.95+row*.68;y=side*(.50+col*.68)
                _s3_can(e40,(x,y,0),.60,1.20,'E40喂条筒 '+str(i+1))
                _s3_pipe(e40,'E40_infeed_sliver',[(x,y,1.26),(x,side*.22,1.80),(-1.65,side*.22,1.80)],.008,'cloth','E40第'+str(i+1)+'根喂条','material')
    for x in (-1.2,.8,3.0):
        for y in (-.25,.25):_s3_box(e40,'E40_powercreel_post',(x,y,.90),(.05,.05,1.80),'teal','E40动力导条架支柱')
    for y in (-.25,.25):_s3_box(e40,'E40_powercreel_rail',(1,y,1.80),(5,.06,.06),'steel','E40动力导条纵轨')
    for j in range(3):
        _s3_roll(e40,'E40下牵伸罗拉',(-2.3,-.25+j*.17,1.47),.048,.35)
        _s3_roll(e40,'E40上牵伸罗拉',(-2.3,-.25+j*.17,1.55),.034,.35,'black')
    _s3_roll(e40,'E40成卷',(-2.3,-.75,1.04),.29,.30,'cloth')
    arc=[(-2.3,-.75+.325*math.cos(a),1.04+.325*math.sin(a)) for a in [math.pi*.15+j*math.pi*1.70/32 for j in range(33)]]
    _s3_pipe(e40,'OMEGA_belt',arc,.026,'black','OMEGAlap环抱卷绕带；宽带结构外观推定','roller')
    _s3_hmi(e40,(-2.9,-1,1.85),'E40操作屏')
    # Public E26 overhead logistics; rail layout is an installation inference.
    _s3_pipe(r,'E26_transport_rail',[(-2.6,3.45,2.55),(-2.6,1.7,2.55),(4.0,1.7,2.55),(4.0,.45,2.55)],.05,'steel','SERVOlap E26棉卷运输轨道')
    for x,y in ((-2.6,3.45),(-2.6,1.7),(4,1.7)):_s3_box(r,'E26_support',(x,y,1.275),(.10,.10,2.55),'teal','自动棉卷运输门架')
    carriage=empty('E26_lap_carrier',(1,1.7,2.30),r,'E26自动棉卷吊运小车')
    _s3_box(carriage,'E26_traverse',(0,0,0),(.65,.32,.18),'teal','棉卷吊运车体')
    for x in (-.20,.20):_s3_box(carriage,'E26_gripper',(x,0,-.23),(.055,.10,.44),'steel','棉卷夹持臂')
    _s3_roll(carriage,'运输棉卷',(0,0,-.40),.275,.30,'cloth')
    return _s3_finish(r)

def _s3_clone_tree(source,parent,loc,name,index=None):
    mapping={}
    for old in [source]+list(source.children_recursive):
        new=old.copy();new.data=old.data if old.type=='MESH' else None
        bpy.context.collection.objects.link(new);mapping[old]=new
    for old,new in mapping.items():new.parent=parent if old==source else mapping[old.parent]
    g=mapping[source];g.location=loc;g.name=name
    if index is not None:g['positionIndex']=index
    return g

def _s3_unit_finish(g):
    # Merge only static direct-child meshes by semantic group/material. Rotating and
    # named process subassemblies remain independent children for interaction.
    bins={}
    for o in list(g.children):
        if o.type!='MESH':continue
        key=(o.get('group','frame'),tuple(m.name for m in o.data.materials))
        bins.setdefault(key,[]).append(o)
    for (group,mats),objects in bins.items():
        if len(objects)<2:continue
        verts=[];faces=[];smooth=[];labels=[]
        for o in objects:
            labels.append(o.get('label',o.name));offset=len(verts)
            mat=o.matrix_basis
            verts.extend(tuple(mat@v.co) for v in o.data.vertices)
            faces.extend(tuple(offset+i for i in p.vertices) for p in o.data.polygons)
            smooth.extend(p.use_smooth for p in o.data.polygons)
        data=bpy.data.meshes.new(g.name+'_'+group);data.from_pydata(verts,[],faces);data.update()
        for m in objects[0].data.materials:data.materials.append(m)
        for p,s in zip(data.polygons,smooth):p.use_smooth=s
        n=_s3_obj(g.name+'_'+group,data,(0,0,0),g,' / '.join(dict.fromkeys(labels)),group)
        n['componentLabels']=' | '.join(dict.fromkeys(labels));n['mergedWithoutOmission']=True
        for o in objects:bpy.data.objects.remove(o,do_unlink=True)
    return g

def _s3_ring_position(parent):
    g=empty('G38_spinning_position',(0,0,0),parent,'G38独立完整纺纱锭位','roller')
    rotor=empty('rotate_G38_spindle',(0,0,.68),g,'G38锭杆与管纱','roller',spin='y')
    _s3_cyl(rotor,'spindle_cop',(0,0,.085),.017,.205,'cloth','z','细纱管纱','material')
    _s3_cyl(rotor,'spindle_blade',(0,0,0),.008,.43,'steel','z','锭杆','roller')
    _s3_cyl(rotor,'spindle_whorl',(0,0,-.18),.012,.020,'orange','z','锭带盘','motor')
    _s3_torus(g,'G38_ring',(0,0,.70),.021,.003,'steel','z','42mm钢领')
    _s3_torus(g,'G38_traveller',(0,.021,.70),.004,.001,'copper','x','钢丝圈')
    _s3_torus(g,'G38_lappet',(0,0,1.01),.008,.002,'steel','z','短气圈导纱钩')
    _s3_box(g,'spindle_partition',(.034,0,.84),(.001,.12,.28),'steel','锭间隔纱板','frame',0)
    _s3_box(g,'ISM_sensor',(0,-.045,.58),(.030,.015,.025),'dark','ISM premium逐锭监测','frame',.002)
    # Compact 3-roller apron drafting and pressure arm at each spinning position.
    for j in range(3):
        yy=.045+j*.060
        _s3_cyl(g,'drafting_bottom',(0,yy,1.115+j*.018),.014,.060,'steel','x','下牵伸罗拉')
        _s3_cyl(g,'drafting_cot',(0,yy,1.143+j*.018),.014,.054,'black','x','上胶辊')
    _s3_box(g,'drafting_apron',(0,.105,1.14),(.045,.085,.012),'black','牵伸皮圈','roller',.003)
    arm=_s3_box(g,'weighting_arm',(0,.105,1.19),(.016,.19,.025),'teal','牵伸加压摇架','roller',.004);arm.rotation_euler[0]=.15
    _s3_pipe(g,'G38_fiber_path',[(0,.17,1.19),(0,.045,1.14),(0,0,1.01),(0,.021,.70),(0,.017,.73)],.0015,'cloth','粗纱—牵伸—导纱钩—钢丝圈—管纱','material')
    _s3_pipe(g,'suction_flute',[(0,.08,1.065),(0,.08,.99),(0,.24,.99)],.009,'steel','逐锭吸棉笛管')
    _s3_cyl(g,'SERVOdisc_tray',(0,-.135,.20),.024,.012,'dark','z','SERVOdisc管纱盘','roller',24)
    _s3_cyl(g,'empty_tube',(0,-.135,.30),.009,.19,'orange','z','自动落纱空管','material')
    _s3_torus(g,'doffer_gripper',(0,-.175,.84),.025,.006,'black','z','整机落纱夹持器')
    _s3_box(g,'doffer_gripper_arm',(0,-.115,.84),(.025,.10,.025),'steel','落纱夹爪连接臂')
    return _s3_unit_finish(g)

def _s3_roving_position(parent):
    g=empty('F40_roving_position',(0,0,0),parent,'F40独立粗纱锭位','roller')
    f=empty('rotate_F40_flyer',(0,0,1.0),g,'F40锭翼','roller',spin='y')
    _s3_cyl(f,'F40_bobbin',(0,0,0),.076,.406,'cloth','z','152mm粗纱卷装','material')
    _s3_cyl(f,'F40_spindle',(0,0,-.03),.015,.58,'steel','z','锭杆与定位冠')
    for side in (-1,1):
        _s3_pipe(f,'F40_flyer_leg',[(0,0,.32),(side*.087,0,.265),(side*.087,0,-.225)],.008,'steel','锭翼及平衡臂','roller')
    _s3_pipe(f,'F40_presser',[(.087,0,-.16),(.071,.026,-.16),(.070,.040,-.11)],.006,'steel','锭翼压掌','roller')
    _s3_torus(g,'F40_spindle_crown',(0,0,.74),.030,.006,'steel','z','粗纱管定位冠')
    for j in range(3):
        _s3_cyl(g,'F40_draft_bottom',(0,.10+j*.065,1.62+j*.016),.020,.10,'steel','x','牵伸下罗拉')
        _s3_cyl(g,'F40_draft_cot',(0,.10+j*.065,1.66+j*.016),.020,.095,'black','x','加压上胶辊')
    _s3_box(g,'HP4080_arm',(0,.17,1.72),(.035,.24,.032),'teal','HP4080牵伸加压臂','roller',.006)
    _s3_box(g,'F40_apron',(0,.155,1.653),(.085,.09,.018),'black','上皮圈架','roller',.004)
    _s3_pipe(g,'F40_roving_path',[(0,.25,1.72),(0,.10,1.67),(0,0,1.32),(.087,0,1.25),(.087,0,.84)],.003,'cloth','牵伸至锭翼压掌粗纱','material')
    _s3_box(g,'F40_roving_monitor',(0,.025,1.55),(.028,.025,.025),'orange','选配逐锭粗纱监测','frame',.003)
    # Full counterpart tube and individual internal exchange gripper.
    _s3_cyl(g,'F40_transport_empty_tube',(0,.52,1.02),.017,.406,'orange','z','内部运输空管','material')
    _s3_torus(g,'F40_doff_gripper',(0,.52,1.26),.026,.009,'black','z','内部自动落纱夹持器')
    _s3_box(g,'F40_doff_slide',(0,.32,1.27),(.06,.45,.05),'steel','向内退入换管滑轨')
    return _s3_unit_finish(g)

def spinning_family(stage,roving=False):
    if roving:
        r=_s3_root('roving','F40全自动粗纱机72锭','F 40','72锭/4节/10.485m；115mm交错锭距；集成自动落纱与端部转运；电子牵伸及逐锭监测选配',_S3_URL+'spinning-preparation/roving-frame-f-40f-20')
        r['spindleCount']=72;r['machineLengthMetres']=10.485;r['sectionCount']=4
        work=8.320;length=10.485
        # Actual 18-position / 2.080m sections; two staggered rows of nine.
        _s3_module(r,'F40_drive_end',(-work/2-.795,0,0),(1.590,1.859,1.82),'F40封闭传动车头',2)
        _s3_module(r,'F40_transfer_end',(work/2+.2875,0,0),(.575,1.859,1.82),'F40自动转运站',1)
        for sec in range(4):
            xx=-work/2+(sec+.5)*2.08
            _s3_module(r,'F40_section_shell',(xx,.28,0),(2.065,1.30,.66),'F40完整18锭预装节段',3)
            for z in (.70,1.45):_s3_box(r,'F40_front_beam',(xx,-.31,z),(2.08,.10,.10),'white','连续锭翼/卷绕承载梁')
            _s3_box(r,'F40_glazed_guard',(xx,-.49,1.05),(2.03,.018,.63),'glass','粗纱工作区防护窗','shell',.008)
            for dx in (-.98,0,.98):_s3_box(r,'F40_section_upright',(xx+dx,.32,1.18),(.06,.07,2.30),'white','粗纱架与机身支柱')
        first=None
        for sec in range(4):
            for row in range(2):
                for j in range(9):
                    i=sec*18+row*9+j;x=-work/2+sec*2.08+.065+j*.230+row*.115;y=-.28+row*.28
                    if first is None:first=_s3_roving_position(r);first.location=(x,y,0);first['positionIndex']=1
                    else:_s3_clone_tree(first,r,(x,y,0),'F40_roving_position',i+1)
                    # All 72 input cans are retained; five-row factory creel layout.
                    cx=-3.85+(i%15)*.535;cy=1.33+(i//15)*.535
                    _s3_can(r,(cx,cy,0),.508,1.10,'F40喂条筒 '+str(i+1))
                    _s3_pipe(r,'F40_input_sliver',[(cx,cy,1.16),(cx,cy,2.20),(x,.72,2.20),(x,y+.25,1.72)],.006,'cloth','粗纱第'+str(i+1)+'锭喂条','material')
        for sec in range(4):
            x=-work/2+sec*2.08+1.04
            for y in (.75,3.75):_s3_box(r,'F40_creel_post',(x,y,1.12),(.06,.06,2.24),'teal','完整导条架支柱')
            _s3_box(r,'F40_creel_crossbeam',(x,2.25,2.20),(.06,3.1,.07),'steel','导条架横梁')
        for y in (.75,3.75):_s3_box(r,'F40_creel_longbeam',(0,y,2.20),(8.4,.06,.07),'steel','导条架纵梁')
        for x in (-2.08,2.08):
            _s3_cyl(r,'F40_central_lift_screw',(x,.28,.94),.018,1.24,'steel','z','每两节中央升降丝杆')
            _s3_box(r,'F40_lift_nut',(x,.28,.72),(.13,.16,.14),'teal','钢领/筒管梁升降螺母座')
            _s3_drive(r,'F40_rail_lift_drive',(x,.28,.25),(.30,.23,.23))
        for i,(name,z) in enumerate((('flyer',.40),('bobbin',.80),('electronic_draft',1.25))):
            _s3_drive(r,'F40_'+name+'_drive',(-4.80,.15,z),(.38,.27,.27),'servo' if i==2 else 'induction')
        _s3_pipe(r,'F40_internal_transport',[(-4.0,.78,1.22),(4.45,.78,1.22)],.032,'steel','机内满纱/空管运输轨道')
        _s3_box(r,'F40_transfer_lift',(4.45,.55,1.38),(.18,.25,1.50),'teal','端部满纱提升转运站')
        _s3_pipe(r,'SERVOtrail_interface',[(4.45,.55,2.23),(4.45,1.2,2.23),(3.0,1.2,2.23)],.035,'steel','SERVOtrail粗纱运输接口')
        _s3_pipe(r,'F40_suction_main',[(-4.8,.65,.35),(-4.8,.65,2.32),(4,.65,2.32)],.085,'steel','吸棉清洁总管')
        _s3_hmi(r,(-4.75,-.96,1.52),'F40自动落纱与牵伸操作屏')
        return _s3_finish(r)
    r=_s3_root('spinning','G38 FE 288锭环锭细纱机','G 38 FE','288锭/6节；70mm锭距；14.260m；FLEXIdraft/ISM premium/SERVOdisc；单侧吸风；直联接口未作产能匹配',_S3_URL+'ring-spinning-machines/ring-spinning-machine-g-38')
    r['spindleCount']=288;r['sectionCount']=6;r['machineLengthMetres']=14.260;r['spindleGaugeMillimetres']=70
    working=10.080
    _s3_module(r,'G38_FE_headstock',(-6.140,0,0),(2.2,1.64,1.80),'G38 FE电子牵伸车头',3)
    _s3_module(r,'G38_suction_end',(6.030,0,0),(1.98,1.64,1.80),'G38吸风与直联输出车尾',3)
    for sec in range(6):
        x=-working/2+(sec+.5)*1.680
        _s3_module(r,'G38_section',(x,0,0),(1.665,.48,.47),'G38完整48锭节段',2)
        for side in (-1,1):
            _s3_box(r,'G38_ring_rail',(x,side*.330,.70),(1.680,.09,.025),'teal','连续钢领板')
            _s3_box(r,'G38_spindle_rail',(x,side*.330,.46),(1.680,.09,.08),'white','锭子支承梁')
            _s3_box(r,'G38_doffer_rail',(x,side*.505,.84),(1.680,.035,.035),'steel','自动集体落纱梁')
            _s3_box(r,'G38_SERVOdisc_track',(x,side*.465,.19),(1.680,.07,.04),'teal','SERVOdisc连续输送轨')
        for y in (-.525,-.315,-.105,.105,.315,.525):_s3_box(r,'G38_roving_creel_rail',(x,y,2.07),(1.680,.035,.04),'steel','粗纱吊锭支承纵轨')
        _s3_box(r,'G38_roving_creel_crossbar',(x,0,2.07),(.035,1.22,.04),'steel','多列粗纱架横梁')
        for xx in (x-.82,x+.82):_s3_box(r,'G38_creel_column',(xx,0,1.13),(.035,.04,1.88),'white','细纱中墙与粗纱架支柱')
    first=_s3_ring_position(r)
    for side in (-1,1):
        for i in range(144):
            x=-working/2+(i+.5)*.070;index=(0 if side<0 else 144)+i+1
            if side<0 and i==0:g=first;g.location=(x,side*.330,0);g['positionIndex']=index
            else:g=_s3_clone_tree(first,r,(x,side*.330,0),'G38_spinning_position',index)
            if side>0:g.rotation_euler[2]=math.pi
            # Full 152mm rovings require a staggered multi-row creel; putting
            # one package at every 70mm spindle pitch would make them overlap.
            cx=-working/2+((i//3)*3+1.5)*.070;cy=side*(.105+(i%3)*.210)
            _s3_cyl(r,'G38_roving_package',(cx,cy,1.74),.076,.406,'cloth','z','完整粗纱卷装；多列架布局待工程核对','material')
            _s3_cyl(r,'G38_roving_hanger',(cx,cy,2.005),.010,.125,'steel','z','粗纱吊锭','frame')
            _s3_pipe(r,'G38_roving_feed',[(cx,cy,1.537),(x,side*.16,1.30),(x,side*.16,1.19)],.002,'cloth','粗纱架至牵伸头喂入','material')
    # 4-spindle tape drive: all 72 groups are present, geometry unverified.
    for j in range(72):
        x=-working/2+(j+.5)*.14
        _s3_cyl(r,'four_spindle_drive_drum',(x,0,.50),.055,.06,'dark','z','四锭传动带轮；位置推定')
        _s3_pipe(r,'four_spindle_tape',[(x-.035,-.330,.50),(x+.035,-.330,.50),(x+.055,0,.50),(x+.035,.330,.50),(x-.035,.330,.50),(x-.055,0,.50),(x-.035,-.330,.50)],.004,'black','完整四锭传动带组；未验证机械细节','motor')
    for side in (-1,1):
        _s3_pipe(r,'G38_suction_channel',[(-5.05,side*.16,.99),(5.05,side*.16,.99),(5.95,0,.85)],.045,'steel','逐锭笛管汇流吸棉总管')
        for x in (-4.2,-2.52,-.84,.84,2.52,4.2):
            _s3_pipe(r,'doffer_scissor_link',[(x,side*.20,.48),(x+.20,side*.505,.84)],.013,'steel','集体落纱升降摆臂')
    _s3_drive(r,'G38_main_spindle_drive',(-6.30,0,.45),(.62,.40,.40),'induction')
    for y in (-.36,.36):_s3_drive(r,'FLEXIdraft_aircooled_motor',(-5.60,y,1.20),(.38,.24,.24))
    _s3_drive(r,'G38_ring_rail_servo',(-6.60,.35,.95),(.32,.22,.22))
    _s3_drive(r,'G38_suction_fan',(6.0,.12,.55),(.52,.39,.39),'induction')
    _s3_cyl(r,'G38_fan_scroll',(6.25,.12,.62),.32,.22,'teal','x','吸风机蜗壳','frame')
    _s3_pipe(r,'G38_exhaust',[(6.25,.12,.90),(6.25,.12,1.95),(6.25,.75,2.1)],.15,'steel','单端吸风排风接口')
    for y in (-.465,.465):_s3_box(r,'G38_link_track',(6.10,y,.19),(2.10,.07,.04),'teal','尾端SmartTray直联输出接口')
    _s3_hmi(r,(-6.75,-.84,1.55),'G38 FE当前电子牵伸操作屏')
    return _s3_finish(r)

def _s3_winder_unit(parent):
    g=empty('X6_winding_unit',(0,0,0),parent,'X6独立卷绕单元','roller')
    _s3_box(g,'X6_unit_column',(0,.08,1.18),(.27,.25,1.72),'white','络筒单元立柱外罩','shell',.025)
    _s3_box(g,'X6_unit_panel',(0,-.065,1.42),(.21,.025,.63),'teal','单锭控制面板','shell',.012)
    for z,ma in ((1.66,'green'),(1.57,'orange'),(1.48,'red')):_s3_cyl(g,'X6_status_lamp',(0,-.085,z),.012,.008,ma,'y','卷绕单元状态灯','shell',16)
    _s3_roll(g,'X6交叉卷绕筒子',(0,-.10,1.98),.145,.23,'cloth')
    _s3_roll(g,'X6槽筒',(0,-.15,1.78),.06,.23,'steel')
    for x in (-.135,.135):_s3_pipe(g,'X6_package_cradle',[(x,.05,1.78),(x,-.10,1.98)],.015,'teal','筒子支承摆臂')
    _s3_box(g,'X6_clearer',(0,-.25,1.25),(.085,.05,.08),'orange','电子清纱器','roller',.006)
    _s3_box(g,'X6_splicer',(0,-.26,1.06),(.10,.10,.13),'steel','气动捻接器外部组件','roller',.008)
    _s3_cyl(g,'X6_tension_disc',(0,-.28,.89),.035,.018,'steel','y','纱线张力盘')
    _s3_pipe(g,'X6_lower_suction',[(0,-.12,.50),(0,-.32,.70),(.075,-.30,.98)],.017,'dark','下纱找头吸嘴')
    _s3_pipe(g,'X6_upper_suction',[(.08,.07,1.25),(.12,-.25,1.50),(.08,-.25,1.78)],.019,'dark','筒子上纱吸嘴')
    _s3_cyl(g,'X6_active_cop',(0,-.21,.47),.026,.23,'cloth','z','SmartTray工作管纱','material')
    _s3_cyl(g,'X6_SmartTray',(0,-.21,.325),.053,.022,'teal','z','RFID SmartTray管纱托盘','roller',24)
    _s3_box(g,'X6_RFID_reader',(.09,-.21,.33),(.04,.04,.035),'dark','托盘RFID识读位置','frame',.003)
    _s3_pipe(g,'X6_yarn_path',[(0,-.21,.60),(0,-.28,.89),(0,-.26,1.06),(0,-.25,1.25),(0,-.20,1.76)],.002,'cloth','管纱—张力—捻接—清纱—卷绕纱路','material')
    _s3_box(g,'X6_unit_motor',(.06,.20,1.78),(.13,.15,.12),'dark','单锭卷绕驱动外壳','motor',.008)
    return _s3_unit_finish(g)

def machine_winding():
    r=_s3_root('winding','Autoconer X6 Type V','Autoconer X6 Type V','96卷绕单元/320mm节距（官网公布上限配置）；Cop Exchanger/RFID SmartTray/自动落筒；未声称与288锭G38产能匹配',_S3_URL+'winding-machines/automatic-package-winding-machine-autoconer')
    r['windingUnitCount']=96;r['unitGaugeMillimetres']=320;r['selectedPublicConfiguration']='published_maximum';working=96*.320
    for sec in range(16):
        x=-working/2+(sec+.5)*1.92
        _s3_box(r,'X6_section_base',(x,0,.18),(1.90,.82,.21),'teal','6单元节段底梁')
        _s3_box(r,'X6_rear_manifold',(x,.28,1.10),(1.92,.12,1.55),'white','单元吸风/电控后梁','shell')
        _s3_box(r,'X6_peg_conveyor',(x,-.23,.30),(1.92,.15,.08),'steel','工作SmartTray输送线')
        _s3_box(r,'X6_return_conveyor',(x,.55,.30),(1.92,.15,.08),'steel','空管回送输送线')
        _s3_box(r,'X6_package_belt',(x,.34,2.25),(1.92,.32,.09),'dark','成品筒子输送带')
        for dx in (-.90,.90):_s3_cyl(r,'X6_level_foot',(x+dx,0,.055),.07,.11,'black','z','机座调平脚','frame',24)
        _s3_box(r,'X6_rail_support',(x,.44,1.49),(.055,.055,2.65),'teal','落筒与空筒输送轨支柱')
        _s3_box(r,'X6_Autodofer_rail',(x,.44,2.80),(1.92,.08,.09),'steel','自动落筒车运行轨道')
    first=_s3_winder_unit(r)
    for i in range(96):
        x=-working/2+(i+.5)*.320
        if i==0:g=first;g.location=(x,0,0);g['positionIndex']=1
        else:g=_s3_clone_tree(first,r,(x,0,0),'X6_winding_unit',i+1)
        _s3_cyl(r,'X6_reserve_tube',(x,.44,2.55),.024,.25,'orange','y','逐单元空筒上部储备','material',24)
        _s3_cyl(r,'X6_return_SmartTray',(x,.55,.36),.053,.022,'teal','z','回送SmartTray','roller',24)
    _s3_module(r,'X6_service_head',(-working/2-.65,0,0),(1.30,1.20,2.12),'X6控制及负压服务车头',2)
    _s3_module(r,'X6_TypeV_interface',(working/2+.65,0,0),(1.30,1.20,2.12),'Type V供料与Cop Exchanger',2)
    _s3_hmi(r,(-working/2-.75,-.64,1.72),'X6当前物料流控制屏')
    _s3_pipe(r,'X6_vacuum_main',[(-working/2-.65,.28,.65),(working/2,.28,.65)],.10,'steel','逐单元捻接/找头负压总管')
    _s3_drive(r,'X6_suction_drive',(-working/2-.65,.18,.50),(.50,.35,.35),'induction')
    _s3_pipe(r,'X6_pneumatic_header',[(-working/2,.12,.82),(working/2,.12,.82)],.014,'steel','捻接压缩空气总管')
    # Full loop at Type V interface; exchange station is separate from winding units.
    for y in (-.23,.55):_s3_box(r,'TypeV_link_rail',(working/2+1.48,y,.30),(2.80,.15,.08),'steel','Type V外部直联供回料接口')
    _s3_box(r,'Cop_Exchanger_reject_gate',(working/2+.55,-.21,.56),(.27,.20,.35),'orange','Cop Exchanger问题管纱自动更换/剔除站','roller')
    _s3_box(r,'Cop_Exchanger_reject_bin',(working/2+.65,-.76,.35),(.50,.45,.65),'dark','问题管纱收集箱')
    doff=empty('X6_Autodofer',(-3,.44,2.70),r,'沿轨自动落筒车','roller',explode=[0,.6,.2])
    _s3_box(doff,'Autodofer_body',(0,0,0),(.68,.54,.55),'white','自动落筒车体','shell',.03)
    for x in (-.22,.22):_s3_pipe(doff,'Autodofer_gripper',[(x,0,-.18),(x,-.52,-.18),(x,-.52,-.70)],.025,'steel','落筒机械夹持与摆臂','roller')
    _s3_box(doff,'tube_feeder_magazine',(.0,.15,.40),(.55,.24,.35),'teal','空筒供应机构','shell')
    return _s3_finish(r)
