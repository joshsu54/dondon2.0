"""Generate an editable first-pass pine in Blender. Run in a fresh background process.

blender --background --factory-startup --python build_welcoming_pine.py
Output is versioned; existing deliveries are never overwritten.
"""
import bpy
import json
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'Models' / 'WelcomingPine'
BASE.mkdir(parents=True, exist_ok=True)
version = 1
while (BASE / f'v{version:03d}').exists():
    version += 1
OUT = BASE / f'v{version:03d}'
OUT.mkdir()
RNG = random.Random(1712)

# A new scene isolates generation from any other open project.
scene = bpy.data.scenes.new('WelcomingPine_Studio')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1

def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

wood = collection('01_Trunk_Branches_Roots')
foliage = collection('02_Pine_Needle_Clusters')
rocks = collection('03_Root_Rocks')
studio = collection('90_Studio_Not_For_Export')
refs = collection('91_Reference_Not_For_Export')
refs.hide_render = True
refs.hide_viewport = True
construction = collection('92_Branch_Construction_Hidden')
construction.hide_render = True
construction.hide_viewport = True

def move_to(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)

def mat(name, color, roughness=0.8):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return m

def textured(name, dark, light, scale, bump_strength):
    m = mat(name, tuple((a+b)/2 for a,b in zip(dark, light)))
    n, l = m.node_tree.nodes, m.node_tree.links
    bsdf = n.get('Principled BSDF')
    tex = n.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 4
    tex.inputs['Roughness'].default_value = 0.72
    coord = n.new('ShaderNodeTexCoord')
    mapping = n.new('ShaderNodeVectorMath')
    mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (2.0, 2.0, 0.6) if 'Bark' in name else (1, 1, 1)
    l.new(coord.outputs['Object'], mapping.inputs[0])
    l.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (*light, 1)
    l.new(tex.outputs['Fac'], ramp.inputs[0])
    l.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bump = n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = bump_strength
    bump.inputs['Distance'].default_value = 0.075
    l.new(tex.outputs['Fac'], bump.inputs['Height'])
    l.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m

bark = textured('Pine_Bark', (0.032, 0.022, 0.014), (0.20, 0.145, 0.085), 9, 0.75)
# Long narrow fissures sit below the mottled bark surface.
bn, bl = bark.node_tree.nodes, bark.node_tree.links
fissures = bn.new('ShaderNodeTexVoronoi')
fissures.feature = 'DISTANCE_TO_EDGE'
fissures.inputs['Scale'].default_value = 6
bl.new(next(n for n in bn if n.type == 'VECT_MATH').outputs['Vector'], fissures.inputs['Vector'])
crack_ramp = bn.new('ShaderNodeValToRGB')
crack_ramp.color_ramp.elements[0].position = .015
crack_ramp.color_ramp.elements[0].color = (.015, .011, .008, 1)
crack_ramp.color_ramp.elements[1].position = .11
crack_ramp.color_ramp.elements[1].color = (.24, .19, .13, 1)
bl.new(fissures.outputs['Distance'], crack_ramp.inputs[0])
bl.new(crack_ramp.outputs['Color'], bn.get('Principled BSDF').inputs['Base Color'])
coarse_bump = bn.new('ShaderNodeBump')
coarse_bump.inputs['Strength'].default_value = .6
coarse_bump.inputs['Distance'].default_value = .10
bl.new(fissures.outputs['Distance'], coarse_bump.inputs['Height'])
fine_bump = next(n for n in bn if n.type == 'BUMP' and n != coarse_bump)
bl.new(fine_bump.outputs['Normal'], coarse_bump.inputs['Normal'])
bl.new(coarse_bump.outputs['Normal'], bn.get('Principled BSDF').inputs['Normal'])
stone = textured('BlueGrey_Rock', (0.085, 0.105, 0.12), (0.30, 0.34, 0.35), 3.3, 0.5)
needle_mats = [
    mat('Needles_Deep_Jade', (0.015, 0.040, 0.018)),
    mat('Needles_Pine_Green', (0.036, 0.092, 0.036)),
    mat('Needles_Sunlit_Tips', (0.09, 0.15, 0.045)),
]
moss_mat = textured('Moss', (0.032, 0.060, 0.018), (0.11, 0.17, 0.035), 20, 0.35)

def mesh_object(name, verts, faces, material, coll, smooth=True):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    if material:
        mesh.materials.append(material)
    for p in mesh.polygons:
        p.use_smooth = smooth
    return obj

def catmull(points, steps=6):
    result = []
    p = [Vector(x[:3]) for x in points]
    r = [x[3] for x in points]
    for i in range(len(p)-1):
        a, b, c, d = p[max(0,i-1)], p[i], p[i+1], p[min(len(p)-1,i+2)]
        for j in range(steps):
            t = j / steps
            v = .5*((2*b) + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t)
            result.append((v, r[i]*(1-t)+r[i+1]*t))
    result.append((p[-1], r[-1]))
    return result

def tube(name, points, sides=12, steps=6):
    path = catmull(points, steps)
    verts, faces = [], []
    previous_n = None
    for i, (p, r) in enumerate(path):
        tangent = (path[min(i+1,len(path)-1)][0]-path[max(0,i-1)][0]).normalized()
        if previous_n is None:
            helper = Vector((0,1,0)) if abs(tangent.y) < .9 else Vector((1,0,0))
            n = tangent.cross(helper).normalized()
        else:
            n = (previous_n - tangent * previous_n.dot(tangent)).normalized()
        b = tangent.cross(n).normalized()
        previous_n = n
        for j in range(sides):
            a = 2*math.pi*j/sides
            ridge = 1 + .095*math.sin(5*a+i*.12) + .04*math.sin(9*a-i*.19)
            verts.append(tuple(p + (n*math.cos(a)+b*math.sin(a))*r*ridge))
        if i:
            for j in range(sides):
                k = (j+1)%sides
                faces.append(((i-1)*sides+j,(i-1)*sides+k,i*sides+k,i*sides+j))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(path)-1)*sides+j for j in range(sides)))
    return mesh_object(name, verts, faces, bark, wood)

# Deliberately asymmetric silhouette: a compact upright crown and a long welcoming arm.
trunk = [(-2.2,0,.6,.68),(-2.45,.05,1.45,.62),(-2.22,.02,2.35,.52),
         (-1.68,.12,3.15,.46),(-1.65,.12,3.9,.37),(-2.02,.18,4.55,.30),
         (-1.72,.24,5.3,.22),(-1.9,.3,6,.13),(-1.5,.4,6.65,.055)]
tube('Trunk_Main', trunk, 40, 10)
arm = [(-1.85,.1,3.35,.43),(-.95,.10,3.95,.36),(.2,.12,4.15,.30),
       (1.3,.03,3.95,.25),(2.5,.02,4.13,.19),(3.7,.15,4.35,.13),
       (4.75,.3,4.62,.075),(5.55,.42,4.8,.02)]
tube('Branch_Welcoming_Arm', arm, 32, 10)
left = [(-2.3,0,2.3,.30),(-3.1,-.04,2.9,.22),(-3.65,-.08,3.5,.16),
        (-4.45,-.18,3.7,.11),(-5.25,-.1,3.9,.025)]
tube('Branch_Left_Counterweight', left, 16, 7)

# Roots lie over and between the rock group.
for i, (endx,endy,endz) in enumerate([(-4,-.55,.16),(-3.5,1.2,.2),(-1.15,-1.35,.08),
                                    (-.45,.25,.13),(-2.25,1.6,.15),(-3.0,-1.35,.1)]):
    start = Vector((-2.18,0,.95))
    end = Vector((endx,endy,endz))
    mid = start.lerp(end,.48) + Vector((0,0,.1))
    tube('Root_%02d'%i,[(*start,.25),(*mid,.19),(*end,.018)],12,8)

# Crown pads are actual needle geometry, not opaque placeholder spheres.
clusters = [
    ((-1.65,.35,6.55),(1.05,.85,.32),(-1.8,.3,5.8)),
    ((-2.75,.4,5.95),(1.10,.78,.30),(-1.83,.2,5.18)),
    ((-.65,.18,5.75),(1.1,.85,.28),(-1.75,.16,4.7)),
    ((-2.3,-.9,5.20),(.95,.65,.27),(-1.75,.15,4.4)),
    ((-.15,.85,4.9),(1.05,.72,.30),(-.7,.10,4.0)),
    ((1.25,.5,5.15),(1.15,.83,.30),(.6,.1,4.05)),
    ((2.55,.85,5.6),(1.14,.83,.3),(2.1,.05,4.05)),
    ((3.7,.65,5.0),(1.2,.8,.28),(3.3,.1,4.3)),
    ((5.0,.3,4.7),(1.15,.9,.30),(4.4,.25,4.55)),
    ((3.3,-.8,3.95),(1.12,.75,.26),(2.5,.03,4.13)),
    ((1.65,-.85,3.45),(.8,.62,.26),(1.25,.05,3.95)),
    ((-4.8,-.05,3.95),(1.1,.82,.3),(-4.15,-.12,3.65)),
    ((-3.85,.75,4.4),(1.05,.75,.28),(-3.35,-.02,3.2)),
    ((-4.75,-.4,3.25),(.85,.62,.26),(-3.75,-.08,3.5)),
]

def needle_pad(index, center, size):
    c = Vector(center)
    sx,sy,sz = size
    verts, faces, mids = [], [], []
    # Denser foliage with volume, retaining clear gaps between crown tiers.
    for shoot in range(180):
        angle = RNG.uniform(0,math.tau)
        radius = math.sqrt(RNG.random())
        p = c + Vector((math.cos(angle)*sx*radius,math.sin(angle)*sy*radius,
                        RNG.uniform(-.65,.9)*sz + .14*(1-radius)))
        axis = Vector((math.cos(angle)*.7,math.sin(angle)*.7,RNG.uniform(.4,1))).normalized()
        u = axis.cross(Vector((0,0,1))).normalized()
        v = axis.cross(u).normalized()
        for n in range(18):
            theta = math.tau*n/18 + RNG.uniform(-.3,.3)
            d = (axis*.6 + (u*math.cos(theta)+v*math.sin(theta))*.85).normalized()
            length = RNG.uniform(.14,.25)
            width = RNG.uniform(.011,.017)
            base = p + axis*RNG.uniform(0,.09)
            side = d.cross(axis).normalized()*width
            tip = base+d*length
            ridge = base + d*length*.40 + axis*width*.7
            k=len(verts)
            verts.extend([tuple(base-side),tuple(base+side),tuple(ridge),tuple(tip)])
            faces.extend([(k,k+2,k+3),(k+2,k+1,k+3),(k+1,k,k+3)])
            material = RNG.choices([0,1,2],[.35,.50,.15])[0]
            mids.extend([material]*3)
    obj = mesh_object('Needle_Pad_%02d'%index,verts,faces,None,foliage,False)
    for m in needle_mats:
        obj.data.materials.append(m)
    for poly, material in zip(obj.data.polygons,mids):
        poly.material_index=material
    return obj

for i, (center, size, anchor) in enumerate(clusters):
    a,c = Vector(anchor),Vector(center)
    mid=a.lerp(c,.40)+Vector((.16 if i%2 else -.18,-.12,.10))
    elbow=a.lerp(c,.73)+Vector((-.07,.12,.11))
    tube('Branch_Crown_%02d'%i,[(*a,.12),(*mid,.082),(*elbow,.052),(*c,.018)],12,5)
    # Radial twig structure makes gaps within needle pads readable.
    for j in range(5):
        theta=j*math.tau/5+RNG.uniform(-.15,.15)
        end=c+Vector((math.cos(theta)*size[0]*.8,math.sin(theta)*size[1]*.8,-.03))
        tube('Twig_%02d_%02d'%(i,j),[(*c,.027),(*c.lerp(end,.5),.018),(*end,.004)],6,3)
    needle_pad(i,center,size)

# Unite major limbs and roots so overlapping branch collars do not remain visible.
# Preserve the unmerged construction meshes in a hidden collection for editing.
major=[o for o in wood.objects if not o.name.startswith('Twig_')]
for obj in scene.objects:
    obj.select_set(False)
for obj in major:
    backup=obj.copy()
    backup.data=obj.data.copy()
    backup.name='Construction_'+obj.name
    construction.objects.link(backup)
    obj.select_set(True)
bpy.context.view_layer.objects.active=major[0]
bpy.ops.object.join()
united=bpy.context.object
united.name='Trunk_Joined_With_Main_Limbs_And_Roots'
remesh=united.modifiers.new('Unite_Branch_Junctions','REMESH')
remesh.mode='VOXEL'
remesh.voxel_size=.035
remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=united.modifiers.new('Soften_Organic_Junctions','SMOOTH')
smooth.factor=.6
smooth.iterations=3
bpy.ops.object.modifier_apply(modifier=smooth.name)
decimate=united.modifiers.new('Reduce_Uniform_Remesh_Density','DECIMATE')
decimate.ratio=.5
bpy.ops.object.modifier_apply(modifier=decimate.name)
for face in united.data.polygons:
    face.use_smooth=True

for i,(position,scale) in enumerate([
    ((-2.8,.30,.58),(1.18,.92,.92)),
    ((-1.32,.18,.41),(.98,.82,.66)),
    ((-2.05,-.75,.31),(.97,.72,.48)),
    ((-3.45,-.7,.16),(.55,.44,.28)),
    ((-.60,-.15,.12),(.36,.30,.24))]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=position)
    obj=bpy.context.object
    obj.name='Root_Rock_%02d'%i
    move_to(obj,rocks)
    for vertex in obj.data.vertices:
        vertex.co *= RNG.uniform(.85,1.13)
        vertex.co.x*=scale[0]
        vertex.co.y*=scale[1]
        vertex.co.z*=scale[2]
        # Keep support stones on the ground, eliminating floating roots/base.
        vertex.co.z=max(vertex.co.z,-position[2]+.01)
    obj.rotation_euler=(RNG.uniform(-.12,.12),RNG.uniform(-.12,.12),RNG.uniform(-.5,.5))
    obj.data.materials.append(stone)
    bevel=obj.modifiers.new('Slightly_Worn_Edges','BEVEL')
    bevel.width=.035
    bevel.segments=2

for i in range(22):
    angle=RNG.uniform(0,math.tau)
    radius=RNG.uniform(.5,1.3)
    p=(-2.25+math.cos(angle)*radius, math.sin(angle)*radius*.65, .03)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=p)
    obj=bpy.context.object
    obj.name='Moss_Patch_%02d'%i
    obj.scale=(RNG.uniform(.12,.3),RNG.uniform(.1,.24),RNG.uniform(.035,.065))
    move_to(obj,rocks)
    obj.data.materials.append(moss_mat)

# Named asset root keeps export and studio cleanly separated.
asset=bpy.data.objects.new('WelcomingPine_ROOT',None)
wood.objects.link(asset)
for coll in (wood,foliage,rocks):
    for obj in list(coll.objects):
        if obj != asset:
            obj.parent=asset
asset['stage']=f'v{version:03d} first-pass modeled asset; not a final game-ready tree'
asset['reference']='ArtReferences/WelcomingPine/01_welcoming_pine_master.png'

reference=ROOT / asset['reference']
if reference.exists():
    image=bpy.data.images.load(str(reference),check_existing=True)
    image.pack()
    empty=bpy.data.objects.new('REFERENCE_Concept_Toggle_Collection_To_View',None)
    refs.objects.link(empty)
    empty.empty_display_type='IMAGE'
    empty.data=image
    empty.empty_display_size=12
    empty.location=(0,3,3.5)
    empty.rotation_euler=(math.pi/2,0,0)

# Studio stays outside exported selection.
floor_mat=mat('Studio_Ground',(0.235,.245,.255))
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.08))
ground=bpy.context.object
ground.name='Studio_Ground'
move_to(ground,studio)
ground.data.materials.append(floor_mat)

world=bpy.data.worlds.new('Pine_Studio_World')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.34,.37,.42,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.world=world

def aim(obj,point):
    obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

for name,loc,power,size,color in [
    ('Key',(-4,-6,11),1700,7,(1,.9,.76)),
    ('Fill',(6,-2,7),1100,6,(.78,.88,1)),
    ('Rim',(0,5,10),1900,5,(1,.95,.85))]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    data.color=color
    obj=bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location=loc
    aim(obj,(0,0,3))

camdata=bpy.data.cameras.new('Main_Camera')
camera=bpy.data.objects.new('Main_Camera',camdata)
studio.objects.link(camera)
camera.location=(9,-23,10)
aim(camera,(.1,0,3.3))
camdata.type='ORTHO'
camdata.ortho_scale=14.6
scene.camera=camera
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1440
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'

# Provide a useful material viewport immediately upon opening.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.shading.type='MATERIAL'
            space.clip_end=1000
            space.region_3d.view_distance=17
            space.region_3d.view_location=Vector((.1,0,3.3))
            space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
for obj in scene.objects:
    obj.select_set(False)
asset.select_set(True)
bpy.context.view_layer.objects.active=asset

asset_objects=[o for coll in (wood,foliage,rocks) for o in coll.objects if o.type=='MESH']
stats={'blender':bpy.app.version_string,'stage':'first-pass', 'mesh_objects':len(asset_objects),
       'vertices':sum(len(o.data.vertices) for o in asset_objects),
       'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in asset_objects),
       'needle_pads':len(foliage.objects),'seed':1712,
       'limitations':['Major limbs are united; fine twigs remain separate editable meshes.',
                     'Procedural bark/rock shaders are not baked to image textures.',
                     'No UV unwrap, LOD, wind rig or Unity import verification yet.']}

blend=OUT/f'WelcomingPine_v{version:03d}.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
print('SAVED_BLEND',blend,flush=True)

# Export only the actual asset. FBX carries base colors, not procedural shaders.
for obj in scene.objects:
    obj.select_set(False)
for obj in asset_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active=asset_objects[0]
try:
    bpy.ops.export_scene.fbx(filepath=str(OUT/f'WelcomingPine_v{version:03d}.fbx'),use_selection=True,
                            object_types={'MESH'},apply_unit_scale=True,bake_anim=False,
                            axis_forward='-Z',axis_up='Y',mesh_smooth_type='FACE')
    stats['fbx_export']='success; base colors only, no shader baking'
except Exception as exc:
    stats['fbx_export']='failed: '+str(exc)

for obj in scene.objects:
    obj.select_set(False)
asset.select_set(True)
bpy.context.view_layer.objects.active=asset
# Avoid .blend1 backup for this save in a fresh, versioned output directory.
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

for name,loc in [('01_front_right',(9,-23,10)),('02_front',(0,-25,8)),('03_rear',(-9,22,10))]:
    camera.location=loc
    aim(camera,(.1,0,3.3))
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True)

(OUT/'model_info.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
print('MODEL_COMPLETE',json.dumps(stats),flush=True)
