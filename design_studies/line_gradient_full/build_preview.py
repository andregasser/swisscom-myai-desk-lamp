"""Full original-gradient preview with straight, continuously sized color runs.

All three inks participate. No solids, print projects or G-code are produced.
"""
from pathlib import Path
import sys
import math
import json
import hashlib
import xml.etree.ElementTree as ET
import numpy as np
from shapely import Polygon, unary_union
import cairosvg

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'cad'))
import line_gradient_regions as src

MIN_WIDTH=.32
HYSTERESIS=.16
SAMPLE_STEP=.01


def continuous_runs(grid,integral,initial):
    """Track integrated color deficits; switch at a continuous error crossing.

A rare third ink receives an occasional minimum-width run instead of setting
    the repeat length for all three inks. No color weights are discarded.
    """
    start=float(grid[0]);end=float(grid[-1]);printed=np.zeros(3)
    current=int(np.argmax(initial));runs=[]
    def target(x):return np.array([np.interp(x,grid,integral[:,i]) for i in range(3)])
    while start<end-1e-9:
        earliest=start+MIN_WIDTH
        if earliest>=end-MIN_WIDTH:
            stop=end
        else:
            xs=np.r_[earliest,grid[(grid>earliest)&(grid<end-MIN_WIDTH)]]
            desired=np.column_stack([np.interp(xs,grid,integral[:,i]) for i in range(3)])
            errors=desired-printed
            errors[:,current]-=xs-start
            others=[i for i in range(3) if i!=current]
            crossing=errors[:,others].max(axis=1)-errors[:,current]-HYSTERESIS
            ids=np.flatnonzero(crossing>=0)
            if not len(ids):stop=end
            else:
                k=int(ids[0]);lower=earliest if k==0 else float(xs[k-1]);upper=float(xs[k])
                for _ in range(30):
                    mid=(lower+upper)/2;err=target(mid)-printed;err[current]-=mid-start
                    if max(err[others])-err[current]>=HYSTERESIS:upper=mid
                    else:lower=mid
                stop=upper
        width=stop-start
        assert width>=MIN_WIDTH-1e-8
        runs.append({'color':current,'start_mm':start,'end_mm':stop,'width_mm':width})
        printed[current]+=width
        if stop>=end-1e-9:break
        error=target(stop)-printed;error[current]=-np.inf
        current=int(np.argmax(error));start=stop
    assert abs(sum(r['width_mm'] for r in runs)-(end-grid[0]))<1e-7
    return runs,printed


def paths(regions):
    return ''.join(f'<path fill="{c}" fill-rule="evenodd" d="{src.svg_path(r)}"/>' for c,r in zip(src.COLORS,regions))


def main():
    all_parts=[[],[],[]];outlines=[];groups=[]
    for index,(gradient,shapes) in enumerate(src.sources()):
        outline=unary_union([p for p in src.polygons(unary_union(shapes)) if p.area>=.001]);outlines.append(outline)
        p0=np.array([float(gradient.attrib[k]) for k in ('x1','y1')])*src.SCALE
        v=np.array([float(gradient.attrib[k]) for k in ('x2','y2')])*src.SCALE-p0
        length=np.linalg.norm(v);direction=v/length;normal=np.array([-direction[1],direction[0]])
        stops=[(float(s.attrib['offset']),src.rgb(s.attrib['stop-color'])) for s in gradient.findall(src.NS+'stop')]
        positions=np.array([s[0] for s in stops]);values=np.array([s[1] for s in stops])
        corners=np.array([(x,y) for x in outline.bounds[::2] for y in outline.bounds[1::2]])
        projection=(corners-p0)@direction
        lo,hi=math.floor(min(projection)/.44)*.44,math.ceil(max(projection)/.44)*.44
        grid=np.linspace(lo,hi,math.ceil((hi-lo)/SAMPLE_STEP)+1)
        weights=np.array([src.weights(src.linear(np.array([np.interp(x/length,positions,values[:,i]) for i in range(3)]))) for x in grid])
        integral=np.vstack([np.zeros(3),np.cumsum(np.diff(grid)[:,None]*(weights[:-1]+weights[1:])/2,axis=0)])
        runs,printed=continuous_runs(grid,integral,weights[0])
        local=[[],[],[]]
        for run in runs:
            a=p0+direction*run['start_mm'];b=p0+direction*run['end_mm']
            local[run['color']].append(outline.intersection(Polygon([a-normal*300,b-normal*300,b+normal*300,a+normal*300])))
        regions=[unary_union(p) for p in local]
        assert outline.symmetric_difference(unary_union(regions)).area<1e-7
        for c in range(3):all_parts[c].append(regions[c])
        # Quantify integrated 1D color balance, including all rare third-color contributions.
        cumulative_actual=np.zeros_like(integral)
        for run in runs:
            cumulative_actual[:,run['color']]+=np.clip(grid-run['start_mm'],0,run['width_mm'])
        groups.append({'name':'Schriftzug' if index==0 else 'Sterne','source_gradient_id':gradient.attrib['id'],
                       'gradient_origin_mm':p0.tolist(),'gradient_direction':direction.tolist(),
                       'runs':runs,'integrated_target_width_mm':integral[-1].tolist(),
                       'integrated_printed_width_mm':printed.tolist(),
                       'maximum_cumulative_width_error_mm':float(np.max(np.abs(cumulative_actual-integral))),
                       'color_area_mm2':[r.area for r in regions]})
    regions=[unary_union(p) for p in all_parts];outline=unary_union(outlines)
    assert all(r.is_valid for r in regions)
    coverage=outline.symmetric_difference(unary_union(regions)).area
    overlap=sum(regions[i].intersection(regions[j]).area for i in range(3) for j in range(i))
    assert max(coverage,overlap)<1e-7
    x0,y0,x1,y1=outline.bounds;box=f'{x0-5} {y0-5} {x1-x0+10} {y1-y0+10}'
    (HERE/'proposal.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{x1-x0+10}mm" height="{y1-y0+10}mm" viewBox="{box}"><rect x="{x0-5}" y="{y0-5}" width="{x1-x0+10}" height="{y1-y0+10}" fill="white"/>{paths(regions)}</svg>')
    original=ET.parse(src.SOURCE).getroot();original_content=''.join(ET.tostring(c,encoding='unicode') for c in original)
    previous_path=ROOT/'design_studies/line_gradient_smooth/proposal.svg'
    previous=ET.parse(previous_path).getroot();previous_content=''.join(ET.tostring(c,encoding='unicode') for c in previous if c.tag==src.NS+'path')
    defs=f'<defs><g id="original" transform="scale({src.SCALE})">{original_content}</g><g id="old">{previous_content}</g><g id="new">{paths(regions)}</g></defs>'
    page=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1370" viewBox="0 0 1600 1370">',defs,
          '<rect width="1600" height="1370" fill="#eef1f5"/><g font-family="DejaVu Sans,sans-serif" fill="#1d2940">',
          '<text x="40" y="52" font-size="30" font-weight="bold">myAI · Alle Farbübergänge feiner verteilt</text>',
          '<text x="40" y="88" font-size="19">Rot, Cyan und Blau gemeinsam · Sterne und Schriftzug · durchgehend gerade Streifen</text>']
    def view(ref,x,y,w,h,vb=box):return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}"><use href="#{ref}"/></svg>'
    for x,title,subtitle,ref in [(40,'Original','Unveränderte SVG','original'),(560,'Letzte Vorschau','Nur Blauübergang verfeinert','old'),(1080,'Gesamter Verlauf','Alle Farben · variable Breiten ab 0,32 mm','new')]:
        page.extend([f'<rect x="{x}" y="118" width="480" height="620" rx="14" fill="white"/>',f'<text x="{x+22}" y="158" font-size="25" font-weight="bold">{title}</text>',f'<text x="{x+22}" y="188" font-size="17">{subtitle}</text>',view(ref,x+12,205,456,515)])
    details=[(40,'Kleiner Stern · Rotübergang',(52,21,33,17)),(560,'Schriftzug · Rotübergang',(49,148,35,17)),(1080,'Grosser Stern · Blauübergang',(143,71,37,19))]
    for x,title,(dx,dy,dw,dh) in details:
        vb=f'{dx*src.SCALE} {dy*src.SCALE} {dw*src.SCALE} {dh*src.SCALE}'
        page.extend([f'<rect x="{x}" y="760" width="480" height="440" rx="14" fill="white"/>',f'<text x="{x+20}" y="798" font-size="20" font-weight="bold">{title}</text>'])
        for y,label,ref in [(829,'Bisher','old'),(1010,'Neu','new')]:
            page.append(f'<text x="{x+20}" y="{y}" font-size="16">{label}</text>')
            page.append(view(ref,x+22,y+10,436,145,vb))
    page.extend(['<text x="40" y="1240" font-size="19">0,4-mm-Düse bleibt vorgesehen. Die schmalen 0,32-mm-Bänder sind experimentell und noch nicht geslict.</text>',
                 '<text x="40" y="1276" font-size="18">Keine Knicke oder Randzonen · keine künstliche Weichzeichnung · noch keine Druckfreigabe oder bestätigter Lückenschluss.</text>',
                 '<text x="40" y="1312" font-size="18">Nominelle Bildschirmfarben; aus der Nähe bleiben Streifen sichtbar. Keine Simulation von Filament oder Hinterleuchtung.</text>',
                 '</g></svg>'])
    (HERE/'comparison.svg').write_text(''.join(page));cairosvg.svg2png(url=str(HERE/'comparison.svg'),write_to=str(HERE/'comparison.png'))
    report={'status':'Full-gradient 2D preview only','nominal_nozzle_mm':.4,'minimum_designed_band_mm':MIN_WIDTH,
            'hysteresis_mm':HYSTERESIS,'integration_step_max_mm':SAMPLE_STEP,
            'source_sha256':hashlib.sha256(src.SOURCE.read_bytes()).hexdigest(),'previous_proposal_sha256':hashlib.sha256(previous_path.read_bytes()).hexdigest(),
            'method':'Continuous deficit-based color scheduling with minimum run length and hysteresis; all three original-derived palette weights retained in both gradient groups.',
            'palette_hex':src.COLORS,'groups':groups,'all_interfaces_straight':True,'endpoint_modifications':False,'contour_border_mm':0,
            'planar_coverage_error_mm2':coverage,'planar_color_overlap_mm2':overlap,
            'color_area_mm2':[r.area for r in regions],'sliced':False,'physical_print_verified':False,
            'limitations':'Minimum band width before contour clipping only. Integrated balance is along the gradient coordinate, not optical or contour-area matching. Perceived smoothness, filament color and full slicer coverage remain unverified.'}
    (HERE/'preview_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'groups':[{k:g[k] for k in ('name','color_area_mm2','maximum_cumulative_width_error_mm')} for g in groups],
                      'run_count':sum(len(g['runs']) for g in groups),'minimum_width_mm':min(r['width_mm'] for g in groups for r in g['runs']),
                      'coverage_error_mm2':coverage,'overlap_mm2':overlap},indent=2))

if __name__=='__main__':main()
