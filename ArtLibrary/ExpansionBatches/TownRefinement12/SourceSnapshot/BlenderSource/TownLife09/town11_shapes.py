"""TownRoads11 design specs: road junction kit, stone bridge, railings, pond,
spawn altar and town archway. Run with TL_SPEC=town11_shapes.

Road tiles are 6 x 6 m with a 3 m carriageway and 0.25 m kerbs; connectors
sit at the middle of each open edge on the paving surface (z = 0.2 m), so
tiles snap edge-to-edge and line up with MountainStonePath (3 m wide).
"""
import math

import numpy as np

from town09_shapes import VIEWS, VIEW_PHRASE, Asset, beam, box, cyl, lathe, merge, rod, tube  # noqa: F401
from town10_shapes import sphere, xf
import town10_shapes as T10

PALETTE = dict(T10.PALETTE, **{
    'paving':  ((.27, .30, .30), (140, 148, 148)),
    'kerb':    ((.40, .41, .38), (170, 170, 162)),
    'soil':    ((.16, .11, .07), (110, 90, 72)),
    'lotus':   ((.75, .32, .40), (230, 160, 170)),
    'pad':     ((.08, .25, .08), (70, 130, 70)),
    'jade':    ((.10, .42, .30), (90, 170, 140)),
    'gold':    ((.60, .42, .12), (214, 180, 96)),
})

TILE, ROAD, KERB, TOP = 6.0, 3.0, .25, .2


# ------------------------------------------------------------- road helpers
def _stones(A, centres, z_of, tilt_of=None, size=.46):
    """Lay paving stones (merged into a few meshes) at the given xy centres."""
    rng = np.random.default_rng(len(centres))
    geos = []
    for (x, y) in centres:
        s = size * rng.uniform(.9, 1.0)
        g = box((0, 0, 0), (s, s * rng.uniform(.85, 1.0), .05), rz=rng.uniform(-.06, .06))
        rx = tilt_of(x, y) if tilt_of else 0
        geos.append(xf(g, rot=(rx, 0, 0), t=(x, y, z_of(x, y) - .02 + rng.uniform(-.006, .006))))
    for k in range(0, len(geos), 160):
        A.add('Road_Paving_Stones', merge(geos[k:k + 160]), 'paving', bevel=False)


def _grid(inside, step=.5):
    pts = []
    for x in np.arange(-TILE / 2 + step / 2, TILE / 2, step):
        for y in np.arange(-TILE / 2 + step / 2, TILE / 2, step):
            if inside(x, y):
                pts.append((x, y))
    return pts


def _verge(A):
    # inset 1 cm so its sides never share a plane with the road bed (avoids z-fighting)
    A.add('Road_Verge_Ground', box((0, 0, .075), (TILE - .02, TILE - .02, .15)), 'soil', bevel=False)


def _kerb(A, a, b, z=TOP):
    A.add('Road_Kerb', beam((*a, z - .07), (*b, z - .07), KERB, .2), 'kerb')


def _arm_bed(A, name, c, s):
    A.add(name, box(c, s), 'stone', bevel=False)


def road_t():
    A = Asset()
    _verge(A)
    h = ROAD / 2
    _arm_bed(A, 'Road_Bed_Main', (0, 0, .09), (TILE, ROAD, .18))
    _arm_bed(A, 'Road_Bed_Branch', (0, (TILE / 2 + h) / 2, .09), (ROAD, TILE / 2 - h, .18))
    _stones(A, _grid(lambda x, y: abs(y) < h - .05 or (y > 0 and abs(x) < h - .05)), lambda x, y: TOP)
    _kerb(A, (-TILE / 2, -h - KERB / 2), (TILE / 2, -h - KERB / 2))
    for sx in (-1, 1):
        _kerb(A, (sx * TILE / 2, h + KERB / 2), (sx * (h + KERB / 2), h + KERB / 2))
        _kerb(A, (sx * (h + KERB / 2), h + KERB / 2), (sx * (h + KERB / 2), TILE / 2))
    return A


def road_cross():
    A = Asset()
    _verge(A)
    h = ROAD / 2
    _arm_bed(A, 'Road_Bed_EW', (0, 0, .09), (TILE, ROAD, .18))
    for sy in (-1, 1):
        _arm_bed(A, 'Road_Bed_NS', (0, sy * (TILE / 2 + ROAD / 2) / 2, .09), (ROAD, TILE / 2 - ROAD / 2, .18))
    _stones(A, _grid(lambda x, y: abs(y) < h - .05 or abs(x) < h - .05), lambda x, y: TOP)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _kerb(A, (sx * TILE / 2, sy * (h + KERB / 2)), (sx * (h + KERB / 2), sy * (h + KERB / 2)))
            _kerb(A, (sx * (h + KERB / 2), sy * (h + KERB / 2)), (sx * (h + KERB / 2), sy * TILE / 2))
    A.add('Crossroad_Centre_Stone', cyl((0, 0, TOP - .03), .7, .05, 24), 'kerb', smooth=True)
    return A


def road_curve():
    """90 degree bend from the -Y edge to the +X edge, centreline radius 3 m about (3, -3)."""
    A = Asset()
    _verge(A)
    cx, cy = TILE / 2, -TILE / 2
    r0, r1 = TILE / 2 - ROAD / 2, TILE / 2 + ROAD / 2
    n = 16
    V, F = [], []
    for i in range(n + 1):
        a = math.pi / 2 + (math.pi / 2) * i / n
        for r in (r0, r1):
            for z in (0, .18):
                V.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for i in range(n):
        b, c = i * 4, (i + 1) * 4
        F += [(b + 1, c + 1, c + 3, b + 3), (b, b + 2, c + 2, c), (b, c, c + 1, b + 1), (b + 2, b + 3, c + 3, c + 2)]
    F += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
    A.add('Road_Bed_Curve', (np.array(V), F), 'stone', bevel=False)

    def inside(x, y):
        r = math.hypot(x - cx, y - cy)
        return r0 + .05 < r < r1 - .05 and x <= cx and y >= cy
    _stones(A, _grid(inside, .5), lambda x, y: TOP)
    for r in (r0 - KERB / 2, r1 + KERB / 2):
        pts = [(cx + r * math.cos(math.pi / 2 + math.pi / 2 * i / 10), cy + r * math.sin(math.pi / 2 + math.pi / 2 * i / 10)) for i in range(11)]
        A.add('Road_Kerb_Curve', merge(beam((*pts[i], TOP - .07), (*pts[i + 1], TOP - .07), KERB, .2) for i in range(10)), 'kerb', bevel=False)
    return A


def road_slope():
    """6 m long, 3 m wide ramp rising 0.6 m toward +Y (10 %)."""
    A = Asset()
    L, rise = TILE, .6
    k = rise / L
    zf = lambda x, y: TOP + (y + L / 2) * k  # noqa: E731
    V = []
    for y in (-L / 2, L / 2):
        for x in (-ROAD / 2 - KERB + .02, ROAD / 2 + KERB - .02):
            V += [(x, y, 0), (x, y, zf(0, y) - .02)]
    V = np.array(V)
    F = [(0, 2, 6, 4), (1, 5, 7, 3), (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)]
    A.add('Road_Bed_Slope', (V, F), 'stone', bevel=False)
    pts = [(x, y) for x in np.arange(-ROAD / 2 + .25, ROAD / 2, .5) for y in np.arange(-L / 2 + .25, L / 2, .5)]
    _stones(A, pts, zf, lambda x, y: -math.atan(k))
    for sx in (-1, 1):
        x = sx * (ROAD / 2 + KERB / 2)
        A.add('Road_Kerb_Slope', beam((x, -L / 2, zf(0, -L / 2) - .05), (x, L / 2, zf(0, L / 2) - .05), KERB, .22), 'kerb')
    for i, y in enumerate(np.arange(-L / 2 + .75, L / 2, 1.5)):
        A.add('Road_Slope_Grip_Strip', xf(box((0, 0, 0), (ROAD - .1, .08, .03)), rot=(-math.atan(k), 0, 0), t=(0, y, zf(0, y) + .012)), 'kerb', bevel=False)
    return A


def stone_arch_bridge():
    A = Asset()
    span, W = 8.0, 2.4
    n = 24
    xs = np.linspace(-span / 2, span / 2, n + 1)
    top = [(x, .25 + 1.15 * math.cos(math.pi * x / span) ** 1.3 if abs(x) < span / 2 else .25) for x in xs]
    top = [(x, max(z, .25)) for x, z in top]
    arch_r = 1.6
    bot = [(x, (math.sqrt(arch_r ** 2 - x * x) * .85 if abs(x) < arch_r else 0)) for x in xs]
    V, F = [], []
    for (x, zt), (_, zb) in zip(top, bot):
        for y in (-W / 2, W / 2):
            V += [(x, y, zb), (x, y, zt)]
    for i in range(n):
        a, b = i * 4, (i + 1) * 4
        F += [(a + 1, b + 1, b + 3, a + 3), (a, a + 2, b + 2, b), (a, b, b + 1, a + 1), (a + 2, a + 3, b + 3, b + 2)]
    F += [(0, 1, 3, 2), (n * 4, n * 4 + 2, n * 4 + 3, n * 4 + 1)]
    A.add('Bridge_Arch_Body', (np.array(V), F), 'stone', smooth=False, bevel=False)
    # voussoir ring and deck paving
    for i in range(1, 12):
        a = math.pi * i / 12
        p = (arch_r * math.cos(a), arch_r * math.sin(a) * .85)
        for y in (-W / 2 - .02, W / 2 + .02):
            A.add('Bridge_Voussoir', xf(box((0, 0, 0), (.32, .06, .22)), rot=(0, -(a - math.pi / 2), 0), t=(p[0], y, p[1])), 'kerb', detail=True)
    for i in range(n):
        (x0, z0), (x1, z1) = top[i], top[i + 1]
        A.add('Bridge_Deck_Slab', beam((x0, 0, z0 + .03), (x1, 0, z1 + .03), W - .3, .06, up=(0, 0, 1)), 'paving', bevel=False)
    # parapets following the deck
    for y in (-W / 2 + .12, W / 2 - .12):
        for i in range(0, n + 1, 3):
            x, z = top[i]
            A.add('Bridge_Parapet_Post', box((x, y, z + .45), (.2, .2, .9)), 'kerb')
            A.add('Bridge_Parapet_Cap', lathe((x, y, z + .9), [(0, 0), (.13, 0), (.14, .06), (.08, .16), (0, .2)], 12), 'kerb', smooth=True)
        for i in range(0, n, 3):
            (x0, z0), (x1, z1) = top[i], top[i + 3] if i + 3 <= n else top[n]
            A.add('Bridge_Parapet_Panel', beam((x0, y, z0 + .4), (x1, y, z1 + .4), .1, .5, up=(0, 0, 1)), 'pale')
            A.add('Bridge_Parapet_Rail', beam((x0, y, z0 + .78), (x1, y, z1 + .78), .14, .1, up=(0, 0, 1)), 'kerb')
    for sx in (-1, 1):
        A.add('Bridge_Abutment', box((sx * (span / 2 + .4), 0, .14), (.8, W + .4, .28)), 'stone')
    return A


def timber_railing():
    A = Asset()
    L = 2.0
    for x in (-L / 2, L / 2):
        A.add('Rail_Post', box((x, 0, .55), (.12, .12, 1.1)), 'lacquer')
        A.add('Rail_Post_Cap', lathe((x, 0, 1.1), [(0, 0), (.085, 0), (.09, .04), (.05, .1), (0, .13)], 12), 'timber', smooth=True)
        A.add('Rail_Post_Base', box((x, 0, .04), (.2, .2, .08)), 'stone')
    A.add('Rail_Top', box((0, 0, 1.0), (L, .1, .07)), 'lacquer')
    A.add('Rail_Mid', box((0, 0, .58), (L, .07, .05)), 'lacquer')
    A.add('Rail_Bottom', box((0, 0, .14), (L, .08, .06)), 'lacquer')
    for k in range(1, 12):
        x = -L / 2 + k * L / 12
        A.add('Rail_Baluster', box((x, 0, .36), (.035, .035, .4)), 'timber', detail=False)
    for k in range(4):
        x0 = -L / 2 + .06 + k * (L - .12) / 4
        x1 = x0 + (L - .12) / 4
        A.add('Rail_Lattice', merge([beam((x0, 0, .62), (x1, 0, .95), .035, .03), beam((x0, 0, .95), (x1, 0, .62), .035, .03)]), 'timber')
    return A


def stone_railing():
    A = Asset()
    L = 2.0
    for x in (-L / 2, L / 2):
        A.add('Stone_Rail_Post', box((x, 0, .5), (.22, .22, 1.0)), 'kerb')
        A.add('Stone_Rail_Lotus_Cap', lathe((x, 0, 1.0), [(0, 0), (.14, 0), (.16, .05), (.12, .12), (.15, .16), (.06, .26), (0, .3)], 16), 'kerb', smooth=True)
    A.add('Stone_Rail_Plinth', box((0, 0, .08), (L + .2, .3, .16)), 'stone')
    A.add('Stone_Rail_Panel', box((0, 0, .5), (L - .22, .12, .68)), 'pale')
    A.add('Stone_Rail_Panel_Inset', box((0, -.065, .5), (L - .6, .02, .4)), 'kerb', detail=True)
    A.add('Stone_Rail_Panel_Inset', box((0, .065, .5), (L - .6, .02, .4)), 'kerb', detail=True)
    A.add('Stone_Rail_Handrail', box((0, 0, .9), (L - .22, .18, .12)), 'kerb')
    A.add('Stone_Rail_Cloud_Medallion', xf(cyl((0, 0, 0), .12, .03, 20), rot=(math.pi / 2, 0, 0), t=(0, -.07, .5)), 'jade', smooth=True, detail=True)
    return A


def pond_edge():
    A = Asset()
    a, b = 2.2, 1.5
    A.add('Pond_Bed', xf(cyl((0, 0, 0), 1, .12, 40), scale=(a, b, 1)), 'soil', smooth=True, bevel=False)
    A.add('Pond_Water', xf(cyl((0, 0, .22), 1, .02, 40), scale=(a - .1, b - .1, 1)), 'water', smooth=True, bevel=False)
    rng = np.random.default_rng(11)
    n = 26
    for k in range(n):
        t = 2 * math.pi * k / n + rng.uniform(-.05, .05)
        r = rng.uniform(.26, .4)
        x, y = (a + .05) * math.cos(t), (b + .05) * math.sin(t)
        A.add('Pond_Edge_Stone', xf(sphere(r, 12, 6), scale=(1.25, .95, .7), rot=(0, 0, t + rng.uniform(-.3, .3)), t=(x, y, .16 + r * .2)),
              'kerb' if k % 3 else 'stone', smooth=True, bevel=False)
    for k in range(5):
        t = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(.3, .75)
        A.add('Lotus_Pad', xf(cyl((0, 0, 0), .22, .012, 16), t=(rr * a * .6 * math.cos(t), rr * b * .6 * math.sin(t), .245)), 'pad', smooth=True, bevel=False)
    for (x, y) in [(.5, .2), (-.6, -.3)]:
        A.add('Lotus_Flower', lathe((x, y, .25), [(0, 0), (.04, 0), (.1, .06), (.09, .12), (.05, .1), (0, .06)], 10), 'lotus', smooth=True)
        A.add('Lotus_Seedpod', cyl((x, y, .3), .03, .03, 10), 'gold', smooth=True)
    for k in range(9):
        x, y = -a * .85 + rng.uniform(-.1, .1), b * .2 + k * .08
        A.add('Pond_Reed', rod((x, y, .2), (x + rng.uniform(-.08, .08), y + .05, .2 + rng.uniform(.7, 1.0)), .012, 5), 'greens', smooth=True, bevel=False)
    return A


def spawn_altar():
    A = Asset()

    def octagon(r, z, h, color, name):
        A.add(name, lathe((0, 0, z), [(0, 0), (r, 0), (r, h), (0, h)], 8, start=math.pi / 8), color, smooth=False)

    octagon(1.75, 0, .3, 'stone', 'Altar_Base_Tier')
    octagon(1.3, .3, .3, 'kerb', 'Altar_Upper_Tier')
    A.add('Altar_Jade_Ring', tube((0, 0, .6), 1.05, .95, .015, 48), 'jade', smooth=True, bevel=False)
    A.add('Altar_Gold_Ring', tube((0, 0, .6), .62, .56, .015, 48), 'gold', smooth=True, bevel=False)
    for k in range(8):
        a = k * math.pi / 4
        A.add('Altar_Rune_Tile', box((.8 * math.cos(a), .8 * math.sin(a), .607), (.16, .1, .015), rz=a), 'jade', bevel=False, detail=True)
    A.add('Altar_Front_Step', box((0, -2.0, .075), (1.4, .3, .15)), 'pale')
    A.add('Altar_Upper_Step', box((0, -1.45, .375), (1.0, .3, .15)), 'pale')
    A.add('Altar_Lotus_Pedestal', lathe((0, 0, .6), [(0, 0), (.42, 0), (.45, .08), (.3, .18), (.36, .28), (.42, .36), (.3, .42), (0, .42)], 16), 'pale', smooth=True)
    A.add('Altar_Spirit_Stone', xf(lathe((0, 0, -.32), [(0, 0), (.22, .32), (0, .64)], 6), t=(0, 0, 1.62)), 'jade')
    A.add('Altar_Spirit_Halo', tube((0, 0, 1.6), .34, .31, .02, 32), 'gold', smooth=True, bevel=False)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = 1.45 * math.cos(a), 1.45 * math.sin(a)
        A.add('Altar_Corner_Lantern_Post', box((x, y, .95), (.16, .16, .7)), 'kerb')
        A.add('Altar_Corner_Lantern', box((x, y, 1.4), (.26, .26, .22)), 'lantern')
        A.add('Altar_Corner_Lantern_Roof', lathe((x, y, 1.51), [(0, 0), (.22, 0), (.06, .12), (0, .16)], 4, start=math.pi / 4), 'tile')
    return A


def town_paifang():
    A = Asset()
    xs = [-3.3, -1.3, 1.3, 3.3]
    for x in xs:
        tall = abs(x) < 2
        h = 5.0 if tall else 3.9
        A.add('Paifang_Column', cyl((x, 0, .45), .17, h - .45, 16), 'lacquer', smooth=True)
        A.add('Paifang_Drum_Base', lathe((x, 0, 0), [(0, 0), (.38, 0), (.4, .2), (.32, .45), (0, .45)], 16), 'kerb', smooth=True)
        for sy in (-1, 1):
            A.add('Paifang_Column_Brace', beam((x, sy * .9, 0), (x, sy * .15, 1.6), .14, .14), 'timber')
            A.add('Paifang_Brace_Foot', box((x, sy * .9, .1), (.34, .34, .2)), 'stone')
    # centre bay
    A.add('Paifang_Centre_Lintel', box((0, 0, 4.4), (3.0, .3, .36)), 'lacquer')
    A.add('Paifang_Centre_Lintel_Low', box((0, 0, 3.55), (2.6, .26, .26)), 'lacquer')
    A.add('Paifang_Plaque', box((0, -.2, 3.98), (1.5, .08, .6)), 'lacquer')
    A.add('Paifang_Plaque_Frame', box((0, -.17, 3.98), (1.7, .06, .74)), 'gold')
    for x in np.linspace(-1.2, 1.2, 7):
        A.add('Paifang_Dougong_Bracket', box((x, 0, 4.67), (.22, .5, .18)), 'jade', detail=True)
    A.gable_roof('Paifang_Centre_Roof', (0, 0, 4.76), 3.9, 1.6, .8, th=.1, ribs=.24, curl=.35)
    # side bays
    for sx in (-1, 1):
        cx = sx * 2.3
        A.add('Paifang_Side_Lintel', box((cx, 0, 3.4), (2.3, .26, .3)), 'lacquer')
        A.add('Paifang_Side_Panel', box((cx, 0, 3.0), (1.7, .08, .4)), 'jade')
        for x in np.linspace(cx - .8, cx + .8, 4):
            A.add('Paifang_Dougong_Bracket', box((x, 0, 3.63), (.2, .44, .16)), 'jade', detail=True)
        A.gable_roof(f'Paifang_Side_Roof_{"E" if sx > 0 else "W"}', (cx, 0, 3.71), 2.6, 1.4, .6, th=.09, ribs=.24, curl=.25)
    return A


C = lambda *p: [round(v, 4) for v in p]  # noqa: E731
H = TILE / 2
ASSETS = {
    'TownRoadTJunction': dict(name_zh='青石路 T 字路口', build=road_t, category='小鎮道路',
                              desc='6 x 6 m stone-paved T junction: 3 m road running east-west with a branch to the north, kerb stones on every edge and earthen verges in the corners.',
                              size='6 x 6 x 0.2 m; open edges at west, east and north.',
                              connectors={'west': C(-H, 0, TOP), 'east': C(H, 0, TOP), 'north': C(0, H, TOP)}),
    'TownRoadCrossroad': dict(name_zh='青石路十字路口', build=road_cross, category='小鎮道路',
                              desc='6 x 6 m stone-paved crossroads with four 3 m arms, kerbed corners, earthen verges and a round centre stone.',
                              size='6 x 6 x 0.2 m; open edges on all four sides.',
                              connectors={'west': C(-H, 0, TOP), 'east': C(H, 0, TOP), 'north': C(0, H, TOP), 'south': C(0, -H, TOP)}),
    'TownRoadCurve': dict(name_zh='青石路彎道', build=road_curve, category='小鎮道路',
                          desc='6 x 6 m tile with a 90 degree stone-paved bend (3 m centreline radius) from the south edge to the east edge, curved kerbs and verges.',
                          size='6 x 6 x 0.2 m; open edges at south and east.',
                          connectors={'south': C(0, -H, TOP), 'east': C(H, 0, TOP)}),
    'TownRoadSlope': dict(name_zh='青石坡路', build=road_slope, category='小鎮道路',
                          desc='6 m long, 3 m wide stone-paved ramp rising 0.6 m (10 percent) toward the north, with sloping kerbs and anti-slip strips.',
                          size='3.5 x 6 x 0.8 m; south edge at 0.2 m, north edge at 0.8 m.',
                          connectors={'south': C(0, -H, TOP), 'north': C(0, H, TOP + .6)}),
    'StoneArchBridge': dict(name_zh='石拱橋', build=stone_arch_bridge, category='橋樑與欄杆',
                            desc='Single-span humpback stone bridge, 8 m span and 2.4 m wide, with a semicircular arch, voussoir ring, paved deck and parapets with lotus-capped posts.',
                            size='Approx. 9.6 x 2.8 x 2.6 m; deck crown 1.45 m above the ends.',
                            connectors={'west': C(-4, 0, .28), 'east': C(4, 0, .28)}),
    'TimberRailing': dict(name_zh='木欄杆段', build=timber_railing, category='橋樑與欄杆',
                          desc='2 m red-lacquered timber railing segment: two capped posts on stone bases, top, middle and bottom rails, balusters and diagonal lattice.',
                          size='2.1 x 0.2 x 1.23 m; posts at x = +/-1.0 m for tiling.'),
    'StoneRailing': dict(name_zh='石欄杆段', build=stone_railing, category='橋樑與欄杆',
                         desc='2 m carved stone balustrade segment: lotus-capped posts, plinth, panel with recessed insets and jade medallion, and a rounded handrail.',
                         size='2.2 x 0.3 x 1.3 m; posts at x = +/-1.0 m for tiling.'),
    'PondEdge': dict(name_zh='荷花池', build=pond_edge, category='庭院',
                     desc='Small oval garden pond ringed by 26 rounded edge stones, with water surface, lotus pads, two pink lotus flowers and a clump of reeds.',
                     size='Approx. 5.2 x 3.8 m; water surface 0.22 m above the bed.'),
    'SpawnAltar': dict(name_zh='出生石台', build=spawn_altar, category='出生點',
                       desc='Two-tier octagonal stone spawn altar with front steps, inlaid jade and gold rings with rune tiles, a lotus pedestal holding a floating jade spirit stone with halo, and four corner lanterns.',
                       size='Approx. 3.5 x 4.3 x 1.9 m.'),
    'TownPaifang': dict(name_zh='小鎮牌樓', build=town_paifang, category='小鎮建築',
                        desc='Three-bay timber town archway (paifang): four red columns on carved drum bases with braces, tall centre bay with blank gold-framed plaque and bracket set, lower side bays with jade panels, curved tile roofs with upturned eaves.',
                        size='Approx. 8.2 x 1.8 x 5.9 m; centre opening 2.3 m wide.'),
}

BATCH_ID = 'TownRoads11'
BATCH_TITLE = '小鎮道路庭院 11'
BATCH_DATE = '2026-10-17'
BATCH_INTRO = '小鎮待辦的第三批：道路接頭、坡路、石拱橋、欄杆、荷花池，以及原本只在組合場景裡的出生石台與小鎮牌樓，共 10 組。'
STATUS = {}
BATCH_NOTES = """## 道路接頭規格

道路方塊為 6 × 6 m，路面寬 3 m、路緣石寬 0.25 m，路面高 0.2 m，與 MountainStonePath 同寬。每件的 `model_info.json` 記錄 `connectors`（開口邊中點、路面高度，以底部中心原點為準），方塊可邊對邊拼接；彎道從南邊轉到東邊，坡路往北升高 0.6 m。

## 其他

- 石拱橋跨距 8 m，橋面頂比兩端高約 1.45 m；兩端接口在 (±4, 0, 0.28) m。
- 木欄杆、石欄杆都是 2 m 一段，柱心在 x = ±1.0 m，可連續排列。
- 出生石台與小鎮牌樓是新建的獨立版本，造型和 SpawnTown 組合場景內的原件不同，可替換使用。

## 尚未完成

UV／貼圖烘焙、碰撞、LOD、導航網格與 Unreal 匯入驗證都還沒做；荷花池水面沒有動態，出生石台靈石沒有發光與浮動特效。"""


def prompt_for(aid, view):
    a = ASSETS[aid]
    return ('Use case: stylized-concept. Asset type: Blender modeling reference for a xianxia (Chinese immortal-cultivation) '
            f'open-world town, single modular game asset: {a["name_zh"]} ({aid}). Design: {a["desc"]} Scale: {a["size"]} '
            'Style: softly beveled stylized 3D game art matching the existing dondon town (blue-grey stone paving, warm cedar timber, '
            'red lacquer, curved blue-grey tile roofs, restrained jade and gold accents). '
            f'View: {VIEW_PHRASE[view]}, entire object visible on a light grey seamless studio background with soft contact shadow. '
            'No characters, no scenery, no text or lettering, no watermark.')
