"""Verify the sliced P1S card and full color coverage; refuse release on gaps."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh
from validate_raster_coverage import analyze
from validate_raster_test import model_segments

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/line_gradient_test'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--allow-withheld',action='store_true',help='Audit only; does not approve printing')
parser.add_argument('--output',type=Path,default=OUT)
args=parser.parse_args()
OUT=args.output.resolve()
card=json.loads((OUT/'geometry_validation.json').read_text())
file=OUT/'print'/f'{card.get("plate_name","11_line_gradient_test")}_P1S.3mf'
for slot in range(1,5):
    mesh=trimesh.load_mesh(OUT/'stl'/f'slot_{slot}.stl')
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
    assert abs(mesh.bounds[0,2]-(0 if slot==1 else .4))<1e-5
    assert abs(mesh.bounds[1,2]-.6)<1e-5
    assert np.all(mesh.extents<=[256,256,250])
with zipfile.ZipFile(file) as archive:
    assert archive.testzip() is None
    config=json.loads(archive.read('Metadata/project_settings.config'))
    raw=archive.read('Metadata/plate_1.gcode')
    assert hashlib.md5(raw).hexdigest()==archive.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    assert config['printer_model']=='Bambu Lab P1S' and config['nozzle_diameter']==['0.4']
    assert config['filament_type']==['PLA']*4 and config['curr_bed_type']=='Textured PEI Plate'
    assert config['filament_colour']==[c['hex'] for c in card['palette']]
    assert config['enable_support']=='0' and config['enable_prime_tower']=='1'
    assert config['nozzle_temperature']==['220']*4
    for key in ('flush_into_infill','flush_into_objects','flush_into_support'): assert config[key]=='0'
    settings=ET.fromstring(archive.read('Metadata/model_settings.config'))
    parts=settings.findall('object/part')
    assert len(parts)==4
    for slot,part in enumerate(parts,1):
        meta={el.get('key'):el.get('value') for el in part.findall('metadata')}
        assert meta['extruder']==str(slot) and meta['source_volume_id']==str(slot-1)
        assert meta['name']==card['palette'][slot-1]['name']
        assert all(int(v)==0 for k,v in part.find('mesh_stat').attrib.items() if k!='face_count')
code=raw.decode()
assert 'machine: P1S' in code and 'G28' in code and 'M83' in code
assert 'FEATURE: Support' not in code
layers=defaultdict(set)
for z,slot,a,b,width in model_segments(code,config):
    layers[z].add(slot)
assert dict(layers)=={.2:{1},.4:{1},.6:{1,2,3,4}}
# Check model, brim and tower extrusion bounds. Start/end/purge macros are
# excluded; arcs are additionally covered by the full footprint parser below.
feature='Custom'; changing=False; x=y=z=0.; points=[]
for line in code.splitlines():
    if re.match(r'M620 S\d+',line): changing=True
    if line.startswith('M621 '): changing=False
    if line.startswith('; FEATURE: '): feature=line.removeprefix('; FEATURE: ')
    if not re.match(r'^G[0123] ',line): continue
    fields={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?\d*\.?\d+)',line)}
    x,y,z=fields.get('X',x),fields.get('Y',y),fields.get('Z',z)
    if changing or feature=='Custom' or fields.get('E',0)<=0 or not ('X' in fields or 'Y' in fields): continue
    assert 0<=x<=256 and 0<=y<=256 and 0<=z<=250
    assert not (x<18.25 and y<28.25)
    points.append((x,y,z))
assert len(points)>100
result=json.loads((OUT/'print/slicer_result.json').read_text())
assert result['return_code']==0
plate=result['sliced_plates'][0]
assert not plate['warning_message'] and plate['filament_change_times']==3
coverage=analyze(file,'',.6,OUT/'surface_coverage',output_root=OUT,palette=card['palette'])
report={'slicer_version':'02.08.02.61','print_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
        'sliced_successfully':True,'profile_assignments_verified':True,
        'gcode_md5_valid':True,'model_layer_slots':{str(z):sorted(s) for z,s in layers.items()},
        'print_extrusion_bounds_mm':[np.min(points,axis=0).tolist(),np.max(points,axis=0).tolist()],
        'supports_generated':False,'slicer_warnings':plate['warning_message'],'color_changes':3,
        'estimated_minutes':round(plate['total_predication']/60,1),
        'estimated_filament_g_including_flush_and_tower':round(sum(f['total_used_g'] for f in plate['filaments']),2),
        'digital_coverage_passed':coverage['digital_coverage_passed'],'physical_print_verified':False,
        'coverage_report':'surface_coverage.json'}
(OUT/'print_validation.json').write_text(json.dumps(report,indent=2)+'\n')
passed=coverage['digital_coverage_passed']
(OUT/'print/STATUS.md').write_text(
    f'# Testkarte {card.get("plate_name","11_line_gradient_test").split("_")[0]} — {card.get("stripe_pitch_mm",.48):g}-mm-Farbbahnen\n\n'+
    ('**Digitale Flächenprüfung bestanden; physischer Probedruck noch ausstehend.**\n\n' if passed else
     '**Nicht als lückenfreier Testdruck freigegeben.** Die Slicer-Datei bleibt zur Prüfung erhalten; '
     'die vollständige Flächenprüfung findet weiterhin Restlücken. Kein bestätigter Fix der weissen Stellen.\n\n')+
    f'Nominell unbedeckte Farbfläche: {coverage["nominal_unprinted_ink_percent"]:.3f} %. '
    f'Nach 0,03 mm Rechentoleranz: {coverage["unprinted_ink_beyond_allowance_mm2"]:.3f} mm².\n\n'+
    'AMS: 1 Weiss, 2 Blau, **3 Cyanblau**, 4 Rot. Cyan ersetzt Violett.\n\n'+
    '[Vollständiger Prüfbericht](../surface_coverage.json) · '+
    f'[Anleitung](../../../docs/{"FARBBAHNEN_VERFEINERT" if card.get("plate_name","").startswith("12_") else "FARBBAHNEN_TEST"}.md).\n')
print(json.dumps({**report,'nominal_unprinted_ink_percent':coverage['nominal_unprinted_ink_percent'],
                 'unprinted_ink_beyond_allowance_percent':coverage['unprinted_ink_beyond_allowance_percent'],
                 'largest_unresolved_area_mm2':coverage['largest_unresolved_area_mm2']},indent=2))
if not passed and not args.allow_withheld:
    raise SystemExit('FAIL: Restlücken in den Farbbahnen; keine Freigabe als geschlossene Farbfläche.')
