"""Create TownLayout_11 from 10: push the old ValleyRidge / DistantPeak scenery out of the LingyunValley15 island.
Each actor's real mesh vertices (world space) are tested against the island outline (superellipse, +3 % for the
outline wobble, plus a 3 m margin); overlapping actors move radially away from the island centre in 1 m steps
until no vertex is inside. Shape, height, rotation and scale are untouched, so the distant silhouette is kept.
Full editor; never saves 10, never overwrites 11.  UnrealEditor <uproject> -ExecutePythonScript=<this> -unattended
"""
import unreal as u
import json,math,hashlib,traceback
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
NEW='/Game/Maps/TownLayout_11';BASE='/Game/Maps/TownLayout_10'
# Island outline from LingyunValley15 terrain15.py, in Blender metres (north +Y); UE cm = (x, -y) * 100.
A,B,YC,N=46.,83.5,8.5,6.;GROW=1.03;MARGIN_CM=300.;CENTRE=u.Vector(0,-YC*100,0)
SCENERY=('ValleyRidge_','DistantPeak_')
report={'status':'starting','map':NEW,'base':BASE,'outline':{'A_m':A,'B_m':B,'YC_m':YC,'N':N,'grow':GROW,'margin_cm':MARGIN_CM},'actors':{}}
def write():(root/'expansion11_build.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
def inside(x_cm,y_cm):
    """True when a UE point lies within the grown island outline plus margin."""
    bx,by=x_cm/100.,-y_cm/100.;nx,ny=bx/(A*GROW),(by-YC)/(B*GROW)
    r=math.hypot(nx,ny)
    if r<1e-9:return True
    c,s=nx/r,ny/r;edge=(abs(c)**N+abs(s)**N)**(-1/N)          # unit-superellipse radius in that direction
    m=MARGIN_CM/100./min(A,B)                                   # margin expressed in normalised units (conservative)
    return r<edge+m
def world_points(actor):
    mesh=actor.static_mesh_component.static_mesh;pts=[]
    for sec in range(mesh.get_num_sections(0)):
        verts=u.ProceduralMeshLibrary.get_section_from_static_mesh(mesh,0,sec)[0]
        pts+=verts
    tf=actor.get_actor_transform();step=max(1,len(pts)//4000)       # subsample very dense meshes
    return [tf.transform_location(p) for p in pts[::step]]
try:
    assert u.load_class(None,'/Script/XiuXianTown.SectQuestDirector'),'Quest module must be loaded'
    assert not u.EditorAssetLibrary.does_asset_exist(NEW),'Never overwrite an existing 11'
    base=root/'XiuXianTown/Content/Maps/TownLayout_10.umap';report['base10_sha256']=hashlib.sha256(base.read_bytes()).hexdigest()
    world=u.EditorLoadingAndSavingUtils.load_map(BASE);eas=u.get_editor_subsystem(u.EditorActorSubsystem)
    count=len(eas.get_all_level_actors())
    for a in eas.get_all_level_actors():
        lab=a.get_actor_label()
        if not lab.startswith(SCENERY):continue
        pts=world_points(a);l0=a.get_actor_location()
        hits=sum(1 for p in pts if inside(p.x,p.y))
        rec={'vertices_sampled':len(pts),'vertices_inside_before':hits,'location_before':[l0.x,l0.y,l0.z]}
        if hits:
            d=u.Vector(l0.x-CENTRE.x,l0.y-CENTRE.y,0);d=d/d.length() if d.length()>1 else u.Vector(1,0,0)
            moved=0.
            while hits and moved<20000:
                moved+=100.;hits=sum(1 for p in pts if inside(p.x+d.x*moved,p.y+d.y*moved))
            assert not hits,(lab,'still overlapping after 200 m')
            a.set_actor_location(u.Vector(l0.x+d.x*moved,l0.y+d.y*moved,l0.z),False,False)
            rec.update(moved_cm=moved,direction=[d.x,d.y])
        l1=a.get_actor_location();rec['location_after']=[l1.x,l1.y,l1.z];report['actors'][lab]=rec
    assert u.EditorLoadingAndSavingUtils.save_map(world,NEW)
    world=u.EditorLoadingAndSavingUtils.load_map(NEW);items=eas.get_all_level_actors()
    checks={'actor_count_unchanged':len(items)==count,'base10_unchanged':hashlib.sha256(base.read_bytes()).hexdigest()==report['base10_sha256']}
    ground=next(a for a in items if a.get_actor_label()=='ValleyGround');gc,ge=ground.get_actor_bounds(False)
    for a in items:
        lab=a.get_actor_label()
        if not lab.startswith(SCENERY):continue
        pts=world_points(a);checks[lab+'_clear_of_island']=not any(inside(p.x,p.y) for p in pts)
        c,e=a.get_actor_bounds(False)
        checks[lab+'_on_valley_ground']=all(gc_-ge_<=c_-e_ and c_+e_<=gc_+ge_ for c_,e_,gc_,ge_ in ((c.x,e.x,gc.x,ge.x),(c.y,e.y,gc.y,ge.y)))
        r=report['actors'][lab];checks[lab+'_height_unchanged']=abs(a.get_actor_location().z-r['location_before'][2])<.1
    report['checks']=checks;assert all(checks.values()),{k:v for k,v in checks.items() if not v}
    report.update(status='saved_reloaded_pending_pie_and_visual',map_sha256=hashlib.sha256((root/'XiuXianTown/Content/Maps/TownLayout_11.umap').read_bytes()).hexdigest());write()
except Exception:
    report.update(status='error',error=traceback.format_exc());write();raise
