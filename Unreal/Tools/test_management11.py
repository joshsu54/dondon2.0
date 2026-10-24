"""Run the established management regression on the new terrain map with a separate report."""
from pathlib import Path
source=Path(__file__).with_name('test_management10.py')
code=source.read_text(encoding='utf-8').replace('/Game/Maps/TownLayout_10','/Game/Maps/TownLayout_11').replace("root/'management10_runtime.json'","root/'management11_runtime.json'")
exec(compile(code,str(source),'exec'),globals())
