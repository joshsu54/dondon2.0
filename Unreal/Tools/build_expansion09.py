"""Create a separate 09 revision from 08: warm fill lights inside the inn (ground and upper floor).
Same light style as 07 (warm candela point lights, folder per revision); unlike 07's outdoor fills these cast
shadows so light does not pass through the inn floor and walls. Never overwrites 09 and never saves 08.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended   (module must be compiled)
"""
import unreal as u
import json,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
report={'status':'starting','map':'/Game/Maps/TownLayout_09','base':'/Game/Maps/TownLayout_08','scope':'UE lighting only; Blender/FBX, 08 and the vegetation sublevel unchanged'}
def write():(root/'expansion09_revision.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
WARM=(1.,.86,.67)
# Inn interior x -1949..-1069, y -2810..-1630; ground floor 161..470, upper floor 507..777 (cm).
LIGHTS=[('InnHallFill09',(-1390,-2220,420),360.,720.),('InnCounterFill09',(-1640,-2650,400),180.,460.),('InnStairFootFill09',(-1700,-1830,420),160.,420.),
        ('InnCorridorFill09',(-1320,-2220,730),220.,620.),('InnRoomSouthFill09',(-1770,-2560,730),140.,360.),('InnRoomMidFill09',(-1770,-2240,730),140.,360.),
        ('InnStairTopFill09',(-1760,-1820,740),140.,380.)]
try:
    ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    assert u.load_class(None,'/Script/XiuXianTown.SectQuestDirector'),'Quest module must be loaded'
    assert not u.EditorAssetLibrary.does_asset_exist(report['map']),'Never overwrite an existing 09'
    source=root/'XiuXianTown/Content/Maps/TownLayout_08.umap';report['source08_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    world=u.EditorLoadingAndSavingUtils.load_map(report['base'])
    base_count=len(actors.get_all_level_actors());report['base_actor_count']=base_count
    for name,pos,intensity,radius in LIGHTS:
        assert -1949<pos[0]<-1069 and -2810<pos[1]<-1630,(name,'outside inn')
        a=actors.spawn_actor_from_class(u.PointLight,u.Vector(*pos));a.set_actor_label(name);a.set_folder_path('Expansion09')
        c=a.get_component_by_class(u.PointLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity_units',u.LightUnits.CANDELAS)
        c.set_intensity(intensity);c.set_attenuation_radius(radius);c.set_light_color(u.LinearColor(*WARM,1.))
        c.set_editor_property('cast_shadows',True);c.set_editor_property('source_radius',8.)
    assert u.EditorLoadingAndSavingUtils.save_map(world,report['map'])
    world=u.EditorLoadingAndSavingUtils.load_map(report['map'])
    items={a.get_actor_label():a for a in actors.get_all_level_actors()}
    checks={'actor_count':len(items)==base_count+len(LIGHTS),'wild_actors':len([a for a in items.values() if a.actor_has_tag('WildVegetation08')])==24,
            'quest_herbs':len([a for a in items.values() if a.actor_has_tag('QuestHerb')])==3,'quest_board':len([a for a in items.values() if a.actor_has_tag('QuestBoard')])==1,
            'source08_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==report['source08_sha256']}
    for name,pos,intensity,radius in LIGHTS:
        a=items.get(name);c=a.get_component_by_class(u.PointLightComponent) if a else None
        checks[name+'_saved']=bool(c) and (a.get_actor_location()-u.Vector(*pos)).length()<.1 and abs(c.intensity-intensity)<.01 and c.cast_shadows
    report['checks']=checks;report['lights']=[{'name':n,'location_cm':p,'candela':i,'radius_cm':r,'color':WARM,'cast_shadows':True} for n,p,i,r in LIGHTS]
    assert all(checks.values()),checks
    report.update(status='saved_reloaded_pending_visual',map_sha256=hashlib.sha256((root/'XiuXianTown/Content/Maps/TownLayout_09.umap').read_bytes()).hexdigest());write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
