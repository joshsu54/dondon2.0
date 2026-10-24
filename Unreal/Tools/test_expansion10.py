"""Real PIE on TownLayout_10: the 07 quest route plus valley/camp segments on the LingyunValley15 terrain.
Runtime only, never saves. Movement via CharacterMovement API; interaction via reflected try_interact (not E-key).
Heights on the new rolling terrain are checked against the ground under the character (line trace), not fixed z.
"""
import unreal as u
import json,time,math,traceback,os
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
MAP=os.environ.get('TOWN_PIE_MAP','TownLayout_10')   # later revisions reuse this route
out=root/('expansion%s_runtime.json'%MAP[-2:])
u.EditorPythonScripting.set_keep_python_script_alive(True)
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert ed.get_editor_world().get_name()==MAP and not ed.get_game_world()
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle=perf.get_editor_property('bThrottleCPUWhenNotForeground');perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
report={'status':'running','map':ed.get_editor_world().get_path_name(),
        'method':'Real PIE, CharacterMovement route; reflected interaction, not physical E-key input','checks':{},'route':[],'valley':[],
        'limitations':['Valley segments start from isolated teleports','Physical keyboard and HUD checks separate','Quest progress resets on new play session']}
route=[('herb1',0,-4450,210,245),('pavilion_approach',-700,-4450,210,245),('pavilion_inside',-1200,-4450,270,290),('pavilion_return',0,-4450,210,245),
       ('herb2',0,-5580,450,490),('herb3',0,-6750,690,730),('gate',0,-7000,690,730),('return_upper',0,-6750,690,730),('return_middle',0,-5580,450,490),
       ('return_lower',0,-4450,210,245),('board',80,-3450,210,245)]
# Valley segments (UE cm). 'tp' teleports to the point first; 'walk' must arrive; 'blocked' must stay clear of a trunk.
valley=[('camp_path_start','tp',0,2000),('camp_path_south','walk',0,4400),('dorm_front','walk',-840,4700),('dorm_inside','walk',-1150,4700),
        ('dorm_out','walk',-840,4700),('branch_east','walk',60,4700),('garden_gate','walk',700,4720),('back_to_path','walk',60,4700),
        ('pavilion_steps','walk',0,6200),('pavilion_centre','walk',0,6660),
        ('north_slope_start','tp',1100,-4300),('north_slope_climb','walk',1100,-6000),
        ('pine_test_start','tp',-3047,5458),('pine_trunk_blocks','blocked',-3047,4658,(-3047,4858),50)]
state={'phase':'begin','started':time.monotonic(),'index':0,'m':0}
def write():out.write_text(json.dumps(report,indent=2,ensure_ascii=False))
def xyz(a):v=a.get_actor_location();return [v.x,v.y,v.z]
def check(name,result):
    report['checks'][name]=bool(result);write()
    if not result:raise AssertionError(name)
def finish():
    perf.set_editor_property('bThrottleCPUWhenNotForeground',old_throttle);level.editor_request_end_play();u.unregister_slate_post_tick_callback(handle)
def ground(gw_actor,x,y,z0=3000.):
    """Surface under (x,y) tracing down from z0: 3000 to find a teleport spot, the character's own z to measure (avoids roofs)."""
    h=u.SystemLibrary.line_trace_single(gw_actor,u.Vector(x,y,z0),u.Vector(x,y,-3000.),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[gw_actor],u.DrawDebugTrace.NONE,True)
    t=h.to_tuple() if h else None;return (t[4].z,t[9].get_actor_label() if t[9] else None) if t and t[0] else (None,None)
def steer(p,tx,ty,t,limit=40):
    v=xyz(p);dx=tx-v[0];dy=ty-v[1];d=math.hypot(dx,dy)
    if d>18 and t<limit:p.character_movement.set_editor_property('max_walk_speed',min(330.,max(12.,d*1.2)));p.add_movement_input(u.Vector(dx/d,dy/d,0),1.);return False
    p.character_movement.stop_movement_immediately();return True
def tick(dt):
    try:
        now=time.monotonic()
        if state.get('previous')!=state['phase']:state.update(previous=state['phase'],phase_start=now)
        t=now-state['phase_start'];phase=state['phase']
        if now-state['started']>480:raise RuntimeError('PIE timeout')
        if phase=='begin':level.editor_request_begin_play();state['phase']='spawn';return
        gw=ed.get_game_world()
        if not gw:return
        p=u.GameplayStatics.get_player_character(gw,0)
        if not p:return
        if phase=='spawn' and t>3:
            ds=u.GameplayStatics.get_all_actors_of_class(gw,u.load_class(None,'/Script/XiuXianTown.SectQuestDirector'));check('one_director',len(ds)==1)
            state['director']=q=ds[0];check('initial_state',q.quest_stage==0 and q.herb_count==0 and q.spirit_stones==0)
            check('far_interaction_denied',not q.try_interact())
            check('valley_vegetation_in_pie',len(u.GameplayStatics.get_all_actors_with_tag(gw,'LY10Vegetation'))==383)
            check('wild08_absent',len(u.GameplayStatics.get_all_actors_with_tag(gw,'WildVegetation08'))==0)
            v=xyz(p);z,lab=ground(p,v[0],v[1],v[2]);report['spawn_ground']=[z,lab]   # recorded only: town paving may sit under spawn
            check('spawned_standing',p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING and z is not None and 60<v[2]-z<120)
            state['cloud']=u.GameplayStatics.get_all_actors_with_tag(gw,'DriftCloud')[0];state['cloud_start']=xyz(state['cloud'])
            p.set_actor_location(u.Vector(110,-4450,230),False,True);p.character_movement.stop_movement_immediately();state['phase']='preaccept'
        elif phase=='preaccept' and t>1:
            q=state['director'];check('collect_before_accept_denied',not q.try_interact() and q.herb_count==0)
            p.set_actor_location(u.Vector(80,-3450,240),False,True);p.character_movement.stop_movement_immediately();state['phase']='accept'
        elif phase=='accept' and t>2:
            q=state['director'];check('accept_quest',q.try_interact() and q.quest_stage==1);check('early_reward_denied',not q.try_interact() and q.spirit_stones==0)
            state['min_z']=xyz(p)[2];state['phase']='walk'
        elif phase=='walk':
            c=route[state['index']];state['min_z']=min(state['min_z'],xyz(p)[2])
            if steer(p,c[1],c[2],t,32):state['phase']='measure'
        elif phase=='measure' and t>1:
            c=route[state['index']];v=xyz(p);d=math.hypot(c[1]-v[0],c[2]-v[1])
            ch={'arrived':d<30,'height':c[3]<v[2]<c[4],'walking':p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING,'no_fall':state['min_z']>50}
            report['route'].append({'id':c[0],'position_cm':v,'distance_cm':d,'checks':ch});write();check(c[0]+'_route',all(ch.values()))
            q=state['director']
            if c[0].startswith('herb'):
                n=int(c[0][-1]);check(c[0]+'_collect',q.try_interact() and q.herb_count==n);check(c[0]+'_duplicate_denied',not q.try_interact() and q.herb_count==n)
                if n==3:check('ready_to_deliver',q.quest_stage==2 and q.spirit_stones==0)
            if c[0]=='board':
                check('reward_once',q.try_interact() and q.quest_stage==3 and q.spirit_stones==10);check('duplicate_reward_denied',not q.try_interact() and q.spirit_stones==10)
                check('clouds_move',math.dist(xyz(state['cloud']),state['cloud_start'])>1);state['phase']='valley_next'
            else:state['index']+=1;state['phase']='walk'
        elif phase=='valley_next':
            seg=valley[state['m']]
            if seg[1]=='tp':
                z,lab=ground(p,seg[2],seg[3]);check(seg[0]+'_ground_found',z is not None)
                p.set_actor_location(u.Vector(seg[2],seg[3],z+110),False,True);p.character_movement.stop_movement_immediately();state['phase']='valley_settle'
            else:state['phase']='valley_walk'
        elif phase=='valley_settle' and t>2:
            seg=valley[state['m']];v=xyz(p);z,lab=ground(p,v[0],v[1],v[2])
            ch={'standing':p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING,'height_above_ground':80<v[2]-z<110}
            report['valley'].append({'id':seg[0],'kind':'teleport','position_cm':v,'ground_cm':z,'ground_actor':lab,'checks':ch});write();check(seg[0],all(ch.values()))
            state['m']+=1;state['phase']='valley_next';state['low']=1e9
        elif phase=='valley_walk':
            seg=valley[state['m']];v=xyz(p)
            if seg[1]=='blocked':state['closest']=min(state.get('closest',1e9),math.hypot(v[0]-seg[4][0],v[1]-seg[4][1]))
            z,_=ground(p,v[0],v[1],v[2]);state['low']=min(state.get('low',1e9),(v[2]-z) if z is not None else 1e9)
            if steer(p,seg[2],seg[3],t,22 if seg[1]=='blocked' else 40):state['phase']='valley_measure'
        elif phase=='valley_measure' and t>1:
            seg=valley[state['m']];v=xyz(p);d=math.hypot(seg[2]-v[0],seg[3]-v[1]);z,lab=ground(p,v[0],v[1],v[2])
            ch={'walking':p.character_movement.movement_mode==u.MovementMode.MOVE_WALKING,'height_above_ground':z is not None and 80<v[2]-z<110,'never_sank':state.get('low',1e9)>60}
            if seg[1]=='walk':ch['arrived']=d<30
            else:ch['kept_clear_of_trunk']=state['closest']>seg[5]
            report['valley'].append({'id':seg[0],'kind':seg[1],'position_cm':v,'ground_cm':z,'ground_actor':lab,'distance_to_target_cm':d,
                                     'closest_to_trunk_cm':state.pop('closest',None),'checks':ch});write();check(seg[0],all(ch.values()))
            state['low']=1e9
            if state['m']+1<len(valley):state['m']+=1;state['phase']='valley_next'
            else:
                q=state['director'];report.update(status='passed',objective=q.get_objective_text(),herbs=q.herb_count,spirit_stones=q.spirit_stones);write();state['phase']='hold'
        elif phase=='hold' and t>3:finish()
    except Exception:
        report.update(status='error',error=traceback.format_exc());write();finish()
handle=u.register_slate_post_tick_callback(tick);write()
