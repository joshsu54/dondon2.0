"""Create a new management map from 09; never overwrites an existing map or source mesh.
Run in full UnrealEditor using -ExecutePythonScript. UE primitives are blockout dressing,
not new standalone Blender deliverables. Uses only already imported assets.
"""
import unreal as u
import json, hashlib, traceback
from pathlib import Path

root = Path(u.Paths.project_dir()).resolve().parent
NEW = '/Game/Maps/TownLayout_10'
report = {'status': 'building', 'map': NEW, 'base': '/Game/Maps/TownLayout_09',
          'scope': 'Walkable sect management blockout using existing assets and engine primitives', 'interactions': []}

def write():
    (root / 'management10_build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

try:
    cls = u.load_class(None, '/Script/XiuXianTown.SectAdventureDirector')
    assert cls, 'Compile the runtime module before saving any map'
    assert not u.EditorAssetLibrary.does_asset_exist(NEW), 'Refusing to overwrite TownLayout_10'
    base = root / 'XiuXianTown/Content/Maps/TownLayout_09.umap'
    digest = hashlib.sha256(base.read_bytes()).hexdigest()
    world = u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_09')
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    old = [a for a in actors.get_all_level_actors() if isinstance(a, u.SectQuestDirector)]
    assert len(old) == 1
    actors.destroy_actor(old[0])
    director = actors.spawn_actor_from_class(cls, u.Vector(0,0,0))
    director.set_actor_label('SectManagement10')
    director.set_folder_path('Management10')
    mats = {}
    for key, name in [('wood','M_Warm_Timber'),('stone','M_Weathered_Blue_Stone'),('leaf','M_Young_Leaf'),('jade','M_Jade')]:
        mat = u.load_asset('/Game/Art/Expansion04/Materials/'+name)
        if mat: mats[key] = mat
    assert 'wood' in mats and 'stone' in mats and 'leaf' in mats
    mats['jade'] = mats.get('jade', mats['leaf'])
    cube = u.load_asset('/Engine/BasicShapes/Cube')
    sphere = u.load_asset('/Engine/BasicShapes/Sphere')
    cylinder = u.load_asset('/Engine/BasicShapes/Cylinder')
    count = [0]
    def mesh(asset, label, xyz, scale=(1,1,1), mat=None, tags=(), collision=False, yaw=0):
        if isinstance(asset,str): asset=u.load_asset(asset)
        assert asset, label
        a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*xyz))
        a.set_actor_label(label);a.set_folder_path('Management10')
        a.static_mesh_component.set_static_mesh(asset)
        if mat: a.static_mesh_component.set_material(0,mat)
        a.set_actor_scale3d(u.Vector(*scale));a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False)
        a.set_actor_enable_collision(collision)
        a.set_editor_property('tags',[u.Name(t) for t in tags])
        count[0]+=1
        return a
    def block(label,xyz,scale,mat='stone',tags=(),collision=False):
        return mesh(cube,label,xyz,scale,mats[mat],tags,collision)
    def text(label,xyz):
        a=actors.spawn_actor_from_class(u.TextRenderActor,u.Vector(*xyz),u.Rotator(pitch=0,yaw=90,roll=0))
        a.set_actor_label('Sign_'+label);a.set_folder_path('Management10')
        a.text_render.set_text(label);a.text_render.set_world_size(32)
        a.text_render.set_text_render_color(u.Color(212,240,210,255))
    def interact(tag,xyz,label):
        # Invisible anchor at hand height keeps interaction and visibility checks away from the ground.
        a=actors.spawn_actor_from_class(u.Actor,u.Vector(*xyz))
        a.set_actor_label(tag);a.set_folder_path('Management10')
        a.set_editor_property('tags',[u.Name('SectInteract'),u.Name(tag)])
        # Generic Actor may not have a root; a scene component is not exposed in Python.
        # Instead use an invisible, collision-free cube with a reliable transform.
        actors.destroy_actor(a)
        a=block(tag,xyz,(.1,.1,.1),'jade',('SectInteract',tag))
        a.set_actor_hidden_in_game(True)
        mesh(cylinder,tag+'_Marker',(xyz[0],xyz[1],-6),(1.2,1.2,.12),mats['jade'])
        text(label,(xyz[0],xyz[1],220))
        report['interactions'].append({'tag':tag,'location_cm':list(xyz),'label':label})
        return a
    def npc(tag,x,y,label,robe):
        interact(tag,(x,y,90),label)
        mesh(cylinder,tag+'_Robe',(x,y,61),(.65,.65,1.25),mats[robe])
        mesh(sphere,tag+'_Head',(x,y,145),(.38,.38,.42),mats['wood'])
        block(tag+'_Belt',(x,y,70),(.68,.68,.07),'stone')
    # Flat stepping stones preserve the existing ground collision and a central 3.5 m corridor.
    for i,y in enumerate(range(1500,6100,200)):
        block('CampPath_%02d'%i,(0,y,-10),(3.5,1.7,.10))
    for x in range(-1400,1600,200):
        block('CampCrossPath_'+str(x),(x,4200,-10),(1.7,2,.10))
    text('LINGYUN  /  REBUILDING CAMP',(0,2100,280))
    npc('SectShiDi',350,2500,'SHI DI','wood')
    npc('SectApplicantLin',-500,2800,'LIN XI','leaf')
    npc('SectApplicantYue',750,2900,'YUE QING','stone')
    npc('SectMaster',0,6000,'YUN BU HE','jade')
    interact('SectGarden',(950,4050,90),'HERB GARDEN')
    interact('SectDorm',(-1000,3600,90),'DISCIPLE HOUSE')
    interact('SectHall',(900,5200,90),'CULTIVATION')
    interact('SectWood',(-1500,3500,90),'BAMBOO / WOOD')
    interact('SectStone',(1650,4750,90),'QUARRY / STONE')
    interact('SectFood',(1250,3400,90),'WILD FRUIT / FOOD')
    # Resource scenery is reusable content. No source material/mesh is modified.
    mesh('/Game/Art/WildVegetation08/Meshes/BambooClump','CampBamboo',(-1660,3500,-15),(.8,.8,.8))
    mesh('/Game/Art/WildVegetation08/Meshes/MossBoulderSet','CampQuarry',(1810,4750,-15),(.8,.8,.8))
    mesh('/Game/Art/WildVegetation08/Meshes/WildShrub','CampBerries',(1400,3400,-15),(1,1,1))
    # Garden: boundary remains visible; planted beds appear when built.
    for x in (700,1250):
        block('GardenSide_'+str(x),(x,4550,0),(.14,6,.3),'wood')
    for y in (4250,4850):
        block('GardenEnd_'+str(y),(975,y,0),(5.6,.14,.3),'wood')
    for row in range(3):
        for col in range(4):
            mesh('/Game/Art/Expansion04/Meshes/SpiritHerbMature','GardenHerb_%d_%d'%(row,col),
                 (790+col*120,4340+row*190,-8),(1.6,1.6,1.6),tags=('SectGardenBuilt',))
    # Dormitory open-front blockout: two paired beds, timber columns and a jade roof.
    dorm=('SectDormBuilt',)
    block('DormBase',(-1000,4030,-5),(7,7,.2),'stone',dorm)
    for x in (-1320,-680):
        for y in (3740,4320): block('DormColumn_%d_%d'%(x,y),(x,y,155),(.18,.18,3.4),'wood',dorm)
    block('DormBack',(-1000,4340,100),(6.6,.16,2.2),'wood',dorm)
    block('DormRoof',(-1000,4030,340),(7.7,7.7,.3),'jade',dorm)
    for x in (-1180,-820):
        for y in (3880,4180):
            block('Bed_%d_%d'%(x,y),(x,y,22),(1.35,2.1,.55),'wood',dorm)
            block('Bedroll_%d_%d'%(x,y),(x,y,53),(1.2,1.9,.08),'leaf',dorm)
    # Meditation pavilion uses the existing production art at reduced size.
    mesh('/Game/Art/Expansion06/Meshes/MountainRestPavilion','SectMeditationPavilion',(900,5690,-15),
         (.75,.75,.75),tags=('SectHallBuilt',))
    for x,y in [(-1450,4200),(1450,4200),(0,2000),(0,5800)]:
        block('Waypost_%d_%d'%(x,y),(x,y,50),(.18,.18,1.3),'wood')
        mesh(sphere,'JadeLamp_%d_%d'%(x,y),(x,y,130),(.35,.35,.35),mats['jade'])
    assert u.EditorLoadingAndSavingUtils.save_map(world,NEW)
    world=u.EditorLoadingAndSavingUtils.load_map(NEW)
    all_actors=actors.get_all_level_actors()
    checks={'one_management_director':len([a for a in all_actors if isinstance(a,u.SectAdventureDirector)])==1,
            'three_quest_herbs':len([a for a in all_actors if a.actor_has_tag('QuestHerb')])==3,
            'ten_interactions':len([a for a in all_actors if a.actor_has_tag('SectInteract')])==10,
            'base_09_unchanged':hashlib.sha256(base.read_bytes()).hexdigest()==digest}
    assert all(checks.values()),checks
    report.update(status='saved_reloaded',checks=checks,added_meshes=count[0],base_sha256=digest,
                  limitations=['Blockout NPCs and dormitory; no character animation or pathfinding',
                               'Buildings are visual dressing; management interactions are at marked entrances'])
    write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write()
    raise
finally:
    u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
