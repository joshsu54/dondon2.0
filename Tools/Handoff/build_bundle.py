"""Pack a clean Git snapshot with real LFS files and deduplicated tar members."""
import argparse
import gzip
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

class Parts:
    def __init__(self, out, limit):
        self.out, self.limit = out, limit
        self.parts = []
        self.file = None
        self.size = 0
        self.total = 0
    def write(self, data):
        original = len(data)
        data = memoryview(data)
        while data:
            if self.file is None:
                name = f'dondon-handoff.tar.gz.part{len(self.parts)+1:03d}'
                self.file = (self.out / name).open('xb')
                self.parts.append({'file': name})
                self.size = 0
                self.hash = hashlib.sha256()
            count = min(len(data), self.limit - self.size)
            chunk = data[:count]
            self.file.write(chunk)
            self.hash.update(chunk)
            self.size += count
            self.total += count
            data = data[count:]
            if self.size == self.limit:
                self.close_part()
        return original
    def close_part(self):
        if self.file:
            self.file.close()
            self.parts[-1].update(bytes=self.size, sha256=self.hash.hexdigest())
            print('PART_COMPLETE', self.parts[-1]['file'], self.size, flush=True)
            self.file = None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--part-mb', type=int, default=700)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit('Output directory must be empty.')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise SystemExit('Commit the snapshot before packaging.')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    names = sorted(p.decode() for p in subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).split(b'\0') if p)
    writer = Parts(out, args.part_mb * 1000000)
    records, first = [], {}
    with gzip.GzipFile(fileobj=writer, mode='wb', compresslevel=3, mtime=0) as compressed, tarfile.open(fileobj=compressed, mode='w|', format=tarfile.PAX_FORMAT) as archive:
        for index, name in enumerate(names):
            p = ROOT / name
            if not p.is_file() or p.is_symlink():
                raise ValueError(f'Unsupported file type: {name}')
            with p.open('rb') as f:
                if f.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError(f'LFS data missing: {name}')
            sha = digest(p)
            size = p.stat().st_size
            mode = p.stat().st_mode & 0o777
            member = tarfile.TarInfo('dondon/' + name)
            member.mode = mode
            member.mtime = 0
            record = {'path': name, 'bytes': size, 'sha256': sha, 'mode': mode}
            if sha in first:
                member.type = tarfile.LNKTYPE
                member.linkname = first[sha]
                archive.addfile(member)
            else:
                member.size = size
                with p.open('rb') as f:
                    archive.addfile(member, f)
                first[sha] = member.name
            records.append(record)
            if index % 200 == 0:
                print('PACKED', index + 1, '/', len(names), flush=True)
    writer.close_part()
    manifest = {'format': 1, 'repository': 'https://github.com/joshsu54/dondon',
                'branch': 'solid-clouds-karst-peaks', 'source_commit': commit,
                'file_count': len(records), 'restored_bytes': sum(r['bytes'] for r in records),
                'unique_contents': len(first), 'archive_bytes': writer.total,
                'parts': writer.parts, 'files': records}
    (out / 'handoff-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print('BUNDLE_COMPLETE', len(records), writer.total, commit, flush=True)

if __name__ == '__main__':
    main()
