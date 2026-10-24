"""Capture the new map and the earned test checkpoint; never changes user progress or assets."""
import unreal as u
import json,time,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_10')
u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old=perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
report={'status':'running','files':[],'note':'Editor images show completed layout; HUD image loads the earned isolated test checkpoint.'}
state={'ready':0,'started':time.monotonic()}
def write():(root/'management10_capture.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def sequence():
    for name,loc,target in [('management10_world.png',(6500,10000,6500),(0,1400,300)),
                            ('management10_camp.png',(2700,6500,2300),(0,4000,80))]:
        v=u.Vector(*loc);ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)))
        yield 6
        dest=root/'Validation'/name
        task=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(dest))
        yield 3
        while not task.is_task_done():yield 1
        assert dest.exists(),str(dest);report['files'].append(str(dest));write()
    level.editor_request_begin_play()
    while not ed.get_game_world():yield .5
    yield 3
    world=ed.get_game_world();q=u.GameplayStatics.get_all_actors_of_class(world,u.SectAdventureDirector)[0]
    # Only the explicitly recorded passing test checkpoint can be loaded for this preview.
    runtime=json.loads((root/'management10_runtime.json').read_text(encoding='utf-8'))
    assert runtime['status']=='passed'
    assert str(q.save_slot)==runtime['test_slot'], 'Launch capture with -ResumeSlot from the passing runtime report'
    report['automatic_load_in_new_editor_process']=q.sect_level==2 and q.herb_count==3 and len(q.disciple_jobs)==3
    assert report['automatic_load_in_new_editor_process']
    p=u.GameplayStatics.get_player_character(world,0)
    p.set_actor_location(u.Vector(0,5100,90),False,True)
    pc=u.GameplayStatics.get_player_controller(world,0)
    pc.set_control_rotation(u.Rotator(pitch=-12,yaw=-90,roll=0))
    yield 5
    dest=root/'Validation/management10_hud.png'
    u.SystemLibrary.execute_console_command(world,'Shot SHOWUI filename="'+str(dest)+'" -nosuffix',pc)
    yield 4
    assert dest.exists(),str(dest);report['files'].append(str(dest))
    report.update(status='captured_pending_visual_review');write()
runner=sequence()
def finish():
    perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
    if ed.get_game_world():level.editor_request_end_play()
    u.unregister_slate_post_tick_callback(handle)
    u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    if state.get('busy'):return
    state['busy']=True
    try:
        now=time.monotonic()
        if now-state['started']>180:raise TimeoutError('capture timeout')
        if now<state['ready']:return
        state['ready']=now+next(runner)
    except StopIteration:finish()
    except Exception:
        report.update(status='error',error=traceback.format_exc());write();finish()
    finally:
        state['busy']=False
handle=u.register_slate_post_tick_callback(tick)
write()
