"""
Step 1 of the Westeros pipeline: the planet's relief, built from canon geography and a tectonic interpretation.

The fictional world grew its continents from simulated plates; here the continent is given (canon), so the order is
reversed: the canon coastline, mountain ranges, uplands, lowlands, rivers and lakes are placed on an Earth-sized
planet (canon_geography.py), and the relief between them follows the tectonic interpretation in ../USAGE.md ('Model decisions'):
  * ocean floor: continental shelf, slope and abyssal plain with Earth's typical depths;
  * the continent: a low platform with coastal lowlands, the ranges as orogens with Earth-analogue summit heights,
    broad uplands and plains, an ice sheet on the Land of Always Winter;
  * canon rivers and lakes are given valleys and basins, so that the water routing of the next steps follows them;
    whether it does is checked in validate_westeros.py.
Essos and Sothoryos are coarse context only (winds, currents, moisture around Westeros).

Usage:   python canon_world.py
Outputs: ../output/world_height.npz, world_plates.npz/.json, world_canon.npz, relief_map.png
"""
import json, math, os
import numpy as np
from matplotlib.path import Path
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont
import canon_geography as cg
from fonts import FONT

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
os.makedirs(OUT, exist_ok=True)
H, W = 720, 1440                       # 0.25 degree, as the fictional world
R = 6371.0
SEED = 7
jj, ii = np.mgrid[0:H, 0:W]
LAT = 90 - (jj + 0.5) / H * 180
LON = -180 + (ii + 0.5) / W * 360
P = np.stack([np.cos(np.radians(LAT)) * np.cos(np.radians(LON)), np.cos(np.radians(LAT)) * np.sin(np.radians(LON)),
              np.sin(np.radians(LAT))], -1).reshape(-1, 3)


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


def km_dist(pts):
    if len(pts) == 0:
        return np.full((H, W), 1e9)
    ch, _ = cKDTree(pts).query(P, workers=-1)
    return (2 * np.arcsin(np.clip(ch / 2, 0, 1)) * R).reshape(H, W)


def fbm(seed, octaves=6, base=3.0, per=14, gain=0.55):
    r = np.random.default_rng(seed)
    out = np.zeros(len(P)); norm = 0.0
    for o in range(octaves):
        f, a = base * 2 ** o, gain ** o
        d = r.normal(size=(per, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
        ph = r.uniform(0, 2 * np.pi, per)
        out += a * np.sin(f * (P @ d.T) * (1 + 0.3 * r.random(per)) + ph).sum(1) / math.sqrt(per / 2)
        norm += a
    return (out / norm).reshape(H, W)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def densify_canon(poly, step_km=5.0):
    pts = []
    for (x0, y0), (x1, y1) in zip(poly[:-1], poly[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step_km))
        for t in np.linspace(0, 1, n, endpoint=False):
            pts.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
    pts.append(poly[-1])
    return np.array(pts, float)


def canon_mask(ring):
    lat, lon = cg.to_latlon(*np.array(ring, float).T)
    return Path(np.column_stack([lon, lat])).contains_points(np.column_stack([LON.ravel(), LAT.ravel()])).reshape(H, W)


def latlon_mask(ring):
    a = np.array(ring, float)
    return Path(np.column_stack([a[:, 1], a[:, 0]])).contains_points(np.column_stack([LON.ravel(), LAT.ravel()])).reshape(H, W)


def ellipse_ring(cx, cy, ax, ay, n=48):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return list(zip(cx + ax * np.cos(t), cy + ay * np.sin(t)))


# ---------------- land ----------------
westeros = canon_mask(cg.COAST)
for spec in cg.ISLANDS.values():
    westeros |= canon_mask(list(zip(*cg.island_ring(spec))))
essos = latlon_mask(cg.ESSOS); sothoryos = latlon_mask(cg.SOTHORYOS)
land = westeros | essos | sothoryos

# canon-km coordinates of every cell (meaningful near Westeros only)
CX, CY = cg.from_latlon(LAT, LON)
near_w = (LAT > 30) & (LAT < 82) & (np.abs(LON) < 40)

# ---------------- distances ----------------
edge = land & ~ndimage.binary_erosion(land, border_value=1)
sea_edge = ~land & ndimage.binary_dilation(land)
d_inland = km_dist(P[edge.ravel()])
d_offshore = km_dist(P[sea_edge.ravel()])

# ---------------- ocean floor ----------------
n_mid = fbm(SEED * 7 + 2, 6, 3.0); n_det = fbm(SEED * 7 + 3, 7, 8.0, gain=0.5)
ocean = -4300 + 400 * n_mid + 150 * n_det                                    # abyssal plain
slope = -150 - 3650 * smoothstep(d_offshore, 70, 330)                         # shelf break ~70 km, foot ~330 km
ocean = np.where(d_offshore < 330, np.maximum(slope, ocean), ocean)
shelf = -20 - 130 * smoothstep(d_offshore, 0, 70) + 25 * n_det
ocean = np.where(d_offshore < 70, shelf, ocean)
ocean = np.minimum(ocean, -15)

# ---------------- Westeros relief ----------------
n_low = fbm(SEED * 7 + 1, 4, 1.5)
ridged = np.clip(1 - np.abs(fbm(SEED * 7 + 4, 6, 6.0)), 0, 1) ** 2
z = 260 + 60 * n_low + 40 * n_det                                             # continental platform
z = np.where((CY > -1650) & (CY < 0), z + 120, z)                            # the North: a higher, older shield
z = np.where(CY >= 0, z + 40, z)                                             # beyond the Wall
for name, ((cx, cy), rad, h) in cg.HILLS.items():
    d = np.hypot(CX - cx, CY - cy)
    z = z + h * np.exp(-(d / rad) ** 2) * (0.8 + 0.4 * ridged)
for name, ((cx, cy), rad, target) in cg.LOWLANDS.items():
    wgt = np.exp(-(np.hypot(CX - cx, CY - cy) / rad) ** 4)
    z = z * (1 - wgt) + (target + 25 * n_det) * wgt
# mountain regions of the canon relief map (outline, summit height, the map's rock texture inside)
range_mask = np.zeros((H, W)); range_h = np.zeros((H, W))
wm, hm = cg.mountain_field(CX[near_w], CY[near_w])
range_mask[near_w] = wm
range_h[near_w] = hm * wm * (0.55 + 0.6 * ridged[near_w])
z = z + range_h
# coasts are low: the platform tapers to sea level within ~40 km of the coast (outside the ranges)
taper = smoothstep(d_inland, 0, 40)
z = 5 + (z - 5) * np.maximum(taper, range_mask * 0.8)
# canon rivers: valleys that descend steadily to the sea (routing of the next steps follows them)
river_pts = []
for name, poly in cg.RIVERS.items():
    lat, lon = cg.to_latlon(*densify_canon(poly, 3.0).T)
    river_pts.append(xyz(lat, lon))
    i_ = np.clip(((lon + 180) / 360 * W).astype(int), 0, W - 1); j_ = np.clip(((90 - lat) / 180 * H).astype(int), 0, H - 1)
    zl = z[j_, i_].copy()
    prof = np.minimum.accumulate(ndimage.uniform_filter1d(zl, 9)) * 0.92  # never rising downstream, a little incised
    z[j_, i_] = np.minimum(z[j_, i_], prof)
d_river = km_dist(np.concatenate(river_pts))
z = z - 40 * np.exp(-(d_river / 15) ** 2) * (1 - range_mask)
# canon lakes: basins
for name, ((cx, cy), (ax, ay)) in cg.LAKES.items():
    e = ((CX - cx) / ax) ** 2 + ((CY - cy) / ay) ** 2
    # a closed basin: the floor lies below the lowest point of the rim (the outflowing river starts at the rim)
    ring_ = (e >= 1) & (e < 4.0)
    if not (e < 1).any():                        # smaller than a cell: deepen the cell that contains its centre
        e = np.where(np.hypot(CX - cx, CY - cy) == np.hypot(CX - cx, CY - cy).min(), 0.0, e)
    rim = float(z[ring_].min()) if ring_.any() else float(z[e < 1].max())
    z = np.where(e < 1, np.minimum(z, rim - 20 - 60 * (1 - e)), z)
# Land of Always Winter: ice sheet surface on a low bedrock platform
ice_t = cg.ICE_SHEET["max_ice_m"] * np.sqrt(smoothstep(CY, cg.ICE_SHEET["from_y_km"], cg.ICE_SHEET["from_y_km"] + 450)) \
    * smoothstep(d_inland, 0, 150)
z = np.where(ice_t > 1.0, np.maximum(z, 300.0 + ice_t), z)                     # ice surface: a dome on the low bedrock platform (Greenland ~3.2 km)
z_w = np.where(westeros & near_w, np.maximum(z, 2), np.nan)

# ---------------- Essos and Sothoryos (coarse context) ----------------
z_e = 450 + 350 * n_low + 120 * n_det + 2200 * ridged ** 3 * smoothstep(d_inland, 100, 600)
z_e = 5 + (z_e - 5) * smoothstep(d_inland, 0, 60)
elev = np.where(land, np.where(westeros & near_w, z_w, z_e), ocean)
elev = np.nan_to_num(elev, nan=200.0).astype(np.float32)
ice = (westeros & near_w) & (ice_t > 50)

# ---------------- outputs ----------------
np.savez_compressed(f"{OUT}/world_height.npz", elevation_m=elev, land=land)
np.savez_compressed(f"{OUT}/world_canon.npz", westeros=westeros & near_w, essos=essos, sothoryos=sothoryos,
                    canon_x_km=CX.astype(np.float32), canon_y_km=CY.astype(np.float32),
                    range_weight=range_mask.astype(np.float32), ice_sheet_m=np.where(ice, ice_t, 0).astype(np.float32),
                    river_dist_km=d_river.astype(np.float32))
# plates file: the tectonic interpretation is descriptive (USAGE.md); the grids keep the fields later steps read
plate = np.where(westeros & near_w, 1, np.where(essos, 2, np.where(sothoryos, 3, 0))).astype(np.int8)
np.savez_compressed(f"{OUT}/world_plates.npz", plate=plate, continental=land, new_crust=np.zeros((H, W), bool),
                    collision=(range_mask > 0.5), boundary_type=np.zeros((H, W), np.int8),
                    boundary_speed_mm_yr=np.zeros((H, W), np.float32), plate_t0=plate, continental_t0=land,
                    omega_rad_per_myr=np.zeros((4, 3)), seeds_t0=np.zeros((4, 3)))
lat_w = LAT[westeros & near_w]
stats = dict(radius_km=R, seed=SEED, scale=cg.SCALE, castle_black_lat=cg.LAT0,
             westeros_area_km2=round(float((np.cos(np.radians(LAT)) * (2 * np.pi * R / W) * (math.pi * R / H))[westeros & near_w].sum())),
             westeros_lat_range=[round(float(lat_w.min()), 2), round(float(lat_w.max()), 2)],
             westeros_max_elev_m=round(float(np.nanmax(z_w))), westeros_mean_elev_m=round(float(np.nanmean(z_w))),
             plates=[dict(id=1, name="Westeros", continental_pct=100.0), dict(id=2, name="Essos", continental_pct=100.0),
                     dict(id=3, name="Sothoryos", continental_pct=100.0)])
json.dump(stats, open(f"{OUT}/world_plates.json", "w"), indent=1)

# relief map of Westeros with canon names
sel = (LAT > 34) & (LAT < 80) & (LON > -16) & (LON < 22)
j0, j1 = np.nonzero(sel.any(1))[0][[0, -1]]; i0, i1 = np.nonzero(sel.any(0))[0][[0, -1]]
sub = elev[j0:j1 + 1, i0:i1 + 1].astype(float); lsub = land[j0:j1 + 1, i0:i1 + 1]
k = 6
img = np.zeros(sub.shape + (3,))
stops = [(0, (70, 120, 70)), (300, (120, 160, 90)), (800, (190, 180, 120)), (1600, (150, 120, 90)), (2600, (230, 230, 230))]
for c in range(3):
    img[..., c] = np.interp(sub, [s for s, _ in stops], [col[c] for _, col in stops])
gy, gx = np.gradient(sub); sh = np.clip(1 + (gx - gy) / 600, 0.6, 1.4)
img = img * sh[..., None]
img[~lsub] = np.stack([np.interp(sub[~lsub], [-5000, 0], [20, 90]), np.interp(sub[~lsub], [-5000, 0], [40, 140]),
                       np.interp(sub[~lsub], [-5000, 0], [90, 200])], -1)
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize(((i1 - i0 + 1) * k, (j1 - j0 + 1) * k), Image.NEAREST)
dr = ImageDraw.Draw(im)


def px(x, y):
    lat, lon = cg.to_latlon(x, y)
    return ((lon + 180) / 360 * W - i0) * k, ((90 - lat) / 180 * H - j0) * k


for name, poly in cg.RIVERS.items():
    dr.line([px(*p) for p in densify_canon(poly, 10)], fill=(40, 90, 220), width=2)
for name, ((cx, cy), (ax, ay)) in cg.LAKES.items():
    dr.polygon([px(*p) for p in ellipse_ring(cx, cy, ax, ay)], outline=(40, 90, 220))
dr.line([px(-240, 0), px(240, 0)], fill=(255, 255, 255), width=3)
for name, (x, y) in cg.PLACES.items():
    u, v = px(x, y)
    dr.ellipse([u - 3, v - 3, u + 3, v + 3], fill=(200, 0, 0))
    dr.text((u + 5, v - 7), name, fill=(0, 0, 0), font=ImageFont.truetype(FONT, 13))
im.save(f"{OUT}/relief_map.png", optimize=True)
print(json.dumps(stats, indent=1))
