"""Render ten consistent views of each saved 3D asset; never edit source blend files.
Optional arguments after -- are asset IDs. Default: the existing four asset sets.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sources={
    'WelcomingPine':ROOT/'Models/WelcomingPine/v002/WelcomingPine_v002.blend',
    'SpawnPlaza':ROOT/'Models/SpawnTown/v001/SpawnTown_v001.blend',
    'StarterHouse':ROOT/'Models/StarterHouse/v004/StarterHouse_v004.blend',
    'Blacksmith':ROOT/'Models/Blacksmith/v001/Blacksmith_v001.blend',
}
shop=sorted((ROOT/'Models/MaterialShop').glob('v*/*.blend'))
if shop: sources['MaterialShop']=shop[-1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
refresh_cardinals='--refresh-cardinals' in args
ids=[x for x in args if x!='--refresh-cardinals'] or ['WelcomingPine','SpawnPlaza','StarterHouse','Blacksmith']
views=[('01_front',(0,-1,0)),('02_right',(1,0,0)),('03_rear',(0,1,0)),('04_left',(-1,0,0)),
       ('05_front_right',(1,-1,.65)),('06_rear_right',(1,1,.65)),('07_rear_left',(-1,1,.65)),
       ('08_front_left',(-1,-1,.65)),('09_top',(0,0,1)),('10_high_front',(0,-1,1))]
for asset_id in ids:
    source=sources[asset_id]
    out=ROOT/'ArtLibrary/Turnarounds'/f'{asset_id}_{source.parent.name}'
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and
             not any(c.name.startswith(('80_','90_','91_','92_')) for c in o.users_collection)]
    deps=bpy.context.evaluated_depsgraph_get()
    pts=[obj.matrix_world@Vector(p) for original in objects for obj in [original.evaluated_get(deps)] for p in obj.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    centre=(lo+hi)/2; extent=hi-lo
    scale=max(math.hypot(extent.x,extent.y),extent.z)*1.13
    camera=scene.camera; camera.data.type='ORTHO'; camera.data.ortho_scale=scale
    scene.render.resolution_x=1024; scene.render.resolution_y=1024; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.render.engine='CYCLES'
    scene.cycles.device='CPU'; scene.cycles.samples=20; scene.cycles.use_denoising=True
    for name,direction in views:
        file=out/(name+'.png')
        cardinal=name[:2] in ('01','02','03','04')
        if refresh_cardinals and not cardinal: continue
        if file.exists() and not refresh_cardinals: continue
        # At a truly horizontal orthographic angle, a studio slab becomes a dark
        # strip through the reference. Hide only studio meshes, retaining lights.
        for obj in scene.objects:
            if obj.type=='MESH' and any(c.name.startswith('90_') for c in obj.users_collection):
                obj.hide_render=cardinal
        camera.location=centre+Vector(direction).normalized()*scale*2
        camera.rotation_euler=(centre-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(file); bpy.ops.render.render(write_still=True)
        print('VIEW_COMPLETE',asset_id,name,flush=True)
    manifest={'asset':asset_id,'source':str(source.relative_to(ROOT)),'views':[n+'.png' for n,d in views],
              'projection':'orthographic','bounds_m':[list(lo),list(hi)],'ortho_width_m':scale,
              'front':'Blender -Y','source_modified':False,'generated_from_same_geometry':True,
              'cardinal_background':'Studio floor hidden for unobstructed elevations'}
    (out/'views.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('ASSET_COMPLETE',asset_id,flush=True)
