"""Read-only Blender material metadata export for the UE prototype."""
import bpy,json,sys,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2]
result={'sources':{},'materials':{},'objects':{}}
for aid,relative in [('StarterHouse_v004','Models/StarterHouse/v004/StarterHouse_v004.blend'),('TownBench_v001','Models/TownBench/v001/TownBench_v001.blend')]:
    path=root/relative
    bpy.ops.wm.open_mainfile(filepath=str(path))
    result['sources'][aid]={'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    for obj in bpy.data.objects:
        if obj.type!='MESH':continue
        result['objects'][aid+'_'+obj.name]=[slot.material.name if slot.material else None for slot in obj.material_slots]
        for slot in obj.material_slots:
            m=slot.material
            if not m:continue
            bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.node_tree else None
            color=list(bs.inputs['Base Color'].default_value if bs else m.diffuse_color)
            linked=bool(bs and bs.inputs['Base Color'].is_linked)
            # Preserve procedural palette by averaging the authored color-ramp endpoints.
            ramps=[n for n in m.node_tree.nodes if n.type=='VALTORGB'] if m.node_tree else []
            if linked and ramps:
                colors=[list(e.color) for e in ramps[0].color_ramp.elements]
                color=[sum(c[i] for c in colors)/len(colors) for i in range(4)]
            result['materials'][m.name]={'base_color_linear':color,'roughness':float(bs.inputs['Roughness'].default_value if bs else m.roughness),'metallic':float(bs.inputs['Metallic'].default_value if bs else m.metallic),'procedural_base_color':linked,'method':'color_ramp_mean' if linked and ramps else 'principled_default'}
(root/'Unreal/blender_palette.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
