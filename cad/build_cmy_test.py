"""Extrude the approved CMY calibration recipes as four AMS material volumes."""
import hashlib
import json
from pathlib import Path
import manifold3d as m
import numpy as np
import build as mono
import build_multicolor as ams

ROOT = mono.ROOT
OUT = ROOT/'output/cmy_calibration'
STUDY = ROOT/'design_studies/cmy_calibration'
PLATE = '14_cmy_calibration'
OFFSET = (40,40,0)
PALETTE = [dict(slot=i,name=n,hex=h) for i,n,h in [
    (1,'Jade White','#FFFFFF'),(2,'Cyan','#0086D6'),
    (3,'Magenta','#EC008C'),(4,'Yellow','#F4EE2A')]]


def main():
    for folder in ('stl','geometry','print','profiles','preview','coverage'):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    for name in ('geometry_validation.json','print_validation.json',f'print/{PLATE}_P1S.3mf','print/slicer_result.json'):
        (OUT/name).unlink(missing_ok=True)
    (OUT/'print/STATUS.md').write_text('Neubau: Slicing und Flächenprüfung ausstehend.\n')
    plan=json.loads((STUDY/'preview_checks.json').read_text())
    assert plan['card_dimensions_mm']==[90,62] and plan['white_base_mm']==.4
    assert plan['nozzle_mm']==.4 and len(plan['fields'])==27
    width,height=plan['card_dimensions_mm']
    base=m.CrossSection.square((width-4,height-4)).translate((2,2)).offset(2,circular_segments=128).extrude(.4)
    groups={c:[] for c in 'CMY'}
    transformed=[]
    for f in plan['fields']:
        # Mirror X for viewing the white underside; Y converts SVG-down to CAD-up.
        x,y=width-f['x_mm']-f['width_mm'],height-f['y_mm']-f['height_mm']
        for layer in f['stack_from_bed'][1:]:
            groups[layer['material']].append(mono.box(f['width_mm'],f['height_mm'],
                layer['z_end_mm']-layer['z_start_mm'],(x,y,layer['z_start_mm'])))
        transformed.append({**f,'print_xy_mm':[x,y]})
    parts=[base,*[mono.union(groups[c]) for c in 'CMY']]
    intersection=0.
    for i,p in enumerate(parts):
        for q in parts[i+1:]:
            intersection+=abs((p^q).volume())
    assert intersection<1e-7
    joined=mono.union(parts)
    assert len(joined.decompose())==1
    expected=base.volume()+sum(f['width_mm']*f['height_mm']*sum(f['layers'].values())*.1 for f in plan['fields'])
    assert abs(joined.volume()-expected)<1e-5
    meshes=[]
    for slot,part in enumerate(parts,1):
        mesh=mono.mesh(part)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        mesh.export(OUT/'stl'/f'slot_{slot}.stl')
        meshes.append({'slot':slot,'volume_mm3':float(mesh.volume),'components':len(mesh.split()),
                       'sha256':hashlib.sha256((OUT/'stl'/f'slot_{slot}.stl').read_bytes()).hexdigest()})
    assert np.allclose(mono.mesh(joined).bounds,[[0,0,0],[90,62,1]],atol=1e-6)
    # Independent section check of every layer against rectangles from the recipes.
    checks=[]
    for z,thickness in [(.2,.2),(.3,.1),(.4,.1),*[(n/10,.1) for n in range(5,11)]]:
        mid=z-thickness/2
        for slot,c in enumerate('WCMY',1):
            expected_region=base.slice(mid) if slot==1 else m.CrossSection()
            if slot>1:
                for f in transformed:
                    for layer in f['stack_from_bed'][1:]:
                        if layer['material']==c and layer['z_start_mm']<mid<layer['z_end_mm']:
                            expected_region+=m.CrossSection.square((f['width_mm'],f['height_mm'])).translate(f['print_xy_mm'])
            actual=parts[slot-1].slice(mid)
            diff=(actual-expected_region).area()+(expected_region-actual).area()
            assert diff<1e-6,(z,slot,diff)
            checks.append({'z_mm':z,'slot':slot,'area_mm2':actual.area(),'difference_mm2':diff})
    ams.multipart_3mf(parts,OUT/'geometry'/f'{PLATE}.3mf','myAI CMY Kalibrierkarte',OFFSET,colors=PALETTE)
    report={'plate_name':PLATE,'size_mm':[90,62,1],'print_offset_mm':OFFSET,'front_is_bed_face':True,
            'palette':PALETTE,'source_study_sha256':hashlib.sha256((STUDY/'preview_checks.json').read_bytes()).hexdigest(),
            'one_connected_card':True,'material_intersections_mm3':intersection,'watertight_slot_components':meshes,
            'section_checks':checks,'fields':transformed,'physical_print_verified':False,
            'view_orientation':'White underside: reverse X from print-bed view, same vertical top edge.',
            'layer_plan':[[.2,.2],[.3,.1],[.4,.1],*[[n/10,.1] for n in range(5,11)]]}
    (OUT/'geometry_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CMY card: 90 x 62 x 1 mm; 27 fields; 4 watertight material meshes; 36 sections checked.')


if __name__=='__main__': main()
