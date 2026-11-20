"""Index independently exported machines by stage. Publish small catalog and lazy drive records."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
from publish_expansion import drive_record, read, unique
from build_motor_applications import main as render_study

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
ASSETS=DIST/'assets/variants'
MAKERS={'jingwei':'经纬纺机','titan':'浙江泰坦','yuejian':'越剑智能','saurer':'卓郎 Saurer',
        'rieter':'立达 Rieter','barmag':'巴马格 Barmag','marzoli':'马佐里 Marzoli',
        'toyota':'丰田自动织机 Toyota','picanol':'必佳乐 Picanol',
        'karl_mayer':'卡尔迈耶 KARL MAYER','staubli':'史陶比尔 Stäubli','benninger':'贝宁格 Benninger',
        'monforts':'门富士 Monforts','andritz':'安德里茨 ANDRITZ','uster':'乌斯特 Uster',
        'ssm':'SSM','swastik':'SWASTIK Textile Engineers','brueckner':'布鲁克纳 Brückner'}
DEFAULT_MAKERS={'Rieter':'rieter','KARL MAYER':'karl_mayer','Stäubli':'staubli','Stäubli 史陶比尔':'staubli',
                'Picanol':'picanol','Benninger':'benninger','Monforts':'monforts','ANDRITZ':'andritz','Uster':'uster',
                'Saurer / Volkmann':'saurer','Barmag':'barmag','SSM':'ssm','SWASTIK Textile Engineers':'swastik','Brückner':'brueckner'}

def save(path, value, compact=False):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=None if compact else 2,
                               separators=(',',':') if compact else None)+'\n',encoding='utf-8')

def main():
    process=read(DIST/'process-data.json')
    stages={item['id']:item for item in process['stages']}
    provenance=read(DIST/'equipment-provenance.json')
    default_refs={item['id']:item for item in provenance['items']}
    apps=read(DIST/'motor-applications.json')
    study_stages={item['id']:item for item in apps['stages']}
    # Replacing a manufacturer record must also retire its old rows and unused source URLs.
    for stage in study_stages.values():
        stage['rows']=[row for row in stage['rows'] if 'modelAssetId' not in row]
    sources=apps['sources']={k:v for k,v in apps['sources'].items() if not k.startswith('machineRef_')}
    references={item['url']:name for name,item in sources.items()}
    models=[]
    for stage_id,stage in stages.items():
        d=default_refs[stage_id];key=DEFAULT_MAKERS[d['referenceManufacturer']]
        models.append(dict(id=stage_id,stageId=stage_id,stageName=stage['name'],makerKey=key,maker=d['referenceManufacturer'],
                           makerLabel=MAKERS[key],model=d['referenceModel'],equipment=stage.get('equipment',stage['name']),
                           configuration=d['referenceConfiguration'],dating=d.get('currentFinding',''),checkedAt=d.get('checkedAt') or provenance.get('checkedAt'),scope='machine'))
    variants=[rec for path in sorted((ROOT/'research').glob('variants-*.json')) for rec in read(path)]
    group_keys=set(stages)
    new_count=Counter()
    for rec in variants:
        mid=rec['id'];stage_id=rec['stageId'];maker=rec['makerKey']
        assert re.fullmatch(r'[a-z][a-z0-9_]+',mid) and mid not in group_keys and stage_id in stages and maker in MAKERS,mid
        group_keys.add(mid)
        assert all(rec.get(field) for field in ('model','maker','configuration','dating','summary','verified','inferred','missing','counts','sources','routes','process','quality','input','output')),mid
        raw=(ASSETS/(mid+'.glb')).read_bytes()
        assert raw[:4]==b'glTF' and len(raw)==struct.unpack_from('<I',raw,8)[0]
        gltf=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
        nodes=[n.get('extras',{}) for n in gltf['nodes']]
        roots=[n for n in nodes if n.get('equipmentId')==mid]
        assert len(roots)==1 and roots[0]['referenceModel']==rec['model'] and roots[0]['referenceManufacturer']==rec['maker'],mid
        assert roots[0]['stageId']==stage_id and roots[0]['makerKey']==maker and roots[0]['stationDriveModel'],mid
        anchors={n['driveAnchorId']:n for n in nodes if n.get('driveAnchorId')}
        assert len(anchors)==sum(bool(n.get('driveAnchorId')) for n in nodes),mid
        assert len({s['id'] for s in rec['routes']})==len(rec['routes'])
        assert all(s['url'].startswith(('https://','http://')) and s['supports'] for s in rec['sources']),mid
        routes=[];known=set();inferred=set();unknown=set()
        for spec in rec['routes']:
            route=drive_record(spec,anchors)
            evidence=[rec['sources'][i] for i in spec['sources']]
            assert evidence
            route['evidence']['sources']=evidence;routes.append(route)
            motors=route['steps'][0]['anchorIds']
            if 'motorLabels' in spec:
                labels=spec['motorLabels']
                assert set(labels)==set(motors) and all(labels.values()),(mid,spec['id'])
                route['motorLabels']=labels
            if spec['status']=='confirmed':known.update(motors)
            elif spec['status']=='inferred':inferred.update(motors)
            elif route.get('loadUnassigned'):unknown.update(motors)
            refs=[]
            for s in evidence:
                url=s['url']
                if url not in references:
                    name='machineRef_'+sha256(url.encode()).hexdigest()[:14]
                    references[url]=name;sources[name]=dict(title=s['title'],url=url,locator=s['supports'])
                refs.append(references[url])
            filters=spec.get('filters') or ['unspecified'];jobs=spec.get('jobs') or ['process']
            study_stages[stage_id]['rows'].append(dict(modelAssetId=mid,routeId=spec['id'],maker=rec['maker'],model=rec['model'],
                station=spec['location']+' · '+spec['label'],path=spec['action'],electric=spec['electric'],work=spec['loadLabel'],
                refs=unique(refs),filters=filters,jobs=jobs,motorJobs={f:jobs for f in filters},
                level={'confirmed':'厂家公开工位驱动','inferred':'按工作机构推定','unassigned':'动力归属或执行边界'}[spec['status']]))
        motors={a for a,e in anchors.items() if e.get('driveRole')=='motor'}
        assert motors==known|inferred|unknown and len(motors)==roots[0]['modeledMotorCount'],mid
        counts=[]
        if known:counts.append(f'{len(known)} 处有厂家驱动功能依据')
        if inferred-known:counts.append(f'{len(inferred-known)} 处按机构功能推定')
        if unknown-known-inferred:counts.append(f'{len(unknown-known-inferred)} 处仅能确认电机外形，负载待核')
        summary=f'模型标出 {len(motors)} 处电机工位。'+'，'.join(counts)+'。'
        drive=dict(id=mid,summary=summary,
                   evidenceNote='各条路线列出安装工位、对应机构及原厂资料。精确安装位置与未披露的联接方式见型号说明。',routes=routes)
        scope=rec.get('scope','machine');assert scope in ('machine','station')
        new_count[scope]+=1
        data=dict(id=mid,stageId=stage_id,process={k:rec[k] for k in ('summary','input','output','process','quality')},
                  drive=drive,provenance=dict(id=mid,referenceManufacturer=rec['maker'],referenceModel=rec['model'],
                  referenceConfiguration=rec['configuration'],currentFinding=rec['dating'],checkedAt=rec['checkedAt'],
                  configurationStatus=rec.get('scopeLabel','整机模型')+'。所选配置及资料边界见下方逐项记录。',
                  selectedCounts=rec['counts'],verified=rec['verified'],inferred=rec['inferred'],missing=rec['missing'],
                  sources=rec['sources'],structuralCompleteness=False))
        path=ASSETS/(mid+'.json');save(path,data,compact=True)
        models.append(dict(id=mid,stageId=stage_id,stageName=stages[stage_id]['name'],makerKey=maker,maker=rec['maker'],
                  makerLabel=MAKERS[maker],model=rec['model'],equipment=rec['equipment'],configuration=rec['configuration'],
                  dating=rec['dating'],checkedAt=rec['checkedAt'],scope=scope,scopeLabel=rec.get('scopeLabel','整机模型'),
                  routes=len(routes),motors=len(motors),sha256=sha256(raw).hexdigest(),bytes=len(raw),
                  detailHash=sha256(path.read_bytes()).hexdigest()))
    apps['checkedAt']=max((r['checkedAt'] for r in variants),default=apps['checkedAt'])
    assert len({m['id'] for m in models})==len(models)
    makers=[dict(id=k,name=v) for k,v in MAKERS.items() if any(m['makerKey']==k for m in models)]
    save(DIST/'model-variants.json',dict(checkedAt=apps['checkedAt'],makers=makers,models=models))
    save(DIST/'motor-applications.json',apps)
    render_study()
    print(f'{len(stages)} classes / {len(models)} model entries / {dict(new_count)} additions / {len(makers)} manufacturers')

if __name__=='__main__':main()
