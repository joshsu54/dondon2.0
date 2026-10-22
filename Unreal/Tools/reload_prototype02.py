"""Validate saved material overrides before repeating runtime checks on the saved version."""
import unreal as u,json
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownPrototype_02')
assert world and world.get_name()=='TownPrototype_02'
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
missing=[];count=0
for a in actors:
    if isinstance(a,u.StaticMeshActor):
        c=a.static_mesh_component
        for i in range(c.get_num_materials()):
            m=c.get_material(i)
            if not m or '/Game/Art/Materials/SectPalette01/' not in m.get_path_name():missing.append(a.get_actor_label())
        count+=1
assert count==485 and not missing,(count,missing)
r=json.loads((root/'material_repair_validation.json').read_text())
r.update(reloaded_map=world.get_path_name(),mesh_actors_with_palette=count,missing_materials=missing,status='saved_and_reloaded_material_overrides_verified')
(root/'material_repair_validation.json').write_text(json.dumps(r,indent=2))
exec(compile((root/'Tools/playtest_prototype.py').read_text(),str(root/'Tools/playtest_prototype.py'),'exec'))
