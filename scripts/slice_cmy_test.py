"""Slice CMY card with resolved official P1S/Bambu PLA Basic presets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/cmy_calibration'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bambu_studio',type=Path)
    parser.add_argument('resources',type=Path,help='Official resources/profiles/BBL directory')
    args=parser.parse_args()
    index={}
    for path in args.resources.rglob('*.json'):
        data=json.loads(path.read_text())
        if 'name' in data:index[data['name']]=(data,path)
        index.setdefault(path.stem,(data,path))
    used={}
    def resolve(name,stack=()):
        assert name not in stack
        data,path=index[name]
        used[str(path.relative_to(args.resources))]=hashlib.sha256(path.read_bytes()).hexdigest()
        merged=resolve(data['inherits'],(*stack,name)) if data.get('inherits') else {}
        for item in data.get('include',[]):merged.update(resolve(item,(*stack,name)))
        merged.update(data)
        merged.pop('inherits',None);merged.pop('include',None)
        return merged
    card=json.loads((OUT/'geometry_validation.json').read_text())
    plate=card['plate_name']
    for name in ('print_validation.json',f'print/{plate}_P1S.3mf','print/slicer_result.json'):
        (OUT/name).unlink(missing_ok=True)
    (OUT/'print/STATUS.md').write_text('Slicing gestartet; keine Druckfreigabe vor Flächenprüfung.\n')
    machine=resolve('Bambu Lab P1S 0.4 nozzle')
    assert len(machine['machine_start_gcode'])>1000 and len(machine['machine_end_gcode'])>100
    (OUT/'profiles/machine.json').write_text(json.dumps(machine,indent=2)+'\n')
    process=json.loads((ROOT/'output/multicolor_v4_2/profiles/process_raster_original.json').read_text())
    process.update(json.loads((ROOT/'cad/cmy_process.json').read_text()))
    process.update(name='myAI CMY 0.10mm P1S',print_settings_id='myAI CMY 0.10mm P1S')
    (OUT/'profiles/process.json').write_text(json.dumps(process,indent=2)+'\n')
    filament=resolve('Bambu PLA Basic @BBL P1S 0.4 nozzle')
    # Bundled presets hold Standard/High-Flow pairs. P1S has one Standard hotend;
    # retaining both makes CLI concatenate eight entries for four filaments.
    assert filament['filament_extruder_variant'][0]=='Direct Drive Standard'
    normalized=[]
    for key,value in list(filament.items()):
        if isinstance(value,list) and len(value)==2 and not key.startswith('filament_dev_ams_'):
            filament[key]=[value[0]]
            normalized.append(key)
    for color in card['palette']:
        name='myAI CMY Bambu PLA Basic '+color['name']
        data={**filament,'name':name,'from':'User','filament_settings_id':[name],
              'filament_colour':[color['hex']], 'additional_cooling_fan_speed':['0'],
              'fan_min_speed':['50'],'fan_max_speed':['50'],'close_fan_the_first_x_layers':['2']}
        (OUT/'profiles'/f'filament_{color["slot"]}.json').write_text(json.dumps(data,indent=2)+'\n')
    (OUT/'profiles/provenance.json').write_text(json.dumps({'official_resource_sha256':used,
        'filament_source':'Bambu PLA Basic @BBL P1S 0.4 nozzle',
        'standard_hotend_selected_for':normalized,
        'filament_overrides':'Names, colors, 50% part fan after two layers, auxiliary fan off; manufacturer Standard hotend values retained.',
        'machine_gcode':'Unmodified resolved official P1S start/end G-code'},indent=2)+'\n')
    scratch=ROOT/'output/logs/cmy_calibration'
    scratch.mkdir(parents=True,exist_ok=True)
    common=[str(args.bambu_studio.resolve()),'--datadir',str(scratch/'config'),'--debug','2',
        '--load-settings',f'{OUT/"profiles/machine.json"};{OUT/"profiles/process.json"}',
        '--load-filaments',';'.join(str(OUT/'profiles'/f'filament_{i}.json') for i in range(1,5)),
        '--arrange','0','--orient','0']
    with (scratch/'convert.log').open('w') as log:
        subprocess.run(common+['--export-3mf','native.3mf','--outputdir',str(scratch),
            str(OUT/'geometry'/f'{plate}.3mf')],cwd=scratch,stdout=log,stderr=subprocess.STDOUT,check=True)
    with zipfile.ZipFile(scratch/'native.3mf') as archive:
        payload={n:archive.read(n) for n in archive.namelist()}
    config=ET.fromstring(payload['Metadata/model_settings.config'])
    part_overrides=json.loads((ROOT/'cad/cmy_part_settings.json').read_text())
    parts=config.findall('object/part')
    assert len(parts)==4
    for slot,part in enumerate(parts,1):
        meta={el.get('key'):el.get('value') for el in part.findall('metadata')}
        assert meta['source_volume_id']==str(slot-1)
        for el in part.findall('metadata'):
            if el.get('key')=='name':el.set('value',card['palette'][slot-1]['name'])
        extruder=part.find("metadata[@key='extruder']")
        if extruder is None:extruder=ET.SubElement(part,'metadata',{'key':'extruder'})
        extruder.set('value',str(slot))
        for key,value in part_overrides.get(str(slot),{}).items():
            setting=part.find(f"metadata[@key='{key}']")
            if setting is None:setting=ET.SubElement(part,'metadata',{'key':key})
            setting.set('value',value)
    payload['Metadata/model_settings.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
    settings=json.loads(payload['Metadata/project_settings.config'])
    settings.update(flush_volumes_vector=['140']*8,
        flush_volumes_matrix=['0' if i==j else ('650' if j==0 else '450') for i in range(4) for j in range(4)],
        wipe_tower_x=['175'],wipe_tower_y=['40'])
    payload['Metadata/project_settings.config']=json.dumps(settings).encode()
    source=scratch/'assigned.3mf'
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in payload.items():archive.writestr(name,data)
    output_name=f'{plate}_P1S.3mf'
    with (scratch/'slicer.log').open('w') as log:
        subprocess.run(common+['--slice','0','--export-3mf',output_name,'--outputdir',str(scratch),str(source)],
            cwd=scratch,stdout=log,stderr=subprocess.STDOUT,check=True)
    result=json.loads((scratch/'result.json').read_text())
    assert result['return_code']==0
    shutil.copyfile(scratch/output_name,OUT/'print'/output_name)
    (OUT/'print/slicer_result.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'print/STATUS.md').write_text('Geslict; Flächenprüfung noch ausstehend.\n')
    print(json.dumps(result['sliced_plates'],indent=2))


if __name__=='__main__':main()
