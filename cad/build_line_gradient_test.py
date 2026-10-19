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


def invalidate(out, plate_name):
    """A failed rebuild must never leave a stale print approval beside new meshes."""
    (out/'print').mkdir(parents=True,exist_ok=True)
    for name in ('geometry_validation.json','print_validation.json','surface_coverage.json',
                 'surface_coverage.svg','surface_coverage.png',
                 f'print/{plate_name}_P1S.3mf','print/slicer_result.json'):
        (out/name).unlink(missing_ok=True)
    (out/'print/STATUS.md').write_text(
        f'# Testkarte {plate_name.split("_")[0]}\n\nNeubau gestartet; keine Druckfreigabe.\n')


def main(source=SOURCE, out=OUT, corner_radius=0., plate_name='11_line_gradient_test', design_metadata=None, ink_outline=None, direct_regions=None):
    SOURCE, OUT = Path(source), Path(out)
    invalidate(OUT,plate_name)
    pitch=(design_metadata or {}).get("stripe_pitch_mm",.48)
    band_label=(design_metadata or {}).get("band_label",f"{pitch:g}mm gerade Farbbahnen")
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
            if piece.area()<.001 and not design_metadata:
                removed.append({'color':path.attrib['fill'],'area_mm2':piece.area(),'bounds_mm':piece.bounds()})
            else:
                keep.append(piece)
        by_color[path.attrib['fill']]=m.CrossSection.batch_boolean(keep,m.OpType.Add).translate((-x0,-y0))
    if direct_regions is not None:
        by_color={c:r.translate((-x0,-y0)) for c,r in direct_regions.items()}
    assert sum(p['area_mm2'] for p in removed)<.001
    if not design_metadata: assert len(removed)==1
    ink_regions=[by_color[c['hex']] for c in COLORS[1:]]
    references=[]
    for slot,x in zip((4,3,2),(width/2-7.5,width/2-1.5,width/2+4.5)):
        ink_regions[slot-2]+=m.CrossSection.square((3,3)).translate((x,height-4))
        references.append({'slot':slot,'xy_mm':[x+1.5,2.5]})
    ink_regions=[r if design_metadata else r.simplify(1e-6) for r in ink_regions]
    inks=[r.extrude(.2) for r in ink_regions]
    if corner_radius:
        envelope=m.CrossSection.square((width-2*corner_radius,height-2*corner_radius)).translate((corner_radius,corner_radius)).offset(corner_radius,circular_segments=64).extrude(.6)
    else:
        envelope=mono.box(width,height,.6)
    all_ink=m.CrossSection.batch_boolean(ink_regions,m.OpType.Add)
    if ink_outline is not None:
        all_ink=ink_outline.translate((-x0,-y0))
        for slot,x in zip((4,3,2),(width/2-7.5,width/2-1.5,width/2+4.5)):
            all_ink+=m.CrossSection.square((3,3)).translate((x,height-4))
    parts=[envelope-(all_ink.extrude(.2) if ink_outline is not None else mono.union(inks)),*inks]
    joined=mono.union(parts)
    # Boolean rounding may retain zero-volume faces; they are not separate solids.
    assert len([p for p in joined.decompose() if abs(p.volume())>1e-8])==1
    assert (joined-envelope).volume()+(envelope-joined).volume()<1e-5
    for i,part in enumerate(parts):
        for other in parts[i+1:]: assert (part^other).volume()<1e-5, (i,(part^other).volume())

    parts=[part.rotate((180,0,0)).translate((0,height,.6)) for part in parts]
    meshes=[]
    for slot,part in enumerate(parts,1):
        mesh=mono.mesh(part)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0, slot
        mesh.export(OUT/'stl'/f'slot_{slot}.stl')
        meshes.append({'slot':slot,'components':len(mesh.split()),'volume_mm3':float(mesh.volume)})
    ams.multipart_3mf(parts,OUT/'geometry'/f'{plate_name}.3mf',
                      f'myAI {band_label}',OFFSET,colors=COLORS)
    preview=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">',
             f'<rect width="{width}" height="{height}" rx="{corner_radius}" fill="white"/>']
    for region,color in zip(ink_regions,COLORS[1:]):
        path=' '.join('M'+' L'.join(f'{x:.6f},{y:.6f}' for x,y in p)+' Z' for p in region.to_polygons())
        preview.append(f'<path d="{path}" fill="{color["hex"]}" fill-rule="evenodd"/>')
    (OUT/'preview/card.svg').write_text('\n'.join([*preview,'</svg>']))
    import cairosvg
    cairosvg.svg2png(url=str(OUT/'preview/card.svg'),write_to=str(OUT/'preview/card.png'),output_width=1000)
    report={'size_mm':[width,height,.6],'color_depth_mm':.2,'white_backing_mm':.4,
            'plate_name':plate_name,'card_corner_radius_mm':corner_radius,
            'front_is_bed_face':False,'color_layer_z_mm':.6,'print_offset_mm':OFFSET,
            'palette':COLORS,'source_preview_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'source_preview':str(SOURCE.relative_to(ROOT)) if SOURCE.is_relative_to(ROOT) else str(SOURCE),
            'removed_original_micro_fragment':removed,'reference_fields':references,
            'one_connected_card':True,'watertight_slot_components':meshes,
            'material_intersections_mm3':0,'physical_print_verified':False}
    if design_metadata: report.update(design_metadata)
    (OUT/'geometry_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'print/STATUS.md').write_text(f'# Testkarte {plate_name.split("_")[0]}\n\nGeometrie neu erstellt. Slicing und Flächenprüfung erforderlich.\n')
    print(f'Card {width:.3f} x {height:.3f} x 0.6 mm; {band_label}, white first, cyan in slot 3.')


if __name__=='__main__': main()
