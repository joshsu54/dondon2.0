"""Real PIE on TownLayout_08: the 07 quest route plus a south-meadow segment for the WildVegetation08 sublevel.
Runtime actors only; never saves map/assets. Movement via CharacterMovement API; interaction via reflected
try_interact, not physical E-key input. Meadow segment starts from an isolated teleport point.
"""
import unreal as u
import json, time, math, traceback
from pathlib import Path

import os
root = Path(u.Paths.project_dir()).resolve().parent
MAP = os.environ.get('TOWN_PIE_MAP', 'TownLayout_08')  # later revisions (09 …) reuse the same route
out = root / ('expansion%s_runtime.json' % MAP[-2:])
u.EditorPythonScripting.set_keep_python_script_alive(True)
ed = u.get_editor_subsystem(u.UnrealEditorSubsystem)
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert ed.get_editor_world().get_name() == MAP
assert not ed.get_game_world()
perf = u.get_default_object(u.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = {
 'status': 'running', 'map': ed.get_editor_world().get_path_name(),
 'method': 'Real PIE, continuous CharacterMovement route after isolated precondition setup; reflected interaction function, not physical E-key input',
 'checks': {}, 'route': [], 'meadow': [],
 'limitations': ['Physical keyboard and HUD visual checks separate', 'Quest progress resets on new play session', 'Meadow segment starts from a teleport, not a walk from the town gate']
}
# (id, x, y, min_z, max_z) — identical to the 07 quest route.
route = [
 ('herb1', 0, -4450, 210, 245), ('pavilion_approach', -700, -4450, 210, 245), ('pavilion_inside', -1200, -4450, 270, 290),
 ('pavilion_return', 0, -4450, 210, 245), ('herb2', 0, -5580, 450, 490), ('herb3', 0, -6750, 690, 730), ('gate', 0, -7000, 690, 730),
 ('return_upper', 0, -6750, 690, 730), ('return_middle', 0, -5580, 450, 490), ('return_lower', 0, -4450, 210, 245), ('board', 80, -3450, 210, 245)
]
# Meadow on ValleyGround (top z -15 cm): capsule centre sits roughly 60-110 cm.
# kind: 'walk' must arrive; 'blocked' walks at an obstacle and must never get closer to its centre than the
# given clearance. A thin round trunk lets the character slide around it, so arrival is not the test.
MEADOW_START = (0, 3000, 120)
meadow = [
 ('meadow_walk_west', 'walk', -1000, 3300), ('meadow_walk_far', 'walk', -1500, 4300), ('meadow_walk_east', 'walk', 400, 4200),
 ('shrub_pass_start', 'walk', -1200, 1500), ('shrub_walk_through', 'walk', -1200, 2300),
 # Pine capsule radius 30 cm x scale .95 + character radius 42 = ~70 cm; boulder box half-depth ~70 cm + 42.
 ('pine_block_start', 'walk', 1900, 2600), ('pine_trunk_blocks', 'blocked', 1900, 3300, (1900, 3100), 60),
 ('boulder_block_start', 'walk', 2650, 3400), ('boulder_blocks', 'blocked', 2650, 4400, (2650, 4100), 90),
]
state = {'phase': 'begin', 'started': time.monotonic(), 'index': 0, 'm': 0}
def write():
 out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
def xyz(actor):
 v=actor.get_actor_location();return [v.x,v.y,v.z]
def check(name, result):
 report['checks'][name]=bool(result);write()
 if not result: raise AssertionError(name)
def finish():
 perf.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
 level.editor_request_end_play()
 u.unregister_slate_post_tick_callback(expansion08_test_handle)
def steer(p, tx, ty, t, limit=32):
 v=xyz(p);dx=tx-v[0];dy=ty-v[1];d=math.hypot(dx,dy)
 if d>18 and t<limit:
  p.character_movement.set_editor_property('max_walk_speed',min(330.,max(12.,d*1.2)));p.add_movement_input(u.Vector(dx/d,dy/d,0),1.);return False
 p.character_movement.stop_movement_immediately();return True
def tick(dt):
 try:
  now=time.monotonic()
  if state.get('previous') != state['phase']:
   state.update(previous=state['phase'], phase_start=now)
  t=now-state['phase_start']; phase=state['phase']
  if now-state['started'] > 420: raise RuntimeError('PIE timeout')
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
   check('wild_actors_in_pie', len(u.GameplayStatics.get_all_actors_with_tag(gw,'WildVegetation08'))==24)
   # Diagnostic (non-fatal): does the PIE world itself see the pine/boulder collision?
   diag={}
   for tag,a,b in [('CommonPine',(1900,2600,90),(1900,3600,90)),('MossBoulderSet',(2650,3300,90),(2650,4900,90))]:
    h=u.SystemLibrary.capsule_trace_single(p,u.Vector(*a),u.Vector(*b),42,96,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,True)
    t=h.to_tuple() if h else None;diag[tag+'_trace']=t[9].get_actor_label() if t and t[0] and t[9] else None
    act=[x for x in u.GameplayStatics.get_all_actors_with_tag(gw,tag)];c=act[0].static_mesh_component
    diag[tag+'_pawn_response']=str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN));diag[tag+'_enabled']=str(c.get_collision_enabled())
    diag[tag+'_actor_collision']=act[0].get_actor_enable_collision();diag[tag+'_level']=act[0].get_level().get_path_name() if hasattr(act[0],'get_level') else None
   report['pie_collision_diagnostic']=diag;write()
   state['cloud']=u.GameplayStatics.get_all_actors_with_tag(gw,'DriftCloud')[0];state['cloud_start']=xyz(state['cloud'])
   p.set_actor_location(u.Vector(110,-4450,230),False,True);p.character_movement.stop_movement_immediately();state['phase']='preaccept'
  elif phase=='preaccept' and t>1:
   q=state['director'];check('collect_before_accept_denied',not q.try_interact() and q.herb_count==0)
   p.set_actor_location(u.Vector(80,-3450,240),False,True);p.character_movement.stop_movement_immediately();state['phase']='accept'
  elif phase=='accept' and t>2:
   q=state['director']
   check('accept_quest',q.try_interact() and q.quest_stage==1)
   check('early_reward_denied',not q.try_interact() and q.spirit_stones==0)
   state['min_z']=xyz(p)[2];state['phase']='walk'
  elif phase=='walk':
   c=route[state['index']];state['min_z']=min(state['min_z'],xyz(p)[2])
   if steer(p,c[1],c[2],t):state['phase']='measure'
  elif phase=='measure' and t>1:
   c=route[state['index']];v=xyz(p);d=math.hypot(c[1]-v[0],c[2]-v[1])
   checks={'arrived':d<30,'height':c[3]<v[2]<c[4],'walking':p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING,'no_fall':state['min_z']>50}
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
    p.set_actor_location(u.Vector(*MEADOW_START),False,True);p.character_movement.stop_movement_immediately()
    state.update(phase='meadow_settle')
   else:
    state['index']+=1;state['phase']='walk'
  elif phase=='meadow_settle' and t>2:
   check('meadow_start_grounded',60<xyz(p)[2]<110 and p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING)
   state.update(phase='meadow_walk',meadow_min_z=xyz(p)[2])
  elif phase=='meadow_walk':
   m=meadow[state['m']];v=xyz(p);state['meadow_min_z']=min(state['meadow_min_z'],v[2])
   if m[1]=='blocked':state['closest']=min(state.get('closest',1e9),math.hypot(v[0]-m[4][0],v[1]-m[4][1]))
   if steer(p,m[2],m[3],t,20 if m[1]=='blocked' else 32):state['phase']='meadow_measure'
  elif phase=='meadow_measure' and t>1:
   m=meadow[state['m']];v=xyz(p);d=math.hypot(m[2]-v[0],m[3]-v[1])
   checks={'height':60<v[2]<110,'walking':p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING,'no_fall':state['meadow_min_z']>40}
   if m[1]=='walk':checks['arrived']=d<30
   else:checks['kept_clear_of_obstacle']=state['closest']>m[5]
   report['meadow'].append({'id':m[0],'kind':m[1],'position_cm':v,'distance_to_target_cm':d,'closest_to_obstacle_cm':state.pop('closest',None),'checks':checks});write()
   check(m[0],all(checks.values()))
   if state['m']+1<len(meadow):state.update(m=state['m']+1,phase='meadow_walk')
   else:
    q=state['director'];report.update(status='passed',objective=q.get_objective_text(),herbs=q.herb_count,spirit_stones=q.spirit_stones);write()
    state['phase']='hold'
  elif phase=='hold' and t>4:
   finish()
 except Exception:
  report.update(status='error',error=traceback.format_exc());write();finish()
expansion08_test_handle=u.register_slate_post_tick_callback(tick)
write()
