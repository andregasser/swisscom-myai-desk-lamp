"""Validate exported STLs, sliced 3MFs and model/brim extrusion coordinates."""
from pathlib import Path
import hashlib
import json
import re
import zipfile
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
report = {'stl': {}, 'plates': {}, 'physical_print_verified': False}
for file in sorted((ROOT / 'output/stl').glob('*.stl')):
    mesh = trimesh.load_mesh(file)
    assert mesh.is_watertight and mesh.is_winding_consistent, file
    assert mesh.volume > 0 and len(mesh.split()) == 1, file
    assert np.all(mesh.extents <= [256, 256, 250]), file
    assert abs(mesh.bounds[0, 2]) < .001, file
    report['stl'][file.name] = {'closed_solid': True, 'size_mm': mesh.extents.tolist()}

for file in sorted((ROOT / 'output/print').glob('*.3mf')):
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        config = json.loads(archive.read('Metadata/project_settings.config'))
        assert config['printer_model'] == 'Bambu Lab P1S'
        assert config['nozzle_diameter'] == ['0.4']
        assert config['filament_type'] == ['PLA']
        assert config['curr_bed_type'] == 'Textured PEI Plate'
        assert config['enable_support'] == '0'
        assert config['sparse_infill_density'] == '100%'
        assert config['wall_generator'] == 'arachne'
        raw = archive.read('Metadata/plate_1.gcode')
        stored = archive.read('Metadata/plate_1.gcode.md5').decode().strip()
        assert hashlib.md5(raw).hexdigest().lower() == stored.lower()
        code = raw.decode()
        assert 'machine: P1S' in code and 'G28' in code
        assert 'FEATURE: Support' not in code
        # Official startup/cleanup uses positions outside the nominal bed.
        # Check only the slicer's actual object/brim paths, not Custom G-code.
        feature = 'Custom'
        x = y = z = 0.0
        points = []
        for line in code.splitlines():
            if line.startswith('; FEATURE: '):
                feature = line.removeprefix('; FEATURE: ')
            if not re.match(r'^G[0123] ', line):
                continue
            fields = {k: float(v) for k, v in re.findall(r'\b([XYZE])(-?\d*\.?\d+)', line)}
            x, y, z = fields.get('X', x), fields.get('Y', y), fields.get('Z', z)
            if feature != 'Custom' and fields.get('E', 0) > 0 and ('X' in fields or 'Y' in fields):
                assert 0 <= x <= 256 and 0 <= y <= 256 and 0 <= z <= 250, (file.name, line)
                # Account for half the widest model/brim line (0.5 mm).
                assert not (x < 18.25 and y < 28.25), (file.name, 'front-left exclusion', line)
                points.append((x, y, z))
        assert len(points) > 100
        result = json.loads(file.with_name(file.stem.replace('_P1S', '_slicer_result') + '.json').read_text())
        assert result['return_code'] == 0
        plate = result['sliced_plates'][0]
        assert not plate['warning_message']
        report['plates'][file.name] = {
            'bambu_studio': '02.08.02.61', 'sliced_successfully': True,
            'slicer_print_warnings': plate['warning_message'],
            'estimated_minutes': round(plate['total_predication'] / 60, 1),
            'estimated_filament_g': round(plate['filaments'][0]['total_used_g'], 2),
            'model_and_brim_extrusion_bounds_mm': [np.min(points, axis=0).tolist(), np.max(points, axis=0).tolist()],
            'gcode_md5_valid': True, 'supports_generated': False,
            'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
        }
(ROOT / 'output/print_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['plates'], indent=2))
