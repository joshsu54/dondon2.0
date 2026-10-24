"""Open TownLayout_08 (or TOWN_PIE_MAP), run test_expansion08 (real PIE), then capture editor views once it passed. No asset changes.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import time,json,traceback,runpy
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
import os
MAP=os.environ.get('TOWN_PIE_MAP','TownLayout_08');N=MAP[-2:]  # TOWN_PIE_NO_CAPTURE=1: PIE only, then quit
NO_CAPTURE=bool(os.environ.get('TOWN_PIE_NO_CAPTURE'))
u.EditorPythonScripting.set_keep_python_script_alive(True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/'+MAP)
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert ed.get_editor_world().get_name()==MAP and not ed.get_game_world()
u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
views=[(f'expansion{N}_south_overview.png',(0,8200,2100),(0,2400,150)),(f'expansion{N}_south_meadow.png',(400,6600,260),(-1700,3000,260)),
       (f'expansion{N}_east_bamboo.png',(2700,3000,450),(3100,-900,250)),(f'expansion{N}_west_strip.png',(-1900,1400,650),(-2950,-1900,150)),
       (f'expansion{N}_board.png',(-240,-3020,420),(260,-3450,290)),(f'expansion{N}_top.png',(0,1200,9500),(0,1150,0))]
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
state={'stage':'testing','i':0,'started':time.monotonic()}
cap=root/('expansion08_capture.json' if N=='08' else f'expansion{N}_pie_review.json')  # 09's capture.json holds the inn views
def done(result):
 cap.write_text(json.dumps(result,indent=2));perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
 u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
 try:
  now=time.monotonic()
  if now-state['started']>900:raise RuntimeError('Review timed out')
  if ed.get_game_world():return
  runtime=json.loads((root/f'expansion{N}_runtime.json').read_text())
  if runtime['status']=='running':return
  if runtime['status']!='passed':done({'status':'runtime_failed','runtime_status':runtime['status']});return
  if NO_CAPTURE:done({'status':'pie_passed_no_capture','map':MAP});return
  name,loc,target=views[state['i']]
  if state['stage']=='testing':state['stage']='set'
  if state['stage']=='set':
   v=u.Vector(*loc);ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));state.update(stage='wait',t=now)
  elif state['stage']=='wait' and now-state['t']>6:
   state['task']=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(root/'Validation'/name));state.update(stage='shot',t=now)
  elif state['stage']=='shot' and state['task'].is_task_done() and now-state['t']>4:
   if state['i']+1<len(views):state.update(i=state['i']+1,stage='set')
   else:done({'status':'captured_pending_visual_review','files':['Validation/'+v[0] for v in views],'missing':[ 'Validation/'+v[0] for v in views if not (root/'Validation'/v[0]).exists()]})
 except Exception:
  done({'status':'error','error':traceback.format_exc()})
# Start the test at top level (as review_expansion07 does); from a tick callback get_editor_world() returned None.
runpy.run_path(str(root/'Tools/test_expansion08.py'))
handle=u.register_slate_post_tick_callback(tick)
