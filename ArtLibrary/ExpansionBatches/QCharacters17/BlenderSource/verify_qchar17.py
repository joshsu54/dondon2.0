"""Reopen every QCharacters17 model, check pivot/size/face parts, round-trip FBX and check the ten views.
blender --background --python-exit-code 1 --python verify_qchar17.py      -> ../validation.json
"""
import bpy,json,math,struct,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
SRC=Path(__file__).resolve().parent;BATCH=SRC.parent
import os
VER=os.environ.get('QCHAR_VERSION','v001')
spec=importlib.util.spec_from_file_location('qchar17',SRC/('qchar17.py' if VER=='v001' else f'qchar17_{VER}.py'));Q=importlib.util.module_from_spec(spec);spec.loader.exec_module(Q)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bounds(objs):
    dg=bpy.context.evaluated_depsgraph_get();pts=[o.evaluated_get(dg).matrix_world@v.co for o in objs for v in o.evaluated_get(dg).data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]),Vector([max(p[i] for p in pts) for i in range(3)])
results=[]
for aid,specd in Q.CHARACTERS.items():
    p=BATCH/'Models'/aid/VER/f'{aid}_{VER}.blend';bpy.ops.wm.open_mainfile(filepath=str(p))
    objs=[o for o in bpy.data.collections['01_Editable_Asset'].objects if o.type=='MESH']
    assert objs and all(o.data.vertices for o in objs) and all(math.isfinite(c) for o in objs for v in o.data.vertices for c in v.co)
    lo,hi=bounds(objs);size=hi-lo
    assert abs(lo.z)<.001 and abs(lo.x+hi.x)<.002 and abs(lo.y+hi.y)<.002,(aid,lo,hi)
    info=json.loads((p.parent/'model_info.json').read_text(encoding='utf-8'));assert max(abs(size[i]-info['dimensions_m'][i]) for i in range(3))<.002
    names=[o.name.split('.')[0] for o in objs]
    eyes=names.count('Eye_Closed') if specd.get('eyes')=='sleepy' else names.count('Eye_Iris')
    head=next(o for o in objs if o.name=='Head');hl,hh=bounds([head])
    # Face parts carry world-space vertices (object origin at 0), so test their vertices, not their origins.
    fp=[o for o in objs if o.name.startswith(('Eye_Iris','Eye_Closed','Mouth'))];fl,fh=bounds(fp)
    checks={'two_eyes':eyes==2,'two_hands':names.count('Hand')+names.count('Hand_Back')==2,'two_shoes':names.count('Shoe')==2,
            'face_in_front_of_head':fh.y<hl.y*.3,'head_height_ratio':(hh.z-hl.z)/size.z}
    assert checks['two_eyes'] and checks['two_hands'] and checks['two_shoes'] and checks['face_in_front_of_head'],(aid,checks)
    count=len(objs)
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(p.with_suffix('.fbx')))
    imp=[o for o in bpy.context.scene.objects if o.type=='MESH'];a,b=bounds(imp);err=max(abs(size[i]-(b-a)[i]) for i in range(3))
    assert len(imp)==count and err<.002,(aid,len(imp),count,err);assert not any(o.type in ('LIGHT','CAMERA') for o in bpy.context.scene.objects)
    folder=BATCH/'ArtLibrary/Turnarounds'/f'{aid}_{VER}';man=json.loads((folder/'views.json').read_text())
    assert man['same_geometry'] and len(man['views'])==10 and len({tuple(v['direction']) for v in man['views']})==10;hs=set()
    for v in man['views']:
        d=(folder/v['file']).read_bytes();assert d[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',d[16:24])==(1024,1024);hs.add(hashlib.sha256(d).hexdigest())
    assert len(hs)==10
    results.append({'asset':aid,'name_zh':specd['zh'],'blend_reopened':True,'bottom_center_pivot':True,'height_m':size.z,'mesh_objects':count,'checks':checks,
                    'fbx_reimported':True,'fbx_dimension_error_m':err,'distinct_1024_views':10,'blend_sha256':sha(p),'fbx_sha256':sha(p.with_suffix('.fbx'))})
    print('VERIFIED',aid,flush=True)
ds=BATCH/('DesignSheets' if VER=='v001' else f'DesignSheets_{VER}');sheets=[f.name for f in ds.glob('lineup_*.png')];assert len(sheets)==3
(BATCH/('validation.json' if VER=='v001' else f'validation_{VER}.json')).write_text(json.dumps({'batch':'QCharacters17','version':VER,'blender':bpy.app.version_string,'assets':results,'design_sheets':sheets,
    'not_verified':['rigging / skinning / animation','UV and texture bake','LOD','Unreal import','in-game scale against doors and furniture']},ensure_ascii=False,indent=2),encoding='utf-8')
print('ALL_VERIFIED',len(results),flush=True)
