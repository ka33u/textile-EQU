"""Rebuild the local equipment catalog from the seven equipment records and their GLBs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
FILES=['expansion-yarn.json','expansion-preparation.json','expansion-wet.json']
ORDER=['assembly_winding','airjet_spinning','warp_tying','washing_range','singeing','mercerizing','sanforizing']
VERSION='20261119-stations'
DATE='2026-11-19'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(name,data):
    (DIST/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def unique(values):
    return list(dict.fromkeys(values))

def expand(groups):
    result=[]
    for group in groups:
        if 'repeat' not in group:
            result.append(group)
            continue
        for n in range(group.get('start',1),group.get('start',1)+group['repeat']):
            result.append({'motor':group['motor'].format(n=n) if group.get('motor') else None,
                           'via':[s.format(n=n) for s in group.get('via',[])],
                           'loads':[s.format(n=n) for s in group['loads']]})
    return result

def drive_record(spec,nodes):
    groups=expand(spec['groups'])
    groups=[dict(g,via=[part for part in g.get('via',[]) if not g.get('motor') or part!=g['motor']+'_out']) for g in groups]
    motors=[g['motor'] for g in groups if g.get('motor')]
    state=spec['status']
    assert state in ('confirmed','inferred','unassigned')
    assert (state!='unassigned' if motors else state=='unassigned' or spec.get('actuation')=='pneumatic') and len(motors)==len(set(motors)),spec['id']
    assert all(g['loads'] for g in groups)
    # Each intermediate entry is a successive mechanism followed by the working loads.
    # Routes with several independent trains are assembled per motor, never by proximity.
    via_count=max((len(g.get('via',[])) for g in groups),default=0)
    columns=[('motor','动力源'),('transmission','电机外伸输出端')]
    for i in range(via_count):columns.append(('transmission','传动机构' if via_count==1 else f'传动机构 {i+1}'))
    columns.append(('load',spec['loadLabel']))
    steps=[{'role':role,'label':label,'match':[],'anchorIds':[],'motorScopes':{}} for role,label in columns]
    links=set()
    for g in groups:
        motor=g.get('motor');via=g.get('via',[])
        levels=[[motor] if motor else [],[motor+'_out'] if motor else []]
        levels.extend([[via[i]] if i<len(via) else [] for i in range(via_count)])
        levels.append(g['loads'])
        for i,ids in enumerate(levels):
            assert set(ids)<=nodes.keys(),(spec['id'],set(ids)-nodes.keys())
            steps[i]['anchorIds'].extend(ids)
            if motor:steps[i]['motorScopes'][motor]=ids
            if i:links.update((a,b,i) for a in levels[i-1] for b in ids)
    for i,step in enumerate(steps):
        step['anchorIds']=unique(step['anchorIds'])
        if not motors:step.pop('motorScopes')
        if i==0:continue
        step['connectionStatus']='functional_inference' if i==1 or spec.get('transmissionKnown') else 'unmodeled'
        if step['role']=='transmission' and i>1 and step['anchorIds']:
            step['label']='、'.join(unique(nodes[a].get('semanticLabel',nodes[a]['label']) for a in step['anchorIds']))[:160]
    map_status={'confirmed':'public_confirmed','inferred':'functional_inference','unassigned':'not_modeled'}
    return dict(id=spec['id'],label=spec['label'],location=spec['location'],role=spec['action'],
        electric=spec['electric'],loadLabel=spec['loadLabel'],steps=steps,
        operation=spec.get('operation','production'),actuation=spec.get('actuation','pneumatic' if 'pneumatic' in spec.get('filters',[]) and not motors else 'electric' if motors else 'unspecified'),
        evidence={'status':map_status[state],'note':spec['electric']},
        graph={'kind':'functional_power_graph','association':'explicit_motor_groups',
               'physicalConnectionClaim':False,'links':sorted(links,key=lambda p:(p[2],p[0],p[1])),
               'note':'实线或虚线均按所选工位关联，点选工作机构可检查具体部位。未公开的中间机械连接以虚线表示。'})

def main():
    records={}; config_files={}
    for name in FILES:
        path=ROOT/'research'/name
        for record in read(path):
            key=record['id'];assert key not in records
            records[key]=record;config_files[key]='research/'+name
    assert set(records)==set(ORDER)
    process=read(DIST/'process-data.json');provenance=read(DIST/'equipment-provenance.json')
    drive=read(DIST/'drive-chains.json');catalog=read(DIST/'motor-applications.json')
    for group,key in [(process,'stages'),(provenance,'items'),(drive,'items'),(catalog,'stages')]:
        group[key]=[r for r in group[key] if r['id'] not in records]
    by_url={s['url']:k for k,s in catalog['sources'].items()}
    coverage=[]
    for key in ORDER:
        rec=records[key];sources=rec['sources']
        asset=(DIST/'assets/models'/(key+'.glb')).read_bytes()
        length=struct.unpack_from('<I',asset,12)[0];gltf=json.loads(asset[20:20+length])
        extras={n['extras']['driveAnchorId']:n['extras'] for n in gltf['nodes'] if n.get('extras',{}).get('driveAnchorId')}
        root=next(n['extras'] for n in gltf['nodes'] if n.get('extras',{}).get('equipmentId')==key)
        assert root['referenceModel']==rec['model'] and root['referenceManufacturer']==rec['maker'] and root['stationDriveModel']
        assert all(s['url'].startswith('https://') for s in sources)
        assert len({s['id'] for s in rec['routes']})==len(rec['routes'])
        rows=[];routes=[];known_motors=set();estimated=set()
        for spec in rec['routes']:
            route=drive_record(spec,extras)
            references=[];evidence=[]
            for i in spec['sources']:
                source=sources[i];url=source['url']
                if url not in by_url:
                    by_url[url]=f'{key}Ref{i+1}'
                    catalog['sources'][by_url[url]]=dict(title=source['title'],url=url,locator=source['supports'])
                references.append(by_url[url]);evidence.append(source)
            assert references
            route['evidence']['sources']=evidence;routes.append(route)
            if spec['status']=='confirmed':known_motors.update(route['steps'][0]['anchorIds'])
            elif spec['status']=='inferred':estimated.update(route['steps'][0]['anchorIds'])
            filters=spec.get('filters') or ['unspecified'];jobs=spec.get('jobs') or ['process']
            if 'ac' in filters and not any(m['id']=='ac' for m in catalog['motorIndex']):
                catalog['motorIndex'].append(dict(id='ac',name='交流电机（电磁型式未细分）',group='厂家明示的电机类型',
                     note='本项收录厂家明确写为 AC motor 的工位。同步、异步等具体电磁结构需进一步核对铭牌。',refs=unique(references)))
            evidence_label={'confirmed':'厂家公开工位驱动','inferred':'按工作机构推定','unassigned':'执行方式与资料边界'}[spec['status']]
            rows.append(dict(maker=rec['maker'],model=rec['model'],station=spec['location']+' · '+spec['label'],
                 path=spec['action'],electric=spec['electric'],work=spec['loadLabel'],filters=filters,jobs=jobs,
                 refs=unique(references),motorJobs={f:jobs for f in filters},level=evidence_label))
        actual={a for a,e in extras.items() if e.get('driveRole')=='motor'}
        assert actual==known_motors|estimated,(key,actual^(known_motors|estimated))
        summary=f'模型标出 {len(actual)} 处电机位置。厂家资料支持其中 {len(known_motors)} 处的工位驱动归属，另有 {len(estimated-known_motors)} 处按机构功能推定。'
        stage={k:rec[k] for k in ('id','name','equipment','en','section','input','output','process','quality','summary','sources')}
        stage.update(group=rec['section'],optional=True,drive=[s['electric'] for s in rec['routes']],note=rec['configuration'])
        process['stages'].append(stage)
        drive['items'].append(dict(id=key,summary=summary,evidenceNote='数量指所选模型中的动力工位。逐条路线列明公开证据、推定安装和未披露项目。',routes=routes))
        provenance['items'].append(dict(id=key,name=rec['name'],referenceManufacturer=rec['maker'],referenceModel=rec['model'],
             referenceConfiguration=rec['configuration'],configurationStatus='依据厂家在列产品及该机型公开资料选择配置。',
             currentFinding='本次核对的厂家产品页和技术资料见下方。',configSource=config_files[key],
             modelVersion=root['modelVersion'],driveRevision=root['driveRevision'],motorDetailScope='external_only',
             fidelityStatus='partial_public_reference',structuralCompleteness=False,selectedCounts=rec['counts'],
             verified=rec['verified'],inferred=rec['inferred'],missing=rec['missing'],sources=sources))
        provenance['assets'][key]=dict(bytes=len(asset),sha256=hashlib.sha256(asset).hexdigest(),
                                      **{k:root[k] for k in ('modelVersion','referenceModel','driveRevision','motorDetailScope')})
        catalog['stages'].append(dict(id=key,question='哪些工位由电机驱动，动力传到哪些机构？',coverage=summary,rows=rows))
        coverage.append(dict(id=key,name=rec['name'],position=rec['maker']+' '+rec['model'],reason=summary,source=sources[0]))
    # Preserve the earlier cross-manufacturer rows and their references in the appropriate equipment sections.
    for old_id,new_id,model in [('spinning','airjet_spinning','J 70'),('drawing_in','warp_tying','TIEPRO')]:
        old=next(s for s in catalog['stages'] if s['id']==old_id);new=next(s for s in catalog['stages'] if s['id']==new_id)
        old_rows=[row for row in old['rows'] if row['model']==model]
        if not old_rows:
            previous=next((s for s in read(DIST/'motor-applications.json')['stages'] if s['id']==new_id),{})
            old_rows=[row for row in previous.get('rows',[]) if row.get('legacyComparison')]
        for row in old_rows:
            row['legacyComparison']=True
            if row in old['rows']:old['rows'].remove(row)
            new['rows'].append(row)
    next(s for s in catalog['stages'] if s['id']=='spinning')['coverage']='环锭分为锭带、分段切向带或共用长切向带传动。转杯纺和喷气纺另设独立设备。'
    next(s for s in catalog['stages'] if s['id']=='drawing_in')['coverage']='穿经工作站将经纱穿过停经片、综眼及钢筘。换轴时连接新旧经纱的工位见自动结经机。'
    audit=process.get('coverageReview',{})
    process['coverageReview']={'finding':'已将此次核查的七类设备分别建模，点击名称可直达各机的电机和工作机构。','modeled':coverage,'candidates':[],
                               'covered':audit.get('covered',[])}
    process.update(researchedAt=DATE,assetVersion=VERSION)
    drive.update(checkedAt=DATE,assetVersion=VERSION);catalog['checkedAt']=DATE
    provenance.update(checkedAt=DATE,assetVersion=VERSION,configuredMachineCount=len(process['stages']),
                      configurationFiles=unique(provenance['configurationFiles']+list(config_files.values())),
                      assetManifestRecordedAt=datetime.now(timezone.utc).isoformat())
    for name,value in [('process-data.json',process),('equipment-provenance.json',provenance),
                       ('drive-chains.json',drive),('motor-applications.json',catalog)]:write(name,value)
    subprocess.run([sys.executable,str(ROOT/'scripts/build_motor_applications.py')],check=True)
    print(f'{len(records)} new equipment models, {sum(len(rec["routes"]) for rec in records.values())} new drive routes')

if __name__=='__main__':main()
