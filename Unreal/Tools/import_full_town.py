"""Import immutable TownLayout v004 into a new UE map. Run in full editor."""
import unreal as u
import json,re,hashlib,traceback,time
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
project_root=root.parent
report_path=root/'town_import_validation.json'
report={'status':'starting','map':'/Game/Maps/TownLayout_01','gameplay_verified':False}
def progress(status,**kw):
    report.update(status=status,**kw);report_path.write_text(json.dumps(report,indent=2));print('TOWN_IMPORT',status)
def clean(s):return re.sub(r'[^A-Za-z0-9_-]','_',s)
def run():
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    assert not u.EditorAssetLibrary.does_asset_exist(report['map']),'Map exists; preserve it and use a new version'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_map_packages(),'Unsaved map edits; save before importing'
    source=project_root/'Models/TownLayout/v004/TownLayout_v004.fbx'
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha=='97f0348cf17ade09c66c9d06eeb57f37fa72aed6c5dada0e48e24039cbc48f85'
    palette=json.loads((root/'town_palette.json').read_text())
    objects={clean(k):v for k,v in palette['objects'].items()}
    tools=u.AssetToolsHelpers.get_asset_tools()
    dest='/Game/Art/Town/TownLayout_v004'
    progress('importing_fbx',source_sha256=sha)
    paths=u.EditorAssetLibrary.list_assets(dest,True) if u.EditorAssetLibrary.does_directory_exist(dest) else []
    meshes=[m for p in paths if isinstance((m:=u.load_asset(p)),u.StaticMesh)]
    if not meshes:
        u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
        task=u.AssetImportTask()
        for k,v in [('filename',str(source)),('destination_path',dest),('automated',True),('save',True)]:task.set_editor_property(k,v)
        opt=u.FbxImportUI()
        for k,v in [('import_mesh',True),('import_as_skeletal',False),('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH),('automated_import_should_detect_type',False),('import_materials',False),('import_textures',False)]:opt.set_editor_property(k,v)
        data=opt.get_editor_property('static_mesh_import_data')
        for k,v in [('combine_meshes',False),('auto_generate_collision',True),('transform_vertex_to_absolute',True),('convert_scene',True),('convert_scene_unit',True),('generate_lightmap_u_vs',False),('build_nanite',False)]:data.set_editor_property(k,v)
        task.set_editor_property('options',opt);task.set_editor_property('factory',u.FbxFactory())
        tools.import_asset_tasks([task])
        meshes=[m for p in task.get_editor_property('imported_object_paths') if isinstance((m:=u.load_asset(p)),u.StaticMesh)]
    assert len(meshes)==3877,('Unexpected or partial import',len(meshes))
    unmatched=[m.get_name() for m in meshes if m.get_name() not in objects]
    assert not unmatched,unmatched[:20]
    for m in meshes:assert len(objects[m.get_name()])==len(m.get_editor_property('static_materials')),m.get_name()
    progress('creating_materials',mesh_count=len(meshes))
    mats={};dedup={}
    for name,d in palette['materials'].items():
        key=tuple(d['base_color_linear'][:3])+tuple([d['roughness'],d['metallic']])
        if key not in dedup:
            folder='/Game/Art/Materials/TownPalette01';an='M_'+clean(name)
            mat=u.load_asset(folder+'/'+an) if u.EditorAssetLibrary.does_asset_exist(folder+'/'+an) else None
            if mat is None:
                mat=tools.create_asset(an,folder,u.Material,u.MaterialFactoryNew())
                base=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-300,0)
                base.set_editor_property('constant',u.LinearColor(*d['base_color_linear'][:3],1))
                u.MaterialEditingLibrary.connect_material_property(base,'',u.MaterialProperty.MP_BASE_COLOR)
                for y,val,prop in [(150,d['roughness'],u.MaterialProperty.MP_ROUGHNESS),(300,d['metallic'],u.MaterialProperty.MP_METALLIC)]:
                    expr=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant,-300,y);expr.set_editor_property('r',val)
                    u.MaterialEditingLibrary.connect_material_property(expr,'',prop)
                u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
            dedup[key]=mat
        mats[name]=dedup[key]
    progress('assembling_map',unique_material_count=len(dedup))
    world=u.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    mins=[float('inf')]*3;maxs=[-float('inf')]*3
    for i,m in enumerate(meshes):
        m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        for j,n in enumerate(objects[m.get_name()]):m.set_material(j,mats[n])
        u.EditorAssetLibrary.save_loaded_asset(m)
        a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0))
        a.set_actor_label(m.get_name());a.set_folder_path('TownLayout_v004');a.static_mesh_component.set_static_mesh(m)
        box=m.get_bounding_box()
        for j,axis in enumerate(('x','y','z')):
            mins[j]=min(mins[j],getattr(box.min,axis));maxs[j]=max(maxs[j],getattr(box.max,axis))
        if i%250==0:progress('assembling_map',placed_meshes=i+1)
    def spawn(cls,label,pos):
        a=actors.spawn_actor_from_class(cls,u.Vector(*pos));a.set_actor_label(label);return a
    sun=spawn(u.DirectionalLight,'TownSun',(0,0,1000))
    sun.set_actor_rotation(u.Rotator(pitch=-40,yaw=-125,roll=0),False)
    sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_editor_property('intensity',3.)
    sky=spawn(u.SkyLight,'TownSkyLight',(0,0,1000));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('real_time_capture',True);sky.light_component.set_editor_property('intensity',1.2)
    spawn(u.SkyAtmosphere,'TownAtmosphere',(0,0,0))
    start=spawn(u.PlayerStart,'TownEntrance',(0,850,140));start.set_actor_rotation(u.Rotator(pitch=0,yaw=-90,roll=0),False)
    world.get_world_settings().set_editor_property('default_game_mode',u.load_class(None,'/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.BP_ThirdPersonGameMode_C'))
    assert u.EditorLoadingAndSavingUtils.save_map(world,report['map'])
    world=u.EditorLoadingAndSavingUtils.load_map(report['map']);assert world.get_name()=='TownLayout_01'
    meshes_in_map=[a for a in actors.get_all_level_actors() if isinstance(a,u.StaticMeshActor)]
    assert len(meshes_in_map)==3877
    missing=[a.get_actor_label() for a in meshes_in_map if any(a.static_mesh_component.get_material(i) is None for i in range(a.static_mesh_component.get_num_materials()))]
    assert not missing,missing
    loc=u.Vector(6200,5900,5600);target=u.Vector(0,-1200,250)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,target))
    progress('saved_and_reloaded_pending_visual_runtime',actor_count=len(actors.get_all_level_actors()),bounds_cm={'min':mins,'max':maxs},missing_materials=missing,limits=['Procedural colors approximated; no baked textures','Complex-as-simple collision for stationary prototype','No navigation or interaction acceptance yet'])
try:run()
except Exception:
    progress('failed',error=traceback.format_exc());raise
