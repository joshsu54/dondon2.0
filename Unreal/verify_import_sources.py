"""Check the first UE import batch without starting or modifying Unreal."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify():
    manifest = json.loads((ROOT / 'Unreal/import_manifest.json').read_text())
    errors = []
    checked = 0
    for item in manifest['assets']:
        path = (ROOT / item['source']).resolve()
        if not path.is_relative_to(ROOT):
            errors.append(f"Source outside repository: {item['id']}")
            continue
        if not path.is_file():
            errors.append(f"Missing source: {item['source']}")
            continue
        data = path.read_bytes()
        if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            errors.append(f"LFS pointer, run git lfs pull: {item['source']}")
        elif hashlib.sha256(data).hexdigest() != item['sha256']:
            errors.append(f"Source changed since preparation: {item['source']}")
        elif len(data) != item['size_bytes']:
            errors.append(f"Incorrect size: {item['source']}")
        else:
            checked += 1
    print(json.dumps({'sources_verified': checked, 'errors': errors,
                     'unreal_import_verified': False,
                     'scope': 'Source files only; no Unreal runtime or collision test.'},
                    ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(verify())
