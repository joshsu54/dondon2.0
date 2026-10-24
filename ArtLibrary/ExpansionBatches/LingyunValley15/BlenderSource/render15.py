"""Studio and ten-view rendering for LingyunValley15. Soft daylight on a pale neutral backdrop (concept look),
orthographic cameras at the project's standard ten directions, north = +Y so 01_front looks from the south.
"""
import bpy,math,json
from mathutils import Vector
VIEWS=[('01_front',(0,-1,.7)),('02_right',(1,0,.45)),('03_rear',(0,1,.7)),('04_left',(-1,0,.45)),('05_front_right',(1,-1,.8)),
       ('06_rear_right',(1,1,.8)),('07_rear_left',(-1,1,.8)),('08_front_left',(-1,-1,.8)),('09_top',(0,0,1)),('10_high_front',(0,-.45,1))]

def studio(scene,coll):
    w=bpy.data.worlds.new('LY15_Daylight_Backdrop');w.use_nodes=True;scene.world=w
    bg=next(n for n in w.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.62,.66,.70,1);bg.inputs[1].default_value=.75
    sun=bpy.data.lights.new('LY15_Sun','SUN');sun.energy=3.2;sun.angle=math.radians(9);sun.color=(1.,.96,.9)
    o=bpy.data.objects.new('LY15_Sun',sun);coll.objects.link(o);o.rotation_euler=(math.radians(42),0,math.radians(32))
    fill=bpy.data.lights.new('LY15_Sky_Fill','SUN');fill.energy=.6;fill.angle=math.radians(40);fill.color=(.85,.9,1.)
    f=bpy.data.objects.new('LY15_Sky_Fill',fill);coll.objects.link(f);f.rotation_euler=(math.radians(60),0,math.radians(210))
    try:scene.render.engine='CYCLES'
    except TypeError as e:raise SystemExit('Cycles unavailable: %s'%e)
    scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
    scene.render.resolution_x=scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX';scene.view_settings.look='None';scene.view_settings.exposure=0.

def camera(scene,coll,centre,extent):
    cam=bpy.data.objects.new('LY15_Reference_Camera',bpy.data.cameras.new('LY15_Reference_Camera'));coll.objects.link(cam);scene.camera=cam
    cam.data.type='ORTHO';cam.data.clip_end=2000.;cam.data.ortho_scale=extent*1.04;return cam

def aim(cam,centre,direction,dist=600.):
    d=Vector(direction).normalized();cam.location=Vector(centre)+d*dist
    cam.rotation_euler=(Vector(centre)-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()

def fits(scene,cam,points):
    from bpy_extras.object_utils import world_to_camera_view
    pr=[world_to_camera_view(scene,cam,p) for p in points]
    return all(.01<p.x<.99 and .01<p.y<.99 and p.z>0 for p in pr)
