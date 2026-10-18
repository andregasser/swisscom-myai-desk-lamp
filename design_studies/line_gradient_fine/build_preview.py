"""2D design study: original gradients mapped to continuous 0.48 mm straight color bands.

Produces SVG/PNG and a planar geometry report only; no CAD, STL, 3MF or G-code.
The proposed cyan spool replaces violet; nominal colors are not filament measurements.
"""
from pathlib import Path
from itertools import combinations
import hashlib
import json
import math
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
from shapely import Polygon, GeometryCollection, unary_union
from svgpathtools import parse_path, Line

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'assets/logos/Mode=Dark, Type=Stacked.svg'
SCALE = json.loads((ROOT/'cad/parameters.json').read_text())['logo_canvas_mm']/216
PITCH = .48
COLORS = ['#F23232', '#1FB9FF', '#0445C8']
NS = '{http://www.w3.org/2000/svg}'


def rgb(color):
    return np.array([int(color[i:i+2], 16)/255 for i in (1, 3, 5)])


def linear(values):
    return np.where(values <= .04045, values/12.92, ((values+.055)/1.055)**2.4)


def weights(target):
    palette = linear(np.array([rgb(c) for c in COLORS]))
    best, result = float('inf'), None
    for size in (1, 2, 3):
        for ids in combinations(range(3), size):
            colors = palette[list(ids)]
            if size == 1:
                w = np.ones(1)
            else:
                tail = np.linalg.lstsq((colors[1:]-colors[0]).T, target-colors[0], rcond=None)[0]
                w = np.r_[1-tail.sum(), tail]
            error = np.sum((w@colors-target)**2)
            if np.min(w) >= -1e-9 and error < best:
                best, result = error, np.zeros(3)
                result[list(ids)] = np.maximum(w, 0)
    return result/result.sum()


def polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape]
    return [p for child in shape.geoms for p in polygons(child)]


def svg_path(shape):
    paths = []
    for poly in polygons(shape):
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)
            paths.append('M'+'L'.join(f'{x:.5f},{y:.5f}' for x,y in coords)+'Z')
    return ''.join(paths)


svg = ET.parse(SOURCE).getroot()
gradients = {g.attrib['id']: g for g in svg.findall(f'{NS}defs/{NS}linearGradient')}
groups = {}
for el in svg.findall(NS+'path'):
    region = GeometryCollection()
    for subpath in parse_path(el.attrib['d']).continuous_subpaths():
        points = []
        for segment in subpath:
            count = 1 if isinstance(segment, Line) else max(8, math.ceil(segment.length()*SCALE/.04))
            for i in range(count):
                p = segment.point(i/count)*SCALE
                points.append((p.real, p.imag))
        region = region.symmetric_difference(Polygon(points).buffer(0))
    gradient = gradients[el.attrib['fill'][5:-1]]
    key = (tuple(gradient.attrib[k] for k in ('x1','y1','x2','y2')),
           tuple((s.attrib['offset'],s.attrib['stop-color']) for s in gradient.findall(NS+'stop')))
    groups.setdefault(key, [gradient, []])[1].append(region)
assert len(groups) == 2  # Separate original gradients for stars and lettering.

parts = [[], [], []]
all_outlines = []
removed_slivers = 0
for gradient, regions in groups.values():
    outline = unary_union(regions)
    all_outlines.append(outline)
    p0 = np.array([float(gradient.attrib[k]) for k in ('x1', 'y1')])*SCALE
    vector = np.array([float(gradient.attrib[k]) for k in ('x2', 'y2')])*SCALE-p0
    length = np.linalg.norm(vector)
    direction = vector/length
    normal = np.array([-direction[1], direction[0]])
    stops = [(float(s.attrib['offset']), rgb(s.attrib['stop-color'])) for s in gradient.findall(NS+'stop')]
    positions, values = np.array([s[0] for s in stops]), np.array([s[1] for s in stops])
    corners = np.array([(x,y) for x in outline.bounds[::2] for y in outline.bounds[1::2]])
    projections = (corners-p0)@direction
    error = np.zeros(3)
    local = [[], [], []]
    for index in range(math.floor(projections.min()/PITCH), math.ceil(projections.max()/PITCH)):
        t = (index+.5)*PITCH/length
        target = np.array([np.interp(t, positions, values[:,c]) for c in range(3)])
        desired = weights(linear(target))+error
        color = int(np.argmax(desired))
        error = desired-np.eye(3)[color]
        a, b = p0+direction*index*PITCH, p0+direction*(index+1)*PITCH
        band = Polygon([a-normal*300,b-normal*300,b+normal*300,a+normal*300])
        local[color].append(outline.intersection(band))
    regions = [unary_union(items) for items in local]
    # Remove nozzle-sized islands created where a stripe clips a pointed contour.
    # Transfer them to the most adjacent color, preserving the source outline.
    for color in range(3):
        for poly in polygons(regions[color]):
            if poly.buffer(-.2).is_empty:
                neighbors = [(poly.buffer(.01).intersection(regions[other]).area, other)
                             for other in range(3) if other != color]
                area, other = max(neighbors)
                if area > 1e-9:
                    regions[color] = regions[color].difference(poly)
                    regions[other] = regions[other].union(poly)
                    removed_slivers += 1
    for color in range(3):
        parts[color].append(regions[color])

regions = [unary_union(items) for items in parts]
outline = unary_union(all_outlines)
coverage_error = outline.symmetric_difference(unary_union(regions)).area
overlap = sum(regions[i].intersection(regions[j]).area for i in range(3) for j in range(i))
assert coverage_error < 1e-6 and overlap < 1e-6
x0,y0,x1,y1 = outline.bounds
box = f'{x0-5} {y0-5} {x1-x0+10} {y1-y0+10}'
color_paths = ''.join(f'<path fill="{c}" fill-rule="evenodd" d="{svg_path(r)}"/>' for c,r in zip(COLORS,regions))
original = ''.join(ET.tostring(el,encoding='unicode') for el in svg)
defs = f'<defs><g id="original" transform="scale({SCALE})">{original}</g><g id="proposal">{color_paths}</g></defs>'
logo = f'<svg xmlns="http://www.w3.org/2000/svg" width="{x1-x0+10}mm" height="{y1-y0+10}mm" viewBox="{box}"><rect x="{x0-5}" y="{y0-5}" width="{x1-x0+10}" height="{y1-y0+10}" fill="white"/>{color_paths}</svg>'
(HERE/'proposal.svg').write_text(logo)


def view(ref, x, y, width, height, vb=box):
    return f'<svg x="{x}" y="{y}" width="{width}" height="{height}" viewBox="{vb}"><use href="#{ref}"/></svg>'


old_svg = ET.parse(HERE.parent/'line_gradient/proposal.svg').getroot()
old_paths = ''.join(ET.tostring(el,encoding='unicode') for el in old_svg if el.tag == NS+'path')
defs = defs.replace('</defs>', f'<g id="previous">{old_paths}</g></defs>')
page = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">',defs,
        '<rect width="1600" height="1200" fill="#F3F4F7"/><g font-family="DejaVu Sans,sans-serif" fill="#182237">',
        '<text x="48" y="62" font-size="32" font-weight="bold">myAI · Feinerer Übergang</text>',
        '<text x="48" y="101" font-size="20" fill="#526076">Gleiche Palette · gerade Farbbahnen · 40 % schmaler als bisher</text>']
for x, title, subtitle, ref in [(48,'Original','Unveränderte SVG','original'),
                               (560,'Bisher','Gerade Streifen · 0,80 mm Abstand','previous'),
                               (1072,'Neuer Vorschlag','Gerade Farbbahnen · 0,48 mm Breite','proposal')]:
    page += [f'<rect x="{x}" y="136" width="480" height="630" rx="16" fill="white"/>',
             f'<text x="{x+24}" y="180" font-size="26" font-weight="bold">{title}</text>',
             f'<text x="{x+24}" y="214" font-size="17" fill="#526076">{subtitle}</text>',
             view(ref,x+16,235,448,510)]
for x, ref, title in [(48,'previous','Bisher · Detail im Schriftzug'),(560,'proposal','Neu · identischer Ausschnitt')]:
    page += [f'<rect x="{x}" y="792" width="480" height="258" rx="16" fill="white"/>',
             f'<text x="{x+24}" y="829" font-size="20" font-weight="bold">{title}</text>',
             view(ref,x+24,852,432,180,f'{47*SCALE} {149*SCALE} {29*SCALE} {12*SCALE}')]
page += ['<text x="1096" y="825" font-size="20" font-weight="bold">Vier Farben im AMS</text>']
for i,(label,color) in enumerate(zip(('Weiss','Rot','Cyanblau','Blau'),['#FFFFFF',*COLORS])):
    y=852+i*44
    page += [f'<rect x="1096" y="{y}" width="25" height="25" rx="4" fill="{color}" stroke="#D6DAE2"/>',
             f'<text x="1134" y="{y+20}" font-size="19">{label}</text>']
page += ['<text x="48" y="1096" font-size="19">Für die 0,4-mm-Düse vorgesehen: 0,48-mm-Farbbahnen, ohne zusätzliche Wellen oder Kurzsegmente.</text>',
         '<text x="48" y="1133" font-size="18" fill="#526076">Ungefilterte 2D-Vorschau · Muster aus der Nähe sichtbar · Randdetails und Slicer-Druckbarkeit noch ungeprüft.</text>',
         '<text x="48" y="1168" font-size="18" fill="#526076">Keine neuen Druckdateien. Nominelle Bildschirmfarben, keine Vorhersage der Filament- oder Leuchtwirkung.</text>',
         '</g></svg>']
preview=''.join(page)
(HERE/'comparison.svg').write_text(preview)
cairosvg.svg2png(bytestring=preview.encode(),write_to=str(HERE/'comparison.png'))
report = {'status':'2D proposal only; awaiting visual feedback; no print files generated',
          'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'stripe_pitch_mm':PITCH, 'nominal_nozzle_mm':.4,
          'palette_hex':COLORS, 'palette_change':'Cyan replaces violet; target color, not measured filament',
          'logo_bounds_mm':list(outline.bounds), 'coverage_error_mm2':coverage_error,
          'color_overlap_mm2':overlap, 'small_clipped_pieces_reassigned':removed_slivers,
          'components_too_small_for_0_4_mm_disk':[
              {'color':color,'area_mm2':p.area} for color,region in zip(COLORS,regions)
              for p in polygons(region) if p.buffer(-.2).is_empty],
          'sliced':False,'physical_print_verified':False,
          'limitations':'0.48 mm is stripe spacing, not a guarantee of minimum width at every curved contour. Slicer coverage and small boundary details remain to check after visual acceptance.'}
(HERE/'preview_checks.json').write_text(json.dumps(report,indent=2)+'\n')
assert sum(p['area_mm2'] for p in report['components_too_small_for_0_4_mm_disk']) < .001
print(HERE/'comparison.png')
