"""
Shared helpers for the great_river_mouth region: configuration, local projection, tile geometry
and sampling of the global planet rasters.

All other region scripts import this module; it does nothing when run on its own.
"""
import json, math, os
import numpy as np
from scipy import ndimage

REGION_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
WORLD_OUT = os.path.normpath(os.path.join(REGION_DIR, "..", "..", "output"))   # fictional_map/output
REGION_OUT = os.path.join(REGION_DIR, "output")
CFG = json.load(open(os.path.join(REGION_DIR, "region.json")))
R_M = 6371000.0

LAT0 = math.radians(CFG["centre_lat_deg"])
LON0 = math.radians(CFG["centre_lon_deg"])
HALF_M = CFG["size_km"] * 500.0


def xy_to_latlon(x, y):
    """Local azimuthal-equidistant coordinates (m, x east / y north) -> latitude, longitude (degrees)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    rho = np.hypot(x, y)
    c = rho / R_M
    with np.errstate(invalid="ignore", divide="ignore"):
        lat = np.arcsin(np.cos(c) * math.sin(LAT0) + np.where(rho > 0, y * np.sin(c) * math.cos(LAT0) / rho, 0))
        lon = LON0 + np.arctan2(x * np.sin(c), rho * math.cos(LAT0) * np.cos(c) - y * math.sin(LAT0) * np.sin(c))
    return np.degrees(lat), (np.degrees(lon) + 180) % 360 - 180


def grid(res_m):
    """Cell-centre coordinates of a north-up grid covering the whole region at res_m metres."""
    n = int(round(2 * HALF_M / res_m))
    c = -HALF_M + (np.arange(n) + 0.5) * res_m
    x, y = np.meshgrid(c, c[::-1])            # row 0 = north
    return x, y


def tile_vertices(col, row):
    """x, y (m) of the vertices of one Unreal tile; edges are shared with neighbours."""
    t = CFG["tiles"]
    size = t["size_km"] * 1000.0
    n = t["vertices"]
    x0 = -HALF_M + col * size
    y0 = HALF_M - row * size
    v = np.linspace(0.0, size, n)
    return np.meshgrid(x0 + v, y0 - v)


def tile_name(col, row):
    return f"tile_x{col}_y{row}"


def sample_world(field, lat, lon, order=1):
    """Sample an equirectangular world raster (row 0 = north, 0.25 deg cells) at lat/lon."""
    H, W = field.shape
    j = (90.0 - lat) / 180.0 * H - 0.5
    i = (lon + 180.0) / 360.0 * W - 0.5
    pad = 4
    f = np.concatenate([field[:, -pad:], field, field[:, :pad]], axis=1)   # longitude wraps
    return ndimage.map_coordinates(f.astype(float), [j, i + pad], order=order, mode="nearest")


def load_world():
    """Load the planet outputs this region is cut from."""
    need = ["world_height.npz", "world_climate.npz", "world_hydrology.npz", "world_plates.npz", "world_climate.json"]
    missing = [n for n in need if not os.path.exists(os.path.join(WORLD_OUT, n))]
    if missing:
        raise SystemExit(f"Missing planet outputs in {WORLD_OUT}: {missing}. Run the planet pipeline first (see USAGE.md).")
    return dict(height=np.load(os.path.join(WORLD_OUT, "world_height.npz")),
                climate=np.load(os.path.join(WORLD_OUT, "world_climate.npz")),
                hydro=np.load(os.path.join(WORLD_OUT, "world_hydrology.npz")),
                plates=np.load(os.path.join(WORLD_OUT, "world_plates.npz")),
                climate_meta=json.load(open(os.path.join(WORLD_OUT, "world_climate.json"))))
