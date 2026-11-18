"""Validate exported exterior-only motors and live drive route coverage.
Checks do not certify an OEM transmission layout or hidden mechanical design.
"""
import argparse, hashlib, json, re, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--models-dir',default='dist/assets/models');p.add_argument('--output',default='qa/drive-validation-v4.json');args=p.parse_args()
model_dir=ROOT/args.models_dir
ids=[s['id'] for s in json.loads((ROOT/'dist/process-data.json').read_text())['stages']]
report={'validationScope':'Motor exterior geometry, preserved anchor transforms, route-to-node links and explicit unmodeled steps; not OEM layout verification','models':[],'errors':[],'structuralCompleteness':False}
def check(ok,msg):
 if not ok:report['errors'].append(msg)
def read(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),hashlib.sha256(raw).hexdigest()
def descend(nodes,index):
 out=[];todo=list(nodes[index].get('children',[]))
 while todo:
  i=todo.pop();out.append(nodes[i]);todo.extend(nodes[i].get('children',[]))
 return out
def step_matches(node,step):
 exact=step.get('anchorIds',[])
 if exact:return node.get('name') in exact or node.get('extras',{}).get('driveAnchorId') in exact
 label=node.get('name','')+' '+str(node.get('extras',{}).get('label',''))
 return any(str(s).lower() in label.lower() for s in step.get('match',[]) if s)
data=json.loads((ROOT/'dist/drive-chains.json').read_text());items={item['id']:item for item in data['items']}
check(set(items)==set(ids),'Drive data must cover all declared equipment stages')
for ident in ids:
 if not (model_dir/(ident+'.glb')).is_file():check(False,ident+': missing GLB');continue
 gltf,sha=read(model_dir/(ident+'.glb'));nodes=gltf['nodes'];backup=ROOT/'blender/v3-backup/models'/(ident+'.glb')
 old,_=read(backup) if backup.exists() else ({'nodes':[]},None);old_by_name={n.get('name'):n for n in old['nodes']}
 motors=[(i,n) for i,n in enumerate(nodes) if n.get('extras',{}).get('driveRole')=='motor']
 row={'id':ident,'sha256':sha,'motorCount':len(motors),'motors':[],'routes':[]};report['models'].append(row)
 roots=[n for n in nodes if n.get('name')=='stage_'+ident]
 check(len(roots)==1,ident+': unique root')
 if roots:check(roots[0].get('extras',{}).get('motorDetailScope')=='external_only',ident+': exterior scope missing')
 for i,n in motors:
  name=n['name'];sub=descend(nodes,i);geometry=[o for o in [n]+sub if 'mesh' in o]
  check(bool(geometry),ident+': motor without geometry '+name)
  forbidden=[o['name'] for o in [n]+sub if re.search(r'stator|rotor_unit|winding|copper_slot|slot_insulation|bearing_ball|bearing_race|定子|转子|绕组',o.get('name','')+' '+o.get('extras',{}).get('label',''),re.I)]
  check(not forbidden,ident+': motor anatomy remains '+str(forbidden))
  old_node=old_by_name.get(name)
  if backup.exists():check(old_node is not None,ident+': original motor anchor renamed '+name)
  else:check(ident in ['compact_spinning','twisting','texturing','rotor_spinning'] or
             (roots and roots[0].get('extras',{}).get('stationDriveModel') is True),ident+': unexpected missing baseline')
  if old_node:
   for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
    a=n.get(key,default);b=old_node.get(key,default);check(len(a)==len(b) and all(abs(x-y)<1e-5 for x,y in zip(a,b)),ident+': changed motor '+key+' '+name)
  row['motors'].append({'name':name,'meshNodes':len(geometry),'forbiddenInteriorNodes':forbidden})
 item=items.get(ident,{})
 check(bool(item.get('routes')),ident+': no route records')
 route_ids=[]
 for route in item.get('routes',[]):
  route_ids.append(route['id']);steps=route.get('steps',[]);check(len(steps)>=3,ident+': incomplete logical path '+route['id'])
  check([s['role'] for s in steps][0]=='motor' and steps[-1]['role']=='load',ident+': drive ordering '+route['id'])
  check(bool(route.get('evidence',{}).get('note')),ident+': missing route evidence note '+route['id'])
  details=[]
  for step in steps:
   matched=[n for n in nodes if step_matches(n,step)]
   if step.get('match') or step.get('anchorIds'):check(bool(matched),ident+'/'+route['id']+': dead selector '+step['label'])
   details.append({'role':step['role'],'label':step['label'],'matchedNodes':len(matched),'modeled':bool(matched)})
  row['routes'].append({'id':route['id'],'steps':details})
 check(len(set(route_ids))==len(route_ids),ident+': duplicate route ids')
 covered=set()
 for route in item.get('routes',[]):
  for step in route.get('steps',[]):
   if step.get('role')=='motor':covered.update(n['name'] for _,n in motors if step_matches(n,step))
 missing=[n['name'] for _,n in motors if n['name'] not in covered]
 row['unassignedMotors']=missing
 check(not missing,ident+': motors absent from workstations '+str(missing))
report['motorCount']=sum(m['motorCount'] for m in report['models']);report['routeCount']=sum(len(m['routes']) for m in report['models']);report['status']='fail' if report['errors'] else 'pass'
out=ROOT/args.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='models'},ensure_ascii=False,indent=2));raise SystemExit(bool(report['errors']))
