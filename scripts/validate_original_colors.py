"""Check gradient sampling independently against CairoSVG; show source vs print."""
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import manifold3d as m
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'cad'))
import raster_original as raster
import build_raster_test as old

OUT = raster.ams.OUT
source_path = ROOT/'assets/logos'/raster.ams.P['logo_source']
source = source_path.read_text()
image = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=source.encode(), output_width=2160, output_height=2160))).convert('RGBA')
pixels = np.asarray(image)
scale = raster.ams.mono.P['logo_canvas_mm']/216
samples, differences, palette_errors = 0, [], []
for section, p0, direction, stops in raster.sources():
    # Direct endpoint checks include the cyan stops omitted by the earlier model.
    for offset, color in stops:
        assert np.allclose(raster.sample_srgb([p0+offset*direction],p0,direction,stops)[0], raster.hex_rgb(color))
    x0,y0,x1,y1 = section.bounds()
    for y in np.arange(y0+.4,y1,.8):
        for x in np.arange(x0+.4,x1,.8):
            px, py = int(x/scale*10), int(y/scale*10)
            if np.any(pixels[py-1:py+2,px-1:px+2,3] != 255):
                continue
            # Evaluate the actual raster pixel center, avoiding subpixel mismatch.
            point = np.array([(px+.5)/10*scale,(py+.5)/10*scale])
            probe = m.CrossSection.square((.04,.04)).translate(point-.02)
            if (probe ^ section).area() < .00159:
                continue
            target = raster.sample_srgb([point],p0,direction,stops)[0]
            differences.append(float(np.max(np.abs(target*255-pixels[py,px,:3]))))
            linear = raster.linear_rgb(target)
            weights = raster.palette_weights([linear])[0]
            palette_errors.append(float(np.linalg.norm(weights@raster.PALETTE-linear)))
            samples += 1
assert samples > 2000
assert max(differences) < 3, max(differences)
report = {'source': source_path.name, 'independent_renderer': 'CairoSVG',
          'opaque_source_samples_checked': samples,
          'max_source_channel_difference_8bit': max(differences),
          'all_original_gradient_stops_checked': True,
          'mean_linear_rgb_projection_error': float(np.mean(palette_errors)),
          'scope': 'Source sampling and ideal nominal palette mixtures only; not final pixel accuracy or measured filament color.',
          'physical_color_match_verified': False}
(OUT/'raster_original_test/color_validation.json').write_text(json.dumps(report,indent=2)+'\n')

# Compare at the same exact contour size, on the same white background.
outline = old.combine([region for region, *_ in raster.sources()])
x0,y0,x1,y1 = outline.bounds()
border=old.BORDER
w,h=x1-x0+2*border,y1-y0+2*border
original = ET.fromstring(source)
original.set('viewBox', f'{(x0-border)/scale} {(y0-border)/scale} {w/scale} {h/scale}')
original.set('x','24'); original.set('y','86')
original.set('width','480'); original.set('height',str(480*h/w))
new = ET.parse(OUT/'raster_original_test/raster.svg').getroot()
new.set('x','536'); new.set('y','86')
new.set('width','480'); new.set('height',str(480*h/w))
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="720" viewBox="0 0 1040 720">
<rect width="1040" height="720" fill="white"/>
<g font-family="DejaVu Sans, sans-serif" fill="#182337">
<text x="24" y="34" font-size="22" font-weight="bold">Original-SVG → Raster mit vorhandenen Filamentfarben</text>
<text x="24" y="66" font-size="18">Original: vollständiger SVG-Verlauf</text>
<text x="536" y="66" font-size="18">Neue Druckprobe: 0,8-mm-Raster</text>
{ET.tostring(original,encoding='unicode')}
{ET.tostring(new,encoding='unicode')}
<text x="24" y="660" font-size="16">Weiß im Raster ist beabsichtigt. Cyan liegt außerhalb der vorhandenen Druckpalette.</text>
<text x="24" y="689" font-size="15">Nominelle Bildschirmfarben; keine Vorhersage von Filamentfarbe oder Hinterleuchtung.</text>
</g></svg>'''
(OUT/'preview/raster_original_comparison.svg').write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(OUT/'preview/raster_original_comparison.png'))
print(json.dumps(report,indent=2))
