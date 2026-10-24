"""Integrate the reviewed terrain into a new map, preserving TownLayout_10."""
import unreal as u,json,re,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;repo=root.parent
SRC=repo/'Models/LingyunValleyTerrain/v002/Unreal11'
MD='/Game/Art/Terrain11/Meshes';MAT='/Game/Art/Terrain11/Materials';NEW='/Game/Maps/TownLayout_11'
report={'status':'building','map':NEW,'base':'/Game/Maps/TownLayout_10'}
def write():(root/'terrain11_build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def clean(s):return re.sub(r'[^A-Za-z0-9_]','_',str(s))
try:
    assert not u.EditorAssetLibrary.does_asset_exist(NEW),'Preserve existing 11'
    base=root/'XiuXianTown/Content/Maps/TownLayout_10.umap';before=hashlib.sha256(base.read_bytes()).hexdigest()
    manifest=json.loads((SRC/'manifest.json').read_text());tools=u.AssetToolsHelpers.get_asset_tools();L=u.MaterialEditingLibrary
    mats={}
    for name,color in manifest['materials'].items():
        key=clean(name);m=u.load_asset(MAT+'/M_'+key)
        if not m:
            m=tools.create_asset('M_'+key,MAT,u.Material,u.MaterialFactoryNew())
            def expr(cls):return L.create_material_expression(m,cls)
            def rgb(c):
                n=expr(u.MaterialExpressionConstant3Vector);n.set_editor_property('constant',u.LinearColor(*c[:3],1));return n
            col=rgb(color)
            if name=='Terrain_Meadow':
                a=rgb((.09,.16,.025));b=rgb((.29,.24,.10));pos=expr(u.MaterialExpressionWorldPosition)
                scale=expr(u.MaterialExpressionMultiply);scale.set_editor_property('const_b',.002);L.connect_material_expressions(pos,'',scale,'A')
                noise=expr(u.MaterialExpressionNoise);noise.set_editor_property('scale',1.0);L.connect_material_expressions(scale,'',noise,'Position')
                lerp=expr(u.MaterialExpressionLinearInterpolate)
                for n,p in [(a,'A'),(b,'B'),(noise,'Alpha')]:L.connect_material_expressions(n,'',lerp,p)
                col=lerp
            elif 'KarstRock' in name:
                a=rgb((.38,.40,.32));b=rgb((.10,.17,.035));normal=expr(u.MaterialExpressionVertexNormalWS)
                mask=expr(u.MaterialExpressionComponentMask)
                for k,v in [('r',False),('g',False),('b',True),('a',False)]:mask.set_editor_property(k,v)
                L.connect_material_expressions(normal,'',mask,'')
                sub=expr(u.MaterialExpressionSubtract);sub.set_editor_property('const_b',.65);L.connect_material_expressions(mask,'',sub,'A')
                mul=expr(u.MaterialExpressionMultiply);mul.set_editor_property('const_b',4);L.connect_material_expressions(sub,'',mul,'A')
                sat=expr(u.MaterialExpressionSaturate);L.connect_material_expressions(mul,'',sat,'')
                lerp=expr(u.MaterialExpressionLinearInterpolate)
                for n,p in [(a,'A'),(b,'B'),(sat,'Alpha')]:L.connect_material_expressions(n,'',lerp,p)
                col=lerp
            L.connect_material_property(col,'',u.MaterialProperty.MP_BASE_COLOR)
            rough=expr(u.MaterialExpressionConstant);rough.set_editor_property('r',.9);L.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
            m.set_editor_property('two_sided',True);L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
        mats[key]=m
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0');meshes={}
    for name,info in manifest['meshes'].items():
        mesh=u.load_asset(MD+'/'+name)
        if not mesh:
            task=u.AssetImportTask()
            for k,v in [('filename',str(SRC/(name+'.fbx'))),('destination_path',MD),('destination_name',name),('automated',True),('save',True)]:task.set_editor_property(k,v)
            opt=u.FbxImportUI()
            for k,v in [('import_mesh',True),('import_as_skeletal',False),('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH),('automated_import_should_detect_type',False),('import_materials',False),('import_textures',False)]:opt.set_editor_property(k,v)
            data=opt.get_editor_property('static_mesh_import_data')
            for k,v in [('combine_meshes',True),('auto_generate_collision',False),('transform_vertex_to_absolute',True),('convert_scene',True),('convert_scene_unit',True),('generate_lightmap_u_vs',False),('build_nanite',False)]:data.set_editor_property(k,v)
            task.set_editor_property('options',opt);task.set_editor_property('factory',u.FbxFactory());tools.import_asset_tasks([task]);mesh=u.load_asset(MD+'/'+name)
        assert mesh,name
        for i,slot in enumerate(mesh.get_editor_property('static_materials')):
            key=clean(slot.get_editor_property('imported_material_slot_name'));assert key in mats,(name,key);mesh.set_material(i,mats[key])
        body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);body.set_editor_property('double_sided_geometry',True)
        u.EditorAssetLibrary.save_loaded_asset(mesh);meshes[name]=mesh
        bounds=mesh.get_bounding_box();dims=[getattr(bounds.max,k)-getattr(bounds.min,k) for k in 'xyz'];expected=[(info['bounds_m'][1][i]-info['bounds_m'][0][i])*100 for i in range(3)]
        assert all(abs(a-b)<max(3,b*.01) for a,b in zip(dims,expected)),(name,dims,expected)
        report.setdefault('meshes',{})[name]={'dimensions_cm':dims,'triangles':mesh.get_num_triangles(0)};write()
    u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_10');actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    remove=('ValleyGround','ValleyRidge_','DistantPeak_','NorthTrailBase','MiddleTrailRock','UpperTrailRock','SectGateTerrace','TownLayout_v004_North_Terrace_Ground','TownLayout_v004_Terrain_Display_Island')
    removed=[]
    for a in list(actors.get_all_level_actors()):
        if a.get_actor_label().startswith(remove):removed.append(a.get_actor_label());actors.destroy_actor(a)
    for name,mesh in meshes.items():
        a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));a.set_actor_label(name);a.set_folder_path('Terrain11')
        a.static_mesh_component.set_static_mesh(mesh);a.set_actor_enable_collision(name!='ValleyDressing11')
        a.static_mesh_component.set_collision_profile_name('BlockAll' if name!='ValleyDressing11' else 'NoCollision')
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert u.EditorLoadingAndSavingUtils.save_map(world,NEW)
    u.EditorLoadingAndSavingUtils.load_map(NEW)
    report.update(status='saved_pending_runtime_validation',removed=removed,base_unchanged=hashlib.sha256(base.read_bytes()).hexdigest()==before)
    assert report['base_unchanged'];write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write()
finally:u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
