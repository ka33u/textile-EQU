"""Publish reviewed three-branch candidates and merge their source-backed records.

The original 16 equipment GLBs are preserved byte for byte. This command only
runs after all three candidate models and drive mappings have been reviewed.
"""
from pathlib import Path
import copy, hashlib, json, shutil, struct
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
IDS=['compact_spinning','twisting','texturing']
VERSION='20261117-v5-branches'
def read(path):return json.loads((ROOT/path).read_text())
def write(path,data):(ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def metadata(path):
    raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    gltf=json.loads(raw[20:20+length])
    roots=[n for n in gltf['nodes'] if n.get('name')=='stage_'+path.stem]
    assert len(roots)==1,path
    return roots[0]['extras'],raw

config=read('research/config-extensions-v5.json')
process=read('research/process-extensions-v5.json')
drives=read('research/drive-extensions-v5.json')
configs={x['id']:x for x in config['items']}
new_stages={x['id']:x for x in process['stages']}
new_drives={x['id']:x for x in drives['items']}
assert set(configs)==set(new_stages)==set(new_drives)==set(IDS)
candidate_meta={}
for ident in IDS:
    path=ROOT/'qa/v5-candidates/models'/(ident+'.glb')
    meta,raw=metadata(path)
    assert meta.get('equipmentId')==ident
    assert meta.get('modelVersion')=='3.0' and meta.get('driveRevision')=='5.0'
    assert meta.get('motorDetailScope')=='external_only'
    assert meta.get('structuralCompleteness') is False
    assert meta.get('referenceModel')==configs[ident]['referenceModel']
    candidate_meta[ident]=(meta,raw)

data=read('dist/process-data.json')
data['stages']=[x for x in data['stages'] if x['id'] not in IDS]+[new_stages[i] for i in IDS]
assert len(data['stages'])==19
stenter=next(s for s in data['stages'] if s['id']=='stenter')
stenter.update(name='拉幅热定型',equipment='拉幅热定型机（兼烘干）',en='STENTERING / HEAT SETTING',
    summary='兼具烘干与幅宽控制功能。全棉主要进行干燥、幅宽调整及适用整理；热塑性纤维可按对应条件进行热定型。')
stenter['note']=process['existingStageClarifications']['stenter']['note']
data['route']='棉纺—机织—染整主线；紧密纺替代、倍捻选配和化纤加弹独立分支'
data['researchedAt']='2026-11-17'
notes=[
    '紧密纺替代普通环锭细纱：粗纱→紧密纺→络筒，不是环锭细纱后的追加工序。',
    '倍捻用于并纱准备后的选配加捻；加弹是化纤POY到DTY的独立路线。两者不串接到棉纺主线末尾。',
    '拉幅设备兼有烘干功能。全棉的干燥和幅宽整理与热塑性纤维的热定型需按材料分别理解。']
data['routeNotes']=list(dict.fromkeys(data.get('routeNotes',[])+notes))

provenance=read('dist/equipment-provenance.json')
provenance['items']=[x for x in provenance['items'] if x['id'] not in IDS]
for ident in IDS:
    item=copy.deepcopy(configs[ident]);stage=new_stages[ident]
    item['configSource']='research/config-extensions-v5.json'
    item['configurationEvidenceStatus']='selected_public_reference'
    item['generationAssessment']=item['currentFinding']
    item['configurationSections']=[{'title':'所选设备结构范围','items':stage.get('modelFeatures',[])}]
    provenance['items'].append(item)
    meta,raw=candidate_meta[ident]
    provenance['assets'][ident]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
        **{key:meta[key] for key in ['modelVersion','referenceModel','driveRevision','motorDetailScope']}}
provenance.update(checkedAt='2026-11-17',assetVersion=VERSION,configuredMachineCount=19,
    driveRevision='5.0',motorDetailScope='external_only',
    assetManifestRecordedAt=datetime.now(timezone.utc).isoformat())
files=provenance.get('configurationFiles',[])
if isinstance(files,list):provenance['configurationFiles']=list(dict.fromkeys(files+['research/config-extensions-v5.json']))

chain=read('dist/drive-chains.json')
chain['items']=[x for x in chain['items'] if x['id'] not in IDS]+[new_drives[i] for i in IDS]
chain.update(driveRevision='5.0',checkedAt='2026-11-17')
for ident in IDS:
    shutil.copy2(ROOT/'qa/v5-candidates/models'/(ident+'.glb'),ROOT/'dist/assets/models'/(ident+'.glb'))
write('dist/process-data.json',data)
write('dist/equipment-provenance.json',provenance)
write('dist/drive-chains.json',chain)
print(json.dumps({'published':IDS,'equipmentCount':19,'assetVersion':VERSION},ensure_ascii=False))
