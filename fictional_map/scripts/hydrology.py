"""
Step 5 of the world pipeline: runoff, fluvial erosion, rivers, lakes and drainage basins.

Physics used:
  * Potential evapotranspiration: Hargreaves-Samani (1985, FAO-56) from 12 monthly temperatures and solar geometry
    (sinusoid through the modelled January / July temperatures).
  * Actual evapotranspiration and runoff: Budyko curve in Fu's form (Fu 1981), w = 2.6.
  * Flow routing: priority-flood depression filling (Barnes et al. 2014) + D8 steepest descent
    on a sphere (true cell distances, longitude wraps around).
  * Fluvial erosion: stream-power law E = K Q^m S^n with m = 0.5, n = 1, solved implicitly
    (Braun & Willett 2013). Runs for EROSION_MYR million years without tectonic uplift.
  * Lakes: every closed depression is filled from its lowest point until lake evaporation (PET - P)
    balances the inflow. If the inflow is larger than the evaporation of the full lake, the lake
    overflows and drains to the sea; otherwise the basin is endorheic (closed, salt lake).

Inputs : world_height.npz, world_climate.npz, world_plates.json
Outputs: rivers_map.png, basins_map.png, world_hydrology.npz, world_hydrology.json
         (world_height.npz keeps the pre-erosion relief; eroded terrain is in world_hydrology.npz)
"""
import heapq, json, math, os
import numpy as np
from numba import njit
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
HD = np.load(f"{OUT}/world_height.npz")
CD = np.load(f"{OUT}/world_climate.npz")
META = json.load(open(f"{OUT}/world_plates.json"))
z0 = HD["elevation_m"].astype(np.float64)
land = HD["land"]
H, W = z0.shape
R_M = META["radius_km"] * 1000.0

EROSION_MYR = 5.0
DT_YR = 1.0e5
K_SP = 2.5e-8           # stream-power erodibility for Q in m3/yr, m = 0.5, n = 1
M_SP = 0.5
FU_W = 2.6              # Budyko-Fu catchment parameter (typical global value)
RIVER_Q_M3S = 150.0     # discharge from which a river is drawn on the map
CHANNEL_AREA_KM2 = 20000.0   # channel initiation for network statistics (Strahler, Hack)
MICRO_RELIEF_M = 40.0
HILLS_RELIEF_M = 160.0       # amplitude of 100-500 km hills added to land before erosion
MIN_CLOSED_BASIN_KM2 = 15000.0   # dry hollows smaller than this are treated as sub-grid noise and filled        # sub-grid roughness of plains used for flow routing (real plains are never perfectly smooth)
CHANNEL_WIDTH_A = 5.0        # hydraulic geometry: channel width ~ a * Q^0.5 (m, Q in m3/s), Leopold & Maddock 1953
FLOODPLAIN_X = 30.0          # wetted floodplain / infiltration zone relative to the channel width (losses in dry lands)

jj, ii = np.mgrid[0:H, 0:W]
LATd = 90 - (jj + 0.5) / H * 180
LAT = np.radians(LATd)
dx_m = 2 * np.pi * R_M / W * np.maximum(np.cos(LAT[:, 0]), 1e-3)   # per row, E-W spacing
dy_m = np.pi * R_M / H
cell_area = (dx_m * dy_m)[:, None] * np.ones((1, W))                # m2

# ---------- 1. runoff: Hargreaves PET + Budyko-Fu ----------
Tjan, Tjul = CD["temp_jan_c"].astype(float), CD["temp_jul_c"].astype(float)
P = CD["precip_annual_mm"].astype(float)
Tm = (Tjan + Tjul) / 2
amp = (Tjul - Tjan) / 2
months = [Tm + amp * math.cos(2 * math.pi * (m - 6.5) / 12) for m in range(12)]   # m=0 Jan ... m=6 Jul
# Hargreaves-Samani (1985) reference evapotranspiration, as recommended by FAO-56 when only
# temperature data exist: ET0 = 0.0023 * Ra * (T + 17.8) * sqrt(Tmax - Tmin)
# Ra = extraterrestrial radiation from latitude and day of year (FAO-56 eq. 21-25).
# Diurnal temperature range is not modelled directly: it is larger under dry, clear skies, so it is
# estimated from annual precipitation (8 C in humid climates up to ~16 C in deserts).
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DTR = 8.0 + 8.0 * np.exp(-P / 500.0)
PET = np.zeros_like(P)
doy = 0
for mth, t in enumerate(months):
    J = doy + MONTH_DAYS[mth] / 2
    doy += MONTH_DAYS[mth]
    decl = 0.409 * math.sin(2 * math.pi * J / 365 - 1.39)
    dr = 1 + 0.033 * math.cos(2 * math.pi * J / 365)
    ws = np.arccos(np.clip(-np.tan(LAT) * math.tan(decl), -1, 1))
    Ra = (24 * 60 / math.pi) * 0.0820 * dr * (ws * np.sin(LAT) * math.sin(decl) + np.cos(LAT) * math.cos(decl) * np.sin(ws))
    Ra_mm = 0.408 * np.clip(Ra, 0, None)                                  # MJ m-2 day-1 -> mm day-1
    et0 = 0.0023 * Ra_mm * np.clip(t + 17.8, 0, None) * np.sqrt(DTR)
    et0 = np.where(t > -5, et0, 0.0)                                      # frozen months: negligible
    PET += et0 * MONTH_DAYS[mth]
phi = PET / np.maximum(P, 1e-6)
ET = P * (1 + phi - (1 + phi ** FU_W) ** (1 / FU_W))
ET = np.clip(ET, 0, P)
runoff_mm = np.where(land, P - ET, 0.0)


# ---------- numba kernels ----------
DI = np.array([1, 1, 0, -1, -1, -1, 0, 1])
DJ = np.array([0, -1, -1, -1, 0, 1, 1, 1])


@njit(cache=True)
def nb_dist(j, di, dj, dx_m, dy_m):
    if dj == 0:
        return dx_m[j]
    if di == 0:
        return dy_m
    jm = j + dj
    return math.sqrt((0.5 * (dx_m[j] + dx_m[jm])) ** 2 + dy_m ** 2)


@njit(cache=True)
def priority_flood(z, is_sink, eps):
    """Fill depressions; sinks (ocean, endorheic lakes) are seeds. Returns filled surface."""

    H, W = z.shape
    f = z.copy()
    done = np.zeros((H, W), np.bool_)
    heap = [(0.0, 0)]
    heap.pop()
    for j in range(H):
        for i in range(W):
            if is_sink[j, i]:
                done[j, i] = True
                heapq.heappush(heap, (f[j, i], j * W + i))
    while len(heap) > 0:
        h, k = heapq.heappop(heap)
        j = k // W; i = k % W
        for d in range(8):
            jn = j + DJ[d]
            if jn < 0 or jn >= H:
                continue
            inn = (i + DI[d]) % W
            if done[jn, inn]:
                continue
            done[jn, inn] = True
            if f[jn, inn] <= f[j, i] + eps:
                f[jn, inn] = f[j, i] + eps
            heapq.heappush(heap, (f[jn, inn], jn * W + inn))
    return f


@njit(cache=True)
def receivers(f, is_sink, dx_m, dy_m):
    H, W = f.shape
    rec = np.empty(H * W, np.int64)
    dist = np.zeros(H * W)
    for j in range(H):
        for i in range(W):
            k = j * W + i
            rec[k] = k
            if is_sink[j, i]:
                continue
            best = 0.0
            for d in range(8):
                jn = j + DJ[d]
                if jn < 0 or jn >= H:
                    continue
                inn = (i + DI[d]) % W
                L = nb_dist(j, DI[d], DJ[d], dx_m, dy_m)
                s = (f[j, i] - f[jn, inn]) / L
                if s > best:
                    best = s; rec[k] = jn * W + inn; dist[k] = L
    return rec, dist


@njit(cache=True)
def accumulate(order_desc, rec, w):
    acc = w.copy()
    for k in order_desc:
        r = rec[k]
        if r != k:
            acc[r] += acc[k]
    return acc


@njit(cache=True)
def accumulate_losses(order_desc, rec, dist, w, e_net, a_w, fx):
    """Accumulate discharge (m3/yr); rivers lose water to evaporation where PET > P."""
    acc = w.copy()
    for k in order_desc:
        q = acc[k]
        if e_net[k] > 0 and q > 0:
            width = a_w * math.sqrt(q / 3.15576e7) * fx
            q = max(q - e_net[k] * width * dist[k], 0.0)
            acc[k] = q
        r = rec[k]
        if r != k:
            acc[r] += acc[k]
    return acc


@njit(cache=True)
def reaches_sea(order_asc, rec, acc, is_ocean, tiny):
    n = rec.shape[0]
    out = np.zeros(n, np.bool_)
    for k in order_asc:
        r = rec[k]
        if r == k:
            out[k] = is_ocean[k]
        else:
            out[k] = out[r] and (acc[k] > tiny or is_ocean[k])
    return out


@njit(cache=True)
def deposit_in_depressions(order_desc, rec, h_old, h_new, fill_gap, area, is_land):
    """Carry eroded sediment downstream; it settles in the first closed depression it meets."""
    n = rec.shape[0]
    sed = np.zeros(n)
    for k in order_desc:
        if is_land[k]:
            sed[k] += max(h_old[k] - h_new[k], 0.0) * area[k]
            if fill_gap[k] > 0 and sed[k] > 0:
                dz = min(fill_gap[k], sed[k] / area[k])
                h_new[k] += dz
                sed[k] -= dz * area[k]
        r = rec[k]
        if r != k:
            sed[r] += sed[k]
    return h_new


@njit(cache=True)
def implicit_stream_power(h, order_asc, rec, dist, Q, K, m, dt, erodible, floor_):
    for k in order_asc:
        r = rec[k]
        if r == k or not erodible[k]:
            continue
        F = K * dt * Q[k] ** m / dist[k]
        hn = (h[k] + F * h[r]) / (1 + F)
        if hn < h[k]:
            h[k] = max(hn, floor_[k])
    return h


@njit(cache=True)
def network_stats(order_desc, rec, dist, area_km2, channel_min_km2):
    n = rec.shape[0]
    lup = np.zeros(n)                       # longest upstream flow path length (m)
    strahler = np.zeros(n, np.int64)
    maxo = np.zeros(n, np.int64)
    cnt = np.zeros(n, np.int64)
    for k in order_desc:                    # donors before receivers
        if area_km2[k] >= channel_min_km2:
            if maxo[k] == 0:
                strahler[k] = 1
            elif cnt[k] >= 2:
                strahler[k] = maxo[k] + 1
            else:
                strahler[k] = maxo[k]
        r = rec[k]
        if r != k:
            if lup[k] + dist[k] > lup[r]:
                lup[r] = lup[k] + dist[k]
            o = strahler[k]
            if o > 0:
                if o > maxo[r]:
                    maxo[r] = o; cnt[r] = 1
                elif o == maxo[r]:
                    cnt[r] += 1
    return lup, strahler


@njit(cache=True)
def basin_labels(order_asc, rec):
    n = rec.shape[0]
    lab = np.empty(n, np.int64)
    for k in order_asc:                     # receivers before donors
        r = rec[k]
        lab[k] = k if r == k else lab[r]
    return lab


_r = np.random.default_rng(META["seed"] + 5000)
_P3 = np.stack([np.cos(LAT) * np.cos(np.radians((ii + 0.5) / W * 360)),
                np.cos(LAT) * np.sin(np.radians((ii + 0.5) / W * 360)), np.sin(LAT)], -1).reshape(-1, 3)
MICRO = np.zeros(H * W)
for o in range(4):
    dirs = _r.normal(size=(12, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    MICRO += 0.6 ** o * np.sin((450 * 1.8 ** o) * (_P3 @ dirs.T) + _r.uniform(0, 6.3, 12)).sum(1) / math.sqrt(6)
MICRO = (MICRO / np.abs(MICRO).max() * MICRO_RELIEF_M).reshape(H, W)


def route(z, sinks):
    zr = np.where(land, z + MICRO, z)
    f = priority_flood(zr, sinks, 1e-3)
    rec, dist = receivers(f, sinks, dx_m, dy_m)
    order_asc = np.argsort(f, axis=None, kind="stable")
    return f, rec, dist, order_asc, order_asc[::-1].copy()


E_net_land = (np.clip(PET - P, 0, None) / 1000.0).ravel()      # m/yr open-water/floodplain deficit

# ---------- 2. fluvial erosion ----------
ocean = ~land
# Hills and low ridges at 100-500 km scale (the global relief model has none): real lowlands carry
# ~100-300 m of relief at these scales, which is what lets rivers gather into dendritic networks.
HILLS = np.zeros(H * W)
for o in range(4):
    dirs = _r.normal(size=(14, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    HILLS += 0.65 ** o * np.sin((70 * 1.9 ** o) * (_P3 @ dirs.T) + _r.uniform(0, 6.3, 14)).sum(1) / math.sqrt(7)
HILLS = HILLS.reshape(H, W) / np.abs(HILLS).max()
coast_d = ndimage.distance_transform_edt(land) 
hill_amp = HILLS_RELIEF_M * np.clip(coast_d / 4.0, 0, 1)        # fades out towards the coast
z = np.where(land, z0 + hill_amp * (HILLS + 0.35), z0)
z = np.where(land, np.maximum(z, 1.0), z)
# Over geological time closed hollows in wet climates overflow, cut an outlet or fill with sediment;
# only in dry climates do they survive as closed basins. Fill hollows where local runoff is non-trivial.
# Hollows smaller than a few grid cells are below the model's resolution and are filled too.
_f = priority_flood(z, ~land, 0.05)
_dep = land & (_f - z > 0.5)
_lab, _n = ndimage.label(_dep, structure=np.ones((3, 3)))
_area = ndimage.sum(cell_area / 1e6, _lab, np.arange(1, _n + 1))
_small = np.zeros(_n + 1, bool); _small[1:] = _area < MIN_CLOSED_BASIN_KM2
fill_here = land & ((runoff_mm > 8) | _small[_lab])
z = np.where(fill_here, _f, z)
z_start = z.copy()
q_cell = (np.clip(runoff_mm, 0, None) / 1000.0 * cell_area).ravel()       # m3/yr produced in each cell
floor_ = np.where(land, 1.0, -1e9).ravel()
erodible = land.ravel()
n_steps = int(round(EROSION_MYR * 1e6 / DT_YR))
for s in range(n_steps):
    f, rec, dist, oa, od = route(z, ocean)
    Q = accumulate_losses(od, rec, dist, q_cell, E_net_land, CHANNEL_WIDTH_A, FLOODPLAIN_X)
    zold = z.ravel().copy()
    zf = implicit_stream_power(zold.copy(), oa, rec, dist, Q, K_SP, M_SP, DT_YR, erodible, floor_)
    gap = np.where(land, f - (z + MICRO), 0.0).ravel()       # depth below the spill level
    zf = deposit_in_depressions(od, rec, zold, zf, np.clip(gap, 0, None), cell_area.ravel(), erodible)
    z = zf.reshape(H, W)
eroded = z_start - z      # positive = erosion, negative = sediment fill

# ---------- 3. lakes and endorheic basins ----------
PET_lake = PET * 1.15                                        # open water evaporates more than land surfaces
E_net = np.clip(PET_lake - P, 0, None) / 1000.0              # m/yr


def find_lakes(z, sinks):
    """Return lake mask, endorheic lake mask, salt flag map."""
    f_plain = priority_flood(z, sinks, 0.0)
    dep = land & (f_plain - z > 0.5) & ~sinks
    lab, n = ndimage.label(dep, structure=np.ones((3, 3)))
    return f_plain, lab, n


sinks = ocean.copy()
lake = np.zeros((H, W), bool)
endo_lake = np.zeros((H, W), bool)
for it in range(3):
    f, rec, dist, oa, od = route(z, sinks)
    Q = accumulate_losses(od, rec, dist, q_cell, E_net_land, CHANNEL_WIDTH_A, FLOODPLAIN_X).reshape(H, W)
    f_plain, lab, n = find_lakes(z, sinks)
    lake[:] = False
    new_endo = endo_lake.copy()
    objs = ndimage.find_objects(lab)
    for d, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        m = lab[sl] == d
        zz = z[sl][m]; aa = cell_area[sl][m]; ee = E_net[sl][m]
        q_in = Q[sl][m].max()
        full_loss = (aa * ee).sum()
        if q_in >= full_loss:                       # overflows -> open lake at spill level
            lake[sl] |= m
            continue
        order = np.argsort(zz)
        cum = np.cumsum((aa * ee)[order])
        k = int(np.searchsorted(cum, q_in)) + 1
        sel = np.zeros(m.sum(), bool); sel[order[:max(k, 1)]] = True
        mm = np.zeros_like(m); mm[m] = sel
        lake[sl] |= mm
        new_endo[sl] |= mm
    if (new_endo == endo_lake).all() and it > 0:
        break
    endo_lake = new_endo
    sinks = ocean | endo_lake
lake |= endo_lake

# final routing with endorheic lakes as terminal sinks
f, rec, dist, oa, od = route(z, sinks)
Q = accumulate_losses(od, rec, dist, q_cell, E_net_land, CHANNEL_WIDTH_A, FLOODPLAIN_X)   # m3/yr
area_up = accumulate(od, rec, (cell_area / 1e6).ravel())         # km2
Q_m3s = (Q / (365.25 * 86400)).reshape(H, W)
lab_b = basin_labels(oa, rec).reshape(H, W)
reach = reaches_sea(oa, rec, Q, ocean.ravel(), 1.0e6).reshape(H, W)
# Endorheic (closed) basins: land that drains topographically into a terminal lake, not to the sea.
term_endo = endo_lake.ravel()[lab_b.ravel()].reshape(H, W)
endo_area = land & term_endo
# Non-contributing land: water evaporates on the way and never reaches the sea (includes dry wadis).
noncontrib = land & ~reach

# ---------- 4. network statistics ----------
lup, strahler = network_stats(od, rec, dist, area_up, CHANNEL_AREA_KM2)
lup = lup.reshape(H, W); strahler = strahler.reshape(H, W); area_up2 = area_up.reshape(H, W)
# Hack's law L = C A^h fitted on channel cells
sel = land.ravel() & (area_up >= 5e3) & (area_up <= 2e6) & (lup.ravel() > 0)
hack_h, hack_c = np.polyfit(np.log(area_up[sel]), np.log(lup.ravel()[sel] / 1000), 1)
# Horton bifurcation ratio: count stream segments per Strahler order
rec2 = rec.reshape(-1)
so = strahler.ravel()
seg_heads = {}
donor_same = np.zeros(H * W, bool)
ks = np.nonzero(so > 0)[0]
r_ = rec2[ks]
same = (so[r_] == so[ks]) & (r_ != ks)
donor_same[r_[same]] = True
for o in range(1, so.max() + 1):
    seg_heads[o] = int(((so == o) & ~donor_same).sum())
orders = [o for o in sorted(seg_heads) if seg_heads[o] > 0]
fit_orders = [o for o in orders if o < max(orders)]      # highest order has 1-2 streams: excluded (small sample)
slope = np.polyfit(fit_orders, np.log([seg_heads[o] for o in fit_orders]), 1)[0]
Rb = float(math.exp(-slope))                             # Horton's law of stream numbers: N_k ~ Rb^-k

# ---------- 5. stats ----------
A_land_m2 = cell_area[land].sum()
runoff_total_km3 = float((np.clip(runoff_mm, 0, None) / 1e6 * cell_area / 1e6)[land].sum())
to_ocean_km3 = float((np.clip(runoff_mm, 0, None) / 1e6 * cell_area / 1e6)[land & ~term_endo].sum())
precip_land_km3 = float((P / 1e6 * cell_area / 1e6)[land].sum())
outlets = np.nonzero(ocean.ravel() & (np.arange(H * W) == lab_b.ravel()))[0]
# biggest rivers by discharge at their mouth (last land cell before the sea)
mouth = land.ravel() & ocean.ravel()[rec2] & (rec2 != np.arange(H * W))
mouth_idx = np.nonzero(mouth)[0]
top = mouth_idx[np.argsort(-Q[mouth_idx])][:10]
rivers_top = [dict(rank=n + 1, discharge_m3s=round(float(Q[k] / 3.15576e7)), basin_km2=round(float(area_up[k])),
                   length_km=round(float(lup.ravel()[k] / 1000)),
                   mouth_latlon=[round(float(LATd.ravel()[k]), 1), round(float((ii.ravel()[k] + 0.5) / W * 360 - 180), 1)])
              for n, k in enumerate(top)]
stats = dict(erosion_myr=EROSION_MYR, k_stream_power=K_SP, m=M_SP, n=1, fu_w=FU_W,
             land_precip_km3=round(precip_land_km3), land_runoff_km3=round(runoff_total_km3),
             runoff_to_ocean_km3=round(to_ocean_km3), runoff_ratio=round(runoff_total_km3 / precip_land_km3, 3),
             endorheic_share_of_land_pct=round(float(cell_area[endo_area].sum() / A_land_m2 * 100), 1),
             noncontributing_share_of_land_pct=round(float(cell_area[noncontrib].sum() / A_land_m2 * 100), 1),
             lake_area_km2=round(float(cell_area[lake].sum() / 1e6)),
             lake_share_of_land_pct=round(float(cell_area[lake].sum() / A_land_m2 * 100), 2),
             salt_lakes=int(ndimage.label(endo_lake)[1]), open_lakes=int(ndimage.label(lake & ~endo_lake)[1]),
             hack_exponent=round(float(hack_h), 3), hack_coefficient_km=round(float(math.exp(hack_c)), 3),
             strahler_max_order=int(so.max()), stream_segments_per_order=seg_heads,
             bifurcation_ratio=round(Rb, 2),
             mean_erosion_land_m=round(float(eroded[land].mean())), max_incision_m=round(float(eroded[land].max())),
             highest_after_erosion_m=round(float(z.max())),
             largest_rivers=rivers_top)
json.dump(stats, open(f"{OUT}/world_hydrology.json", "w"), indent=1)
np.savez_compressed(f"{OUT}/world_hydrology.npz", elevation_eroded_m=z.astype(np.float32),
                    erosion_m=eroded.astype(np.float32), discharge_m3s=Q_m3s.astype(np.float32),
                    upstream_area_km2=area_up2.astype(np.float32), receiver=rec.reshape(H, W).astype(np.int32),
                    lake=lake, salt_lake=endo_lake, endorheic=endo_area, basin=lab_b.astype(np.int32),
                    strahler=strahler.astype(np.int8), pet_mm=PET.astype(np.float32),
                    runoff_mm=runoff_mm.astype(np.float32))
print(json.dumps({k: v for k, v in stats.items() if k != "largest_rivers"}))
for r in rivers_top[:5]:
    print(r)

# ---------- 6. render ----------
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
S = 1.25
biome = CD["biome"]
pal = {0: (38, 78, 128), 1: (205, 222, 235), 2: (242, 246, 250), 3: (158, 168, 140), 4: (150, 140, 134),
       5: (52, 102, 82), 6: (82, 140, 66), 7: (36, 112, 72), 8: (160, 160, 70), 9: (70, 150, 90),
       10: (196, 190, 112), 11: (190, 178, 150), 12: (232, 206, 140), 13: (200, 168, 80), 14: (110, 160, 50),
       15: (20, 110, 40)}
lut = np.zeros((16, 3)); [lut.__setitem__(k, v) for k, v in pal.items()]


def hillshade(e):
    dxx = (dx_m[:, None] * np.ones((1, W)))
    gx = (np.roll(e, -1, 1) - np.roll(e, 1, 1)) / (2 * dxx)
    gy = (np.vstack([e[:1], e[:-1]]) - np.vstack([e[1:], e[-1:]])) / (2 * dy_m)
    nx, ny = -gx * 22, -gy * 22
    sh = (nx * -0.6 + ny * 0.6 + 0.55) / (np.sqrt(nx ** 2 + ny ** 2 + 1) * math.sqrt(1.0225))
    sh = np.clip(sh, 0, 1)
    return sh / sh[land].mean()


def draw_rivers(img, color, q_min, wscale):
    d = ImageDraw.Draw(img)
    on_ice = (biome == 2).ravel()                     # ice sheets drain through glaciers, not rivers
    ks = np.nonzero((Q_m3s.ravel() >= q_min) & land.ravel() & ~lake.ravel() & ~on_ice)[0]
    for k in ks:
        r = rec2[k]
        if r == k:
            continue
        j, i = divmod(k, W); jr, ir = divmod(r, W)
        if abs(ir - i) > 1:
            continue
        q = Q_m3s.ravel()[k]
        wdt = max(1, int(round(wscale * math.log10(q / q_min + 1) * 2.2)))
        d.line([((i + 0.5) * S, (j + 0.5) * S), ((ir + 0.5) * S, (jr + 0.5) * S)], fill=color, width=wdt)


sh = hillshade(np.where(land, z, 0))
rgb = lut[biome].copy()
rgb = np.where(land[..., None], rgb * (0.55 + 0.45 * sh)[..., None], rgb * (1.15 - 0.45 * np.clip(-z / 6000, 0, 1))[..., None])
rgb[lake & ~endo_lake] = (70, 130, 190)
rgb[endo_lake] = (150, 200, 205)
coast = land ^ ndimage.binary_erosion(land)
rgb[coast] *= 0.6
img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((int(W * S), int(H * S)), Image.LANCZOS)
draw_rivers(img, (40, 95, 175), RIVER_Q_M3S, 1.0)
LEG = 80
canvas = Image.new("RGB", (img.width, img.height + LEG), (24, 26, 32))
canvas.paste(img, (0, 0))
dd = ImageDraw.Draw(canvas)
f18 = ImageFont.truetype(FONT, 18)
y0 = img.height + 14
for x, c, t in ((24, (40, 95, 175), f"Ріки (витрата > {int(RIVER_Q_M3S)} м³/с, товщина ∝ витраті)"),
                (24, (70, 130, 190), "Прісні проточні озера"),
                (900, (150, 200, 205), "Солоні безстічні озера")):
    yy = y0 if x == 900 or c != (70, 130, 190) else y0 + 30
    dd.rectangle([x, yy + 3, x + 30, yy + 19], fill=c)
    dd.text((x + 42, yy), t, font=f18, fill=(230, 230, 230))
canvas.save(f"{OUT}/rivers_map.png", optimize=True)

# basins map
big = np.zeros(H * W, bool)
lb = lab_b.ravel()
ids, counts = np.unique(lb[land.ravel()], return_counts=True)
area_by = ndimage.sum(cell_area.ravel()[land.ravel()], lb[land.ravel()], ids)
top_ids = ids[np.argsort(-area_by)][:40]
rng = np.random.default_rng(3)
cols = {t: np.array(__import__("colorsys").hsv_to_rgb((0.11 + n * 0.6180339) % 1, 0.5, 0.88)) * 255
        for n, t in enumerate(top_ids)}
rgbb = np.where(land[..., None], np.array([200, 200, 196.0]), np.array([30, 40, 62.0]))
for t, c in cols.items():
    rgbb[(lab_b == t) & land] = c
rgbb[endo_area] = (120, 112, 104)
rgbb = rgbb * np.where(land, 0.7 + 0.3 * sh, 1.0)[..., None]
rgbb[lake] = (110, 170, 215)
rgbb[coast] *= 0.5
imgb = Image.fromarray(np.clip(rgbb, 0, 255).astype(np.uint8)).resize((int(W * S), int(H * S)), Image.NEAREST)
draw_rivers(imgb, (25, 55, 110), 600.0, 0.7)
cb = Image.new("RGB", (imgb.width, imgb.height + 60), (24, 26, 32))
cb.paste(imgb, (0, 0))
dd = ImageDraw.Draw(cb)
dd.rectangle([24, imgb.height + 17, 54, imgb.height + 33], fill=(120, 112, 104))
dd.text((66, imgb.height + 14), "Безстічні (ендорейні) області", font=f18, fill=(230, 230, 230))
dd.text((500, imgb.height + 14), "Кольори: 40 найбільших річкових басейнів; сірий: малі басейни",
        font=f18, fill=(230, 230, 230))
cb.save(f"{OUT}/basins_map.png", optimize=True)
