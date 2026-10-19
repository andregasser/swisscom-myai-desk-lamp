"""Original SVG contour and nominal three-color mixture helpers; no file writes."""
from pathlib import Path
from itertools import combinations
import json
import math
import xml.etree.ElementTree as ET

import numpy as np
from shapely import Polygon, GeometryCollection, unary_union
from svgpathtools import parse_path, Line

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'assets/logos/Mode=Dark, Type=Stacked.svg'
SCALE = json.loads((ROOT/'cad/parameters.json').read_text())['logo_canvas_mm']/216
COLORS = ['#F23232', '#1FB9FF', '#0445C8']
NS = '{http://www.w3.org/2000/svg}'


def rgb(color):
    return np.array([int(color[i:i+2], 16)/255 for i in (1, 3, 5)])


def linear(values):
    return np.where(values <= .04045, values/12.92, ((values+.055)/1.055)**2.4)


def weights(target):
    palette = linear(np.array([rgb(c) for c in COLORS]))
    best, result = float('inf'), None
    for size in (1, 2, 3):
        for ids in combinations(range(3), size):
            colors = palette[list(ids)]
            if size == 1:
                w = np.ones(1)
            else:
                tail = np.linalg.lstsq((colors[1:]-colors[0]).T, target-colors[0], rcond=None)[0]
                w = np.r_[1-tail.sum(), tail]
            error = np.sum((w@colors-target)**2)
            if np.min(w) >= -1e-9 and error < best:
                best, result = error, np.zeros(3)
                result[list(ids)] = np.maximum(w, 0)
    return result/result.sum()


def polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape]
    return [p for child in getattr(shape,'geoms',[]) for p in polygons(child)]


def svg_path(shape):
    paths = []
    for poly in polygons(shape):
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)
            paths.append('M'+'L'.join(f'{x:.5f},{y:.5f}' for x,y in coords)+'Z')
    return ''.join(paths)


def sources():
    svg = ET.parse(SOURCE).getroot()
    gradients = {g.attrib['id']: g for g in svg.findall(f'{NS}defs/{NS}linearGradient')}
    groups = {}
    for el in svg.findall(NS+'path'):
        region = GeometryCollection()
        for subpath in parse_path(el.attrib['d']).continuous_subpaths():
            points = []
            for segment in subpath:
                count = 1 if isinstance(segment, Line) else max(8, math.ceil(segment.length()*SCALE/.04))
                for i in range(count):
                    p = segment.point(i/count)*SCALE
                    points.append((p.real, p.imag))
            region = region.symmetric_difference(Polygon(points).buffer(0))
        gradient = gradients[el.attrib['fill'][5:-1]]
        key = (tuple(gradient.attrib[k] for k in ('x1','y1','x2','y2')),
               tuple((s.attrib['offset'],s.attrib['stop-color']) for s in gradient.findall(NS+'stop')))
        groups.setdefault(key, [gradient, []])[1].append(region)
    assert len(groups) == 2  # Separate original gradients for stars and lettering.

    return list(groups.values())
