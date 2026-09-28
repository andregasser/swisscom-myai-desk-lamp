"""Check v3 mesh integrity, AMS assignment, sliced layers and print-bed bounds."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/multicolor_v3'
P = json.loads((ROOT / 'cad/multicolor_parameters.json').read_text())
report = {'physical_print_verified': False, 'stl': {}, 'plates': {}}
assert len(list((OUT / 'stl').glob('*.stl'))) == 7
assert {p.stem for p in (OUT / 'print').glob('*.3mf')} == {
    '01_color_test_P1S', '02_panel_P1S', '03_frame_P1S', '04_base_P1S', '05_lid_P1S'}
for file in sorted((OUT / 'stl').glob('*.stl')):
    mesh = trimesh.load_mesh(file)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, file
    assert np.all(mesh.extents <= [256, 256, 250]), file
    assert abs(mesh.bounds[0, 2]) < .001, file
    report['stl'][file.name] = {'watertight': True, 'size_mm': mesh.extents.tolist(),
                               'components': len(mesh.split())}

for file in sorted((OUT / 'print').glob('*.3mf')):
    multi = file.name.startswith(('01_', '02_'))
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        config = json.loads(archive.read('Metadata/project_settings.config'))
        assert config['printer_model'] == 'Bambu Lab P1S'
        assert config['nozzle_diameter'] == ['0.4']
        assert config['filament_type'] == ['PLA'] * (4 if multi else 1)
        assert config['curr_bed_type'] == 'Textured PEI Plate'
        assert config['enable_support'] == '0'
        assert config['sparse_infill_density'] == '100%'
        assert config['wall_generator'] == 'arachne'
        if multi:
            assert config['filament_colour'] == [c['hex'] for c in P['colors']]
            assert config['enable_prime_tower'] == '1'
            assert config['flush_into_infill'] == '0'
            settings = ET.fromstring(archive.read('Metadata/model_settings.config'))
            parts = settings.findall('object/part')
            assert len(parts) == 4
            for slot, part in enumerate(parts, 1):
                meta = {e.get('key'): e.get('value') for e in part.findall('metadata')}
                assert meta['extruder'] == str(slot)
                assert meta['source_volume_id'] == str(slot - 1)
                assert meta['name'] == P['colors'][slot - 1]['name']
                assert all(int(v) == 0 for k, v in part.find('mesh_stat').attrib.items() if k != 'face_count')
        raw = archive.read('Metadata/plate_1.gcode')
        assert hashlib.md5(raw).hexdigest().lower() == archive.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
        code = raw.decode()
        assert 'machine: P1S' in code and 'G28' in code and 'M83' in code
        assert 'FEATURE: Support' not in code
        feature, tool, changing = 'Custom', 0, False
        x = y = z = 0.
        points, layers = [], defaultdict(set)
        for line in code.splitlines():
            ams = re.match(r'M620 S(\d+)', line)
            if ams:
                tool, changing = int(ams[1]), True
            if line.startswith('M621 '):
                changing = False
            if line.startswith('; FEATURE: '):
                feature = line.removeprefix('; FEATURE: ')
            if not re.match(r'^G[0123] ', line):
                continue
            fields = {k: float(v) for k, v in re.findall(r'\b([XYZE])(-?\d*\.?\d+)', line)}
            x, y, z = fields.get('X', x), fields.get('Y', y), fields.get('Z', z)
            if feature == 'Custom' or changing or fields.get('E', 0) <= 0 or not ('X' in fields or 'Y' in fields):
                continue
            assert 0 <= x <= 256 and 0 <= y <= 256 and 0 <= z <= 250, (file.name, line)
            assert not (x < 18.25 and y < 28.25), (file.name, 'bed exclusion', line)
            points.append((x, y, z))
            if feature not in ('Prime tower', 'Brim'):
                layers[round(z, 3)].add(tool + 1)
        assert len(points) > 100
        if multi:
            assert dict(layers) == {.2: {1, 2, 3, 4}, .4: {1, 2, 3, 4}, .6: {1}, .8: {1}}, layers
        result = json.loads(file.with_name(file.stem.replace('_P1S', '_slicer_result') + '.json').read_text())
        assert result['return_code'] == 0
        plate = result['sliced_plates'][0]
        assert not plate['warning_message']
        assert plate['filament_change_times'] == (6 if multi else 0)
        report['plates'][file.name] = {
            'sliced_successfully': True, 'bambu_studio': '02.08.02.61',
            'estimated_minutes': round(plate['total_predication'] / 60, 1),
            'estimated_filament_g_including_flush_and_tower': round(sum(f['total_used_g'] for f in plate['filaments']), 2),
            'color_changes': plate['filament_change_times'],
            'print_extrusion_bounds_mm': [np.min(points, axis=0).tolist(), np.max(points, axis=0).tolist()],
            'model_layer_slots': {str(z): sorted(slots) for z, slots in layers.items()} if multi else 'white only',
            'slicer_print_warnings': plate['warning_message'], 'supports_generated': False,
            'gcode_md5_valid': True, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
        }
(OUT / 'print_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['plates'], indent=2))
