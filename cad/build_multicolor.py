#!/usr/bin/env python3
"""v3.2: red/violet/blue logo inlays, including the wordmark gradient."""
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import manifold3d as m
import numpy as np
from svgpathtools import parse_path, Line
import trimesh
import build as mono

ROOT = mono.ROOT
P = json.loads((ROOT / 'cad/multicolor_parameters.json').read_text())
OUT = ROOT / 'output/multicolor_v3'
PW, PH = P['panel_width_mm'], P['panel_height_mm']
TH, CD = P['panel_thickness_mm'], P['color_depth_mm']
box, union, around, mesh = mono.box, mono.union, mono.around, mono.mesh
FOOT_CENTERS = [(x, y) for x in (18, 132) for y in (18, 132)]


def feet():
    pad = m.Manifold.cylinder(P['foot_height_mm'], P['foot_diameter_mm']/2,
                             P['foot_diameter_mm']/2, 64)
    peg = m.Manifold.cylinder(P['foot_peg_height_mm'] + .02, P['foot_peg_diameter_mm']/2,
                             P['foot_peg_diameter_mm']/2, 48).translate((0, 0, P['foot_height_mm'] - .02))
    return union([(pad + peg).translate((x, y, 0)) for x, y in FOOT_CENTERS])


def inlet_slots():
    return union([around(box(P['inlet_slot_length_mm'], P['inlet_slot_width_mm'], 7,
                            (x, 16, -1)), q) for x in (35, 87) for q in range(4)])


def base():
    # Assemble at Z=2: a 1 mm outer flange retains the original frame seat
    # at Z=3. The central plate is reinforced to 3 mm, with LED seat at Z=5.
    bottom = P['foot_height_mm']
    assert 0 < bottom < 3
    plate = union([box(150, 150, 3-bottom, (0, 0, bottom)),
                   box(134, 134, 2.02, (8, 8, 2.98)),
                   mono.locators(3, cable_gap=True), mono.led_ring(4.98)])
    sockets = union([m.Manifold.cylinder(P['foot_socket_depth_mm']+.02,
                        P['foot_socket_diameter_mm']/2, P['foot_socket_diameter_mm']/2,
                        48).translate((x, y, bottom-.02)) for x, y in FOOT_CENTERS])
    # Sockets open on the bed; only their 4.4 mm roofs require bridging.
    return (plate - inlet_slots() - sockets).translate((0, 0, -bottom))


def logo_regions():
    source = ET.parse(ROOT / 'assets/logos' / P['logo_source']).getroot()
    ns = '{http://www.w3.org/2000/svg}'
    gradients = {g.attrib['id']: g for g in source.findall(f'{ns}defs/{ns}linearGradient')}
    scale = mono.P['logo_canvas_mm'] / 216
    sections = []
    red_parts, violet_parts, blue_parts = [], [], []
    edge_red, edge_violet = P['gradient_band_edges']
    assert 0 < edge_red < edge_violet < 1
    for el in source.findall('{http://www.w3.org/2000/svg}path'):
        contours = []
        for path in parse_path(el.attrib['d']).continuous_subpaths():
            points = []
            for segment in path:
                count = 1 if isinstance(segment, Line) else max(4, math.ceil(segment.length() * scale / .2))
                for i in range(count):
                    pt = segment.point(i / count)
                    points.append((pt.real * scale, pt.imag * scale))
            contours.append(points)
        section = m.CrossSection(contours, m.FillRule.EvenOdd)
        if section.area() < .02:
            continue
        sections.append(section)
        fill = el.attrib['fill']
        assert fill.startswith('url(#') and fill.endswith(')'), 'Every logo path must use its SVG gradient'
        gradient = gradients[fill[5:-1]]
        assert gradient.attrib['gradientUnits'] == 'userSpaceOnUse'
        assert 'gradientTransform' not in gradient.attrib
        # Preserve each source path's gradient vector. The wordmark and stars
        # have separate coordinate systems. Re-map their colors to the user's
        # requested red -> violet -> blue three-band palette; no cyan return.
        p0 = np.array([float(gradient.attrib[k]) for k in ('x1', 'y1')]) * scale
        p1 = np.array([float(gradient.attrib[k]) for k in ('x2', 'y2')]) * scale
        direction = p1 - p0
        perpendicular = np.array([-direction[1], direction[0]])
        perpendicular *= 500 / np.linalg.norm(perpendicular)
        def band(low, high):
            a, b = p0 + low * direction, p0 + high * direction
            return m.CrossSection([[a-perpendicular, b-perpendicular, b+perpendicular, a+perpendicular]], m.FillRule.EvenOdd)
        red = section ^ band(-5, edge_red)
        violet = section ^ band(edge_red, edge_violet)
        blue = section ^ band(edge_violet, 5)
        red_parts.append(red)
        violet_parts.append(violet)
        blue_parts.append(blue)
    combine = lambda parts: m.CrossSection.batch_boolean(parts, m.OpType.Add)
    blue, violet, red = map(combine, (blue_parts, violet_parts, red_parts))
    unsplit_outline = combine(sections)
    xmin, ymin, xmax, ymax = unsplit_outline.bounds()
    # Local print Y maps downwards on the assembled face; the artwork is
    # correctly readable from the outward (bed-contact) face after assembly.
    target_x = 75 - P['panel_left_mm']
    target_y = P['panel_bottom_mm'] + PH - 75
    delta = (target_x - (xmin + xmax) / 2, target_y - (ymin + ymax) / 2)
    return [s.translate(delta) for s in (blue, violet, red, unsplit_outline)]


def panel_parts():
    regions = logo_regions()
    inks = [m.Manifold.extrude(region, CD) for region in regions[:3]]
    white = box(PW, PH, TH) - m.Manifold.extrude(regions[3], CD)
    return [white, *inks]


def assemble_panel(part):
    return part.transform(((1, 0, 0, P['panel_left_mm']),
                           (0, 0, 1, P['panel_front_depth_mm']),
                           (0, -1, 0, P['panel_bottom_mm'] + PH)))


def frame():
    height = mono.H
    shape = box(150, 150, height) - box(144, 144, height + 2, (3, 3, -1))
    # Open at the top: no unsupported 128 mm lintel. The lid carries the
    # removable top bezel, so the panels can slide down from above.
    cut = box(128, 5, height + 2, (11, -1, 8))
    shape -= union([around(cut, q) for q in range(4)])
    rails = union([
        box(1.5, 3.02, height - 4.3, (6.5, 2.98, 4.3)),
        box(4, 1.6, height - 4.3, (6.5, 4.4, 4.3)),
        box(1.5, 3.02, height - 4.3, (142, 2.98, 4.3)),
        box(4, 1.6, height - 4.3, (139.5, 4.4, 4.3)),
        box(134, 3.02, 1, (8, 2.98, 4.3)),
    ])
    shape += union([around(rails, q) for q in range(4)])
    cable = mono.front_prism([(72, -1), (78, -1), (78, 4), (75, 7), (72, 4)], 7, -1)
    return shape - around(cable, 2)


def lid():
    rim = box(150, 150, 2) - box(134, 134, 4, (8, 8, -1))
    parts = [box(150, 150, .8), rim]
    for q in range(4):
        # 0.3 mm end clearance to the frame's corner posts.
        parts.append(around(box(127.4, P['lid_baffle_thickness_mm'], 9.02, (11.3, 0, 1.98)), q))
    for x in (4.5, 145.5):
        for y in (4.5, 145.5):
            parts.append(m.Manifold.cylinder(4.02, 1.15, 1.15, 48).translate((x, y, 1.98)))
    cap = union(parts)
    # Leave the complete 0.8 mm top intact. Shallow channels on its underside
    # discharge downward behind the outer baffles, in front of the panels.
    start = (150 - P['outlet_channel_length_mm'])/2
    channels = [around(box(P['outlet_channel_length_mm'], 9-P['lid_baffle_thickness_mm'],
                          P['outlet_channel_height_mm']+.02,
                          (start, P['lid_baffle_thickness_mm'], 2-P['outlet_channel_height_mm'])), q)
                for q in range(4)]
    return cap - union(channels)


def check_air_paths(assembly):
    """Collision-free connected clearance volumes, not a thermal simulation."""
    solid = union(assembly)
    inlet = union([box(27.8, 18, 1.2, (35.1, -1, .4)),
                   box(27.8, 1.8, 5.6, (35.1, 16.1, -.2))])
    outlet = union([box(99.8, 8.7, 1, (25.1, 1.3, 148.1)),
                    box(99.8, 1.8, 9.8, (25.1, 1.3, 138.5)),
                    box(99.8, 2.5, .4, (25.1, -1, 138.5))])
    assert len(inlet.decompose()) == len(outlet.decompose()) == 1
    for q in range(4):
        for path in (inlet, inlet.translate((52, 0, 0)), outlet):
            assert (around(path, q) ^ solid).volume() < .001, ('blocked air path', q)
    # The old visible side holes are filled; the only wall opening is the
    # retained rear cable exit. The top surface is continuous over its area.
    for x in (24, 42, 108, 126):
        filled = box(1, 2, 1, (x-.5, .5, 6))
        for q in range(4):
            assert (around(filled, q) - solid).volume() < .001
    assert (box(150, 150, .8, (0, 0, 149.2)) - solid).volume() < .001
    return {'underside_clearance_mm': P['foot_height_mm'],
            'inlet_count': 8, 'inlet_open_area_mm2': 8*P['inlet_slot_length_mm']*P['inlet_slot_width_mm'],
            'outlet_count': 4, 'outlet_channel_area_mm2': 4*P['outlet_channel_length_mm']*P['outlet_channel_height_mm'],
            'connected_clearance_paths_verified': True, 'visible_side_vents': False,
            'top_surface_closed': True, 'thermal_performance_verified': False}


def multipart_3mf(parts, target, title, offset=(53, 40, 0)):
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('', ns)
    tag = lambda s: '{' + ns + '}' + s
    root = ET.Element(tag('model'), {'unit': 'millimeter'})
    ET.SubElement(root, tag('metadata'), {'name': 'Title'}).text = title
    resources = ET.SubElement(root, tag('resources'))
    mats = ET.SubElement(resources, tag('basematerials'), {'id': '10'})
    for color in P['colors']:
        ET.SubElement(mats, tag('base'), {'name': color['name'], 'displaycolor': color['hex'] + 'FF'})
    for i, solid in enumerate(parts, 1):
        obj = mesh(solid)
        objel = ET.SubElement(resources, tag('object'), {'id': str(i), 'type': 'model', 'pid': '10', 'pindex': str(i-1)})
        me = ET.SubElement(objel, tag('mesh'))
        vertices = ET.SubElement(me, tag('vertices'))
        for v in obj.vertices:
            ET.SubElement(vertices, tag('vertex'), dict(zip(('x', 'y', 'z'), (f'{c:.6f}' for c in v))))
        triangles = ET.SubElement(me, tag('triangles'))
        for f in obj.faces:
            ET.SubElement(triangles, tag('triangle'), dict(zip(('v1', 'v2', 'v3'), map(str, f))))
    group = ET.SubElement(resources, tag('object'), {'id': '5', 'type': 'model', 'name': title})
    components = ET.SubElement(group, tag('components'))
    for i in range(1, 5):
        ET.SubElement(components, tag('component'), {'objectid': str(i)})
    build = ET.SubElement(root, tag('build'))
    ET.SubElement(build, tag('item'), {'objectid': '5', 'transform': '1 0 0 0 1 0 0 0 1 ' + ' '.join(map(str, offset))})
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/xml"/></Types>')
        archive.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        archive.writestr('3D/3dmodel.model', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def main():
    for folder in ('stl', 'geometry', 'preview', 'print', 'profiles'):
        (OUT/folder).mkdir(parents=True, exist_ok=True)
    panel = panel_parts()
    colors = [p['hex'] for p in P['colors']]
    mono_parts = {'03_frame': frame(), '04_base': base(), '05_lid': lid(), '06_feet': feet()}
    report = {'version': P['version'], 'physical_print_verified': False, 'parts': {}}
    for i, solid in enumerate(panel):
        obj = mesh(solid)
        assert obj.is_watertight and obj.is_winding_consistent and obj.volume > 0
        obj.export(OUT/'stl'/f'02_panel_{i+1}_{P["colors"][i]["name"]}.stl')
        report['parts'][f'panel_slot_{i+1}'] = {'watertight': True, 'volume_mm3': float(obj.volume), 'components': len(obj.split())}
    # Fail if the wordmark accidentally regresses to a single solid color.
    # The lower 40 mm of the artwork contain only text, below both stars.
    regions = logo_regions()
    logo_ymax = regions[3].bounds()[3]
    wordmark = m.CrossSection.square((PW, 40)).translate((0, logo_ymax-40))
    wordmark_areas = [float((s ^ wordmark).area()) for s in regions[:3]]
    assert all(area > 5 for area in wordmark_areas), wordmark_areas
    report['logo_colors'] = {'source': P['logo_source'], 'gradient_band_edges': P['gradient_band_edges'],
                             'sequence': ['Rot', 'Violett', 'Blau'],
                             'lower_wordmark_area_mm2_by_slot_2_3_4': wordmark_areas,
                             'continuous_gradient': False}
    # Coplanar interfaces between materials can leave sub-micron Boolean
    # slivers. Validate their coverage against the analytic panel envelope;
    # export the separately watertight material volumes for the slicer.
    complete_panel = box(PW, PH, TH)
    combined = union(panel)
    assert (complete_panel - combined).volume() < .001
    assert (combined - complete_panel).volume() < .001
    for i in range(4):
        for j in range(i+1, 4):
            assert (panel[i] ^ panel[j]).volume() < .001
    for name, solid in mono_parts.items():
        obj = mesh(solid)
        assert obj.is_watertight and obj.is_winding_consistent, name
        assert len(obj.split()) == (4 if name == '06_feet' else 1), name
        assert abs(obj.bounds[0, 2]) < .001
        obj.export(OUT/'stl'/f'{name}.stl')
        mono.core_3mf([(name, obj, (53, 53, 0))], OUT/'geometry'/f'{name}.3mf')
        report['parts'][name] = {'watertight': True, 'size_mm': obj.extents.tolist()}
    multipart_3mf(panel, OUT/'geometry/02_panel.3mf', 'Logo-Paneel — 4x drucken')
    # A small, flat four-color sample uses the same 0.4 + 0.4 mm layer stack.
    ink = [s.scale((.35, .35, 1)) for s in panel[1:]]
    test = [panel[0].scale((.35,.35,1)), *ink]
    multipart_3mf(test, OUT/'geometry/01_color_test.3mf', 'AMS Farb- und Lichtprobe', (90, 90, 0))
    assembly = [mono_parts['04_base'].translate((0, 0, P['foot_height_mm'])), mono_parts['03_frame'].translate((0,0,3)),
                mono_parts['05_lid'].rotate((180,0,0)).translate((0,150,150))]
    assembly.append(mono_parts['06_feet'])
    assembly.extend(around(assemble_panel(complete_panel), q) for q in range(4))
    for i in range(len(assembly)):
        for j in range(i+1,len(assembly)):
            assert (assembly[i] ^ assembly[j]).volume() < .001, ('collision',i,j)
    for height in (1, 30, 100, 150):
        assert (assemble_panel(complete_panel).translate((0,0,height)) ^ assembly[1]).volume() < .001
    ink_bounds = np.asarray(assemble_panel(union(panel[1:])).bounding_box()).reshape(2,3)
    assert np.allclose(ink_bounds.mean(axis=0)[[0,2]], [75,75], atol=.001)
    bounds = np.asarray(union(assembly).bounding_box()).reshape(2, 3)
    assert np.allclose(bounds[0], [0, 0, 0], atol=.001)
    assert np.allclose(bounds[1] - bounds[0], [150, 150, 150], atol=.001)
    report['ventilation'] = check_air_paths(assembly)
    report.update({'assembled_size_mm': (bounds[1] - bounds[0]).tolist(),
                   'logo_center_xz_mm': ink_bounds.mean(axis=0)[[0,2]].tolist(),
                   'assembly_interference_mm3': 0, 'vertical_panel_insertion_clear': True,
                   'panel_color_depth_mm': CD, 'panel_white_backing_mm': TH-CD})
    scene = trimesh.Scene()
    for name, solid in zip(('base','frame','lid','feet'), assembly[:4]):
        obj=mesh(solid); obj.visual.face_colors=[238,240,241,255]
        scene.add_geometry(obj, node_name=name, geom_name=name)
    for q in range(4):
        for slot, part in enumerate(panel):
            obj=mesh(around(assemble_panel(part),q))
            obj.visual.face_colors=[int(colors[slot][j:j+2],16) for j in (1,3,5)]+[255]
            scene.add_geometry(obj, node_name=f'panel_{q}_slot_{slot+1}', geom_name=f'panel_{q}_slot_{slot+1}')
    scene.export(OUT/'preview/assembly.glb')
    (OUT/'geometry_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
