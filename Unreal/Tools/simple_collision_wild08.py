"""Full editor: give the blocking WildVegetation08 meshes analytic simple collision (no triangle cooking needed).
Complex-as-simple left the pine and boulders with no collision when loaded from disk (traces and PIE passed through),
so: CommonPine gets one trunk capsule (canopy pads start 2.74 m up, so the character walks under it);
MossBoulderSet gets one box per large boulder (Boulder_00..02, 85 % of their Blender bounds; small stones stay open).
Trace flag becomes CTF_USE_DEFAULT so movement sweeps use these shapes. Blender->UE: x*100, -y*100, z*100 (verified below).
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
report={'status':'starting','shapes':{},'traces':{}}
def write():(root/'wild08_simple_collision.json').write_text(json.dumps(report,indent=2))
# Blender bounds (m) of the three large boulders, read from MossBoulderSet_v001.blend.
BOULDERS={'Boulder_00':([-1.055,-.863,0],[1.021,.796,1.516]),'Boulder_01':([.581,-.199,0],[1.545,.916,.68]),'Boulder_02':([-1.466,-.735,0],[-.357,.244,.788])}
def boxes(ysign):
    out=[]
    for lo,hi in BOULDERS.values():
        b=u.KBoxElem();c=[(lo[i]+hi[i])/2*100 for i in range(3)]
        b.set_editor_property('center',u.Vector(c[0],ysign*c[1],c[2]))
        for k,i in (('x',0),('y',1),('z',2)):b.set_editor_property(k,(hi[i]-lo[i])*100*(.85 if i<2 else .95))
        out.append(b)
    return out
def set_geom(mesh,sphyls=(),bxs=()):
    bs=mesh.get_editor_property('body_setup');g=bs.get_editor_property('agg_geom')
    g.set_editor_property('sphyl_elems',list(sphyls));g.set_editor_property('box_elems',list(bxs));g.set_editor_property('convex_elems',[])
    bs.set_editor_property('agg_geom',g);bs.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_DEFAULT)
    u.EditorAssetLibrary.save_loaded_asset(mesh)
def down(ctx,x,y):
    h=u.SystemLibrary.line_trace_single(ctx,u.Vector(x,y,400),u.Vector(x,y,-5),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,False)
    t=h.to_tuple() if h else None;return t[9].get_actor_label() if t and t[0] and t[9] else None
def sweep(ctx,a,b):
    h=u.SystemLibrary.capsule_trace_single(ctx,u.Vector(*a),u.Vector(*b),42,96,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,False)
    t=h.to_tuple() if h else None;return {'hit':t[9].get_actor_label() if t and t[0] and t[9] else None,'at':[t[4].x,t[4].y,t[4].z] if t and t[0] else None}
try:
    pine=u.load_asset('/Game/Art/WildVegetation08/Meshes/CommonPine');rock=u.load_asset('/Game/Art/WildVegetation08/Meshes/MossBoulderSet')
    cap=u.KSphylElem();cap.set_editor_property('center',u.Vector(0,0,130));cap.set_editor_property('radius',30.);cap.set_editor_property('length',200.)
    set_geom(pine,[cap]);report['shapes']['CommonPine']={'capsule_center_cm':[0,0,130],'radius_cm':30,'cylinder_length_cm':200}
    u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_08')
    acts=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    ctx=next(a for a in acts if a.get_actor_label()=='ValleyGround');r1=next(a for a in acts if a.get_actor_label()=='Wild08_MossBoulderSet_17')
    tf=r1.get_actor_transform()
    # Points inside Boulder_01 under one Y mapping only (local x 106 cm, y -50 vs +50).
    pa=tf.transform_location(u.Vector(106,-50,0));pb=tf.transform_location(u.Vector(106,50,0))
    for ysign in (-1,1):
        set_geom(rock,bxs=boxes(ysign));inside,outside=(pb,pa) if ysign==1 else (pa,pb)
        # Re-register so the edited body setup is used by the placed actors.
        for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
            if a.actor_has_tag('MossBoulderSet'):a.static_mesh_component.set_static_mesh(None);a.static_mesh_component.set_static_mesh(rock)
        ok=down(ctx,inside.x,inside.y)=='Wild08_MossBoulderSet_17' and down(ctx,outside.x,outside.y)!='Wild08_MossBoulderSet_17'
        report['traces']['ysign_%d'%ysign]=ok
        if ok:report['shapes']['MossBoulderSet']={'boxes':list(BOULDERS),'blender_to_ue_y_sign':ysign,'scale_xy':.85,'scale_z':.95};break
    assert 'MossBoulderSet' in report['shapes'],'Neither Y mapping matched; boxes not trusted'
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if a.actor_has_tag('CommonPine'):a.static_mesh_component.set_static_mesh(None);a.static_mesh_component.set_static_mesh(pine)
    report['traces']['pine_sweep']=sweep(ctx,(1900,2600,90),(1900,3600,90))
    report['traces']['under_canopy_sweep']=sweep(ctx,(1900+250,2600,90),(1900+250,3600,90))
    report['traces']['boulder_sweep']=sweep(ctx,(2650,3300,90),(2650,4900,90))
    write()
    assert report['traces']['pine_sweep']['hit']=='Wild08_CommonPine_01' and report['traces']['boulder_sweep']['hit']=='Wild08_MossBoulderSet_17'
    report['status']='saved_verified_in_editor_session';write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
