"""Compare the whole CAD surface with nominal swept G-code extrusion footprints.

This is a conservative geometric screening, not a simulation of molten PLA.
Intentional white raster regions are excluded from the colored-surface metric.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

import cairosvg
import manifold3d as m
import numpy as np
import trimesh

from validate_raster_test import OUT, P, model_segments


def union(regions):
    return m.CrossSection.batch_boolean(list(regions), m.OpType.Add)


def footprint(a, b, width):
    """Inscribed capsule: straight segment plus round ends, 32 edges per circle.

    Maximum radial polygon error is width/2 * (1-cos(pi/32)); <0.0025 mm
    for widths <=1 mm. Arc flattening and G-code rounding add uncertainty.
    """
    theta = np.arctan2(*(b-a)[::-1])
    angles = np.linspace(-np.pi/2, np.pi/2, 17)+theta
    arc = np.stack((np.cos(angles), np.sin(angles)), axis=1)*width/2
    return np.vstack((b+arc, a-arc))


def svg_path(region, height, flip_y=True):
    return ' '.join('M'+' L'.join(f'{x:.5f},{height-y if flip_y else y:.5f}' for x,y in p)+' Z'
                    for p in region.to_polygons())


def analyze(file, folder, color_layer, output_prefix=None, *, output_root=None, palette=None):
    root = OUT if output_root is None else Path(output_root)
    palette = P['colors'] if palette is None else palette
    card = json.loads((root/folder/'geometry_validation.json').read_text())
    origin = np.array(card['print_offset_mm'][:2])
    width, height = card['size_mm'][:2]
    with zipfile.ZipFile(file) as archive:
        config = json.loads(archive.read('Metadata/project_settings.config'))
        raw = archive.read('Metadata/plate_1.gcode')
        assert hashlib.md5(raw).hexdigest() == archive.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    polygons = defaultdict(list)
    for z, slot, a, b, line_width in model_segments(raw.decode(), config):
        assert line_width <= 1., 'Footprint approximation must be refined for wider lines'
        polygons[z, slot].append(footprint(a-origin, b-origin, line_width))
    coverage = {key: union(m.CrossSection(items[i:i+512], m.FillRule.Positive)
                           for i in range(0,len(items),512)) for key,items in polygons.items()}
    meshes = {}
    for slot in range(1,5):
        mesh = trimesh.load_mesh(root/folder/'stl'/f'slot_{slot}.stl')
        assert mesh.is_watertight and mesh.is_winding_consistent
        meshes[slot] = m.Manifold(m.Mesh(np.float32(mesh.vertices), np.uint32(mesh.faces)))
    regions = {s: mesh.slice(color_layer-.1) for s,mesh in meshes.items()}
    all_color_paths = union(coverage.get((color_layer,s),m.CrossSection()) for s in range(1,5))
    ink = union(regions[s] for s in (2,3,4))
    unprinted = ink-all_color_paths
    # 0.03 mm allowance covers nominal path rounding and tiny boundary seams;
    # it is NOT a calibrated estimate of spreading or an increase in extrusion.
    allowance = .03
    unresolved = ink-all_color_paths.offset(allowance, circular_segments=32)
    by_slot, wrong_or_absent = {}, []
    for slot, region in regions.items():
        own = coverage.get((color_layer,slot),m.CrossSection())
        missing = region-own
        if slot != 1:
            wrong_or_absent.append(region-own.offset(allowance,circular_segments=32))
        by_slot[str(slot)] = {
            'intended_area_mm2': region.area(),
            'not_covered_by_own_color_mm2': missing.area(),
            'not_covered_by_any_color_mm2': (region-all_color_paths).area(),
            'own_color_missing_beyond_allowance_mm2': (region-own.offset(allowance,circular_segments=32)).area(),
        }
    backing = {}
    for z in (.2,.4,.6):
        if z == color_layer:
            continue
        intended = meshes[1].slice(z-.1)
        paths = coverage.get((z,1),m.CrossSection())
        remaining = intended-paths.offset(allowance,circular_segments=32)
        backing[str(z)] = {'area_mm2': intended.area(),
                            'nominal_uncovered_mm2': (intended-paths).area(),
                            'uncovered_beyond_allowance_mm2': remaining.area(),
                            'largest_unresolved_area_mm2': max((p.area() for p in remaining.decompose()),default=0.)}
    components = sorted((p for p in unresolved.decompose() if p.area() > 1e-7),
                        key=lambda p:p.area(),reverse=True)
    # Do not approve a connected nominal deficit >0.01 mm², or a distributed
    # deficit >=0.1% of the ink area after allowance. Physical printing remains
    # necessary even for a digital pass. Keep these limits fixed across trials.
    largest = components[0].area() if components else 0.
    own_deficit = union(wrong_or_absent)
    largest_own = max((p.area() for p in own_deficit.decompose()),default=0.)
    passed = (unresolved.area()/ink.area() <= .001 and largest <= .01
              and own_deficit.area()/ink.area() <= .001 and largest_own <= .01
              and all(b['uncovered_beyond_allowance_mm2']/b['area_mm2'] <= .001
                      and b['largest_unresolved_area_mm2'] <= .01 for b in backing.values()))
    report = {
        'schema_version': 1, 'print_file': str(Path(file).name),
        'print_sha256': hashlib.sha256(Path(file).read_bytes()).hexdigest(),
        'gcode_sha256': hashlib.sha256(raw).hexdigest(),
        'mesh_sha256_by_slot': {str(s):hashlib.sha256((root/folder/'stl'/f'slot_{s}.stl').read_bytes()).hexdigest() for s in range(1,5)},
        'method': 'CAD layer cross-sections minus union of nominal G-code width capsules with round end caps; arcs flattened to <=0.001 mm chord error',
        'color_layer_z_mm': color_layer, 'intentional_white_excluded_from_ink_metrics': True,
        'ink_area_mm2': ink.area(), 'nominal_unprinted_ink_area_mm2': unprinted.area(),
        'nominal_unprinted_ink_percent': 100*unprinted.area()/ink.area(),
        'geometric_allowance_mm': allowance,
        'unprinted_ink_beyond_allowance_mm2': unresolved.area(),
        'unprinted_ink_beyond_allowance_percent': 100*unresolved.area()/ink.area(),
        'largest_unresolved_area_mm2': largest,
        'own_ink_missing_beyond_allowance_mm2': own_deficit.area(),
        'largest_own_ink_deficit_mm2': largest_own,
        'largest_unresolved_regions': [{'area_mm2':p.area(),'bounds_mm':p.bounds()} for p in components[:12]],
        'slots': by_slot, 'white_backing_layers': backing,
        'acceptance': {'max_unresolved_ink_percent': .1, 'max_connected_unresolved_area_mm2': .01,
                       'apply_limits_to_own_ink_and_each_backing_layer_also': True},
        'digital_coverage_passed': passed, 'physical_print_verified': False,
        'limitations': 'Nominal planar footprint, not measured filament flow, surface sheen, bonding or optical opacity. Does not model the order/overlap of neighboring colors. Tiny CAD corner differences and molten material behavior remain uncertain.',
    }
    if output_prefix:
        flip_y = not card['front_is_bed_face']
        prefix = Path(output_prefix)
        prefix.parent.mkdir(parents=True,exist_ok=True)
        prefix.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
               f'<rect width="{width}" height="{height}" fill="white"/>']
        for slot in (2,3,4):
            svg.append(f'<path d="{svg_path(regions[slot],height,flip_y)}" fill="{palette[slot-1]["hex"]}" fill-rule="evenodd"/>')
        svg.append(f'<path d="{svg_path(unresolved,height,flip_y)}" fill="#00D37F" fill-rule="evenodd"/>')
        svg.append('</svg>')
        prefix.with_suffix('.svg').write_text('\n'.join(svg))
        cairosvg.svg2png(bytestring='\n'.join(svg).encode(),write_to=str(prefix.with_suffix('.png')),
                        output_width=1453,output_height=round(1453*height/width))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file',type=Path,default=OUT/'print/10_raster_original_test_P1S.3mf')
    parser.add_argument('--old',action='store_true')
    parser.add_argument('--output',type=Path,default=OUT/'raster_original_test/surface_coverage')
    parser.add_argument('--require-pass',action='store_true')
    args = parser.parse_args()
    result = analyze(args.file,'raster_test' if args.old else 'raster_original_test',
                     .2 if args.old else .6,args.output)
    print(json.dumps({k:result[k] for k in ('nominal_unprinted_ink_percent',
          'unprinted_ink_beyond_allowance_percent','largest_unresolved_area_mm2','digital_coverage_passed')},indent=2))
    if args.require_pass and not result['digital_coverage_passed']:
        raise SystemExit('FAIL: Raster coverage is insufficient; do not certify a closed color surface.')
