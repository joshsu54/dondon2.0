"""PIE check of the QCharacters17 v005 player characters on TownLayout_13: the pawn, its mesh and capsule, standing on the
ground, Idle playing, walking with real movement input (Walk state, play rate, stepping feet), back to Idle, the female
character possessed and walked the same way, and third-person screenshots. Writes ../qplayer13_runtime.json.
"""
import unreal as u,json,time,traceback,math
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;out=root/'qplayer13_runtime.json';VAL=root/'Validation'
MAP='/Game/Maps/TownLayout_13';ART='/Game/Art/QCharacters17';HALF=73.
u.EditorLoadingAndSavingUtils.load_map(MAP);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
u.EditorPythonScripting.set_keep_python_script_alive(True)
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'));old=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
DRV=u.load_class(None,'/Script/XiuXianTown.QCharacterAnimDriver')
report={'status':'running','map':MAP,'checks':{},'measures':{},'screenshots':[],'method':'Real PIE; movement through AddMovementInput each frame (not teleports)'}
state={'started':time.monotonic(),'ready':0}
def write():out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def check(n,v,hard=False):
    """Record; only setup failures stop the run, so one failed run still reports walking and screenshots."""
    report['checks'][n]=bool(v);write()
    if hard:assert v,n
def vec(v):return [round(v.x,2),round(v.y,2),round(v.z,2)]
def local(p,pt):
    t=p.get_actor_transform();return t.inverse_transform_location(pt)
def trace(world,a,b,p):
    """(hit?, impact point) whatever shape the binding returns: HitResult, (bool, HitResult) or None."""
    r=u.SystemLibrary.line_trace_single(world,a,b,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[p],u.DrawDebugTrace.NONE,True)
    if isinstance(r,tuple):r=next((x for x in r if isinstance(x,u.HitResult)),None)
    if r is None:return False,None
    t=r.to_tuple();return bool(t[0]),t[5]   # Break Hit Result order: blocking hit, ..., impact point
def floor_gap(world,p):
    loc=p.get_actor_location();hit,pt=trace(world,loc,loc-u.Vector(0,0,400),p)
    return (loc.z-HALF)-pt.z if hit else None
def clear_direction(world,p):
    loc=p.get_actor_location()+u.Vector(0,0,10)
    for yaw in range(0,360,30):
        d=u.Vector(math.cos(math.radians(yaw)),math.sin(math.radians(yaw)),0)
        if not trace(world,loc,loc+d*800,p)[0]:return yaw,d
    return None,None
def shot(world,pc,name):
    dest=VAL/f'qplayer13_{name}.png';u.SystemLibrary.execute_console_command(world,'Shot SHOWUI filename="'+str(dest)+'" -nosuffix',pc);report['screenshots'].append(str(dest.relative_to(root)));write()
    return dest

def walk_test(world,pc,p,tag,frames=None):
    drv=p.get_component_by_class(DRV);mesh=p.get_editor_property('mesh');mov=p.get_editor_property('character_movement')
    yaw,d=clear_direction(world,p);check(f'{tag}_clear_walk_direction',d is not None,True)
    start=p.get_actor_location();states=set();rates=[];feet=[];speeds=[];t0=time.monotonic();shot_taken=None
    while time.monotonic()-t0<3.:
        p.add_movement_input(d,1.,False);yield 0
        states.add(drv.get_anim_state());rates.append(drv.get_play_rate());speeds.append(p.get_velocity().size2d() if hasattr(p.get_velocity(),'size2d') else math.hypot(p.get_velocity().x,p.get_velocity().y))
        feet.append(local(p,mesh.get_socket_location('foot_l')))   # foot_l keeps its name
        if shot_taken is None and time.monotonic()-t0>1.6:shot_taken=shot(world,pc,f'{tag}_walking')
    moved=math.dist(vec(start)[:2],vec(p.get_actor_location())[:2])
    # foot travel along the walking direction, in the character's own frame (its forward is the mesh's walking axis)
    fx=[f.x for f in feet[len(feet)//3:]];fy=[f.y for f in feet[len(feet)//3:]];travel=max(max(fx)-min(fx),max(fy)-min(fy))
    top=max(speeds);rate=max(rates)
    report['measures'][tag+'_walk']={'yaw':yaw,'moved_cm':moved,'max_speed_cm_s':top,'max_play_rate':rate,'foot_travel_cm':travel,'states':sorted(states)}
    check(f'{tag}_walk_moves',moved>300);check(f'{tag}_walk_state','Walk' in states);check(f'{tag}_play_rate_matches_speed',abs(rate-min(top/60.,3.4))<.25)
    check(f'{tag}_feet_step',travel>15)   # cm along the walk, foot bone in the character's frame;check(f'{tag}_speed_capped',top<=205)
    t0=time.monotonic()
    while time.monotonic()-t0<1.5:yield 0
    check(f'{tag}_back_to_idle',drv.get_anim_state()=='Idle' and mov.is_moving_on_ground())

def front_shot(world,pc,p,name):
    r=p.get_actor_rotation();pc.set_control_rotation(u.Rotator(roll=0,pitch=-8,yaw=r.yaw+180));yield 1.5
    shot(world,pc,name);yield 2

def anim_data_motion():
    r={}
    for aid in ('QPlayerMale','QPlayerFemale'):
        for act in ('Idle','Walk'):
            a=u.load_asset(f'{ART}/{aid}/SK_{aid}_Anim_Armature_{act}');L=a.get_play_length()
            for bone in ('thigh_l','upperarm_l','spine'):
                q=[u.AnimationLibrary.get_bone_pose_for_time(a,bone,t*L,False).rotation for t in (0,.25,.5)]
                r[f'{aid}_{act}_{bone}_deg']=max(math.degrees(2*math.acos(min(1,abs(q[0].x*x.x+q[0].y*x.y+q[0].z*x.z+q[0].w*x.w)))) for x in q[1:])
    return r
try:report['measures']['imported_anim_rotation_deg']=anim_data_motion()
except Exception:report['measures']['imported_anim_error']=traceback.format_exc()
write()
def session(tag,aid):
    """One PIE session with the game mode's default pawn = aid."""
    level.editor_request_begin_play()
    while not ed.get_game_world():yield .5
    yield 3;world=ed.get_game_world();pc=u.GameplayStatics.get_player_controller(world,0);p=u.GameplayStatics.get_player_character(world,0)
    check(f'{tag}_pawn_class',f'BP_{aid}' in p.get_class().get_name(),True)
    mesh=p.get_editor_property('mesh');check(f'{tag}_mesh_is_v006',mesh.get_editor_property('skeletal_mesh_asset').get_name()==f'SK_{aid}')
    names=[str(mesh.get_bone_name(i)) for i in range(mesh.get_num_bones())];report['measures'][tag+'_bone_names']=names
    check(f'{tag}_seventeen_bones_named',len(names)==17 and {'head','neck','spine','hand_l','foot_l'}<=set(names))
    check(f'{tag}_capsule_73cm',abs(p.get_editor_property('capsule_component').get_scaled_capsule_half_height()-HALF)<.5)
    hz=mesh.get_socket_transform('head',u.RelativeTransformSpace.RTS_COMPONENT).translation.z;report['measures'][tag+'_head_joint_height_cm']=hz
    check(f'{tag}_skeleton_in_cm',70<hz<90)   # neck/head joint about 77 cm above the feet (v005 FBX gave 0.77)
    yield 2;g=floor_gap(world,p);report['measures'][tag+'_foot_floor_gap_cm']=g;check(f'{tag}_stands_on_ground',g is not None and abs(g)<5)
    drv=p.get_component_by_class(DRV);check(f'{tag}_anim_driver_present',drv is not None,True);check(f'{tag}_idle_state',drv.get_anim_state()=='Idle')
    report['measures'][tag+'_mesh']=[mesh.is_playing(),mesh.get_editor_property('animation_mode').name,str(mesh.get_editor_property('visibility_based_anim_tick_option'))]
    BONES=('head','hand_l','hand_r');hs={k:[] for k in BONES}
    for _ in range(12):
        for k in BONES:hs[k].append(vec(local(p,mesh.get_socket_location(k))))
        yield .1
    sway={k:max(math.dist(a,b) for a in v for b in v) for k,v in hs.items()};report['measures'][tag+'_idle_bone_motion_cm']=sway
    check(f'{tag}_idle_animates',max(sway.values())>.3)
    yield from front_shot(world,pc,p,tag+'_idle_front')
    yield from walk_test(world,pc,p,tag)
    yield from front_shot(world,pc,p,tag+'_after_walk_front')
    level.editor_request_end_play()
    while ed.get_game_world():yield .5
    yield 1

def scenario():
    gm=u.get_default_object(u.load_class(None,f'{ART}/Blueprints/BP_QPlayerGameMode.BP_QPlayerGameMode_C'))
    male=gm.get_editor_property('default_pawn_class')
    yield from session('male','QPlayerMale')
    gm.set_editor_property('default_pawn_class',u.load_class(None,f'{ART}/Blueprints/BP_QPlayerFemale.BP_QPlayerFemale_C'))   # in memory only, never saved
    try:yield from session('female','QPlayerFemale')
    finally:gm.set_editor_property('default_pawn_class',male)
    report['status']='passed' if all(report['checks'].values()) else 'failed';write()

runner=scenario()
def finish():
    perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
    if ed.get_game_world():level.editor_request_end_play()
    u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
def tick(dt):
    if state.get('busy'):return
    state['busy']=True
    try:
        now=time.monotonic();assert now-state['started']<300,'timeout'
        if now<state['ready']:return
        state['ready']=now+next(runner)
    except StopIteration:finish()
    except Exception:report.update(status='error',error=traceback.format_exc());write();finish()
    finally:state['busy']=False
handle=u.register_slate_post_tick_callback(tick);write()
