"""
Region step 1: regional process model at 100 m.

Scientific decisions (details and sources in ../MODEL_NOTES.md):
  1. Glacial cycles: the planet has polar ice sheets and land near the pole, so it is in an "icehouse"
     state with glacial cycles like Earth's Quaternary. At the last glacial maximum the region was ~10 C
     colder (Earth: ~6 C globally, ~14 C at high latitudes - Tierney et al. 2020), with July still
     around +14 C: too warm for glaciers. The region was ice-free but periglacial (permafrost), so it has
     no moraines or eskers; hillslopes are smoothed (diffusion) and sea level stood ~120 m lower,
     exposing the whole shelf inside the square.
  2. Holocene delta: modern marine deltas started to grow 8000-7000 years ago, when sea-level rise
     slowed (Stanley & Warne 1994). Delta age here: 7500 years.
  3. Sediment supply: the basin is high (57% above 1000 m, 10% above 4000 m under ice), so two independent
     estimates are combined: the global BQART model (Syvitski & Milliman 2007, B = 1) and the sediment
     concentration of the Mackenzie River, the Arctic river with a large mountain source area
     (127 Mt/yr in 330 km3/yr). Central value = geometric mean; the Lena River (lowland basin) is
     reported as a lower reference only.
  4. Sea ice in winter and a shallow semi-enclosed sea give weak waves: river-dominated (bird's-foot)
     delta with distributaries, levees and shallow interdistributary bays (analogues: Mississippi, Lena).
  5. Main channel width from hydraulic geometry w = a Q^0.5 (a = 5, as in the planet model),
     depth from Manning's equation for the river's slope; meander wavelength ~11 channel widths.
  6. Shoreface outside the delta follows Dean's equilibrium profile h = A x^(2/3), A = 0.1 (fine sand).
  7. Tributary valleys are carved by the same stream-power law as the planet model (K = 2.5e-8, m = 0.5)
     during 1 Myr, with hillslope diffusion.

Usage:  python regional_model.py
Outputs (../output): regional_model.npz, regional_model.json, regional_relief.png, regional_water.png
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont
from region_common import CFG, HALF_M, REGION_OUT, WORLD_OUT, sample_world, xy_to_latlon, load_world
from region_flow import accumulate, diffuse, priority_flood, route, stream_power

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
from fonts import FONT, FONTB

rng = np.random.default_rng(CFG["world_seed"] * 101 + 7)
DX = float(CFG["model_resolution_m"])

# ---------------- parameters (see MODEL_NOTES.md) ----------------
DOMAIN_X = (-60e3, 200e3)        # model domain is larger than the 100 km square (delta and boundary effects)
DOMAIN_Y = (-100e3, 100e3)
EROSION_YR, EROSION_DT = 2.6e6, 5.0e4      # Quaternary (glacial cycles)
K_SP, M_SP = 1.0e-6, 0.5         # soft sedimentary cover of a platform erodes far faster than the planet average
D_HILL = 0.005                   # m2/yr hillslope diffusivity (periglacial / temperate lowland)
SEED_RELIEF_M = 20.0             # initial roughness from which the valley network organises itself
SINUOSITY = 1.5                  # typical of large meandering lowland rivers
MEANDER_LAMBDA_W = 11.0          # meander wavelength ~ 11 channel widths (empirical rule)
RIVER_SLOPE = 2.5e-5             # water-surface slope of a large lowland river
MANNING_N = 0.030                # sand-bed lowland river
WIDTH_A = 5.0                    # w = a Q^0.5
FLOODPLAIN_HALF_M = 7000.0
TERRACE_M = []                   # valley sides come from erosion, not drawn by hand
DELTA_AGE_YR = 7500.0
DELTA_RETENTION = 0.7            # Lena: less than 30% of the load reaches the open sea
BULK_DENSITY = 1600.0            # kg/m3, unconsolidated deltaic sediment
BQART_OMEGA = 0.02               # kg/s
LENA_LOAD_KGS = 680.0 + 170.0    # Lena River suspended + bedload (Fedorova et al. 2015) - lowland reference
LENA_Q_M3S = 16800.0
MACKENZIE_CONC_KG_M3 = 127e9 / 330e9   # Mackenzie: 127 Mt/yr in 330 km3/yr of water (Arctic journal)
SEDIMENT_CASE = os.environ.get("SEDIMENT_CASE", "central")   # central | low (Mackenzie) | high (BQART)
DEAN_A, CLOSURE_M = 0.10, 8.0
LGM_COOLING_GLOBAL, LGM_COOLING_POLAR = 6.0, 14.0

os.makedirs(REGION_OUT, exist_ok=True)
wd = load_world()
river = json.load(open(os.path.join(REGION_OUT, "river_coarse.json")))

# ---------------- grid ----------------
xs = np.arange(DOMAIN_X[0] + DX / 2, DOMAIN_X[1], DX)
ys = np.arange(DOMAIN_Y[1] - DX / 2, DOMAIN_Y[0], -DX)
X, Y = np.meshgrid(xs, ys)
Hn, Wn = X.shape
LAT, LON = xy_to_latlon(X, Y)


def fbm2(seed, octaves, base_km, amp):
    r = np.random.default_rng(seed)
    out = np.zeros_like(X)
    norm = 0
    for o in range(octaves):
        k = 2 * math.pi / (base_km * 1000 / 2 ** o)
        a = 0.55 ** o
        for _ in range(8):
            th = r.uniform(0, math.pi)
            out += a * np.sin(k * (X * math.cos(th) + Y * math.sin(th)) + r.uniform(0, 2 * math.pi))
        norm += a * math.sqrt(8 / 2)
    return out / norm * amp


# ---------------- planet-scale trend ----------------
trend = sample_world(wd["hydro"]["elevation_eroded_m"], LAT, LON, 3)
trend = ndimage.gaussian_filter(trend, 30)                 # remove planet-grid artefacts (sigma 3 km)
runoff_m = sample_world(wd["hydro"]["runoff_mm"], LAT, LON, 1) / 1000.0
Tjan = sample_world(wd["climate"]["temp_jan_c"], LAT, LON, 1)
Tjul = sample_world(wd["climate"]["temp_jul_c"], LAT, LON, 1)
sea0 = trend <= 0

# ---------------- main river centreline ----------------
pts = np.array([[p["x_m"], p["y_m"]] for p in river["points"]] + [[river["sea_point"]["x_m"], river["sea_point"]["y_m"]]], float)
mouth_xy = np.array(CFG.get("mouth_xy_m", [pts[-2][0], pts[-2][1]]), float)
mouth_xy = pts[-2].copy()
for _ in range(5):                                          # Chaikin smoothing
    q = 0.75 * pts[:-1] + 0.25 * pts[1:]
    r_ = 0.25 * pts[:-1] + 0.75 * pts[1:]
    pts = np.vstack([pts[:1], np.column_stack([q, r_]).reshape(-1, 2), pts[-1:]])
seg = np.diff(pts, axis=0)
cum = np.r_[0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
s_line = np.arange(0, cum[-1], 50.0)
cl = np.column_stack([np.interp(s_line, cum, pts[:, 0]), np.interp(s_line, cum, pts[:, 1])])
k_mouth = int(np.argmin(np.hypot(cl[:, 0] - mouth_xy[0], cl[:, 1] - mouth_xy[1])))
valley = cl[:k_mouth + 1]                                    # upstream ... mouth
s_valley = s_line[:k_mouth + 1]
seaward = cl[min(k_mouth + 40, len(cl) - 1)] - cl[k_mouth]
seaward /= np.linalg.norm(seaward)
# the smoothed coast may lie further seaward than the planet's mouth cell: extend the valley to it
ext = []
p = valley[-1].copy()
for _ in range(600):
    p = p + 100.0 * seaward
    jj = int((DOMAIN_Y[1] - p[1]) / DX); ii = int((p[0] - DOMAIN_X[0]) / DX)
    if not (0 <= jj < Hn and 0 <= ii < Wn) or trend[jj, ii] <= 0:
        break
    ext.append(p.copy())
if ext:
    valley = np.vstack([valley, np.array(ext)])
    s_valley = np.r_[s_valley, s_valley[-1] + 100.0 * np.arange(1, len(ext) + 1)]

tree_v = cKDTree(valley)
d_val, i_val = tree_v.query(np.column_stack([X.ravel(), Y.ravel()]))
d_val = d_val.reshape(Hn, Wn); i_val = i_val.reshape(Hn, Wn)
dist_to_mouth_along = (s_valley[-1] - s_valley[i_val])          # m upstream of the mouth
water_level = RIVER_SLOPE * dist_to_mouth_along

# ---------------- 1. lowstand landscape + valley + erosion ----------------
z = trend.copy()
z = np.where(sea0, z, np.maximum(z, 2.0) + fbm2(11, 5, 14, SEED_RELIEF_M) + SEED_RELIEF_M)
seaward_proj = (X - valley[-1][0]) * seaward[0] + (Y - valley[-1][1]) * seaward[1]
landward = (i_val < len(valley) - 1) | (seaward_proj <= 0)
upstream_side = landward | (d_val > 2 * FLOODPLAIN_HALF_M)
fp_half = FLOODPLAIN_HALF_M * (0.75 + 0.25 * fbm2(41, 3, 30, 1.0)) + 900.0 * fbm2(43, 3, 4, 1.0)   # width varies along the valley
floodplain = (d_val <= fp_half) & landward & ~sea0
fp_level = water_level + 4.0
z = np.where(floodplain, fp_level, z)
for a, b, hgt in TERRACE_M:
    band = (d_val > a) & (d_val <= b) & landward & ~sea0
    z = np.where(band, np.minimum(z, fp_level + hgt) if hgt > 20 else np.maximum(np.minimum(z, fp_level + hgt), fp_level + hgt * 0.8), z)

fixed = sea0 | floodplain
q_cell = (np.clip(runoff_m, 0, None) * DX * DX).ravel()
zf = z.ravel().copy()
for step in range(int(EROSION_YR / EROSION_DT)):
    f, rec, dist, oa, od = route(zf.reshape(Hn, Wn), fixed, DX)
    Q = accumulate(od, rec, q_cell)
    zf = stream_power(zf, oa, rec, dist, Q, K_SP, M_SP, EROSION_DT, fixed.ravel())
    zf = diffuse(zf.reshape(Hn, Wn), D_HILL, EROSION_DT, DX, fixed, 1).ravel()
z = zf.reshape(Hn, Wn)
_ff = priority_flood(z, fixed, 1e-3)
z = np.where(~fixed, _ff, z)                    # humid climate: upland hollows overflow or silt up
z_lowland = z.copy()

# ---------------- 2. main channel (meandering) ----------------
Q_RIVER = float(river["points"][-1]["discharge_m3s"])
width = WIDTH_A * Q_RIVER ** 0.5
# Manning: Q = w * d * (1/n) d^(2/3) S^(1/2)  ->  d^(5/3) = Q n / (w S^0.5)
depth = (Q_RIVER * MANNING_N / (width * RIVER_SLOPE ** 0.5)) ** 0.6
velocity = (1 / MANNING_N) * depth ** (2 / 3) * RIVER_SLOPE ** 0.5
wavelength = 11.0 * width
t = np.gradient(valley, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True)
nrm = np.column_stack([-t[:, 1], t[:, 0]])
L_valley = s_valley[-1] - s_valley[0]


def sine_generated(phase0, seed):
    """Langbein & Leopold (1966) sine-generated curve: direction angle = omega * sin(2 pi s / M)."""
    r = np.random.default_rng(seed)
    omega = 2.2 * math.sqrt((SINUOSITY - 1) / SINUOSITY)        # max deflection angle (rad)
    M = wavelength * SINUOSITY                                    # arc length of one meander
    u, v, s_arc, th_noise = 0.0, 0.0, 0.0, 0.0
    U, V = [0.0], [0.0]
    while u < L_valley:
        taper_ = min(1.0, (L_valley - u) / 8000.0)
        th_noise = 0.97 * th_noise + r.normal(0, 0.05)
        th = taper_ * (omega * math.sin(2 * math.pi * s_arc / M * (1 + 0.15 * math.sin(s_arc / 9000 + seed)) + phase0)
                       + th_noise) - 2e-4 * v                    # weak pull back towards the valley axis
        u += 50.0 * math.cos(th); v += 50.0 * math.sin(th); s_arc += 50.0
        v = float(np.clip(v, -0.8 * FLOODPLAIN_HALF_M, 0.8 * FLOODPLAIN_HALF_M))
        U.append(u); V.append(v)
    U = np.clip(np.array(U), 0, L_valley); V = np.array(V)
    base = np.column_stack([np.interp(U, s_valley - s_valley[0], valley[:, 0]),
                            np.interp(U, s_valley - s_valley[0], valley[:, 1])])
    nn = np.column_stack([np.interp(U, s_valley - s_valley[0], nrm[:, 0]), np.interp(U, s_valley - s_valley[0], nrm[:, 1])])
    return base + nn * V[:, None], U


channel_line, ch_u = sine_generated(0.0, 3)
old_line, _ = sine_generated(2.1, 17)               # an earlier course: its abandoned loops become oxbow lakes
tree_c = cKDTree(channel_line)
d_ch, i_ch = tree_c.query(np.column_stack([X.ravel(), Y.ravel()]))
d_ch = d_ch.reshape(Hn, Wn)
wl_ch = RIVER_SLOPE * (L_valley - ch_u[i_ch.reshape(Hn, Wn)])
in_ch = (d_ch <= width / 2) & ~sea0
bed = wl_ch - depth * (1 - (d_ch / (width / 2)) ** 2)
z = np.where(in_ch, np.minimum(z, bed), z)
main_channel = in_ch
# natural levees and point-bar scroll relief on the floodplain
lev = 1.5 * np.exp(-np.clip(d_ch - width / 2, 0, None) / 400.0)
z = np.where(floodplain & ~in_ch, fp_level - 2.5 + lev + 1.2 * fbm2(23, 3, 3, 1.0), z)
d_old = cKDTree(old_line).query(np.column_stack([X.ravel(), Y.ravel()]))[0].reshape(Hn, Wn)
ox = floodplain & (d_old <= width / 2) & (d_ch > 2.5 * width)
ox_lbl, n_ox = ndimage.label(ox)
if n_ox:
    sizes = ndimage.sum(ox, ox_lbl, range(1, n_ox + 1))
    keep = np.argsort(-sizes)[:8] + 1
    oxbow = np.isin(ox_lbl, keep)
    z = np.where(oxbow, fp_level - 2.5 - 4.0, z)        # cut-off loops, partly filled
else:
    oxbow = np.zeros_like(ox)

# ---------------- 3. sediment budget (BQART) ----------------
basin_area_km2 = float(wd["hydro"]["upstream_area_km2"][128, 884])
hz = wd["hydro"]["elevation_eroded_m"]; bas = wd["hydro"]["basin"]
bmask = (bas == bas[128, 884]) & wd["height"]["land"]
H_, W_ = hz.shape
latw = np.cos(np.radians(90 - (np.arange(H_) + 0.5) / H_ * 180))[:, None] * np.ones((1, W_))
basin_T = float((wd["climate"]["temp_annual_c"] * latw)[bmask].sum() / latw[bmask].sum())
basin_relief_km = float(hz[bmask].max()) / 1000.0
B = 1.0
if basin_T >= 2:
    qs_kgs = BQART_OMEGA * B * Q_RIVER ** 0.31 * basin_area_km2 ** 0.5 * basin_relief_km * basin_T
else:
    qs_kgs = 2 * BQART_OMEGA * B * Q_RIVER ** 0.31 * basin_area_km2 ** 0.5 * basin_relief_km
bqart_kgs = qs_kgs
mack_kgs = MACKENZIE_CONC_KG_M3 * Q_RIVER
lena_kgs = LENA_LOAD_KGS * (Q_RIVER / LENA_Q_M3S) ** 0.31
qs_kgs = {"central": math.sqrt(bqart_kgs * mack_kgs), "low": mack_kgs, "high": bqart_kgs}[SEDIMENT_CASE]
to_mt = lambda v: v * 3.15576e7 / 1e9
qs_mt_yr = to_mt(qs_kgs)
V_target = qs_kgs * 3.15576e7 * DELTA_AGE_YR * DELTA_RETENTION / BULK_DENSITY     # m3

# ---------------- 4. Holocene delta (mass-balanced progradation) ----------------
# The delta plain advances into the sea until the deposited volume equals the sediment budget:
# a topset (delta plain, +3 m at the apex to +0.4 m at the shore) and a foreset slope down to the old sea floor.
# River-dominated, so the plain is elongated along the river axis and cut by a branching distributary network.
pre = z.copy()                       # transgressed surface before the delta (sea floor = planet trend)
apex = channel_line[-1]
base_ang = math.atan2(seaward[1], seaward[0])
DELTA_ELONGATION = 1.5               # river-dominated: longer along the river axis than across it
TOPSET_APEX_M, TOPSET_SHORE_M = 3.0, 0.4
FORESET_GRADIENT = 0.006             # ~0.3 degrees, muddy delta front
U = (X - apex[0]) * seaward[0] + (Y - apex[1]) * seaward[1]
V = -(X - apex[0]) * seaward[1] + (Y - apex[1]) * seaward[0]
Dn = np.sqrt((np.clip(U, 0, None) / DELTA_ELONGATION) ** 2 + V ** 2) * (1 + 0.16 * fbm2(51, 4, 40, 1.0))
Dn = Dn + np.where(U < 0, -U * 4.0, 0.0)             # little growth behind the apex
can_fill = (pre <= TOPSET_APEX_M) & (U > -3000)


def delta_surface(R):
    t = np.clip(Dn / R, 0, 1)
    top = TOPSET_APEX_M * (1 - t) + TOPSET_SHORE_M * t
    front = -2.0 - FORESET_GRADIENT * (Dn - R)
    surf = np.where(Dn <= R, top, front)
    new = np.where(can_fill, np.maximum(pre, surf), pre)
    return new, float(np.clip(new - pre, 0, None).sum() * DX * DX)


lo, hi = 1000.0, 300000.0
for _ in range(30):                                  # bisection: delta volume = sediment budget
    mid = 0.5 * (lo + hi)
    if delta_surface(mid)[1] < V_target:
        lo = mid
    else:
        hi = mid
R_delta = 0.5 * (lo + hi)
z, V_built = delta_surface(R_delta)
delta_land = (Dn <= R_delta) & can_fill & (z > 0)

# distributary network: a branching tree that fans out from the apex to the delta shore
r_ = np.random.default_rng(4242)
net = []
stack = [(apex.copy(), base_ang, 0)]
while stack:
    p0, ang, g = stack.pop()
    seg_len = 9000.0 * 0.8 ** g
    line = [p0]; a = ang; reached = False
    for k in range(int(4 * R_delta / 100)):
        pnew = line[-1] + 100.0 * np.array([math.cos(a), math.sin(a)])
        line.append(pnew)
        jj = int((DOMAIN_Y[1] - pnew[1]) / DX); ii = int((pnew[0] - DOMAIN_X[0]) / DX)
        if not (0 <= jj < Hn and 0 <= ii < Wn) or Dn[jj, ii] > R_delta:
            reached = True
            break
        radial = math.atan2(pnew[1] - apex[1], pnew[0] - apex[0])
        a += 0.04 * math.sin(radial - a) + r_.normal(0, 0.02)     # fan out radially, with wiggle
        if g < 4 and len(line) * 100.0 >= seg_len:
            break
    line = np.array(line)
    net.append((line, g, reached))
    if not reached and g < 4:
        spread = r_.uniform(0.28, 0.5)
        stack.append((line[-1], a + spread, g + 1))
        stack.append((line[-1], a - spread * r_.uniform(0.6, 1.0), g + 1))
allp = np.vstack([l for l, g, _ in net]); gen = np.concatenate([[g] * len(l) for l, g, _ in net])
dch, ixc = cKDTree(allp).query(np.column_stack([X.ravel(), Y.ravel()]), distance_upper_bound=20000)
dch = dch.reshape(Hn, Wn); gch = gen[np.clip(ixc, 0, len(allp) - 1)].reshape(Hn, Wn)
w_g = width / 2 ** (gch / 2)
d_g = np.maximum(depth * 0.85 ** gch, 3.0)
plain = (Dn <= R_delta) & can_fill
z = np.where(plain, z + 0.9 * np.exp(-np.clip(dch - w_g / 2, 0, None) / 500.0), z)       # natural levees
micro = fbm2(53, 4, 3, 1.0)
z = np.where(plain & (dch > w_g), z + 0.5 * micro, z)                                      # marsh micro-relief
delta_lakes = plain & (dch > 2 * w_g) & (micro < -0.42)
z = np.where(delta_lakes, -0.8, z)                                                          # thaw / floodplain lakes
dist_ch = (dch <= w_g / 2) & ((Dn <= R_delta * 1.02) | (pre <= 0)) & (U > -3000)
z = np.where(dist_ch, np.minimum(z, 0.5 - d_g * (1 - (dch / (w_g / 2)) ** 2)), z)
V_built = float(np.clip(z - pre, 0, None).sum() * DX * DX)
delta_land = plain & (z > 0)
shore_advance_km = float(U[delta_land].max() / 1000.0) if delta_land.any() else 0.0

# ---------------- 5. shoreface (Dean profile) outside the delta ----------------
land_now = z > 0
cdist = np.where(land_now, ndimage.distance_transform_edt(land_now), ndimage.distance_transform_edt(~land_now)) * DX
z = np.where(upstream_side & ~floodplain, z + 5.0 * fbm2(31, 4, 9, 1.0) * np.exp(-cdist / 3000.0), z)
land_now = z > 0
coast_d = ndimage.distance_transform_edt(~land_now) * DX
delta_zone = ndimage.binary_dilation(delta_land, iterations=int(9000 / DX))
dean = -np.minimum(DEAN_A * coast_d ** (2 / 3), CLOSURE_M)
shore = sea0 & ~land_now & ~delta_zone & (coast_d < 6000) & ~main_channel & ~dist_ch   # the sea, not river channels
z = np.where(shore, np.minimum(np.maximum(dean, z - 0.0), np.where(z > dean, dean, z)), z)
beach = land_now & ~delta_zone & (ndimage.distance_transform_edt(land_now) * DX <= 200)
z = np.where(beach, np.clip(z, 0.6, 3.0), z)

# ---------------- 6. lakes and rivers ----------------
sea = z <= 0
sea_lbl, n_lbl = ndimage.label(sea & ~main_channel & ~dist_ch)     # river channels are not sea
edge_lbls = set(np.unique(np.r_[sea_lbl[0], sea_lbl[-1], sea_lbl[:, 0], sea_lbl[:, -1]])) - {0}
open_sea = np.isin(sea_lbl, list(edge_lbls))
water_fixed = open_sea | main_channel | dist_ch
f_plain = priority_flood(z, water_fixed, 0.0)
lake = (f_plain - z > 1.0) & ~water_fixed
f, rec, dist, oa, od = route(z, water_fixed, DX)
inflow = np.zeros(Hn * Wn)
q_loc = (np.clip(runoff_m, 0, None) * DX * DX).ravel()
Qn = accumulate(od, rec, q_loc) / 3.15576e7
rivers = (Qn.reshape(Hn, Wn) >= 5.0) & ~sea & ~lake

# ---------------- statistics ----------------
inside = (np.abs(X) <= HALF_M) & (np.abs(Y) <= HALF_M)
lgm_cool = LGM_COOLING_GLOBAL + (LGM_COOLING_POLAR - LGM_COOLING_GLOBAL) * (abs(CFG["centre_lat_deg"]) - 30) / 60
lgm_july = float(Tjul[inside].mean() - lgm_cool)
lgm_maat = float(((Tjan + Tjul) / 2)[inside].mean() - lgm_cool)
stats = dict(
    domain_km=[(DOMAIN_X[1] - DOMAIN_X[0]) / 1000, (DOMAIN_Y[1] - DOMAIN_Y[0]) / 1000], resolution_m=DX,
    lgm=dict(cooling_c=round(lgm_cool, 1), july_c=round(lgm_july, 1), mean_annual_c=round(lgm_maat, 1),
             glaciated=lgm_july < 0.0, permafrost=lgm_maat < -1.0),
    sediment=dict(basin_area_km2=round(basin_area_km2), basin_mean_temp_c=round(basin_T, 1),
                  basin_relief_km=round(basin_relief_km, 2), bqart_form="T < 2 C" if basin_T < 2 else "T >= 2 C",
                  case=SEDIMENT_CASE, load_mt_yr=round(qs_mt_yr, 1),
                  bqart_b1_mt_yr=round(to_mt(bqart_kgs), 1), mackenzie_concentration_mt_yr=round(to_mt(mack_kgs), 1),
                  lena_lowland_reference_mt_yr=round(to_mt(lena_kgs), 1), delta_age_yr=DELTA_AGE_YR, retention=DELTA_RETENTION,
                  target_volume_km3=round(V_target / 1e9, 2), built_volume_km3=round(V_built / 1e9, 2)),
    channel=dict(discharge_m3s=round(Q_RIVER), width_m=round(width), depth_m=round(depth, 1),
                 velocity_ms=round(velocity, 2), slope=RIVER_SLOPE, manning_n=MANNING_N,
                 capacity_m3s=round(width * depth * velocity), meander_wavelength_m=round(wavelength),
                 sinuosity=round(float(np.sum(np.hypot(*np.diff(channel_line, axis=0).T)) /
                                       np.sum(np.hypot(*np.diff(valley, axis=0).T))), 2)),
    delta=dict(distributary_mouths=int(sum(1 for _, g, reached in net if reached)),
               radius_km=round(R_delta / 1000, 1), shoreline_advance_km=round(shore_advance_km, 1),
               delta_plain_km2=round(float(delta_land.sum() * DX * DX / 1e6)),
               delta_land_km2_in_square=round(float((delta_land & inside & (z > 0)).sum() * DX * DX / 1e6)),
               delta_land_km2_domain=round(float((delta_land & (z > 0)).sum() * DX * DX / 1e6))),
    square=dict(land_pct=round(float((~sea & inside).sum() / inside.sum() * 100), 1),
                lake_km2=round(float((lake & inside).sum() * DX * DX / 1e6)),
                elev_min_m=round(float(z[inside].min()), 1), elev_max_m=round(float(z[inside].max()), 1),
                mean_land_elev_m=round(float(z[inside & ~sea].mean()), 1),
                planet_mean_land_elev_m=round(float(trend[inside & (trend > 0)].mean()), 1),
                river_km_per_km2=round(float((rivers & inside).sum() * DX / 1000 / ((inside & ~sea).sum() * DX * DX / 1e6)), 3)),
    erosion=dict(years=EROSION_YR, k=K_SP, m=M_SP, hill_diffusivity_m2_yr=D_HILL),
)
json.dump(stats, open(os.path.join(REGION_OUT, "regional_model.json"), "w"), indent=1)
np.savez_compressed(os.path.join(REGION_OUT, "regional_model.npz"),
                    x_m=xs.astype(np.float32), y_m=ys.astype(np.float32), elevation_m=z.astype(np.float32),
                    pre_delta_m=pre.astype(np.float32), sea=sea, open_sea=open_sea, lake=lake,
                    main_channel=main_channel, distributaries=dist_ch, delta_land=delta_land,
                    floodplain=floodplain, rivers=rivers, discharge_m3s=Qn.reshape(Hn, Wn).astype(np.float32),
                    shoreface=shore, beach=beach)
print(json.dumps(stats, indent=1))

# ---------------- maps of the 100 km square ----------------
j0 = int(np.argmin(abs(ys - HALF_M))); j1 = int(np.argmin(abs(ys + HALF_M))) + 1
i0 = int(np.argmin(abs(xs + HALF_M))); i1 = int(np.argmin(abs(xs - HALF_M))) + 1
zc = z[j0:j1, i0:i1]
sl = (slice(j0, j1), slice(i0, i1))


def shade(e):
    gx = np.gradient(e, axis=1) / DX; gy = np.gradient(e, axis=0) / DX
    nx, ny = -gx * 12, gy * 12
    s = (nx * -0.6 + ny * 0.6 + 0.6) / np.sqrt(nx ** 2 + ny ** 2 + 1)
    return np.clip(s / 0.6, 0.35, 1.5)


def ramp(e):
    sea_st = [(-60, (20, 55, 110)), (-20, (40, 95, 155)), (-5, (80, 140, 190)), (0, (130, 185, 215))]
    land_st = [(0, (120, 150, 95)), (5, (100, 140, 85)), (30, (90, 130, 75)), (80, (150, 155, 100)), (140, (175, 150, 110))]
    out = np.zeros(e.shape + (3,))
    for st, m in ((sea_st, e <= 0), (land_st, e > 0)):
        xs_ = [a for a, _ in st]
        for c in range(3):
            out[..., c] = np.where(m, np.interp(e, xs_, [b[c] for _, b in st]), out[..., c])
    return out


rgb = ramp(zc) * np.where(zc > 0, shade(zc), 1.0)[..., None]
img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(img)
n = img.width
for k in range(1, 4):
    d.line([(k * n / 4, 0), (k * n / 4, n)], fill=(255, 255, 255), width=1)
    d.line([(0, k * n / 4), (n, k * n / 4)], fill=(255, 255, 255), width=1)
for r in range(4):
    for c in range(4):
        d.text((c * n / 4 + 6, r * n / 4 + 4), f"x{c}_y{r}", font=ImageFont.truetype(FONTB, 15), fill=(255, 255, 255),
               stroke_width=2, stroke_fill=(0, 0, 0))
img.save(os.path.join(REGION_OUT, "regional_relief.png"), optimize=True)

wat = np.full(zc.shape + (3,), 236.0)
wat[(z > 0)[sl]] = (226, 222, 205)
wat[floodplain[sl] & (z > 0)[sl]] = (205, 220, 190)
wat[delta_land[sl] & (z > 0)[sl]] = (190, 215, 185)
wat[sea[sl]] = (150, 190, 225)
wat[(sea & (z < -10))[sl]] = (110, 160, 210)
wat[lake[sl]] = (95, 150, 210)
wat[rivers[sl]] = (60, 110, 200)
wat[(main_channel | dist_ch)[sl]] = (30, 80, 180)
wimg = Image.fromarray(wat.astype(np.uint8))
dw = ImageDraw.Draw(wimg)
for k in range(1, 4):
    dw.line([(k * n / 4, 0), (k * n / 4, n)], fill=(120, 120, 120), width=1)
    dw.line([(0, k * n / 4), (n, k * n / 4)], fill=(120, 120, 120), width=1)
wimg.save(os.path.join(REGION_OUT, "regional_water.png"), optimize=True)
