"""eFK Standard PET / V / 16-section 384-position selected public configuration.
Definitions only. Original geometry; public brochure envelope and older authored
V-layout reference are evidence layers, not complete OEM assembly drawings.
Exec after build_models.py definition prefix. No dist files are written here.
"""
from pathlib import Path
import importlib.util, math
from mathutils import Vector, Matrix

_E5_SPEC = {
    'sections':16, 'positionsPerSection':24, 'sides':2,
    'positionsPerSidePerSection':12, 'windingDecks':3,
    'positionsPerDeckPerSidePerSection':4, 'positions':384,
    'sectionPitchM':1.44, 'yarnPitchM':.110,
    'lengthOverallM':27.406, 'widthUpperM':7.944,
    'widthBaseM':4.764, 'widthStationaryCreelM':6.724,
    'heightOverallM':5.678, 'primaryHeaterLengthM':2.0,
    'coolingRailLengthM':1.1, 'secondaryHeaterLengthM':1.46,
    'maximumPackageStrokeM':.250, 'maximumPackageDiameterM':.250,
}
_E5_DATA_URL='https://www.oerlikon.com/ecoma/files/DL_Texturing_OBA_DTY_2023_05_datasheet_manual_en.pdf?download=true'
_E5_PRODUCT_URL='https://www.barmag.com/en/solutions-technologies/from-melt-to%E2%80%A6/textured-yarn-dty/efk/'
_E5_OLD_LAYOUT='https://www.yumpu.com/en/document/view/2029394/efk-technical-data-oerlikon-barmag-oerlikon-textile'
_E5_COMPONENT_URL='https://www.barmag.com/ecomaXL/files/barmag_DTY_2026-04_en.pdf?download=true'

for _key,_color,_metal,_rough in (
    ('e5enamel',(.79,.82,.81),.22,.36),('e5alloy',(.57,.62,.64),.82,.28),
    ('e5graphite',(.045,.053,.058),.32,.39),('e5ceramic',(.85,.86,.80),.04,.25),
    ('e5poy',(.87,.89,.84),0,.65),('e5dty',(.93,.87,.72),0,.83),
    ('e5yarn',(.66,.45,.13),0,.7),('e5yellow',(.9,.63,.045),.08,.37)):
    if _key not in M:M[_key]=mat(_key,_color,_metal,_rough)

_e5_spec=importlib.util.spec_from_file_location('textile_e5_drive_exterior',BLEND/'refine_drives_v4.py')
_e5_exterior=importlib.util.module_from_spec(_e5_spec);_e5_spec.loader.exec_module(_e5_exterior)

def _e5_meta(object,role=None,desc=None):
    if role:object['componentRole']=role
    if desc:object['description']=desc
    object['evidenceStatus']='public_function_selected_geometry'
    return object

def _e5_beam(parent,name,a,b,width=.045,depth=.045,ma='e5alloy',label='型材支承'):
    a,b=Vector(a),Vector(b);o=_s3_box(parent,name,tuple((a+b)/2),(width,depth,(b-a).length),ma,label,'frame',min(width,depth)*.12)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def _e5_drive(parent,name,loc,label,style='induction',size=(.42,.27,.27),rotation=None):
    g=empty(name,loc,parent,label,'motor',explode=[.2,.1,.15]);
    _e5_exterior.add_exterior(g,style,size,size[0]*.63,-size[2]*.58 if style=='induction' else None,False)
    if rotation:g.rotation_euler=rotation
    g['driveRevision']='5.0';g['motorLayoutEvidence']='selected_functional_station_location_inferred'
    g['description']='完整设备的功能驱动工位外观；实际电机数量、位置、功率与传动BOM未获厂家装配图确认。'
    # Every selected exterior station has an actual load-bearing mounting path.
    x,y,z=loc;bottom=z-size[2]*.58
    mount=empty(name+'_support',(x,y,0),parent,'驱动托座与地脚支承；安装位置推定','frame')
    _s3_box(mount,'EFK_drive_mounting_plate',(0,0,bottom-.018),(size[0]*1.12,size[1]*1.5,.036),'e5alloy','电机安装托板','frame',.006)
    for xx in (-size[0]*.36,size[0]*.36):
        _s3_box(mount,'EFK_drive_support_post',(xx,0,bottom/2),(.055,.055,max(bottom,.06)),'e5enamel','驱动工位支承立柱','frame',.006)
    _s3_box(mount,'EFK_drive_baseplate',(0,0,.035),(size[0]*1.3,size[1]*1.7,.07),'e5graphite','驱动托座底脚','frame',.008)
    _s3_unit_finish(mount)
    return g

def _e5_godet(parent,name,loc,feed):
    g=empty(name,loc,parent,feed+'导丝盘与分纱导轮','roller')
    _e5_meta(g,feed+'_godet','导丝盘运输纱线；外观参考厂家喂纱机构照片。背部电机形式、数量及实际安装未核实，不据此宣称一工位一马达。')
    rotor=empty(name+'_rotation',(0,0,0),g,feed+'导丝盘','roller',spin='z')
    _s3_cyl(rotor,name+'_drum',(0,-.038,0),.048,.076,'e5alloy','y',feed+'抛光导丝盘','roller',48)
    _s3_cyl(rotor,name+'_nose',(0,-.081,0),.044,.010,'e5graphite','y',feed+'端面','roller',48)
    _s3_cyl(rotor,name+'_hub',(0,-.088,0),.009,.008,'e5alloy','y','导丝盘端面紧固','roller',24)
    _s3_cyl(g,name+'_separator',(.034,-.075,.071),.010,.061,'e5ceramic','y',feed+'分纱小导轮','roller',24)
    _s3_box(g,name+'_support',(0,.020,.018),(.098,.025,.178),'e5enamel',feed+'安装面板','frame',.007)
    _s3_box(g,name+'_guard',(-.038,.052,.009),(.014,.040,.106),'e5graphite',feed+'后侧局部防护片；避开盘面及相邻纱路','shell',.006)
    _s3_box(g,name+'_tab',(.019,-.01,-.060),(.043,.024,.040),'e5yellow','穿丝操作拨片','frame',.006)
    _s3_unit_finish(rotor);_s3_unit_finish(g)
    return g

def _e5_friction(parent,loc):
    g=empty('efk_friction_unit',loc,parent,'三轴摩擦盘假捻器','roller');_e5_meta(g,'friction_unit','三轴、错层摩擦盘与轴承安装结构。选用9层盘的可视构型，非已取得的厂家盘片BOM；未混入气流变形喷嘴。')
    for xx in (-.035,.035):_s3_box(g,'friction_base_side',(xx,.014,-.018),(.032,.093,.026),'e5alloy','假捻器轴承安装底座侧梁','frame',.003)
    _s3_box(g,'friction_base_rear',(0,.038,-.018),(.038,.044,.026),'e5alloy','假捻器底座后桥；中央出纱留空','frame',.003)
    centers=[(-.021,-.014),(.021,-.014),(0,.022)]
    for k,(x,y) in enumerate(centers):
        shaft=empty('efk_friction_shaft_'+str(k+1),(x,y,0),g,'摩擦盘轴组','roller',spin='y')
        _s3_cyl(shaft,'friction_spindle',(0,0,.056),.006,.136,'e5graphite','z','假捻器三轴轴伸','roller',24)
        for level in range(k,9,3):
            z=.012+level*.011
            _s3_cyl(shaft,'friction_disc',(0,0,z),.026,.009,'e5ceramic','z','错层摩擦工作盘','roller',48)
            _s3_cyl(shaft,'friction_disc_spacer',(0,0,z+.0055),.010,.002,'e5alloy','z','摩擦盘隔圈','roller',24)
        _s3_unit_finish(shaft)
        _s3_cyl(g,'friction_bearing_seat',(x,y,-.004),.012,.018,'e5alloy','z','摩擦轴轴承座','frame',32)
    _s3_box(g,'friction_guard',(0,.063,.05),(.10,.012,.17),'e5graphite','假捻器后侧防护','shell',.004)
    _s3_unit_finish(g)
    return g


def _e5_package(parent,name,loc,material,label,r=.119,length=.245):
    g=empty(name,loc,parent,label,'material');_e5_meta(g,name,'卷装外径及卷绕填充量为所选展示状态；不表示实际工艺的满卷质量。')
    _s3_cyl(g,name+'_body',(0,0,0),r,length,material,'y',label,'material',64)
    for yy in (-length/2,length/2):
        _s3_cyl(g,name+'_end',(0,yy,0),r*.92,.008,material,'y',label+'端面','material',64)
        _s3_cyl(g,name+'_tube',(0,yy*1.08,0),.025,.022,'e5graphite','y','卷装纸管端部','material',32)
    _s3_unit_finish(g);return g

def _e5_position(parent,j,layout):
    """One complete yarn end; three deck variants remain individually selectable."""
    g=empty('EFK_texturing_position',(0,0,0),parent,'eFK完整加弹工位','frame')
    g['componentRole']='texturing_position';g['completeYarnPath']=True
    g['description']='单股PET路线：POY供纱、G1、一次加热、冷却、三轴摩擦盘假捻、G2、二次加热、W3、上油和一处DTY卷绕。'
    deck=j%3;column=j//3
    winding_x=(column-1.5)*.36-(j-5.5)*.11
    poy_x=winding_x
    poy_z=layout['poy'][1]+deck*.45
    wind_z=layout['winder'][1]+deck*.49
    _e5_package(g,'EFK_active_POY_package',(poy_x,layout['poy'][0],poy_z),'e5poy','工作中的POY供纱卷装',.145,.29)
    _s3_cyl(g,'POY_holder',(poy_x,layout['poy'][0]+.09,poy_z),.018,.45,'e5alloy','y','POY供纱锭杆','frame',24)
    for feed in ('G1','G2'):_e5_godet(g,'EFK_'+feed+'_godet',(0,*layout[feed]),feed)
    for code,label,points in [('primary','一次热箱纱道',[layout['primary_in'],layout['primary_out']]),('cooling','接触式冷却轨',[layout['cooling_in'],layout['cooling_out']]),('secondary','二次热箱纱道',[layout['secondary_in'],layout['secondary_out']])]:
        a,b=[(0,*p) for p in points]
        cg=empty('EFK_'+code+'_channel',(0,0,0),g,label,'roller')
        # Open U profile: yarn runs in the clearance, never through a solid beam.
        aa,bb=Vector(a),Vector(b)
        channel=_e5_beam(cg,'EFK_'+code+'_rail',aa+Vector((0,.025,0)),bb+Vector((0,.025,0)),.050,.010,'e5alloy',label+'槽底')
        for xx in (-.023,.023):_e5_beam(cg,'EFK_'+code+'_lip',aa+Vector((xx,0,0)),bb+Vector((xx,0,0)),.006,.05,'e5alloy',label+'槽壁')
        cg['componentRole']=code+'_channel';cg['measuredPathLengthMetres']=(Vector(a)-Vector(b)).length
        cg['openChannel']=True;cg['yarnClearanceVerified']=True
        channel['componentRole']=code+'_channel';channel['measuredPathLengthMetres']=(Vector(a)-Vector(b)).length
    _e5_friction(g,(0,*layout['friction']))
    winding=empty('EFK_DTY_winding_position',(winding_x,layout['winder'][0],wind_z),g,'三层卷绕中的独立卷绕位','roller')
    winding['windingDeck']=deck+1;winding['windingColumn']=column+1;winding['componentRole']='takeup_position'
    drum=empty('EFK_take_up_drum',(0,0,-.175),winding,'卷绕接触辊','roller',spin='z')
    _s3_cyl(drum,'takeup_contact_roller',(0,0,0),.055,.275,'e5graphite','y','卷绕接触辊','roller',40)
    package=_e5_package(winding,'EFK_DTY_package',(0,0,0),'e5dty','DTY成品卷装',.120,.245)
    package['componentRole']='dty_package';package['spinAxis']='z';package['spinSpeed']=.5
    for yy in (-.15,.15):
        _s3_box(winding,'takeup_cradle',(0,yy,-.15),(.028,.025,.33),'e5alloy','接至卷装两端的摇架臂','frame',.005)
        _s3_cyl(winding,'package_end_support',(0,yy,0),.020,.045,'e5alloy','y','卷装轴端支座','frame',24)
    _s3_cyl(winding,'cradle_pivot',(0,0,-.315),.018,.36,'e5alloy','y','与卷装平行的摇架铰轴','frame',24)
    tg=empty('EFK_traverse_guide',(.06,-.165,-.045),winding,'Camshaft横动导丝器','roller')
    _s3_torus(tg,'traverse_guide_eye',(0,0,0),.005,.0015,'e5ceramic','y','横动导丝器陶瓷眼圈','roller')
    _s3_box(winding,'winder_guard',(0,.18,-.08),(.31,.025,.30),'e5enamel','卷绕位后支板','frame',.007)
    _s3_box(winding,'doff_lever',(.16,-.05,-.035),(.018,.13,.025),'e5yellow','落筒摇架手柄','frame',.004)
    _s3_unit_finish(winding)
    # Local process points follow one yarn end. Thermal lengths are measured channel lengths.
    def godet_arc(feed,start,stop):
        yy,zz=layout[feed]
        return [(.0498*math.cos(a),yy-.038,zz+.0498*math.sin(a)) for a in [start+(stop-start)*n/24 for n in range(25)]]
    points=[(poy_x,layout['poy'][0]-.16,poy_z+.146),(poy_x,layout['poy'][0]-.24,2.35)]
    points+=godet_arc('G1',-math.pi/2,-3*math.pi/2)
    points.extend([(0,layout['G1'][0]-.038,5.64),(0,layout['primary_in'][0],5.64)])
    points.extend([(0,*layout['primary_in']),(0,*layout['primary_out']),(0,*layout['cooling_out'])])
    # Nine disc levels: cross each physical slab at its outer tangent, with a
    # short lateral change only in the inter-disc gap; no straight line through discs.
    fy,fz=layout['friction'];centers=[(-.021,-.014),(.021,-.014),(0,.022)]
    for level in reversed(range(9)):
        cx,cy=centers[level%3];v=Vector((-cx,-cy)).normalized();px=cx+v.x*.027;py=cy+v.y*.027
        zz=fz+.012+level*.011
        points.extend([(px,fy+py,zz+.0053),(px,fy+py,zz-.0053)])
    points.append((0,layout['G2'][0]-.038,layout['friction'][1]-.035))
    points+=godet_arc('G2',math.pi/2,-math.pi/2)
    points.extend([(0,*layout['secondary_in']),(0,*layout['secondary_out'])])
    def tangent_to_left_arc(source,center,radius):
        dy=source[0]-center[0];dz=source[1]-center[1]
        start=math.atan2(dz,dy)+math.acos(radius/math.hypot(dy,dz))
        return [(0,center[0]+radius*math.cos(a),center[1]+radius*math.sin(a)) for a in [start+(math.pi-start)*n/20 for n in range(21)]]
    points+=tangent_to_left_arc(layout['secondary_out'],layout['W3'],.0475)
    w3clear=(layout['W3'][0]-.0475,layout['W3'][1]-.06)
    points.append((0,*w3clear));points+=tangent_to_left_arc(w3clear,layout['oil'],.0265)
    # Pass below the take-up frames, then rise in front of the packages. Separate
    # the three deck paths rather than drawing them through lower packages.
    front=layout['winder'][0]-.23-deck*.025;lane_x=winding_x+.06+(deck-1)*.008
    points.extend([(0,layout['oil'][0]-.05,layout['oil'][1]),(0,layout['oil'][0]-.05,.24+deck*.018),
        (lane_x,front,.24+deck*.018),(lane_x,front,wind_z-.110),
        (winding_x+.06,layout['winder'][0]-.136,wind_z-.045),
        (winding_x+.06,layout['winder'][0]-.165,wind_z-.045),
        (winding_x+.06,layout['winder'][0]-.174,wind_z-.045),
        (winding_x+.06,layout['winder'][0]-.174,wind_z+.121),
        (winding_x+.06,layout['winder'][0]-.10,wind_z+.121),
        (winding_x,layout['winder'][0]-.10,wind_z+.121)])
    yarn=w3_path(g,'EFK_continuous_yarn',points,.0007,'e5yarn','POY至DTY独立连续纱路','material',5)
    yarn['componentRole']='continuous_yarn_path';yarn['thicknessStatus']='visual_yarn_display';yarn['physicalSimulation']=False
    # Keep semantic subgroup selection for the working devices; batch the static support/channel surfaces.
    _s3_unit_finish(g)
    return g

def _e5_section(parent,layout):
    """One 1.44 m section, one side: twelve complete ends / four by three take-ups."""
    s=empty('EFK_section_side',(0,0,0),parent,'eFK单侧一节：12完整工位','frame')
    s['sectionPitchMetres']=1.44;s['positionsOnSectionSide']=12
    for j in range(12):
        p=_e5_position(s,j,layout);p.location.x=(j-5.5)*.11
        p['sectionPosition']=j+1;p['windingDeck']=j%3+1
        p['thermalLengthsMetres']=[2.0,1.1,1.46]
    # Shared support rails, with open working faces so the continuous path is visible.
    f=empty('EFK_section_structure',(0,0,0),s,'1.44m节距机架与独立检修板','frame')
    for y in (.22,1.38):
        for z in (.14,.42,2.08):
            _s3_box(f,'EFK_longitudinal_frame',(0,y,z),(1.44,.07,.08),'e5enamel','分节纵向机架','frame',.01)
    for x in (-.68,.68):
        for y in (.22,1.38):
            _s3_box(f,'EFK_lower_upright',(x,y,1.14),(.08,.08,2.14),'e5enamel','卷绕机架立柱','frame',.01)
        _s3_box(f,'EFK_section_crossfoot',(x,1.191,.12),(.12,2.382,.12),'e5graphite','主机底宽半幅横撑','frame',.012)
        # Heated process-zone supports are outside the 110 mm yarn pitch array.
        _e5_beam(f,'EFK_thermal_diagonal',(x,1.44,2.11),(x,3.61,5.57),.065,.065,'e5enamel','热区斜置支架')
        _e5_beam(f,'EFK_thermal_inner',(x,1.35,2.08),(x,1.52,3.25),.045,.065,'e5enamel','假捻与冷轨支承')
        _s3_box(f,'EFK_creel_upright',(x,3.292,1.37),(.055,.065,2.70),'e5alloy','固定POY筒架立柱','frame',.007)
        _s3_box(f,'EFK_creel_foot',(x,3.24,.07),(.10,.244,.08),'e5graphite','固定筒架底脚','frame',.007)
    for z in (.65,1.10,1.55,2.35):
        _s3_box(f,'EFK_creel_crossrail',(0,3.26,z),(1.44,.04,.045),'e5alloy','固定筒架三层支承与导纱横杆','frame',.006)
    # Back/side walls leave the yarn-side heater channels visible; neither heater
    # is falsely filled with a solid block that would hide the yarn trajectory.
    for code,label in [('primary','2m一次加热箱'),('secondary','1.46m二次加热箱')]:
        a=Vector((0,*layout[code+'_in']));b=Vector((0,*layout[code+'_out']))
        offset=Vector((0,.05,0));h=empty('EFK_'+code+'_heater_casing',(0,0,0),s,label+'分节外壳','shell',explode=[0,.15,.18])
        _e5_beam(h,'EFK_'+code+'_back',a+offset,b+offset,1.34,.07,'e5enamel',label+'后背保温板')
        for x in (-.665,.665):
            _e5_beam(h,'EFK_'+code+'_edge',a+Vector((x,0,0)),b+Vector((x,0,0)),.035,.13,'e5graphite',label+'侧边框')
        for t in (.25,.72):
            q=a.lerp(b,t);_s3_box(h,'EFK_heater_handle',(0,q.y-.05,q.z),(.18,.03,.025),'e5graphite','热箱盖操作横柄','shell',.006)
        _s3_unit_finish(h)
    # W3 is a shared longitudinal shaft; each end has its own nip/guide interface.
    w3=empty('EFK_W3_section_shaft',(0,*layout['W3']),s,'W3卷前喂纱轴段','roller',spin='x')
    _s3_cyl(w3,'EFK_W3_surface',(0,0,0),.038,1.44,'e5alloy','x','W3共轴喂纱表面','roller',48)
    for j in range(12):
        x=(j-5.5)*.11
        _s3_cyl(w3,'EFK_W3_nip_sleeve',(x,0,0),.046,.082,'e5graphite','x','W3工位摩擦套','roller',32)
        _s3_cyl(f,'EFK_W3_pressure_roller',(x,layout['W3'][0]-.076,layout['W3'][1]),.027,.078,'e5graphite','x','W3逐纱压辊；3mm选定穿丝净隙','roller',24)
        oil=empty('EFK_oil_contact',(x,layout['oil'][0],layout['oil'][1]),s,'卷绕前上油接触位','roller',spin='x')
        _s3_cyl(oil,'EFK_oil_wheel',(0,0,0),.025,.080,'e5ceramic','x','卷绕前上油轮','roller',32)
    _s3_unit_finish(w3)
    _s3_box(f,'EFK_oil_trough',(0,layout['oil'][0]+.012,layout['oil'][1]-.045),(1.40,.08,.055),'e5alloy','机底上油槽','frame',.006)
    for deck in range(3):
        z=layout['winder'][1]+deck*.49
        _s3_box(f,'EFK_winding_deck_support',(0,.82,z-.10),(1.44,.07,.07),'e5enamel','卷绕层后板承托纵梁','frame',.006)
        for xx in (-.68,.68):_s3_box(f,'EFK_winding_deck_crossbrace',(xx,.8,z-.10),(.055,1.16,.07),'e5enamel','卷绕层接至机架立柱的横撑','frame',.006)
        cam=empty('EFK_camshaft_section',(0,layout['winder'][0]+.30,z-.12),s,'Camshaft机械横动共轴段','roller',spin='x')
        _s3_cyl(cam,'EFK_camshaft_steel',(0,0,0),.018,1.44,'e5alloy','x','分层机械横动轴','roller',32)
        for c in range(4):
            x=(c-1.5)*.36
            _s3_cyl(cam,'EFK_traverse_cam',(x,0,0),.045,.055,'e5graphite','x','横动凸轮外形；槽形与相位未核实','roller',32)
        _s3_unit_finish(cam)
    # A physically present belt span: no invisible single motor per yarn end.
    fy,fz=layout['friction']
    belt=empty('EFK_friction_tangential_belt',(0,fy+.065,fz-.04),s,'type 8假捻器切向带区段','motor')
    _s3_box(belt,'EFK_tangential_working_run',(0,0,0),(1.44,.012,.025),'e5graphite','假捻器切向带工作边','motor',.001)
    _s3_box(belt,'EFK_tangential_return_run',(0,.07,0),(1.44,.012,.025),'e5graphite','假捻器切向带回程边','motor',.001)
    for j in range(12):
        _s3_cyl(belt,'EFK_friction_belt_whorl',((j-5.5)*.11,.026,0),.026,.025,'e5alloy','z','假捻器切向带传动轮','motor',32)
    _s3_unit_finish(belt);_s3_unit_finish(f)
    return s

def machine_texturing():
    r=empty('stage_texturing',label='eFK Standard双面V型加弹机');roots.append(r)
    config='eFK Standard；PET单股；V型；16节×24=384工位；固定筒架；godet喂纱；type 8切向带假捻；Camshaft三层卷绕；手动落筒'
    metadata={
        'stage':'texturing','equipmentId':'texturing','modelVersion':'3.0','driveRevision':'5.0',
        'referenceManufacturer':'Barmag','referenceModel':'eFK','referenceConfiguration':config,
        'referenceStatus':'partial_public_reference','fidelityStatus':'partial_public_reference',
        'structuralCompleteness':False,'motorDetailScope':'external_only','dimensionsUnit':'metres',
        'modelType':'public_configuration_reconstruction','capacityMatchedLine':False,
        'selectedTexturingPositions':384,'selectedSections':16,'sectionPitchMetres':1.44,
        'selectedPrimaryHeaterLengthMetres':2.0,'selectedCoolingLengthMetres':1.1,'selectedSecondaryHeaterLengthMetres':1.46,
        'selectedActivePOYPackages':384,'selectedReservePOYPackages':0,'selectedDTYPackages':384,'selectedContinuousYarnPaths':384,
        'referenceUrl':_E5_PRODUCT_URL,'parameterEvidenceUrl':_E5_DATA_URL,'componentReferenceUrl':_E5_COMPONENT_URL,
        'layoutReferenceUrl':_E5_OLD_LAYOUT,'dimensionSourceStatus':'official_2023_index_original_download_unavailable',
        'layoutEvidenceStatus':'historical_manufacturer_V_description_local_coordinates_inferred',
        'motorCountEvidence':'7 selected common-drive exterior stations; installation count and gearbox connectivity inferred; G1/G2 integrated drives not separately modeled',
        'actualScope':'384完整单股工位及连续纱路；含全POY、G1/G2、2m热段、1.1m冷段、三轴假捻、1.46m二热、W3、上油、三层卷绕。全套订单BOM、隐藏驱动与全部传动尚未核实。',
    }
    for k,v in metadata.items():r[k]=v
    r['selectedCounts']={'sections':16,'positionsPerSection':24,'positions':384,'sides':2,'positionsPerSide':192,'windingDecksPerSide':3,'windersPerDeckPerSection':4,'primaryHeaterPaths':384,'coolingPaths':384,'secondaryHeaterPaths':384,'activePOYPackages':384,'DTYPackages':384,'continuousYarnPaths':384,'frictionUnits':384,'frictionShafts':1152,'commonDriveStations':7}
    # One straight 3.1 m primary/cooling zone per side. The thermal path lengths
    # are published; these exact installation coordinates remain reconstruction.
    top=Vector((3.55,5.55));delta=Vector((-2.0,-math.sqrt(3.1**2-2.0**2)));joint=top+delta*(2/3.1);bottom=top+delta
    layout={'poy':(3.10,.65),'G1':(3.77,5.43),'primary_in':tuple(top),'primary_out':tuple(joint),
        'cooling_in':tuple(joint),'cooling_out':tuple(bottom),'friction':(bottom.x,bottom.y-.16),'G2':(1.43,2.85),
        'secondary_in':(1.32,2.68),'secondary_out':(1.32,1.22),'W3':(1.24,1.08),'oil':(1.10,.83),'winder':(.62,.65)}
    prototype=_e5_section(r,layout)
    section_groups=[]
    for side in range(2):
        for sec in range(16):
            x=(sec-7.5)*1.44
            if side==0 and sec==0:s=prototype;s.location.x=x
            else:s=_s3_clone_tree(prototype,r,(x,0,0),'EFK_section_side')
            s.scale.y=1 if side==0 else -1
            s['sectionIndex']=sec+1;s['machineSide']='A' if side==0 else 'B'
            positions=sorted((o for o in s.children if o.get('componentRole')=='texturing_position'),key=lambda o:o.get('sectionPosition',0))
            for p in positions:
                index=side*192+sec*12+p['sectionPosition'];p['positionIndex']=index
                p['label']='eFK完整加弹工位';p['sectionIndex']=sec+1;p['machineSide']=s['machineSide']
            section_groups.append(s)
    # Full length machine heads / thermal crossframes. The active 23.04 m is
    # exact section-pitch multiplication; the 4.366 m non-working head allocation
    # is selected geometry, not a recovered OEM cabinet dimension.
    structure=empty('EFK_full_length_frame',(0,0,0),r,'完整16节机架与热媒主管','frame')
    for k in range(17):
        x=-11.52+k*1.44
        _s3_box(structure,'EFK_top_crossframe',(x,0,5.638),(.09,7.944,.08),'e5enamel','7.944m顶部跨梁；位置推定','frame',.01)
        for y in (-1.4,1.4):
            _s3_box(structure,'EFK_main_tower',(x,y,2.81),(.09,.09,5.50),'e5enamel','热区支承立柱','frame',.012)
        for y in (-3.30,3.30):
            _s3_box(structure,'EFK_header_support',(x,y,5.53),(.08,.16,.12),'e5graphite','热媒管安装托架','frame',.009)
    for sign in (-1,1):
        _s3_cyl(structure,'EFK_primary_thermal_header',(0,sign*3.30,5.48),.055,23.10,'e5alloy','x','一次热箱热媒分配总管；管径待核','frame',32)
        _s3_box(structure,'EFK_electrical_tray',(0,sign*1.53,2.30),(23.10,.12,.065),'e5graphite','纵向电气线槽','frame',.006)
    for sign in (-1,1):
        x=sign*(11.52+2.183/2)
        head=_s3_module(r,'EFK_machine_end',(x,0,0),(2.138,2.65,2.35),'机头电气及传动柜；非订单钣金图',4,'e5enamel')
        head['dimensionsEvidence']='overall_length_minus_16_section_pitch_head_split_inferred'
        for side in (-1,1):
            for j in range(8):_s3_box(head,'EFK_end_vent',(0,side*1.337,.36+j*.055),(1.40,.015,.022),'e5graphite','机头散热百叶','shell',.003)
        if sign==-1:
            _s3_hmi(r,(x-.5,-1.4,1.7),'eFK工艺操作终端')
    # Seven explicitly inferred shared-drive locations; never 384 guessed motors.
    for side in (-1,1):
        tag='A' if side==1 else 'B';fy,fz=layout['friction']
        _e5_drive(r,'EFK_friction_drive_'+tag,(-12.12,side*(fy+.10),fz-.04),tag+'侧type 8假捻切向带驱动')
        _e5_drive(r,'EFK_W3_drive_'+tag,(-12.08,side*1.83,layout['W3'][1]),tag+'侧W3共轴喂纱驱动',size=(.37,.24,.24))
        _e5_drive(r,'EFK_camshaft_drive_'+tag,(12.12,side*1.70,1.30),tag+'侧Camshaft卷绕共用驱动',size=(.45,.29,.29),rotation=(0,0,math.pi))
        # End returns complete the selected tangential belt loop, not the unknown
        # motor-to-belt gearbox. Those upstream connections remain unmodeled.
        for xx in (-11.56,11.56):
            _s3_cyl(r,'EFK_belt_end_return',(xx,side*(fy+.10),fz-.04),.060,.035,'e5alloy','z','切向带端部回转轮；机构尺寸推定','motor',40)
    _e5_drive(r,'EFK_oil_circulation_drive',(12.05,-2.10,.42),'卷绕上油循环泵驱动',size=(.27,.18,.18))
    _s3_box(r,'EFK_oil_reservoir',(12.65,-1.80,.28),(.75,.63,.42),'e5alloy','上油循环箱；安装尺寸推定','shell',.035)
    for side in (-1,1):
        _s3_cyl(r,'EFK_oil_distribution_line',(0,side*1.12,.76),.014,24.20,'e5alloy','x','上油分配管','frame',24)
    _s3_unit_finish(structure)
    print('EFK_ASSEMBLED',len(section_groups),'section-sides / 384 positions',flush=True)
    return _s3_finish(r)
