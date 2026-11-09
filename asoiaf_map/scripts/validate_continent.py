"""
Checks of the continental model (continent.py).

  * science - compared with Earth data (must all pass);
  * canon   - compared with the canon geography (reported; a canon check that is not met marks a canon feature the
              science does not support).

Usage:  python validate_continent.py
Writes ../output/VALIDATION_CONTINENT.md and ../output/validation_continent.json; exits with code 1 if a science check fails.
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage
import canon_geography as cg
from matplotlib.path import Path
from frame import latlon_to_xy, xy_to_latlon

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "VALIDATION_CONTINENT.md")
SOURCES = {
    "hypsometry": ("Mean elevation of the continents ~840 m; Europe ~300 m, North America ~720 m", "https://www.ngdc.noaa.gov/mgg/global/etopo1_surface_histogram.html"),
    "spectrum": ("Topography transect spectra ~k^-2 at landscape scales (Perron, Kirchner & Dietrich 2008, JGR 113, F04003)", "https://doi.org/10.1029/2007JF000866"),
    "lakes": ("Verpoorter et al. 2014: lakes cover ~3.7% of non-glaciated land, more in formerly glaciated terrain", "https://hal.archives-ouvertes.fr/hal-01066344"),
    "ice": ("LGM ice-sheet margins on Earth: Laurentide ~40 N, Fennoscandian ~52 N, Barents-Kara (W Siberia) ~61-62 N (Hughes et al. 2016, DATED-1, Boreas 45)", "https://doi.org/10.1111/bor.12142"),
    "coast": ("Mandelbrot 1967, How long is the coast of Britain? (Science 156): D ~1.25 for the west coast of Britain; "
              "Feder 1988, Fractals: Norway ~1.52", "https://doi.org/10.1126/science.156.3775.636"),
    "mountains": ("Kapos et al. 2000, Developing a map of the world's mountain forests (UNEP-WCMC): mountains ~24 % of the land",
                  "https://www.unep-wcmc.org/resources-and-data/mountains-and-forests-in-mountains"),
    "isotropy": ("Natural relief has no preferred directions tied to a grid; D8 flow routing is known to imprint them "
                 "(Tarboton 1997, WRR 33)", "https://doi.org/10.1029/96WR03137"),
    "canon": ("canon_geography.py", "../scripts/canon_geography.py"),
}
checks = []


def check(kind, name, value, ref, lo, hi, unit, src, note=""):
    checks.append(dict(kind=kind, name=name, value=value if isinstance(value, bool) else round(float(value), 3), reference=ref,
                       band=[lo, hi], unit=unit, source=src, passed=bool(lo <= value <= hi), note=note))


C = np.load(os.path.join(OUT, "continent.npz"))
z = C["elevation_m"]; land = C["land"]; lake = C["lake"]; Q = C["discharge_m3s"]; xs = C["x_m"]; ys = C["y_m"]
dx = float(C["dx_m"]); A = dx * dx / 1e6


def cell(xm, ym):
    return int(round((ys[0] - ym) / dx)), int(round((xm - xs[0]) / dx))


# ---------------- science ----------------
check("science", "Mean land elevation", float(z[land].mean()), "~840 m continents; 300-720 m Europe / North America", 250, 1000, "m", "hypsometry")
check("science", "Highest summit", float(z[land].max()), "canon ranges are Alpine to Pyrenean (Mont Blanc 4.8 km, Aneto 3.4 km)",
      2500, 5500, "m", "hypsometry")
# lakes are a glacial landform: the Earth average (3.7 % of non-glaciated land) mixes lake-rich formerly glaciated shields
# (Finland ~10 %, Sweden ~9 %, the glaciated North German plain ~2 %) with lake-poor river landscapes
bed = land & C["ice_lgm"] & ~C["accumulation_lgm"] & ~C["ice_now"]
off = land & ~C["ice_lgm"]
check("science", "Lake share on the former LGM ice-sheet bed", 100 * float(lake[bed].mean()),
      "Finland ~10 %, Sweden ~9 %, North German plain ~2 %", 2, 15, "%", "lakes", f"{bed.sum() * A:,.0f} km2 of bed")
check("science", "Lake share beyond the LGM ice", 100 * float(lake[off].mean()), "river landscapes: few lakes", 0, 3, "%", "lakes")
lat_ice = None
if C["ice_lgm"].any():
    # the ice sheet of the North: LGM ice masses of >= 50 000 km2 centred north of 50 N (the separate ice cap of the
    # Mountains of the Moon, ~45 N, is a mountain ice field like the Alps' ~150 000 km2 at the LGM)
    lab_, n_ = ndimage.label(C["ice_lgm"])
    sz_ = ndimage.sum(C["ice_lgm"], lab_, range(1, n_ + 1)) * A
    keep_ = []
    for k_ in np.nonzero(sz_ >= 50000)[0] + 1:
        jj, ii = np.nonzero(lab_ == k_)
        if xy_to_latlon(xs[ii].mean(), ys[jj].mean())[0] > 50:
            keep_.append(k_)
    if keep_:
        jj, ii = np.nonzero(np.isin(lab_, keep_) & ~C["accumulation_lgm"])
        la, lo = xy_to_latlon(xs[ii], ys[jj])
        lat_ice = float(np.percentile(la, 1))
check("science", "Southern margin of the LGM ice sheet of the North (ice masses >= 50 000 km2 north of 50 N, 1st percentile latitude)", lat_ice if lat_ice is not None else 0,
      "Earth's LGM ice sheets: Laurentide ~40 N, British-Irish ~51.5 N, Fennoscandian ~52 N, Barents-Kara in continental Siberia ~61-62 N", 38, 62, "deg N", "ice")
# landscape spectrum on long east-west transects across the land (5 - 100 km)
rows = []
for j in range(0, z.shape[0], int(50e3 / dx)):
    r = land[j]
    if r.mean() < 0.4:
        continue
    # the longest unbroken run of land (a transect across a bay would add sea-floor steps)
    rl, nr = ndimage.label(r)
    if nr == 0:
        continue
    best = np.argmax(ndimage.sum(r, rl, range(1, nr + 1))) + 1
    k_ = np.nonzero(rl == best)[0]; seg = z[j, k_[0]:k_[-1] + 1]
    if seg.size * dx < 300e3:
        continue
    seg = seg[: int(300e3 / dx)].astype(float)
    xx = np.arange(seg.size); seg = seg - np.polyval(np.polyfit(xx, seg, 1), xx)
    rows.append(seg)
if rows:
    rows = np.array(rows); win = np.hanning(rows.shape[1])
    ps = np.mean(np.abs(np.fft.rfft(rows * win, axis=1)) ** 2, axis=0); k = np.fft.rfftfreq(rows.shape[1], d=dx)
    band = (k > 1 / 100e3) & (k < 1 / 5e3)
    beta = -np.polyfit(np.log(k[band]), np.log(ps[band]), 1)[0]
    check("science", "Spectral exponent of 300 km land transects (5-100 km)", beta, "~2", 1.6, 2.6, "", "spectrum", f"{len(rows)} transects")
# coastline fractal dimension (box counting, 1-32 km)
coast = land & ~ndimage.binary_erosion(land)
bs = [b_ for b_ in (1, 2, 4, 8, 16, 32, 64) if 1000 <= b_ * dx <= 32000]
cnt = []
for b_ in bs:
    n0, n1 = -(-coast.shape[0] // b_) * b_, -(-coast.shape[1] // b_) * b_
    cc = np.zeros((n0, n1), bool); cc[:coast.shape[0], :coast.shape[1]] = coast
    cnt.append(cc.reshape(n0 // b_, b_, n1 // b_, b_).any(axis=(1, 3)).sum())
Dc = -np.polyfit(np.log(np.array(bs) * dx), np.log(cnt), 1)[0]
check("science", "Fractal dimension of the coastline (box counting, %g-%g km)" % (bs[0] * dx / 1000, bs[-1] * dx / 1000), Dc,
      "1.1-1.5 (Britain's west coast ~1.25, Norway ~1.5)", 1.1, 1.5, "", "coast")
# isotropy: no preferred grid directions in the relief at 1-4 km (D8 erosion leaves rills along the 8 grid directions)
N_ = 256; kk = np.fft.fftfreq(N_, dx); KX, KY = np.meshgrid(kk, kk); KK = np.hypot(KX, KY)
th = np.degrees(np.arctan2(KY, KX)) % 45; dth = np.minimum(th, 45 - th)
bandk = (KK > 1 / 4000) & (KK < 1 / 1000); ax_, ot_ = bandk & (dth < 4), bandk & (dth > 8)
win2 = np.outer(np.hanning(N_), np.hanning(N_)); yy_, xx_ = np.mgrid[:N_, :N_]
A_pl = np.c_[xx_.ravel(), yy_.ravel(), np.ones(N_ * N_)]
rat = []
for j0 in range(0, z.shape[0] - N_, N_):
    for i0 in range(0, z.shape[1] - N_, N_):
        if land[j0:j0 + N_, i0:i0 + N_].mean() < 0.95:
            continue
        blk = z[j0:j0 + N_, i0:i0 + N_].astype(float)
        blk = blk - (A_pl @ np.linalg.lstsq(A_pl, blk.ravel(), rcond=None)[0]).reshape(N_, N_)
        P_ = np.abs(np.fft.fft2(blk * win2)) ** 2
        rat.append(P_[ax_].mean() / P_[ot_].mean())
check("science", "Relief isotropy: power along the 8 grid directions / other directions at 1-4 km, median of land blocks",
      float(np.median(rat)), "1 (isotropic)", 0.7, 1.5, "", "isotropy", f"{len(rat)} blocks of {N_ * dx / 1000:.0f} km")
check("science", "Relief isotropy, 90th percentile of land blocks", float(np.percentile(rat, 90)), "1 (isotropic)", 0.7, 3.0, "",
      "isotropy")

# mountains (Kapos et al. 2000 / UNEP-WCMC criteria): > 2500 m; 1500-2500 m with slope > 2 deg; 1000-1500 m with slope
# > 5 deg or local relief > 300 m (7 km radius); 300-1000 m with local relief > 300 m. Earth: ~24 % of the land.
gy_, gx_ = np.gradient(z.astype(np.float32), dx)
slope_ = np.degrees(np.arctan(np.hypot(gx_, gy_))); del gy_, gx_
rad_ = max(1, int(7000 / dx))
loc_rel = ndimage.maximum_filter(z, size=2 * rad_ + 1) - ndimage.minimum_filter(z, size=2 * rad_ + 1)
mtn = land & ((z > 2500) | ((z > 1500) & (slope_ > 2)) | ((z > 1000) & ((slope_ > 5) | (loc_rel > 300))) | ((z > 300) & (loc_rel > 300)))
check("science", "Mountain share of the land (Kapos et al. 2000 criteria)", 100 * float(mtn[land].mean()), "Earth ~24 %", 10, 35, "%",
      "mountains")
del slope_, loc_rel
# proportions of each canon mountain region: highest summit / equivalent half-width (Earth's ranges stay below ~0.07:
# Alps 4.8 km / ~100 km, Andes 6.9 km / ~150 km, Pyrenees 3.4 km / ~50 km)
LA_, LO_ = None, None
ratios = {}
for mname, (poly, h_) in cg.MOUNTAINS.items():
    px_, py_ = latlon_to_xy(*cg.to_latlon(*np.array(poly, float).T))
    j0_, j1_ = max(0, int((ys[0] - py_.max()) / dx)), min(z.shape[0], int((ys[0] - py_.min()) / dx) + 1)
    i0_, i1_ = max(0, int((px_.min() - xs[0]) / dx)), min(z.shape[1], int((px_.max() - xs[0]) / dx) + 1)
    Xw, Yw = np.meshgrid(xs[i0_:i1_], ys[j0_:j1_])
    inside = Path(np.column_stack([px_, py_])).contains_points(np.column_stack([Xw.ravel(), Yw.ravel()])).reshape(Xw.shape)
    inside &= land[j0_:j1_, i0_:i1_]
    if not inside.any():
        continue
    zmax = float(z[j0_:j1_, i0_:i1_][inside].max()); half = math.sqrt(inside.sum() * dx * dx / math.pi)
    ratios[mname] = (zmax, half / 1000, zmax / half)
check("science", "Mountain regions: highest summit / equivalent half-width, largest", max(r[2] for r in ratios.values()),
      "< ~0.07 (Alps 0.05, Andes 0.05, Pyrenees 0.07)", 0, 0.07, "", "mountains",
      "; ".join(f"{k} {r[0]:.0f} m / {r[1]:.0f} km" for k, r in ratios.items()))

# ---------------- canon ----------------
chan = (Q >= 10) & land
dch = ndimage.distance_transform_edt(~chan) * dx
riv = {}
for name, pts in cg.RIVERS.items():
    p = np.array(pts, float)
    if np.hypot(*np.diff(p, axis=0).T).sum() < 150:      # rivers of the map at least 150 canon km long
        continue
    dense = np.concatenate([np.linspace(p[k], p[k + 1], 20, endpoint=False) for k in range(len(p) - 1)] + [p[-1:]])
    rx, ry = latlon_to_xy(*cg.to_latlon(*dense.T))
    vals = [dch[cell(a, b)] for a, b in zip(rx, ry) if 0 <= cell(a, b)[0] < z.shape[0] and 0 <= cell(a, b)[1] < z.shape[1]]
    riv[name] = 100 * float(np.mean(np.array(vals) <= 6000))
check("canon", "Map rivers >= 150 km followed by model rivers (>= 10 m3/s within 6 km), mean", float(np.mean(list(riv.values()))), "canon river network",
      70, 100, "%", "canon", "; ".join(f"{k} {v:.0f}%" for k, v in riv.items()))
lake_found = {}
for name, ((ccx, ccy), (ax, ay)) in cg.LAKES.items():
    t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    ex, ey = latlon_to_xy(*cg.to_latlon(ccx + 1.3 * max(ax, 12) * np.cos(t), ccy + 1.3 * max(ay, 12) * np.sin(t)))
    jl, il = np.nonzero(lake)
    inside = Path(np.column_stack([ex, ey])).contains_points(np.column_stack([xs[il], ys[jl]])) if jl.size else np.zeros(0, bool)
    if name.startswith("lake "):
        lake_found[name] = bool(inside.any())
    else:
        check("canon", f"{name} exists (lake area within its canon outline)", float(inside.sum() * A), "> 0", 1, 1e9, "km2", "canon")
if lake_found:
    check("canon", "Smaller lakes of the map present in the model", 100 * float(np.mean(list(lake_found.values()))),
          "the map's lakes", 70, 100, "%", "canon", ", ".join(k for k, ok in lake_found.items() if not ok) or "all")
stand = {}
for mname, (poly, h_) in cg.MOUNTAINS.items():
    px_, py_ = latlon_to_xy(*cg.to_latlon(*np.array(poly, float).T))
    jj_, ii_ = np.nonzero(land)
    sel = np.random.default_rng(0).choice(jj_.size, min(jj_.size, 400000), replace=False)
    pin = Path(np.column_stack([px_, py_])).contains_points(np.column_stack([xs[ii_[sel]], ys[jj_[sel]]]))
    stand[mname] = float(np.median(z[jj_[sel][pin], ii_[sel][pin]])) if pin.any() else 0.0
check("canon", "Canon mountain regions rise above the plains (median elevation inside each region), lowest", min(stand.values()),
      "mountains and hills where the canon map draws them", 300, 1e9, "m", "canon", "; ".join(f"{k} {v:.0f} m" for k, v in stand.items()))
# the valley floor within ~3 km of the line, at the water surface where the river crosses a lake
zws = np.where(lake, np.nan_to_num(C["lake_level_m"], nan=0.0), z)
zfloor = ndimage.minimum_filter(zws, size=2 * max(1, int(3000 / dx)) + 1)
del zws
climb = {}
for name, pts in cg.RIVERS.items():
    p = np.array(pts, float)
    if np.hypot(*np.diff(p, axis=0).T).sum() < 150:
        continue
    dense = np.concatenate([np.linspace(p[k], p[k + 1], 20, endpoint=False) for k in range(len(p) - 1)] + [p[-1:]])
    rx, ry = latlon_to_xy(*cg.to_latlon(*dense.T))
    zz_ = np.array([zfloor[cell(a, b)] for a, b in zip(rx, ry) if 0 <= cell(a, b)[0] < z.shape[0] and 0 <= cell(a, b)[1] < z.shape[1]])
    climb[name] = float(np.max(zz_ - np.minimum.accumulate(zz_)))
check("canon", "Map rivers >= 150 km whose course never climbs more than 100 m (no ridge crossed)",
      100 * float(np.mean([c_ <= 100 for c_ in climb.values()])), "rivers flow downhill along their canon course", 80, 100, "%",
      "canon", "; ".join(f"{k} +{v:.0f} m" for k, v in climb.items() if v > 100))
isl_ok = []
NAMED = {k: v for k, v in cg.ISLANDS.items() if not k.startswith("isle ")}
def isl_cell(spec):
    # the outline vertex nearest to the centroid, moved halfway to the centroid: inside even a curved island
    x, y = cg.island_ring(spec); cx_, cy_ = cg.island_centre(spec)
    return cell(*latlon_to_xy(*cg.to_latlon(cx_, cy_)))
for iname, spec in NAMED.items():
    jc, ic = isl_cell(spec)
    isl_ok.append(bool(land[max(0, jc - 4):jc + 5, max(0, ic - 4):ic + 5].any()))
check("canon", "Named canon islands exist as land", sum(isl_ok), f"{len(isl_ok)}", len(isl_ok), len(isl_ok), "", "canon",
      ", ".join(n for n, ok in zip(NAMED, isl_ok) if not ok) or "all")
lab_l, _ = ndimage.label(land)
main_ = np.argmax(np.bincount(lab_l.ravel())[1:]) + 1
ids = []
for iname, spec in NAMED.items():
    jc, ic = isl_cell(spec)
    w_ = lab_l[max(0, jc - 4):jc + 5, max(0, ic - 4):ic + 5]
    ids.append(np.bincount(w_[w_ > 0]).argmax() if (w_ > 0).any() else -1)
sep = len(set(i for i in ids if i > 0 and i != main_)) if -1 not in ids else 0
check("canon", "Named canon islands are separate islands (not joined to each other or to the mainland)", sep, f"{len(ids)}",
      len(ids), len(ids), "", "canon")
inland = [n for n in ("Winterfell", "Riverrun", "Harrenhal", "Highgarden", "the Eyrie", "Last Hearth", "Deepwood Motte")]
ok_in = sum(int(land[cell(*latlon_to_xy(*cg.to_latlon(*cg.PLACES[n])))] and not lake[cell(*latlon_to_xy(*cg.to_latlon(*cg.PLACES[n])))]) for n in inland)
check("canon", "Inland castles stand on dry land", ok_in, f"{len(inland)}", len(inland), len(inland), "", "canon", ", ".join(inland))

sci = [c for c in checks if c["kind"] == "science"]; can = [c for c in checks if c["kind"] == "canon"]
ps_, pc_ = sum(c["passed"] for c in sci), sum(c["passed"] for c in can)
stats = json.load(open(os.path.join(OUT, "continent.json")))
lines = ["# Validation of the continental model", "", "Generated by `scripts/validate_continent.py`.", "",
         f"Grid {stats['size_km'][0]} x {stats['size_km'][1]} km at {stats['dx_m']:.0f} m; land {stats['land_km2']:,} km2; "
         f"LGM ice {stats['ice_lgm_km2']:,} km2.", "",
         f"**Science checks: {ps_} / {len(sci)} passed. Canon checks: {pc_} / {len(can)} met.**", "",
         "| Kind | Check | Value | Reference | Accepted band | Result | Source |", "|---|---|---|---|---|---|---|"]
for c in checks:
    u = f" {c['unit']}" if c["unit"] else ""; note = f" ({c['note']})" if c["note"] else ""
    lines.append(f"| {c['kind']} | {c['name']}{note} | {c['value']}{u} | {c['reference']} | {c['band'][0]}–{c['band'][1]}{u} | "
                 f"{'PASS' if c['passed'] else ('FAIL' if c['kind'] == 'science' else 'NOT MET')} | {c['source']} |")
lines += ["", "## Sources", ""] + [f"- **{k}**: [{t}]({u})" for k, (t, u) in SOURCES.items()]
open(DOC, "w").write("\n".join(lines) + "\n")
json.dump(dict(science_passed=ps_, science_total=len(sci), canon_met=pc_, canon_total=len(can), checks=checks),
          open(os.path.join(OUT, "validation_continent.json"), "w"), indent=1)
for c in checks:
    print(("PASS " if c["passed"] else "FAIL ") + f"[{c['kind']}] {c['name']}: {c['value']} (band {c['band']}) {c['note'][:300]}")
print(f"science {ps_}/{len(sci)}, canon {pc_}/{len(can)}")
sys.exit(0 if ps_ == len(sci) else 1)
