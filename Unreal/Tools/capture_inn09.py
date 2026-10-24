"""Full editor: capture the same inn interior views in 08 (before) and 09 (after), plus one exterior view of the
inn front to check for light leaking outside. No asset or map changes. Quits when done.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,time,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;VAL=root/'Validation'
u.EditorPythonScripting.set_keep_python_script_alive(True)
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
VIEWS=[('hall',(-1130,-2220,330),(-1800,-2220,280)),('counter_stairs',(-1230,-1720,360),(-1800,-2550,250)),
       ('stairs_up',(-1650,-2350,330),(-1880,-1700,470)),('upper_corridor',(-1300,-2760,690),(-1300,-1700,640)),
       ('upper_room',(-1600,-2540,700),(-1900,-2560,560)),('exterior_front',(-250,-2220,380),(-1300,-2220,400))]
import os
MAPS=[('08','/Game/Maps/TownLayout_08'),('09','/Game/Maps/TownLayout_09')]
if os.environ.get('INN09_ONLY'):MAPS=MAPS[1:]  # re-capture 09 after tuning; 08 "before" images are unchanged
report={'status':'starting','files':[]}
def write():(root/'expansion09_capture.json').write_text(json.dumps(report,indent=2))
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
state={'m':0,'v':0,'stage':'load','t':time.monotonic(),'start':time.monotonic()}
def done(status):
    report['status']=status;write();perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
    u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    try:
        now=time.monotonic()
        if now-state['start']>900:raise RuntimeError('capture timeout')
        tag,path=MAPS[state['m']]
        if state['stage']=='load':
            u.EditorLoadingAndSavingUtils.load_map(path);u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
            state.update(stage='settle',t=now)
        elif state['stage']=='settle' and now-state['t']>(20 if state['m']==0 else 8):state['stage']='set'
        elif state['stage']=='set':
            name,loc,target=VIEWS[state['v']];v=u.Vector(*loc)
            ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));state.update(stage='wait',t=now)
        elif state['stage']=='wait' and now-state['t']>5:
            # Set the stage first: the screenshot call can re-enter this callback.
            f='inn%s_%s.png'%(tag,VIEWS[state['v']][0]);state.update(stage='shot',t=now);report['files'].append('Validation/'+f)
            state['task']=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(VAL/f))
        elif state['stage']=='shot' and state.get('task') and state['task'].is_task_done() and now-state['t']>3:
            state['task']=None
            if state['v']+1<len(VIEWS):state.update(v=state['v']+1,stage='set')
            elif state['m']+1<len(MAPS):state.update(m=state['m']+1,v=0,stage='load')
            else:report['missing']=[f for f in report['files'] if not (root/f).exists()];write();done('captured_pending_visual_review')
    except Exception:
        report['error']=traceback.format_exc();done('error')
write();handle=u.register_slate_post_tick_callback(tick)
