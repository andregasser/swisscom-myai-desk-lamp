"""Check all color participation, continuous-run bounds, and the stored preview."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from build_preview import continuous_runs,MIN_WIDTH,HERE,ROOT

# In particular, a rare third ink must not force all three into a long period
# or disappear from the result. Pure-color inputs must stay pure.
for fractions in ([1.,0.,0.],[.5,.5,0.],[.49,.49,.02],[.1,.3,.6]):
    w=np.array(fractions);grid=np.linspace(0,100,10001);integral=grid[:,None]*w
    runs,printed=continuous_runs(grid,integral,w)
    assert min(r['width_mm'] for r in runs)>=MIN_WIDTH-1e-8
    assert np.max(np.abs(printed-100*w))<.65
    for c in range(3):
        assert (printed[c]>0)==(w[c]>0)
    assert all(a['color']!=b['color'] for a,b in zip(runs,runs[1:]))
    assert all(abs(a['end_mm']-b['start_mm'])<1e-8 for a,b in zip(runs,runs[1:]))

report=json.loads((HERE/'preview_checks.json').read_text())
assert report['source_sha256']==hashlib.sha256((ROOT/'assets/logos/Mode=Dark, Type=Stacked.svg').read_bytes()).hexdigest()
assert report['previous_proposal_sha256']==hashlib.sha256((ROOT/'design_studies/line_gradient_smooth/proposal.svg').read_bytes()).hexdigest()
assert report['nominal_nozzle_mm']==.4 and not report['sliced'] and not report['physical_print_verified']
assert report['all_interfaces_straight'] and not report['endpoint_modifications'] and report['contour_border_mm']==0
assert {g['name'] for g in report['groups']}=={'Sterne','Schriftzug'}
for g in report['groups']:
    assert all(area>0 for area in g['color_area_mm2'])
    assert min(r['width_mm'] for r in g['runs'])>=MIN_WIDTH-1e-8
    assert g['maximum_cumulative_width_error_mm']<.32
assert max(report['planar_coverage_error_mm2'],report['planar_color_overlap_mm2'])<1e-7
for p in HERE.glob('*.svg'):ET.parse(p)
assert not any(p.suffix in ('.stl','.3mf','.gcode') for p in HERE.rglob('*'))
print('All three colors checked in both gradient groups; four scheduler cases passed. Preview only, no print approval.')
