"""Render the actual test meshes from the upward-facing color side."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'cad/multicolor_parameters.json').read_text())
OUT=ROOT/'output'/P['output_folder']
CARD=json.loads((OUT/'raster_original_test/geometry_validation.json').read_text())
WIDTH, HEIGHT = [v*.001 for v in CARD['size_mm'][:2]]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for color in P['colors']:
    bpy.ops.wm.stl_import(filepath=str(OUT/'raster_original_test/stl'/f'slot_{color["slot"]}.stl'))
    obj=bpy.context.object
    obj.scale=(.001,)*3
    mat=bpy.data.materials.new(color['name'])
    rgb=[int(color['hex'][i:i+2],16)/255 for i in (1,3,5)]
    linear=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb)+(1,)
    mat.diffuse_color=linear
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=linear
    bsdf.inputs['Roughness'].default_value=.7
    if color['slot'] != 1:
        emission=mat.node_tree.nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value=linear
        mat.node_tree.links.new(emission.outputs[0],mat.node_tree.nodes.get('Material Output').inputs['Surface'])
    obj.data.materials.append(mat)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1200
scene.render.resolution_y=round(1200*HEIGHT/WIDTH)
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.world.color=(.5,.5,.5)
data=bpy.data.lights.new('Softbox','AREA')
data.energy=5
data.shape='DISK'
data.size=.3
light=bpy.data.objects.new('Softbox',data)
scene.collection.objects.link(light)
light.location=(.04,.02,.3)
light.rotation_euler=(Vector((WIDTH/2,HEIGHT/2,0))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(WIDTH/2,HEIGHT/2,.3),rotation=(0,0,0))
camera=bpy.context.object
camera.data.type='ORTHO'
camera.data.ortho_scale=max(WIDTH,HEIGHT)+.004
scene.camera=camera
scene.render.filepath=str(OUT/'preview/raster_original_test.png')
bpy.ops.render.render(write_still=True)
