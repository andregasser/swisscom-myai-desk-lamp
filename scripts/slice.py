"""Slice every prepared plate using official Bambu Studio CLI (no printer I/O)."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('bambu_studio', type=Path)
parser.add_argument('--plates', nargs='+', default=['01_tests', '02_body', '03_base', '04_lid'])
args = parser.parse_args()
profiles = root / 'output/profiles'
printdir = root / 'output/print'
printdir.mkdir(exist_ok=True)
for plate in args.plates:
    scratch = root / 'output/logs' / plate
    scratch.mkdir(parents=True, exist_ok=True)
    command = [str(args.bambu_studio), '--datadir', str(scratch / 'config'), '--debug', '2',
               '--load-settings', f'{profiles / "p1s_0.4.json"};{profiles / "cube_0.20.json"}',
               '--load-filaments', str(profiles / 'pla_white.json'),
               '--arrange', '0', '--orient', '0', '--slice', '0',
               '--export-3mf', plate + '_P1S.3mf',
               '--outputdir', str(scratch), str(root / 'output/3mf' / (plate + '_geometry.3mf'))]
    with (scratch / 'slicer.log').open('w') as log:
        subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
    shutil.copyfile(scratch / (plate + '_P1S.3mf'), printdir / (plate + '_P1S.3mf'))
    result = json.loads((scratch / 'result.json').read_text())
    (printdir / (plate + '_slicer_result.json')).write_text(json.dumps(result, indent=2) + '\n')
    print('Sliced:', plate, flush=True)
