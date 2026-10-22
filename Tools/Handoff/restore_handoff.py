"""Verify, restore and audit a split handoff bundle; Python 3.9+ standard library."""
import argparse
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def safe_name(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or not p.parts or p.parts[0] != 'dondon':
        raise ValueError(f'Unsafe archive path: {name}')
    return '/'.join(p.parts[1:])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--destination', type=Path, default=Path.cwd() / 'dondon-handoff')
    args = parser.parse_args()
    src, dst = args.bundle_dir.resolve(), args.destination.resolve()
    manifest = json.loads((src / 'handoff-manifest.json').read_text())
    if manifest['format'] != 1:
        raise ValueError('Unknown bundle format')
    if dst.exists() and any(dst.iterdir()):
        raise SystemExit('Destination must be empty; existing work is never overwritten.')
    expected = {r['path']: r for r in manifest['files']}
    if len(expected) != manifest['file_count']:
        raise ValueError('Duplicate manifest paths')
    for name in expected:
        if safe_name('dondon/' + name) != name:
            raise ValueError('Invalid manifest path')
    # Verify every compressed part before creating the output tree.
    for part in manifest['parts']:
        if Path(part['file']).name != part['file']:
            raise ValueError('Invalid part name')
        p = src / part['file']
        if p.stat().st_size != part['bytes'] or digest(p) != part['sha256']:
            raise ValueError(f'Corrupt part: {p.name}')
        print('PART_VERIFIED', p.name, flush=True)
    dst.mkdir(parents=True, exist_ok=True)
    extracted = set()
    with tempfile.TemporaryFile() as joined:
        for part in manifest['parts']:
            with (src / part['file']).open('rb') as f:
                shutil.copyfileobj(f, joined, 4 * 1024 * 1024)
        joined.seek(0)
        with tarfile.open(fileobj=joined, mode='r|gz') as archive:
            for member in archive:
                name = safe_name(member.name)
                if name not in expected or name in extracted:
                    raise ValueError(f'Unexpected archive member: {name}')
                target = dst / name
                target.parent.mkdir(parents=True, exist_ok=True)
                if member.islnk():
                    original = safe_name(member.linkname)
                    if original not in extracted:
                        raise ValueError('Hardlink target not yet restored')
                    # Independent copies avoid editing one duplicate changing another.
                    shutil.copyfile(dst / original, target)
                elif member.isfile():
                    with archive.extractfile(member) as f, target.open('xb') as output:
                        shutil.copyfileobj(f, output, 4 * 1024 * 1024)
                else:
                    raise ValueError('Only regular files and internal duplicate references are allowed')
                os.chmod(target, expected[name]['mode'] & 0o777)
                extracted.add(name)
                if len(extracted) % 200 == 0:
                    print('RESTORED', len(extracted), '/', len(expected), flush=True)
    if extracted != set(expected):
        raise ValueError('Incomplete archive')
    for name, row in expected.items():
        p = dst / name
        if p.stat().st_size != row['bytes'] or digest(p) != row['sha256']:
            raise ValueError(f'Restored content mismatch: {name}')
    print('RESTORE_VERIFIED', len(extracted), 'files; commit', manifest['source_commit'])
    print('Next: cd', dst, '; python3 Tools/Handoff/verify_project.py')

if __name__ == '__main__':
    main()
