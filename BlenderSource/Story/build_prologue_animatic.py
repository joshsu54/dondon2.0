"""Build the prologue animatic 〈凌雲重開〉 from Story/序章劇情動畫_凌雲重開.md.

Build (creates the next free Models/PrologueAnimatic/vNNN, never overwrites):
  Tools/bin/blender -b --factory-startup --python BlenderSource/Story/build_prologue_animatic.py
  optional after --:  --out DIR   build into DIR instead (scratch / review builds)
                      --stills    also render one 3D still per camera cut into <out>/stills
                      --frames work/PrologueAnimatic/v001_frames   reuse an identical earlier 3D render
                      --no-audio  skip the placeholder sound (macOS `say` voices + synthesised SFX/music stems)
Render (run on the saved .blend):
  Tools/bin/blender -b <blend> --python BlenderSource/Story/build_prologue_animatic.py -- --render-frames
  Tools/bin/blender -b <blend> --python BlenderSource/Story/build_prologue_animatic.py -- --render-edit
  --render-frames renders scene Animatic3D to JPEG frames (resumable; existing frames are skipped).
  --render-edit renders scene AnimaticEdit (frames + burned-in shot ID, timecode, subtitles) to mp4.

Existing models are only linked (library links, read-only); nothing in Models/ or ArtLibrary/ is written.
Characters, VFX, the mountain stair and gate doors are grey/emissive placeholders.
"""
import bpy, bmesh, math, json, sys, random, re, shutil
from pathlib import Path
from mathutils import Vector, Matrix, Euler

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / 'Models'
MW07 = ROOT / 'ArtLibrary/ExpansionBatches/MountainWind07/Models'
STORY_DOC = 'Story/序章劇情動畫_凌雲重開.md'
FPS = 24
RES = (960, 540)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []

# ---------------------------------------------------------------- shot table
# (id, seconds, short label, subtitles [(t0, t1, text)]) - order and lengths from the storyboard doc
SHOTS = [
    ('1-1', 8, '雲海淡入，前推見孤峰剪影', [(2.0, 7.5, '旁白：「凌雲孤峰，高可摘星。」')]),
    ('1-2', 10, '低角度沿層岩峭壁上搖，迎風松', [(1.0, 9.0, '旁白：「三百年前，凌雲宗於此鎮守秘境，萬人來朝。」')]),
    ('1-3', 12, '空拍掠過山頂宗門，急降轉場山腳', [(1.5, 5.0, '旁白：「後來……」'), (6.0, 10.0, '旁白：「……就沒人來了。」')]),
    ('2-1', 6, '迎客松後推出，晨光出生廣場', [(0.5, 5.5, '〔鳥叫、遠處的打鐵聲〕')]),
    ('2-2', 5, '鐵匠鋪：鎚落火星，淬火白煙', [(0.5, 4.5, '〔叮、叮、嗤——〕')]),
    ('2-3', 5, '藥草攤、晾藥架，橫移過材料鋪', [(0.5, 4.5, '〔市集環境聲〕')]),
    ('2-4', 8, '主角長凳打瞌睡，指路碑', [(2.0, 7.5, '鐵匠（畫外音）：「又在這睡！太陽都曬屁股了！」')]),
    ('2-5', 11, '天暗，光柱落在出生石台，衝擊波', [(0.5, 6.0, '〔低頻轟鳴〕'), (8.0, 10.5, '〔突然靜音〕')]),
    ('3-1', 6, '光散，主角低頭看掌心光紋', [(0.5, 5.5, '〔心跳聲〕')]),
    ('3-2', 6, '掌門從牌樓屋頂跳下，差點滑倒', [(3.3, 5.8, '掌門：「咳——此乃，仙緣！」')]),
    ('3-3', 8, '正反打：掌門繞主角打量', [(0.4, 2.6, '掌門：「靈根……有！」'), (2.8, 5.2, '掌門：「骨骼……還行！」'),
                                     (5.4, 7.8, '掌門：「牙口……不錯！」')]),
    ('3-4', 7, '鐵匠探頭，掌門抽出舊法劍', [(0.4, 3.6, '鐵匠：「老雲，那把劍不是上個月拿來當的嗎？」'), (4.4, 6.8, '掌門：「……贖回來了。」')]),
    ('3-5', 8, '遞劍，劍柄特寫，主角握緊', [(0.8, 7.2, '掌門：「拿著。從今天起，你就是凌雲宗的弟子了。」')]),
    ('4-1', 8, '上山長階蒙太奇：遠景／側面／背影', [(0.4, 7.6, '掌門：「想當年……我一口氣……上下……三趟……」')]),
    ('4-2', 6, '抵達山頂，仰拍山門與歪斜牌匾', [(1.0, 5.5, '〔風聲，牌匾吱呀作響〕')]),
    ('4-3', 4, '推門卡住，一腳踹開', [(2.0, 3.6, '〔砰！〕')]),
    ('4-4', 12, '長鏡頭：藥圃→演武場→大殿→煉丹房', [(0.4, 3.8, '掌門：「這是……藥圃。」'), (4.0, 7.4, '掌門：「這是演武場。」'),
                                         (7.6, 11.8, '掌門：「這是……咳，總之以後都歸你管。」')]),
    ('4-5', 5, '主角回頭看掌門，掌門別開視線', [(0.3, 2.0, '主角：「……」'), (2.4, 4.8, '掌門：「掃把在倉庫。」')]),
    ('5-1', 6, '主角走上修煉台，坐上蒲團', [(0.5, 5.5, '〔音樂開始堆疊〕')]),
    ('5-2', 8, '陣紋亮起，靈氣聚集，幼苗抬頭', [(1.5, 6.0, '掌門（輕聲）：「三百年了……」')]),
    ('5-3', 8, '急速拉遠：宗門→山頂→孤峰，山後紅光', [(0.5, 7.5, '〔音樂推到最高點〕')]),
    ('5-4', 8, '雲海標題，淡出後切回 5-1 機位', [(6.4, 8.0, '提示：「按住〔打坐鍵〕開始修煉」')]),
]
START = {}
_f = 0
for _id, _sec, *_ in SHOTS:
    START[_id] = _f
    _f += _sec * FPS
FRAME_END = _f - 1  # 165 s -> frames 0..3959, so timecode equals the storyboard time


def F(shot, t=0.0):
    return START[shot] + int(round(t * FPS))


# ------------------------------------------------------------- world layout (metres)
TOWN = Vector((0, 0, 0))                 # TownLayout v002 at origin, north exit at (0, 11.7, 1.32)
STAIR_Y0, STAIR_Y1, STAIR_Z0, STAIR_Z1 = 26.0, 104.0, 1.32, 48.0
STAIR_STEPS, STAIR_W = 156, 3.6
PLATEAU = Vector((0, 160, 0))            # SectSummitPlateau: flat top at 48 m from local y -55..45
SECT = Vector((0, 150.5, 48))            # SectLayout v003 campus centre (y 9.5) over plateau centre
PEAK = Vector((0, 262, 0))
PEAK_SCALE = 2.4
DAIS = Vector((0, -3.3, 0.49))           # spawn stone dais centre / top
BENCH = Vector((-3.65, -3.1, 0.85))
ANVIL = Vector((11.25, 7.85, 1.38))
BARREL = Vector((10.5, 10.23, 1.07))
PLATFORM = SECT + Vector((10, 12.13, 0))  # cultivation platform seat centre
SEAT_TOP = 48.82 + 0.19                   # woven seat top + MeditationCushion height


def sect(x, y, z=0.0):
    return SECT + Vector((x, y, z))


def stair_z(y):
    if y <= STAIR_Y0:
        return STAIR_Z0
    if y >= STAIR_Y1:
        return STAIR_Z1
    run = (STAIR_Y1 - STAIR_Y0) / STAIR_STEPS
    i = min(int((y - STAIR_Y0) / run), STAIR_STEPS - 1)
    return STAIR_Z0 + (i + 1) * (STAIR_Z1 - STAIR_Z0) / STAIR_STEPS


# ------------------------------------------------------------------ helpers
def col(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def material(name, color, rough=.7, emit=0.0, emit_color=None, alpha=1.0, metal=0.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    m.diffuse_color = (*color, alpha)
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    if emit or emit_color:
        bs.inputs['Emission Color'].default_value = (*(emit_color or color), 1)
        bs.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        bs.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
        try:
            m.use_transparency_overlap = False
        except Exception:
            pass
    return m


def bsdf(m):
    return m.node_tree.nodes.get('Principled BSDF')


def key_mat(m, socket, frame, value):
    inp = bsdf(m).inputs[socket]
    inp.default_value = value
    inp.keyframe_insert('default_value', frame=frame)


def mesh_obj(name, bm, mat, coll, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    coll.objects.link(o)
    o.parent = parent
    o.location = loc
    return o


def box(name, size, center, mat, coll, parent=None, loc=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(center) @ Matrix.Diagonal((*size, 1)))
    return mesh_obj(name, bm, mat, coll, parent, loc)


def cylinder(name, r, depth, mat, coll, center=(0, 0, 0), segs=32, r2=None, parent=None, loc=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2,
                          depth=depth, matrix=Matrix.Translation(center))
    for f in bm.faces:
        f.smooth = True
    return mesh_obj(name, bm, mat, coll, parent, loc)


def sphere(name, r, mat, coll, loc=(0, 0, 0), parent=None, segs=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(6, segs // 2), radius=r)
    for f in bm.faces:
        f.smooth = True
    return mesh_obj(name, bm, mat, coll, parent, loc)


def torus(name, major, minor, mat, coll, loc=(0, 0, 0), segs=64, ring=8):
    bm = bmesh.new()
    verts = []
    for i in range(segs):
        a = i * math.tau / segs
        for j in range(ring):
            b = j * math.tau / ring
            rr = major + minor * math.cos(b)
            verts.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), minor * math.sin(b))))
    for i in range(segs):
        for j in range(ring):
            q = [verts[(i * ring + j)], verts[((i + 1) % segs) * ring + j],
                 verts[((i + 1) % segs) * ring + (j + 1) % ring], verts[i * ring + (j + 1) % ring]]
            bm.faces.new(q).smooth = True
    return mesh_obj(name, bm, mat, coll, None, loc)


def plane(name, sx, sy, mat, coll, loc=(0, 0, 0), rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, matrix=Matrix.Diagonal((sx, sy, 1, 1)))
    o = mesh_obj(name, bm, mat, coll, None, loc)
    o.rotation_euler = rot
    return o


def empty(name, coll, loc=(0, 0, 0), size=0.3, parent=None, kind='PLAIN_AXES'):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = kind
    o.empty_display_size = size
    o.location = loc
    o.parent = parent
    coll.objects.link(o)
    return o


def kf(o, frame, **props):
    for k, v in props.items():
        setattr(o, k, v)
        o.keyframe_insert(k, frame=frame)


def fcurves(idb):
    ad = getattr(idb, 'animation_data', None)
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, 'fcurves'):
        return list(act.fcurves)
    from bpy_extras import anim_utils
    cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
    return list(cb.fcurves) if cb else []


def set_interp(idb, interp):
    for fc in fcurves(idb):
        for kp in fc.keyframe_points:
            kp.interpolation = interp


def show(o, f_on, f_off, scale=(1, 1, 1)):
    """Visible (via scale) between f_on and f_off inclusive, scale 0 elsewhere."""
    s0 = (0.0, 0.0, 0.0)
    kf(o, 0, scale=s0)
    if f_on > 1:
        kf(o, f_on - 1, scale=s0)
    kf(o, f_on, scale=scale)
    kf(o, f_off, scale=scale)
    kf(o, f_off + 1, scale=s0)


def face_angle(src, dst):
    d = Vector(dst).to_3d().xy - Vector(src).to_3d().xy
    return math.atan2(d.x, -d.y)  # rotation Z that turns the -Y front toward dst


# ------------------------------------------------------------ linked sources
LINKED = {}       # path -> wrapper collection
SOURCES_USED = {}  # instance name -> relative source path


def link_wrapper(path, label):
    path = Path(path)
    if path in LINKED:
        return LINKED[path]
    if not path.exists():
        raise FileNotFoundError(path)
    # take the top-level collections of the source scene (skips orphan leftovers such as a stray 'Cube')
    with bpy.data.libraries.load(str(path), link=True) as (src, dst):
        dst.scenes = list(src.scenes)
    lscs = [s for s in dst.scenes if s is not None]
    lsc = max(lscs, key=lambda s: len(s.collection.all_objects))  # e.g. TownLayout also keeps an empty default 'Scene'
    skip = ('Not_Exported', 'Not_For_Export', 'Hidden', 'Studio', 'Reference')
    top = [c for c in lsc.collection.children if not any(s in c.name for s in skip) and len(c.all_objects) > 0]
    w = bpy.data.collections.new('SRC_' + label)
    LINKED_ROOT.children.link(w)
    for c in top:
        w.children.link(c)
    LINKED[path] = w
    for s in lscs:
        try:
            bpy.data.scenes.remove(s)
        except Exception:
            pass
    return w


def instance(label, path, coll, loc=(0, 0, 0), rot_z=0.0, scale=1.0, name=None, parent=None):
    w = link_wrapper(path, label)
    o = bpy.data.objects.new(name or ('SET_' + label), None)
    o.instance_type = 'COLLECTION'
    o.instance_collection = w
    o.empty_display_size = 1.0
    o.location = loc
    o.rotation_euler = (0, 0, rot_z)
    o.scale = (scale, scale, scale)
    o.parent = parent
    coll.objects.link(o)
    SOURCES_USED[o.name] = str(path.relative_to(ROOT))
    return o


def latest(asset):
    vs = sorted((MODELS / asset).glob('v[0-9][0-9][0-9]/%s_v[0-9][0-9][0-9].blend' % asset))
    return vs[-1]


# --------------------------------------------------------------- ray helpers
IGNORE_PREFIX = ('CHR_', 'FX_', 'CAM_', 'PH_Cloud')


def ray_down(x, y, z_from):
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    origin = Vector((x, y, z_from))
    for _ in range(8):
        hit, loc, nrm, idx, obj, mtx = sc.ray_cast(dg, origin, Vector((0, 0, -1)))
        if not hit:
            return None
        if obj and obj.name.startswith(IGNORE_PREFIX):
            origin = loc - Vector((0, 0, 0.01))
            continue
        return loc.z
    return None


def ground(x, y, z_hint):
    z = ray_down(x, y, z_hint + 1.2)
    return z_hint if z is None else z


# ---------------------------------------------------------- placeholder people
class Char:
    def __init__(self, name, label, gray, accent, coll, build=1.0):
        g = material('PH_%s_Gray' % name, (gray,) * 3, .8)
        dark = material('PH_%s_Face' % name, (gray * .45,) * 3, .8)
        acc = material('PH_%s_Accent' % name, accent, .6)
        self.name, self.label = name, label
        self.root = empty('CHR_' + name, coll, size=.4, kind='ARROWS')
        w = .46 * build
        self.torso = box('CHR_%s_Torso' % name, (w, .26 * build, .62), (0, 0, .31), g, coll, self.root, (0, 0, .9))
        self.head = box('CHR_%s_Head' % name, (.24, .25, .26), (0, 0, .13), g, coll, self.torso, (0, 0, .64))
        box('CHR_%s_FaceMark' % name, (.08, .05, .05), (0, -.14, .14), dark, coll, self.head)
        self.legs = [box('CHR_%s_Leg%s' % (name, s), (.17, .2, .88), (0, 0, -.44), g, coll, self.root, (sx * .11, 0, .9))
                     for s, sx in (('L', 1), ('R', -1))]
        self.arms = [box('CHR_%s_Arm%s' % (name, s), (.1, .12, .6), (0, 0, -.3), g, coll, self.torso,
                         (sx * (w / 2 + .06), 0, .58)) for s, sx in (('L', 1), ('R', -1))]
        self.acc_mat, self.coll, self.gray = acc, coll, g
        self.state = dict(loc=Vector((0, -600, -60)), rz=0.0, lean=0.0, nod=0.0, turn=0.0,
                          legL=0.0, legR=0.0, armL=(0.0, 0.0), armR=(0.0, 0.0))

    def pose(self, f, **kw):
        st = self.state
        if 'rz' in kw:  # unwrap so linear interpolation takes the short way round
            r = kw['rz']
            while r - st['rz'] > math.pi:
                r -= math.tau
            while r - st['rz'] < -math.pi:
                r += math.tau
            kw['rz'] = r
        if 'loc' in kw:
            kw['loc'] = Vector(kw['loc'])
        st.update(kw)
        d = math.radians
        kf(self.root, f, location=st['loc'], rotation_euler=(0, 0, st['rz']))
        kf(self.torso, f, rotation_euler=(d(st['lean']), 0, 0))
        kf(self.head, f, rotation_euler=(d(st['nod']), 0, d(st['turn'])))
        kf(self.legs[0], f, rotation_euler=(d(st['legL']), 0, 0))
        kf(self.legs[1], f, rotation_euler=(d(st['legR']), 0, 0))
        kf(self.arms[0], f, rotation_euler=(d(st['armL'][0]), d(st['armL'][1]), 0))
        kf(self.arms[1], f, rotation_euler=(d(st['armR'][0]), d(st['armR'][1]), 0))

    def cut(self, f, **kw):
        """Hold the previous state until f-1, jump to the new state at f."""
        self.pose(f - 1)
        self.pose(f, **kw)

    def walk(self, f0, f1, dst, z_hint=None, stride=7, face=True, swing=24, **end):
        src = Vector(self.state['loc'])
        dst = Vector(dst)
        rz = face_angle(src, dst) if face and (dst - src).xy.length > .05 else self.state['rz']
        self.pose(f0, rz=rz)
        n = max(1, (f1 - f0) // stride)
        for i in range(1, n + 1):
            f = f0 + round((f1 - f0) * i / n)
            p = src.lerp(dst, i / n)
            if z_hint is not None:
                p.z = ground(p.x, p.y, z_hint(p) if callable(z_hint) else z_hint)
            s = swing if i % 2 else -swing
            if i == n:
                self.pose(f, loc=p, legL=0, legR=0, armL=(0, 0), armR=(0, 0), **end)
            else:
                self.pose(f, loc=p, legL=s, legR=-s, armL=(-s * .6, 0), armR=(s * .6, 0))


# ------------------------------------------------------------------ cameras
CAMS = []


def camera(shot, t0, keys, suffix='', lens=35):
    """keys: [(t, cam_loc, target, lens|None)] in seconds from the shot start."""
    name = 'CAM_%s%s' % (shot, suffix)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = .05, 5000
    cd.sensor_width = 36
    cam = bpy.data.objects.new(name, cd)
    COL_CAM.objects.link(cam)
    tgt = empty(name + '_Target', COL_CAM, size=.5)
    c = cam.constraints.new('TRACK_TO')
    c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    for t, loc, target, ln in keys:
        f = F(shot, t)
        kf(cam, f, location=Vector(loc))
        kf(tgt, f, location=Vector(target))
        if ln:
            cd.lens = ln
            cd.keyframe_insert('lens', frame=f)
    m = bpy.context.scene.timeline_markers.new(shot, frame=F(shot, t0))
    m.camera = cam
    CAMS.append(dict(shot=shot, camera=name, frame=F(shot, t0)))
    return cam


# ======================================================================= BUILD
def build(out_dir, frames_dir):
    global LINKED_ROOT, COL_CAM
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.name = 'Animatic3D'
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, FRAME_END
    sc.unit_settings.system = 'METRIC'
    random.seed(7)

    LINKED_ROOT = col('00_Linked_Sources_Not_Rendered')
    c_town, c_mtn, c_sect = col('10_Set_Town'), col('11_Set_Mountain'), col('12_Set_Sect')
    c_ph = col('20_Placeholder_Geometry')
    c_chr = col('21_Placeholder_Characters')
    c_fx = col('22_Placeholder_FX')
    COL_CAM = col('30_Cameras')
    c_light = col('40_Lights')
    sc.view_layers[0].layer_collection.children[LINKED_ROOT.name].exclude = True

    # ---------- sets (linked, read-only)
    instance('TownLayout_v002', MODELS / 'TownLayout/v002/TownLayout_v002.blend', c_town)
    instance('MaterialShop', latest('MaterialShop'), c_town, (-12.2, -8.4, 0), math.radians(90))
    instance('HerbalStall', latest('HerbalStall'), c_town, (-6.0, -7.0, 0), math.radians(90))
    instance('DryingRack', latest('DryingRack'), c_town, (-6.0, -9.3, 0), math.radians(90), name='SET_DryingRack_A')
    instance('DryingRack', latest('DryingRack'), c_town, (-6.3, -10.7, 0), math.radians(80), name='SET_DryingRack_B')
    instance('SalesCounter', latest('SalesCounter'), c_town, (-7.6, -5.3, 0), math.radians(90))

    instance('SectSummitPlateau', MW07 / 'SectSummitPlateau/v001/SectSummitPlateau_v001.blend', c_mtn, PLATEAU)
    instance('CloudpiercerPeak', MW07 / 'CloudpiercerPeak/v001/CloudpiercerPeak_v001.blend', c_mtn, PEAK,
             0, PEAK_SCALE)
    ridge = MW07 / 'MountainRidge/v001/MountainRidge_v001.blend'
    instance('MountainRidge', ridge, c_mtn, (-215, 215, 0), math.radians(70), 2.6, name='SET_MountainRidge_West')
    instance('MountainRidge', ridge, c_mtn, (230, 250, 0), math.radians(-65), 2.8, name='SET_MountainRidge_East')
    instance('MountainRidge', ridge, c_mtn, (40, 560, 0), math.radians(8), 3.4, name='SET_MountainRidge_North')
    cliff = MW07 / 'LayeredCliff/v001/LayeredCliff_v001.blend'
    instance('LayeredCliff', cliff, c_mtn, (-30, 52, 0), math.radians(90), 1.3, name='SET_LayeredCliff_West')
    instance('LayeredCliff', cliff, c_mtn, (26, 80, 0), math.radians(-90), 1.6, name='SET_LayeredCliff_East')
    instance('SectLayout_v003', MODELS / 'SectLayout/v003/SectLayout_v003.blend', c_sect, SECT)
    instance('MeditationCushion', latest('MeditationCushion'), c_sect, (PLATFORM.x, PLATFORM.y, 48.82))

    # ---------- placeholder geometry
    m_ground = material('PH_Ground', (.32, .36, .26), .95)
    m_stair = material('PH_Stair_Stone', (.55, .53, .49), .85)
    plane('PH_Ground_Plane', 4000, 4000, m_ground, c_ph, (0, 0, -.32))
    bm = bmesh.new()
    run, rise = (STAIR_Y1 - STAIR_Y0) / STAIR_STEPS, (STAIR_Z1 - STAIR_Z0) / STAIR_STEPS
    for i in range(STAIR_STEPS):
        top = STAIR_Z0 + (i + 1) * rise
        y0 = STAIR_Y0 + i * run
        bot = -.3 if i < 8 else top - 3.5  # thick slab, not a solid wall, so the cliffs read
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, y0 + run / 2, (top + bot) / 2))
                              @ Matrix.Diagonal((STAIR_W, run, top - bot, 1)))
    mesh_obj('PH_Mountain_Stair_156_Steps', bm, m_stair, c_ph)
    box('PH_Path_Town_To_Stair', (STAIR_W, STAIR_Y0 - 10.5, 1.62), (0, (STAIR_Y0 + 10.5) / 2, STAIR_Z0 - .81),
        m_stair, c_ph)
    box('PH_Path_Stair_To_SectGate', (STAIR_W, 131.5 - 103.5, .5), (0, (131.5 + 103.5) / 2, 47.8), m_stair, c_ph)
    # gate leaves behind the blank nameboard (SectGate has no door pieces yet)
    m_door = material('PH_Gate_Door', (.33, .2, .12), .7)
    door_hinge_y = SECT.y - 14.55
    doors = []
    for side, sx in (('L', -1), ('R', 1)):
        h = empty('PH_Gate_Door_Hinge_' + side, c_ph, (sx * 1.25, door_hinge_y, 48.0), .2)
        box('PH_Gate_Door_' + side, (1.25, .1, 3.1), (-sx * .625, 0, 1.55), m_door, c_ph, h)
        doors.append((h, sx))
    m_plaque = material('PH_Plaque', (.24, .14, .08), .6)
    plaque_pivot = empty('PH_Crooked_Plaque_Pivot', c_ph, (-1.15, SECT.y - 14.98, 48 + 3.95), .2)
    box('PH_Crooked_Plaque', (2.4, .08, .62), (1.2, 0, -.31), m_plaque, c_ph, plaque_pivot)

    # cloud cards (ring around the summit, clear over the sect so 1-3 / 4-x stay readable)
    m_cloud = material('PH_Cloud_Card', (1, 1, 1), .9, emit=.5, emit_color=(.9, .93, 1), alpha=.32)
    rng = random.Random(11)
    n = 0
    while n < 70:
        x, y = rng.uniform(-320, 320), rng.uniform(-170, 420)
        if (Vector((x, y)) - Vector((0, 190))).length < 135:
            continue
        z = rng.uniform(64, 98)
        s = rng.uniform(45, 110)
        plane('PH_Cloud_%02d' % n, s, s * rng.uniform(.4, .8), m_cloud, c_ph, (x, y, z),
              (0, 0, rng.uniform(0, math.pi)))
        n += 1
    # 1-1 push-in path: a few cards straddling the camera route
    for i, (y, z, s) in enumerate([(-112, 88, 70), (-95, 82, 80), (-78, 90, 60), (-64, 84, 75), (-50, 87, 55)]):
        plane('PH_Cloud_Path_%d' % i, s, s * .6, m_cloud, c_ph, (rng.uniform(-12, 12), y, z),
              (math.radians(rng.uniform(-8, 8)), 0, rng.uniform(0, 3)))

    bpy.context.view_layer.update()

    # ---------- foliage on terrain (linked instances, placed by ray cast)
    pine = MW07 / 'WindPine/v001/WindPine_v001.blend'
    grass = MW07 / 'WindGrass/v001/WindGrass_v001.blend'
    for i, (x, y, zh, rz, s) in enumerate([(-22.5, 50, 60, 90, 1.1), (-23.5, 62, 60, 80, .9), (14.5, 74, 70, -95, 1.0),
                                           (-9, 107, 60, 15, 1.0), (9.5, 109, 60, -10, .9), (-30, 150, 60, 40, 1.2),
                                           (31, 168, 60, -30, 1.1)]):
        z = ray_down(x, y, zh + 40)
        instance('WindPine', pine, c_mtn, (x, y, (z or 0) - .1), math.radians(rz), s, name='SET_WindPine_%d' % i)
    gr = random.Random(3)
    placed = 0
    for _ in range(900):
        if placed >= 160:
            break
        if gr.random() < .35:   # tufts along the approach path and gate (kept clear of the 4-2/4-3 lenses)
            x, y = gr.uniform(-9, 9), gr.uniform(106, 134)
            if abs(x) < 5.0 and y > 118:
                continue
            if abs(x) < STAIR_W / 2 + .2:
                continue
        else:                    # overgrown courtyard
            x, y = gr.uniform(-20, 20), gr.uniform(132, 188)
        z = ray_down(x, y, 60)
        if z is None or not (47.85 < z < 48.15):
            continue  # skip roofs, platforms, paths raised above the yard
        instance('WindGrass', grass, c_sect, (x, y, z), gr.uniform(0, math.tau), gr.uniform(.7, 1.3),
                 name='SET_WindGrass_%03d' % placed)
        placed += 1
    seedlings = []
    for i in range(6):
        p = sect(-13.2 + i * .9, 9.25)
        o = instance('SpiritHerbSeedling', latest('SpiritHerbSeedling'), c_sect, (p.x, p.y, 48.02), 0, 2.2,
                     name='SET_SpiritHerbSeedling_%d' % i)
        seedlings.append(o)
    sword_e = instance('BasicSword01', MODELS / 'BasicSword01/v001/BasicSword01_v001.blend', c_chr,
                       name='SET_BasicSword01_Elder')
    sword_p = instance('BasicSword01', MODELS / 'BasicSword01/v001/BasicSword01_v001.blend', c_chr,
                       name='SET_BasicSword01_Hero')
    bpy.context.view_layer.update()

    # ---------- lights / sky
    world = bpy.data.worlds.new('Animatic_Sky')
    sc.world = world
    try:
        world.use_nodes = True
    except Exception:
        pass
    bg = world.node_tree.nodes['Background']
    sun_d = bpy.data.lights.new('Sun_Morning', 'SUN')
    sun_d.color = (1.0, .9, .78)
    sun_d.angle = math.radians(2)
    sun = bpy.data.objects.new('Sun_Morning', sun_d)
    sun.rotation_euler = (math.radians(62), 0, math.radians(60))
    c_light.objects.link(sun)
    sky_day, sky_dark = (.42, .56, .76, 1), (.05, .06, .11, 1)

    def sky(f, strength, color, sun_e):
        bg.inputs['Strength'].default_value = strength
        bg.inputs['Strength'].keyframe_insert('default_value', frame=f)
        bg.inputs['Color'].default_value = color
        bg.inputs['Color'].keyframe_insert('default_value', frame=f)
        sun_d.energy = sun_e
        sun_d.keyframe_insert('energy', frame=f)

    sky(0, 1.0, sky_day, 4.0)
    sky(F('2-5', 0.0), 1.0, sky_day, 4.0)
    sky(F('2-5', 2.0), .18, sky_dark, .25)
    sky(F('3-1', 0) - 1, .18, sky_dark, .25)
    sky(F('3-1', 0), .6, sky_day, 2.0)
    sky(F('3-1', 6), 1.0, sky_day, 4.0)

    # ---------- characters
    hero = Char('Hero', '主角', .3, (.12, .28, .62), c_chr)
    elder = Char('Elder', '老掌門', .2, (.85, .85, .82), c_chr, build=1.05)
    smith = Char('Smith', '鐵匠', .25, (.35, .18, .08), c_chr, build=1.25)
    box('CHR_Hero_Sash', (.48, .28, .07), (0, 0, .12), hero.acc_mat, c_chr, hero.torso)
    box('CHR_Elder_Beard', (.16, .06, .16), (0, -.145, .02), elder.acc_mat, c_chr, elder.head)
    box('CHR_Elder_Topknot', (.1, .1, .1), (0, 0, .3), elder.acc_mat, c_chr, elder.head)
    box('CHR_Smith_Apron', (.5, .04, .75), (0, -.18, .1), smith.acc_mat, c_chr, smith.torso)
    box('CHR_Smith_Hammer_Placeholder', (.09, .26, .1), (0, -.08, -.66), material('PH_Iron', (.18,) * 3, .4, metal=.8),
        c_chr, smith.arms[1])
    m_palm = material('FX_Palm_Glow', (.6, .95, 1), emit=0, emit_color=(.55, .95, 1))
    palm = plane('FX_Palm_Glow_Disc', .16, .16, m_palm, c_fx, (0, 0, -.62), (math.radians(90), 0, 0))
    palm.parent = hero.arms[1]

    # world positions per beat
    off = Vector((0, -600, -60))
    for c in (hero, elder, smith):
        c.pose(0, loc=off)
    def sit_z(seat):
        return seat - .9

    # 2-1 .. 2-5: hero dozing on the bench, smith at the anvil
    hero.cut(F('2-1'), loc=(BENCH.x, BENCH.y, sit_z(BENCH.z)), rz=math.radians(90), legL=-82, legR=-82,
             lean=12, nod=25, armL=(-25, 0), armR=(-25, 0))
    smith.cut(F('2-1'), loc=(12.05, 7.85, .42), rz=math.radians(-90), armR=(-60, 0))
    for i, t in enumerate([0.2, 0.75, 1.0, 1.75, 2.0, 2.75, 3.0, 3.7, 4.2]):
        up = i % 2 == 0
        smith.pose(F('2-2', t), armR=(-165, 0) if up else (-55, 0), lean=-6 if up else 14)
    smith.pose(F('2-2', 5))
    hero.pose(F('2-4', 0))
    for t, nod in ((1.5, 40), (2.6, 18), (4.0, 45), (5.0, 20), (6.0, 48), (8.0, 48)):
        hero.pose(F('2-4', t), nod=nod)
    hero.pose(F('2-5', 0), nod=48)
    hero.pose(F('2-5', 2.0), nod=-10, lean=-8)       # wakes as the sky darkens
    hero.pose(F('2-5', 6.0), nod=-20, lean=-15, armL=(-70, -20), armR=(-70, 20))
    hero.pose(F('2-5', 7.0), lean=-25, armL=(-120, -20), armR=(-120, 20))  # shields eyes at impact
    hero.pose(F('2-5', 11.0))
    smith.pose(F('2-5', 11.0))

    # 3-1 hero standing on the dais looking at the palm
    hero.cut(F('3-1'), loc=DAIS, rz=0, legL=0, legR=0, lean=8, nod=10, armL=(0, 0), armR=(-20, 0))
    hero.pose(F('3-1', 1.5), armR=(-75, 25), nod=38, lean=12)
    hero.pose(F('3-1', 6.0), armR=(-80, 28), nod=40, lean=12)
    key_mat(m_palm, 'Emission Strength', F('3-1') - 1, 0.0)
    key_mat(m_palm, 'Emission Strength', F('3-1'), 25.0)
    key_mat(m_palm, 'Emission Strength', F('3-2', 1.0), 6.0)
    key_mat(m_palm, 'Emission Strength', F('3-3'), 0.0)
    # 3-2 elder jumps from the town gateway roof
    hero.cut(F('3-2'), loc=DAIS, rz=math.radians(180), nod=0, lean=0, armR=(0, 0))
    roof = Vector((0, 5.45, 6.12))
    land = Vector((0, 3.1, ground(0, 3.1, 1.4)))
    elder.cut(F('3-2'), loc=roof, rz=0, armL=(-10, -20), armR=(-10, 20))
    elder.pose(F('3-2', 1.3), lean=20, legL=-30, legR=-30)                       # crouch
    elder.pose(F('3-2', 1.7), loc=roof + Vector((0, -.6, .9)), lean=-5, legL=10, legR=-15,
               armL=(-150, -40), armR=(-150, 40))
    elder.pose(F('3-2', 2.3), loc=land, lean=25, legL=-40, legR=-40, armL=(-60, -50), armR=(-60, 50))
    elder.pose(F('3-2', 2.7), loc=land + Vector((0, -.35, 0)), lean=-28, legL=25, legR=-35,
               armL=(-170, -70), armR=(-30, 80))                                 # slips
    elder.pose(F('3-2', 3.2), loc=land + Vector((0, -.5, 0)), lean=6, legL=0, legR=0, armL=(0, -25), armR=(0, 25))
    elder.pose(F('3-2', 4.0), lean=-6, armL=(-30, 0), armR=(-95, 0))            # 「此乃，仙緣！」 pointing
    elder.pose(F('3-2', 6.0))
    # 3-3 elder circles the hero
    hero.cut(F('3-3'), loc=DAIS, rz=0, nod=0, lean=0)
    r = 1.3
    for i in range(13):
        t = i * 7.6 / 12
        a = math.radians(-90 + 360 * i / 12 + 90)  # starts east of the hero, walks around counter-clockwise
        p = DAIS + Vector((r * math.cos(a), r * math.sin(a), 0))
        poke = (-85, 0) if i in (2, 5, 9) else (-20, 0)
        s = 20 if i % 2 else -20
        kw = dict(loc=p, rz=face_angle(p, DAIS), armR=poke, legL=s, legR=-s, lean=10)
        (elder.cut if i == 0 else elder.pose)(F('3-3', t), **kw)
        hero.pose(F('3-3', t), turn=max(-70, min(70, math.degrees(face_angle(DAIS, p)))) * .5)
    elder.pose(F('3-3', 8), legL=0, legR=0, lean=0, armR=(0, 0))
    hero.pose(F('3-3', 8))
    # 3-4 / 3-5 hand-over: hero faces +X, elder faces -X
    e_pos = DAIS + Vector((1.15, 0, 0))
    hero.cut(F('3-4'), loc=DAIS, rz=math.radians(90), turn=0)
    elder.cut(F('3-4'), loc=e_pos, rz=math.radians(-90), lean=0, legL=0, legR=0)
    smith.cut(F('3-4'), loc=(11.4, 6.2, .42), rz=face_angle((11.4, 6.2), DAIS), armR=(0, 0), lean=0)
    smith.walk(F('3-4', .1), F('3-4', 1.2), (9.55, 4.45, .25), z_hint=1.0)
    smith.pose(F('3-4', 1.3), lean=15, armL=(-40, -30), armR=(-90, 15))
    smith.pose(F('3-4', 3.6), lean=10, armR=(-40, 15))
    smith.pose(F('3-4', 7.0))
    elder.pose(F('3-4', 1.0), turn=-55)
    elder.pose(F('3-4', 3.6), turn=-55)
    elder.pose(F('3-4', 4.0), turn=0, armR=(-160, 30))       # reaches over the shoulder
    elder.pose(F('3-4', 4.8), armR=(-80, 0))
    elder.pose(F('3-4', 7.0), armR=(-80, 0))
    hero.pose(F('3-4', 1.0), turn=40)
    hero.pose(F('3-4', 3.6), turn=40)
    hero.pose(F('3-4', 4.2), turn=0)
    hero.pose(F('3-4', 7.0))
    elder.cut(F('3-5'), armR=(-75, 0), armL=(-60, 0))
    hero.cut(F('3-5'), armR=(0, 0))
    hero.pose(F('3-5', 2.5), armR=(-15, 0))
    hero.pose(F('3-5', 4.0), armR=(-62, -12))                # grips the hilt
    hero.pose(F('3-5', 8.0), armR=(-62, -12))
    elder.pose(F('3-5', 4.5), armR=(-75, 0), armL=(-60, 0))
    elder.pose(F('3-5', 5.5), armR=(-20, 0), armL=(-15, 0))
    elder.pose(F('3-5', 8.0))

    # swords: elder's copy parented to the elder until the hand-over, hero carries his own from 4-1
    sword_e.parent = elder.root
    back = dict(location=Vector((.12, .2, 1.62)), rotation_euler=(math.pi, .25, 0))
    kf(sword_e, 0, **back)
    kf(sword_e, F('3-4', 4.0), **back)
    offer = dict(location=Vector((0, -.5, 1.12)), rotation_euler=(math.pi, 0, 0))
    kf(sword_e, F('3-4', 4.8), **offer)
    kf(sword_e, F('3-5', 5.0), **offer)
    kf(sword_e, F('3-5', 8.0), location=Vector((0, -.62, 1.0)), rotation_euler=(math.pi, 0, 0))
    show(sword_e, F('3-2'), F('3-5', 8.0) - 1)
    sword_p.parent = hero.root
    sword_p.location, sword_p.rotation_euler = back['location'], back['rotation_euler']
    show(sword_p, F('4-1'), FRAME_END)

    # 4-1 stair montage (three set-ups, characters re-placed per cut)
    def on_stair(y, x=0.0):
        return Vector((x, y, stair_z(y)))
    for cut_t, y0, y1, puff in ((0.0, 34, 38.5, 0), (3.0, 64, 67, 1), (5.6, 91, 94, 2)):
        f0, f1 = F('4-1', cut_t), F('4-1', cut_t + 2.5)
        hero.cut(f0, loc=on_stair(y0 + 1.6, .55), rz=math.pi, legL=0, legR=0, nod=0, turn=0, lean=0,
                 armL=(0, 0), armR=(0, 0))
        elder.cut(f0, loc=on_stair(y0, -.55), rz=math.pi, legL=0, legR=0, nod=0, turn=0, armL=(0, 0), armR=(0, 0),
                  lean=10 + puff * 12)
        hero.walk(f0 + 1, f1, on_stair(y1 + 1.6, .55), z_hint=lambda p: stair_z(p.y), stride=6)
        elder.walk(f0 + 1, f1, on_stair(y1, -.55), z_hint=lambda p: stair_z(p.y), stride=6 + puff * 2,
                   swing=24 - puff * 6, lean=10 + puff * 12)
    hero.pose(F('4-1', 8.0))
    elder.pose(F('4-1', 8.0), lean=34, armL=(-30, 0), armR=(-45, 0))

    # 4-2 arriving at the gate, 4-3 the stuck door
    hero.cut(F('4-2'), loc=(1.3, 124.0, 48.05), rz=math.radians(180), lean=0, nod=-15)
    elder.cut(F('4-2'), loc=(-.4, 125.0, 48.05), rz=math.radians(180), lean=26, nod=0, armL=(0, 0), armR=(0, 0))
    hero.walk(F('4-2', .2), F('4-2', 5.6), (.9, 132.6, 48.05), z_hint=48.1, nod=-20)
    elder.walk(F('4-2', .2), F('4-2', 5.6), (-.3, 134.0, 48.05), z_hint=48.1, lean=14)
    elder.pose(F('4-2', 6.0), turn=0)
    pz = ground(0, SECT.y - 15.5, 48.4)
    elder.cut(F('4-3'), loc=(0, SECT.y - 15.45, pz), rz=math.radians(180), lean=12, armL=(-85, 0), armR=(-85, 0))
    hero.cut(F('4-3'), loc=(-1.2, SECT.y - 17.6, 48.05), rz=math.radians(180), nod=0)
    for i, t in enumerate((0.3, 0.55, 0.8, 1.05, 1.3)):
        elder.pose(F('4-3', t), lean=18 if i % 2 else 8)
    elder.pose(F('4-3', 1.6), lean=-15, armL=(-20, -30), armR=(-20, 30), legR=20)     # wind-up
    elder.pose(F('4-3', 2.0), lean=-20, legR=-95)                                   # kick
    elder.pose(F('4-3', 2.6), lean=0, legR=0, armL=(0, 0), armR=(0, 0))
    elder.pose(F('4-3', 4.0))
    hero.pose(F('4-3', 2.0), lean=-10)
    hero.pose(F('4-3', 4.0), lean=0)
    for h, sx in doors:
        rz_closed, rz_open = 0.0, math.radians(-sx * 105)
        kf(h, 0, rotation_euler=(0, 0, rz_closed))
        for i, t in enumerate((0.3, 0.55, 0.8, 1.05, 1.3)):
            kf(h, F('4-3', t), rotation_euler=(0, 0, math.radians(-sx * (4 if i % 2 else 1))))
        kf(h, F('4-3', 2.05), rotation_euler=(0, 0, rz_closed))
        kf(h, F('4-3', 2.45), rotation_euler=(0, 0, rz_open))
        kf(h, F('4-3', 2.8), rotation_euler=(0, 0, rz_open * .9))
    for i, t in enumerate([0, 0.8, 1.6, 2.4, 3.2, 4.0, 4.8, 5.6, 6.0]):
        kf(plaque_pivot, F('4-2', t), rotation_euler=(0, math.radians(-9 + (2.5 if i % 2 else -1.0)), 0))
    kf(plaque_pivot, F('4-3', 2.05), rotation_euler=(0, math.radians(-9), 0))
    kf(plaque_pivot, F('4-3', 2.3), rotation_euler=(0, math.radians(-16), 0))
    kf(plaque_pivot, F('4-3', 2.9), rotation_euler=(0, math.radians(-12), 0))

    # 4-4 tour along the central path
    elder.cut(F('4-4'), loc=(-.3, 139.5, 48.05), rz=math.pi, lean=10, legL=0, legR=0, armL=(0, 0), armR=(0, 0))
    hero.cut(F('4-4'), loc=(.6, 137.8, 48.05), rz=math.pi, lean=0, nod=0)
    beats = [(0.0, 3.8, (-.2, 144.0), dict(armL=(-20, -80), turn=-50)),
             (3.8, 7.4, (.4, 148.5), dict(armR=(-20, 80), turn=55, armL=(0, 0))),
             (7.4, 9.6, (.2, 151.5), dict(armR=(-110, 0), turn=0, armL=(0, 0))),
             (9.6, 12.0, (-.6, 154.0), dict(armL=(-40, -60), armR=(0, 0), turn=-35))]
    for t0, t1, (x, y), gest in beats:
        elder.walk(F('4-4', t0), F('4-4', t1 - .6), (x, y, 48.05), z_hint=48.1, stride=8, lean=10)
        elder.pose(F('4-4', t1 - .3), **gest)
        hero.walk(F('4-4', t0 + .3), F('4-4', t1 - .3), (x + .9, y - 1.7, 48.05), z_hint=48.1, stride=8,
                  turn=gest.get('turn', 0) * .6)
    elder.pose(F('4-4', 12.0))
    hero.pose(F('4-4', 12.0))
    # 4-5 the look
    hp, ep = Vector((-.8, 153.0, 48.05)), Vector((.75, 153.4, 48.05))
    hero.cut(F('4-5'), loc=hp, rz=math.radians(180), turn=0, nod=0, lean=0, legL=0, legR=0, armL=(0, 0), armR=(0, 0))
    elder.cut(F('4-5'), loc=ep, rz=math.radians(180), turn=0, lean=0, legL=0, legR=0, armL=(0, 0), armR=(0, 0))
    hero.pose(F('4-5', .3))
    hero.pose(F('4-5', .9), rz=face_angle(hp, ep))
    hero.pose(F('4-5', 5.0))
    elder.pose(F('4-5', 1.0))
    elder.pose(F('4-5', 1.4), turn=-75, nod=-12)
    elder.pose(F('4-5', 2.4), turn=-80, armR=(-60, 25))
    elder.pose(F('4-5', 3.6), turn=-80, armR=(-30, 25))
    elder.pose(F('4-5', 5.0))

    # 5-1 .. 5-4 platform
    walk_in = Vector((PLATFORM.x, PLATFORM.y - 5.2, 48.05))
    hero.cut(F('5-1'), loc=walk_in, rz=math.radians(180), turn=0, nod=0, lean=0, armL=(0, 0), armR=(0, 0))
    elder.cut(F('5-1'), loc=(PLATFORM.x - 4.2, PLATFORM.y - 4.6, 48.05), rz=face_angle((6, 158), PLATFORM),
              turn=0, nod=0, lean=8, armL=(0, 0), armR=(0, 0))
    hero.walk(F('5-1', .2), F('5-1', 3.4), (PLATFORM.x, PLATFORM.y - .1, ground(PLATFORM.x, PLATFORM.y - 1.4, 48.6)),
              z_hint=lambda p: 48.6, stride=7)
    hero.pose(F('5-1', 3.7), rz=0)
    hero.pose(F('5-1', 4.6), loc=(PLATFORM.x, PLATFORM.y, sit_z(SEAT_TOP)), legL=-90, legR=-90,
              armL=(-35, -10), armR=(-35, 10), lean=0)
    hero.pose(F('5-1', 6.0))
    hero.pose(F('5-2', 1.0), nod=12)
    hero.pose(F('5-4', 8.0), nod=12)
    elder.pose(F('5-2', 4.0))
    elder.pose(F('5-2', 5.0), nod=12, lean=0)
    elder.pose(F('5-4', 8.0))
    smith.cut(F('3-5') + 1, loc=off)

    # ---------- VFX placeholders
    def emit(name, color, strength, alpha=1.0):
        return material(name, color, .5, emit=strength, emit_color=color, alpha=alpha)
    # 2-2 sparks and steam
    m_spark = emit('FX_Spark', (1, .55, .12), 40)
    for hit_t in (1.0, 2.0, 3.0):
        for i in range(10):
            s = sphere('FX_Spark_%.0f_%d' % (hit_t, i), .035, m_spark, c_fx, ANVIL + Vector((0, 0, .03)), segs=8)
            d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(.3, 1.2))).normalized()
            f0 = F('2-2', hit_t)
            kf(s, f0, location=ANVIL + Vector((0, 0, .03)))
            kf(s, f0 + 9, location=ANVIL + d * random.uniform(.5, 1.0) + Vector((0, 0, -.25)))
            show(s, f0, f0 + 9)
    m_steam = emit('FX_Steam', (.95, .95, .95), 1.5, alpha=.35)
    steam = cylinder('FX_Steam_Column', .3, 1.0, m_steam, c_fx, (0, 0, .5), r2=.6, loc=BARREL)
    show(steam, F('2-2', 3.2), F('2-2', 5.0) - 1)
    kf(steam, F('2-2', 3.2), scale=(.5, .5, .2))
    kf(steam, F('2-2', 5.0) - 1, scale=(1.4, 1.4, 1.8))
    # 2-5 light streak, pillar, shockwave
    m_light = emit('FX_Spirit_Light', (1, .93, .7), 60)
    streak = sphere('FX_Light_Streak', 2.2, m_light, c_fx, segs=24)
    path = [(2.5, (55, 262, 175)), (3.6, (40, 170, 120)), (4.8, (18, 70, 55)), (5.6, (4, 10, 12)), (6.0, DAIS)]
    for t, p in path:
        kf(streak, F('2-5', t), location=Vector(p))
    show(streak, F('2-5', 2.5), F('2-5', 6.0), (1, 1, 1))
    kf(streak, F('2-5', 2.5), scale=(1, 1, 1))
    kf(streak, F('2-5', 5.0), scale=(.8, .8, .8))
    kf(streak, F('2-5', 6.0), scale=(.5, .5, .5))
    pillar = cylinder('FX_Light_Pillar', 1.4, 400, m_light, c_fx, (0, 0, 200), loc=DAIS)
    show(pillar, F('2-5', 6.0), F('2-5', 9.5))
    kf(pillar, F('2-5', 6.0), scale=(.3, .3, 1))
    kf(pillar, F('2-5', 6.4), scale=(1.2, 1.2, 1))
    kf(pillar, F('2-5', 8.0), scale=(.8, .8, 1))
    kf(pillar, F('2-5', 9.5), scale=(.05, .05, 1))
    m_wave = emit('FX_Shockwave', (1, .9, .65), 25, alpha=.8)
    wave = torus('FX_Shockwave_Ring', 1.0, .12, m_wave, c_fx, DAIS + Vector((0, 0, .3)))
    show(wave, F('2-5', 6.0), F('2-5', 8.2))
    kf(wave, F('2-5', 6.0), scale=(1, 1, 1))
    kf(wave, F('2-5', 8.2), scale=(22, 22, 4))
    key_mat(m_wave, 'Alpha', F('2-5', 6.0), .9)
    key_mat(m_wave, 'Alpha', F('2-5', 8.2), 0.0)
    flash_d = bpy.data.lights.new('FX_Impact_Flash', 'POINT')
    flash_d.color = (1, .92, .7)
    flash_d.shadow_soft_size = 1.0
    flash = bpy.data.objects.new('FX_Impact_Flash', flash_d)
    flash.location = DAIS + Vector((0, 0, 3))
    c_fx.objects.link(flash)
    for f, e in ((0, 0), (F('2-5', 5.5), 0), (F('2-5', 6.1), 60000), (F('2-5', 9.5), 6000), (F('3-1', 0) - 1, 0),
                 (F('3-1', 0), 0)):
        flash_d.energy = e
        flash_d.keyframe_insert('energy', frame=f)
    # 5-2 array rings, spirit motes, seedlings lifting
    m_ring = emit('FX_Array_Ring', (.1, 1, .55), 0)
    for i, rr in enumerate((1.03, 1.62, 2.2)):
        ring = torus('FX_Array_Ring_%d' % i, rr, .035, m_ring if i == 0 else m_ring.copy(), c_fx,
                     (PLATFORM.x, PLATFORM.y, 48.52))
        m = ring.data.materials[0]
        key_mat(m, 'Emission Strength', 0, 0.0)
        key_mat(m, 'Emission Strength', F('5-2', .8 + i * 1.3), 0.0)
        key_mat(m, 'Emission Strength', F('5-2', 1.4 + i * 1.3), 4.0)
        key_mat(m, 'Emission Strength', F('5-4', 8.0), 4.0)
    m_mote = emit('FX_Spirit_Mote', (.2, 1, .7), 6)
    centre = Vector((PLATFORM.x, PLATFORM.y, 49.5))
    mr = random.Random(5)
    for i in range(36):
        a = mr.uniform(0, math.tau)
        start = centre + Vector((math.cos(a) * mr.uniform(5, 10), math.sin(a) * mr.uniform(5, 10), mr.uniform(-1, 2.5)))
        t0 = mr.uniform(1.2, 5.5)
        mote = sphere('FX_Spirit_Mote_%02d' % i, .07, m_mote, c_fx, start, segs=8)
        f0, f1 = F('5-2', t0), F('5-2', t0 + 2.2)
        kf(mote, f0, location=start)
        kf(mote, f1, location=centre + Vector((0, 0, mr.uniform(-.2, .4))))
        show(mote, f0, f1)
    for o in seedlings:
        kf(o, 0, rotation_euler=(math.radians(-38), 0, 0))
        kf(o, F('5-2', 6.0), rotation_euler=(math.radians(-38), 0, 0))
        kf(o, F('5-2', 7.6), rotation_euler=(0, 0, 0))
    # 5-3 red light from a crack on the north face of the peak
    m_red = emit('FX_Secret_Realm_Crack', (1, .08, .03), 80)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, *_ = sc.ray_cast(dg, Vector((-8, PEAK.y + 150, 75)), Vector((0, -1, 0)))
    crack_at = loc if hit else PEAK + Vector((-8, 40, 75))
    crack = box('FX_Secret_Realm_Crack', (3.0, 2.0, 55), (0, 0, 0), m_red, c_fx)
    crack.location = crack_at + Vector((0, -.6, 0))
    crack.rotation_euler = (0, math.radians(8), 0)
    red_d = bpy.data.lights.new('FX_Crack_Red_Light', 'POINT')
    red_d.color, red_d.energy, red_d.shadow_soft_size = (1, .1, .05), 5.0e5, 6
    red = bpy.data.objects.new('FX_Crack_Red_Light', red_d)
    red.location = crack_at + Vector((0, 14, 0))
    c_fx.objects.link(red)

    # ---------- cameras (one per shot; sub-cuts get extra cameras under the same shot marker)
    camera('1-1', 0, [(0, (0, -150, 92), (0, 260, 105), 35), (8, (0, -28, 86), (0, 260, 100), 35)])
    camera('1-2', 0, [(0, (-7.5, 34, 1.4), (-20, 50, 3), 22), (2, (-7.5, 34.5, 1.4), (-20, 50.5, 5), None),
                      (9, (-7.0, 37, 1.6), (-21.5, 52, 31), None), (10, (-7.0, 37.3, 1.6), (-21.5, 52, 32), None)])
    camera('1-3', 0, [(0, (-70, 95, 92), (0, 160, 48), 30), (8, (35, 190, 78), (0, 158, 48), None),
                      (10, (6, 102, 64), (0, 40, 10), None), (12, (4, 42, 14), (0, 0, 2), None)])
    camera('2-1', 0, [(0, (-.4, 1.3, 4.1), (.6, -4.4, .9), 26), (6, (2.9, -.4, 3.1), (0, -4.0, .9), None)])
    camera('2-2', 0, [(0, (9.55, 5.7, 1.75), (11.4, 7.85, 1.25), 32), (2.8, (9.55, 5.9, 1.75), (11.3, 8.1, 1.25), None),
                      (4.0, (9.6, 6.6, 1.75), (10.5, 10.2, 1.3), None), (5, (9.6, 6.8, 1.8), (10.5, 10.25, 1.5), None)])
    camera('2-3', 0, [(0, (-1.8, -5.6, 1.7), (-7.0, -6.6, 1.3), 30), (5, (-1.8, -9.8, 1.7), (-7.0, -11.0, 1.3), None)])
    camera('2-4', 0, [(0, (-.2, -9.8, 1.6), (-1.0, -2.2, 1.0), 30), (8, (-.5, -8.5, 1.45), (-1.2, -2.3, 1.0), None)])
    camera('2-5', 0, [(0, (7, -21, 3.2), (0, 2, 6), 24), (2.5, (7, -21.2, 3.2), (4, 60, 45), None),
                      (4.6, (7, -21.4, 3.2), (6, 30, 20), None), (6.0, (7, -21.6, 3.2), (0, -2, 3), None),
                      (11, (6.5, -20.5, 3.0), (0, -2.5, 3), None)])
    camera('3-1', 0, [(0, (.8, -7.4, 1.75), (-.1, -3.3, 1.7), 40), (6, (.6, -6.4, 1.8), (-.15, -3.3, 1.75), None)])
    camera('3-2', 0, [(0, (1.8, -6.8, 1.4), (0, 4.6, 5.6), 28), (1.6, (1.8, -6.8, 1.4), (0, 4.4, 5.2), None),
                      (2.4, (1.8, -6.8, 1.4), (0, 3.0, 2.0), None), (6, (1.6, -6.2, 1.45), (0, 2.6, 2.0), None)])
    camera('3-3', 0, [(0, (2.6, -7.2, 1.6), (0, -3.3, 1.3), 35), (2.6, (2.4, -6.8, 1.6), (0, -3.3, 1.3), None)], 'a')
    camera('3-3', 2.7, [(2.7, (-2.3, -.2, 1.7), (.3, -4.0, 1.3), 35), (5.3, (-2.1, -.5, 1.7), (.3, -4.0, 1.3), None)], 'b')
    camera('3-3', 5.4, [(5.4, (2.5, -6.2, 1.7), (1.2, -3.3, 1.6), 50), (8, (2.4, -5.9, 1.7), (1.2, -3.3, 1.6), None)], 'c')
    camera('3-4', 0, [(0, (-3.0, -10.5, 2.4), (4.5, .5, 1.6), 30), (3.8, (-2.4, -9.8, 2.2), (4.0, -.5, 1.5), None),
                      (7, (-1.0, -7.6, 1.8), (.7, -3.3, 1.45), 40)])
    camera('3-5', 0, [(0, (1.05, -5.0, 1.65), (.6, -3.3, 1.5), 55), (8, (.85, -4.55, 1.6), (.6, -3.3, 1.45), None)])
    camera('4-1', 0, [(0, (16, 27, 13), (0, 37, 8), 35), (2.9, (15.5, 28, 13), (0, 38.5, 9), None)], 'a')
    camera('4-1', 3.0, [(3.0, (6.0, 63.5, stair_z(64) + 1.6), (0, 66.5, stair_z(66) + 1.0), 32),
                        (5.5, (6.0, 66, stair_z(66) + 1.6), (0, 68.5, stair_z(68) + 1.0), None)], 'b')
    camera('4-1', 5.6, [(5.6, (.4, 85.5, stair_z(86) + 2.6), (0, 95, stair_z(95) + 1.2), 30),
                        (8, (.4, 87.5, stair_z(88) + 2.6), (0, 97, stair_z(97) + 1.2), None)], 'c')
    camera('4-2', 0, [(0, (2.6, 132.0, 48.45), (0, 135.5, 51.4), 20), (6, (2.4, 132.4, 48.4), (0, 135.5, 52.4), None)])
    camera('4-3', 0, [(0, (2.0, 133.0, 49.4), (0, SECT.y - 14.6, 49.3), 28), (4, (1.9, 133.3, 49.4), (0, SECT.y - 14, 49.3), None)])
    camera('4-4', 0, [(0, (2.6, 140.2, 50.0), (-9, 160, 48.8), 26), (3.2, (2.2, 142.5, 50.0), (-10.5, 161, 48.6), None),
                      (5.6, (1.6, 144.5, 50.2), (11, 149.4, 49.3), None), (8.6, (-.6, 148.0, 50.6), (0, 160, 52), None),
                      (12, (-3.0, 153.5, 50.4), (-13, 174, 50), None)])
    camera('4-5', 0, [(0, (.3, 157.4, 49.75), (0, 153.2, 49.5), 38), (5, (.3, 156.8, 49.7), (0, 153.2, 49.5), None)])
    cam51 = [(0, (16.5, 154.0, 51.4), (PLATFORM.x, PLATFORM.y - 1, 48.9), 30), (6, (16.0, 155.0, 51.1), (PLATFORM.x, PLATFORM.y, 49.0), None)]
    camera('5-1', 0, cam51)
    camera('5-2', 0, [(0, (13.6, 158.6, 50.0), (PLATFORM.x, PLATFORM.y, 49.2), 32), (6, (14.4, 160.4, 50.4), (PLATFORM.x, PLATFORM.y, 49.2), None)], 'a')
    camera('5-2', 6.0, [(6.0, (-10.6, SECT.y + 6.4, 48.75), (-10.6, SECT.y + 9.25, 48.2), 40), (8, (-10.6, SECT.y + 6.6, 48.7), (-10.6, SECT.y + 9.25, 48.25), None)], 'b')
    camera('5-3', 0, [(0, (15.0, 155.0, 51.6), (PLATFORM.x, PLATFORM.y, 48.8), 30), (2.5, (55, 105, 115), (0, 170, 55), None),
                      (5.0, (-95, 95, 200), (0, 230, 95), None), (8, (-215, 420, 165), (0, 262, 85), None)])
    camera('5-4', 0, [(0, (0, -95, 112), (0, 262, 128), 30), (6.0, (0, -80, 110), (0, 262, 126), None)], 'a')
    camera('5-4', 6.0, [(6.0, cam51[0][1], cam51[0][2], 30), (8, cam51[0][1], cam51[0][2], None)], 'b')

    # interpolation: blocky linear for performance/FX, eased bezier for camera moves
    for o in bpy.data.objects:
        if not o.name.startswith('CAM_'):
            set_interp(o, 'LINEAR')
    for d in list(bpy.data.lights) + list(bpy.data.materials) + [world]:
        set_interp(d, 'LINEAR')
        if getattr(d, 'node_tree', None):
            set_interp(d.node_tree, 'LINEAR')
    for d in bpy.data.cameras:
        set_interp(d, 'CONSTANT')
    sc.camera = bpy.data.objects['CAM_1-1']

    # ---------- render settings (3D pass)
    r = sc.render
    r.engine = 'BLENDER_EEVEE'
    r.resolution_x, r.resolution_y, r.resolution_percentage = *RES, 100
    r.image_settings.file_format = 'JPEG'
    r.image_settings.quality = 90
    r.use_overwrite = False
    r.use_placeholder = True
    r.filepath = rel(frames_dir / 'f_####', out_dir)
    sc.eevee.taa_render_samples = 8
    for attr, v in (('use_raytracing', False), ('use_shadows', True), ('shadow_ray_count', 1), ('shadow_step_count', 4)):
        if hasattr(sc.eevee, attr):
            setattr(sc.eevee, attr, v)
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass

    build_edit_scene(sc, frames_dir, out_dir)


def rel(path, out_dir):
    import os
    return '//' + os.path.relpath(str(path), str(out_dir)).replace(os.sep, '/')


def cjk_font():
    for p in ('/System/Library/Fonts/STHeiti Medium.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc',
              Path(bpy.utils.resource_path('LOCAL')) / 'datafiles/fonts/Noto Sans CJK Regular.woff2'):
        if Path(p).exists():
            try:
                return bpy.data.fonts.load(str(p), check_existing=True)
            except Exception:
                continue
    return None


def text_strip(sed, name, text, ch, f0, f1, size, loc, anchor=('CENTER', 'BOTTOM'), color=(1, 1, 1, 1), box=True,
               font=None):
    s = sed.strips.new_effect(name=name, type='TEXT', channel=ch, frame_start=f0, length=f1 - f0)
    s.text = text
    s.font_size = size
    s.location = loc
    s.color = color
    for k, v in (('anchor_x', anchor[0]), ('anchor_y', anchor[1]), ('alignment_x', anchor[0]),
                 ('use_shadow', True), ('use_box', box), ('box_color', (0, 0, 0, .55)), ('box_margin', .012),
                 ('wrap_width', .95)):
        try:
            setattr(s, k, v)
        except Exception:
            pass
    if font:
        s.font = font
    s.blend_type = 'ALPHA_OVER'
    return s


def build_edit_scene(sc3d, frames_dir, out_dir):
    ed = bpy.data.scenes.new('AnimaticEdit')
    ed.render.fps = FPS
    ed.frame_start, ed.frame_end = 0, FRAME_END
    ed.render.resolution_x, ed.render.resolution_y, ed.render.resolution_percentage = *RES, 100
    ed.view_settings.view_transform = 'Standard'
    sed = ed.sequence_editor_create()
    font = cjk_font()
    img = sed.strips.new_image(name='Animatic3D_Frames', filepath=str(frames_dir / 'f_0000.jpg'), channel=1,
                               frame_start=0)
    img.directory = rel(frames_dir, out_dir) + '/'
    for f in range(1, FRAME_END + 1):
        img.elements.append('f_%04d.jpg' % f)
    # fades: 1-1 from black, 5-4 title fade-out then hard cut to the 5-1 set-up
    black = sed.strips.new_effect(name='Fade_In_1-1', type='COLOR', channel=2, frame_start=0, length=F('1-1', 2.5))
    black.color = (0, 0, 0)
    black.blend_type = 'ALPHA_OVER'
    for f, a in ((0, 1.0), (F('1-1', .4), 1.0), (F('1-1', 2.5) - 1, 0.0)):
        black.blend_alpha = a
        black.keyframe_insert('blend_alpha', frame=f)
    out = sed.strips.new_effect(name='Fade_Out_5-4', type='COLOR', channel=2, frame_start=F('5-4', 4.8),
                                length=F('5-4', 6.25) - F('5-4', 4.8))
    out.color = (0, 0, 0)
    out.blend_type = 'ALPHA_OVER'
    for f, a in ((F('5-4', 4.8), 0.0), (F('5-4', 5.7), 1.0), (F('5-4', 6.25) - 1, 1.0)):
        out.blend_alpha = a
        out.keyframe_insert('blend_alpha', frame=f)
    # title card placeholder
    text_strip(sed, 'Title_Placeholder', '修先溝八', 5, F('5-4', .8), F('5-4', 5.6), 110, (.5, .55),
               ('CENTER', 'CENTER'), box=False, font=font)
    text_strip(sed, 'Title_Sub_Placeholder', '序章〈凌雲重開〉（標題字卡暫代）', 6, F('5-4', 1.4), F('5-4', 5.6), 30, (.5, .41),
               ('CENTER', 'CENTER'), box=False, font=font)
    # per-shot slate + subtitles
    for sid, sec, label, subs in SHOTS:
        text_strip(sed, 'Slate_' + sid, '%s  %s（%ds）' % (sid, label, sec), 3, F(sid), F(sid) + sec * FPS, 22,
                   (.012, .93), ('LEFT', 'TOP'), font=font)
        for i, (t0, t1, line) in enumerate(subs):
            text_strip(sed, 'Sub_%s_%d' % (sid, i), line, 4, F(sid, t0), F(sid, t1), 26, (.5, .07), font=font,
                       color=(1, .96, .82, 1))
    for m in sc3d.timeline_markers:
        ed.timeline_markers.new(m.name, frame=m.frame)
    r = ed.render
    r.use_stamp = True
    for k in ('use_stamp_date', 'use_stamp_render_time', 'use_stamp_camera', 'use_stamp_lens', 'use_stamp_scene',
              'use_stamp_filename', 'use_stamp_memory', 'use_stamp_hostname', 'use_stamp_sequencer_strip',
              'use_stamp_frame_range'):
        setattr(r, k, False)
    for k in ('use_stamp_time', 'use_stamp_frame', 'use_stamp_marker', 'use_stamp_labels'):
        setattr(r, k, True)
    r.use_stamp_note = False
    text_strip(sed, 'Version_Tag', '%s｜24fps｜暫代畫面與聲音' % OUT_NAME, 5, 0, FRAME_END + 1, 14, (.988, .985),
               ('RIGHT', 'TOP'), font=font, color=(1, 1, 1, .8))
    r.stamp_font_size = 15
    r.stamp_background = (0, 0, 0, .6)
    try:
        r.image_settings.media_type = 'VIDEO'
    except Exception:
        pass
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'MEDIUM'
    r.ffmpeg.ffmpeg_preset = 'GOOD'
    r.ffmpeg.audio_codec = 'NONE'
    r.use_file_extension = True
    r.filepath = '//%s_preview_960x540' % OUT_NAME
    return ed


# ------------------------------------------------------------- temp audio (v002+)
# Placeholder sound only: macOS `say` voices for narration/dialogue, numpy-synthesised SFX / ambience / music stems.
SR = 44100
VOICES = {'旁白': ('Meijia', 175), '掌門': ('Grandpa (中文（台灣）)', 185), '鐵匠': ('Eddy (中文（台灣）)', 200)}
LINE_RE = re.compile(r'^(?P<who>[^（：]+)(?:（(?P<how>[^）]*)）)?：「(?P<text>.*)」$')


def T(shot, t=0.0):
    return F(shot, t) / FPS


def _synth():
    import numpy as np
    rng = np.random.default_rng(1)
    total = (FRAME_END + 1) / FPS

    def tt(d):
        return np.arange(int(d * SR)) / SR

    def band(d, lo, hi):
        n = int(d * SR)
        spec = np.fft.rfft(rng.standard_normal(n))
        fr = np.fft.rfftfreq(n, 1 / SR)
        spec[(fr < lo) | (fr > hi)] = 0
        x = np.fft.irfft(spec, n)
        return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)

    def env(x, a=.01, r=.05):
        n = len(x)
        e = np.ones(n, np.float32)
        na, nr = min(n, int(a * SR)), min(n, int(r * SR))
        if na:
            e[:na] = np.linspace(0, 1, na)
        if nr:
            e[n - nr:] *= np.linspace(1, 0, nr)
        return x * e

    def decay(d, tau):
        return np.exp(-tt(d) / tau).astype(np.float32)

    def tone(d, f, tau=None):
        x = np.sin(2 * np.pi * f * tt(d)).astype(np.float32)
        return x * decay(d, tau) if tau else x

    def sweep(d, f0, f1):
        f = np.geomspace(f0, f1, int(d * SR))
        return np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)

    def ding(f=1850, d=1.4):
        return sum(a * tone(d, f * k, tau) for k, a, tau in ((1, 1, .5), (2.76, .5, .25), (5.4, .25, .12), (8.9, .1, .06)))

    def bell(f, d=2.5):
        return sum(a * tone(d, f * k, tau) for k, a, tau in ((1, 1, 1.2), (2.0, .35, .6), (3.0, .15, .3)))

    def thump(f=55, d=.3, tau=.07):
        return np.sin(2 * np.pi * np.cumsum(np.linspace(f * 1.6, f, int(d * SR))) / SR).astype(np.float32) * decay(d, tau)

    def knock(d=.15):
        return band(d, 150, 1200) * decay(d, .03)

    def boom(d=3.0):
        return .8 * sweep(d, 90, 28) * decay(d, .7) + .6 * band(d, 20, 300) * decay(d, .5)

    def whoosh(d, lo=300, hi=2500):
        x = band(d, lo, hi)
        return x * np.sin(np.linspace(0, np.pi, len(x))).astype(np.float32) ** 2

    def wind(d, gain_lfo=.4):
        x = band(d, 120, 900)
        lfo = 1 - gain_lfo + gain_lfo * np.sin(2 * np.pi * .13 * tt(d) + rng.uniform(0, 6)).astype(np.float32)
        return env(x * lfo, 1.0, 1.0)

    def creak(d=.7):
        t_ = tt(d)
        f = 300 + 90 * np.sin(2 * np.pi * 7 * t_) + 30 * rng.standard_normal(len(t_)).cumsum() / np.sqrt(len(t_))
        ph = np.cumsum(f) / SR
        x = sum(np.sin(2 * np.pi * k * ph) / k for k in range(1, 6)).astype(np.float32)
        return env(x * .5, .05, .25)

    def pad(d, freqs, a=1.5):
        x = sum(np.sin(2 * np.pi * f * tt(d)) + .5 * np.sin(2 * np.pi * f * 1.003 * tt(d)) for f in freqs)
        return env((x / len(freqs)).astype(np.float32), a, 1.0)

    class Stem:
        def __init__(self):
            self.a = np.zeros(int(total * SR) + SR, np.float32)

        def add(self, t, sig, gain=1.0):
            i = int(t * SR)
            n = max(0, min(len(sig), len(self.a) - i))
            self.a[i:i + n] += sig[:n] * gain

    amb, sfx, mus = Stem(), Stem(), Stem()
    # scene 1: wind over the peak
    amb.add(0, env(wind(30.5), 2.5, 1.0), .35)
    sfx.add(T('1-3', 8.5), whoosh(3.5, 200, 1800), .5)
    # scene 2: town morning
    for k in range(70):
        t = rng.uniform(T('2-1'), T('2-5', 1.0))
        c = sweep(.07, rng.uniform(2300, 3000), rng.uniform(3600, 4600)) * decay(.07, .03)
        for j in range(rng.integers(2, 5)):
            amb.add(t + j * .11, c, .12)
    t = T('2-1', .4)
    while t < T('2-5', .5):
        if not (T('2-2') - .3 < t < T('2-3')):
            amb.add(t, ding(1700, 1.0), .07)    # distant smithing
        t += 1.15
    for h in (1.0, 2.0, 3.0):
        sfx.add(T('2-2', h), ding(), .55)
    sfx.add(T('2-2', 3.2), env(band(1.8, 2500, 9000), .02, 1.2), .3)
    m = band(5.2, 250, 1800)
    amb.add(T('2-3'), env(m * (.6 + .4 * np.abs(np.sin(2 * np.pi * 1.7 * tt(5.2)))).astype(np.float32), .5, .5), .14)
    # 2-5 rumble -> streak -> impact -> sudden silence
    r = band(6.0, 25, 110) + .5 * tone(6.0, 38)
    sfx.add(T('2-5', .5), r * np.linspace(.1, 1, len(r)).astype(np.float32), .45)
    w = band(3.5, 400, 4000)
    sfx.add(T('2-5', 2.5), w * np.linspace(0, 1, len(w)).astype(np.float32) ** 2, .35)
    sfx.add(T('2-5', 6.0), boom(2.2), .9)
    # 3-1 heartbeat, 3-2 landing, 3-4 sword draw, 3-5 grip
    t = T('3-1', .3)
    while t < T('3-1', 5.6):
        sfx.add(t, thump(52, .25), .8)
        sfx.add(t + .22, thump(48, .25), .55)
        t += .85
    amb.add(T('3-2'), env(wind(31.0), 1.5, 1.0), .06)
    sfx.add(T('3-2', 1.6), whoosh(.6, 300, 2500), .3)
    sfx.add(T('3-2', 2.3), thump(70, .35, .08) + .4 * knock(.35), .8)
    sfx.add(T('3-2', 2.7), env(band(.35, 1500, 6000), .01, .2), .25)
    sfx.add(T('3-4', 4.0), band(.7, 4000, 12000) * decay(.7, .2) + .3 * sweep(.7, 2800, 5200) * decay(.7, .3), .35)
    sfx.add(T('3-5', 4.0), knock(.12), .5)
    # scene 4: climbing, gate, kick, tour
    amb.add(T('4-1'), env(wind(14.0), 1.0, 1.0), .3)
    for t0, t1 in ((0.04, 2.9), (3.0, 5.5), (5.6, 8.0)):
        t = T('4-1', t0)
        while t < T('4-1', t1):
            sfx.add(t, knock(.08), .12)
            t += .27
    amb.add(T('4-2', .3), env(wind(5.5, .7), .8, 1.5), .45)
    for c in (.8, 2.4, 4.0):
        sfx.add(T('4-2', c), creak(.7), .22)
    for t in (.3, .55, .8, 1.05, 1.3):
        sfx.add(T('4-3', t), knock(.15) + .5 * thump(90, .15, .03), .45)
    sfx.add(T('4-3', 2.05), band(.6, 60, 2500) * decay(.6, .12) + thump(45, .6, .12), 1.0)
    sfx.add(T('4-3', 2.15), creak(1.0), .2)
    amb.add(T('4-4'), env(wind(17.0, .3), 1.0, 1.0), .15)
    for k in range(25):
        t = rng.uniform(T('4-4'), T('5-1'))
        amb.add(t, sweep(.07, 2600, 4200) * decay(.07, .03), .06)
    # scene 5: array chimes, motes, pull-back, title
    for i, f in enumerate((660, 880, 1046.5)):
        sfx.add(T('5-2', 1.4 + i * 1.3), bell(f), .28)
    sfx.add(T('5-2', 1.2), env(band(5.5, 5000, 11000), 1.5, 2.0), .05)
    sfx.add(T('5-3', .2), whoosh(3.0, 150, 2000), .55)
    sfx.add(T('5-3', 4.0), band(4.0, 25, 120) * decay(4.0, 2.0), .4)
    amb.add(T('5-4'), env(wind(5.6), 1.0, 1.0), .2)
    for i, f in enumerate((1318.5, 1760.0)):
        sfx.add(T('5-4', 6.4 + i * .12), bell(f, 1.5), .22)
    # music builds from 5-1 to the title, fades with the picture at 5-4 4.8-5.7 s
    d = T('5-4', 5.8) - T('5-1')
    mus.add(T('5-1'), pad(d, (110, 164.81)), .5)
    mus.add(T('5-2'), pad(T('5-4', 5.8) - T('5-2'), (220, 261.63, 329.63), 2.0), .35)
    mus.add(T('5-3'), pad(T('5-4', 5.8) - T('5-3'), (659.26, 880, 987.77), 2.5), .18)
    t = T('5-3', .5)
    while t < T('5-4', .8):
        mus.add(t, thump(60, .35, .1), .5)
        t += .5
    mus.add(T('5-4', .8), boom(3.0), .6)
    for f in (440, 554.37, 659.26, 880):
        mus.add(T('5-4', .8), bell(f, 4.0), .12)
    keys = [(0, 0), (T('5-1'), 0), (T('5-1', 3), .45), (T('5-2'), .55), (T('5-3'), .75), (T('5-3', 8), 1.0),
            (T('5-4', 4.8), .9), (T('5-4', 5.7), 0), (total + 1, 0)]
    tx = np.arange(len(mus.a)) / SR
    mus.a *= np.interp(tx, [k[0] for k in keys], [k[1] for k in keys]).astype(np.float32)
    # 2-5 "突然靜音": hard mute everything from 8.0 s to the end of the shot
    a, b = int(T('2-5', 8.0) * SR), int(T('3-1') * SR)
    for s in (amb, sfx, mus):
        s.a[a:b] = 0
    return {'Amb': amb.a, 'SFX': sfx.a, 'Music': mus.a}


def _write_wav(path, x):
    import numpy as np, wave
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _wav_seconds(path):
    import wave
    with wave.open(str(path), 'rb') as w:
        return w.getnframes() / w.getframerate()


def build_audio(ed, out_dir):
    import subprocess, shutil as sh
    adir = out_dir / 'audio'
    adir.mkdir(exist_ok=True)
    sed = ed.sequence_editor
    stems = _synth()
    for i, (name, x) in enumerate(stems.items()):
        p = adir / ('%s_temp_stem.wav' % name)
        _write_wav(p, x)
        s = sed.strips.new_sound(name='Audio_%s' % name, filepath=str(p), channel=7 + i, frame_start=0)
        s.volume = {'Amb': .9, 'SFX': 1.0, 'Music': .8}[name]
    have_say = sh.which('say') is not None
    timing = []
    sub_starts = sorted((F(sid, t0), sid, i) for sid, _, _, subs in SHOTS for i, (t0, _, _) in enumerate(subs))
    ch = 10
    for sid, sec, _, subs in SHOTS:
        for i, (t0, t1, line) in enumerate(subs):
            m = LINE_RE.match(line)
            if not m or m['who'] not in VOICES:
                continue
            voice, rate = VOICES[m['who']]
            soft = m['how'] == '輕聲'
            text = m['text']
            row = dict(shot=sid, line=line, speaker=m['who'], voice=voice, start_s=round(T(sid, t0), 2),
                       subtitle_s=[t0, t1], shot_length_s=sec)
            if not have_say:
                row['status'] = 'skipped: macOS say not available'
                timing.append(row)
                continue
            p = adir / ('VO_%s_%d.wav' % (sid, i))
            subprocess.run(['say', '-v', voice, '-r', str(150 if soft else rate), '-o', str(p), '--file-format=WAVE',
                            '--data-format=LEI16@%d' % SR, text], check=True)
            dur = _wav_seconds(p)
            s = sed.strips.new_sound(name='VO_%s_%d' % (sid, i), filepath=str(p), channel=ch,
                                     frame_start=F(sid, t0))
            s.volume = .75 if soft else 1.0
            ch = 10 if ch == 11 else 11   # alternate so back-to-back lines never collide
            end = t0 + dur
            nxt = [f for f, *_ in sub_starts if f > F(sid, t0)]
            next_start = nxt[0] if nxt else FRAME_END + 1
            st = sed.strips.get('Sub_%s_%d' % (sid, i))
            want = min(F(sid, end + .15), next_start - 1)
            if st and want > st.right_handle:
                st.right_handle = want   # keep the subtitle up while the line is still being read
            row.update(voice_s=round(dur, 2), ends_at_shot_s=round(end, 2),
                       over_subtitle_s=round(max(0, end - t1), 2), over_shot_s=round(max(0, end - sec), 2),
                       overlaps_next_line=F(sid, end) > next_start)
            timing.append(row)
    r = ed.render
    r.ffmpeg.audio_codec = 'AAC'
    r.ffmpeg.audio_bitrate = 160
    r.ffmpeg.audio_channels = 'STEREO'
    r.ffmpeg.audio_mixrate = 48000
    short = [s.name for s in sed.strips if s.type == 'SOUND' and s.frame_final_duration < FPS // 2]
    assert not short, 'sound strips failed to load: %s' % short
    (adir / 'audio_timing.json').write_text(json.dumps(timing, ensure_ascii=False, indent=2), encoding='utf-8')
    over = [t for t in timing if t.get('over_shot_s', 0) > 0 or t.get('overlaps_next_line')]
    print('AUDIO lines', len(timing), 'overrunning', [(t['shot'], t['voice_s'], t['over_shot_s']) for t in over])
    return timing


# ========================================================================= main
def next_version_dir():
    base = MODELS / 'PrologueAnimatic'
    n = 1
    while (base / ('v%03d' % n)).exists():
        n += 1
    return base / ('v%03d' % n), 'v%03d' % n


def shot_table():
    rows = []
    for sid, sec, label, subs in SHOTS:
        cams = [c['camera'] for c in CAMS if c['shot'] == sid]
        rows.append(dict(shot=sid, seconds=sec, frame_start=F(sid), frame_end=F(sid) + sec * FPS - 1,
                         timecode_start='%d:%02d' % divmod(F(sid) // FPS, 60), label=label, cameras=cams,
                         lines=[s[2] for s in subs]))
    return rows


def main_build():
    global OUT_NAME
    if '--out' in ARGS:
        out = Path(ARGS[ARGS.index('--out') + 1]).resolve()
        out.mkdir(parents=True, exist_ok=True)
        ver = 'dev'
        frames = out / 'frames'
    else:
        out, ver = next_version_dir()
        out.mkdir(parents=True)
        frames = ROOT / 'work/PrologueAnimatic' / (ver + '_frames')
    if '--frames' in ARGS:  # reuse an identical earlier 3D render, e.g. work/PrologueAnimatic/v001_frames
        frames = (ROOT / ARGS[ARGS.index('--frames') + 1]).resolve()
    OUT_NAME = 'PrologueAnimatic_' + ver
    build(out, frames)
    timing = [] if '--no-audio' in ARGS else build_audio(bpy.data.scenes['AnimaticEdit'], out)
    blend = out / (OUT_NAME + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), relative_remap=True, compress=True)
    info = dict(asset='PrologueAnimatic', name_zh='序章動態分鏡〈凌雲重開〉', version=ver, source_doc=STORY_DOC,
                fps=FPS, frame_start=0, frame_end=FRAME_END, duration_s=(FRAME_END + 1) / FPS,
                resolution=list(RES), scenes=['Animatic3D', 'AnimaticEdit'],
                frames_dir=str(frames.relative_to(ROOT)) if frames.is_relative_to(ROOT) else str(frames),
                linked_sources=sorted(set(SOURCES_USED.values())), instances=SOURCES_USED,
                shots=shot_table(), blender=bpy.app.version_string,
                world_layout_m=dict(town_origin=list(TOWN), stair=dict(y0=STAIR_Y0, y1=STAIR_Y1, z0=STAIR_Z0,
                                                                        z1=STAIR_Z1, steps=STAIR_STEPS, width=STAIR_W),
                                    plateau_origin=list(PLATEAU), sect_origin=list(SECT), peak_origin=list(PEAK),
                                    peak_scale=PEAK_SCALE),
                audio='none' if '--no-audio' in ARGS else dict(
                    note='placeholder: macOS say voices + numpy-synthesised stems', stems=['audio/Amb_temp_stem.wav',
                    'audio/SFX_temp_stem.wav', 'audio/Music_temp_stem.wav'], timing='audio/audio_timing.json',
                    voices={k: v[0] for k, v in VOICES.items()}))
    (out / 'animatic_info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print('BUILT', blend)
    if '--stills' in ARGS:
        render_stills(out)


def render_stills(out):
    sc = bpy.data.scenes['Animatic3D']
    d = out / 'stills'
    d.mkdir(exist_ok=True)
    only = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None
    marks = sorted(sc.timeline_markers, key=lambda m: m.frame)
    for i, m in enumerate(marks):
        end = marks[i + 1].frame - 1 if i + 1 < len(marks) else FRAME_END
        cam_name = m.camera.name
        if only and m.name not in only and cam_name[4:] not in only:
            continue
        for tag, f in (('a', m.frame + 3), ('b', (m.frame + end) // 2), ('c', end - 2)):
            if '--mid' in ARGS and tag != 'b':
                continue
            sc.frame_set(f)
            sc.camera = m.camera
            sc.render.filepath = str(d / ('%s_%s_f%04d.jpg' % (cam_name, tag, f)))
            sc.render.use_overwrite = True
            bpy.ops.render.render(write_still=True, scene=sc.name)
    print('STILLS', d)


def main_render():
    blend_dir = Path(bpy.data.filepath).parent
    if '--render-frames' in ARGS:
        sc = bpy.data.scenes['Animatic3D']
        if '--range' in ARGS:
            a, b = ARGS[ARGS.index('--range') + 1].split('-')
            sc.frame_start, sc.frame_end = int(a), int(b)
        bpy.ops.render.render(animation=True, scene=sc.name)
    if '--render-edit' in ARGS:
        ed = bpy.data.scenes['AnimaticEdit']
        bpy.ops.render.render(animation=True, scene=ed.name)
        final = blend_dir / ('%s_preview_960x540.mp4' % OUT_NAME)
        for p in blend_dir.glob('%s_preview_960x540?*.mp4' % OUT_NAME):  # Blender appends the frame range
            if not final.exists():
                p.rename(final)
        print('MOVIE', final)


OUT_NAME = 'PrologueAnimatic_dev'
if __name__ == '__main__':
    if any(a.startswith('--render-') for a in ARGS) and bpy.data.filepath:
        OUT_NAME = Path(bpy.data.filepath).stem
        main_render()
    elif '--stills-only' in ARGS and bpy.data.filepath:
        render_stills(Path(bpy.data.filepath).parent)
    else:
        main_build()
