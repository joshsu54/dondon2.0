"""Create TownPrototype_02 with per-actor material overrides; preserve _01 and source meshes."""
import unreal as u
import json,re
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
u.EditorPythonScripting.set_keep_python_script_alive(True)
assert not u.EditorAssetLibrary.does_asset_exist('/Game/Maps/TownPrototype_02'), 'Version 02 already exists; use a new version instead'
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='TownPrototype_01'
palette=json.loads((root/'blender_palette.json').read_text())
def clean(s):return re.sub(r'[^A-Za-z0-9_-]','_',s)
objects={clean(k):v for k,v in palette['objects'].items()}
tools=u.AssetToolsHelpers.get_asset_tools()
mats={}
report={'source_map':'/Game/Maps/TownPrototype_01','map':'/Game/Maps/TownPrototype_02','assigned_mesh_actors':0,'unmatched':[],'material_method':'Blender procedural color-ramp mean; no texture baking','materials':[]}
def material(name,color,rough,metal=0):
    asset_name='M_'+clean(name)
    path='/Game/Art/Materials/SectPalette01/'+asset_name
    m=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else None
    if not m:
        m=tools.create_asset(asset_name,'/Game/Art/Materials/SectPalette01',u.Material,u.MaterialFactoryNew())
        base=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector,-300,0)
        base.set_editor_property('constant',u.LinearColor(*color[:3],1))
        assert u.MaterialEditingLibrary.connect_material_property(base,'',u.MaterialProperty.MP_BASE_COLOR)
        for offset,value,prop in [(150,rough,u.MaterialProperty.MP_ROUGHNESS),(300,metal,u.MaterialProperty.MP_METALLIC)]:
            expr=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant,-300,offset)
            expr.set_editor_property('r',value)
            assert u.MaterialEditingLibrary.connect_material_property(expr,'',prop)
        u.MaterialEditingLibrary.recompile_material(m)
        u.EditorAssetLibrary.save_loaded_asset(m)
    return m
for name,data in palette['materials'].items():
    mats[name]=material(name,data['base_color_linear'],data['roughness'],data['metallic'])
    report['materials'].append(mats[name].get_path_name())
ground=material('PrototypeGround',[.19,.235,.205],.95)
cube=material('CalibrationJade',[.22,.48,.40],.7)
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
for a in actors:
    if isinstance(a,u.StaticMeshActor):
        comp=a.static_mesh_component; mesh=comp.static_mesh;name=mesh.get_name()
        if a.get_actor_label()=='PrototypeGround':comp.set_material(0,ground)
        elif name=='UnitCube_1m':comp.set_material(0,cube)
        elif name in objects:
            slots=objects[name]
            assert len(slots)==comp.get_num_materials(),(name,len(slots),comp.get_num_materials())
            for i,n in enumerate(slots):
                assert n in mats,(name,n)
                comp.set_material(i,mats[n])
            report['assigned_mesh_actors']+=1
        else:report['unmatched'].append(name)
    elif isinstance(a,u.DirectionalLight):
        a.set_actor_rotation(u.Rotator(pitch=-40,yaw=-125,roll=0),False)
        a.light_component.set_mobility(u.ComponentMobility.MOVABLE)
        a.light_component.set_editor_property('intensity',3.0)
    elif isinstance(a,u.SkyLight):
        a.light_component.set_mobility(u.ComponentMobility.MOVABLE)
        a.light_component.set_editor_property('real_time_capture',True)
        a.light_component.set_editor_property('intensity',1.2)
    elif isinstance(a,u.PlayerStart):
        a.set_actor_location(u.Vector(700,1700,110),False,True)
        a.set_actor_rotation(u.Rotator(pitch=0,yaw=-90,roll=0),False)
assert report['assigned_mesh_actors']==483 and not report['unmatched'],report
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
loc=u.Vector(2100,2400,1200)
ed.set_level_viewport_camera_info(loc,u.MathLibrary.find_look_at_rotation(loc,u.Vector(1000,900,250)))
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Maps/TownPrototype_02')
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownPrototype_02')
assert world and world.get_name()=='TownPrototype_02'
report['status']='saved_pending_visual_runtime_review'
(root/'material_repair_validation.json').write_text(json.dumps(report,indent=2))
exec(compile((root/'Tools/playtest_prototype.py').read_text(),str(root/'Tools/playtest_prototype.py'),'exec'))
