"""
Scientific validation of the mountain regional model (region step 1).

Kinds of checks:
  * Earth data - the model's decision or result is compared with published observations;
  * physics    - the model satisfies the relations it claims to use;
  * planet     - the regional model stays consistent with the planet it was cut from.

Usage:  python validate_region.py
Writes ../VALIDATION.md and ../output/validation_region.json; exits with code 1 if any check fails.
"""
import json, math, os, sys
import numpy as np
from region_common import HALF_M, REGION_DIR, REGION_OUT

SOURCES = {
    "tierney": ("Tierney et al. 2020, Glacial cooling and climate sensitivity revisited - University of Arizona summary",
                "https://news.arizona.edu/news/how-cold-was-ice-age-researchers-now-know"),
    "ohmura": ("Ohmura, Kasser & Funk 1992, Climate at the equilibrium line of glaciers (Journal of Glaciology)",
               "https://www.cambridge.org/core/services/aop-cambridge-core/content/view/8DCF1C24E32A6781CC365853535CD16F/S0022143000002276a.pdf/climate-at-the-equilibrium-line-of-glaciers.pdf"),
    "aar": ("Pellitero et al. / Ribolini et al., paleo-ELA reconstruction toolbox: AAR values for cirque and valley glaciers",
            "https://arpi.unipi.it/bitstream/11568/785076/5/Ribolini_785076.pdf"),
    "trough": ("Numerical simulation of the evolution of glacial valley cross sections (arXiv:0901.1177), field data Tian Shan",
               "https://arxiv.org/pdf/0901.1177"),
    "ue": ("Unreal Engine Landscape Technical Guide",
           "https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine"),
    "planet": ("This planet's model (region_context.json)", "output/region_context.json"),
}

st = json.load(open(os.path.join(REGION_OUT, "regional_model.json")))
ctx = json.load(open(os.path.join(REGION_OUT, "region_context.json")))
m = np.load(os.path.join(REGION_OUT, "regional_model.npz"))
z = m["elevation_m"]; xs = m["x_m"]; ys = m["y_m"]; DX = float(xs[1] - xs[0])
inside = (np.abs(xs)[None, :] <= HALF_M) & (np.abs(ys)[:, None] <= HALF_M)
checks = []


def check(kind, name, value, ref, lo, hi, unit, src, note=""):
    checks.append(dict(kind=kind, name=name, value=value if isinstance(value, bool) else round(float(value), 3),
                       reference=ref, band=[round(lo, 2), round(hi, 2)], unit=unit, source=src,
                       passed=bool(lo <= value <= hi), note=note))


g = st["glaciers"]; c = st["climate"]; sq = st["square"]
# --- Earth data ---
check("Earth data", "Accumulation-area ratio used for glacier extent", g["aar"], "0.5-0.67 (cirque and valley glaciers)",
      0.5, 0.67, "", "aar")
check("Earth data", "LGM cooling applied to the region", c["lgm_cooling_c"], "6 (global) to 14 (Arctic)", 6.0, 14.0, "C", "tierney")

# trough cross-section exponent b in z - z_floor = a |y|^b, fitted on transects across the trough axes
axis = m["trough_axis"]
aj, ai = np.nonzero(axis & inside)
rng = np.random.default_rng(1)
bs = []
for k in rng.choice(aj.size, size=min(400, aj.size), replace=False) if aj.size else []:
    j, i = aj[k], ai[k]
    if not (6 < j < z.shape[0] - 7 and 6 < i < z.shape[1] - 7):
        continue
    # valley direction from the trough-axis cells around this point (principal axis), then measure across it
    win = axis[j - 6:j + 7, i - 6:i + 7]
    wj, wi = np.nonzero(win)
    if wj.size < 5:
        continue
    cov = np.cov(np.vstack([wj - wj.mean(), wi - wi.mean()]))
    evals, evecs = np.linalg.eigh(cov)
    dj, di = evecs[:, -1]                    # along-valley (rows, cols)
    px, py = -di, dj                         # perpendicular, as (row step, col step)
    ys_, zs_ = [], []
    hw_cells = int(m["trough_halfwidth_m"][j, i] / DX)       # measure across the trough, up to its shoulders
    if hw_cells < 4:
        continue
    for s in range(1, hw_cells + 1):
        for sgn in (-1, 1):
            jj = int(round(j + sgn * s * px)); ii = int(round(i + sgn * s * py))
            if 0 <= jj < z.shape[0] and 0 <= ii < z.shape[1]:
                ys_.append(s * DX); zs_.append(z[jj, ii] - z[j, i])
    ys_ = np.array(ys_); zs_ = np.array(zs_)
    ok = zs_ > 2.0
    if ok.sum() < 6:
        continue
    b, _ = np.polyfit(np.log(ys_[ok]), np.log(zs_[ok]), 1)
    if 0.5 < b < 5:
        bs.append(b)
b_med = float(np.median(bs)) if bs else 0.0
check("Earth data", "Glacial trough cross-section exponent b (z ~ |y|^b), median of transects", b_med,
      "1.3-2.5 (most field values, Tian Shan)", 1.3, 2.5, "", "trough", f"{len(bs)} transects")

# --- physics ---
present_ok = (sq["elev_max_m"] < c["ela_now_m"]) == (g["present_ice_km2_in_square"] == 0)
check("physics", "Present glaciers exist only if summits reach today's ELA", bool(present_ok), True, True, True, "", "ohmura",
      f"highest point {sq['elev_max_m']} m, ELA {c['ela_now_m']} m")
check("physics", "LGM glacier fronts lie below the LGM ELA (accumulation-area method)", g["lgm_lowest_terminus_m"],
      f"< {c['ela_lgm_m']} m", 0, c["ela_lgm_m"], "m", "aar")

# --- planet ---
check("planet", "Mean elevation of the square vs planet", sq["mean_elev_m"], sq["planet_mean_elev_m"],
      0.9 * sq["planet_mean_elev_m"], 1.1 * sq["planet_mean_elev_m"], "m", "planet")
check("planet", "Highest point vs planet", sq["elev_max_m"], sq["planet_max_elev_m"],
      0.9 * sq["planet_max_elev_m"], 1.1 * sq["planet_max_elev_m"], "m", "planet")
rs = ctx["relief_shares_pct"]
for key, name in (("mountains_pct", "mountains_gt_1000m"), ("foothills_pct", "foothills_300_1000m"), ("plain_pct", "plain_lt_300m")):
    check("planet", f"Share of {name.replace('_', ' ')} vs planet", sq[key], rs[name], rs[name] - 8, rs[name] + 8, "%", "planet")
check("planet", "The square's largest river drains out of the region (towards the sea)", bool(sq["largest_river_reaches_sea_or_edge"]),
      True, True, True, "", "planet")
check("Earth data", "Height range fits Unreal Z scale 1000 (-2560 ... +2560 m)", float(max(abs(z[inside].min()), z[inside].max())),
      "<= 2559.9", 0, 2559.9, "m", "ue")

passed = sum(c_["passed"] for c_ in checks)
lines = ["# Scientific validation — region `southern_coast_range`", "",
         "Generated by `scripts/validate_region.py`. Kinds: **Earth data** (compared with published observations), "
         "**physics** (the model satisfies its own relations), **planet** (consistent with the planet it was cut from).", "",
         f"**Result: {passed} / {len(checks)} checks passed.**", "",
         "| Kind | Check | Model | Reference | Accepted band | Result | Source |", "|---|---|---|---|---|---|---|"]
for c_ in checks:
    u = f" {c_['unit']}" if c_["unit"] else ""
    note = f" ({c_['note']})" if c_["note"] else ""
    lines.append(f"| {c_['kind']} | {c_['name']}{note} | {c_['value']}{u} | {c_['reference']} | {c_['band'][0]}–{c_['band'][1]}{u} | "
                 f"{'PASS' if c_['passed'] else 'FAIL'} | {c_['source']} |")
lines += ["", "## Sources", ""] + [f"- **{k}**: [{t}]({u})" for k, (t, u) in SOURCES.items()]
open(os.path.join(REGION_DIR, "VALIDATION.md"), "w").write("\n".join(lines) + "\n")
json.dump(dict(passed=passed, total=len(checks), checks=checks), open(os.path.join(REGION_OUT, "validation_region.json"), "w"), indent=1)
for c_ in checks:
    print(("PASS " if c_["passed"] else "FAIL ") + f"[{c_['kind']}] {c_['name']}: {c_['value']} (band {c_['band']})")
print(f"{passed}/{len(checks)} passed")
sys.exit(0 if passed == len(checks) else 1)
