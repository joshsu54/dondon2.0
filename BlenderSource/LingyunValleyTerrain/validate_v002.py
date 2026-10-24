import bpy,bmesh,json,math,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Models/LingyunValleyTerrain/v002'
VIEWS=ROOT/'ArtLibrary/Turnarounds/LingyunValleyTerrain_v002'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LingyunValleyTerrain_v002.blend'))
scene=bpy.context.scene
selected=[o for c in ('10_ContinuousTerrain','20_KarstPeaks','30_GroundCoverAndFoothills') for o in bpy.data.collections[c].objects if o.type=='MESH']
def bounds(objects):
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
before=bounds(selected)
terrain=bpy.data.objects['Lingyun_ContinuousTerrain']
bm=bmesh.new();bm.from_mesh(terrain.data)
geometry={'vertices':len(bm.verts),'faces':len(bm.faces),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'loose_vertices':sum(not v.link_edges for v in bm.verts),'finite_coordinates':all(math.isfinite(x) for v in bm.verts for x in v.co)}
bm.free()
manifest=json.loads((VIEWS/'views.json').read_text())
sizes={p.name:list(struct.unpack('>II',p.read_bytes()[16:24])) for p in VIEWS.glob('*.png')}
report={'blend_reopened':True,'units':'metres','front':'-Y','north':'+Y','terrain_geometry':geometry,'png_sizes':sizes,'unique_cameras':len(set(tuple(v['camera_m']) for v in manifest['views'])),'export_mesh_count':len(selected),'export_bounds_m':before,'visual_review':'Ten renders inspected; terrain study, not finished gameplay terrain. Peaks and ground need further art refinement.','unreal_import_verified':False,'collision_ready':False,'uv_baked':False,'lod_ready':False}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(OUT/'LingyunValleyTerrain_v002.fbx'))
imported=[o for o in bpy.context.scene.objects if o.type=='MESH']
after=bounds(imported)
delta=max(abs(before[i][j]-after[i][j]) for i in range(2) for j in range(3))
report.update(fbx_reimport_mesh_count=len(imported),fbx_reimport_bounds_m=after,fbx_max_bounds_error_m=delta)
report['checks']={'ten_1024_views':len(sizes)==10 and all(s==[1024,1024] for s in sizes.values()),'ten_unique_camera_positions':report['unique_cameras']==10,'fbx_mesh_count_matches':len(selected)==len(imported),'fbx_bounds_match':delta<.005,'terrain_closed_edges':geometry['nonmanifold_edges']==0,'finite_geometry':geometry['finite_coordinates']}
report['status']='passed' if all(report['checks'].values()) else 'needs_review'
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True),flush=True)
