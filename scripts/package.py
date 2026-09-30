"""Bundle the print projects, editable sources and instructions, without caches."""
from pathlib import Path
import hashlib
import zipfile

root = Path(__file__).resolve().parents[1]
name = 'myAI_Cube_150_P1S_AMS_v3_2'
target = root / 'output' / (name + '.zip')
files = [root / 'README.md', root / '.gitignore']
for folder in ('assets', 'cad', 'docs', 'scripts', 'output/stl', 'output/3mf',
               'output/print', 'output/profiles', 'output/preview', 'output/multicolor_v3'):
    files.extend(p for p in (root / folder).rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts)
files.extend(root / 'output' / n for n in ('validation.json', 'print_validation.json'))
checksums = []
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for file in sorted(files):
        relative = file.relative_to(root).as_posix()
        archive.write(file, name + '/' + relative)
        checksums.append(hashlib.sha256(file.read_bytes()).hexdigest() + '  ' + relative)
    archive.writestr(name + '/SHA256SUMS.txt', '\n'.join(checksums) + '\n')
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    for entry in checksums:
        digest, relative = entry.split('  ', 1)
        assert hashlib.sha256(archive.read(name + '/' + relative)).hexdigest() == digest
print(target, f'({target.stat().st_size / 1e6:.2f} MB; {len(files)} files, checksums verified)')
