"""UE scene-only stair landing revision; source Blender and mesh assets unchanged."""
import unreal as u
import json
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);actor_sub=u.get_editor_subsystem(u.EditorActorSubsystem)
w=ed.get_editor_world();assert w.get_name()=='TownLayout_02' and not ed.get_game_world()
assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
assert not u.EditorAssetLibrary.does_asset_exist('/Game/Maps/TownLayout_03')
by={a.get_actor_label():a for a in actor_sub.get_all_level_actors()}
changes=[]
for n in ['Inn_Room_Partition','Inn_Bed_Frame','Inn_Bed_Quilt','Inn_Bed_Pillow']:
 a=by['TownLayout_v004_'+n];v=a.get_actor_location();sc=a.get_actor_scale3d()
 assert max(abs(v.x),abs(v.y),abs(v.z))<.01 and max(abs(sc.x-1),abs(sc.y-1),abs(sc.z-1))<.001, 'Preserve modified actor: '+n

wall=by['TownLayout_v004_Inn_Room_Partition']
# Preserve east edge -1569 cm; shorten west end from -1969 to -1810.
# Imported vertices are in world coordinates, so compensate the scaled origin.
scale=(1810-1569)/(1969-1569)
wall.set_actor_scale3d(u.Vector(scale,1,1))
wall.set_actor_location(u.Vector(-1569*(1-scale),0,0),False,True)
changes.append({'actor':wall.get_actor_label(),'scale_x':scale,'offset_cm':[-1569*(1-scale),0,0],'purpose':'Open 159 cm at the stair-side end of the partition'})
for name in ['Inn_Bed_Frame','Inn_Bed_Quilt','Inn_Bed_Pillow']:
 a=by['TownLayout_v004_'+name];a.set_actor_location(u.Vector(0,-125,0),False,True)
 changes.append({'actor':a.get_actor_label(),'offset_cm':[0,-125,0],'purpose':'Clear the upper landing; keep bed within first room'})
assert u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Maps/TownLayout_03')
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_03');assert w.get_name()=='TownLayout_03'
by={a.get_actor_label():a for a in actor_sub.get_all_level_actors()}
for c in changes:
 a=by[c['actor']];v=a.get_actor_location();assert max(abs(x-y) for x,y in zip([v.x,v.y,v.z],c['offset_cm']))<.01
(root/'town03_landing_revision.json').write_text(json.dumps({'map':w.get_path_name(),'status':'saved_reloaded_pending_route_review','source_map':'/Game/Maps/TownLayout_02','scope':'UE actor transforms only; no source geometry or asset mutation','changes':changes},indent=2))
