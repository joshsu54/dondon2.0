"""Full editor: respawn the 24 WildVegetation08 actors inside TownWild08_Sublevel with identical label, transform,
mesh, tags and collision, then save the sublevel. The commandlet-spawned actors loaded from disk with no physics
(traces and PIE passed through), while GUI-spawned Expansion06 actors collide normally.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
SUB='/Game/Maps/Sublevels/TownWild08_Sublevel';umap=root/'XiuXianTown/Content/Maps/Sublevels/TownWild08_Sublevel.umap'
report={'status':'starting','sublevel':SUB,'before_sha256':hashlib.sha256(umap.read_bytes()).hexdigest()}
def write():(root/'wild08_actor_rebuild.json').write_text(json.dumps(report,indent=2))
try:
    eas=u.get_editor_subsystem(u.EditorActorSubsystem);les=u.get_editor_subsystem(u.LevelEditorSubsystem)
    u.EditorLoadingAndSavingUtils.load_map(SUB)
    old=[a for a in eas.get_all_level_actors() if a.actor_has_tag('WildVegetation08')];assert len(old)==24,len(old)
    rows=[]
    for a in old:
        c=a.static_mesh_component
        rows.append({'label':a.get_actor_label(),'loc':a.get_actor_location(),'rot':a.get_actor_rotation(),'scale':a.get_actor_scale3d(),
                     'mesh':c.static_mesh,'tags':list(a.tags),'collision':a.get_actor_enable_collision()})
    for a in old:eas.destroy_actor(a)
    for r in rows:
        a=eas.spawn_actor_from_class(u.StaticMeshActor,r['loc'],r['rot']);a.set_actor_label(r['label']);a.set_folder_path('WildVegetation08')
        a.static_mesh_component.set_static_mesh(r['mesh']);a.set_actor_scale3d(r['scale']);a.set_actor_rotation(r['rot'],False)
        a.set_actor_enable_collision(r['collision']);a.set_editor_property('tags',r['tags'])
    assert les.save_current_level()
    u.EditorLoadingAndSavingUtils.load_map(SUB)
    new={a.get_actor_label():a for a in eas.get_all_level_actors() if a.actor_has_tag('WildVegetation08')}
    report['checks']={'count':len(new)==24,'same_transforms':all((new[r['label']].get_actor_location()-r['loc']).length()<.1 and new[r['label']].static_mesh_component.static_mesh==r['mesh'] and new[r['label']].get_actor_enable_collision()==r['collision'] for r in rows)}
    assert all(report['checks'].values()),report['checks']
    report.update(status='rebuilt_saved_reloaded',after_sha256=hashlib.sha256(umap.read_bytes()).hexdigest());write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
