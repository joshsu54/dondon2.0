"""Run full UnrealEditor -ExecutePythonScript=<this file>; FBX import requires Slate.

Rebuilds TownPrototype_01. Preserve manual map edits in another map before rerunning.
"""
import unreal as u
import json, hashlib
from pathlib import Path

project = Path(u.Paths.project_dir()).resolve()
root = project.parents[1]
manifest = json.loads((root / 'Unreal/import_manifest.json').read_text())
report = {'engine': u.SystemLibrary.get_engine_version(), 'imports': [], 'status': 'in_progress', 'gameplay_verified': False}
report_path = root / 'Unreal/import_validation.json'
asset_tools = u.AssetToolsHelpers.get_asset_tools()
u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
all_meshes = {}
for row in manifest['assets']:
    if row['id'] == 'TownLayout_v004':
        continue
    source = root / row['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == row['sha256'], str(source)
    target = row['destination']
    paths = u.EditorAssetLibrary.list_assets(target, recursive=True) if u.EditorAssetLibrary.does_directory_exist(target) else []
    if not paths:
        task = u.AssetImportTask()
        task.set_editor_property('filename', str(source))
        task.set_editor_property('destination_path', target)
        task.set_editor_property('automated', True)
        task.set_editor_property('save', True)
        options = u.FbxImportUI()
        options.set_editor_property('import_mesh', True)
        options.set_editor_property('import_as_skeletal', False)
        options.set_editor_property('mesh_type_to_import', u.FBXImportType.FBXIT_STATIC_MESH)
        options.set_editor_property('automated_import_should_detect_type', False)
        options.set_editor_property('import_materials', True)
        options.set_editor_property('import_textures', False)
        mesh_options = options.get_editor_property('static_mesh_import_data')
        for name, value in [('combine_meshes', False), ('auto_generate_collision', True), ('transform_vertex_to_absolute', True), ('convert_scene', True), ('convert_scene_unit', True), ('generate_lightmap_u_vs', False), ('build_nanite', False)]:
            mesh_options.set_editor_property(name, value)
        task.set_editor_property('options', options)
        task.set_editor_property('factory', u.FbxFactory())
        asset_tools.import_asset_tasks([task])
        paths = list(task.get_editor_property('imported_object_paths'))
    meshes = [a for p in paths if isinstance((a := u.load_asset(p)), u.StaticMesh)]
    assert meshes, 'No imported meshes: ' + row['id']
    mins, maxs = [float('inf')]*3, [-float('inf')]*3
    for mesh in meshes:
        bounds = mesh.get_bounding_box()
        for i, axis in enumerate(('x', 'y', 'z')):
            mins[i] = min(mins[i], getattr(bounds.min, axis)); maxs[i] = max(maxs[i], getattr(bounds.max, axis))
        body = mesh.get_editor_property('body_setup')
        body.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        u.EditorAssetLibrary.save_loaded_asset(mesh)
    dims = [maxs[i]-mins[i] for i in range(3)]
    if 'expected_total_bounds_cm' in row:
        assert max(abs(a-b) for a,b in zip(sorted(dims),sorted(row['expected_total_bounds_cm']))) < 1.0, (row['id'],dims)
    all_meshes[row['id']] = meshes
    report['imports'].append({'id': row['id'], 'source_sha256': row['sha256'], 'mesh_count':len(meshes), 'bounds_cm':dims, 'collision':'complex_as_simple_static_prototype', 'assets':[m.get_path_name() for m in meshes]})
    report_path.write_text(json.dumps(report, indent=2))
world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
def spawn(cls, label, pos, rotation=u.Rotator()):
    obj = actors.spawn_actor_from_class(cls,u.Vector(*pos),rotation)
    obj.set_actor_label(label)
    return obj
floor = spawn(u.StaticMeshActor,'PrototypeGround',(0,0,-10))
floor.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(u.Vector(60,60,.2))
for aid, offset in [('UnitCube_1m',(300,0,0)),('TownBench_v001',(300,300,0)),('StarterHouse_v004',(1000,800,0))]:
    for mesh in all_meshes[aid]:
        actor = spawn(u.StaticMeshActor, aid+'_'+mesh.get_name(), offset)
        actor.static_mesh_component.set_static_mesh(mesh)
sun = spawn(u.DirectionalLight,'Sun',(0,0,600),u.Rotator(-45,-35,0))
sun.light_component.set_editor_property('intensity',3.0)
sky = spawn(u.SkyLight,'SkyLight',(0,0,500))
sky.light_component.set_editor_property('intensity',1.0)
spawn(u.SkyAtmosphere,'SkyAtmosphere',(0,0,0))
spawn(u.PlayerStart,'PlayerStart',(0,0,110))
world.get_world_settings().set_editor_property('default_game_mode',u.load_class(None,'/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.BP_ThirdPersonGameMode_C'))
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Maps/TownPrototype_01')
report.update(status='imported_and_map_saved',map='/Game/Maps/TownPrototype_01',actor_count=len(actors.get_all_level_actors()),limits=['Full town not imported yet','Collision set for stationary prototype only; character testing pending','Blender procedural materials are not baked textures'])
report_path.write_text(json.dumps(report,indent=2))
print('XIU_IMPORT_COMPLETE', report['map'])
