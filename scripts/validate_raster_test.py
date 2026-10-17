"""Verify ink remains in each full cell's central 0.2 mm disk after slicing."""
from collections import defaultdict
import json
import math
from pathlib import Path
import re
import zipfile

import numpy as np
from PIL import Image, ImageDraw
import trimesh

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT/'cad/multicolor_parameters.json').read_text())
OUT = ROOT/'output'/P['output_folder']


def model_segments(code, config):
    """Polyline approximation of G2/G3 to <=0.05 mm steps, in model XY space."""
    offset = np.array([float(v) for v in config['extruder_offset'][0].split('x')])
    feature, tool, changing = 'Custom', 0, False
    x = y = z = 0.
    width = None
    for line in code.splitlines():
        match = re.match(r'M620 S(\d+)', line)
        if match:
            tool, changing = int(match[1]), True
        if line.startswith('M621 '):
            changing = False
        if line.startswith('; FEATURE: '):
            feature = line.removeprefix('; FEATURE: ')
        if line.startswith('; LINE_WIDTH: '):
            width = float(line.split(':')[1])
        if not re.match(r'^G[0123] ', line):
            continue
        fields = {k: float(v) for k, v in re.findall(r'\b([XYZIJE])(-?\d*\.?\d+)', line)}
        start = np.array((x, y))
        x, y, z = fields.get('X', x), fields.get('Y', y), fields.get('Z', z)
        if changing or feature in ('Custom', 'Prime tower', 'Brim') or fields.get('E', 0) <= 0:
            continue
        if not ('X' in fields or 'Y' in fields):
            continue
        assert width is not None and 0 < width < 2
        end = np.array((x, y))
        points = [start, end]
        if line.startswith(('G2 ', 'G3 ')):
            assert 'I' in fields or 'J' in fields
            center = start + (fields.get('I', 0), fields.get('J', 0))
            radius = np.linalg.norm(start-center)
            a = math.atan2(*(start-center)[::-1])
            b = math.atan2(*(end-center)[::-1])
            angle = (b-a) % (2*math.pi) if line.startswith('G3 ') else -((a-b) % (2*math.pi))
            count = max(1, math.ceil(abs(angle)*radius/.05))
            points = [start, *[center+radius*np.array((math.cos(a+angle*i/count),
                       math.sin(a+angle*i/count))) for i in range(1, count)], end]
        for a, b in zip(points, points[1:]):
            if np.linalg.norm(b-a) > 1e-7:
                yield round(z, 3), tool+1, a+offset, b+offset, width


def validate(file=OUT/'print/09_raster_test_P1S.3mf', original=False):
    folder = 'raster_original_test' if original else 'raster_test'
    color_layer = .6 if original else .2
    card = json.loads((OUT/folder/'geometry_validation.json').read_text())
    for slot in range(1, 5):
        mesh = trimesh.load_mesh(OUT/folder/'stl'/f'slot_{slot}.stl')
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
        assert abs(mesh.bounds[0, 2]-(.4 if original and slot != 1 else 0)) < 1e-6
        assert abs(mesh.bounds[1, 2]-(card['size_mm'][2] if slot == 1 or original else card['color_depth_mm'])) < 1e-6
    with zipfile.ZipFile(file) as archive:
        config = json.loads(archive.read('Metadata/project_settings.config'))
        code = archive.read('Metadata/plate_1.gcode').decode()
    segments = defaultdict(list)
    draw_scale, margin = 12, 3
    width, height = card['size_mm'][:2]
    picture = Image.new('RGB', (round((width+2*margin)*draw_scale), round((height+2*margin)*draw_scale)), '#E8E8EB')
    draw = ImageDraw.Draw(picture)
    origin = np.array(card['print_offset_mm'][:2])
    for z, slot, a, b, line_width in model_segments(code, config):
        segments[z, slot].append([*a, *b, line_width/2])
        if z == color_layer:
            coords = np.array([a,b])-origin
            if original:
                coords[:, 1] = height-coords[:, 1]
            xy = ((coords+margin)*draw_scale).flatten().tolist()
            draw.line(xy, fill=P['colors'][slot-1]['hex'], width=max(1, round(line_width*draw_scale)))
    picture.save(OUT/'preview'/('raster_original_toolpaths.png' if original else 'raster_toolpaths.png'))
    arrays = {key: np.array(value) for key, value in segments.items()}
    failures, worst = [], 0.
    counts = defaultdict(int)
    # Check ink reaches the central 0.2 mm disk of every full 0.8 mm cell. Arachne
    # can leave small central gaps between variable-width paths; this is a cell
    # retention check, not a claim of complete coverage. Both white backing layers
    # must cover the centers, with 0.03 mm rounding/arc approximation tolerance.
    for probe in [*card['full_cell_probes'], *card.get('reference_fields', [])]:
        point = np.array(probe['xy_mm'])+origin
        for layer in (.2, .4, .6):
            slot = probe['slot'] if layer == color_layer else 1
            lines = arrays[layer, slot]
            a, delta = lines[:, :2], lines[:, 2:4]-lines[:, :2]
            t = np.clip(np.sum((point-a)*delta, axis=1)/np.sum(delta*delta, axis=1), 0, 1)
            clearance = np.linalg.norm(a+t[:, None]*delta-point, axis=1)-lines[:, 4]
            gap = float(np.min(clearance))
            worst = max(worst, gap)
            if gap > (.1 if layer == color_layer else .03):
                failures.append({'layer': layer, **probe, 'gap_mm': gap})
        counts[probe['slot']] += 1
    assert not failures, f'{len(failures)} uncovered cell/layer samples: {failures[:8]}'
    report = {'full_cell_count': len(card['full_cell_probes']),
              ('color_layer_cells_and_references_by_slot' if original else 'first_layer_cell_central_disks_verified_by_slot'): dict(counts),
              'central_disk_diameter_mm': .2,
              'both_white_backing_layers_verified_at_all_cell_centers': True,
              'missing_cell_layer_samples': len(failures), 'max_center_gap_mm': worst,
              'extrusion_widths_and_arcs_considered': True,
              'physical_print_verified': False,
              'scope': 'Ink reaches central 0.2 mm disks of full cells. Not complete surface coverage, exact corners, partial boundary cells or real optical mixing.'}
    (OUT/folder/'toolpath_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
