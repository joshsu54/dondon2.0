"""Create an isolated Blueprint project from the locally installed Epic template."""
import argparse
import json
import shutil
import uuid
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--engine', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
dest = root / 'Unreal/XiuXianTown'
if dest.exists():
    raise SystemExit('Project already exists; refusing to overwrite it.')
template = args.engine / 'Templates/TP_ThirdPersonBP'
packs = args.engine / 'Templates/TemplateResources/High'
for p in [template, *(packs / n / 'Content' for n in ('Characters', 'Input', 'LevelPrototyping'))]:
    if not p.is_dir():
        raise SystemExit(f'Missing installed template content: {p}')
dest.mkdir()
shutil.copytree(template / 'Content', dest / 'Content')
(dest / 'Config').mkdir()
for p in (template / 'Config').glob('Default*.ini'):
    text = p.read_text(encoding='utf-8-sig').replace('TP_ThirdPersonBP', 'XiuXianTown')
    (dest / 'Config' / p.name).write_text(text)
for name in ('Characters', 'Input', 'LevelPrototyping'):
    shutil.copytree(packs / name / 'Content', dest / 'Content' / name)
project = json.loads((template / 'TP_ThirdPersonBP.uproject').read_text())
project.update(EngineAssociation='5.8', Description='XiuXian town movement prototype', Category='Games')
project['Plugins'] += [{'Name': n, 'Enabled': True, 'TargetAllowList': ['Editor']} for n in ('PythonScriptPlugin', 'EditorScriptingUtilities')]
(dest / 'XiuXianTown.uproject').write_text(json.dumps(project, indent=2) + '\n')
(dest / 'Config/DefaultGame.ini').write_text(f'[/Script/EngineSettings.GeneralProjectSettings]\nProjectID={uuid.uuid4().hex.upper()}\nProjectName=XiuXianTown\nProjectVersion=0.1.0\n')
p = dest / 'Config/DefaultEngine.ini'
s = p.read_text().replace('r.ReflectionMethod=1', 'r.ReflectionMethod=2').replace('r.GenerateMeshDistanceFields=True','r.GenerateMeshDistanceFields=False').replace('r.DynamicGlobalIlluminationMethod=1','r.DynamicGlobalIlluminationMethod=0').replace('r.Shadow.Virtual.Enable=1','r.Shadow.Virtual.Enable=0')
p.write_text(s)
report = {'engine': json.loads((args.engine / 'Engine/Build/Build.version').read_text()), 'template': 'TP_ThirdPersonBP', 'shared_content': ['Characters', 'Input', 'LevelPrototyping'], 'status': 'created_not_yet_opened', 'project': 'Unreal/XiuXianTown/XiuXianTown.uproject'}
(root / 'Unreal/starter_creation.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'Created {dest}; preserved original Third Person test map.')
