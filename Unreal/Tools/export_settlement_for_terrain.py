"""Read-only export of existing settlement geometry for a separate Blender terrain study."""
import unreal as u
import json,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parents[1]
out=root/'Models/LingyunValleyTerrain/v001/Source'
out.mkdir(parents=True,exist_ok=True)
report={'status':'starting','map':'/Game/Maps/TownLayout_10'}
try:
    source=root/'Unreal/XiuXianTown/Content/Maps/TownLayout_10.umap'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    world=u.EditorLoadingAndSavingUtils.load_map(report['map'])
    subsystem=u.get_editor_subsystem(u.EditorActorSubsystem)
    selected=[];rows=[]
    excluded=('ValleyGround','ValleyRidge','DistantPeak','DriftingCloud','NorthTrailBase','MiddleTrailRock','UpperTrailRock','SectGateTerrace')
    for a in subsystem.get_all_level_actors():
        if not isinstance(a,u.StaticMeshActor):continue
        label=a.get_actor_label()
        if label.startswith(excluded) or a.actor_has_tag('SectInteract'):continue
        c=a.static_mesh_component
        if not c.static_mesh:continue
        selected.append(a)
        p=a.get_actor_location();b,e=a.get_actor_bounds(False)
        rows.append({'name':label,'position_cm':[p.x,p.y,p.z],
                     'bounds_cm':[[b.x-e.x,b.y-e.y,b.z-e.z],[b.x+e.x,b.y+e.y,b.z+e.z]]})
    subsystem.set_selected_level_actors(selected)
    task=u.AssetExportTask();task.set_editor_property('object',world)
    task.set_editor_property('filename',str(out/'Settlement10.fbx'))
    task.set_editor_property('automated',True);task.set_editor_property('replace_identical',False)
    task.set_editor_property('selected',True);task.set_editor_property('prompt',False)
    task.set_editor_property('exporter',u.LevelExporterFBX())
    options=u.FbxExportOption();options.set_editor_property('level_of_detail',False)
    options.set_editor_property('collision',False);options.set_editor_property('ascii',False)
    task.set_editor_property('options',options)
    assert u.Exporter.run_asset_export_task(task)
    assert (out/'Settlement10.fbx').stat().st_size>1000
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    report.update(status='exported',actor_count=len(selected),source_map_unchanged=True,actors=rows)
except Exception:
    report.update(status='error',error=traceback.format_exc())
finally:
    (out/'export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
