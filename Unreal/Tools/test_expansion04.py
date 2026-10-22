"""Real PIE continuous quest route. Runtime actors only; never saves map/assets."""
import unreal as u
import json, time, math, traceback
from pathlib import Path

root = Path(u.Paths.project_dir()).resolve().parent
out = root / 'expansion04_runtime.json'
u.EditorPythonScripting.set_keep_python_script_alive(True)
ed = u.get_editor_subsystem(u.UnrealEditorSubsystem)
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert ed.get_editor_world().get_name() in ('TownLayout_04', 'TownLayout_05')
out = root / ('expansion05_runtime.json' if ed.get_editor_world().get_name() == 'TownLayout_05' else 'expansion04_runtime.json')
assert not ed.get_game_world()
perf = u.get_default_object(u.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = {
 'status': 'running', 'map': ed.get_editor_world().get_path_name(),
 'method': 'Real PIE, continuous CharacterMovement route after isolated precondition setup; reflected interaction function, not physical E-key input',
 'checks': {}, 'route': [], 'limitations': ['Physical keyboard and HUD visual checks separate', 'Quest progress resets on new play session']
}
route = [
 ('herb1', 0, -4450, 210, 245), ('herb2', 0, -5580, 450, 490),
 ('herb3', 0, -6750, 690, 730), ('gate', 0, -7000, 690, 730),
 ('return_upper', 0, -6750, 690, 730), ('return_middle', 0, -5580, 450, 490),
 ('return_lower', 0, -4450, 210, 245), ('board', 80, -3450, 210, 245)
]
state = {'phase': 'begin', 'started': time.monotonic(), 'index': 0}
def write():
 out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
def xyz(actor):
 v=actor.get_actor_location()
 return [v.x,v.y,v.z]
def check(name, result):
 report['checks'][name]=bool(result);write()
 if not result: raise AssertionError(name)
def finish():
 perf.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
 level.editor_request_end_play()
 u.unregister_slate_post_tick_callback(expansion04_test_handle)
def tick(dt):
 try:
  now=time.monotonic()
  if state.get('previous') != state['phase']:
   state.update(previous=state['phase'], phase_start=now)
  t=now-state['phase_start']; phase=state['phase']
  if now-state['started'] > 300: raise RuntimeError('PIE timeout')
  if phase=='begin':
   level.editor_request_begin_play();state['phase']='spawn';return
  gw=ed.get_game_world()
  if not gw:return
  p=u.GameplayStatics.get_player_character(gw,0)
  if not p:return
  if phase=='spawn' and t>3:
   directors=u.GameplayStatics.get_all_actors_of_class(gw,u.load_class(None,'/Script/XiuXianTown.SectQuestDirector'))
   check('one_director', len(directors)==1)
   state['director']=directors[0];q=directors[0]
   check('initial_state', q.quest_stage==0 and q.herb_count==0 and q.spirit_stones==0)
   check('far_interaction_denied', not q.try_interact())
   state['cloud']=u.GameplayStatics.get_all_actors_with_tag(gw,'DriftCloud')[0]
   state['cloud_start']=xyz(state['cloud'])
   p.set_actor_location(u.Vector(110,-4450,230),False,True)
   p.character_movement.stop_movement_immediately();state['phase']='preaccept'
  elif phase=='preaccept' and t>1:
   q=state['director'];check('collect_before_accept_denied',not q.try_interact() and q.herb_count==0)
   p.set_actor_location(u.Vector(80,-3450,240),False,True)
   p.character_movement.stop_movement_immediately();state['phase']='accept'
  elif phase=='accept' and t>2:
   q=state['director']
   check('accept_quest',q.try_interact() and q.quest_stage==1)
   check('early_reward_denied',not q.try_interact() and q.spirit_stones==0)
   state['min_z']=xyz(p)[2];state['phase']='walk'
  elif phase=='walk':
   c=route[state['index']];v=xyz(p);dx=c[1]-v[0];dy=c[2]-v[1];d=math.hypot(dx,dy)
   state['min_z']=min(state['min_z'],v[2])
   if d>18 and t<32:
    p.character_movement.set_editor_property('max_walk_speed',min(330.,max(12.,d*1.2)))
    p.add_movement_input(u.Vector(dx/d,dy/d,0),1.)
   else:
    p.character_movement.stop_movement_immediately();state['phase']='measure'
  elif phase=='measure' and t>1:
   c=route[state['index']];v=xyz(p);d=math.hypot(c[1]-v[0],c[2]-v[1])
   checks={'arrived':d<30,'height':c[3]<v[2]<c[4],
           'walking':p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING,
           'no_fall':state['min_z']>50}
   report['route'].append({'id':c[0],'position_cm':v,'distance_cm':d,'checks':checks});write()
   check(c[0]+'_route',all(checks.values()))
   q=state['director']
   if c[0].startswith('herb'):
    n=int(c[0][-1])
    check(c[0]+'_collect',q.try_interact() and q.herb_count==n)
    check(c[0]+'_duplicate_denied',not q.try_interact() and q.herb_count==n)
    if n==3:check('ready_to_deliver',q.quest_stage==2 and q.spirit_stones==0)
   if c[0]=='board':
    check('reward_once',q.try_interact() and q.quest_stage==3 and q.spirit_stones==10)
    check('duplicate_reward_denied',not q.try_interact() and q.spirit_stones==10)
    check('clouds_move',math.dist(xyz(state['cloud']),state['cloud_start'])>1)
    report.update(status='passed',objective=q.get_objective_text(),herbs=q.herb_count,spirit_stones=q.spirit_stones)
    write();state['phase']='hold'
    pc=u.GameplayStatics.get_player_controller(gw,0)
    pc.set_control_rotation(u.Rotator(pitch=-10,yaw=-90,roll=0))
   else:
    state['index']+=1;state['phase']='walk'
  elif phase=='hold' and t>45:
   finish()
 except Exception:
  report.update(status='error',error=traceback.format_exc());write();finish()
expansion04_test_handle=u.register_slate_post_tick_callback(tick)
write()
