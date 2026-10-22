"""Read-only integrity check; Python standard library only, no Blender required."""
import hashlib
import json
import struct
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[2]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src', 'poster') and value:
                u = urlsplit(value)
                if not u.scheme and not u.netloc and u.path:
                    self.paths.append(unquote(u.path))

def check():
    library = ROOT / 'ArtLibrary'
    catalog = json.loads((library / 'asset_catalog.json').read_text())
    errors = []
    total_views = 0
    assets = 0
    for entry in catalog['entries']:
        for field in ('blend', 'fbx'):
            path = library / entry[field]
            if not path.is_file():
                errors.append(f'Missing {path}')
            else:
                with path.open('rb') as f:
                    if f.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'):
                        errors.append(f'LFS pointer, run git lfs pull: {path}')
        views = entry.get('views', [])
        if not views:
            continue
        assets += 1
        total_views += len(views)
        if len(views) < 10 or len(set(views)) != len(views):
            errors.append(f'Insufficient or duplicate view paths: {entry["id"]}')
        for rel in views:
            p = library / rel
            if not p.is_file():
                errors.append(f'Missing view: {p}')
                continue
            with p.open('rb') as f:
                head = f.read(24)
            if head[:8] != b'\x89PNG\r\n\x1a\n' or len(head) != 24:
                errors.append(f'Not a real PNG (possibly LFS pointer): {p}')
            elif min(struct.unpack('>II', head[16:24])) < 1024:
                errors.append(f'View smaller than 1024 pixels: {p}')
    if assets != catalog['model_asset_sets'] or total_views != catalog['consistent_turnaround_images']:
        errors.append('Catalog totals disagree with entries')
    pages = [library / 'index.html'] + [library / p for p in catalog.get('supplemental_batches', [])]
    for page in pages:
        if not page.is_file():
            errors.append(f'Missing gallery: {page}')
            continue
        parser = Links()
        parser.feed(page.read_text())
        errors.extend(f'Broken link: {page} -> {p}' for p in parser.paths if not (page.parent / p).exists())
    verified = 0
    for batch in ('MountainWaters09', 'MountainWayside10'):
        b = library / 'ExpansionBatches' / batch
        for row in json.loads((b / 'validation.json').read_text()):
            aid = row['asset']
            for ext, key in (('.blend', 'blend_sha256'), ('.fbx', 'fbx_sha256')):
                for folder in (b, ROOT):
                    p = folder / 'Models' / aid / 'v001' / (aid + '_v001' + ext)
                    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != row[key]:
                        errors.append(f'Validated file changed or missing: {p}')
            verified += 1
    report = {'model_sets': assets, 'basic_view_images': total_views,
              'gallery_pages_checked': len(pages), 'recent_asset_hashes_checked': verified,
              'errors': errors,
              'note': 'Read-only file audit; does not replace Blender or Unreal testing. See HANDOFF.md for older index versions.'}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(check())
