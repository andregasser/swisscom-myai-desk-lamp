"""Render the actual v3 meshes; studio colors, not a light-output simulation."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/multicolor_v3/preview'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
P = json.loads((ROOT / 'cad/multicolor_parameters.json').read_text())
parts = []
def load(stem, name, color):
    bpy.ops.wm.stl_import(filepath=str(OUT.parent / 'stl' / (stem + '.stl')))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (.001,) * 3
    mat = bpy.data.materials.new(name)
    # Hex codes are sRGB; Blender material input is scene-linear.
    rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    mat.diffuse_color = tuple(c / 12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb) + (1,)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = mat.diffuse_color
    bsdf.inputs['Roughness'].default_value = .65
    obj.data.materials.append(mat)
    parts.append(obj)
    return obj

base = load('04_base', 'base', '#EEF0F1')
base.location.z = P['foot_height_mm']/1000
load('06_feet', 'feet', '#EEF0F1')
frame = load('03_frame', 'frame', '#EEF0F1')
frame.location.z = .003
lid = load('05_lid', 'lid', '#EEF0F1')
lid.rotation_euler.x = math.pi
lid.location = (0, .150, .150)
for q in range(4):
    rotation = Matrix.Rotation(q * math.pi / 2, 4, 'Z')
    for color in P['colors']:
        obj = load(f'02_panel_{color["slot"]}_{color["name"]}', f'panel_{q}_slot_{color["slot"]}', color['hex'])
        obj.rotation_euler = (rotation @ Matrix.Rotation(-math.pi/2, 4, 'X')).to_euler()
        pos = Vector((P['panel_left_mm']/1000, P['panel_front_depth_mm']/1000,
                      (P['panel_bottom_mm'] + P['panel_height_mm'])/1000))
        center = Vector((.075, .075, 0))
        obj.location = rotation @ (pos - center) + center

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.render.resolution_x = 1200
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.world.color = (.2, .2, .2)
scene.view_settings.view_transform = 'AgX'

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.0002))
floor = bpy.context.object
mat = bpy.data.materials.new('Slate backdrop')
mat.diffuse_color = (.065, .085, .12, 1)
mat.use_nodes = True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = mat.diffuse_color
floor.data.materials.append(mat)

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

for name, location, power, size in (
    ('Softbox', (-.15, -.25, .42), 10, .3),
    ('Fill', (.4, -.1, .18), 5, .3),
    ('Rim', (.2, .3, .36), 12, .25),
):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = power, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, (.075, .075, .075))

bpy.ops.object.camera_add(location=(.35, -.39, .29))
camera = bpy.context.object
aim(camera, (.075, .075, .075))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .29
scene.camera = camera
scene.render.filepath = str(OUT / 'assembled.png')
bpy.ops.render.render(write_still=True)

floor.hide_render = True
data = bpy.data.lights.new('Underside softbox', 'AREA')
data.energy, data.shape, data.size = 7, 'DISK', .25
underlight = bpy.data.objects.new('Underside softbox', data)
scene.collection.objects.link(underlight)
underlight.location = (.075, -.1, -.25)
aim(underlight, (.075, .075, .02))
camera.location = (.32, -.36, -.25)
aim(camera, (.075, .075, .075))
camera.data.ortho_scale = .33
scene.render.filepath = str(OUT / 'underside.png')
bpy.ops.render.render(write_still=True)
underlight.hide_render = True
floor.hide_render = False
camera.location = (.35, -.39, .29)

for obj in parts:
    if obj.name == 'lid':
        obj.location.z += .085
    elif obj.name.startswith('panel_0_'):
        obj.location.z += .045
aim(camera, (.075, .075, .12))
camera.data.ortho_scale = .38
scene.render.filepath = str(OUT / 'insertion.png')
bpy.ops.render.render(write_still=True)
