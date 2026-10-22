"""One-metre calibration cube, exported identically to the current source assets."""
import bpy
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ArtLibrary/Calibration'; OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.data.scenes.new('Unit_Calibration'); bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.5))
cube=bpy.context.object; cube.name='UnitCube_1m'
cube['expected_unreal_dimensions_cm']='100, 100, 100'
bpy.ops.export_scene.fbx(filepath=str(OUT/'UnitCube_1m.fbx'),use_selection=True,object_types={'MESH'},
                        apply_unit_scale=True,bake_anim=False,axis_forward='-Z',axis_up='Y',mesh_smooth_type='FACE')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'UnitCube_1m.blend'))
(OUT/'dimensions.json').write_text(json.dumps({'blender_dimensions_m':[1,1,1],
    'expected_unreal_dimensions_cm':[100,100,100],'unreal_import_verified':False},indent=2),encoding='utf-8')
print('CALIBRATION_COMPLETE',flush=True)
