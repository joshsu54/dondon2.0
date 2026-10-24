"""Lingyun valley terrain for TownLayout_09: continuous meadow, north slope to the sect gate, columnar cliff rim,
rim boulders and five tiered karst peaks. World coordinates match UE (Blender m, north +Y; UE (x,-y,z)/100).
Imported by build_lingyun15.py; every function only adds to the given collection.
"""
import bpy,bmesh,math,random,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix,noise
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('wild13',HERE.parents[1]/'WildVegetation13/BlenderSource/build_wild13.py')
W13=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(W13)  # reuse lumpy_into / chisel / flat_base

# Island outline: superellipse, centre (0, YC), semi-axes A x B, exponent N.
A,B,YC,N=46.0,83.5,8.5,6.0
GROUND=-0.15  # UE ValleyGround top
PEAKS=[  # (name, x, y, base radius, height) — layout from the concept top view, highest to the north-east;
    # inner edges stay clear of the gate terrace (x +-7.5) and the town (x -26..22)
    ('Peak_NorthEast',27.,79.,16.,48.),('Peak_NorthWest',-26.,76.,14.,40.),('Peak_EastMid',38.5,34.,10.,31.),
    ('Peak_WestMid',-38.5,21.,10.,28.),('Peak_WestSouth',-38.,-14.,7.5,19.)]
GROUND_WORDS=('Terrace','Trail','Stair','Road','Foundation','Paving','Plinth','Floor','Ground','Plaza','Paver','Slab','Step',
              'Landing','Kerb','Curb','Base','Island','Apron','Lane','Street','Footing','Platform','Dais','Approach','Forecourt')
SKIP_WORDS=('Pine','Grass','Lantern','Herb','Cloud','Waymarker')   # trail support 'Rock' blocks count as ground

def smooth(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)

def outline(theta,m=1.):
    """World XY of the island outline at angle theta, shrunk by ring factor m; the wobble keeps it organic."""
    c,s=math.cos(theta),math.sin(theta)
    r=(abs(c)**N+abs(s)**N)**(-1/N)
    wob=1+.022*noise.noise(Vector((c*2.3,s*2.3,.7)))+.008*math.sin(theta*23)
    return A*r*c*wob*m,YC+B*r*s*wob*m

def ring_factor(x,y):
    """Inverse of outline(): 0 at the centre, 1 on the island edge, >1 outside."""
    nx,ny=x/A,(y-YC)/B;th=math.atan2(ny,nx);ox,oy=outline(th);return math.hypot(nx,ny)/max(1e-9,math.hypot(ox/A,(oy-YC)/B))

def ground_bvh(context_objects):
    """BVH of near-ground context surfaces (paving, steps, terraces, floors, plinths)."""
    verts=[];faces=[];used=[]
    for o in context_objects:
        if o.type!='MESH' or any(w in o.name for w in SKIP_WORDS):continue
        pts=[o.matrix_world@Vector(c) for c in o.bound_box];zmin=min(p.z for p in pts);zmax=max(p.z for p in pts)
        if not (any(w in o.name for w in GROUND_WORDS) or (zmin<.8 and zmax-zmin<1.8)):continue
        off=len(verts);mw=o.matrix_world
        verts+= [mw@v.co for v in o.data.vertices];faces+= [tuple(off+i for i in p.vertices) for p in o.data.polygons];used.append(o.name)
    return BVHTree.FromPolygons(verts,faces),used

def lowest_up_surface(tree,x,y,zcap=14.):
    """Lowest upward-facing context surface under (x,y), or None."""
    o=Vector((x,y,40.));d=Vector((0,0,-1));best=None;steps=0
    while steps<30:
        hit=tree.ray_cast(o,d,80.)
        if hit[0] is None:break
        p,n=hit[0],hit[1]
        if n.z>.5 and p.z<zcap:best=p.z if best is None else min(best,p.z)
        o=p+d*.004;steps+=1
    return best

# Levelled camp platforms and path corridors (rectangles x0,y0,x1,y1 with a feathered edge), kept in sync with camp15.
LEVEL_RECTS=[(-19.,-54.,-6.,-40.),(4.5,-53.,18.,-42.),(-5.,-71.,5.,-61.),(-2.,-64.,2.,-13.),(-9.,-48.5,8.,-45.5)]
def level_weight(x,y,feather=3.):
    w=0.
    for x0,y0,x1,y1 in LEVEL_RECTS:
        dx=max(x0-x,0.,x-x1);dy=max(y0-y,0.,y-y1);w=max(w,1-smooth(0.,feather,math.hypot(dx,dy)))
    return w

# Winding dirt footpaths across the meadow (concept detail); painted into the 'dirt' attribute only.
TRAILS=[[(-9.,-47.),(-18.,-38.),(-27.,-30.),(-31.,-20.),(-33.,-15.)],
        [(23.,10.),(28.,18.),(31.,26.),(32.,30.)],
        [(-14.,46.),(-19.,55.),(-21.,62.),(-22.,66.)],
        [(8.,-47.),(16.,-58.),(10.,-66.),(3.,-67.)],
        [(0.,-30.),(-9.,-24.),(-19.,-19.),(-27.,-12.)],
        [(0.,-36.),(12.,-30.),(22.,-24.),(30.,-14.)]]
def trail_weight(x,y,width=.7):
    best=9.
    for pts in TRAILS:
        for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
            dx,dy=x1-x0,y1-y0;t=max(0.,min(1.,((x-x0)*dx+(y-y0)*dy)/(dx*dx+dy*dy)))
            wob=.5*noise.noise(Vector((x/6.,y/6.,4.)))       # gentle meander off the polyline
            best=min(best,abs(math.hypot(x-x0-t*dx,y-y0-t*dy)+wob))
    return 1-smooth(width,width+.8,best)

def natural_height(x,y):
    roll=.55*noise.fractal(Vector((x/24.,y/24.,.3)),.6,2.,3)+.18*noise.noise(Vector((x/7.,y/7.,1.9)))
    roll*=1-level_weight(x,y)
    h=GROUND+roll
    h+=6.05*smooth(45.,65.,y)+2.6*smooth(78.,95.,y)          # north slope up to the gate terrace and beyond
    for _,px,py,r,ph in PEAKS:                                # foothill mounds around each peak
        d=math.hypot(x-px,y-py);h+=min(4.,ph*.11)*math.exp(-(d/(r*1.9))**2)
    return h

def build_terrain(coll,tree,mats,nu=200,nv=360):
    """Grid in [-1,1]^2 mapped onto concentric superellipses; heights follow context surfaces where present."""
    cols=[];zs=[];con=[]
    for j in range(nv+1):
        v=-1+2*j/nv
        for i in range(nu+1):
            u=-1+2*i/nu;m=max(abs(u),abs(v))
            x,y=(0.,YC) if m<1e-9 else outline(math.atan2(v,u),m)
            cols.append((x,y,m))
    # Context constraint pass: snap under near-ground surfaces, then blend shoulders outwards (BFS on the grid).
    W=nu+1;H=[0.]*len(cols);fixed=[None]*len(cols)
    for idx,(x,y,m) in enumerate(cols):
        H[idx]=natural_height(x,y)
        if -32<x<28 and -16<y<84:
            # Minimum over a small cross (grid spacing ~0.46 m) so triangles spanning a step edge stay under the lower tread.
            ss=[lowest_up_surface(tree,x+dx,y+dy) for dx,dy in ((0,0),(.3,0),(-.3,0),(0,.3),(0,-.3))]
            if ss[0] is not None:fixed[idx]=min(s for s in ss if s is not None)-.03
    from collections import deque
    dist=[1e9]*len(cols);near=[None]*len(cols);q=deque()
    for idx,f in enumerate(fixed):
        if f is not None:dist[idx]=0.;near[idx]=f;q.append(idx)
    while q:
        idx=q.popleft();j,i=divmod(idx,W)
        for dj,di in ((1,0),(-1,0),(0,1),(0,-1)):
            jj,ii=j+dj,i+di
            if 0<=jj<=nv and 0<=ii<=nu:
                n=jj*W+ii;d=dist[idx]+math.dist(cols[idx][:2],cols[n][:2])
                if d<dist[n] and d<9.:dist[n]=d;near[n]=near[idx];q.append(n)
    dirt=[0.]*len(cols)
    for idx,(x,y,m) in enumerate(cols):
        if fixed[idx] is not None:H[idx]=fixed[idx];dirt[idx]=.25  # mostly hidden under paving; grass where plates are removed
        elif near[idx] is not None:
            w=smooth(0.,1.,1-dist[idx]/9.)**1.3   # soil shoulder: meet the structure flush, fade to natural ground
            H[idx]=near[idx]-.04*(1-w)+(H[idx]-near[idx])*(1-w);dirt[idx]=max(dirt[idx],.75*smooth(0.,1.,1-dist[idx]/2.5))
        H[idx]+=.35*smooth(.94,1.,m)           # slight raised lip before the rim boulders
        dirt[idx]=max(dirt[idx],.9*trail_weight(x,y))
    bm=bmesh.new();lay=bm.verts.layers.float.new('dirt')  # layer first: adding it later invalidates vert refs
    bv=[bm.verts.new((x,y,H[k])) for k,(x,y,m) in enumerate(cols)]
    for k,v in enumerate(bv):v[lay]=dirt[k]
    for j in range(nv):
        for i in range(nu):
            a=j*W+i;bm.faces.new((bv[a],bv[a+1],bv[a+W+1],bv[a+W]))
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.001)   # collapse the duplicate centre column
    me=bpy.data.meshes.new('Terrain_Meadow_Mesh');bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    me.materials.append(mats['meadow'])
    o=bpy.data.objects.new('Terrain_Meadow',me);coll.objects.link(o)
    o['note']='Continuous ground; snapped 3 cm under near-ground TownLayout_09 surfaces with 9 m soil shoulders'
    return o,cols,H,nu,nv

def height_at(terrain,x,y,_cache={}):
    t=_cache.get(terrain.name)
    if t is None:
        dg=bpy.context.evaluated_depsgraph_get();t=_cache[terrain.name]=BVHTree.FromObject(terrain,dg)
    hit=t.ray_cast(Vector((x,y,200.)),Vector((0,0,-1)),400.)
    return hit[0].z if hit[0] is not None else None

def build_cliff_rim(coll,terrain,mats,samples=720,depth=-11.):
    """Vertical columnar limestone skirt under the outline, plus a row of chiselled rim boulders."""
    rng=random.Random(1501);bm=bmesh.new();rings=[]
    zlevels=[0,.25,.5,.75,1.]
    for k in range(samples):
        th=2*math.pi*k/samples;x,y=outline(th);ix,iy=outline(th,.999)
        top=(height_at(terrain,ix,iy) or GROUND)-.08
        outward=Vector((x/A**2,(y-YC)/B**2,0)).normalized()
        col=.55*abs(noise.noise(Vector((th*38.,0,.2))))+.25*noise.noise(Vector((th*90.,0,.8)))
        ring=[]
        for t in zlevels:
            z=top+(depth-top)*t;bulge=col*(1-t*.4)+.35*noise.noise(Vector((th*12.,z/3.,1.)))-.6*t
            ring.append(bm.verts.new(Vector((x,y,z))+outward*bulge))
        rings.append(ring)
    for k in range(samples):
        a,b=rings[k],rings[(k+1)%samples]
        for z in range(len(zlevels)-1):bm.faces.new((a[z],b[z],b[z+1],a[z+1]))
    bm.faces.new([r[-1] for r in reversed(rings)])
    me=bpy.data.meshes.new('Cliff_Rim_Mesh');bm.to_mesh(me);bm.free();me.materials.append(mats['cliff'])
    for p in me.polygons:p.use_smooth=False
    rim=bpy.data.objects.new('Cliff_Rim',me);coll.objects.link(rim)
    # Rim boulders: a handful of chiselled variants instanced along the edge.
    variants=[]
    for n in range(6):
        bm=bmesh.new();r=(rng.uniform(1.,1.6),rng.uniform(.9,1.3),rng.uniform(.9,1.7))
        W13.lumpy_into(bm,(0,0,r[2]*.35),r,1600+n,3,.16,1.2,rng.uniform(0,6));W13.chisel(bm,(0,0,r[2]*.35),r,6,rng);W13.flat_base(bm,-1.2)
        me=bpy.data.meshes.new('Rim_Boulder_Variant_%d'%n);bm.to_mesh(me);bm.free();me.materials.append(mats['rock']);variants.append(me)
    count=0;k=0
    while k<samples:
        th=2*math.pi*k/samples;x,y=outline(th,.985);z=height_at(terrain,x,y)
        if z is not None and not (-4<x<4 and y<-60):   # keep the south path end open
            o=bpy.data.objects.new('Rim_Boulder_%03d'%count,variants[count%len(variants)]);coll.objects.link(o)
            sc=rng.uniform(.7,1.25);o.location=(x,y,z-.35*sc);o.rotation_euler=(0,0,th+rng.uniform(-.5,.5));o.scale=(sc,sc,sc*rng.uniform(.8,1.2));count+=1
        k+=rng.randint(3,6)
    return rim,count

def _tier(bm,cx,cy,z0,rad,ry,th,seed):
    """Superellipsoid tier: near-vertical cliff walls, rounded top edge, vertical grooves and lumpy plan."""
    vs=bmesh.ops.create_icosphere(bm,subdivisions=4,radius=1)['verts'];off=Vector((seed*1.7,seed*.9,seed*.3))
    for v in vs:
        d=v.co.normalized();zn=d.z;hl=math.hypot(d.x,d.y)
        a=math.atan2(d.y,d.x);radial=(1-abs(zn)**8)**(1/8)
        plan=1+.16*noise.noise(Vector((math.cos(a)*1.3,math.sin(a)*1.3,0))+off)+.07*noise.noise(Vector((math.cos(a)*4,math.sin(a)*4,zn*2))+off)
        groove=.05*noise.noise(Vector((a*9.,zn*1.2,0))+off)   # vertical weathering: high freq in angle, low in height
        k=radial*(plan+groove)
        v.co=Vector((cx+math.cos(a)*rad*k,cy+math.sin(a)*ry*k,z0+th*.5+zn*th*.5))
    return vs

def _column(bm,cx,cy,r,h,z0,seed,ledges):
    """One limestone column: 3-4 near-vertical tiers that step in slightly, each top a green ledge."""
    rng=random.Random(seed);tiers=3 if h<22 else 4;z=z0
    for t in range(tiers):
        f=t/max(1,tiers-1);rad=r*(1-.32*f)*rng.uniform(.93,1.03);th=(h-z0+z0)/tiers*rng.uniform(1.12,1.3)
        cx+=rng.uniform(-.05,.05)*r;cy+=rng.uniform(-.05,.05)*r
        _tier(bm,cx,cy,z,rad,rad*rng.uniform(.8,.97),th,seed*10+t);ledges.append((cx,cy,z+th,rad*.7));z+=th*.84

def build_peak(coll,mats,name,px,py,r,h,base_z,seed):
    """Cluster of limestone columns (main + 2-3 shorter satellites) like the concept karst; returns (object, ledges)."""
    rng=random.Random(seed);bm=bmesh.new();ledges=[];z0=base_z-1.5
    _column(bm,px,py,r*.72,h,z0,seed,ledges)
    for k in range(rng.randint(2,3)):
        a=rng.uniform(0,2*math.pi);d=r*rng.uniform(.45,.65)
        _column(bm,px+math.cos(a)*d,py+math.sin(a)*d,r*rng.uniform(.38,.52),h*rng.uniform(.4,.75),z0,seed*7+k,ledges)
    W13.flat_base(bm,z0)
    me=bpy.data.meshes.new(name+'_Mesh');bm.to_mesh(me);bm.free();me.materials.append(mats['peak'])
    for p in me.polygons:p.use_smooth=True
    o=bpy.data.objects.new(name,me);coll.objects.link(o);o['height_m']=h;o['base_radius_m']=r
    return o,ledges

def build_peaks(coll,terrain,mats):
    out=[]
    for k,(name,x,y,r,h) in enumerate(PEAKS):
        base=height_at(terrain,x,y) or GROUND
        out.append((name,)+build_peak(coll,mats,name,x,y,r,h,base,1510+k))
    return out
