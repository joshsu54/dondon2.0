"""Read existing Blender assets for UE material colors; never saves source files."""
import bpy,json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[2]
assets={'CloudpiercerPeak':'v002','MountainRidge':'v002','SectGate':'v001','MountainStoneStairs':'v001','MountainStonePath':'v001','SpiritHerbMature':'v001','MountainSanctuary':'v004'}
result={'sources':{},'materials':{}}
for name,v in assets.items():
 p=r/'Models'/name/v/(name+'_'+v+'.blend');bpy.ops.wm.open_mainfile(filepath=str(p))
 result['sources'][name]={'version':v,'blend':str(p.relative_to(r)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 for m in bpy.data.materials:
  bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.node_tree else None
  color=list(bs.inputs['Base Color'].default_value if bs else m.diffuse_color)
  ramps=[n for n in m.node_tree.nodes if n.type=='VALTORGB'] if m.node_tree else []
  if bs and bs.inputs['Base Color'].is_linked and ramps:
   colors=[list(e.color) for e in ramps[0].color_ramp.elements];color=[sum(c[i] for c in colors)/len(colors) for i in range(4)]
  result['materials'][m.name]={'color':color,'roughness':float(bs.inputs['Roughness'].default_value if bs else m.roughness),'metallic':float(bs.inputs['Metallic'].default_value if bs else m.metallic)}
(r/'Unreal/expansion04_palette.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
