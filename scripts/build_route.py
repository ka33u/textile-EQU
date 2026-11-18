"""Draw the clickable cotton, weaving, finishing and optional yarn-processing routes."""
from html import escape
from pathlib import Path

out=Path(__file__).resolve().parents[1]/'dist/assets/process-route.svg'
height=1640
parts=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{height}" viewBox="0 0 1440 {height}" role="img" aria-labelledby="title desc">
<title id="title">纺织装备工艺路线与驱动工位</title><desc id="desc">棉纺、机织、染整及各条品种分支，设备框可打开本机传动模型。</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M1 1L6 4L1 7" fill="none" stroke="#bc663e" stroke-width="1.5"/></marker></defs>
<style>text{{font-family:system-ui,-apple-system,'PingFang SC',sans-serif;fill:#173237}}.head{{font-size:31px;font-weight:700}}.section{{font-size:23px;font-weight:650}}.lead{{font-size:18px;font-weight:600}}.title{{font-size:19px;font-weight:650}}.note{{font-size:15px;fill:#516964}}a:hover rect,a:focus rect{{stroke:#b2542b;stroke-width:3}}</style>
<rect width="1440" height="{height}" fill="#f4f4ee"/>''']

def text(x,y,label,cls):
    parts.append(f'<text x="{x}" y="{y}" class="{cls}">{escape(label)}</text>')

def section(y,name):
    parts.append(f'<path d="M44 {y-28}H1396" stroke="#cbd4ce"/>')
    text(44,y+5,name,'section')

def row(y,label,steps):
    text(44,y+6,label,'lead')
    left=260;gap=28;width=min(266,(1384-left-gap*(len(steps)-1))/len(steps))
    for i,(ident,name,sub) in enumerate(steps):
        x=left+i*(width+gap);cx=x+width/2
        if i:
            parts.append(f'<path d="M{x-gap+3:.2f} {y}H{x-6:.2f}" fill="none" stroke="#bc663e" stroke-width="2" marker-end="url(#arrow)"/>')
        if ident:parts.append(f'<a href="../#{ident}/drive" aria-label="查看{escape(name)}的驱动工位">')
        parts.append(f'<rect x="{x:.2f}" y="{y-29}" width="{width:.2f}" height="60" rx="7" fill="{"#fff" if ident else "#e8ede5"}" stroke="#bdccc2"/>')
        parts.append(f'<text x="{cx:.2f}" y="{y-4}" text-anchor="middle" class="title">{escape(name)}</text><text x="{cx:.2f}" y="{y+18}" text-anchor="middle" class="note">{escape(sub)}</text>')
        if ident:parts.append('</a>')

text(44,57,'纺织装备工艺路线与驱动工位','head')
text(44,88,'点击设备框可进入三维传动视图。各行标出适用路线，同一台设备可服务于多种工艺。','note')
section(151,'棉纺与纱线加工')
row(213,'环锭纱主线',[('opening','开清棉','开松与混合'),('carding','梳棉','生条'),('drawing','并条','匀整条子'),('roving','粗纱','粗纱管'),('spinning','环锭细纱','管纱'),('winding','自动络筒','筒子纱')])
row(293,'精梳品种',[('drawing','预并条','条子准备'),('combing','成卷及精梳','E 40 与 E 90 机组'),('drawing','精梳后并条','并合与匀整'),('roving','粗纱','进入细纱路线')])
row(373,'紧密纺品种',[('roving','粗纱','喂入粗纱'),('compact_spinning','紧密纺','集聚后环锭成纱'),('winding','自动络筒','筒子纱')])
row(453,'转杯成纱',[('drawing','条子准备','熟条'),('rotor_spinning','气流纺／转杯纺','分梳与转杯凝聚'),(None,'转杯纱筒子','用于整经或供纬')])
row(533,'喷气成纱',[('drawing','条子准备','熟条'),('airjet_spinning','喷气纺','牵伸与喷嘴成纱'),(None,'喷气纱筒子','用于整经或供纬')])
row(613,'股线加工',[(None,'单纱筒子','两根或多根单纱'),('assembly_winding','并纱','平行合股卷装'),('twisting','倍捻','加捻股线')])
row(693,'化纤长丝加工',[(None,'预取向丝','POY'),('texturing','假捻加弹','牵伸、加热与假捻'),(None,'变形长丝','DTY')])

section(784,'经纱准备与机织')
row(848,'经纱通道',[('warping','整经','筒纱形成经轴'),('sizing','浆纱','按品种上浆'),('drawing_in','穿综穿筘','建立经纱路径'),('weaving','机织','经、纬交织')])
row(928,'沿用穿法换轴',[(None,'新旧经片','织机换经轴'),('warp_tying','自动结经','逐根对应打结'),('weaving','机织','接续生产')])
row(1008,'纬纱通道',[(None,'适用筒子纱','按织机要求备纬'),('weaving','机织','供纬与引纬')])

section(1104,'连续染整与成品检验')
row(1167,'前处理选配',[('singeing','烧毛','布面毛羽处理'),('pretreatment','湿前处理','退浆、煮练、漂白'),('mercerizing','丝光','按品种进行碱处理')])
row(1247,'冷轧堆染色',[('dyeing','冷轧堆','浸轧及堆置固色'),('washing_range','平幅水洗／皂洗','染后独立水洗'),('stenter','拉幅整理','干燥及幅宽控制')])
row(1327,'布面整理选配',[('stenter','拉幅整理','按材料选择热定型'),('calender','轧光','调节布面光泽'),('inspection','织物疵点检测','成品检测与复核')])
row(1407,'尺寸稳定整理',[('stenter','拉幅整理','准备待预缩布'),('sanforizing','橡毯预缩','经向压缩与稳定'),('inspection','织物疵点检测','成品检测与复核')])
text(44,1515,'烧毛、丝光、轧光和预缩均按织物及产品要求选用。前处理、染色和后整理的具体组合见各设备工艺说明。','note')
text(44,1560,'三维页面可查询厂家型号、选定配置、电机及执行机构的资料来源。','note')
parts.append('</svg>')
out.write_text('\n'.join(parts),encoding='utf-8')
