"""Create TownLayout_10 from 09 with the LingyunValley15 terrain (full editor; never saves 09, never overwrites 10).
- imports ArtLibrary/ExpansionBatches/LingyunValley15/UE/*.fbx (world-space vertices; actors at the origin)
- removes the two UE ground plates the terrain replaces
- removes the WildVegetation08 streaming sublevel and places the LingyunValley15 vegetation scatter instead
- lowers ValleyGround and the distant ridge/peak actors by 50 cm so the terrain is the only surface at -15 cm
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,re,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;repo=root.parent
BATCH=repo/'ArtLibrary/ExpansionBatches/LingyunValley15';UE=BATCH/'UE'
NEW='/Game/Maps/TownLayout_10';BASE='/Game/Maps/TownLayout_09'
MESH_DIR='/Game/Art/LingyunValley10/Meshes';MAT_DIR='/Game/Art/LingyunValley10/Materials'
PLATES=('TownLayout_v004_Terrain_Display_Island','TownLayout_v004_North_Terrace_Ground')
LOWER=('ValleyGround','ValleyRidge_','DistantPeak_');DROP_CM=50.
VEG_COLLISION={'CommonPine':True,'MossBoulderSet':True,'BambooClump':False,'WildShrub':False,'ScreePile':False}
report={'status':'starting','map':NEW,'base':BASE}
def write():(root/'expansion10_build.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
def clean(s):return re.sub(r'[^A-Za-z0-9_]','_',s)
L=u.MaterialEditingLibrary
def const3(mat,c,x,y):
    e=L.create_material_expression(mat,u.MaterialExpressionConstant3Vector,x,y);e.set_editor_property('constant',u.LinearColor(*c,1));return e
def make_material(name,d):
    an='M_'+clean(name);mat=u.load_asset(MAT_DIR+'/'+an)
    if mat:return mat
    mat=u.AssetToolsHelpers.get_asset_tools().create_asset(an,MAT_DIR,u.Material,u.MaterialFactoryNew())
    a=const3(mat,d['color'],-600,0)
    if name=='LY15_Meadow':   # grass -> dirt by vertex colour R (the baked 'dirt' attribute)
        b=const3(mat,d['second'],-600,140);vc=L.create_material_expression(mat,u.MaterialExpressionVertexColor,-600,300)
        lerp=L.create_material_expression(mat,u.MaterialExpressionLinearInterpolate,-250,80)
        L.connect_material_expressions(a,'',lerp,'A');L.connect_material_expressions(b,'',lerp,'B');L.connect_material_expressions(vc,'R',lerp,'Alpha')
        L.connect_material_property(lerp,'',u.MaterialProperty.MP_BASE_COLOR)
    elif d.get('second'):     # limestone with moss on upward world normals
        b=const3(mat,d['second'],-600,140);n=L.create_material_expression(mat,u.MaterialExpressionVertexNormalWS,-900,300)
        mk=L.create_material_expression(mat,u.MaterialExpressionComponentMask,-760,300)
        for k,v in (('r',False),('g',False),('b',True),('a',False)):mk.set_editor_property(k,v)
        sub=L.create_material_expression(mat,u.MaterialExpressionSubtract,-640,300);sub.set_editor_property('const_b',.55)
        mul=L.create_material_expression(mat,u.MaterialExpressionMultiply,-520,300);mul.set_editor_property('const_b',4.)
        sat=L.create_material_expression(mat,u.MaterialExpressionSaturate,-420,300);lerp=L.create_material_expression(mat,u.MaterialExpressionLinearInterpolate,-250,80)
        L.connect_material_expressions(n,'',mk,'');L.connect_material_expressions(mk,'',sub,'A');L.connect_material_expressions(sub,'',mul,'A');L.connect_material_expressions(mul,'',sat,'')
        L.connect_material_expressions(a,'',lerp,'A');L.connect_material_expressions(b,'',lerp,'B');L.connect_material_expressions(sat,'',lerp,'Alpha')
        L.connect_material_property(lerp,'',u.MaterialProperty.MP_BASE_COLOR)
    else:L.connect_material_property(a,'',u.MaterialProperty.MP_BASE_COLOR)
    for y,v,p in ((420,d['roughness'],u.MaterialProperty.MP_ROUGHNESS),(540,d['metallic'],u.MaterialProperty.MP_METALLIC)):
        e=L.create_material_expression(mat,u.MaterialExpressionConstant,-600,y);e.set_editor_property('r',v);L.connect_material_property(e,'',p)
    L.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat);return mat
try:
    assert u.load_class(None,'/Script/XiuXianTown.SectQuestDirector'),'Quest module must be loaded'
    assert not u.EditorAssetLibrary.does_asset_exist(NEW),'Never overwrite an existing 10'
    base=root/'XiuXianTown/Content/Maps/TownLayout_09.umap';report['base09_sha256']=hashlib.sha256(base.read_bytes()).hexdigest()
    pal=json.loads((UE/'ue15_palette.json').read_text())
    for k,v in pal['parts'].items():assert hashlib.sha256((UE/v['fbx']).read_bytes()).hexdigest()==v['sha256'],k
    world=u.EditorLoadingAndSavingUtils.load_map(BASE);eas=u.get_editor_subsystem(u.EditorActorSubsystem)
    allbase=eas.get_all_level_actors();base_count=len(allbase);report['base_actor_count']=base_count
    wild08=len([a for a in allbase if a.actor_has_tag('WildVegetation08')]);report['wild08_actors_removed_with_sublevel']=wild08
    mats={k:make_material(k,v) for k,v in pal['materials'].items()}
    tools=u.AssetToolsHelpers.get_asset_tools();u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    meshes={};report['meshes']={}
    for part,v in pal['parts'].items():
        mesh=u.load_asset(MESH_DIR+'/'+part)
        if not mesh:
            t=u.AssetImportTask()
            for k,val in (('filename',str(UE/v['fbx'])),('destination_path',MESH_DIR),('destination_name',part),('automated',True),('save',True)):t.set_editor_property(k,val)
            o=u.FbxImportUI()
            for k,val in (('import_mesh',True),('import_as_skeletal',False),('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH),('automated_import_should_detect_type',False),('import_materials',False),('import_textures',False)):o.set_editor_property(k,val)
            sd=o.get_editor_property('static_mesh_import_data')
            for k,val in (('combine_meshes',True),('auto_generate_collision',False),('transform_vertex_to_absolute',True),('convert_scene',True),('convert_scene_unit',True),
                          ('generate_lightmap_u_vs',False),('build_nanite',False),('vertex_color_import_option',u.VertexColorImportOption.REPLACE)):sd.set_editor_property(k,val)
            t.set_editor_property('options',o);t.set_editor_property('factory',u.FbxFactory());tools.import_asset_tasks([t]);mesh=u.load_asset(MESH_DIR+'/'+part)
        assert isinstance(mesh,u.StaticMesh),part
        for i,slot in enumerate(mesh.get_editor_property('static_materials')):
            key=str(slot.get_editor_property('imported_material_slot_name'))
            key=key if key in mats else next((m for m in mats if clean(m)==clean(key)),None);assert key,(part,slot)
            mesh.set_material(i,mats[key])
        bs=mesh.get_editor_property('body_setup');bs.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);bs.set_editor_property('double_sided_geometry',True)
        u.EditorAssetLibrary.save_loaded_asset(mesh);meshes[part]=mesh
        b=mesh.get_bounding_box();lo,hi=v['bounds_m']
        exp=([lo[0]*100,-hi[1]*100,lo[2]*100],[hi[0]*100,-lo[1]*100,hi[2]*100])   # Blender (x,y,z) m -> UE (x,-y,z) cm
        got=([b.min.x,b.min.y,b.min.z],[b.max.x,b.max.y,b.max.z]);err=max(abs(g-e) for G,E in zip(got,exp) for g,e in zip(G,E))
        report['meshes'][part]={'bounds_cm':got,'bounds_error_cm':err};assert err<2.,(part,got,exp)
    for part,mesh in meshes.items():
        a=eas.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0));a.set_actor_label(part);a.set_folder_path('LingyunValley10')
        a.static_mesh_component.set_static_mesh(mesh);a.set_actor_enable_collision(True);a.set_editor_property('tags',[u.Name('LingyunValley10')])
    removed=[]
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() in PLATES:removed.append(a.get_actor_label());eas.destroy_actor(a)
    assert sorted(removed)==sorted(PLATES),removed
    lowered=[]
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(LOWER):
            l=a.get_actor_location();a.set_actor_location(u.Vector(l.x,l.y,l.z-DROP_CM),False,False);lowered.append(a.get_actor_label())
    def wild08_levels(w):return [lv for lv in u.EditorLevelUtils.get_levels(w) if 'TownWild08' in lv.get_path_name()]
    sub=wild08_levels(world);assert len(sub)==1,[lv.get_path_name() for lv in u.EditorLevelUtils.get_levels(world)]
    assert u.EditorLevelUtils.remove_level_from_world(sub[0]),'sublevel removal failed'
    sc=json.loads((BATCH/'Models/LingyunValley/v001/vegetation_scatter_ue.json').read_text())['placements'];vm={}
    for i,p in enumerate(sc):
        mesh=vm.get(p['asset']) or vm.setdefault(p['asset'],u.load_asset('/Game/Art/WildVegetation08/Meshes/'+p['asset']))
        a=eas.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*p['ue_location_cm']));a.set_actor_label('LY10_%s_%03d'%(p['asset'],i));a.set_folder_path('LingyunValley10/Vegetation')
        a.static_mesh_component.set_static_mesh(mesh);s=p['scale'];a.set_actor_scale3d(u.Vector(s,s,s));a.set_actor_rotation(u.Rotator(pitch=0,yaw=p['ue_yaw_deg'],roll=0),False)
        a.set_actor_enable_collision(VEG_COLLISION[p['asset']]);a.set_editor_property('tags',[u.Name('LingyunValley10'),u.Name('LY10Vegetation'),u.Name(p['asset'])])
    assert u.EditorLoadingAndSavingUtils.save_map(world,NEW)
    world=u.EditorLoadingAndSavingUtils.load_map(NEW);items=eas.get_all_level_actors()
    lbl={a.get_actor_label() for a in items}
    checks={'terrain_parts':all(p in lbl for p in pal['parts']),'plates_removed':not any(p in lbl for p in PLATES),
            'vegetation':len([a for a in items if a.actor_has_tag('LY10Vegetation')])==len(sc),'wild08_sublevel_gone':not wild08_levels(world),
            'quest_herbs':len([a for a in items if a.actor_has_tag('QuestHerb')])==3,'quest_board':len([a for a in items if a.actor_has_tag('QuestBoard')])==1,
            'actor_count':len(items)==base_count-wild08+len(pal['parts'])-len(PLATES)+len(sc),'base09_unchanged':hashlib.sha256(base.read_bytes()).hexdigest()==report['base09_sha256']}
    report.update(checks=checks,removed_plates=removed,lowered_cm=DROP_CM,lowered_actors=lowered,vegetation=len(sc),actor_count=len(items))
    assert all(checks.values()),checks
    report.update(status='saved_reloaded_pending_pie_and_visual',map_sha256=hashlib.sha256((root/'XiuXianTown/Content/Maps/TownLayout_10.umap').read_bytes()).hexdigest());write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
