"""Reload TownLayout_03 and rerun eight PIE cases without mutating assets."""
import unreal as u
import runpy
from pathlib import Path
u.EditorPythonScripting.set_keep_python_script_alive(True)
runpy.run_path(str(Path(u.Paths.project_dir()).resolve().parent/'Tools/test_town_routes.py'))
