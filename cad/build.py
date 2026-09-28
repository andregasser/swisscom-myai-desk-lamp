#!/usr/bin/env python3
"""Parametric cube lamp; dimensions in mm. Run with the project venv Python."""
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET
import zipfile

import manifold3d as m
import numpy as np
from svgpathtools import parse_path, Line
import trimesh

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / 'cad/parameters.json').read_text())
OUT = ROOT / 'output'
S = P['outside_mm']
B = P['base_mm']
L = P['lid_edge_mm']
H = S - B - L
W = P['diffuser_mm']
F = P['frame_mm']
C = P['fit_clearance_per_side_mm']
EPS = 0.02


def box(x, y, z, at=(0, 0, 0)):
    return m.Manifold.cube((x, y, z)).translate(at)


def union(parts):
    return m.Manifold.batch_boolean(parts, m.OpType.Add)


def square_taper(side0, side1, height, z):
    cs = m.CrossSection.square((side0, side0), center=True)
    return m.Manifold.extrude(cs, height, scale_top=(side1 / side0,) * 2).translate((S / 2, S / 2, z))


def cavity_loft(levels):
    vertices, faces = [], []
    for z, side in levels:
        low, high = (S - side) / 2, (S + side) / 2
        vertices.extend([(low, low, z), (high, low, z), (high, high, z), (low, high, z)])
    faces.extend([(0, 2, 1), (0, 3, 2)])
    for row in range(len(levels) - 1):
        for j in range(4):
            a, b = row * 4 + j, row * 4 + (j + 1) % 4
            faces.extend([(a, b, b + 4), (a, b + 4, a + 4)])
    top = 4 * (len(levels) - 1)
    faces.extend([(top, top + 1, top + 2), (top, top + 2, top + 3)])
    return m.Manifold(m.Mesh(np.asarray(vertices, dtype=np.float32), np.asarray(faces, dtype=np.uint32)))


def front_prism(points, depth, y=0):
    """Polygon coordinates are (x,z), extrude inward along +y."""
    cs = m.CrossSection([points], m.FillRule.EvenOdd)
    return m.Manifold.extrude(cs, depth).transform(((1, 0, 0, 0), (0, 0, 1, y), (0, 1, 0, 0)))


def around(part, quarter):
    return part.translate((-S / 2, -S / 2, 0)).rotate((0, 0, 90 * quarter)).translate((S / 2, S / 2, 0))


def logo_section():
    root = ET.parse(ROOT / 'assets/logos/Mode=Light, Type=Stacked.svg').getroot()
    parts = []
    scale = P['logo_canvas_mm'] / 216
    for el in root.findall('{http://www.w3.org/2000/svg}path'):
        contours = []
        for path in parse_path(el.attrib['d']).continuous_subpaths():
            points = []
            for seg in path:
                steps = 1 if isinstance(seg, Line) else max(4, math.ceil(seg.length() * scale / 0.20))
                for i in range(steps):
                    p = seg.point(i / steps)
                    points.append((p.real * scale, (216 - p.imag) * scale))
            contours.append(points)
        cs = m.CrossSection(contours, m.FillRule.EvenOdd)
        # The source contains a separate ~0.001 mm² triangle touching the A.
        # It is far below nozzle resolution and can create point contacts.
        if cs.area() >= .02:
            parts.append(cs)
    return m.CrossSection.batch_boolean(parts, m.OpType.Add)


LOGO = logo_section()


def front_logo():
    xmin, zmin, xmax, zmax = LOGO.bounds()
    relief = P['logo_relief_mm']
    offset_x = S / 2 - (xmin + xmax) / 2
    # Center the projected extra material on the assembled 150 mm face.
    # Beyond the 0.8 mm wall, extrusion depths are EPS .. relief + EPS.
    offset_z = S / 2 - B - (zmin + zmax) / 2 - relief / 2 - EPS
    return m.Manifold.extrude(LOGO, relief + EPS).transform((
        (1, 0, 0, offset_x), (0, 0, 1, W - EPS), (0, 1, 1, offset_z)))


def body():
    transition = F - W
    cavity = cavity_loft([(-1, S - 2 * F), (5, S - 2 * F),
                          (5 + transition, S - 2 * W),
                          (H - 6 - transition, S - 2 * W),
                          (H - 6, S - 2 * F), (H + 1, S - 2 * F)])
    shell = box(S, S, H) - cavity
    corner = P['corner_mm']
    parts = [shell]
    for x in (0, S - corner):
        for y in (0, S - corner):
            parts.append(box(corner, corner, H, (x, y, 0)))
    # A 45-degree upward shear makes the inward relief grow by at most one
    # layer height per layer; there is no sudden 0.8 mm horizontal ledge.
    logo = front_logo()
    parts.extend(around(logo, q) for q in range(4))
    shell = union(parts)
    vents = []
    for x in (24, 42, 108, 126):
        diamond = front_prism([(x - 2, 3.5), (x, 1.5), (x + 2, 3.5), (x, 5.5)], F + 2, -1)
        vents.extend(around(diamond, q) for q in range(4))
    # The rear cable opening is open at the bottom. Lay the cable in before
    # seating the body; neither USB plug nor inline switch needs threading.
    cx = S / 2
    half = P['cable_slot_width_mm'] / 2
    cable = front_prism([(cx - half, -1), (cx + half, -1),
                         (cx + half, 4), (cx, 4 + half), (cx - half, 4)], F + 2, -1)
    vents.append(around(cable, 2))
    # Small rear access notch under the lid, outside the logo.
    vents.append(box(16, F + 2, 1.6, (cx - 8, S - F - 1, H - 1.6)))
    return shell - union(vents)


def locators(z, cable_gap=False):
    """Four separate tapered guide rails avoid interference with corner posts."""
    height = P['locator_height_mm']
    inset = F + C
    length = S - 30
    # Lead-in chamfer: 0.6 mm on the final 0.6 mm of the outer face.
    p = [(inset, z - EPS), (inset + 2, z - EPS),
         (inset + 2, z + height), (inset + .6, z + height),
         (inset, z + height - .6)]
    rail = front_prism(p, length, 15)
    guides = union([around(rail, q) for q in range(4)])
    if cable_gap:
        guides -= box(8, 15, height + 2, (S / 2 - 4, S - 15, z - 1))
    return guides


def led_ring(z=0):
    inner = P['led_pocket_diameter_mm'] / 2
    outer = inner + P['led_ring_wall_mm']
    ring = m.Manifold.cylinder(P['led_ring_height_mm'], outer, outer, 192)
    ring -= m.Manifold.cylinder(P['led_ring_height_mm'] + 2, inner, inner, 192).translate((0, 0, -1))
    ring -= box(8, outer + 2, 8, (-4, 0, -1))
    return ring.translate((S / 2, S / 2, z))


def base():
    return union([box(S, S, B), locators(B, cable_gap=True), led_ring(B - EPS)])


def lid():
    # Print exterior down: flat diffuser first, rim and guide rails upward.
    rim = box(S, S, L) - box(S - 16, S - 16, L + 2, (8, 8, -1))
    cap = union([box(S, S, W), rim, locators(L)])
    slots = [around(box(28, 2, L + 2, (S / 2 - 14, 10, -1)), q) for q in range(4)]
    return cap - union(slots)


SEGMENTS = {
    '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd',
    '4': 'fgbc', '5': 'afgcd', '6': 'afgecd', '8': 'abcdefg',
}


def label(text, x, y, z):
    pieces = []
    for ch in text:
        if ch == '.':
            pieces.append(box(.65, .65, .4, (x, y, z)))
            x += 1.2
            continue
        segments = {
            'a': (0, 4, 2.5, .55), 'g': (0, 2, 2.5, .55), 'd': (0, 0, 2.5, .55),
            'f': (0, 2, .55, 2.5), 'e': (0, 0, .55, 2.5),
            'b': (1.95, 2, .55, 2.5), 'c': (1.95, 0, .55, 2.5),
        }
        for key in SEGMENTS[ch]:
            dx, dy, sx, sy = segments[key]
            pieces.append(box(sx, sy, .4, (x + dx, y + dy, z)))
        x += 3.6
    return union(pieces)


def coupon(thickness):
    rim = box(40, 40, 2) - box(34, 34, 4, (3, 3, -1))
    head = box(40, 10, 2, (0, 40, 0))
    logo = m.Manifold.extrude(LOGO.scale((26 / P['logo_canvas_mm'],) * 2),
                              P['logo_relief_mm'] + EPS).translate((7, 7, thickness - EPS))
    return union([box(40, 40, thickness), rim, head, logo, label(f'{thickness:.1f}', 16, 42.5, 2 - EPS)])


def led_fit():
    flange = m.Manifold.cylinder(.8, 35, 35, 192) - m.Manifold.cylinder(2, 27, 27, 192).translate((0, 0, -.5))
    flange -= box(8, 38, 3, (-4, 0, -.5))
    return union([flange.translate((S / 2, S / 2, 0)), led_ring(.8 - EPS)]).translate((35 - S / 2, 35 - S / 2, 0))


def joint_fit():
    # Cropped original parts preserve full-width opposed guide clearance.
    # Test this short ring strip vertically on the matching base strip.
    crop = box(S + 2, 12, 8, (-1, S / 2 - 6, 0))
    female = body() ^ crop
    female = female.translate((0, -(S / 2 - 6), 0))
    male_crop = box(S + 2, 12, B + 5, (-1, S / 2 - 6, 0))
    male = (base() ^ male_crop).translate((0, -(S / 2 - 6), 0))
    # Female needs its two ends joined; the tie sits above the mating rails.
    female += box(S, 12, 1, (0, 0, 7))
    # Print the joining strip on the bed; otherwise it would bridge 144 mm.
    female = female.rotate((180, 0, 0)).translate((0, 12, 8))
    return female, male


def mesh(solid):
    assert solid.status() == m.Error.NoError, solid.status()
    raw = solid.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(raw.vert_properties)[:, :3], faces=raw.tri_verts, process=True)


def core_3mf(items, target):
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('', ns)
    def tag(t): return '{' + ns + '}' + t
    root = ET.Element(tag('model'), {'unit': 'millimeter', '{http://www.w3.org/XML/1998/namespace}lang': 'en-US'})
    ET.SubElement(root, tag('metadata'), {'name': 'Title'}).text = 'myAI Cube 150 — print-oriented geometry'
    resources = ET.SubElement(root, tag('resources'))
    build = ET.SubElement(root, tag('build'))
    for i, (name, obj, offset) in enumerate(items, 1):
        objel = ET.SubElement(resources, tag('object'), {'id': str(i), 'type': 'model', 'name': name})
        me = ET.SubElement(objel, tag('mesh'))
        verts = ET.SubElement(me, tag('vertices'))
        for v in obj.vertices:
            ET.SubElement(verts, tag('vertex'), dict(zip(('x', 'y', 'z'), (f'{c:.6f}' for c in v))))
        faces = ET.SubElement(me, tag('triangles'))
        for f in obj.faces:
            ET.SubElement(faces, tag('triangle'), dict(zip(('v1', 'v2', 'v3'), map(str, f))))
        x, y, z = offset
        ET.SubElement(build, tag('item'), {'objectid': str(i), 'transform': f'1 0 0 0 1 0 0 0 1 {x} {y} {z}'})
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        archive.writestr('3D/3dmodel.model', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def main():
    for directory in ('stl', '3mf', 'preview'):
        (OUT / directory).mkdir(parents=True, exist_ok=True)
    solids = {'02_body': body(), '03_base': base(), '04_lid': lid(), '01e_led_fit': led_fit()}
    for letter, value in zip('abcd', (.6, .8, 1., 1.2)):
        solids[f'01{letter}_light_{value:.1f}mm'] = coupon(value)
    female, male = joint_fit()
    solids['01f_joint_socket'] = female
    solids['01g_joint_rail'] = male
    meshes, report = {}, {}
    for name, solid in solids.items():
        obj = mesh(solid)
        assert obj.is_watertight and obj.is_winding_consistent and obj.volume > 0, name
        assert len(obj.split()) == 1, (name, 'disconnected parts')
        assert np.all(obj.extents <= 256) and abs(obj.bounds[0, 2]) < .001, name
        obj.export(OUT / 'stl' / (name + '.stl'))
        meshes[name] = obj
        report[name] = {'bounds_mm': obj.bounds.tolist(), 'size_mm': obj.extents.tolist(),
                        'watertight': bool(obj.is_watertight), 'connected_solids': 1,
                        'triangles': len(obj.faces), 'solid_volume_cm3': round(obj.volume / 1000, 3)}
        print(name, report[name], flush=True)
    for name in ('02_body', '03_base', '04_lid'):
        core_3mf([(name, meshes[name], (53, 53, 0))], OUT / '3mf' / (name + '_geometry.3mf'))
    items = []
    for i, letter in enumerate('abcd'):
        name = next(n for n in meshes if n.startswith('01' + letter))
        # Reserve the P1S front-left exclusion zone, including the 4 mm brim.
        items.append((name, meshes[name], (26 + 46 * i, 32, 0)))
    items += [('01e_led_fit', meshes['01e_led_fit'], (20, 90, 0)),
              ('01f_joint_socket', meshes['01f_joint_socket'], (20, 180, 0)),
              ('01g_joint_rail', meshes['01g_joint_rail'], (20, 204, 0))]
    core_3mf(items, OUT / '3mf/01_tests_geometry.3mf')
    # Assembly contacts are planar, with no intersecting material.
    assembled_body = solids['02_body'].translate((0, 0, B))
    assembled_lid = solids['04_lid'].rotate((180, 0, 0)).translate((0, S, S))
    assembly = [solids['03_base'], assembled_body, assembled_lid]
    for i in range(3):
        for j in range(i + 1, 3):
            overlap = (assembly[i] ^ assembly[j]).volume()
            assert overlap < .001, ('assembly collision', i, j, overlap)
    nominal_led = m.Manifold.cylinder(18, P['led_nominal_diameter_mm'] / 2,
                                      P['led_nominal_diameter_mm'] / 2, 192).translate((S / 2, S / 2, B))
    assert (nominal_led ^ union(assembly)).volume() < .001
    report['assembly'] = {'size_mm': list(union(assembly).bounding_box()[3:]),
                          'pairwise_intersection_mm3': 0,
                          'nominal_guide_clearance_per_side_mm': C,
                          'nominal_led_cylinder_collision_free': True,
                          'physical_fit_tested': False}
    visible_relief = front_logo() ^ box(S, F, H, (0, W, 0))
    bounds = np.asarray(visible_relief.bounding_box()).reshape(2, 3)
    center = bounds.mean(axis=0)
    assert np.allclose([center[0], center[2] + B], [S / 2, S / 2], atol=.001)
    report['logo'] = {'centering': 'projected contour bounds, including relief slope',
                      'assembled_face_center_xz_mm': [float(center[0]), float(center[2] + B)],
                      'projected_size_xz_mm': (bounds[1] - bounds[0])[[0, 2]].tolist(),
                      'identical_on_all_four_sides': True}
    # Keep assembly out of the print folder to avoid accidental printing of it.
    scene = trimesh.Scene()
    for name, solid in zip(('base', 'body', 'lid'), assembly):
        scene.add_geometry(mesh(solid), node_name=name, geom_name=name)
    scene.export(OUT / 'preview/assembly.glb')
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
