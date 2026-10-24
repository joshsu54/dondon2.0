"""Read-only: extract WildVegetation13 material colours and bounds for UE material overrides.
Blender CLI: blender --background --python-exit-code 1 --python extract_wild08_palette.py
Writes Unreal/wild08_palette.json. Colours are each material's mid tone (diffuse_color), as earlier palettes.
"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
unreal=Path(__file__).resolve().parents[1];repo=unreal.parent
ASSETS=['CommonPine','BambooClump','WildShrub','MossBoulderSet','ScreePile']
TWO_SIDED={'Bamboo_Leaf'}
out={'batch':'WildVegetation13','sources':{},'materials':{}}
for aid in ASSETS:
    blend=repo/'Models'/aid/'v001'/f'{aid}_v001.blend';fbx=blend.with_suffix('.fbx')
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes=[o for o in bpy.data.collections['01_Editable_Asset'].objects if o.type=='MESH']
    pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    out['sources'][aid]={'version':'v001','blend':blend.relative_to(repo).as_posix(),'sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'bounds_m':[lo,hi],'objects':len(meshes)}
    for m in {s.material for o in meshes for s in o.material_slots if s.material}:
        bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        out['materials'][m.name]={'color':list(m.diffuse_color)[:3],'roughness':bs.inputs['Roughness'].default_value,'metallic':bs.inputs['Metallic'].default_value,'two_sided':m.name in TWO_SIDED}
(unreal/'wild08_palette.json').write_text(json.dumps(out,indent=2))
print('PALETTE_DONE',len(out['materials']),'materials')
