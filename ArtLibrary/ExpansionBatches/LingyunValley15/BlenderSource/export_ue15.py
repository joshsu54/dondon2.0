"""Export a UE-ready mesh set from LingyunValley_v001.blend (does not modify the blend):
merged meshes per logical part, world-space vertices (place actors at 0), the terrain 'dirt' attribute baked into
vertex colour R for the UE meadow material, and a palette JSON of material base colours.
blender --background --python-exit-code 1 --python export_ue15.py      -> ../UE/*.fbx, ../UE/ue15_palette.json
"""
import bpy,bmesh,json,hashlib
from pathlib import Path
BATCH=Path(__file__).resolve().parents[1];OUT=BATCH/'UE'
SRC=BATCH/'Models/LingyunValley/v001/LingyunValley_v001.blend'
assert not (OUT/'ue15_palette.json').exists(),'UE export already exists'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
dg=bpy.context.evaluated_depsgraph_get()
def merged(name,objs):
    """Evaluated, world-space merge of objs into one mesh with their materials."""
    bm=bmesh.new();mats=[]
    for o in objs:
        if o.type!='MESH':continue
        me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg);me.transform(o.matrix_world)
        remap={}
        for i,slot in enumerate(o.material_slots):
            m=slot.material
            if m not in mats:mats.append(m)
            remap[i]=mats.index(m)
        for p in me.polygons:p.material_index=remap.get(p.material_index,0)
        bm.from_mesh(me);bpy.data.meshes.remove(me)
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free()
    for m in mats:me.materials.append(m)
    return me
def children(root):return [o for o in bpy.data.objects if o.parent==root]
parts={'LY10_Terrain':[bpy.data.objects['Terrain_Meadow']],
       'LY10_CliffRim':[bpy.data.objects['Cliff_Rim']]+[o for o in bpy.data.collections['30_RimRocks'].objects if o.name.startswith('Rim_Boulder')],
       'LY10_Camp_Dormitory':children(bpy.data.objects['Camp_Dormitory']),'LY10_Camp_HerbGarden':children(bpy.data.objects['Camp_HerbGarden']),
       'LY10_Camp_HexPavilion':children(bpy.data.objects['Camp_HexPavilion']),'LY10_Camp_Paths':children(bpy.data.objects['Camp_Paths'])}
for o in bpy.data.collections['20_KarstPeaks'].objects:parts['LY10_'+o.name]=[o]
scene=bpy.data.scenes.new('UE_Export');palette={'materials':{},'parts':{}}
for name,objs in parts.items():
    me=merged(name,objs)
    if name=='LY10_Terrain':   # bake dirt (0..1) into vertex colour R
        src=objs[0].data.attributes['dirt'].data;col=me.color_attributes.new('Col','FLOAT_COLOR','POINT')
        for i,d in enumerate(src):col.data[i].color=(d.value,0.,0.,1.)
        me.color_attributes.active_color=col
    ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
    with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0],active_object=ob,selected_objects=[ob]):
        bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',
                                 apply_unit_scale=True,colors_type='LINEAR',use_mesh_modifiers=False,bake_anim=False)
    scene.collection.objects.unlink(ob)
    lo=[min(v.co[i] for v in me.vertices) for i in range(3)];hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
    palette['parts'][name]={'fbx':name+'.fbx','sha256':hashlib.sha256((OUT/(name+'.fbx')).read_bytes()).hexdigest(),'bounds_m':[lo,hi],
                            'triangles':sum(len(p.vertices)-2 for p in me.polygons),'materials':[m.name for m in me.materials]}
    for m in me.materials:
        if m.name in palette['materials']:continue
        bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        ramps=[n for n in m.node_tree.nodes if n.type=='VALTORGB']
        cols=[[sum(c)/2 for c in zip(r.color_ramp.elements[0].color[:3],r.color_ramp.elements[1].color[:3])] for r in ramps]
        palette['materials'][m.name]={'color':cols[0] if cols else list(m.diffuse_color)[:3],'second':cols[1] if len(cols)>1 else None,
                                      'roughness':bs.inputs['Roughness'].default_value,'metallic':bs.inputs['Metallic'].default_value}
    print('EXPORTED',name,palette['parts'][name]['triangles'],flush=True)
palette['note']='World-space vertices in metres (north +Y); import into UE with transform_vertex_to_absolute and place actors at 0. Terrain vertex colour R = dirt.'
(OUT/'ue15_palette.json').write_text(json.dumps(palette,indent=2))
print('UE_EXPORT_DONE',len(parts),flush=True)
