"""Full-size ordered-dither logo, one 0.2 mm color layer on 0.4 mm white."""
import json
import math
import xml.etree.ElementTree as ET

import manifold3d as m
import numpy as np
from svgpathtools import Line, parse_path

import build as mono
import build_multicolor as ams

OUT = ams.OUT
PITCH, BORDER = .8, 5.
STOPS = (0., .36, .80)
OFFSET = (40., 40., 0.)
BAYER = np.array([[0, 2], [3, 1]])
for _ in range(2):
    BAYER = np.block([[4*BAYER, 4*BAYER+2], [4*BAYER+3, 4*BAYER+1]])
THRESHOLDS = (BAYER + .5) / BAYER.size


def combine(parts):
    return m.CrossSection.batch_boolean(parts, m.OpType.Add)


def color_index(t, column, row):
    if t <= STOPS[0]:
        return 0
    if t >= STOPS[-1]:
        return 2
    low = 0 if t < STOPS[1] else 1
    fraction = (t-STOPS[low]) / (STOPS[low+1]-STOPS[low])
    return low + int(fraction > THRESHOLDS[row % 8, column % 8])


def source_regions():
    """Use the production contour sampling, but keep each SVG gradient vector."""
    svg = ET.parse(mono.ROOT/'assets/logos'/ams.P['logo_source']).getroot()
    ns = '{http://www.w3.org/2000/svg}'
    gradients = {g.attrib['id']: g for g in svg.findall(f'{ns}defs/{ns}linearGradient')}
    scale = mono.P['logo_canvas_mm'] / 216
    for el in svg.findall(ns+'path'):
        contours = []
        for path in parse_path(el.attrib['d']).continuous_subpaths():
            points = []
            for segment in path:
                count = 1 if isinstance(segment, Line) else max(4, math.ceil(segment.length()*scale/.2))
                for i in range(count):
                    pt = segment.point(i/count)
                    points.append((pt.real*scale, pt.imag*scale))
            contours.append(points)
        region = m.CrossSection(contours, m.FillRule.EvenOdd)
        if region.area() < .02:
            continue
        gradient = gradients[el.attrib['fill'][5:-1]]
        assert gradient.attrib['gradientUnits'] == 'userSpaceOnUse'
        assert 'gradientTransform' not in gradient.attrib
        vector = np.array([float(gradient.attrib[k]) for k in ('x1', 'y1', 'x2', 'y2')])*scale
        yield region, vector[:2], vector[2:]-vector[:2]


def main():
    for folder in ('geometry', 'raster_test/stl', 'preview'):
        (OUT/folder).mkdir(parents=True, exist_ok=True)
    sources = list(source_regions())
    outline = combine([s[0] for s in sources])
    xmin, ymin, xmax, ymax = outline.bounds()
    shift = np.array([BORDER-xmin, BORDER-ymin])
    width, height = xmax-xmin+2*BORDER, ymax-ymin+2*BORDER
    pixels, probes = [[], [], []], []  # red, violet, blue
    junctions = [[], [], []]
    for region, p0, direction in sources:
        x0, y0, x1, y1 = region.bounds()
        for row in range(math.floor(y0/PITCH), math.ceil(y1/PITCH)):
            for col in range(math.floor(x0/PITCH), math.ceil(x1/PITCH)):
                center = np.array([(col+.5)*PITCH, (row+.5)*PITCH])
                t = np.dot(center-p0, direction)/np.dot(direction, direction)
                index = color_index(t, col, row)
                square = m.CrossSection.square((PITCH, PITCH)).translate((col*PITCH, row*PITCH))
                clipped = square ^ region
                if clipped.area() < 1e-8:
                    continue
                pixels[index].append(clipped)
                # Entire cells: verify the intended ink survives slicing at its center.
                if abs(clipped.area()-PITCH**2) < 1e-6:
                    probes.append({'xy_mm': (center+shift).tolist(), 'slot': (4, 3, 2)[index]})
        # Checkerboard pixels otherwise share a vertical edge with their diagonal
        # neighbor: a non-manifold mesh after vertex welding. Small round junctions
        # resolve that ambiguity without introducing another palette color.
        for row in range(math.floor(y0/PITCH), math.ceil(y1/PITCH)+1):
            for col in range(math.floor(x0/PITCH), math.ceil(x1/PITCH)+1):
                neighbors = []
                for dx, dy in ((-1,-1), (0,-1), (0,0), (-1,0)):
                    center = np.array([(col+dx+.5)*PITCH, (row+dy+.5)*PITCH])
                    t = np.dot(center-p0, direction)/np.dot(direction, direction)
                    neighbors.append(color_index(t, col+dx, row+dy))
                a, b, c, d = neighbors
                chosen = a if a == c and a != b and a != d else b if b == d and b != a and b != c else None
                if chosen is not None:
                    joint = m.CrossSection.circle(.08, 16).translate((col*PITCH, row*PITCH)) ^ region
                    if joint.area() > 1e-8:
                        junctions[chosen].append(joint)
    colors = [combine(items) for items in pixels]
    for index, items in enumerate(junctions):
        joints = combine(items)
        for other in range(3):
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
        candidates = [i for i in range(3) if i != original]
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
    inks = [colors[i].extrude(ams.CD) for i in (2, 1, 0)]
    envelope = mono.box(width, height, ams.TH)
    white = envelope-outline.extrude(ams.CD)
    parts = [white, *inks]
    joined = mono.union(parts)
    assert (envelope-joined).volume()+(joined-envelope).volume() < .001
    assert len(joined.decompose()) == 1
    components = []
    for i, part in enumerate(parts):
        mesh = mono.mesh(part)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
        mesh.export(OUT/'raster_test/stl'/f'slot_{i+1}.stl')
        components.append(len(mesh.split()))
        for other in parts[i+1:]:
            assert (part ^ other).volume() < .001
    assert components[0] == 1
    for probe in probes:
        x, y = probe['xy_mm']
        sample = mono.box(.1, .1, ams.CD, (x-.05, y-.05, 0))
        assert abs((parts[probe['slot']-1] ^ sample).volume()-.01*ams.CD) < 1e-6
    ams.multipart_3mf(parts, OUT/'geometry/09_raster_test.3mf',
                      'Rasterprobe: myAI Originalgroesse, 0.8 mm Raster', OFFSET)
    report = {'physical_print_verified': False, 'size_mm': [width, height, ams.TH],
              'logo_size_mm': [xmax-xmin, ymax-ymin], 'production_logo_scale': 1.,
              'source_contour_preserved': True, 'raster_pitch_mm': PITCH,
              'gradient_stops': STOPS, 'bayer_size': 8,
              'corner_junction_radius_mm': .08,
              'color_depth_mm': ams.CD, 'white_backing_mm': ams.TH-ams.CD,
              'front_is_bed_face': True, 'print_offset_mm': OFFSET,
              'one_connected_card': True, 'watertight_slot_components': components,
              'material_intersections_mm3': 0, 'reassigned_small_islands': len(scraps),
              'reassigned_area_mm2': removed_area, 'full_cell_probes': probes}
    (OUT/'raster_test/geometry_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'Validated raster card {width:.2f} x {height:.2f} x {ams.TH} mm; '
          f'{len(probes)} full cells; reassigned {len(scraps)} tiny islands ({removed_area:.2f} mm2)')


if __name__ == '__main__':
    main()
