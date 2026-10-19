"""Reproduce or inspect profile-only gap trials; never release a failed test."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from validate_raster_coverage import analyze
from validate_raster_test import model_segments

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/line_gradient_full'
OUT=ROOT/'output/line_gradient_gap_audit'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(out, recipe):
    card=json.loads((out/'geometry_validation.json').read_text())
    original=json.loads((BASE/'geometry_validation.json').read_text())
    assert card==original
    meshes={str(s):digest(out/'stl'/f'slot_{s}.stl') for s in range(1,5)}
    assert meshes=={str(s):digest(BASE/'stl'/f'slot_{s}.stl') for s in range(1,5)}
    file=out/'print/13_full_line_test_P1S.3mf'
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        config=json.loads(archive.read('Metadata/project_settings.config'))
        raw=archive.read('Metadata/plate_1.gcode')
        assert hashlib.md5(raw).hexdigest()==archive.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    assert config['printer_model']=='Bambu Lab P1S' and config['nozzle_diameter']==['0.4']
    assert config['filament_colour']==[c['hex'] for c in card['palette']]
    assert config['filament_type']==['PLA']*4
    assert config['enable_support']=='0' and config['enable_prime_tower']=='1'
    assert config['curr_bed_type']=='Textured PEI Plate'
    assert config['nozzle_temperature']==['220']*4
    for key in ('flush_into_infill','flush_into_objects','flush_into_support'):
        assert config[key]=='0'
    applied={k:config.get(k) for k in recipe['process']}
    assert applied==recipe['process'],(recipe['name'],applied)
    assert [float(config[k][0]) for k in ('wipe_tower_x','wipe_tower_y')]==recipe['tower_position_mm']
    code=raw.decode()
    assert 'FEATURE: Support' not in code
    layers=defaultdict(set)
    for z,slot,a,b,width in model_segments(code,config):
        layers[z].add(slot)
    thin=config['layer_height']=='0.1'
    expected={.2:{1},.4:{1},.6:{1,2,3,4}}
    if thin:
        expected.update({.3:{1},.5:{1,2,3,4}})
    assert dict(layers)==expected
    # Model, brim and prime-tower extrusion must stay on the P1S bed.
    feature='Custom';changing=False;x=y=z=0.;points=[]
    for line in code.splitlines():
        if re.match(r'M620 S\d+',line):changing=True
        if line.startswith('M621 '):changing=False
        if line.startswith('; FEATURE: '):feature=line.removeprefix('; FEATURE: ')
        if not re.match(r'^G[0123] ',line):continue
        fields={k:float(v) for k,v in re.findall(r'\b([XYZE])(-?\d*\.?\d+)',line)}
        x,y,z=fields.get('X',x),fields.get('Y',y),fields.get('Z',z)
        if changing or feature=='Custom' or fields.get('E',0)<=0 or not ('X' in fields or 'Y' in fields):continue
        assert 0<=x<=256 and 0<=y<=256 and 0<=z<=250
        assert not (x<18.25 and y<28.25)
        points.append((x,y,z))
    assert points
    result=json.loads((out/'print/slicer_result.json').read_text())
    assert result['return_code']==0
    plate=result['sliced_plates'][0]
    assert not plate['warning_message']
    # The slicer reverses the color order on the second ink layer, avoiding
    # a redundant switch between those two layers.
    assert plate['filament_change_times']==(6 if thin else 3)
    coverage={}
    for layer in ((.5,.6) if thin else (.6,)):
        options={'color_layer_height':.1,'backing_layers':((.2,.2),(.3,.1),(.4,.1))} if thin else {}
        prefix=out/('checked_layer_'+str(layer).replace('.','p'))
        coverage[str(layer)]=analyze(file,'',layer,prefix,
                                    output_root=out,palette=card['palette'],**options)
    return {'sliced_successfully':True,'requested_options_verified':True,
            'print_sha256':digest(file),'gcode_sha256':hashlib.sha256(raw).hexdigest(),
            'mesh_sha256_by_slot':meshes,'material_geometry_unchanged':True,
            'input_process':json.loads((out/'profiles/process.json').read_text()),
            'verified_options_in_export':applied,
            'color_changes':plate['filament_change_times'],
            'estimated_minutes':round(plate['total_predication']/60,1),
            'coverage_by_color_layer':coverage,
            'digital_coverage_passed':all(c['digital_coverage_passed'] for c in coverage.values()),
            'physical_print_verified':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bambu-studio',type=Path)
    parser.add_argument('--workdir',type=Path,default=ROOT/'output/logs/line_gap_audit')
    parser.add_argument('--inspect-existing',action='store_true')
    parser.add_argument('--allow-withheld',action='store_true',help='Audit only, never print approval')
    args=parser.parse_args()
    assert args.inspect_existing or args.bambu_studio,'Specify the local slicer or inspect existing trials'
    manifest=json.loads((ROOT/'cad/line_gap_trials.json').read_text())
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'trials.json').unlink(missing_ok=True)
    (OUT/'STATUS.md').write_text('# Lückenschluss-Prüfung\n\nPrüfung läuft; keine neue Druckfreigabe.\n')
    records=[]
    for recipe in manifest['trials']:
        out=args.workdir.resolve()/recipe['name']
        if not args.inspect_existing:
            shutil.copytree(BASE,out,dirs_exist_ok=True)
            (out/'profile_trials.json').unlink(missing_ok=True)
            override=out/'override.json'
            override.write_text(json.dumps(recipe['process'],indent=2)+'\n')
            with (out/'run.log').open('w') as log:
                command=[sys.executable,str(ROOT/'scripts/slice_line_gradient_test.py'),str(args.bambu_studio.resolve()),
                         '--output',str(out),'--process',str(override),'--tower-position',*[str(v) for v in recipe['tower_position_mm']]]
                subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
        record={'name':recipe['name'],'requested_process':recipe['process'],**inspect(out,recipe)}
        records.append(record)
        print(recipe['name'],record['digital_coverage_passed'],flush=True)
    report={'slicer_version':'02.08.02.61','basis_print_sha256':digest(BASE/'print/13_full_line_test_P1S.3mf'),
            'source_preview_sha256':digest(ROOT/'design_studies/line_gradient_full/proposal.svg'),
            'manifest_sha256':digest(ROOT/'cad/line_gap_trials.json'),
            'coverage_analyzer_sha256':digest(ROOT/'scripts/validate_raster_coverage.py'),
            'acceptance_thresholds_unchanged':True,'trials':records,
            'passing_trials':[r['name'] for r in records if r['digital_coverage_passed']],
            'physical_print_verified':False}
    (OUT/'trials.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'STATUS.md').write_text(
        '# Lückenschluss-Prüfung\n\n'+
        ('Digitale Kandidaten vorhanden; noch keine physische Bestätigung.\n\n' if report['passing_trials'] else
         '**Keine neue Druckfreigabe.** Keine der geprüften Profileinstellungen besteht die vollständige Flächenprüfung.\n\n')+
        f'{len(records)} Profile an identischen Farbvolumen geprüft; P1S mit 0,4-mm-Düse. '
        'Gerade Streifen, keine neue Farbzuordnung. Grenzwerte unverändert.\n\n'+
        '[Prüfberichte](trials.json) · [Erklärung](../../docs/LUECKENSCHLUSS_PRUEFUNG.md)\n')
    if not report['passing_trials'] and not args.allow_withheld:
        raise SystemExit('FAIL: Keine geprüfte Einstellung schliesst die Farbflächen ausreichend; keine neue Druckfreigabe.')


if __name__=='__main__':main()
