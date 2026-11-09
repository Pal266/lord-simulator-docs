"""
The continental frame of Westeros (imported, not run): azimuthal-equidistant projection centred on CENTRE, x = east,
y = north, metres; and the global plot grid, anchored so that Winterfell lies in the middle of plot (0, 0).
Every region and plot is placed in this one frame, so neighbouring regions join exactly.
"""
import math
import numpy as np
import canon_geography as cg

CENTRE = (52.0, 0.0)                     # lat, lon of the frame centre (middle of Westeros)
R_M = 6371000.0
TILE_M = 10000.0                         # global plot size


def xy_to_latlon(x, y):
    lat0, lon0 = map(math.radians, CENTRE)
    x = np.asarray(x, float); y = np.asarray(y, float)
    rho = np.hypot(x, y); c = rho / R_M
    with np.errstate(invalid="ignore", divide="ignore"):
        lat = np.arcsin(np.cos(c) * math.sin(lat0) + np.where(rho > 0, y * np.sin(c) * math.cos(lat0) / rho, 0))
        lon = lon0 + np.arctan2(x * np.sin(c), rho * math.cos(lat0) * np.cos(c) - y * math.sin(lat0) * np.sin(c))
    return np.degrees(lat), np.degrees(lon)


def latlon_to_xy(lat, lon):
    lat0, lon0 = map(math.radians, CENTRE)
    la = np.radians(np.asarray(lat, float)); lo = np.radians(np.asarray(lon, float))
    c = np.arccos(np.clip(math.sin(lat0) * np.sin(la) + math.cos(lat0) * np.cos(la) * np.cos(lo - lon0), -1, 1))
    k = np.where(c > 1e-12, c / np.sin(np.maximum(c, 1e-12)), 1.0)
    return (R_M * k * np.cos(la) * np.sin(lo - lon0),
            R_M * k * (math.cos(lat0) * np.sin(la) - math.sin(lat0) * np.cos(la) * np.cos(lo - lon0)))


def canon_xy(name):
    """Continental x, y (m) of a canon place."""
    x, y = latlon_to_xy(*cg.to_latlon(*cg.PLACES[name]))
    return float(x), float(y)


ANCHOR = canon_xy("Winterfell")          # the global plot grid is anchored here


def tile_nw(i, j):
    """Continental x, y (m) of the north-west corner of global plot (i, j); i grows east, j grows south."""
    return ANCHOR[0] - TILE_M / 2 + i * TILE_M, ANCHOR[1] + TILE_M / 2 - j * TILE_M
