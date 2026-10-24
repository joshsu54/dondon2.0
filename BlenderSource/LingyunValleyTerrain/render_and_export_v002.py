import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Models/LingyunValleyTerrain/v002'
VIEWS=ROOT/'ArtLibrary/Turnarounds/LingyunValleyTerrain_v002';VIEWS.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'LingyunValleyTerrain_v002.blend'))
scene=bpy.context.scene;camera=scene.camera
defs=[('01_front',0,25),('02_right',90,25),('03_rear',180,25),('04_left',270,25),('05_front_right',45,35),
      ('06_rear_right',135,35),('07_rear_left',225,35),('08_front_left',315,35),('09_top',0,90),('10_high_front',0,65)]
bpy.context.view_layer.update()
objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
points=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box]
lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)));center=(lo+hi)*.5
manifest={'asset':'LingyunValleyTerrain_v002','units':'metres','front':'-Y','north':'+Y','bounds_m':[list(lo),list(hi)],
          'same_geometry_all_views':True,'source_context':'../v001/Source/Settlement10.fbx','views':[],
          'unreal_import_verified':False,'uv_baked':False,'collision_ready':False,'lod_ready':False}
for name,az,el in defs:
    a,e=math.radians(az),math.radians(el);d=Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
    camera.location=center+d*400;camera.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
    if name=='09_top':camera.rotation_euler=(0,0,0) # Image up is world +Y (north).
    bpy.context.view_layer.update()
    pp=[camera.matrix_world.inverted()@p for p in points]
    minx,maxx=min(p.x for p in pp),max(p.x for p in pp);miny,maxy=min(p.y for p in pp),max(p.y for p in pp)
    camera.data.ortho_scale=max(maxx-minx,maxy-miny)*1.10
    camera.location+=camera.matrix_world.to_quaternion()@Vector(((minx+maxx)/2,(miny+maxy)/2,0))
    dest=VIEWS/(name+'.png');scene.render.filepath=str(dest)
    if not dest.exists() or name=='09_top':bpy.ops.render.render(write_still=True)
    manifest['views'].append({'file':name+'.png','azimuth_deg':az,'elevation_deg':el,'camera_m':list(camera.location),
                              'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    (VIEWS/'views.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('VIEW_DONE',name,flush=True)
bpy.ops.object.select_all(action='DESELECT')
for coll in ('10_ContinuousTerrain','20_KarstPeaks','30_GroundCoverAndFoothills'):
    for o in bpy.data.collections[coll].objects:
        if o.type=='MESH':
            # FBX requires consistent mesh/material indices per object.
            materials=[slot.material for slot in o.material_slots]
            o.data=o.data.copy()
            for index,mat in enumerate(materials):
                o.material_slots[index].link='DATA';o.material_slots[index].material=mat
            o.select_set(True)
fbx=OUT/'LingyunValleyTerrain_v002.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
manifest['fbx_sha256']=hashlib.sha256(fbx.read_bytes()).hexdigest()
manifest['blend_sha256']=hashlib.sha256((OUT/'LingyunValleyTerrain_v002.blend').read_bytes()).hexdigest()
(OUT/'model_info.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('EXPORT_COMPLETE',flush=True)
