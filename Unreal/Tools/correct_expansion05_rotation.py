"""Correct the working 05 landscape axes using explicit Rotator fields."""
import unreal as u
import json
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not ed.get_game_world()
world=ed.get_editor_world();assert world.get_name()=='TownLayout_05'
assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
desired={**{'ValleyRidge_%02d'%i:y for i,y in enumerate([20,-30,50,-50])},
         **{'DistantPeak_%02d'%i:i*43 for i in range(3)}}
changes=[]
for a in actors:
 if a.get_actor_label() in desired:
  r=a.get_actor_rotation();yaw=desired[a.get_actor_label()]
  changes.append({'actor':a.get_actor_label(),'before':{'pitch':r.pitch,'yaw':r.yaw,'roll':r.roll},'after':{'pitch':0,'yaw':yaw,'roll':0}})
  a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False)
assert len(changes)==7
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Maps/TownLayout_05')
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_05')
p=root/'expansion05_revision.json';d=json.loads(p.read_text());d['rotation_corrections']=changes;p.write_text(json.dumps(d,indent=2))
