"""Saved-map PIE validation and actual UE captures. Temporarily enable background rendering."""
import unreal as u
import runpy, time, json, traceback
from pathlib import Path
u.EditorPythonScripting.set_keep_python_script_alive(True)
root=Path(u.Paths.project_dir()).resolve().parent
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle=perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
status={'phase':'routes','started':time.monotonic()}
out=root/'town03_pipeline.json'
initial_capture_mtime=(root/'town03_capture_status.json').stat().st_mtime if (root/'town03_capture_status.json').exists() else 0
def write(): out.write_text(json.dumps(status,indent=2))
def done():
 perf.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
 u.unregister_slate_post_tick_callback(validation_handle)
def tick(dt):
 try:
  if time.monotonic()-status['started']>360: raise RuntimeError('Validation timeout')
  if status['phase']=='routes':
   report=json.loads((root/'town_routes_TownLayout_03.json').read_text())
   if report['status']!='running' and not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world():
    status.update(phase='capture',route_status=report['status']);write()
    runpy.run_path(str(root/'Tools/preview_town03_landing.py'))
  elif status['phase']=='capture':
   p=root/'town03_capture_status.json'
   if p.exists() and p.stat().st_mtime>initial_capture_mtime:
    report=json.loads(p.read_text());status.update(phase=report['status']);write();done()
 except Exception:
  status.update(phase='error',error=traceback.format_exc());write();done()
runpy.run_path(str(root/'Tools/test_town_routes.py'))
write()
validation_handle=u.register_slate_post_tick_callback(tick)
