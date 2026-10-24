"""TownLayout_13 = TownLayout_12 + the QCharacters17 v006 player characters (male default pawn, female ready to swap).
Imports the QCharacters17 batch's Models/QPlayerMale|QPlayerFemale/v006/*.fbx as skeletal meshes with their Idle/Walk loops, copies the template
character and game mode (originals untouched), and sets the game mode only on the new map.
Run in the GUI editor:  UnrealEditor.exe XiuXianTown.uproject -ExecutePythonScript=build_qplayer13.py -unattended
"""
import unreal as u,json,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;repo=root.parent;out=root/'qplayer13_build.json'
BASE,NEW='/Game/Maps/TownLayout_12','/Game/Maps/TownLayout_13';ART='/Game/Art/QCharacters17'
RIG='v006'   # v005 FBX left a x100 scale on the Armature node; Unreal dropped it and the skeleton came in 100x too small
BATCH=repo/'ArtLibrary/ExpansionBatches/QCharacters17'
TP_CHAR,TP_MODE='/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter','/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode'
HALF,RADIUS=73.,32.          # capsule for a 1.45 m character (template: 96 / 42)
WALK_SPEED=204.              # = WalkCycleSpeed 60 x MaxWalkPlayRate 3.4: the steps keep pace, no foot sliding
report={'status':'running','map':NEW,'base':BASE};sub=u.get_engine_subsystem(u.SubobjectDataSubsystem);BL=u.SubobjectDataBlueprintFunctionLibrary
def write():out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def import_character(aid):
    fbx=BATCH/'Models'/aid/RIG/f'{aid}_{RIG}.fbx';dest=f'{ART}/{aid}'
    t=u.AssetImportTask()
    for k,v in (('filename',str(fbx)),('destination_path',dest),('destination_name','SK_'+aid),('automated',True),('save',True)):t.set_editor_property(k,v)
    o=u.FbxImportUI()
    for k,v in (('import_mesh',True),('import_as_skeletal',True),('mesh_type_to_import',u.FBXImportType.FBXIT_SKELETAL_MESH),('automated_import_should_detect_type',False),
                ('import_materials',True),('import_textures',False),('import_animations',True),('create_physics_asset',True)):o.set_editor_property(k,v)
    o.skeletal_mesh_import_data.set_editor_property('import_meshes_in_bone_hierarchy',True)
    o.anim_sequence_import_data.set_editor_property('animation_length',u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    t.set_editor_property('options',o);t.set_editor_property('factory',u.FbxFactory());u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    sk=u.load_asset(f'{dest}/SK_{aid}');assert isinstance(sk,u.SkeletalMesh),(aid,'skeletal mesh')
    anims={}
    for p in u.EditorAssetLibrary.list_assets(dest,recursive=False):
        a=u.load_asset(p)
        if isinstance(a,u.AnimSequence):anims['Walk' if 'Walk' in a.get_name() else 'Idle' if 'Idle' in a.get_name() else a.get_name()]=a
    assert {'Idle','Walk'}<=set(anims),(aid,list(anims))
    for a in anims.values():a.set_editor_property('enable_root_motion',False);u.EditorAssetLibrary.save_loaded_asset(a)
    b=sk.get_bounds();report.setdefault('imports',{})[aid]={'fbx':str(fbx.relative_to(repo)),'rig_version':RIG,'fbx_sha256':sha(fbx),'skeletal_mesh':sk.get_path_name(),
        'skeleton':sk.get_editor_property('skeleton').get_path_name(),
        'bounds_extent_cm':[b.box_extent.x,b.box_extent.y,b.box_extent.z],'materials':len(sk.materials),
        'anims':{k:{'asset':v.get_path_name(),'length_s':v.get_play_length()} for k,v in anims.items()}};write()
    return sk,anims

def handles(bp):
    r={}
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d=sub.k2_find_subobject_data_from_handle(h);r[str(BL.get_variable_name(d))]=(h,BL.get_object(d))
    return r

def make_character(aid,sk,anims):
    path=f'{ART}/Blueprints/BP_{aid}';bp=u.EditorAssetLibrary.duplicate_asset(TP_CHAR,path);assert bp,path
    H=handles(bp);report.setdefault('template_components',sorted(H))
    mesh=next(o for _,o in H.values() if isinstance(o,u.SkeletalMeshComponent))
    mesh.set_editor_property('skeletal_mesh_asset',sk);mesh.set_editor_property('anim_class',None)
    mesh.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)   # template: pose ticks but bones stay put when not rendered
    mesh.set_editor_property('animation_mode',u.AnimationMode.ANIMATION_SINGLE_NODE)
    play=mesh.get_editor_property('animation_data');play.set_editor_property('anim_to_play',anims['Idle']);play.set_editor_property('saved_looping',True)
    mesh.set_editor_property('animation_data',play)
    mesh.set_editor_property('relative_location',u.Vector(0,0,-HALF));mesh.set_editor_property('relative_rotation',u.Rotator(roll=0,pitch=0,yaw=-90))   # asset faces +Y
    cap=next(o for _,o in H.values() if isinstance(o,u.CapsuleComponent));cap.set_editor_property('capsule_half_height',HALF);cap.set_editor_property('capsule_radius',RADIUS)
    mov=next(o for _,o in H.values() if isinstance(o,u.CharacterMovementComponent));mov.set_editor_property('max_walk_speed',WALK_SPEED)
    boom=next((o for _,o in H.values() if isinstance(o,u.SpringArmComponent)),None)
    if boom:boom.set_editor_property('target_arm_length',330.);boom.set_editor_property('relative_location',u.Vector(0,0,35))   # look at the big head, not the hips
    cls=u.load_class(None,'/Script/XiuXianTown.QCharacterAnimDriver');assert cls,'compile the module first'
    actor_handle=sub.k2_gather_subobject_data_for_blueprint(bp)[0]
    h,fail=sub.add_new_subobject(u.AddNewSubobjectParams(parent_handle=actor_handle,new_class=cls,blueprint_context=bp));assert not str(fail),fail
    sub.rename_subobject_member_variable(bp,h,'QAnimDriver')
    drv=BL.get_object(sub.k2_find_subobject_data_from_handle(h));drv.set_editor_property('idle_animation',anims['Idle']);drv.set_editor_property('walk_animation',anims['Walk'])
    u.BlueprintEditorLibrary.compile_blueprint(bp);assert u.EditorAssetLibrary.save_loaded_asset(bp)
    report.setdefault('characters',{})[aid]={'blueprint':path,'capsule':[RADIUS,HALF],'max_walk_speed':WALK_SPEED,'mesh_offset_z':-HALF,'mesh_yaw':-90,
        'camera_boom':bool(boom),'anim_driver':{'idle':anims['Idle'].get_path_name(),'walk':anims['Walk'].get_path_name(),'walk_cycle_speed':drv.get_editor_property('walk_cycle_speed'),
        'max_walk_play_rate':drv.get_editor_property('max_walk_play_rate')}};write()
    return u.BlueprintEditorLibrary.generated_class(bp)

try:
    assert not u.EditorAssetLibrary.does_asset_exist(NEW),'Preserve existing 13'
    assert not u.EditorAssetLibrary.does_directory_exist(ART) or not u.EditorAssetLibrary.list_assets(ART),'QCharacters17 assets already imported'
    src=root/'XiuXianTown/Content/Maps/TownLayout_12.umap';before=sha(src);tp=[sha(root/'XiuXianTown/Content/ThirdPerson/Blueprints'/n) for n in ('BP_ThirdPersonCharacter.uasset','BP_ThirdPersonGameMode.uasset')]
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    classes={aid:make_character(aid,*import_character(aid)) for aid in ('QPlayerMale','QPlayerFemale')}
    gm=u.EditorAssetLibrary.duplicate_asset(TP_MODE,f'{ART}/Blueprints/BP_QPlayerGameMode');gmc=u.BlueprintEditorLibrary.generated_class(gm)
    u.get_default_object(gmc).set_editor_property('default_pawn_class',classes['QPlayerMale']);u.BlueprintEditorLibrary.compile_blueprint(gm);assert u.EditorAssetLibrary.save_loaded_asset(gm)
    # the import task's save only writes the mesh and the anims: save skeleton, physics asset and materials too
    assert u.EditorAssetLibrary.save_directory(ART,only_if_is_dirty=False,recursive=True)
    report['saved_assets']=sorted(u.EditorAssetLibrary.list_assets(ART,recursive=True));write()
    assert any(x.endswith('_Skeleton') for x in report['saved_assets']) and any('PhysicsAsset' in x for x in report['saved_assets'])
    u.EditorLoadingAndSavingUtils.load_map(BASE);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings()
    report['base_game_mode_override']=str(ws.get_editor_property('default_game_mode'))
    ws.set_editor_property('default_game_mode',gmc);assert u.EditorLoadingAndSavingUtils.save_map(world,NEW)
    u.EditorLoadingAndSavingUtils.load_map(NEW)
    report.update(status='saved',game_mode=gm.get_path_name(),default_pawn='BP_QPlayerMale',base_12_unchanged=sha(src)==before,
        template_blueprints_unchanged=tp==[sha(root/'XiuXianTown/Content/ThirdPerson/Blueprints'/n) for n in ('BP_ThirdPersonCharacter.uasset','BP_ThirdPersonGameMode.uasset')],
        map_sha256=sha(root/'XiuXianTown/Content/Maps/TownLayout_13.umap'));write()
except Exception:report.update(status='error',error=traceback.format_exc());write()
finally:u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
