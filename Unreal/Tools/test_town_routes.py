"""Non-mutating real PIE route and barrier tests; isolated teleport starts, engine movement."""
import unreal as u
import json,time,math,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert ed.get_editor_world().get_name() in ('TownLayout_02','TownLayout_03')
assert not ed.get_game_world()
cases=[
 {'id':'market_main_road','start':[0,-1250,250],'target':[0,-2450],'z':[200,240]},
 {'id':'inn_open_entrance','start':[-850,-2220,260],'target':[-1100,-2220],'z':[240,270],'stop_cm':5},
 {'id':'inn_internal_stairs','start':[-1874,-1700,330],'target':[-1874,-2140],'z':[580,630]},
 {'id':'inn_upper_landing_turn','start':[-1874,-2140,620],'target':[-1680,-2140],'z':[580,630]},
 {'id':'smithy_open_front','start':[800,-910,170],'target':[1150,-910],'z':[125,145]},
 {'id':'garden_open_gateway','start':[800,-2900,260],'target':[1130,-2900],'z':[195,240]},
 {'id':'inn_back_wall_blocks','start':[-1800,-2350,280],'target':[-2150,-2350],'z':[240,270],'blocked_axis':0,'blocked_range':[-1920,-1850]},
 {'id':'garden_fence_blocks','start':[1200,-2350,250],'target':[1200,-2700],'z':[195,240],'blocked_axis':1,'blocked_range':[-2485,-2420]},
]
out=root/('town_routes_'+ed.get_editor_world().get_name()+'.json')
report={'map':ed.get_editor_world().get_path_name(),'status':'running','method':'Real PIE CharacterMovement inputs, independent teleported starts; not keyboard or continuous whole-town navigation','cases':[]}
state={'phase':'begin','index':0,'started':time.monotonic()}
def write():out.write_text(json.dumps(report,indent=2))
def pos(p):v=p.get_actor_location();return [v.x,v.y,v.z]
def tick(dt):
 try:
  now=time.monotonic()
  if state.get('last')!=state['phase']:state['last']=state['phase'];state['t']=now
  t=now-state['t'];phase=state['phase']
  if now-state['started']>240:raise RuntimeError('Route timeout')
  if phase=='begin':level.editor_request_begin_play();state['phase']='spawn';return
  gw=ed.get_game_world()
  if not gw:return
  p=u.GameplayStatics.get_player_character(gw,0)
  if not p:return
  c=cases[state['index']]
  if phase=='spawn' and t>3:state['phase']='place'
  elif phase=='place':
   p.set_actor_location(u.Vector(*c['start']),False,True);p.character_movement.stop_movement_immediately()
   p.character_movement.set_editor_property('max_walk_speed',180.)
   state['phase']='settle'
  elif phase=='settle' and t>2:
   state['initial']=pos(p);state['min_z']=pos(p)[2];state['max_z']=pos(p)[2];state['phase']='walk'
  elif phase=='walk':
   v=pos(p);dx=c['target'][0]-v[0];dy=c['target'][1]-v[1];d=math.hypot(dx,dy)
   state['min_z']=min(state['min_z'],v[2]);state['max_z']=max(state['max_z'],v[2])
   if d>c.get('stop_cm',22) and t<11:
    # Slow near endpoints so background editor frame timing cannot overshoot into furniture.
    p.character_movement.set_editor_property('max_walk_speed',min(180.,max(10.,d*.8)))
    p.add_movement_input(u.Vector(dx/d,dy/d,0),1.)
   else:
    p.character_movement.stop_movement_immediately();state['phase']='measure'
  elif phase=='measure' and t>1:
   v=pos(p);distance=math.hypot(c['target'][0]-v[0],c['target'][1]-v[1])
   checks={'standing_at_expected_height':c['z'][0]<v[2]<c['z'][1],'walking_mode':p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING,'no_fall_through':state['min_z']>50}
   if 'blocked_axis' in c:checks['barrier_blocks']=c['blocked_range'][0]<v[c['blocked_axis']]<c['blocked_range'][1]
   else:checks['destination_reached']=distance<30
   report['cases'].append({'id':c['id'],'start_settled_cm':state['initial'],'end_cm':v,'target_distance_cm':distance,'height_range':[state['min_z'],state['max_z']],'checks':checks,'passed':all(checks.values())});write()
   if state['index']+1==len(cases):
    report['status']='passed' if all(x['passed'] for x in report['cases']) else 'issues_found';write();level.editor_request_end_play();u.unregister_slate_post_tick_callback(route_handle)
   else:state['index']+=1;state['phase']='place'
 except Exception:
  report.update(status='error',error=traceback.format_exc());write();level.editor_request_end_play();u.unregister_slate_post_tick_callback(route_handle)
route_handle=u.register_slate_post_tick_callback(tick)
write()
