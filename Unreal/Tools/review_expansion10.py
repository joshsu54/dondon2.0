"""Open TownLayout_10 (or TOWN_PIE_MAP), run test_expansion10 (real PIE), then capture editor views once it passed. No asset changes.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import time,json,traceback,runpy,os
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
u.EditorPythonScripting.set_keep_python_script_alive(True)
MAP=os.environ.get('TOWN_PIE_MAP','TownLayout_10');N=MAP[-2:]
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/'+MAP)
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert ed.get_editor_world().get_name()==MAP and not ed.get_game_world()
u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
views=[(f'expansion{N}_south_overview.png',(0,14500,4200),(0,1500,300)),(f'expansion{N}_camp.png',(1800,7600,700),(-300,4800,150)),
       (f'expansion{N}_dormitory.png',(-300,4300,320),(-1500,4700,200)),(f'expansion{N}_north_slope.png',(2600,-2600,900),(300,-6500,700)),
       (f'expansion{N}_town_ground.png',(1800,1600,900),(-400,-1600,150)),(f'expansion{N}_top.png',(0,800,22000),(0,700,0))]
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
state={'stage':'testing','i':0,'started':time.monotonic()};cap=root/f'expansion{N}_capture.json'
def done(result):
    cap.write_text(json.dumps(result,indent=2));perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
    u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    try:
        now=time.monotonic()
        if now-state['started']>1100:raise RuntimeError('Review timed out')
        if ed.get_game_world():return
        rt=json.loads((root/f'expansion{N}_runtime.json').read_text())
        if rt['status']=='running':return
        if rt['status']!='passed':done({'status':'runtime_failed','runtime_status':rt['status']});return
        name,loc,target=views[state['i']]
        if state['stage']=='testing':state['stage']='set'
        if state['stage']=='set':
            v=u.Vector(*loc);ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));state.update(stage='wait',t=now)
        elif state['stage']=='wait' and now-state['t']>6:
            state.update(stage='shot',t=now,task=None)   # set first: the screenshot call can re-enter this callback
            state['task']=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(root/'Validation'/name))
        elif state['stage']=='shot' and state.get('task') and state['task'].is_task_done() and now-state['t']>4:
            if state['i']+1<len(views):state.update(i=state['i']+1,stage='set')
            else:done({'status':'captured_pending_visual_review','files':['Validation/'+v[0] for v in views],'missing':['Validation/'+v[0] for v in views if not (root/'Validation'/v[0]).exists()]})
    except Exception:
        done({'status':'error','error':traceback.format_exc()})
# Start the test at top level: from a tick callback get_editor_world() returned None (see review_expansion08).
runpy.run_path(str(root/'Tools/test_expansion10.py'))
handle=u.register_slate_post_tick_callback(tick)
