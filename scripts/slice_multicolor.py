"""Prepare and slice the v3 four-slot AMS design using Bambu Studio."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/multicolor_v3'
P = json.loads((ROOT/'cad/multicolor_parameters.json').read_text())
parser = argparse.ArgumentParser()
parser.add_argument('bambu_studio', type=Path)
parser.add_argument('--plates', nargs='+', default=['01_color_test','02_panel','03_frame','04_base','05_lid'])
args = parser.parse_args()
process = json.loads((ROOT/'output/profiles/cube_0.20.json').read_text())
process.update({'name':'myAI Cube v3 AMS 0.20mm', 'print_settings_id':'myAI Cube v3 AMS 0.20mm',
                'enable_prime_tower':'1', 'prime_tower_width':'35',
                'flush_into_infill':'0', 'flush_into_objects':'0', 'flush_into_support':'0'})
(OUT/'profiles/process.json').write_text(json.dumps(process,indent=2)+'\n')
mono_process = dict(process, enable_prime_tower='0')
(OUT/'profiles/process_white.json').write_text(json.dumps(mono_process,indent=2)+'\n')
for color in P['colors']:
    data=json.loads((ROOT/'output/profiles/pla_white.json').read_text())
    data.update({'name':'myAI PLA '+color['name'], 'from':'User',
                 'filament_settings_id':['myAI PLA '+color['name']], 'filament_colour':[color['hex']]})
    (OUT/'profiles'/f'filament_{color["slot"]}.json').write_text(json.dumps(data,indent=2)+'\n')
for plate in args.plates:
    multicolor=plate in ('01_color_test','02_panel')
    scratch=ROOT/'output/logs'/('v3_'+plate)
    scratch.mkdir(parents=True,exist_ok=True)
    profile=OUT/'profiles'/('process.json' if multicolor else 'process_white.json')
    filaments=';'.join(str(OUT/'profiles'/f'filament_{i}.json') for i in range(1,5 if multicolor else 2))
    common=[str(args.bambu_studio),'--datadir',str(scratch/'config'),'--debug','2',
             '--load-settings',f'{ROOT/"output/profiles/p1s_0.4.json"};{profile}',
             '--load-filaments',filaments,'--arrange','0','--orient','0']
    source=OUT/'geometry'/f'{plate}.3mf'
    if multicolor:
        # Let Bambu create its own complete native multipart structure first.
        # Assign extruders to the resulting parts, then slice that project.
        with (scratch/'convert.log').open('w') as log:
            subprocess.run(common+['--export-3mf','native.3mf','--outputdir',str(scratch),str(source)],
                           cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        with zipfile.ZipFile(scratch/'native.3mf') as archive:
            payload={n:archive.read(n) for n in archive.namelist()}
        config=ET.fromstring(payload['Metadata/model_settings.config'])
        parts=config.findall('object/part')
        assert len(parts)==4
        for slot,part in enumerate(parts,1):
            metadata = {el.get('key'): el.get('value') for el in part.findall('metadata')}
            assert metadata['source_volume_id'] == str(slot - 1), 'Unexpected native part ordering'
            for el in part.findall('metadata'):
                if el.get('key')=='name':el.set('value',P['colors'][slot-1]['name'])
            extruder = part.find("metadata[@key='extruder']")
            if extruder is None:
                extruder = ET.SubElement(part,'metadata',{'key':'extruder'})
            extruder.set('value', str(slot))
        payload['Metadata/model_settings.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
        settings=json.loads(payload['Metadata/project_settings.config'])
        settings.update({'flush_volumes_vector':['140']*8,
                         'flush_volumes_matrix':['0' if i==j else ('650' if j==0 else '450') for i in range(4) for j in range(4)],
                         'wipe_tower_x':['205'],'wipe_tower_y':['170']})
        payload['Metadata/project_settings.config']=json.dumps(settings).encode()
        source=scratch/'assigned.3mf'
        with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
            for name,data in payload.items():archive.writestr(name,data)
    command=common+['--slice','0','--export-3mf',plate+'_P1S.3mf','--outputdir',str(scratch),str(source)]
    with (scratch/'slicer.log').open('w') as log:
        subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    result=json.loads((scratch/'result.json').read_text())
    assert result['return_code']==0
    shutil.copyfile(scratch/(plate+'_P1S.3mf'),OUT/'print'/(plate+'_P1S.3mf'))
    (OUT/'print'/(plate+'_slicer_result.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(plate, result['sliced_plates'][0]['filament_change_times'], 'color changes', flush=True)
