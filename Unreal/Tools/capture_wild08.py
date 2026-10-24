"""Full editor only: load TownLayout_07, stream the Wild08 sublevel in memory (07 is never saved), capture views.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended (so startup warning dialogs do not block). Screenshots go to Unreal/Validation/wild08_*.png.
Waits WILD08_WARMUP seconds after loading so first-run shader compilation can finish; quits when done.
"""
import unreal as u
import json,os,time,traceback
from pathlib import Path
REPO=Path(os.environ.get('WILD08_REPO',r'D:\dondon2.0-main\dondon2.0-main'));VAL=REPO/'Unreal'/'Validation'
REPORT=REPO/'Unreal'/'wild08_capture.json';WARMUP=float(os.environ.get('WILD08_WARMUP','150'))
SHOTS=[('wild08_south_overview',(0,8200,2100),(0,2400,150)),('wild08_south_meadow',(400,6600,260),(-1700,3000,260)),
       ('wild08_east_bamboo',(2700,3000,450),(3100,-900,250)),('wild08_west_strip',(-1900,1400,650),(-2950,-1900,150)),
       ('wild08_top',(0,1200,9500),(0,1150,0))]
report={'status':'starting','base_map_read_only':'/Game/Maps/TownLayout_07','screenshots':[]}
def write():REPORT.write_text(json.dumps(report,indent=2))
u.EditorPythonScripting.set_keep_python_script_alive(True)  # otherwise -ExecutePythonScript quits before the tick callback runs
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_07')
u.EditorLevelUtils.add_level_to_world(world,'/Game/Maps/Sublevels/TownWild08_Sublevel',u.LevelStreamingAlwaysLoaded)
report['streamed_wild_actors']=len([a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.actor_has_tag('WildVegetation08')])
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
state={'phase':'warmup','start':time.monotonic(),'index':0}
def finish():
    perf.set_editor_property('bThrottleCPUWhenNotForeground',old);u.unregister_slate_post_tick_callback(handle)
    u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    try:
        now=time.monotonic()
        if state['phase']=='warmup' and now-state['start']>WARMUP:state['phase']='view'
        elif state['phase']=='view':
            name,loc,target=SHOTS[state['index']];v=u.Vector(*loc)
            ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));state.update(phase='capture',t=now)
        elif state['phase']=='capture' and now-state['t']>5:
            path=str(VAL/(SHOTS[state['index']][0]+'.png'));report['screenshots'].append(path);state.update(phase='next',t=now)
            u.AutomationLibrary.take_high_res_screenshot(1600,1000,path)
        elif state['phase']=='next' and now-state['t']>5:
            if state['index']+1<len(SHOTS):state.update(index=state['index']+1,phase='view')
            else:report['status']='captured_pending_review';write();finish()
    except Exception:
        report.update(status='error',error=traceback.format_exc());write();finish()
write();handle=u.register_slate_post_tick_callback(tick)
