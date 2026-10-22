"""Capture actual UE landing views after runtime validation; no asset changes."""
import unreal as u
import time,json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert ed.get_editor_world().get_name()=='TownLayout_03' and not ed.get_game_world()
u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
views=[('town03_landing_from_stairs.png',(-1874,-1950,560),(-1874,-2250,620)),('town03_landing_above.png',(-1740,-2180,695),(-1860,-2020,510))]
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle=perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
state={'stage':'set','i':0,'started':time.monotonic()}
def tick(dt):
 try:
  if time.monotonic()-state['started']>90: raise RuntimeError('Viewport capture timed out; check editor visibility')
  i=state['i'];name,loc,target=views[i]
  if state['stage']=='set':
   v=u.Vector(*loc);ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));state.update(stage='wait',t=time.monotonic())
  elif state['stage']=='wait' and time.monotonic()-state['t']>7:
   state['task']=u.AutomationLibrary.take_high_res_screenshot(1280,720,str(root/'Validation'/name));state.update(stage='shot',t=time.monotonic())
  elif state['stage']=='shot' and state['task'].is_task_done() and time.monotonic()-state['t']>7:
   if i+1<len(views):state.update(i=i+1,stage='set')
   else:
    (root/'town03_capture_status.json').write_text(json.dumps({'status':'captured_pending_visual_review','files':[v[0] for v in views]}));perf.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle);u.unregister_slate_post_tick_callback(landing_preview_handle)
 except Exception:
  (root/'town03_capture_status.json').write_text(json.dumps({'status':'error','error':traceback.format_exc()}));perf.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle);u.unregister_slate_post_tick_callback(landing_preview_handle)
landing_preview_handle=u.register_slate_post_tick_callback(tick)
