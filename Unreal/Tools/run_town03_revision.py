"""Run saved-map revision, real PIE routes and editor captures in a fresh editor."""
import unreal as u
import runpy, time, json, traceback
from pathlib import Path
u.EditorPythonScripting.set_keep_python_script_alive(True)
_pipeline_root = Path(u.Paths.project_dir()).resolve().parent
_pipeline_status = _pipeline_root / 'town03_pipeline.json'
_pipeline = {'phase':'fix', 'started':time.monotonic()}
def _pipeline_write(**values):
    _pipeline.update(values)
    _pipeline_status.write_text(json.dumps(_pipeline, indent=2))
try:
    runpy.run_path(str(_pipeline_root/'Tools/fix_inn_landing.py'))
    runpy.run_path(str(_pipeline_root/'Tools/test_town_routes.py'))
    _pipeline_write(phase='routes')
except Exception:
    _pipeline_write(phase='error', error=traceback.format_exc())
def _pipeline_tick(dt):
    try:
        if _pipeline['phase'] in ('error','captured_pending_visual_review'):
            u.unregister_slate_post_tick_callback(_pipeline_handle); return
        if time.monotonic()-_pipeline['started']>360:
            raise RuntimeError('Pipeline timeout')
        if _pipeline['phase']=='routes':
            report=json.loads((_pipeline_root/'town_routes_TownLayout_03.json').read_text())
            if report['status']!='running' and not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world():
                _pipeline_write(phase='capture', route_status=report['status'])
                runpy.run_path(str(_pipeline_root/'Tools/preview_town03_landing.py'))
        elif _pipeline['phase']=='capture':
            p=_pipeline_root/'town03_capture_status.json'
            if p.exists():
                report=json.loads(p.read_text())
                _pipeline_write(phase=report['status'])
    except Exception:
        _pipeline_write(phase='error', error=traceback.format_exc())
_pipeline_handle=u.register_slate_post_tick_callback(_pipeline_tick)
