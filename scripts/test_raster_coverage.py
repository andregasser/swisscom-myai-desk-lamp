"""Regression checks for defects that cell-center sampling cannot detect."""
import math
import unittest

import manifold3d as m
import numpy as np

from validate_raster_coverage import footprint, union
from validate_raster_test import model_segments


class CoverageChecks(unittest.TestCase):
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
