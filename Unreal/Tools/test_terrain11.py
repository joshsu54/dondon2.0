"""Runtime ground and walking checks plus actual UE screenshots, using an isolated save."""
import unreal as u,json,time,math,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;out=root/'terrain11_runtime.json'
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_11')
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'));old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
report={'status':'running','checks':{},'routes':[],'screenshots':[],'limitations':['API movement, not a complete keyboard playthrough','No full world navigation or performance acceptance']};state={'started':time.monotonic(),'ready':0}
def write():out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def check(n,v):
    report['checks'][n]=bool(v);write()
    assert v,n
def down(ctx,x,y):
    h=u.SystemLibrary.line_trace_single(ctx,u.Vector(x,y,1500),u.Vector(x,y,-2000),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,True)
    t=h.to_tuple();return {'actor':t[9].get_actor_label() if t[0] and t[9] else None,'z':t[4].z if t[0] else None}
def walk(p,x,y):
    start=time.monotonic();minz=1e8
    while True:
        v=p.get_actor_location();minz=min(minz,v.z);d=math.hypot(x-v.x,y-v.y)
        if d<25:break
        assert time.monotonic()-start<35,('route_timeout',x,y,list((v.x,v.y,v.z)))
        assert v.z>-300,'fell_below_world'
        p.character_movement.set_editor_property('max_walk_speed',min(450.,max(25.,d*2)))
        p.add_movement_input(u.Vector((x-v.x)/d,(y-v.y)/d,0),1);yield 0
    p.character_movement.stop_movement_immediately();yield .4
    report['routes'].append({'target':[x,y],'position':[p.get_actor_location().x,p.get_actor_location().y,p.get_actor_location().z],'min_z':minz})
    check('walk_%s_%s'%(x,y),p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING)
def scenario():
    u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
    for name,loc,target in [('terrain11_world.png',(14000,17500,13000),(0,-1200,1000)),('terrain11_camp.png',(2700,6500,2300),(0,4000,80))]:
        v=u.Vector(*loc);ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));yield 7
        dest=root/'Validation'/name;t=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(dest));yield 3
        while not t.is_task_done():yield 1
        check(name,dest.exists());report['screenshots'].append(str(dest));write()
    level.editor_request_begin_play()
    while not ed.get_game_world():yield .5
    yield 3
    world=ed.get_game_world();p=u.GameplayStatics.get_player_character(world,0);check('player_spawned',p is not None)
    q=u.GameplayStatics.get_all_actors_of_class(world,u.SectAdventureDirector)[0];check('isolated_save',str(q.save_slot).startswith('Management10_Test_'))
    traces={}
    for x,y in [(0,4000),(900,5500),(-1000,6000),(2500,0),(-2600,-2000),(0,-7000)]:
        hit=down(p,x,y);traces[str((x,y))]=hit;report['ground_traces']=traces;check('ground_%s_%s'%(x,y),hit['actor'] is not None)
    p.set_actor_location(u.Vector(0,5000,300),False,True);yield 2
    check('camp_spawn_grounded',p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING)
    yield from walk(p,0,4200);yield from walk(p,0,3000);yield from walk(p,0,2000)
    p.set_actor_location(u.Vector(-800,3000,400),False,True);yield 2
    yield from walk(p,-800,4400)
    p.set_actor_location(u.Vector(80,-3450,350),False,True);yield 2
    for x,y in [(0,-4450),(-700,-4450),(-1200,-4450),(0,-4450),(0,-5580),(0,-6750),(0,-7000),(0,-5580),(80,-3450)]:yield from walk(p,x,y)
    report['status']='passed';write()
runner=scenario()
def finish():
    perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
    if ed.get_game_world():level.editor_request_end_play()
    u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    if state.get('busy'):return
    state['busy']=True
    try:
        now=time.monotonic();assert now-state['started']<420,'test_timeout'
        if now<state['ready']:return
        state['ready']=now+next(runner)
    except StopIteration:finish()
    except Exception:report.update(status='error',error=traceback.format_exc());write();finish()
    finally:state['busy']=False
handle=u.register_slate_post_tick_callback(tick);write()
