"""Full editor: enable per-section collision on the WildVegetation08 meshes meant to block (pine, boulders),
save those two mesh assets, then verify with physics traces in TownLayout_08. Maps are not saved.
Context: the meshes were imported by commandlet; PIE and traces showed no collision although the
body setup was Complex-as-Simple and actors used BlockAll.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
report={'status':'starting','meshes':{},'traces':{}}
def write():(root/'wild08_collision_fix.json').write_text(json.dumps(report,indent=2))
try:
    lib=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)  # EditorStaticMeshLibrary is gone in 5.8
    for aid in ['CommonPine','MossBoulderSet','BambooClump']:
        m=u.load_asset('/Game/Art/WildVegetation08/Meshes/'+aid);n=m.get_num_sections(0)
        before=[lib.is_section_collision_enabled(m,0,i) for i in range(n)]
        rec={'sections':n,'collision_before':before}
        if aid!='BambooClump':  # bamboo, shrub and scree stay walk-through by design
            for i in range(n):
                if not before[i]:lib.enable_section_collision(m,True,0,i)
            m.get_editor_property('body_setup').set_editor_property('double_sided_geometry',True)
            u.EditorAssetLibrary.save_loaded_asset(m)
            rec['collision_after']=[lib.is_section_collision_enabled(m,0,i) for i in range(n)]
        report['meshes'][aid]=rec
    write()
    u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_08')
    ctx=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.actor_has_tag('CommonPine'))
    for name,a,b in [('pine_trunk_y',(1900,2600,80),(1900,3600,80)),('pine_trunk_x',(1500,3100,80),(2300,3100,80)),('boulder',(2650,3300,60),(2650,4900,60)),('railing_reference',(-1200,-5200,250),(-1200,-3700,250))]:
        hit=u.SystemLibrary.line_trace_single(ctx,u.Vector(*a),u.Vector(*b),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],u.DrawDebugTrace.NONE,True).to_tuple()
        report['traces'][name]={'hit':bool(hit[0]),'actor':hit[9].get_actor_label() if hit[0] and hit[9] else None,'location':[hit[4].x,hit[4].y,hit[4].z] if hit[0] else None}
    report['status']='done';write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
