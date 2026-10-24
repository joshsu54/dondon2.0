"""Tune the new meadow material to metre-scale variation and capture the final editor view."""
import unreal as u,json,time,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_12');ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
L=u.MaterialEditingLibrary;m=u.load_asset('/Game/Art/Terrain11/Materials/M_Terrain_Meadow');L.delete_all_material_expressions(m)
def node(cls):return L.create_material_expression(m,cls)
def rgb(col):
    n=node(u.MaterialExpressionConstant3Vector);n.set_editor_property('constant',u.LinearColor(*col,1));return n
a=rgb((.09,.16,.025));b=rgb((.29,.24,.10));pos=node(u.MaterialExpressionWorldPosition)
mul=node(u.MaterialExpressionMultiply);mul.set_editor_property('const_b',.002);assert L.connect_material_expressions(pos,'',mul,'A')
noise=node(u.MaterialExpressionNoise);noise.set_editor_property('scale',1.0);assert L.connect_material_expressions(mul,'',noise,'Position')
lerp=node(u.MaterialExpressionLinearInterpolate)
for n,p in [(a,'A'),(b,'B'),(noise,'Alpha')]:assert L.connect_material_expressions(n,'',lerp,p)
L.connect_material_property(lerp,'',u.MaterialProperty.MP_BASE_COLOR);rough=node(u.MaterialExpressionConstant);rough.set_editor_property('r',.9);L.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
u.EditorPythonScripting.set_keep_python_script_alive(True);u.get_editor_subsystem(u.EditorActorSubsystem).clear_actor_selection_set()
report={'status':'running','files':[]};state={'ready':0,'started':time.monotonic()}
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'));old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
def write():(root/'workers12_capture.json').write_text(json.dumps(report,indent=2))
def sequence():
    for name,loc,target in [('workers12_world.png',(10500,12500,9500),(0,-1200,800)),('workers12_camp.png',(2700,6500,2300),(0,4000,80))]:
        v=u.Vector(*loc);ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)));yield 8
        dest=root/'Validation'/name;t=u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(dest));yield 3
        while not t.is_task_done():yield 1
        assert dest.exists();report['files'].append(str(dest));write()
    report['status']='captured_pending_visual_review';write()
runner=sequence()
def tick(dt):
    if state.get('busy'):return
    state['busy']=True
    try:
        now=time.monotonic();assert now-state['started']<150
        if now<state['ready']:return
        state['ready']=now+next(runner)
    except StopIteration:
        perf.set_editor_property('bThrottleCPUWhenNotForeground',old);u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
    except Exception:
        report.update(status='error',error=traceback.format_exc());write();u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
    finally:state['busy']=False
handle=u.register_slate_post_tick_callback(tick);write()
