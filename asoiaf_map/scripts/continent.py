"""
Step 4 of the Westeros pipeline: the continental model — all of Westeros on one fine grid (default 500 m).

Every detailed region is cut from this model, so the continent is seamless: large relief, rivers, lakes and the
glacial history are computed here once, for everyone. The steps:
  1. Frame: azimuthal-equidistant grid centred on Westeros (x = east, y = north, metres).
  2. Land: the canon coastline with fractal detail (real coastlines are fractal; detail fades away from the canon line).
  3. Relief: the planet relief (0.25 deg, smoothed); inside the canon mountain regions the canon mountain field (relief
     map outlines and rock texture) on the lowland around them; plus the relief the planet grid cannot resolve (swells
     and basins of 3-50 km, scaled by the local relief), plus the canon river courses with beds that never rise
     downstream (gorges where a course crosses higher ground).
  4. Rivers: 0.5 million years of stream-power erosion and hillslope diffusion with the planet's runoff, on stochastic
     flow paths that start from a rough initial surface (branching networks, no grid-aligned rills); the isostatic
     relaxation restores only the planet scale (> RELAX_SIGMA_M), so valleys, swells and drainage organise themselves.
  5. Last Glacial Maximum: equilibrium line (Ohmura et al. 1992) with the LGM cooling of the latitude; the ice sheet
     spreads from each complex of accumulation zones over the adjacent land, the coldest ground first, until the
     accumulation area is ICE_AAR of the ice area (the accumulation-area method of valley glaciers, with an ice-sheet
     AAR); its bed is scoured
     (small relief planed, rock basins).
  6. Today: lakes (closed basins at their spill level), rivers and their discharge.

Usage:   python continent.py [--dx 500]
Outputs: ../output/continent.npz (not in Git), continent.json, continent_map.png
"""
import argparse, json, math, os, time
import numpy as np
from matplotlib.path import Path
from scipy import ndimage
from PIL import Image
import canon_geography as cg
from flow import accumulate, diffuse, grow_coldest_first, priority_flood, route, stream_power

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--dx", type=float, default=500.0, help="grid spacing in metres (default 500; 250 needs ~4x the memory)")
args = ap.parse_args()

# ---------------- parameters ----------------
DX = args.dx
MARGIN_M = 60e3                          # sea around the continent
# fractal coast: the coastline is the level set of (signed distance to the canon coast + fBm noise); a level set of a
# self-affine surface with Hurst exponent H has fractal dimension ~2 - H (Mandelbrot), real coasts 1.1-1.5 (Britain's
# west coast ~1.25, Norway ~1.5). Noise std at wavelength L: COAST_NOISE_KM * (L / 100 km)^COAST_HURST
COAST_NOISE_KM, COAST_HURST = 20.0, 0.6
COAST_OCTAVES_KM = (6.25, 3.1, 1.6)      # the outline itself (digitised map) carries the forms above ~6 km
COAST_FADE_KM = 60.0                     # the noise fades out this far from the canon coast
COAST_PLACE_KM = 8.0                     # coastal canon places stay on the coast: noise damped within ~this distance
ISLAND_ZONE_KM = 20.0                    # near an island each noise octave's std is limited to 1/12 of its half-width
ISLAND_SHELF = (60.0, 6.0)               # sea floor around islands: -60 m at the coast, 6 m deeper per km (a shelf)
ISLAND_RELIEF = (12.0, 800.0)            # island summits: 12 m x sqrt(area km2), at most 800 m (Hebrides, Orkney, Channel Islands: 100-800 m)
HIERARCHY = ((10.0, 0.15, 3e3), (100.0, 0.3, 12e3), (1000.0, 0.55, 50e3))   # (stream size m3/s, share of the relief, e-folding distance m)
SUBGRID_AMP = (150.0, 0.5)
SUBGRID_STD_CAP = 400.0                  # m: relief std above which the sub-grid relief grows no further
BASE_WINDOW_M = 300e3                    # the lowland base under a range: lowest land within ~150 km
MASSIF_KM = 50.0                         # massifs and passes within the canon mountain regions (ridged noise)
ROUGH_SHARE, ROUGH_BASE_KM = 0.14, 40.0  # initial self-affine roughness (40 ... 2.5 km), share of the local relief amplitude
EROSION_YR, EROSION_DT = 0.5e6, 2.5e4    # short steps: the stochastic flow paths change between steps
K_SP, M_SP, D_HILL = 1.0e-6, 0.5, 0.01   # stream-power K (m^(1-2m)/yr), m; hillslope diffusivity (m2/yr)
RELAX, RELAX_SIGMA_M = 0.5, 20e3         # isostatic relaxation of scales above RELAX_SIGMA_M towards the planet relief + swells
CANON_VALLEY = (25.0, 8000.0)            # depth (m) and width (m) of the canon river valleys given before the erosion
CANON_GORGE_SLOPE = 0.08                 # valley sides of the canon rivers' beds (~4.6 deg)
CANON_BED_SLOPE = 0.006                  # steepest mean bed gradient of a canon river (6 m/km: mountain rivers 2-10 m/km)
CANON_MIN_SLOPE = 0.0002                 # gentlest bed gradient (0.2 m/km, lowland rivers)
CANON_WANDER = ((10e3, 400.0),)          # (wavelength m, amplitude m): bends below the map's resolution (the digitised
                                         # rivers carry the larger meanders themselves)
LAPSE = 0.0065
LGM_COOLING_GLOBAL, LGM_COOLING_POLAR = 6.0, 14.0      # Tierney et al. 2020
OHMURA = (645.0, 296.0, 9.0)
ICE_AAR = 0.7                            # accumulation-area ratio of an ice sheet (large ice sheets ~0.6-0.9)
SCOUR_KEEP, ROCK_BASIN_M = 0.6, 6.0      # ice-sheet bed: share of relief < ~3 km kept; depth of plucked rock basins
LAKE_MIN_DEPTH_M = 2.0

t0 = time.time()


# ---------------- 1. frame ----------------
from frame import CENTRE, R_M, xy_to_latlon, latlon_to_xy


cx, cy = latlon_to_xy(*cg.to_latlon(*np.array(cg.COAST, float).T))
x0, x1 = cx.min() - MARGIN_M, cx.max() + MARGIN_M
y0, y1 = cy.min() - MARGIN_M, cy.max() + MARGIN_M
xs = np.arange(math.floor(x0 / DX) * DX + DX / 2, x1, DX)
ys = np.arange(math.ceil(y1 / DX) * DX - DX / 2, y0, -DX)          # row 0 = north
H, W = ys.size, xs.size
print(f"grid {W} x {H} = {H * W / 1e6:.1f} M cells at {DX:.0f} m", flush=True)


def grid_xy(rows=slice(None)):
    return np.meshgrid(xs, ys[rows])


FBM_WAVES = 16                           # plane waves per octave (fewer give a visibly regular, cellular pattern)


def fbm(seed, base_km, octaves, amp, gain=0.55, block=1024):
    """Plane-wave fBm on the frame's metres (seamless, depends on position only); std ~ amp / 2 for one octave."""
    r = np.random.default_rng(seed)
    waves = []
    for o in range(octaves):
        k = 2 * math.pi / (base_km * 1000 / 2 ** o); a = gain ** o
        for _ in range(FBM_WAVES):
            th = r.uniform(0, math.pi)
            waves.append((k * math.cos(th), k * math.sin(th), r.uniform(0, 2 * math.pi), a))
    norm = math.sqrt(2 * sum(w[3] ** 2 for w in waves))          # output std ~ amp / 2
    out = np.empty((H, W), np.float32)
    for j0 in range(0, H, block):
        X, Y = grid_xy(slice(j0, j0 + block))
        acc = np.zeros(X.shape)
        for kx, ky, ph, a in waves:
            acc += a * np.sin(kx * X + ky * Y + ph)
        out[j0:j0 + block] = acc / norm * amp
    return out


def rows_latlon(fn, block=1024):
    """Evaluate fn(lat, lon) on the grid in row blocks (keeps memory low)."""
    out = None
    for j0 in range(0, H, block):
        X, Y = grid_xy(slice(j0, j0 + block))
        v = fn(*xy_to_latlon(X, Y))
        if out is None:
            out = np.empty((H, W), v.dtype)
        out[j0:j0 + block] = v
    return out


def sample_world(field, order=1):
    Hw, Ww = field.shape
    f = np.concatenate([field[:, -4:], field, field[:, :4]], axis=1).astype(np.float64)

    def fn(lat, lon):
        return ndimage.map_coordinates(f, [(90 - lat) / 180 * Hw - 0.5, (lon + 180) / 360 * Ww - 0.5 + 4], order=order,
                                       mode="nearest").astype(np.float32)
    return rows_latlon(fn)


# ---------------- 2. land ----------------
def poly_mask(px, py):
    path = Path(np.column_stack([px, py]))
    out = np.zeros((H, W), bool)
    for j0 in range(0, H, 512):
        X, Y = grid_xy(slice(j0, j0 + 512))
        out[j0:j0 + 512] = path.contains_points(np.column_stack([X.ravel(), Y.ravel()])).reshape(X.shape)
    return out


def window(px, py, margin_m):
    """Grid slices of the box around (px, py) plus a margin."""
    j0 = max(0, int((ys[0] - py.max() - margin_m) / DX)); j1 = min(H, int((ys[0] - py.min() + margin_m) / DX) + 2)
    i0 = max(0, int((px.min() - margin_m - xs[0]) / DX)); i1 = min(W, int((px.max() + margin_m - xs[0]) / DX) + 2)
    return slice(j0, j1), slice(i0, i1)


land0 = poly_mask(cx, cy)
# islands: each its own outline; the fractal coast noise is scaled down with the island's size (a +-9 km wobble would
# merge or drown islands a few km across), within ISLAND_ZONE_KM of the island
half_w = np.full((H, W), np.inf, np.float32)    # half-width (km) of the nearest island, within ISLAND_ZONE_KM
island_masks = {}                                # name: (window slices, mask in the window)
for iname, spec in cg.ISLANDS.items():
    ix, iy = latlon_to_xy(*cg.to_latlon(*cg.island_ring(spec)))
    sl_ = window(ix, iy, ISLAND_ZONE_KM * 1000 + 2 * DX)
    Xw, Yw = np.meshgrid(xs[sl_[1]], ys[sl_[0]])
    m_ = Path(np.column_stack([ix, iy])).contains_points(np.column_stack([Xw.ravel(), Yw.ravel()])).reshape(Xw.shape)
    island_masks[iname] = (sl_, m_)
    land0[sl_] |= m_
    zone = ndimage.distance_transform_edt(~m_) * DX < ISLAND_ZONE_KM * 1000
    hw_ = half_w[sl_]; hw_[zone] = np.minimum(hw_[zone], cg.island_halfwidth(spec) * cg.SCALE)
sd = (ndimage.distance_transform_edt(land0) - ndimage.distance_transform_edt(~land0)) * DX / 1000.0   # km, + inland
coast_n = np.zeros((H, W), np.float32)
for k_, lam in enumerate(COAST_OCTAVES_KM):
    sig = COAST_NOISE_KM * (lam / 100.0) ** COAST_HURST
    coast_n += fbm(101 + k_, lam, 1, 2 * sig) * np.minimum(1.0, half_w / (12 * sig))
# coastal canon places (ports, sea castles) keep the canon coast around them
near_place = np.zeros((H, W), bool)
for pname, (px_, py_) in cg.PLACES.items():
    gx_, gy_ = latlon_to_xy(*cg.to_latlon(px_, py_))
    j_, i_ = int(round((ys[0] - gy_) / DX)), int(round((gx_ - xs[0]) / DX))
    if 0 <= j_ < H and 0 <= i_ < W and abs(sd[j_, i_]) < 10.0:
        near_place[j_, i_] = True
damp = 1 - np.exp(-((ndimage.distance_transform_edt(~near_place) * DX / 1000.0) / COAST_PLACE_KM) ** 2)
land = (sd + coast_n * damp * np.clip(1 - np.abs(sd) / COAST_FADE_KM, 0, 1)) > 0
del half_w, near_place, damp
land = ndimage.binary_opening(land, iterations=1)
lab, nl = ndimage.label(land)
sizes = ndimage.sum(land, lab, range(1, nl + 1))
land = np.isin(lab, 1 + np.nonzero(sizes * DX * DX / 1e6 >= 2.0)[0])        # drop islets < 2 km2
del sd, coast_n, lab
print(f"land {land.mean() * H * W * DX * DX / 1e6:,.0f} km2, {time.time() - t0:.0f} s", flush=True)

# ---------------- 3. relief ----------------
Hy = np.load(os.path.join(OUT, "world_hydrology.npz")); Cl = np.load(os.path.join(OUT, "world_climate.npz"))
planet = sample_world(Hy["elevation_eroded_m"], 3)
planet = ndimage.gaussian_filter(planet, 10e3 / DX).astype(np.float32)
# the canon mountain regions at the continental resolution: inside them the relief is the canon field (outline,
# foothills, a rise to the core, the rock texture of the relief map, massifs of ~50 km) standing on the lowland base
# around them; the planet grid (~28 km) gave their mass to the climate only
mfield = np.empty((H, W), np.float32)
for j0 in range(0, H, 512):
    X, Y = grid_xy(slice(j0, j0 + 512))
    ckx, cky = cg.from_latlon(*xy_to_latlon(X, Y))
    wm_, hm_ = cg.mountain_field(ckx, cky)
    mfield[j0:j0 + 512] = wm_ * hm_
mfield *= (0.5 + 0.5 * np.clip(1 - np.abs(fbm(241, MASSIF_KM, 3, 1.0)), 0, 1) ** 2).astype(np.float32)
rw = sample_world(np.load(os.path.join(OUT, "world_canon.npz"))["range_weight"], 1)
zone = land & ((rw > 0.05) | (mfield > 0))
# the lowland the ranges stand on: the lower envelope of the land relief (lowest level within ~150 km, smoothed)
ice_ = sample_world(np.load(os.path.join(OUT, "world_canon.npz"))["ice_sheet_m"], 1) > 50      # (bedrock, not ice surface)
k_ = max(1, int(5e3 / DX))                                                    # on a 5 km grid
lo_ = np.where(land & ~ice_, planet, 1e4).astype(np.float32)[::k_, ::k_]
lo_ = ndimage.minimum_filter(lo_, size=int(BASE_WINDOW_M / (k_ * DX)) | 1)
lo_ = ndimage.gaussian_filter(np.where(lo_ > 9e3, 5.0, lo_), 30e3 / (k_ * DX))
base = ndimage.zoom(lo_, (H / lo_.shape[0], W / lo_.shape[1]), order=1)[:H, :W]
del ice_, lo_
base = np.clip(base, 5.0, None)
planet = np.where(zone, np.minimum(np.maximum(planet, base), base) + mfield, planet).astype(np.float32)
del mfield, rw, zone, base
win = int(100e3 / DX) | 1
pl_ = np.maximum(planet, 0).astype(np.float64)             # land relief only (the sea floor is not mountain relief)
pm = ndimage.uniform_filter(pl_, win); pm2 = ndimage.uniform_filter(pl_ ** 2, win)
del pl_
relief_std = np.sqrt(np.clip(pm2 - pm * pm, 0, None)).astype(np.float32)
del pm, pm2
trend = np.where(land, np.maximum(planet, 5.0), np.minimum(planet, -10.0)).astype(np.float32)
# coasts reach sea level: blend the planet relief to 5 m within ~15 km of the (fractal) coast
dco = ndimage.distance_transform_edt(land) * DX
trend = np.where(land, 5 + (trend - 5) * np.clip(dco / 15e3, 0, 1) ** 0.7, trend).astype(np.float32)
del planet, dco
amp = (SUBGRID_AMP[0] + SUBGRID_AMP[1] * np.minimum(relief_std, SUBGRID_STD_CAP)).astype(np.float32)   # (the canon mountain field carries the large relief)
# islands smaller than the planet grid have no planet relief: a dome rising from the coast, higher on larger islands
lumps_all = fbm(221, 12.0, 2, 0.74)
isl_all = np.zeros((H, W), bool)
for iname, (sl_, m_) in island_masks.items():
    m_ = m_ & land[sl_]
    if not m_.any():
        continue
    isl_all[sl_] |= m_
    di = ndimage.distance_transform_edt(m_)
    h_ = min(ISLAND_RELIEF[1], ISLAND_RELIEF[0] * math.sqrt(m_.sum() * DX * DX / 1e6))
    lumps = 0.55 + 0.45 * np.clip(lumps_all[sl_] * 0.5 + 0.5, 0, 1)                 # summits and saddles
    dome = h_ * np.sqrt(di / max(di.max(), 1)) * lumps
    trend[sl_] = np.where(m_, np.maximum(trend[sl_], dome), trend[sl_])
d_isl = ndimage.distance_transform_edt(~isl_all) * DX / 1000.0
shelf = -(ISLAND_SHELF[0] + ISLAND_SHELF[1] * d_isl)
trend = np.where(~land & (d_isl < ISLAND_ZONE_KM), np.maximum(trend, shelf), trend).astype(np.float32)
del island_masks, isl_all, d_isl, shelf, lumps_all

# canon river valleys (the digitised courses, with small bends below the map resolution)
canon_line = np.zeros((H, W), bool)
canon_paths = []                                 # cells of each canon river, source to mouth
for k, (rname, pts) in enumerate(cg.RIVERS.items()):
    p = np.array(pts, float)
    rx, ry = latlon_to_xy(*cg.to_latlon(*p.T))
    s = np.r_[0, np.cumsum(np.hypot(np.diff(rx), np.diff(ry)))]
    t = np.arange(0, s[-1], DX / 2)
    rx, ry = np.interp(t, s, rx), np.interp(t, s, ry)
    tx, ty = np.gradient(rx), np.gradient(ry); tn = np.hypot(tx, ty) + 1e-9
    rng = np.random.default_rng(300 + k)
    off = sum(a_ * np.sin(2 * np.pi * t / lam_ + rng.uniform(0, 6.3)) for lam_, a_ in CANON_WANDER)
    off *= np.clip(t / 5e3, 0, 1) * np.clip((t[-1] - t) / 5e3, 0, 1)       # source and mouth stay on their control points
    rx, ry = rx - off * ty / tn, ry + off * tx / tn
    ci = ((rx - xs[0]) / DX).round().astype(int); cj = ((ys[0] - ry) / DX).round().astype(int)
    ok = (ci >= 0) & (ci < W) & (cj >= 0) & (cj < H)
    canon_line[cj[ok], ci[ok]] = True
    canon_paths.append((cj[ok], ci[ok]))
dcan = ndimage.distance_transform_edt(~canon_line) * DX
valley = (CANON_VALLEY[0] * np.exp(-(dcan / (CANON_VALLEY[1] / 2)) ** 2) * land).astype(np.float32)
runoff = np.clip(sample_world(Hy["runoff_mm"], 1), 0, None) / 1000.0
# today's ice sheet (Land of Always Winter) loses its mass as glacier ice to the sea, not as rivers
ice_now = sample_world(np.load(os.path.join(OUT, "world_canon.npz"))["ice_sheet_m"], 1) > 50
runoff = np.where(ice_now, 0.0, runoff)
q_cell = (np.where(land, runoff, 0) * DX * DX).ravel()
sea = ~land
# relief below the planet grid, organised by the drainage network: valleys deepen and widen with the size of their
# river (Horton hierarchy: streams >= 10, 100, 1000 m3/s), interfluves rise between them; no closed basins arise and
# the spacing of the river hierarchy gives relief at all scales between ~3 and ~100 km
# plus initial self-affine roughness, so that the drainage organises into branching networks instead of following the
# smooth planet slopes in parallel lines
# (smooth along the canon rivers, whose shallow valleys must guide the drainage)
rough = ROUGH_SHARE * amp * fbm(211, ROUGH_BASE_KM, 5, 1.0) * np.clip(dcan / 15e3, 0, 1)
z0 = np.where(land, trend - valley + rough, trend).astype(np.float64)
del rough, dcan
f, rec, dist, oa, od = route(z0, sea, DX, seed=999)     # stochastic paths: no grid-straight valleys
Q0 = (accumulate(od, rec, q_cell) / 3.15576e7).reshape(H, W)
del f, rec, dist, oa, od
drel = np.zeros((H, W), np.float32)
for qmin, share, L in HIERARCHY:
    d = ndimage.distance_transform_edt(~((Q0 >= qmin) & land)) * DX
    drel += (share * (1 - np.exp(-d / L))).astype(np.float32)
del Q0, d
drel = drel * amp * land
target = (z0 + drel).astype(np.float32)                      # what the isostatic relaxation restores
# canon rivers keep their course: along each river the bed never rises downstream (where the course crosses higher
# ground the river has cut a gorge through it - antecedent or superimposed drainage, as the Indus, the Columbia or the
# water gaps of the Appalachians); valley sides rise from the bed at CANON_GORGE_SLOPE
def carve_canon_beds(surf, skip=None):
    """Lower `surf` along the canon rivers: beds that never rise downstream and fall towards the mouth at least at
    CANON_BED_SLOPE; valley sides at CANON_GORGE_SLOPE. Cells in `skip` (lakes) neither lower the bed nor are cut."""
    bed = np.full((H, W), np.inf, np.float32)
    for cj_, ci_ in canon_paths:
        if cj_.size < 2:
            continue
        zl = surf[cj_, ci_].astype(np.float64)
        sk = skip[cj_, ci_] if skip is not None else np.zeros(cj_.size, bool)
        zl = np.where(sk, np.inf, ndimage.uniform_filter1d(zl, 5))
        b_ = np.minimum.accumulate(zl) - CANON_VALLEY[0]
        # never flat: a river always falls a little (lowland rivers 0.1-0.3 m/km)
        ds_ = np.r_[0, np.hypot(np.diff(cj_), np.diff(ci_))] * DX
        for k_ in range(1, len(b_)):
            if np.isfinite(b_[k_]) and np.isfinite(b_[k_ - 1]):
                b_[k_] = min(b_[k_], b_[k_ - 1] - CANON_MIN_SLOPE * ds_[k_])
        # ... and falls towards its mouth at least as steeply as a river crossing a range must: the gorge, not a flat
        # bed held up by the mountains
        for k_ in range(len(b_) - 2, -1, -1):
            b_[k_] = min(b_[k_], b_[k_ + 1] + CANON_BED_SLOPE * ds_[k_ + 1])
        ok_ = np.isfinite(b_) & ~sk
        bed[cj_[ok_], ci_[ok_]] = np.minimum(bed[cj_[ok_], ci_[ok_]], np.maximum(b_[ok_], 1.0))
    has = np.isfinite(bed) & land
    dist_, (ij_, ii_) = ndimage.distance_transform_edt(~has, return_indices=True)
    cut = bed[ij_, ii_] + CANON_GORGE_SLOPE * dist_ * DX
    del dist_, ij_, ii_
    keep = ~land if skip is None else (~land | skip)
    return np.where(keep, surf, np.minimum(surf, cut)).astype(surf.dtype)


target = carve_canon_beds(target)
# canon lakes: closed basins whose floor lies below the lowest point of their rim
canon_lake_zone = np.zeros((H, W), bool)
for lname, ((lcx, lcy), (lax, lay)) in cg.LAKES.items():
    t_ = np.linspace(0, 2 * np.pi, 144, endpoint=False)
    rng_l = np.random.default_rng(500 + len(lname))
    # natural shores: the canon ellipse with bays and points (radius varies by up to ~+-25 %)
    rad = 1 + sum(a_ * np.sin(k_ * t_ + rng_l.uniform(0, 6.3)) for k_, a_ in ((2, 0.08), (3, 0.07), (5, 0.05), (8, 0.04), (13, 0.025)))
    ex, ey = latlon_to_xy(*cg.to_latlon(lcx + lax * rad * np.cos(t_), lcy + lay * rad * np.sin(t_)))
    mx, my = latlon_to_xy(*cg.to_latlon(lcx, lcy))
    ja, jb = int((ys[0] - ey.max()) / DX) - 20, int((ys[0] - ey.min()) / DX) + 21
    ia, ib = int((ex.min() - xs[0]) / DX) - 20, int((ex.max() - xs[0]) / DX) + 21
    Xl, Yl = np.meshgrid(xs[ia:ib], ys[ja:jb])
    rr = Path(np.column_stack([ex, ey])).contains_points(np.column_stack([Xl.ravel(), Yl.ravel()])).reshape(Xl.shape)
    if not rr.any():
        rr = np.hypot(Xl - mx, Yl - my) <= DX
    ring_ = ndimage.binary_dilation(rr, iterations=6) & ~rr
    rim = float(target[ja:jb, ia:ib][ring_].min())
    dc = ndimage.distance_transform_edt(rr) * DX; dc = dc / max(dc.max(), 1)
    target[ja:jb, ia:ib] = np.where(rr, np.minimum(target[ja:jb, ia:ib], rim - 5 - 40 * dc), target[ja:jb, ia:ib])
    canon_lake_zone[ja:jb, ia:ib] |= ndimage.binary_dilation(rr, iterations=4)
z = target.astype(np.float64)
del drel, relief_std, z0
print(f"relief ready, {time.time() - t0:.0f} s", flush=True)

# ---------------- 4. rivers ----------------
for step in range(int(EROSION_YR / EROSION_DT)):
    f, rec, dist, oa, od = route(z, sea, DX, seed=1000 + step)      # stochastic flow paths (see flow.receivers_random)
    Q = accumulate(od, rec, q_cell)
    zf = stream_power(z.ravel().copy(), oa, rec, dist, Q, K_SP, M_SP, EROSION_DT, sea.ravel())
    del f, oa, od, Q
    z = diffuse(zf.reshape(H, W), D_HILL, EROSION_DT, DX, sea, 1)
    # relax the large-scale departure from the target (smoothing the departure, not the surface: smoothing the surface
    # mixes the sea floor into small islands and coasts and would lift them without limit)
    misfit = -ndimage.gaussian_filter(z - target, RELAX_SIGMA_M / DX)
    z = np.where(sea, z, z + RELAX * misfit)
    if (step + 1) % 5 == 0:
        print(f"erosion step {step + 1}/{int(EROSION_YR / EROSION_DT)}: {time.time() - t0:.0f} s", flush=True)
del target, misfit

# a river landscape has no closed depressions: the pits left by the rough initial surface are filled (lakes silt up,
# low sills are cut through); only the canon lake basins stay. Glacial lakes are made below, on the LGM ice bed.
z = np.where(canon_lake_zone | sea, z, priority_flood(z, sea | canon_lake_zone, 1e-3))

# ---------------- 5. Last Glacial Maximum ----------------
T_jul = sample_world(Cl["temp_jul_c"], 3); T_jan = sample_world(Cl["temp_jan_c"], 3); P = sample_world(Cl["precip_annual_mm"], 3)
LAT = rows_latlon(lambda la, lo: la.astype(np.float32))
# (float32 throughout: this section holds many continental fields at once)
z0p = np.maximum(z, 0).astype(np.float32)
dz = z0p - np.maximum(sample_world(Hy["elevation_eroded_m"], 1), 0)          # temperatures to the fine grid's heights
cool = (LGM_COOLING_GLOBAL + (LGM_COOLING_POLAR - LGM_COOLING_GLOBAL) * (np.abs(LAT) - 30) / 60).astype(np.float32)
a_, b_, c_ = OHMURA
t_ela = ((-b_ + np.sqrt(b_ * b_ - 4 * c_ * (a_ - P))) / (2 * c_)).astype(np.float32)
ela_lgm = (z0p + (T_jul - LAPSE * dz - cool - t_ela) / LAPSE).astype(np.float32)
del t_ela
accum = land & (z0p > ela_lgm)
T_lgm = ((T_jul + T_jan) / 2 - LAPSE * dz - cool).astype(np.float64)   # (the heap in flow.py is float64)
del dz, cool, z0p
# each ice complex (accumulation zones closer than ~20 km to each other) spreads over the adjacent land, the coldest
# ground first, until its accumulation area is ICE_AAR of its whole area
complexes, nc = ndimage.label(ndimage.binary_dilation(accum, iterations=max(1, int(10e3 / DX))) & land)
ice_lgm = accum.copy()
sizes = ndimage.sum(accum, complexes, range(1, nc + 1))
for c_id in np.argsort(-sizes) + 1:
    seed_ = accum & (complexes == c_id)
    if seed_.sum() * DX * DX / 1e6 < 50:                # tiny ice caps: no ice sheet
        continue
    grown = grow_coldest_first(T_lgm, seed_, land & ~ice_lgm, int(seed_.sum() / ICE_AAR))
    ice_lgm |= grown
ice_margin_t = float(np.percentile(T_lgm[ice_lgm & ~accum], 99)) if (ice_lgm & ~accum).any() else float("nan")
# ice-sheet bed: relief smaller than ~3 km planed down, rock basins plucked along the flow (flow away from the
# accumulation zones: down the gradient of the distance to them)
if ice_lgm.any():
    d_acc = ndimage.distance_transform_edt(~accum) * DX
    gy_, gx_ = np.gradient(ndimage.gaussian_filter(d_acc, 20e3 / DX))
    zs = ndimage.gaussian_filter(z, 3e3 / DX / 2)
    z = np.where(ice_lgm & ~accum, np.minimum(z, zs + SCOUR_KEEP * (z - zs)), z)     # ice erodes: ridges lowered, valleys kept
    flow_az = np.degrees(np.arctan2(gx_, -gy_)) % 360                 # towards increasing distance (x east, rows south)
    basins = fbm(401, 6.0, 2, 0.74) * fbm(402, 2.5, 2, 0.74)            # patchy, km-scale
    z = np.where(ice_lgm & ~accum, z - ROCK_BASIN_M * np.clip((basins - 0.05) / 0.2, 0, 1), z)
    del d_acc, gy_, gx_, zs, basins
else:
    flow_az = np.zeros((H, W), np.float32)

# the canon rivers once more on the final surface: erosion and the ice may have shifted a valley by a few km off the
# canon course, or left a sill on it; the rivers keep cutting their beds (the same gorge rule; canon lakes untouched)
z = carve_canon_beds(z, skip=canon_lake_zone)
del canon_lake_zone, canon_paths

# ---------------- 6. today: lakes, rivers ----------------
f = priority_flood(z, sea, 0.0)
lake = land & ((f - z) > LAKE_MIN_DEPTH_M)
lab, n = ndimage.label(land & ((f - z) > 0.01))
deep = np.zeros(n + 1, bool); deep[np.unique(lab[lake])] = True; deep[0] = False
lake = deep[lab]                                                # whole basins of the lakes, at their spill level
lake_level = np.where(lake, f, np.nan).astype(np.float32)
del lab
f2, rec, dist, oa, od = route(z, sea, DX)
Qd = (accumulate(od, rec, q_cell) / 3.15576e7).reshape(H, W).astype(np.float32)
del f2, oa, od, dist

# ---------------- outputs ----------------
np.savez_compressed(os.path.join(OUT, "continent.npz"), x_m=xs.astype(np.float32), y_m=ys.astype(np.float32),
                    centre_latlon=np.array(CENTRE), dx_m=DX, elevation_m=z.astype(np.float32), land=land, lake=lake,
                    lake_level_m=lake_level, discharge_m3s=Qd, receiver=rec.reshape(H, W).astype(np.int64),
                    ice_lgm=ice_lgm, accumulation_lgm=accum, ela_lgm_m=ela_lgm, ice_flow_azimuth_deg=flow_az.astype(np.float32),
                    canon_river=canon_line, ice_now=ice_now, runoff_mm=(runoff * 1000).astype(np.float32),
                    temp_jul_c=T_jul.astype(np.float32), temp_jan_c=T_jan.astype(np.float32), precip_mm=P.astype(np.float32))
A_ = DX * DX / 1e6
stats = dict(dx_m=DX, cells=int(H * W), size_km=[round(W * DX / 1000), round(H * DX / 1000)], centre=CENTRE,
             land_km2=round(float(land.sum() * A_)), lake_km2=round(float(lake.sum() * A_)),
             ice_lgm_km2=round(float(ice_lgm.sum() * A_)), accumulation_lgm_km2=round(float(accum.sum() * A_)),
             ice_margin_lgm_mean_annual_t_c=round(ice_margin_t, 1),
             ice_sheet_south_lat=round(float(np.percentile(LAT[ice_lgm & ~accum], 1)), 2) if (ice_lgm & ~accum).any() else None,
             highest_m=round(float(z[land].max())), mean_land_m=round(float(z[land].mean())),
             largest_discharge_m3s=round(float(Qd[land].max())), seconds=round(time.time() - t0))
json.dump(stats, open(os.path.join(OUT, "continent.json"), "w"), indent=1)

# map (1/20 resolution)
s_ = max(1, int(5000 / DX))
zz = z[::s_, ::s_]; ll = land[::s_, ::s_]
stops = [(-4000, (20, 40, 90)), (0, (90, 140, 200)), (1, (70, 120, 70)), (300, (120, 160, 90)), (800, (190, 180, 120)),
         (1600, (150, 120, 90)), (2600, (240, 240, 240))]
rgb = np.stack([np.interp(zz, [a for a, _ in stops], [c[i] for _, c in stops]) for i in range(3)], -1)
gy, gx = np.gradient(zz); rgb *= np.clip(1 + (gx - gy) / 150, 0.6, 1.4)[..., None]
rgb[(Qd[::s_, ::s_] > 50) & ll] = (40, 90, 220)
rgb[lake[::s_, ::s_]] = (60, 120, 210)
rgb[(ice_lgm[::s_, ::s_]) & ll] = rgb[(ice_lgm[::s_, ::s_]) & ll] * 0.75 + np.array([255, 255, 255]) * 0.25
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "continent_map.png"), optimize=True)
print(json.dumps(stats, indent=1))
