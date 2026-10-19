"""Verify CMY recipes, P1S settings, bed bounds and every material layer."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

import cairosvg
import manifold3d as m
import numpy as np
import trimesh
from validate_raster_coverage import analyze, footprint, union
from validate_raster_test import model_segments

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/cmy_calibration'


def main():
    (OUT/'print_validation.json').unlink(missing_ok=True)
    (OUT/'print/STATUS.md').write_text('Prüfung läuft; noch keine Druckfreigabe.\n')
    card=json.loads((OUT/'geometry_validation.json').read_text())
    source=ROOT/'design_studies/cmy_calibration/preview_checks.json'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==card['source_study_sha256']
    meshes={}
    for slot in range(1,5):
        file=OUT/'stl'/f'slot_{slot}.stl'
        assert hashlib.sha256(file.read_bytes()).hexdigest()==card['watertight_slot_components'][slot-1]['sha256']
        mesh=trimesh.load_mesh(file)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        meshes[slot]=m.Manifold(m.Mesh(np.float32(mesh.vertices),np.uint32(mesh.faces)))
    file=OUT/'print'/f'{card["plate_name"]}_P1S.3mf'
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        config=json.loads(archive.read('Metadata/project_settings.config'))
        raw=archive.read('Metadata/plate_1.gcode')
        assert hashlib.md5(raw).hexdigest()==archive.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
        settings=ET.fromstring(archive.read('Metadata/model_settings.config'))
    assert config['printer_model']=='Bambu Lab P1S' and config['nozzle_diameter']==['0.4']
    assert config['curr_bed_type']=='Textured PEI Plate'
    assert config['filament_type']==['PLA']*4
    assert config['filament_colour']==[p['hex'] for p in card['palette']]
    assert config['filament_flow_ratio']==['0.98']*4
    assert config['nozzle_temperature']==['220']*4
    assert config['nozzle_temperature_initial_layer']==['220']*4
    assert config['textured_plate_temp']==['55']*4
    assert config['layer_height']=='0.1' and config['initial_layer_print_height']=='0.2'
    assert config['enable_support']=='0' and config['enable_prime_tower']=='1'
    for key in ('flush_into_infill','flush_into_objects','flush_into_support'):
        assert config[key]=='0'
    for key,value in json.loads((ROOT/'cad/cmy_process.json').read_text()).items():
        assert config[key]==value,(key,config[key],value)
    machine=json.loads((OUT/'profiles/machine.json').read_text())
    for key in ('machine_start_gcode','machine_end_gcode'):
        assert config[key]==machine[key],key
    overrides=json.loads((ROOT/'cad/cmy_part_settings.json').read_text())
    parts=settings.findall('object/part')
    assert len(parts)==4
    for slot,part in enumerate(parts,1):
        meta={el.get('key'):el.get('value') for el in part.findall('metadata')}
        assert meta['extruder']==str(slot) and meta['source_volume_id']==str(slot-1)
        assert meta['name']==card['palette'][slot-1]['name']
        for key,value in overrides.get(str(slot),{}).items():assert meta[key]==value
        assert all(int(v)==0 for k,v in part.find('mesh_stat').attrib.items() if k!='face_count')
    code=raw.decode()
    version=re.search(r'; BambuStudio ([\d.]+)',code).group(1)
    assert 'machine: P1S' in code and 'G28' in code and 'M83' in code
    assert 'FEATURE: Support' not in code
    segments=list(model_segments(code,config))
    layers=defaultdict(set)
    capsules=defaultdict(list)
    origin=np.array(card['print_offset_mm'][:2])
    for z,slot,a,b,width in segments:
        layers[z].add(slot)
        capsules[z,slot].append(footprint(a-origin,b-origin,width))
    expected_layers={}
    for z,thickness in card['layer_plan']:
        expected_layers[z]={slot for slot,mesh in meshes.items() if mesh.slice(z-thickness/2).area()>1e-6}
    assert dict(layers)==expected_layers,(dict(layers),expected_layers)
    coverage={key:union(m.CrossSection(items[i:i+512],m.FillRule.Positive)
                       for i in range(0,len(items),512)) for key,items in capsules.items()}
    # Each field/layer is checked separately against its recipe, not a union
    # through the thickness. No other color can satisfy the intended color.
    field_checks=[]
    for field in card['fields']:
        region=m.CrossSection.square((field['width_mm'],field['height_mm'])).translate(field['print_xy_mm'])
        for z,thickness in card['layer_plan']:
            mid=z-thickness/2
            recipe_layer=next((r for r in field['stack_from_bed'] if r['z_start_mm']<mid<r['z_end_mm']),None)
            if recipe_layer is None:continue
            slot='WCMY'.index(recipe_layer['material'])+1
            intended=meshes[slot].slice(mid)
            assert (region-intended).area()<1e-5,(field['id'],z,'wrong CAD recipe')
            own=coverage.get((z,slot),m.CrossSection())
            missing=region-own.offset(.03,circular_segments=32)
            largest=max((p.area() for p in missing.decompose()),default=0.)
            passed=missing.area()/region.area()<=.001 and largest<=.01
            field_checks.append({'field':field['id'],'z_mm':z,'slot':slot,
                'nominal_uncovered_mm2':(region-own).area(),'uncovered_beyond_allowance_mm2':missing.area(),
                'largest_unresolved_mm2':largest,'passed':passed})
    # Bound all modeled extrusion, including brim/tower, using line widths.
    # Arc fitting is disabled for this project, so there are no arc extrema.
    feature='Custom';changing=False;x=y=z=0.;line_width=.4;bounds=[]
    for line in code.splitlines():
        if re.match(r'M620 S\d+',line):changing=True
        if line.startswith('M621 '):changing=False
        if line.startswith('; FEATURE: '):feature=line.removeprefix('; FEATURE: ')
        if line.startswith('; LINE_WIDTH: '):line_width=float(line.split(':')[1])
        if not re.match(r'^G[0123] ',line):continue
        fields={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?\d*\.?\d+)',line)}
        start=np.array([x,y]);x,y,z=fields.get('X',x),fields.get('Y',y),fields.get('Z',z)
        if changing or feature=='Custom' or fields.get('E',0)<=0 or not ('X' in fields or 'Y' in fields):continue
        assert not line.startswith(('G2 ','G3 '))
        low=np.minimum(start,[x,y])-line_width/2
        high=np.maximum(start,[x,y])+line_width/2
        assert np.all(low>=0) and np.all(high<=256) and 0<=z<=250
        assert low[0]>=18.25 or low[1]>=28.25
        bounds.extend([low,high])
    assert len(bounds)>100
    reports=[]
    for n in range(5,11):
        reports.append(analyze(file,'',n/10,OUT/'coverage'/f'layer_{n:02d}',output_root=OUT,
            palette=card['palette'],color_layer_height=.1,backing_layers=((.2,.2),(.3,.1),(.4,.1))))
    result=json.loads((OUT/'print/slicer_result.json').read_text())
    assert result['return_code']==0
    plate=result['sliced_plates'][0]
    assert not plate['warning_message']
    assert len(plate['objects'])==1
    bb=plate['objects'][0]['bbox']
    assert np.allclose([bb[k] for k in ('width','depth','height','x','y')],[90,62,1,40,40])
    passed=all(r['digital_coverage_passed'] for r in reports) and all(f['passed'] for f in field_checks)
    report={'slicer_version':version,'print_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
        'gcode_sha256':hashlib.sha256(raw).hexdigest(),'gcode_md5_valid':True,
        'profile_assignments_verified':True,'manufacturer_start_end_gcode_verified':True,
        'material_layer_schedule':{str(z):sorted(slots) for z,slots in layers.items()},
        'field_layer_checks':field_checks,'field_layer_count':len(field_checks),
        'model_brim_tower_bounds_xy_mm':[np.min(bounds,axis=0).tolist(),np.max(bounds,axis=0).tolist()],
        'supports_generated':False,'slicer_warnings':plate['warning_message'],
        'color_changes':plate['filament_change_times'],
        'estimated_minutes':round(plate['total_predication']/60,1),
        'estimated_filament_g_including_flush_and_tower':round(sum(f['total_used_g'] for f in plate['filaments']),2),
        'digital_coverage_passed':passed,'physical_print_verified':False,
        'color_layer_reports':[f'coverage/layer_{n:02d}.json' for n in range(5,11)],
        'worst_nominal_unprinted_color_percent':max(r['nominal_unprinted_ink_percent'] for r in reports),
        'worst_unprinted_color_percent_after_allowance':max(r['unprinted_ink_beyond_allowance_percent'] for r in reports),
        'largest_color_gap_mm2_after_allowance':max(r['largest_own_ink_deficit_mm2'] for r in reports),
        'geometric_allowance_mm':.03,'acceptance':reports[0]['acceptance'],
        'limitations':'Digital nominal path coverage with fixed tolerance; not zero mathematical gaps, '
                      'not a prediction of optical CMY mixing, adhesion or real material flow.'}
    (OUT/'print_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    # Actual nominal toolpaths for all nine layers, shown from the print side.
    page=['<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="1000" viewBox="0 0 1260 1000">',
          '<rect width="1260" height="1000" fill="#edf1f5"/>',
          '<g font-family="DejaVu Sans,sans-serif" fill="#1d2940">',
          '<text x="30" y="38" font-size="25">CMY-Testkarte · tatsächliche Slicer-Bahnen je Lage</text>']
    for i,(z,height) in enumerate(card['layer_plan']):
        tx,ty=30+(i%3)*410,65+(i//3)*290
        page.append(f'<text x="{tx}" y="{ty+20}" font-size="18">Z = {z:.2f} mm · Lage {i+1}</text>')
        page.append(f'<svg x="{tx}" y="{ty+35}" width="390" height="245" viewBox="0 0 90 62">')
        page.append('<rect width="90" height="62" fill="#d5dbe2"/>')
        for sz,slot,a,b,width in segments:
            if sz!=z:continue
            a,b=a-origin,b-origin
            page.append(f'<path d="M{a[0]:.4f},{62-a[1]:.4f} L{b[0]:.4f},{62-b[1]:.4f}" stroke="{card["palette"][slot-1]["hex"]}" stroke-width="{width:.4f}" stroke-linecap="round" fill="none"/>')
        page.append('</svg>')
    page.append('<text x="30" y="970" font-size="17">Draufsicht im Drucker; weisse Sichtseite auf der Unterseite. Farben zeigen Materialzuordnung, keine Lichtmischung.</text></g></svg>')
    (OUT/'preview/toolpaths.svg').write_text(''.join(page))
    cairosvg.svg2png(url=str(OUT/'preview/toolpaths.svg'),write_to=str(OUT/'preview/toolpaths.png'))
    (OUT/'print/STATUS.md').write_text('# CMY-Testkarte 14\n\n'+
        ('**Digitale Prüfung bestanden; physischer Farbtest ausstehend.**' if passed else '**Keine Druckfreigabe: Flächenprüfung nicht bestanden.**')+
        '\n\nP1S, 0,4-mm-Düse, strukturierte PEI-Platte. AMS: 1 Jade White, 2 Cyan, 3 Magenta, 4 Yellow.\n\n'+
        f'{report["estimated_minutes"]:.1f} Minuten; {report["estimated_filament_g_including_flush_and_tower"]:.2f} g inklusive Reinigung und Turm.\n\n'+
        'Alle neun Lagen geprüft; feste Rechentoleranz 0,03 mm. Kein Versprechen vollständig lückenfreier oder farbtreuer realer Drucke.\n\n'+
        '[Anleitung](../../../docs/CMY_TESTDRUCK.md) · [Prüfbericht](../print_validation.json)\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('field_layer_checks','limitations')},indent=2))
    if not passed:raise SystemExit('FAIL: CMY coverage insufficient')


if __name__=='__main__':main()
