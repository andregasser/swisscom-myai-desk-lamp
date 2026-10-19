"""Preview straight bands with continuous blue/cyan duty cycles; no print files."""
from pathlib import Path
import sys
import json
import hashlib
import math
import xml.etree.ElementTree as ET
import numpy as np
from shapely import Polygon, unary_union
import cairosvg

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'cad'))
import line_gradient_regions as src

OLD_PITCH=.44
MIN_WIDTH=.32
SAMPLE_STEP=.02


def path_regions(regions):
    return ''.join(f'<path fill="{color}" fill-rule="evenodd" d="{src.svg_path(region)}"/>' for color,region in zip(src.COLORS,regions))


def main():
    old_parts=[[],[],[]];new_parts=[[],[],[]];outlines=[];cycles=[];runs=[]
    for group,(gradient,shapes) in enumerate(src.sources()):
        outline=unary_union([p for p in src.polygons(unary_union(shapes)) if p.area>=.001]);outlines.append(outline)
        p0=np.array([float(gradient.attrib[k]) for k in ('x1','y1')])*src.SCALE
        vector=np.array([float(gradient.attrib[k]) for k in ('x2','y2')])*src.SCALE-p0
        length=np.linalg.norm(vector);direction=vector/length;normal=np.array([-direction[1],direction[0]])
        stops=[(float(s.attrib['offset']),src.rgb(s.attrib['stop-color'])) for s in gradient.findall(src.NS+'stop')]
        positions=np.array([s[0] for s in stops]);values=np.array([s[1] for s in stops])
        def weights(x):
            target=np.array([np.interp(x/length,positions,values[:,i]) for i in range(3)])
            return src.weights(src.linear(target))
        def strip(a,b):
            a=p0+direction*a;b=p0+direction*b
            return outline.intersection(Polygon([a-normal*300,b-normal*300,b+normal*300,a+normal*300]))
        corners=np.array([(x,y) for x in outline.bounds[::2] for y in outline.bounds[1::2]])
        projections=(corners-p0)@direction
        lo,hi=math.floor(projections.min()/OLD_PITCH)*OLD_PITCH,math.ceil(projections.max()/OLD_PITCH)*OLD_PITCH
        local=[[],[],[]];error=np.zeros(3);last=None
        for index in range(round(lo/OLD_PITCH),round(hi/OLD_PITCH)):
            w=weights((index+.5)*OLD_PITCH);desired=w+error;color=int(np.argmax(desired));error=desired-np.eye(3)[color]
            local[color].append(strip(index*OLD_PITCH,(index+1)*OLD_PITCH))
            if last is not None and last['color']==color:last['width_mm']+=OLD_PITCH
            else:
                last={'group':group,'color':color,'start_mm':index*OLD_PITCH,'width_mm':OLD_PITCH};runs.append(last)
        raw=[unary_union(p) for p in local];new=raw.copy()
        grid=np.linspace(lo,hi,math.ceil((hi-lo)/SAMPLE_STEP)+1)
        ws=np.array([weights(x) for x in grid])
        # Only change the blue/cyan mixture. Leave all red-containing regions as before.
        active=(ws[:,0]<1e-8)&(np.minimum(ws[:,1],ws[:,2])>=.02)
        breaks=np.diff(np.r_[False,active,False].astype(int))
        for begin,end in zip(np.where(breaks==1)[0],np.where(breaks==-1)[0]):
            if end-begin<3:continue
            x=grid[begin:end];q=ws[begin:end,2];minority=np.minimum(q,1-q)
            cumulative=np.r_[0,np.cumsum(np.diff(x)*(minority[:-1]+minority[1:])/2)]
            blue_integral=np.r_[0,np.cumsum(np.diff(x)*(q[:-1]+q[1:])/2)]
            count=int(cumulative[-1]/MIN_WIDTH)
            if count<1:continue
            boundaries=np.interp(np.linspace(0,cumulative[-1],count+1),cumulative,x)
            replacement=strip(x[0],x[-1]);new=[r.difference(replacement) for r in new]
            for a,b in zip(boundaries[:-1],boundaries[1:]):
                blue=float(np.interp(b,x,blue_integral)-np.interp(a,x,blue_integral))
                cyan=float(b-a-blue)
                assert min(blue,cyan)>=MIN_WIDTH-1e-8
                new[1]=new[1].union(strip(a,a+cyan));new[2]=new[2].union(strip(a+cyan,b))
                cycles.append({'group':group,'start_mm':float(a),'end_mm':float(b),'cyan_width_mm':cyan,'blue_width_mm':blue})
        for i in range(3):old_parts[i].append(raw[i]);new_parts[i].append(new[i])
    old=[unary_union(p) for p in old_parts];new=[unary_union(p) for p in new_parts];outline=unary_union(outlines)
    assert all(r.is_valid for r in new)
    coverage=outline.symmetric_difference(unary_union(new)).area
    overlap=sum(new[i].intersection(new[j]).area for i in range(3) for j in range(i))
    assert max(coverage,overlap)<1e-7
    # No red color geometry or logo contour is changed by this blue-only proposal.
    assert old[0].symmetric_difference(new[0]).area<1e-7
    x0,y0,x1,y1=outline.bounds;box=f'{x0-5} {y0-5} {x1-x0+10} {y1-y0+10}'
    for name,regions in [('proposal',new),('previous',old)]:
        (HERE/f'{name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{x1-x0+10}mm" height="{y1-y0+10}mm" viewBox="{box}"><rect x="{x0-5}" y="{y0-5}" width="{x1-x0+10}" height="{y1-y0+10}" fill="white"/>{path_regions(regions)}</svg>')
    original=ET.parse(src.SOURCE).getroot();content=''.join(ET.tostring(c,encoding='unicode') for c in original)
    defs=f'<defs><g id="original" transform="scale({src.SCALE})">{content}</g><g id="old">{path_regions(old)}</g><g id="new">{path_regions(new)}</g></defs>'
    page=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1220" viewBox="0 0 1600 1220">',defs,
          '<rect width="1600" height="1220" fill="#eef1f5"/><g font-family="DejaVu Sans,sans-serif" fill="#1d2940">',
          '<text x="40" y="52" font-size="30" font-weight="bold">myAI · Gleichmässigerer Blauübergang</text>',
          '<text x="40" y="88" font-size="19">Durchgehend gerade Streifen · kleinere Breitensprünge · keine veränderten Enden</text>']
    def view(ref,x,y,w,h,vb=box):return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}"><use href="#{ref}"/></svg>'
    for x,title,subtitle,ref in [(40,'Original','Unveränderte SVG','original'),(560,'Bisher','Feste Schritte von 0,44 mm','old'),(1080,'Vorschlag','Variable Breiten · ab 0,32 mm','new')]:
        page.extend([f'<rect x="{x}" y="118" width="480" height="620" rx="14" fill="white"/>',f'<text x="{x+22}" y="158" font-size="25" font-weight="bold">{title}</text>',f'<text x="{x+22}" y="188" font-size="17">{subtitle}</text>',view(ref,x+12,205,456,515)])
    # Same detail of the large star's blue transition, without blurring or simulated lighting.
    zoom=f'{143*src.SCALE} {71*src.SCALE} {37*src.SCALE} {23*src.SCALE}'
    for x,title,ref in [(40,'Bisher · Blauübergang vergrössert','old'),(560,'Vorschlag · gleicher Ausschnitt','new')]:
        page.extend([f'<rect x="{x}" y="760" width="480" height="310" rx="14" fill="white"/>',f'<text x="{x+22}" y="800" font-size="21" font-weight="bold">{title}</text>',view(ref,x+22,820,436,225,zoom)])
    page.extend(['<text x="1100" y="800" font-size="21" font-weight="bold">Was sich ändert</text>',
                 '<text x="1100" y="842" font-size="18">Feinere Hell-/Dunkelblau-Anteile.</text>',
                 '<text x="1100" y="876" font-size="18">Breiten wachsen ohne 0,44-mm-Stufen.</text>',
                 '<text x="1100" y="910" font-size="18">Alle Farbgrenzen bleiben gerade.</text>',
                 '<text x="1100" y="944" font-size="18">Rotbereich vorerst unverändert.</text>',
                 '<text x="40" y="1110" font-size="19">Für den P1S mit 0,4-mm-Düse vorgesehen. 0,32 mm ist eine Entwurfsbreite, noch keine bestätigte Druckeinstellung.</text>',
                 '<text x="40" y="1146" font-size="18">Nur Vorschau · noch nicht geslict · Streifen bleiben sichtbar · keine Vorhersage von Filamentfarben oder Hinterleuchtung.</text>',
                 '</g></svg>'])
    (HERE/'comparison.svg').write_text(''.join(page));cairosvg.svg2png(url=str(HERE/'comparison.svg'),write_to=str(HERE/'comparison.png'))
    report={'status':'2D preview only, not sliced','nominal_nozzle_mm':.4,'previous_quantization_mm':OLD_PITCH,'minimum_designed_new_band_mm':MIN_WIDTH,
            'source_sha256':hashlib.sha256(src.SOURCE.read_bytes()).hexdigest(),'method':'Integrate minority fraction in original blue/cyan mixture, divide into equal-area cycles, set continuous cyan/blue widths from integrated target. Red-containing and near-pure zones keep the previous straight-band pattern.',
            'integration_step_max_mm':SAMPLE_STEP,'target_blue_fraction_range_modified':[.02,.98],'all_band_interfaces_straight':True,'endpoint_modifications':False,
            'planar_coverage_error_mm2':coverage,'planar_color_overlap_mm2':overlap,'palette_hex':src.COLORS,
            'previous_runs':runs,'new_cycles':cycles,'color_areas_before_mm2':[r.area for r in old],'color_areas_after_mm2':[r.area for r in new],
            'sliced':False,'physical_print_verified':False,'limitations':'Narrower nominal bands are experimental. Clipped contours can contain smaller features. No claim of gap closure or globally monotonic perceived gradient; original source gradient retained.'}
    (HERE/'preview_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cycles':len(cycles),'coverage_error_mm2':coverage,'overlap_mm2':overlap,'minimum_actual_cycle_band_mm':min(min(c['blue_width_mm'],c['cyan_width_mm']) for c in cycles),'color_areas_before':report['color_areas_before_mm2'],'color_areas_after':report['color_areas_after_mm2']},indent=2))

if __name__=='__main__':main()
