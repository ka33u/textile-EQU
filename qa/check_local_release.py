"""Verify deployed bytes and version-sensitive caching on the local viewer."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, urllib.request

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:4173/'
parser=argparse.ArgumentParser()
parser.add_argument('--output',default='qa/local-deployment.json')
args=parser.parse_args()
VERSION=json.loads((ROOT/'dist/model-variants.json').read_text())['checkedAt']+'-models'
paths=['index.html','model-library.js','model-variants.json','app.js','style.css','ui-data.js','drive-view.js','drive-chains.json',
       'equipment-provenance.json','process-data.json','camera-fit.js','scene-geometry.js','texturing-motion.js','model-rendering.js','rotor-motion.js','station-motion.js','station-yarn.js','assets/process-route.svg','motor-applications.html','motor-applications.json']
paths += [str(p.relative_to(ROOT/'dist')) for p in sorted((ROOT/'dist/assets/models').glob('*.glb'))]
paths += [str(p.relative_to(ROOT/'dist')) for p in sorted((ROOT/'dist/assets/variants').iterdir()) if p.suffix in ('.glb','.json')]
rows=[];errors=[]
for path in paths:
    expected=(ROOT/'dist'/path).read_bytes()
    try:
        with urllib.request.urlopen(URL+path+'?revision='+VERSION,timeout=20) as response:
            actual=response.read();cache=response.headers.get('Cache-Control','')
            row={'path':path,'status':response.status,'bytes':len(actual),
                 'sha256':hashlib.sha256(actual).hexdigest(),'diskBytesMatch':actual==expected,'cacheControl':cache}
            if actual!=expected or response.status!=200 or 'no-store' not in cache:errors.append(path)
    except Exception as exc:
        row={'path':path,'error':str(exc)};errors.append(path)
    rows.append(row)
for path in [p for p in paths if p.endswith('.glb')]:
    expected=hashlib.sha256((ROOT/'dist'/path).read_bytes()).hexdigest()
    for digest,required in [(expected[:16],'immutable'),('0'*16,'no-store')]:
        try:
            req=urllib.request.Request(URL+path+'?sha='+digest,method='HEAD')
            with urllib.request.urlopen(req,timeout=20) as response:
                actual=response.headers.get('Cache-Control','')
                rows.append({'path':path,'fingerprint':digest,'cacheControl':actual})
                if required not in actual:errors.append(path+'?sha='+digest)
        except OSError as exc:
            errors.append(path+'?sha='+digest+': '+str(exc))
report={'checkedAt':datetime.now(timezone.utc).isoformat(),'url':URL,'assetVersion':VERSION,
        'status':'fail' if errors else 'pass','files':rows,'errors':errors}
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':report['status'],'files':len(rows),'errors':errors},ensure_ascii=False))
raise SystemExit(bool(errors))
