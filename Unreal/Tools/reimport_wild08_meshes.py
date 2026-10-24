"""Full editor: reimport the five WildVegetation08 meshes in place (same FBX, same options as build_wild08_sublevel),
so collision data is built by the editor as for the Expansion06 meshes. The commandlet import left the pine and
boulder with no collision once loaded from disk. Existing references (sublevel, TownLayout_08) are kept.
UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,re,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent;repo=root.parent
MESH_DIR='/Game/Art/WildVegetation08/Meshes';MAT_DIR='/Game/Art/WildVegetation08/Materials'
report={'status':'starting','meshes':{}}
def write():(root/'wild08_reimport.json').write_text(json.dumps(report,indent=2))
def clean(s):return re.sub(r'[^A-Za-z0-9_]','_',str(s))
try:
    palette=json.loads((root/'wild08_palette.json').read_text());tools=u.AssetToolsHelpers.get_asset_tools()
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    for aid,src in palette['sources'].items():
        fbx=repo/'Models'/aid/'v001'/f'{aid}_v001.fbx';assert hashlib.sha256(fbx.read_bytes()).hexdigest()==src['fbx_sha256'],aid
        task=u.AssetImportTask()
        for k,v in [('filename',str(fbx)),('destination_path',MESH_DIR),('destination_name',aid),('automated',True),('save',True),('replace_existing',True)]:task.set_editor_property(k,v)
        opt=u.FbxImportUI()
        for k,v in [('import_mesh',True),('import_as_skeletal',False),('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH),('automated_import_should_detect_type',False),('import_materials',False),('import_textures',False)]:opt.set_editor_property(k,v)
        data=opt.get_editor_property('static_mesh_import_data')
        for k,v in [('combine_meshes',True),('auto_generate_collision',False),('transform_vertex_to_absolute',True),('convert_scene',True),('convert_scene_unit',True),('generate_lightmap_u_vs',False),('build_nanite',False)]:data.set_editor_property(k,v)
        task.set_editor_property('options',opt);task.set_editor_property('factory',u.FbxFactory());tools.import_asset_tasks([task])
        mesh=u.load_asset(MESH_DIR+'/'+aid);assert isinstance(mesh,u.StaticMesh),aid
        for i,slot in enumerate(mesh.get_editor_property('static_materials')):
            key=clean(slot.get_editor_property('imported_material_slot_name'))
            mat=u.load_asset(MAT_DIR+'/M_'+key);assert mat,(aid,key);mesh.set_material(i,mat)
        bs=mesh.get_editor_property('body_setup');bs.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);bs.set_editor_property('double_sided_geometry',True)
        u.EditorAssetLibrary.save_loaded_asset(mesh)
        report['meshes'][aid]={'sections':mesh.get_num_sections(0),'triangles':mesh.get_num_triangles(0),'materials':[str(s.get_editor_property('material_interface').get_name()) for s in mesh.get_editor_property('static_materials')]}
        write()
    report['status']='reimported';write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
