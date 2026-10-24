"""Read-only: export the TownLayout_09 settlement (buildings, roads, steps, gate, expansions) as layout context for
the LingyunValley15 Blender terrain. Each unique StaticMesh goes to Context/Meshes/<name>.fbx; every actor's
transform (location, forward/right/up axes, scale) and material slot names go to settlement09_context.json, with
material base colours. Level "export selected" wrote no file in commandlet mode, hence per-mesh export.
Excluded: ValleyGround, distant ridges/peaks/clouds, lights/fog and the WildVegetation08 sublevel. Never saves a map.
UnrealEditor-Cmd <uproject> -run=pythonscript -script=<this>
"""
import unreal as u
import json,os,re,traceback
from pathlib import Path
REPO=Path(os.environ.get('LY15_REPO',r'D:\dondon2.0-main\dondon2.0-main'))
OUT=REPO/'ArtLibrary/ExpansionBatches/LingyunValley15/Context';(OUT/'Meshes').mkdir(parents=True,exist_ok=True)
SKIP=('ValleyGround','ValleyRidge_','DistantPeak_','DriftingClouds_')
report={'status':'starting','map':'/Game/Maps/TownLayout_09','units':'UE cm, left-handed; Blender = (x, -y, z)/100',
        'axes_note':'Blender rotation columns = (M*forward, -M*right, M*up) with M = diag(1,-1,1)'}
def vec(v):return [v.x,v.y,v.z]
def colour(mat):
    m=mat
    while isinstance(m,u.MaterialInstance):
        for name in ('BaseColor','Base Color','Color','Colour','Tint'):
            try:
                v=u.MaterialEditingLibrary.get_material_instance_vector_parameter_value(m,name)
                if v.r+v.g+v.b>0:return [v.r,v.g,v.b]
            except Exception:pass
        m=m.get_editor_property('parent')
    if isinstance(m,u.Material):
        node=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
        if node and isinstance(node,u.MaterialExpressionConstant3Vector):c=node.get_editor_property('constant');return [c.r,c.g,c.b]
    return None
try:
    u.EditorLoadingAndSavingUtils.load_map(report['map'])
    eas=u.get_editor_subsystem(u.EditorActorSubsystem)
    actors=[];meshes={};mats={}
    for a in eas.get_all_level_actors():
        if not isinstance(a,u.StaticMeshActor) or a.actor_has_tag('WildVegetation08') or a.get_actor_label().startswith(SKIP):continue
        c=a.static_mesh_component;sm=c.static_mesh
        if not sm:continue
        key=re.sub(r'[^A-Za-z0-9_]','_',sm.get_path_name().split('.')[0].replace('/Game/',''))
        meshes[key]=sm;slots=[]
        for i in range(c.get_num_materials()):
            mt=c.get_material(i);slots.append(mt.get_name() if mt else None)
            if mt and mt.get_name() not in mats:mats[mt.get_name()]=colour(mt)
        actors.append({'label':a.get_actor_label(),'folder':str(a.get_folder_path()),'mesh':key,'location':vec(a.get_actor_location()),
                       'forward':vec(a.get_actor_forward_vector()),'right':vec(a.get_actor_right_vector()),'up':vec(a.get_actor_up_vector()),
                       'scale':vec(a.get_actor_scale3d()),'materials':slots,'collision':a.get_actor_enable_collision()})
    failed=[]
    for key,sm in meshes.items():
        f=OUT/'Meshes'/(key+'.fbx')
        if f.exists():continue
        task=u.AssetExportTask()
        for k,v in [('object',sm),('filename',str(f)),('replace_identical',True),('prompt',False),('automated',True)]:task.set_editor_property(k,v)
        opts=u.FbxExportOption();opts.set_editor_property('collision',False);opts.set_editor_property('level_of_detail',False);task.set_editor_property('options',opts)
        if not u.Exporter.run_asset_export_task(task) or not f.exists():failed.append(key)
    report.update(status='exported' if not failed else 'partial',actors=actors,unique_meshes=len(meshes),failed=failed,materials=mats,
                  unresolved_colours=sorted(k for k,v in mats.items() if v is None))
    (OUT/'settlement09_context.json').write_text(json.dumps(report,ensure_ascii=False))
    print('CTX15',report['status'],len(actors),len(meshes),len(failed))
except Exception:
    report.update(status='error',error=traceback.format_exc());(OUT/'settlement09_context.json').write_text(json.dumps(report,indent=2));raise
