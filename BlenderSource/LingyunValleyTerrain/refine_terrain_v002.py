"""Refine the first terrain study non-destructively: organic karst and blended town foundations."""
import bpy,bmesh,ast,math,random,json
from pathlib import Path
from mathutils import Vector,noise
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Models/LingyunValleyTerrain/v002';OUT.mkdir(parents=True,exist_ok=True)
target=OUT/'LingyunValleyTerrain_v002.blend'
assert not target.exists(),'Preserve existing v002'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Models/LingyunValleyTerrain/v001/LingyunValleyTerrain_v001.blend'))
scene=bpy.context.scene
assets=bpy.data.collections['20_KarstPeaks']
for o in list(assets.objects):bpy.data.objects.remove(o,do_unlink=True)
root=bpy.data.objects.new('KarstMassif_EditableGroup',None);assets.objects.link(root)
# Reuse the project's existing, inspected karst geometry functions without executing its build/export entry point.
source=ROOT/'ArtLibrary/ExpansionBatches/MountainWind07/BlenderSource/build_peaks_v002.py'
tree=ast.parse(source.read_text(encoding='utf-8'))
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('smooth','rock_material','pillar')]
exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),globals())
MAT=rock_material();MAT.name='Terrain14_KarstRockMoss'
definitions=[(-44,63,10,12,34),(-22,98,12,13,43),(28,97,13,12,51),(51,56,8,9,30),(-53,3,7,8,23)]
pine=bpy.data.objects.get('Wild08_CommonPine_00')
rng=random.Random(231027)
for i,(x,y,rx,ry,h) in enumerate(definitions):
    o=pillar('Terrain14_MainPeak_%02d'%i,x,y,rx,ry,h,231027+i,lean=(1.5,-1),taper=.18,cap=.32,flare=.22)
    o.location.z=2
    # Satellite columns form a rocky shoulder and break the simple tower silhouette.
    for j,(dx,dy,sz) in enumerate([(-.7,-.50,.58),(.65,-.35,.72)]):
        p=pillar('Terrain14_Satellite_%d_%d'%(i,j),x+dx*rx,y+dy*ry,rx*.55,ry*.58,h*sz,3000+i*10+j,
                 lean=(.5,.8),taper=.22,cap=.40,flare=.3)
        p.location.z=2
    if pine:
        for j in range(3):
            p=pine.copy();p.data=pine.data;assets.objects.link(p);p.name='SummitPine_%d_%d'%(i,j)
            p.location=(x+rng.uniform(-rx*.3,rx*.3),y+rng.uniform(-ry*.3,ry*.3),h+1.8)
            p.scale=tuple(a*.5 for a in pine.scale)
# Replace visible rectangular soil display bases with continuous land at the same elevations.
for name in ['TownLayout_v004_North_Terrace_Ground','TownLayout_v004_Terrain_Display_Island']:
    o=bpy.data.objects.get(name)
    if o:o.hide_render=True;o.hide_viewport=True
terrain=bpy.data.objects['Lingyun_ContinuousTerrain']
def weight(value,lo,hi,fade):
    return smooth(lo-fade,lo,value)*(1-smooth(hi,hi+fade,value))
for v in terrain.data.vertices:
    x,y,z=v.co
    if z< -5:continue
    town=weight(x,-25.7,21.7,2.5)*weight(y,12,40.4,2.5)
    lower=weight(x,-10.7,17.7,1.5)*weight(y,-12.7,13.7,1.5)
    path=weight(x,-1.8,1.8,1)*weight(y,-61,-15,1)
    if town>0:v.co.z=v.co.z*(1-town)+1.10*town
    if lower>0:v.co.z=v.co.z*(1-lower)-.035*lower
    if path>0:v.co.z=v.co.z*(1-path)-.065*path
bm=bmesh.new();bm.from_mesh(terrain.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(terrain.data);bm.free()
terrain.data.update()
grass=bpy.data.materials['Terrain_Meadow']
ramp=next(n for n in grass.node_tree.nodes if n.bl_idname=='ShaderNodeValToRGB')
for elem,col in zip(sorted(ramp.color_ramp.elements,key=lambda e:e.position),[(.065,.14,.022,1),(.17,.25,.055,1),(.32,.29,.12,1)]):elem.color=col
# The uniform grey studio is only a viewing background, not a game landscape.
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.82,.86,1)
scene.cycles.samples=12
bpy.ops.wm.save_as_mainfile(filepath=str(target))
print('REFINED_TERRAIN_READY',str(target),flush=True)
