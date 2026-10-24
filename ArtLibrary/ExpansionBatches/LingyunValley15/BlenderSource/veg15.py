"""Vegetation scatter for LingyunValley15 using the WildVegetation13 assets as shared-mesh instances.
Denser toward the karst peaks and the rim (like the concept), open meadow in the middle; keeps clear of the
town, the north trail, the camp, peak bodies and the cliff edge. Ledge pines sit on peak tier tops.
Placements are also returned for the UE scatter JSON (Blender m, yaw in radians about +Z).
"""
import bpy,math,random
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ASSETS=['CommonPine','BambooClump','WildShrub','MossBoulderSet','ScreePile']
# Rectangles that stay free of scatter (x0,y0,x1,y1): town + north trail + rest stop + camp + paths.
KEEP_OUT=[(-29.,-16.,25.,43.),(-10.,42.,10.,81.),(-21.,38.,0.,51.),(-20.,-55.,-5.,-39.),(3.5,-54.,19.,-41.),
          (-6.,-72.,6.,-60.),(-3.,-64.,3.,-12.),(-10.,-49.,9.,-45.)]

def load_assets(repo,coll):
    """Append each WildVegetation13 asset and merge its parts into one mesh for instancing."""
    out={}
    for aid in ASSETS:
        path=repo/'Models'/aid/'v001'/f'{aid}_v001.blend'
        with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=[n for n in src.objects]
        meshes=[o for o in dst.objects if o and o.type=='MESH']
        for o in dst.objects:
            if o:coll.objects.link(o)
        bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get();import bmesh
        bm=bmesh.new();mats=[]
        for o in meshes:
            me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg);me.transform(o.matrix_world)
            remap={}
            for i,m in enumerate(me.materials):
                if m not in mats:mats.append(m)
                remap[i]=mats.index(m)
            for p in me.polygons:p.material_index=remap.get(p.material_index,0)
            bm.from_mesh(me);bpy.data.meshes.remove(me)
        merged=bpy.data.meshes.new('LY15_'+aid);bm.to_mesh(merged);bm.free()
        for m in mats:merged.materials.append(m)
        for o in list(dst.objects):
            if o:bpy.data.objects.remove(o,do_unlink=True)
        out[aid]=merged
    return out

def _blocked(x,y,peaks,margin):
    if any(x0-margin<x<x1+margin and y0-margin<y<y1+margin for x0,y0,x1,y1 in KEEP_OUT):return True
    return any(math.hypot(x-px,y-py)<r*.72 for _,px,py,r,h in peaks)

def scatter(coll,meshes,terrain,peaks_spec,peak_objs,inside,seed=1540):
    """inside(x,y) -> ring factor m (<1 inside the island). Returns placements list."""
    rng=random.Random(seed);placed=[];pts=[]
    dg=bpy.context.evaluated_depsgraph_get();tt=BVHTree.FromObject(terrain,dg)
    def ground(x,y):
        h=tt.ray_cast(Vector((x,y,200.)),Vector((0,0,-1)),400.);return h[0].z if h[0] is not None else None
    def near_feature(x,y):
        dp=min(math.hypot(x-px,y-py)-r for _,px,py,r,h in peaks_spec);m=inside(x,y)
        return max(math.exp(-max(dp,0.)/9.),(m-.8)/.2 if m>.8 else 0.)
    plan=[('CommonPine',125,4.2,(.55,.95),.25),('BambooClump',22,4.,(.6,.9),.0),('WildShrub',95,2.4,(.7,1.25),.3),
          ('MossBoulderSet',22,4.,(.45,.85),.05),('ScreePile',14,3.,(.6,1.),.0)]
    for aid,count,mind,(s0,s1),base_p in plan:
        n=0;tries=0
        while n<count and tries<count*400:
            tries+=1;x=rng.uniform(-46,46);y=rng.uniform(-75,92)
            m=inside(x,y)
            if m>.955 or _blocked(x,y,peaks_spec,1.5 if aid!='CommonPine' else 3.):continue
            f=near_feature(x,y)
            if aid in ('BambooClump','ScreePile','MossBoulderSet') and f<.35:continue
            if rng.random()>base_p+(1-base_p)*f:continue
            if any((x-px)**2+(y-py)**2<max(mind,pm)**2 for px,py,pm in pts):continue
            z=ground(x,y)
            if z is None:continue
            sc=rng.uniform(s0,s1);yaw=rng.uniform(0,2*math.pi)
            o=bpy.data.objects.new('Scatter_%s_%03d'%(aid,n),meshes[aid]);coll.objects.link(o)
            o.location=(x,y,z-.05);o.rotation_euler=(0,0,yaw);o.scale=(sc,sc,sc)
            pts.append((x,y,mind*.6));placed.append({'asset':aid,'location_m':[x,y,z-.05],'yaw_rad':yaw,'scale':sc,'on':'ground'});n+=1
    # Ledge pines on the peak tiers (ray onto the peak itself).
    for name,obj,ledges in peak_objs:
        pt=BVHTree.FromObject(obj,dg)
        for cx,cy,ztop,rad in ledges:
            for _ in range(rng.randint(1,3)):
                a=rng.uniform(0,2*math.pi);d=rng.uniform(0,rad*.75);x,y=cx+math.cos(a)*d,cy+math.sin(a)*d
                h=pt.ray_cast(Vector((x,y,ztop+30.)),Vector((0,0,-1)),60.)
                if h[0] is None or h[1].z<.6:continue
                sc=rng.uniform(.3,.55);yaw=rng.uniform(0,2*math.pi)
                o=bpy.data.objects.new('Ledge_Pine_%s'%name,meshes['CommonPine']);coll.objects.link(o)
                o.location=h[0]-Vector((0,0,.08));o.rotation_euler=(0,0,yaw);o.scale=(sc,sc,sc)
                placed.append({'asset':'CommonPine','location_m':list(o.location),'yaw_rad':yaw,'scale':sc,'on':name})
    return placed
