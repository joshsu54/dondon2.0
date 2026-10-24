"""Attach the local-camp worker system to a new map; preserve the validated terrain map."""
import unreal as u,json,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;NEW='/Game/Maps/TownLayout_12';out=root/'workers12_build.json'
try:
    assert not u.EditorAssetLibrary.does_asset_exist(NEW),'Preserve existing 12'
    src=root/'XiuXianTown/Content/Maps/TownLayout_11.umap';before=hashlib.sha256(src.read_bytes()).hexdigest()
    u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_11');actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    counts={}
    for i,tag in enumerate(['SectShiDi','SectApplicantLin','SectApplicantYue']):
        counts[tag]=0
        for a in actors.get_all_level_actors():
            if a.get_actor_label() in [tag+'_Robe',tag+'_Head',tag+'_Belt',tag+'_Marker','Sign_'+['SHI DI','LIN XI','YUE QING'][i]]:
                a.tags=list(a.tags)+[u.Name('WorkerPart%d'%i)];a.root_component.set_mobility(u.ComponentMobility.MOVABLE);counts[tag]+=1
            if a.actor_has_tag(tag):a.root_component.set_mobility(u.ComponentMobility.MOVABLE)
        assert counts[tag]==5,(tag,counts)
    cls=u.load_class(None,'/Script/XiuXianTown.SectWorkers');assert cls
    a=actors.spawn_actor_from_class(cls,u.Vector(0,0,0));a.set_actor_label('SectWorkers12')
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert u.EditorLoadingAndSavingUtils.save_map(world,NEW)
    u.EditorLoadingAndSavingUtils.load_map(NEW)
    out.write_text(json.dumps({'status':'saved','map':NEW,'parts':counts,'base_11_unchanged':hashlib.sha256(src.read_bytes()).hexdigest()==before},indent=2))
except Exception:out.write_text(json.dumps({'status':'error','error':traceback.format_exc()}))
finally:u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
