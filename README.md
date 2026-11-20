# 纺织装备工艺与传动交互演示系统

系统覆盖棉纺、机织、染整及纱线加工的 **27 类设备、43 个机型条目、18 家厂商**。其中 42 个条目展示所选整机配置，巴马格 eFK EvoSmart 展示厂家已披露的工位。点选某个电机可查看安装位置、带动的机构、传动依据及运动示意。

## 本地运行

在项目根目录运行以下命令，然后打开 [本地演示系统](http://127.0.0.1:4173/)。

```sh
npm start
```

也可直接执行 `python3 scripts/serve.py`。可运行文件都在 `dist/`，包含 Three.js、设备模型、流程图和研究资料。通过静态 HTTP 服务即可使用，运行期间无需访问 CDN。

## 按厂家和机型切换

在三维窗口上方先选「厂家 / 品牌」，再选「机型」。结构视图、传动视图、GLB 下载、工艺说明和研究记录会一起切换。首页「查找厂家与机型」支持按工序、品牌和关键词检索。地址栏保存当前机型和视图，可直接分享。各型号的发布时间、资料版次和核查日期见「型号与配置」。本次资料核查于 2026 年 11 月 20 日完成。

| 工序 | 新增机型 | 可对照的传动功能 |
|---|---|---|
| 梳棉 | 经纬青岛宏大 JWF1217 | 锡林永磁同步直联、刺辊和盖板变频、五组伺服工位，可与立达 C 81 对照 |
| 并条 | 经纬沈阳宏大华明 JWF1366Pro、立达 RSB-D 27 | 单眼差速匀整与双眼独立牵伸，各眼圈条、筒底盘、吸风及换筒 |
| 环锭细纱 | 经纬 JWF1590A、卓郎 Zinser 51、马佐里 MDS2、丰田 RX300E | 与立达 G 38 FE 对照四锭锭带、切向带分区、牵伸电机、钢领板升降及落纱 |
| 转杯纺 | 浙江泰坦 TQF-K90、卓郎 Autocoro 11 和 BD 8、立达 R 37 | 逐位转杯、步进喂棉、分梳和卷绕，各款可追踪的传动不同。可与立达 R 70 对照 |
| 喷气纺 | 卓郎 Autoairo | 牵伸、气动成纱、导纱、卷绕与落筒，可与立达 J 70 对照 |
| 剑杆织造 | 浙江泰坦 TT-868 | 直驱主轴、伺服送经和卷取、步进绞边、机械打纬与引纬 |
| 假捻加弹 | 越剑 YJ1000V-240、巴马格 eAFK HQ、巴马格 eFK EvoSmart | 前两款分别为 240 和 576 纱位。EvoSmart 提供 Smart Godet 导丝盘和 EvoHeater 工位，原有 eFK 384 位整机亦可选 |

例如，打开 [立达 RSB-D 27 双眼并条机传动](http://127.0.0.1:4173/#drawing/drive/rieter_rsb_d27)，选择「两眼主牵伸」后即可在两个电机间切换。在同一工序改选经纬 JWF1366Pro，可以检查匀整伺服与差速机构的连接。从「设备结构」进入加弹机的「纱线路径」可选择一根纱，运行并近看其在模型中的路径。

### 环锭细纱机的传动对照

打开「环锭细纱」，切换厂家后，在「传动链 / 驱动工位」选择一路。工作机构选项列出全机锭号和所在侧，点击「定位所选机构」即可近看。下表列出四台新增整机的选定锭数。

| 厂家和机型 | 选定锭数 | 可核对的传动差异 | 原厂资料 |
|---|---:|---|---|
| [经纬 JWF1590A](http://127.0.0.1:4173/#spinning/drive/jingwei_jwf1590a) | 1,440 | 每根锭带带四锭。全电子分段牵伸、螺杆升降和钢带集体落纱可分别查看。分段配套电机的实际数量待核。 | [经纬官网及联合样本](https://www.jwgf.com/cpfw/mfjx/xsj/jwzn/202607/t20260731_648822.html) |
| [卓郎 Zinser 51](http://127.0.0.1:4173/#spinning/drive/saurer_zinser_51_ring) | 288 | 选六节常规三罗拉机，展示切向锭带、NSD-i 牵伸、Optisuction 吸风和 Cowemat 396 F 落纱。当前模型依据 2025 年 10 月样本，2026 年 11 月的换代公告另列于型号说明。 | [常规机型资料](https://saurer.com/en/products/machines/spinning/ring-spinning/zinser-51) · [2026 年公告](https://saurer.com/en/news/pressrelease-itma-asia-2026) |
| [马佐里 MDS2](http://127.0.0.1:4173/#spinning/drive/marzoli_mds2_384) | 384 | 选两台主电机、两条切向带，各负责 192 锭。可逐个检查所属锭位。每组在两侧各分配 96 锭是模型选用的布置。 | [MDS2 产品与样本](https://www.marzoli.com/en/spinning-solutions/spinning-section/ring-spinning-frame-mds2) |
| [丰田 RX300E](http://127.0.0.1:4173/#spinning/drive/toyota_rx300e) | 1,008 | 单根锭带带四锭。前罗拉通长驱动，中、后罗拉各在两端设独立伺服。采用 2025 年 8 月样本中 41.035 m 的筐式供管机，分段交界的具体锭号按中点布置。 | [丰田样本，印刷第 3、4、7–10 页](https://textile-machinery.toyota-industries.com/en/catalog2022/catalog/rx300_e.pdf) |

经纬 JWF1366Pro 的 2026 年 7 月说明书提供主传动图、电机型号和功率。立达 RSB-D 27 的 2026 年 5 月版手册给出双眼的布置图与功率分项。越剑使用厂家在 DirectIndustry 展厅公开的参数表，首发日期和实机配套电机清单待核实。eAFK HQ 收录于巴马格 2026 年样本，eFK EvoSmart 于 2025 年推出。整机几何按已公开的选定配置重建，详情中列有尚待装配图核实的部分。[经纬说明书](https://www.jwgf.com/cpfw/mfjx/btj/syhm/202607/P020260731520695347371.pdf) · [立达并条机手册](https://www.rieter.com/fileadmin/user_upload/products/documents/systems/spinning-preparation/rieter-draw-frames-brochure-3690-v2-100158-en.pdf) · [越剑厂商展厅](https://www.directindustry.com/prod/zhejiang-yuejian-intelligent-equipment-company/product-235275-2369973.html) · [巴马格 EvoSmart 公告](https://www.barmag.com/en/about-us/news/barmags-new-texturing-machine-impresses-the-market/)

新增机型的配置、来源和电机分组位于 `research/variants-*.json`。按同名 `blender/variants_*.py` 重建的 Blender 工程位于 `blender/variants/`，网页按需读取 `dist/assets/variants/` 内相应型号的 GLB 和研究记录。更新模型或研究记录后执行下列命令，可重新生成目录及电机应用对照表，并核验每个电机的受驱范围。

```sh
blender --background --factory-startup --python-exit-code 1 --python blender/build_expansion.py -- rieter_rsb_d27
python3 scripts/publish_model_variants.py
npm run check:variants
```

## 七类工序扩展设备

下表列出模型中可定位的电机位置。两列分别统计厂家资料支持驱动归属的位置，以及按设备功能推定的位置。同一电机带动多个机构时只计一次。具体电机型号、功率、安装尺寸及尚待核实的轴系可在每台设备的「型号与配置」和路线详情中查阅。

| 设备及厂家资料 | 展示的工位和机构 | 厂家资料支持驱动归属 | 功能推定 |
|---|---|---:|---:|
| 并纱机 · [SSM CWX-D](https://www.ssm.ch/products/winding-solutions/assembly-winding-machines) | 双面 10 锭，每锭独立驱动槽筒，筒子表面接触卷绕，槽沟同时往复排纱 | 10 | 0 |
| 喷气纺 · [Rieter J 70](https://www.rieter.com/products/systems/air-jet-spinning-machines/air-jet-spinning-machine-j-70) | 40 个独立卷绕单元、牵伸区、落筒机器人和成筒输送。单列压缩空气成纱喷嘴 | 40 | 44 |
| 自动结经 · [Stäubli TIEPRO 与 TPF](https://www.staubli.com/global/en/textile/products/warp-tying-machine/tiepro.html) | 上下两片经纱、锥形分纱、打结与剪尾，共享主驱动按功能演示 | 0 | 1 |
| 烧毛 · [SWASTIK Super Singe](https://www.swastiktextile.com/gas-singening-machine-super-singe/) | 前后两对刷辊由交流电机直联，另列助燃风机、排风、抽绒及出布牵引 | 4 | 4 |
| 平幅水洗／皂洗 · [Benninger BEN-WASH](https://benningergroup.com/en/textile-finishing/washing-solutions) | 厂家后洗示例的两台 TRIKOFLEX、三台 EXTRACTA 和一台 TEMPACTA，可逐段定位输布、轧液和循环泵 | 0 | 18 |
| 丝光 · [Benninger BEN-DIMENSA](https://benningergroup.com/en/textile-finishing/mercerizing-solutions) | 浸渍导布、夹链、调幅、真空抽碱与后洗，逐段查看机械作用范围 | 0 | 22 |
| 橡毯预缩 · [Brückner POWER-SHRINK](https://www.brueckner-textile.com/en/products/details/power-shrink-sanfor-range.html) | 橡毯、预缩热滚筒、毛毯稳定和出布，磨毯与抽屑在停产维护时单独演示 | 0 | 12 |
| **合计** | **76 条路线，包括有电机、气动及动力资料待核的工位** | **54** | **101** |

在「传动链 / 驱动工位」选中路线。重复工位可逐个切换，如 J 70 的第 40 个卷绕单元。右侧依次显示安装工位、电机与动力源、受驱机构和来源。点击「定位电机」可近看电机外观，点击机构名称可跳到对应的工作部件。「运行演示」显示传动方向，可暂停并切回整机。由于公开资料的范围有限，推定的电机工位和安装位置已逐项标注，整机实际配置仍取决于厂家订单与电气资料。

## 项目文件

- `dist/` 提供 27 类设备各机型的 GLB、旧版独立电机资产、交互网页与 [电机应用对照表](dist/motor-applications.html)。
- `blender/` 包含可编辑的设备工程与建模脚本。新增 7 台均有各自的 `.blend`，复用 `build_expansion.py` 导出。
- `research/expansion-*.json` 记录所选配置、厂家链接、证据支持范围、安装工位和电机与部件的对应关系。
- `qa/` 提供完整取景、零件选择、传动关系与动画检查。新增设备的工位数量与模型指纹见 [逐台检查结果](qa/equipment-stations-validation.json)。

以重建水洗线为例，安装 Blender 5、Python 3.9 或更高版本，以及支持 `node:module.registerHooks` 的 Node.js 后，在项目根目录运行以下命令。其他设备的标识见上述逐台检查结果。

```sh
blender --background --factory-startup --python-exit-code 1 --python blender/build_expansion.py -- washing_range
python3 scripts/publish_expansion.py
python3 scripts/publish_model_variants.py
npm run check
npm run check:stations
npm run check:drives
npm run check:motion
npm run check:camera
npm run check:rendering
node qa/verify-frontend-v3.mjs
```

## 使用方式

从「棉纺」选择「气流纺（转杯纺）」，在「传动链 / 驱动工位」选择驱动路线及纺位，可观察立达 R 70 双面基础机的逐位传动。两节各有 24 个纺位，总计 48 位。五类逐位电机分别驱动喂条、分梳、转杯、卷绕和横动导纱。配置来源及其他设备的覆盖核查见「研究与资料」。

从首页选择「研究电机与工位」可进入跨厂家对照，从任一设备的「电机与传动」可直接查看该工序。研究页支持按电机、工作负载、设备及关键词组合筛选，并可返回对应的三维工位。[电机应用对照](dist/motor-applications.html)

原厂资料、适用范围和工位记录收录在 [研究数据](dist/motor-applications.json) 中。更新数据后运行 `python3 scripts/build_motor_applications.py` 即可校验引用并重新生成可离线阅读的页面。

选择工序查看设备与输入输出；拖动旋转、滚轮缩放；运行按钮演示传动运动；外壳透视查看设备内部；拆解滑块分离部件；切换“传动链”查看本机的电机工位、传动环节和工作机构，点击工位可定位；点击部件可读结构说明。模型可从网页下载，`blender/` 内工程可继续编辑。

默认“完整取景”会随旋转、拆解和窗口尺寸调整，保持整机在画布内。滚轮或双指缩放进入“自由近看”；点击“适配全部”恢复全景。顶部提供立体、前、后、左、右、顶、底七个方向，底视时地面会自动隐藏。标题和零件说明位于画布之外。

v3 保留所选配置的完整重复工位数量；厂家确认的参数与推定的尺寸、布置分别记录。动画服务于原理理解，不代表实际转速、功率或控制时序。电机外壳区分伺服与通用工业形式；尺寸和配套型号未确认时明确标记。传动链连线表示功能关联，不代表经厂家核验的轴线、齿轮比或电缆走向。

## 技术与许可

使用 Blender 5.0.1、glTF 2.0 和 Three.js 0.180.0。Three.js 的 MIT 许可证见 `dist/vendor/THREE-LICENSE.txt`。模型几何为原创，未使用厂家 CAD；官方照片和样本仅用于本地工艺、外形及装配核对，不用作网页模型贴图。引用保留原链接。

<details>
<summary>历史版本与本地验收档案（v2 至 v6）</summary>

以下为各版本发布时的记录。历史候选模型、原厂样本副本、旧版总装及各轮截图保存在原工作目录，仓库提供当前可运行模型、可编辑工程、厂家原链接和复核脚本。

第二版的逐机型参考、观察要点与改模清单见 `research/visual-reference-v2.md`；装配复核记录见 `qa/review-v2.md`。这些记录区分照片观察、可计算的几何关系与教学简化。

2026-11-16 结构真实性复核更正：v2 是参考公开照片/样本制作的结构示意模型，存在缩短机身、减少重复工位、跨代参考和推定内部结构，不满足用户新增的“最新款式、不简化或省略”要求。浏览器验收仅证明加载、取景和交互正常；几何检查仅证明检查过的模型关系，并非厂家实机结构、尺寸或零件完整性认证。当前不得将 v2 描述为最新机型完整复刻。逐类现款来源与重建资料缺口记录在 `research/current-model-audit-*.json`，具体建模简化记录在 `qa/structural-fidelity-audit-v3.json`。

此前 v2 代码确认：细纱模型为双面各 18 锭、合计 36 锭；精梳模型为 4 个工作头；拉幅模型为 3 节烘房。这些均为展示模型自行设置的数量，未对照选定实机的完整配置。下一版的来源、数量、装配和验收要求见 `qa/reconstruction-acceptance-v3.json`；未知零件与配置保持待核实，不得以通用构件或推测填补后声称完整。

```sh
npm run check
npm run check:camera
```

验证脚本检查全流程数据、GLB 二进制结构、交互所需零件属性和本地资源完整性。相机回归按当前模型清单加载 GLB，验证连续切换后的归一化、不同拆解程度/运动相位/画布尺寸/方向的投影边界及地板净空；报告保留模型哈希。

本地服务会核对模型地址中的 SHA-256 指纹。同一版本的模型可从浏览器缓存再次打开，模型文件更新后使用新的地址。页面和工艺资料每次读取最新版本。

## 重新生成 Blender 模型

```sh
"/Applications/Blender 2.app/Contents/MacOS/Blender" --background --factory-startup --python blender/build_models.py
```

其他平台将命令开头替换为 Blender 可执行文件路径。脚本使用分场景构建，再合并设备展陈，重新生成两份 `.blend`、全部 GLB 和渲染预览。`industrial_v2.py` 提供通用构建函数，`current_spinning_v3.py`、`current_weaving_v3.py`、`current_finishing_v3.py` 定义 v3 设备；`motor_precision.py` 保留旧独立电机教学资产的构建代码；v4 使用 `refine_drives_v4.py` 对 v3 源文件进行外观更新。请将这些模块与主脚本一同保留。

第一版浏览器验收记录见 `qa/browser-validation.json`，第二版已完成 17 个模型、七向视图、拆解与旋转缩放、手机/平板/矮窗口的浏览器验收，实测范围与截图见 `qa/browser-validation-v2.json`。最终渲染检查、相机回归和本地服务核验分别记录于 `qa/render-validation-v2.json`、`qa/camera-validation.json` 与 `qa/local-deployment-v2.json`。模型保留中文零件标签、说明、运动节点和拆解层级，可在 Blender 中继续编辑。

## 第三版当前配置与范围

v3 重建的 16 个设备分别保留所选的完整工位和模块数，包括 F 40 的 72 锭、G 38 的 288 锭、E 90 的 8 个梳理头、X6 的 96 个络筒单元、整经的 480 个供纱位置、浆纱的 6 个退绕轴和 12 个烘筒、MONTEX 案例的 6 个烘房。72/288/96 是所选机型配置，不代表整条生产线已通过产能配套；480 锭及浆纱模块数是公开范围内的展示选择，尚无该订单总图。

染色采用 Küsters DyePad 冷轧堆路线，堆置后的水洗作为后续独立工序；检测采用 Fabriq Vision 2 主机、控制台和复核工作站，配套放卷/收卷机尚未取得指定型号资料。网页不会把这些局部系统称为完整成套线。所有设备仍标记 `structuralCompleteness=false`。

- `research/config-*-v3.json`：逐设备配置、已确认/推定/缺失项、官方来源。
- `blender/v3-source/`：16 份单设备可编辑源文件。
- `blender/textile-machinery-v3.blend`：按实际包围盒排布的 v3 总装。
- `qa/v3-model-previews/`：逐设备渲染验收图。
- `qa/selected-population-v3.json`：实际 GLB 工位数量与来源配置的核验；不等于 OEM 完整性认证。
- `qa/browser-validation-v3.json`、`qa/camera-validation-v3.json`：16 台新版设备与独立电机、长设备拆解七向取景、手机配置面板及 74,664 次投影检查。
- `qa/local-deployment-v3.json`：25 个本地响应与已验收文件逐字节一致。
- `blender/v2-backup/`：更新前的模型与两份工程文件，供回退。

先生成候选且不覆盖本地服务：

```sh
"/Applications/Blender 2.app/Contents/MacOS/Blender" --background --factory-startup --python blender/build_current_v3.py
python3 qa/verify_current_v3.py --models-dir qa/v3-candidates/models
```

## 厂家当前机型核查（2026-11-16）

以下保留 2026-11-16 的初始核查记录，表中“现模型”“旧模型”指重建前的 v2。v3 已据此重建 16 个设备 GLB，最终所选配置及未确认部分见 `research/config-*-v3.json`。当前官网列售、首次发布和某个具体订单配置分别判断；不宣称已经穷尽全球最新产品。完整来源、资料日期、配置冲突和缺口见 `research/current-model-audit.json`。

| 工序 | 厂家当前参考 | 核查结果及现模型问题 |
|---|---|---|
| 开清棉 | [Rieter UNIfloc A 12 / VARIOline](https://www.rieter.com/products/systems/fiber-preparation/bale-opener-unifloc-a-12) | A 12 当前在列，至少 2017 已存在；单台抓棉机不等于完整开清棉联合线。 |
| 梳棉 | [Rieter C 81](https://www.rieter.com/products/systems/fiber-preparation/card-c-81) | 2023 推出；旧模型混用 C 80 剖面与 C 81 外形，未完整对应 CGC、TLM、IGS 等结构。 |
| 并条 | [Rieter RSB-D 55](https://www.rieter.com/products/systems/spinning-preparation/draw-frame-rsb-dsb-d-55) | 2023 新一代单眼平台仍在列；需明确 RSB 自调匀整配置，不能混用 SB 或双眼参数。 |
| 精梳 | [Rieter E 90](https://www.rieter.com/products/systems/spinning-preparation/comber-e-90) | 2019 发布、当前在列；现 4 头模型没有对应完整 8 并合配置，成卷准备、换卷与输送也需单独核对。 |
| 粗纱 | [Rieter F 40](https://www.rieter.com/products/systems/spinning-preparation/roving-frame-f-40f-20) | 全自动 F 40 与半自动 F 20 是不同配置；F 40 为 2019 发布、当前在列，现模型缺完整自动落纱及物流。 |
| 环锭细纱 | [Rieter G 38 当前版本](https://www.rieter.com/products/systems/ring-spinning-machines/ring-spinning-machine-g-38) | 2024 有同名新一代；原 v5 样本仍被当前官网提供，但现模型仅 36 锭并缺完整落纱、SERVOdisc 和实际驱动。 |
| 自动络筒 | [Rieter Autoconer X6](https://www.rieter.com/products/systems/winding-machines/automatic-package-winding-machine-autoconer) | 2025 有 Cop Exchanger 更新；RM/D/V 供料配置必须分开。官网现链接 v3 手册，全文抓取超时，修订内容未全部核对。 |
| 分批整经 | [KARL MAYER WARPDIRECT 2.0](https://www.downloadcenter.karlmayer.com/en/news-events/my-textile-news/karl-mayer-at-the-weaving-hall-of-itma-asia-2026-high-performance-warp-preparation-for-high-quality-fabrics-made-from-staple-fibers-and-new-horizons-in-textiles/) | 2026-10-29 官方公告证实 2025 年末推出；压辊由液压改电动。旧 WARPDIRECT 单页不能代表 2.0。 |
| 浆纱 | [KARL MAYER PROSIZE / HSB](https://www.karlmayer.com/en/products/warp-preparation/sizing-and-assembling-machines/prosize/) | 当前模块平台，2026 仍展示 HSB；2024 有 CASCADE/Smart Size Box 更新。浆槽、烘筒和选件数量需锁定，不能拼合 HSB/VSB。 |
| 穿经 | [Stäubli SAFIR PRO S67](https://www.staubli.com/global/en/textile/products/drawing-in-machine/safir-pro-s67.html) | 2024 发布、可作为现代棉机织参考；S80 当前仍在列，面向更复杂单/双经片，S67 不是其等能力直接继任。 |
| 剑杆织造 | [Picanol Ultimax](https://www.picanol.be/en/machines-features/machines/ultimax-rapier-weaving-machine) | 2023 发布的后继剑杆平台；OptiMax-i Connect 不宜再作最新代。全棉配置、幅宽、开口和边组织需另定，不能套用混纤展样。 |
| 前处理 | [Benninger BEN-BLEACH](https://benningergroup.com/en/textile-finishing/bleaching-solutions) | 当前模块化联合线，未确认统一最新代号；必须确定完整工艺模块、布路、辅助系统和数量。 |
| 染色 | [Benninger Küsters DyePad / BEN-Colour](https://benningergroup.com/en/textile-finishing/dyeing-solutions) | 当前系列，不能据在列称为新发布；CPB 堆置与连续固色配置应分开，不得拼成一台无对应实机的设备。 |
| 拉幅 | [Monforts MONTEX](https://www.monforts.de/produkte/spannrahmen/) | 当前定制系列；2026-11-09 官方案例为 6 烘房、3.2m、全电加热及热回收，不能代表所有 MONTEX。现 3 箱模型没有对应配置。 |
| 轧光 | [ANDRITZ teXcal 系列](https://www.andritz.com/products-en/power-to-x/nonwoven-textile/textile/textile-calendering-nonwoven-and-textile) | s-roll、Raconip L、trike、Raconip TT 用途/辊组不同；TT 至少 2019 已发布。须选单一构型，不能把网页 new 当作 2026 新机。 |
| 验布 | [Uster Fabriq Vision 2](https://www.uster.com/fileadmin/user_upload/Images/AboutUster/News_and_Media/2025/251024_Uster_press_release_ITMA_Asia_2025_novelties_and_news.pdf) | 2025-10-24 官方新品公告；原 EVS Fabriq Vision / Q-Bar 2 参考未跟进，且检测单元不能代替未指定的完整放卷/收卷机。 |
| 独立电机 | [ABB Process performance induction 系列](https://www.abb.com/global/en/areas/motion/motors-generators/low-voltage-motors/iec-low-voltage-motors/process-performance-motors/process-performance-induction-motors) | 原依据为 2022-12 通用结构目录，未选订货号，绕组是原创示意；不能称为厂家现款或各纺机实际配套电机。 |

目前这 17 项均未具备足以证明全部内部零件无遗漏的资料。v3 已固定展示配置并保留完整所选工位数量，但若要达到实机全部内部零件无遗漏，仍需取得相应订单总装/分装图、完整部件清单、关键尺寸以及传动和管线资料，或同等完整的实机记录。已公开的部分可核对，未公开的部分保留待核实；结构完整性验收与网页显示验收分别记录。

## 第四版驱动工位与电机外观（2026-11-17）

按本轮要求，实时页面不再提供电机内部解剖。切换“传动链”仍显示整台所选设备，通过工位标记和有向连线观察电机→传动→工作机构。重复工位支持逐个定位；未独立建模的动力源明确列出，不用另一台电机代替。原有工序和选定工位数量保持不变。

电机更新为封闭外观：保留工业电机与伺服电机的区别，细化壳体、端盖、法兰、紧固件、接线盒、出线接口、安装脚及输出轴。几何仍为公开资料参考下的外观建模，精确配套电机和安装尺寸待厂家资料验证。旧 `motor.glb` 及 v3 文件只作历史归档。

- `dist/drive-chains.json`：逐设备的驱动工位、功能路径与对应节点。
- `research/drive-evidence-v4.json`：传动关系的依据与未确认项。
- `blender/refine_drives_v4.py`：只更新已知电机的后处理脚本。
- `blender/v4-source/`、`blender/textile-machinery-v4.blend`：本轮可编辑设备与总装。
- `blender/v3-backup/`：修改前的网页和模型备份。
- `qa/drive-validation-v4.json`：实际导出电机、位置保留和传动数据命中检查。

```sh
"/Applications/Blender 2.app/Contents/MacOS/Blender" --background --factory-startup --python blender/refine_drives_v4.py
python3 qa/verify_drives_v4.py --models-dir qa/v4-candidates/models
"/Applications/Blender 2.app/Contents/MacOS/Blender" --background --factory-startup --python blender/assemble_current_v3.py -- --drive-v4
```

传动箭头是功能连接说明，不能作为实际机械轴线使用。对未知中间传动明确显示资料缺口，不把跳过中间机构的连线称为完整实机装配。

本轮验收入口：`npm run check:drives`；报告汇总 `qa/release-v4.json`。桌面与手机操作、七向完整取景及本地27项响应核验通过，最终页面截图 `qa/browser-v4-final.jpg`。

## 第五版纱线加工分支（2026-11-17）

本轮增加三类独立设备，图谱共19台。原16台棉纺—机织—染整入口保持原编号；新增分支使用A/B/C，浏览导航不是生产工序先后关系：

- A 紧密纺：粗纱→紧密纺→络筒，替代普通环锭细纱；增加纤维集聚和负压工位。
- B 倍捻：单纱经并纱准备后按用途选配，空心锭每转形成两捻；并纱设备未单列。
- C 加弹：化纤POY→牵伸/加热/冷却/假捻→DTY，独立于棉纺主线；与倍捻的真捻工艺不同。

现有MONTEX入口明确为“拉幅热定型机（兼烘干）”，没有另加一台定型设备。全棉的干燥、幅宽控制与适用整理，不等同于热塑性纤维在对应工艺条件下的热定型。

新增模型继续采用精细电机外观、整机工位定位和可追溯传动分支。仅保留所选配置的完整数量，不将模型称为厂家CAD或已通过完整BOM认证的装配。新增源文件在 `blender/v5-source/`，19台可编辑总装为 `blender/textile-machinery-v5.blend`；逐设备资料见 `research/config-extensions-v5.json`，修改前网页保留在 `blender/v4-backup/`。

| 分支 | 所选厂家与配置 | 证据范围 |
|---|---|---|
| 紧密纺 | Rieter K 48；6节×48=288锭，70mm锭距、单侧吸风、C3直联 | 2025-04版v6官方样本；筛鼓、Detect导流和72组四锭带全部保留。 |
| 倍捻 | Saurer CompactTwister Series 8；机械控制、1节20锭、VTS07 | 机械控制配置单列，不混入最少120锭的电子控制配置。 |
| 加弹 | Barmag eFK Standard PET单股V型；16节×24=384工位 | 按用户选择采用当前在列eFK；不是eFK EvoSmart。2023官方表原链接失效，尺寸与数量依据官方URL搜索索引；局部机构依据可取得的原厂资料，完整截面与订单装配仍待核实。 |

新增候选先导出到 `qa/v5-candidates/`，不直接覆盖服务：

```sh
"/Applications/Blender 2.app/Contents/MacOS/Blender" --background --factory-startup --python blender/build_extensions_v5.py
"/Applications/Blender 2.app/Contents/MacOS/Blender" --background --factory-startup --python blender/build_texturing_v5.py
python3 qa/verify_extensions_v5.py --models-dir qa/v5-candidates/models
# 审阅候选与驱动映射后发布；保留旧16台GLB。
python3 scripts/publish_branches_v5.py
"/Applications/Blender 2.app/Contents/MacOS/Blender" --background --factory-startup --python blender/assemble_current_v3.py -- --branches-v5
```

第五版验收报告：`qa/extensions-validation-v5.json`、`qa/drive-anchor-validation-v5.json`、`qa/drive-validation-v5.json`、`qa/frontend-validation-v5.json`、`qa/camera-validation-v5.json`、`qa/browser-validation-v5.json` 和 `qa/local-deployment-v5.json`。加弹机候选报告包含12类工位、1560段中心线的实际表面穿越检查；不等同于纱线全截面碰撞或制造级校验。页面最终截图为 `qa/browser-v5-final.jpg`。

第五版最终交付汇总见 `qa/release-v5.json`，包含当前模型文件校验值、本地验收记录及19台可编辑总装的校验值。总装结果见 `qa/v5-assembly-report.json`。

## 第六版加弹机纱路与驱动联动（2026-11-18）

本地入口：`http://127.0.0.1:4173/?revision=20261118-v6-motion#texturing/drive`。

加弹机增加两种观察方式：“全机联动”显示 POY→G1→一次加热→冷却→假捻→G2→二次加热→W3→上油→横动卷绕的纱流；“单电机观察”只运行所选模型电机关联的机构，整条纱路不作连续产纱运行。青色标记表示纱流，橙色脉冲与高亮表示动力方向和作用范围。支持 0.25/0.5/1/2 倍演示、同步暂停、从头播放、A/B 侧各192纱位选择、单纱位近看及全部384条纱路。暂停时停止重复渲染，运行时复用几何与传动线缓存。

- M1/M2：A/B侧假捻，各16段切向带、192个假捻单元、576根摩擦轴。
- M3/M4：A/B侧W3喂纱，各16共轴段、192纱位。
- M5/M6：A/B侧横动与卷绕，各48段凸轮轴、192导眼，并关联192接触辊和192卷装；内部卷绕分配仍留空，不画出虚构轴线。
- M7：油剂循环泵，为两侧供油管和384上油位供液，不作为油轮旋转动力。

这7处是现有公开参考模型中的动力工位，未验证实机全部电机数量或安装。G1/G2集成动力源未独立建模，保留明确提示，不分配给其他电机。所选工位与原19台GLB均未缩减或重建。运动速度、相位、横动行程和传动比为观察用示意；运行时将导眼放到卷装径向包络外，末段纱线随动，退出设备时恢复源模型。

实现入口为 `dist/texturing-motion.js`、`dist/drive-view.js` 与 `dist/app.js`。独立验证：`npm run check:motion`；证据与检查报告见 `qa/texturing-motion-evidence-v6.json`、`qa/texturing-motion-validation-v6.json`、`qa/drive-animation-validation-v6.json`、`qa/browser-validation-v6.json` 和 `qa/local-deployment-v6.json`。最终交付文件清单见 `qa/release-v6.json`。

</details>
