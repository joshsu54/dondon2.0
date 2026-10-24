"""Rebuild the TownLayout_09 settlement in Blender from Unreal/Tools/export_town_context15.py output, as read-only
layout context for the terrain. UE cm/left-handed -> Blender m, north +Y: p_b = (x, -y, z)/100 and rotation
columns (M f, -M r, M u) with M = diag(1,-1,1). Colours come from the UE material base colours.
blender --background --python-exit-code 1 --python import_context15.py -- <dir with per-mesh FBX>
Writes ../Context/Settlement09_context.blend (refuses to overwrite).
"""
import bpy,json,sys,time
from pathlib import Path
from mathutils import Matrix,Vector
BATCH=Path(__file__).resolve().parents[1];CTX=BATCH/'Context'
mesh_dir=Path(sys.argv[sys.argv.index('--')+1])
out=CTX/'Settlement09_context.blend'
assert not out.exists(),'Context blend already exists'
data=json.loads((CTX/'settlement09_context.json').read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
coll=bpy.data.collections.new('00_Settlement09_UE_Context');bpy.context.scene.collection.children.link(coll)
mats={}
def material(name):
    if name in mats:return mats[name]
    c=data['materials'].get(name) or [.5,.5,.5]
    m=bpy.data.materials.new('UE_'+name);m.use_nodes=True;m.diffuse_color=(*c,1)
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*c,1)
    bs.inputs['Roughness'].default_value=.85;bs.inputs['Specular IOR Level'].default_value=.2
    mats[name]=m;return m
M=Matrix.Diagonal((1,-1,1))
meshdata={};t0=time.time()
for i,key in enumerate(sorted({a['mesh'] for a in data['actors']})):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(mesh_dir/(key+'.fbx')))
    new=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    assert len(new)==1,(key,len(new))
    o=new[0];o.data.name=key
    # Bake the importer's object transform into the mesh so instances only carry the UE actor transform.
    o.data.transform(o.matrix_world);meshdata[key]=o.data
    for x in [x for x in bpy.data.objects if x not in before]:bpy.data.objects.remove(x,do_unlink=True)
    if i%250==0:print('IMPORTED',i,round(time.time()-t0),flush=True)
for a in data['actors']:
    f=M@Vector(a['forward']);r=M@Vector(a['right']);up=M@Vector(a['up'])
    rot=Matrix((f,-r,up)).transposed()
    loc=Vector((a['location'][0],-a['location'][1],a['location'][2]))/100
    o=bpy.data.objects.new(a['label'],meshdata[a['mesh']]);coll.objects.link(o)
    o.matrix_world=Matrix.Translation(loc)@rot.to_4x4()@Matrix.Diagonal((*a['scale'],1))
    o['ue_folder']=a['folder'];o['ue_collision']=a['collision']
    for i,mn in enumerate(a['materials']):
        if mn is None:continue
        m=material(mn)
        if i<len(o.material_slots):o.material_slots[i].link='OBJECT';o.material_slots[i].material=m
        else:o.data.materials.append(m)
CTX.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('CONTEXT_DONE',len(data['actors']),'actors',len(meshdata),'meshes',round(time.time()-t0),'s',flush=True)
