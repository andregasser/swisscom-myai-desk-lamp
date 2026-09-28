"""Resolve bundled Bambu Studio presets, including inherited G-code templates."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('resources', type=Path, help='BambuStudio resources/profiles/BBL')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
out = root / 'output/profiles'
out.mkdir(exist_ok=True)
index = {}
for p in args.resources.rglob('*.json'):
    data = json.loads(p.read_text())
    if 'name' in data:
        index[data['name']] = data
    index.setdefault(p.stem, data)


def resolve(name, stack=()):
    assert name not in stack, name
    d = index[name]
    merged = {}
    if d.get('inherits'):
        merged.update(resolve(d['inherits'], stack + (name,)))
    for template in d.get('include', []):
        merged.update(resolve(template, stack + (name,)))
    merged.update(d)
    merged.pop('inherits', None)
    merged.pop('include', None)
    return merged


machine = resolve('Bambu Lab P1S 0.4 nozzle')
assert len(machine['machine_start_gcode']) > 1000
process = resolve('0.20mm Standard @BBL X1C')
process.update({
    'name': 'myAI Cube 0.20mm P1S', 'from': 'User',
    'print_settings_id': 'myAI Cube 0.20mm P1S',
    'layer_height': '0.2', 'initial_layer_print_height': '0.2',
    'wall_generator': 'arachne', 'wall_loops': '2',
    'line_width': '0.4', 'outer_wall_line_width': '0.4', 'inner_wall_line_width': '0.4',
    'sparse_infill_density': '100%', 'sparse_infill_pattern': 'zig-zag',
    'top_shell_layers': '5', 'bottom_shell_layers': '5',
    'enable_support': '0', 'brim_type': 'outer_only', 'brim_width': '4',
    'brim_object_gap': '0.15', 'seam_position': 'back',
    'outer_wall_speed': ['45', '45'], 'inner_wall_speed': ['60', '60'],
    'initial_layer_speed': ['25', '25'], 'initial_layer_infill_speed': ['40', '40'],
    'top_surface_speed': ['40', '40'], 'internal_solid_infill_speed': ['80', '80'],
    'sparse_infill_speed': ['80', '80'], 'bridge_speed': ['30', '30'],
    'outer_wall_acceleration': ['1500', '1500'],
    'default_acceleration': ['3000', '3000'],
    'curr_bed_type': 'Textured PEI Plate',
})
filament = resolve('Generic PLA')
filament.update({'filament_colour': ['#FFFFFF'], 'filament_settings_id': ['Generic PLA'],
                 'filament_max_volumetric_speed': ['12', '12']})
for name, data in [('p1s_0.4', machine), ('cube_0.20', process), ('pla_white', filament)]:
    (out / (name + '.json')).write_text(json.dumps(data, indent=2) + '\n')
print('Resolved P1S, process and Generic PLA profiles to', out)
