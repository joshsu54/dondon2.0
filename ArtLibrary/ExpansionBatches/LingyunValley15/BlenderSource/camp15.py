"""Southern sect camp for LingyunValley15 (the camp in the concept set): open-front timber dormitory (west, facing the
path), raised herb garden (east), hexagonal tiled pavilion (south end), stone-slab path with branches and lantern posts.
Coordinates: Blender m, north +Y, same world frame as TownLayout_09. Each builder returns its root empty.
"""
import bpy,bmesh,math,random
from mathutils import Vector,Matrix

PATH_MAIN=((0.,-13.5),(0.,-62.5))          # town south edge -> pavilion steps
PATH_BRANCH=((-8.6,-47.),(7.,-47.))        # west to dormitory front, east to herb garden gate
DORM=(-13.,-47.)                            # centre; long axis N-S, open front faces +X (the path)
GARDEN=(11.,-47.5)
PAVILION=(0.,-66.6)
FLAT_ZONES=[(-19.,-54.,-6.,-40.),(4.5,-53.,18.,-42.),(-5.,-71.,5.,-61.)]   # x0,y0,x1,y1 levelled to ground
CAMP_GROUND=-.15

class Kit:
    """Small mesh toolkit; every part is parented to root and tagged with its part group."""
    def __init__(self,coll,root,mats):self.coll,self.root,self.m=coll,root,mats
    def mesh(self,name,v,f,mat,smooth=False,group=None):
        d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update();d.materials.append(self.m[mat])
        for p in d.polygons:p.use_smooth=smooth
        o=bpy.data.objects.new(name,d);self.coll.objects.link(o);o.parent=self.root
        if group:o['part']=group
        return o
    def box(self,name,c,s,mat,bevel=0.,rot=0.,group=None):
        x,y,z=c;a,b,h=s[0]/2,s[1]/2,s[2]/2
        pts=[(-a,-b,-h),(a,-b,-h),(a,b,-h),(-a,b,-h),(-a,-b,h),(a,-b,h),(a,b,h),(-a,b,h)]
        R=Matrix.Rotation(rot,3,'Z');v=[tuple(Vector((x,y,z))+R@Vector(p)) for p in pts]
        o=self.mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,group=group)
        if bevel:
            md=o.modifiers.new('Bevel','BEVEL');md.width=bevel;md.segments=2;o.modifiers.new('WN','WEIGHTED_NORMAL')
        return o
    def beam(self,name,a,b,w,h,mat,group=None):
        a,b=Vector(a),Vector(b);d=b-a;L=d.length;dn=d.normalized()
        side=dn.cross(Vector((0,0,1)));side=side.normalized() if side.length>1e-4 else Vector((1,0,0))
        up=side.cross(dn).normalized();sw,uh=side*w/2,up*h/2
        v=[tuple(p) for p in (a-sw-uh,b-sw-uh,b+sw-uh,a+sw-uh,a-sw+uh,b-sw+uh,b+sw+uh,a+sw+uh)]
        return self.mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,group=group)
    def cyl(self,name,c,r,h,mat,n=12,r2=None,group=None):
        x,y,z=c;r2=r if r2 is None else r2
        v=[(x+rr*math.cos(i*2*math.pi/n),y+rr*math.sin(i*2*math.pi/n),z+dz) for dz,rr in ((0,r),(h,r2)) for i in range(n)]
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
        return self.mesh(name,v,f,mat,True,group)
    def tube(self,name,pts,r,mat,sides=8,group=None):
        v=[];f=[]
        for j,p in enumerate(pts):
            t=(Vector(pts[min(j+1,len(pts)-1)])-Vector(pts[max(j-1,0)])).normalized();u=t.cross(Vector((0,0,1)))
            if u.length<.01:u=t.cross(Vector((0,1,0)))
            u.normalize();w=t.cross(u)
            v+= [tuple(Vector(p)+r*(u*math.cos(i*2*math.pi/sides)+w*math.sin(i*2*math.pi/sides))) for i in range(sides)]
        for j in range(len(pts)-1):f+= [(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i) for i in range(sides)]
        f+= [tuple(reversed(range(sides))),tuple(range((len(pts)-1)*sides,len(pts)*sides))]
        return self.mesh(name,v,f,mat,True,group)

def _root(coll,name,loc):
    e=bpy.data.objects.new(name,None);coll.objects.link(e);e.location=loc;return e

# ------------------------------------------------------------------ dormitory
def dormitory(coll,mats,ground):
    """Open-front timber dormitory, 10 m (N-S) x 6 m, local +X = open front toward the path."""
    root=_root(coll,'Camp_Dormitory',(*DORM,ground));k=Kit(coll,root,mats);rng=random.Random(1531)
    L,D,P=10.,6.,.4   # length (y), depth (x), plinth height
    k.box('Dorm_Stone_Plinth',(0,0,P/2-.05),(D+.6,L+.6,P+.1),'stone_base',.04)
    k.box('Dorm_Front_Step',(D/2+.55,0,.12),(.6,2.6,.24),'stone_base',.02)
    k.box('Dorm_Floor_Boards',(0,0,P+.03),(D,L,.06),'board')
    for j in range(13):k.box('Dorm_Floor_Joint_%02d'%j,(0,-L/2+.4+j*.77,P+.062),(D-.1,.025,.005),'timber')
    xs=(-D/2+.2,D/2-.2);ys=(-L/2+.2,-L/6,L/6,L/2-.2);H=3.1
    for x in xs:
        for y in ys:
            k.cyl('Dorm_Post',(x,y,P),.13,H,'timber',10)
            k.cyl('Dorm_Post_Base',(x,y,P),.2,.12,'stone_base',8)
    for x in xs:k.beam('Dorm_Wall_Plate',(x,-L/2-.3,P+H),(x,L/2+.3,P+H),.24,.26,'timber')
    for y in ys:k.beam('Dorm_Tie_Beam',(-D/2-.2,y,P+H),(D/2+.2,y,P+H),.2,.24,'timber')
    for y in ys:  # king-post trusses carry the ridge
        k.beam('Dorm_King_Post',(0,y,P+H+.1),(0,y,P+H+1.55),.16,.16,'timber')
        for s in (-1,1):k.beam('Dorm_Truss_Strut',(s*(D/2-.3),y,P+H+.15),(0,y,P+H+1.4),.12,.12,'timber')
    k.beam('Dorm_Ridge_Beam',(0,-L/2-.6,P+H+1.6),(0,L/2+.6,P+H+1.6),.22,.24,'timber')
    for x in xs:
        for y,sgn in ((ys[0],1),(ys[-1],-1)):k.beam('Dorm_Corner_Brace',(x,y,P+H-.75),(x,y+sgn*.75,P+H-.05),.1,.1,'timber')
    # Back wall (west) and gable ends: plaster panels in a timber frame, lattice windows on the gable sides.
    k.box('Dorm_Back_Wall',(-D/2+.2,0,P+H/2),(.12,L-.4,H),'plaster')
    for y in (-L/3,0,L/3):k.box('Dorm_Back_Wall_Stud',(-D/2+.13,y,P+H/2),(.06,.14,H),'timber')
    k.box('Dorm_Back_Wall_Rail',(-D/2+.13,0,P+1.1),(.06,L-.4,.12),'timber')
    for y in (-L/2+.2,L/2-.2):
        sgn=1 if y>0 else -1
        k.box('Dorm_End_Wall',(0,y,P+H/2),(D-.4,.12,H),'plaster')
        k.box('Dorm_End_Window_Frame',(-.6,y+sgn*.07,P+1.75),(1.6,.06,1.),'timber')
        for i in range(5):k.box('Dorm_End_Lattice_V',(-1.2+i*.3,y+sgn*.09,P+1.75),(.04,.03,.9),'timber')
        for i in range(3):k.box('Dorm_End_Lattice_H',(-.6,y+sgn*.09,P+1.45+i*.3),(1.5,.03,.04),'timber')
        gable=[(-D/2-.1,y,P+H),(D/2+.1,y,P+H),(0,y,P+H+1.6)]
        k.mesh('Dorm_Gable_Board',[tuple(Vector(p)+Vector((0,sgn*.02,0))) for p in gable],[(0,1,2)],'board')
    # Front: low railing at the ends of the open side, wide opening in the middle.
    for y0,y1 in ((-L/2+.2,-1.6),(1.6,L/2-.2)):
        k.beam('Dorm_Front_Rail',(D/2-.2,y0,P+.85),(D/2-.2,y1,P+.85),.1,.1,'timber')
        k.beam('Dorm_Front_Rail_Low',(D/2-.2,y0,P+.3),(D/2-.2,y1,P+.3),.08,.08,'timber')
        n=int(abs(y1-y0)/.35)
        for i in range(1,n):k.box('Dorm_Front_Baluster',(D/2-.2,y0+(y1-y0)*i/n,P+.57),(.05,.05,.55),'timber')
    # Thatch roof: two thick slopes with a rounded ridge roll and visible rafter tails.
    ov,thick=.85,.32
    for s in (-1,1):
        e=s*(D/2+ov);v=[]
        for yy in (-L/2-ov,L/2+ov):
            v+= [(0,yy,P+H+1.85),(e,yy,P+H+.15),(e,yy,P+H+.15-thick),(0,yy,P+H+1.85-thick)]
        k.mesh('Dorm_Thatch_Slope',v,[(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5),(0,3,2,1),(4,5,6,7)],'thatch',group='removable_roof')
        for i in range(14):
            yy=-L/2+.2+i*(L-.4)/13
            k.beam('Dorm_Rafter_Tail',(s*(D/2-.1),yy,P+H+.5),(s*(D/2+ov-.1),yy,P+H+.1),.08,.1,'timber').__setitem__('part','removable_roof')
        k.tube('Dorm_Thatch_Eave_Roll',[(e,-L/2-ov+.05,P+H+.08),(e,L/2+ov-.05,P+H+.08)],.13,'thatch',8,'removable_roof')
    k.tube('Dorm_Thatch_Ridge_Roll',[(0,-L/2-ov,P+H+1.92),(0,L/2+ov,P+H+1.92)],.22,'thatch_dark').__setitem__('part','removable_roof')
    for y in (-L/2-ov+.4,-L/4,L/4,L/2+ov-.4):
        k.box('Dorm_Ridge_Tie',(0,y,P+H+1.92),(.6,.08,.5),'timber').__setitem__('part','removable_roof')
    # Interior: raised sleeping platform along the back wall with bedding, low table, chest, lantern.
    k.box('Dorm_Sleeping_Platform',(-D/2+1.2,0,P+.25),(2.0,L-.8,.5),'board',.02)
    k.box('Dorm_Platform_Edge',(-D/2+2.2,0,P+.25),(.1,L-.8,.5),'timber')
    for i in range(6):
        y=-L/2+1.1+i*1.55
        k.box('Dorm_Bed_Mat',(-D/2+1.2,y,P+.53),(1.8,.95,.06),'straw',.01)
        k.box('Dorm_Bedding_Quilt',(-D/2+1.05,y,P+.62),(1.25,.85,.12),'cloth',.04)
        k.box('Dorm_Pillow',(-D/2+.45,y,P+.62),(.3,.55,.14),'plaster',.04)
    k.box('Dorm_Low_Table',(.6,-1.,P+.32),(1.,.7,.06),'board',.01)
    for dx in (-.42,.42):
        for dy in (-.28,.28):k.box('Dorm_Table_Leg',(.6+dx,-1.+dy,P+.15),(.06,.06,.3),'timber')
    k.box('Dorm_Storage_Chest',(-D/2+.6,L/2-.75,P+.3),(.8,.6,.5),'timber',.02)
    k.box('Dorm_Chest_Lid',(-D/2+.6,L/2-.75,P+.58),(.84,.64,.08),'board',.02)
    for y in (-2.2,2.2):
        k.tube('Dorm_Lantern_Cord',[(D/2-.3,y,P+H),(D/2-.3,y,P+H-.45)],.01,'timber',5)
        k.cyl('Dorm_Hanging_Lantern',(D/2-.3,y,P+H-.95),.17,.5,'paper',10,.17)
        k.cyl('Dorm_Lantern_Cap',(D/2-.3,y,P+H-.47),.12,.04,'timber',10)
    root.rotation_euler=(0,0,0)   # local +X already faces east (the path)
    return root

# ------------------------------------------------------------------ herb garden
def _herb(k,name,c,rng,bloom):
    """Rosette of broad leaves, optionally with a flower spike."""
    x,y,z=c;v=[];f=[];n=rng.randint(7,10)
    for i in range(n):
        a=i*2*math.pi/n+rng.uniform(-.2,.2);L=rng.uniform(.36,.52);w=rng.uniform(.11,.16);lift=rng.uniform(.2,.45)
        d=Vector((math.cos(a),math.sin(a),0));s=Vector((-d.y,d.x,0))
        base=Vector((x,y,z));mid=base+d*L*.5+Vector((0,0,lift));tip=base+d*L+Vector((0,0,lift*.55))
        o=len(v);v+= [tuple(base),tuple(mid+s*w),tuple(tip),tuple(mid-s*w)];f.append((o,o+1,o+2,o+3))
    leaf=k.mesh(name,v,f,'herb' if rng.random()<.6 else 'herb_light',True)
    if bloom:
        h=rng.uniform(.35,.5);k.tube(name+'_Stem',[(x,y,z),(x,y,z+h)],.012,'herb',5)
        k.cyl(name+'_Bloom',(x,y,z+h),.045,.12,'bloom',8,.02)
    return leaf

def herb_garden(coll,mats,ground):
    root=_root(coll,'Camp_HerbGarden',(*GARDEN,ground));k=Kit(coll,root,mats);rng=random.Random(1532)
    W,L,h=5.,7.5,.38    # x width, y length, bed height
    k.box('Garden_Gravel_Apron',(0,0,.03),(W+1.4,L+1.4,.06),'paving_dark')
    for s in (-1,1):
        k.box('Garden_Bed_Frame_Long',(s*W/2,0,h/2),(.12,L,h),'board',.01)
        k.box('Garden_Bed_Frame_Short',(0,s*L/2,h/2),(W,.12,h),'board',.01)
    for xs in (-W/2,W/2):
        for ys in (-L/2,L/2):k.box('Garden_Bed_Corner_Post',(xs,ys,h/2+.05),(.16,.16,h+.1),'timber',.01)
    k.box('Garden_Bed_Soil',(0,0,h-.06),(W-.12,L-.12,.1),'soil')
    for i in (-1,1):k.box('Garden_Bed_Divider',(i*W/6,0,h-.02),(.06,L-.15,.08),'board')
    for col in range(3):
        for row in range(6):
            x=-W/3+col*W/3;y=-L/2+.7+row*(L-1.4)/5
            _herb(k,'Garden_Herb_%d_%d'%(col,row),(x+rng.uniform(-.08,.08),y+rng.uniform(-.08,.08),h-.01),rng,bloom=(col==1 and row%2==0) or rng.random()<.15)
    # Bamboo fence with a gate gap facing the path (west side, toward -X).
    fx,fy=W/2+.6,L/2+.6
    edges=[((-fx,-fy),(fx,-fy)),((fx,-fy),(fx,fy)),((fx,fy),(-fx,fy)),((-fx,fy),(-fx,.7)),((-fx,-.7),(-fx,-fy))]
    for (x0,y0),(x1,y1) in edges:
        n=max(2,int(math.hypot(x1-x0,y1-y0)/1.2))
        for i in range(n+1):
            t=i/n;k.cyl('Garden_Fence_Post',(x0+(x1-x0)*t,y0+(y1-y0)*t,0),.045,.95,'bamboo',8)
        for z in (.4,.8):k.tube('Garden_Fence_Rail',[(x0,y0,z),(x1,y1,z)],.03,'bamboo',6)
    for y in (-.7,.7):k.cyl('Garden_Gate_Post',(-fx,y,0),.07,1.15,'timber',8)
    k.beam('Garden_Gate_Lintel',(-fx,-.85,1.15),(-fx,.85,1.15),.1,.12,'timber')
    k.box('Garden_Sign_Board',(-fx-.05,0,1.32),(.04,.7,.28),'board',.01)
    # Water trough and bucket by the gate.
    k.box('Garden_Water_Trough',(-fx-.9,-1.7,.25),(.55,1.4,.5),'board',.02)
    k.box('Garden_Trough_Water',(-fx-.9,-1.7,.46),(.42,1.27,.04),'water')
    k.cyl('Garden_Wooden_Bucket',(-fx-.9,-.7,0),.2,.38,'board',12,.23)
    k.cyl('Garden_Bucket_Hoop',(-fx-.9,-.7,.27),.225,.04,'bronze',12)
    return root

# ------------------------------------------------------------------ hex pavilion
def hex_pavilion(coll,mats,ground,radius=2.1):
    """Three-step hexagonal plinth, six columns, benches, bracket sets and a curved blue-green tiled roof."""
    root=_root(coll,'Camp_HexPavilion',(*PAVILION,ground));k=Kit(coll,root,mats)
    R=radius;steps=[(R+.75,0,.16),(R+.5,.16,.16),(R+.28,.32,.16)];top=.48
    for i,(r,z,h) in enumerate(steps):
        k.cyl('Pavilion_Plinth_Tier_%d'%i,(0,0,z),r,h,'stone_base' if i<2 else 'paving',6)
    # Corners at 0,60,...deg so the edges centred on 90/270 deg (i=1,4) face the north-south path and stay open.
    pts=[Vector((R*math.cos(i*math.pi/3),R*math.sin(i*math.pi/3),0)) for i in range(6)]
    H=2.55
    for i,p in enumerate(pts):
        k.cyl('Pavilion_Column_Base',(p.x,p.y,top),.19,.16,'stone_base',8)
        k.cyl('Pavilion_Column',(p.x,p.y,top),.11,H,'timber',12)
        k.cyl('Pavilion_Column_Band',(p.x,p.y,top+.25),.125,.06,'bronze',12)
        q=pts[(i+1)%6];k.beam('Pavilion_Ring_Beam',(p.x,p.y,top+H),(q.x,q.y,top+H),.16,.2,'timber')
        k.beam('Pavilion_Lintel_Board',(p.x*.98,p.y*.98,top+H-.32),(q.x*.98,q.y*.98,top+H-.32),.06,.18,'board')
        for zz,L in ((top+H+.12,.44),(top+H+.24,.6)):   # stacked bracket arms (dougong)
            t=Vector((-p.y,p.x,0)).normalized()*L/2;k.beam('Pavilion_Bracket',(p.x-t.x,p.y-t.y,zz),(p.x+t.x,p.y+t.y,zz),.1,.11,'timber')
        k.box('Pavilion_Bracket_Block',(p.x,p.y,top+H+.36),(.24,.24,.14),'timber',.01)
        if i in (1,4):continue   # north and south openings stay clear (path axis)
        a,b=p.lerp(q,.15),p.lerp(q,.85)
        k.beam('Pavilion_Bench_Seat',(a.x*.9,a.y*.9,top+.45),(b.x*.9,b.y*.9,top+.45),.36,.07,'board')
        k.beam('Pavilion_Bench_Back',(a.x,a.y,top+.8),(b.x,b.y,top+.8),.06,.1,'timber')
        for t in (.2,.8):
            m=p.lerp(q,t);k.box('Pavilion_Bench_Leg',(m.x*.9,m.y*.9,top+.22),(.08,.08,.44),'timber')
    radii=[.08,.35,.8,1.45,2.15,2.75,3.05];heights=[4.55,4.38,4.0,3.62,3.32,3.2,3.32]
    def rp(side,j,u):
        a=side*math.pi/3;b=a+math.pi/3;r=radii[j]
        return Vector((r*((1-u)*math.cos(a)+u*math.cos(b)),r*((1-u)*math.sin(a)+u*math.sin(b)),heights[j]+.18*(2*u-1)**4*(r/3.05)**3))
    for side in range(6):
        cols=12;v=[tuple(rp(side,j,i/cols)) for j in range(len(radii)) for i in range(cols+1)]
        f=[(j*(cols+1)+i,(j+1)*(cols+1)+i,(j+1)*(cols+1)+i+1,j*(cols+1)+i+1) for j in range(len(radii)-1) for i in range(cols)]
        o=k.mesh('Pavilion_Roof_Sector',v,f,'tile',True,'removable_roof');o.modifiers.new('Thick','SOLIDIFY').thickness=.08
        for i in range(0,13):
            k.tube('Pavilion_Tile_Rib',[tuple(rp(side,j,i/12)+Vector((0,0,.03))) for j in range(1,len(radii))],.022,'tile_ridge',6,'removable_roof')
        k.tube('Pavilion_Hip_Ridge',[tuple(rp(side,j,0)+Vector((0,0,.06))) for j in range(len(radii))],.06,'jade',8,'removable_roof')
        k.tube('Pavilion_Eave_Fascia',[tuple(rp(side,len(radii)-1,i/12)) for i in range(13)],.06,'timber',8,'removable_roof')
        for i in (2,5,8,11):
            k.tube('Pavilion_Rafter',[tuple(rp(side,j,i/12)-Vector((0,0,.16))) for j in range(3,7)],.045,'timber',6,'removable_roof')
    for j,(r,z,h) in enumerate([(.2,4.5,.1),(.13,4.6,.16),(.06,4.76,.2)]):k.cyl('Pavilion_Finial',(0,0,z),r,h,'bronze',10).__setitem__('part','removable_roof')
    return root

# ------------------------------------------------------------------ paths and lanterns
def _slab_row(k,a,b,width,ground_at,rng,name):
    a,b=Vector(a),Vector(b);d=b-a;L=d.length;dn=d.normalized();side=Vector((-dn.y,dn.x))
    t=0.;n=0
    while t<L-.05:
        sl=min(rng.uniform(.75,1.05),L-t);cols=2 if width>1.6 else 1
        for c in range(cols):
            w=width/cols;off=(c-(cols-1)/2)*w+rng.uniform(-.03,.03)
            cx=a+dn*(t+sl/2)+side*off;z=ground_at(cx.x,cx.y)
            if z is None:continue
            k.box('%s_%03d'%(name,n),(cx.x,cx.y,z+.04),(sl-.06,w-.06,.12),'paving',.015,math.atan2(dn.y,dn.x));n+=1
        t+=sl
    return n

def paths(coll,mats,ground_at):
    root=_root(coll,'Camp_Paths',(0,0,0));k=Kit(coll,root,mats);rng=random.Random(1533)
    n=_slab_row(k,PATH_MAIN[0],PATH_MAIN[1],2.2,ground_at,rng,'Path_Main_Slab')
    n+=_slab_row(k,PATH_BRANCH[0],(-1.2,-47.),1.5,ground_at,rng,'Path_West_Slab')
    n+=_slab_row(k,(1.2,-47.),PATH_BRANCH[1],1.5,ground_at,rng,'Path_East_Slab')
    lant=0
    for y in range(-18,-62,-9):
        for s in (-1,1):
            x=s*1.75;z=ground_at(x,y+s*2.)
            if z is None or abs(y+47)<2.5:continue
            yy=y+s*2.
            k.box('Lantern_Post_Base',(x,yy,z+.12),(.36,.36,.24),'stone_base',.02)
            k.box('Lantern_Post_Shaft',(x,yy,z+.62),(.18,.18,.8),'stone_base',.01)
            k.box('Lantern_Post_Lamp',(x,yy,z+1.17),(.3,.3,.3),'paper',.02)
            k.box('Lantern_Post_Cap',(x,yy,z+1.38),(.44,.44,.1),'tile',.02);lant+=1
    return root,n,lant
