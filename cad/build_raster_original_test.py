"""Full-size original-SVG raster test, printed white first and color face up."""
import json
import math

import manifold3d as m
import numpy as np

import build as mono
import build_multicolor as ams

OUT = ams.OUT
import hashlib
import raster_original as raster

PITCH, BORDER = .8, 5.
OFFSET = (40., 40., 0.)
TEST = OUT/'raster_original_test'


def combine(parts):
    return m.CrossSection.batch_boolean(parts, m.OpType.Add)


def main():
    for folder in ('geometry', 'raster_original_test/stl', 'preview'):
        (OUT/folder).mkdir(parents=True, exist_ok=True)
    sources = list(raster.sources())
    outline = combine([s[0] for s in sources])
    xmin, ymin, xmax, ymax = outline.bounds()
    shift = np.array([BORDER-xmin, BORDER-ymin])
    width, height = xmax-xmin+2*BORDER, ymax-ymin+2*BORDER
    pixels, probes = [[], [], [], []], []  # white, blue, violet, red
    junctions = [[], [], [], []]
    source_samples = []
    for region, p0, direction, stops in sources:
        x0, y0, x1, y1 = region.bounds()
        cells, clipped_cells, centers = [], [], []
        for row in range(math.floor(y0/PITCH), math.ceil(y1/PITCH)):
            for col in range(math.floor(x0/PITCH), math.ceil(x1/PITCH)):
                square = m.CrossSection.square((PITCH, PITCH)).translate((col*PITCH, row*PITCH))
                clipped = square ^ region
                if clipped.area() < 1e-8:
                    continue
                cells.append((row,col))
                clipped_cells.append(clipped)
                centers.append(((col+.5)*PITCH, (row+.5)*PITCH))
        targets = raster.sample_srgb(centers, p0, direction, stops)
        assignments, weights = raster.diffuse(cells, targets)
        source_samples.append({'stops': stops, 'sample_count': len(cells),
                               'mean_target_srgb': targets.mean(axis=0).tolist(),
                               'mean_palette_weights': weights.mean(axis=0).tolist()})
        for cell, clipped, center in zip(cells, clipped_cells, centers):
            index = assignments[cell]
            pixels[index].append(clipped)
            if abs(clipped.area()-PITCH**2) < 1e-6:
                probes.append({'xy_mm': (np.array(center)+shift).tolist(), 'slot': index+1})
        # Checkerboard pixels otherwise share a vertical edge with their diagonal
        # neighbor: a non-manifold mesh after vertex welding. Small round junctions
        # resolve that ambiguity without introducing another palette color.
        for row in range(math.floor(y0/PITCH), math.ceil(y1/PITCH)+1):
            for col in range(math.floor(x0/PITCH), math.ceil(x1/PITCH)+1):
                neighbors = [assignments.get((row+dy, col+dx), -1)
                             for dx, dy in ((-1,-1), (0,-1), (0,0), (-1,0))]
                a, b, c, d = neighbors
                chosen = a if a == c and a != b and a != d else b if b == d and b != a and b != c else None
                if chosen is not None and chosen >= 0:
                    joint = m.CrossSection.circle(.08, 16).translate((col*PITCH, row*PITCH)) ^ region
                    if joint.area() > 1e-8:
                        junctions[chosen].append(joint)
    colors = [combine(items) for items in pixels]
    for index, items in enumerate(junctions):
        joints = combine(items)
        for other in range(4):
            colors[other] = colors[other]+joints if other == index else colors[other]-joints
    # Contour-clipped raster islands smaller than a nozzle path are assigned to
    # an adjacent printable color. Do not cut holes in the original silhouette.
    scraps, removed_area = [], 0.
    for index, color in enumerate(colors):
        keep = []
        for piece in color.decompose():
            if piece.offset(-.20).area() > .002:
                keep.append(piece)
            else:
                scraps.append((index, piece))
                removed_area += piece.area()
        colors[index] = combine(keep)
    for original, piece in scraps:
        candidates = [i for i in range(4) if i != original]
        scores = [(piece.offset(.05) ^ colors[i]).area() for i in candidates]
        if max(scores) < 1e-8:
            scores = [(piece.offset(PITCH) ^ colors[i]).area() for i in candidates]
        chosen = candidates[int(np.argmax(scores))]
        colors[chosen] += piece
    assert (outline-combine(colors)).area() < 1e-5
    assert (combine(colors)-outline).area() < 1e-5
    outline = outline.translate(shift)
    # Compare against the unchanged production logo: no scaling or contour edits.
    production = ams.logo_regions()[3]
    px, py, _, _ = production.bounds()
    production = production.translate((BORDER-px, BORDER-py))
    assert (outline-production).area()+(production-outline).area() < 1e-5
    # Remove numerical collinear slivers before conversion to float32 STL vertices.
    colors = [c.translate(shift).simplify(1e-5) for c in colors]
    logo_areas = [c.area() for c in colors]
    # A reference strip keeps all three actual spools visible even when the
    # closest original-color approximation does not select a given filament.
    reference_fields = []
    for slot, x in zip((4,3,2), (width/2-7.5, width/2-1.5, width/2+4.5)):
        colors[slot-1] += m.CrossSection.square((3,3)).translate((x,height-4))
        reference_fields.append({'slot': slot, 'xy_mm': [x+1.5, 2.5], 'size_mm': 3})
    inks = [colors[i].extrude(ams.CD) for i in (1, 2, 3)]
    envelope = mono.box(width, height, ams.TH)
    white = envelope-mono.union(inks)
    parts = [white, *inks]
    joined = mono.union(parts)
    assert (envelope-joined).volume()+(joined-envelope).volume() < .001
    assert len(joined.decompose()) == 1
    components = []
    for i, part in enumerate(parts):
        mesh = mono.mesh(part)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
        components.append(len(mesh.split()))
        for other in parts[i+1:]:
            assert (part ^ other).volume() < .001
    assert components[0] == 1
    for probe in probes:
        x, y = probe['xy_mm']
        sample = mono.box(.1, .1, ams.CD, (x-.05, y-.05, 0))
        assert abs((parts[probe['slot']-1] ^ sample).volume()-.01*ams.CD) < 1e-6
    # Rotate around X, so the upward-facing logo is readable without mirroring.
    parts = [part.rotate((180,0,0)).translate((0,height,ams.TH)) for part in parts]
    for i, part in enumerate(parts, 1):
        obj = mono.mesh(part)
        assert obj.is_watertight and obj.is_winding_consistent
        obj.export(TEST/'stl'/f'slot_{i}.stl')
    for probe in probes:
        probe['xy_mm'][1] = height-probe['xy_mm'][1]
    ams.multipart_3mf(parts, OUT/'geometry/10_raster_original_test.3mf',
                      'Original-SVG Rasterprobe: Weiss zuerst, Logo oben', OFFSET)
    # Vector preview of the exact final color regions, before print rotation.
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">',
           f'<rect width="{width}" height="{height}" fill="white"/>']
    for region, color in zip(colors, ams.P['colors']):
        path = ' '.join('M'+' L'.join(f'{x:.6f},{y:.6f}' for x,y in p)+' Z' for p in region.to_polygons())
        svg.append(f'<path d="{path}" fill="{color["hex"]}" fill-rule="evenodd"/>')
    (TEST/'raster.svg').write_text('\n'.join([*svg, '</svg>']))
    report = {'physical_print_verified': False, 'size_mm': [width, height, ams.TH],
              'logo_size_mm': [xmax-xmin, ymax-ymin], 'production_logo_scale': 1.,
              'source_contour_preserved': True, 'raster_pitch_mm': PITCH,
              'source_sha256': hashlib.sha256((mono.ROOT/'assets/logos'/ams.P['logo_source']).read_bytes()).hexdigest(),
              'gradient_sources': source_samples, 'method': 'original sRGB stops, linear-RGB convex palette projection, serpentine Floyd-Steinberg',
              'logo_area_mm2_by_slot': logo_areas, 'reference_fields': reference_fields,
              'corner_junction_radius_mm': .08,
              'color_depth_mm': ams.CD, 'white_backing_mm': ams.TH-ams.CD,
              'front_is_bed_face': False, 'color_layer_z_mm': .6, 'print_offset_mm': OFFSET,
              'one_connected_card': True, 'watertight_slot_components': components,
              'material_intersections_mm3': 0, 'reassigned_small_islands': len(scraps),
              'reassigned_area_mm2': removed_area, 'full_cell_probes': probes}
    (TEST/'geometry_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'Validated raster card {width:.2f} x {height:.2f} x {ams.TH} mm; '
          f'{len(probes)} full cells; reassigned {len(scraps)} tiny islands ({removed_area:.2f} mm2)')


if __name__ == '__main__':
    main()
