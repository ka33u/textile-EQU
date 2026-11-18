import json,re,urllib.parse,subprocess,concurrent.futures
from pathlib import Path
P=Path(__file__).parent/'visual-sources'
pages={
 'spinning':'https://www.rieter.com/products/systems/ring-spinning-machines/ring-spinning-machine-g-38',
 'carding':'https://www.rieter.com/products/system-applications/man-made-fiber-spinning-system',
 'drawing':'https://www.rieter.com/products/systems/spinning-preparation/draw-frame-rsb-dsb-d-55',
 'weaving':'https://www.picanol.be/en/machines-features/machines',
 'drawing_in':'https://www.staubli.com/global/en/textile/products/drawing-in-machine/safir-s80.html',
}
def get(row):
 name,url=row
 if not (P/name).exists():
  c=subprocess.run(['curl','-L','--max-time','50','--retry','0','-A','Mozilla/5.0','-o',str(P/name),url],capture_output=True)
  if c.returncode: return {'file':name,'url':url,'ok':False,'error':c.stderr.decode()[-150:]}
 return {'file':name,'url':url,'ok':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
 print(list(ex.map(get,[(k+'.html',v) for k,v in pages.items()])),flush=True)
data=json.loads((Path(__file__).parent/'process-data.json').read_text())
for s in data['stages']:pages.setdefault(s['id'],s['sources'][0]['url'])
rows=[]
for f in P.glob('*.html'):
 if f.stem=='stenter':continue
 html=f.read_text(errors='ignore');seen=set()
 for t in re.findall(r'<img\b[^>]*>',html):
  m=re.search(r'(?:data-src|src)=["\']([^"\']+)',t)
  if not m:continue
  src=m.group(1)
  if any(k in src.lower() for k in ['logo','flag','icon','svg','placeholder','avatar']):continue
  if not re.search(r'\.(?:jpg|png|webp|jpeg)(?:\?|$)',src):continue
  if src in seen:continue
  seen.add(src)
  alt=re.search(r'alt=["\']([^"\']*)',t)
  rows.append({'file':f.stem+'-photo-'+str(len(seen))+Path(urllib.parse.urlparse(src).path).suffix,'url':urllib.parse.urljoin(pages[f.stem],src),'alt':alt.group(1) if alt else ''})
  if len(seen)>=5:break
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
 results=list(ex.map(get,[(r['file'],r['url']) for r in rows]))
for a,b in zip(rows,results):a.update(b)
(P/'photos.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
for r in rows:print(r['file'],r['ok'],r['alt'],flush=True)
