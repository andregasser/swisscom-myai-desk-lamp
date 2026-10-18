"""Slice only the 0.48 mm straight-band card, with cyan replacing violet."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/line_gradient_test'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('bambu_studio',type=Path)
parser.add_argument('--process',type=Path,help='Explicit test process override; archived with output')
args=parser.parse_args()
args.bambu_studio=args.bambu_studio.resolve()
card=json.loads((OUT/'geometry_validation.json').read_text())
process=json.loads((ROOT/'output/multicolor_v4_2/profiles/process_raster_original.json').read_text())
process.update(name='myAI Farbbahnen 0.48mm P1S',print_settings_id='myAI Farbbahnen 0.48mm P1S',
               wall_generator='classic',detect_thin_wall='1',wall_loops='1',
               outer_wall_line_width='0.4',inner_wall_line_width='0.4',top_surface_line_width='0.4',
               seam_gap='0%',resolution='0.005')
if args.process: process.update(json.loads(args.process.read_text()))
profile=OUT/'profiles/process.json'
profile.write_text(json.dumps(process,indent=2)+'\n')
for color in card['palette']:
    data=json.loads((ROOT/'output/profiles/pla_white.json').read_text())
    name='myAI PLA '+color['name']+' Farbbahnen'
    data.update(name=name,filament_settings_id=[name],filament_colour=[color['hex']],
                additional_cooling_fan_speed=['0'],fan_min_speed=['50'],fan_max_speed=['50'],
                close_fan_the_first_x_layers=['2'])
    data['from']='User'
    # Cyan is a new generic PLA profile, not the former 210 C ecoPLA Purple.
    (OUT/'profiles'/f'filament_{color["slot"]}.json').write_text(json.dumps(data,indent=2)+'\n')
scratch=ROOT/'output/logs/line_gradient_test'
scratch.mkdir(parents=True,exist_ok=True)
for name in ('print_validation.json','surface_coverage.json','surface_coverage.svg','surface_coverage.png'):
    (OUT/name).unlink(missing_ok=True)
(OUT/'print/STATUS.md').write_text('# Testkarte 11\n\nSlicing gestartet; vor einer neuen Flächenprüfung keine Druckfreigabe.\n')
common=[str(args.bambu_studio),'--datadir',str(scratch/'config'),'--debug','2',
        '--load-settings',f'{ROOT/"output/profiles/p1s_0.4.json"};{profile}',
        '--load-filaments',';'.join(str(OUT/'profiles'/f'filament_{i}.json') for i in range(1,5)),
        '--arrange','0','--orient','0']
with (scratch/'convert.log').open('w') as log:
    subprocess.run(common+['--export-3mf','native.3mf','--outputdir',str(scratch),
                          str(OUT/'geometry/11_line_gradient_test.3mf')],
                   cwd=scratch,stdout=log,stderr=subprocess.STDOUT,check=True)
with zipfile.ZipFile(scratch/'native.3mf') as archive:
    payload={n:archive.read(n) for n in archive.namelist()}
config=ET.fromstring(payload['Metadata/model_settings.config'])
parts=config.findall('object/part')
assert len(parts)==4
for slot,part in enumerate(parts,1):
    meta={el.get('key'):el.get('value') for el in part.findall('metadata')}
    assert meta['source_volume_id']==str(slot-1)
    for el in part.findall('metadata'):
        if el.get('key')=='name': el.set('value',card['palette'][slot-1]['name'])
    extruder=part.find("metadata[@key='extruder']")
    if extruder is None: extruder=ET.SubElement(part,'metadata',{'key':'extruder'})
    extruder.set('value',str(slot))
payload['Metadata/model_settings.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
settings=json.loads(payload['Metadata/project_settings.config'])
settings.update(flush_volumes_vector=['140']*8,
                flush_volumes_matrix=['0' if i==j else ('650' if j==0 else '450') for i in range(4) for j in range(4)],
                wipe_tower_x=['205'],wipe_tower_y=['170'])
payload['Metadata/project_settings.config']=json.dumps(settings).encode()
source=scratch/'assigned.3mf'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,data in payload.items(): archive.writestr(name,data)
name='11_line_gradient_test_P1S.3mf'
with (scratch/'slicer.log').open('w') as log:
    subprocess.run(common+['--slice','0','--export-3mf',name,'--outputdir',str(scratch),str(source)],
                   cwd=scratch,stdout=log,stderr=subprocess.STDOUT,check=True)
result=json.loads((scratch/'result.json').read_text())
assert result['return_code']==0
shutil.copyfile(scratch/name,OUT/'print'/name)
(OUT/'print/slicer_result.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'print/STATUS.md').write_text('# Testkarte 11\n\nNeu geslict. Flächenprüfung vor Druckempfehlung erforderlich.\n')
print(json.dumps(result['sliced_plates'],indent=2))
