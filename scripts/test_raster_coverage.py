"""Regression checks for defects that cell-center sampling cannot detect."""
import math
import unittest
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

import manifold3d as m
import numpy as np
import trimesh

from validate_raster_coverage import analyze, footprint, union
from validate_raster_test import model_segments


class CoverageChecks(unittest.TestCase):
    def test_thin_color_schedule_checks_intermediate_white_layer(self):
        # At 0.1-mm layer height a missing patch at Z=0.3 must not disappear
        # from an audit that historically checked only Z=0.2 and Z=0.4.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'stl').mkdir()
            backing = trimesh.creation.box(extents=(3,1,.4))
            backing.apply_translation((1.5,.5,.2))
            backing.export(root/'stl/slot_1.stl')
            for slot in (2,3,4):
                ink = trimesh.creation.box(extents=(1,1,.2))
                ink.apply_translation((slot-1.5,.5,.5))
                ink.export(root/'stl'/f'slot_{slot}.stl')
            (root/'geometry_validation.json').write_text(json.dumps({
                'print_offset_mm':[0,0,0], 'size_mm':[3,1,.6]}))
            rows=[]
            for z in (.2,.3,.4,.5,.6):
                for slot in ((1,) if z<=.4 else (2,3,4)):
                    left,right=(-.5,3.5) if slot==1 else (slot-2.5,slot-.5)
                    if z==.3:
                        right=1.0  # Deliberate missing white backing patch.
                    rows.extend([f'M620 S{slot-1}A',f'M621 S{slot-1}A',
                        f'G1 X{left} Y0.5 Z{z}', '; FEATURE: Top surface',
                        '; LINE_WIDTH: 1.0',f'G1 X{right} E1'])
            raw='\n'.join(rows).encode()
            file=root/'synthetic.3mf'
            with zipfile.ZipFile(file,'w') as archive:
                archive.writestr('Metadata/project_settings.config',json.dumps({'extruder_offset':['0x0']}))
                archive.writestr('Metadata/plate_1.gcode',raw)
                archive.writestr('Metadata/plate_1.gcode.md5',hashlib.md5(raw).hexdigest())
            result=analyze(file,'',.5,output_root=root,color_layer_height=.1,
                           backing_layers=((.2,.2),(.3,.1),(.4,.1)))
            self.assertAlmostEqual(result['ink_area_mm2'],3,places=5)
            self.assertAlmostEqual(result['nominal_unprinted_ink_area_mm2'],0,places=5)
            self.assertGreater(result['white_backing_layers']['0.3']['uncovered_beyond_allowance_mm2'],1)
            self.assertFalse(result['digital_coverage_passed'])

    def test_round_caps_are_included(self):
        bead = m.CrossSection([footprint(np.array([0.,0.]),np.array([1.,0.]),.4)])
        self.assertAlmostEqual(bead.area(), .4+math.pi*.2**2, delta=.001)
        # A butt-ended line drawing misses this valid deposited material.
        end_probe = m.CrossSection.square((.02,.02)).translate((1.10,-.01))
        self.assertAlmostEqual((bead ^ end_probe).area(), .0004, places=6)

    def test_center_covered_but_off_center_void_is_detected(self):
        intended = m.CrossSection.square((.8,.8))
        defect = m.CrossSection.square((.2,.2)).translate((.05,.05))
        deposited = intended-defect
        center = m.CrossSection.circle(.1,32).translate((.4,.4))
        self.assertAlmostEqual((center-deposited).area(),0.,places=8)
        self.assertAlmostEqual((intended-deposited).area(),.04,places=8)
        self.assertGreater((intended-deposited.offset(.03)).area(),.019)

    def test_planned_white_is_not_counted_as_missing_ink(self):
        card = m.CrossSection.square((2,2))
        white = m.CrossSection.square((.8,.8)).translate((.6,.6))
        ink = card-white
        all_paths = union([white,ink])
        self.assertAlmostEqual((ink-all_paths).area(),0.,places=8)
        # Conversely, a missing ink patch remains visible in the metric.
        patch = m.CrossSection.square((.2,.2)).translate((.1,.1))
        self.assertAlmostEqual((ink-union([white,ink-patch])).area(),.04,places=8)

    def test_arc_and_model_offset(self):
        code = '''M620 S1A
M621 S1A
G1 X1 Y0 Z0.6
; FEATURE: Outer wall
; LINE_WIDTH: 0.4
G3 X0 Y1 I-1 J0 E0.1
'''
        paths = list(model_segments(code,{'extruder_offset':['0x2']}))
        self.assertGreater(len(paths),15)
        for z,slot,a,b,width in paths:
            self.assertEqual((z,slot,width),(.6,2,.4))
            self.assertLessEqual(np.linalg.norm(b-a),.09)
            self.assertAlmostEqual(np.linalg.norm(a-[0,2]),1.,places=7)
        np.testing.assert_allclose(paths[-1][3],[0,3])

    def test_full_circle_without_xy_is_not_lost(self):
        code = '''M620 S1A
M621 S1A
G1 X1 Y0 Z0.6
; FEATURE: Outer wall
; LINE_WIDTH: 0.4
G2 I-1 J0 E0.1
'''
        paths = list(model_segments(code,{'extruder_offset':['0x0']}))
        length = sum(np.linalg.norm(b-a) for _,_,a,b,_ in paths)
        self.assertAlmostEqual(length,2*math.pi,delta=.003)


if __name__ == '__main__':
    unittest.main()
