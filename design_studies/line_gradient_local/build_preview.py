"""Preview only: local straight-band junction adjustment, without a contour border.

No CAD solids, slicer projects, G-code, or printing approval are generated.
"""
from pathlib import Path
import sys
import math
import json
import hashlib
import xml.etree.ElementTree as ET

import numpy as np
import cairosvg
from shapely import Polygon, LineString, Point, unary_union
from shapely.ops import nearest_points

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'cad'))
import line_gradient_regions as source

PITCH=.44
MAX_MOVE=.20
LOCAL_LENGTH=.50


def lines(shape):
    if shape.is_empty: return []
    if shape.geom_type=='LineString': return [shape]
    return [line for child in getattr(shape,'geoms',[]) for line in lines(child)]


def paths(regions):
    return ''.join(f'<path fill="{c}" fill-rule="evenodd" d="{source.svg_path(r)}"/>'
                   for c,r in zip(source.COLORS,regions))


def main():
    originals=[[],[],[]];modified=[[],[],[]];outlines=[];patches=[];removed=[]
    for group_index,(gradient,shapes) in enumerate(source.sources()):
        outline=unary_union(shapes)
        tiny=[p for p in source.polygons(outline) if p.area<.001]
        removed.extend(p.area for p in tiny)
        outline=unary_union([p for p in source.polygons(outline) if p.area>=.001])
        outlines.append(outline)
        p0=np.array([float(gradient.attrib[k]) for k in ('x1','y1')])*source.SCALE
        vector=np.array([float(gradient.attrib[k]) for k in ('x2','y2')])*source.SCALE-p0
        length=np.linalg.norm(vector);direction=vector/length;normal=np.array([-direction[1],direction[0]])
        stops=[(float(s.attrib['offset']),source.rgb(s.attrib['stop-color'])) for s in gradient.findall(source.NS+'stop')]
        positions=np.array([s[0] for s in stops]);values=np.array([s[1] for s in stops])
        corners=np.array([(x,y) for x in outline.bounds[::2] for y in outline.bounds[1::2]])
        projections=(corners-p0)@direction
        indices=range(math.floor(projections.min()/PITCH),math.ceil(projections.max()/PITCH))
        pieces=[[],[],[]];labels={};error=np.zeros(3)
        for index in indices:
            t=(index+.5)*PITCH/length
            target=np.array([np.interp(t,positions,values[:,c]) for c in range(3)])
            desired=source.weights(source.linear(target))+error
            color=int(np.argmax(desired));error=desired-np.eye(3)[color]
            labels[index]=color
            a,b=p0+direction*index*PITCH,p0+direction*(index+1)*PITCH
            pieces[color].append(outline.intersection(Polygon([a-normal*300,b-normal*300,b+normal*300,a+normal*300])))
        regions=[unary_union(parts) for parts in pieces]
        raw=regions.copy()
        for index in indices:
            if index-1 not in labels or labels[index-1]==labels[index]: continue
            origin=p0+direction*index*PITCH
            boundary=LineString([origin-normal*300,origin+normal*300]).intersection(outline)
            for segment in lines(boundary):
                if segment.length<.8: continue
                for end in (0,1):
                    point=segment.interpolate(0 if end==0 else segment.length)
                    reach=min(LOCAL_LENGTH,segment.length/3)
                    inside=segment.interpolate(reach if end==0 else segment.length-reach)
                    candidate=nearest_points(inside,outline.boundary)[1]
                    delta=np.array(candidate.coords[0])-point.coords[0]
                    distance=np.linalg.norm(delta)
                    if distance<.05: continue
                    # Bound the endpoint displacement; the intervening strip stays straight.
                    if distance>MAX_MOVE:
                        candidate=nearest_points(Point(np.array(point.coords[0])+delta*MAX_MOVE/distance),outline.boundary)[1]
                    if candidate.distance(point)>MAX_MOVE+1e-6: continue
                    if abs(np.dot(np.array(candidate.coords[0])-point.coords[0],direction))<.02: continue
                    patch=Polygon([point.coords[0],inside.coords[0],candidate.coords[0]]).intersection(outline)
                    if patch.area<.001: continue
                    shift=np.dot(np.array(candidate.coords[0])-point.coords[0],direction)
                    donor,receiver=(labels[index],labels[index-1]) if shift>0 else (labels[index-1],labels[index])
                    transfer=patch.intersection(regions[donor])
                    if transfer.area<.001: continue
                    regions[donor]=regions[donor].difference(transfer)
                    regions[receiver]=regions[receiver].union(transfer)
                    patches.append({'group':group_index,'area_mm2':transfer.area,'bounds_mm':list(transfer.bounds),
                                    'endpoint_shift_mm':candidate.distance(point),'reach_mm':reach})
        for i in range(3):
            originals[i].append(raw[i]);modified[i].append(regions[i])
    outline=unary_union(outlines)
    raw=[unary_union(parts) for parts in originals];regions=[unary_union(parts) for parts in modified]
    assert all(r.is_valid for r in regions)
    union=unary_union(regions)
    uncovered=outline.difference(union).area
    outside=union.difference(outline).area
    overlap=sum(regions[i].intersection(regions[j]).area for i in range(3) for j in range(i))
    assert max(uncovered,outside,overlap)<1e-7
    changed=sum(raw[i].difference(regions[i]).area for i in range(3))
    x0,y0,x1,y1=outline.bounds
    box=f'{x0-5} {y0-5} {x1-x0+10} {y1-y0+10}'
    for name,items in [('proposal',regions),('uncorrected',raw)]:
        (HERE/f'{name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{x1-x0+10}mm" height="{y1-y0+10}mm" viewBox="{box}"><rect x="{x0-5}" y="{y0-5}" width="{x1-x0+10}" height="{y1-y0+10}" fill="white"/>{paths(items)}</svg>')
    # Original SVG is embedded without changing its gradients, only scaled to millimetres.
    original=ET.parse(source.SOURCE).getroot()
    original_content=''.join(ET.tostring(child,encoding='unicode') for child in original)
    defs=f'<defs><g id="original" transform="scale({source.SCALE})">{original_content}</g><g id="raw">{paths(raw)}</g><g id="new">{paths(regions)}</g></defs>'
    page=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1210" viewBox="0 0 1600 1210">',defs,
          '<rect width="1600" height="1210" fill="#eef1f5"/><g font-family="DejaVu Sans,sans-serif" fill="#1d2940">',
          '<text x="40" y="53" font-size="30" font-weight="bold">myAI · Lokale Anschlüsse statt Randzonen</text>',
          '<text x="40" y="88" font-size="19">Gerade 0,44-mm-Streifen · für die 0,4-mm-Düse vorgesehen · zunächst nur eine Vorschau</text>']
    def view(ref,x,y,w,h,vb=box):
        return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}"><use href="#{ref}"/></svg>'
    for x,title,subtitle,ref in [(40,'Original','Unveränderte SVG','original'),(560,'Ohne Randzone','0,44 mm · noch ohne Endkorrektur','raw'),(1080,'Neuer Vorschlag','Nur lokale Farbanschlüsse verändert','new')]:
        page.extend([f'<rect x="{x}" y="118" width="480" height="620" rx="14" fill="white"/>',f'<text x="{x+22}" y="158" font-size="25" font-weight="bold">{title}</text>',f'<text x="{x+22}" y="188" font-size="17">{subtitle}</text>',view(ref,x+12,205,456,515)])
    # Show a real, strongly affected lettering junction at the same enlargement.
    detail=max((p for p in patches if p['group']==0),key=lambda p:p['area_mm2'])
    bx0,by0,bx1,by1=detail['bounds_mm'];cx=(bx0+bx1)/2;cy=(by0+by1)/2
    zoom=f'{cx-2.8} {cy-1.5} 5.6 3'
    for x,title,ref in [(40,'Vorher · Anschluss vergrössert','raw'),(560,'Vorschlag · gleicher Ausschnitt','new')]:
        page.extend([f'<rect x="{x}" y="760" width="480" height="305" rx="14" fill="white"/>',f'<text x="{x+22}" y="800" font-size="21" font-weight="bold">{title}</text>',view(ref,x+22,820,436,225,zoom)])
    page.extend([f'<text x="1100" y="800" font-size="21" font-weight="bold">Kleine, gezielte Änderungen</text>',
                 '<text x="1100" y="842" font-size="18">Keine umlaufende Randfarbe.</text>',
                 '<text x="1100" y="876" font-size="18">Endpunkte höchstens 0,20 mm versetzt.</text>',
                 f'<text x="1100" y="910" font-size="18">{100*changed/outline.area:.2f} % der Farbfläche neu zugeordnet.</text>',
                 '<text x="1100" y="944" font-size="18">Keine Aufhellung oder Weichzeichnung.</text>',
                 '<text x="40" y="1110" font-size="19">Die lokalen Knicke sollen spitze Farbkeile entschärfen. Eine geschlossene Druckfläche ist noch nicht nachgewiesen.</text>',
                 '<text x="40" y="1146" font-size="18">Noch nicht geslict · keine neuen Druckdateien · nominelle Bildschirmfarben, keine Filament- oder Lichtsimulation.</text>',
                 '</g></svg>'])
    (HERE/'comparison.svg').write_text(''.join(page))
    cairosvg.svg2png(url=str(HERE/'comparison.svg'),write_to=str(HERE/'comparison.png'))
    report={'status':'2D design proposal only; no printing approval','source_sha256':hashlib.sha256(source.SOURCE.read_bytes()).hexdigest(),
            'nominal_nozzle_mm':.4,'stripe_pitch_mm':PITCH,'max_endpoint_shift_mm':MAX_MOVE,'max_local_reach_mm':LOCAL_LENGTH,
            'palette_hex':source.COLORS,'intentional_contour_border_mm':0,'local_adjustments':len(patches),
            'reassigned_area_mm2':changed,'reassigned_percent_vs_uncorrected_same_pitch':100*changed/outline.area,
            'planar_uncovered_mm2':uncovered,'planar_outside_mm2':outside,'planar_color_overlap_mm2':overlap,
            'removed_original_micro_fragments_mm2':removed,'local_patches':patches,'detail_viewbox':zoom,
            'color_area_mm2_before':[r.area for r in raw],'color_area_mm2_after':[r.area for r in regions],
            'sliced':False,'physical_print_verified':False,
            'limitations':'Planar coverage does not prove slicer coverage. Acute tips may remain. No global minimum extrusion width is guaranteed. Visual equivalence not measured.'}
    (HERE/'preview_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['local_adjustments','reassigned_percent_vs_uncorrected_same_pitch','planar_uncovered_mm2','planar_color_overlap_mm2']},indent=2))

if __name__=='__main__':main()
