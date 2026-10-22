"""Extend saved TownLayout_05 using existing immutable FBX sources and runtime quest module."""
import unreal as u
import json,re,hashlib,traceback,time
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent; repo=root.parent
out=root/'expansion06_build.json'; report={'status':'starting','map':'/Game/Maps/TownLayout_06','sources':{},'added_actors':[]}
def write(status,**kw):report.update(status=status,**kw);out.write_text(json.dumps(report,indent=2,ensure_ascii=False))
def clean(s):return re.sub(r'[^A-Za-z0-9_]','_',str(s))
def run():
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 ed=u.get_editor_subsystem(u.UnrealEditorSubsystem); actors=u.get_editor_subsystem(u.EditorActorSubsystem)
 assert not ed.get_game_world() and not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
 assert not u.EditorAssetLibrary.does_asset_exist(report['map']), 'Preserve existing 06'
 cls=u.load_class(None,'/Script/XiuXianTown.SectQuestDirector');assert cls,'Runtime module required'
 world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_05')
 palette=json.loads((root/'expansion06_palette.json').read_text())
 tools=u.AssetToolsHelpers.get_asset_tools();mats={};md='/Game/Art/Expansion06/Materials'
 for name,d in palette['materials'].items():
  an='M_'+clean(name);mat=u.load_asset(md+'/'+an)
  if not mat:
   mat=tools.create_asset(an,md,u.Material,u.MaterialFactoryNew())
   expr=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-250,0);expr.set_editor_property('constant',u.LinearColor(*d['color'][:3],1));u.MaterialEditingLibrary.connect_material_property(expr,'',u.MaterialProperty.MP_BASE_COLOR)
   for y,value,prop in [(130,d['roughness'],u.MaterialProperty.MP_ROUGHNESS),(260,d['metallic'],u.MaterialProperty.MP_METALLIC)]:
    e=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant,-250,y);e.set_editor_property('r',value);u.MaterialEditingLibrary.connect_material_property(e,'',prop)
   u.MaterialEditingLibrary.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat)
  mats[clean(name)]=mat
 sources={n:(repo/d['blend']).with_suffix('.fbx') for n,d in palette['sources'].items() if n!='MountainSanctuary'}
 meshes={};u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 for name,p in sources.items():
  write('importing',current=name)
  path='/Game/Art/Expansion06/Meshes/'+name;mesh=u.load_asset(path)
  if not mesh:
   task=u.AssetImportTask()
   for k,v in [('filename',str(p)),('destination_path','/Game/Art/Expansion06/Meshes'),('destination_name',name),('automated',True),('save',True)]:task.set_editor_property(k,v)
   opt=u.FbxImportUI()
   for k,v in [('import_mesh',True),('import_as_skeletal',False),('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH),('automated_import_should_detect_type',False),('import_materials',False),('import_textures',False)]:opt.set_editor_property(k,v)
   data=opt.get_editor_property('static_mesh_import_data')
   for k,v in [('combine_meshes',True),('auto_generate_collision',False),('transform_vertex_to_absolute',True),('convert_scene',True),('convert_scene_unit',True),('generate_lightmap_u_vs',False),('build_nanite',False)]:data.set_editor_property(k,v)
   task.set_editor_property('options',opt);task.set_editor_property('factory',u.FbxFactory());tools.import_asset_tasks([task]);mesh=u.load_asset(path)
  assert isinstance(mesh,u.StaticMesh),name
  unmatched=[]
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):
   key=clean(slot.get_editor_property('imported_material_slot_name'))
   if key not in mats:key=clean(slot.get_editor_property('material_slot_name'))
   if key not in mats:unmatched.append(key)
   else:mesh.set_material(i,mats[key])
  assert not unmatched,(name,unmatched)
  mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  u.EditorAssetLibrary.save_loaded_asset(mesh);meshes[name]=mesh
  b=mesh.get_bounding_box();report['sources'][name]={'fbx':str(p.relative_to(repo)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'asset':path,'dimensions_cm':[getattr(b.max,a)-getattr(b.min,a) for a in ['x','y','z']]}
 def place(mesh,label,pos,scale=(1,1,1),yaw=0,collision=True,movable=False,tags=()):
  a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos));a.set_actor_label(label);a.set_folder_path('Expansion06');a.static_mesh_component.set_static_mesh(mesh)
  if movable:a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
  a.set_actor_scale3d(u.Vector(*scale));a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False);a.set_actor_enable_collision(collision);a.set_editor_property('tags',[u.Name(t) for t in tags]);report['added_actors'].append(label);return a
 # Preserve all original assets; only edit a newly saved map after imports succeed.
 cube=u.load_asset('/Engine/BasicShapes/Cube')
 stone=next(m for n,m in mats.items() if 'Stone' in n)
 def block(label,pos,scale,mat=stone):
  a=place(cube,label,pos,scale);a.static_mesh_component.set_material(0,mat);return a
 # Lower trail rest stop: terrace cap reaches the existing trail's 132 cm surface.
 block('RestStopFoundation06',(-1025,-4450,46),(17.5,10,1.32))
 block('RestStopPaving06',(-1025,-4450,122),(17.5,10,.20))
 place(meshes['MountainRestPavilion'],'RestPavilion06',(-1200,-4450,132),yaw=90)
 # Keep rails independent, with separated end posts and no rails across entrances.
 for i,(x,y,yaw) in enumerate([(-1200,-4920,0),(-1200,-3980,0),(-1770,-4450,90)]):
  place(meshes['TrailStoneRailing'],'RestRailing06_%02d'%i,(x,y,132),yaw=yaw)
 for i,(x,y,z) in enumerate([(-300,-4130,132),(-300,-4770,132),(-1380,-4810,132),(-1380,-4090,132),(-285,-5510,372),(-285,-6650,612),(-590,-7300,612),(590,-7300,612)]):
  place(meshes['StoneLantern'],'TrailLantern06_%02d'%i,(x,y,z),(.75,.75,.75))
 for i,(x,y) in enumerate([(-420,-4200),(290,-4700)]):
  place(meshes['TownWaymarker'],'TrailWaymarker06_%02d'%i,(x,y,132),yaw=90)
 # Trees remain away from the playable path and pavilion eaves; static FBX foliage.
 for i,(x,y,s,yaw) in enumerate([(-2350,-4500,.85,35),(-1500,-5500,.75,-35),(1450,-4200,.85,125),(1400,-6050,.75,50),(-1600,-7100,.8,20),(1750,-7800,.9,-20)]):
  place(meshes['WindPine'],'WaysidePine06_%02d'%i,(x,y,-5),(s,s,s),yaw,True)
 for i,(x,y) in enumerate([(-2250,-4100),(-2200,-4780),(-1700,-5300),(-1300,-5750),(1220,-4040),(1570,-4480),(1280,-5700),(1540,-6350),(-1320,-6930),(-1740,-7450),(1450,-7720),(1950,-7940)]):
  place(meshes['WindGrass'],'WaysideGrass06_%02d'%i,(x,y,-15),(1.8,1.8,1.8),i*37,False)
 # Full source board grounded on the platform; interaction radius includes approach.
 for a in list(actors.get_all_level_actors()):
  if a.get_actor_label()=='SectQuestBoard' or a.get_actor_label().startswith('QuestBoardPost_'):
   actors.destroy_actor(a)
 board=place(meshes['NoticeBoard'],'SectQuestBoard06',(260,-3450,132),yaw=90,tags=['QuestBoard'])
 assert u.EditorLoadingAndSavingUtils.save_map(world,report['map'])
 world=u.EditorLoadingAndSavingUtils.load_map(report['map']);assert world.get_name()=='TownLayout_06'
 all_actors=actors.get_all_level_actors()
 assert len([a for a in all_actors if a.actor_has_tag('QuestHerb')])==3
 assert len([a for a in all_actors if a.actor_has_tag('QuestBoard')])==1
 loc=u.Vector(-2500,-2800,1600);ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(-1000,-4450,400)))
 write('saved_reloaded_pending_runtime_visual',actor_count=len(all_actors),limits=['Existing source models and ten-view images reused unchanged','Foliage FBX is static; wind shader not ported','Complex static collision prototype; no LOD or packaged performance acceptance'])
try:run()
except Exception:write('error',error=traceback.format_exc());raise
