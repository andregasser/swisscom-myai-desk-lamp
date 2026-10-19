"""CMY calibration card concept: dimensioned 2D layout, recipes, no print files.

Colors illustrate ideal selective absorption with deliberately arbitrary
coefficients; they are NOT measured filament transmission or predicted prints.
"""
from pathlib import Path
import csv
import io
import json
import math
import xml.etree.ElementTree as ET

import cairosvg

HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 90, 62
WHITE = .4
LAYER = .1
COLOR = {'C': '#0086D6', 'M': '#EC008C', 'Y': '#F4EE2A', 'W': '#FFFFFF'}


def schematic_color(recipe):
    # Teaching model only. Optical density here is not a filament measurement.
    return '#' + ''.join(f'{round(255*math.exp(-.85*recipe[c])):02x}' for c in 'CMY')


def samples():
    result = []
    # A: one, two and four layers of each individual ink.
    for i, (color, count) in enumerate((c,n) for c in 'CMY' for n in (1,2,4)):
        recipe = {c: count if c == color else 0 for c in 'CMY'}
        result.append({'id': f'A{i+1}', 'row': 'A', 'x_mm': 7+i*8.5,
                       'y_mm': 8, 'width_mm': 8, 'height_mm': 8, 'layers': recipe})
    # B/C share the same cyan/yellow progression, differing only in magenta.
    # Final cell is the identical pure-cyan control in both rows.
    cy = [(0,3),(0,2),(0,1),(0,0),(1,0),(2,0),(3,0),(4,0),(4,0)]
    for row, y, magenta in [('B',25,1), ('C',43,2)]:
        for i, (cyan,yellow) in enumerate(cy):
            result.append({'id': f'{row}{i+1}', 'row': row, 'x_mm': 7+i*8.5,
                           'y_mm': y, 'width_mm': 8, 'height_mm': 10,
                           'layers': {'C': cyan, 'M': magenta if i < 8 else 0, 'Y': yellow}})
    for sample in result:
        z = WHITE
        stack = [{'material': 'W', 'z_start_mm': 0, 'z_end_mm': WHITE}]
        for c in 'YMC':
            n = sample['layers'][c]
            if n:
                stack.append({'material': c, 'z_start_mm': round(z,3),
                              'z_end_mm': round(z+n*LAYER,3)})
                z += n*LAYER
        sample['stack_from_bed'] = stack
        sample['total_height_mm'] = round(z,3)
        sample['schematic_hex_not_prediction'] = schematic_color(sample['layers'])
    return result


def main():
    fields = samples()
    assert len(fields) == 27 and len({f['id'] for f in fields}) == 27
    assert max(f['total_height_mm'] for f in fields) == 1.0
    for f in fields:
        assert 0 <= f['x_mm'] < f['x_mm']+f['width_mm'] <= WIDTH
        assert 0 <= f['y_mm'] < f['y_mm']+f['height_mm'] <= HEIGHT
        assert all(isinstance(n,int) and n >= 0 for n in f['layers'].values())
        for a,b in zip(f['stack_from_bed'],f['stack_from_bed'][1:]):
            assert a['z_end_mm'] == b['z_start_mm']
    for i,a in enumerate(fields):
        for b in fields[i+1:]:
            assert (a['x_mm']+a['width_mm'] <= b['x_mm'] or b['x_mm']+b['width_mm'] <= a['x_mm']
                    or a['y_mm']+a['height_mm'] <= b['y_mm'] or b['y_mm']+b['height_mm'] <= a['y_mm'])
    for i in range(9):
        b,c = fields[9+i],fields[18+i]
        assert b['layers']['C'] == c['layers']['C'] and b['layers']['Y'] == c['layers']['Y']
        assert c['layers']['M']-b['layers']['M'] == (1 if i < 8 else 0)
    report = {
        'status': 'Preview and calibration recipes only; not sliced',
        'machine': 'Bambu Lab P1S', 'nozzle_mm': .4,
        'card_dimensions_mm': [WIDTH,HEIGHT], 'white_base_mm': WHITE,
        'proposed_first_layer_mm': .2, 'proposed_subsequent_layer_mm': LAYER,
        'white_layer_tops_mm': [.2,.3,.4],
        'max_total_height_mm': 1.0,
        'slot_mapping': {'1': 'PLA Basic Jade White', '2': 'PLA Basic Cyan',
                         '3': 'PLA Basic Magenta', '4': 'PLA Basic Yellow'},
        'nominal_filament_hex_not_transmission': COLOR,
        'stack_order_from_bed': ['W','Y','M','C'],
        'viewing_side': 'Flat white bed-contact side; colored relief faces lamp inside',
        'physical_labels': False,
        'fields': fields,
        'checks': {'field_bounds': True, 'nonoverlapping_fields': True,
                   'continuous_vertical_stacks': True, 'paired_rows_differ_only_in_magenta': True},
        'color_model': 'Illustrative RGB channel attenuation: channel = round(255*exp(-0.85*layer_count)); '
                       'C affects R, M affects G, Y affects B. Arbitrary, not calibrated. '
                       'No scattering, white-base transmission, LED spectrum, or real pigment spectra modeled.',
        'sliced': False, 'physical_print_verified': False,
        'limitations': ['Stepped calibration samples, not a continuous logo gradient.',
                        'Neither light transmission nor perceived color is predicted.',
                        'No claim of full slicer coverage or gap closure.',
                        'Variable thickness on the inside; not a 0.6 mm production side panel.',
                        '0.5 mm white spaces separate samples intentionally; not print defects.',
                        'Labels in the preview are annotations, not a fifth print color.'],
    }
    (HERE/'preview_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    csvfile=io.StringIO()
    writer=csv.writer(csvfile, lineterminator='\n')
    writer.writerow(['field','cyan_mm','magenta_mm','yellow_mm','white_mm','total_mm'])
    for f in fields:
        writer.writerow([f['id'],*[f'{f["layers"][c]*LAYER:.1f}' for c in 'CMY'],f'{WHITE:.1f}',f'{f["total_height_mm"]:.1f}'])
    (HERE/'recipes.csv').write_text(csvfile.getvalue())

    card=[f'<rect width="{WIDTH}" height="{HEIGHT}" rx="2" fill="white" stroke="#c8d1dc" stroke-width=".2"/>']
    for f in fields:
        card.append(f'<rect x="{f["x_mm"]}" y="{f["y_mm"]}" width="{f["width_mm"]}" height="{f["height_mm"]}" fill="{f["schematic_hex_not_prediction"]}"/>')
    content=''.join(card)
    (HERE/'card.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="90mm" height="62mm" viewBox="0 0 90 62"><title>Schematische CMY-Testkarte; keine Farbvorhersage</title>{content}</svg>')
    page=['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1160" viewBox="0 0 1500 1160">',
          '<rect width="1500" height="1160" fill="#edf1f5"/>',
          '<g font-family="DejaVu Sans,sans-serif" fill="#1d2940">']
    def text(x,y,value,size=20,bold=False):
        page.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{"bold" if bold else "normal"}">{value}</text>')
    text(42,54,'CMY · Kleine Verlaufskarte',32,True)
    text(42,91,'P1S · 0,4-mm-Düse · ein AMS · 90 × 62 mm',23)
    page.append('<rect x="42" y="112" width="1416" height="48" rx="10" fill="#fff0cc"/>')
    text(60,143,'Schematische Farbillustration – keine Vorhersage des Drucks oder der LED-Wirkung.',20,True)
    # The same dimensioned card is used for standalone SVG and annotated layout.
    page.append(f'<g transform="translate(88 215) scale(9)">{content}</g>')
    text(88,197,'Durchsicht von der ebenen weissen Seite · Farben liegen dahinter',18)
    for f in fields:
        x=88+(f['x_mm']+4)*9
        y=215+(f['y_mm']+f['height_mm']+2.6)*9
        page.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="14">{f["id"]}</text>')
    for y,letter in [(215+12*9,'A'),(215+30*9,'B'),(215+48*9,'C')]:
        text(50,y+8,letter,24,True)
    text(88,807,'27 breite Prüffelder · weisse Zwischenräume bewusst vorgesehen',18)
    text(88,836,'Feldnummern nur als Bildlegende; sie werden nicht mitgedruckt.',17)
    # Right-hand guide avoids presenting a smoothed fictional gradient.
    text(952,221,'A · Einzelne Farben',23,True)
    text(952,254,'Cyan / Magenta / Gelb',19)
    text(952,284,'Je 0,10 / 0,20 / 0,40 mm Farbe',19)
    text(952,314,'Vergleich: Sättigung und Lichtverlust',18)
    text(952,370,'B · Weniger Magenta',23,True)
    text(952,403,'0,10 mm Magenta + variable C/Y',19)
    text(952,433,'Rotbereich → Violett/Blau → Cyan',18)
    text(952,489,'C · Mehr Magenta',23,True)
    text(952,522,'0,20 mm Magenta + gleiche C/Y',19)
    text(952,552,'Vergleich: Rot und Blau gegenüber B',18)
    text(952,589,'B9 / C9: identische Cyan-Kontrolle',17)
    text(952,645,'Schichten statt schmaler Farbstreifen',21,True)
    # Physical cross-section of C6, through field center (0.2 C + 0.2 M).
    example=next(f for f in fields if f['id']=='C6')
    text(952,677,'Beispiel C6 · Querschnitt, stark vergrössert',16)
    ztop=example['total_height_mm']
    for layer in reversed(example['stack_from_bed']):
        top=700+(ztop-layer['z_end_mm'])*140
        height=(layer['z_end_mm']-layer['z_start_mm'])*140
        page.append(f'<rect x="960" y="{top}" width="200" height="{height}" fill="{COLOR[layer["material"]]}" stroke="#526071" stroke-width="1"/>')
        names={'C':'0,20 mm Cyan','M':'0,20 mm Magenta','W':'0,40 mm Weiss'}
        text(1175,top+height/2+6,names[layer['material']],17)
    text(960,840,'LED oben · Blick von unten',17)
    page.append('<rect x="42" y="882" width="1416" height="214" rx="14" fill="white"/>')
    text(64,919,'Was wir damit herausfinden',24,True)
    text(64,956,'Welche Schichtmischungen mit deinem LED-Kit gute Rot-, Violett- und Blautöne ergeben – und wie hell sie bleiben.',19)
    text(64,990,'Geplant: 0,40 mm Weiss + 0,10-mm-Farblagen; bis 1,00 mm Gesamtdicke. Rückseite gestuft, Vorderseite eben.',19)
    text(64,1024,'Zuerst Materialabgleich in breiten Feldern. Ein feiner Logo-Verlauf folgt erst aus den beobachteten Farben.',19)
    text(64,1060,'Nur Vorschau und Schichtrezepte · noch keine Druckdatei, Slicer-Prüfung oder bestätigte Farbmischung.',18,True)
    page.append('</g></svg>')
    (HERE/'preview.svg').write_text(''.join(page))
    cairosvg.svg2png(url=str(HERE/'preview.svg'),write_to=str(HERE/'preview.png'))
    for file in HERE.glob('*.svg'):
        ET.parse(file)
    assert not any(p.suffix in ('.stl','.3mf','.gcode') for p in HERE.rglob('*'))
    print('27 fields checked: bounds, separation, continuous stacks, paired recipes; preview only.')


if __name__ == '__main__':
    main()
