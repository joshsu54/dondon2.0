"""Verify actual worker travel/reassignment/food pause in PIE against the earned test save."""
import unreal as u,json,time,traceback,math
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;out=root/'workers12_runtime.json'
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_12');ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'));old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
report={'status':'running','checks':{},'sampled_states':[],'scope':'Local camp visibility-graph pathfinding and procedural blockout work motion, not skeletal character animation'};state={'started':time.monotonic(),'ready':0}
def write():out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def check(n,v):
    report['checks'][n]=bool(v);write();assert v,n
def pos(w,i):
    v=w.get_worker_location(i);return [v.x,v.y,v.z]
def scenario():
    level.editor_request_begin_play()
    while not ed.get_game_world():yield .5
    yield 3;world=ed.get_game_world();q=u.GameplayStatics.get_all_actors_of_class(world,u.SectAdventureDirector)[0]
    w=u.GameplayStatics.get_all_actors_of_class(world,u.load_class(None,'/Script/XiuXianTown.SectWorkers'))[0]
    check('fresh_workers_wait',all(w.get_worker_state(i)=='WaitingRecruitment' for i in range(3)))
    earned=json.loads((root/'management11_runtime.json').read_text());assert earned['status']=='passed' and earned['test_slot'].startswith('Management10_Test_')
    q.set_editor_property('save_slot',earned['test_slot']);check('load_earned_test_progress',q.load_progress())
    q.set_editor_property('save_slot','Management10_Test_Workers12_Isolated');q.set_actor_tick_enabled(False)
    check('earned_food_available',q.food>0)
    for i,j in enumerate([0,1,2]):check('assign_%d'%i,q.assign_job(i,j))
    before=[pos(w,i) for i in range(3)];yield 3
    check('all_workers_move',all(math.dist(before[i],pos(w,i))>100 for i in range(3)))
    start=time.monotonic()
    while not all(w.get_worker_state(i)=='Working' for i in range(3)):
        report['sampled_states'].append([w.get_worker_state(i) for i in range(3)]);write()
        assert time.monotonic()-start<55,'workers_cannot_reach_jobs'
        yield 1
    check('all_arrived_at_work',True);report['work_positions']=[pos(w,i) for i in range(3)]
    parts=u.GameplayStatics.get_all_actors_with_tag(world,'WorkerPart1');head=next(a for a in parts if 'Head' in a.get_actor_label())
    z0=head.get_actor_location().z;yield .35;check('procedural_work_motion',abs(head.get_actor_location().z-z0)>.05)
    for i in range(3):check('depletion_gather_job_%d'%i,q.assign_job(i,0))
    q.set_actor_tick_enabled(True);u.GameplayStatics.set_global_time_dilation(world,20);start=time.monotonic()
    while q.food>0:
        assert time.monotonic()-start<20,'food_depletion_timeout';yield .3
    u.GameplayStatics.set_global_time_dilation(world,1);q.set_actor_tick_enabled(False);yield .3
    check('no_food_pauses',all(w.get_worker_state(i)=='PausedNoFood' for i in range(3)))
    p=u.GameplayStatics.get_player_character(world,0);food=u.GameplayStatics.get_all_actors_with_tag(world,'SectFood')[0];v=food.get_actor_location()
    p.set_actor_location(u.Vector(v.x,v.y+140,90),False,True);yield .3;check('gather_food_to_resume',q.try_interact() and q.food>0)
    check('reassign_first_worker',q.assign_job(0,2));start=time.monotonic()
    yield 1;check('reassignment_travels',w.get_worker_state(0)=='Traveling')
    while w.get_worker_state(0)!='Working':
        assert time.monotonic()-start<55,'reassigned_worker_cannot_arrive';yield 1
    check('reassignment_arrived',True);check('reassignment_changed_position',math.dist(report['work_positions'][0],pos(w,0))>500)
    p=u.GameplayStatics.get_player_character(world,0);p.set_actor_location(u.Vector(0,5100,130),False,True)
    pc=u.GameplayStatics.get_player_controller(world,0);pc.set_control_rotation(u.Rotator(pitch=-12,yaw=0,roll=0));yield 4
    dest=root/'Validation/workers12_hud.png';u.SystemLibrary.execute_console_command(world,'Shot SHOWUI filename="'+str(dest)+'" -nosuffix',pc);yield 3
    check('hud_capture_exists',dest.exists());report['status']='passed';write()
runner=scenario()
def finish():
    perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
    if ed.get_game_world():
        u.GameplayStatics.set_global_time_dilation(ed.get_game_world(),1);level.editor_request_end_play()
    u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    if state.get('busy'):return
    state['busy']=True
    try:
        now=time.monotonic();assert now-state['started']<200,'timeout'
        if now<state['ready']:return
        state['ready']=now+next(runner)
    except StopIteration:finish()
    except Exception:report.update(status='error',error=traceback.format_exc());write();finish()
    finally:state['busy']=False
handle=u.register_slate_post_tick_callback(tick);write()
