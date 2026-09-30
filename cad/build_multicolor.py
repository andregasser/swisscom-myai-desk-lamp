#!/usr/bin/env python3
"""v4: full-face flush AMS panels with concealed sliding dovetail rails."""
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
OUT = ROOT / 'output' / P['output_folder']
PW, PH = P['panel_width_mm'], P['panel_height_mm']
TH, CD = P['panel_thickness_mm'], P['color_depth_mm']
box, union, around, mesh = mono.box, mono.union, mono.around, mono.mesh
FOOT_CENTERS = [(x, y) for x in (18, 132) for y in (18, 132)]
POST_CENTERS = [(x, y) for x in (6.5, 143.5) for y in (6.5, 143.5)]


def feet():
    pad = m.Manifold.cylinder(P['foot_height_mm'], P['foot_diameter_mm']/2,
                             P['foot_diameter_mm']/2, 64)
    peg = m.Manifold.cylinder(P['foot_peg_height_mm'] + .02, P['foot_peg_diameter_mm']/2,
                             P['foot_peg_diameter_mm']/2, 48).translate((0, 0, P['foot_height_mm'] - .02))
    return union([(pad + peg).translate((x, y, 0)) for x, y in FOOT_CENTERS])


def inlet_slots():
    return union([around(box(P['inlet_slot_length_mm'], P['inlet_slot_width_mm'], 10,
                            (x, 16, -1)), q) for x in (35, 87) for q in range(4)])


def base():
    # Inset beneath the four uninterrupted faces. The feet leave room for
    # both intake air and the cable, which now exits entirely underneath.
    bottom = P['foot_height_mm']
    seat = P['frame_bottom_mm']
    plate = union([box(148, 148, seat-bottom, (1, 1, bottom)),
                   box(130, 130, 1.02, (10, 10, seat-.02)),
                   mono.led_ring(seat+.98),
                   *[m.Manifold.cylinder(2.02, 1.5, 1.5, 48).translate((x, y, seat-.02))
                     for x, y in POST_CENTERS]])
    sockets = union([m.Manifold.cylinder(P['foot_socket_depth_mm']+.02,
                        P['foot_socket_diameter_mm']/2, P['foot_socket_diameter_mm']/2,
                        48).translate((x, y, bottom-.02)) for x, y in FOOT_CENTERS])
    # Sockets open on the bed; only their 4.4 mm roofs require bridging.
    cable_slot = box(6, 19, 10, (72, 133, bottom-.1))
    return (plate - inlet_slots() - sockets - cable_slot).translate((0, 0, -bottom))


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


def rail_profile(center):
    return [(center-1, TH-.02), (center+1, TH-.02),
            (center+2, TH+2), (center-2, TH+2)]


def panel_envelope(with_rails=True):
    # Mitred vertical edges leave only narrow corner assembly seams.
    panel = mono.front_prism([(0, 0), (PW, 0), (PW-TH, TH), (TH, TH)], PH)
    if with_rails:
        length = PH-P['rail_top_margin_mm']-P['rail_bottom_margin_mm']
        for center in (6-P['panel_left_mm'], 144-P['panel_left_mm']):
            panel += mono.front_prism(rail_profile(center), length, P['rail_top_margin_mm'])
    return panel


def panel_parts(with_rails=True):
    regions = logo_regions()
    inks = [m.Manifold.extrude(region, CD) for region in regions[:3]]
    white = panel_envelope(with_rails) - m.Manifold.extrude(regions[3], CD)
    return [white, *inks]


def assemble_panel(part):
    return part.transform(((1, 0, 0, P['panel_left_mm']),
                           (0, 0, 1, P['panel_front_depth_mm']),
                           (0, -1, 0, P['panel_bottom_mm'] + PH)))


def frame():
    height = P['frame_height_mm']
    ring = box(148, 148, 2, (1, 1, 0)) - box(136, 136, 4, (7, 7, -1))
    shape = ring + union([box(9, 9, height, (x, y, 0)) for x in (1, 140) for y in (1, 140)])
    channels = []
    for center in (6, 144):
        profile = m.CrossSection([rail_profile(center)]).offset(P['rail_clearance_mm'])
        channel = m.Manifold.extrude(profile, height).translate((0, 0, 2))
        channels.extend(around(channel, q) for q in range(4))
    for x, y in POST_CENTERS:
        channels.append(m.Manifold.cylinder(3.3, 1.7, 1.7, 48).translate((x, y, -1)))
        channels.append(m.Manifold.cylinder(5.4, 1.5, 1.5, 48).translate((x, y, height-4.4)))
    return shape - union(channels)


def lid():
    inset = P['lid_inset_mm']
    rim = box(150-2*inset, 150-2*inset, 2, (inset, inset, 0)) - box(134, 134, 4, (8, 8, -1))
    parts = [box(150-2*inset, 150-2*inset, .8, (inset, inset, 0)), rim]
    for x, y in POST_CENTERS:
        parts.append(m.Manifold.cylinder(4.02, 1.3, 1.3, 48).translate((x, y, 1.98)))
    cap = union(parts)
    # Intact lid surface, with outlets in the 0.8 mm perimeter joint on top.
    # No exterior side bezel or step remains in front of the panels.
    start = (150 - P['outlet_channel_length_mm'])/2
    channels = [around(box(P['outlet_channel_length_mm'], 9-inset+.1,
                          P['outlet_channel_height_mm']+.02,
                          (start, inset-.1, 2-P['outlet_channel_height_mm'])), q)
                for q in range(4)]
    return cap - union(channels)


def check_air_paths(assembly):
    """Collision-free connected clearance volumes, not a thermal simulation."""
    solid = union(assembly)
    inlet = union([box(27.8, 18, 2, (35.1, -1, 1)),
                   box(27.8, 1.8, 6.5, (35.1, 16.1, 1))])
    outlet = union([box(119.8, 8.1, 1, (15.1, .9, 148.1)),
                    box(119.8, .6, 2.4, (15.1, .9, 148.1))])
    assert len(inlet.decompose()) == len(outlet.decompose()) == 1
    for q in range(4):
        for path in (inlet, inlet.translate((52, 0, 0)), outlet):
            assert (around(path, q) ^ solid).volume() < .001, ('blocked air path', q)
    cable = union([box(4, 4, 8, (73, 134, 1)), box(4, 18, 2, (73, 135, 1))])
    assert (cable ^ solid).volume() < .001, 'Cable path obstructed'
    # Entire visible face, including the area where the frame used to be.
    face_skin = box(PW-2*TH, .1, PH, (P['panel_left_mm']+TH, 0, P['panel_bottom_mm']))
    for q in range(4):
        assert (around(face_skin, q) - solid).volume() < .001, ('recessed face', q)
    inset = P['lid_inset_mm']
    assert (box(150-2*inset, 150-2*inset, .8, (inset, inset, 149.2)) - solid).volume() < .001
    return {'underside_clearance_mm': P['foot_height_mm'],
            'inlet_count': 8, 'inlet_open_area_mm2': 8*P['inlet_slot_length_mm']*P['inlet_slot_width_mm'],
            'outlet_count': 4, 'outlet_channel_area_mm2': 4*P['outlet_channel_length_mm']*P['outlet_channel_height_mm'],
            'top_joint_width_mm': inset-TH, 'outlet_joint_area_mm2': 4*P['outlet_channel_length_mm']*(inset-TH),
            'cable_exits_under_base': True, 'side_recess_mm': 0,
            'connected_clearance_paths_verified': True, 'visible_side_vents': False,
            'top_surface_closed': True, 'thermal_performance_verified': False}


def multipart_3mf(parts, target, title, offset=(35, 40, 0)):
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
    complete_panel = panel_envelope()
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
    # Small pieces cut directly from the actual guide geometries, in their
    # production print orientations, to test tolerances before a full frame.
    fit_parts = [
        ('07_fit_panel', (complete_panel ^ box(12, 20, 4, (0, 20, 0))).translate((0, -20, 0)), (90, 110, 0)),
        ('07_fit_corner', (mono_parts['03_frame'] ^ box(10, 10, 20, (0, 0, 10))).translate((-1, -1, -10)), (120, 110, 0)),
    ]
    for name, solid, offset in fit_parts:
        obj = mesh(solid)
        assert obj.is_watertight and obj.is_winding_consistent and len(obj.split()) == 1
        obj.export(OUT/'stl'/f'{name}.stl')
        report['parts'][name] = {'watertight': True, 'size_mm': obj.extents.tolist()}
    mono.core_3mf([(name, mesh(solid), offset) for name, solid, offset in fit_parts], OUT/'geometry/07_fit.3mf')
    multipart_3mf(panel, OUT/'geometry/02_panel.3mf', 'Logo-Paneel — 4x drucken')
    # A small, flat four-color sample uses the same 0.4 + 0.4 mm layer stack.
    test = [s.scale((.35, .35, 1)) for s in panel_parts(with_rails=False)]
    multipart_3mf(test, OUT/'geometry/01_color_test.3mf', 'AMS Farb- und Lichtprobe', (90, 90, 0))
    assembly = [mono_parts['04_base'].translate((0, 0, P['foot_height_mm'])), mono_parts['03_frame'].translate((0,0,P['frame_bottom_mm'])),
                mono_parts['05_lid'].rotate((180,0,0)).translate((0,150,150))]
    assembly.append(mono_parts['06_feet'])
    assembly.extend(around(assemble_panel(complete_panel), q) for q in range(4))
    for i in range(len(assembly)):
        for j in range(i+1,len(assembly)):
            assert (assembly[i] ^ assembly[j]).volume() < .001, ('collision',i,j)
    for height in (1, 30, 100, 150):
        assert (assemble_panel(complete_panel).translate((0,0,height)) ^ assembly[1]).volume() < .001
    assert (assemble_panel(complete_panel).translate((0, -.8, 0)) ^ assembly[1]).volume() > 10
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
