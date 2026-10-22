"""Read-only source extraction for existing wayside assets; no blend is saved."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
r=Path(__file__).resolve().parents[2]
assets={n:'v001' for n in ['MountainRestPavilion','TrailStoneRailing','WindPine','WindGrass','StoneLantern','TownWaymarker']}
assets['NoticeBoard']='v002'
result={'sources':{},'materials':{}}
for name,v in assets.items():
 p=r/'Models'/name/v/(name+'_'+v+'.blend');bpy.ops.wm.open_mainfile(filepath=str(p))
 obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith(('Ground','Backdrop','Studio'))]
 coords=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
 result['sources'][name]={'version':v,'blend':str(p.relative_to(r)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fbx_sha256':hashlib.sha256(p.with_suffix('.fbx').read_bytes()).hexdigest(),'bounds_m':[[min(c[i] for c in coords) for i in range(3)],[max(c[i] for c in coords) for i in range(3)]],'objects':len(obs)}
 for m in bpy.data.materials:
  bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.node_tree else None
  color=list(bs.inputs['Base Color'].default_value if bs else m.diffuse_color)
  ramps=[n for n in m.node_tree.nodes if n.type=='VALTORGB'] if m.node_tree else []
  if bs and bs.inputs['Base Color'].is_linked and ramps:
   colors=[list(e.color) for e in ramps[0].color_ramp.elements];color=[sum(c[i] for c in colors)/len(colors) for i in range(4)]
  result['materials'][m.name]={'color':color,'roughness':float(bs.inputs['Roughness'].default_value if bs else m.roughness),'metallic':float(bs.inputs['Metallic'].default_value if bs else m.metallic)}
(r/'Unreal/expansion06_palette.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print(json.dumps(result['sources'],indent=2))
