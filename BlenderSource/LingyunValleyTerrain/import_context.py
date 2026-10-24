import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[2]
out=root/'Models/LingyunValleyTerrain/v001'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(out/'Source/Settlement10.fbx'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
rows=[]
for o in meshes:
    if any(s in o.name for s in ['CampPath_00','GardenHerb_0_0','DormRoof','Wild08_CommonPine_00','SectGate04','SectRoad_00','TownLayout_v004_Ground']):
        p=[o.matrix_world@Vector(v) for v in o.bound_box]
        rows.append({'name':o.name,'location':list(o.location),'bounds':[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]],
                     'materials':[(m.name,list(m.diffuse_color)) for m in o.data.materials if m]})
report={'mesh_count':len(meshes),'bounds':[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]],
        'anchors':rows,'names':[o.name for o in meshes[:35]]}
(out/'Source/context_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Source/SettlementContext.blend'))
