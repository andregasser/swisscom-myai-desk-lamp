"""Sample the untouched SVG gradients and dither to the four available PLA colors."""
from itertools import combinations
import xml.etree.ElementTree as ET

import numpy as np
import build_multicolor as ams
import build_raster_test as old


def linear_rgb(rgb):
    rgb = np.asarray(rgb)
    return np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)


def hex_rgb(value):
    return np.array([int(value[i:i+2], 16)/255 for i in (1, 3, 5)])


PALETTE = linear_rgb([hex_rgb(c['hex']) for c in ams.P['colors']])


def sources():
    svg = ET.parse(ams.ROOT/'assets/logos'/ams.P['logo_source']).getroot()
    ns = '{http://www.w3.org/2000/svg}'
    scale = ams.mono.P['logo_canvas_mm']/216
    gradients = {}
    for gradient in svg.findall(f'{ns}defs/{ns}linearGradient'):
        assert gradient.get('spreadMethod', 'pad') == 'pad'
        assert gradient.get('color-interpolation', 'sRGB') == 'sRGB'
        vector = np.array([float(gradient.attrib[k]) for k in ('x1','y1','x2','y2')])*scale
        stops = []
        for stop in gradient.findall(ns+'stop'):
            offset = stop.attrib['offset']
            t = float(offset[:-1])/100 if offset.endswith('%') else float(offset)
            assert float(stop.get('stop-opacity', '1')) == 1
            stops.append((t, stop.attrib['stop-color']))
        assert all(a[0] < b[0] for a, b in zip(stops, stops[1:]))
        gradients[tuple(np.round(vector, 10))] = stops
    # Reuse only the original contour tessellation and vector extraction, never
    # the old artificial stops, reduced bands, Bayer thresholds or image assets.
    for section, p0, direction in old.source_regions():
        stops = gradients[tuple(np.round(np.r_[p0, p0+direction], 10))]
        yield section, p0, direction, stops


def sample_srgb(points, p0, direction, stops):
    t = (np.asarray(points)-p0) @ direction / np.dot(direction, direction)
    positions = np.array([stop[0] for stop in stops])
    colors = np.array([hex_rgb(stop[1]) for stop in stops])
    return np.stack([np.interp(t, positions, colors[:, i]) for i in range(3)], axis=-1)


def palette_weights(targets):
    """Closest convex mixture in linear RGB; explicit gamut clipping, not new stops.

    Enumerate every palette face and solve its affine least-squares projection.
    Reject negative coefficients; the best remaining face gives nonnegative
    area weights summing to one. Nominal reflectance only, not filament optics.
    """
    targets = np.asarray(targets)
    best = np.full(len(targets), np.inf)
    weights = np.zeros((len(targets), 4))
    for size in range(1, 5):
        for indices in combinations(range(4), size):
            colors = PALETTE[list(indices)]
            if size == 1:
                local = np.ones((len(targets), 1))
            else:
                basis = (colors[1:]-colors[0]).T
                tail = (targets-colors[0]) @ np.linalg.pinv(basis).T
                local = np.c_[1-tail.sum(axis=1), tail]
            error = np.sum((local@colors-targets)**2, axis=1)
            valid = np.all(local >= -1e-9, axis=1) & (error < best)
            best[valid] = error[valid]
            weights[valid] = 0
            for j, index in enumerate(indices):
                weights[valid, index] = local[valid, j]
    weights = np.maximum(weights, 0)
    weights /= weights.sum(axis=1, keepdims=True)
    assert np.allclose(weights.sum(axis=1), 1)
    return weights


def diffuse(cells, targets, forced=None):
    """Serpentine Floyd–Steinberg, accounting for forced contour assignments.

    A forced color participates in error propagation, so its deviation from the
    original target is carried into later cells. This is not an exact optical
    or area-weighted color reproduction, especially along clipped boundaries.
    """
    weights = palette_weights(linear_rgb(targets))
    positions = {cell: i for i, cell in enumerate(cells)}
    errors = np.zeros_like(weights)
    result = {}
    forced = forced or {}
    for row in sorted({cell[0] for cell in cells}):
        step = 1 if row % 2 == 0 else -1
        for cell in sorted((c for c in cells if c[0] == row), key=lambda c: step*c[1]):
            i = positions[cell]
            value = weights[i]+errors[i]
            index = forced.get(cell, int(np.argmax(value)))
            result[cell] = index
            error = value-np.eye(4)[index]
            r, c = cell
            for neighbor, fraction in (((r,c+step), 7/16), ((r+1,c-step), 3/16),
                                       ((r+1,c), 5/16), ((r+1,c+step), 1/16)):
                if neighbor in positions:
                    errors[positions[neighbor]] += error*fraction
    return result, weights
