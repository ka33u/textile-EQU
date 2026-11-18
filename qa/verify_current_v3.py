"""Check v3 provenance and full SELECTED populations, not an OEM completeness claim.

Examples:
  python3 qa/verify_current_v3.py --models-dir qa/v3-candidates/models --allow-partial
  python3 qa/verify_current_v3.py --models-dir dist/assets/models
A partial run reports INCOMPLETE, never PASS. --allow-partial only permits an
incomplete run to exit zero while model production is still in progress.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = 'opening carding drawing combing roving spinning winding warping sizing drawing_in weaving pretreatment dyeing stenter calender inspection'.split()
CONFIG_PATHS = ['research/config-spinning-v3.json', 'research/config-weaving-v3.json', 'research/config-finishing-v3.json']
# Frozen selections for this candidate release. They are deliberately checked
# against the configuration files as well as against exported populations.
COUNT_CONTRACTS = {
    'warping': {'creelPositions': 480, 'modeledContinuousEnds': 480},
    'sizing': {'backBeams': 6, 'endsPerBackBeam': 480, 'totalWarpEnds': 2880, 'dryingCylinders': 12, 'sizeBoxes': 1},
    'drawing_in': {'mobileTrucks': 2, 'healdFramesPerTruck': 2, 'loadedWarpEndsPerTruck': 2880},
    'weaving': {'warpEnds': 2880, 'healdFrames': 2, 'weftFeeders': 4, 'rapierTapes': 2},
    'dyeing': {'workingRolls': 2, 'batchCarts': 1},
    'stenter': {'chambers': 6, 'chainWorkingLinksPerSide': 256, 'chainReturnLinksPerSide': 256},
    'calender': {'workingRolls': 2},
    'inspection': {'controlUnits': 1, 'reviewWorkstations': 1},
}
FACT_CONTRACTS = {
    'carding': {'Working flats': 40},
    'drawing': {'Doubling': 8, 'Delivery count': 1},
    'combing': {'Combing heads/doubling': 8, 'E40 feed cans / diameter mm': [28, 600]},
    'roving': {'Spindles / sections / machine length mm': [72, 4, 10485]},
    'spinning': {'Standard minimum / positions per section': [288, 48], 'Selected gauge mm': 70},
    'winding': {'Published maximum winding units': 96, 'Unit gauge mm': 320},
}


def read_glb(path):
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError('Truncated GLB header')
    magic, version, length = struct.unpack_from('<III', raw)
    if magic != 0x46546C67 or version != 2 or length != len(raw):
        raise ValueError('Invalid GLB header/version/length')
    chunks = {}; offset = 12
    while offset < length:
        if offset + 8 > length:
            raise ValueError('Truncated GLB chunk header')
        size, kind = struct.unpack_from('<II', raw, offset); offset += 8
        if offset + size > length:
            raise ValueError('Truncated GLB chunk')
        chunks[kind] = raw[offset:offset + size]; offset += size
    if 0x4E4F534A not in chunks:
        raise ValueError('Missing GLB JSON chunk')
    return json.loads(chunks[0x4E4F534A]), raw


def base_name(node, name):
    return re.fullmatch(re.escape(name) + r'(?:\.\d+)?', node.get('name', '')) is not None


def descendants(nodes, index):
    seen = set(); todo = list(nodes[index].get('children', []))
    while todo:
        i = todo.pop()
        if i in seen:
            continue
        if not 0 <= i < len(nodes):
            raise ValueError('Invalid child node index')
        seen.add(i); todo.extend(nodes[i].get('children', []))
    return [nodes[i] for i in sorted(seen)]


def config_source_urls(cfg):
    found = set()
    def walk(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k.lower() in ('url', 'evidenceurl', 'currentcatalogevidence') and isinstance(v, str) and v.startswith('https://'):
                    found.add(v)
                else:
                    walk(v)
        elif isinstance(value, list):
            for v in value:walk(v)
    walk(cfg)
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models-dir', type=Path, default=Path('dist/assets/models'))
    parser.add_argument('--output', type=Path, default=Path('qa/current-v3-verification.json'))
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    model_dir = args.models_dir if args.models_dir.is_absolute() else ROOT / args.models_dir
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = {'validationKind': 'v3_provenance_and_selected_population_contract',
              'validationScope': 'Export metadata, selected configuration records, actual node populations and declared batched populations.',
              'scopeExclusions': ['OEM BOM completeness', 'manufacturer engineering dimensions', 'physical motion/collision validation', 'render/visual inspection', 'production-line capacity matching'],
              'structuralCompleteness': False, 'fullOemReplicaPass': False,
              'modelsDirectory': str(model_dir), 'models': [], 'configs': [],
              'missingAssets': [], 'missingConfigs': [], 'errors': []}
    configs = {}
    for rel in CONFIG_PATHS:
        path = ROOT / rel
        if not path.is_file():
            report['missingConfigs'].append(rel); continue
        try:
            raw = path.read_bytes(); data = json.loads(raw)
            entries = data.get('items', [])
            if isinstance(entries, dict):
                entries = [dict(value, id=key) for key, value in entries.items()]
            for entry in entries:
                ident = entry.get('equipmentId', entry.get('id'))
                if ident in configs:report['errors'].append('Duplicate config for ' + str(ident))
                if ident:configs[ident] = (entry, rel)
            report['configs'].append({'file': rel, 'sha256': hashlib.sha256(raw).hexdigest(), 'items': len(entries)})
        except Exception as exc:
            report['errors'].append(f'{rel}: {exc}')

    for ident in IDS:
        path = model_dir / (ident + '.glb')
        if not path.is_file():
            report['missingAssets'].append(ident); continue
        out = {'id': ident, 'checks': [], 'structuralCompleteness': False, 'oemCompletenessVerified': False}
        report['models'].append(out)
        def check(label, actual, expected, basis='actual_nodes'):
            ok = actual == expected
            out['checks'].append({'name': label, 'actual': actual, 'expected': expected, 'basis': basis, 'status': 'pass' if ok else 'fail'})
            if not ok:report['errors'].append(f'{ident}: {label}: expected {expected!r}, got {actual!r}')
        try:
            gltf, raw = read_glb(path); nodes = gltf.get('nodes', [])
            out.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), nodeCount=len(nodes))
            candidates = [(i, n) for i, n in enumerate(nodes) if n.get('name') == 'stage_' + ident]
            check('one matching equipment root', len(candidates), 1)
            if len(candidates) != 1:continue
            root_index, root_node = candidates[0]; meta = root_node.get('extras', {})
            content = descendants(nodes, root_index)
            check('v3 modelVersion', str(meta.get('modelVersion')), '3.0', 'root_metadata')
            check('stage id', meta.get('stage'), ident, 'root_metadata')
            for key in ['referenceManufacturer', 'referenceModel', 'referenceConfiguration']:
                check(key + ' present', isinstance(meta.get(key), str) and bool(meta[key].strip()), True, 'root_metadata')
            check('partial evidence boundary', meta.get('fidelityStatus'), 'partial_public_reference', 'root_metadata')
            check('no unsupported completeness claim', meta.get('structuralCompleteness') is False, True, 'root_metadata')
            out['referenceModel'] = meta.get('referenceModel'); out['referenceConfiguration'] = meta.get('referenceConfiguration')
            cfg_tuple = configs.get(ident)
            if not cfg_tuple:
                report['missingConfigs'].append('record:' + ident)
            else:
                cfg, cfg_file = cfg_tuple; out['configFile'] = cfg_file
                check('config model matches export', meta.get('referenceModel'), cfg.get('referenceModel'), 'config_vs_root')
                check('config manufacturer matches export', meta.get('referenceManufacturer'), cfg.get('manufacturer'), 'config_vs_root')
                check('config completeness is false', cfg.get('structuralCompleteness') is False, True, 'config_record')
                check('config has unresolved evidence', bool(cfg.get('missing')), True, 'config_record')
                urls = config_source_urls(cfg); out['evidenceUrls'] = urls
                check('config has source URLs', bool(urls), True, 'config_record')
                out['inferredItems'] = len(cfg.get('inferred', []));out['missingEvidenceItems'] = len(cfg.get('missing', []))
                for key, value in COUNT_CONTRACTS.get(ident, {}).items():
                    check('config selected count: ' + key, cfg.get('selectedCounts', {}).get(key), value, 'configuration_record')
                facts = {f.get('item'): f.get('value') for f in cfg.get('verified', []) if isinstance(f, dict)}
                for key, value in FACT_CONTRACTS.get(ident, {}).items():
                    check('config published selection: ' + key, facts.get(key), value, 'configuration_record_with_source')

            def exact(name, within=None):return [n for n in (content if within is None else within) if base_name(n, name)]
            def pattern(expr, within=None):return [n for n in (content if within is None else within) if re.fullmatch(expr, n.get('name', ''))]
            def rotating(label_expr):return [n for n in content if n.get('extras', {}).get('spinAxis') and re.fullmatch(label_expr, n.get('extras', {}).get('label', ''))]
            def population(prefix, count):
                selected = exact(prefix)
                check(prefix + ' population', len(selected), count)
                values = [n.get('extras', {}).get('positionIndex') for n in selected]
                check(prefix + ' unique 1-based indices', sorted(values) if all(isinstance(v, int) for v in values) else values, list(range(1, count + 1)), 'node_position_indices')
            def direct(index, expr):return [nodes[i] for i in nodes[index].get('children', []) if re.fullmatch(expr, nodes[i].get('name', ''))]

            if ident == 'opening':
                for name in ['A12_travelling_tower', 'B12', 'B72', 'A79', 'A49', 'A21']:
                    check('selected opening module ' + name, len(exact(name)), 1)
            elif ident == 'carding':
                check('working flats', len(exact('C81_working_flat')), 40)
                out['notVerifiedByThisCheck'] = 'Return-flat total, wire density and CGC/IGS internals remain unresolved.'
            elif ident == 'drawing':
                feed = [n for n in content if base_name(n, 'sliver_can') and re.fullmatch(r'喂入棉条筒 \d+', n.get('extras', {}).get('label', ''))]
                check('feeding cans', len(feed), 8)
            elif ident == 'combing':
                heads = exact('E90_combing_head');check('E90 complete head count', len(heads), 8)
                check('E90 head indices', sorted(n.get('extras', {}).get('headIndex', -1) for n in heads), list(range(1, 9)))
                check('separate E40 preparation machine', len(exact('OMEGAlap_E40')), 1)
                feed = [n for n in content if base_name(n, 'sliver_can') and re.fullmatch(r'E40喂条筒 \d+', n.get('extras', {}).get('label', ''))]
                check('E40 complete feeding cans', len(feed), 28)
            elif ident == 'roving':
                population('F40_roving_position', 72)
                check('declared spindle count', meta.get('spindleCount'), 72, 'root_metadata')
                check('full section count', len(exact('F40_section_shell')), 4)
                check('published selected machine length', meta.get('machineLengthMetres'), 10.485, 'root_metadata_not_measured_bounds')
                feed = [n for n in content if base_name(n, 'sliver_can') and re.fullmatch(r'F40喂条筒 \d+', n.get('extras', {}).get('label', ''))]
                check('feeding cans', len(feed), 72)
            elif ident == 'spinning':
                population('G38_spinning_position', 288)
                check('declared spindle count', meta.get('spindleCount'), 288, 'root_metadata')
                check('full section count', len(exact('G38_section')), 6)
                check('all roving packages', len(exact('G38_roving_package')), 288)
                check('four-spindle drive groups', len(exact('four_spindle_drive_drum')), 72)
                check('published length formula', meta.get('machineLengthMetres'), 14.260, 'root_metadata_not_measured_bounds')
            elif ident == 'winding':
                population('X6_winding_unit', 96)
                check('declared winding units', meta.get('windingUnitCount'), 96, 'root_metadata')
                check('complete selected support sections', len(exact('X6_section_base')), 16)
                check('current Cop Exchanger', len(exact('Cop_Exchanger_reject_gate')), 1)
                check('automatic package doffer', len(exact('X6_Autodofer')), 1)
            elif ident == 'warping':
                creel = pattern(r'creel_position_\d+(?:\.\d+)?')
                check('complete creel positions', len(creel), 480)
                indices = sorted(int(re.search(r'creel_position_(\d+)', n['name']).group(1)) for n in creel)
                check('all 480 named position indices', indices, list(range(1, 481)), 'node_position_names')
                check('individual creel feed yarns', len(pattern(r'creel_yarn_\d+(?:\.\d+)?')), 480)
                check('declared creel positions', meta.get('modeledCreelPositions'), 480, 'root_metadata')
            elif ident == 'sizing':
                sheets = [(i, n) for i, n in enumerate(nodes) if re.fullmatch(r'beam_sheet_[1-6](?:\.\d+)?', n.get('name', ''))]
                check('complete back-beam feed sheets', len(sheets), 6)
                for i, n in sheets:check(n['name'] + ' actual feed ends', len(pattern(r'warp_end_\d+(?:\.\d+)?', descendants(nodes, i))), 480)
                check('back-beam physical rotating assemblies', len(rotating(r'退绕经轴 [1-6]')), 6)
                check('complete dryer cylinders', len(rotating(r'SoftDry烘筒 \d+')), 12)
                check('HSB size boxes', len(exact('hsb_size_box')), 1)
                check('full process warp sheet', len(direct(root_index, r'warp_end_\d+(?:\.\d+)?')), 2880)
                check('declared back beams', meta.get('selectedBackBeams'), 6, 'root_metadata')
                check('declared drying cylinders', meta.get('selectedDryingCylinders'), 12, 'root_metadata')
            elif ident == 'drawing_in':
                trucks = [(i, n) for i, n in enumerate(nodes) if re.fullmatch(r's67_mobile_truck_[12](?:\.\d+)?', n.get('name', ''))]
                check('complete mobile trucks', len(trucks), 2)
                for i, n in trucks:
                    sub = descendants(nodes, i)
                    check(n['name'] + ' actual warp ends', len(pattern(r'warp_end_\d+(?:\.\d+)?', sub)), 2880)
                    frames = [o for o in sub if 'modeledHealds' in o.get('extras', {})]
                    check(n['name'] + ' heald-frame assemblies', len(frames), 2)
                    check(n['name'] + ' declared batched healds', sum(o['extras']['modeledHealds'] for o in frames), 2880, 'batched_mesh_metadata_not_individual_heald_recount')
            elif ident == 'weaving':
                check('complete warp ends', len(pattern(r'warp_end_\d+(?:\.\d+)?')) + len(pattern(r'shed_warp_[01](?:\.\d+)?')), 2880)
                frames = [n for n in content if 'modeledHealds' in n.get('extras', {})]
                check('heald-frame assemblies', len(frames), 2)
                check('declared batched healds', sum(n['extras']['modeledHealds'] for n in frames), 2880, 'batched_mesh_metadata_not_individual_heald_recount')
                check('weft feeder drums', len(exact('feeder_drum')), 4)
                check('active plus reserve weft packages', len(exact('weft_package')), 8)
                check('paired rapier tapes', len(exact('flat_rapier_tape')), 2)
            elif ident == 'dyeing':
                check('pad working rollers', len(rotating('DyePad泳动工作辊')), 2)
                check('selected CPB batch cart', len(exact('f3_cpb_batch_cart')), 1)
            elif ident == 'stenter':
                rooms = exact('f3_stenter_chamber');check('complete drying chambers', len(rooms), 6)
                check('chamber indices', sorted(n.get('extras', {}).get('chamberIndex', -1) for n in rooms), list(range(1, 7)))
                check('declared chambers', meta.get('verifiedChamberCount'), 6, 'root_metadata')
                check('working chain links', len(exact('f3_chain_clip')), 512)
                check('return chain links', len(exact('f3_chain_return')), 512)
                check('selected working width', meta.get('verifiedWorkingWidthMetres'), 3.2, 'root_metadata_not_measured_width')
            elif ident == 'calender':
                check('s-roll working roll', len(rotating('s-roll复合工作辊')), 1)
                check('heated steel working roll', len(rotating('镀铬加热钢辊')), 1)
            elif ident == 'inspection':
                check('review workstation', len(exact('f3_review_station')), 1)
                out['motorRequirement'] = 'Not required: selected asset is a standalone optical inspection unit, not a fabricated unwinder/rewinder.'
            out['status'] = 'pass' if all(c['status'] == 'pass' for c in out['checks']) else 'fail'
        except Exception as exc:
            out['status'] = 'fail';report['errors'].append(f'{ident}: {type(exc).__name__}: {exc}')

    motor = model_dir / 'motor.glb'
    if motor.is_file():
        try:
            data, raw = read_glb(motor)
            found = [n for n in data.get('nodes', []) if n.get('name') == 'stage_motor']
            report['motorDetailAsset'] = {'present': True, 'sha256': hashlib.sha256(raw).hexdigest(), 'rootFound': len(found) == 1, 'classification': 'Independent educational motor detail; not promoted to a current OEM motor replica by this validator.', 'structuralCompleteness': False}
        except Exception as exc:report['errors'].append('motor: ' + str(exc))
    else:
        report['motorDetailAsset'] = {'present': False, 'classification': 'Outside the 16-stage v3 selected-population check.'}
    report['missingConfigs'] = sorted(set(report['missingConfigs']))
    incomplete = bool(report['missingAssets'] or report['missingConfigs'])
    report['status'] = 'fail' if report['errors'] else ('incomplete' if incomplete else 'pass')
    report['passMeaning'] = 'All available selected-population and provenance checks passed. This never certifies no omissions, OEM completeness, current hidden design or visual/physical accuracy.'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'modelsChecked': len(report['models']), 'missingAssets': report['missingAssets'], 'missingConfigs': report['missingConfigs'], 'errors': report['errors'], 'structuralCompleteness': False, 'report': str(output)}, ensure_ascii=False, indent=2))
    return 1 if report['errors'] else (0 if not incomplete or args.allow_partial else 2)


if __name__ == '__main__':
    raise SystemExit(main())
