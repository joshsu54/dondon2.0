"""Reopen LingyunValley15 outputs, measure terrain fit against the settlement, round-trip FBX, check ten views.
blender --background --python-exit-code 1 --python verify_lingyun15.py      -> ../validation.json
Reports measured numbers; asserts only on hard failures (missing data, broken FBX, wrong image sets).
"""
import bpy,sys,json,math,struct,hashlib,random,importlib.util
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SRC=Path(__file__).resolve().parent;BATCH=SRC.parent
def load(name):
    spec=importlib.util.spec_from_file_location(name,SRC/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sys.modules[name]=m;return m
T=load('terrain15');V=load('veg15');C=load('camp15')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bounds(objs):
    dg=bpy.context.evaluated_depsgraph_get();pts=[o.evaluated_get(dg).matrix_world@v.co for o in objs for v in o.evaluated_get(dg).data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]),Vector([max(p[i] for p in pts) for i in range(3)])
def views_ok(folder):
    man=json.loads((folder/'views.json').read_text());assert man['same_geometry'] and len(man['views'])==10
    assert len({tuple(v['direction']) for v in man['views']})==10;hs=set()
    for v in man['views']:
        d=(folder/v['file']).read_bytes();assert d[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',d[16:24])==(1024,1024);hs.add(hashlib.sha256(d).hexdigest())
    assert len(hs)==10;return 10
def fbx_roundtrip(path,count,size):
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path))
    imp=[o for o in bpy.context.scene.objects if o.type=='MESH'];a,b=bounds(imp)
    assert not any(o.type in ('LIGHT','CAMERA') for o in bpy.context.scene.objects)
    return len(imp),max(abs((b-a)[i]-size[i]) for i in range(3))
report={'batch':'LingyunValley15','blender':bpy.app.version_string,'assets':[]}
# ---------------- scene
blend=BATCH/'Models/LingyunValley/v001/LingyunValley_v001.blend';bpy.ops.wm.open_mainfile(filepath=str(blend))
info=json.loads((blend.parent/'model_info.json').read_text(encoding='utf-8'))
need=['00_Settlement09_UE_Context','10_ContinuousTerrain','20_KarstPeaks','30_RimRocks','40_SouthCamp','50_VegetationScatter']
assert all(n in bpy.data.collections for n in need)
terr=bpy.data.objects['Terrain_Meadow'];assert 'dirt' in terr.data.attributes
assert all(math.isfinite(c) for v in terr.data.vertices for c in v.co)
dg=bpy.context.evaluated_depsgraph_get();tt=BVHTree.FromObject(terr,dg)
def th(x,y):
    h=tt.ray_cast(Vector((x,y,200.)),Vector((0,0,-1)),400.);return h[0].z if h[0] is not None else None
ctx=list(bpy.data.collections['00_Settlement09_UE_Context'].all_objects)
tree,used=T.ground_bvh([o for o in ctx if not o.get('replaced_by')])
def top_up_surface(x,y):
    """Highest upward-facing near-ground surface (what the player sees on stacked slabs)."""
    h=tree.ray_cast(Vector((x,y,40.)),Vector((0,0,-1)),80.)
    while h[0] is not None and h[1].z<=.5:h=tree.ray_cast(h[0]-Vector((0,0,.004)),Vector((0,0,-1)),80.)
    return h[0].z if h[0] is not None and h[0].z<14 else None
rng=random.Random(7);samples=0;vis=0;vis_worst=0.;hidden=0;gap=0
for _ in range(12000):   # replaced plates are excluded, so only ~20 % of the box holds near-ground surfaces
    x,y=rng.uniform(-30,26),rng.uniform(-14,82);s=T.lowest_up_surface(tree,x,y)
    if s is None:continue
    z=th(x,y);top=top_up_surface(x,y)
    if z is None or top is None:continue
    samples+=1;vis_worst=max(vis_worst,z-top)
    if z-top>.02:vis+=1           # terrain shows through the visible top surface
    if z-s>.02:hidden+=1          # terrain above a lower slab but still under the top one (not visible)
    if z-s<-.25:gap+=1            # more than 25 cm below the lowest slab (hidden under the structure)
fit={'surface_samples':samples,'visible_pokes_above_top_surface_gt_2cm':vis,'visible_poke_ratio':vis/max(1,samples),'max_visible_poke_m':vis_worst,
     'between_stacked_slabs_not_visible':hidden,'more_than_25cm_below_lowest_slab':gap,
     'note':'Samples on near-ground settlement surfaces; plates replaced by the terrain excluded. Only visible pokes are defects.'}
assert samples>500,samples
camp={}
for name,(x,y) in (('Camp_Dormitory',C.DORM),('Camp_HerbGarden',C.GARDEN),('Camp_HexPavilion',C.PAVILION)):
    o=bpy.data.objects[name];camp[name]={'root_z':o.location.z,'terrain_z':th(x,y),'grounded':abs(o.location.z-th(x,y))<.06}
assert all(v['grounded'] for v in camp.values())
town_lo,town_hi=Vector((-26.2,-13.1,0)),Vector((22.3,49.6,0));clear={}
for n,x,y,r,h in T.PEAKS:
    o=bpy.data.objects[n];a,b=bounds([o])
    dx=max(town_lo.x-b.x,a.x-town_hi.x,0.);dy=max(town_lo.y-b.y,a.y-town_hi.y,0.)
    gx=max(-7.5-b.x,a.x-7.5,0.) if b.y>66.6 and a.y<77.4 else None
    clear[n]={'height_m':b.z-a.z,'clearance_to_town_box_m':math.hypot(dx,dy),'clearance_to_gate_terrace_x_m':gx}
scat=[o for o in bpy.data.collections['50_VegetationScatter'].objects]
bad=[o.name for o in scat if o.name.startswith('Scatter_') and any(x0<o.location.x<x1 and y0<o.location.y<y1 for x0,y0,x1,y1 in V.KEEP_OUT)]
assert not bad,bad[:5]
js=json.loads((blend.parent/'vegetation_scatter_ue.json').read_text());assert js['count']==len(scat)
export=[o for c in ('10_ContinuousTerrain','20_KarstPeaks','30_RimRocks','40_SouthCamp') for o in bpy.data.collections[c].all_objects if o.type=='MESH']
lo,hi=bounds(export);size=hi-lo;n=len(export)
cnt,err=fbx_roundtrip(blend.with_suffix('.fbx'),n,size);assert cnt==n and err<.01,(cnt,n,err)
report['assets'].append({'asset':'LingyunValley','blend_reopened':True,'terrain_fit':fit,'camp_grounding':camp,'peaks':clear,
    'vegetation_instances':len(scat),'scatter_in_keep_out':0,'fbx_mesh_objects':cnt,'fbx_dimension_error_m':err,'distinct_1024_views':views_ok(BATCH/'ArtLibrary/Turnarounds/LingyunValley_v001'),
    'blend_sha256':sha(blend),'fbx_sha256':sha(blend.with_suffix('.fbx')),'scatter_json_sha256':sha(blend.parent/'vegetation_scatter_ue.json')})
print('VERIFIED LingyunValley',flush=True)
# ---------------- camp assets
for aid in ('CampDormitory','CampHerbGarden','CampHexPavilion'):
    p=BATCH/'Models'/aid/'v001'/f'{aid}_v001.blend';bpy.ops.wm.open_mainfile(filepath=str(p))
    objs=[o for o in bpy.data.collections['01_Editable_Asset'].objects if o.type=='MESH'];lo,hi=bounds(objs)
    assert abs(lo.z)<.001 and abs(lo.x+hi.x)<.002 and abs(lo.y+hi.y)<.002,(aid,lo,hi)
    inf=json.loads((p.parent/'model_info.json').read_text(encoding='utf-8'));assert max(abs((hi-lo)[i]-inf['dimensions_m'][i]) for i in range(3))<.002
    cnt,err=fbx_roundtrip(p.with_suffix('.fbx'),len(objs),hi-lo);assert cnt==len(objs) and err<.005,(aid,cnt,len(objs),err)
    report['assets'].append({'asset':aid,'blend_reopened':True,'bottom_center_pivot':True,'mesh_objects':len(objs),'fbx_reimported':True,'fbx_dimension_error_m':err,
        'distinct_1024_views':views_ok(BATCH/'ArtLibrary/Turnarounds'/f'{aid}_v001'),'blend_sha256':sha(p),'fbx_sha256':sha(p.with_suffix('.fbx'))})
    print('VERIFIED',aid,flush=True)
report['not_verified']=['Unreal import of the terrain FBX','collision / navigation on the new terrain','UV and texture bake (procedural materials)','LOD','PIE traversal of camp and meadow']
(BATCH/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('ALL_VERIFIED',flush=True)
