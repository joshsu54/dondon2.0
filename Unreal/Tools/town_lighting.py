"""Create exposure revision 02 from saved 01; preserve prior map."""
import unreal as u
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
w=ed.get_editor_world();assert w.get_name()=='TownLayout_01'
assert not u.EditorAssetLibrary.does_asset_exist('/Game/Maps/TownLayout_02'), 'Revision 02 exists'
assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Unsaved map edits'
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
pp=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=='TownExposure'),None)
if pp is None:pp=actors.spawn_actor_from_class(u.PostProcessVolume,u.Vector(0,0,0));pp.set_actor_label('TownExposure')
pp.set_editor_property('unbound',True)
s=pp.get_editor_property('settings')
for key,val in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',0.),('auto_exposure_max_brightness',0.),('override_auto_exposure_bias',True),('auto_exposure_bias',0.),('override_bloom_intensity',True),('bloom_intensity',0.1)]:s.set_editor_property(key,val)
pp.set_editor_property('settings',s)
loc=u.Vector(3200,2600,3100);ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(0,-1200,200)))
assert u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Maps/TownLayout_02')
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_02')
assert w.get_name()=='TownLayout_02'
ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(0,-1200,200)))
print('TOWN_EXPOSURE_SAVED')
