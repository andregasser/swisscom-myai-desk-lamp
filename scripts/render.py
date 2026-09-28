"""Blender preview of the actual print meshes, with illustrative lighting."""
from pathlib import Path
import bpy
from mathutils import Vector
import math

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1100
scene.render.resolution_y = 950
scene.render.resolution_percentage = 100
scene.world.color = (.18, .18, .18)
scene.view_settings.view_transform = 'AgX'


def material(name, color, translucent=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = .64
    if translucent:
        # Volume-based attenuation represents thickness, but is not a
        # measurement or calibrated prediction of any actual filament.
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        trans = nodes.new('ShaderNodeBsdfTranslucent')
        trans.inputs['Color'].default_value = (.92, .94, .98, 1)
        mix = nodes.new('ShaderNodeMixShader')
        mix.inputs[0].default_value = .65
        links.new(bsdf.outputs['BSDF'], mix.inputs[1])
        links.new(trans.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], nodes.get('Material Output').inputs['Surface'])
        volume = nodes.new('ShaderNodeVolumeAbsorption')
        volume.inputs['Color'].default_value = (.8, .8, .8, 1)
        volume.inputs['Density'].default_value = 800
        links.new(volume.outputs[0], nodes.get('Material Output').inputs['Volume'])
    return mat


white = material('White PLA / illustrative translucency', (.86, .88, .92), True)
solid = material('White PLA frame', (.8, .82, .87))
floor_mat = material('Backdrop', (.045, .065, .105))


def load(name, mat):
    bpy.ops.wm.stl_import(filepath=str(ROOT / 'output/stl' / (name + '.stl')))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (.001,) * 3
    obj.data.materials.append(mat)
    return obj


base = load('03_base', solid)
body = load('02_body', white)
body.location.z = .003
lid = load('04_lid', white)
lid.rotation_euler.x = math.pi
lid.location = (0, .150, .150)

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.0002))
floor = bpy.context.object
floor.data.materials.append(floor_mat)


def light(name, location, target, power, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    return obj


light('Softbox', (.0, -.25, .42), (.075, .075, .08), 12, .28, (.8, .88, 1))
light('Edge', (.33, .25, .3), (.075, .075, .1), 18, .22, (.7, .8, 1))
led = light('LED — schematic illumination', (.075, .075, .013), (.075, .075, .15), 1.5, .055, (1, .82, .58))

bpy.ops.object.camera_add(location=(.35, -.39, .29))
camera = bpy.context.object
camera.rotation_euler = (Vector((.075, .075, .075)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .29
scene.camera = camera
scene.render.filepath = str(ROOT / 'output/preview/assembled.png')
bpy.ops.render.render(write_still=True)

body.location.z = .032
lid.location.z = .230
led.data.energy = .0
body.data.materials.clear()
body.data.materials.append(solid)
lid.data.materials.clear()
lid.data.materials.append(solid)
camera.location = (.36, -.43, .43)
camera.rotation_euler = (Vector((.075, .075, .112)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.ortho_scale = .40
scene.render.filepath = str(ROOT / 'output/preview/exploded.png')
bpy.ops.render.render(write_still=True)
