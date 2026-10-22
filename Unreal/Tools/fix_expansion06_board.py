"""Ground the new noticeboard and two trail lights; preserve the pre-fix map snapshot."""
import unreal as u,json,shutil,runpy
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not ed.get_game_world() and ed.get_editor_world().get_name()=='TownLayout_06'
assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
backup=root/'Validation/TownLayout_06_before_board_fix.umap.bak'
if not backup.exists():shutil.copy2(root/'XiuXianTown/Content/Maps/TownLayout_06.umap',backup)
changes=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 name=a.get_actor_label()
 target={'SectQuestBoard06':(260,-3450,132),'TrailLantern06_04':(-285,-5510,372),'TrailLantern06_05':(-285,-6650,612)}.get(name)
 if target:
  old=a.get_actor_location();changes.append({'actor':name,'before':[old.x,old.y,old.z],'after':target});a.set_actor_location(u.Vector(*target),False,True)
assert len(changes)==3
assert u.EditorLoadingAndSavingUtils.save_map(ed.get_editor_world(),'/Game/Maps/TownLayout_06')
(root/'expansion06_board_fix.json').write_text(json.dumps(changes,indent=2))
runpy.run_path(str(root/'Tools/validate_expansion06.py'))
