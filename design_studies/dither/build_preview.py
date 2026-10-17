"""Visual study only: ordered three-color dithering within original SVG paths."""
from pathlib import Path
from html import escape
import json
import math
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
from svgpathtools import parse_path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = json.loads((ROOT / 'cad/multicolor_parameters.json').read_text())
MONO = json.loads((ROOT / 'cad/parameters.json').read_text())
SVG = ET.parse(ROOT / 'assets/logos' / P['logo_source']).getroot()
NS = '{http://www.w3.org/2000/svg}'
SCALE = MONO['logo_canvas_mm'] / 216
CELL_MM = 0.8
PITCH = CELL_MM / SCALE
COLORS = [P['colors'][i]['hex'] for i in (3, 2, 1)]  # red, violet, blue
# Broaden the transitions around the former abrupt band boundaries.
STOPS = [0.0, 0.36, 0.80]
BAYER = np.array([[0, 2], [3, 1]])
for _ in range(2):
    BAYER = np.block([[4*BAYER, 4*BAYER+2], [4*BAYER+3, 4*BAYER+1]])
THRESHOLDS = (BAYER + .5) / BAYER.size


def color_index(t, column, row):
    if t <= STOPS[0]:
        return 0
    if t >= STOPS[-1]:
        return 2
    lo = 0 if t < STOPS[1] else 1
    fraction = (t - STOPS[lo]) / (STOPS[lo+1] - STOPS[lo])
    return lo + int(fraction > THRESHOLDS[row % 8, column % 8])


defs = []
groups = {}
for path in SVG.findall(NS + 'path'):
    gradient = SVG.find(f"{NS}defs/{NS}linearGradient[@id='{path.attrib['fill'][5:-1]}']")
    vector = tuple(float(gradient.attrib[k]) for k in ('x1', 'y1', 'x2', 'y2'))
    groups.setdefault(vector, []).append(path.attrib['d'])

band_uses, raster_uses = [], []
counts = [0, 0, 0]
for index, (vector, paths) in enumerate(groups.items()):
    p0, p1 = np.array(vector[:2]), np.array(vector[2:])
    direction = p1 - p0
    clip = f'outline{index}'
    defs.append(f'<clipPath id="{clip}" clipPathUnits="userSpaceOnUse">')
    defs.extend(f'<path d="{escape(d)}" clip-rule="evenodd"/>' for d in paths)
    defs.append('</clipPath>')
    gradient_id = f'bands{index}'
    defs.append(f'<linearGradient id="{gradient_id}" gradientUnits="userSpaceOnUse" '
                f'x1="{p0[0]}" y1="{p0[1]}" x2="{p1[0]}" y2="{p1[1]}">')
    edges = P['gradient_band_edges']
    for t, color in ((0, COLORS[0]), (edges[0], COLORS[0]), (edges[0], COLORS[1]),
                     (edges[1], COLORS[1]), (edges[1], COLORS[2]), (1, COLORS[2])):
        defs.append(f'<stop offset="{t}" stop-color="{color}"/>')
    defs.append('</linearGradient>')
    band_uses.append(f'<rect width="216" height="216" fill="url(#{gradient_id})" clip-path="url(#{clip})"/>')
    bounds = [parse_path(d).bbox() for d in paths]
    xmin, xmax = min(b[0] for b in bounds), max(b[1] for b in bounds)
    ymin, ymax = min(b[2] for b in bounds), max(b[3] for b in bounds)
    cells = [[], [], []]
    for row in range(math.floor(ymin/PITCH), math.ceil(ymax/PITCH)):
        for column in range(math.floor(xmin/PITCH), math.ceil(xmax/PITCH)):
            center = np.array([(column+.5)*PITCH, (row+.5)*PITCH])
            t = np.dot(center-p0, direction) / np.dot(direction, direction)
            color = color_index(t, column, row)
            counts[color] += 1
            cells[color].append(f'M{column*PITCH:.6f},{row*PITCH:.6f}h{PITCH:.6f}v{PITCH:.6f}h-{PITCH:.6f}z')
    # Crisp interior pixels avoid white antialiasing seams between adjacent cells.
    raster_uses.append(f'<g clip-path="url(#{clip})">')
    raster_uses.extend(f'<path d="{"".join(cells[i])}" fill="{color}" shape-rendering="crispEdges"/>'
                       for i, color in enumerate(COLORS))
    raster_uses.append('</g>')

defs.extend(['<g id="bands">', *band_uses, '</g>', '<g id="raster">', *raster_uses, '</g>'])
definitions = '<defs>' + ''.join(defs) + '</defs>'


def viewport(ref, x, y, width, height, box='0 0 216 216'):
    return f'<svg x="{x}" y="{y}" width="{width}" height="{height}" viewBox="{box}"><use href="#{ref}"/></svg>'


standalone = f'<svg xmlns="http://www.w3.org/2000/svg" width="116mm" height="116mm" viewBox="0 0 216 216">{definitions}<rect width="216" height="216" fill="white"/><use href="#raster"/></svg>'
(HERE / 'logo_dither.svg').write_text(standalone)
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="960" viewBox="0 0 1600 960">',
         definitions, '<rect width="1600" height="960" fill="#F2F3F6"/>',
         '<g font-family="DejaVu Sans, sans-serif" fill="#182237">',
         '<text x="48" y="65" font-size="34" font-weight="bold">myAI · Gerasterter Farbverlauf</text>',
         '<text x="48" y="104" font-size="19" fill="#556176">Rot → Violett → Blau · dieselben drei Filamentfarben, weichere Übergänge</text>']
for x, heading, sub in ((48, 'Bisher', 'Drei abgegrenzte Farbbänder'),
                        (568, 'Vorschlag', 'Farben räumlich ineinander verteilen'),
                        (1088, 'Raster im Detail', 'Vergrösserte Ausschnitte')):
    parts.extend([f'<rect x="{x}" y="144" width="464" height="634" rx="18" fill="white"/>',
                  f'<text x="{x+24}" y="186" font-size="24" font-weight="bold">{heading}</text>',
                  f'<text x="{x+24}" y="219" font-size="16" fill="#556176">{sub}</text>'])
parts.extend([viewport('bands', 64, 266, 432, 432), viewport('raster', 584, 266, 432, 432),
              viewport('raster', 1112, 246, 416, 226, '88 30 51 54'),
              viewport('raster', 1112, 508, 416, 226, '27 143 54 40'),
              '<text x="1112" y="494" font-size="14" fill="#556176">Stern: Violett und Blau verzahnen sich.</text>',
              '<text x="1112" y="756" font-size="14" fill="#556176">Schrift: Rot und Violett verzahnen sich.</text>'])
for i, (name, color) in enumerate(zip(('Rot', 'Violett', 'Blau'), COLORS)):
    x = 48 + 160*i
    parts.extend([f'<rect x="{x}" y="817" width="25" height="25" rx="5" fill="{color}"/>',
                  f'<text x="{x+38}" y="837" font-size="18">{name}</text>'])
parts.extend(['<text x="568" y="837" font-size="18">Rasterweite: 0,8 mm am späteren Logo</text>',
              '<text x="48" y="894" font-size="17" fill="#556176">Gestaltungsstudie aus den Originalkonturen. Nah sichtbar gerastert; aus Abstand optisch weicher.</text>',
              '<text x="48" y="925" font-size="17" fill="#556176">Nominelle Bildschirmfarben · noch kein geslictes Druckmodell und keine Vorhersage der Leuchtwirkung.</text>',
              '</g></svg>'])
preview = ''.join(parts)
(HERE / 'comparison.svg').write_text(preview)
cairosvg.svg2png(bytestring=preview.encode(), write_to=str(HERE / 'comparison.png'))
# Check that the pattern actually mixes neighboring colors across both transitions.
assert all(count > 0 for count in counts)
for t, expected in ((.18, {0, 1}), (.58, {1, 2})):
    assert {color_index(t, x, y) for x in range(8) for y in range(8)} == expected
print(f'Generated {HERE / "comparison.png"}; {CELL_MM} mm grid, original paths and gradient vectors.')
