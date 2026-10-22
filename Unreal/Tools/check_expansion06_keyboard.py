"""Passive E-key verification in PIE. Teleports between targets; never calls TryInteract."""
import unreal as u
import json,time,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert ed.get_editor_world().get_name() == 'TownLayout_06' and not ed.get_game_world()
u.EditorPythonScripting.set_keep_python_script_alive(True)
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old=perf.get_editor_property('bThrottleCPUWhenNotForeground')
perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
report={'status':'starting','map':ed.get_editor_world().get_path_name(),'method':'Physical E via UI; engine setup teleports, no reflected interaction call','events':[]}
state={'phase':'begin','started':time.monotonic(),'last_state':None,'target':0}
targets=[(80,-3450,240),(0,-4450,240),(0,-5580,480),(0,-6750,720),(80,-3450,240)]
expected=[(1,0,0),(1,1,0),(1,2,0),(2,3,0),(3,3,10)]
def write(): (root/'expansion06_keyboard.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
def done():
 perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
 u.unregister_slate_post_tick_callback(keyboard04_handle)
def tick(dt):
 try:
  now=time.monotonic()
  if now-state['started']>300:raise RuntimeError('Keyboard test timed out')
  if state['phase']=='begin':
   level.editor_request_begin_play();state['phase']='spawn';return
  gw=ed.get_game_world()
  if not gw:return
  p=u.GameplayStatics.get_player_character(gw,0)
  if not p:return
  q=u.GameplayStatics.get_all_actors_of_class(gw,u.load_class(None,'/Script/XiuXianTown.SectQuestDirector'))[0]
  pc=u.GameplayStatics.get_player_controller(gw,0)
  if state['phase']=='spawn':
   p.set_actor_location(u.Vector(*targets[state['target']]),False,True)
   p.character_movement.stop_movement_immediately()
   pc.set_control_rotation(u.Rotator(pitch=-12,yaw=(0 if state['target'] in (0,4) else -90),roll=0))
   state['phase']='wait';state['placed']=now
   report.update(status='waiting_for_E',target=state['target'],objective=q.get_objective_text());write()
  elif state['phase']=='wait':
   actual=(q.quest_stage,q.herb_count,q.spirit_stones)
   if actual==expected[state['target']]:
    report['events'].append({'target':state['target'],'quest_state':list(actual),'objective':q.get_objective_text()})
    u.SystemLibrary.execute_console_command(gw,'Shot SHOWUI filename="'+str(root/'Validation'/('expansion06_key_%d.png'%state['target']))+'" -nosuffix',pc)
    state['phase']='capture';state['captured']=now;write()
  elif state['phase']=='capture' and now-state['captured']>3:
   if state['target']==4:
    report.update(status='passed',objective=q.get_objective_text());write();done();level.editor_request_end_play()
   else:state['target']+=1;state['phase']='spawn'
 except Exception:
  report.update(status='error',error=traceback.format_exc());write();done()
keyboard04_handle=u.register_slate_post_tick_callback(tick)
write()
