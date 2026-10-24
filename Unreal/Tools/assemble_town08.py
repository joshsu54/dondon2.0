"""NOT YET RUN. Use only in the real project after the XiuXianTown C++ module compiles (needs VS 2022 17.8+).
Loads TownLayout_07, streams in /Game/Maps/Sublevels/TownWild08_Sublevel (always loaded) and saves a new
/Game/Maps/TownLayout_08. Refuses to overwrite 08, never saves 07, and checks the quest actors survived.
UnrealEditor <uproject> -ExecutePythonScript=<this>   (full editor, module loaded)
"""
import unreal as u
import json,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
NEW='/Game/Maps/TownLayout_08';SUB='/Game/Maps/Sublevels/TownWild08_Sublevel'
report={'status':'starting','map':NEW,'base':'/Game/Maps/TownLayout_07','sublevel':SUB}
def write():(root/'town08_assembly.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
try:
    assert u.load_class(None,'/Script/XiuXianTown.SectQuestDirector'),'Quest module not loaded; do not save 08 without it'
    assert not u.EditorAssetLibrary.does_asset_exist(NEW),'Never overwrite an existing 08'
    base=root/'XiuXianTown/Content/Maps/TownLayout_07.umap';report['base_sha256']=hashlib.sha256(base.read_bytes()).hexdigest()
    world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_07')
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    before=len(actors.get_all_level_actors());report['base_actor_count']=before
    assert u.EditorLevelUtils.add_level_to_world(world,SUB,u.LevelStreamingAlwaysLoaded)
    assert u.EditorLoadingAndSavingUtils.save_map(world,NEW)
    world=u.EditorLoadingAndSavingUtils.load_map(NEW);all_actors=actors.get_all_level_actors()
    report['checks']={'wild_actors':len([a for a in all_actors if a.actor_has_tag('WildVegetation08')])==24,
        'quest_herbs':len([a for a in all_actors if a.actor_has_tag('QuestHerb')])==3,
        'quest_board':len([a for a in all_actors if a.actor_has_tag('QuestBoard')])==1,
        'base_actor_count_kept':len(all_actors)-24==before,
        'base_07_unchanged':hashlib.sha256(base.read_bytes()).hexdigest()==report['base_sha256']}
    assert all(report['checks'].values()),report['checks']
    report['status']='saved_reloaded_pending_pie_and_visual';write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
