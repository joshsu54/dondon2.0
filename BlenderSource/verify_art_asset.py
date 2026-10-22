"""Validate one saved asset and its FBX in Blender. Does not validate Unreal import."""
import bpy
import json
import sys
import math
from pathlib import Path
from mathutils import Vector
folder=Path(sys.argv[sys.argv.index('--')+1])
blend=next(folder.glob('*.blend')); fbx=next(folder.glob('*.fbx'))
bpy.ops.wm.open_mainfile(filepath=str(blend))
source=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and
        not any(c.name.startswith(('80_','90_','91_','92_')) for c in o.users_collection)]
assert source
assert all(math.isfinite(v) for o in source for p in o.data.vertices for v in p.co)
def bounds(objects):
    deps=bpy.context.evaluated_depsgraph_get()
    pts=[o.matrix_world@Vector(p) for src in objects for o in [src.evaluated_get(deps)] for p in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
before=bounds(source)
test=bpy.data.scenes.new('Asset_FBX_Validation'); bpy.context.window.scene=test
bpy.ops.import_scene.fbx(filepath=str(fbx))
imported=[o for o in test.objects if o.type=='MESH']
assert len(source)==len(imported),(len(source),len(imported))
after=bounds(imported)
error=max(abs(a-b) for aa,bb in zip(before,after) for a,b in zip(aa,bb))
assert error<.01,error
assert not any(o.type in ('CAMERA','LIGHT') for o in test.objects)
report={'blend_reopened':True,'finite_vertices':True,'source_meshes':len(source),'fbx_meshes':len(imported),
        'fbx_bounds_max_error_m':error,'world_bounds_m':before,'studio_excluded':True,'unreal_import_verified':False}
(folder/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('VALIDATED',json.dumps(report),flush=True)
