"""Standalone sublevel with WildVegetation13 placed around the TownLayout_07 town.
Never saves or edits 07: it is loaded read-only to collect obstacle bounds, then a new level is created.
Runs in a full editor or commandlet:  UnrealEditor-Cmd <uproject> -run=pythonscript -script=<this>
Because the C++ quest module could not be compiled on Windows (VS 2019 only), this was run in a temporary
project copy without the module; the sublevel holds no quest actors, so nothing depends on it.
Writes Unreal/wild08_sublevel.json beside the uproject's parent (override with env WILD08_REPORT).
"""
import unreal as u
import json,os,re,hashlib,traceback
from pathlib import Path
REPO=Path(os.environ.get('WILD08_REPO',r'D:\dondon2.0-main\dondon2.0-main'))
REPORT=Path(os.environ.get('WILD08_REPORT',str(REPO/'Unreal'/'wild08_sublevel.json')))
SUB='/Game/Maps/Sublevels/TownWild08_Sublevel';BASE='/Game/Maps/TownLayout_07'
MESH_DIR='/Game/Art/WildVegetation08/Meshes';MAT_DIR='/Game/Art/WildVegetation08/Materials'
GROUND_Z=-15.0  # ValleyGround top surface
COLLISION={'CommonPine':True,'MossBoulderSet':True,'BambooClump':False,'WildShrub':False,'ScreePile':False}
# (asset, x, y, yaw, scale) in cm. South meadow keeps the entrance corridor clear; side strips sit
# between the town fences and the ridge feet (ridges have no collision, so their boxes are avoided).
PLACEMENTS=[('CommonPine',-1800,2700,20,1.0),('CommonPine',1900,3100,-35,.95),('CommonPine',-2500,4600,70,1.1),('CommonPine',2900,1900,140,.9),('CommonPine',-900,5600,0,1.05),
 ('BambooClump',3100,-700,0,1.0),('BambooClump',3200,-1950,60,.9),('BambooClump',3000,700,110,.85),('BambooClump',-2900,-1500,30,.7),
 ('WildShrub',-1200,1900,0,1.0),('WildShrub',1300,1800,40,1.0),('WildShrub',-2300,2300,80,.9),('WildShrub',2500,2700,120,1.1),('WildShrub',800,3700,200,.9),('WildShrub',-900,4100,250,1.0),('WildShrub',3350,-1500,10,.9),('WildShrub',-2900,400,300,.8),
 ('MossBoulderSet',2650,4100,25,1.0),('MossBoulderSet',-2450,3500,-40,.9),('MossBoulderSet',-2950,-2200,80,.8),('MossBoulderSet',-1600,5200,150,.7),
 ('ScreePile',3450,1300,0,.9),('ScreePile',-2950,-2700,30,.8),('ScreePile',400,4700,90,1.0)]
SCENERY=('ValleyGround','ValleyRidge_','DistantPeak_','DriftingClouds_')
report={'status':'starting','sublevel':SUB,'base_map_read_only':BASE,'placements':[]}
def write(status,**kw):report.update(status=status,**kw);REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False))
def clean(s):return re.sub(r'[^A-Za-z0-9_]','_',str(s))
def box(a):c,e=a.get_actor_bounds(False);return [c.x-e.x,c.y-e.y,c.z-e.z,c.x+e.x,c.y+e.y,c.z+e.z]
def hit2d(a,b,m=0):return a[0]-m<b[3] and b[0]-m<a[3] and a[1]-m<b[4] and b[1]-m<a[4]
def make_material(tools,name,d):
    an='M_'+clean(name);mat=u.load_asset(MAT_DIR+'/'+an)
    if mat:return mat
    mat=tools.create_asset(an,MAT_DIR,u.Material,u.MaterialFactoryNew());L=u.MaterialEditingLibrary
    def const3(rgb,x,y):
        e=L.create_material_expression(mat,u.MaterialExpressionConstant3Vector,x,y);e.set_editor_property('constant',u.LinearColor(*rgb,1));return e
    col=const3(d['color'],-400,0)
    if name=='Jade_Gray_Rock_Moss_Cap':
        # Upward world normals blend to moss, matching the Blender shader mask.
        moss=const3((.04,.065,.02),-400,120);n=L.create_material_expression(mat,u.MaterialExpressionVertexNormalWS,-700,260)
        mask=L.create_material_expression(mat,u.MaterialExpressionComponentMask,-560,260)
        for k,v in [('r',False),('g',False),('b',True),('a',False)]:mask.set_editor_property(k,v)
        sub=L.create_material_expression(mat,u.MaterialExpressionSubtract,-430,260);sub.set_editor_property('const_b',.55)
        mul=L.create_material_expression(mat,u.MaterialExpressionMultiply,-320,260);mul.set_editor_property('const_b',4.0)
        sat=L.create_material_expression(mat,u.MaterialExpressionSaturate,-220,260)
        lerp=L.create_material_expression(mat,u.MaterialExpressionLinearInterpolate,-150,60)
        L.connect_material_expressions(n,'',mask,'');L.connect_material_expressions(mask,'',sub,'A');L.connect_material_expressions(sub,'',mul,'A')
        L.connect_material_expressions(mul,'',sat,'');L.connect_material_expressions(col,'',lerp,'A');L.connect_material_expressions(moss,'',lerp,'B');L.connect_material_expressions(sat,'',lerp,'Alpha')
        L.connect_material_property(lerp,'',u.MaterialProperty.MP_BASE_COLOR)
    else:L.connect_material_property(col,'',u.MaterialProperty.MP_BASE_COLOR)
    for y,value,prop in [(300,d['roughness'],u.MaterialProperty.MP_ROUGHNESS),(420,d['metallic'],u.MaterialProperty.MP_METALLIC)]:
        e=L.create_material_expression(mat,u.MaterialExpressionConstant,-400,y);e.set_editor_property('r',value);L.connect_material_property(e,'',prop)
    if d.get('two_sided'):mat.set_editor_property('two_sided',True)
    L.recompile_material(mat);u.EditorAssetLibrary.save_loaded_asset(mat);return mat

def run():
    actors=u.get_editor_subsystem(u.EditorActorSubsystem);les=u.get_editor_subsystem(u.LevelEditorSubsystem)
    assert not u.EditorAssetLibrary.does_asset_exist(SUB),'Never overwrite an existing sublevel'
    palette=json.loads((REPO/'Unreal'/'wild08_palette.json').read_text())
    for aid,src in palette['sources'].items():
        fbx=REPO/'Models'/aid/'v001'/f'{aid}_v001.fbx';assert hashlib.sha256(fbx.read_bytes()).hexdigest()==src['fbx_sha256'],aid
    # 1. Obstacles from 07, read only.
    u.EditorLoadingAndSavingUtils.load_map(BASE);obstacles=[];entrance=None
    for a in actors.get_all_level_actors():
        label=a.get_actor_label()
        if label.startswith(SCENERY[1:]):obstacles.append((label,box(a)))  # ridge boxes: avoid the mountain feet
        elif label.startswith(SCENERY[0]) or a.get_class().get_name() in ('DirectionalLight','SkyLight','SkyAtmosphere','PostProcessVolume','ExponentialHeightFog','PointLight'):continue
        elif a.get_class().get_name()=='PlayerStart':l=a.get_actor_location();entrance=[l.x,l.y];obstacles.append((label,[l.x-150,l.y-150,0,l.x+150,l.y+150,300]))
        else:obstacles.append((label,box(a)))
    obstacles.append(('EntranceCorridor',[-500,850,-50,500,4000,500]))
    report['obstacles_from_07']=len(obstacles);report['entrance']=entrance
    # 2. Assets (shared /Game paths; created only if missing).
    tools=u.AssetToolsHelpers.get_asset_tools();mats={clean(n):make_material(tools,n,d) for n,d in palette['materials'].items()}
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0');meshes={}
    for aid in palette['sources']:
        write('importing',current=aid);path=MESH_DIR+'/'+aid;mesh=u.load_asset(path)
        if not mesh:
            task=u.AssetImportTask()
            for k,v in [('filename',str(REPO/'Models'/aid/'v001'/f'{aid}_v001.fbx')),('destination_path',MESH_DIR),('destination_name',aid),('automated',True),('save',True)]:task.set_editor_property(k,v)
            opt=u.FbxImportUI()
            for k,v in [('import_mesh',True),('import_as_skeletal',False),('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH),('automated_import_should_detect_type',False),('import_materials',False),('import_textures',False)]:opt.set_editor_property(k,v)
            data=opt.get_editor_property('static_mesh_import_data')
            for k,v in [('combine_meshes',True),('auto_generate_collision',False),('transform_vertex_to_absolute',True),('convert_scene',True),('convert_scene_unit',True),('generate_lightmap_u_vs',False),('build_nanite',False)]:data.set_editor_property(k,v)
            task.set_editor_property('options',opt);task.set_editor_property('factory',u.FbxFactory());tools.import_asset_tasks([task]);mesh=u.load_asset(path)
        assert isinstance(mesh,u.StaticMesh),aid
        unmatched=[]
        for i,slot in enumerate(mesh.get_editor_property('static_materials')):
            key=clean(slot.get_editor_property('imported_material_slot_name'))
            if key not in mats:key=clean(slot.get_editor_property('material_slot_name'))
            if key not in mats:unmatched.append(key)
            else:mesh.set_material(i,mats[key])
        assert not unmatched,(aid,unmatched)
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        u.EditorAssetLibrary.save_loaded_asset(mesh);meshes[aid]=mesh
        b=mesh.get_bounding_box();dims=[getattr(b.max,k)-getattr(b.min,k) for k in 'xyz']
        bm=palette['sources'][aid]['bounds_m'];expected=sorted([(bm[1][i]-bm[0][i])*100 for i in (0,1)])+[(bm[1][2]-bm[0][2])*100]
        assert all(abs(x-y)<max(2,y*.02) for x,y in zip(sorted(dims[:2])+[dims[2]],expected)),(aid,dims,expected)
        report.setdefault('meshes',{})[aid]={'asset':path,'dimensions_cm':dims,'material_slots':len(mesh.get_editor_property('static_materials')),'collision':COLLISION[aid]}
    # 3. New level holding only the placements.
    assert les.new_level(SUB),'new_level failed'
    state['created']=True  # new_level writes the package immediately; a failed run removes only this one
    placed=[]
    for i,(aid,x,y,yaw,s) in enumerate(PLACEMENTS):
        a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,GROUND_Z));label='Wild08_%s_%02d'%(aid,i)
        a.set_actor_label(label);a.set_folder_path('WildVegetation08');a.static_mesh_component.set_static_mesh(meshes[aid])
        a.set_actor_scale3d(u.Vector(s,s,s));a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False);a.set_actor_enable_collision(COLLISION[aid])
        a.set_editor_property('tags',[u.Name('WildVegetation08'),u.Name(aid)])
        b=box(a);clash=[n for n,o in obstacles if hit2d(b,o,40)]+[p['label'] for p in placed if hit2d(b,p['box'],20)]
        assert not clash,(label,clash[:5])
        assert abs(b[2]-GROUND_Z)<1,(label,'not grounded',b[2])
        placed.append({'label':label,'asset':aid,'location_cm':[x,y,GROUND_Z],'yaw':yaw,'scale':s,'box':b,'collision':COLLISION[aid]})
    assert les.save_current_level(),'save failed'
    # 4. Reload from disk and compare.
    u.EditorLoadingAndSavingUtils.load_map(SUB)
    items={a.get_actor_label():a for a in actors.get_all_level_actors() if a.actor_has_tag('WildVegetation08')}
    checks={'actor_count':len(items)==len(PLACEMENTS),'per_asset_counts':{aid:sum(1 for p in PLACEMENTS if p[0]==aid) for aid in meshes}}
    for p in placed:
        a=items.get(p['label']);assert a,p['label']
        assert (a.get_actor_location()-u.Vector(*p['location_cm'])).length()<.1 and a.static_mesh_component.static_mesh==meshes[p['asset']]
    checks['positions_meshes_after_reload']=True;checks['no_overlap_with_07_or_each_other']=True;checks['grounded_at_valley_floor_cm']=GROUND_Z
    umap=Path(u.Paths.project_content_dir())/'Maps'/'Sublevels'/'TownWild08_Sublevel.umap'
    write('saved_reloaded',placements=placed,checks=checks,sublevel_sha256=hashlib.sha256(umap.read_bytes()).hexdigest(),
          limits=['Standalone sublevel; not yet streamed into or merged with a saved TownLayout_08','07 was opened read-only and never saved','No PIE traversal test (quest module not compiled on Windows)','Constant-colour materials; foliage is static, no wind; no LOD'])
    print('WILD08_DONE',len(placed))
state={'created':False}
try:run()
except Exception:
    write('error',error=traceback.format_exc())
    if state['created']:
        u.EditorLoadingAndSavingUtils.load_map(BASE);u.EditorAssetLibrary.delete_asset(SUB)
    raise
