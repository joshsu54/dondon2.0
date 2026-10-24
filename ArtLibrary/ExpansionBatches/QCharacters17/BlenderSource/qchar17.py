"""Q-version (chibi, ~2 heads tall) character kit for QCharacters17.
Every character is assembled from the same body, face, hair, outfit and prop parts so proportions and style match.
Units metres, front -Y, origin bottom centre, base height 1.25 m (head ~ half). A-pose arms (~35 deg) for later rigging.
Palette follows SectCore04: teal-green, warm timber, pale stone, pale jade, soft light.
"""
import bpy,bmesh,math
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

# ------------------------------------------------------------------ materials
def mat(name,c,rough=.75,spec=.25,sss=0.):
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=rough;b.inputs['Specular IOR Level'].default_value=spec
    if sss:
        b.inputs['Subsurface Weight'].default_value=sss;b.inputs['Subsurface Radius'].default_value=(.6,.25,.15)
    return m

COLORS={'skin':(.86,.60,.47),'skin_tan':(.74,.47,.33),'blush':(.93,.45,.45),'iris':(.07,.04,.03),'iris_jade':(.04,.18,.14),
        'eye_hi':(1.,1.,1.),'mouth':(.42,.12,.10),'lash':(.03,.02,.02),
        'hair_black':(.035,.028,.026),'hair_brown':(.12,.06,.03),'hair_white':(.80,.80,.76),'hair_grey':(.45,.44,.42),
        'teal':(.06,.24,.22),'teal_light':(.18,.42,.38),'white_robe':(.78,.78,.72),'cream':(.70,.64,.50),'jade':(.10,.36,.28),
        'timber':(.16,.065,.028),'leather':(.20,.09,.035),'ochre':(.45,.26,.07),'plum':(.30,.12,.18),'sage':(.30,.40,.24),
        'stone':(.36,.37,.33),'charcoal':(.08,.08,.08),'iron':(.10,.11,.11),'brass':(.40,.28,.08),'straw':(.55,.40,.18),
        'rust':(.40,.12,.06),'indigo':(.06,.09,.20),'pants_dark':(.07,.08,.08),'shoe':(.06,.04,.03),'red':(.55,.08,.06),
        'herb':(.10,.30,.08),'wood':(.30,.16,.07)}
def M(key):
    c=COLORS[key];rough={'iris':.15,'iris_jade':.15,'eye_hi':.2,'hair_black':.6,'hair_brown':.6,'hair_white':.6,'hair_grey':.6,
                        'jade':.35,'iron':.4,'brass':.35}.get(key,.75)
    metal={'iron':.6,'brass':.7}.get(key,0.)
    # Hair specular kept low: with the large studio area lights a 0.35 sheen turned black hair grey-brown.
    spec=.35 if key.startswith(('iris','eye')) else (.12 if key.startswith('hair') else .2)
    m=mat('Q17_'+key,c,rough,spec,.12 if key.startswith('skin') else 0.)
    if metal:next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Metallic'].default_value=metal
    return m

# ------------------------------------------------------------------ geometry kit
class Kit:
    def __init__(s,coll,root):s.coll,s.root,s.count=coll,root,0
    def obj(s,name,bm,key,smooth=True,group=None):
        me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.materials.append(M(key))
        for p in me.polygons:p.use_smooth=smooth
        o=bpy.data.objects.new(name,me);s.coll.objects.link(o);o.parent=s.root;s.count+=1
        if group:o['part']=group
        return o
    def ellipsoid(s,name,c,r,key,rot=None,segs=32,rings=16,group=None):
        bm=bmesh.new();m=Matrix.Translation(Vector(c))@(rot or Matrix.Identity(3)).to_4x4()@Matrix.Diagonal((*r,1))
        bmesh.ops.create_uvsphere(bm,u_segments=segs,v_segments=rings,radius=1,matrix=m)
        return s.obj(name,bm,key,group=group)
    def lathe(s,name,prof,key,segs=36,c=(0,0),group=None,bm_only=False):
        """prof: list of (z, rx, ry[, dy]) bottom->top; closed with centre caps."""
        bm=bmesh.new();rings=[]
        for p in prof:
            z,rx,ry=p[:3];dy=p[3] if len(p)>3 else 0.
            rings.append([bm.verts.new((c[0]+rx*math.cos(a),c[1]+dy+ry*math.sin(a),z)) for a in (i*2*math.pi/segs for i in range(segs))])
        for a,b in zip(rings,rings[1:]):
            for i in range(segs):bm.faces.new((a[i],a[(i+1)%segs],b[(i+1)%segs],b[i]))
        for ring,z,flip in ((rings[0],prof[0][0],True),(rings[-1],prof[-1][0],False)):
            ctr=bm.verts.new((c[0],c[1]+(prof[0][3] if len(prof[0])>3 and flip else (prof[-1][3] if len(prof[-1])>3 else 0.)),z))
            for i in range(segs):
                f=(ring[i],ring[(i+1)%segs],ctr) if not flip else (ring[(i+1)%segs],ring[i],ctr)
                bm.faces.new(f)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        return bm if bm_only else s.obj(name,bm,key,group=group)
    def sweep(s,name,pts,rx,ry,key,segs=12,ups=None,cap=True,group=None,closed=False):
        """Elliptic section swept along pts; rx/ry scalar or per point; ups gives the ry (thickness) direction."""
        n=len(pts);pts=[Vector(p) for p in pts];rx=rx if isinstance(rx,(list,tuple)) else [rx]*n;ry=ry if isinstance(ry,(list,tuple)) else [ry]*n
        bm=bmesh.new();rings=[]
        for j,p in enumerate(pts):
            if closed:t=(pts[(j+1)%n]-pts[j-1]).normalized()
            else:t=(pts[min(j+1,n-1)]-pts[max(j-1,0)]).normalized()
            up=Vector(ups[j]) if ups else (Vector((0,-1,0)) if abs(t.z)>.7 else Vector((0,0,1)))
            u=(up-t*up.dot(t));u=u.normalized() if u.length>1e-6 else t.orthogonal().normalized();w=t.cross(u).normalized()
            rings.append([bm.verts.new(p+w*rx[j]*math.cos(a)+u*ry[j]*math.sin(a)) for a in (i*2*math.pi/segs for i in range(segs))])
        for j in range(n if closed else n-1):
            a,b=rings[j],rings[(j+1)%n]
            for i in range(segs):bm.faces.new((a[i],a[(i+1)%segs],b[(i+1)%segs],b[i]))
        if cap and not closed:
            bm.faces.new(list(reversed(rings[0])));bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        return s.obj(name,bm,key,group=group)

def frame(n,ref=Vector((1,0,0))):
    """Rotation whose Z = n (outward), X ~ ref."""
    n=n.normalized();x=(ref-n*ref.dot(n)).normalized();y=n.cross(x);return Matrix((x,y,n)).transposed()

def taper(a,b,n):return [a+(b-a)*(i/(n-1)) for i in range(n)]

# ------------------------------------------------------------------ body
class Body:
    """Head/torso landmarks for the 2-head chibi; girth widens torso and limbs."""
    def __init__(s,girth=1.,head=1.):
        s.g=girth;s.hs=head
        s.C=Vector((0,0,.94));s.hr=Vector((.30,.275,.285))*head        # head centre and radii
        s.neck=.66;s.waist=.40;s.hip=.30
        s.shoulder=lambda sx:Vector((sx*.13*girth,0,.615))
        s.hand=lambda sx:Vector((sx*(.27+.03*(girth-1)),-.02,.40))

def build_head(k,b,skin='skin'):
    bm=bmesh.new();C=b.C;R=b.hr
    bmesh.ops.create_uvsphere(bm,u_segments=48,v_segments=24,radius=1,matrix=Matrix.Translation(C)@Matrix.Diagonal((*R,1)))
    for v in bm.verts:      # soft round cheeks and a small chin: narrow the lower half, push cheeks slightly forward
        t=max(0.,(C.z-v.co.z)/R.z)
        v.co.x=C.x+(v.co.x-C.x)*(1-.14*t**1.6)
        if v.co.y<C.y:v.co.y=C.y+(v.co.y-C.y)*(1+.05*math.sin(min(1.,t*1.6)*math.pi))
    tree=BVHTree.FromBMesh(bm);b.head_tree=tree
    k.obj('Head',bm,skin)
    for sx in (-1,1):k.ellipsoid('Ear',(sx*R.x*.97,C.y+.01,C.z-.02),(.035,.05,.06),skin,segs=16,rings=8)
    k.lathe('Neck',[(b.neck-.04,.06,.055),(C.z-R.z*.7,.06,.055)],skin,segs=16)

def on_head(b,x,z,outset=0.):
    hit,n,_,_=b.head_tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))
    return hit+n*outset,n

def build_face(k,b,iris='iris',brow='hair_black',style='round',blush=True):
    C=b.C;s=b.hs
    for sx in (-1,1):
        p,n=on_head(b,sx*.105*s,C.z-.035*s);F=frame(n);h=.058;w=.038
        if style=='sleepy':   # smiling closed eyes: an upward arc (^^) instead of an iris
            arc=[p+F@Vector((w*1.05*math.cos(a)*s,(.022*math.sin(a)-.006)*s,.006)) for a in taper(math.radians(170),math.radians(10),7)]
            k.sweep('Eye_Closed',arc,[.005,.007,.008,.008,.008,.007,.005],.004,'lash',segs=8,ups=[n]*7)
        else:
            k.ellipsoid('Eye_Iris',p-n*.004,(w*s,h*s,.014),iris,rot=F,segs=24,rings=12)
        if style!='sleepy':   # same light direction (upper left) on both eyes
            k.ellipsoid('Eye_Highlight',p+F@Vector((-.012,.022,.011))*s,(.013*s,.016*s,.006),'eye_hi',rot=F,segs=12,rings=6)
            k.ellipsoid('Eye_Highlight_Small',p+F@Vector((.012,-.022,.011))*s,(.006*s,.007*s,.004),'eye_hi',rot=F,segs=10,rings=6)
            inner,outer=(math.radians(165),math.radians(-15)) if sx>0 else (math.radians(15),math.radians(195))
            arc=[p+F@Vector((w*1.08*math.cos(a)*s,(h*1.02*math.sin(a)+.004)*s,.006)) for a in taper(inner,outer,7)]
            k.sweep('Eye_Lash',arc,[.005,.006,.007,.007,.008,.009,.011],.004,'lash',segs=8,ups=[n]*7)   # thicker toward the outer corner
        bp,bn=on_head(b,sx*.105*s,C.z+.075*s);BF=frame(bn)
        k.sweep('Eyebrow',[bp+BF@Vector((dx*s,dz*s,.004)) for dx,dz in ((-.032,-.004),(0,.006),(.032,-.002))],.006,.0035,brow,segs=8,ups=[bn]*3)
        if blush:
            cp,cn=on_head(b,sx*.175*s,C.z-.105*s);k.ellipsoid('Blush',cp-cn*.003,(.034*s,.018*s,.006),'blush',rot=frame(cn),segs=16,rings=8)
    mp,mn=on_head(b,0,C.z-.155*s);MF=frame(mn)
    k.sweep('Mouth',[mp+MF@Vector((dx*s,(-.007*(1-(dx/.022)**2))*s,.003)) for dx in taper(-.022,.022,7)],.004,.003,'mouth',segs=8,ups=[mn]*7)

def build_limbs(k,b,sleeve='teal',cuff='white_robe',skin='skin',sleeve_style='wide',pants='pants_dark',shoes='shoe',leg_show=.24):
    g=b.g
    for sx in (-1,1):
        sh=b.shoulder(sx);hd=b.hand(sx);el=sh.lerp(hd,.5)+Vector((sx*.012,0,0))
        path=[sh+Vector((-sx*.02,0,.01)),sh.lerp(el,.5),el,el.lerp(hd,.55),hd+Vector((0,0,.045))]
        if sleeve_style=='wide':        # hanfu sleeve flaring to a wide cuff
            k.sweep('Sleeve',path,[.062*g,.064*g,.070*g,.082*g,.092*g],[.060*g,.060*g,.066*g,.078*g,.088*g],sleeve,segs=20)
            k.sweep('Sleeve_Cuff',[path[-1]-(path[-1]-path[-2]).normalized()*.012,path[-1]+(path[-1]-path[-2]).normalized()*.008],.096*g,.092*g,cuff,segs=20)
        elif sleeve_style=='short':     # rolled sleeve to the elbow, bare forearm
            k.sweep('Sleeve',path[:3],[.064*g,.066*g,.064*g],[.06*g,.06*g,.058*g],sleeve,segs=18)
            k.sweep('Sleeve_Roll',[el-(el-sh).normalized()*.02,el+(el-sh).normalized()*.012],.072*g,.068*g,cuff,segs=18)
            k.sweep('Forearm',[el,el.lerp(hd,.5),hd+Vector((0,0,.04))],[.046*g,.044*g,.040*g],[.044*g,.042*g,.038*g],skin,segs=16)
        hc=hd+Vector((sx*.005,-.005,0))
        k.ellipsoid('Hand',hc,(.046*g,.040*g,.050*g),skin,segs=20,rings=10)
        k.ellipsoid('Thumb',hc+Vector((-sx*.010,-.035,.012)),(.016,.018,.022),skin,segs=12,rings=8)
    for sx in (-1,1):
        x=sx*.072*g
        k.lathe('Leg',[(.06,.058*g,.058),(leg_show+.04,.062*g,.062),(b.hip,.066*g,.064)],pants,c=(x,0),segs=20)
        k.ellipsoid('Shoe',(x,-.018,.045),(.068*g,.098,.055),shoes,segs=24,rings=12)
        k.ellipsoid('Shoe_Sole',(x,-.018,.018),(.072*g,.10,.02),'shoe',segs=24,rings=8)

# ------------------------------------------------------------------ outfit
def robe_profile(b,hem=.20,flare=1.,belly=0.):
    g=b.g;p=[(hem,.175*g*flare,.15*flare),(hem+.06,.170*g*flare,.145*flare)]
    if hem<b.hip-.04:p.append(((hem+b.hip)/2,.165*g*(1+.5*(flare-1)),.14))
    p+=[(b.hip,.160*g,.135+belly*.5),(b.waist,.150*g,.128+belly),(.50,.158*g,.132+belly*.7),(.58,.155*g,.128),(.63,.140*g,.118),(b.neck,.10*g,.085),(b.neck+.03,.07*g,.06)]
    return p

def build_robe(k,b,outer='teal',inner='white_robe',trim='white_robe',belt='leather',hem=.20,flare=1.,belly=0.,sash_tails=True,collar=True,belt_out=0.):
    """belt_out pushes the belt, knot and tails outwards so they sit over an apron (apron itself sits over the lapel)."""
    prof=robe_profile(b,hem,flare,belly);robe=k.lathe('Robe',prof,outer,segs=48)
    bm=bmesh.new();bm.from_mesh(robe.data);tree=BVHTree.FromBMesh(bm);bm.free();b.robe_tree=tree
    def surf(x,z,out=.006):
        hit,n,_,_=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)));return (hit+n*out,n) if hit else (Vector((x,-.13,z)),Vector((0,-1,0)))
    g=b.g
    if collar:   # crossed collar: inner V, then the overlapping lapel from the wearer's right shoulder to the left waist
        vpts=[surf(x,z,.004) for x,z in ((-.05*g,b.neck+.01),(0,b.waist+.08),(.05*g,b.neck+.01))]
        k.sweep('Collar_Inner',[p for p,_ in vpts],.022,.006,inner,segs=10,ups=[n for _,n in vpts])
        lap=[surf(x,z,.008) for x,z in ((.07*g,b.neck+.02),(.04*g,.58),(0,.52),(-.05*g,b.waist+.04),(-.075*g,b.waist+.005))]
        k.sweep('Collar_Lapel',[p for p,_ in lap],.024,.008,trim,segs=10,ups=[n for _,n in lap])
        # Neckband: continues the lapel round the back of the neck and down the other side to the chest.
        z=b.neck+.025;band=[]
        for a in taper(math.radians(-60),math.radians(240),15):
            band.append(Vector((.088*g*math.cos(a),.075*math.sin(a)+.004,z+.012*math.sin(a))))
        band+= [surf(-.06*g,.60,.008)[0],surf(-.035*g,.55,.008)[0]]
        k.sweep('Collar_Neckband',band,.022,.009,trim,segs=10,ups=[Vector((math.cos(math.atan2(p.y,p.x)),math.sin(math.atan2(p.y,p.x)),0)) for p in band])
    hemring=[Vector(((prof[0][1]+.004)*math.cos(a),(prof[0][2]+.004)*math.sin(a),hem+.025)) for a in taper(0,2*math.pi,49)[:-1]]
    k.sweep('Hem_Trim',hemring,.022,.008,trim,segs=8,ups=[Vector((math.cos(a),math.sin(a),0)) for a in taper(0,2*math.pi,49)[:-1]],closed=True)
    # Belt / sash with a knot and two tails in front.
    bz=b.waist+.01;wr=[(prof[i][1],prof[i][2]) for i in range(len(prof)) if abs(prof[i][0]-b.waist)<1e-6][0]
    ring=[Vector(((wr[0]+.012+belt_out)*math.cos(a),(wr[1]+.012+belt_out)*math.sin(a),bz)) for a in taper(0,2*math.pi,49)[:-1]]
    k.sweep('Belt',ring,.032,.010,belt,segs=8,ups=[Vector((math.cos(a),math.sin(a),0)) for a in taper(0,2*math.pi,49)[:-1]],closed=True)
    kp,kn=surf(.03*g,bz,.016+belt_out);k.ellipsoid('Belt_Knot',kp,(.026,.02,.024),belt,rot=frame(kn),segs=16,rings=8)
    if sash_tails:
        for dx,L in ((.02,.13),(.045,.10)):
            pts=[surf(dx*g+.01*i,bz-.01-L*i/4,.014+belt_out)[0] for i in range(5)]
            k.sweep('Belt_Tail',pts,[.016,.017,.018,.018,.016],.005,belt,segs=8,ups=[Vector((0,-1,0))]*5)
    return robe,surf

def front_panel(k,name,surf,x0,x1,z0,z1,key,out=.012,nx=8,nz=10,thick=.008,group=None):
    """Curved plate following the robe front (apron)."""
    bm=bmesh.new();grid=[]
    for j in range(nz+1):
        z=z1+(z0-z1)*j/nz;row=[]
        for i in range(nx+1):
            p,n=surf(x0+(x1-x0)*i/nx,z,out);row.append(bm.verts.new(p))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):bm.faces.new((grid[j][i],grid[j][i+1],grid[j+1][i+1],grid[j+1][i]))
    me_o=k.obj(name,bm,key,group=group);md=me_o.modifiers.new('Thickness','SOLIDIFY');md.thickness=thick;md.offset=1
    return me_o

def capelet(k,b,key,trim=None,z0=.50,flare=1.18):
    g=b.g;k.lathe('Capelet',[(z0,.175*g*flare,.15*flare),(z0+.05,.17*g*flare,.145*flare),(.60,.165*g,.14),(.645,.15*g,.128),(b.neck+.015,.11*g,.092),(b.neck+.035,.08*g,.068)],key,segs=48)
    if trim:
        ring=[Vector(((.175*g*flare+.004)*math.cos(a),(.15*flare+.004)*math.sin(a),z0+.012)) for a in taper(0,2*math.pi,49)[:-1]]
        k.sweep('Capelet_Trim',ring,.014,.007,trim,segs=8,ups=[Vector((math.cos(a),math.sin(a),0)) for a in taper(0,2*math.pi,49)[:-1]],closed=True)

# ------------------------------------------------------------------ hair
def hair_cap(k,b,key,hairline=.30,side_low=-.40,back_low=-.55,scale=1.07):
    C=b.C;R=b.hr*scale;bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=64,v_segments=32,radius=1,matrix=Matrix.Translation(C+Vector((0,.012,.012)))@Matrix.Diagonal((*R,1)))
    # Instead of deleting faces (stair-stepped edge), sink the opening smoothly inside the head: the visible
    # hairline becomes a continuous curve. Opening = front oval between the temples, plus everything below the nape line.
    C2=C+Vector((0,.012,.012))
    def sstep(x):x=max(0.,min(1.,x));return x*x*(3-2*x)
    for v in bm.verts:
        d=v.co-C2;d=Vector((d.x/R.x,d.y/R.y,d.z/R.z))
        front=min((-.12-d.y)/.10,(.80-abs(d.x))/.10,(hairline+.25*d.x*d.x-d.z)/.08)
        low=side_low+(back_low-side_low)*max(0.,min(1.,(d.y+.12)/.6))
        f=sstep(max(front,(low-d.z)/.08)*1.+.5)
        if f>0:v.co=C2+(v.co-C2)*(1-f*.30)   # 0.70 x cap radius ~ 0.75 x head: inside even the narrowed jaw
    o=k.obj('Hair_Cap',bm,key);md=o.modifiers.new('Thickness','SOLIDIFY');md.thickness=.018;md.offset=1
    nape_strands(k,b,key,side_low,back_low)
    return o

def nape_strands(k,b,key,side_low,back_low,n=9):
    """Broad rounded locks round the lower rim of the cap, alternating length, so the back is neither a flat
    bowl cut nor a row of icicles."""
    for i in range(n):
        a=math.radians(-25+230*i/(n-1))          # from the right temple round the back to the left temple
        dx,dy=math.cos(a),math.sin(a)
        if dy<-.15:continue
        low=side_low+(back_low-side_low)*max(0.,min(1.,(dy+.12)/.6))
        top=_hair_dir(b,(dx*.95,dy*.95,low+.30),1.07);rim=_hair_dir(b,(dx,dy,low+.02),1.08)
        L=.045+.025*(i%2);tip=rim+Vector((dx*.015,dy*.022,-L))
        k.sweep('Hair_Nape',[top,rim,rim.lerp(tip,.6),tip],[.07,.066,.05,.022],[.022,.022,.02,.014],key,segs=12,ups=[Vector((dx,dy,0))]*4)

def _hair_dir(b,d,out=1.075):
    d=Vector(d).normalized();return b.C+Vector((0,.012,.012))+Vector((d.x*b.hr.x,d.y*b.hr.y,d.z*b.hr.z))*out

def bangs(k,b,key,n=7,span=.62,tip=.10,length=1.,part=None):
    """Chunky anime fringe strands from the crown down over the forehead."""
    for i in range(n):
        u=-1+2*i/(n-1);x=u*span
        if part is not None and abs(u-part)<.12:continue
        d0=Vector((x*.35,-.15,1.));d1=Vector((x*1.05,-1.,tip+.12*abs(u)**2-.06*length*(1-abs(u))))
        pts=[_hair_dir(b,d0.lerp(d1,t),1.07+.03*t) for t in taper(0,1,8)]
        ups=[(p-b.C).normalized() for p in pts]
        w=[.055,.055,.052,.048,.042,.034,.022,.006];k.sweep('Hair_Bang',pts,w,[.022]*7+[.008],key,segs=10,ups=ups)

def side_locks(k,b,key,length=.30,width=.045):
    for sx in (-1,1):
        top=_hair_dir(b,(sx*.85,-.45,.25),1.06);mid=_hair_dir(b,(sx*.98,-.35,-.35),1.10)
        pts=[top,mid,mid+Vector((sx*.01,-.01,-length*.5)),mid+Vector((sx*.025,-.02,-length))]
        k.sweep('Hair_SideLock',pts,[width,width,width*.8,.008],[.022,.022,.02,.006],key,segs=10,ups=[Vector((sx,0,0))]*4)

def bun(k,b,key,d,size=.11,band=None,pin=None):
    p=_hair_dir(b,d,1.12);n=(p-b.C).normalized()
    k.ellipsoid('Hair_Bun',p+n*size*.55,(size,size,size*.9),key,rot=frame(n),segs=28,rings=14)
    if band:
        F=frame(n);ring=[p+n*size*.05+F@Vector((size*.75*math.cos(a),size*.75*math.sin(a),0)) for a in taper(0,2*math.pi,25)[:-1]]
        k.sweep('Hair_Band',ring,.018,.012,band,segs=8,ups=[n]*24,closed=True)
    if pin:
        a=p+n*size*.55+Vector((-size*1.5,0,.02));c=p+n*size*.55+Vector((size*1.5,0,-.03))
        k.sweep('Hairpin',[a,c],.008,.008,pin[0],segs=8);k.ellipsoid('Hairpin_Bead',a,(.018,.018,.018),pin[1],segs=12,rings=8)
    return p+n*size*.55

def ponytail(k,b,key,band=None,length=.42,high=True):
    tie=_hair_dir(b,(0,.75,.55 if high else -.1),1.08)
    pts=[tie,tie+Vector((0,.08,.0)),tie+Vector((0,.13,-.10)),tie+Vector((0,.14,-length*.6)),tie+Vector((0,.11,-length))]
    k.sweep('Hair_Ponytail',pts,[.06,.075,.072,.055,.012],[.05,.06,.058,.045,.01],key,segs=16)
    if band:k.sweep('Hair_Tie',[tie+Vector((0,.015,0)),tie+Vector((0,.05,0))],.055,.05,band,segs=16)

def long_back(k,b,key,bottom=.42,width=.20):
    top=_hair_dir(b,(0,.9,.2),1.05);pts=[top,top+Vector((0,.05,-.18)),Vector((0,top.y+.03,(top.z-.18+bottom)/2)),Vector((0,top.y-.02,bottom))]
    k.sweep('Hair_Back',pts,[width,width*1.05,width*.95,width*.75],[.07,.07,.05,.025],key,segs=20,ups=[Vector((0,1,0))]*4)

def beard(k,b,key,length=.22,mustache=True,width=.10):
    p,n=on_head(b,0,b.C.z-.20*b.hs,.004)
    pts=[p+Vector((0,.02,.03)),p+Vector((0,-.02,-.04)),p+Vector((0,-.03,-length*.6)),p+Vector((0,-.01,-length))]
    k.sweep('Beard',pts,[width*.9,width,width*.55,.008],[.05,.06,.04,.006],key,segs=16)
    if mustache:
        mp,mn=on_head(b,0,b.C.z-.12*b.hs,.008)
        for sx in (-1,1):k.sweep('Mustache',[mp,mp+Vector((sx*.04,-.01,-.005)),mp+Vector((sx*.075,-.005,-.04))],[.016,.014,.004],[.010,.009,.003],key,segs=8)

def straw_hat(k,b):
    top=b.C.z+b.hr.z*1.02
    k.lathe('Straw_Hat',[(top-.10,.42,.40),(top-.085,.42,.40),(top-.02,.22,.21),(top+.10,.03,.03),(top+.11,.0,.0)],'straw',segs=48)
    ring=[Vector((.215*math.cos(a),.205*math.sin(a),top-.005)) for a in taper(0,2*math.pi,41)[:-1]]
    k.sweep('Straw_Hat_Band',ring,.018,.006,'rust',segs=8,ups=[Vector((math.cos(a),math.sin(a),0)) for a in taper(0,2*math.pi,41)[:-1]],closed=True)

def skull_cap(k,b,key,knob='red'):
    C=b.C;R=b.hr;bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=48,v_segments=24,radius=1,matrix=Matrix.Translation(C+Vector((0,.01,.03)))@Matrix.Diagonal((R.x*1.06,R.y*1.07,R.z*1.05,1)))
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_center_median().z<C.z+R.z*.30],context='FACES')
    o=k.obj('Skull_Cap',bm,key);md=o.modifiers.new('Thickness','SOLIDIFY');md.thickness=.012;md.offset=1
    k.ellipsoid('Skull_Cap_Knob',(0,.01,C.z+R.z*1.08),(.025,.025,.022),knob,segs=12,rings=8)

def headscarf(k,b,key):
    C=b.C;R=b.hr;bm=bmesh.new()
    C2=C+Vector((0,.02,.02));RR=Vector((R.x*1.10,R.y*1.12,R.z*1.10))
    bmesh.ops.create_uvsphere(bm,u_segments=64,v_segments=32,radius=1,matrix=Matrix.Translation(C2)@Matrix.Diagonal((*RR,1)))
    def sstep(x):x=max(0.,min(1.,x));return x*x*(3-2*x)
    for v in bm.verts:   # smooth opening (face and below the jaw), same approach as hair_cap: sink inside the head
        d=v.co-C2;d=Vector((d.x/RR.x,d.y/RR.y,d.z/RR.z))
        f=sstep(max(min((-.25-d.y)/.10,(.55-d.z)/.08),(-.15-d.z)/.08)+.5)
        if f>0:v.co=C2+(v.co-C2)*(1-f*.32)
    o=k.obj('Headscarf',bm,key);md=o.modifiers.new('Thickness','SOLIDIFY');md.thickness=.015;md.offset=1
    knot=Vector((0,C.y+R.y*1.05,C.z+.02));k.ellipsoid('Headscarf_Knot',knot,(.05,.035,.04),key,segs=16,rings=8)
    for sx in (-1,1):k.sweep('Headscarf_Tail',[knot,knot+Vector((sx*.04,.03,-.08)),knot+Vector((sx*.06,.04,-.15))],[.03,.028,.01],[.008]*3,key,segs=8)

# ------------------------------------------------------------------ props (in the right hand unless noted)
def prop_hammer(k,b):
    h=b.hand(1);top=h+Vector((.02,-.04,.27))
    k.sweep('Hammer_Handle',[h+Vector((0,-.01,-.08)),top],.02,.02,'wood',segs=10)
    k.sweep('Hammer_Head',[top+Vector((-.08,0,0)),top+Vector((.09,0,0))],.048,.044,'iron',segs=14)
    k.sweep('Hammer_Band',[top+Vector((-.02,0,0)),top+Vector((.02,0,0))],.052,.048,'brass',segs=14)
def prop_staff(k,b,top_key='jade'):
    h=b.hand(1)+Vector((.015,-.02,0))
    k.sweep('Staff',[Vector((h.x,h.y,.01)),Vector((h.x,h.y,1.12)),Vector((h.x+.03,h.y,1.20))],[.017,.015,.012],[.017,.015,.012],'wood',segs=10)
    k.ellipsoid('Staff_Gourd',(h.x+.035,h.y,1.17),(.035,.035,.045),'ochre',segs=16,rings=8)
    k.ellipsoid('Staff_Jade',(h.x+.03,h.y,1.23),(.03,.03,.03),top_key,segs=16,rings=8)
def prop_cane(k,b):
    h=b.hand(1)+Vector((.01,-.03,0))
    k.sweep('Cane',[Vector((h.x+.02,h.y,.01)),Vector((h.x,h.y,h.z+.02)),Vector((h.x-.04,h.y,h.z+.06)),Vector((h.x-.07,h.y,h.z+.03))],.014,.014,'wood',segs=10)
def prop_abacus(k,b):
    c=Vector((0,-.21,.46))
    k.sweep('Abacus_Frame',[c+Vector((-.13,0,.06)),c+Vector((.13,0,.06)),c+Vector((.13,0,-.06)),c+Vector((-.13,0,-.06))],.012,.012,'timber',segs=6,closed=True)
    for i in range(7):
        x=-.10+i*.033;k.sweep('Abacus_Rod',[c+Vector((x,0,-.06)),c+Vector((x,0,.06))],.003,.003,'brass',segs=6)
        for z in (.035,-.01,-.03):k.ellipsoid('Abacus_Bead',c+Vector((x,0,z)),(.013,.009,.009),'red' if z>0 else 'timber',segs=10,rings=6)
    k.sweep('Abacus_Bar',[c+Vector((-.13,0,.015)),c+Vector((.13,0,.015))],.008,.008,'timber',segs=6)
def prop_teapot(k,b):
    h=b.hand(1);c=h+Vector((0,-.03,-.075))
    k.ellipsoid('Teapot',c,(.075,.075,.06),'jade',segs=24,rings=12);k.ellipsoid('Teapot_Lid',c+Vector((0,0,.055)),(.035,.035,.015),'jade',segs=16,rings=6)
    k.sweep('Teapot_Spout',[c+Vector((-.06,-.02,0)),c+Vector((-.10,-.03,.04)),c+Vector((-.115,-.03,.06))],[.016,.012,.009],[.016,.012,.009],'jade',segs=10)
    k.sweep('Teapot_Handle',[c+Vector((.06,0,.03)),c+Vector((.10,0,.02)),c+Vector((.095,0,-.03)),c+Vector((.06,0,-.02))],.008,.008,'timber',segs=8)
def prop_axe(k,b):
    h=b.hand(1);top=h+Vector((.01,-.02,.07));low=h+Vector((.05,-.02,-.30))   # hanging at the side, blade outward
    k.sweep('Axe_Handle',[top,low],.018,.018,'wood',segs=10)
    k.sweep('Axe_Blade',[low+Vector((0,0,.06)),low+Vector((.12,0,.03))],[.012,.012],[.045,.075],'iron',segs=12,ups=[Vector((0,0,1))]*2)
    k.sweep('Axe_Edge',[low+Vector((.115,0,.03)),low+Vector((.13,0,.03))],.010,.08,'stone',segs=10,ups=[Vector((0,0,1))]*2)
def prop_basket_back(k,b):
    c=Vector((0,.25,.50))
    k.lathe('Back_Basket',[(c.z-.17,.10,.08),(c.z-.15,.12,.10),(c.z+.10,.16,.13),(c.z+.12,.165,.135)],'straw',c=(0,c.y),segs=28)
    for x in (-.06,0,.06):k.sweep('Basket_Herb',[Vector((x,c.y,c.z+.10)),Vector((x*1.6,c.y+.03,c.z+.24))],[.02,.035],[.02,.035],'herb',segs=10)
    for sx in (-1,1):k.sweep('Basket_Strap',[Vector((sx*.10,c.y-.04,c.z+.10)),Vector((sx*.10,.02,.66)),Vector((sx*.09,-.11,.60)),Vector((sx*.10,-.13,.46))],.014,.006,'leather',segs=8)
def prop_sword_back(k,b):
    a=Vector((-.16,.16,.20));c=Vector((.16,.16,.78))
    k.sweep('Sword_Scabbard',[a,a.lerp(c,.75)],[.022,.025],[.012,.012],'timber',segs=10)
    k.sweep('Sword_Guard',[a.lerp(c,.75)+Vector((-.03,0,.03)),a.lerp(c,.75)+Vector((.03,0,-.03))],.012,.018,'brass',segs=8)
    k.sweep('Sword_Hilt',[a.lerp(c,.77),c],.014,.014,'jade',segs=10);k.ellipsoid('Sword_Pommel',c,(.02,.02,.02),'brass',segs=12,rings=6)
    k.sweep('Sword_Strap',[Vector((.13,-.12,.62)),Vector((0,-.14,.50)),Vector((-.12,-.12,.40))],.012,.005,'leather',segs=8)
def prop_gourd_belt(k,b):
    c=Vector((-.15*b.g,-.08,.33))
    k.ellipsoid('Belt_Gourd_Low',c,(.04,.04,.045),'ochre',segs=16,rings=8);k.ellipsoid('Belt_Gourd_High',c+Vector((0,0,.06)),(.028,.028,.03),'ochre',segs=16,rings=8)
    k.sweep('Belt_Gourd_Cord',[c+Vector((0,0,.09)),Vector((-.12*b.g,-.10,b.waist))],.005,.005,'rust',segs=6)
def prop_pill_bottle(k,b):
    h=b.hand(-1);c=h+Vector((0,-.04,-.02))
    k.lathe('Pill_Bottle',[(c.z-.05,.028,.028),(c.z,.035,.035),(c.z+.035,.02,.02),(c.z+.05,.013,.013)],'white_robe',c=(c.x,c.y),segs=20)
    k.ellipsoid('Pill_Bottle_Stopper',c+Vector((0,0,.06)),(.014,.014,.012),'red',segs=12,rings=6)

PROPS={'hammer':prop_hammer,'staff':prop_staff,'cane':prop_cane,'abacus':prop_abacus,'teapot':prop_teapot,'axe':prop_axe,
       'basket':prop_basket_back,'sword':prop_sword_back,'gourd':prop_gourd_belt,'pill':prop_pill_bottle}

# ------------------------------------------------------------------ characters
CHARACTERS={
 'QPlayerMale':dict(zh='玩家（男）',hair='topknot',hair_key='hair_black',outer='teal',inner='white_robe',trim='white_robe',belt='leather',hem=.20),
 'QPlayerFemale':dict(zh='玩家（女）',hair='double_buns',hair_key='hair_black',outer='teal',inner='white_robe',trim='white_robe',belt='leather',hem=.14,flare=1.1,band='jade',lash=True),
 'QDiscipleSword':dict(zh='劍修弟子',hair='ponytail',hair_key='hair_black',outer='white_robe',inner='teal_light',trim='teal',belt='teal',hem=.18,props=['sword'],band='teal'),
 'QDiscipleAlchemy':dict(zh='丹修弟子',hair='long_pin',hair_key='hair_brown',outer='cream',inner='white_robe',trim='jade',belt='jade',hem=.12,flare=1.12,props=['pill','gourd'],iris='iris_jade'),
 'QDiscipleFarmer':dict(zh='體修弟子',hair='short_band',hair_key='hair_brown',outer='ochre',inner='cream',trim='timber',belt='timber',hem=.24,sleeves='short',skin='skin_tan',girth=1.08),
 'QSectElder':dict(zh='宗門長老',hair='elder',hair_key='hair_white',outer='white_robe',inner='teal',trim='jade',belt='jade',hem=.05,flare=1.18,props=['staff'],capelet=('teal','jade'),eyes='sleepy',scale=1.04),
 'QBlacksmith':dict(zh='鐵匠',hair='spiky',hair_key='hair_black',outer='charcoal',inner='charcoal',trim='leather',belt='leather',hem=.24,sleeves='short',skin='skin_tan',girth=1.18,apron='leather',props=['hammer'],stubble=True),
 'QShopkeeper':dict(zh='雜貨店主',hair='cap',hair_key='hair_black',outer='ochre',inner='cream',trim='timber',belt='timber',hem=.10,girth=1.14,belly=.03,props=['abacus'],mustache=True,eyes='sleepy',hands_front=True),
 'QInnkeeper':dict(zh='客棧老闆娘',hair='low_bun',hair_key='hair_black',outer='plum',inner='cream',trim='cream',belt='cream',hem=.10,flare=1.1,apron='white_robe',props=['teapot'],lash=True),
 'QHerbalist':dict(zh='藥師',hair='braid',hair_key='hair_brown',outer='sage',inner='cream',trim='timber',belt='timber',hem=.14,flare=1.08,props=['basket'],lash=True),
 'QGranny':dict(zh='村中婆婆',hair='scarf',hair_key='hair_grey',outer='rust',inner='cream',trim='cream',belt='timber',hem=.08,flare=1.1,props=['cane'],eyes='sleepy',scale=.92,capelet=('indigo',None)),
 'QWoodcutter':dict(zh='樵夫',hair='straw_hat',hair_key='hair_black',outer='indigo',inner='cream',trim='cream',belt='straw',hem=.24,sleeves='short',skin='skin_tan',props=['axe'],girth=1.06),
}

def build_hair(k,b,spec):
    h=spec['hair'];key=spec['hair_key'];band=spec.get('band','red')
    if h=='topknot':
        hair_cap(k,b,key,hairline=.38,side_low=-.30);bangs(k,b,key,n=5,span=.55,tip=.20,length=.6,part=0.)
        bun(k,b,key,(0,.15,1.),.085,band='timber',pin=('wood','jade'))
    elif h=='double_buns':
        hair_cap(k,b,key,hairline=.30,side_low=-.45);bangs(k,b,key,n=7,span=.62,tip=.08)
        for sx in (-1,1):
            c=bun(k,b,key,(sx*.75,.25,.65),.085,band=band)
            k.sweep('Bun_Ribbon',[c+Vector((sx*.02,.06,-.02)),c+Vector((sx*.05,.10,-.12)),c+Vector((sx*.06,.11,-.20))],[.02,.022,.012],.005,band,segs=8,ups=[Vector((0,1,0))]*3)
        side_locks(k,b,key,length=.22)
    elif h=='ponytail':
        hair_cap(k,b,key,hairline=.32,side_low=-.35);bangs(k,b,key,n=6,span=.6,tip=.12,length=.8);ponytail(k,b,key,band=band,length=.48);side_locks(k,b,key,length=.16,width=.035)
    elif h=='long_pin':
        hair_cap(k,b,key,hairline=.30,side_low=-.55,back_low=-.75);bangs(k,b,key,n=7,span=.62,tip=.05,length=1.1,part=-.33);side_locks(k,b,key,length=.30)
        long_back(k,b,key,bottom=.40,width=.21);bun(k,b,key,(0,.7,.6),.07,band='jade',pin=('brass','jade'))
    elif h=='short_band':
        hair_cap(k,b,key,hairline=.42,side_low=-.25);bangs(k,b,key,n=6,span=.6,tip=.25,length=.5)
        ring=[_hair_dir(b,(math.cos(a),math.sin(a)*1.0,.42),1.13) for a in taper(0,2*math.pi,33)[:-1]]
        k.sweep('Headband',ring,.025,.01,'red',segs=8,ups=[(p-b.C).normalized() for p in ring],closed=True)
    elif h=='elder':
        hair_cap(k,b,key,hairline=.50,side_low=-.30,back_low=-.40);bun(k,b,key,(0,.1,1.),.08,band='jade',pin=('jade','jade'))
        k.ellipsoid('Elder_Crown',_hair_dir(b,(0,.1,1.),1.10)+Vector((0,0,.07)),(.06,.035,.03),'jade',segs=16,rings=8)
        beard(k,b,key,length=.26,width=.11)
    elif h=='spiky':
        hair_cap(k,b,key,hairline=.42,side_low=-.25);bangs(k,b,key,n=5,span=.6,tip=.28,length=.4)
        for i in range(7):
            a=-1.1+i*.37;base=_hair_dir(b,(math.sin(a)*.6,.2+.1*math.cos(a),.95),1.05);n=(base-b.C).normalized()
            k.sweep('Hair_Spike',[base,base+n*.06+Vector((0,.04,0)),base+n*.10+Vector((0,.08,0))],[.045,.03,.004],[.03,.02,.003],key,segs=10)
    elif h=='cap':
        hair_cap(k,b,key,hairline=.35,side_low=-.30);skull_cap(k,b,'indigo')
    elif h=='low_bun':
        hair_cap(k,b,key,hairline=.32,side_low=-.40);bangs(k,b,key,n=6,span=.6,tip=.10,length=.9,part=.2);bun(k,b,key,(0,.9,-.05),.095,band='cream',pin=('brass','red'))
    elif h=='braid':
        hair_cap(k,b,key,hairline=.30,side_low=-.40);bangs(k,b,key,n=7,span=.6,tip=.09)
        start=_hair_dir(b,(.6,.5,-.35),1.06)
        for i in range(5):
            c=start+Vector((.03+.01*i,-.04-.012*i,-.07*i));k.ellipsoid('Hair_Braid',c,(.042-.004*i,.042-.004*i,.05),key,segs=16,rings=8)
        k.sweep('Hair_Braid_Tie',[start+Vector((.08,-.09,-.34)),start+Vector((.08,-.09,-.37))],.03,.03,'jade',segs=12)
    elif h=='scarf':
        hair_cap(k,b,key,hairline=.32,side_low=-.30);headscarf(k,b,'indigo')
    elif h=='straw_hat':
        hair_cap(k,b,key,hairline=.38,side_low=-.30);bangs(k,b,key,n=5,span=.55,tip=.2,length=.6);straw_hat(k,b)

def build_character(coll,aid):
    spec=CHARACTERS[aid];root=bpy.data.objects.new(aid+'_ROOT',None);coll.objects.link(root);k=Kit(coll,root)
    b=Body(spec.get('girth',1.));skin=spec.get('skin','skin')
    build_head(k,b,skin);build_face(k,b,spec.get('iris','iris'),spec['hair_key'] if spec['hair']!='elder' else 'hair_white',spec.get('eyes','round'))
    build_limbs(k,b,spec['outer'],spec['trim'],skin,{'short':'short'}.get(spec.get('sleeves'),'wide'),leg_show=spec['hem']-.02)
    robe,surf=build_robe(k,b,spec['outer'],spec['inner'],spec['trim'],spec['belt'],spec['hem'],spec.get('flare',1.),spec.get('belly',0.),
                         belt_out=.022 if spec.get('apron') else 0.)
    if spec.get('apron'):front_panel(k,'Apron',surf,-.12*b.g,.12*b.g,max(.10,spec['hem']+.02),.56,spec['apron'],out=.017)
    if spec.get('capelet'):capelet(k,b,*spec['capelet'])
    build_hair(k,b,spec)
    if spec.get('mustache'):
        mp,mn=on_head(b,0,b.C.z-.12,.008)   # ends curl upward so the face reads cheerful, not frowning
        for sx in (-1,1):k.sweep('Mustache',[mp,mp+Vector((sx*.04,-.008,-.012)),mp+Vector((sx*.07,-.004,.004))],[.014,.012,.004],[.009,.008,.003],spec['hair_key'],segs=8)
    for p in spec.get('props',[]):PROPS[p](k,b)
    s=spec.get('scale',1.)
    if s!=1.:
        for o in coll.objects:
            if o.type=='MESH' and o.parent==root:o.data.transform(Matrix.Scale(s,4))
    return root
