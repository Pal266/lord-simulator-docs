"""
Checks for the exported water bodies (export_water.py) against the exported terrain and Earth data.

  * physics    - river water surfaces fall downstream; river splines run inside the carved channels (the terrain
                 under them lies below the water surface); lakes cover their basins and do not stand on dry ground;
  * Earth data - mean flow velocities v = Q / (w d) are within the range of natural rivers (hydraulic geometry).

Usage:  python validate_water.py
Writes ../VALIDATION_WATER.md and ../output/validation_water.json; exits with code 1 if any check fails.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from matplotlib.path import Path
from region_common import REGION_DIR, REGION_OUT
import detail_plots as dp

SOURCES = {
    "leopold": ("Leopold & Maddock 1953, The hydraulic geometry of stream channels and some physiographic implications "
                "(USGS Professional Paper 252)", "https://pubs.usgs.gov/publication/pp252"),
    "lakes": ("Verpoorter et al. 2014, A global inventory of lakes based on high-resolution satellite imagery (GRL): lakes cover "
              "~3.7% of non-glaciated land, most densely in formerly glaciated terrain", "https://hal.archives-ouvertes.fr/hal-01066344"),
    "model": ("This region's exported plots (export/tile_*/heightmap.png)", "USAGE.md"),
}
checks = []


def check(kind, name, value, ref, lo, hi, unit, src, note=""):
    checks.append(dict(kind=kind, name=name, value=round(float(value), 4), reference=ref, band=[lo, hi], unit=unit,
                       source=src, passed=bool(lo <= value <= hi), note=note))


SP = dp.SPACING * 100.0
rises = steps = 0
in_channel = []; depth_ratio = []; vel = []
lake_wet_in = []; lake_dry_out = []
for c_ in range(4):
    for r_ in range(4):
        name = f"tile_x{c_}_y{r_}"
        w = json.load(open(os.path.join(dp.EXPORT, name, "water.json")))
        hm = np.array(Image.open(os.path.join(dp.EXPORT, name, "heightmap.png")))
        z = (hm.astype(np.float32) - 32768) / dp.UNITS_PER_M
        del hm
        for rv in w["rivers"]:
            p = np.array(rv["points_cm"])
            ws = p[:, 2] / 100.0
            dz = np.diff(ws); rises += int((dz > 0.2).sum()); steps += dz.size
            fi = p[:, 0] / SP; fj = p[:, 1] / SP
            ok = (fi >= 0) & (fi <= dp.NV - 1) & (fj >= 0) & (fj <= dp.NV - 1)
            if ok.any():
                t = ndimage.map_coordinates(z, [fj[ok], fi[ok]], order=1)
                in_channel.extend(list(t <= ws[ok] + 0.1))
                d = np.array(rv["depth_m"])[ok]
                depth_ratio.extend(list((ws[ok] - t) / d))
            vel.extend(rv["velocity_ms"])
        # lakes: terrain sampled every 4th vertex (~12 m)
        sub = z[::4, ::4]
        jj, ii = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
        pts = np.column_stack([(ii * 4 * SP).ravel(), (jj * 4 * SP).ravel()])
        for lk in w["lakes"]:
            poly = np.array(lk["outline_cm"])
            x0, y0 = poly.min(0) - 10000; x1, y1 = poly.max(0) + 10000    # bounding box + 100 m
            sel = (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)
            if not sel.any():
                continue
            inside = Path(poly).contains_points(pts[sel])
            below = sub.ravel()[sel] < lk["level_m"]
            if inside.any():
                lake_wet_in.append(float(below[inside].mean()))
            # dry hollows below the lake level just outside the outline (water missing there)
            if (~inside).any():
                lake_dry_out.append(float(below[~inside].mean()))
        del z, sub
        print(name, "checked", flush=True)

summ = json.load(open(os.path.join(REGION_OUT, "water_summary.json")))
check("physics", "River water surfaces fall downstream: share of spline steps rising > 0.2 m", 100.0 * rises / max(steps, 1),
      "~0", 0, 2.0, "%", "model", f"{steps} steps")
check("physics", "River splines lie in the carved channel: share of points with terrain at or below the water surface",
      100.0 * np.mean(in_channel), "~100", 95.0, 100.0, "%", "model", f"{len(in_channel)} points")
check("physics", "Water depth over the terrain / Manning depth, median", float(np.median(depth_ratio)), "~1", 0.5, 1.5, "", "model")
check("Earth data", "Mean flow velocity v = Q/(w d), median", float(np.median(vel)), "~0.3-2 m/s in natural rivers", 0.2, 3.0, "m/s", "leopold")
check("Earth data", "Mean flow velocity, 99th percentile", float(np.percentile(vel, 99)), "< ~5 m/s", 0, 5.0, "m/s", "leopold")
check("physics", "Lakes cover their basins: median share of terrain below the lake level inside the outline",
      100.0 * float(np.median(lake_wet_in)), "most of the lake area", 50.0, 100.0, "%", "model", f"{len(lake_wet_in)} lake parts")
check("physics", "No dry hollows next to lakes: median share of terrain below the level within 100 m outside the outline",
      100.0 * float(np.median(lake_dry_out)), "~0", 0, 5.0, "%", "model")

prep = np.load(dp.PREP)
res = float(prep["res"]); n_ = prep["lake"].shape
xs = float(prep["x0"]) + np.arange(n_[1]) * res; ys = float(prep["y0"]) - np.arange(n_[0]) * res
from region_common import HALF_M
ins = (np.abs(xs)[None, :] <= HALF_M) & (np.abs(ys)[:, None] <= HALF_M)
check("Earth data", "Lake share of the square", 100.0 * float(prep["lake"][ins].mean()),
      "3.7% of Earth's land; more in formerly glaciated terrain", 1.0, 12.0, "%", "lakes")

passed = sum(c["passed"] for c in checks)
lines = ["# Validation of the water bodies — region `southern_coast_range`", "",
         "Generated by `scripts/validate_water.py` from `export/tile_*/water.json` and the exported heightmaps.", "",
         f"**Result: {passed} / {len(checks)} checks passed.** Rivers: {summ['rivers']} splines, {summ['river_km']} km; "
         f"lakes: {summ['lakes']} outlines.", "",
         "| Kind | Check | Value | Reference | Accepted band | Result | Source |", "|---|---|---|---|---|---|---|"]
for c in checks:
    u = f" {c['unit']}" if c["unit"] else ""
    note = f" ({c['note']})" if c["note"] else ""
    lines.append(f"| {c['kind']} | {c['name']}{note} | {c['value']}{u} | {c['reference']} | {c['band'][0]}–{c['band'][1]}{u} | "
                 f"{'PASS' if c['passed'] else 'FAIL'} | {c['source']} |")
lines += ["", "## Sources", ""] + [f"- **{k}**: [{t}]({u})" for k, (t, u) in SOURCES.items()]
open(os.path.join(REGION_DIR, "VALIDATION_WATER.md"), "w").write("\n".join(lines) + "\n")
json.dump(dict(passed=passed, total=len(checks), checks=checks), open(os.path.join(REGION_OUT, "validation_water.json"), "w"), indent=1)
for c in checks:
    print(("PASS " if c["passed"] else "FAIL ") + f"[{c['kind']}] {c['name']}: {c['value']} (band {c['band']})")
print(f"{passed}/{len(checks)} passed")
sys.exit(0 if passed == len(checks) else 1)
