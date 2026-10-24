"""Materials for LingyunValley15. Concept palette: yellow-green meadow, warm dirt, pale limestone with moss caps,
blue-green tiles and warm timber. Low specular (0.15) as in WildVegetation13 so studio lights do not wash colours out.
"""
import bpy

def _bsdf(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')

def flat(name,c,rough=.85,spec=.15,metal=0.):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);b=_bsdf(m)
    b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=rough;b.inputs['Specular IOR Level'].default_value=spec;b.inputs['Metallic'].default_value=metal
    return m

def _noise(nt,scale,detail=4,coords='Object',stretch=None):
    n=nt.nodes;l=nt.links;tc=n.new('ShaderNodeTexCoord');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=detail
    src=tc.outputs[coords]
    if stretch:
        mp=n.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=stretch;l.new(src,mp.inputs['Vector']);src=mp.outputs['Vector']
    l.new(src,tex.inputs['Vector']);return tex

def _ramp(nt,fac,a,b,p0=.3,p1=.72):
    r=nt.nodes.new('ShaderNodeValToRGB');e=r.color_ramp.elements;e[0].position=p0;e[0].color=(*a,1);e[1].position=p1;e[1].color=(*b,1)
    nt.links.new(fac,r.inputs[0]);return r

def _mix(nt,f,a,b):
    m=nt.nodes.new('ShaderNodeMix');m.data_type='RGBA';l=nt.links
    l.new(f,m.inputs['Factor']);l.new(a,m.inputs['A']);l.new(b,m.inputs['B']);return m.outputs['Result']

def _bump(nt,h,strength,dist=.05):
    b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=dist
    nt.links.new(h,b.inputs['Height']);nt.links.new(b.outputs['Normal'],_bsdf_of(nt).inputs['Normal'])

def _bsdf_of(nt):return next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')

def _upward(nt,lo=.55,hi=.8,jitter=None):
    """0..1 mask of upward-facing normals, optionally broken up by a noise output."""
    n=nt.nodes;l=nt.links;g=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(g.outputs['Normal'],sep.inputs[0])
    src=sep.outputs['Z']
    if jitter is not None:
        add=n.new('ShaderNodeMath');add.operation='ADD';l.new(src,add.inputs[0]);sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT'
        l.new(jitter,sub.inputs[0]);sub.inputs[1].default_value=.5;l.new(sub.outputs[0],add.inputs[1]);src=add.outputs[0]
    mr=n.new('ShaderNodeMapRange');mr.inputs['From Min'].default_value=lo;mr.inputs['From Max'].default_value=hi;l.new(src,mr.inputs['Value'])
    return mr.outputs['Result']

GRASS=((.075,.13,.022),(.22,.29,.055));DIRT=((.20,.14,.065),(.34,.25,.13))
STONE=((.17,.17,.15),(.38,.37,.33));MOSS=((.07,.13,.025),(.17,.25,.05))

def meadow():
    m=flat('LY15_Meadow',(.09,.14,.03),.95);nt=m.node_tree;l=nt.links;b=_bsdf(m)
    big=_noise(nt,.08,5);fine=_noise(nt,1.6,6)
    grass=_ramp(nt,fine.outputs['Fac'],*GRASS);dirt=_ramp(nt,fine.outputs['Fac'],*DIRT)
    attr=nt.nodes.new('ShaderNodeAttribute');attr.attribute_name='dirt'
    # Dirt where the 'dirt' attribute marks shoulders/paths, plus organic bare patches from large noise.
    patch=nt.nodes.new('ShaderNodeMapRange');patch.inputs['From Min'].default_value=.53;patch.inputs['From Max'].default_value=.62;l.new(big.outputs['Fac'],patch.inputs['Value'])
    mx=nt.nodes.new('ShaderNodeMath');mx.operation='MAXIMUM';l.new(attr.outputs['Fac'],mx.inputs[0]);l.new(patch.outputs['Result'],mx.inputs[1])
    edge=nt.nodes.new('ShaderNodeMapRange');edge.inputs['From Min'].default_value=.35;edge.inputs['From Max'].default_value=.75;l.new(mx.outputs[0],edge.inputs['Value'])
    l.new(_mix(nt,edge.outputs['Result'],grass.outputs['Color'],dirt.outputs['Color']),b.inputs['Base Color'])
    _bump(nt,fine.outputs['Fac'],.25,.08);return m

def stone(name,moss=True,streak=True,scale=.6):
    m=flat(name,(.17,.17,.15),.9);nt=m.node_tree;b=_bsdf(m)
    tex=_noise(nt,scale,6,stretch=(1.,1.,.18) if streak else None)
    rock=_ramp(nt,tex.outputs['Fac'],*STONE,.25,.75);col=rock.outputs['Color']
    if moss:
        jit=_noise(nt,1.2,4);mm=_ramp(nt,jit.outputs['Fac'],*MOSS,0.,1.)
        col=_mix(nt,_upward(nt,.5,.75,jit.outputs['Fac']),col,mm.outputs['Color'])
    nt.links.new(col,b.inputs['Base Color']);_bump(nt,tex.outputs['Fac'],.45,.12);return m

def build_all():
    return {'meadow':meadow(),'cliff':stone('LY15_Cliff_Limestone',moss=True,streak=True,scale=.35),
            'rock':stone('LY15_Rim_Boulder',moss=True,streak=False,scale=1.1),'peak':stone('LY15_Karst_Peak',moss=True,streak=True,scale=.25),
            'paving':flat('LY15_Paving_Stone',(.30,.31,.29),.8),'paving_dark':flat('LY15_Paving_Joint',(.13,.13,.12),.9),
            'timber':flat('LY15_Warm_Timber',(.16,.065,.028),.75),'board':flat('LY15_Cedar_Board',(.29,.14,.055),.75),
            'tile':flat('LY15_BlueGreen_Tile',(.065,.15,.155),.6),'tile_ridge':flat('LY15_Tile_Ridge',(.04,.10,.10),.6),
            'plaster':flat('LY15_Plaster',(.62,.58,.48),.9),'stone_base':flat('LY15_Pale_Stone_Base',(.36,.37,.33),.85),
            'jade':flat('LY15_Jade_Trim',(.08,.29,.24),.4,.3),'bronze':flat('LY15_Aged_Bronze',(.25,.17,.065),.45,.4,.6),
            'soil':flat('LY15_Bed_Soil',(.08,.05,.025),.95),'herb':flat('LY15_Herb_Leaf',(.05,.16,.04),.8),
            'herb_light':flat('LY15_Herb_Leaf_Light',(.13,.24,.06),.8),'bloom':flat('LY15_Herb_Bloom',(.50,.30,.42),.6),
            'cloth':flat('LY15_Bedding_Cloth',(.16,.27,.20),.9),'straw':flat('LY15_Straw_Mat',(.42,.32,.15),.9),
            'paper':flat('LY15_Lantern_Paper',(.61,.49,.29),.7),'water':flat('LY15_Trough_Water',(.03,.12,.13),.15,.5),
            'thatch':thatch('LY15_Mossy_Thatch',(.10,.13,.025),(.24,.30,.07)),'thatch_dark':flat('LY15_Thatch_Ridge',(.10,.11,.03),.95),
            'bamboo':flat('LY15_Bamboo_Pole',(.30,.30,.13),.6,.35)}

def thatch(name,dark,light):
    """Lime-green mossy thatch like the concept camp roof, with fibre streaks along the slope."""
    m=flat(name,tuple((a+b)/2 for a,b in zip(dark,light)),.95);nt=m.node_tree
    tex=_noise(nt,3.,6,stretch=(1.,6.,1.));r=_ramp(nt,tex.outputs['Fac'],dark,light,.25,.75)
    nt.links.new(r.outputs['Color'],_bsdf(m).inputs['Base Color']);_bump(nt,tex.outputs['Fac'],.5,.04);return m
