"""Real PIE regression and management loop; reflected actions, no simulated keyboard.
Uses a unique test save slot supplied on the command line, never the player's save.
Does not modify or save map assets. Report includes limits and raw check results.
"""
import unreal as u
import time, json, traceback, re
from pathlib import Path

root=Path(u.Paths.project_dir()).resolve().parent
report={'status':'running','checks':{},'method':'Real PIE; reflected interaction; teleports between functional checks; continuous walking checked separately',
        'limitations':['Not a physical keyboard playthrough','NPCs are static blockout figures','No performance or packaged build acceptance']}
out=root/'management10_runtime.json'
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_10')
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle=perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
state={'started':time.monotonic(),'ready':0}

def write():out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def check(name,value):
    report['checks'][name]=bool(value);write()
    if not value:raise AssertionError(name)
def tagged(tag):return u.GameplayStatics.get_all_actors_with_tag(ed.get_game_world(),tag)[0]
def arrive(tag):
    a=tagged(tag);v=a.get_actor_location()
    if tag=='QuestBoard':loc=u.Vector(80,-3450,230)
    elif tag=='QuestHerb':loc=u.Vector(v.x-130,v.y,v.z+100)
    else:loc=u.Vector(v.x,v.y+140,90)
    state['pawn'].set_actor_location(loc,False,True)
    state['pawn'].character_movement.stop_movement_immediately()
    return a
def resources():
    q=state['q'];return [q.wood,q.stone,q.food,q.spirit_stones,q.renown]
def interact(tag,name,expected=True):
    arrive(tag);yield .25
    check(name,state['q'].try_interact()==expected)
    yield .1
def supply(wood=0,stone=0,food=0,money=0):
    # Earn everything through the same actions as the player, respecting cooldowns.
    q=state['q']
    for attempt in range(80):
        if q.spirit_stones>=money and q.wood>=wood and q.stone>=stone and q.food>=food:return
        if q.food<food:
            arrive('SectFood');yield .2;q.try_interact()
        if q.wood<wood or (q.spirit_stones<money and q.wood<4):
            arrive('SectWood');yield .2;q.try_interact()
        if q.stone<stone or (q.spirit_stones<money and q.stone<2):
            arrive('SectStone');yield .2;q.try_interact()
        if q.spirit_stones<money and q.wood>=4 and q.stone>=2:
            arrive('QuestBoard');yield .2;check('commission_%d_%d'%(money,attempt),q.try_interact())
        yield 6.1
    raise AssertionError('Resource progression stalled')

def scenario():
    level.editor_request_begin_play()
    while not ed.get_game_world():yield .5
    while not u.GameplayStatics.get_player_character(ed.get_game_world(),0):yield .5
    yield 3
    p=u.GameplayStatics.get_player_character(ed.get_game_world(),0);state['pawn']=p
    found=u.GameplayStatics.get_all_actors_of_class(ed.get_game_world(),u.SectAdventureDirector)
    check('one_director',len(found)==1);q=found[0];state['q']=q
    check('isolated_test_slot',str(q.save_slot).startswith('Management10_Test_'))
    report['test_slot']=str(q.save_slot)
    check('fresh_progress',q.quest_stage==0 and len(q.disciple_jobs)==0 and q.sect_level==1)
    check('far_interaction_denied',not q.try_interact())
    yield from interact('SectShiDi','recruit_before_quest_denied',False)
    check('locked_job_denied',not q.assign_job(0,1))
    yield from interact('QuestBoard','accept_herb_quest')
    yield from interact('QuestBoard','early_reward_denied',False)
    herbs=sorted(u.GameplayStatics.get_all_actors_with_tag(ed.get_game_world(),'QuestHerb'),key=lambda a:a.get_actor_location().y,reverse=True)
    for i,a in enumerate(herbs):
        v=a.get_actor_location();p.set_actor_location(u.Vector(v.x-130,v.y,v.z+100),False,True);yield .4
        check('collect_%d'%i,q.try_interact());check('duplicate_herb_%d'%i,not q.try_interact())
        if i==0:
            check('partial_save',q.save_progress());check('partial_load',q.load_progress())
            check('partial_herb_restored',q.herb_count==1 and q.quest_stage==1)
    yield from interact('QuestBoard','claim_10_stones')
    check('quest_reward',q.quest_stage==3 and q.spirit_stones==10)
    yield from interact('SectApplicantLin','recruit_order_denied',False)
    yield from interact('SectShiDi','recruit_shidi')
    check('first_disciple',len(q.disciple_jobs)==1 and q.get_capacity()==1)
    yield from interact('SectApplicantLin','bed_capacity_denied',False)
    check('unbuilt_hall_job_denied',not q.assign_job(0,2))
    yield from interact('SectGarden','build_garden')
    check('garden_state',q.has_building('SectGarden') and list(q.disciple_jobs)==[1])
    herbs_built=u.GameplayStatics.get_all_actors_with_tag(ed.get_game_world(),'SectGardenBuilt')
    check('garden_appears',len(herbs_built)==12 and all(not a.get_editor_property('hidden') for a in herbs_built))
    before=q.food;yield 21
    check('garden_production_consumes_one_returns_four',q.food>=before+3)
    before=q.food
    yield from interact('SectFood','gather_food')
    check('gather_cooldown_denied',not q.try_interact())
    check('gather_did_not_double',q.food==before+4)
    yield from supply(12,8,2,6)
    yield from interact('SectDorm','build_dorm')
    check('capacity_expanded',q.get_capacity()==4)
    before=resources();yield from interact('SectDorm','duplicate_dorm_denied',False)
    check('duplicate_build_no_charge',resources()==before)
    yield from supply(food=2,money=5)
    yield from interact('SectApplicantLin','recruit_lin')
    check('second_disciple',len(q.disciple_jobs)==2)
    before=(q.wood,q.stone);yield 21
    check('gatherer_production',q.wood>=before[0]+4 and q.stone>=before[1]+3)
    yield from supply(8,6,3,8)
    yield from interact('SectHall','build_hall')
    yield from supply(food=3,money=8)
    yield from interact('SectApplicantYue','recruit_yue')
    check('three_unique_disciples',len(q.disciple_jobs)==3)
    check('assign_cultivation',q.assign_job(2,2))
    check('invalid_disciple_denied',not q.assign_job(3,0))
    check('invalid_job_denied',not q.assign_job(0,7))
    before=q.renown;yield 21
    check('cultivation_production',q.renown>=before+3)
    yield from supply(money=15,food=4)
    while q.renown<30:yield 10
    yield from interact('SectMaster','promote_sect')
    check('level_two',q.sect_level==2)
    before=q.spirit_stones;yield from interact('SectMaster','duplicate_promotion_denied',False)
    check('promotion_charged_once',q.spirit_stones==before)
    yield from end_checks()

def end_checks():
    q=state['q'];p=state['pawn']
    # Use real work/food consumption in an isolated slot, with faster game time only for this edge case.
    check('earned_checkpoint_saved',q.save_progress())
    earned_slot=str(q.save_slot)
    edge_slot=earned_slot+'_Starvation'
    q.set_editor_property('save_slot',edge_slot);check('starvation_fixture_saved',q.save_progress())
    for i in range(len(q.disciple_jobs)):check('starvation_job_%d'%i,q.assign_job(i,0))
    u.GameplayStatics.set_global_time_dilation(ed.get_game_world(),20)
    while q.food>0:yield 1
    before=(q.wood,q.stone,q.renown);yield 2
    check('starvation_stops_work',(q.wood,q.stone,q.renown)==before)
    u.GameplayStatics.set_global_time_dilation(ed.get_game_world(),1)
    yield from interact('SectFood','starvation_recovery')
    check('recovery_food',q.food>=4)
    q.set_editor_property('save_slot',earned_slot);check('earned_progress_restored',q.load_progress())
    # Continuous movement through the camp checks the central approach remains walkable.
    p.set_actor_location(u.Vector(0,2000,90),False,True);yield 1
    started=time.monotonic();min_z=10000
    while True:
        v=p.get_actor_location();min_z=min(min_z,v.z);delta=4200-v.y
        if abs(delta)<25:break
        if time.monotonic()-started>25:raise AssertionError('camp route timeout')
        p.character_movement.set_editor_property('max_walk_speed',min(400.,max(30.,abs(delta)*2)))
        p.add_movement_input(u.Vector(0,1 if delta>0 else -1,0),1)
        yield 0
    p.character_movement.stop_movement_immediately();yield .5
    check('continuous_camp_walk',min_z>50 and p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING)
    # An actual second PIE session, not only LoadGame within the same world.
    check('final_save',q.save_progress());saved=resources();jobs=list(q.disciple_jobs)
    level.editor_request_end_play()
    while ed.get_game_world():yield .5
    yield 1;level.editor_request_begin_play()
    while not ed.get_game_world():yield .5
    found=[]
    while not found:
        found=u.GameplayStatics.get_all_actors_of_class(ed.get_game_world(),u.SectAdventureDirector)
        if not found:yield .1
    q2=found[0]
    q2.set_actor_tick_enabled(False)
    q2.set_editor_property('save_slot',earned_slot);check('restart_load_earned_slot',q2.load_progress())
    check('restart_progress',q2.quest_stage==3 and q2.herb_count==3 and q2.sect_level==2)
    check('restart_jobs',list(q2.disciple_jobs)==jobs)
    check('restart_resources',[q2.wood,q2.stone,q2.food,q2.spirit_stones,q2.renown]==saved)
    check('restart_buildings',all(q2.has_building(tag) for tag in ['SectGarden','SectDorm','SectHall']))
    report.update(status='passed',test_slot=earned_slot,final_objective=q2.get_objective_text(),check_count=len(report['checks']))
    write()

def resume_scenario(slot):
    assert slot.startswith('Management10_Test_')
    previous=json.loads(out.read_text(encoding='utf-8'))
    assert previous['checks'].get('level_two') and all(previous['checks'].values())
    report['checks']=previous['checks'];report['resumed_from']=slot
    level.editor_request_begin_play()
    while not ed.get_game_world():yield .5
    yield 2
    state['pawn']=u.GameplayStatics.get_player_character(ed.get_game_world(),0)
    q=u.GameplayStatics.get_all_actors_of_class(ed.get_game_world(),u.SectAdventureDirector)[0];state['q']=q
    q.set_editor_property('save_slot',slot);check('resume_earned_checkpoint',q.load_progress())
    yield from end_checks()

resume=re.search(r'-SectResumeSlot=(\S+)',u.SystemLibrary.get_command_line())
# Read the previous checkpoint report before the first tick writes a fresh status.
if resume:
    previous_report=json.loads(out.read_text(encoding='utf-8'))
    assert previous_report['checks'].get('level_two') and all(previous_report['checks'].values())
    report['checks']=previous_report['checks']
runner=resume_scenario(resume.group(1)) if resume else scenario()
def finish():
    perf.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle)
    if ed.get_game_world():
        u.GameplayStatics.set_global_time_dilation(ed.get_game_world(),1)
        level.editor_request_end_play()
    u.unregister_slate_post_tick_callback(handle)
    u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    if state.get('busy'):return
    state['busy']=True
    try:
        now=time.monotonic()
        if now-state['started']>900:raise TimeoutError('Management PIE exceeded 15 minutes')
        if now<state['ready']:return
        state['ready']=now+next(runner)
    except StopIteration:finish()
    except Exception:
        report.update(status='error',error=traceback.format_exc());write();finish()
    finally:
        state['busy']=False
handle=u.register_slate_post_tick_callback(tick)
write()
