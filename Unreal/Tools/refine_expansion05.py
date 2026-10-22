"""Preserve 04; lift distant cloud formations clear of the playable route."""
import unreal as u
import json,hashlib
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
assert not ed.get_game_world()
assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
dest='/Game/Maps/TownLayout_05'
assert not u.EditorAssetLibrary.does_asset_exist(dest)
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_04')
clouds=sorted([a for a in actors.get_all_level_actors() if a.actor_has_tag('DriftCloud')],key=lambda a:a.get_actor_label())
assert len(clouds)==3
changes=[]
for a,(x,y,z,s) in zip(clouds,[(-6200,-11000,3400,.16),(6200,-13500,4200,.17),(0,-18500,6000,.20)]):
 b=a.static_mesh_component.static_mesh.get_bounding_box();c=(b.min+b.max)*.5
 before={'location':str(a.get_actor_location()),'scale':str(a.get_actor_scale3d())}
 a.set_actor_scale3d(u.Vector(s,s,s))
 a.set_actor_location(u.Vector(x-c.x*s,y-c.y*s,z-c.z*s),False,True)
 a.static_mesh_component.set_editor_property('cast_shadow',False)
 changes.append({'actor':a.get_actor_label(),'before':before,'center_cm':[x,y,z],'scale':s,'cast_shadow':False})
assert u.EditorLoadingAndSavingUtils.save_map(world,dest)
world=u.EditorLoadingAndSavingUtils.load_map(dest)
loc=u.Vector(12000,4500,10000)
ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(0,-6500,1800)))
(root/'expansion05_revision.json').write_text(json.dumps({'status':'saved_reloaded_pending_visual','map':dest,'changes':changes,'preserved':'TownLayout_04','geometry_changes':'Only three scenic cloud actor transforms/shadows; trail and quest targets unchanged'},indent=2))
