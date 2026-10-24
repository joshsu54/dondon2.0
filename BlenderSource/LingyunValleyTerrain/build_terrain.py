"""Versioned, editable valley terrain study using the user's actual exported settlement.
Blender 5.2, metres, front -Y, north +Y. Never edits the live Unreal level.
Run: blender --background --python <this script>
"""
import bpy,bmesh,math,random,json,re,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.noise import noise_vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Models/LingyunValleyTerrain/v001'
VIEWS=ROOT/'ArtLibrary/Turnarounds/LingyunValleyTerrain_v001'
VIEWS.mkdir(parents=True,exist_ok=True)
BLEND=OUT/'LingyunValleyTerrain_v001.blend'
assert not BLEND.exists(),'Version already exists; use another version or the render-only script.'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Source/SettlementContext.blend'))
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
rng=random.Random(231026)

def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
context=collection('00_ExistingSettlement_UE10')
terrain=collection('10_ContinuousTerrain')
peaks=collection('20_KarstPeaks')
dressing=collection('30_GroundCoverAndFoothills')
studio=collection('90_CamerasAndLighting')
for o in list(scene.objects):
    for c in list(o.users_collection):c.objects.unlink(o)
    context.objects.link(o)
def move(o,c):
    for old in list(o.users_collection):old.objects.unlink(o)
    c.objects.link(o)
def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color[:3],1)
    p.inputs['Roughness'].default_value=.85;m.diffuse_color=(*color[:3],1);return m
colors={}
for path in ['town_palette.json','expansion04_palette.json','expansion06_palette.json','wild08_palette.json']:
    data=json.loads((ROOT/'Unreal'/path).read_text(encoding='utf-8'))
    for name,entry in data.get('materials',{}).items():
        color=entry.get('base_color_linear',entry.get('color'))
        if color:colors[re.sub(r'[^A-Za-z0-9_]+','_',name)]=color
def fallback(name):
    n=name.lower()
    if any(s in n for s in ['tile','celadon','jade']):return (.10,.28,.25,1)
    if any(s in n for s in ['leaf','grass','moss','pine_pad','needle','bamboo_culm']):return (.15,.24,.08,1)
    if any(s in n for s in ['wood','timber','bark','chestnut','bamboo']):return (.30,.16,.065,1)
    if any(s in n for s in ['paper','plaster','ivory']):return (.74,.68,.51,1)
    if any(s in n for s in ['water']):return (.12,.35,.32,1)
    return (.40,.43,.39,1)
for m in list(bpy.data.materials):
    name=re.sub(r'\.\d+$','',m.name).removeprefix('M_')
    col=colors.get(name,fallback(name))
    m.use_nodes=True;m.node_tree.nodes.clear()
    p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=(*col[:3],1)
    p.inputs['Roughness'].default_value=.78
    output=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],output.inputs['Surface'])
    m.diffuse_color=(*col[:3],1)
stone=material('Terrain_PaleWeatheredLimestone',(.46,.47,.39))
darkstone=material('Terrain_ShadowLimestone',(.32,.35,.30))
earth=material('Terrain_CutEarth',(.25,.19,.11))
jade=material('Terrain_BlueGreenRoof',(.09,.25,.23))
grassmat=material('Terrain_Meadow',(.23,.31,.10))
foliage=material('Terrain_GroundGrass',(.17,.28,.055))
flower=material('Terrain_TinyIvoryFlowers',(.86,.78,.49))

def noise_shader(mat,scale,amount):
    tree=mat.node_tree;p=tree.nodes.get('Principled BSDF')
    tex=tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale
    tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.7
    coords=tree.nodes.new('ShaderNodeTexCoord');tree.links.new(coords.outputs['Generated'],tex.inputs['Vector'])
    bump=tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.45;bump.inputs['Distance'].default_value=amount
    tree.links.new(tex.outputs['Fac'],bump.inputs['Height']);tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return tex
noise_shader(stone,32,.18)
tex=noise_shader(grassmat,55,.08)
tree=grassmat.node_tree;p=tree.nodes.get('Principled BSDF')
ramp=tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[0].color=(.15,.20,.055,1)
ramp.color_ramp.elements[1].position=.76;ramp.color_ramp.elements[1].color=(.40,.38,.20,1)
mid=ramp.color_ramp.elements.new(.5);mid.color=(.27,.33,.115,1)
tree.links.new(tex.outputs['Fac'],ramp.inputs[0]);tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
for o in context.objects:
    if o.name=='DormRoof':o.data.materials.clear();o.data.materials.append(jade)
    if o.name.startswith(('SectShiDi_','SectApplicant','SectMaster_')):
        o.hide_render=True # no blockout people in modeling references

def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def trail(y):
    keys=[(32,1.06),(48.8,1.06),(54.0,3.46),(59.6,3.46),(64.8,5.86),(77,5.86),(90,3.2)]
    if y<32:return -.2
    for (a,za),(b,zb) in zip(keys,keys[1:]):
        if a<=y<=b:return za+(zb-za)*(y-a)/(b-a)
    return 3.2
def height(x,y):
    n=noise_vector(Vector((x*.08,y*.08,.7))).x
    z=.35+1.1*n+1.8*math.sin(x*.055+1)*math.sin(y*.035)
    # Flat construction pads and existing streets remain exactly where exported.
    town_mask=(1-smooth(27,37,abs(x)))*(1-smooth(28,38,abs(y-10)))
    camp_mask=(1-smooth(19,30,abs(x)))*(1-smooth(21,31,abs(y+40)))
    mask=max(town_mask,camp_mask)
    z=z*(1-mask)+(-.20)*mask
    if y>31:
        w=(1-smooth(5,19,abs(x)))*smooth(31,34,y)*(1-smooth(78,90,y))
        z=z*(1-w)+trail(y)*w
    # Soil shoulders lead into the rocks rather than vertical cube foundations.
    for px,py,r,h in [(-44,63,20,7),(-22,98,23,9),(28,97,25,10),(51,56,18,6),(-53,3,15,4)]:
        d=math.hypot(x-px,y-py);z+=h*math.exp(-2*(d/r)**2)*(1-mask)
    boundary=(abs(x)/70)**4+(abs((y-15)/100))**4
    z-=smooth(.80,1.0,boundary)*3.8
    return z

verts=[];faces=[];indices={}
NX,NY=225,321
for j in range(NY):
    y=-85+200*j/(NY-1)
    for i in range(NX):
        x=-70+140*i/(NX-1)
        if (abs(x)/70)**4+(abs((y-15)/100))**4>1:continue
        indices[i,j]=len(verts);verts.append((x,y,height(x,y)))
for j in range(NY-1):
    for i in range(NX-1):
        keys=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
        if all(k in indices for k in keys):faces.append(tuple(indices[k] for k in keys))
# Close the terrain boundary down to an earth section for a watertight editable mesh.
edges={}
for f in faces:
    for a,b in zip(f,f[1:]+f[:1]):
        key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
boundary=[edge for edge,n in edges.items() if n==1]
bottom={}
for a,b in boundary:
    for v in (a,b):
        if v not in bottom:bottom[v]=len(verts);verts.append((verts[v][0],verts[v][1],-8))
    faces.append((a,b,bottom[b],bottom[a]))
# A center fan closes the base and keeps FBX triangulation unambiguous.
center=len(verts);verts.append((0,15,-8))
for a,b in boundary:faces.append((bottom[b],bottom[a],center))
mesh=bpy.data.meshes.new('ContinuousValleyTerrainMesh');mesh.from_pydata(verts,[],faces);mesh.update()
ground=bpy.data.objects.new('Lingyun_ContinuousTerrain',mesh);terrain.objects.link(ground)
ground.data.materials.append(grassmat);ground.data.materials.append(earth)
for polygon in mesh.polygons:
    polygon.use_smooth=True
    if polygon.center.z< -4:polygon.material_index=1
ground['units']='metres';ground['protected_areas']='existing settlement pads, camp pads, north trail'

rock_meshes={}
def rock(name,loc,scale,mat=stone,coll=dressing):
    if mat.name not in rock_meshes:
        data=bpy.data.meshes.new('LinkedRock_'+mat.name);bm=bmesh.new()
        bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1);bm.to_mesh(data);bm.free()
        data.materials.append(mat);rock_meshes[mat.name]=data
    o=bpy.data.objects.new(name,rock_meshes[mat.name]);coll.objects.link(o)
    o.location=loc;o.scale=scale;o.rotation_euler=(rng.uniform(-.3,.3),rng.uniform(-.3,.3),rng.random()*math.tau)
    return o
for idx,(px,py,r,h) in enumerate([(-44,63,12,42),(-22,98,13,52),(28,97,14,62),(51,56,9,35),(-53,3,8,25)]):
    vs=[];fs=[];segments=48;levels=25;base=height(px,py)-2
    columns=[rng.uniform(.87,1.13) for _ in range(segments)]
    for j in range(levels):
        t=j/(levels-1);radius=r*(1-.72*t**.8)
        for i in range(segments):
            angle=math.tau*i/segments
            flute=columns[i]*(1+.035*math.sin(t*19+i*.6))
            rr=radius*flute
            z=base+h*t+(.3*math.sin(angle*5+idx) if j not in (0,levels-1) else 0)
            vs.append((px+rr*math.cos(angle)+2.1*t*t,py+rr*math.sin(angle),z))
    for j in range(levels-1):
        for i in range(segments):
            n=(i+1)%segments;fs.append((j*segments+i,j*segments+n,(j+1)*segments+n,(j+1)*segments+i))
    fs.append(tuple(reversed(range(segments))));fs.append(tuple((levels-1)*segments+i for i in range(segments)))
    data=bpy.data.meshes.new('KarstFlutedMesh_%d'%idx);data.from_pydata(vs,[],fs);data.update()
    o=bpy.data.objects.new('KarstPeak_%02d'%idx,data);peaks.objects.link(o)
    for mat in [stone,darkstone]:data.materials.append(mat)
    for polygon in data.polygons:polygon.material_index=1 if rng.random()<.12 else 0
    for k in range(18):
        a=rng.random()*math.tau;d=r*rng.uniform(.7,1.5);x=px+math.cos(a)*d;y=py+math.sin(a)*d
        rock('Foothill_%d_%d'%(idx,k),(x,y,height(x,y)),(rng.uniform(1.5,3.5),rng.uniform(1.5,3.5),rng.uniform(2,5)))
    # Small grassy summit and sparse pines keep peak silhouettes readable.
    rock('PeakMoss_%d'%idx,(px+2,py,base+h+.03),(r*.27,r*.26,.45),grassmat,peaks)

pine=next((o for o in context.objects if o.name=='Wild08_CommonPine_00'),None)
shrub=next((o for o in context.objects if o.name.startswith('Wild08_WildShrub')),None)
def protected(x,y):
    if abs(x)<3.2 and -65<y<78:return True
    if abs(x)<33 and -15<y<34:return True
    if abs(x)<20 and -64<y< -15:return True
    return False
def linked(source,name,x,y,z,s):
    o=source.copy();o.data=source.data;o.name=name;dressing.objects.link(o)
    o.location=(x,y,z);o.scale=tuple(v*s for v in source.scale);o.rotation_euler.z=rng.random()*math.tau
    return o
for i in range(100):
    x=rng.uniform(-60,60);y=rng.uniform(-74,100)
    if protected(x,y) or height(x,y)>7:continue
    if pine:linked(pine,'TerrainPine_%03d'%i,x,y,height(x,y)-.05,rng.uniform(.65,1.2))
for i in range(300):
    x=rng.uniform(-64,64);y=rng.uniform(-78,106)
    if protected(x,y):continue
    if i%3==0 and shrub:linked(shrub,'TerrainShrub_%03d'%i,x,y,height(x,y),rng.uniform(.8,1.4))
    else:rock('TerrainScree_%03d'%i,(x,y,height(x,y)),(rng.uniform(.35,1.1),rng.uniform(.3,.9),rng.uniform(.25,.7)))
# Grass clumps: one linked mesh, separate from traversable ground and not inside paths/buildings.
gv=[];gf=[]
for i in range(12):
    a=rng.random()*math.tau;x=rng.uniform(-.3,.3);y=rng.uniform(-.3,.3);w=.07;h=rng.uniform(.25,.65)
    n=len(gv);gv.extend([(x-w,y,0),(x+w,y,0),(x+.14*math.cos(a),y+.14*math.sin(a),h)])
    gf.append((n,n+1,n+2))
gd=bpy.data.meshes.new('LinkedGrassClump');gd.from_pydata(gv,[],gf);gd.materials.append(foliage)
for i in range(1500):
    x=rng.uniform(-64,64);y=rng.uniform(-78,106)
    if protected(x,y):continue
    o=bpy.data.objects.new('GroundGrass_%04d'%i,gd);dressing.objects.link(o);o.location=(x,y,height(x,y)+.015)
    o.rotation_euler.z=rng.random()*math.tau;o.scale=(rng.uniform(.7,1.5),)*3

print('GEOMETRY_READY',len(scene.objects),flush=True)
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('TerrainReferenceWorld');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.78,.82,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.view_settings.view_transform='AgX'
def light(kind,name,location,energy,size=0):
    data=bpy.data.lights.new(name,kind);data.energy=energy
    if kind=='AREA':data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);studio.objects.link(o);o.location=location
    o.rotation_euler=(Vector((0,20,0))-o.location).to_track_quat('-Z','Y').to_euler();return o
sun=light('SUN','SoftMorningSun',(-60,-80,120),2.2);sun.data.angle=math.radians(12)
light('AREA','SkyFill',(30,-20,100),70000,100)
camera_data=bpy.data.cameras.new('ReferenceCamera');camera=bpy.data.objects.new('ReferenceCamera',camera_data);studio.objects.link(camera);scene.camera=camera
camera.data.type='ORTHO';camera.data.clip_end=2000
view_defs=[('01_front',0,25),('02_right',90,25),('03_rear',180,25),('04_left',270,25),
           ('05_front_right',45,35),('06_rear_right',135,35),('07_rear_left',225,35),('08_front_left',315,35),
           ('09_top',0,90),('10_high_front',0,65)]
points=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' and not o.hide_render for v in o.bound_box]
lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
center=(lo+hi)*.5
manifest={'asset':'LingyunValleyTerrain_v001','units':'metres','north':'+Y','front':'-Y','seed':231026,
          'bounds_m':[list(lo),list(hi)],'terrain_vertices':len(mesh.vertices),'terrain_faces':len(mesh.polygons),
          'source_context':'Source/Settlement10.fbx','source_context_is_exported_from_UE':True,
          'not_imported_into_live_game':True,'views':[]}
for name,az,el in view_defs:
    a=math.radians(az);e=math.radians(el)
    direction=Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
    camera.location=center+direction*400;camera.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    inverse=camera.matrix_world.inverted();pp=[inverse@p for p in points]
    minx,maxx=min(p.x for p in pp),max(p.x for p in pp);miny,maxy=min(p.y for p in pp),max(p.y for p in pp)
    camera.data.ortho_scale=max(maxx-minx,maxy-miny)*1.12
    camera.location+=camera.matrix_world.to_quaternion()@Vector(((minx+maxx)/2,(miny+maxy)/2,0))
    scene.render.filepath=str(VIEWS/(name+'.png'))
    if name=='01_front':bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.render.render(write_still=True)
    manifest['views'].append({'file':name+'.png','azimuth_deg':az,'elevation_deg':el,'projection':'orthographic','camera_m':list(camera.location)})
    (VIEWS/'views.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('TERRAIN_VIEW_DONE',name,flush=True)
# Export only newly modeled terrain/rock meshes; source buildings stay separate and editable in the blend.
bpy.ops.object.select_all(action='DESELECT')
for coll in (terrain,peaks,dressing):
    for o in coll.objects:
        if o.type=='MESH':o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'LingyunValleyTerrain_v001.fbx'),use_selection=True,object_types={'MESH'},
                         apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
(OUT/'model_info.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('TERRAIN_COMPLETE',str(BLEND),flush=True)
