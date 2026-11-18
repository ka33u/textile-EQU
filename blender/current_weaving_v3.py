"""Current public-reference weaving equipment, v3.
Exec after industrial_v2.py (and motor_precision.py). Does not export or mutate other stages.
Units: metres. Selected installation counts are not a manufacturer order/BOM.
All four builders start anew. Full selected repetitive populations are created.
"""
from mathutils import Vector

_W3_CACHE = {}
_W3_CFG = {
 'warping': ('KARL MAYER','WARPDIRECT 2.0','2.2 m工作幅；1.0 m经轴；480位筒子架（2侧×6层×40列）；电动压辊'),
 'sizing': ('KARL MAYER','PROSIZE HSB','2.2 m；6根经轴×480根；1个HSB湿区；12烘筒；2880根经纱；1织轴'),
 'drawing_in': ('Stäubli','SAFIR PRO S67','固定机头；2辆2.2 m完整移动车；单经片；2综框平纹；AWC 2.0'),
 'weaving': ('Picanol','Ultimax 4-R 220','2.2 m筘幅平台；2.1 m全棉平纹；2880经纱；2综框；4路供纬'),
}
for _key, _color, _metal, _rough in (
 ('w3white',(.81,.84,.83),.12,.33),('w3graphite',(.045,.060,.071),.28,.34),
 ('w3cyan',(.015,.40,.38),.25,.32),('w3alloy',(.55,.61,.64),.78,.26),
 ('w3yarn',(.79,.75,.65),0,.79),('w3safety',(.95,.65,.035),.05,.4)):
 if _key not in M: M[_key]=mat(_key,_color,_metal,_rough)
if 'w3guardglass' not in M:
 M['w3guardglass']=mat('Clear machine guard',(.34,.48,.52),.05,.14)
 _bs=M['w3guardglass'].node_tree.nodes.get('Principled BSDF')
 _bs.inputs['Alpha'].default_value=.10
 if 'Transmission Weight' in _bs.inputs:_bs.inputs['Transmission Weight'].default_value=.45
 try:M['w3guardglass'].surface_render_method='DITHERED'
 except Exception:pass

def w3_mesh(name,verts,faces,material,parent,label,group='frame',loc=(0,0,0),smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();me.materials.append(M[material])
 for f in me.polygons:f.use_smooth=smooth
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.parent=parent;o.location=loc;meta(o,label,group)
 return o

def w3_instance(me,name,loc,parent,label,group='frame'):
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.parent=parent;o.location=loc;meta(o,label,group);return o

def w3_box(parent,name,loc,size,material='w3white',label=None,group='frame',bevel=.015):
 key=('box',tuple(size),material,bevel);me=_W3_CACHE.get(key)
 if me is None or me.name not in bpy.data.meshes:
  o=box(name,loc,size,material,parent,label or name,group,bevel);_W3_CACHE[key]=o.data;return o
 return w3_instance(me,name,loc,parent,label or name,group)

def w3_cyl(parent,name,loc,r,length,material='w3alloy',axis='x',label=None,group='roller',n=32):
 key=('cylinder',r,length,material,axis,n);me=_W3_CACHE.get(key)
 if me is None or me.name not in bpy.data.meshes:
  vs=[]
  for h in (-length/2,length/2):
   for i in range(n):
    a=2*math.pi*i/n;c=r*math.cos(a);s=r*math.sin(a)
    vs.append((h,c,s) if axis=='x' else (c,h,s) if axis=='y' else (c,s,h))
  fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  o=w3_mesh(name,vs,fs,material,parent,label or name,group,loc)
  for poly in o.data.polygons:poly.use_smooth=poly.index>=2
  _W3_CACHE[key]=o.data;return o
 return w3_instance(me,name,loc,parent,label or name,group)

def w3_path(parent,name,points,r=.003,material='w3yarn',label='连续经纱',group='material',sides=4):
 """Small polygonal tube; smooth sides and shared mesh across repeated yarns."""
 pts=[Vector(p) for p in points];vs=[];fs=[]
 for i,p in enumerate(pts):
  t=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();a=t.cross(Vector((1,0,0)))
  if a.length<.01:a=t.cross(Vector((0,1,0)))
  a.normalize();b=t.cross(a).normalized()
  vs += [tuple(p+r*(a*math.cos(j*2*math.pi/sides)+b*math.sin(j*2*math.pi/sides))) for j in range(sides)]
 for i in range(len(pts)-1):
  for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
 return w3_mesh(name,vs,fs,material,parent,label,group,smooth=True)

def w3_parallel(parent,points,count=2880,width=2.1,label='经纱',r=.00028):
 proto=w3_path(parent,'warp_end_0001',[(0,y,z) for y,z in points],r,label=label+' 1/'+str(count))
 proto.location.x=-width/2+.5*width/count
 for i in range(1,count):w3_instance(proto.data,'warp_end_%04d'%(i+1),(-width/2+(i+.5)*width/count,0,0),parent,label+' '+str(i+1)+'/'+str(count),'material')
 parent['modeledWarpEnds']=count
 return proto

def w3_root(id,w,d):
 maker,model,conf=_W3_CFG[id];r=base(id,model+' 配置研究模型',w,d)
 r['modelVersion']='3.0';r['referenceManufacturer']=maker;r['referenceModel']=model;r['referenceConfiguration']=conf
 r['fidelityStatus']='partial_public_reference';r['structuralCompleteness']=False;r['units']='metres'
 r['configurationEvidence']='厂家公开结构＋明确标注的所选安装配置；非订单CAD/BOM'
 return r

def w3_shell(parent,name,loc,size,color='w3white',open_front=False):
 x,y,z=loc;w,d,h=size;g=empty(name,parent=parent,label='可拆模块化机罩',group='shell',explode=[.5,.2,0])
 for xx in (-w/2,w/2):w3_box(g,name+'_side',(x+xx,y,z),(.035,d,h),color,'机罩侧壁','shell',.012)
 w3_box(g,name+'_roof',(x,y,z+h/2),(w,d,.035),color,'机罩顶板','shell')
 w3_box(g,name+'_rear',(x,y+d/2,z),(w,.035,h),color,'后检修板','shell')
 if not open_front:w3_box(g,name+'_front',(x,y-d/2,z),(w,.035,h),color,'前检修门','shell')
 return g

def w3_panel(parent,loc,w,h,material='w3white',label='检修门'):
 x,y,z=loc;w3_box(parent,'door_seal',(x,y,z),(w+.012,.025,h+.012),'w3graphite','门板密封缝','shell',.006)
 w3_box(parent,'service_door',(x,y-.018,z),(w,.025,h),material,label,'shell',.012)
 w3_box(parent,'flush_handle',(x+w*.37,y-.04,z),(.022,.03,.13),'w3graphite','检修门嵌入把手','shell',.006)

def w3_bearing(parent,x,y,z,r=.085):
 w3_box(parent,'bearing_foot',(x,y,z-r*.7),(.14,r*2.8,r*.65),'w3graphite','轴承座安装脚')
 w3_cyl(parent,'bearing_cast_body',(x,y,z),r,.13,'w3graphite',label='辊端轴承壳体')
 w3_cyl(parent,'bearing_end_cap',(x+(1 if x>0 else -1)*.075,y,z),r*.82,.025,label='轴承端盖')
 for yy in (-r,r):w3_cyl(parent,'bearing_bolt',(x,y+yy,z-r*.15),.009,.07,axis='z',label='轴承座紧固件',group='frame',n=6)

def w3_roll(parent,label,y,z,rad=.08,width=2.2,x=0,material='w3alloy',bearings=True):
 g=empty('rotate_'+label,(x,y,z),parent,label,'roller',spin='x')
 w3_cyl(g,'working_roll',(0,0,0),rad,width,material,label=label)
 w3_cyl(g,'roll_journal',(0,0,0),min(rad*.3,.07),width+.28,label='辊轴轴颈')
 if bearings:
  for xx in (x-width/2-.12,x+width/2+.12):w3_bearing(parent,xx,y,z,min(.12,max(.065,rad*.3)))
 return g

def w3_beam(parent,y,z=.78,width=2.2,diam=1.0,package=.43,label='经轴',x=0,standbase=.18):
 g=w3_roll(parent,label,y,z,package,width,x,'w3yarn')
 for side in (-1,1):
  w3_cyl(parent,'beam_flange',(x+side*(width/2+.04),y,z),diam/2,.04,'w3alloy',label=label+'盘片',n=64)
  w3_cyl(parent,'beam_hub',(x+side*(width/2+.09),y,z),.13,.12,'w3graphite',label=label+'锥面夹持轮毂')
  w3_box(parent,'beam_stand',(x+side*(width/2+.15),y,(z+standbase)/2),(.18,.45,z-standbase),'w3graphite','经轴托持机架')
 return g

def w3_drive(parent,x,y,z,scale=.32,label='辊组驱动',direction=-1):
 """Visible supported motor with shaft pointing at load; appearance is not an OEM motor claim."""
 m=motor(parent,(x,y,z),scale);m['description']=label+'；电机精确型号和内部未获厂家BOM，形体为布局推定。'
 if direction<0:m.rotation_euler[2]=math.pi
 top=z-.75*scale
 w3_box(parent,'drive_bed',(x,y,(top+.18)/2),(scale*1.35,scale*1.25,max(.02,top-.18)),'w3graphite','驱动承重安装台')
 return m

def w3_hmi(parent,x,y,z=1.35,integrated=False):
 g=empty('integrated_operator_hmi',(x,y,z),parent,'集成操作触屏','shell')
 o=w3_box(g,'hmi_case',(0,0,0),(.35,.20,.25),'w3graphite','倾斜操作屏','shell',.035);o.rotation_euler.x=-.25
 w3_box(g,'hmi_screen',(0,-.108,.015),(.285,.008,.17),'glass','触摸显示屏','shell',.008)
 for xx in (-.10,.1):w3_cyl(g,'control_button',(xx,-.12,-.095),.012,.012,'red' if xx<0 else 'green',axis='y',label='急停/运行按钮',group='shell',n=16)
 if not integrated:w3_box(parent,'hmi_stand',(x,y,z/2),(.07,.07,z),'w3graphite','操作台支柱')
 return g

def w3_guard(parent,y0,y1,z0,z1,width=2.5):
 g=empty('inclined_safety_guard',parent=parent,label='倾斜透明联锁防护门',group='shell',explode=[0,.45,.3])
 for x in (-width/2,0,width/2):w3_path(g,'guard_stile',[(x,y0,z0),(x,y1,z1)],.022,'w3alloy','防护门框','shell',6)
 for y,z in ((y0,z0),(y1,z1)):w3_box(g,'guard_crossbar',(0,y,z),(width,.04,.04),'w3alloy','防护门横框','shell')
 for side in (-1,1):
  xa,xb=(0,width/2) if side>0 else (-width/2,0)
  w3_mesh('clear_guard_panel',[(xa,y0,z0),(xb,y0,z0),(xb,y1,z1),(xa,y1,z1)],[(0,1,2,3)],'w3guardglass',g,'透明防护门板','shell')
 w3_box(g,'guard_interlock',(width/2,y0,z0+.05),(.045,.06,.10),'w3safety','安全门联锁传感器','shell')
 return g

def w3_arc(c,r,a,b,n=12):return [(c[0]+r*math.cos(a+(b-a)*j/n),c[1]+r*math.sin(a+(b-a)*j/n)) for j in range(n+1)]

def w3_tangent_point(p,c,r,sign=1):
 a=math.atan2(p[1]-c[1],p[0]-c[0])+sign*math.acos(r/math.hypot(p[0]-c[0],p[1]-c[1]));return (c[0]+r*math.cos(a),c[1]+r*math.sin(a))

def w3_signal(parent,x,y,z):
 w3_cyl(parent,'status_light_stem',(x,y,z),.013,.4,'w3graphite',axis='z',label='状态灯支柱',group='frame',n=12)
 for j,col in enumerate(('red','w3safety','green')):w3_cyl(parent,'status_lamp',(x,y,z+.22+j*.045),.026,.04,col,axis='z',label='设备状态灯',group='shell',n=16)

def machine_warping():
 r=w3_root('warping',6.0,22.0);r['modeledCreelPositions']=480;r['selectedWorkingWidthM']=2.2
 # Complete selected 2 x 6 x 40 creel; every position includes holder, tensioner, stop sensor and guide eye.
 creel=empty('complete_480_position_creel',parent=r,label='480位完整筒子架：2侧×6层×40列',group='frame')
 for side in (-1,1):
  for row in range(6):w3_box(creel,'creel_level_rail',(side*2.22,2.2,.55+row*.28),(.06,14.6,.045),'w3alloy','筒子架分层横梁')
  for col in range(40):
   yy=-4.6+col*.35;w3_box(creel,'creel_column',(side*2.22,yy,1.2),(.055,.055,2.04),'w3graphite','筒子架立柱')
   if col%5==0:w3_box(creel,'creel_floor_foot',(side*2.22,yy,.21),(.6,.3,.06),'w3graphite','筒子架地脚')
   for row in range(6):
    zz=.55+row*.28;idx=(0 if side<0 else 240)+col*6+row
    st=empty('creel_position_%03d'%(idx+1),(side*1.99,yy,zz),creel,'筒子架锭位 '+str(idx+1),'material')
    w3_cyl(st,'cotton_package',(0,0,0),.116,.23,'w3yarn',label='棉纱筒子',group='material',n=24)
    w3_cyl(st,'package_holder',(side*.07,0,0),.018,.40,'w3alloy',label='筒子托杆',group='frame',n=12)
    w3_box(st,'tension_module',(-side*.30,0,0),(.08,.07,.10),'w3graphite','逐锭张力器（具体型号待核实）')
    w3_cyl(st,'tension_disc',(-side*.35,0,0),.033,.018,'w3alloy',label='张力盘',group='roller',n=16)
    w3_box(st,'end_break_detector',(-side*.43,0,.04),(.045,.035,.055),'w3cyan','逐锭断头检测器')
    # Routes run along distinct row heights; all 480 feeds are included, not a sample set.
    xout=-1.05+(idx+.5)*2.1/480
    w3_path(r,'creel_yarn_%03d'%(idx+1),[(side*1.86,yy,zz),(side*1.64,yy,zz),(side*(1.48+col*.0015),yy,zz+.04),(side*(1.48+col*.0015),-5.25,zz+.04),(xout,-6.15,1.55),(xout,-7.963,1.309)],.00028,label='筒子—张力—断头检测—集纱—整经轴 '+str(idx+1))
  for yy in (-4.7,9.2):w3_box(creel,'creel_cross_brace',(side*2.22,yy,2.1),(.10,.12,.10),'w3cyan','筒子架联接节点')
 # Low modern beam head: closed asymmetric side cabinets and two-part inclined clear guard.
 heady=-7.9;w3_beam(r,heady,.85,2.2,1.0,.46,'整经经轴')
 for side in (-1,1):
  x=side*1.47;sh=w3_shell(r,'warper_side_pod',(x,-7.55,.91),(.53,1.65,1.42))
  w3_panel(sh,(x,-8.39,.85),.47,1.23)
  w3_box(sh,'cyan_edge_strip',(x-side*.25,-8.42,.88),(.025,.03,1.30),'w3cyan','主机标识边条','shell',.004)
  w3_box(sh,'black_bumper',(x+side*.27,-8.4,.85),(.045,.08,1.30),'w3graphite','侧箱防护包边','shell')
  # Electric press-roll screw actuator; hydraulics not used for contact pressure.
  w3_box(r,'pressure_slide_rail',(side*1.20,-7.1,1.00),(.09,1.04,.09),'w3alloy','压辊直线导轨')
  w3_cyl(r,'pressure_electric_screw',(side*1.20,-7.06,1.11),.018,.88,axis='y',label='电动压辊丝杆',group='motor',n=16)
  w3_box(r,'pressure_servo',(side*1.20,-6.58,1.11),(.14,.20,.16),'w3graphite','电动压辊执行轴（内部布置待图纸）','motor')
  w3_box(r,'pressure_carriage',(side*1.20,-7.318,1.11),(.15,.18,.20),'w3cyan','压辊进退滑座')
 w3_roll(r,'电动压辊',-7.318,1.030,.15,2.2)
 w3_box(r,'smart_reed_beam',(0,-6.15,1.45),(2.4,.13,.12),'w3graphite','Smart-Riet自动伸缩筘支承')
 for i in range(481):w3_box(r,'smart_reed_dent',(-1.05+i*2.1/480,-6.15,1.55),(.0015,.018,.17),'w3alloy','伸缩筘筘齿','roller',0)
 for side in (-1,1):w3_box(r,'reed_adjustment_module',(side*1.24,-6.15,1.48),(.16,.24,.17),'w3cyan','伸缩筘调幅执行模块')
 w3_guard(r,-8.45,-6.45,1.0,1.95,2.55)
 w3_box(r,'nip_safety_bar',(0,-8.35,1.38),(2.5,.055,.055),'w3safety','整经辊区安全横杆')
 w3_drive(r,1.65,heady,.85,.32,'整经轴主驱动');w3_cyl(r,'beam_coupling',(1.30,heady,.85),.055,.48,label='整经轴联轴器',group='motor')
 w3_hmi(r,1.48,-7.95,1.63,True);w3_signal(r,1.4,-6.75,1.85)
 return r

# A public-range selected HSB line; no claim this is a photographed customer order.
def machine_sizing():
 r=w3_root('sizing',5.0,25.0);r['selectedDryingCylinders']=12;r['selectedBackBeams']=6;r['selectedSizeBoxes']=1;r['selectedWorkingWidthM']=2.2
 # Six complete back beams, all 480 ends each carried to the wet zone.
 for j in range(6):
  yy=10.4-j*1.15;w3_beam(r,yy,.76,2.2,1.0,.42,'退绕经轴 '+str(j+1))
  zcollect=1.7+j*.035
  guidec=(yy-.32,zcollect-.0555)
  w3_roll(r,'轴架抬纱导辊 '+str(j+1),guidec[0],guidec[1],.055,2.2)
  p,ge,ga=w3_common_tangent((yy,.76),.425,guidec,.0555,-1)
  g=empty('beam_sheet_'+str(j+1),parent=r,label='第'+str(j+1)+'根经轴的480根经纱',group='material')
  g.location.x=(j-2.5)*2.1/2880
  w3_parallel(g,[p]+w3_arc(guidec,.0555,ga,math.pi/2,12)+[(3.85,zcollect),(3.35,1.64)],480,2.1,'退绕经纱',.00028)
  for side in (-1,1):w3_box(r,'beam_brake',(side*1.30,yy,.76),(.20,.20,.22),'w3graphite','经轴张力制动模块','motor')
 # HSB short wet application zone, bearings outboard, access doors and recirculation system.
 wet=empty('hsb_size_box',parent=r,label='HSB单浆槽浸轧湿区',group='frame')
 for xx in (-1.23,1.23):w3_box(wet,'hsb_side_structure',(xx,2.35,1.05),(.16,2.55,1.62),'w3graphite','浆槽侧承力机架')
 for yy in (1.3,3.4):w3_box(wet,'hsb_tank_end',(0,yy,.69),(2.5,.06,.79),'w3alloy','浆槽端壁','shell')
 w3_box(wet,'hsb_tank_floor',(0,2.35,.30),(2.5,2.1,.06),'w3alloy','浆槽底板','shell')
 for side in (-1,1):w3_panel(wet,(side*.65,1.25,.8),1.2,.9,'w3white','HSB湿区检修门')
 for yy,zz,rr,lab in ((2.85,1.23,.18,'浸浆导辊'),(1.90,1.37,.23,'轧浆下辊'),(1.90,1.8308,.23,'轧浆上辊')):w3_roll(wet,lab,yy,zz,rr,2.2,material='rubber' if '上' in lab else 'w3alloy')
 for side in (-1,1):
  w3_box(wet,'hsb_pressure_column',(side*1.26,1.9,1.5),(.20,.3,1.85),'w3white','轧浆压力机架')
  hydraulic_cylinder(wet,(side*1.26,1.9,2.30),.30,.08,.20)
 w3_box(r,'size_recirculation_tank',(1.75,2.4,.70),(.65,1.1,1.04),'w3alloy','浆液循环过滤箱')
 for yy in (2.05,2.75):w3_path(r,'size_liquor_loop',[(1.74,yy,.4),(2.1,yy,.4),(2.1,yy,1.15),(1.24,yy,1.15)],.025,'w3alloy','浆液供回流与过滤管路','frame',8)
 # Twelve drying cylinders. Matched serpentine yarn path has nonintersecting internal tangents.
 centers=[(.45-i*.77,1.52) for i in range(12)];rad=.28;clear=.282
 for i,(yy,zz) in enumerate(centers):
  w3_roll(r,'SoftDry烘筒 '+str(i+1),yy,zz,rad,2.2)
  for side in (-1,1):
   w3_box(r,'dryer_bearing_support',(side*1.28,yy,.90),(.18,.22,1.44),'w3graphite','烘筒轴承支承立柱')
  w3_cyl(r,'steam_rotary_union',(1.36,yy,zz),.055,.20,label='烘筒蒸汽旋转接头',group='frame')
  w3_path(r,'steam_branch',[(1.47,yy,zz),(1.76,yy,zz),(1.76,yy,.72)],.021,'w3alloy','蒸汽与冷凝水支路','frame',6)
  # Individual drive, each of the 12 motor/roll axes is included and supported.
  w3_drive(r,-1.55,yy,zz,.22,'SoftDry烘筒独立驱动',1)
  w3_cyl(r,'dryer_drive_coupling',(-1.25,yy,zz),.045,.28,label='烘筒驱动联轴器',group='motor')
 for side in (-1,1):
  w3_box(r,'dryer_longitudinal_beam',(side*1.25,-3.8,.35),(.22,9.2,.28),'w3graphite','烘燥区纵向承梁')
 # Exact 2880 parallel yarns for selected 6 x 480 configuration, shared one filament mesh.
 imm=(2.85,1.23); nip=(1.90,1.37)
 first=w3_tangent_point((3.35,1.64),imm,.183,-1)
 # Opposite-side tangent from below the dip roll to above the squeeze roll.
 ang=math.atan2(nip[1]-imm[1],nip[0]-imm[0])+math.acos((.183+.2304)/math.dist(imm,nip))
 exitang=ang%(2*math.pi)-2*math.pi; entryang=(ang+math.pi)%(2*math.pi)
 p=[(3.35,1.64)]+w3_arc(imm,.183,math.atan2(first[1]-imm[1],first[0]-imm[0]),exitang,14)+w3_arc(nip,.2304,entryang,math.pi/2,10)+[(1.5,1.6004)]
 a=math.acos(2*clear/.77)
 # First wrap starts at its upper right tangent; alternating circles keep a visible contact arc.
 for i,c in enumerate(centers):
  if i==0:
   ct=w3_tangent_point(p[-1],c,clear,1);aa,bb=math.atan2(ct[1]-c[1],ct[0]-c[0]),math.pi-a
  elif i%2:aa,bb=2*math.pi-a,math.pi+a
  else:aa,bb=a,math.pi-a
  if i==11:
   endpoint=w3_tangent_point((-8.65,1.80),c,clear,1)
   bb=math.atan2(endpoint[1]-c[1],endpoint[0]-c[0])%(2*math.pi)
  p+=w3_arc(c,clear,aa,bb,10)
 # Exit and dry splitting rods before beam head.
 p += [(-8.65,1.80),(-9.05,1.80),(-9.55,1.80),(-10.2,1.80)]
 p += [w3_tangent_point(p[-1],(-11.0,.85),.463,1)]
 w3_parallel(r,p,2880,2.1,'完整浆纱经纱片',.00028)
 for yy in (-9.05,-9.55):w3_roll(r,'干分绞/测湿导辊',yy,1.72,.075,2.2)
 w3_box(r,'moisture_sensor',(1.27,-9.05,1.70),(.12,.18,.14),'w3cyan','残余湿度检测器')
 # Liftable segmented exhaust hood with thin walls, open inlet/outlet slots.
 for j in range(3):
  yy=-.75-j*3.05;hood=empty('dryer_hood_'+str(j),parent=r,label='分段排湿罩',group='shell',explode=[0,.8,0])
  w3_box(hood,'hood_roof',(0,yy,2.2),(2.95,2.9,.04),'w3alloy','排湿罩顶板','shell')
  for side in (-1,1):w3_box(hood,'hood_side',(side*1.48,yy,1.75),(.04,2.9,.85),'w3white','烘房侧罩','shell')
  w3_path(r,'dryer_exhaust',[(0,yy,2.22),(0,yy,2.6),(.5,yy,2.87),(1.6,yy,2.87)],.13,'w3alloy','烘燥排湿支管','frame',12)
 # Complete weaving-beam head and safety mesh, instead of a naked roll.
 w3_beam(r,-11.0,.85,2.2,1.016,.46,'浆纱织轴')
 for side in (-1,1):
  sh=w3_shell(r,'sizing_beaming_pod',(side*1.48,-10.8,.95),(.54,1.6,1.54));w3_panel(sh,(side*1.48,-11.62,.9),.46,1.38)
 w3_drive(r,1.6,-11,.85,.30,'织轴卷绕驱动');w3_cyl(r,'weaver_beam_coupling',(1.3,-11,.85),.05,.42,label='织轴同轴联接',group='motor')
 gate=empty('beaming_safety_mesh',parent=r,label='卷绕机头联锁网门',group='shell',explode=[0,.3,.4])
 for x in (-1.23,0,1.23):w3_box(gate,'gate_post',(x,-11.7,.92),(.035,.04,1.45),'w3graphite','卷绕防护门框','shell')
 for z in (.23,1.6):w3_box(gate,'gate_rail',(0,-11.7,z),(2.5,.04,.04),'w3safety','门框安全边条','shell')
 for i in range(64):w3_box(gate,'mesh_wire',(-1.23+i*2.46/63,-11.7,.92),(.003,.003,1.36),'w3graphite','卷绕门防护网','shell',0)
 for j in range(35):w3_box(gate,'mesh_crosswire',(0,-11.7,.25+j*.039),(2.46,.003,.003),'w3graphite','卷绕门防护网','shell',0)
 w3_hmi(r,1.48,-10.45,1.85,True);w3_signal(r,1.4,-10.1,1.85)
 return r

# Batched full-count metal populations: each opening is physically hollow.
def w3_batch_boxes(parent,name,parts,material='w3alloy',label='重复装配',group='roller'):
 vs=[];fs=[]
 for (x,y,z),(w,d,h) in parts:
  k=len(vs);vs += [(x+sx*w/2,y+sy*d/2,z+sz*h/2) for sx,sy,sz in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
  fs += [tuple(k+i for i in f) for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))]
 return w3_mesh(name,vs,fs,material,parent,label,group)

def w3_heald_frame(parent,y,eye_z,phase=0,count=1440,width=2.1,height=.48,label='综框'):
 g=empty('heald_frame_'+str(phase),(0,y,0),parent,label,'roller')
 for zz in (eye_z-height/2,eye_z+height/2):w3_box(g,'heald_carrier',(0,0,zz),(width+.18,.045,.028),'w3alloy','综框横梁')
 for side in (-1,1):w3_box(g,'heald_side',(side*(width/2+.08),0,eye_z),(.035,.05,height),'w3graphite','综框侧档')
 parts=[]
 for j in range(count):
  xx=-width/2+(j*2+phase+.5)*width/(count*2)
  # Eye opening .00070 x .004 m, intentionally open through the yarn direction.
  for zz in (eye_z-.122,eye_z+.122):parts.append(((xx,0,zz),(.00030,.00025,.230)))
  for dx in (-.000425,.000425):parts.append(((xx+dx,0,eye_z),(.00015,.00035,.0043)))
  for dz in (-.00215,.00215):parts.append(((xx,0,eye_z+dz),(.001,.00035,.0003)))
 w3_batch_boxes(g,'all_%d_healds'%count,parts,'w3alloy',str(count)+'根综丝与真实开孔综眼')
 g['modeledHealds']=count
 return g

def w3_dropwire_bank(parent,y,z,count=2880,width=2.1):
 parts=[]
 for j in range(count):
  xx=-width/2+(j+.5)*width/count
  for dx in (-.00032,.00032):parts.append(((xx+dx,y,z),(.00010,.00035,.006)))
  for dz in (-.003,.003):parts.append(((xx,y,z+dz),(.00074,.00035,.00016)))
  parts.append(((xx,y,z-.060),(.00060,.00030,.11)))
 g=w3_batch_boxes(parent,'full_end_stop_motion',parts,'w3alloy',str(count)+'片停经片（逐根对应）')
 g['modeledDropWires']=count
 for xx in (-width/2-.08,width/2+.08):w3_box(parent,'stop_motion_support',(xx,y,z-.12),(.045,.11,.34),'w3graphite','停经片支架')
 w3_box(parent,'stop_motion_contact_bar',(0,y,z-.105),(width+.2,.025,.014),'w3graphite','停经片电极条')
 return g

def w3_reed(parent,y,z,width=2.1,dents=1441,height=.22,label='钢筘'):
 parts=[]
 for i in range(dents):parts.append(((-width/2+i*width/(dents-1),y,z),(.00018,.014,height)))
 o=w3_batch_boxes(parent,'all_reed_dents',parts,'w3alloy',label+'：'+str(dents)+'片筘齿')
 o['modeledReedDents']=dents
 for zz in (z-height/2-.015,z+height/2+.015):w3_box(parent,'reed_baulks',(0,y,zz),(width+.12,.042,.03),'w3graphite','钢筘上下筘梁')
 return o

def w3_wheel(parent,x,y,z=.28):
 w3_cyl(parent,'truck_wheel',(x,y,z),.085,.05,'w3graphite',label='移动车承重轮',n=24)
 w3_cyl(parent,'truck_wheel_hub',(x,y,z),.035,.064,'w3alloy',label='移动车轮毂',n=16)
 w3_box(parent,'wheel_fork',(x,y,z+.07),(.08,.14,.16),'w3alloy','轮叉与固定连接')

def machine_drawing_in():
 if 'w3violet' not in M:M['w3violet']=mat('SAFIR reference violet',(.13,.16,.34),.25,.35)
 r=w3_root('drawing_in',9.8,3.4);r['selectedTrucks']=2;r['selectedHealdFrames']=2;r['modeledWarpEnds']=2880
 # Actual S67 topology: fixed asymmetric head at one end of a long track, two complete mobile trucks.
 for yy in (-.70,.70):
  w3_box(r,'truck_linear_floor_rail',(-1.05,yy,.195),(7.25,.08,.025),'w3alloy','长行程移动车地轨')
  for xx in (-4.5,-3,-1.5,0,1.5,2.4):w3_box(r,'track_mount',(xx,yy,.18),(.16,.2,.02),'w3graphite','轨道地脚固定片')
 for truck_index,xcenter in enumerate((.60,-2.75)):
  cart=empty('s67_mobile_truck_'+str(truck_index+1),(xcenter,0,0),r,'完整移动车 '+str(truck_index+1),'frame')
  cart['selectedWidthM']=2.2
  for yy in (-.70,.70):w3_box(cart,'truck_long_beam',(0,yy,.40),(2.8,.10,.16),'w3alloy','移动车下纵梁')
  for xx in (-1.27,1.27):
   w3_box(cart,'truck_end_crossbeam',(xx,0,.40),(.10,1.50,.16),'w3alloy','移动车端梁')
   for yy in (-.70,.70):w3_wheel(cart,xx,yy)
   for yy in (-.42,.42):w3_box(cart,'truck_stanchion',(xx,yy,.98),(.07,.07,1.08),'w3alloy','工作架立柱')
  w3_beam(cart,.54,.90,2.2,1.0,.42,'移动车经轴',standbase=.48)
  w3_roll(cart,'经片展平导辊',.13,1.43,.055,2.2)
  for yy in (-.37,-.17):w3_box(cart,'upper_suspension_rail',(0,yy,1.69),(2.65,.035,.035),'w3alloy','综框悬挂导轨')
  w3_heald_frame(cart,-.37,1.38,0,label='奇数经纱综框（1440综丝）')
  w3_heald_frame(cart,-.17,1.38,1,label='偶数经纱综框（1440综丝）')
  w3_dropwire_bank(cart,-.02,1.38)
  w3_reed(cart,-.54,1.38)
  for xx in (-1.20,1.20):w3_box(cart,'reed_clamp',(xx,-.54,1.38),(.075,.12,.27),'w3cyan','筘夹与定位装置')
  beamc=(.54,.90); guidec=(.13,1.43)
  tangent,guide_entry,ga=w3_common_tangent(beamc,.423,guidec,.058,-1)
  guide_exit=w3_tangent_point((-.02,1.38),guidec,.058,-1)
  gb=math.atan2(guide_exit[1]-guidec[1],guide_exit[0]-guidec[0])
  # Loaded active truck is shown near the end of drawing-in; standby sheet remains clamped upstream.
  path=[tangent]+w3_arc(guidec,.058,ga,gb,10)+[(-.02,1.38)]
  path += [(-.17,1.38),(-.37,1.38),(-.54,1.38),(-.69,1.38)] if truck_index==0 else [(-.10,1.38)]
  w3_parallel(cart,path,2880,2.1,'穿经后经片' if truck_index==0 else '备用车待穿经片',.00025)
  if truck_index==1:w3_box(cart,'standby_sheet_clamp',(0,-.11,1.36),(2.2,.025,.02),'w3cyan','待穿经片夹持条')
  w3_box(cart,'truck_blue_endcap',(-1.37,0,.65),(.12,1.65,.48),'w3violet','移动车端部护罩','shell',.035)
  for xx in (-1.30,1.30):w3_path(cart,'truck_pushing_handle',[(xx,-.75,.75),(xx,-.90,.75),(xx,-.90,1.0),(xx,-.75,1.0)],.018,'w3alloy','移动车推行手柄','frame',8)
 # Fixed machine head, mechanically connected to a base and the two-column gantry.
 head=empty('safir_fixed_head',parent=r,label='S67固定式穿经机头',group='frame')
 w3_box(head,'head_base',(2.18,.55,.33),(.72,1.40,.30),'w3violet','固定机头底座')
 for yy in (.16,.95):w3_box(head,'head_column',(2.23,yy,1.32),(.20,.20,1.95),'w3violet','固定机头承力立柱')
 w3_box(head,'head_upper_bridge',(2.05,.35,2.27),(.65,1.72,.25),'w3violet','固定头上桥与驱动罩','shell',.04)
 for yy in (-.40,-.03):
  w3_box(head,'hanging_selection_unit',(1.80,yy,1.85),(.30,.25,.55),'w3cyan','选纱与穿经功能机头（外部轮廓）','shell',.025)
  w3_box(head,'selection_linear_axis',(1.80,yy,1.52),(.15,.13,.18),'w3alloy','穿经头末端导向组件')
  w3_cyl(head,'drawing_needle',(1.65,yy,1.38),.003,.29,'w3alloy',axis='y',label='穿经针工作端',group='roller',n=12)
  w3_path(head,'head_pneumatic_line',[(1.84,yy,2.12),(2.08,yy,2.37),(2.25,.8,2.37),(2.25,.8,.75)],.016,'w3graphite','机头气管与线束','frame',8)
 w3_box(head,'awc_vision_housing',(1.65,.02,1.57),(.16,.16,.12),'w3graphite','AWC 2.0双纱检测外部模块')
 w3_cyl(head,'awc_optical_window',(1.65,-.067,1.55),.025,.008,'glass',axis='y',label='双纱检测光学窗口',group='shell',n=24)
 w3_shell(head,'fixed_head_service_cabinet',(2.43,1.04,1.09),(.62,.48,1.65),'w3violet')
 w3_panel(head,(2.43,.79,1.09),.54,1.48,'w3violet','固定机头电气检修门')
 w3_hmi(r,2.62,-.54,1.65);w3_signal(r,2.4,.85,2.25)
 # Yellow protective crossbeam follows the official photo without enclosing the mobile track.
 for xx in (-.9,1.95):w3_box(r,'operator_guard_post',(xx,-1.03,.76),(.045,.045,1.16),'w3safety','前侧安全护栏立柱')
 w3_box(r,'operator_guard_crossbar',(.525,-1.03,1.35),(2.9,.045,.045),'w3safety','穿经操作安全横杆')
 return r

def w3_cloth(parent,path,width=2.1,label='连续成布'):
 vs=[]
 for y,z in path:vs += [(-width/2,y,z),(width/2,y,z)]
 fs=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(path)-1)]
 o=w3_mesh('continuous_woven_cloth',vs,fs,'w3yarn',parent,label,'material')
 return o

def machine_weaving():
 r=w3_root('weaving',6.2,4.4);r['selectedReedWidthM']=2.2;r['selectedClothWidthM']=2.1;r['modeledWarpEnds']=2880;r['selectedHealdFrames']=2;r['selectedWeftFeeders']=4
 # Low modern Ultimax silhouette, broad white nose and dark lower skirt; hollow removable panels.
 for side in (-1,1):
  x=side*1.43
  w3_box(r,'main_cast_sideframe',(x,.12,.60),(.40,2.35,.80),'w3graphite','织机承力侧架',bevel=.06)
  sh=w3_shell(r,'ultimax_side_pod',(x,.03,.93),(.64,2.4,1.28),open_front=True)
  w3_panel(sh,(x,-1.19,1.02),.57,1.05)
  w3_box(sh,'pod_dark_lower_skin',(x,-1.225,.45),(.59,.05,.30),'w3graphite','下侧防护裙板','shell',.055)
  w3_box(sh,'pod_top_dark_inset',(x,-.09,1.59),(.54,1.95,.06),'w3graphite','机头上方防护嵌板','shell',.025)
  for yy in (-.85,.9):w3_box(r,'machine_floor_foot',(x,yy,.22),(.50,.35,.08),'w3alloy','可调安装机脚')
 for yy in (-.70,.58):w3_box(r,'loom_lower_crossmember',(0,yy,.42),(2.7,.18,.20),'w3graphite','织机下横梁')
 # Actual yarn population, rear beam and regulated backrest.
 w3_beam(r,1.15,.77,2.2,1.0,.44,'织机送经轴')
 w3_roll(r,'电子送经后梁',1.35,1.38,.065,2.2)
 for side in (-1,1):
  w3_path(r,'backrest_support',[(side*1.22,1.15,.55),(side*1.22,1.35,1.38)],.035,'w3graphite','后梁支承臂','frame',8)
  w3_box(r,'backrest_loadcell',(side*1.22,1.35,1.38),(.10,.12,.12),'w3cyan','后梁张力检测单元')
 w3_dropwire_bank(r,.84,1.405)
 w3_heald_frame(r,.40,1.445,0,label='平纹第一综框：1440综丝')
 w3_heald_frame(r,.25,1.365,1,label='平纹第二综框：1440综丝')
 # Covered shedding drive and physical lever connections, without invented OEM internal gears.
 shed=w3_shell(r,'covered_shedding_module',(.03,.63,.77),(2.32,.45,.52),'w3graphite',True)
 for side in (-1,1):
  for yy,zz in ((.40,1.445),(.25,1.365)):
   w3_path(r,'heald_drive_link',[(side*1.13,.60,.60),(side*1.13,yy,zz-.25)],.012,'w3alloy','开口机构综框连杆','motor',6)
 # Two shared strand meshes create all 2,880 unique ends in the two shed planes.
 beamc=(1.15,.77);backc=(1.35,1.38)
 rearpoint,backentry,ba=w3_common_tangent(beamc,.443,backc,.068,-1)
 backexit=w3_tangent_point((.84,1.405),backc,.068,-1)
 bb=math.atan2(backexit[1]-backc[1],backexit[0]-backc[0])
 rearpath=[rearpoint]+w3_arc(backc,.068,ba,bb,10)+[(.84,1.405)]
 for phase,zz in ((0,1.445),(1,1.365)):
  path=rearpath+[(.50,1.405),(.40,zz if phase==0 else 1.385),(.25,zz),(-.40,1.23),(-.53,1.23)]
  proto=w3_path(r,'shed_warp_'+str(phase),[(0,y,z) for y,z in path],.00025,label='平纹经纱完整群 '+str(phase+1));proto.location.x=-1.05+(phase+.5)*2.1/2880
  for j in range(1,1440):w3_instance(proto.data,'warp_end_%04d'%(j*2+phase+1),(-1.05+(j*2+phase+.5)*2.1/2880,0,0),r,'经纱 '+str(j*2+phase+1)+'/2880','material')
 w3_reed(r,-.40,1.23,2.1,1441,.20)
 # Rapier tapes: paired, flat and positively supported by side guides, at the open shed.
 for side in (-1,1):
  w3_box(r,'rapier_drive_housing',(side*1.46,-.22,1.22),(.42,.40,.30),'w3graphite','剑杆驱动轮箱（护罩）','shell',.045)
  w3_box(r,'rapier_tape_guide',(side*1.19,-.23,1.22),(.28,.06,.045),'w3alloy','剑带导向座')
  w3_box(r,'flat_rapier_tape',(side*.65,-.23,1.22),(1.18,.027,.006),'w3graphite','左/右柔性剑带','roller',.001)
  w3_box(r,'rapier_gripper',(side*.035,-.23,1.224),(.075,.036,.013),'w3alloy','传纬/接纬剑头','roller',.003)
 # Entire cloth path to take-up roll, separate from low frontal operating fascia.
 w3_roll(r,'织口胸梁',-.76,1.155,.075,2.2)
 w3_roll(r,'卷取牵引辊',-.97,1.04,.055,2.2,material='rubber')
 w3_roll(r,'成品布卷',-1.10,.58,.30,2.2,material='w3yarn')
 # Horizontal upper tangent to breast beam; smooth wrap followed by tangent to traction roller.
 breast=(-.76,1.155);traction=(-.97,1.04);takeup=(-1.10,.58)
 bp,tp,ta=w3_common_tangent(breast,.077,traction,.057,-1)
 te,be,tb=w3_common_tangent(traction,.057,takeup,.302,-1)
 clothpath=[(-.53,1.232)]+w3_arc(breast,.077,math.pi/2,ta,10)+w3_arc(traction,.057,ta,tb,10)+[be]
 w3_cloth(r,clothpath)
 for side in (-1,1):
  w3_bearing(r,side*1.22,-1.10,.58)
  w3_cyl(r,'cloth_roll_coupling',(side*1.32,-1.10,.58),.045,.16,label='卷取轴联接',group='motor')
 # Front fascia sits above cloth roll and ahead of the textile path, matching the current exterior.
 fascia=empty('full_width_front_fascia',parent=r,label='整幅前操作护板',group='shell',explode=[0,-.4,.2])
 w3_box(fascia,'white_operator_fascia',(0,-1.25,1.12),(2.20,.13,.24),'w3white','整幅白色前操作护板','shell',.045)
 for xx in (-.78,-.27,.27,.78):w3_cyl(fascia,'front_control',(xx,-1.324,1.13),.025,.012,'green',axis='y',label='前面板操作按键',group='shell',n=24)
 w3_hmi(r,-1.43,-.76,1.65,True)
 # Four weft channels, four active + four reserve packages. Only channel 1 is selected at this instant.
 feed=empty('four_channel_weft_system',parent=r,label='四路储纬与供纬系统',group='frame')
 for yy in (-.48,.34):w3_box(feed,'weft_creel_vertical',(-2.45,yy,1.05),(.055,.055,1.74),'w3alloy','纬纱筒子架立柱')
 for zz in (.56,.91,1.26,1.61):w3_box(feed,'weft_creel_horizontal',(-2.45,-.07,zz),(.065,.98,.04),'w3alloy','纬纱架层横梁')
 for yy in (-.48,.34):w3_box(feed,'weft_creel_foot',(-2.45,yy,.22),(.55,.32,.08),'w3graphite','纬纱架地脚')
 for i in range(4):
  z=.56+i*.35
  for reserve,yy in enumerate((-.48,.34)):
   w3_cyl(feed,'weft_package',(-2.28,yy,z),.12,.24,'w3yarn',label=('备用' if reserve else '在用')+'纬纱筒子 '+str(i+1),group='material',n=32)
   w3_cyl(feed,'weft_package_spindle',(-2.41,yy,z),.018,.45,label='纬纱筒子托杆',group='frame',n=12)
  fy=-.38+(i%2)*.40;fz=1.33+(i//2)*.31
  w3_box(feed,'feeder_bracket',(-1.94,fy,fz-.13),(.33,.12,.08),'w3graphite','储纬器安装托架')
  w3_path(feed,'feeder_support',[(-2.06,fy,.28),(-2.06,fy,fz-.14)],.025,'w3alloy','储纬器独立支柱','frame',8)
  w3_cyl(feed,'feeder_motor',(-1.98,fy,fz),.10,.14,'w3graphite',label='储纬器驱动外壳',group='motor',n=32)
  w3_cyl(feed,'feeder_drum',(-1.84,fy,fz),.085,.16,'w3alloy',label='储纬滚筒 '+str(i+1),group='roller',n=32)
  # Fifteen continuous winding turns per selected visual stock level, connected to both supply and exit.
  winding=[(-1.91+.15*k/240,fy+.086*math.sin(k*2*math.pi/16),fz+.086*math.cos(k*2*math.pi/16)) for k in range(241)]
  route=[(-2.15,-.48,z),(-2.10,-.60,z+.12),(-2.10,fy,fz+.087)]+winding+[(-1.73,fy,fz+.086),(-1.72,fy,fz),(-1.37,-.24,1.23+i*.025)]
  o=w3_path(feed,'continuous_weft_feed',route,.0010,'w3yarn','供纬—储纬连续15圈—选纬通道 '+str(i+1),'material',4);o['selectedReserveTurns']=15
  w3_box(feed,'feeder_support_foot',(-2.06,fy,.22),(.20,.22,.08),'w3graphite','储纬器立柱地脚')
 w3_box(r,'weft_selector',(-1.35,-.24,1.31),(.14,.16,.25),'w3graphite','四路选纬模块')
 w3_path(r,'selected_pick',[(-1.28,-.24,1.23),(-.04,-.23,1.23)],.0010,'w3yarn','当前引纬通道：纯棉纬纱','material',4)
 # Supported integrated drive housings, no free-floating generic motor.
 for x,y,z,lab in ((-1.43,.43,.86,'主轴直驱外壳'),(1.43,1.15,.77,'电子送经驱动外壳'),(1.43,-1.10,.58,'电子卷取驱动外壳')):
  w3_cyl(r,'integrated_axis_motor',(x,y,z),.13,.25,'w3graphite',label=lab+'（型号/内部未知）',group='motor',n=32)
  w3_box(r,'integrated_motor_bracket',(x,y,z-.14),(.32,.30,.065),'w3alloy','驱动轴安装托座')
  w3_cyl(r,'integrated_axis_coupling',(x-math.copysign(.16,x),y,z),.045,.12,'w3alloy',label='驱动负载同轴连接',group='motor',n=24)
 w3_signal(r,1.5,1.01,1.63)
 return r


def w3_common_tangent(c1,r1,c2,r2,side=-1):
 """Outer common tangent; side=-1 selects the exposed upper/outer path used here."""
 a=math.atan2(c2[1]-c1[1],c2[0]-c1[0])+side*math.acos((r1-r2)/math.dist(c1,c2))
 a=a%(2*math.pi)
 return (c1[0]+r1*math.cos(a),c1[1]+r1*math.sin(a)),(c2[0]+r2*math.cos(a),c2[1]+r2*math.sin(a)),a
