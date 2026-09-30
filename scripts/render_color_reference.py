"""Compare unchanged source SVGs with the CAD's nominal, unlit sRGB palette."""
from pathlib import Path
import sys
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cad'))
import build_multicolor as cad

OUT = ROOT / 'output/multicolor_v3/preview'
pieces = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="570" viewBox="0 0 1080 570">',
          '<rect width="1080" height="570" fill="#F1F3F7"/>',
          '<g font-family="DejaVu Sans, sans-serif" fill="#182337">',
          '<text x="24" y="34" font-size="23" font-weight="bold">Originalfarben und Druckpalette</text>']
for x, label, mode, background in (
    (24, 'Original: Light', 'Light', '#FFFFFF'),
    (376, 'Original: Dark', 'Dark', '#001155'),
    (728, 'Druck: drei Farbstufen + Weiß', None, '#FFFFFF'),
):
    pieces.append(f'<text x="{x}" y="66" font-size="17">{label}</text>')
    pieces.append(f'<rect x="{x}" y="82" width="328" height="328" rx="8" fill="{background}"/>')
    if mode:
        source = (ROOT / 'assets/logos' / f'Mode={mode}, Type=Stacked.svg').read_text()
        source = source.replace('width="216" height="216"', f'x="{x+20}" y="102" width="288" height="288"', 1)
        pieces.append(source)
    else:
        regions = cad.logo_regions()
        # Fit the actual logo outline, preserving its aspect ratio and colors.
        xmin, ymin, xmax, ymax = regions[3].bounds()
        width, height = xmax-xmin, ymax-ymin
        scale = 246 / height
        pieces.append(f'<g transform="translate({x+164-width*scale/2} {102+(288-246)/2}) scale({scale}) translate({-xmin} {-ymin})">')
        for region, color in zip(regions[:3], cad.P['colors'][1:]):
            contours = []
            for polygon in region.to_polygons():
                contours.append('M'+' L'.join(f'{px:.5f},{py:.5f}' for px, py in polygon)+' Z')
            pieces.append(f'<path d="{" ".join(contours)}" fill="{color["hex"]}" fill-rule="evenodd"/>')
        pieces.append('</g>')
pieces.append('<text x="24" y="445" font-size="16">Nominelle Druckfarben (ohne Beleuchtung oder fotografische Tonwertkorrektur):</text>')
for index, color in enumerate(cad.P['colors']):
    x = 24 + index*260
    pieces.append(f'<rect x="{x}" y="465" width="38" height="38" rx="4" fill="{color["hex"]}" stroke="#BDC4CF"/>')
    pieces.append(f'<text x="{x+50}" y="488" font-size="16">{color["name"]} · {color["hex"]}</text>')
pieces.extend(['<text x="24" y="540" font-size="14">Violett ist eine gewählte Zwischenfarbe. Die Druckpalette bildet den Originalverlauf nicht exakt ab.</text>',
               '</g></svg>'])
svg = '\n'.join(pieces)
(OUT / 'color_reference.svg').write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OUT / 'color_reference.png'))
print(OUT / 'color_reference.png')
