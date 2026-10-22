"""Real PIE smoke checks of imported town; leaves editor on overview afterwards."""
import unreal as u
import json,time,traceback,re
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
out=root/'town_playtest_validation.json';shots=root/'Validation';shots.mkdir(exist_ok=True)
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert ed.get_editor_world().get_name()=='TownLayout_02'
report={'map':ed.get_editor_world().get_path_name(),'status':'running','method':'PIE CharacterMovement API input; not physical keyboard testing','checks':{},'samples':[],'limits':['Full navigation coverage, interiors and interactions pending','No baked procedural textures or animated water']}
palette=json.loads((root/'town_palette.json').read_text())
clean=lambda s:re.sub(r'[^A-Za-z0-9_-]','_',s)
source_bounds={clean(k):v for k,v in palette['bounds'].items()}
source_slots={clean(k):v for k,v in palette['objects'].items()}
mesh_actors=[a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.StaticMeshActor)]
assert len(mesh_actors)==3877
max_bounds_error=0.;slot_errors=[]
for a in mesh_actors:
    comp=a.static_mesh_component;mesh=comp.static_mesh;name=mesh.get_name();b=source_bounds[name]
    expected_min=[b['min'][0]*100,-b['max'][1]*100,b['min'][2]*100]
    expected_max=[b['max'][0]*100,-b['min'][1]*100,b['max'][2]*100]
    bounds=mesh.get_bounding_box()
    err=max(abs(getattr(bounds.min,ax)-expected_min[i]) for i,ax in enumerate(('x','y','z')))
    err=max(err,max(abs(getattr(bounds.max,ax)-expected_max[i]) for i,ax in enumerate(('x','y','z'))))
    max_bounds_error=max(max_bounds_error,err)
    for i in range(comp.get_num_materials()):
        mat=comp.get_material(i)
        if not mat or not mat.get_path_name().startswith('/Game/Art/Materials/TownPalette01/'):slot_errors.append(name)
report['source_bounds_max_error_cm']=max_bounds_error
report['checks']['source_scale_and_orientation']=max_bounds_error<3
report['checks']['all_materials_reloaded']=not slot_errors
report['material_slot_errors']=slot_errors

state={'phase':'view','started':time.monotonic()}
def write():out.write_text(json.dumps(report,indent=2))
def pos(p):
    v=p.get_actor_location();return [v.x,v.y,v.z]
def sample(name,p):
    v=pos(p);report['samples'].append({'name':name,'position_cm':v,'movement_mode':str(p.character_movement.movement_mode)});write();return v
def overview():
    loc=u.Vector(3200,2600,3100);ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(0,-1200,200)))
overview()
def tick(dt):
    try:
        if state.get('last_phase')!=state['phase']:state['last_phase']=state['phase'];state['phase_start']=time.monotonic()
        phase=state['phase'];t=time.monotonic()-state['phase_start']
        if time.monotonic()-state['started']>240:raise RuntimeError('Timed out')
        if phase=='view':
            if t>6:
                state['shot']=u.AutomationLibrary.take_high_res_screenshot(1280,720,str(shots/'town02_overview.png'))
                state['phase']='shot'
            return
        if phase=='shot':
            if state['shot'].is_task_done():level.editor_request_begin_play();state['phase']='spawn'
            return
        if phase=='finish':
            if t>3:
                overview();u.unregister_slate_post_tick_callback(town_tick_handle)
            return
        gw=ed.get_game_world()
        if not gw:return
        p=u.GameplayStatics.get_player_character(gw,0)
        if not p:return
        if phase=='spawn' and t>4:
            v=sample('settled_entrance',p);state['spawn']=v
            report['checks']['entrance_ground_collision']=abs(v[0])<50 and 90<v[2]<150
            u.GameplayStatics.get_player_controller(gw,0).set_control_rotation(u.Rotator(pitch=-12,yaw=-90,roll=0))
            state['phase']='walk'
        elif phase=='walk':
            v=pos(p)
            if v[1]>-450 and t<10:p.add_movement_input(u.Vector(0,-1,0),1.)
            else:
                v=sample('central_stair_route',p)
                report['checks']['walked_into_town']=state['spawn'][1]-v[1]>400
                report['checks']['central_stairs_climbed']=v[1]<-300 and 200<v[2]<270
                p.character_movement.stop_movement_immediately();state['phase']='settle'
        elif phase=='settle' and t>2:
            state['jump_start']=pos(p)[2];state['peak']=pos(p)[2];p.jump();state['phase']='jump'
        elif phase=='jump':
            state['peak']=max(state['peak'],pos(p)[2])
            if t>.2:p.stop_jumping()
            if t>3:
                v=sample('jump_landing',p)
                report['checks']['jump']=state['peak']-state['jump_start']>40
                report['checks']['landing']=abs(v[2]-state['jump_start'])<4
                state['shot']=u.AutomationLibrary.take_high_res_screenshot(1280,720,str(shots/'town02_editor_view_during_pie.png'));state['phase']='pie_shot'
        elif phase=='pie_shot' and state['shot'].is_task_done():
            report['status']='passed_smoke_checks' if all(report['checks'].values()) else 'failed_smoke_checks'
            write();level.editor_request_end_play();state['phase']='finish'
    except Exception:
        report['status']='error';report['error']=traceback.format_exc();write()
        level.editor_request_end_play();u.unregister_slate_post_tick_callback(town_tick_handle)
town_tick_handle=u.register_slate_post_tick_callback(tick)
write()
