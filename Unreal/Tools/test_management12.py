"""Run the established economy/save regression with the live worker controller enabled."""
from pathlib import Path
source=Path(__file__).with_name('test_management10.py')
code=source.read_text(encoding='utf-8').replace('/Game/Maps/TownLayout_10','/Game/Maps/TownLayout_12').replace("root/'management10_runtime.json'","root/'management12_runtime.json'").replace('NPCs are static blockout figures','NPCs use blockout geometry with local camp travel')
exec(compile(code,str(source),'exec'),globals())
