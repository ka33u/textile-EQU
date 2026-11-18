# -*- coding: utf-8 -*-
import json,struct,hashlib,re,datetime
from pathlib import Path
base=Path(__file__).resolve().parents[1]
data_path=base/'research/drive-extensions-v5.json'
config_path=base/'research/config-extensions-v5.json'
process_path=base/'research/process-extensions-v5.json'
raw=data_path.read_bytes();data=json.loads(raw)
config=json.loads(config_path.read_bytes());process=json.loads(process_path.read_bytes())
expected={'compact_spinning','texturing','twisting'}
issues=[];reviews=[]
def issue(stage,kind,**kw):issues.append({'stage':stage,'kind':kind,**kw})
def sanitize(s):return re.sub(r'[\[\]\.:/]', '',s).replace(' ','_')
for source,items in [('drives',data.get('items',[])),('config',config.get('items',[])),('process',process.get('stages',[]))]:
 ids=[i.get('id') for i in items]
 if set(ids)!=expected or len(ids)!=3:issue(None,'stage_coverage',source=source,ids=ids)
for item in data['items']:
 stage=item['id'];model=base/'qa/v5-candidates/models'/f'{stage}.glb';before=model.stat();blob=model.read_bytes();after=model.stat()
 if before.st_mtime_ns!=after.st_mtime_ns or before.st_size!=after.st_size:issue(stage,'candidate_changed_during_read')
 assert blob[:4]==b'glTF';size,kind=struct.unpack_from('<II',blob,12);assert kind==0x4e4f534a
 glb=json.loads(blob[20:20+size]);nodes=glb.get('nodes',[])
 byname={};byanchor={};bysanitized={}
 for index,node in enumerate(nodes):
  name=node.get('name','');anchor=node.get('extras',{}).get('driveAnchorId')
  if name:
   byname.setdefault(name,[]).append(index);bysanitized.setdefault(sanitize(name),[]).append(index)
  if anchor:byanchor.setdefault(str(anchor),[]).append(index)
 motors={i for i,n in enumerate(nodes) if n.get('extras',{}).get('driveRole')=='motor'}
 covered=set();route_records=[];unknowns=[];anchor_total=0
 for route in item.get('routes',[]):
  steps=route.get('steps',[])
  if len(steps)<3:issue(stage,'route_too_short',route=route.get('id'))
  if not steps or steps[0].get('role')!='motor':issue(stage,'route_missing_motor_start',route=route.get('id'))
  if 'transmission' not in [s.get('role') for s in steps] or 'load' not in [s.get('role') for s in steps]:issue(stage,'route_missing_required_roles',route=route.get('id'))
  graph=route.get('graph',{})
  if graph.get('physicalConnectionClaim') is not False:issue(stage,'physical_graph_claim_not_false',route=route.get('id'))
  rs=[]
  for si,step in enumerate(steps):
   anchors=step.get('anchorIds',[]);patterns=step.get('match',[]);resolved=set();missing=[];ambiguous=[];exact=0;alias=0;fallback=0
   for a in anchors:
    anchor_total+=1
    if a in byanchor:found=byanchor[a];alias+=1
    elif a in byname:found=byname[a];exact+=1
    else:found=bysanitized.get(sanitize(a),[]);fallback+=bool(found)
    if not found:missing.append(a)
    if len(found)>1:ambiguous.append({'anchorId':a,'indices':found})
    resolved.update(found)
   if missing:issue(stage,'partial_or_full_anchor_mismatch',route=route['id'],stepIndex=si,missing=missing,totalDeclared=len(anchors))
   if ambiguous:issue(stage,'ambiguous_anchor',route=route['id'],stepIndex=si,anchors=ambiguous)
   if anchors and len(anchors)!=len(set(anchors)):issue(stage,'duplicate_anchor_within_step',route=route['id'],stepIndex=si)
   if not anchors and patterns:
    for p in patterns:
     hits={i for i,n in enumerate(nodes) if str(p).lower() in n.get('name','').lower() or str(p).lower() in str(n.get('extras',{}).get('label','')).lower()}
     if not hits:issue(stage,'unmatched_pattern',route=route['id'],stepIndex=si,pattern=p)
     resolved.update(hits)
   if step.get('role')=='motor':
    covered.update(resolved&motors)
    if resolved-motors:issue(stage,'motor_step_targets_non_motor',route=route['id'],stepIndex=si,names=[nodes[i].get('name') for i in sorted(resolved-motors)])
   if not anchors and not patterns:
    unknowns.append({'route':route['id'],'stepIndex':si,'label':step.get('label')})
    if step.get('role')!='motor' and step.get('connectionStatus')!='unmodeled':issue(stage,'empty_nonmotor_step_not_explicit_unmodeled',route=route['id'],stepIndex=si)
   if si and step.get('connectionStatus') not in ['unmodeled','functional_inference']:issue(stage,'incoming_connection_status_missing',route=route['id'],stepIndex=si)
   rs.append({'stepIndex':si,'role':step.get('role'),'label':step.get('label'),'declaredAnchorCount':len(anchors),'matchedAnchorCount':len(anchors)-len(missing),'resolvedNodeCount':len(resolved),'driveAnchorMatches':alias,'exactNameMatches':exact,'sanitizedFallbackMatches':fallback,'connectionStatus':step.get('connectionStatus'),'missingAnchorIds':missing})
  route_records.append({'id':route['id'],'steps':rs})
 uncovered=motors-covered
 if uncovered:issue(stage,'unassigned_model_motor',names=[nodes[i].get('name') for i in sorted(uncovered)])
 root=next((n for n in nodes if n.get('extras',{}).get('stage')==stage),{})
 attrs=root.get('extras',{})
 if attrs.get('driveRevision')!='5.0':issue(stage,'unexpected_drive_revision',value=attrs.get('driveRevision'))
 if attrs.get('modelVersion')!='3.0':issue(stage,'unexpected_model_version',value=attrs.get('modelVersion'))
 if attrs.get('structuralCompleteness') is not False:issue(stage,'completeness_not_false')
 rec={'id':stage,'candidatePath':str(model.relative_to(base)),'candidateSha256':hashlib.sha256(blob).hexdigest(),'candidateBytes':len(blob),'candidateMtimeNs':after.st_mtime_ns,'candidateStableDuringRead':before.st_mtime_ns==after.st_mtime_ns and before.st_size==after.st_size,'nodeCount':len(nodes),'routeCount':len(route_records),'declaredAnchorOccurrences':anchor_total,'motorCount':len(motors),'assignedMotorCount':len(covered),'unassignedMotorNames':[nodes[i].get('name') for i in sorted(uncovered)],'allModelMotorNames':[nodes[i].get('name') for i in sorted(motors)],'intentionallyUnmodeledSteps':unknowns,'routeChecks':[{'id':r['id'],'stepCount':len(r['steps']),'declaredAnchorCount':sum(s['declaredAnchorCount'] for s in r['steps']),'matchedAnchorCount':sum(s['matchedAnchorCount'] for s in r['steps']),'sanitizedFallbackMatches':sum(s['sanitizedFallbackMatches'] for s in r['steps'])} for r in route_records]}
 reviews.append(rec)
report={'schemaVersion':1,'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only verification of all three v5 extension data items against actual candidate GLB nodes','dataPath':str(data_path.relative_to(base)),'dataSha256':hashlib.sha256(raw).hexdigest(),'checks':{'everyDeclaredAnchorCheckedIndividually':True,'partialAnchorMismatchIsFailure':True,'ambiguousAnchorIsFailure':True,'motorCoverageUsesActualDriveRoleMetadata':True,'emptyUnknownStepsNotInvented':True,'modelVersionsAndCompletenessChecked':True},'passed':not issues,'issueCount':len(issues),'issues':issues,'totalRoutes':sum(x['routeCount'] for x in reviews),'totalModelMotors':sum(x['motorCount'] for x in reviews),'totalAssignedModelMotors':sum(x['assignedMotorCount'] for x in reviews),'totalDeclaredAnchorOccurrences':sum(x['declaredAnchorOccurrences'] for x in reviews),'items':reviews,'limitations':['Node correspondence is checked; OEM geometry and real motor counts are not verified.','Rerun after candidate export; report records candidate and data SHA-256.','Intentionally unmodeled connections remain explicit.']}
out=base/'qa/drive-anchor-validation-v5.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['passed','issueCount','totalRoutes','totalModelMotors','totalAssignedModelMotors','totalDeclaredAnchorOccurrences']},ensure_ascii=False))
for i in reviews:print(i['id'],i['candidateSha256'],i['motorCount'],i['assignedMotorCount'])
for i in issues:print(json.dumps(i,ensure_ascii=False))
raise SystemExit(bool(issues))
