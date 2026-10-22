"""Passive PIE recorder for manual/CUA keyboard tests. Never moves the pawn."""
import unreal as u,json,time,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not level.is_in_play_in_editor()
records={'method':'Passive recording; no programmatic pawn movement','map':ed.get_editor_world().get_path_name(),'status':'waiting_for_pawn','samples':[]}
path=root/'keyboard_playtest.json'
start=time.monotonic();last=0
level.editor_request_begin_play()
def observe(dt):
    global last
    try:
        now=time.monotonic()
        w=ed.get_game_world()
        p=u.GameplayStatics.get_player_character(w,0) if w else None
        if p and now-last>.1:
            last=now;v=p.get_actor_location();rot=u.GameplayStatics.get_player_controller(w,0).get_control_rotation()
            records['status']='recording'
            records['samples'].append({'t':round(now-start,2),'xyz':[round(v.x,2),round(v.y,2),round(v.z,2)],'view':[round(rot.pitch,2),round(rot.yaw,2)],'mode':str(p.character_movement.movement_mode)})
            path.write_text(json.dumps(records,indent=2))
        if now-start>120 or (not level.is_in_play_in_editor() and records['samples']):
            records['status']='recording_finished';path.write_text(json.dumps(records,indent=2))
            u.unregister_slate_post_tick_callback(observer_handle)
    except Exception:
        records['status']='error';records['error']=traceback.format_exc();path.write_text(json.dumps(records,indent=2));u.unregister_slate_post_tick_callback(observer_handle)
observer_handle=u.register_slate_post_tick_callback(observe)
