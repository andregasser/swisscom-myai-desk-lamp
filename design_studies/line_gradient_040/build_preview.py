"""Preview only: straight bands with a 0.40 mm minimum, no print exports."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
from shapely import Polygon, unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'cad'))
import line_gradient_regions as src

BASE = ROOT / 'design_studies/line_gradient_full'
spec = importlib.util.spec_from_file_location('full_preview', BASE / 'build_preview.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
MIN_WIDTH = .40


def regions_for(outline, origin, direction, runs):
    normal = np.array([-direction[1], direction[0]])
    parts = [[], [], []]
    for run in runs:
        a = origin + direction * run['start_mm']
        b = origin + direction * run['end_mm']
        band = Polygon([a-normal*300, b-normal*300, b+normal*300, a+normal*300])
        parts[run['color']].append(outline.intersection(band))
    return [unary_union(p) for p in parts]


def main():
    old_report = json.loads((BASE / 'preview_checks.json').read_text())
    base.MIN_WIDTH = MIN_WIDTH
    groups, outlines = [], []
    old_parts, new_parts = [[], [], []], [[], [], []]
    for index, (gradient, shapes) in enumerate(src.sources()):
        old = old_report['groups'][index]
        outline = unary_union([p for p in src.polygons(unary_union(shapes)) if p.area >= .001])
        outlines.append(outline)
        origin = np.array(old['gradient_origin_mm'])
        direction = np.array(old['gradient_direction'])
        end = np.array([float(gradient.attrib[k]) for k in ('x2', 'y2')]) * src.SCALE
        length = np.linalg.norm(end-origin)
        stops = gradient.findall(src.NS + 'stop')
        positions = [float(s.attrib['offset']) for s in stops]
        colors = np.array([src.rgb(s.attrib['stop-color']) for s in stops])
        lo, hi = old['runs'][0]['start_mm'], old['runs'][-1]['end_mm']
        grid = np.linspace(lo, hi, math.ceil((hi-lo)/base.SAMPLE_STEP)+1)
        weights = np.array([src.weights(src.linear(np.array([
            np.interp(x/length, positions, colors[:,i]) for i in range(3)]))) for x in grid])
        integral = np.vstack([np.zeros(3), np.cumsum(np.diff(grid)[:,None] *
                             (weights[:-1]+weights[1:])/2, axis=0)])
        runs, printed = base.continuous_runs(grid, integral, weights[0])
        assert all(r['width_mm'] >= MIN_WIDTH-1e-8 for r in runs)
        assert all(abs(a['end_mm']-b['start_mm']) < 1e-9 for a,b in zip(runs,runs[1:]))
        assert abs(runs[0]['start_mm']-lo) < 1e-9 and abs(runs[-1]['end_mm']-hi) < 1e-9
        before = regions_for(outline, origin, direction, old['runs'])
        after = regions_for(outline, origin, direction, runs)
        actual = np.zeros_like(integral)
        for run in runs:
            actual[:,run['color']] += np.clip(grid-run['start_mm'], 0, run['width_mm'])
        for c in range(3):
            old_parts[c].append(before[c])
            new_parts[c].append(after[c])
        groups.append({
            'name': old['name'], 'gradient_origin_mm': origin.tolist(),
            'gradient_direction': direction.tolist(), 'runs': runs,
            'previous_run_count': len(old['runs']),
            'integrated_target_width_mm': integral[-1].tolist(),
            'integrated_printed_width_mm': printed.tolist(),
            'maximum_cumulative_width_error_mm': float(np.max(abs(actual-integral))),
            'previous_color_area_mm2': [r.area for r in before],
            'color_area_mm2': [r.area for r in after],
        })
    before = [unary_union(p) for p in old_parts]
    after = [unary_union(p) for p in new_parts]
    outline = unary_union(outlines)
    coverage = outline.symmetric_difference(unary_union(after)).area
    overlap = sum(after[i].intersection(after[j]).area for i in range(3) for j in range(i))
    assert max(coverage, overlap) < 1e-7
    assert all(r.is_valid for r in after)
    x0,y0,x1,y1 = outline.bounds
    box = f'{x0-5} {y0-5} {x1-x0+10} {y1-y0+10}'
    proposal = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{x1-x0+10}mm" '
                f'height="{y1-y0+10}mm" viewBox="{box}"><rect x="{x0-5}" y="{y0-5}" '
                f'width="{x1-x0+10}" height="{y1-y0+10}" fill="white"/>{base.paths(after)}</svg>')
    (HERE / 'proposal.svg').write_text(proposal)
    report = {
        'status': 'Design preview only; gap closure unverified',
        'nominal_nozzle_mm': .4, 'minimum_designed_band_mm': MIN_WIDTH,
        'previous_minimum_designed_band_mm': .32, 'hysteresis_mm': base.HYSTERESIS,
        'source_sha256': hashlib.sha256(src.SOURCE.read_bytes()).hexdigest(),
        'previous_proposal_sha256': hashlib.sha256((BASE/'proposal.svg').read_bytes()).hexdigest(),
        'palette_hex': src.COLORS, 'groups': groups,
        'all_interfaces_straight': True, 'endpoint_modifications': False, 'contour_border_mm': 0,
        'planar_coverage_error_mm2': coverage, 'planar_color_overlap_mm2': overlap,
        'color_area_mm2': [r.area for r in after],
        'previous_color_area_mm2': [r.area for r in before],
        'color_area_change_percentage_points': [(a.area-b.area)/outline.area*100 for a,b in zip(after,before)],
        'reassigned_area_percent': sum(a.symmetric_difference(b).area for a,b in zip(after,before))/2/outline.area*100,
        'sliced': False, 'physical_print_verified': False,
        'limitations': '0.40 mm is an experimental design minimum, not a proven printable threshold. '
                      'Clipping at the unchanged logo contour still creates smaller tapered fragments. '
                      'Color area balance does not prove local or perceived color equality. '
                      'A wider minimum does not prove closure of contour or inter-stripe gaps.'
    }
    (HERE / 'preview_checks.json').write_text(json.dumps(report, indent=2)+'\n')
    page = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1420" viewBox="0 0 1440 1420">',
            f'<defs><g id="old">{base.paths(before)}</g><g id="new">{base.paths(after)}</g></defs>',
            '<rect width="1440" height="1420" fill="#edf1f5"/>',
            '<g font-family="DejaVu Sans,sans-serif" fill="#1d2940">',
            '<text x="36" y="48" font-size="29" font-weight="bold">myAI · Schmale Streifen etwas verbreitern</text>',
            '<text x="36" y="82" font-size="19">Gleiche Palette und ursprüngliche Verlaufsrichtungen · durchgehend gerade Farbgrenzen</text>']
    def view(ref, x, y, w, h, vb=box):
        return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}"><use href="#{ref}"/></svg>'
    for x,ref,title,subtitle in [(36,'old','Bisher · ab 0,32 mm','Farbaufteilung der Testkarte 13'),
                                 (738,'new','Vorschlag · ab 0,40 mm','Neu verteilt aus denselben Originalfarbanteilen')]:
        page += [f'<rect x="{x}" y="110" width="666" height="665" rx="14" fill="white"/>',
                 f'<text x="{x+22}" y="150" font-size="25" font-weight="bold">{title}</text>',
                 f'<text x="{x+22}" y="181" font-size="18">{subtitle}</text>',view(ref,x+20,197,626,558)]
    details = [('Kleiner Stern · Rotübergang',(52,21,33,17)),
               ('Schrift · Rotübergang',(49,148,35,17)),
               ('Grosser Stern · Blauübergang',(143,71,37,19))]
    for i,(title,(dx,dy,dw,dh)) in enumerate(details):
        x=36+i*468
        vb=f'{dx*src.SCALE} {dy*src.SCALE} {dw*src.SCALE} {dh*src.SCALE}'
        page += [f'<rect x="{x}" y="795" width="432" height="448" rx="14" fill="white"/>',
                 f'<text x="{x+16}" y="829" font-size="18" font-weight="bold">{title}</text>']
        for y,label,ref in [(860,'Bisher','old'),(1046,'Vorschlag','new')]:
            page += [f'<text x="{x+16}" y="{y}" font-size="16">{label}</text>',view(ref,x+16,y+12,400,150,vb)]
    page += ['<text x="36" y="1282" font-size="19">Änderung: Mindestbreite +0,08 mm. Breiten bleiben variabel; die Streifen können etwas deutlicher sichtbar sein.</text>',
             '<text x="36" y="1318" font-size="18">Reine Gestaltungsvorschau. Keine simulierten Druckbahnen; Lückenschluss mit der 0,4-mm-Düse noch ungeprüft.</text>',
             '<text x="36" y="1354" font-size="18">Beide Ansichten zeigen ideale Farbflächen ohne Druckfehler. Keine Simulation von Filament oder Hinterleuchtung.</text>',
             '</g></svg>']
    (HERE / 'comparison.svg').write_text(''.join(page))
    cairosvg.svg2png(url=str(HERE/'comparison.svg'), write_to=str(HERE/'comparison.png'))
    for file in HERE.glob('*.svg'):
        ET.parse(file)
    assert not any(p.suffix in ('.stl','.3mf','.gcode') for p in HERE.rglob('*'))
    print(json.dumps({k: report[k] for k in ('color_area_change_percentage_points','reassigned_area_percent',
                                           'planar_coverage_error_mm2','planar_color_overlap_mm2')}, indent=2))
    print([(g['name'], len(g['runs']), g['maximum_cumulative_width_error_mm']) for g in groups])


if __name__ == '__main__':
    main()
