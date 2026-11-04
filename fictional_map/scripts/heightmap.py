"""
Step 3 of the world pipeline: global elevation map built from the tectonic plates.

Rules (simplified real-world geology):
  continent-continent convergence -> broad high ranges / plateaus (Himalaya-like)
  ocean-continent convergence     -> coastal ranges on land + deep trench offshore (Andes-like)
  ocean-ocean convergence         -> volcanic island arc on the overriding plate + trench (Japan-like)
  divergent in ocean              -> mid-ocean ridge; sea floor deepens with distance (age) from it
  divergent in continent          -> rift valley with raised shoulders (East-Africa-like)
  continental interiors           -> low plains + old eroded ranges (Appalachian-like)
  continental margins             -> shelf (~ -120 m) and slope to the abyss

Inputs : world_plates.npz, world_plates.json
Outputs: relief_map.png, heightmap_16bit.png, world_height.npz, world_height.json
"""
import json, math, sys
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
D = np.load(f"{OUT}/world_plates.npz")
META = json.load(open(f"{OUT}/world_plates.json"))
SEED = META["seed"]
plate = D["plate"].astype(int)
cont = D["continental"]
omega = D["omega_rad_per_myr"]
H, W = plate.shape
R = META["radius_km"]
LAND_TARGET = 0.29
rng = np.random.default_rng(SEED + 1000)

jj, ii = np.mgrid[0:H, 0:W]
LAT = (0.5 - (jj + 0.5) / H) * np.pi
LON = ((ii + 0.5) / W) * 2 * np.pi - np.pi
Pg = np.stack([np.cos(LAT) * np.cos(LON), np.cos(LAT) * np.sin(LON), np.sin(LAT)], -1)
P = Pg.reshape(-1, 3)
AREA = np.cos(LAT)


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def fbm(X, seed, octaves=6, base=2.0, per=14, gain=0.55):
    r = np.random.default_rng(seed)
    out = np.zeros(len(X)); norm = 0.0
    for o in range(octaves):
        f, a = base * 2 ** o, gain ** o
        d = unit(r.normal(size=(per, 3)))
        ph = r.uniform(0, 2 * np.pi, per)
        out += a * np.sin(f * (X @ d.T) * (1 + 0.3 * r.random(per)) + ph).sum(1) / math.sqrt(per / 2)
        norm += a
    return (out / norm).reshape(H, W)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


_wr = np.random.default_rng(SEED + 77)
WARP = np.stack([fbm(P, SEED * 3 + k, octaves=4, base=5.0).ravel() for k in range(3)], -1)
PQ = unit(P + 0.035 * WARP)


def km_dist(points_xyz, query=PQ):
    """Great-circle distance (km) from every cell to the nearest point, + its index."""
    if len(points_xyz) == 0:
        return np.full((H, W), 1e9), np.zeros((H, W), int)
    tree = cKDTree(points_xyz)
    chord, idx = tree.query(query, k=1, workers=-1)
    return (2 * np.arcsin(np.clip(chord / 2, 0, 1)) * R).reshape(H, W), idx.reshape(H, W)


# ---------- plate boundaries with both sides known ----------
cont_blur = ndimage.gaussian_filter(cont.astype(float), sigma=(3, 3), mode="wrap")
plate_cont = {p["id"]: p["continental_pct"] for p in META["plates"]}
rank = np.array([plate_cont.get(p, 0) + 0.01 * p for p in range(len(omega))])

pts, attrs = [], []
for di, dj in ((1, 0), (0, 1)):
    if di:
        b = np.roll(plate, -1, 1); pb = np.roll(Pg, -1, 1); cb = np.roll(cont_blur, -1, 1)
    else:
        b = np.vstack([plate[1:], plate[-1:]]); pb = np.vstack([Pg[1:], Pg[-1:]]); cb = np.vstack([cont_blur[1:], cont_blur[-1:]])
    m = plate != b
    a_ = plate[m]; b_ = b[m]
    mid = unit(Pg[m] + pb[m])
    nvec = unit(pb[m] - Pg[m] + 1e-12)
    rel = np.cross(omega[a_], mid) - np.cross(omega[b_], mid)
    conv = (rel * nvec).sum(-1)
    mag = np.linalg.norm(rel, axis=-1) + 1e-12
    typ = np.where(conv > 0.35 * mag, 1, np.where(conv < -0.35 * mag, 2, 3))
    ca, cb_ = cont_blur[m], cb[m]
    sub = np.where((ca > 0.5) & (cb_ > 0.5), 0, np.where((ca > 0.5) | (cb_ > 0.5), 1, 2))  # 0 cc,1 oc,2 oo
    over = np.where(rank[a_] >= rank[b_], a_, b_)
    pts.append(mid)
    attrs.append(np.stack([typ, sub, a_, b_, over, mag * R], -1))
pts = np.concatenate(pts); attrs = np.concatenate(attrs)
btyp, bsub, bover, bspeed = attrs[:, 0].astype(int), attrs[:, 1].astype(int), attrs[:, 4].astype(int), attrs[:, 5]
spd = np.clip(bspeed / 25.0, 0.55, 1.5)        # mm/yr -> uplift factor

conv_i = np.where(btyp == 1)[0]
div_i = np.where(btyp == 2)[0]
tra_i = np.where(btyp == 3)[0]
d_conv, n_conv = km_dist(pts[conv_i]); n_conv = conv_i[n_conv]
d_div, n_div = km_dist(pts[div_i]); n_div = div_i[n_div]
d_tra, _ = km_dist(pts[tra_i])

# coastline distance (continental crust edge)
edge = cont & ~ndimage.binary_erosion(cont, iterations=1, border_value=1)
edge |= ~cont & ndimage.binary_dilation(cont, iterations=1)
coast_pts = Pg[edge & cont]
d_coast_land, _ = km_dist(coast_pts)                  # for land cells: distance inland
d_coast_sea, _ = km_dist(Pg[edge & ~cont])            # for sea cells: distance offshore

# ---------- noise fields ----------
n_low = fbm(P, SEED * 7 + 1, octaves=4, base=1.5)
n_mid = fbm(P, SEED * 7 + 2, octaves=6, base=3.0)
n_det = fbm(P, SEED * 7 + 3, octaves=7, base=8.0, gain=0.5)
ridged = 1 - np.abs(fbm(P, SEED * 7 + 4, octaves=6, base=4.0))
ridged = np.clip(ridged, 0, 1) ** 3
arc_spots = fbm(P, SEED * 7 + 5, octaves=4, base=8.0)

# ---------- ocean floor ----------
age_proxy = np.clip(d_div / 2800.0, 0, 1)
ocean = -2600 - 2700 * np.sqrt(age_proxy)                        # ridge crest -> abyssal plain
ocean += 900 * np.exp(-(d_div / 90) ** 2)                        # ridge axis relief
ocean += 250 * n_mid + 120 * n_det
ocean += 350 * np.exp(-(d_tra / 40) ** 2) * n_det * 2            # fracture-zone roughness
# shelf + slope near continents
shelf = -60 - 90 * smoothstep(d_coast_sea, 0, 120) + 40 * n_det
ocean = np.where(d_coast_sea < 160, shelf, ocean * smoothstep(d_coast_sea, 120, 420) +
                 (-1500) * (1 - smoothstep(d_coast_sea, 120, 420)))
ocean = np.minimum(ocean, -40)

# ---------- continents ----------
land = 180 + 350 * (n_low + 0.3) + 120 * n_mid
land *= 0.35 + 0.65 * smoothstep(d_coast_land, 0, 450)            # coastal plains
land += 50 * n_det
old_mask = smoothstep(fbm(P, SEED * 7 + 6, octaves=3, base=2.5), 0.05, 0.35)
land += 1900 * ridged ** 0.7 * old_mask * (0.6 + 0.4 * n_mid)       # old eroded ranges
land += 650 * smoothstep(fbm(P, SEED * 7 + 9, octaves=4, base=2.0), 0.15, 0.5)   # uplands / plateaus
land -= 220 * smoothstep(fbm(P, SEED * 7 + 10, octaves=3, base=2.5), 0.25, 0.6)  # interior basins
land += 900 * ndimage.gaussian_filter(D["collision"].astype(float), 4, mode="wrap") * (0.5 + ridged)

# ---------- convergent margins ----------
cs = bsub[n_conv]; sp = spd[n_conv]; over = bover[n_conv]
rug = 0.45 + 0.9 * ridged + 0.2 * n_det
wmod = 0.7 + 0.6 * (fbm(P, SEED * 7 + 8, octaves=4, base=6.0) * 0.5 + 0.5)
# continent-continent: wide high belt / plateau
cc_w = (420 + 220 * (sp - 1)) * wmod
mount_cc = 5200 * sp * np.exp(-(d_conv / cc_w) ** 2) * rug
plateau = 1800 * sp * smoothstep(cc_w * 1.2 - d_conv, 0, 250) * (0.8 + 0.2 * n_mid)
mount_cc = np.maximum(mount_cc, plateau)
# ocean-continent: coastal cordillera on land
mount_oc = 4300 * sp * np.exp(-((d_conv - 170 * wmod) / (230 * wmod)) ** 2) * rug
volc = 1200 * np.exp(-((d_conv - 220) / 40) ** 2) * (arc_spots > 0.35)
uplift = np.where(cs == 0, mount_cc, np.where(cs == 1, mount_oc + volc, 0.0))
uplift = ndimage.gaussian_filter(np.where(d_conv < 1400, uplift, 0), 1.3, mode="wrap")
land = land + uplift * (0.75 + 0.5 * np.clip(n_det + 0.5, 0, 1))

# trench on the subducting oceanic side; island arcs on the overriding side
on_over = plate == over
trench = -4200 * sp * np.exp(-(d_conv / 55) ** 2)
arc = 4800 * sp * np.exp(-((d_conv - 150) / 45) ** 2) * smoothstep(arc_spots, -0.05, 0.45) \
      + 1400 * np.exp(-((d_conv - 150) / 90) ** 2)
ocean_conv = np.where(cs == 1, np.where(~on_over | True, trench, 0),
                      np.where(cs == 2, np.where(on_over, arc + 0.4 * trench, trench), 0.0))
ocean = ocean + np.where(d_conv < 600, ocean_conv, 0)

# ---------- continental rifts ----------
rift = (-1300 * np.exp(-(d_div / 45) ** 2) + 700 * np.exp(-((d_div - 110) / 55) ** 2))
land = land + np.where(d_div < 300, rift, 0)

elev = np.where(cont, land, ocean)
d_coast = np.minimum(np.where(cont, d_coast_land, 1e9), np.where(cont, 1e9, d_coast_sea))
coast_noise = fbm(P, SEED * 7 + 11, octaves=6, base=9.0) + 0.6 * fbm(P, SEED * 7 + 12, octaves=5, base=18.0)
elev += 620 * coast_noise * np.exp(-(d_coast / 280) ** 2)
# blend the coastline a little so crust edges are not razor sharp
elev = ndimage.gaussian_filter(elev, 0.8, mode="wrap")

# ---------- sea level: hit the target land fraction ----------
order = np.argsort(elev, axis=None)
cum = np.cumsum(AREA.ravel()[order]); cum /= cum[-1]
sea = elev.ravel()[order][np.searchsorted(cum, 1 - LAND_TARGET)]
elev = elev - sea
hi = elev > 4000
elev[hi] = 4000 + 5000 * np.tanh((elev[hi] - 4000) / 5000)
land_mask = elev > 0
land_pct = float((AREA * land_mask).sum() / AREA.sum() * 100)

# ---------- render relief map ----------
stops_sea = [(-9000, (6, 14, 40)), (-6000, (12, 32, 78)), (-4000, (22, 58, 118)), (-2500, (40, 92, 150)),
             (-1000, (58, 120, 175)), (-150, (95, 160, 205)), (0, (150, 200, 225))]
stops_land = [(0, (84, 140, 84)), (200, (120, 160, 92)), (600, (178, 182, 112)), (1200, (196, 168, 106)),
              (2000, (168, 124, 82)), (3000, (140, 104, 82)), (4200, (170, 160, 156)), (5500, (245, 245, 245))]


def ramp(z, stops):
    xs = [s[0] for s in stops]
    out = np.zeros(z.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(z, xs, [s[1][c] for s in stops])
    return out


col = np.where(land_mask[..., None], ramp(elev, stops_land), ramp(elev, stops_sea))
dx_km = 2 * np.pi * R / W * np.maximum(np.cos(LAT), 0.05)
dy_km = np.pi * R / H
gx = (np.roll(elev, -1, 1) - np.roll(elev, 1, 1)) / (2 * dx_km * 1000)
gy = (np.vstack([elev[:1], elev[:-1]]) - np.vstack([elev[1:], elev[-1:]])) / (2 * dy_km * 1000)
ex = 22.0
nx, ny, nz = -gx * ex, -gy * ex, np.ones_like(elev)
nn = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
lx, ly, lz = -0.6, 0.6, 0.55
ln = math.sqrt(lx ** 2 + ly ** 2 + lz ** 2)
shade = (nx * lx + ny * ly + nz * lz) / (nn * ln)
shade = np.clip(shade, 0, 1)
k = np.where(land_mask, 0.55, 0.3)
col = col * ((1 - k) + k * shade / shade.mean())[..., None]
coast = land_mask ^ ndimage.binary_erosion(land_mask, iterations=1)
col[coast] = col[coast] * 0.55

S = 1.25
img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((int(W * S), int(H * S)), Image.LANCZOS)
d = ImageDraw.Draw(img)
for lat_d in range(-60, 61, 30):
    y = (0.5 - lat_d / 180) * img.height
    d.line([(0, y), (img.width, y)], fill=(255, 255, 255), width=1)

from fonts import FONT, FONTB
LEG = 110
canvas = Image.new("RGB", (img.width, img.height + LEG), (24, 26, 32))
canvas.paste(img, (0, 0))
d = ImageDraw.Draw(canvas)
f = ImageFont.truetype(FONT, 16); fb = ImageFont.truetype(FONTB, 17)
bar_x0, bar_x1, by = 40, img.width - 40, img.height + 40
zs = np.linspace(-8000, 6000, bar_x1 - bar_x0)
bar = np.where(zs[:, None] > 0, ramp(zs, stops_land), ramp(zs, stops_sea))
for k_, c in enumerate(bar):
    d.line([(bar_x0 + k_, by), (bar_x0 + k_, by + 22)], fill=tuple(int(v) for v in c))
for z in (-8000, -6000, -4000, -2000, 0, 1000, 2000, 3000, 4000, 5000, 6000):
    x = bar_x0 + (z + 8000) / 14000 * (bar_x1 - bar_x0)
    d.line([(x, by + 22), (x, by + 30)], fill=(220, 220, 220))
    lbl = f"{z:+d}" if z else "0"
    d.text((x - 18, by + 32), lbl + (" м" if z == 6000 else ""), font=f, fill=(220, 220, 220))
d.text((bar_x0, img.height + 10), "Висота над рівнем моря", font=fb, fill=(235, 235, 235))
canvas.save(f"{OUT}/relief_map.png", optimize=True)

# ---------- export ----------
zmin, zmax = float(elev.min()), float(elev.max())
h16 = np.round((elev - zmin) / (zmax - zmin) * 65535).astype(np.uint16)
Image.fromarray(h16).save(f"{OUT}/heightmap_16bit.png")
np.savez_compressed(f"{OUT}/world_height.npz", elevation_m=elev.astype(np.float32), land=land_mask)
j_hi = np.unravel_index(elev.argmax(), elev.shape); j_lo = np.unravel_index(elev.argmin(), elev.shape)
stats = dict(seed=SEED, grid=[W, H], projection="equirectangular", km_per_px_equator=round(2 * np.pi * R / W, 1),
             land_pct=round(land_pct, 1), highest_m=round(zmax), deepest_m=round(zmin),
             mean_land_m=round(float((elev * AREA)[land_mask].sum() / AREA[land_mask].sum())),
             mean_ocean_m=round(float((elev * AREA)[~land_mask].sum() / AREA[~land_mask].sum())),
             heightmap_16bit_range_m=[round(zmin), round(zmax)],
             highest_at_latlon=[round(float(np.degrees(LAT[j_hi])), 1), round(float(np.degrees(LON[j_hi])), 1)],
             deepest_at_latlon=[round(float(np.degrees(LAT[j_lo])), 1), round(float(np.degrees(LON[j_lo])), 1)])
json.dump(stats, open(f"{OUT}/world_height.json", "w"), indent=1)
print(json.dumps(stats))
lbl, nlab = ndimage.label(land_mask)
sizes = ndimage.sum(AREA, lbl, range(1, nlab + 1)) / AREA.sum() * 100
print("landmasses >0.3%:", sorted([round(float(s), 2) for s in sizes if s > 0.3], reverse=True), "islands total", nlab)
