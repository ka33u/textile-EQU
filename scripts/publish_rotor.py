"""Integrate the R 70 asset and its drive/study records while retaining all other equipment."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
SOURCE='research/config-rotor.json'
data=json.loads((ROOT/SOURCE).read_text())
ref=data['items'][0]
stage=data['stage']
ident=stage['id']
version='20261118-rotor-r70'

def read(name):
    return json.loads((DIST/name).read_text())

def write(name,value):
    (DIST/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def replace(rows,entry):
    return [r for r in rows if r['id']!=entry['id']]+[entry]

glb=(DIST/'assets/models'/f'{ident}.glb').read_bytes()
n=struct.unpack_from('<I',glb,12)[0]
nodes=json.loads(glb[20:20+n])['nodes']
meta=next(node['extras'] for node in nodes if node.get('name')=='stage_'+ident)
assert meta['referenceModel']==ref['referenceModel'] and meta['equipmentId']==ident
assert sum(node.get('extras',{}).get('driveRole')=='motor' for node in nodes)==240
assert meta['structuralCompleteness'] is False
anchors={node['extras']['driveAnchorId'] for node in nodes if node.get('extras',{}).get('driveAnchorId')}
stations=[f'{side}{i:02}' for side in 'AB' for i in range(1,25)]

def step(role,label,ids=(),status=None,scopes=None):
    assert len(set(ids))==len(ids) and set(ids)<=anchors, (label,set(ids)-anchors)
    result={'role':role,'label':label,'match':[],'anchorIds':list(ids)}
    if status:result['connectionStatus']=status
    if scopes:result['motorScopes']=scopes
    return result

def route(key,title,place,action,steps,evidence,note,by_position=False):
    return {'id':key,'label':title,'location':place,'role':action,'steps':steps,
            'evidence':{'status':evidence,'note':note,'sources':ref['sources'][:2]},
            'graph':{'kind':'functional_power_graph','association':'same_spinning_position' if by_position else 'functional',
                     'physicalConnectionClaim':False,'note':'纺位号由模型锚点确定。虚线及空步骤表示动力归属或中间连接待核实。'}}

routes=[]
for key,label,place,load,action,job in data['functions']:
    ids={role:[f'R70_{s}_{key}_{role}' for s in stations] for role in ['motor','out','load']}
    associate=lambda role:{motor:[target] for motor,target in zip(ids['motor'],ids[role])}
    comment='技术册第 9 页确认该工位独立电机驱动。输出端形状和安装朝向为外观示意。'
    connection='unmodeled' if key in ['guide','package'] else 'functional_inference'
    if connection=='unmodeled':comment+=' 电机至工作件间的传动结构尚未公开。'
    routes.append(route(key,label+'独立驱动',place,action,[
        step('motor',label+'电机',ids['motor']),
        step('transmission','电机外伸输出端',ids['out'],'functional_inference',associate('out')),
        step('load',load,ids['load'],connection,associate('load'))],'public_confirmed',comment,True))
for key,label,load,ids,place in [
    ('delivery','引纱','引纱罗拉及压辊',[f'R70_{s}_delivery_load' for s in stations],'引纱嘴上方、卷绕单元前'),
    ('vacuum','工艺负压','车尾过滤与排风接口',['R70_vacuum_end'],'车尾过滤单元'),
    ('convey','成筒输送','双侧成筒输送带',['R70_conveyor_A','R70_conveyor_B'],'机节上方至出筒端'),
    ('doff','自动落筒','两台机器人的夹持机构',['R70_doffer_A','R70_doffer_B'],'两侧上部行走轨')]:
    routes.append(route(key,label+'机构',place,'已定位'+load+'。动力源与详细传动待实机资料核实。',[
        step('motor','动力源归属待核实'),step('transmission','内部连接待核实',status='unmodeled'),
        step('load',load,ids,'unmodeled')],'not_modeled','厂家提供机构功能。公开资料不足以给该负载指定电机型号、数量或安装点。'))
chain=read('drive-chains.json')
chain['items']=replace(chain['items'],{'id':ident,'summary':'48 个纺位各有五项独立驱动，可按机侧及纺位定位。引纱、吸风、成筒输送和落筒机构另列。',
    'evidenceNote':'240 处是五项逐位驱动的合计。机器人的轴数、共用辅机及引纱的动力归属另待订单资料。','routes':routes})
chain.update(checkedAt=data['checkedAt'],assetVersion=version)

process=read('process-data.json')
stage['sources']=ref['sources']
process['stages']=replace(process['stages'],stage)
process['route']='棉纺—机织—染整主线；紧密纺、转杯纺、倍捻及化纤加弹分支'
process['routeNotes']=list(dict.fromkeys([*process['routeNotes'],stage['note']]))
process.update(researchedAt=data['checkedAt'],coverageReview=data['coverageReview'],assetVersion=version)
provenance=read('equipment-provenance.json')
provenance['items']=replace(provenance['items'],dict(ref,configSource=SOURCE,configurationEvidenceStatus='selected_public_reference'))
provenance['configurationFiles']=list(dict.fromkeys([*provenance['configurationFiles'],SOURCE]))
provenance['assets'][ident]=dict(sha256=hashlib.sha256(glb).hexdigest(),bytes=len(glb),**{
    k:meta[k] for k in ['modelVersion','referenceModel','driveRevision','motorDetailScope']})
provenance.update(checkedAt=data['checkedAt'],configuredMachineCount=len(process['stages']),assetVersion=version,
                  assetManifestRecordedAt=datetime.now(timezone.utc).isoformat())

catalog=read('motor-applications.json')
ring=next(s for s in catalog['stages'] if s['id']=='spinning')
original=next((row for s in catalog['stages'] for row in s['rows'] if 'rotorS' in row['refs']),None)
assert original, 'Saurer comparison row lost'
ring['rows']=[row for row in ring['rows'] if row is not original]
ring['coverage']='环锭机可用四锭锭带、分段切向带或共用长切向带。喷气成纱单元作为另一种成纱原理的实例。转杯纺另设设备条目。'
catalog['sources']['rotorR70']={'title':'立达 R 70 原厂技术册','url':ref['sources'][1]['url'],'locator':'第 8–10 页，基础机和纺位驱动'}
rows=[]
for key,label,place,load,action,job in data['functions']:
    electric='厂家列为独立电机，未公开电磁类型和铭牌。'
    if key=='cup':electric+=' 转杯采用磁轴承，设计上限 180 000 r/min。磁轴承描述支承方式。'
    if key=='opening':electric+=' 分梳辊可在 6 000–11 000 r/min 范围内电子调速。'
    if key=='feed':electric+=' 喂条采用数字控制。'
    filters=['single','position'] if key=='guide' else ['single']
    rows.append(dict(maker='Rieter',model='R 70',station=place+' · '+label,path=label+'电机 → '+load+'。'+action,
        electric=electric,work={'feed':'调整棉条喂入量。','opening':'按原料调节梳解强度。','cup':'转杯高速稳定成纱。','package':'按纱支和用途设置成筒条件。','guide':'控制铺纱位置与卷装外形。'}[key],
        refs=['rotorR70'],filters=filters,jobs=[job],motorJobs={t:[job] for t in filters},level='整机或原厂配置'))
rows.append(original)
catalog['stages']=replace(catalog['stages'],{'id':ident,'question':'每个转杯纺位有哪些独立电机？','coverage':'逐项对照 R 70 的五类工位，并列出 Autocoro 11 的另一家厂家实例。', 'rows':rows})
write('process-data.json',process);write('drive-chains.json',chain);write('equipment-provenance.json',provenance);write('motor-applications.json',catalog)
subprocess.run([sys.executable,str(ROOT/'scripts/build_motor_applications.py')],check=True)
print(f'{ident}: {len(stations)} positions / 240 unit drives / {len(routes)} routes')
