"""
Region step 1b: refine the 100 m regional model to 25 m with the same erosion physics.

Noise alone gives the right roughness statistics but the wrong shapes (lumps instead of gullies and spurs).
Real hillslopes at 100 m - 1 km are organised by small streams, so this step lets water organise them:
  * start from the 100 m model (cubic interpolation) plus small random relief;
  * stream-power erosion (same K and m as the regional model) and hillslope diffusion;
  * where glaciers stood at the last glacial maximum the surface is only ~15 000 years old, so erosion there
    is scaled by 15 000 / ERODE_YR (troughs and moraines stay fresh);
  * the sea and the lakes of the regional model are kept as fixed base levels.

Usage:  python refine_25m.py           (~10 minutes, ~3 GB of memory)
Output: ../output/refined_25m.npz (not stored in Git)
"""
import json, math, os, sys, time
import numpy as np
from scipy import ndimage
from region_common import CFG, HALF_M, REGION_OUT
from region_flow import accumulate, diffuse, route, stream_power

DX = 25.0
MARGIN_M = 2000.0                 # beyond the square, so the plots' edges are not at the model edge
ERODE_YR, DT = 1.0e6, 5.0e4      # most of the late Quaternary: long enough for small valleys to form
K_SP, M_SP = 1.0e-6, 0.5          # same as the regional model
D_HILL = 0.002                    # m2/yr, soil-mantled hillslopes (typical range ~0.001-0.01): lets small valleys survive
POSTGLACIAL_YR = 1.5e4
SEED_RELIEF_M = 8.0               # sub-100 m roughness from which gullies start
# cirques (Evans & Cox 2015, global medians: width ~656 m, floor ~7.7 deg, headwall maximum ~57 deg)
CIRQUE_WIDTH_M = 650.0
CIRQUE_SPACING_M = 700.0          # neighbouring cirque centres; closer spacing lets their walls meet in aretes
CIRQUE_FLOOR_DEG = 8.0
CIRQUE_WALL_DEG = 50.0            # mean headwall gradient (below the ~57 deg maximum)
CIRQUE_OVERDEEPEN_M = 15.0
CIRQUE_MIN_RELIEF_M = 200.0       # ground rising behind the site (median cirque wall ~210 m)
CIRQUE_BACK_TEST_M = 700.0        # ... within this distance up the valley axis
CIRQUE_FLOOR_HALFWIDTH_M = 260.0  # floor half-width; with the walls the rim-to-rim width is ~650 m
CIRQUE_FLOOR_BACK_M = 250.0       # floor reaches this far behind the site (cirque length ~ width)        # rock basin behind the lip (room for a small tarn)
# outwash plains (sandur): concave long profile, coarse near the ice front, at most ~100 m thick
OUTWASH_LENGTH_M = 15000.0
OUTWASH_DECAY_M = 4000.0          # the fill thins downstream (e-folding length): sediment is dropped near the ice first
OUTWASH_HALFWIDTH_M = 1500.0
OUTWASH_MAX_THICK_M = 100.0
OUTWASH_Q_MIN = 5.0               # m3/s today: glacier-fed rivers large enough to build a plain
OUTWASH_MIN_RUN_M = 2000.0
OUTWASH_HEAD_M = 40.0             # fill thickness at the ice front (moraine ridges are ~30 m; deposits reach ~100 m)
OUTWASH_TERRACE_M = 8.0           # Holocene incision of the river into the fill

t0 = time.time()
m = np.load(os.path.join(REGION_OUT, "regional_model.npz"))
z100 = m["elevation_m"].astype(np.float64); xs = m["x_m"]; ys = m["y_m"]
half = HALF_M + MARGIN_M
x = np.arange(-half + DX / 2, half, DX); y = np.arange(half - DX / 2, -half, -DX)
X, Y = np.meshgrid(x, y)
fi = (X - xs[0]) / 100.0; fj = (ys[0] - Y) / 100.0
z = ndimage.map_coordinates(z100, [fj, fi], order=3)
rng = np.random.default_rng(CFG["world_seed"] * 31 + 5)
noise = ndimage.gaussian_filter(rng.normal(size=z.shape), 2.0)
noise = noise / noise.std() * SEED_RELIEF_M
lake = ndimage.map_coordinates(m["lake"].astype(float), [fj, fi], order=0) > 0.5
sea = ndimage.map_coordinates(m["sea"].astype(float), [fj, fi], order=0) > 0.5
ice = ndimage.map_coordinates(m["ice_lgm"].astype(float), [fj, fi], order=1)
# runoff per unit area from the planet's water balance (precipitation minus evapotranspiration)
from region_common import load_world, sample_world, xy_to_latlon
wd = load_world()
LAT, LON = xy_to_latlon(X, Y)
runoff = np.clip(sample_world(wd["hydro"]["runoff_mm"], LAT, LON, 1), 0, None) / 1000.0
del LAT, LON
fixed = sea | lake
# rivers that enter the refined area from outside (e.g. the main river rising on the range crest west of the
# square): inject the regional model's discharge where they cross into the 25 m grid
f100, rec100, _, _, _ = route(z100, m["sea"], 100.0)
X100, Y100 = np.meshgrid(xs, ys)
ins100 = (np.abs(X100) < half) & (np.abs(Y100) < half)
r_ = rec100.reshape(-1)
src = np.nonzero(~ins100.ravel() & ins100.ravel()[r_] & (np.arange(r_.size) != r_))[0]
inflow = np.zeros(z.shape)
Q100 = m["discharge_m3s"].ravel() * 3.15576e7
for k in src:
    if Q100[k] <= 0:
        continue
    # follow the regional river ~1 km into the grid: cells at the grid edge drain straight out of the model
    kk = int(r_[k])
    for _ in range(100):
        jx, ix_ = divmod(kk, xs.size)
        if min(half - abs(xs[ix_]), half - abs(ys[jx])) > 1000.0 or r_[kk] == kk:
            break
        kk = int(r_[kk])
    jx, ix_ = divmod(kk, xs.size)
    jj = int(np.clip((y[0] - ys[jx]) / DX, 0, z.shape[0] - 1)); ii = int(np.clip((xs[ix_] - x[0]) / DX, 0, z.shape[1] - 1))
    inflow[jj, ii] += Q100[k]
del X100, Y100
z = np.where(fixed, z, z + noise)
kfac = (1 - ice) + ice * (POSTGLACIAL_YR / ERODE_YR)       # young glacial surfaces barely eroded
q_cell = (runoff * DX * DX + inflow).ravel()
H, W = z.shape
print(f"grid {W} x {H} = {H * W / 1e6:.1f} M cells, setup {time.time() - t0:.0f} s")
CACHE = os.path.join(REGION_OUT, "eroded_25m.npz")       # fluvial stage only; lets the glacial stage be re-run quickly
if "--reuse-erosion" in sys.argv and os.path.exists(CACHE):
    z = np.load(CACHE)["z"].astype(np.float64)
    print("fluvial stage loaded from", CACHE)
else:
    for step in range(int(ERODE_YR / DT)):
        f, rec, dist, oa, od = route(z, fixed, DX)
        Q = accumulate(od, rec, q_cell)
        zf = stream_power(z.ravel().copy(), oa, rec, dist, Q * kfac.ravel() ** 2, K_SP, M_SP, DT, fixed.ravel())
        z = diffuse(zf.reshape(H, W), D_HILL, DT, DX, fixed, 1)
        print(f"step {step + 1}: {time.time() - t0:.0f} s", flush=True)
    np.savez_compressed(CACHE, z=z.astype(np.float32))

# ---------------- cirques: armchair hollows at glacier heads, steep headwalls -> aretes and horns ----------------
# Dimensions from global cirque morphometry (Evans & Cox 2015, medians): length ~625 m, width ~656 m,
# floor gradient ~8 deg, headwall (maximum) gradient ~57 deg, wall height ~210 m.
# Neighbouring cirques cut into the same ridge from both sides; where their walls meet, a sharp ridge (arete)
# remains, and where three or more meet, a pyramidal peak (horn).
ela_lgm = ndimage.map_coordinates(m["ela_lgm_m"], [fj, fi], order=1)
f, rec, dist, oa, od = route(z, fixed, DX)
area_km2 = (accumulate(od, rec, np.full(z.size, DX * DX / 1e6))).reshape(z.shape)
# cirques need a valley head below a steep enough mountain: the ground CIRQUE_BACK_TEST_M behind the site (up the
# valley axis) must rise at least CIRQUE_MIN_RELIEF_M above it. On gentle plateau ground real cirques are shallow or
# absent, so none are carved there.
zs = ndimage.gaussian_filter(z, 200.0 / DX)
gsy, gsx = np.gradient(zs, DX)                             # rows (south), cols (east)
head = (ice > 0.5) & (z > ela_lgm) & (z < ela_lgm + 450) & (area_km2 > 0.05) & (area_km2 < 2.0) & ~fixed
sites = []
if head.any():
    hj, hi_ = np.nonzero(head)
    order = np.argsort(-z[hj, hi_])                       # highest heads first
    taken = np.zeros(z.shape, bool)
    sep = int(CIRQUE_SPACING_M / DX)
    for o in order:
        j, i = hj[o], hi_[o]
        if taken[max(0, j - sep):j + sep + 1, max(0, i - sep):i + sep + 1].any():
            continue
        # downslope direction (the cirque opens this way) from the 200 m-smoothed surface; (north, east) components
        uy, ux = gsy[j, i], -gsx[j, i]
        nrm = math.hypot(uy, ux)
        if nrm < 1e-3:
            continue
        uy, ux = uy / nrm, ux / nrm
        jb = int(round(j + uy * CIRQUE_BACK_TEST_M / DX)); ib = int(round(i - ux * CIRQUE_BACK_TEST_M / DX))
        if not (0 <= jb < H and 0 <= ib < W) or z[jb, ib] - z[j, i] < CIRQUE_MIN_RELIEF_M:
            continue
        taken[j, i] = True
        sites.append((j, i, uy, ux))                       # (row, col, unit vector downslope as (north, east))
del zs, gsy, gsx
cirque = np.zeros(z.shape, bool)
R_OUT = 1.6 * (CIRQUE_FLOOR_HALFWIDTH_M + CIRQUE_FLOOR_BACK_M) + 400.0
tan_floor = math.tan(math.radians(CIRQUE_FLOOR_DEG))
rad = int(R_OUT / DX) + 1
crng = np.random.default_rng(CFG["world_seed"] * 31 + 11)
params = []
for (j, i, uy, ux) in sites:
    # natural spread between cirques: size, wall steepness and orientation vary around the medians
    R_FLOOR = CIRQUE_FLOOR_HALFWIDTH_M * float(np.exp(crng.normal(0, 0.25)))
    BACK_ = CIRQUE_FLOOR_BACK_M * float(np.exp(crng.normal(0, 0.25)))
    tan_wall = math.tan(math.radians(float(np.clip(crng.normal(CIRQUE_WALL_DEG, 5.0), 38.0, 60.0))))
    rot = math.radians(float(crng.normal(0, 12.0)))
    uy, ux = uy * math.cos(rot) - ux * math.sin(rot), uy * math.sin(rot) + ux * math.cos(rot)
    params.append((R_FLOOR, BACK_, uy, ux))
    j0, j1 = max(0, j - rad), min(H, j + rad + 1); i0, i1 = max(0, i - rad), min(W, i + rad + 1)
    yy = (j - np.arange(j0, j1))[:, None] * DX             # north positive
    xx = (np.arange(i0, i1) - i)[None, :] * DX
    u = xx * ux + yy * uy                                  # along the cirque axis (positive = out of the cirque)
    v = -xx * uy + yy * ux
    zf = z[j, i] - CIRQUE_OVERDEEPEN_M
    back = np.clip(-u, 0, None)                            # distance behind the lip end of the floor
    # the floor is a rounded strip reaching CIRQUE_FLOOR_BACK_M up the axis; walls rise from its rim
    ub = np.where(u < -BACK_, u + BACK_, 0.0)
    r = np.hypot(ub, v)
    s = zf + tan_floor * back + tan_wall * np.clip(r - R_FLOOR, 0, None)
    s = np.where(u > 0, np.maximum(s, zf + tan_floor * u), s)  # floor rises again to the rock lip
    blk = z[j0:j1, i0:i1]
    # open towards the valley: the cut fades out over one floor half-width beyond the lip (no step at the mouth)
    t_ = np.clip(u / R_FLOOR, 0, 1)
    new = blk - np.clip(blk - s, 0, None) * (1 - t_ * t_ * (3 - 2 * t_))
    new = np.where(fixed[j0:j1, i0:i1], blk, new)
    cirque[j0:j1, i0:i1] |= new < blk - 1.0
    z[j0:j1, i0:i1] = new

# ---------------- outwash plains below the LGM ice fronts, later cut into terraces ----------------
# Meltwater spread sand and gravel from the ice fronts down the valleys: valley floors are filled to a surface with
# a concave long profile (steeper near the ice front, flatter downstream), at most ~100 m thick (outwash plains can
# reach ~100 m). In the Holocene the river cut into this fill, leaving a terrace on both sides.
# meltwater leaves the ice where a drainage line crosses the LGM ice margin (lakes are passed through: at the LGM
# the ice filled today's lake basins)
f, rec, dist, oa, od = route(z, sea, DX)
Qa = accumulate(od, rec, q_cell).reshape(z.shape) / 3.15576e7
ice_mask = ice > 0.5
cross = np.zeros(z.size, bool)
ki = np.nonzero(ice_mask.ravel())[0]
cross[rec[ki][~ice_mask.ravel()[rec[ki]]]] = True
src = cross.reshape(z.shape) & (Qa > OUTWASH_Q_MIN) & ~fixed
outwash = np.zeros(z.shape, bool)
fill_top = np.full(z.shape, -np.inf)
sj, si = np.nonzero(src)
order = np.argsort(-Qa[sj, si])
used = np.zeros(z.size, bool)
path_id = np.full(z.size, -1, np.int32); path_s = np.zeros(z.size, np.float32)
print(f"outwash sources {len(sj)}", flush=True)
for o in order:
    k = sj[o] * W + si[o]
    if used[k]:
        continue
    s = 0.0; path = []
    run_ice = 0.0; s_out = 0.0; skirt = False
    # the stream is followed through small lakes (kettle lakes are common on outwash plains) and across short
    # stretches of the ragged ice outline; it stops at the sea or after ~500 m back under the ice
    while s < OUTWASH_LENGTH_M and not sea.flat[k] and not used[k] and run_ice < 500.0:
        path.append((k, s))
        r = rec[k]
        if r == k:
            break
        run_ice = run_ice + dist[k] if ice_mask.flat[r] else 0.0
        skirt |= bool(ice_mask.flat[r]) and s < OUTWASH_MIN_RUN_M     # back under the ice: a lateral margin, not a front
        s_out += 0.0 if ice_mask.flat[k] else dist[k]
        s += dist[k]; k = r
    # a real ice front: the meltwater stream stays out of the ice for at least OUTWASH_MIN_RUN_M;
    # streams that only skirt the ice margin and run back under it are not glacier fronts
    if skirt or s_out < OUTWASH_MIN_RUN_M:
        continue
    # fill surface = smoothed, never-rising valley floor + a deposit that thins downstream; the surface is then
    # steeper near the ice front than further down (concave long profile)
    kk = np.array([p_[0] for p_ in path]); ss = np.array([p_[1] for p_ in path])
    zfl = np.minimum.accumulate(ndimage.uniform_filter1d(z.flat[kk], 41, mode="nearest"))
    tops = zfl + OUTWASH_HEAD_M * np.exp(-ss / OUTWASH_DECAY_M)
    for k, top, s_ in zip(kk, tops, ss):
        used[k] = True
        if ice_mask.flat[k] or fixed.flat[k]:
            continue
        fill_top.flat[k] = max(fill_top.flat[k], top); path_id[k] = o; path_s[k] = s_
# spread each valley-floor surface sideways while the ground is lower than it (fills the valley floor only,
# connected to the meltwater channel - never a neighbouring valley)
seed = np.isfinite(fill_top)
thick = np.zeros(z.shape)
dlat = np.full(z.shape, np.inf)
if seed.any():
    dlat, (nj, ni) = ndimage.distance_transform_edt(~seed, return_indices=True)
    dlat = dlat * DX
    top_near = fill_top[nj, ni]
    cand = (dlat <= OUTWASH_HALFWIDTH_M) & (z < top_near - 0.5) & ~fixed & ~ice_mask
    lab, _ = ndimage.label(cand)
    keep = np.unique(lab[seed & cand]); keep = keep[keep > 0]
    fill = np.isin(lab, keep)
    new = np.minimum(top_near, z + OUTWASH_MAX_THICK_M)
    thick = np.where(fill, new - z, 0.0)
    outwash = fill
    z = np.where(fill, new, z)
    # Holocene incision: the river cut a belt ~300 m wide a few metres into the fill, leaving terraces
    belt = outwash & (dlat < 150.0)
    z = np.where(belt, z - OUTWASH_TERRACE_M * (1 - np.clip((dlat - 100.0) / 50.0, 0, 1)), z)
print(f"cirques {len(sites)}, cirque area {cirque.sum() * DX * DX / 1e6:.1f} km2, outwash {outwash.sum() * DX * DX / 1e6:.1f} km2, "
      f"max fill {thick.max():.0f} m", flush=True)

# today's discharge: water flows through the lakes (only the sea is a sink)
f, rec, dist, oa, od = route(z, sea, DX)
Qs = (accumulate(od, rec, q_cell) / 3.15576e7).reshape(H, W)
np.savez_compressed(os.path.join(REGION_OUT, "refined_25m.npz"), x_m=x.astype(np.float32), y_m=y.astype(np.float32),
                    elevation_m=z.astype(np.float32), discharge_m3s=Qs.astype(np.float32), lake=lake, sea=sea,
                    receiver=rec.reshape(H, W).astype(np.int32), cirque=cirque, outwash=outwash,
                    outwash_thickness_m=thick.astype(np.float32), outwash_trunk=np.isfinite(fill_top),
                    outwash_path_id=path_id.reshape(H, W), outwash_path_s=path_s.reshape(H, W),
                    cirque_sites=np.array(sites, np.float64).reshape(-1, 4), cirque_params=np.array(params, np.float64).reshape(-1, 4), ice_lgm=ice.astype(np.float32))
json.dump(dict(resolution_m=DX, cells=int(H * W), years=ERODE_YR, postglacial_years=POSTGLACIAL_YR,
               cirques=len(sites), cirque_width_m=CIRQUE_WIDTH_M, cirque_floor_halfwidth_m=CIRQUE_FLOOR_HALFWIDTH_M,
               cirque_floor_back_m=CIRQUE_FLOOR_BACK_M, cirque_km2=round(float(cirque.sum() * DX * DX / 1e6), 1),
               outwash_km2=round(float(outwash.sum() * DX * DX / 1e6), 1), outwash_max_thickness_m=round(float(thick.max()), 1),
               seconds=round(time.time() - t0)), open(os.path.join(REGION_OUT, "refined_25m.json"), "w"), indent=1)
print("done", round(time.time() - t0), "s")
