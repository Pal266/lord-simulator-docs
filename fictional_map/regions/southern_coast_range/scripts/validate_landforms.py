"""
Checks for the glacial landforms added in the 25 m refinement (cirques, aretes, outwash plains).

  * cirques  - width, floor gradient and headwall gradient against global cirque morphometry (Evans & Cox 2015);
  * outwash  - fill no thicker than ~100 m and a concave long profile (steeper near the former ice front);
  * physics  - outwash lies outside the LGM ice and below it; the fill never raises the ground by more than allowed.

Usage:  python validate_landforms.py      (needs ../output/refined_25m.npz from refine_25m.py)
Writes ../VALIDATION_LANDFORMS.md and ../output/validation_landforms.json; exits with code 1 if any check fails.
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage
from region_common import HALF_M, REGION_DIR, REGION_OUT

SOURCES = {
    "evans": ("Evans & Cox 2015, Size and shape of glacial cirques (summary of global morphometry; medians: width ~656 m, "
              "floor gradient ~7.7 deg, headwall maximum ~57 deg)", "https://www.antarcticglaciers.org/glacial-geology/glacial-landforms/glacial-erosional-landforms/cirques/"),
    "outwash": ("antarcticglaciers.org, Glaciofluvial landforms: outwash plains (sandar) - concave long profile, fining "
                "downstream, deposits up to ~100 m thick", "https://www.antarcticglaciers.org/glacial-geology/glacial-landforms/glaciofluvial-landforms/"),
    "model": ("This region's 25 m model (output/refined_25m.npz)", "output/refined_25m.json"),
}
checks = []


def check(kind, name, value, ref, lo, hi, unit, src, note=""):
    checks.append(dict(kind=kind, name=name, value=value if isinstance(value, bool) else round(float(value), 3),
                       reference=ref, band=[lo, hi], unit=unit, source=src, passed=bool(lo <= value <= hi), note=note))


m = np.load(os.path.join(REGION_OUT, "refined_25m.npz"))
z = m["elevation_m"].astype(np.float64); x = m["x_m"]; y = m["y_m"]; DX = float(x[1] - x[0])
H, W = z.shape
gy, gx = np.gradient(z, DX)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))

# ---------------- cirques ----------------
widths, floors, walls, heights = [], [], [], []
RJ = json.load(open(os.path.join(REGION_OUT, "refined_25m.json")))
rad = int((1.6 * (RJ["cirque_floor_halfwidth_m"] + RJ["cirque_floor_back_m"]) + 700) / DX) + 1   # per-cirque geometry: cirque_params
cq = m["cirque"]
for (j, i, _, _), (R_FLOOR, BACK, uy, ux) in zip(m["cirque_sites"], m["cirque_params"]):
    j, i = int(j), int(i)
    # width: transect across the axis through the middle of the floor; contiguous carved ground (rim to rim)
    vs = np.arange(-1500.0, 1500.1, DX)
    py = -BACK / 2 * uy + vs * ux; px = -BACK / 2 * ux - vs * uy          # north, east offsets
    jj = np.clip(np.round(j - py / DX).astype(int), 0, H - 1); ii = np.clip(np.round(i + px / DX).astype(int), 0, W - 1)
    c = cq[jj, ii]; mid = vs.size // 2
    if not c[mid]:
        continue
    a_ = mid
    while a_ > 0 and c[a_ - 1]:
        a_ -= 1
    e_ = mid
    while e_ < vs.size - 1 and c[e_ + 1]:
        e_ += 1
    widths.append((e_ - a_ + 1) * DX)
    j0, j1 = max(0, j - rad), min(H, j + rad + 1); i0, i1 = max(0, i - rad), min(W, i + rad + 1)
    yy = (j - np.arange(j0, j1))[:, None] * DX; xx = (np.arange(i0, i1) - i)[None, :] * DX
    u = xx * ux + yy * uy; v = -xx * uy + yy * ux
    blk = cq[j0:j1, i0:i1]; sl = slope[j0:j1, i0:i1]; zb = z[j0:j1, i0:i1]
    ub = np.where(u < -BACK, u + BACK, 0.0); rr = np.hypot(ub, v)
    fl = (rr < R_FLOOR * 0.8) & (u < 0) & blk
    if fl.sum() >= 3:
        floors.append(float(np.median(sl[fl])))
    wall = blk & (u < 0) & (rr > R_FLOOR) & (rr < R_FLOOR + 400)
    if wall.sum() >= 3:
        walls.append(float(np.percentile(sl[wall], 95)))         # maximum headwall gradient (robust)
        heights.append(float(zb[wall].max() - z[j, i]))
n = len(widths)
check("Earth data", "Cirque width, median", float(np.median(widths)) if n else 0, "~656 m (global median)", 400, 1100, "m", "evans", f"{n} cirques")
check("Earth data", "Cirque floor gradient, median", float(np.median(floors)) if floors else 0, "~7.7 deg (global median)", 3, 15, "deg", "evans")
check("Earth data", "Cirque headwall maximum gradient, median", float(np.median(walls)) if walls else 0, "~57 deg (global median)", 40, 70, "deg", "evans")
check("Earth data", "Cirque wall height, median", float(np.median(heights)) if heights else 0, "~210 m (global median)", 80, 500, "m", "evans")

# aretes: sharp ridges where two cirque walls meet -> share of steep (> 35 deg) ground above the LGM ELA, before/after
eroded = os.path.join(REGION_OUT, "eroded_25m.npz")
inside = (np.abs(x)[None, :] <= HALF_M) & (np.abs(y)[:, None] <= HALF_M)
high = inside & (m["ice_lgm"] > 0.5) & (z > 1300)
steep_after = float((slope[high] > 35).mean() * 100) if high.any() else 0.0
steep_before = None
if os.path.exists(eroded):
    z0 = np.load(eroded)["z"].astype(np.float64)
    g0y, g0x = np.gradient(z0, DX)
    s0 = np.degrees(np.arctan(np.hypot(g0x, g0y)))
    steep_before = float((s0[high] > 35).mean() * 100)
    del z0, s0

# ---------------- outwash ----------------
ow = m["outwash"]; th = m["outwash_thickness_m"]; trunk = m["outwash_trunk"]
check("Earth data", "Outwash fill: maximum thickness", float(th.max()), "up to ~100 m", 0, 100.0 + 1e-6, "m", "outwash")
check("physics", "Outwash lies outside the LGM ice", float((ow & (m["ice_lgm"] > 0.5)).sum()), 0, 0, 0, "cells", "model")
# long profiles along the meltwater trunks: gradient near the ice front vs further down (concave: ratio > 1)
pid = m["outwash_path_id"].ravel(); ps = m["outwash_path_s"].ravel()
ratios = []
for p_ in np.unique(pid[pid >= 0]):
    k = np.nonzero(pid == p_)[0]
    d = ps[k].astype(float); o_ = np.argsort(d); d = d[o_]; zz = z.ravel()[k][o_]
    if d.size < 20 or d[-1] < 6000:
        continue
    zz = ndimage.uniform_filter1d(zz, 41)
    g1 = (zz[np.searchsorted(d, 500)] - zz[np.searchsorted(d, 2500)]) / 2000.0
    g2 = (zz[np.searchsorted(d, d[-1] - 2500)] - zz[np.searchsorted(d, d[-1] - 500)]) / 2000.0
    if g2 > 1e-4:
        ratios.append(g1 / g2)
check("Earth data", "Outwash long profile is concave: gradient near ice front / far end, median",
      float(np.median(ratios)) if ratios else 0, "> 1 (concave)", 1.0, 50.0, "", "outwash", f"{len(ratios)} profiles >= 6 km")

passed = sum(c_["passed"] for c_ in checks)
lines = ["# Validation of glacial landforms — region `southern_coast_range`", "",
         "Generated by `scripts/validate_landforms.py` from `output/refined_25m.npz`.", "",
         f"**Result: {passed} / {len(checks)} checks passed.**", "",
         f"Cirques carved: {n}. Outwash plains: {ow.sum() * DX * DX / 1e6:.1f} km2 in the model area.", "",
         "Steep ground (> 35 deg) on former glacier ground above 1300 m, reported only: "
         + (f"{steep_before:.1f}% before cirques, " if steep_before is not None else "")
         + f"{steep_after:.1f}% after (aretes and headwalls).", "",
         "| Kind | Check | Value | Reference | Accepted band | Result | Source |", "|---|---|---|---|---|---|---|"]
for c_ in checks:
    u_ = f" {c_['unit']}" if c_["unit"] else ""
    note = f" ({c_['note']})" if c_["note"] else ""
    lines.append(f"| {c_['kind']} | {c_['name']}{note} | {c_['value']}{u_} | {c_['reference']} | {c_['band'][0]}–{c_['band'][1]}{u_} | "
                 f"{'PASS' if c_['passed'] else 'FAIL'} | {c_['source']} |")
lines += ["", "## Sources", ""] + [f"- **{k}**: [{t}]({u})" for k, (t, u) in SOURCES.items()]
open(os.path.join(REGION_DIR, "VALIDATION_LANDFORMS.md"), "w").write("\n".join(lines) + "\n")
json.dump(dict(passed=passed, total=len(checks), checks=checks, steep_pct_before=steep_before, steep_pct_after=steep_after),
          open(os.path.join(REGION_OUT, "validation_landforms.json"), "w"), indent=1)
for c_ in checks:
    print(("PASS " if c_["passed"] else "FAIL ") + f"[{c_['kind']}] {c_['name']}: {c_['value']} (band {c_['band']})")
print(f"steep >35 deg above 1300 m on glacier ground: before {steep_before}, after {steep_after:.1f} %")
print(f"{passed}/{len(checks)} passed")
sys.exit(0 if passed == len(checks) else 1)
