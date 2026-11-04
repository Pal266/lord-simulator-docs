"""
Region step 1: regional process model at 100 m for a mountain range, its foothills and a river plain.

Scientific decisions (details and sources in ../MODEL_NOTES.md):
  1. Tectonics: no active plate boundary within ~320 km, so the range is an old orogen held up by isostasy
     (like the Scandinavian mountains or the Appalachians). Rivers erode it while the large-scale shape is
     kept by slow isostatic uplift: the 4 km-smoothed relief is relaxed back to the planet relief every step.
  2. Fluvial landscape: stream-power erosion (K = 1e-6, m = 0.5, discharge-based) and hillslope diffusion
     for 2 million years carve the ridges and valleys.
  3. Glaciers: equilibrium-line altitude (ELA) from the Ohmura et al. (1992) relation between summer
     temperature and annual precipitation at the ELA; lapse rate 6.5 C/km. At the Last Glacial Maximum the
     region was ~8 C colder (Tierney et al. 2020: 6 C globally, 14 C in the Arctic, interpolated by latitude),
     so the ELA was ~1.2 km lower. Glacier extent per valley from the accumulation-area ratio AAR = 0.6
     (typical of mid-latitude cirque and valley glaciers).
  4. Glacial landforms: U-shaped troughs with parabolic cross-sections (z ~ y^2), over-deepened floors,
     cirques at glacier heads, terminal and lateral moraines; after the ice melted, lakes fill the
     over-deepened basins behind the moraines.
  5. Present day: glaciers only where the mountains still reach above today's ELA.

Usage:  python regional_model.py
Outputs (../output): regional_model.npz, regional_model.json, regional_relief.png, regional_landforms.png
"""
import json, math, os, sys
import numpy as np
from numba import njit
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont
from region_common import CFG, HALF_M, REGION_OUT, sample_world, xy_to_latlon, load_world
from region_flow import accumulate, diffuse, priority_flood, route, stream_power

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
from fonts import FONT, FONTB

DX = float(CFG["model_resolution_m"])
# ---------------- parameters (see MODEL_NOTES.md) ----------------
DOMAIN_HALF = 70e3                 # model domain 140 x 140 km around the 100 km square
EROSION_YR, EROSION_DT = 2.0e6, 5.0e4
K_SP, M_SP = 1.0e-6, 0.5
D_HILL = 0.01                      # m2/yr
RELAX = 0.5                        # share of the large-scale misfit restored each step (isostatic uplift)
RELAX_SIGMA_M = 4000.0
SEED_RELIEF_M = 30.0
LAPSE = 0.0065                     # C per m
LGM_COOLING_GLOBAL, LGM_COOLING_POLAR = 6.0, 14.0
AAR = 0.6
MIN_ACCUM_KM2 = 0.5                # smallest glacier accumulation area modelled
OHMURA = (645.0, 296.0, 9.0)       # P = a + b T + c T^2 (mm, C)

os.makedirs(REGION_OUT, exist_ok=True)
wd = load_world()
xs = np.arange(-DOMAIN_HALF + DX / 2, DOMAIN_HALF, DX)
ys = np.arange(DOMAIN_HALF - DX / 2, -DOMAIN_HALF, -DX)
X, Y = np.meshgrid(xs, ys)
Hn, Wn = X.shape
LAT, LON = xy_to_latlon(X, Y)
inside = (np.abs(X) <= HALF_M) & (np.abs(Y) <= HALF_M)


def fbm2(seed, octaves, base_km, amp):
    r = np.random.default_rng(seed)
    out = np.zeros_like(X); norm = 0
    for o in range(octaves):
        k = 2 * math.pi / (base_km * 1000 / 2 ** o); a = 0.55 ** o
        for _ in range(8):
            th = r.uniform(0, math.pi)
            out += a * np.sin(k * (X * math.cos(th) + Y * math.sin(th)) + r.uniform(0, 2 * math.pi))
        norm += a * 2.0
    return out / norm * amp


# ---------------- planet frame ----------------
trend = ndimage.gaussian_filter(sample_world(wd["hydro"]["elevation_eroded_m"], LAT, LON, 3), 20)
sea0 = trend <= 0
P = sample_world(wd["climate"]["precip_annual_mm"], LAT, LON, 1)
runoff_m = np.clip(sample_world(wd["hydro"]["runoff_mm"], LAT, LON, 1), 0, None) / 1000.0
summer_is_jan = CFG["centre_lat_deg"] < 0
T_summer_planet = sample_world(wd["climate"]["temp_jan_c" if summer_is_jan else "temp_jul_c"], LAT, LON, 1)
T_winter_planet = sample_world(wd["climate"]["temp_jul_c" if summer_is_jan else "temp_jan_c"], LAT, LON, 1)

# ---------------- 1. fluvial landscape with isostatic uplift ----------------
z = np.where(sea0, trend, trend + fbm2(7, 5, 12, SEED_RELIEF_M))
fixed = sea0.copy()
q_cell = (runoff_m * DX * DX).ravel()
for step in range(int(EROSION_YR / EROSION_DT)):
    f, rec, dist, oa, od = route(z, fixed, DX)
    Q = accumulate(od, rec, q_cell)
    zf = stream_power(z.ravel().copy(), oa, rec, dist, Q, K_SP, M_SP, EROSION_DT, fixed.ravel())
    z = diffuse(zf.reshape(Hn, Wn), D_HILL, EROSION_DT, DX, fixed, 1)
    misfit = trend - ndimage.gaussian_filter(z, RELAX_SIGMA_M / DX)
    z = np.where(fixed, z, z + RELAX * misfit)
z_fluvial = z.copy()


# ---------------- 2. glaciers: ELA and extent ----------------
def t_at_ela(p_mm):
    a, b, c = OHMURA
    return (-b + np.sqrt(b * b - 4 * c * (a - p_mm))) / (2 * c)


T_summer_z = T_summer_planet + LAPSE * (trend - z)          # summer temperature at each 100 m cell
ela_now = z + (T_summer_z - t_at_ela(P)) / LAPSE              # height where summer temperature = ELA temperature
ela_now = ndimage.gaussian_filter(ela_now, 20)
lgm_cool = LGM_COOLING_GLOBAL + (LGM_COOLING_POLAR - LGM_COOLING_GLOBAL) * (abs(CFG["centre_lat_deg"]) - 30) / 60
ela_lgm = ela_now - lgm_cool / LAPSE


@njit(cache=True)
def glacier_systems(order_asc, rec, zf, floor_):
    """Label every cell above `floor_` with the cell where its flow path first drops below the floor."""
    n = rec.shape[0]
    lab = np.full(n, -1, np.int64)
    for k in order_asc:
        if zf[k] < floor_[k]:
            continue
        r = rec[k]
        if r == k:
            lab[k] = k
        elif zf[r] < floor_[r]:
            lab[k] = r
        else:
            lab[k] = lab[r]
    return lab


def glacier_extent(zg, ela):
    f, rec, dist, oa, od = route(zg, sea0, DX)
    floor_ = (ela - 1500.0).ravel()
    lab = glacier_systems(oa, rec, zg.ravel(), floor_)
    ice = np.zeros(Hn * Wn, bool)
    terminus = np.full(Hn * Wn, np.nan)
    zr = zg.ravel(); er = ela.ravel()
    order = np.argsort(lab)
    labs = lab[order]
    bounds = np.flatnonzero(np.diff(labs)) + 1
    n_glaciers = 0
    for grp in np.split(order, bounds):
        if lab[grp[0]] < 0:
            continue
        acc = grp[zr[grp] > er[grp]]
        if acc.size * DX * DX / 1e6 < MIN_ACCUM_KM2:
            continue
        need = int(acc.size / AAR)
        zs = np.sort(zr[grp])[::-1]
        if need >= zs.size:
            zt = zs[-1]
        else:
            zt = zs[need - 1]
        members = grp[zr[grp] >= zt]
        ice[members] = True
        terminus[members] = zt
        n_glaciers += 1
    return ice.reshape(Hn, Wn), terminus.reshape(Hn, Wn), n_glaciers, rec, od


ice_lgm, term_lgm, n_glac_lgm, rec_g, od_g = glacier_extent(z, ela_lgm)

# ---------------- 3. glacial landforms ----------------
ice_area_up = accumulate(od_g, rec_g, (ice_lgm.ravel() * DX * DX / 1e6)).reshape(Hn, Wn)   # km2 of ice upstream
axis = ice_lgm & (ice_area_up >= 2.0)
z_pre_glacial = z.copy()
trough_hw = np.zeros_like(z)
if axis.any():
    aj, ai = np.nonzero(axis)
    a_area = ice_area_up[aj, ai]
    a_half = 400.0 * a_area ** 0.35                                 # trough half-width (m): ~0.5 km for 2 km2 of ice, ~3 km for 300 km2
    a_depth = np.minimum(0.4 * 2 * a_half, 700.0)                  # trough depth below its shoulders
    # over-deepening: strongest in the middle of the glacier, none at the terminus lip
    zt = term_lgm[aj, ai]; ze = ela_lgm[aj, ai]
    frac = np.clip((z[aj, ai] - zt) / np.maximum(ze - zt, 1.0), 0, 1)
    a_over = 30.0 * a_area ** 0.4 * np.sin(np.pi * np.clip(frac, 0, 1)) ** 0.7
    a_floor = z[aj, ai] - a_over
    trough_hw[aj, ai] = a_half
    # trough shoulders: mean pre-glacial height on a ring of radius = half-width around each axis cell
    from scipy.signal import fftconvolve
    radii = np.array([4, 7, 11, 16, 22, 30])
    ring_mean = []
    for rc in radii:
        yy, xx = np.mgrid[-rc - 1:rc + 2, -rc - 1:rc + 2]
        ker = (np.abs(np.hypot(yy, xx) - rc) < 0.75).astype(float); ker /= ker.sum()
        ring_mean.append(fftconvolve(z, ker, mode="same")[aj, ai])
    ring_mean = np.array(ring_mean)
    pick_r = np.clip(np.searchsorted(radii, a_half / DX), 0, len(radii) - 1)
    a_shoulder = ring_mean[pick_r, np.arange(aj.size)]
    a_shoulder = np.maximum(a_shoulder, a_floor + 20.0)
    tr = cKDTree(np.column_stack([X[aj, ai], Y[aj, ai]]))
    near = (ndimage.distance_transform_edt(~axis) * DX) < 3000
    qj, qi = np.nonzero(near)
    d, ix = tr.query(np.column_stack([X[qj, qi], Y[qj, qi]]))
    hw = a_half[ix]
    in_trough = d < hw
    zu = a_floor[ix] + (a_shoulder[ix] - a_floor[ix]) * (d / hw) ** 2   # parabola from the floor to the real shoulders
    cand = z[qj, qi].copy()
    cand[in_trough] = np.minimum(cand[in_trough], zu[in_trough])   # glaciers only erode: the parabola lies below the old V
    z[qj, qi] = cand
# cirques: armchair hollows at glacier heads above the ELA
heads = ice_lgm & (ice_area_up >= 0.3) & (ice_area_up < 1.5) & (z > ela_lgm)
hj, hi = np.nonzero(heads)
cirque = np.zeros_like(heads)
if hj.size:
    pick = np.random.default_rng(5).choice(hj.size, size=min(hj.size, 150), replace=False)
    ctr = cKDTree(np.column_stack([X[hj[pick], hi[pick]], Y[hj[pick], hi[pick]]]))
    near = ndimage.binary_dilation(heads, iterations=8)
    qj, qi = np.nonzero(near)
    d, ix = ctr.query(np.column_stack([X[qj, qi], Y[qj, qi]]))
    R = 700.0
    zc = z[hj[pick], hi[pick]][ix] - 15.0      # shallow lip: most cirques drain, a few hold tarns
    bowl = zc + 120.0 * (d / R) ** 2.5
    m = d < R
    newz = z[qj, qi].copy()
    newz[m] = np.minimum(newz[m], bowl[m])
    z[qj, qi] = newz
    cirque[qj[m], qi[m]] = True
# moraines: terminal arcs just outside the ice front, lateral ridges along the lower margins
margin_d = ndimage.distance_transform_edt(~ice_lgm) * DX
_, (nj, ni) = ndimage.distance_transform_edt(~ice_lgm, return_indices=True)
zt_near = term_lgm[nj, ni]
low_part = z < zt_near + 250.0
ridge = np.exp(-((margin_d - 250.0) / 150.0) ** 2) * (margin_d > 0) * low_part
moraine_h = 30.0 * ridge
z = z + moraine_h
moraine = moraine_h > 5.0

# ---------------- 4. present glaciers ----------------
ice_now, term_now, n_glac_now, _, _ = glacier_extent(z, ela_now)

# ---------------- 5. lakes and rivers today ----------------
sea = z <= 0
f_plain = priority_flood(z, sea, 0.0)
lake = (f_plain - z > 2.0) & ~sea
f, rec, dist, oa, od = route(z, sea, DX)
Qn = (accumulate(od, rec, q_cell) / 3.15576e7).reshape(Hn, Wn)
rivers = (Qn >= 2.0) & ~sea & ~lake
# where does the square's largest river go?
k0 = int(np.argmax(np.where(inside & ~lake, Qn, -1)))
k = k0; steps = 0
while rec[k] != k and steps < 100000:
    k = rec[k]; steps += 1
end_j, end_i = divmod(k, Wn)
end_is_sea = bool(sea[end_j, end_i] or end_i == Wn - 1 or end_j in (0, Hn - 1))


# ---------------- statistics ----------------
def pct(m):
    return round(float(m[inside].mean() * 100), 1)


land = ~sea
gy, gx = np.gradient(z, DX)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
mt = inside & land & (z > 1000)
stats = dict(
    resolution_m=DX, domain_km=2 * DOMAIN_HALF / 1000,
    tectonics="old orogen, isostatic uplift (no active plate boundary within ~320 km)",
    climate=dict(lgm_cooling_c=round(lgm_cool, 1), ela_now_m=round(float(ela_now[inside].mean())),
                 ela_lgm_m=round(float(ela_lgm[inside].mean())), lapse_c_per_km=LAPSE * 1000,
                 summer_temp_highest_point_c=round(float(T_summer_z[inside][np.argmax(z[inside])]), 1)),
    glaciers=dict(aar=AAR, lgm_glaciers=n_glac_lgm, lgm_ice_pct_of_square=pct(ice_lgm),
                  lgm_lowest_terminus_m=round(float(np.nanmin(term_lgm[inside & ice_lgm]))) if (inside & ice_lgm).any() else None,
                  present_glacier_systems_in_domain=n_glac_now, present_ice_km2_in_square=round(float((ice_now & inside).sum() * DX * DX / 1e6), 1),
                  troughs_axis_km=round(float((axis & inside).sum() * DX / 1000)),
                  cirque_pct=pct(cirque), moraine_pct=pct(moraine)),
    square=dict(elev_min_m=round(float(z[inside].min())), elev_max_m=round(float(z[inside].max())),
                mean_elev_m=round(float(z[inside & land].mean())),
                planet_mean_elev_m=round(float(trend[inside & land].mean())),
                planet_max_elev_m=round(float(trend[inside].max())),
                mountains_pct=pct(land & (z > 1000)), foothills_pct=pct(land & (z > 300) & (z <= 1000)),
                plain_pct=pct(land & (z <= 300)),
                lake_km2=round(float((lake & inside).sum() * DX * DX / 1e6), 1),
                lakes=int(ndimage.label(lake & inside)[1]),
                mountain_slope_median_deg=round(float(np.median(slope[mt])), 1) if mt.any() else None,
                mountain_slope_p90_deg=round(float(np.percentile(slope[mt], 90)), 1) if mt.any() else None,
                largest_river_m3s=round(float(Qn.ravel()[k0]), 1), largest_river_reaches_sea_or_edge=end_is_sea),
    erosion=dict(years=EROSION_YR, k=K_SP, m=M_SP, hill_diffusivity=D_HILL, relax=RELAX),
)
json.dump(stats, open(os.path.join(REGION_OUT, "regional_model.json"), "w"), indent=1)
np.savez_compressed(os.path.join(REGION_OUT, "regional_model.npz"),
                    x_m=xs.astype(np.float32), y_m=ys.astype(np.float32), elevation_m=z.astype(np.float32),
                    elevation_fluvial_m=z_fluvial.astype(np.float32), sea=sea, lake=lake, rivers=rivers,
                    discharge_m3s=Qn.astype(np.float32), ice_lgm=ice_lgm, ice_now=ice_now, trough_axis=axis, trough_halfwidth_m=trough_hw.astype(np.float32),
                    cirque=cirque, moraine=moraine, ela_now_m=ela_now.astype(np.float32),
                    ela_lgm_m=ela_lgm.astype(np.float32), terminus_lgm_m=term_lgm.astype(np.float32),
                    summer_temp_c=T_summer_z.astype(np.float32), winter_temp_c=(T_winter_planet + LAPSE * (trend - z)).astype(np.float32),
                    precip_mm=P.astype(np.float32))
print(json.dumps(stats, indent=1))

# ---------------- maps of the 100 km square ----------------
j0 = int(np.argmin(abs(ys - HALF_M))); j1 = int(np.argmin(abs(ys + HALF_M))) + 1
i0 = int(np.argmin(abs(xs + HALF_M))); i1 = int(np.argmin(abs(xs - HALF_M))) + 1
sl = (slice(j0, j1), slice(i0, i1))
zc = z[sl]


def shade(e):
    gy_, gx_ = np.gradient(e, DX)
    nx, ny = -gx_ * 3, gy_ * 3
    s = (nx * -0.6 + ny * 0.6 + 0.6) / np.sqrt(nx ** 2 + ny ** 2 + 1)
    return np.clip(s / 0.6, 0.25, 1.6)


def ramp(e):
    st = [(0, (95, 140, 85)), (200, (120, 155, 90)), (500, (150, 165, 100)), (900, (165, 150, 105)),
          (1300, (150, 130, 110)), (1700, (175, 170, 165)), (2100, (240, 240, 240))]
    out = np.zeros(e.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(e, [a for a, _ in st], [b[c] for _, b in st])
    return out


rgb = ramp(zc) * shade(zc)[..., None]
rgb[lake[sl]] = (80, 135, 200)
rgb[rivers[sl]] = (60, 110, 200)
rgb[ice_now[sl]] = (245, 248, 252)
rgb[sea[sl]] = (60, 105, 170)
img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(img); n = img.width
for k_ in range(1, 4):
    d.line([(k_ * n / 4, 0), (k_ * n / 4, n)], fill=(255, 255, 255), width=1)
    d.line([(0, k_ * n / 4), (n, k_ * n / 4)], fill=(255, 255, 255), width=1)
for r in range(4):
    for c in range(4):
        d.text((c * n / 4 + 6, r * n / 4 + 4), f"x{c}_y{r}", font=ImageFont.truetype(FONTB, 15), fill=(255, 255, 255),
               stroke_width=2, stroke_fill=(0, 0, 0))
img.save(os.path.join(REGION_OUT, "regional_relief.png"), optimize=True)

lf = np.full(zc.shape + (3,), 0.0)
lf[:] = (225, 222, 205)
lf[(z > 300)[sl]] = (210, 200, 175); lf[(z > 1000)[sl]] = (190, 175, 155)
lf[ice_lgm[sl]] = (200, 225, 245)
lf[cirque[sl]] = (150, 190, 230)
lf[axis[sl]] = (120, 165, 220)
lf[moraine[sl]] = (150, 110, 70)
lf[lake[sl]] = (60, 120, 200)
lf[rivers[sl]] = (40, 90, 190)
lf[ice_now[sl]] = (255, 255, 255)
lf = lf * shade(zc)[..., None] ** 0.5
Image.fromarray(np.clip(lf, 0, 255).astype(np.uint8)).save(os.path.join(REGION_OUT, "regional_landforms.png"), optimize=True)
