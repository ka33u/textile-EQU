export const fallbackData = {
  routeNotes: [
    '转杯纺从条子直接制成筒子纱，可接整经或供纬。粗纱、环锭细纱与管纱络筒属于另一条成纱路线。',
    '本图谱以棉纺环锭纱、机织物及匹染整理为主线，各工序以代表性设备说明材料变化。',
    '精梳为选配工艺：精梳路线需预并条、成卷准备、精梳及精梳后并条；普通梳棉纱可省略精梳。',
    '经纱经整经、浆纱和穿综穿筘进入织机；纬纱按纱线与织机要求准备，不经过经纱准备路线。',
    '前处理、染色及整理按纤维、组织和产品要求组合；轧光、烧毛、丝光与预缩等并非所有品种都需要。',
    '紧密纺是环锭细纱的替代分支，粗纱经紧密纺后进入络筒；不是环锭细纱之后追加的工序。',
    '倍捻属于并纱准备后的可选加捻路线；加弹属于化纤 POY 到 DTY 的独立路线，不接在棉纺主线末尾。',
    '拉幅设备兼有烘干与幅宽控制功能。全棉以干燥、幅宽调整及适用整理为主；热塑性纤维可按相应条件热定型，二者不能等同。',
    '模型版本、厂家参考与配置缺项见「型号与配置」；未公开内部结构保留待核实，运动为原理示意。'
  ],
  sources: [],
  stages: [
    ['opening','开清棉','OPENING','spinning','棉包','棉束','将棉包中的纤维逐步开松、混合并清除部分杂质。','开棉机组'],
    ['carding','梳棉','CARDING','spinning','棉束','生条','进一步梳理纤维、分离杂质，使纤维凝聚成连续棉条。','梳棉机'],
    ['drawing','并条','DRAWING','spinning','多根棉条','熟条','通过并合与牵伸改善条干均匀度，提高纤维平行度。','并条机'],
    ['combing','精梳','COMBING','spinning','精梳小卷','精梳条','在成卷准备后去除部分短纤维与棉结，提升纱线质量。','精梳机'],
    ['roving','粗纱','ROVING','spinning','熟条','粗纱','牵伸棉条并施加适量捻度，将其卷绕为粗纱。','粗纱机'],
    ['spinning','细纱','RING SPINNING','spinning','粗纱','管纱','进一步牵伸、加捻与卷绕，形成满足用途要求的细纱。','环锭细纱机'],
    ['winding','络筒','WINDING','spinning','管纱','筒子纱','清除部分纱疵，将纱线重新卷绕成适合后道的大卷装。','自动络筒机'],
    ['warping','整经','WARPING','weaving','筒子纱','经轴','按一定根数、长度与张力将经纱平行卷绕。','整经机'],
    ['sizing','浆纱','SIZING','weaving','经轴','织轴','在经纱上施加浆料，改善织造耐磨性并控制毛羽。','浆纱机'],
    ['drawing_in','穿综穿筘','DRAWING IN','weaving','织轴','上机经纱系统','按照组织要求将经纱穿过停经片、综眼和筘齿。','穿经工作站'],
    ['weaving','织造','WEAVING','weaving','经纱 ＋ 纬纱','坯布','经纬纱按织物组织交织，通过协调运动连续形成布面。','织机'],
    ['pretreatment','前处理','PRETREATMENT','finishing','坯布','待染布','通过退浆、煮练与漂白等适用工艺，为均匀染色准备布面。','连续前处理线'],
    ['dyeing','冷轧堆染色','COLD PAD-BATCH','finishing','待染布','堆置卷装（后洗另配）','选择 DyePad CPB：浸轧后卷装堆置，再独立水洗；不是连续汽蒸固色线。','冷轧堆染色单元'],
    ['stenter','拉幅热定型','STENTERING / HEAT SETTING','finishing','湿布 / 待整理织物','干燥、幅宽受控的整理织物','拉幅热定型兼具烘干功能；全棉主要进行干燥、幅宽调整及适用整理，热塑性纤维可按对应条件进行热定型。','拉幅热定型机（兼烘干）'],
    ['calender','轧光','CALENDERING','finishing','待整理布','表面整理布','通过辊隙压力及适当温度，调整织物表面光泽和手感。','轧光机'],
    ['inspection','织物疵点检测','FABRIC INSPECTION','finishing','整理织物','疵点与复核记录','参照 Fabriq Vision 2 检测系统、控制台和复核工作站；收放卷设备另行选配，不属于当前模型。','织物疵点检测系统'],
    ['compact_spinning','紧密纺','COMPACT SPINNING','yarn_processing','粗纱','紧密纺管纱','在环锭纺的牵伸后增加纤维集聚环节；这是细纱成纱方式的替代分支，后续可进入络筒。','紧密纺细纱机'],
    ['twisting','倍捻','TWO-FOR-ONE TWISTING','yarn_processing','并纱后的供纱卷装','加捻股线卷装','并纱机准备平行单纱卷装后，可进入倍捻工序生产股线。','倍捻机'],
    ['texturing','加弹','FALSE-TWIST TEXTURING','yarn_processing','化纤 POY','变形丝 DTY','以化纤预取向丝 POY 为原料，经适用的牵伸、加热、假捻与卷绕形成 DTY；这是独立于棉纺的路线。','假捻加弹机'],
    ['rotor_spinning','气流纺（转杯纺）','ROTOR SPINNING','yarn_processing','棉条','转杯纱筒子','棉条经分梳、气流输纤和转杯凝聚成纱后直接卷成筒子。','气流纺（转杯纺纱机）'],
    ['assembly_winding','并纱','ASSEMBLY WINDING','yarn_processing','单纱筒子','平行合股卷装','将两根或多根单纱平行卷成倍捻用喂入卷装。','并纱机'],
    ['airjet_spinning','喷气纺','AIR-JET SPINNING','yarn_processing','熟条','喷气纱筒子','牵伸纤维条，利用压缩空气在喷嘴内成纱，再卷成筒子。','喷气纺纱机'],
    ['warp_tying','自动结经','WARP TYING','weaving','新旧经片','已接续的经纱','沿用原穿法换轴时，逐根分离并连接新旧经纱。','自动结经机'],
    ['washing_range','平幅水洗与皂洗','OPEN-WIDTH WASHING','finishing','染后布','洗净布','连续处理染后布，洗除浮色并控制各段布面张力。','平幅水洗／皂洗线'],
    ['singeing','织物烧毛','FABRIC SINGEING','finishing','坯布','烧毛坯布','刷起布面毛羽后烧除，并牵引布幅通过灭火段。','织物烧毛机'],
    ['mercerizing','丝光','MERCERIZING','finishing','棉织物','丝光织物','浸渍后控制纵向张力与幅宽，随后稳定、洗去余碱。','丝光机'],
    ['sanforizing','橡毯预缩','COMPRESSIVE SHRINKING','finishing','待预缩织物','预缩织物','橡毯与热辊配合压缩织物，稳定整理后的缩水率。','橡毯预缩机']
  ].map(([id,name,en,section,input,output,summary,equipment])=>({id,name,en,section,input,output,summary,equipment,optional:['combing','calender','twisting'].includes(id),process:[summary],drive:['电机通过转轴、联轴器或传动机构驱动工艺执行部件。'],quality:['关注材料均匀性、张力与工艺一致性。'],sources:[]}))
};
export const equipmentNames = Object.fromEntries(fallbackData.stages.map(s=>[s.id,s.equipment]));

// These are process relationships, not a claim that the branches form one continuous line.
export const branchConnections = {
  compact_spinning:{code:'A',kind:'替代分支',cottonSpinning:true,label:'环锭细纱的替代方案',path:'粗纱 → 紧密纺 → 络筒',description:'紧密纺替代主线中的环锭细纱，随后进入络筒。',links:[{id:'roving',label:'查看粗纱'},{id:'spinning',label:'对照环锭细纱'},{id:'winding',label:'查看络筒'}]},
  twisting:{code:'B',kind:'选配分支',label:'并纱准备后的可选加捻',path:'单纱 → 并纱 → 倍捻 → 股线',description:'并纱工位准备多股平行卷装，倍捻工位施加捻度。',links:[{id:'assembly_winding',label:'查看上游并纱'},{id:'winding',label:'查看络筒'}]},
  texturing:{code:'C',kind:'独立路线',label:'化纤 POY → DTY',path:'POY → 牵伸 / 加热 / 假捻 → DTY',description:'属于化纤长丝加工，不串接到棉纺—机织—染整主线中。',links:[]},
  rotor_spinning:{code:'D',kind:'替代分支',cottonSpinning:true,label:'棉条直接成筒',path:'并条 → 转杯纺 → 筒子纱 → 整经或供纬',description:'纤维在高速转杯内凝聚成纱。已准备的条子直接喂入这台机器。',links:[{id:'drawing',label:'查看上游并条'},{id:'warping',label:'查看下游整经'},{id:'spinning',label:'对照环锭细纱'}]},
  assembly_winding:{code:'E',kind:'准备分支',label:'倍捻喂入卷装',path:'单纱筒子 → 并纱 → 倍捻',description:'各根单纱在同一卷装平行并合。',links:[{id:'winding',label:'单纱络筒'},{id:'twisting',label:'倍捻'}]},
  airjet_spinning:{code:'F',kind:'替代分支',cottonSpinning:true,label:'喷嘴气流成纱',path:'并条 → 喷气纺 → 筒子纱',description:'纤维牵伸后在喷嘴内形成包缠纱，并由卷绕单元成筒。',links:[{id:'drawing',label:'并条'},{id:'rotor_spinning',label:'对照转杯纺'},{id:'warping',label:'整经'}]},
  warp_tying:{code:'G',kind:'换轴分支',label:'沿用原穿法续接经轴',path:'新旧经片 → 结经 → 织造',description:'新旧经纱逐根对应打结，延用织机上的穿综穿筘关系。',links:[{id:'drawing_in',label:'对照穿经'},{id:'weaving',label:'织造'}]},
  washing_range:{code:'H',kind:'后洗分支',label:'染后洗除浮色',path:'冷轧堆固色 → 水洗／皂洗 → 整理',description:'各槽按品种组织水洗、热处理和挤液。',links:[{id:'dyeing',label:'冷轧堆染色'},{id:'stenter',label:'拉幅烘干'}]},
  singeing:{code:'I',kind:'选配分支',label:'坯布表面处理',path:'坯布 → 烧毛 → 湿前处理',description:'整理布面毛羽时，可在湿处理前配置烧毛设备。',links:[{id:'weaving',label:'查看坯布来源'},{id:'pretreatment',label:'湿前处理'}]},
  mercerizing:{code:'J',kind:'选配分支',label:'棉织物碱处理',path:'湿前处理 → 丝光 → 染整',description:'按织物品种选择碱处理和张力、幅宽条件。',links:[{id:'pretreatment',label:'前处理'},{id:'dyeing',label:'染色'}]},
  sanforizing:{code:'K',kind:'选配分支',label:'控制经向剩余缩水率',path:'整理布 → 橡毯预缩 → 成品检验',description:'按成品尺寸稳定性要求配置预缩。',links:[{id:'stenter',label:'拉幅整理'},{id:'inspection',label:'成品检验'}]}
};
