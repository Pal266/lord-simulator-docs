"""
Step 2 of the world pipeline: tectonic plates for an Earth-like planet
in the "recent supercontinent breakup" phase.

Model (simplified but physically motivated):
 1. Plates at breakup time = noise-warped spherical Voronoi cells.
 2. One irregular supercontinent (+ a few microcontinents) of continental crust.
 3. Each plate gets an Euler pole; continental plates drift away from the
    old supercontinent centre, oceanic plates move randomly.
 4. Every plate is rotated forward by DRIFT_MYR million years.
    Overlaps -> denser (oceanic) crust subducts, continent-continent = collision.
    Gaps    -> new oceanic crust, split between neighbours (mid-ocean ridges).
 5. Boundaries classified by relative plate velocity:
    convergent / divergent / transform.

Outputs: plates_map.png, history.png, world_plates.npz, world_plates.json
"""
import json, math, sys
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
W, H = 1440, 720                 # simulation grid (equirectangular)
R_KM = 6371.0                    # planet radius (Earth-like)
DRIFT_MYR = 150.0                # time since the supercontinent started to break up
N_MAJOR, N_MINOR = 8, 9
CONT_FRACTION = 0.30             # share of the surface that is continental crust

rng = np.random.default_rng(SEED)

# ---------- grid ----------
jj, ii = np.mgrid[0:H, 0:W]
LAT = (0.5 - (jj + 0.5) / H) * np.pi
LON = ((ii + 0.5) / W) * 2 * np.pi - np.pi
P = np.stack([np.cos(LAT) * np.cos(LON), np.cos(LAT) * np.sin(LON), np.sin(LAT)], -1).reshape(-1, 3)


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def fbm(X, seed, octaves=5, base=1.6, per=14):
    """Seamless 3D fractal noise on the sphere via random Fourier features (~[-1,1])."""
    r = np.random.default_rng(seed)
    out = np.zeros(len(X))
    norm = 0.0
    for o in range(octaves):
        f, a = base * 2 ** o, 0.55 ** o
        d = unit(r.normal(size=(per, 3)))
        ph = r.uniform(0, 2 * np.pi, per)
        out += a * np.sin(f * (X @ d.T) * (1 + 0.3 * r.random(per)) + ph).sum(1) / math.sqrt(per / 2)
        norm += a
    return out / norm


def to_idx(X):
    lat = np.arcsin(np.clip(X[:, 2], -1, 1))
    lon = np.arctan2(X[:, 1], X[:, 0])
    j = np.clip(((0.5 - lat / np.pi) * H).astype(int), 0, H - 1)
    i = ((lon + np.pi) / (2 * np.pi) * W).astype(int) % W
    return j * W + i


def rot(axis, ang):
    a = axis / np.linalg.norm(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def wrap_edt(mask_false_is_target):
    """EDT with horizontal wrap: returns nearest-True indices for every cell."""
    m = np.tile(mask_false_is_target, (1, 3))
    _, (ji, ii_) = ndimage.distance_transform_edt(~m, return_indices=True)
    ji, ii_ = ji[:, W:2 * W], ii_[:, W:2 * W] % W
    return ji, ii_


# ---------- 1. plate seeds & breakup-time tessellation ----------
n = N_MAJOR + N_MINOR
seeds = []
while len(seeds) < n:
    s = unit(rng.normal(size=3))
    min_sep = 0.55 if len(seeds) < N_MAJOR else 0.32
    if all(np.arccos(np.clip(s @ t, -1, 1)) > min_sep for t in seeds):
        seeds.append(s)
seeds = np.array(seeds)
size = np.r_[rng.uniform(1.0, 1.45, N_MAJOR), rng.uniform(0.45, 0.7, N_MINOR)]

warp = np.stack([fbm(P, SEED * 10 + k, octaves=5, base=1.8) for k in range(3)], -1)
PW = unit(P + 0.22 * warp)


def tessellate(seed_vecs):
    d = np.arccos(np.clip(PW @ seed_vecs.T, -1, 1)) / size
    return d.argmin(1)


T0 = tessellate(seeds)

# ---------- 2. supercontinent ----------
c0 = unit(rng.normal(size=3))
c0 = unit(c0 * np.array([1, 1, 0.35]))          # keep the old supercontinent at mid latitudes
# elongate it: anisotropic metric along a random tangent direction
t_dir = unit(np.cross(c0, unit(rng.normal(size=3))))
ang = np.arccos(np.clip(PW @ c0, -1, 1))
along = np.abs(PW @ t_dir)
score = ang - 0.45 * along * np.exp(-((ang - 0.9) ** 2) / 0.5) - 0.20 * fbm(P, SEED * 10 + 5, octaves=6, base=2.4)
C0 = score < np.quantile(score, CONT_FRACTION - 0.025)
# a few microcontinents far from the supercontinent
for k in range(6):
    mc = unit(rng.normal(size=3))
    if mc @ c0 < -0.1:
        a2 = np.arccos(np.clip(PW @ mc, -1, 1))
        r_mc = rng.uniform(0.06, 0.13)
        C0 |= a2 < r_mc * (1 + 0.5 * fbm(P, SEED * 10 + 20 + k, base=5))
C0 = ndimage.binary_opening(C0.reshape(H, W), iterations=2).reshape(-1)

# ---------- 3. Euler poles ----------
cont_frac = np.array([C0[T0 == p].mean() if (T0 == p).any() else 0 for p in range(n)])
centroid = np.array([unit(P[T0 == p].mean(0)) for p in range(n)])
axes, angles = [], []
for p in range(n):
    if cont_frac[p] > 0.25:
        ax = np.cross(c0, centroid[p])
        if np.linalg.norm(ax) < 0.15:            # plate sits on the old centre: slow, random
            ax, a = unit(rng.normal(size=3)), rng.uniform(0.06, 0.14)
        else:
            ax = unit(unit(ax) + 0.30 * unit(rng.normal(size=3)))
            a = rng.uniform(0.38, 0.70)
    else:
        ax, a = unit(rng.normal(size=3)), rng.uniform(0.20, 0.75)
    axes.append(ax); angles.append(a)
axes, angles = np.array(axes), np.array(angles)
omega = axes * (angles / DRIFT_MYR)[:, None]           # rad / Myr

# ---------- 4. drift forward ----------
rank = cont_frac + rng.uniform(0, 0.05, n)             # buoyancy: continental plates win
best = np.full(len(P), -1.0)
plate = np.full(len(P), -1)
cont = np.zeros(len(P), bool)
n_cont_cover = np.zeros(len(P), np.int8)
for p in range(n):
    Rm = rot(axes[p], angles[p])
    src = to_idx(P @ Rm)                               # inverse rotation: x = R^T y
    cov = T0[src] == p
    c = C0[src] & cov
    pr = np.where(cov, 2.0 * c + rank[p], -1.0)
    win = pr > best
    best[win], plate[win], cont[win] = pr[win], p, c[win]
    n_cont_cover += c

gap = plate < 0
ji, ii_ = wrap_edt((~gap).reshape(H, W))
plate = plate.reshape(H, W)
plate[gap.reshape(H, W)] = plate[ji, ii_][gap.reshape(H, W)]
cont = cont.reshape(H, W)
new_crust = gap.reshape(H, W)
collision = (n_cont_cover >= 2).reshape(H, W)
# smooth plate edges a little (majority filter) so boundaries are not jagged
for _ in range(2):
    counts = np.stack([ndimage.uniform_filter((plate == p).astype(float), 5, mode="wrap") for p in range(n)])
    plate = counts.argmax(0)
# continental crust stays only on its carrying plate after smoothing (drop slivers)
cont = ndimage.binary_opening(cont, iterations=1)

# ---------- 5. boundary classification ----------
Pg = P.reshape(H, W, 3)
btype = np.zeros((H, W), np.int8)       # 0 none, 1 convergent, 2 divergent, 3 transform
bstrength = np.zeros((H, W))
for dj, di in ((0, 1), (1, 0)):
    a = plate
    b = np.roll(plate, -di, 1) if di else np.vstack([plate[1:], plate[-1:]])
    pb = np.roll(Pg, -di, 1) if di else np.vstack([Pg[1:], Pg[-1:]])
    diff = a != b
    m = unit(Pg + pb)
    nvec = unit(pb - Pg + 1e-12)
    va = np.cross(omega[a], m)
    vb = np.cross(omega[b], m)
    rel = va - vb                                   # a relative to b
    conv = (rel * nvec).sum(-1)                     # >0: a moves towards b
    mag = np.linalg.norm(rel, axis=-1) + 1e-12
    t = np.where(conv > 0.35 * mag, 1, np.where(conv < -0.35 * mag, 2, 3))
    t = np.where(diff, t, 0)
    upd = diff & (btype == 0)
    btype[upd] = t[upd]
    bstrength[upd] = (mag * R_KM)[upd]               # km/Myr == mm/yr

# ---------- per-plate stats ----------
plate_info = []
for p in range(n):
    msk = plate == p
    area = (np.cos(LAT) * msk).sum() / np.cos(LAT).sum()
    if area < 0.004:          # ignore slivers
        continue
    # label anchor: deepest interior point
    tiled = np.tile(msk, (1, 3))
    dist = ndimage.distance_transform_edt(tiled)[:, W:2 * W] * np.cos(LAT) ** 0.5
    j, i = np.unravel_index(dist.argmax(), dist.shape)
    x = Pg[j, i]
    v = np.cross(omega[p], x) * R_KM                 # km/Myr
    east = np.array([-math.sin(LON[j, i]), math.cos(LON[j, i]), 0])
    north = np.array([-math.sin(LAT[j, i]) * math.cos(LON[j, i]),
                      -math.sin(LAT[j, i]) * math.sin(LON[j, i]), math.cos(LAT[j, i])])
    plate_info.append(dict(id=int(p), area_pct=round(100 * float(area), 1),
                           continental_pct=round(100 * float(cont[msk].mean()), 1),
                           major=bool(p < N_MAJOR), speed_cm_yr=round(float(np.linalg.norm(v)) / 10, 1),
                           anchor=[int(i), int(j)], vel_en=[float(v @ east), float(v @ north)]))

for k_, inf in enumerate(sorted(plate_info, key=lambda d_: -d_["area_pct"])):
    inf["num"] = k_ + 1
# ---------- render ----------
def hsv(h, s, v):
    import colorsys
    return np.array(colorsys.hsv_to_rgb(h, s, v))

golden = 0.61803398875
pal = np.array([hsv((0.07 + p * golden) % 1, 0.55, 0.9) for p in range(n)])
ocean = np.array([0.10, 0.22, 0.40]); young = np.array([0.22, 0.45, 0.66]); land = np.array([0.80, 0.70, 0.48])

def render_map(plate_f, cont_f, new_f, btype_f, scale):
    base = np.where(cont_f[..., None], 0.82 * land + 0.18 * pal[plate_f], 0.85 * ocean + 0.15 * pal[plate_f])
    if new_f is not None:
        base = np.where((new_f & ~cont_f)[..., None], 0.88 * young + 0.12 * pal[plate_f], base)
    edge = np.zeros_like(plate_f, bool)
    edge |= plate_f != np.roll(plate_f, 1, 1)
    edge |= np.vstack([plate_f[:1], plate_f[:-1]]) != plate_f
    base = np.where(edge[..., None], base * 0.6, base)
    img = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).resize(
        (int(W * scale), int(H * scale)), Image.NEAREST)
    if btype_f is not None:
        cols = {1: (230, 50, 40), 2: (60, 220, 255), 3: (255, 210, 40)}
        bt = np.array(Image.fromarray(btype_f).resize(img.size, Image.NEAREST))
        thick = ndimage.grey_dilation(bt, size=(3, 3))
        arr = np.array(img)
        for k, c in cols.items():
            arr[thick == k] = c
        img = Image.fromarray(arr)
    return img

from fonts import FONT, FONTB
S = 1.25
mp = render_map(plate, cont, new_crust, btype, S)
d = ImageDraw.Draw(mp)
f_lab = ImageFont.truetype(FONTB, 17)
f_sm = ImageFont.truetype(FONT, 13)
# graticule
for lat_d in range(-60, 61, 30):
    y = (0.5 - lat_d / 180) * mp.height
    d.line([(0, y), (mp.width, y)], fill=(255, 255, 255, 60), width=1)
for lon_d in range(-150, 181, 30):
    x = (lon_d + 180) / 360 * mp.width
    d.line([(x, 0), (x, mp.height)], fill=(255, 255, 255), width=1) if lon_d == 0 else None
# arrows + labels
for info in plate_info:
    i, j = info["anchor"]; x, y = i * S, j * S
    ve, vn = info["vel_en"]
    L = 6 + 6.0 * math.hypot(ve, vn) / 10
    nrm = math.hypot(ve, vn) + 1e-9
    dx, dy = ve / nrm * L, -vn / nrm * L
    d.line([(x, y), (x + dx, y + dy)], fill=(255, 255, 255), width=4)
    ah = math.atan2(dy, dx)
    tip = (x + dx, y + dy)
    for s_ in (0.5, -0.5):
        d.line([tip, (tip[0] - 12 * math.cos(ah + s_), tip[1] - 12 * math.sin(ah + s_))], fill=(255, 255, 255), width=4)
    txt = f"{info['num']}"
    d.text((x - 6, y - 24), txt, font=f_lab, fill=(255, 255, 255), stroke_width=3, stroke_fill=(20, 20, 30))
    d.text((x - 10, y + 6), f"{info['speed_cm_yr']} см/р", font=f_sm, fill=(255, 255, 255), stroke_width=2, stroke_fill=(20, 20, 30))

# legend strip
LEG_H = 120
canvas = Image.new("RGB", (mp.width, mp.height + LEG_H), (24, 26, 32))
canvas.paste(mp, (0, 0))
d = ImageDraw.Draw(canvas)
f_l = ImageFont.truetype(FONT, 18)
y0 = mp.height + 18
items = [((230, 50, 40), "Конвергентна межа (зіткнення / субдукція → гори, вулкани)"),
         ((60, 220, 255), "Дивергентна межа (рифт / серединно-океанічний хребет)"),
         ((255, 210, 40), "Трансформна межа (зсув, землетруси)")]
for k, (c, t) in enumerate(items):
    yy = y0 + k * 30
    d.rectangle([20, yy + 4, 52, yy + 16], fill=c)
    d.text((64, yy), t, font=f_l, fill=(230, 230, 230))
xx = 960
for k, (c, t) in enumerate([(tuple((land * 255).astype(int)), "Континентальна кора"),
                            (tuple((ocean * 255).astype(int)), "Стара океанічна кора"),
                            (tuple((young * 255).astype(int)), "Молода кора (після розпаду)")]):
    yy = y0 + k * 30
    d.rectangle([xx, yy + 2, xx + 32, yy + 18], fill=c, outline=(200, 200, 200))
    d.text((xx + 44, yy), t, font=f_l, fill=(230, 230, 230))
canvas.save(f"{OUT}/plates_map.png", optimize=True)

# history: breakup time vs now
S2 = 0.55
then = render_map(T0.reshape(H, W), C0.reshape(H, W), None, None, S2)
now = render_map(plate, cont, new_crust, None, S2)
hist = Image.new("RGB", (then.width * 2 + 30, then.height + 50), (24, 26, 32))
hist.paste(then, (0, 50)); hist.paste(now, (then.width + 30, 50))
d = ImageDraw.Draw(hist)
f_h = ImageFont.truetype(FONTB, 20)
d.text((10, 14), f"{int(DRIFT_MYR)} млн років тому: суперконтинент", font=f_h, fill=(235, 235, 235))
d.text((then.width + 40, 14), "Зараз: розійшлися материки", font=f_h, fill=(235, 235, 235))
hist.save(f"{OUT}/history.png", optimize=True)

# ---------- save data for the next steps ----------
np.savez_compressed(f"{OUT}/world_plates.npz", plate=plate.astype(np.int8), continental=cont,
                    new_crust=new_crust, collision=collision, boundary_type=btype,
                    boundary_speed_mm_yr=bstrength.astype(np.float32),
                    plate_t0=T0.reshape(H, W).astype(np.int8), continental_t0=C0.reshape(H, W),
                    omega_rad_per_myr=omega, seeds_t0=seeds)
land_pct = float((np.cos(LAT) * cont).sum() / np.cos(LAT).sum() * 100)
meta = dict(seed=SEED, grid=[W, H], projection="equirectangular", radius_km=R_KM,
            drift_myr=DRIFT_MYR, continental_crust_pct=round(land_pct, 1),
            supercontinent_centre=c0.tolist(), plates=plate_info)
json.dump(meta, open(f"{OUT}/world_plates.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: meta[k] for k in ("seed", "continental_crust_pct")}))
for pi in plate_info:
    print(pi["num"], pi["area_pct"], pi["continental_pct"], pi["speed_cm_yr"], pi["major"])
print("boundary cells:", {k: int((btype == k).sum()) for k in (1, 2, 3)}, "collision cells", int(collision.sum()))
