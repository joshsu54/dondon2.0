import unreal as u,json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
try:
    m=u.load_asset('/Game/Art/Terrain11/Materials/M_Terrain14_KarstRockMoss');L=u.MaterialEditingLibrary;assert m
    L.delete_all_material_expressions(m)
    def node(cls):return L.create_material_expression(m,cls)
    def rgb(c):
        e=node(u.MaterialExpressionConstant3Vector);e.set_editor_property('constant',u.LinearColor(*c,1));return e
    stone=rgb((.38,.40,.32));moss=rgb((.10,.17,.035));normal=node(u.MaterialExpressionVertexNormalWS);mask=node(u.MaterialExpressionComponentMask)
    for k,v in [('r',False),('g',False),('b',True),('a',False)]:mask.set_editor_property(k,v)
    sub=node(u.MaterialExpressionSubtract);sub.set_editor_property('const_b',.65)
    mul=node(u.MaterialExpressionMultiply);mul.set_editor_property('const_b',4.)
    sat=node(u.MaterialExpressionSaturate);lerp=node(u.MaterialExpressionLinearInterpolate)
    for a,b,p in [(normal,mask,''),(mask,sub,'A'),(sub,mul,'A'),(mul,sat,''),(stone,lerp,'A'),(moss,lerp,'B'),(sat,lerp,'Alpha')]:assert L.connect_material_expressions(a,'',b,p),(a,b,p)
    assert L.connect_material_property(lerp,'',u.MaterialProperty.MP_BASE_COLOR)
    rough=node(u.MaterialExpressionConstant);rough.set_editor_property('r',.9);L.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
    L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
    (root/'terrain11_material_fix.json').write_text(json.dumps({'status':'saved','all_connections_valid':True}))
except Exception:(root/'terrain11_material_fix.json').write_text(json.dumps({'status':'error','error':traceback.format_exc()}))
finally:u.SystemLibrary.execute_console_command(None,'QUIT_EDITOR')
