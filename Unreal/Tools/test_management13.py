"""Run the established economy/save regression on TownLayout_13 (QCharacters17 v006 player pawn: smaller capsule, 204 cm/s)."""
from pathlib import Path
source=Path(__file__).with_name('test_management10.py')
code=source.read_text(encoding='utf-8').replace('/Game/Maps/TownLayout_10','/Game/Maps/TownLayout_13').replace("root/'management10_runtime.json'","root/'management13_runtime.json'").replace('NPCs are static blockout figures','NPCs use blockout geometry with local camp travel; player pawn is the QCharacters17 v006 chibi')
exec(compile(code,str(source),'exec'),globals())
