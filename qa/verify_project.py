"""Validate asset usability, not OEM fidelity or structural completeness."""
import argparse
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--models-dir', type=Path, default=ROOT / 'dist/assets/models')
parser.add_argument('--output', type=Path, default=ROOT / 'qa/verification.json')
args = parser.parse_args()
MODEL_DIR = args.models_dir if args.models_dir.is_absolute() else ROOT / args.models_dir
OUTPUT = args.output if args.output.is_absolute() else ROOT / args.output
MAIN_IDS = 'opening carding drawing combing roving spinning winding warping sizing drawing_in weaving pretreatment dyeing stenter calender inspection'.split()
IDS = [s['id'] for s in json.loads((ROOT/'dist/process-data.json').read_text())['stages']]
errors = []
report = {'models': [], 'data': {}, 'modelsDirectory': str(MODEL_DIR.relative_to(ROOT) if MODEL_DIR.is_relative_to(ROOT) else MODEL_DIR),
          'validationScope': 'File availability, glTF buffers and semantic interaction data only.',
          'manufacturerCompletenessVerified': False,
          'scopeExclusions': ['OEM BOM completeness', 'current-model accuracy', 'manufacturing dimensions', 'physical simulation']}

def expect(condition, message):
    if not condition:
        errors.append(message)

def read_glb(path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw), 'Invalid GLB header'
    cursor, chunks = 12, {}
    while cursor < len(raw):
        size, kind = struct.unpack_from('<II', raw, cursor)
        cursor += 8
        assert cursor + size <= length, 'Truncated GLB chunk'
        chunks[kind] = raw[cursor:cursor + size]
        cursor += size
    return json.loads(chunks[0x4E4F534A]), chunks.get(0x004E4942, b'')

for identifier in IDS + ['motor']:
    path = MODEL_DIR / (identifier + '.glb')
    expect(path.is_file(), f'Missing model {identifier}')
    if not path.is_file():
        continue
    try:
        gltf, binary = read_glb(path)
        nodes = gltf.get('nodes', [])
        meshes = gltf.get('meshes', [])
        labels = [n.get('extras', {}).get('label') for n in nodes if n.get('extras', {}).get('label')]
        groups = {n.get('extras', {}).get('group') for n in nodes}
        expect(bool(meshes), f'{identifier}: no renderable geometry')
        expect(bool(labels), f'{identifier}: missing semantic component labels')
        # A standalone optical inspection unit, for example, need not contain a
        # modeled process motor. Requiring one would encourage fabricated parts.
        if identifier == 'motor':
            expect('motor' in groups, 'motor: no motor detail group')
        stage_roots = [n for n in nodes if n.get('name') == 'stage_' + identifier]
        expect(len(stage_roots) == 1, f'{identifier}: missing/duplicate stage root')
        root_extras = stage_roots[0].get('extras', {}) if stage_roots else {}
        for node in nodes:
            extras = node.get('extras', {})
            axis = extras.get('spinAxis')
            expect(axis is None or axis in ['x', 'y', 'z'], f'{identifier}: invalid rotation axis')
            direction = extras.get('explode')
            expect(direction is None or (isinstance(direction, list) and len(direction) == 3 and all(isinstance(v, (int,float)) and math.isfinite(v) for v in direction)), f'{identifier}: invalid explode vector')
        for view in gltf.get('bufferViews', []):
            expect(view.get('byteOffset', 0) + view['byteLength'] <= len(binary), f'{identifier}: buffer view out of bounds')
        for accessor in gltf.get('accessors', []):
            for key in ['min', 'max']:
                expect(all(math.isfinite(v) for v in accessor.get(key, [])), f'{identifier}: nonfinite geometry bound')
        triangles = sum(gltf['accessors'][p['indices']]['count'] // 3 for mesh in meshes for p in mesh['primitives'] if 'indices' in p and p.get('mode',4) == 4)
        report['models'].append({'id':identifier,'bytes':path.stat().st_size,'nodes':len(nodes),'meshes':len(meshes),'triangles':triangles,'labeled_components':len(labels),'rotating_nodes':sum(bool(n.get('extras',{}).get('spinAxis')) for n in nodes),'exploding_nodes':sum(bool(n.get('extras',{}).get('explode')) for n in nodes),'has_motor_detail_group':'motor' in groups,'modelVersion':root_extras.get('modelVersion'),'referenceModel':root_extras.get('referenceModel'),'declaredStructuralCompleteness':root_extras.get('structuralCompleteness'),'manufacturerCompletenessVerified':False})
        # motor.glb remains an archived teaching asset. The live drive view uses
        # the selected equipment, and deliberately does not expose motor internals.
        if identifier == 'motor':
            report['models'][-1]['usage'] = 'archived_not_loaded_by_live_view'
    except Exception as exc:
        errors.append(f'{identifier}: {exc}')

data_candidates = [ROOT/'dist/process-data.json', ROOT/'research/process-data.json']
data = None
for candidate in data_candidates:
    try:
        value = json.loads(candidate.read_text())
        if isinstance(value, dict) and 'stages' in value:
            data = value
            report['data']['file'] = str(candidate.relative_to(ROOT))
            break
    except Exception:
        pass
expect(data is not None, 'Missing structured process research')
if data:
    stages = data['stages']
    expect(set(MAIN_IDS).issubset({s['id'] for s in stages}), 'Main cotton route is missing stages')
    expect(len(stages) == len(set(IDS)), 'Duplicate/missing stage records')
    for stage in stages:
        for field in ['name','input','output','summary','process','drive','quality','sources']:
            expect(bool(stage.get(field)), f"{stage['id']}: missing {field}")
        expect(all(source.get('url','').startswith('https://') for source in stage.get('sources',[])), f"{stage['id']}: invalid source link")
    report['data']['stage_count'] = len(stages)

for resource in ['index.html','style.css','app.js','camera-fit.js','scene-geometry.js','vendor/three.module.js','vendor/three.core.js','vendor/addons/controls/OrbitControls.js','vendor/addons/loaders/GLTFLoader.js','vendor/addons/utils/BufferGeometryUtils.js','vendor/THREE-LICENSE.txt']:
    expect((ROOT/'dist'/resource).is_file(), f'Missing web resource {resource}')
expect(any((ROOT/'blender').glob('*.blend')), 'Missing editable Blender deliverable')
report['status'] = 'pass' if not errors else 'fail'
report['errors'] = errors
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
