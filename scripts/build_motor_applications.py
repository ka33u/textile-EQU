"""Render the offline motor application catalog from the published research data."""
from collections import Counter, defaultdict
from html import escape
import json
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
NAMES = {
    "opening": "开清棉", "carding": "梳棉", "drawing": "并条", "combing": "精梳",
    "roving": "粗纱", "spinning": "环锭细纱", "winding": "自动络筒",
    "warping": "整经", "sizing": "浆纱", "drawing_in": "穿经与结经", "weaving": "织造",
    "pretreatment": "织物前处理", "dyeing": "织物染色", "stenter": "拉幅热定型",
    "calender": "轧光整理", "inspection": "验布与复卷", "compact_spinning": "紧密纺",
    "twisting": "倍捻", "texturing": "牵伸假捻加弹", "rotor_spinning":"气流纺（转杯纺）",
    "assembly_winding":"并纱","airjet_spinning":"喷气纺","warp_tying":"自动结经","washing_range":"平幅水洗／皂洗",
    "singeing":"织物烧毛","mercerizing":"丝光","sanforizing":"橡毯预缩",
}
SECTION_NAMES = {"spinning": "棉纺", "weaving": "机织", "finishing": "染整", "yarn_processing": "纱线加工分支"}


def read(name):
    return json.loads((DIST / name).read_text(encoding="utf-8"))


def options(pairs):
    return "".join(f'<option value="{escape(key)}">{escape(label)}</option>' for key, label in pairs)


def source_links(refs, sources):
    links = []
    for key in refs:
        source = sources[key]
        links.append(f'<a href="{escape(source["url"])}" target="_blank" rel="noopener noreferrer" '
                     f'title="{escape(source["locator"])}">{escape(source["title"])}</a>')
    return '<div class="references">' + "".join(links) + "</div>"


def equipment_rows(rows, sources, stage_id):
    result = []
    for entry in rows:
        filters = " ".join(entry["filters"])
        jobs = " ".join(entry["jobs"])
        motor_jobs = escape(json.dumps(entry["motorJobs"], separators=(",", ":")))
        model_link = ""
        model_key = escape(entry.get("modelAssetId", ""))
        model_name = escape(entry["model"])
        if entry.get("modelAssetId"):
            url = f'./index.html#{stage_id}/drive/{entry["modelAssetId"]}'
            model_link = f'<a class="maker" href="{escape(url)}">定位这款机型 ↗</a>'
        result.append(f'''<tr data-model="{model_key}" data-model-name="{model_name}" data-motors="{filters}" data-jobs="{jobs}" data-motor-jobs="{motor_jobs}">
          <td data-label="设备与工位"><strong>{escape(entry["station"])}</strong>
            <span class="maker">{escape(entry["maker"])} · {escape(entry["model"])}</span>{model_link}</td>
          <td data-label="动力怎样传到机构">{escape(entry["path"])}</td>
          <td data-label="电机资料"><span class="evidence">{escape(entry["level"])}</span>{escape(entry["electric"])}</td>
          <td data-label="适用场景及来源">{escape(entry["work"])}{source_links(entry["refs"], sources)}</td></tr>''')
    return "".join(result)


def model_routes(asset, routes, url, model_key=""):
    entries = []
    for item in routes:
        status = {"public_confirmed":"厂家资料支持该工位驱动","not_modeled":"动力归属另列或待核"}.get(item["evidence"]["status"],"模型功能推定")
        entries.append(f'<li><strong>{escape(item["label"])}</strong> · {escape(item["location"])}'
                       f'<br>{escape(item["role"])} <small>{status}</small></li>')
    model = asset["referenceModel"]
    link = f'<a class="back-model" href="{escape(url)}">在三维中查看 {escape(model)} ↗</a>'
    return (f'<details class="model-routes" data-model="{escape(model_key)}"><summary>三维模型中的 {len(routes)} 条传动路线'
            f' <span>· {escape(model)}</span></summary><p class="scope-note">{link}</p><ul>{"".join(entries)}</ul></details>')


def stage_section(s, process, assets, chains, sources, variants):
    key = s["id"]
    section_name = SECTION_NAMES[process[key]["section"]]
    route_sections = [model_routes(assets[key], chains[key]["routes"], f"./index.html#{key}/drive")]
    for model, drive in variants[key]:
        route_sections.append(model_routes({"referenceModel":model["model"]}, drive["routes"],
                                          f'./index.html#{key}/drive/{model["id"]}', model["id"]))
    return f'''<section class="equipment" id="{key}" data-stage="{key}">
      <header class="equipment-head"><div><div class="scope">{section_name}</div>
        <h2>{NAMES[key]}</h2><p class="question">{escape(s["question"])}</p></div>
        <a class="back-model" href="./index.html#{key}/drive">查看三维传动 ↗</a></header>
      <p class="scope-note">{escape(s["coverage"])}</p>
      <table><caption class="screenreader">{NAMES[key]}的厂家、电机工位、传动及应用对照</caption>
        <colgroup><col class="col-station"><col class="col-path"><col class="col-evidence"><col class="col-use"></colgroup>
        <thead><tr><th scope="col">设备与工位</th><th scope="col">动力怎样传到机构</th><th scope="col">电机资料</th><th scope="col">适用场景及来源</th></tr></thead>
        <tbody>{equipment_rows(s["rows"], sources, key)}</tbody></table>
      {"".join(route_sections)}
      </section>'''


def main():
    catalog = read("motor-applications.json")
    stages, index, sources = catalog["stages"], catalog["motorIndex"], catalog["sources"]
    process = {s["id"]: s for s in read("process-data.json")["stages"]}
    chains = {s["id"]: s for s in read("drive-chains.json")["items"]}
    assets = read("equipment-provenance.json")["assets"]
    variants = defaultdict(list)
    if (DIST / "model-variants.json").exists():
        for model in read("model-variants.json")["models"]:
            if model["id"] != model["stageId"]:
                drive = read(f'assets/variants/{model["id"]}.json')["drive"]
                variants[model["stageId"]].append((model, drive))
    stage_ids = [s["id"] for s in stages]
    assert stage_ids == list(process) and set(stage_ids) == set(NAMES) == set(chains), "Stage mismatch"
    all_rows = [row for stage in stages for row in stage["rows"]]
    tag_ids = {entry["id"] for entry in index}
    for row in all_rows:
        assert row["refs"] and set(row["refs"]) <= sources.keys()
        assert row["filters"] and set(row["filters"]) <= tag_ids
        assert row["jobs"] and set(row["jobs"]) <= catalog["jobs"].keys()
        assert set(row["motorJobs"]) == set(row["filters"])
        assert all(set(jobs) <= set(row["jobs"]) for jobs in row["motorJobs"].values())
    used_sources = {r for x in [*all_rows, *index] for r in x["refs"]} | {catalog["market"]["source"]}
    assert used_sources == sources.keys()
    assert len(set(s["url"] for s in sources.values())) == len(sources)
    motor_groups = {}
    glossary = []
    for entry in index:
        motor_groups.setdefault(entry["group"], []).append((entry["id"], entry["name"]))
        glossary.append(f'<article><button type="button" data-term="{entry["id"]}">{escape(entry["name"])}'
                        f' <span aria-hidden="true">↗</span></button><p>{escape(entry["note"])}</p>'
                        f'{source_links(entry["refs"], sources)}</article>')
    filters = "".join(f'<optgroup label="{escape(group)}">{options(choices)}</optgroup>'
                      for group, choices in motor_groups.items())
    market = catalog["market"]
    market_items = "".join(f'<div><h3>{x["title"]}</h3><p><b>{x["figures"]}</b> {x["meaning"]}</p></div>'
                           for x in market["observations"])
    tag_data = {x["id"]: x["name"] for x in index}
    evidence = Counter(r["evidence"]["status"] for item in chains.values() for r in item["routes"])
    evidence.update(r["evidence"]["status"] for items in variants.values() for _, drive in items for r in drive["routes"])
    page = Template((ROOT / "research" / "motor-applications-template.html").read_text(encoding="utf-8"))
    result = page.substitute(
        TITLE=catalog["title"], DATE=catalog["checkedAt"], COUNT=len(all_rows), STAGES=len(stages),
        SOURCES=len(sources), GLOSSARY="".join(glossary), MOTOROPTIONS=filters,
        STAGEOPTIONS=options((k, NAMES[k]) for k in stage_ids), JOBOPTIONS=options(catalog["jobs"].items()),
        MARKETITEMS=market_items, MARKETSCOPE=market["scope"], MARKETLINK=source_links([market["source"]], sources),
        SCOPE=catalog["scope"], ROUTES=sum(evidence.values()),
        MODELCONF=evidence["public_confirmed"], MODELINFER=evidence["functional_inference"],
        SECTIONS="".join(stage_section(s, process, assets, chains, sources, variants) for s in stages),
        TAGDATA=json.dumps({"motors": tag_data, "jobs": catalog["jobs"]}, ensure_ascii=False).replace("<", "&#60;"),
    )
    (DIST / "motor-applications.html").write_text(result, encoding="utf-8")
    print(f'{len(stages)} 类设备，{len(all_rows)} 条工位记录，{len(sources)} 份资料')


if __name__ == "__main__":
    main()
