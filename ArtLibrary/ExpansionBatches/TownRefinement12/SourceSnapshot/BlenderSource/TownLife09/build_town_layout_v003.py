"""TownLayout v003: extend the v002 town north with the TownLife09-11 assets.

Step 1 (concept, before any assembly): a blockout of the new north block -
v002 as-is plus coloured footprint boxes for every placement - is rendered
from the ten standard angles in the Codex-like studio style into
ArtReferences/TownLayout_v003_10Views.
Step 2: v002 is opened unchanged, every placement is appended from its own
.blend (01_Editable_Asset collection), the north terrace, retaining wall and
railings are added, the ten concept views are loaded as references, and the
scene is saved/exported to Models/TownLayout/v003 with three previews.

Run: python3 build_town_layout_v003.py [--concept-only]
"""
import bpy  # noqa: I001
import json
import math
import sys
from pathlib import Path
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]
SRC = ROOT / 'Models/TownLayout/v002/TownLayout_v002.blend'
OUT = ROOT / 'Models/TownLayout/v003'
REFS = ROOT / 'ArtReferences/TownLayout_v003_10Views'
Z = 1.12   # terrace top: road tiles (paving at +0.2) meet v002 north street at 1.32 m

# (asset, x, y, z, rotation_z_degrees, note)
PLACEMENTS = [
    ('MountainStonePath', 0, 14.7, Z, 0, 'north street continues from v002 (1.32 m)'),
    ('TownRoadCrossroad', 0, 20.7, Z, 0, 'market crossroads'),
    ('MountainStonePath', 0, 26.7, Z, 0, 'street under the archway'),
    ('TownRoadTJunction', 0, 32.7, Z, 180, 'north T: branch points back south'),
    ('MountainStonePath', -6, 32.7, Z, 90, 'west lane stub'),
    ('MountainStonePath', 6, 32.7, Z, 90, 'east lane stub'),
    ('MountainStonePath', -6, 20.7, Z, 90, 'lane to the inn'),
    ('MountainStonePath', 6, 20.7, Z, 90, 'lane to the well square'),
    ('TownPaifang', 0, 26.7, Z, 0, 'archway over the street'),
    ('TownInn', -16.2, 22.2, Z, 90, 'inn faces east onto the west lane'),
    ('IngredientCrate', -8.3, 17.2, Z, 90, 'delivery at the inn door'),
    ('GrainSacks', -10.6, 13.4, Z, 0, 'inn yard'),
    ('FirewoodStack', -13.6, 13.0, Z, 0, 'inn yard'),
    ('WoodenCrate', -8.6, 13.0, Z, 15, 'inn yard'),
    ('ClayJar', -7.7, 13.1, Z, 0, 'inn yard'),
    ('BambooBasket', -7.6, 14.0, Z, 0, 'inn yard'),
    ('TownWell', 12.0, 20.7, Z, 0, 'well square'),
    ('NoticeBoard', 4.6, 24.4, Z, -45, 'notice board at the crossroads'),
    ('SpawnAltar', -6.5, 27.5, Z, 90, 'waypoint altar beside the archway'),
    ('PondEdge', 11.0, 29.0, Z, 0, 'fenced lotus garden'),
]
# fenced garden 7..15 x 25..33 around the pond
for x in (9, 11, 13):
    PLACEMENTS += [('BambooFence', x, 25, Z, 0, 'garden fence'), ('BambooFence', x, 33, Z, 0, 'garden fence')]
for y in (27, 29, 31):
    PLACEMENTS.append(('BambooFence', 15, y, Z, 90, 'garden fence'))
PLACEMENTS += [('BambooFence', 7, 27, Z, 90, 'garden fence'), ('BambooFence', 7, 31, Z, 90, 'garden fence'),
               ('FenceGate', 7, 29, Z, -90, 'garden gate faces the street'),
               ('BambooFenceCorner', 15, 25, Z, 0, 'garden corner'), ('BambooFenceCorner', 7, 25, Z, -90, 'garden corner'),
               ('BambooFenceCorner', 7, 33, Z, 180, 'garden corner'), ('BambooFenceCorner', 15, 33, Z, 90, 'garden corner')]
# stone balustrade along the terrace edge, leaving the street opening
RAILS = [x for x in range(-23, 22, 2) if abs(x) > 2.5]


def model_path(aid):
    return ROOT / 'Models' / aid / 'v001' / f'{aid}_v001.blend'


def dims(aid):
    return Vector(json.loads((ROOT / 'Models' / aid / 'v001' / 'model_info.json').read_text())['dimensions_m'])


def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def mat(name, rgb, rough=.85):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


def add_box(name, centre, size, material, coll, rz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre, rotation=(0, 0, rz))
    o = bpy.context.object
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    o.data.materials.append(material)
    return o


def terrace(coll):
    grass = mat('TL_Layout_Terrace_Grass', (.16, .22, .10))
    stone = mat('TL_Layout_Retaining_Stone', (.26, .28, .27))
    add_box('North_Terrace_Ground', (-2, 26.2, Z / 2), (48, 29, Z), grass, coll)
    add_box('North_Terrace_Retaining_Wall', (-2, 11.75, Z / 2 + .02), (48, .3, Z + .04), stone, coll)
    add_box('North_Terrace_Wall_Coping', (-2, 11.75, Z + .05), (48.2, .42, .1), stone, coll)


# ------------------------------------------------------------------ concept
CATEGORY_RGB = {'road': (.30, .32, .32), 'building': (.70, .30, .20), 'prop': (.55, .40, .20),
                'fence': (.50, .45, .20), 'water': (.10, .30, .40), 'arch': (.65, .10, .06)}


def category(aid):
    if aid.startswith(('TownRoad', 'Mountain')):
        return 'road'
    if aid in ('TownInn', 'SpawnAltar'):
        return 'building'
    if aid.startswith(('Bamboo', 'Fence', 'Stone')):
        return 'fence'
    if aid == 'PondEdge':
        return 'water'
    if aid == 'TownPaifang':
        return 'arch'
    return 'prop'


def concept():
    import concept_render09 as CR
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    scene = bpy.context.scene
    for c in list(bpy.data.collections):
        if c.name.startswith(('80_', '90_')):
            for o in list(c.objects):
                bpy.data.objects.remove(o)
    blk = new_coll('Concept_Blockout')
    terrace(blk)
    mats = {k: mat('TL_Concept_' + k, v) for k, v in CATEGORY_RGB.items()}
    for aid, x, y, z, rz, _ in PLACEMENTS:
        d = dims(aid)
        h = d.z if category(aid) != 'road' else .22
        add_box('Blockout_' + aid, (x, y, z + h / 2), (d.x, d.y, h), mats[category(aid)], blk, math.radians(rz))
    for x in RAILS:
        add_box('Blockout_StoneRailing', (x, 11.75, Z + .6), (2, .3, 1.2), mats['fence'], blk)
    objs = [o for o in scene.objects if o.type == 'MESH' and not o.name.startswith('Terrain_Display')]
    lo = Vector((-26, -14, 0))
    hi = Vector((22, 41, 7))
    centre, R = (lo + hi) / 2, (hi - lo).length / 2
    for name, direction, power in [('Key', (-.9, -1.2, 1.6), 650), ('Fill', (1.3, -.6, .8), 220), ('Top', (0, .4, 2.2), 260)]:
        dl = bpy.data.lights.new(name, 'AREA')
        dl.energy, dl.size = power * R * R / 4, R * 1.6
        o = bpy.data.objects.new(name, dl)
        scene.collection.objects.link(o)
        o.location = centre + Vector(direction).normalized() * R * 3
        o.rotation_euler = (centre - o.location).to_track_quat('-Z', 'Y').to_euler()
    scene.world = bpy.data.worlds.new('Concept_Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.46, .46, .47, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .55
    scene.render.film_transparent = True
    cam = bpy.data.objects.new('Concept_Camera', bpy.data.cameras.new('Concept_Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens, cam.data.clip_end = 50, 2000
    scene.render.engine = 'CYCLES'
    scene.cycles.device, scene.cycles.samples, scene.cycles.use_denoising = 'CPU', 16, True
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = -.75
    REFS.mkdir(parents=True, exist_ok=True)
    records = []
    for view, direction, label in CR.S.VIEWS:
        dvec = Vector(direction).normalized()
        cam.location = centre + dvec * (R / math.sin(cam.data.angle / 2) * 1.02)
        cam.rotation_euler = (0, 0, 0) if abs(dvec.z) > .99 else (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(REFS / f'{view}.png')
        bpy.ops.render.render(write_still=True)
        CR.studio_backdrop(REFS / f'{view}.png')
        records.append({'name': f'{view}.png', 'title': label, 'direction': list(direction),
                        'prompt': 'Layout concept for the dondon xianxia town north block: v002 town unchanged in the south; '
                                  'raised grass terrace with stone retaining wall and balustrade; north street of 6 m stone road tiles '
                                  'with crossroads, archway and T junction; inn to the west, well square to the east, fenced lotus '
                                  f'garden north-east, waypoint altar by the archway. View: {CR.S.VIEW_PHRASE[view]}. '
                                  'Colour-coded blockout: grey roads, red buildings, brown props, ochre fences, blue water.'})
        print('LAYOUT_CONCEPT', view, flush=True)
    (REFS / 'prompts.json').write_text(json.dumps({
        'asset': 'TownLayout_v003', 'stage': 'pre-assembly layout concept', 'master': '05_front_right.png',
        'method': 'v002 scene plus colour-coded footprint blockout of every planned placement, Codex-style studio render '
                  '(BlenderSource/TownLife09/build_town_layout_v003.py --concept-only); no AI image model in the cloud session.',
        'images': records}, ensure_ascii=False, indent=2), encoding='utf-8')
    (REFS / 'README.md').write_text('\n'.join([
        '# 小鎮配置 v003：10 張配置前概念圖', '',
        '組合場景前先產生。南半部是原封不動的 v002 小鎮；北側新街區以色塊標出每個擺放位置與實際尺寸：'
        '灰＝道路方塊、紅＝建築（客棧、出生石台）、棕＝道具、黃＝籬笆與欄杆、藍＝荷花池、深紅＝牌樓。'
        '雲端環境沒有 AI 生圖模型，這些是程式渲染的配置草模；提示詞在 `prompts.json`。', '',
        '## 圖片索引', ''] + [f'{i + 1}. [{r["title"]}]({r["name"]})' for i, r in enumerate(records)] + [
        '', '成品：`Models/TownLayout/v003/`；這十張圖已放進 .blend 的 `80_Concept_References` 集合（不渲染、不匯出）。', '']),
        encoding='utf-8')


# ------------------------------------------------------------------ assembly
def append_asset(aid, coll, tag):
    with bpy.data.libraries.load(str(model_path(aid)), link=False) as (src, dst):
        dst.collections = ['01_Editable_Asset']
    c = dst.collections[0]
    root = next(o for o in c.objects if o.name.startswith(aid + '_ROOT'))
    for o in list(c.objects):
        coll.objects.link(o)
    bpy.data.collections.remove(c)
    root.name = f'{tag}_ROOT'
    return root, [o for o in coll.objects if o.type == 'MESH']


def merge_duplicate_materials():
    for m in list(bpy.data.materials):
        base, _, suffix = m.name.rpartition('.')
        if suffix.isdigit() and base in bpy.data.materials:
            m.user_remap(bpy.data.materials[base])
            bpy.data.materials.remove(m)


def assemble():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    scene = bpy.context.scene
    north = new_coll('12_North_Block_v003')
    terrace(new_coll('01_North_Terrace', north))
    counts, placed = {}, []
    groups = {}
    for aid, x, y, z, rz, note in PLACEMENTS + [('StoneRailing', x, 11.75, Z, 0, 'terrace balustrade') for x in RAILS]:
        counts[aid] = counts.get(aid, 0) + 1
        tag = f'{aid}_{counts[aid]:02d}'
        grp = groups.get(category(aid)) or groups.setdefault(category(aid), new_coll(f'0{len(groups) + 2}_North_{category(aid).title()}', north))
        coll = new_coll(tag, grp)
        root, meshes = append_asset(aid, coll, tag)
        root.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rz), 4, 'Z')
        placed.append({'asset': aid, 'instance': tag, 'location_m': [x, y, z], 'rotation_z_degrees': rz,
                       'note': note, 'mesh_objects': len(meshes)})
        print('PLACED', tag, flush=True)
    merge_duplicate_materials()
    markers = bpy.data.collections.get('80_Gameplay_Markers_Not_Exported')
    for name, loc in [('North_Crossroad_Centre', (0, 20.7, Z + .2)), ('Inn_Entry_Feet', (-8.6, 22.2, Z + .2)),
                      ('Well_Square_Centre', (9.5, 20.7, Z + .2)), ('Garden_Gate_Feet', (6.2, 29, Z)),
                      ('Waypoint_Altar_Feet', (-6.5, 27.5, Z + .6)), ('Town_Exit_North_v003', (0, 35.7, Z + .2))]:
        e = bpy.data.objects.new(name, None)
        e.location = loc
        markers.objects.link(e)
    # concept references
    refc = new_coll('80_Concept_References')
    for i, f in enumerate(sorted(REFS.glob('*.png'))):
        img = bpy.data.images.load(str(f), check_existing=True)
        e = bpy.data.objects.new('Concept_' + f.stem, None)
        e.empty_display_type, e.data, e.empty_display_size = 'IMAGE', img, 20
        e.location = (-60 + (i % 5) * 21, 60, 21 - (i // 5) * 21)
        e.rotation_euler = (math.pi / 2, 0, 0)
        e.hide_render = True
        e['concept_reference'] = str(f.relative_to(ROOT))
        refc.objects.link(e)
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    export = [o for o in scene.objects if o.type in ('MESH', 'EMPTY') and not any(
        c.name.startswith(('80_', '90_')) for c in o.users_collection)]
    for o in export:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT / 'TownLayout_v003.fbx'), use_selection=True, object_types={'MESH', 'EMPTY'},
                             add_leaf_bones=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True, bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'TownLayout_v003.blend'), relative_remap=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
    # street-level surface samples along the new street and lanes
    dg = bpy.context.evaluated_depsgraph_get()
    samples = []
    for (x, y) in [(0, 11.2), (0, 12.2), (0, 17.7), (0, 20.7), (0, 23.7), (0, 29.7), (0, 32.7), (-4, 20.7), (-8.8, 20.7),
                   (4, 20.7), (8.8, 20.7), (-4, 32.7), (4, 32.7)]:
        hit, loc, _, _, obj, _ = scene.ray_cast(dg, Vector((x, y, 30)), Vector((0, 0, -1)))
        samples.append({'x': x, 'y': y, 'surface_z': round(loc.z, 3) if hit else None, 'object': obj.name if hit else None})
    meshes = [o for o in scene.objects if o.type == 'MESH' and not any(c.name.startswith(('80_', '90_')) for c in o.users_collection)]
    info = {'stage': 'v002 town plus north block (inn, crossroads, archway, well square, fenced lotus garden, waypoint altar)',
            'source_scene_unchanged': 'Models/TownLayout/v002/TownLayout_v002.blend',
            'concept_references': 'ArtReferences/TownLayout_v003_10Views', 'terrace_top_m': Z,
            'street_surface_m': Z + .2, 'placements': placed, 'mesh_objects': len(meshes),
            'street_surface_samples': samples,
            'note': 'Visual layout prototype; not a navigation, collision or Unreal-import test.'}
    (OUT / 'layout_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    previews(scene)


def previews(scene):
    cam = scene.camera
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1100
    scene.cycles.samples = 24
    for c in bpy.data.collections:
        if c.name == '80_Concept_References':
            c.hide_render = True
    shots = [('01_town_north_block_overview.png', 'PERSP', (34, -26, 34), (-2, 16, 0), 30),
             ('02_town_top_plan_v003.png', 'ORTHO', (-2, 13, 80), (-2, 13, 0), 60),
             ('03_north_street_archway.png', 'PERSP', (2.5, 13, 3.2), (0, 30, 3.0), 28)]
    for name, kind, loc, target, lens in shots:
        cam.data.type = kind
        if kind == 'ORTHO':
            cam.data.ortho_scale = lens
        else:
            cam.data.lens = lens
        cam.data.clip_end = 1000
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
        print('PREVIEW', name, flush=True)


if __name__ == '__main__':
    concept()
    if '--concept-only' not in sys.argv:
        assemble()
