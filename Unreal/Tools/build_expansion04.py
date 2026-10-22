"""Extend saved TownLayout_03 using existing immutable FBX sources and runtime quest module."""
import unreal as u
import json,re,hashlib,traceback,time
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent; repo=root.parent
out=root/'expansion04_build.json'; report={'status':'starting','map':'/Game/Maps/TownLayout_04','sources':{},'added_actors':[]}
def write(status,**kw):report.update(status=status,**kw);out.write_text(json.dumps(report,indent=2,ensure_ascii=False))
def clean(s):return re.sub(r'[^A-Za-z0-9_]','_',str(s))
def run():
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 ed=u.get_editor_subsystem(u.UnrealEditorSubsystem); actors=u.get_editor_subsystem(u.EditorActorSubsystem)
 assert not ed.get_game_world() and not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
 assert not u.EditorAssetLibrary.does_asset_exist(report['map']), 'Preserve existing 04'
 cls=u.load_class(None,'/Script/XiuXianTown.SectQuestDirector');assert cls,'Runtime module required'
 world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_03')
 palette=json.loads((root/'expansion04_palette.json').read_text())
 tools=u.AssetToolsHelpers.get_asset_tools();mats={};md='/Game/Art/Expansion04/Materials'
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
 sources['SolidClouds']=repo/'Models/MountainSanctuary/v004/SolidClouds_v004.fbx'
 meshes={};u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
 for name,p in sources.items():
  write('importing',current=name)
  path='/Game/Art/Expansion04/Meshes/'+name;mesh=u.load_asset(path)
  if not mesh:
   task=u.AssetImportTask()
   for k,v in [('filename',str(p)),('destination_path','/Game/Art/Expansion04/Meshes'),('destination_name',name),('automated',True),('save',True)]:task.set_editor_property(k,v)
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
  a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos));a.set_actor_label(label);a.set_folder_path('Expansion04');a.static_mesh_component.set_static_mesh(mesh)
  if movable:a.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
  a.set_actor_scale3d(u.Vector(*scale));a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False);a.set_actor_enable_collision(collision);a.set_editor_property('tags',[u.Name(t) for t in tags]);report['added_actors'].append(label);return a
 # Use reusable primitive terrain/supports, not new standalone model deliverables.
 cube=u.load_asset('/Engine/BasicShapes/Cube');green=next(m for n,m in mats.items() if 'Moss' in n or 'Grass' in n)
 stone=next(m for n,m in mats.items() if 'Stone' in n);wood=next(m for n,m in mats.items() if 'Wood' in n or 'Timber' in n)
 def block(label,pos,scale,mat):
  a=place(cube,label,pos,scale);a.static_mesh_component.set_material(0,mat);return a
 block('ValleyGround',(0,-1000,-65),(450,450,1),green)
 block('NorthTrailBase',(0,-4230,46),(7,13.8,1.32),green)
 for i,(y,z) in enumerate([(-3900,112),(-4500,112),(-5580,352),(-6660,592)]):place(meshes['MountainStonePath'],'SectRoad_%02d'%i,(0,y,z))
 for i,(y,z) in enumerate([(-5040,132),(-6120,372)]):place(meshes['MountainStoneStairs'],'SectStairs_%02d'%i,(0,y,z))
 block('MiddleTrailRock',(0,-5580,176),(7,6,3.52),stone)
 block('UpperTrailRock',(0,-6660,296),(7,6,5.92),stone)
 block('SectGateTerrace',(0,-7200,296),(15,10.8,5.92),stone)
 block('SectGateTerraceTop',(0,-7200,602),(15,10.8,.2),stone)
 place(meshes['SectGate'],'SectGate04',(0,-7240,612))
 for i,(x,y,z,s,yaw) in enumerate([(-6500,-7600,0,1.4,20),(7200,-8100,0,1.5,-30),(-8000,1000,-100,1.1,50),(9000,1500,-100,1.2,-50)]):
  place(meshes['MountainRidge'],'ValleyRidge_%02d'%i,(x,y,z),(s,s,s),yaw,False)
 for i,(x,y,s) in enumerate([(-4000,-10800,1.35),(4000,-13000,1.5),(0,-16000,1.6)]):place(meshes['CloudpiercerPeak'],'DistantPeak_%02d'%i,(x,y,-120),(s,s,s),i*43,False)
 cloud=meshes['SolidClouds'];b=cloud.get_bounding_box();center=(b.min+b.max)*.5
 for i,(x,y,z,s) in enumerate([(-6500,-7200,1800,.65),(6400,-9000,2300,.6),(0,-13500,3200,.8)]):
  place(cloud,'DriftingClouds_%02d'%i,(x-center.x*s,y-center.y*s,z-center.z*s),(s,s,s),0,False,True,['DriftCloud'])
 fog=actors.spawn_actor_from_class(u.ExponentialHeightFog,u.Vector(0,0,0));fog.set_actor_label('ValleyMist04');fog.set_folder_path('Expansion04');fog.component.set_editor_property('fog_density',.008);fog.component.set_editor_property('fog_height_falloff',.13)
 board=block('SectQuestBoard',(260,-3450,230),(1.6,.22,1.7),wood);board.set_editor_property('tags',[u.Name('QuestBoard')])
 for x in [205,315]:block('QuestBoardPost_'+str(x),(x,-3450,190),(.12,.12,1.5),wood)
 for i,(y,z) in enumerate([(-4450,132),(-5580,372),(-6750,612)]):place(meshes['SpiritHerbMature'],'QuestSpiritHerb_%d'%i,(110,y,z),(2.5,2.5,2.5),0,False,False,['QuestHerb'])
 director=actors.spawn_actor_from_class(cls,u.Vector(0,0,0));director.set_actor_label('SectQuestDirector04');director.set_folder_path('Expansion04')
 assert u.EditorLoadingAndSavingUtils.save_map(world,report['map'])
 world=u.EditorLoadingAndSavingUtils.load_map(report['map']);assert world.get_name()=='TownLayout_04'
 all_actors=actors.get_all_level_actors();assert len([a for a in all_actors if a.actor_has_tag('QuestHerb')])==3
 loc=u.Vector(13500,7000,10000);ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(0,-4800,1200)))
 write('saved_reloaded_pending_runtime_visual',actor_count=len(all_actors),limits=['Existing FBX assets reused; no new Blender geometry','No quest persistence across sessions yet','Scenic distant meshes have no collision; trail uses complex static collision'])
try:run()
except Exception:write('error',error=traceback.format_exc());raise
