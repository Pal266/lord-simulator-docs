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
import json, math, os, time
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
for step in range(int(ERODE_YR / DT)):
    f, rec, dist, oa, od = route(z, fixed, DX)
    Q = accumulate(od, rec, q_cell)
    zf = stream_power(z.ravel().copy(), oa, rec, dist, Q * kfac.ravel() ** 2, K_SP, M_SP, DT, fixed.ravel())
    z = diffuse(zf.reshape(H, W), D_HILL, DT, DX, fixed, 1)
    print(f"step {step + 1}: {time.time() - t0:.0f} s", flush=True)
# today's discharge: water flows through the lakes (only the sea is a sink)
f, rec, dist, oa, od = route(z, sea, DX)
Qs = (accumulate(od, rec, q_cell) / 3.15576e7).reshape(H, W)
np.savez_compressed(os.path.join(REGION_OUT, "refined_25m.npz"), x_m=x.astype(np.float32), y_m=y.astype(np.float32),
                    elevation_m=z.astype(np.float32), discharge_m3s=Qs.astype(np.float32), lake=lake, sea=sea,
                    receiver=rec.reshape(H, W).astype(np.int32))
json.dump(dict(resolution_m=DX, cells=int(H * W), years=ERODE_YR, postglacial_years=POSTGLACIAL_YR,
               seconds=round(time.time() - t0)), open(os.path.join(REGION_OUT, "refined_25m.json"), "w"), indent=1)
print("done", round(time.time() - t0), "s")
