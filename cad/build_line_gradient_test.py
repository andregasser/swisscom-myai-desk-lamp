"""Make the approved 0.48 mm straight-band study into a face-up AMS test card."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import manifold3d as m
from svgpathtools import parse_path, Line

import build as mono
import build_multicolor as ams

ROOT = mono.ROOT
OUT = ROOT/'output/line_gradient_test'
SOURCE = ROOT/'design_studies/line_gradient_fine/proposal.svg'
OFFSET = (40,40,0)
COLORS = [{'slot':1,'name':'Weiss','hex':'#FFFFFF'},
          {'slot':2,'name':'Blau','hex':'#0445C8'},
          {'slot':3,'name':'Cyanblau','hex':'#1FB9FF'},
          {'slot':4,'name':'Rot','hex':'#F23232'}]


def main():
    for folder in ('stl','geometry','print','profiles','preview'):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    svg = ET.parse(SOURCE).getroot()
    ns='{http://www.w3.org/2000/svg}'
    x0,y0,width,height=map(float,svg.attrib['viewBox'].split())
    by_color={}
    removed=[]
    for path in svg.findall(ns+'path'):
        contours=[]
        for loop in parse_path(path.attrib['d']).continuous_subpaths():
            assert all(isinstance(s,Line) for s in loop)
            contours.append([(s.start.real,s.start.imag) for s in loop])
        region=m.CrossSection(contours,m.FillRule.EvenOdd)
        keep=[]
        for piece in region.decompose():
            if piece.area()<.001:
                removed.append({'color':path.attrib['fill'],'area_mm2':piece.area(),'bounds_mm':piece.bounds()})
            else:
                keep.append(piece)
        by_color[path.attrib['fill']]=m.CrossSection.batch_boolean(keep,m.OpType.Add).translate((-x0,-y0))
    assert len(removed)==1 and sum(p['area_mm2'] for p in removed)<.001
    ink_regions=[by_color[c['hex']] for c in COLORS[1:]]
    references=[]
    for slot,x in zip((4,3,2),(width/2-7.5,width/2-1.5,width/2+4.5)):
        ink_regions[slot-2]+=m.CrossSection.square((3,3)).translate((x,height-4))
        references.append({'slot':slot,'xy_mm':[x+1.5,2.5]})
    inks=[r.simplify(1e-6).extrude(.2) for r in ink_regions]
    envelope=mono.box(width,height,.6)
    parts=[envelope-mono.union(inks),*inks]
    joined=mono.union(parts)
    assert len(joined.decompose())==1
    assert (joined-envelope).volume()+(envelope-joined).volume()<1e-5
    for i,part in enumerate(parts):
        for other in parts[i+1:]: assert (part^other).volume()<1e-5
    parts=[part.rotate((180,0,0)).translate((0,height,.6)) for part in parts]
    meshes=[]
    for slot,part in enumerate(parts,1):
        mesh=mono.mesh(part)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        mesh.export(OUT/'stl'/f'slot_{slot}.stl')
        meshes.append({'slot':slot,'components':len(mesh.split()),'volume_mm3':float(mesh.volume)})
    ams.multipart_3mf(parts,OUT/'geometry/11_line_gradient_test.3mf',
                      'myAI 0.48mm gerade Farbbahnen',OFFSET,colors=COLORS)
    preview=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">',
             f'<rect width="{width}" height="{height}" fill="white"/>']
    for region,color in zip(ink_regions,COLORS[1:]):
        path=' '.join('M'+' L'.join(f'{x:.6f},{y:.6f}' for x,y in p)+' Z' for p in region.to_polygons())
        preview.append(f'<path d="{path}" fill="{color["hex"]}" fill-rule="evenodd"/>')
    (OUT/'preview/card.svg').write_text('\n'.join([*preview,'</svg>']))
    import cairosvg
    cairosvg.svg2png(url=str(OUT/'preview/card.svg'),write_to=str(OUT/'preview/card.png'),output_width=1000)
    report={'size_mm':[width,height,.6],'color_depth_mm':.2,'white_backing_mm':.4,
            'front_is_bed_face':False,'color_layer_z_mm':.6,'print_offset_mm':OFFSET,
            'palette':COLORS,'source_preview_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'source_preview':'design_studies/line_gradient_fine/proposal.svg',
            'removed_original_micro_fragment':removed,'reference_fields':references,
            'one_connected_card':True,'watertight_slot_components':meshes,
            'material_intersections_mm3':0,'physical_print_verified':False}
    (OUT/'geometry_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in ('print_validation.json','surface_coverage.json','surface_coverage.svg','surface_coverage.png',
                 'print/11_line_gradient_test_P1S.3mf','print/slicer_result.json'):
        (OUT/name).unlink(missing_ok=True)
    (OUT/'print/STATUS.md').write_text('# Testkarte 11\n\nGeometrie neu erstellt. Slicing und Flächenprüfung erforderlich.\n')
    print(f'Card {width:.3f} x {height:.3f} x 0.6 mm; approved straight bands, white first, cyan in slot 3.')


if __name__=='__main__': main()
