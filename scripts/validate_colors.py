"""Verify nominal palette values in the reference sheet and technical render."""
from pathlib import Path
from collections import Counter
import json
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / 'cad/multicolor_parameters.json').read_text())
OUT = ROOT / 'output' / P['output_folder']
source = ET.parse(ROOT / 'assets/logos' / P['logo_source']).getroot()
stops = {e.attrib['stop-color'].upper() for e in source.iter() if 'stop-color' in e.attrib}
reference = Image.open(OUT / 'preview/color_reference.png').convert('RGB')
render = Image.open(OUT / 'preview/assembled.png').convert('RGB')
pixels = Counter(render.get_flattened_data())
report = {'version': P['version'], 'render_mode': 'nominal sRGB camera colors; shaded white geometry',
          'predicts_physical_filament_color': False, 'colors': {}}
for i, color in enumerate(P['colors']):
    target = tuple(int(color['hex'][j:j+2], 16) for j in (1, 3, 5))
    assert reference.getpixel((24 + i*260 + 19, 484)) == target, color
    entry = {'hex': color['hex'], 'reference_swatch_exact': True}
    if i:
        # Check large interiors, excluding antialiasing/denoising boundaries.
        assert pixels[target] > 1000, (color, pixels[target])
        entry['exact_render_pixels'] = pixels[target]
        entry['is_original_svg_stop'] = color['hex'].upper() in stops
        if color['name'] in ('Rot', 'Blau'):
            assert entry['is_original_svg_stop'], color
    report['colors'][color['name']] = entry
report['violet_note'] = 'Chosen intermediate printing color, not an original SVG stop.'
(OUT / 'color_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
