"""Refine straight-band endpoints locally; derive every color from the original SVG."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import manifold3d as m
import numpy as np
from shapely import unary_union

import build_line_gradient_test as card
import line_gradient_regions as source


def combine(parts):
    return m.CrossSection.batch_boolean(list(parts),m.OpType.Add)


def section(shape):
    contours=[]
    for p in source.polygons(shape):
        contours.extend(np.asarray(ring.coords)[:-1] for ring in [p.exterior,*p.interiors])
    return m.CrossSection(contours,m.FillRule.EvenOdd)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pitch',type=float,default=.44)
    parser.add_argument('--guard',type=float,default=.6)
    parser.add_argument('--radius',type=float,default=.20)
    parser.add_argument('--output',type=Path,default=card.ROOT/'output/line_gradient_refined')
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    card.invalidate(out,'12_refined_line_test')
    assert .4<=args.pitch<=.48 and 0<=args.guard<=1.2 and 0<=args.radius<args.pitch/2
    raw_parts=[[],[],[]];parts=[[],[],[]];outlines=[]
    for gradient,shapes in source.sources():
        outline=section(unary_union(shapes))
        outline=combine(p for p in outline.decompose() if p.area()>.001)
        outlines.append(outline)
        p0=np.array([float(gradient.attrib[k]) for k in ('x1','y1')])*source.SCALE
        vector=np.array([float(gradient.attrib[k]) for k in ('x2','y2')])*source.SCALE-p0
        length=np.linalg.norm(vector);direction=vector/length;normal=np.array([-direction[1],direction[0]])
        stops=[(float(s.attrib['offset']),source.rgb(s.attrib['stop-color'])) for s in gradient.findall(source.NS+'stop')]
        positions=np.array([s[0] for s in stops]);values=np.array([s[1] for s in stops])
        corners=np.array([(x,y) for x in outline.bounds()[::2] for y in outline.bounds()[1::2]])
        projections=(corners-p0)@direction
        raw=[[],[],[]];base=[[],[],[]];error=np.zeros(3)
        for index in range(math.floor(projections.min()/args.pitch),math.ceil(projections.max()/args.pitch)):
            t=(index+.5)*args.pitch/length
            target=np.array([np.interp(t,positions,values[:,c]) for c in range(3)])
            weights=source.weights(source.linear(target))
            desired=weights+error;chosen=int(np.argmax(desired));error=desired-np.eye(3)[chosen]
            a,b=p0+direction*index*args.pitch,p0+direction*(index+1)*args.pitch
            band=m.CrossSection([np.array([a-normal*300,b-normal*300,b+normal*300,a+normal*300])])^outline
            raw[chosen].append(band);base[int(np.argmax(weights))].append(band)
        raw=[combine(x) for x in raw];base=[combine(x) for x in base]
        interior=outline.offset(-args.guard,circular_segments=64)
        rounded=[]
        for i in range(3):
            minority=(raw[i]-base[i])^interior
            opened=minority.offset(-args.radius,circular_segments=64).offset(args.radius,circular_segments=64).simplify(.001)
            rounded.append(combine(p for p in opened.decompose() if p.area()>=.5))
        # Subtract minority strokes directly from the continuous base colors.
        # Avoid subtract/refill of coincident edges along every raw stripe.
        refined=[(base[i]-combine(rounded[j] for j in range(3) if j!=i))+rounded[i] for i in range(3)]
        assert (outline-combine(refined)).area()<1e-5
        for i in range(3):
            raw_parts[i].append(raw[i]);parts[i].append(refined[i])
    raw=[combine(p) for p in raw_parts];regions=[combine(p) for p in parts]
    outline=combine(outlines)
    changed=sum((raw[i]-regions[i]).area() for i in range(3))
    x0,y0,x1,y1=outline.bounds();width,height=x1-x0+10,y1-y0+10
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="{x0-5} {y0-5} {width} {height}">',
         f'<rect x="{x0-5}" y="{y0-5}" width="{width}" height="{height}" fill="white"/>']
    for region,color in zip(regions,source.COLORS):
        path=' '.join('M'+' L'.join(f'{x:.10f},{y:.10f}' for x,y in p)+' Z' for p in region.to_polygons())
        svg.append(f'<path d="{path}" fill="{color}" fill-rule="evenodd"/>')
    preview=out/'design.svg';preview.write_text('\n'.join([*svg,'</svg>']))
    metadata={'stripe_pitch_mm':args.pitch,'endpoint_radius_mm':args.radius,'contour_guard_mm':args.guard,
              'endpoint_reassigned_area_mm2':changed,'endpoint_reassigned_percent':100*changed/outline.area(),
              'source_svg_sha256':hashlib.sha256(source.SOURCE.read_bytes()).hexdigest(),
              'method':'Original SVG palette weights; minority bands inset and rounded; remainder assigned to local dominant ink.',
              'minimum_rounded_fragment_mm2':.5,'source_outline_preserved_except_original_micro_fragment':True,'visual_equivalence_verified':False}
    card.main(preview,out,corner_radius=1.,plate_name='12_refined_line_test',design_metadata=metadata,ink_outline=outline, direct_regions={c:r for c,r in zip(source.COLORS,regions)})
    print(json.dumps(metadata,indent=2))


if __name__=='__main__': main()
