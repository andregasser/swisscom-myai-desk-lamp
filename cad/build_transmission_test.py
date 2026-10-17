"""One labeled AMS card comparing 0.2/0.4 mm ink at 0.6 mm total thickness."""
import json
import manifold3d as m
import build as mono
import build_multicolor as ams

OUT = ams.OUT
WIDTH, HEIGHT, TOTAL, RIM = 142., 80., .6, 1.
OFFSET = (30., 40., 0.)
WINDOW = 24.
ROWS = [(8., .2), (44., .4)]
COLUMNS = [(23., 4), (53., 3), (83., 2), (113., 1)]


def front_label(text, x, y):
    # The colored face is the bed-contact face. In its readable view, +Y is down.
    return mono.label(text, 0, 0, 0).scale((1.4, -1.4, .5)).translate((x, y, 0))


def main():
    for folder in ('geometry', 'transmission_test/stl', 'preview'):
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    envelope = mono.box(WIDTH, HEIGHT, RIM)
    notch = m.CrossSection([[(0, 0), (4, 0), (0, 4)]]).extrude(RIM)
    envelope -= notch
    inks = {2: [], 3: [], 4: []}
    windows = []
    for y, depth in ROWS:
        inks[2].append(front_label(f'{depth:.1f}', 4, y+15))
        for x, slot in COLUMNS:
            envelope -= mono.box(WINDOW, WINDOW, RIM, (x, y, TOTAL))
            if slot != 1:
                inks[slot].append(mono.box(WINDOW, WINDOW, depth, (x, y, 0)))
            windows.append({'x_mm': x, 'y_mm': y, 'size_mm': WINDOW, 'slot': slot,
                            'row_color_depth_mm': depth,
                            'color_depth_mm': depth if slot != 1 else 0,
                            'white_depth_mm': TOTAL-depth if slot != 1 else TOTAL})
    for x, slot in COLUMNS:
        inks[2].append(front_label(str(slot), x+10, 77))
    colors = [mono.union(inks[slot]) for slot in (2, 3, 4)]
    white = envelope - mono.union(colors)
    parts = [white, *colors]
    joined = mono.union(parts)
    assert (joined - envelope).volume() < .001
    assert (envelope - joined).volume() < .001
    assert len(joined.decompose()) == 1
    for i, part in enumerate(parts):
        mesh = mono.mesh(part)
        assert mesh.is_watertight and mesh.is_winding_consistent
        if i == 0:
            assert len(mesh.split()) == 1
        mesh.export(OUT / 'transmission_test/stl' / f'slot_{i+1}.stl')
        for other in parts[i+1:]:
            assert (part ^ other).volume() < .001
    # Verify the actual material in the center of every window, layer by layer.
    for window in windows:
        for layer in range(3):
            z = layer * .2
            probe = mono.box(20, 20, .2, (window['x_mm']+2, window['y_mm']+2, z))
            expected = window['slot'] if z < window['color_depth_mm']-.001 else 1
            for slot, part in enumerate(parts, 1):
                volume = (probe ^ part).volume()
                assert abs(volume - (80 if slot == expected else 0)) < .001
    ams.multipart_3mf(parts, OUT / 'geometry/08_transmission_test.3mf',
                      'Lichtvergleich: 0.2 und 0.4 mm Farbe', OFFSET)
    report = {'physical_print_verified': False, 'size_mm': [WIDTH, HEIGHT, RIM],
              'window_total_thickness_mm': TOTAL, 'print_offset_mm': OFFSET,
              'one_connected_card': True, 'material_intersections_mm3': 0,
              'layer_material_checks_passed': True, 'front_is_bed_face': True,
              'orientation': 'Clipped corner top left when colored face is viewed with labels readable.',
              'windows': windows}
    (OUT / 'transmission_test/geometry_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Validated transmission card:', WIDTH, 'x', HEIGHT, 'mm; eight 0.6 mm windows')


if __name__ == '__main__':
    main()
