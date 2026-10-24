"""Full editor: retune the inn fill lights in TownLayout_09 after visual review (first pass blew out the interior
under the fixed EV100 0 / +1 exposure). Only the seven Expansion09 lights change; values are logged before/after.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
import os
PASS=int(os.environ.get('INN09_TUNE_PASS','1'))
# Pass 1: ~1/5 intensity, hall light lowered. Pass 2: corridor hotspot (light 77 cm under ceiling) and dark north end.
TUNE={'InnHallFill09':(70.,(-1390,-2220,380)),'InnCounterFill09':(35.,None),'InnStairFootFill09':(30.,None),
      'InnCorridorFill09':(45.,(-1320,-2220,700)),'InnRoomSouthFill09':(28.,None),'InnRoomMidFill09':(28.,None),'InnStairTopFill09':(30.,None)}
ADD={}
if PASS==2:
    TUNE={'InnCorridorFill09':(40.,(-1320,-2300,640))}
    ADD={'InnUpperNorthFill09':(30.,(-1320,-1780,650),420.)}
log=root/'expansion09_tune.json'
history=json.loads(log.read_text()) if log.exists() else {}
passes=history.get('passes',[history] if history.get('changes') else [])
report={'status':'starting','pass':PASS,'map':'/Game/Maps/TownLayout_09','changes':[],'added':[]}
def write():log.write_text(json.dumps({'passes':passes+[report]},indent=2))
try:
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=u.EditorLoadingAndSavingUtils.load_map(report['map'])
    items={a.get_actor_label():a for a in actors.get_all_level_actors()}
    for name,(cd,loc) in TUNE.items():
        a=items[name];c=a.get_component_by_class(u.PointLightComponent);l=a.get_actor_location()
        report['changes'].append({'light':name,'candela_before':c.intensity,'candela_after':cd,'location_before':[l.x,l.y,l.z],'location_after':list(loc) if loc else [l.x,l.y,l.z]})
        c.set_intensity(cd)
        if loc:a.set_actor_location(u.Vector(*loc),False,False)
    for name,(cd,loc,radius) in ADD.items():
        assert name not in items,name
        a=actors.spawn_actor_from_class(u.PointLight,u.Vector(*loc));a.set_actor_label(name);a.set_folder_path('Expansion09')
        c=a.get_component_by_class(u.PointLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.CANDELAS)
        c.set_intensity(cd);c.set_attenuation_radius(radius);c.set_light_color(u.LinearColor(1.,.86,.67,1.));c.set_editor_property('cast_shadows',True);c.set_editor_property('source_radius',8.)
        report['added'].append({'light':name,'candela':cd,'location':list(loc),'radius_cm':radius,'cast_shadows':True})
    assert u.EditorLoadingAndSavingUtils.save_map(world,report['map'])
    u.EditorLoadingAndSavingUtils.load_map(report['map'])
    items={a.get_actor_label():a for a in actors.get_all_level_actors()}
    report['checks']={n:abs(items[n].get_component_by_class(u.PointLightComponent).intensity-cd)<.01 for n,(cd,_) in TUNE.items()}
    report['checks'].update({n:n in items for n in ADD})
    assert all(report['checks'].values())
    report.update(status='retuned_saved_reloaded',map_sha256=hashlib.sha256((root/'XiuXianTown/Content/Maps/TownLayout_09.umap').read_bytes()).hexdigest());write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
