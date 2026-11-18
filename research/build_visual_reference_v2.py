"""Build a visual-reference ledger from actually inspected official photographs/pages."""
import json, hashlib
from pathlib import Path
P=Path(__file__).parent; V=P/'visual-sources'; root=P.parent
photos=json.loads((V/'photos.json').read_text())+json.loads((V/'extra-photos.json').read_text())
photo_urls={x['file']:x['url'] for x in photos}
photo_urls.update({
 'stenter.webp':'https://www.monforts.de/wp-content/uploads/2025/09/montex-8500-vaz-da-costa-05.webp',
 'stenter-line.webp':'https://www.monforts.de/wp-content/uploads/2025/09/montex-8500-gta-linie-2-15-kopie.webp',
 'calender-page-14.png':'https://www.andritz.com/resource/blob/299446/80243e217ab3aca4d81c1611e62ee64b/brochure-textile-keep-profits-rolling-with-calenders-2023--data.pdf#page=14',
 'calender-page-16.png':'https://www.andritz.com/resource/blob/299446/80243e217ab3aca4d81c1611e62ee64b/brochure-textile-keep-profits-rolling-with-calenders-2023--data.pdf#page=16',
 'warping-page-01.png':'https://www.karlmayer.com/ecomaXL/files/KM_FS_WARPDIRECT_encn.pdf#page=1',
 'sizing-page-01.png':'https://www.karlmayer.com/ecomaXL/files/KM_FS_PROSIZE_en.pdf#page=1',
 'inspection-page-05.png':'https://www.uster.com/fileadmin/user_upload/Downloads/1_Products/1.4_Fabric_Inspection/Q-Bar/Uster_Fabric_Inspection_Q-Bar_brochure_web_en_23.pdf#page=5',
 'inspection-page-04.png':'https://www.uster.com/fileadmin/user_upload/Downloads/1_Products/1.4_Fabric_Inspection/Q-Bar/Uster_Fabric_Inspection_Q-Bar_brochure_web_en_23.pdf#page=4',
 'carding-page-03.png':'https://www.rieter.com/fileadmin/user_upload/products/documents/systems/fiber-preparation/c-81/rieter-c-81-card-brochure-3586-v1-98697-en.pdf#page=3',
 'carding-page-08.png':'https://www.rieter.com/fileadmin/user_upload/products/documents/systems/fiber-preparation/c-81/rieter-c-81-card-brochure-3586-v1-98697-en.pdf#page=8',
 'spinning-page-08.png':'https://www.rieter.com/fileadmin/user_upload/products/documents/systems/end-spinning/rieter-g-38-ring-spinning-machine-brochure-3236-v5-100402-en.pdf#page=8',
 'spinning-page-14.png':'https://www.rieter.com/fileadmin/user_upload/products/documents/systems/end-spinning/rieter-g-38-ring-spinning-machine-brochure-3236-v5-100402-en.pdf#page=14',
 'weaving-page-08.png':'https://www.picanol.be/sites/picanol/files/2021-11/pic_optimax-i-connect_brochure_2021_en_0.pdf#page=8',
})
records=[]
def row(id,name,reference,files,proportion,observed,changes,difference,priority='P1'):
 records.append(dict(id=id,name=name,priority=priority,reference=reference,
  visualEvidence=[{'localPath':'research/visual-sources/'+f,'sourceUrl':photo_urls[f],
                   'inspection':'已通过view_image实际查看照片/渲染PDF页面','sha256':hashlib.sha256((V/f).read_bytes()).hexdigest()} for f in files],
  relativeProportion=proportion,observedAssembly=observed,modelChanges=changes,v1Gap=difference))
row('calender','轧光机','ANDRITZ teXcal s-roll / Raconip L',
 ['calender-page-14.png','calender-page-16.png'],
 '工作辊横向跨度占主体宽度的大部分；主辊组集中于机体上半部，下半部留出垂直导布空间。承压侧架显著厚于导布小支架。',
 ['双侧厚实承压机架和大体积辊端轴承座形成闭合受力结构。','s-roll为双工作辊；Raconip L为L形三辊，不可混成三只等径悬空辊。','一侧大控制柜、另一侧轴承/压力系统不对称；细导布辊位于工作辊前下方。','液压/工艺软管从侧轴端接头伸出，传动与承压部件均有安装支承。'],
 ['选择一种明确构型：优先双辊压力轧光机，保留上硬辊、下复合辊的差异。','机架做厚板/铸件轮廓、底承压板、滑动轴承座和压力缸，不能只加螺栓。','电机→联轴器→减速箱→辊轴必须同轴或给出真实转向机构；每件下方有承重台。','布路按辊的切线和包覆圆弧连续构造，轧点布厚与辊隙匹配。','补进出布导辊架、油站、回油/压力管、可拆传动罩和电控柜。'],
 'v1三辊等距竖排、细立柱与简化侧置电机未形成真实轧光机体量；v2已有厚C架/双辊方向，待修支承与布路穿插。','P0')
row('weaving','剑杆织机','Picanol OptiMax-i Connect',
 ['weaving-photo-3.jpg','weaving-page-08.png','inspection-page-04.png'],
 '整机低矮宽展，主体横跨布幅；两端厚侧箱占一定宽度。纬纱架高于织机工作台，布辊位于工作台下方。',
 ['左右不对称厚侧箱夹持工作区，前侧有贯通全幅的梁/面板。','左侧独立筒子架和成组储纬器；右侧为较大的传动/开口罩。','综框处于经轴与织口之间，筘座在前方；布面从织口向前下方引出。','近景可看到两端滑动/连杆部件、侧板、轴承与线束，而不是单一框架。'],
 ['改为铸造/厚板侧机架，明确左侧供纬装置与右侧驱动箱。','建多组筒子、张力器、储纬器和从储纬器到引纬端的连续纬纱线。','经纱划分上下梭口并穿过对应综眼，剑杆从侧面进入梭口，避免全宽静态圆杆。','补后梁、送经轴支座、压布/卷取辊，以及主轴到筘座/开口模块的传动说明。','主驱动可采用真实直联示意；不做只围单个轮的假同步带。'],
 'v1主要是细骨架+梳齿；侧箱、供纬系统和实际梭口不足，主传动轮与电机之间没有完整带路径。','P0')
row('spinning','环锭细纱机','Rieter G 38',
 ['spinning-photo-1.jpg','spinning-photo-2.jpg','spinning-photo-3.jpg','spinning-page-08.png','spinning-page-14.png'],
 '机身长度明显大于机宽/高度；端部车头是大封闭箱体，重复锭位紧密排列。粗纱架高于牵伸区，锭子区位于其下。',
 ['端车头高大、门缝和通风口清楚，下面有低底座。','锭位间有薄隔板；连续钢领板和导轨贯穿整机。','细纱管、钢领/钢丝圈、导纱钩与牵伸装置形成清楚的竖向层次。','顶部喂纱架/输送吊挂设施与机身不在同一高度层；PDF第8页可见上架由连续立柱支承。','PDF第14页显示电子/半电子牵伸驱动中电机、带轮/带和罗拉轴的连接，不能仅放置一个未联接的电机。'],
 ['拉长机身，采用双面密集重复锭位，避免只有一排疏松的10个管。','每锭增加牵伸摇架/加压臂、胶辊、导纱钩、隔纱板、独立钢领与小钢丝圈。','形成连续钢领板、升降联接、底部锭带/龙带区域及外罩。','把主电机纳入端部车头，剖视时显示带轮/带与锭子传动路径；禁止漂浮通用电机。','粗纱须由上部卷装进入牵伸单元，再走到导纱与管纱；保留细线而非粗棒。'],
 'v1细纱与粗纱共享简化框架，缺密集双面工业机身、隔纱板与实际牵伸单元。','P0')
row('carding','梳棉机','Rieter C 80 / C 81',
 ['carding-photo-5.jpg','carding-whole.jpg','carding-webbridge.jpg','carding-page-03.png','carding-page-08.png'],
 '大锡林主导内部体积，刺辊与道夫明显更小；整机外罩与后高喂棉箱主导外部轮廓。出条部分比主梳理腔低。',
 ['剖面显示盖板链绕过锡林上部弧面形成回程闭环，而非水平悬浮块。','主锡林下方/侧面紧邻小辊，针布和固定梳理元件贴近圆周。','外罩为连续大型钣金包壳，门缝/把手/面板克制；控制屏支臂位于操作侧。','棉网在输出端经宽桥板收拢为条，再进入圈条机构。'],
 ['把盖板条沿圆弧布置并添加回程链/导轮，主锡林保留针布微结构。','喂棉箱、刺辊区、锡林腔、道夫/棉网桥分成清楚的高低体量。','增加可拆侧板与真实轴承、带轮、闭合皮带，正常视图显示整机包壳，剖视再看内部。','让棉网从道夫切向离开，在导网/集条位置收窄，圈条头位于条筒上方。'],
 'v1大圆筒直接裸露，盖板水平悬置，缺实际机壳体量与盖板回程。','P0')
row('stenter','拉幅烘干机','Monforts MONTEX 8500',
 ['stenter.webp','stenter-line.webp'],
 '纵向烘房由连续模块组成，长度显著大于入口宽度；入口轧车、展幅/超喂平台与烘房形成长前端段。导布辊很宽而轴颈较细。',
 ['入口有宽轧车罩和厚两侧机座，布面之后仍有较长的水平引导区域。','两侧针/铗轨与布边同高，轨道外有传感小轮和小执行组件。','烘房是连续平整箱体、规则门缝，顶部风道/排湿与桥架接入。','轧车近景可见轴承块、轴颈、联轴器、软管及支座。'],
 ['明确入口轧车→展布/超喂→针轨→多区烘房→冷却落布的体量层次。','针轨沿布边连续布置，加入入口链轮、张紧/回程结构与横向调幅丝杆。','顶部/侧部风机用法兰和支架安装，电机联接风机轴，不可只放电机在箱顶。','烘房增加分段检修门与内喷嘴/风道，正常状态包壳完整，剖视选择性打开。'],
 'v1短箱体+箱顶裸电机，入口过短、针轨无回程，工业风路和进布单元不足。','P0')
row('opening','开清棉','Rieter VARIOline / UNIfloc A 12',
 ['opening-photo-1.jpg','opening-plucker.jpg'],
 '棉包沿长轨道成列，抓棉臂横跨棉包；竖直回转/行走塔比棉包高，气流管径明显小于塔宽。',
 ['长直行走轨道带抓棉塔与横向悬臂。','抓棉臂底部滚筒接触棉包上表面，不是一个跨在四角立柱上的固定盖。','除杂/混棉设备为独立封闭箱体，由架空风管连接。'],
 ['改成长轨道+移动塔+悬臂抓棉头，棉包沿轨道两侧成列。','给抓棉头、行走轴和吸棉管建立明确连接；弯管采用分节法兰。','开松箱与棉包分开，底部留风机/落杂区和检修门。'],
 'v1把棉包、抓棉横梁和清棉箱压在同一个小方底盘上，缺主要线性布局。')
row('drawing','并条','Rieter RSB-D 55',
 ['drawing-photo-1.jpg','drawing-photo-2.jpg','drawing-photo-3.jpg'],
 '主机是紧凑高箱体；条筒约接近操作台下沿高度，喂入条筒列向后延伸，输出筒由侧前方圈条头罩住。',
 ['主机具有倾斜上盖、下部通风/检修门和侧维护台。','上部导条架把并行条子送进紧凑牵伸入口，而不是整机宽度的一组巨辊。','输出条筒处有圈条罩和换筒机构。'],
 ['缩小外露牵伸罗拉宽度并集中到主机头，外加可拆上罩。','喂入导条架建立两级高度，条子在进入牵伸前保持分列。','在输出筒上方建真实圈条盘/罩，补条筒脚轮、薄壁口圈、换筒导向。'],
 'v1把牵伸单元做成整幅宽的轧辊台，圈条机构缺失。')
row('combing','精梳','Rieter E 90',
 ['combing-photo-1.jpg','combing-photo-4.jpg'],
 '多梳理头沿横向长机身重复，棉卷排在后上方；前端集条/输出机头与条筒连接，外罩遮住大部分小机构。',
 ['棉卷有明显中空卷芯，在支承辊/托架上成排。','前侧是连续有门缝的下机壳和局部上盖。','条筒靠近集条端，维护平台/护栏不与工作辊混在一起。'],
 ['棉卷做中空筒芯与层叠卷面，增卷架/托辊，而非实心粗圆柱。','每头建立钳板、圆梳、顶梳、分离罗拉，剖视展示一头，其余保留壳。','集条台沿机长收集后引向输出端，不把四根线聚向任意中心点。'],
 'v1棉卷悬在裸台上，机身与前集条单元过于稀疏。')
row('roving','粗纱','Rieter F 40 / F 20',
 ['roving-photo-1.jpg','roving-photo-3.jpg'],
 '长机身远长于高度，封闭端车头大；锭翼和大粗纱卷装在下层，成列牵伸加压臂位于上层。',
 ['前侧长观察/防护罩覆盖锭翼区。','顶部导条架是一片密集纱路及托辊，不是粗纱筒架。','牵伸单元具有可抬起的加压臂和胶辊组件。'],
 ['保留后方熟条筒供料，导条架跨过其上并进入牵伸区。','每锭建立牵伸摇架、锭翼空心臂和压掌、筒管龙筋；卷装比细纱管粗。','增加长机身前护罩/透明窗、端部传动箱和升降同步机构。'],
 'v1虽有锭翼，但比例/喂入/加压臂不足，外形与细纱过于相同。')
row('winding','自动络筒','Rieter Autoconer X6',
 ['winding-photo-1.jpg','winding-photo-3.jpg'],
 '狭长单元阵列，筒子位于上部、管纱在下部；中间的络筒单元壳体明显高于筒子直径，端部控制台较宽。',
 ['每个锭位为独立有倾斜轮廓的设备单元，不是空背板上一个卷筒。','槽筒/筒子托架、吸嘴、清纱及张力路径占中间高度。','上部输送/落筒通道和下部管纱输送形成两条连续结构。'],
 ['构造重复的单元外壳、筒子托架、槽筒或导纱器。','下部加管纱托盘轨道，保持清纱器→接头→卷绕路径连续。','吸嘴采用弯管并与抽吸主管相接，端部设置封闭控制/风机区。'],
 'v1只表示筒子+管纱+小方块，未形成络筒单元的主体轮廓。')
row('warping','分批整经','KARL MAYER WARPDIRECT',
 ['warping-page-01.png'],
 '前方大经轴位于宽机头的下半部，上方透明/网式护罩倾斜覆盖经纱路径；后方筒子架向纵深延伸。',
 ['主机左右有封闭侧柜，经轴架为厚实双侧支承。','上部倾斜防护罩与横向分纱部件明确。','筒子架是两侧密集立柱阵列，中间留纱片汇集空间。'],
 ['扩大经轴挡盘和轴承支承，加入压纱辊/压力机构。','添加可拆倾斜防护罩与门缝，左右电控柜避免完全对称。','筒子架增加真实退绕朝向、张力器和逐级导纱眼，使纱线来源可追踪。'],
 'v1整经头过低，纱线从空中开始，后部筒子未与具体导纱器连接。')
row('sizing','浆纱','KARL MAYER PROSIZE',
 ['sizing-page-01.png'],
 '整线纵向很长，湿区/烘干区/卷绕机头形成不同大体量；前卷轴为宽幅低位，排湿罩在上方。',
 ['前方卷绕机头具有防护网门、两侧柜、多个导辊。','上方大排湿罩连接粗风管，后方是连续封闭机段。','经纱是密集平行片纱，远看可似布，但局部不应画经纬交织纹理。'],
 ['增加多经轴架、浆槽双轧点和独立烘筒区；外罩按功能分段。','烘筒按真实接触包角设置上下交错纱路，不能只从全部筒顶一条直线掠过。','增加排湿集气罩/风管、分纱棒与织轴双侧支承。','放大时显示分离纱线或纱片透明间隙，绝不能使用织物纹理。'],
 'v1浆槽、烘筒与织轴被压缩，烘筒包角和结构外罩/排湿系统不足。')
row('drawing_in','穿综穿筘','Stäubli SAFIR S80',
 ['drawing-in-whole.jpg'],
 '固定穿经头/机架明显高于低位长移动小车；设备外形是高头+长床，不能等同一个对称方形织机。',
 ['高门架内的穿经头在一端，长导轨/小车伸向侧面。','低位长梁承载织造组件并带支承/导轨。','独立控制台在侧，黄护栏界定行走区域。'],
 ['建立高穿经头与低长移动小车的非对称布局。','给综框、筘、停经片分开挂载托架，增加可识别穿经针头/定位滑轨。','小车轮/导轨/牵引机构须着地并有完整行走方向。'],
 'v1三个裸综框+经轴组合看起来像简化织机，未突出穿经头和移动床身。')
row('pretreatment','连续前处理','Benninger BEN-BLEACH',
 ['pretreatment-photo-2.jpg'],
 '工业线为多模块长线，汽蒸/反应段可高于洗槽并配维护楼梯；并非三只等高小水槽。',
 ['高反应箱表面有多列辊轴端盖/维护孔。','上下模块之间有支柱、楼梯、平台、栏杆。','低位洗槽、轧辊、进布架与独立电柜连接成线。'],
 ['至少区分浸渍/轧液、较高反应箱、后水洗模块。','导辊两端穿过侧壁并有轴承/密封，布在箱内呈连续折返。','添加循环泵与回路、过滤壳/阀、走台/楼梯；电机为泵或辊组服务。'],
 'v1三只相同白槽不能体现退煮漂反应/水洗设备的高度层次和辅助系统。')
row('dyeing','平幅浸轧染色','Benninger Küsters DyePad',
 ['dyeing-photo-3.jpg','dyeing-photo-1.png'],
 '双轧辊跨满幅宽，厚实左右机座托住轧辊；高进布架远高于轧点，浸液槽紧邻轧点下方。',
 ['上进布框架与多个宽导辊构成显著的高门式轮廓。','侧面电机/轴承装在明确机座上，下方可见液压/循环单元。','操作屏位于侧机座上方，真实软管弯曲接到辊端/阀块。'],
 ['浸轧段建立高进布架、双辊轧点、低液槽、双侧厚机座。','保留染液管路和循环泵，泵壳、联轴器、电机的连接要可见。','若选连续固色路线，另接汽蒸/水洗；若选CPB，接真实堆置卷装，不把两种流程拼成一个无说明设备。','染前与染后布颜色分段合理，布穿过液槽和轧点但不切穿辊体。'],
 'v1仅箱体+少量辊，缺高进布架、真实双轧辊机座与可识别循环单元。')
row('inspection','验布成卷','Uster EVS Fabriq Vision / Q-Bar 2',
 ['inspection-page-05.png','inspection-page-04.png'],
 '离线机器视觉检测为宽而高的封闭光学框架，底部导辊/布道较低；在线Q-Bar是低厚度横梁，不能混为同一安装形态。',
 ['Fabriq Vision为整幅宽封闭柜式光学框架，有连续门板与下方光带/导辊。','侧面有独立控制终端，线缆通过线槽进入机体。','Q-Bar直接跨在织口上方，支座固定到织机两侧。'],
 ['明确本节点用离线验布卷装：倾斜验布台/照明罩+前后卷绕，不把三相机悬空当检测系统。','为相机横梁和照明设置可遮光罩、调整支架、线槽；镜头指向布面。','补张力辊、计长轮、纠偏传感和带座轴承，收卷轴接减速驱动。'],
 'v1悬空相机和薄桌板过于简化，应有清楚光学检测腔和卷绕侧框。')

common=[
 '先完成整机轮廓和真实装配树，再加门缝/螺栓：长机身、厚承压架、连续箱体和功能独立模块优先。',
 '每个电机必须有受力支承；可见安装托架下方还必须连接到底座/机架，不能托架与电机一起悬空。',
 '驱动链要连续：电机轴→联轴器或传动带→减速箱/主轴→负载；所有轴承与轴同心。',
 '布/纱路径按圆柱切线和包角生成，禁止折线穿辊；实心侧箱不得堵住预定纱路/布路。',
 '圆柱端面使用平面法线、侧面平滑，倒角环使用合适加权法线；不得出现熔化状高光。',
 '管线采用弯曲半径、接头/法兰和夹持点，不做无支承直角悬空线。',
 '普通状态尽量保持工业防护罩，剖视/拆解模式选择性展示内部，避免所有设备都像裸骨架教具。',
 '相对比例均为照片中可见关系，不是实测尺寸。所有原始照片仅作参考与核对，不直接作为自制模型宣传图或贴图。'
]
data={'version':'2.0','reviewedAt':'2026-11-16','method':'已实际查看本地官方照片和pdftoppm渲染的PDF页；不以网页摘要代替视觉检查。','purpose':'按主流真实工业构型重建原创设备外形，非OEM尺寸复刻','priorityOrder':['calender','weaving','spinning','carding','stenter'],'commonRules':common,'stages':records}
(P/'visual-reference-v2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
lines=['# 第二版设备视觉参考与改模清单','核对日期：2026-11-16。全部16类已查看真实官方照片或PDF页面；相对比例是视觉关系，不是制造尺寸。','## 通用几何与装配规则']
lines += ['- '+s for s in common]
for s in records:
 lines += [f'## {s["name"]} · {s["id"]} · {s["priority"]}',f'参考：{s["reference"]}。',f'**相对比例：** {s["relativeProportion"]}','**已观察结构：**']
 lines += ['- '+x for x in s['observedAssembly']]
 lines += ['**改模动作：**']+['- '+x for x in s['modelChanges']]
 lines += ['**现有差异：** '+s['v1Gap'],'**已实际查看的视觉证据：**']
 lines += [f'- [官方图/样本页面]({e["sourceUrl"]}) · 本地检查图：`{e["localPath"]}`' for e in s['visualEvidence']]
(P/'visual-reference-v2.md').write_text('\n\n'.join(lines)+'\n')
assert len(records)==16 and len({r['id'] for r in records})==16
print('16 visual reference records written; all evidence files exist and checksummed')
