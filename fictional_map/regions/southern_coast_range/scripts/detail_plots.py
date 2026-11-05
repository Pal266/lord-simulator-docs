"""
Region step 2: detail every 25 x 25 km plot to ~3 m and export it for Unreal Engine.

For every vertex of a plot (4033 x 4033 for 10 x 10 km, spacing 10000/4032 = 2.48 m; set in region.json):
  1. Regional surface: cubic-spline interpolation of the 100 m regional model.
  2. Sub-100 m relief: self-affine fractal detail with Hurst exponent H = 0.5 (power spectrum ~ k^-2 along
     transects, as measured for Earth's topography), with an amplitude that depends on the terrain:
     rough on steep mountain slopes, smooth on plains and valley floors, none on lake floors.
  3. River channels cut along smoothed river courses: width w = 5 Q^0.5, depth from Manning's equation with
     the local channel slope, parabolic cross-section, banks blending into the floodplain.
  4. Lake floors below the lake level of the regional model.
  5. Ground layers, blended softly (weights of all layers add up to 255 at every vertex): rock (steep walls),
     scree (talus at 28-38 deg below the walls), alpine meadow (above the treeline), forest (below it), wet meadow
     (flat river floodplains), gravel (river bars and the Holocene floodplain cut into the outwash plains),
     riverbed and lakebed. The treeline follows the ~6.7 C growing-season mean temperature found at high-altitude
     treelines worldwide (Koerner & Paulsen 2004) and is a ~150 m wide transition (ecotone), not a line.

Every value depends only on world coordinates, never on the plot, so neighbouring plots share identical edge
vertices: the plots join without steps.

Usage:
  python detail_plots.py --tiles all                 # all 100 plots (~25 s each), then the mosaic
  python detail_plots.py --mosaic                    # only rebuild ../output/plots_mosaic.jpg from the previews
  python detail_plots.py --tiles x2_y1 x3_y1         # selected plots
  python detail_plots.py --tiles x2_y1 --preview     # quick 1/8-resolution preview only (seconds)
Outputs: ../export/tile_x{c}_y{r}/ (heightmap.png, layer_*.png, tile.json), ../output/previews/preview_tile_*.png
(not in Git) and ../output/plots_mosaic.jpg
"""
import argparse, json, math, os, sys
import numpy as np
from numba import njit, prange
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image
from region_common import CFG, HALF_M, REGION_DIR, REGION_OUT
from region_flow import priority_flood, route, accumulate

DX_REG = float(CFG["model_resolution_m"])
TILE_M = CFG["tiles"]["size_km"] * 1000.0
NV = CFG["tiles"]["vertices"]
SPACING = TILE_M / (NV - 1)
Z_SCALE = CFG["unreal"]["scale_z"]
UNITS_PER_M = 128.0 * 100.0 / Z_SCALE           # heightmap units per metre (12.8 for Z scale 1000)

# ---------------- parameters (see MODEL_NOTES.md) ----------------
HURST = 0.5                     # Earth topography: spectrum ~ k^-2 along transects -> H ~ 0.5
DETAIL_WAVELENGTHS = [100.0, 50.0, 25.0]        # below the 25 m base grid (the base carries larger scales)
DETAIL_C = 1.0                  # detail std at 640 m = DETAIL_C x local relief std (2 km) x (640/2000)^H
FINE_WAVELENGTHS = [12.0, 6.0]   # below ~20 m soil-covered slopes are smooth; only rocky ground stays rough
SOIL_FINE_FACTOR = 0.25
AMP_PLAIN, AMP_STEEP, AMP_ALPINE = 0.8, 7.0, 3.0  # metres at the 160 m wavelength
RIVER_Q_MIN = 1.0               # m3/s: smaller streams stay as fractal relief only
SHORE_M, SHORE_PIT_M, SHORE_FLAT_M = 100.0, 2.0, 0.2   # shore flats next to lakes (see build_tile)
SHORE_FADE_M = 150.0            # fine relief fades out towards lake shores over this distance
KETTLE_MIN_DEPTH_M = 2.0        # closed hollows on former glacier ground deeper than this hold a lake (kettles, tarns)
KETTLE_MIN_CELLS = 8            # ... if at least this many 25 m cells (0.5 ha)
WIDTH_A, MANNING_N = 5.0, 0.035
TREELINE_GS_TEMP = 6.7          # C, growing-season mean at the treeline
GS_THRESHOLD = 0.0              # months with mean temperature above this form the growing season
LAPSE = 0.0065
ROCK_SLOPE_DEG = 38.0           # above the angle of repose of talus (~32-38 deg): bare rock
SCREE_SLOPE_DEG = (28.0, 34.0)  # talus slopes stand at ~30-38 deg; scree fades in over this range
TREELINE_ECOTONE_M = 150.0      # width of the forest -> alpine meadow transition
TREELINE_NOISE_M = 60.0         # the treeline wanders up and down with local exposure and soil
SEED = CFG["world_seed"] * 7919 + 13
LAYERS = ["rock", "scree", "alpine_meadow", "forest", "wet_meadow", "gravel", "riverbed", "lakebed"]
L_ = {n: k for k, n in enumerate(LAYERS)}


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def to_weights255(wf):
    """float weights (..., L) summing to 1 -> uint8 weights summing exactly to 255 (remainder to the largest)."""
    w8 = np.floor(wf * np.float32(255.0)).astype(np.int16)
    rem = 255 - w8.sum(axis=-1)
    top = np.argmax(wf, axis=-1)
    np.put_along_axis(w8, top[..., None], np.take_along_axis(w8, top[..., None], -1) + rem[..., None], -1)
    return w8.astype(np.uint8)

EXPORT = os.path.join(REGION_DIR, "export")
PREP = os.path.join(REGION_OUT, "detail_prep.npz")
PREVIEWS = os.path.join(REGION_OUT, "previews")
MOSAIC = os.path.join(REGION_OUT, "plots_mosaic.jpg")
MOSAIC_PX = 1600


# ---------------- seamless value-noise fBm on world coordinates ----------------
@njit(cache=True)
def _hash(ix, iy, o, seed):
    h = (ix * 374761393 + iy * 668265263 + o * 2147483647 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / 16777215.0 * 2.0 - 1.0


@njit(parallel=True, cache=True)
def fbm(xw, yw, amp160, wavelengths, hurst, seed):
    n0, n1 = xw.shape
    out = np.zeros((n0, n1))
    for a in prange(n0):
        for b in range(n1):
            s = 0.0
            for o in range(wavelengths.size):
                lam = wavelengths[o]
                u = xw[a, b] / lam + o * 0.37; v = yw[a, b] / lam + o * 0.71
                iu = math.floor(u); iv = math.floor(v)
                fu = u - iu; fv = v - iv
                fu = fu * fu * (3 - 2 * fu); fv = fv * fv * (3 - 2 * fv)
                c00 = _hash(iu, iv, o, seed); c10 = _hash(iu + 1, iv, o, seed)
                c01 = _hash(iu, iv + 1, o, seed); c11 = _hash(iu + 1, iv + 1, o, seed)
                val = (c00 * (1 - fu) + c10 * fu) * (1 - fv) + (c01 * (1 - fu) + c11 * fu) * fv
                s += val * (lam / wavelengths[0]) ** hurst
            out[a, b] = s * amp160[a, b]
    return out


@njit(cache=True)
def isotonic_decreasing(y):
    """Pool-adjacent-violators: least-squares non-increasing fit to y."""
    n = y.size
    val = np.empty(n); wt = np.empty(n); cnt = np.empty(n, np.int64)
    k = 0
    for i in range(n):
        val[k] = y[i]; wt[k] = 1.0; cnt[k] = 1
        while k > 0 and val[k - 1] < val[k]:
            v = (val[k - 1] * wt[k - 1] + val[k] * wt[k]) / (wt[k - 1] + wt[k])
            wt[k - 1] += wt[k]; cnt[k - 1] += cnt[k]; val[k - 1] = v; k -= 1
        k += 1
    out = np.empty(n); i = 0
    for b in range(k):
        for _ in range(cnt[b]):
            out[i] = val[b]; i += 1
    return out


# ---------------- preparation (once) ----------------
def prepare():
    m = np.load(os.path.join(REGION_OUT, "regional_model.npz"))
    refined = os.path.join(REGION_OUT, "refined_25m.npz")
    if os.path.exists(refined):                      # preferred base: the 25 m refinement (refine_25m.py)
        b = np.load(refined)
        z = b["elevation_m"].astype(np.float64); xs = b["x_m"].astype(np.float64); ys = b["y_m"].astype(np.float64)
        sea = b["sea"]; lake = b["lake"]; Q = b["discharge_m3s"].ravel(); rec = b["receiver"].ravel().astype(np.int64)
        if "outwash" in b.files:   # Holocene floodplain inside the outwash terraces (gravel at the surface)
            dt_ = ndimage.distance_transform_edt(~b["outwash_trunk"]) * float(xs[1] - xs[0])
            ow_belt = b["outwash"] & (dt_ < 150.0)
        else:
            ow_belt = np.zeros(z.shape, bool)
    else:                                            # fallback: the 100 m regional model
        z = m["elevation_m"].astype(np.float64); xs = m["x_m"].astype(np.float64); ys = m["y_m"].astype(np.float64)
        sea = m["sea"]; lake = m["lake"]; Q = m["discharge_m3s"].ravel()
        rec = route(z, sea, DX_REG)[1]
        ow_belt = np.zeros(z.shape, bool)
    res = float(xs[1] - xs[0])
    level = priority_flood(z, sea, 0.0)
    # Closed depressions of the 25 m surface. In this humid climate (precipitation exceeds evapotranspiration) a real
    # closed basin fills with water up to its spill point, so:
    #  * a depression that contains a regional lake is that lake's full basin (the lake reaches its spill level); a lake
    #    is always a flat water surface, so regional lake cells outside a closed depression (on a slope of the 25 m
    #    surface, where the 100 m lake outline does not fit the finer terrain) are land;
    #  * a depression on former glacier ground (>= 0.5 ha, >= 2 m deep) is a kettle lake or tarn;
    #  * any other depression is an artefact of the erosion model (river landscapes have almost no closed pits):
    #    it is filled to its spill level, so no dry hollows lie below the water table.
    ice = np.zeros(z.shape, bool)
    if os.path.exists(refined) and "ice_lgm" in np.load(refined).files:
        ice = np.load(refined)["ice_lgm"] > 0.5
    dep = ((level - z) > 0.01) & ~sea
    lab_, n_ = ndimage.label(dep)
    idx = range(1, n_ + 1)
    has_lake = np.r_[False, ndimage.maximum(lake, lab_, idx) > 0]
    kettle = np.r_[False, (ndimage.sum(dep, lab_, idx) >= KETTLE_MIN_CELLS)
                   & (ndimage.maximum(level - z, lab_, idx) >= KETTLE_MIN_DEPTH_M) & (ndimage.mean(ice, lab_, idx) > 0.5)]
    keep = has_lake | kettle
    z = np.where(dep & ~keep[lab_], level, z)          # fill artefact pits
    lake = dep & keep[lab_]
    lake_level = np.where(lake, level, np.nan)
    # river courses: trace downstream from every channel head, smooth, keep discharge
    river = (Q >= RIVER_Q_MIN) & ~lake.ravel() & ~sea.ravel()
    has_up = np.zeros(Q.size, bool)
    ks = np.nonzero(river)[0]
    has_up[rec[ks][river[rec[ks]] & (rec[ks] != ks)]] = True
    heads = ks[~has_up[ks]]
    visited = np.zeros(Q.size, bool)
    W = z.shape[1]
    lines = []
    for h in heads:
        k = h; path = []
        while True:
            path.append(k)
            if visited[k]:
                break
            visited[k] = True
            r = rec[k]
            if r == k or not river[r] and not lake.ravel()[r]:
                if r != k:
                    path.append(r)
                break
            if lake.ravel()[r]:
                path.append(r); break
            k = r
        if len(path) < 2:
            continue
        pj, pi = np.divmod(np.array(path), W)
        p = np.column_stack([xs[pi], ys[pj]]).astype(float)
        q = Q[path]
        for _ in range(3):                                   # Chaikin smoothing (keeps the end points)
            a_ = 0.75 * p[:-1] + 0.25 * p[1:]; b_ = 0.25 * p[:-1] + 0.75 * p[1:]
            qa = 0.75 * q[:-1] + 0.25 * q[1:]; qb = 0.25 * q[:-1] + 0.75 * q[1:]
            p = np.vstack([p[:1], np.column_stack([a_, b_]).reshape(-1, 2), p[-1:]])
            q = np.r_[q[:1], np.column_stack([qa, qb]).ravel(), q[-1:]]
        lines.append((p, q))
    # densify to <= 3 m spacing so distances to the polyline are exact enough at 3 m
    P, Qp = [], []
    for p, q in lines:
        seg = np.hypot(*np.diff(p, axis=0).T)
        s = np.r_[0, np.cumsum(seg)]
        t = np.arange(0, s[-1], 2.5)
        P.append(np.column_stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])]))
        Qp.append(np.interp(t, s, q))
    spl = ndimage.spline_filter(z, order=3)
    # snap every river to the lowest line of the smooth (cubic) valley floor: sample across the river and move
    # each point to the lowest spot within +-80 m, then smooth again so the channel stays continuous
    snapped = []
    for p in P:
        t = np.gradient(p, axis=0); t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
        nrm = np.column_stack([-t[:, 1], t[:, 0]])
        offs = np.arange(-2 * res - 30, 2 * res + 30.1, 10.0)
        cand = p[:, None, :] + offs[None, :, None] * nrm[:, None, :]
        zz = ndimage.map_coordinates(spl, [(ys[0] - cand[..., 1]) / res, (cand[..., 0] - xs[0]) / res],
                                     order=3, prefilter=False)
        best = offs[np.argmin(zz, axis=1)]
        best = ndimage.gaussian_filter1d(best, 40, mode="nearest")      # ~100 m smoothing along the river
        snapped.append(p + best[:, None] * nrm)
    line_len = np.array([len(p) for p in snapped], np.int64)         # points per river line (for export_water.py)
    P = np.vstack(snapped); Qp = np.concatenate(Qp)
    ws = ndimage.map_coordinates(spl, [(ys[0] - P[:, 1]) / res, (P[:, 0] - xs[0]) / res], order=3, prefilter=False)
    # water never flows uphill: the water surface along each river line is the closest never-rising profile to the
    # valley floor (isotonic regression), so the channel cuts through small bumps and fills small pits
    o_ = 0
    for n_ in line_len:
        ws[o_:o_ + n_] = isotonic_decreasing(ws[o_:o_ + n_]); o_ += n_
    # local channel slope from the base surface along each river (smoothed over ~200 m), for Manning depth
    gy, gx = np.gradient(ndimage.gaussian_filter(z, 200.0 / res), res)
    slope_reg = np.hypot(gx, gy)
    Sp = ndimage.map_coordinates(slope_reg, [(ys[0] - P[:, 1]) / res, (P[:, 0] - xs[0]) / res], order=1)
    Sp = np.clip(Sp, 2e-4, 0.05)
    width = WIDTH_A * Qp ** 0.5
    depth = (Qp * MANNING_N / (width * Sp ** 0.5)) ** 0.6
    # treeline height: growing-season mean temperature = 6.7 C (monthly sinusoid from summer / winter)
    Ts, Tw = m["summer_temp_c"].astype(float), m["winter_temp_c"].astype(float)
    months = [(Ts + Tw) / 2 + (Ts - Tw) / 2 * math.cos(2 * math.pi * k / 12) for k in range(12)]

    def gs_mean(dz):
        tm = [t - LAPSE * dz for t in months]
        num = sum(np.where(t > GS_THRESHOLD, t, 0) for t in tm); den = sum((t > GS_THRESHOLD).astype(float) for t in tm)
        return np.where(den > 0, num / np.maximum(den, 1), -10)
    z100 = m["elevation_m"].astype(np.float64)
    lo = np.full(z100.shape, -1000.0); hi = np.full(z100.shape, 4000.0)
    for _ in range(25):
        mid = (lo + hi) / 2
        warm = gs_mean(mid) > TREELINE_GS_TEMP
        lo = np.where(warm, mid, lo); hi = np.where(warm, hi, mid)
    treeline100 = ndimage.gaussian_filter(z100 + (lo + hi) / 2, 5)
    XB, YB = np.meshgrid(xs, ys)
    treeline = ndimage.map_coordinates(treeline100, [(m["y_m"][0] - YB) / 100.0, (XB - m["x_m"][0]) / 100.0], order=1)
    del XB, YB
    # distance to the nearest lake and that lake's level (for the shore flats in build_tile)
    lake_dist, (nj_, ni_) = ndimage.distance_transform_edt(~lake, return_indices=True)
    lake_dist = lake_dist * res
    lake_near_level = np.nan_to_num(lake_level, nan=-9999.0)[nj_, ni_]
    gyz, gxz = np.gradient(z, res)
    slope_deg = np.degrees(np.arctan(np.hypot(gxz, gyz)))
    win = int(round(2000.0 / res)) | 1
    mz = ndimage.uniform_filter(z, win); mz2 = ndimage.uniform_filter(z * z, win)
    relief_std = np.sqrt(np.clip(mz2 - mz * mz, 0, None))                     # relief std in a ~2 km window
    np.savez_compressed(PREP, spline=spl, z=z, x0=xs[0], y0=ys[0], res=res, lake_level=np.nan_to_num(lake_level, nan=-9999.0),
                        lake=lake, sea=sea, river_pts=P, river_line_len=line_len, river_q=Qp, river_ws=ws, river_w=width, river_d=depth,
                        treeline=treeline, slope_deg=slope_deg, relief_std=relief_std, river_mask=river.reshape(z.shape),
                        outwash_belt=ow_belt,
                        river_near=ndimage.binary_dilation(river.reshape(z.shape), iterations=int(math.ceil(250.0 / res))),
                        lake_dist=lake_dist.astype(np.float32), lake_near_level=lake_near_level.astype(np.float32))
    return dict(rivers=len(lines), river_points=int(P.shape[0]),
                treeline_m=round(float(np.median(treeline[(np.abs(xs)[None, :] <= HALF_M) & (np.abs(ys)[:, None] <= HALF_M)])), 0))


# ---------------- one plot ----------------
def build_tile(col, row, prep, step=1, out_dir=None, window=None):
    """window = (row0, row1, col0, col1) in vertex indices, for testing a part of a plot."""
    x0 = -HALF_M + col * TILE_M; y0 = HALF_M - row * TILE_M
    idx = np.arange(0, NV, step)
    if window:
        xv = x0 + np.arange(window[2], window[3], step) * SPACING; yv = y0 - np.arange(window[0], window[1], step) * SPACING
    else:
        xv = x0 + idx * SPACING; yv = y0 - idx * SPACING
    Xw, Yw = np.meshgrid(xv, yv)
    res = float(prep["res"])
    fi = (Xw - prep["x0"]) / res; fj = (prep["y0"] - Yw) / res
    base = ndimage.map_coordinates(prep["spline"], [fj, fi], order=3, prefilter=False)
    slope100 = ndimage.map_coordinates(prep["slope_deg"], [fj, fi], order=1)
    tl = ndimage.map_coordinates(prep["treeline"], [fj, fi], order=1)
    lake_f = ndimage.map_coordinates(prep["lake"].astype(float), [fj, fi], order=1)
    lake_lv = ndimage.map_coordinates(prep["lake_level"], [fj, fi], order=0)
    steep = np.clip((slope100 - 3.0) / 25.0, 0, 1)
    alpine = np.clip((base - tl) / 200.0, 0, 1)
    # continue the regional relief spectrum to smaller scales with the same self-affine law (beta ~ 2):
    # detail amplitude scales with the local relief of the regional model
    rstd = ndimage.map_coordinates(prep["relief_std"], [fj, fi], order=1)
    # valley floors, floodplains and plains stay smooth: damp the detail where the regional surface is gentle
    gentle = np.clip(slope100 / 10.0, 0.12, 1.0)
    amp = DETAIL_C * rstd * gentle * (DETAIL_WAVELENGTHS[0] / 2000.0) ** HURST + AMP_PLAIN * 0.3
    amp = np.where(lake_f > 0.5, 0.0, amp)
    # lake shores are smoothed by waves and shore ice: the fine relief fades out towards the water (within ~150 m),
    # so it cannot dig hollows below the lake level beside the lake
    sd = ndimage.map_coordinates(prep["lake_dist"], [fj, fi], order=1)
    sl_ = ndimage.map_coordinates(prep["lake_near_level"], [fj, fi], order=0)
    amp = amp * np.where(sl_ > -9000, 0.1 + 0.9 * smoothstep(0.0, SHORE_FADE_M, sd), 1.0)
    rocky = np.clip((slope100 - 25.0) / 10.0, 0, 1) + alpine * 0.5
    amp_fine = amp * (FINE_WAVELENGTHS[0] / DETAIL_WAVELENGTHS[0]) ** HURST * \
        (SOIL_FINE_FACTOR + (1 - SOIL_FINE_FACTOR) * np.clip(rocky, 0, 1))
    z = base + fbm(Xw, Yw, amp, np.array(DETAIL_WAVELENGTHS), HURST, SEED) \
             + fbm(Xw, Yw, amp_fine, np.array(FINE_WAVELENGTHS), HURST, SEED + 1)
    # lake shores: the fine relief must not dig dry pits below the water level next to a lake. Within SHORE_M of a
    # lake, shallow hollows below the level (up to SHORE_PIT_M deep: the scale of the fine relief) become flats just
    # above the water, like the wet shore flats of real lakes; deeper ground (e.g. below a moraine dam) is left as it is.
    shore = (sd < SHORE_M) & (sl_ > -9000) & (z < sl_ + SHORE_FLAT_M) & (z > sl_ - SHORE_PIT_M)
    z = np.where(shore & ~((lake_f > 0.5) & (lake_lv > -9000)), sl_ + SHORE_FLAT_M, z)
    # rivers
    near = ndimage.map_coordinates(prep["river_near"].astype(float), [fj, fi], order=0) > 0.5
    riverbed = np.zeros(z.shape); wet = np.zeros(z.shape); gravel = np.zeros(z.shape)
    P = prep["river_pts"]
    sel = (P[:, 0] > xv[0] - 600) & (P[:, 0] < xv[-1] + 600) & (P[:, 1] < yv[0] + 600) & (P[:, 1] > yv[-1] - 600)
    if sel.any() and near.any():
        tr = cKDTree(P[sel])
        qj, qi = np.nonzero(near)
        d, ix = tr.query(np.column_stack([Xw[qj, qi], Yw[qj, qi]]))
        hw = prep["river_w"][sel][ix] / 2; dep = prep["river_d"][sel][ix]; ws = prep["river_ws"][sel][ix] - 0.3
        zc = z[qj, qi]
        inch = d < hw
        bed = ws - dep * (1 - (d / hw) ** 2)
        reach = 3.0 * hw + 30.0                                # banks blend back into the terrain within ~3 widths
        target = ws + 0.8 + 0.15 * np.clip(d - hw, 0, None)  # banks rise ~15% from the water's edge
        t = np.clip((d - hw) / reach, 0, 1)
        wgt = 1 - t * t * (3 - 2 * t)                          # smooth fade, zero at the edge of the bank zone
        cut = np.where(zc > target, (zc - target) * wgt, 0.0)
        zc = np.where(inch, bed, zc - cut)
        z[qj, qi] = zc
        qq = prep["river_q"][sel][ix]
        riverbed[qj, qi] = 1 - smoothstep(hw - 3.0, hw + 1.0, d)            # wet channel, soft water's edge
        bar = np.maximum(2.0, 0.4 * hw)                                      # gravel bars along the banks
        gravel[qj, qi] = np.where(qq >= 3.0, smoothstep(hw - 3.0, hw, d) * (1 - smoothstep(hw + 0.3 * bar, hw + bar + 3.0, d)), 0.0)
        wet[qj, qi] = np.where(qq >= 20.0, smoothstep(hw, hw + 15.0, d) * (1 - smoothstep(hw + 150.0, hw + 230.0, d)), 0.0)  # inside river_near (250 m)
    # lakes
    lk = (lake_f > 0.5) & (lake_lv > -9000)            # nearest regional cell must itself be lake
    z = np.where(lk, np.minimum(z, lake_lv - 1.5), z)
    # lakebed weight: under water, with a soft shoreline (the lake surface is lake_lv)
    lakebed = np.where(lake_lv > -9000, smoothstep(-0.5, 0.5, lake_lv - z) * smoothstep(0.3, 0.6, lake_f), 0.0)
    z = np.clip(z, -2559.9, 2559.9)
    # layers
    gy, gx = np.gradient(ndimage.uniform_filter(z, 3) if step == 1 else z, SPACING * step)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))             # slope over ~9 m (ignores single-vertex bumps)
    if step == 1:
        slope = ndimage.gaussian_filter(slope, 2.0)                 # ~15 m: layer patches, not vertex-by-vertex flicker
    # soft layers, painted bottom to top: each layer covers the ones below by its weight ("over" blending),
    # so the weights always add up to 1
    ones = np.ones(z.shape)
    tl_n = tl + TREELINE_NOISE_M * fbm(Xw, Yw, ones, np.array([400.0, 200.0, 100.0]), HURST, SEED + 2) / 1.6
    alp = smoothstep(tl_n - TREELINE_ECOTONE_M / 2, tl_n + TREELINE_ECOTONE_M / 2, z)
    wf = np.zeros(z.shape + (len(LAYERS),), np.float32)
    wf[..., L_["forest"]] = 1 - alp
    wf[..., L_["alpine_meadow"]] = alp

    def over(name, a):
        a = np.clip(a, 0, 1).astype(np.float32)
        wf[...] *= (1 - a)[..., None]
        wf[..., L_[name]] += a
    over("wet_meadow", wet * (1 - smoothstep(2.0, 5.0, slope)))
    ow = ndimage.map_coordinates(prep["outwash_belt"].astype(float), [fj, fi], order=1)
    over("gravel", np.maximum(gravel, 0.6 * smoothstep(0.3, 0.7, ow) * (1 - smoothstep(3.0, 8.0, slope))))
    # scree accumulates below rock walls near and above the treeline
    over("scree", smoothstep(*SCREE_SLOPE_DEG, slope) * smoothstep(tl - 250.0, tl - 50.0, z))
    over("rock", np.maximum(smoothstep(ROCK_SLOPE_DEG - 5.0, ROCK_SLOPE_DEG + 3.0, slope),
                            smoothstep(tl + 100.0, tl + 250.0, z) * smoothstep(22.0, 28.0, slope)))
    over("riverbed", riverbed)
    over("lakebed", lakebed)
    w8 = to_weights255(wf)
    stats = dict(tile=f"tile_x{col}_y{row}", step=step, min_m=round(float(z.min()), 2), max_m=round(float(z.max()), 2),
                 mean_m=round(float(z.mean()), 2),
                 layers_pct={n: round(float(w8[..., k].mean() / 2.55), 2) for k, n in enumerate(LAYERS)})
    return z, w8, stats


def export_tile(col, row, prep, out_dir, strip=512):
    """Full-resolution plot, built in strips of rows so memory stays below ~3 GB (run one plot per process on
    machines with less than ~8 GB: python detail_plots.py --tiles x0_y0, then the next)."""
    os.makedirs(out_dir, exist_ok=True)
    h16 = np.empty((NV, NV), np.uint16)
    lay = np.empty((NV, NV, len(LAYERS)), np.uint8)
    zsum, zmin, zmax = 0.0, 1e9, -1e9
    for r0 in range(0, NV, strip):
        r1 = min(NV, r0 + strip)
        # HALO-vertex margin on every side (also beyond the plot edge): slopes, and so the layer weights, are then
        # identical on both sides of a strip boundary and of a plot seam
        HALO = 12
        a0, a1 = r0 - HALO, r1 + HALO
        z, layer, _ = build_tile(col, row, prep, step=1, window=(a0, a1, -HALO, NV + HALO))
        z = z[HALO:HALO + (r1 - r0), HALO:HALO + NV]; layer = layer[HALO:HALO + (r1 - r0), HALO:HALO + NV]
        h16[r0:r1] = np.clip(np.round(32768 + z * UNITS_PER_M), 0, 65535).astype(np.uint16)
        lay[r0:r1] = layer
        zsum += float(z.sum()); zmin = min(zmin, float(z.min())); zmax = max(zmax, float(z.max()))
    Image.fromarray(h16).save(os.path.join(out_dir, "heightmap.png"))
    for k, n in enumerate(LAYERS):
        Image.fromarray(np.ascontiguousarray(lay[..., k])).save(os.path.join(out_dir, f"layer_{n}.png"), optimize=True)
    stats = dict(tile=f"tile_x{col}_y{row}", vertices=NV, spacing_m=round(SPACING, 4),
                 min_m=round(zmin, 2), max_m=round(zmax, 2), mean_m=round(zsum / NV / NV, 2),
                 layers_pct={n: round(float(lay[..., k].mean(dtype=np.float64) / 2.55), 2) for k, n in enumerate(LAYERS)},
                 layer_weights="8-bit weight maps, all layers add up to 255 at every vertex",
                 heightmap_encoding=f"value = 32768 + height_m * {UNITS_PER_M} (Unreal Z scale {Z_SCALE})")
    json.dump(stats, open(os.path.join(out_dir, "tile.json"), "w"), indent=1)
    z_prev = (h16[::8, ::8].astype(np.float64) - 32768) / UNITS_PER_M
    return z_prev, lay[::8, ::8], stats


def preview(z, layer, path, step):
    pal = np.array([[150, 140, 130], [185, 180, 165], [175, 190, 120], [70, 115, 65], [140, 175, 110], [200, 190, 160],
                    [180, 165, 130], [80, 130, 190]], float)
    gy, gx = np.gradient(z, SPACING * step)
    nx, ny = -gx * 2, gy * 2
    sh = np.clip((nx * -0.6 + ny * 0.6 + 0.6) / np.sqrt(nx ** 2 + ny ** 2 + 1) / 0.6, 0.3, 1.5)
    rgb = (layer.astype(float) / 255.0) @ pal * sh[..., None]
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    if img.width > 1100:
        img = img.resize((1016, 1016), Image.LANCZOS)
    img.save(path, optimize=True)


def mosaic():
    """All plot previews side by side (MOSAIC_PX wide), north up."""
    nx, ny = CFG["tiles"]["count_x"], CFG["tiles"]["count_y"]
    t = MOSAIC_PX // nx
    img = Image.new("RGB", (t * nx, t * ny), (255, 255, 255))
    for r in range(ny):
        for c in range(nx):
            p = os.path.join(PREVIEWS, f"preview_tile_x{c}_y{r}.png")
            if os.path.exists(p):
                img.paste(Image.open(p).convert("RGB").resize((t, t), Image.LANCZOS), (c * t, r * t))
    img.save(MOSAIC, quality=88)
    return MOSAIC


def parse_tiles(arg):
    if arg == ["all"]:
        return [(c, r) for r in range(CFG["tiles"]["count_y"]) for c in range(CFG["tiles"]["count_x"])]
    out = []
    for t in arg:
        t = t.replace("tile_", "")
        c, r = t.split("_")
        out.append((int(c[1:]), int(r[1:])))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tiles", nargs="+", default=["all"], help="'all' or names like x2_y1 (tile_x2_y1 also works)")
    ap.add_argument("--preview", action="store_true", help="only a 1/8-resolution preview image, no export")
    ap.add_argument("--reprep", action="store_true", help="rebuild the river / lake / treeline preparation file")
    ap.add_argument("--mosaic", action="store_true", help="only rebuild the mosaic of all plot previews")
    args = ap.parse_args()
    if args.mosaic:
        print(mosaic()); sys.exit(0)
    if args.reprep or not os.path.exists(PREP):
        print("preparing rivers, lakes and treeline ...", prepare())
    prep = dict(np.load(PREP))
    for col, row in parse_tiles(args.tiles):
        name = f"tile_x{col}_y{row}"
        if args.preview:
            z, layer, st = build_tile(col, row, prep, step=8)
        else:
            z, layer, st = export_tile(col, row, prep, os.path.join(EXPORT, name))
        os.makedirs(PREVIEWS, exist_ok=True)
        preview(z, layer, os.path.join(PREVIEWS, f"preview_{name}.png"), 8)
        print(json.dumps(st))
    if args.tiles == ["all"]:
        print(mosaic())
