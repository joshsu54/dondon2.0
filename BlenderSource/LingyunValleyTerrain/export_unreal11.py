"""Prepare grouped UE meshes from the reviewed Blender study; leave the blend unchanged."""
import bpy,bmesh,json,re
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Models/LingyunValleyTerrain/v002/Unreal11';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT.parent/'LingyunValleyTerrain_v002.blend'))
palette={};report={}
for coll,name in [('10_ContinuousTerrain','ValleyTerrain11'),('20_KarstPeaks','ValleyPeaks11'),('30_GroundCoverAndFoothills','ValleyDressing11')]:
    bpy.ops.object.select_all(action='DESELECT')
    objects=[o for o in bpy.data.collections[coll].objects if o.type=='MESH' and not o.hide_render]
    for o in objects:
        mats=[s.material for s in o.material_slots];o.data=o.data.copy()
        for i,m in enumerate(mats):o.material_slots[i].link='DATA';o.material_slots[i].material=m
        if name=='ValleyTerrain11':
            bm=bmesh.new();bm.from_mesh(o.data)
            bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS');bm.to_mesh(o.data);bm.free()
        for m in mats:
            if m:palette[m.name]=list(m.diffuse_color)
        o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join();obj=bpy.context.object;obj.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    pts=[obj.matrix_world@Vector(p) for p in obj.bound_box]
    report[name]={'bounds_m':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],'vertices':len(obj.data.vertices),'faces':len(obj.data.polygons)}
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
(OUT/'manifest.json').write_text(json.dumps({'meshes':report,'materials':palette},indent=2),encoding='utf-8')
print('UE11_EXPORT_COMPLETE')
