import urllib.request, concurrent.futures, json
from pathlib import Path
P=Path(__file__).parent/'visual-sources';P.mkdir(exist_ok=True)
sources={
'calender.pdf':'https://www.andritz.com/resource/blob/299446/80243e217ab3aca4d81c1611e62ee64b/brochure-textile-keep-profits-rolling-with-calenders-2023--data.pdf',
'weaving.pdf':'https://www.picanol.be/sites/picanol/files/2021-11/pic_optimax-i-connect_brochure_2021_en_0.pdf',
'carding.pdf':'https://www.rieter.com/fileadmin/user_upload/products/documents/systems/fiber-preparation/c-81/rieter-c-81-card-brochure-3586-v1-98697-en.pdf',
'spinning.pdf':'https://www.rieter.com/fileadmin/user_upload/products/documents/systems/end-spinning/rieter-g-38-ring-spinning-machine-brochure-3236-v5-100402-en.pdf',
'stenter.webp':'https://www.monforts.de/wp-content/uploads/2025/09/montex-8500-vaz-da-costa-05.webp',
'stenter-detail.webp':'https://www.monforts.de/wp-content/uploads/2025/09/header-spannrahmen-8500-detail-3.webp',
'stenter-line.webp':'https://www.monforts.de/wp-content/uploads/2025/09/montex-8500-gta-linie-2-15-kopie.webp',
}
data=json.loads((Path(__file__).parent/'process-data.json').read_text())
for s in data['stages']:
 if s['id'] not in ['weaving','carding','spinning','calender','stenter']:
  source=s['sources'][0]['url']
  sources[s['id']+('.pdf' if '.pdf' in source else '.html')]=source
sources['motor.pdf']=data['motor']['sources'][0]['url']
def dl(kv):
 name,url=kv
 if (P/name).exists():return {'file':name,'url':url,'status':'exists'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  body=urllib.request.urlopen(req,timeout=50).read()
  (P/name).write_bytes(body)
  return {'file':name,'url':url,'status':'downloaded','bytes':len(body)}
 except Exception as e:return {'file':name,'url':url,'status':'failed','error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 rows=list(ex.map(dl,sources.items()))
(P/'downloads.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
for x in rows:print(x['file'],x['status'],x.get('bytes',x.get('error','')))
