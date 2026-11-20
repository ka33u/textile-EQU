import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { fallbackData, equipmentNames, branchConnections } from './ui-data.js?v=20261119-stations';
import { fitPerspectiveBounds } from './camera-fit.js?v=20261118-v6-motion';
import { normalizeImportedModel, worldModelBounds } from './scene-geometry.js?v=20261118-render';

import { DriveView, driveObjectContext, driveRoutePoints, exteriorDriveDirection, scopeDriveRoute } from './drive-view.js?v=20261120-models';
import { TexturingMotion, TEXTURING_PHASES } from './texturing-motion.js?v=20261119-stations';
import { ModelMaterials, ModelBatches, PICK_LAYER } from './model-rendering.js?v=20261118-render';

import { RotorMotion } from './rotor-motion.js?v=20261118-rotor';
import { StationMotion } from './station-motion.js?v=20261120-ring';

import { StationYarn } from './station-yarn.js?v=20261120-models';
import { ModelPicker, machineHash, parseMachineHash } from './model-library.js?v=20261120-models';

const ASSET_VERSION = '20261118-v6-motion';
const $ = (id) => document.getElementById(id);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { data: fallbackData, provenance: null, driveData: null, driveError: false, loadedIdentity: null, library: null, variant: null, variantDetails: null, current: 'weaving', mode: 'machine', filter: 'all', playing: false, rotating: false, xray: false, wire: false, explode: 0, autoFit: true, loaded: false, request: 0 };
const sections = { spinning: {name:'棉纺',en:'SPINNING',index:'01'}, weaving: {name:'机织',en:'WEAVING',index:'02'}, finishing: {name:'染整',en:'FINISHING',index:'03'}, yarn_processing: {name:'纺纱与纱线加工',en:'SPINNING & YARN PROCESSING',index:'分支'} };
let scene, camera, renderer, controls, content, modelRoot, selectedObject, floor, grid;
let meshes = [], exploded = [], spinning = [], selectable = [];
let partGroups = new Map(), selectedPartIndex = -1;
let activeRecord=null,modelBatches=null,loadController=null,batchTransformsDirty=false,lastBatchTime=0;
const recentModels=new Map();
let driveView, driveHighlights = new Set();
let rotorMotion=null;
let stationMotion=null,stationYarn=null;
let texturingMotion = null, playbackTime = 0, lastMotionReadout = -Infinity;
const texturing = { mode:'process', speed:1, yarnMode:'single', side:'A', position:1, motorId:null, focusYarn:false };
let yarnFocusObjects=new Set();
const texturingMotors = [
  {id:'EFK_friction_drive_A',code:'M1',side:'A',route:'false_twist',name:'A 侧假捻电机',scope:'16 段切向带 → 192 假捻单元',detail:'带动 A 侧 16 节中的 192 个摩擦假捻单元，共 576 根摩擦盘轴。'},
  {id:'EFK_friction_drive_B',code:'M2',side:'B',route:'false_twist',name:'B 侧假捻电机',scope:'16 段切向带 → 192 假捻单元',detail:'带动 B 侧 16 节中的 192 个摩擦假捻单元，共 576 根摩擦盘轴。'},
  {id:'EFK_W3_drive_A',code:'M3',side:'A',route:'w3',name:'A 侧 W3 喂纱电机',scope:'16 段共轴喂纱 → 192 纱位',detail:'带动 A 侧 16 段 W3 喂纱轴；每段对应 12 个纱位，合计 192 个。'},
  {id:'EFK_W3_drive_B',code:'M4',side:'B',route:'w3',name:'B 侧 W3 喂纱电机',scope:'16 段共轴喂纱 → 192 纱位',detail:'带动 B 侧 16 段 W3 喂纱轴；每段对应 12 个纱位，合计 192 个。'},
  {id:'EFK_camshaft_drive_A',code:'M5',side:'A',route:'camshaft_traverse',name:'A 侧横动 / 卷绕电机',scope:'48 段凸轮轴 → 192 横动及卷绕位',detail:'关联 A 侧 48 段分层凸轮轴、192 个横动导丝器，以及 192 个接触辊和 DTY 卷装。卷绕内部分配待核实。'},
  {id:'EFK_camshaft_drive_B',code:'M6',side:'B',route:'camshaft_traverse',name:'B 侧横动 / 卷绕电机',scope:'48 段凸轮轴 → 192 横动及卷绕位',detail:'关联 B 侧 48 段分层凸轮轴、192 个横动导丝器，以及 192 个接触辊和 DTY 卷装。卷绕内部分配待核实。'},
  {id:'EFK_oil_circulation_drive',code:'M7',side:null,route:'oiling',name:'油剂循环泵电机',scope:'两侧供油管 → 384 上油接触位',detail:'为两侧油剂管和 384 个上油接触位提供流体循环；这里不将它解释为油轮旋转驱动。泵内机构尚未建模。'}
];
let initialized = false, resizeObserver, animationHandle, frameDirty = true;
const motionEnvelope = new THREE.Box3();
const geometryBounds = new THREE.Box3();
let boundsDirty = true;
let explosionPending=false;
const explosionVector=new THREE.Vector3();
let lastTime = performance.now();
const loader = new GLTFLoader();
const raycaster = new THREE.Raycaster();
raycaster.layers.enable(PICK_LAYER);
const pointer = new THREE.Vector2();
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const motionSpeed = reduceMotion ? .55 : 1;
const escapeHTML = (value) => String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const toArray = (value) => Array.isArray(value) ? value : value ? [value] : [];
const stage = () => state.data.stages.find(item=>item.id===state.current) || state.data.stages[0];
const modelID = () => state.variant || state.current;
const selectedVariant = () => state.variant ? state.library?.models.find(item=>item.stageId===state.current&&item.id===state.variant) : null;
const preferredModels = new Map();
const picker = new ModelPicker(choice=>selectMachine(choice.stageId, choice.id===choice.stageId ? null : choice.id), async()=>{
  if(await getModelLibrary() && state.variant && !state.loaded)await loadModel();
});
async function getModelLibrary(){
  try{
    const response=await fetch('./model-variants.json?v=20261120-models',{cache:'no-store'});
    if(!response.ok)throw new Error('Model catalog HTTP '+response.status);
    const library=await response.json();
    if(!Array.isArray(library.models)||!Array.isArray(library.makers)||!library.models.length)throw new Error('Invalid model catalog');
    state.library=library;picker.setCatalog(library);renderNavigation();renderDetails();
    return true;
  }catch(error){picker.unavailable();console.warn('Model catalog unavailable:',error.message);return false}
}
const stageCode = item => branchConnections[item.id]?.code||String(state.data.stages.filter(s=>!branchConnections[s.id]).indexOf(item)+1).padStart(2,'0');
const stageLabel = item => item.id==='stenter'?'拉幅热定型':item.name;
function modelAssetURL(){
  const variant=selectedVariant();
  if(state.variant)return variant?'./assets/variants/'+variant.id+'.glb?sha='+variant.sha256.slice(0,16)+'&record='+variant.detailHash.slice(0,12):'';
  const id=state.current,sha=state.provenance?.assets?.[id]?.sha256;
  return './assets/models/'+id+'.glb?v='+ASSET_VERSION+(sha?'&sha='+sha.slice(0,16):'');
}
const normalizeSource = (item) => typeof item==='string'?{title:item,url:item}:item;
const isSafeURL = (value) => { try { const url=new URL(value); return ['https:','http:'].includes(url.protocol); } catch { return false; } };
function sourceLink(source, full=false){
  const item=normalizeSource(source);
  if(!isSafeURL(item.url)) return '';
  const host=new URL(item.url).hostname.replace(/^www\./,'');
  return `<a href="${escapeHTML(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(item.title||item.name||host)} ↗${full?`<small>${escapeHTML(host)}</small>`:''}</a>`;
}

async function getProvenance(){
  try {
    const response=await fetch(`./equipment-provenance.json?v=${ASSET_VERSION}`,{cache:'no-store'});
    if(!response.ok)throw new Error('Equipment provenance unavailable');
    const data=await response.json();
    if(!Array.isArray(data.items))throw new Error('Invalid equipment provenance');
    state.provenance=data;
  } catch(error){console.warn('Equipment provenance unavailable:',error.message)}
  renderProvenance();
}
function readModelIdentity(root){
  // Scene extras or the shallowest assembly root owns identity, never an embedded drive motor.
  const queue=[root];
  for(let i=0;i<queue.length;i++){
    const node=queue[i],data=node.userData||{};
    if(data.modelVersion!==undefined||data.referenceModel){
      return Object.fromEntries(['modelVersion','modelType','referenceManufacturer','referenceModel','referenceConfiguration','fidelityStatus','referenceStatus','structuralCompleteness','equipmentId','actualScope','unresolved','stationDriveModel','driveRevision','stageId','makerKey'].filter(key=>data[key]!==undefined).map(key=>[key,data[key]]));
    }
    queue.push(...node.children);
  }
  return {};
}
function resolveModelIdentity(metadata,item){
  const version=String(metadata?.modelVersion||'');
  const hasReference=Number.parseFloat(version)>=3&&typeof metadata?.referenceModel==='string'&&metadata.referenceModel.trim().length>0;
  return {
    version:metadata?.stationDriveModel&&metadata.driveRevision?`传动模型 v${metadata.driveRevision}`:version?`v${version}`:'版本未标注',
    model:hasReference?metadata.referenceModel:'结构教学模型',
    manufacturer:hasReference?String(metadata.referenceManufacturer||''):'',
    configuration:hasReference?String(metadata.referenceConfiguration||'模型未记录具体配置'):null,
    scope:hasReference?String(metadata.actualScope||metadata.unresolved||''):'',
    previousReference:hasReference?'':item?.previousReference||'原始参考资料未载入',
    // Model metadata establishes identity; public-reference geometry is not certified full OEM CAD.
    status:hasReference?'型号参考 · 结构待核实':'教学结构 · 型号未绑定',
    hasReference
  };
}
const provenanceItem=()=>state.variant?state.variantDetails?.provenance:state.provenance?.items.find(item=>item.id===state.current);
function equipmentDisplay(){
  if(state.variant){
    const choice=selectedVariant();
    const name=choice?.equipment||stage().name;
    const title=choice&&!name.toLowerCase().includes(choice.model.toLowerCase())?choice.model+' · '+name:name;
    return {title,subtitle:choice?[choice.makerLabel,choice.model,choice.scope==='station'?'公开工位模型':''].filter(Boolean).join(' · '):'正在核对机型'};
  }
  const metadata=state.loadedIdentity?.id===modelID()?state.loadedIdentity.metadata:null;
  if(Number.parseFloat(metadata?.modelVersion)>=3){
    if(state.current==='inspection'&&/Fabriq Vision 2/i.test(metadata.referenceModel||''))return {title:'织物疵点检测系统',subtitle:'检测单元 · 控制台 · 复核工作站'};
    if(state.current==='dyeing'&&/DyePad.*CPB/i.test(metadata.referenceModel||''))return {title:'冷轧堆染色单元',subtitle:'浸轧 · 卷装堆置 · 后洗独立配置'};
  }
  if(metadata&&Number.parseFloat(metadata.modelVersion)<3){
    if(state.current==='inspection')return {title:'验布卷布机 · 旧版',subtitle:'v2 教学结构 / 当前检测系统参照见型号资料'};
    if(state.current==='dyeing')return {title:'平幅浸轧染色线 · 旧版',subtitle:'v2 教学结构 / 当前 CPB 参照见型号资料'};
  }
  const item=stage();
  if(item.id==='stenter')return {title:'拉幅热定型机（兼烘干）',subtitle:'全棉：干燥与整理 · 热塑纤维：适用条件下热定型'};
  if(branchConnections[item.id])return {title:equipmentNames[item.id]||item.equipment||item.name,subtitle:branchConnections[item.id].label};
  return {title:equipmentNames[item.id]||item.equipment||item.name,subtitle:item.id==='weaving'?'送经 · 开口 · 引纬 · 打纬 · 卷取':item.optional?'选配工序 / 代表性设备结构':'工艺结构 / 代表性设备'};
}
function evidenceText(value){
  if(value===null||value===undefined)return '待确认';
  if(typeof value==='string'||typeof value==='number'||typeof value==='boolean')return String(value);
  if(Array.isArray(value))return value.map(evidenceText).join('；');
  return value.text||value.description||value.summary||value.detail||Object.entries(value).map(([key,item])=>`${key}：${evidenceText(item)}`).join('；');
}
function evidenceList(values,empty='暂无已确认记录'){
  const items=toArray(values);
  return items.length?`<ul>${items.map(value=>`<li>${escapeHTML(evidenceText(value))}</li>`).join('')}</ul>`:`<p class="evidence-empty">${escapeHTML(empty)}</p>`;
}
function renderProvenance(){
  const item=provenanceItem(),loaded=state.loadedIdentity?.id===modelID()?state.loadedIdentity:null;
  const identity=loaded?resolveModelIdentity(loaded.metadata,item):null;
  $('provenance-loaded-version').textContent=identity?`当前载入 / ${identity.version}`:'当前模型 / 载入后核对';
  $('provenance-actual-model').textContent=identity?[identity.manufacturer,identity.model].filter(Boolean).join(' · '):'正在读取模型身份';
  $('provenance-status').textContent=identity?.status||'等待模型';
  $('provenance-target-model').textContent=item?[item.referenceManufacturer,item.referenceModel].filter(Boolean).join(' · '):'资料暂未载入，可继续观察模型';
  if($('provenance-dialog').open)renderProvenanceDialog();
}
function renderProvenanceDialog(){
  const item=provenanceItem(),loaded=state.loadedIdentity?.id===modelID()?state.loadedIdentity:null;
  const identity=loaded?resolveModelIdentity(loaded.metadata,item):null;
  $('provenance-dialog-title').textContent=`${equipmentDisplay().title} · 型号与配置`;
  let html='<section class="provenance-identity"><span class="provenance-caption">当前实际载入的模型</span>';
  html+=identity?`<h3>${escapeHTML([identity.manufacturer,identity.model].filter(Boolean).join(' · '))}</h3><div class="provenance-meta"><span>${escapeHTML(identity.version)}</span><span class="evidence-badge">${escapeHTML(identity.status)}</span></div>${identity.hasReference?`<p>${escapeHTML(identity.configuration)}</p>`:`<p>原参考：${escapeHTML(identity.previousReference)}</p><p class="evidence-empty">此文件尚未绑定下方当前型号。资料更新不会改变已载入模型的身份。</p>`}`:'<p>模型尚未载入，身份将在 GLB 读取完成后显示。</p>';
  if(identity?.scope)html+=`<p class="evidence-empty">模型范围与待核实：${escapeHTML(identity.scope)}</p>`;
  html+='</section>';
  if(!item){
    html+='<p>设备来源文件暂未载入。可重新打开页面读取资料，工艺来源仍可在「研究与资料」中查看。</p>';
  } else {
    html+=`<section class="provenance-section"><span class="provenance-caption">厂家资料对照 / ${escapeHTML(item.checkedAt||state.provenance?.checkedAt||'核查日期未标注')}</span><h3>${escapeHTML(item.referenceManufacturer)} · ${escapeHTML(item.referenceModel)}</h3><p>${escapeHTML(item.currentFinding||'')}</p><dl class="configuration-facts"><div><dt>所选配置</dt><dd>${escapeHTML(item.referenceConfiguration||'待确认')}</dd></div><div><dt>配置依据</dt><dd>${escapeHTML(item.configurationStatus||'待核实')}</dd></div>${item.referenceYear?`<div><dt>参考代次</dt><dd>${escapeHTML(item.referenceYear)} · 不是文件下载年份</dd></div>`:''}</dl>${item.generationAssessment&&item.generationAssessment.trim()!==(item.currentFinding||'').trim()?`<p class="evidence-empty">${escapeHTML(item.generationAssessment)}</p>`:''}</section>`;
    const counts=Object.entries(item.selectedCounts||{});
    if(counts.length)html+=`<section class="provenance-section"><h3>所选数量与尺寸</h3><p class="evidence-empty">各项依据与推定范围见下方记录；选定数量不等于厂家完整订单证明。</p><dl class="configuration-facts">${counts.map(([key,value])=>`<div><dt>${escapeHTML(item.selectedCountLabels?.[key]||key)}</dt><dd>${escapeHTML(evidenceText(value))}</dd></div>`).join('')}</dl></section>`;
    for(const section of toArray(item.configurationSections))html+=`<section class="provenance-section"><h3>${escapeHTML(section.title||'配置明细')}</h3>${evidenceList(section.rows||section.items||section.notes)}</section>`;
    html+=`<section class="provenance-section"><h3><span class="evidence-dot confirmed"></span>资料已确认</h3>${evidenceList(item.verified,'当前仅完成型号核查，详细配置依据待补充。')}</section>`;
    if(toArray(item.inferred).length)html+=`<section class="provenance-section"><h3><span class="evidence-dot selected"></span>建模选定 / 尚非实装证明</h3>${evidenceList(item.inferred)}</section>`;
    html+=`<section class="provenance-section"><h3><span class="evidence-dot pending"></span>结构待核实</h3>${evidenceList(item.missing,'尚未取得完整装配清单，结构完整性待核实。')}</section>`;
    if(toArray(item.sourceConflicts).length)html+=`<details class="evidence-differences"><summary>代次与配置差异</summary>${evidenceList(item.sourceConflicts)}</details>`;
    html+=`<section class="provenance-section"><h3>型号与配置资料</h3><div class="provenance-sources">${toArray(item.sources).map(source=>{const normalized=normalizeSource(source),date=normalized.publicationDate||normalized.publishedDate;return `<div>${sourceLink(normalized,true)}${date?`<span class="source-date">资料日期 ${escapeHTML(date)}</span>`:''}${toArray(normalized.printedPages).length?`<span class="source-date">印刷页码 ${escapeHTML(normalized.printedPages.join('、'))}</span>`:''}${normalized.supports&&normalized.supports.trim()!==(normalized.title||normalized.name||'').trim()?`<p>${escapeHTML(normalized.supports)}</p>`:''}</div>`}).join('')}</div></section>`;
  }
  html+='<p class="technical-credit">型号参考用于逐项核对结构；运动展示为原理示意。传动路径按工位证据展示，功能连线不代表精确机械轴线或传动比。</p>';
  $('provenance-dialog-content').innerHTML=html;
}

function mergeProcessData(data){
  if(!Array.isArray(data.stages)||!data.stages.length||data.stages.some(item=>!item.id)||new Set(data.stages.map(item=>item.id)).size!==data.stages.length)throw new Error('Invalid process data');
  const incoming=new Map(data.stages.map(item=>[item.id,item]));
  const stages=fallbackData.stages.map(fallback=>({...fallback,...incoming.get(fallback.id),section:incoming.get(fallback.id)?.section||incoming.get(fallback.id)?.group||fallback.section}));
  for(const item of data.stages)if(!stages.some(stage=>stage.id===item.id))stages.push({...item,section:item.section||item.group||'yarn_processing'});
  return {...fallbackData,...data,stages,routeNotes:[...new Set([...toArray(data.routeNotes||data.notes),...fallbackData.routeNotes])]};
}
async function getData(){
  try {
    const response = await fetch(`./process-data.json?v=${ASSET_VERSION}`,{cache:'no-store'});
    if(!response.ok) throw new Error('Research data unavailable');
    state.data=mergeProcessData(await response.json());
  } catch(error) { console.warn('Using bundled process overview:',error.message); }
  renderNavigation(); renderDetails(); renderSources();
}
function bindRelatedStageLinks(id){
  $$(`#${id} [data-related-stage]`).forEach(button=>button.addEventListener('click',()=>selectStage(button.dataset.relatedStage)));
}
function renderBranchMap(){
  $('branch-map-content').innerHTML='<p>棉纺 → 机织 → 染整为主线，各工序仍按品种选配。</p>'+Object.entries(branchConnections).map(([id,branch])=>`<button data-related-stage="${id}"><b>${branch.code} · ${escapeHTML(branch.kind)}</b><strong>${escapeHTML(stageLabel(state.data.stages.find(item=>item.id===id)))}</strong><small>${escapeHTML(branch.path)}</small></button>`).join('');
  bindRelatedStageLinks('branch-map-content');
}
function matchesProcessFilter(item,filter){
  return filter==='all'||item.section===filter||(filter==='spinning'&&branchConnections[item.id]?.cottonSpinning);
}
function renderNavigation(){
  const items=state.data.stages,branchCount=items.filter(item=>branchConnections[item.id]).length;
  $('equipment-count').textContent=items.length;
  $('equipment-count-note').textContent=state.library?state.library.models.length+' 款机型 · '+state.library.makers.length+' 家厂商':`${items.length-branchCount} 主线 · ${branchCount} 分支`;
  let html='';
  for(const [key,group] of Object.entries(sections)){
    const cottonBranches=state.filter==='spinning'&&key==='yarn_processing';
    const visibleItems=items.filter(item=>item.section===key&&matchesProcessFilter(item,state.filter));
    if(!visibleItems.length)continue;
    html+=`<div class="stage-group-label${key==='yarn_processing'?' branch-group-label':''}">${group.index} / ${cottonBranches?'替代成纱工艺':group.name}</div>`;
    html+=visibleItems.map(item=>{
      const branch=branchConnections[item.id];
      const modelCount=state.library?.models.filter(machine=>machine.stageId===item.id).length||0;
      return `<button class="stage-button${item.id===state.current?' active':''}${branch?' branch-stage':''}" data-stage="${item.id}" aria-current="${item.id===state.current?'step':'false'}"><span class="stage-number">${stageCode(item)}</span><span class="stage-name">${escapeHTML(stageLabel(item))}</span>${modelCount>1?`<span class="stage-models">${modelCount}款</span>`:branch?`<span class="stage-optional branch-kind">${escapeHTML(branch.kind.replace('分支',''))}</span>`:item.optional?'<span class="stage-optional">选配</span>':''}</button>`;
    }).join('');
  }
  $('stage-list').innerHTML=html;
  $$('#stage-list [data-stage]').forEach(button=>button.addEventListener('click',()=>selectStage(button.dataset.stage)));
  $$('[data-filter]').forEach(button=>{const active=button.dataset.filter===state.filter;button.classList.toggle('active',active);button.setAttribute('aria-pressed',active)});
  renderBranchMap();
}
function renderRouteContext(item){
  const branch=branchConnections[item.id];
  let title='棉纺—机织—染整主线',description='按品种与用途组合工序；系统中的设备并非全部必经。',links=[];
  if(branch){title=`${branch.code} · ${branch.kind} / ${branch.label}`;description=`${branch.path}。${branch.description}`;links=branch.links}
  else if(item.id==='drawing'){description='准备好的条子可进入粗纱、转杯纺或喷气纺路线。';links=[{id:'roving',label:'粗纱'},{id:'rotor_spinning',label:'转杯纺'},{id:'airjet_spinning',label:'喷气纺'}]}
  else if(item.id==='spinning'){description='主线采用环锭细纱；也可选择紧密纺替代本工序，然后进入络筒。';links=[{id:'compact_spinning',label:'查看紧密纺替代分支'},{id:'rotor_spinning',label:'对照转杯纺'}]}
  else if(item.id==='winding'){description='生产股线时，单纱筒子先经过并纱，再进入倍捻。';links=[{id:'assembly_winding',label:'并纱机'},{id:'twisting',label:'倍捻机'}]}
  else if(item.id==='dyeing'){description='冷轧堆布卷堆置固色后，接独立平幅水洗／皂洗线。';links=[{id:'washing_range',label:'染后水洗'}]}
  else if(item.id==='drawing_in'){description='新品种可重新穿经。沿用原穿法换轴时也可结经接续。';links=[{id:'warp_tying',label:'换轴结经'}]}
  else if(item.id==='pretreatment'){description='按布面及染色要求组合烧毛、湿前处理与丝光。';links=[{id:'singeing',label:'烧毛'},{id:'mercerizing',label:'丝光'}]}
  else if(item.id==='stenter'){title='拉幅热定型 · 兼具烘干功能';description='全棉主要进行干燥、幅宽调整与适用整理；热塑性纤维可在相应工艺条件下热定型。二者作用不同，不将全棉烘干等同于热塑性热定型。'}
  $('route-context').classList.toggle('is-branch',!!branch);
  $('route-context').innerHTML=`<strong>${escapeHTML(title)}</strong><p>${escapeHTML(description)}</p>${links.length?`<div>${links.map(link=>`<button data-related-stage="${link.id}">${escapeHTML(link.label)} ↗</button>`).join('')}</div>`:''}`;
  bindRelatedStageLinks('route-context');
}
let motorCatalog = null;
async function loadMotorCatalog() {
  try {
    const response = await fetch('./motor-applications.json', {cache:'no-store'});
    if (!response.ok) return;
    const data = await response.json();
    if (!Array.isArray(data.stages) || !data.sources) return;
    motorCatalog = data;
    renderMotorExamples(stage().id);
  } catch (error) {
    console.warn('Motor application catalog unavailable:', error.message);
  }
}
function renderMotorExamples(id) {
  const choice=selectedVariant();
  $('stage-motor-study').href = './motor-applications.html'+(choice?'?model='+encodeURIComponent(choice.id):'')+'#' + id;
  const panel = $('study-examples');
  if (panel.dataset.stage !== modelID()) panel.open = false;
  panel.dataset.stage = modelID();
  const group = motorCatalog?.stages.find(item => item.id === id);
  const rows=(group?.rows||[]).filter(row=>state.variant?row.modelAssetId===state.variant:!row.modelAssetId);
  panel.hidden = !rows.length;
  if (!rows.length) { $('study-rows').replaceChildren(); return; }
  $('study-example-count').textContent = (choice?'本机工位记录':'厂家工位实例')+'（' + rows.length + '）';
  $('study-rows').innerHTML = rows.map(row => {
    const links = row.refs.map(key => sourceLink(motorCatalog.sources[key])).join('');
    return '<article><strong>' + escapeHTML(row.station) + '</strong><small>'
      + escapeHTML(row.maker + ' · ' + row.model + ' · ' + row.level) + '</small><p>'
      + escapeHTML(row.path) + '</p><p>' + escapeHTML(row.electric) + '</p><div>'
      + links + '</div></article>';
  }).join('');
}
function renderDetails(){
  const item=stage(),index=state.data.stages.indexOf(item),section=sections[item.section]||sections.yarn_processing;
  $('detail-title').textContent=stageLabel(item);
  picker.refresh(state.current,modelID());
  const choice=selectedVariant(),variantInfo=state.variantDetails;
  const currentModel=choice||state.library?.models.find(model=>model.id===modelID());
  $('machine-dating').textContent=choice ? choice.dating+' · 资料核查 '+choice.checkedAt : '';
  $('machine-dating').hidden=!choice;
  $('detail-title').textContent=currentModel?.scope==='station'?item.name+' · 公开工位':stageLabel(item);
  const description=state.variant ? (variantInfo?.process||{}) : item;
  $('detail-summary').textContent=description.summary||(choice?choice.configuration:'正在读取本机型的资料');
  $('detail-section').textContent=`${section.index} / ${section.name}`;
  $('detail-index').textContent=`设备 ${index+1} / ${state.data.stages.length}`;
  renderRouteContext(item);
  renderMotorExamples(item.id);
  $('input-material').textContent=toArray(description.input).join(' / ')||'—';
  $('output-material').textContent=toArray(description.output).join(' / ')||'—';
  const points=state.variant?{...description,drive:variantInfo?.drive.routes.map(r=>r.location+' · '+r.electric)}:item;
  ['process','drive','quality'].forEach(key=>$(key+'-list').innerHTML=toArray(points[key]).map(text=>`<li>${escapeHTML(typeof text==='object'?(text.text||text.description||JSON.stringify(text)):text)}</li>`).join(''));
  $('stage-note').textContent=state.variant?'':item.note||'';
  $('stage-note').hidden=!$('stage-note').textContent;
  $('stage-sources').innerHTML=toArray(state.variant?variantInfo?.provenance.sources:item.sources).map(source=>sourceLink(source)).join('');
  $('prev-stage').disabled=index===0;
  $('next-stage').disabled=index===state.data.stages.length-1;
  updateViewerLabels();
}
function updateViewerLabels(){
  const item=stage(),drive=state.mode==='drive',scope=selectedVariant()?.scope;
  const driveTitle=scope==='station'?'工位传动链':'整机传动链';
  $('drive-panel-title').textContent=driveTitle;
  $('stage-code').textContent=drive?'DRIVE MAP / '+driveTitle:`${branchConnections[item.id]?'BRANCH ':''}${stageCode(item)} / ${item.en||item.id.toUpperCase()}`;
  const display=equipmentDisplay();
  $('viewer-title').textContent=display.title;
  $('viewer-subtitle').textContent=drive?'点击编号工位 · 追踪动力到工作机构':display.subtitle;
  if(modelAssetURL())$('download-model').href=modelAssetURL();else $('download-model').removeAttribute('href');
  $('download-model').download=`textile-${modelID()}.glb`;
  $('download-model').setAttribute('aria-disabled',String(!state.loaded));
  $$('[data-mode]').forEach(button=>{const active=button.dataset.mode===state.mode;button.classList.toggle('active',active);button.setAttribute('aria-pressed',active)});
  renderProvenance();renderDrivePanel();
}
function renderSources(){
  const audit=state.data.coverageReview,section=$('coverage-review');
  section.hidden=!audit;
  if(audit)section.innerHTML='<h3>设备覆盖核查</h3><p>'+escapeHTML(audit.finding)+'</p><ul>'+toArray(audit.modeled).map(item=>
    '<li><a href="#'+escapeHTML(item.id)+'/drive" data-covered-machine="'+escapeHTML(item.id)+'">'+escapeHTML(item.name)+'</a> · '+escapeHTML(item.position)+'<br>'+escapeHTML(item.reason)+'</li>').join('')+toArray(audit.candidates).map(item=>
    `<li><strong>${escapeHTML(item.name)}</strong> · ${escapeHTML(item.position)}<br>${escapeHTML(item.reason)} ${sourceLink(item.source)}</li>`).join('')+
    '</ul><h4>已包含在现有模型中</h4>'+evidenceList(audit.covered);
  section.querySelectorAll('[data-covered-machine]').forEach(link=>link.addEventListener('click',()=>$('research-dialog').close()));
  const notes=state.data.routeNotes||state.data.notes||fallbackData.routeNotes;
  $('route-notes').innerHTML=toArray(notes).map(n=>`<li>${escapeHTML(typeof n==='string'?n:n.text||n.description||'')}</li>`).join('');
  const raw=[...toArray(state.data.sources),...state.data.stages.flatMap(s=>toArray(s.sources))];
  const seen=new Set();
  const sources=raw.map(normalizeSource).filter(s=>s&&s.url&&!seen.has(s.url)&&seen.add(s.url));
  $('all-sources').innerHTML=sources.map(s=>sourceLink(s,true)).join('')||'<p>工序说明已随页面提供，完整来源将在资料文件载入后显示。</p>';
}
async function selectMachine(id,variant=null,{mode=state.mode,navigate=true}={}){
  if(!state.data.stages.some(stage=>stage.id===id))return;
  const changed=state.current!==id||state.variant!==variant;
  if(!changed&&state.mode===mode&&state.loaded)return;
  state.current=id;state.variant=variant;state.mode=mode;
  if(changed){state.loaded=false;state.variantDetails=null;state.loadedIdentity=null}
  if(!variant||selectedVariant())preferredModels.set(id,variant);
  if(!matchesProcessFilter(stage(),state.filter))state.filter='all';
  const hash=machineHash(id,variant,mode);
  if(navigate&&location.hash!==hash)history.pushState(null,'',hash);
  renderNavigation();renderDetails();
  if(changed||!state.loaded)await loadModel();else syncDriveMode();
}
function selectStage(id){return selectMachine(id,preferredModels.get(id)||null)}
function selectMode(mode){
  return selectMachine(state.current,state.variant,{mode:mode==='drive'||mode==='motor'?'drive':'machine'});
}

const currentDriveData=()=>state.variant?state.variantDetails?.drive:state.driveData?.items.find(item=>item.id===state.current);
async function getDriveData(){
  try {
    state.driveError=false;
    const response=await fetch(`./drive-chains.json?v=${ASSET_VERSION}`,{cache:'no-store'});
    if(!response.ok)throw new Error('Drive routes unavailable');
    const data=await response.json();
    if(!Array.isArray(data.items))throw new Error('Invalid drive routes');
    state.driveData=data;
    if(state.loaded&&modelRoot&&!state.variant){
      driveView?.setModel(modelRoot,currentDriveData());
      stationMotion?.setRoutes(driveView.routes);
      if(texturingMotion){
        modelBatches?.dispose();modelBatches=null;
        texturingMotion.dispose();texturingMotion=null;initializeTexturing();prepareBatches();
      }
    }
  } catch(error){state.driveError=true;console.warn('Drive routes unavailable:',error.message)}
  syncDriveMode();
}
function syncDriveMode(){
  const active=state.mode==='drive';
  driveView?.setVisible(active&&state.loaded);
  rotorMotion?.select(active?driveView.selectedRoute():null);
  stationMotion?.select(active&&driveView.selectedRoute()?driveView.selectedMotorRoutes():null);
  syncStationYarn();
  driveHighlights=active&&state.loaded?driveView?.highlightedObjects()||new Set():new Set();
  syncTexturingMotion();
  if(active&&texturingMotion)for(const object of texturingMotion.highlightedObjects())driveHighlights.add(object);
  applyMaterials();renderDrivePanel();invalidateFrame();
}
function renderDrivePanel(){
  const active=state.mode==='drive';
  $('drive-toolbar').hidden=!active;$('drive-panel').hidden=!active;
  if(!active)return;
  const data=currentDriveData(),routes=state.loaded?driveView?.routes||[]:[],selected=driveView?.selectedRoute();
  $('drive-summary').textContent=data?.summary||(state.driveError?'传动资料暂未载入。仍可查看整机并选择部件。':'正在读取本设备的驱动工位');
  $('drive-evidence-note').textContent=data?.evidenceNote||'功能路径用于说明动力流向，隐藏机构仍需厂家资料核实。';
  $('drive-route-select').innerHTML='<option value="">全部工位</option>'+routes.map(route=>`<option value="${escapeHTML(route.id)}">${String(route.index+1).padStart(2,'0')} · ${escapeHTML(route.label)}</option>`).join('');
  $('drive-route-select').value=selected?.id||'';$('drive-route-select').disabled=!routes.length;
  $('drive-show-all').setAttribute('aria-pressed',String(!selected));
  $('drive-route-list').innerHTML=routes.map(route=>{
    const declared=route.graph?.association==='explicit_motor_groups';
    let badge=route.motors.length?`${route.motors.length} 处`:'待核';
    if(declared&&route.motors.length)badge+=route.loadUnassigned?' · 负载待核':route.evidence.status==='public_confirmed'?' · 有据':' · 推定';
    if(declared&&!route.motors.length)badge=route.actuation==='pneumatic'?'气动':'见说明';
    return `<button data-drive-route="${escapeHTML(route.id)}" class="${selected?.id===route.id?'active':''}" aria-pressed="${selected?.id===route.id}"><b>${String(route.index+1).padStart(2,'0')}</b><span>${escapeHTML(route.label)}<small>${escapeHTML(route.location)}</small></span><em>${badge}</em></button>`;
  }).join('')||`<p class="drive-empty">${state.loaded?'当前没有可用的路线标记':'设备载入后显示工位位置'}</p>${state.driveError?'<button id="retry-drive" class="inline-link">重试读取传动资料 ↻</button>':''}`;
  $$('#drive-route-list [data-drive-route]').forEach(button=>button.addEventListener('click',()=>selectDriveRoute(button.dataset.driveRoute)));
  $('retry-drive')?.addEventListener('click',getDriveData);
  const count=selected?.motors.length||0;
  $('drive-station-count').textContent=selected?(count?`同类电机 ${count} 处 · 第 ${selected.motorIndex+1} 处`:'此路线的动力源尚未独立建模'):`${routes.length} 条路线 · ${new Set(routes.flatMap(route=>route.motors)).size} 处已建模动力源`;
  $('drive-prev-station').hidden=count<2;$('drive-next-station').hidden=count<2;
  $('drive-focus-motor').disabled=!count;
  const exact=selected?.graph?.association==='same_spinning_position';
  const declared=selected?.graph?.association==='explicit_motor_groups';
  if(declared&&!count){
    $('drive-station-count').textContent=selected.actuation==='pneumatic'?'气动工位 · 可定位机构':'机构位置与动力说明见工位详情';
  }
  $('rotor-station-label').hidden=!(exact||declared&&count>1);
  if(exact||declared&&count>1){
    const select=$('rotor-station');
    $('station-selector-title').textContent=exact?'转杯纺位':'电机工位';
    select.innerHTML=selected.motors.map((motor,i)=>{
      const {machineSide,sectionIndex,sidePosition}=driveObjectContext(motor);
      const title=exact?`${machineSide} 侧 · 第 ${sidePosition} 位 · 第 ${sectionIndex} 节`:stationLabel(motor,i,selected);
      return `<option value="${i}">${escapeHTML(title)}</option>`;
    }).join('');
    select.value=selected.motorIndex;
    $('drive-station-count').textContent=exact?'同类电机 '+count+' 处 · 当前纺位独立驱动':'可选电机 '+count+' 处';
  }
  if(!selected){$('drive-route-detail').innerHTML='<p class="drive-empty">点击模型上的编号或上方路线，查看动力源、传动与工作机构。重复工位可逐一定位。</p>';return}
  if(declared){renderStationDrive(selected);return}
  const scope=(texturingMotion||exact)&&selected.motors.length?scopeDriveRoute(selected,selected.motorIndex):selected;
  const points=driveRoutePoints(scope),statuses={public_confirmed:'驱动功能有公开依据',functional_inference:'功能关系推定',not_modeled:'尚未独立建模'};
  $('drive-route-detail').innerHTML=`<div class="drive-route-purpose"><strong>${escapeHTML(selected.label)}</strong><p>${escapeHTML(selected.role)}</p><p class="drive-branch-scope">${exact?'按纺位编号对应电机、输出端和工作机构':(selected.branches?.length||0)+' 条功能连接 · 保留全部已映射分支；空间邻接为布局推定'}</p></div><ol class="drive-step-list">${points.map(({step,object},index)=>`<li class="${object?'resolved':'unresolved'}"><span class="drive-step-role">${({motor:'动力源',transmission:'传动',load:'工作机构'})[step.role]||'机构'}</span><strong>${escapeHTML(step.label)}</strong>${step.connectionStatus==='unmodeled'?'<small>上游连接未建模 · 以虚线表达功能关系</small>':''}${object?`<small>已映射 ${step.objects.length} 个部件</small><button data-drive-step="${index}">${step.objects.length>1?'近看一处':step.role==='motor'?'定位电机':'定位机构'} ↗</button>`:'<small>未独立建模 · 不代选其它部件</small>'}</li>`).join('')}</ol><details class="drive-route-evidence"><summary>${escapeHTML(statuses[selected.evidence?.status]||'路线证据与待核实')}</summary><p>${escapeHTML(selected.evidence?.note||'传动细节需进一步核实。')}</p>${selected.graph?`<p>${escapeHTML(selected.graph.note||evidenceText(selected.graph))}</p>${toArray(selected.graph.expectedFunctionalRelations).length?evidenceList(selected.graph.expectedFunctionalRelations):''}`:''}${toArray(selected.notes).length?evidenceList(selected.notes):''}<div>${toArray(selected.evidence?.sources).map(source=>sourceLink(source)).join('')}</div></details>`;
  if(texturingMotion&&selected.motors.length){
    const scopes=driveView.selectedMotorRoutes(),allPoints=[];
    const stepNames={false_twist:['动力源','外伸输出轴','同侧切向带区段','同侧摩擦盘轴'],w3:['动力源','外伸输出轴','同侧 W3 共轴喂纱机构'],camshaft_traverse:['动力源','外伸输出轴','同侧分层凸轮轴','同侧横动导丝器'],takeup:['动力源','外伸输出轴','卷绕内部分配（未建模）','同侧卷绕接触辊','同侧 DTY 卷装'],oiling:['动力源','泵外伸输出轴','泵内部工作机构（未建模）','两侧油剂分配管','上油接触位']};
    const scopeHTML=scopes.map(route=>`<h4 class="texturing-scope-heading">${escapeHTML(({false_twist:'摩擦假捻',w3:'W3 卷前喂纱',camshaft_traverse:'机械横动',takeup:'接触辊卷绕',oiling:'油剂流体供给'})[route.id]||route.label)}</h4><ol class="drive-step-list">${driveRoutePoints(route).map(({step,object},i)=>{const index=allPoints.push({step,object})-1;return `<li class="${object?'resolved':'unresolved'}"><span class="drive-step-role">${({motor:'动力源',transmission:'传动',load:'工作机构'})[step.role]||'机构'}</span><strong>${escapeHTML(stepNames[route.id]?.[i]||step.label)}</strong><small>${object?`当前电机范围：${step.objects.length} 个已映射部件`:'未独立建模 · 不补造连接'}${step.connectionStatus==='unmodeled'?' · 上游连接待核实':''}</small>${object?`<button data-drive-step="${index}">近看一处 ↗</button>`:''}</li>`}).join('')}</ol>`).join('');
    $('drive-route-detail').innerHTML=`<div class="drive-route-purpose"><strong>当前电机的 ${scopes.length} 条关联路线</strong><p>仅列出对应机侧的全部已映射机构。橙色脉冲表示功能方向，虚线或空步骤表示尚未建模的连接。</p></div>${scopeHTML}`;
    $$('#drive-route-detail [data-drive-step]').forEach(button=>button.addEventListener('click',()=>focusDriveObject(allPoints[Number(button.dataset.driveStep)]?.object)));
  }else $$('#drive-route-detail [data-drive-step]').forEach(button=>button.addEventListener('click',()=>focusDriveObject(points[Number(button.dataset.driveStep)]?.object)));
}
function stationLabel(motor,index,route){
  const named=route?.motorLabels?.[motor.userData.driveAnchorId];
  if(named)return named;
  const context=driveObjectContext(motor);
  const side=context.machineSide?context.machineSide+' 侧 · ':'';
  const number=context.sidePosition||context.positionIndex||index+1;
  return side+'第 '+number+' 处 · '+(motor.userData.label||'驱动电机');
}

function renderStationDrive(selected){
  const detail=$('drive-route-detail'),motor=selected.motors[selected.motorIndex];
  const scopes=motor?driveView.selectedMotorRoutes():[selected];
  const objects=[],rows=[],status={public_confirmed:'厂家公开驱动功能',functional_inference:'工位动力按功能推定',not_modeled:'执行机构与动力边界'};
  for(const scope of scopes){
    const sections=scope.steps.filter(step=>step.role!=='motor'&&step.objects.length);
    const controls=sections.map(step=>{
      const indexedSpindles=step.objects.length>0&&step.objects.every(node=>Number.isInteger(node.userData.spindleIndex));
      const mechanisms=indexedSpindles?[...step.objects].sort((a,b)=>a.userData.spindleIndex-b.userData.spindleIndex):step.objects;
      const options=mechanisms.map((node,i)=>{
        const id=objects.push(node)-1;
        const label=node.userData.label||step.label;
        if(indexedSpindles)return {id,label:node.userData.spindleIndex+' 锭 · '+node.userData.machineSide+' 侧 · '+label};
        return {id,label:step.objects.length>1?String(i+1).padStart(2,'0')+' · '+label:label};
      });
      if(options.length<=4)return '<li><span>'+escapeHTML(step.label)+'</span><div class="load-picks">'+options.map(o=>
        '<button type="button" data-station-object="'+o.id+'">'+escapeHTML(o.label)+'</button>').join('')+'</div></li>';
      return '<li><label>'+escapeHTML(step.label)+' · '+options.length+' 处<select data-station-options>'+
        options.map(o=>'<option value="'+o.id+'">'+escapeHTML(o.label)+'</option>').join('')+
        '</select></label><button type="button" data-focus-station>定位所选机构</button></li>';
    }).join('');
    rows.push('<section class="drive-route-purpose station-evidence"><strong>'+escapeHTML(scope.label)+'</strong>'+
      (scope.operation==='maintenance'?'<p>停产维护工位，单独演示。</p>':'')+
      (scope.operation==='doffing'?'<p>落纱换管周期。选择本工位可单独查看动作。</p>':'')+'<dl>'+
      '<dt>安装工位</dt><dd>'+escapeHTML(scope.motorLabels?.[motor?.userData.driveAnchorId]||scope.location)+'</dd><dt>电机与动力源</dt><dd>'+escapeHTML(scope.electric)+'</dd>'+
      '<dt>带动机构</dt><dd>'+escapeHTML(scope.role)+'</dd></dl>'+
      '<small>'+(scope.loadUnassigned?'厂家照片可辨认电机外观':status[scope.evidence.status])+'</small><div class="station-sources">'+scope.evidence.sources.map(s=>sourceLink(s)).join('')+'</div>'+
      '<ul class="station-loads">'+controls+'</ul></section>');
  }
  detail.innerHTML=rows.join('');
  detail.querySelectorAll('[data-station-object]').forEach(b=>b.addEventListener('click',()=>focusDriveObject(objects[Number(b.dataset.stationObject)])));
  detail.querySelectorAll('[data-focus-station]').forEach(b=>b.addEventListener('click',()=>focusDriveObject(objects[Number(b.parentElement.querySelector('select').value)])));
}

function selectDriveRoute(id,index){
  if(!driveView)return;
  const previous=driveView.selectedRoute();
  if(texturingMotion&&id){
    const candidate=driveView.routes.find(route=>route.id===id),motor=candidate?.motors[index||0];
    const anchor=motor?.userData.driveAnchorId||motor?.name;
    if(texturingMotors.some(item=>item.id===anchor)){selectTexturingMotor(anchor);return}
    texturing.mode='motor';texturing.motorId=null;texturing.focusYarn=false;
    state.mode='drive';updateViewerLabels();history.replaceState(null,'','#texturing/drive');
  }else if(texturingMotion){texturing.mode='process';texturing.motorId=null}
  driveView.setActive(id);
  const route=driveView.selectedRoute();
  if(rotorMotion&&route?.motors.length&&previous?.motors.length&&index===undefined)index=previous.motorIndex;
  if(route&&Number.isInteger(index))route.motorIndex=THREE.MathUtils.clamp(index,0,Math.max(0,route.motors.length-1));
  if(stationMotion&&route?.motors.length)driveView.setActiveMotor(route.id,route.motorIndex);
  selectPart(null);syncDriveMode();
  if((rotorMotion||stationMotion)&&route?.motors.length&&!state.autoFit)focusDriveObject(route.motors[route.motorIndex]);
}
function focusDriveObject(object){
  if(!object)return;
  selectPart(object);
  const isMotor=driveView?.routes.some(route=>route.motors.includes(object));
  const side=rotorMotion&&driveObjectContext(object).machineSide;
  if(Number.isInteger(object.userData.spindleIndex)){
    const center=worldModelBounds(object).getCenter(new THREE.Vector3());
    const sign=center.z>=currentBounds().getCenter(new THREE.Vector3()).z?1:-1;
    focusSelectedPart({direction:new THREE.Vector3(.14,.22,sign).normalize(),distanceScale:1.65});
  }else if(side){
    const sign=side==='A'?1:-1;
    focusSelectedPart({direction:new THREE.Vector3(.14*sign,.22,sign).normalize(),distanceScale:1.28});
  }else if(isMotor)focusSelectedPart({direction:exteriorDriveDirection(currentBounds(),worldModelBounds(object)),distanceScale:1.22});
  else focusSelectedPart();
}
function cycleDriveStation(direction){
  if(texturingMotion){
    const route=driveView?.selectedRoute();if(!route?.motors.length)return;
    const index=(route.motorIndex+direction+route.motors.length)%route.motors.length;
    selectDriveRoute(route.id,index);return;
  }
  driveView?.moveStation(direction);syncDriveMode();
  const route=driveView?.selectedRoute();
  if(route?.motors.length){if(!state.autoFit)focusDriveObject(route.motors[route.motorIndex]);else selectPart(route.motors[route.motorIndex])}
}

function setPlaying(playing){
  if(!state.loaded)return;
  if(playing&&!state.playing)lastTime=performance.now();
  state.playing=Boolean(playing);setPressed('play-toggle',state.playing);
  syncStationYarn();
  $('play-text').textContent=state.playing?'暂停演示':'运行演示';
  $('play-icon').innerHTML=state.playing?'<path d="M7 5h4v14H7zM15 5h4v14h-4z"/>':'<path d="m9 5 11 7-11 7z"/>';
  syncTexturingMotion();renderer.shadowMap.needsUpdate=true;invalidateFrame();
}
function syncStationYarn(){
  const panel=$('station-yarn-panel'),overlay=stationYarn?.overlay;
  panel.hidden=!overlay;
  if(!overlay)return;
  const singleMotor=state.mode==='drive'&&Boolean(driveView?.selectedRoute());
  overlay.visible=!singleMotor;
  $('station-yarn-readout').textContent=singleMotor?'当前仅演示所选动力工位。打开纱路可回到连续走纱。':
    selectedVariant()?.scope==='station'?'导丝盘包绕段。加热器作为单独工位展示。':'青色标记沿所选纱位从 POY 退绕，经加热、冷却与假捻，行至 DTY 卷装。';
  $('station-yarn-play').textContent=singleMotor?'打开并运行纱路':state.playing?'暂停纱路':'运行纱路';
  $('station-yarn-play').setAttribute('aria-pressed',String(!singleMotor&&state.playing));
}
function initializeStationYarn(){
  if(state.current!=='texturing'||!state.variant)return;
  stationYarn=new StationYarn(modelRoot,scene);
  if(!stationYarn.paths.length)return;
  const sides=new Map();
  $('station-yarn-position').replaceChildren(...stationYarn.paths.map(({side},index)=>{
    const n=(sides.get(side)||0)+1;sides.set(side,n);
    return new Option(side?side+' 侧 · 第 '+n+' 纱位':'Smart Godet 导丝盘',String(index));
  }));
  $('station-yarn-position').disabled=stationYarn.paths.length===1;
  syncStationYarn();
}
$('station-yarn-position').addEventListener('change',()=>{
  if(!stationYarn)return;
  if(state.mode==='drive'&&driveView.selectedRoute())selectDriveRoute(null);
  stationYarn.select(Number($('station-yarn-position').value));invalidateFrame();
});
$('station-yarn-play').addEventListener('click',()=>{
  const scoped=state.mode==='drive'&&driveView.selectedRoute();
  if(scoped)selectDriveRoute(null);
  setPlaying(scoped?true:!state.playing);
});
$('station-yarn-focus').addEventListener('click',()=>{
  if(!stationYarn?.paths.length)return;
  if(state.mode==='drive'&&driveView.selectedRoute())selectDriveRoute(null);
  focusDriveObject(stationYarn.paths[stationYarn.index].node);
});
function texturingStationIndex(){return (texturing.side==='B'?192:0)+texturing.position}
function syncTexturingMotion(){
  const active=modelID()==='texturing'&&state.loaded&&Boolean(texturingMotion);
  $('texturing-panel').hidden=!active;$('texturing-motors').hidden=!active;
  document.querySelector('.atlas').classList.toggle('has-texturing-motion',active);
  if(!active)return;
  const route=driveView?.selectedRoute();
  texturingMotion.setSelection({mode:texturing.mode,routeId:route?.id||null,motorIndex:route?.motorIndex||0,motorAnchorId:texturing.motorId,stationIndex:texturingStationIndex(),side:texturing.side,yarnMode:texturing.yarnMode,running:state.playing});
  texturingMotion.setVisible(true);
  yarnFocusObjects=new Set(texturing.focusYarn?texturingMotion.getStationObjects(texturingStationIndex()):[]);
  $('texturing-play').textContent=state.playing?'Ⅱ 暂停演示':'▶ 开始联动';
  $('texturing-play').setAttribute('aria-pressed',String(state.playing));
  $('texturing-whole').setAttribute('aria-pressed',String(texturing.mode==='process'));
  $('texturing-side').value=texturing.side;$('texturing-position').value=texturing.position;
  $('texturing-speed').value=texturing.speed;$('texturing-yarn-mode').value=texturing.yarnMode;
  $('texturing-motor-select').value=texturing.motorId||(texturing.mode==='motor'&&route?`unmodeled:${route.id}`:'');
  const motor=texturingMotors.find(item=>item.id===texturing.motorId);
  $('texturing-explanation').textContent=texturing.mode==='motor'
    ?(motor?`单电机观察：${motor.name}。只演示关联机构的动作；整条纱路不作连续产纱运行。`:`${route?.label||'所选路线'}的动力源尚未独立建模。这里只标出工作机构，不补造电机或内部传动。`)
    :'全机联动：跟踪纱线从 POY 退绕，经牵伸、热处理和假捻，到上油及 DTY 卷绕。'+(texturing.focusYarn?' 已突出当前纱位，可用“整机位置”恢复全貌。':'');
  $('texturing-motor-summary').innerHTML=motor
    ?`<strong>${motor.code} · ${escapeHTML(motor.name)}</strong><p>${escapeHTML(motor.detail)}</p><button id="texturing-focus-selected-motor">近看这台电机 ↗</button><button id="texturing-scope-view">看全部关联工位</button>`
    :'<strong>7 个已建模动力工位 · 384 个纱位</strong><p>每侧 192 个纱位。电机配置与安装位置为公开资料下的建模选定，尚非厂家完整装配证明。</p>';
  $('texturing-focus-selected-motor')?.addEventListener('click',()=>{const selected=driveView?.selectedRoute();focusDriveObject(selected?.motors[selected.motorIndex])});
  $('texturing-scope-view')?.addEventListener('click',()=>{selectPart(null);setAutoFit(true);fitModelView(camera.position.clone().sub(controls.target))});
  $$('#texturing-motor-list [data-texturing-motor]').forEach(button=>{const selected=button.dataset.texturingMotor===texturing.motorId;button.classList.toggle('active',selected);button.setAttribute('aria-pressed',String(selected))});
  renderTexturingReadout(true);invalidateFrame();
}
function initializeTexturing(){
  if(modelID()!=='texturing')return;
  texturingMotion=new TexturingMotion(modelRoot,scene,{routes:driveView.routes});
  $('texturing-flow').innerHTML=TEXTURING_PHASES.map((phase,index)=>`<span data-texturing-phase="${index}">${escapeHTML(phase.label)}</span>`).join('');
  $('texturing-motor-select').innerHTML='<option value="">全机联动 · 全部动力源</option>'+texturingMotors.map(motor=>`<option value="${motor.id}">${motor.code} · ${motor.name} · ${motor.side?'192':'384'} 纱位</option>`).join('')+'<option value="unmodeled:feed_g1">G1 集成动力源 · 未独立建模</option><option value="unmodeled:feed_g2">G2 集成动力源 · 未独立建模</option>';
  $('texturing-motor-list').innerHTML=texturingMotors.map(motor=>`<button data-texturing-motor="${motor.id}" aria-pressed="false"><b>${motor.code}</b><span><strong>${motor.name}</strong><small>${motor.scope}</small></span></button>`).join('');
  $$('#texturing-motor-list [data-texturing-motor]').forEach(button=>button.addEventListener('click',()=>selectTexturingMotor(button.dataset.texturingMotor)));
  syncTexturingMotion();
}
function selectTexturingMotor(id){
  const motor=texturingMotors.find(item=>item.id===id);if(!motor||!texturingMotion)return;
  const route=driveView.routes.find(item=>item.id===motor.route);
  const index=route?.motors.findIndex(item=>item.userData.driveAnchorId===motor.id||item.name===motor.id);
  if(!route||index<0)return;
  texturing.mode='motor';texturing.motorId=id;texturing.focusYarn=false;if(motor.side)texturing.side=motor.side;
  state.mode='drive';updateViewerLabels();
  driveView.setActiveMotor(motor.route,index);selectPart(null);
  history.replaceState(null,'',`#texturing/drive`);
  syncDriveMode();setAutoFit(true);fitModelView(new THREE.Vector3(.28,.34,motor.side==='B'?1:-1));
}
function showTexturingProcess(){
  if(!texturingMotion)return;
  texturing.mode='process';texturing.motorId=null;
  state.mode='drive';updateViewerLabels();driveView.setActive(null);selectPart(null);
  history.replaceState(null,'','#texturing/drive');syncDriveMode();
}
function renderTexturingReadout(force=false){
  if(!texturingMotion||modelID()!=='texturing')return;
  const now=performance.now();if(!force&&now-lastMotionReadout<100)return;lastMotionReadout=now;
  const current=texturingMotion.getState();
  $('texturing-state').textContent=state.playing?(texturing.mode==='motor'?(texturing.motorId?'单电机运行':'动力源未建模'):'全机联动中'):'已暂停';
  $('texturing-state').classList.toggle('running',state.playing);
  $('texturing-station-label').textContent=`${texturing.side} 侧 · 第 ${texturing.position} / 192 纱位${current.section?` · 第 ${current.section} 节`:''}`;
  $('texturing-phase').textContent=texturing.mode==='motor'?(texturing.motorId?'观察橙色动力脉冲与关联机构':'动力源未独立建模 · 机构位置参考'):current.phaseLabel||'POY 退绕';
  $('texturing-progress').value=Number(current.progress)||0;
  $('texturing-progress').hidden=texturing.mode==='motor';
  $('texturing-panel').dataset.elapsed=playbackTime.toFixed(3);
  $('texturing-panel').dataset.motionMode=texturing.mode;
  $('texturing-panel').dataset.stationIndex=texturingStationIndex();
  $$('#texturing-flow [data-texturing-phase]').forEach(node=>{const active=texturing.mode==='process'&&Number(node.dataset.texturingPhase)===current.phaseIndex;node.classList.toggle('active',active);node.setAttribute('aria-current',active?'step':'false')});
}
function focusTexturingYarn(){
  if(!texturingMotion)return;
  texturing.focusYarn=true;syncTexturingMotion();applyMaterials();
  const bounds=texturingMotion.getStationBounds(texturingStationIndex());
  if(!bounds||bounds.isEmpty())return;
  setAutoFit(false);const direction=new THREE.Vector3(.7,.3,texturing.side==='A'?-.85:.85);
  const fit=fitPerspectiveBounds({min:bounds.min.toArray(),max:bounds.max.toArray()},{direction:direction.toArray(),width:renderer.domElement.clientWidth,height:renderer.domElement.clientHeight,padding:35});
  camera.position.fromArray(fit.position);controls.target.fromArray(fit.center);
  camera.near=fit.near;camera.far=fit.far;camera.updateProjectionMatrix();controls.update();invalidateFrame();
}

function initViewer(){
  try {
    renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});
  } catch(error){
    showError('当前浏览器无法启动 3D','请开启硬件加速，或使用支持 WebGL 的浏览器。');
    return false;
  }
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.04;
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate=false;
  renderer.shadowMap.needsUpdate=true;
  renderer.setClearColor(0xe9ece4);
  renderer.domElement.tabIndex=0;
  renderer.domElement.setAttribute('role','img');
  renderer.domElement.setAttribute('aria-label','三维设备模型。方向键旋转视角，加减键缩放；也可拖动旋转、滚轮缩放和点击部件。');
  $('canvas-host').appendChild(renderer.domElement);
  scene=new THREE.Scene();
  camera=new THREE.PerspectiveCamera(37,1,.1,120);
  camera.position.set(10,7.3,10);
  controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=false;
  controls.enablePan=false;
  controls.minDistance=.05;
  controls.maxDistance=100;
  controls.minPolarAngle=.000001;
  controls.maxPolarAngle=Math.PI-.000001;
  controls.autoRotateSpeed=.7;
  controls.target.set(0,2,0);
  controls.addEventListener('start',()=>{$$('[data-view]').forEach(b=>b.classList.remove('active'))});
  controls.addEventListener('change',()=>{invalidateFrame()});
  const hemi=new THREE.HemisphereLight(0xf9fff4,0x7d8c82,1.85);
  scene.add(hemi);
  const key=new THREE.DirectionalLight(0xfff3df,2.4);
  key.position.set(-5,12,8);
  key.castShadow=true;
  key.shadow.mapSize.set(2048,2048);
  key.shadow.camera.left=-12;key.shadow.camera.right=12;key.shadow.camera.top=12;key.shadow.camera.bottom=-12;
  key.shadow.camera.near=1;key.shadow.camera.far=40;
  key.shadow.bias=-.0003;key.shadow.normalBias=.035;
  scene.add(key);
  const fill=new THREE.DirectionalLight(0xd0e4ec,1.4);
  fill.position.set(9,7,-6);scene.add(fill);
  const front=new THREE.DirectionalLight(0xffffff,.7);
  front.position.set(2,5,12);scene.add(front);
  floor=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({color:0xe5e9df,roughness:1,metalness:0}));
  floor.rotation.x=-Math.PI/2;floor.position.y=-.035;floor.receiveShadow=true;scene.add(floor);
  grid=new THREE.GridHelper(38,38,0xcbd3c7,0xd9dfd3);grid.position.y=-.025;grid.material.transparent=true;grid.material.opacity=.36;scene.add(grid);
  content=new THREE.Group();scene.add(content);
  driveView=new DriveView(scene,$('drive-markers'),selectDriveRoute);
  resizeObserver=new ResizeObserver(resizeViewer);resizeObserver.observe($('canvas-area'));resizeViewer();
  renderer.domElement.addEventListener('wheel',()=>setAutoFit(false),{passive:true});
  renderer.domElement.addEventListener('touchstart',event=>{if(event.touches.length>1)setAutoFit(false)},{passive:true});
  let downPosition=null;
  renderer.domElement.addEventListener('pointerdown',event=>{downPosition={x:event.clientX,y:event.clientY}});
  renderer.domElement.addEventListener('pointerup',event=>{
    if(!downPosition||Math.hypot(event.clientX-downPosition.x,event.clientY-downPosition.y)>6) return;
    const rect=renderer.domElement.getBoundingClientRect();
    pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
    raycaster.setFromCamera(pointer,camera);
    const hit=raycaster.intersectObjects(meshes,false).find(h=>h.object.visible);
    if(hit) selectPart(hit.object);
  });
  renderer.domElement.addEventListener('keydown',event=>{
    const keys=['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-'];
    if(!keys.includes(event.key))return;
    event.preventDefault();
    const offset=camera.position.clone().sub(controls.target),spherical=new THREE.Spherical().setFromVector3(offset);
    if(event.key==='ArrowLeft')spherical.theta-=.12;
    if(event.key==='ArrowRight')spherical.theta+=.12;
    if(event.key==='ArrowUp')spherical.phi=Math.max(.000001,spherical.phi-.1);
    if(event.key==='ArrowDown')spherical.phi=Math.min(Math.PI-.000001,spherical.phi+.1);
    if(['+','=','-'].includes(event.key))setAutoFit(false);
    if(['+','='].includes(event.key))spherical.radius=Math.max(controls.minDistance,spherical.radius*.9);
    if(event.key==='-')spherical.radius=Math.min(controls.maxDistance,spherical.radius*1.1);
    camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(spherical));controls.update();
  });
  renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();state.loaded=false;showError('3D 显示已暂停','显卡资源暂时不可用，请刷新页面重试。');});
  renderer.domElement.addEventListener('webglcontextrestored',()=>location.reload());
  initialized=true;
  animate();return true;
}
function resizeViewer(){
  if(!renderer)return;
  const {width,height}= $('canvas-area').getBoundingClientRect();
  renderer.setSize(Math.max(width,1),Math.max(height,1),false);
  camera.aspect=width/Math.max(height,1);camera.updateProjectionMatrix();
  invalidateFrame();
  if(state.loaded&&modelRoot&&state.autoFit)fitModelView(camera.position.clone().sub(controls.target));
}
function showError(title,description){
  $('load-screen').hidden=false;
  $('load-screen').classList.add('error');
  $('load-label').textContent=title;$('load-detail').textContent=description;
  $('retry-load').hidden=false;
  $('model-status').textContent='模型未载入 · 可重试';
}
function resetModelState(){
  selectPart(null);
  motionEnvelope.makeEmpty();
  geometryBounds.makeEmpty();boundsDirty=true;explosionPending=false;
  setAutoFit(true);
  state.explode=0;$('explode').value=0;$('explode-value').textContent='0%';
  state.playing=false;setPressed('play-toggle',false);$('play-text').textContent='运行演示';$('play-icon').innerHTML='<path d="m9 5 11 7-11 7z"/>';
  playbackTime=0;lastMotionReadout=-Infinity;
  Object.assign(texturing,{mode:'process',side:'A',position:1,motorId:null,focusYarn:false});yarnFocusObjects.clear();
}
function disposeModel(root){
  if(!root)return;
  const geometries=new Set(),materials=new Set(),textures=new Set();
  root.traverse(object=>{if(object.geometry)geometries.add(object.geometry);for(const material of toArray(object.material))materials.add(material)});
  for(const material of materials){for(const value of Object.values(material))if(value?.isTexture)textures.add(value);material.dispose()}
  for(const geometry of geometries)geometry.dispose();
  for(const texture of textures)texture.dispose();
}
function prepareBatches(){
  const moving=stationMotion?.managedNodes||rotorMotion?.managedNodes||texturingMotion?.managedNodes||new Set(spinning);
  modelRoot.traverse(node=>{
    if(node.matrixAutoUpdate&&!moving.has(node)&&!Array.isArray(node.userData.explode)){
      node.updateMatrix();node.matrixAutoUpdate=false;
    }
  });
  modelBatches=new ModelBatches(scene,modelRoot,meshes,moving);
  batchTransformsDirty=false;lastBatchTime=playbackTime;
}
function retireModel(){
  stationYarn?.dispose();stationYarn=null;$('station-yarn-panel').hidden=true;
  rotorMotion?.dispose();rotorMotion=null;stationMotion?.dispose();stationMotion=null;
  modelBatches?.dispose();modelBatches=null;
  texturingMotion?.dispose();texturingMotion=null;
  if(!activeRecord)return;
  activeRecord.materials.restore();
  for(const object of exploded)object.position.copy(object.userData.basePosition);
  for(const object of spinning)object.quaternion.copy(object.userData.baseQuaternion);
  modelRoot.removeFromParent();modelRoot.visible=true;
  recentModels.set(activeRecord.url,activeRecord);
  while(recentModels.size>2){
    const [key,old]=recentModels.entries().next().value;
    recentModels.delete(key);old.materials.dispose();disposeModel(old.root);
  }
  activeRecord=null;modelRoot=null;meshes=[];exploded=[];spinning=[];selectable=[];partGroups=new Map();
}
function indexModel(root,url,metadata){
  const meshes=[],exploded=[],spinning=[],shells=new Set(),groups=new Map();
  root.traverse(object=>{
    if(Array.isArray(object.userData.explode)&&object.userData.explode.length===3){object.userData.basePosition=object.position.clone();exploded.push(object)}
    if(['x','y','z'].includes(object.userData.spinAxis)){object.userData.baseQuaternion=object.quaternion.clone();spinning.push(object)}
    if(object.isMesh){
      const group=inheritedData(object,'group');
      if(group==='shell'||object.userData.shell===true)shells.add(object);
      object.castShadow=true;
      const fineYarn=group==='material'&&/^(warp_end_|shed_warp_|creel_yarn_|continuous_weft_feed|selected_pick)/.test(object.name);
      object.receiveShadow=!inheritedData(object,'thicknessStatus')&&!fineYarn;
      meshes.push(object);
    }
    if(object.userData.label){
      const key=semanticPartKey(object),parent=labeledPart(object.parent);
      if(!parent||semanticPartKey(parent)!==key){
        if(!groups.has(key))groups.set(key,{key,label:key,objects:[]});
        groups.get(key).objects.push(object);
      }
    }
  });
  for(const group of groups.values()){
    if(group.objects.every(object=>Number.isInteger(object.userData.spindleIndex)))
      group.objects.sort((a,b)=>a.userData.spindleIndex-b.userData.spindleIndex);
  }
  return {root,url,metadata,meshes,exploded,spinning,shells,groups,materials:new ModelMaterials(meshes)};
}
async function readModelBytes(response,onProgress){
  const total=Number(response.headers.get('content-length'));
  if(!total||!response.body||typeof TransformStream==='undefined'||response.headers.get('content-encoding'))return response.arrayBuffer();
  let loaded=0,lastPercent=-1;
  const stream=response.body.pipeThrough(new TransformStream({transform(chunk,controller){
    loaded+=chunk.byteLength;
    const percent=Math.min(100,Math.floor(100*loaded/total));
    if(percent!==lastPercent){onProgress(percent);lastPercent=percent}
    controller.enqueue(chunk);
  }}));
  return new Response(stream).arrayBuffer();
}
async function loadModel(){
  if(!initialized)return;
  const request=++state.request;
  if(state.variant&&!state.library){
    if(modelRoot)modelRoot.visible=false;
    await libraryReady;
    if(request!==state.request)return;
  }
  state.loaded=false;
  loadController?.abort();loadController=new AbortController();
  const {signal}=loadController,loadedID=modelID(),url=modelAssetURL(),variant=selectedVariant();
  const cached=recentModels.get(url);recentModels.delete(url);
  if(modelRoot)modelRoot.visible=false;
  retireModel();
  syncTexturingMotion();
  state.loadedIdentity=null;state.variantDetails=null;
  $('download-model').setAttribute('aria-disabled','true');
  driveHighlights.clear();driveView?.clear();if(driveView){driveView.routes=[];driveView.activeId=null;driveView.setVisible(false)}
  renderProvenance();renderDrivePanel();
  resetModelState();
  $('part-select').disabled=true;$('explode').disabled=true;$('play-toggle').disabled=true;
  $('load-screen').hidden=false;$('load-screen').classList.remove('error');$('retry-load').hidden=true;
  $('load-label').textContent='正在载入 '+(variant?.model||equipmentNames[state.current]||stage().name);
  $('load-detail').textContent='准备几何、材质与零件信息';
  $('model-status').textContent='LOADING / 模型载入中';
  try {
    if(state.variant&&!variant){
      showError('此机型未在当前工序的目录中','可用「机型目录」选择设备，或重新读取目录。');return;
    }
    let record=cached;
    if(!record){
      const detail=async()=>{
        if(!variant)return null;
        const res=await fetch('./assets/variants/'+variant.id+'.json?v='+variant.detailHash.slice(0,16),{signal});
        if(!res.ok)throw new Error('Machine record unavailable: '+res.status);
        const data=await res.json();
        if(data.id!==loadedID||data.stageId!==variant.stageId||data.drive?.id!==loadedID||data.provenance?.referenceModel!==variant.model||data.provenance?.referenceManufacturer!==variant.maker)throw new Error('Machine record identity mismatch');
        return data;
      };
      const binary=async()=>{
        const response=await fetch(url,{signal});
        if(!response.ok)throw new Error('Model fetch failed: '+response.status);
        return readModelBytes(response,percent=>{if(request===state.request)$('load-detail').textContent=`载入 ${percent}%`});
      };
      const [bytes,details]=await Promise.all([binary(),detail()]);
      if(request!==state.request)return;
      const gltf=await loader.parseAsync(bytes,new URL('.',new URL(url,document.baseURI)).href);
      if(request!==state.request){disposeModel(gltf.scene);return}
      const metadata=readModelIdentity(gltf.scene);
      if(metadata.equipmentId&&metadata.equipmentId!==loadedID){disposeModel(gltf.scene);throw new Error('Model equipment identity mismatch')}
      if(variant&&(metadata.equipmentId!==loadedID||metadata.stageId!==variant.stageId||metadata.makerKey!==variant.makerKey||metadata.referenceModel!==variant.model||metadata.referenceManufacturer!==variant.maker)){
        disposeModel(gltf.scene);throw new Error('Selected manufacturer or machine does not match geometry');
      }
      record=indexModel(gltf.scene,url,metadata);record.variantDetails=details;
    }
    activeRecord=record;modelRoot=record.root;
    ({meshes,exploded,spinning,groups:partGroups}=record);
    const normalized=normalizeImportedModel(modelRoot,content,7.2,record.rawBounds);
    record.rawBounds=normalized.rawBounds;
    selectable=[...partGroups.values()];
    $('part-select').innerHTML='<option value="">定位零件类型</option>'+selectable.map((group,i)=>`<option value="${i}">${escapeHTML(group.label)}${group.objects.length>1?` · ${group.objects.length} 处`:''}</option>`).join('');
    $('part-select').disabled=selectable.length===0;
    $('explode').disabled=exploded.length===0;
    $('play-toggle').disabled=spinning.length===0;
    state.loaded=true;
    state.loadedIdentity={id:loadedID,metadata:record.metadata};state.variantDetails=record.variantDetails||null;
    driveView.setModel(modelRoot,currentDriveData());initializeTexturing();initializeStationYarn();
    if(loadedID==='rotor_spinning')rotorMotion=new RotorMotion(modelRoot);
    if(record.metadata.stationDriveModel){
      stationMotion=new StationMotion(modelRoot);stationMotion.setRoutes(driveView.routes);$('play-toggle').disabled=!stationMotion.entries.length;
    }
    syncDriveMode();prepareBatches();
    renderDetails();
    setView('perspective');renderer.shadowMap.needsUpdate=true;
    $('load-screen').hidden=true;
    $('model-status').textContent=`${meshes.length} 几何节点 · ${selectable.length} 类零件`;
    renderer.domElement.setAttribute('aria-label',`${$('viewer-title').textContent}三维模型，${selectable.length} 类零件。拖动或方向键旋转，滚轮或加减键缩放，点击或下方列表选择零件。`);
  } catch(error){
    if(request!==state.request)return;
    console.error('Model loading failed:',error);
    state.loaded=false;state.loadedIdentity=null;
    const failed=activeRecord;
    if(failed){
      retireModel();recentModels.delete(failed.url);
      failed.materials.dispose();disposeModel(failed.root);
    }
    driveView.clear();driveView.routes=[];syncDriveMode();renderProvenance();
    $('download-model').setAttribute('aria-disabled','true');$('play-toggle').disabled=true;
    if(!state.variant&&branchConnections[state.current]&&!state.provenance?.assets?.[state.current])showError('这台设备的模型尚未就绪','工艺分支资料可先查看；模型就绪后可点击重新加载。');
    else showError('模型暂未加载成功','请检查网络后重试，也可继续查看右侧工艺资料。');
  }
}
function inheritedData(object,key){let current=object;while(current&&current!==content){if(current.userData[key]!==undefined)return current.userData[key];current=current.parent}return undefined}
function labeledPart(object){let current=object;while(current&&current!==content){if(current.userData.label)return current;current=current.parent}return null}
function semanticPartKey(object){
  const label=String(object.userData.semanticLabel||object.userData.label||object.name).normalize('NFKC').trim().replace(/\s+/g,' ');
  if(Number.isInteger(object.userData.spindleIndex))return '旋转锭子与纱管';
  if(Number.isInteger(object.userData.positionIndex)&&/^(?:完整)?环锭工位\s*\d/.test(label))return '环锭纺纱工位';
  if(object.userData.semanticLabel)return label;
  if(object.userData.group==='material'&&/^shed_warp_\d+(?:\.\d+)?$/.test(object.name))return '经纱';
  // Keep model numbers such as G38/C81. Only remove explicit ordinal or trailing position indices.
  return label.replace(/第\s*\d+\s*(?=[\u3400-\u9fff])/g,'').replace(/([\u3400-\u9fff])\s+\d+\s*\/\s*\d+$/,'$1').replace(/([\u3400-\u9fff])\s+\d+$/,'$1');
}
function semanticPartRepresentative(object){
  let labeled=labeledPart(object);
  if(!labeled)return object;
  let parent=labeledPart(labeled.parent);
  while(parent&&semanticPartKey(parent)===semanticPartKey(labeled)){labeled=parent;parent=labeledPart(labeled.parent)}
  return labeled;
}
function applyMaterials(){
  if(!activeRecord)return;
  const rotorFocus=Boolean((rotorMotion||stationMotion)&&state.mode==='drive'&&driveView.selectedRoute());
  const motorTint=rotorFocus||Boolean(texturingMotion&&texturing.mode==='motor');
  const changed=activeRecord.materials.apply({
    wire:state.wire,xray:state.xray,motorTint,dimMotor:motorTint&&state.mode==='drive',
    dimYarn:texturingMotion&&texturing.mode==='process'&&texturing.focusYarn,selected:selectedObject,
    highlighted:driveHighlights,yarns:yarnFocusObjects,shells:activeRecord.shells
  });
  if(changed){modelBatches?.rebuild();renderer.shadowMap.needsUpdate=true;invalidateFrame()}
}
function selectPart(object){
  object=object?semanticPartRepresentative(object):null;
  const changed=selectedObject!==object;
  selectedObject=object;
  if(!object){selectedPartIndex=-1;$('part-card').hidden=true;$('part-select').value='';if(changed)applyMaterials();return}
  const label=inheritedData(object,'label')||object.name.replaceAll('_',' ');
  const components=inheritedData(object,'componentLabels');
  const description=(inheritedData(object,'description')||'在设备中承担支承、传动或材料处理功能。可拖动模型，从不同方向观察连接关系。')+(components?` 包含：${String(components).split(' | ').join('、')}。`:'');
  $('part-title').textContent=label;$('part-description').textContent=description;$('part-card').hidden=false;
  const group=partGroups.get(semanticPartKey(object));
  const index=selectable.indexOf(group);$('part-select').value=index<0?'':String(index);
  selectedPartIndex=group?.objects.indexOf(object)??-1;
  const count=group?.objects.length||1;
  const position=inheritedData(object,'positionIndex');
  const spindle=inheritedData(object,'spindleIndex');
  const location=spindle?' / '+inheritedData(object,'machineSide')+' 侧 · 全机第 '+spindle+' 锭':position?' / 机位 '+position:'';
  $('part-instance-counter').textContent=(count>1?`同类 ${count} 处 · 第 ${selectedPartIndex+1} 处`:'当前零件')+location;
  $('prev-part-instance').hidden=count<2;$('next-part-instance').hidden=count<2;
  applyMaterials();
}
function cyclePartInstance(direction){
  if(!selectedObject)return;
  const group=partGroups.get(semanticPartKey(selectedObject));
  if(!group?.objects.length)return;
  const index=(selectedPartIndex+direction+group.objects.length)%group.objects.length;
  selectPart(group.objects[index]);
  if(!state.autoFit)focusSelectedPart();
}
function focusSelectedPart(options={}){
  if(!selectedObject||!state.loaded)return;
  const bounds=worldModelBounds(selectedObject);
  if(bounds.isEmpty())return;
  const {width,height}=$('canvas-area').getBoundingClientRect();
  if(width<=40||height<=40)return;
  const direction=options.direction||camera.position.clone().sub(controls.target);
  const fit=fitPerspectiveBounds({min:bounds.min.toArray(),max:bounds.max.toArray()},{direction:direction.toArray(),width,height,fov:camera.fov,padding:Math.min(70,width*.15,height*.15)});
  setAutoFit(false);
  controls.target.fromArray(fit.center);camera.position.fromArray(fit.position);
  if(options.distanceScale)camera.position.sub(controls.target).multiplyScalar(options.distanceScale).add(controls.target);
  camera.near=.001;camera.far=Math.max(100,fit.far);camera.updateProjectionMatrix();
  controls.update();invalidateFrame();
  $$('[data-view]').forEach(button=>button.classList.remove('active'));
}
function setPressed(id,pressed){$(id).setAttribute('aria-pressed',String(pressed))}
function setAutoFit(enabled){
  state.autoFit=enabled;
  $('fit-all').setAttribute('aria-pressed',String(enabled));
  $('view-mode').textContent=enabled?'完整取景':'自由近看 · 可适配全部';
  $('view-mode').classList.toggle('free-view',!enabled);
  invalidateFrame();
}
function currentBounds(){
  // Orbiting changes projection, not geometry. Reuse bounds for long static assemblies.
  if(boundsDirty||geometryBounds.isEmpty()){geometryBounds.copy(worldModelBounds(content));boundsDirty=false}
  const bounds=geometryBounds;
  if(state.playing)motionEnvelope.union(bounds);else motionEnvelope.copy(bounds);
  const effective=state.playing?motionEnvelope:bounds;
  // Exploded or animated parts may travel below their assembly's original ground level.
  floor.position.y=effective.min.y-.035;
  grid.position.y=effective.min.y-.025;
  return effective;
}
function fitModelView(direction,{settle=false}={}){
  if(!camera||!controls||!modelRoot)return;
  const bounds=currentBounds();
  if(bounds.isEmpty())return;
  const {width,height}= $('canvas-area').getBoundingClientRect();
  if(width<=40||height<=40)return;
  const fit=fitPerspectiveBounds({min:bounds.min.toArray(),max:bounds.max.toArray()},{direction:direction.toArray(),width,height,fov:camera.fov,padding:20});
  const currentDistance=camera.position.distanceTo(controls.target);
  // Expansion is immediate, so no intermediate frame clips. Shrinking may ease without competing with controls damping.
  const distance=settle?Math.max(fit.distance,THREE.MathUtils.lerp(currentDistance,fit.distance,.18)):fit.distance;
  controls.target.fromArray(fit.center);
  camera.position.copy(controls.target).addScaledVector(new THREE.Vector3(...fit.direction),distance);
  camera.near=fit.near;camera.far=Math.max(fit.far,distance*3);
  controls.maxDistance=Math.max(100,fit.distance*4);
  camera.lookAt(controls.target);camera.updateProjectionMatrix();camera.updateMatrixWorld();
}
function setView(view){
  if(!camera||!controls||!modelRoot)return;
  if(texturing.focusYarn){texturing.focusYarn=false;syncTexturingMotion();applyMaterials()}
  const directions={perspective:[.73,.47,.82],front:[0,0,1],back:[0,0,-1],left:[-1,0,0],right:[1,0,0],top:[0,1,.000001],bottom:[0,-1,-.000001]};
  if(texturingMotion)directions.perspective=[.28,.34,-1];
  if(rotorMotion)directions.perspective=[.37,.28,1];
  if(stationMotion){
    const size=activeRecord?.rawBounds?.getSize(new THREE.Vector3());
    directions.perspective=size&&size.x>3*Math.max(size.y,size.z)?[.19,.20,1]:[.45,.35,1];
  }
  setAutoFit(true);
  fitModelView(new THREE.Vector3(...(directions[view]||directions.perspective)));
  controls.update();
  $$('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  invalidateFrame();
}
function applyExplosion(){
  for(const object of exploded)object.position.copy(object.userData.basePosition).addScaledVector(explosionVector.fromArray(object.userData.explode),state.explode);
  motionEnvelope.makeEmpty();
  boundsDirty=true;batchTransformsDirty=true;driveView?.markDirty();
  texturingMotion?.markDirty();
  renderer.shadowMap.needsUpdate=true;
  explosionPending=false;
}
function scheduleFrame(){
  if(initialized&&animationHandle==null&&!document.hidden)animationHandle=requestAnimationFrame(animate);
}
function invalidateFrame(){
  frameDirty=true;scheduleFrame();
}
document.addEventListener('visibilitychange',()=>{
  lastTime=performance.now();
  if(!document.hidden)invalidateFrame();
});
function animate(now=performance.now()){
  animationHandle=null;
  const delta=Math.min((now-lastTime)/1000,.05);lastTime=now;
  if(document.hidden)return;
  if(explosionPending&&state.loaded)applyExplosion();
  controls.autoRotate=state.rotating;controls.update(delta);
  const needsRender=frameDirty||state.playing||state.rotating||renderer.shadowMap.needsUpdate;
  if(state.playing&&state.loaded){
    playbackTime+=delta*motionSpeed*(texturingMotion?texturing.speed:1);
    if(stationMotion)stationMotion.update(delta*motionSpeed);
    else if(rotorMotion)rotorMotion.update(delta*motionSpeed);
    else if(!texturingMotion){spinning.forEach(object=>{const axis=object.userData.spinAxis;object.rotation[axis]+=delta*motionSpeed*(object.userData.spinSpeed||.7)});boundsDirty=true;driveView?.markDirty()}
    // eFK rotates work surfaces within the fixed machine envelope; keep its static
    // shadow pass cached instead of drawing all 17k equipment meshes twice per frame.
    if(!texturingMotion&&!rotorMotion&&!stationMotion)renderer.shadowMap.needsUpdate=true;
  }
  if(stationYarn&&needsRender)stationYarn.update(state.playing?delta*motionSpeed:0);
  if(texturingMotion&&needsRender){texturingMotion.update(playbackTime,state.playing?delta*motionSpeed*texturing.speed:0);renderTexturingReadout()}
  if(modelBatches&&needsRender&&(batchTransformsDirty||lastBatchTime!==playbackTime)){
    modelBatches.update(batchTransformsDirty);batchTransformsDirty=false;lastBatchTime=playbackTime;
  }
  if(state.loaded&&(frameDirty||(state.playing&&!texturingMotion&&!rotorMotion&&!stationMotion))){
    if(state.autoFit)fitModelView(camera.position.clone().sub(controls.target),{settle:true});
    else {
      const bounds=currentBounds(),diagonal=bounds.getSize(new THREE.Vector3()).length();
      camera.near=.001;camera.far=Math.max(100,camera.position.distanceTo(controls.target)+diagonal*4);camera.updateProjectionMatrix();
    }
  }
  frameDirty=false;
  // The ground must not hide the underside when the user inspects a bottom view.
  floor.visible=camera.position.y>floor.position.y+.01;grid.visible=floor.visible;
  if(state.loaded&&state.mode==='drive'&&needsRender){
    driveView.update(camera,renderer.domElement.clientWidth,renderer.domElement.clientHeight,playbackTime);
    if(state.playing&&rotorMotion?.activeGuides.length)driveView.updateTraverseEndpoints();
    if(state.playing&&stationMotion)driveView.updateMovingEndpoints();
  }
  if(needsRender)modelBatches?.sortFades(camera);
  if(needsRender)renderer.render(scene,camera);
  if(state.playing||state.rotating)scheduleFrame();
}

$$('[data-filter]').forEach(button=>button.addEventListener('click',()=>{
  state.filter=button.dataset.filter;
  $$('[data-filter]').forEach(b=>{const active=b===button;b.classList.toggle('active',active);b.setAttribute('aria-pressed',active)});
  renderNavigation();
}));
$$('[data-mode]').forEach(button=>button.addEventListener('click',()=>selectMode(button.dataset.mode)));
$$('[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
$('reset-view').addEventListener('click',()=>setView('perspective'));
$('fit-all').addEventListener('click',()=>{texturing.focusYarn=false;syncTexturingMotion();applyMaterials();setAutoFit(true);fitModelView(camera.position.clone().sub(controls.target))});
$('retry-load').addEventListener('click',()=>initialized?Promise.allSettled([getProvenance(),getModelLibrary()]).then(loadModel):location.reload());
$('download-model').addEventListener('click',event=>{if(!state.loaded)event.preventDefault()});
$('play-toggle').addEventListener('click',()=>{if(texturingMotion&&state.mode!=='drive')selectMode('drive');setPlaying(!state.playing)});
$('texturing-play').addEventListener('click',()=>{if(state.mode!=='drive')selectMode('drive');setPlaying(!state.playing)});
$('texturing-speed').addEventListener('change',()=>{texturing.speed=Number($('texturing-speed').value);syncTexturingMotion()});
$('texturing-restart').addEventListener('click',()=>{playbackTime=0;texturingMotion?.update(0,0);renderTexturingReadout(true);invalidateFrame()});
$('texturing-whole').addEventListener('click',showTexturingProcess);
$('texturing-motor-select').addEventListener('change',()=>{const value=$('texturing-motor-select').value;if(value.startsWith('unmodeled:'))selectDriveRoute(value.split(':')[1]);else if(value)selectTexturingMotor(value);else showTexturingProcess()});
$('texturing-yarn-mode').addEventListener('change',()=>{texturing.yarnMode=$('texturing-yarn-mode').value;syncTexturingMotion()});
$('texturing-side').addEventListener('change',()=>{
  texturing.side=$('texturing-side').value;
  const selected=texturingMotors.find(item=>item.id===texturing.motorId);
  if(texturing.mode==='motor'&&selected?.side){const peer=texturingMotors.find(item=>item.route===selected.route&&item.side===texturing.side);if(peer){selectTexturingMotor(peer.id);return}}
  syncTexturingMotion();if(texturing.focusYarn)focusTexturingYarn();
});
for(const event of ['input','change'])$('texturing-position').addEventListener(event,()=>{
  const value=Number($('texturing-position').value);
  if(event==='input'&&(!$('texturing-position').value||!Number.isInteger(value)||value<1||value>192))return;
  texturing.position=Math.round(THREE.MathUtils.clamp(value||1,1,192));syncTexturingMotion();if(texturing.focusYarn)focusTexturingYarn();
});
$('texturing-focus-yarn').addEventListener('click',focusTexturingYarn);
$('texturing-fit').addEventListener('click',()=>{texturing.focusYarn=false;syncTexturingMotion();applyMaterials();setAutoFit(true);if(state.loaded)fitModelView(camera.position.clone().sub(controls.target))});
$('rotate-toggle').addEventListener('click',()=>{state.rotating=!state.rotating;if(state.rotating)setAutoFit(true);setPressed('rotate-toggle',state.rotating)});
$('xray-toggle').addEventListener('click',()=>{state.xray=!state.xray;setPressed('xray-toggle',state.xray);applyMaterials()});
$('wire-toggle').addEventListener('click',()=>{state.wire=!state.wire;setPressed('wire-toggle',state.wire);applyMaterials()});
$('explode').addEventListener('input',()=>{state.explode=Number($('explode').value)/100;$('explode-value').textContent=$('explode').value+'%';explosionPending=true;setAutoFit(true)});
$('part-select').addEventListener('change',()=>selectPart($('part-select').value===''?null:selectable[Number($('part-select').value)]?.objects[0]));
$('prev-part-instance').addEventListener('click',()=>cyclePartInstance(-1));
$('next-part-instance').addEventListener('click',()=>cyclePartInstance(1));
$('focus-part').addEventListener('click',focusSelectedPart);
$('close-part').addEventListener('click',()=>selectPart(null));
$('rotor-station').addEventListener('change',()=>selectDriveRoute(driveView.activeId,Number($('rotor-station').value)));
$('drive-route-select').addEventListener('change',()=>selectDriveRoute($('drive-route-select').value));
$('drive-show-all').addEventListener('click',()=>{selectDriveRoute(null);setAutoFit(true);if(state.loaded)fitModelView(camera.position.clone().sub(controls.target))});
$('drive-prev-station').addEventListener('click',()=>cycleDriveStation(-1));
$('drive-next-station').addEventListener('click',()=>cycleDriveStation(1));
$('drive-focus-motor').addEventListener('click',()=>{const route=driveView?.selectedRoute();focusDriveObject(route?.motors[route.motorIndex])});
$('drive-fit-machine').addEventListener('click',()=>{setAutoFit(true);if(state.loaded)fitModelView(camera.position.clone().sub(controls.target))});
$('inspect-motor').addEventListener('click',()=>{selectMode('drive');if(innerWidth<980)$('viewer').scrollIntoView({behavior:reduceMotion?'auto':'smooth',block:'center'})});
$('prev-stage').addEventListener('click',()=>{const index=state.data.stages.indexOf(stage());if(index>0)selectStage(state.data.stages[index-1].id)});
$('next-stage').addEventListener('click',()=>{const index=state.data.stages.indexOf(stage());if(index<state.data.stages.length-1)selectStage(state.data.stages[index+1].id)});
const openDialog=()=>$('research-dialog').showModal();
$('sources-button').addEventListener('click',openDialog);$('route-info').addEventListener('click',openDialog);$('close-dialog').addEventListener('click',()=>$('research-dialog').close());
$('research-dialog').addEventListener('click',event=>{if(event.target===$('research-dialog')){const rect=event.target.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)event.target.close()}});
const openProvenanceDialog=()=>{renderProvenanceDialog();$('provenance-dialog').showModal()};
$('model-provenance-button').addEventListener('click',openProvenanceDialog);
$('provenance-details-button').addEventListener('click',openProvenanceDialog);
$('close-provenance-dialog').addEventListener('click',()=>$('provenance-dialog').close());
$('provenance-dialog').addEventListener('click',event=>{if(event.target===$('provenance-dialog')){const rect=event.target.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)event.target.close()}});
function readHashRoute(){return parseMachineHash(location.hash,state.data.stages)}
async function syncHashRoute(){
  const route=readHashRoute();
  if(!route)return;
  await selectMachine(route.current,route.variant,{mode:route.mode,navigate:false});
}
const initialRoute=readHashRoute();
if(initialRoute)Object.assign(state,initialRoute);
window.addEventListener('hashchange',syncHashRoute);
renderNavigation();renderDetails();renderSources();
loadMotorCatalog();getData();
const driveReady=getDriveData(),provenanceReady=getProvenance(),libraryReady=getModelLibrary();
if(initViewer())Promise.allSettled([provenanceReady,driveReady,libraryReady]).finally(()=>{if(!state.request)loadModel()});
