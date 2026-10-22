import unreal, json
from pathlib import Path
project = Path(unreal.Paths.project_dir())
checks = {}
for path in ['/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode', '/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter','/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple','/Game/Input/IMC_Default']:
    asset = unreal.load_asset(path)
    checks[path] = asset is not None
checks['editor_version'] = unreal.SystemLibrary.get_engine_version()
world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownPrototype_01')
checks['prototype_map_loaded'] = world is not None
if world:
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    checks['prototype_actor_count'] = len(actors)
    checks['player_start_count'] = sum(isinstance(a, unreal.PlayerStart) for a in actors)
    checks['static_mesh_actor_count'] = sum(isinstance(a, unreal.StaticMeshActor) for a in actors)
    checks['default_game_mode'] = str(world.get_world_settings().get_editor_property('default_game_mode'))
checks['gameplay_verified'] = False
checks['map_api'] = [n for n in dir(unreal.EditorLoadingAndSavingUtils) if 'map' in n or 'save' in n]
checks['mesh_api'] = [n for n in dir(unreal.StaticMeshEditorSubsystem) if 'collision' in n or 'bound' in n]
(project.parent / 'engine_check.json').write_text(json.dumps(checks, indent=2))
print('XIU_ENGINE_CHECK', checks)
