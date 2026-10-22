"""Finalize this turn's exposure revision and capture two editor views."""
import unreal as u
import time,json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
w=ed.get_editor_world();assert w.get_name()=='TownLayout_02'
assert not ed.get_game_world(),'Stop PIE before finalizing'
pp=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='TownExposure')
s=pp.get_editor_property('settings');s.set_editor_property('auto_exposure_bias',1.0);pp.set_editor_property('settings',s)
assert u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Maps/TownLayout_02')
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_02')
pp=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='TownExposure')
s=pp.get_editor_property('settings');assert pp.get_editor_property('unbound') and s.get_editor_property('auto_exposure_bias')==1.
review={'map':w.get_path_name(),'status':'capturing','exposure_ev100_min_max':0,'exposure_compensation':1,'bloom':.1,'actor_count':len(actors.get_all_level_actors()),'saved_reloaded_settings_verified':True}
views=[('town02_overview_final.png',(3200,2600,3100),(0,-1200,200)),('town02_street_final.png',(550,450,360),(0,-1500,320))]
state={'index':0,'stage':'set','start':time.monotonic()}
def tick(dt):
    try:
        i=state['index']
        if state['stage']=='set':
            name,loc,target=views[i];v=u.Vector(*loc)
            ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)))
            state.update(stage='wait',start=time.monotonic())
        elif state['stage']=='wait' and time.monotonic()-state['start']>8:
            state['task']=u.AutomationLibrary.take_high_res_screenshot(1280,720,str(root/'Validation'/views[i][0]));state.update(stage='capture',start=time.monotonic())
        elif state['stage']=='capture' and state['task'].is_task_done() and time.monotonic()-state['start']>8:
            if i+1<len(views):state.update(index=i+1,stage='set')
            else:
                review['status']='saved_reloaded_captures_written_pending_visual_review'
                (root/'town02_exposure_validation.json').write_text(json.dumps(review,indent=2))
                u.unregister_slate_post_tick_callback(finalize_handle)
    except Exception:
        review.update(status='error',error=traceback.format_exc());(root/'town02_exposure_validation.json').write_text(json.dumps(review,indent=2));u.unregister_slate_post_tick_callback(finalize_handle)
finalize_handle=u.register_slate_post_tick_callback(tick)
