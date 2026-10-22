"""Capture actual UE landing views after runtime validation; no asset changes."""
import unreal as u
import time,json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert ed.get_editor_world().get_name()=='TownLayout_07' and not ed.get_game_world()
u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
views=[('expansion07_board.png',(-240,-3020,420),(260,-3450,290)),('expansion07_footing.png',(-60,-3220,210),(260,-3450,132)),('expansion07_pavilion_inside.png',(-960,-4450,310),(-1350,-4450,320))]
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle=perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
state={'stage':'set','i':0,'started':time.monotonic()}
def tick(dt):
 try:
  if time.monotonic()-state['started']>360: raise RuntimeError('Viewport capture timed out; check editor visibility')
  i=state['i'];name,loc,target=views[i]
  if ed.get_game_world():return
  runtime=json.loads((root/'expansion07_runtime.json').read_text())
  if runtime['status']=='running':return
  assert runtime['status']=='passed',runtime
  if state['stage']=='set':
   v=u.Vector(*loc);ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));state.update(stage='wait',t=time.monotonic())
  elif state['stage']=='wait' and time.monotonic()-state['t']>7:
   state['task']=u.AutomationLibrary.take_high_res_screenshot(1280,720,str(root/'Validation'/name));state.update(stage='shot',t=time.monotonic())
  elif state['stage']=='shot' and state['task'].is_task_done() and time.monotonic()-state['t']>7:
   if i+1<len(views):state.update(i=i+1,stage='set')
   else:
    (root/'expansion07_capture.json').write_text(json.dumps({'status':'captured_pending_visual_review','files':[v[0] for v in views]}));perf.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle);u.unregister_slate_post_tick_callback(landing_preview_handle)
 except Exception:
  (root/'expansion07_capture.json').write_text(json.dumps({'status':'error','error':traceback.format_exc()}));perf.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle);u.unregister_slate_post_tick_callback(landing_preview_handle)
import runpy
runpy.run_path(str(root/'Tools/test_expansion07.py'))
landing_preview_handle=u.register_slate_post_tick_callback(tick)
