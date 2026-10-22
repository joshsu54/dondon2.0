"""Full Editor -ExecutePythonScript; exercises real PIE CharacterMovement.
No OS input emulation. Does not modify or save the source map/assets.
"""
import unreal as u
import json, time, traceback
from pathlib import Path
root = Path(u.Paths.project_dir()).resolve().parent
out = root / 'playtest_validation.json'
shots = root / 'Validation'
shots.mkdir(exist_ok=True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
world = editor.get_editor_world()
assert world.get_name() in ('TownPrototype_01','TownPrototype_02'), world.get_name()
loc=u.Vector(2100,2400,1200)
editor.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(1000,900,250)))
report = {'engine':u.SystemLibrary.get_engine_version(),'map':world.get_path_name(),'status':'running','method':'real PIE; CharacterMovement input via engine Python API, not keyboard input','checks':{},'samples':[],'limitations':['Keyboard and mouse controls not yet tested','House doors remain closed static geometry','Full town not imported']}
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
report['representative_bounds'] = []
for a in actors:
    if isinstance(a,u.StaticMeshActor) and any(x in a.get_actor_label() for x in ['UnitCube','Bench_Seat','Foundation','Step_']):
        origin,extent=a.get_actor_bounds(False)
        report['representative_bounds'].append({'actor':a.get_actor_label(),'center':[origin.x,origin.y,origin.z],'extent':[extent.x,extent.y,extent.z]})
state={'phase':'view','t':0.0,'started':time.monotonic(),'peak':0.0}
def write(): out.write_text(json.dumps(report,indent=2))
def pos(p):
    v=p.get_actor_location();return [v.x,v.y,v.z]
def sample(name,p):
    v=pos(p);report['samples'].append({'name':name,'position_cm':v,'movement_mode':str(p.character_movement.movement_mode)});write();return v

def tick(dt):
    try:
        if state.get('last_phase')!=state['phase']:
            state['last_phase']=state['phase'];state['phase_start']=time.monotonic()
        phase=state['phase'];t=time.monotonic()-state['phase_start']
        if time.monotonic()-state['started']>180: raise RuntimeError('PIE validation timed out')
        if phase=='view':
            if t>5:
                u.AutomationLibrary.take_high_res_screenshot(1280,720,str(shots/'prototype02_editor.png'))
                state.update(phase='capture_wait',t=0)
            return
        if phase=='capture_wait':
            if t>5:level.editor_request_begin_play();state.update(phase='spawn',t=0)
            return
        gw=editor.get_game_world()
        if not gw:return
        p=u.GameplayStatics.get_player_character(gw,0)
        if not p:return
        if phase=='spawn' and t>3:
            state['start']=sample('settled_spawn',p)
            report['checks']['spawn_above_ground']=80<state['start'][2]<120
            state.update(phase='walk',t=0)
        elif phase=='walk':
            p.add_movement_input(u.Vector(-1,0,0),1.0)
            if t>1.5:
                end=sample('after_walk',p)
                report['checks']['movement']=state['start'][0]-end[0]>300
                state.update(phase='stop',t=0)
        elif phase=='stop' and t>1:
            state['jump_start']=pos(p)[2];state['peak']=pos(p)[2];p.jump();state.update(phase='jump',t=0)
        elif phase=='jump':
            state['peak']=max(state['peak'],pos(p)[2])
            if t>.2:p.stop_jumping()
            if t>3:
                end=sample('after_jump_landing',p)
                report['jump_height_cm']=state['peak']-state['jump_start']
                report['checks']['jump']=report['jump_height_cm']>40
                report['checks']['landed']=abs(end[2]-state['jump_start'])<3
                p.set_actor_location(u.Vector(100,0,100),False,True)
                p.character_movement.stop_movement_immediately()
                state.update(phase='cube_settle',t=0)
        elif phase=='cube_settle' and t>1:
            sample('cube_test_start',p);state.update(phase='cube',t=0)
        elif phase=='cube':
            p.add_movement_input(u.Vector(1,0,0),1.0)
            if t>2:
                end=sample('cube_blocked',p)
                report['checks']['cube_blocks_character']=150<end[0]<250 and 80<end[2]<120
                u.AutomationLibrary.take_high_res_screenshot(1280,720,str(shots/'prototype02_cube_pie.png'))
                state.update(phase='cube_capture_wait',t=0)
        elif phase=='cube_capture_wait' and t>4:
            p.set_actor_location(u.Vector(1000,1500,100),False,True)
            p.character_movement.stop_movement_immediately()
            controller=u.GameplayStatics.get_player_controller(gw,0)
            controller.set_control_rotation(u.Rotator(pitch=-12,yaw=-90,roll=0))
            state.update(phase='stairs_settle',t=0)
        elif phase=='stairs_settle' and t>1:
            sample('stairs_start',p);state.update(phase='stairs',t=0);state['stairs_peak']=0
        elif phase=='stairs':
            p.add_movement_input(u.Vector(0,-1,0),1.0)
            state['stairs_peak']=max(state['stairs_peak'],pos(p)[2])
            if t>3:
                end=sample('stairs_and_closed_door',p)
                report['checks']['stairs_climbed']=state['stairs_peak']>140 and 135<end[2]<160
                report['checks']['closed_door_blocks']=1000<end[1]<1120
                u.AutomationLibrary.take_high_res_screenshot(1280,720,str(shots/'prototype02_stairs_pie.png'))
                state.update(phase='finish',t=0)
        elif phase=='finish' and t>4:
            report['status']='passed_basic_runtime_checks' if all(report['checks'].values()) else 'failed_basic_runtime_checks'
            write();level.editor_request_end_play();u.unregister_slate_post_tick_callback(handle)
            print('XIU_PLAYTEST_RESULT',report['status'])
    except Exception:
        report['status']='error';report['error']=traceback.format_exc();write()
        u.unregister_slate_post_tick_callback(handle)
        print(report['error'])
handle=u.register_slate_post_tick_callback(tick)
write()
