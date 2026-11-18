"""Independent contract check for the three selected full equipment branches."""
from pathlib import Path
import argparse,hashlib,json,re,struct
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--models-dir',default='dist/assets/models');p.add_argument('--output',default='qa/extensions-validation-v5.json');args=p.parse_args()
required={'compact_spinning':288,'twisting':20,'texturing':384};errors=[];rows=[]
def check(ok,msg):
 if not ok:errors.append(msg)
def read_glb(path):
 raw=path.read_bytes();magic,version,length=struct.unpack_from('<III',raw);check(magic==0x46546c67 and version==2 and length==len(raw),str(path)+': invalid GLB')
 n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw
for stage,count in required.items():
 path=ROOT/args.models_dir/(stage+'.glb')
 if not path.exists():check(False,stage+': missing file');continue
 gltf,raw=read_glb(path);nodes=gltf['nodes'];roots=[n for n in nodes if n.get('name')=='stage_'+stage]
 check(len(roots)==1,stage+': root identity')
 if not roots:continue
 meta=roots[0].get('extras',{});check(meta.get('equipmentId')==stage,stage+': equipment identity');check(meta.get('modelVersion')=='3.0',stage+': public-reference generation');check(meta.get('driveRevision')=='5.0',stage+': drive revision');check(meta.get('motorDetailScope')=='external_only',stage+': motor scope');check(meta.get('structuralCompleteness') is False,stage+': unsupported completeness claim')
 for key in ['referenceManufacturer','referenceModel','referenceConfiguration']:check(bool(meta.get(key)),stage+': missing '+key)
 positions=[n for n in nodes if isinstance(n.get('extras',{}).get('positionIndex'),int)]
 # Every selected position must remain an independently identifiable assembly.
 indexes=[n['extras']['positionIndex'] for n in positions]
 check(sorted(indexes)==list(range(1,count+1)),stage+': selected position population/index set')
 check(all(n.get('children') for n in positions),stage+': empty position placeholder')
 motors=[n for n in nodes if n.get('extras',{}).get('driveRole')=='motor']
 check(bool(motors),stage+': no drive position visible')
 for n in motors:
  e=n.get('extras',{});check(e.get('internalGeometryModeled') is False,stage+': motor interior');check(e.get('driveAnchorId')==n['name'],stage+': unstable motor anchor')
 def names(prefix):return [n for n in nodes if re.fullmatch(re.escape(prefix)+r'(?:\.\d+)?',n.get('name',''))]
 if stage=='compact_spinning':
  for prefix,total in [('K48_compact_position',288),('K48_perforated_compacting_drum',288),('K48_Detect_air_guide',288),('K48_four_spindle_tape_group',72),('K48_48_spindle_section',6)]:check(len(names(prefix))==total,stage+': '+prefix+' population')
  for role in ['compacting_suction_branch','doffer_working_set','drafting_working_set','ringrail_working_set']:
   check(sum(n.get('extras',{}).get('componentRole')==role and bool(n.get('children')) for n in nodes)==288,stage+': separately selectable '+role)
 if stage=='texturing':
  for role in ['EFK_active_POY_package','continuous_yarn_path','dty_package','takeup_position','friction_unit','G1_godet','G2_godet']:
   check(sum(n.get('extras',{}).get('componentRole')==role for n in nodes)==384,stage+': complete '+role)
  for role,length in [('primary_channel',2.0),('cooling_channel',1.1),('secondary_channel',1.46)]:
   channels=[n for n in nodes if n.get('extras',{}).get('componentRole')==role and n.get('children')]
   check(len(channels)==384,stage+': complete '+role)
   check(all(abs(n.get('extras',{}).get('measuredPathLengthMetres',0)-length)<1e-5 for n in channels),stage+': '+role+' length metadata')
 rows.append({'id':stage,'referenceModel':meta.get('referenceModel'),'positions':len(positions),'motors':len(motors),'nodes':len(nodes),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
# The pre-existing 16 models are not rebuilt or silently substituted by additions.
old=json.loads((ROOT/'blender/v4-backup/equipment-provenance.json').read_text())
unchanged=[]
for ident,asset in old['assets'].items():
 if ident=='motor':continue
 path=ROOT/'dist/assets/models'/(ident+'.glb');same=hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256'];check(same,ident+': existing v4 asset changed');unchanged.append(ident)
report={'status':'fail' if errors else 'pass','scope':'Actual selected position counts, identity, exterior drive anchors and preservation of previous assets; not OEM hidden assembly completeness','models':rows,'preservedOriginalEquipment':unchanged,'structuralCompleteness':False,'errors':errors}
out=ROOT/args.output;out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
