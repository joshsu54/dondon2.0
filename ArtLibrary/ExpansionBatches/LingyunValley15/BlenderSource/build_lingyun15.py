"""LingyunValley15 builder (Blender 5.2 CLI). Writes only inside this batch folder and refuses to overwrite results.
  blender --background --python-exit-code 1 --python build_lingyun15.py -- scene   # valley scene, FBX, scatter JSON, 10 views
  blender --background --python-exit-code 1 --python build_lingyun15.py -- camp    # three camp buildings as standalone assets
Scene coordinates are the TownLayout_09 world frame (Blender m, north +Y = UE -Y); not recentred, so it lines up with UE.
"""
import bpy,sys,json,math,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
SRC=Path(__file__).resolve().parent;BATCH=SRC.parent;REPO=BATCH.parents[2]
def load(name):
    spec=importlib.util.spec_from_file_location(name,SRC/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sys.modules[name]=m;return m
T=load('terrain15');MT=load('materials15');C=load('camp15');V=load('veg15');RD=load('render15')
REPLACED_PLATES=('TownLayout_v004_Terrain_Display_Island','TownLayout_v004_North_Terrace_Ground')

def new_coll(name,parent=None):
    c=bpy.data.collections.new(name);(parent or bpy.context.scene.collection).children.link(c);return c

def bounds(objs):
    dg=bpy.context.evaluated_depsgraph_get();pts=[]
    for o in objs:
        e=o.evaluated_get(dg)
        if o.type=='MESH':pts+= [e.matrix_world@v.co for v in e.data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]),Vector([max(p[i] for p in pts) for i in range(3)])

def render_views(scene,cam,centre,points,folder):
    records=[];folder.mkdir(parents=True,exist_ok=True)
    for name,d in RD.VIEWS:
        RD.aim(cam,centre,d);scale=1.
        while not RD.fits(scene,cam,points) and scale<1000:scale*=1.04;cam.data.ortho_scale=scale
        scene.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True)
        records.append({'file':name+'.png','direction':list(d),'camera_location':list(cam.location),'ortho_scale':scale,'projection':'orthographic','framing_checked':True})
        print('VIEW_COMPLETE',folder.name,name,flush=True)
    return records

def scene_build():
    out=BATCH/'Models/LingyunValley/v001';views=BATCH/'ArtLibrary/Turnarounds/LingyunValley_v001'
    if (views/'views.json').exists():print('ALREADY_COMPLETE scene');return
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;bpy.context.preferences.filepaths.save_version=0
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    # Settlement context appended (self-contained file); two UE ground plates are hidden because the terrain replaces them.
    with bpy.data.libraries.load(str(BATCH/'Context/Settlement09_context.blend'),link=False) as (src,dst):dst.collections=['00_Settlement09_UE_Context']
    ctx=dst.collections[0];s.collection.children.link(ctx)
    # Evaluate transforms before building the ground BVH: freshly appended objects still report identity
    # matrix_world, which silently dropped every Expansion04/06 surface (gate terrace, stairs) on the first build.
    bpy.context.view_layer.update()
    for n in REPLACED_PLATES:
        o=bpy.data.objects[n];o.hide_render=o.hide_viewport=True;o['replaced_by']='Terrain_Meadow'
    mats=MT.build_all()
    cT=new_coll('10_ContinuousTerrain');cP=new_coll('20_KarstPeaks');cR=new_coll('30_RimRocks');cC=new_coll('40_SouthCamp')
    cV=new_coll('50_VegetationScatter');lib=new_coll('90_AssetLibrary_Hidden');lib.hide_render=True;lib.hide_viewport=True
    st=new_coll('99_Studio_Not_Exported')
    tree,used=T.ground_bvh(list(ctx.all_objects))
    terr,cols,H,nu,nv=T.build_terrain(cT,tree,mats)
    rim,nboulders=T.build_cliff_rim(cR,terr,mats)
    peaks=T.build_peaks(cP,terr,mats)
    ga=lambda x,y:T.height_at(terr,x,y)
    camp=[C.dormitory(cC,mats,ga(*C.DORM)),C.herb_garden(cC,mats,ga(*C.GARDEN)),C.hex_pavilion(cC,mats,ga(*C.PAVILION))]
    proot,nslabs,nlanterns=C.paths(cC,mats,ga)
    meshes=V.load_assets(REPO,lib);placed=V.scatter(cV,meshes,terr,T.PEAKS,peaks,T.ring_factor)
    # FBX: new geometry only (terrain, rim, peaks, camp, paths); vegetation goes to the scatter JSON.
    bpy.context.view_layer.update()
    export=[o for c in (cT,cP,cR,cC) for o in c.all_objects]
    bpy.ops.object.select_all(action='DESELECT')
    for o in export:o.select_set(True)
    bpy.context.view_layer.objects.active=terr
    bpy.ops.export_scene.fbx(filepath=str(out/'LingyunValley_v001.fbx'),use_selection=True,object_types={'MESH','EMPTY'},add_leaf_bones=False,
                             axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',use_mesh_modifiers=True,bake_anim=False)
    ue=[{'asset':p['asset'],'ue_location_cm':[p['location_m'][0]*100,-p['location_m'][1]*100,p['location_m'][2]*100],
         'ue_yaw_deg':-math.degrees(p['yaw_rad']),'scale':p['scale'],'on':p['on']} for p in placed]
    (out/'vegetation_scatter_ue.json').write_text(json.dumps({'note':'UE coords: x=bx*100, y=-by*100, z=bz*100, yaw=-blender_yaw. Meshes: /Game/Art/WildVegetation08/Meshes/<asset>.',
        'count':len(ue),'placements':ue},indent=1))
    mesh_objs=[o for o in export if o.type=='MESH'];lo,hi=bounds(mesh_objs)
    tris=sum(len(p.vertices)-2 for o in mesh_objs for p in o.data.polygons)
    info={'asset':'LingyunValley','name_zh':'凌雲山谷地形','version':'v001','units':'meters','north':'+Y (UE -Y)','frame':'TownLayout_09 world; not recentred',
          'dimensions_m':list(hi-lo),'bounds_m':[list(lo),list(hi)],'export_mesh_objects':len(mesh_objs),'export_triangles':tris,
          'terrain_vertices':len(terr.data.vertices),'context_ground_objects':len(used),'rim_boulders':nboulders,
          'peaks':[{'name':n,'x':x,'y':y,'radius_m':r,'height_m':h} for n,x,y,r,h in T.PEAKS],
          'camp':{'dormitory':list(C.DORM),'herb_garden':list(C.GARDEN),'hex_pavilion':list(C.PAVILION),'path_slabs':nslabs,'lantern_posts':nlanterns},
          'vegetation_instances':len(placed),'replaced_ue_ground_plates':list(REPLACED_PLATES),
          'concept_references':'References/*.webp (13 images, art direction only)','uv_baked':False,'collision':False,'lod':False,'unreal_import_verified':False}
    (out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    RD.studio(s,st);cam=RD.camera(s,st,(0,8.5,8),150.)
    for o in st.objects:o['studio']=True
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'LingyunValley_v001.blend'))
    pts=[Vector((x,y,z)) for x in (lo.x-1,hi.x+1) for y in (lo.y-1,hi.y+1) for z in (lo.z,hi.z)]
    recs=render_views(s,cam,((lo.x+hi.x)/2,(lo.y+hi.y)/2,(lo.z+hi.z)/2),pts,views)
    (views/'views.json').write_text(json.dumps({'asset':'LingyunValley','source':'Models/LingyunValley/v001/LingyunValley_v001.blend','same_geometry':True,'views':recs},indent=2))
    print('SCENE_COMPLETE',flush=True)

def camp_build():
    builders=[('CampDormitory','營地宿舍',C.dormitory),('CampHerbGarden','營地藥圃',C.herb_garden),('CampHexPavilion','營地六角亭',C.hex_pavilion)]
    for aid,zh,fn in builders:
        out=BATCH/'Models'/aid/'v001';views=BATCH/'ArtLibrary/Turnarounds'/f'{aid}_v001'
        if (views/'views.json').exists():print('ALREADY_COMPLETE',aid);continue
        out.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;bpy.context.preferences.filepaths.save_version=0
        mats=MT.build_all();coll=new_coll('01_Editable_Asset');st=new_coll('90_Studio_Not_Exported')
        root=fn(coll,mats,0.);root.name=aid+'_ROOT';root.location=(0,0,0);bpy.context.view_layer.update()
        objs=[o for o in coll.objects if o.type=='MESH'];lo,hi=bounds(objs)
        shift=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))   # bottom-centre origin; root stays at 0
        for o in objs:o.location-=shift
        bpy.context.view_layer.update();lo,hi=bounds(objs)
        bpy.ops.object.select_all(action='DESELECT')
        for o in [root]+objs:o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.fbx(filepath=str(out/f'{aid}_v001.fbx'),use_selection=True,object_types={'MESH','EMPTY'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False)
        tris=sum(len(p.vertices)-2 for o in objs for p in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
        info={'asset':aid,'name_zh':zh,'units':'meters','front':'+X faces the path in the valley scene; turnaround 01_front looks from -Y',
              'pivot':'bottom centre','dimensions_m':list(hi-lo),'mesh_objects':len(objs),'triangles':tris,'removable_roof_parts':len([o for o in objs if o.get('part')=='removable_roof']),
              'scene_placement_m':list({'CampDormitory':C.DORM,'CampHerbGarden':C.GARDEN,'CampHexPavilion':C.PAVILION}[aid]),
              'stage':'editable procedural prototype','uv_baked':False,'collision':False,'lod':False,'unreal_import_verified':False}
        (out/'model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
        RD.studio(s,st);cam=RD.camera(s,st,(0,0,0),10.)
        bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{aid}_v001.blend'))
        pts=[Vector((x,y,z)) for x in (lo.x,hi.x) for y in (lo.y,hi.y) for z in (lo.z,hi.z)]
        recs=render_views(s,cam,((lo.x+hi.x)/2,(lo.y+hi.y)/2,(lo.z+hi.z)/2),pts,views)
        (views/'views.json').write_text(json.dumps({'asset':aid,'source':f'Models/{aid}/v001/{aid}_v001.blend','same_geometry':True,'views':recs},indent=2))
        print('ASSET_COMPLETE',aid,flush=True)

if __name__=='__main__':
    mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'scene'
    {'scene':scene_build,'camp':camp_build}[mode]()
