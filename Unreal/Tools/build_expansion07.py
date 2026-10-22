"""Create a separate 07 revision: board footing and local warm fill lighting."""
import unreal as u
import json,hashlib,traceback,runpy
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
report={'status':'starting','map':'/Game/Maps/TownLayout_07','scope':'UE placement and light polish only; source Blender/FBX unchanged'}
def write(): (root/'expansion07_revision.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
try:
 ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
 actors=u.get_editor_subsystem(u.EditorActorSubsystem)
 assert not ed.get_game_world() and not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
 assert not u.EditorAssetLibrary.does_asset_exist(report['map']), 'Never overwrite existing 07'
 source=root/'XiuXianTown/Content/Maps/TownLayout_06.umap'
 report['source06_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
 world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_06')
 board=next(a for a in actors.get_all_level_actors() if a.actor_has_tag('QuestBoard'))
 assert (board.get_actor_location()-u.Vector(260,-3450,132)).length()<.1
 # A low stone plinth bridges the shallow gutter under both feet, flush with board bottom.
 base=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(260,-3450,112))
 base.set_actor_label('QuestBoardFooting07');base.set_folder_path('Expansion07')
 base.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
 base.static_mesh_component.set_material(0,u.load_asset('/Game/Art/Expansion06/Materials/M_Pale_Edge_Stone'))
 base.set_actor_scale3d(u.Vector(1.2,3.5,.4))
 base.set_actor_enable_collision(True)
 for name,pos,intensity,radius in [('BoardWarmFill07',(30,-3450,360),280.,500.),('PavilionWarmFill07',(-1200,-4450,480),700.,640.)]:
  a=actors.spawn_actor_from_class(u.PointLight,u.Vector(*pos));a.set_actor_label(name);a.set_folder_path('Expansion07')
  c=a.get_component_by_class(u.PointLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
  c.set_editor_property('intensity_units',u.LightUnits.CANDELAS)
  c.set_intensity(intensity);c.set_attenuation_radius(radius);c.set_light_color(u.LinearColor(1.,.86,.67,1.))
  c.set_editor_property('cast_shadows',False)
 assert u.EditorLoadingAndSavingUtils.save_map(world,report['map'])
 world=u.EditorLoadingAndSavingUtils.load_map(report['map'])
 items={a.get_actor_label():a for a in actors.get_all_level_actors()}
 report['checks']={'actor_count':len(items)==3948,'board_unchanged':(items['SectQuestBoard06'].get_actor_location()-u.Vector(260,-3450,132)).length()<.1,'base_collision':items['QuestBoardFooting07'].get_actor_enable_collision(),'source06_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==report['source06_sha256']}
 c,e=items['QuestBoardFooting07'].get_actor_bounds(False)
 report['checks']['plinth_top_flush']=abs(c.z+e.z-132)<.1
 report['checks']['clear_interaction_approach']=c.x-e.x>150
 for n in ['BoardWarmFill07','PavilionWarmFill07']:
  c=items[n].get_component_by_class(u.PointLightComponent)
  report['checks'][n+'_saved']=c.intensity>0 and not c.cast_shadows
 assert all(report['checks'].values()),report['checks']
 report.update(status='saved_reloaded_pending_runtime_visual',map_sha256=hashlib.sha256((root/'XiuXianTown/Content/Maps/TownLayout_07.umap').read_bytes()).hexdigest());write()
 runpy.run_path(str(root/'Tools/review_expansion07.py'))
except Exception:
 report.update(status='error',error=traceback.format_exc());write();raise
