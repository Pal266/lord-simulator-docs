"""
Checks of the Westeros planet model.

Two kinds of checks, reported separately:
  * science - the model is compared with Earth data (these must all pass: realism comes first);
  * canon   - the model is compared with the books' geography and climate. A failed canon check is not an error of the
              model: it marks a canon feature that the science does not support (yet); each one is discussed in
              ../USAGE.md, section "Canon deviations".

Usage:  python validate_westeros.py
Writes ../output/VALIDATION.md and ../output/validation.json; exits with code 1 if a SCIENCE check fails.
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage
import canon_geography as cg

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "VALIDATION.md")
SOURCES = {
    "canon": ("canon_geography.py: canon facts (A Wiki of Ice and Fire, the books)", "../scripts/canon_geography.py"),
    "wall": ("The Wall is about 300 miles (480 km) long (A Game of Thrones, Jon VI; World of A Song of Ice and Fire)",
             "https://en.wikipedia.org/wiki/World_of_A_Song_of_Ice_and_Fire"),
    "koppen": ("Peel, Finlayson & McMahon 2007, Updated world map of the Koppen-Geiger climate classification", "https://hess.copernicus.org/articles/11/1633/2007/"),
    "treeline": ("Forest requires a warmest month of at least ~10 C (Koppen E/D boundary; Koerner & Paulsen 2004)", "https://edoc.unibas.ch/8594"),
    "hypsometry": ("Mean elevation of the continents ~840 m; Europe ~300 m, North America ~720 m (Cogley 1985 / Segar)", "https://www.ngdc.noaa.gov/mgg/global/etopo1_surface_histogram.html"),
    "runoff": ("Runoff ratio over land ~0.35 globally, 0.2-0.6 for humid mid- and high-latitude basins (Trenberth et al. 2007)", "https://journals.ametsoc.org/view/journals/hydr/8/4/jhm600_1.xml"),
}
checks = []


# Canon features the user has accepted as deviations (CANON.md, "Canon deviations"): a canon check of one of them that
# is not met is reported as an accepted deviation, not as an open problem.
ACCEPTED = {"north_winters": "accepted deviation (CANON.md: the North has mild maritime winters south of the Wall)",
            "rainwood": "accepted deviation (CANON.md: the Rainwood faces the Narrow Sea, a narrow sea, and is semi-arid)"}


def check(kind, name, value, ref, lo, hi, unit, src, note="", accepted=None):
    passed = bool(lo <= value <= hi)
    checks.append(dict(kind=kind, name=name, value=value if isinstance(value, bool) else round(float(value), 3), reference=ref,
                       band=[lo, hi], unit=unit, source=src, passed=passed, note=note,
                       accepted=ACCEPTED[accepted] if accepted and not passed else None))


Hh = np.load(f"{OUT}/world_height.npz"); C = np.load(f"{OUT}/world_climate.npz"); Hy = np.load(f"{OUT}/world_hydrology.npz")
K = np.load(f"{OUT}/world_canon.npz"); codes = json.load(open(f"{OUT}/world_climate.json"))["koppen_codes"]
H, W = Hh["land"].shape
w = K["westeros"]; y = K["canon_y_km"]; x = K["canon_x_km"]
kop = np.array([codes[v] if v >= 0 else "" for v in C["koppen"].ravel()]).reshape(H, W)
area = np.cos(np.radians(90 - (np.arange(H) + 0.5) / H * 180))[:, None] * np.ones((1, W))


def cell(name):
    lat, lon = cg.to_latlon(*cg.PLACES[name])
    return int((90 - lat) / 180 * H), int((lon + 180) / 360 * W)


def gc_km(a, b):
    la1, lo1 = map(math.radians, cg.to_latlon(*cg.PLACES[a])); la2, lo2 = map(math.radians, cg.to_latlon(*cg.PLACES[b]))
    return 6371.0 * math.acos(min(1, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(lo1 - lo2)))


def share(mask, classes):
    m = mask & w
    return 100.0 * np.isin(kop[m], classes).sum() / max(m.sum(), 1)


# regions in canon km: the Neck (Moat Cailin, y ~ -1600) closes the North; the Blackwater (King's Landing, y ~ -2850)
# divides the Riverlands band from the Reach band; Dorne lies south of the Red Mountains (y ~ -3550), east of the Reach
REG = {"Land of Always Winter": y > 1300, "Haunted Forest band (0-600 km north of the Wall)": (y > 0) & (y <= 600),
       "the North": (y <= 0) & (y > -1600), "the Reach / Crownlands / Stormlands band": (y <= -2850) & (y > -3550),
       "Dorne": (y <= -3550) & (x > -760), "Riverlands / Vale / Westerlands band": (y <= -1600) & (y > -2850)}

# ---------------- scale ----------------
for a, b, canon_km, src in cg.CANON_DISTANCES:
    target = canon_km * cg.SCALE
    check("science", f"Distance {a} - {b} (canon {canon_km:.0f} km x scale {cg.SCALE})", gc_km(a, b), f"{target:.0f} km",
          0.9 * target, 1.1 * target, "km", "wall" if src == "wall" else "canon")

# ---------------- relief ----------------
z = Hh["elevation_m"]
zl = z[w & (K["ice_sheet_m"] < 50)]
check("science", "Mean elevation of Westeros (without the ice sheet)", float(np.average(zl, weights=area[w & (K["ice_sheet_m"] < 50)])),
      "~840 m continents; 300-720 m Europe / North America", 250, 1000, "m", "hypsometry")
neck = w & (np.hypot(x - cg.LOWLANDS['the Neck'][0][0], y - cg.LOWLANDS['the Neck'][0][1]) < 120) & (K['range_weight'] < 0.05)   # not the Vale's foothills
check("canon", "The Neck is low marshland: mean elevation", float(z[neck].mean()), "bogs and marshes", 0, 60, "m", "canon")

# ---------------- climate ----------------
check("canon", "The North: share of cold-winter (Koppen D) climates", share(REG["the North"], ["Df", "Dw", "Ds"]),
      "cold, snowy winters", 70, 100, "%", "canon", accepted="north_winters")
check("canon", "Haunted Forest band: share of forest climates (Koppen D)", share(REG["Haunted Forest band (0-600 km north of the Wall)"], ["Df", "Dw", "Ds"]),
      "a great forest north of the Wall", 50, 100, "%", "treeline")
check("canon", "Land of Always Winter: share of polar climates (EF/ET)", share(REG["Land of Always Winter"], ["EF", "ET"]),
      "ice and snow", 80, 100, "%", "canon")
jw, iw = cell("Winterfell")
check("canon", "Winterfell: coldest-season mean temperature", float(C["temp_jan_c"][jw, iw]), "snowy winters", -25, -3, "C", "canon", accepted="north_winters")
check("science", "Winterfell: warmest-season mean temperature (crops need >= ~10 C)", float(C["temp_jul_c"][jw, iw]),
      "12-20 C: cool-summer farming (barley, oats, rye)", 12, 20, "C", "koppen")
check("canon", "The Reach band: share of temperate (Koppen C) climates", share(REG["the Reach / Crownlands / Stormlands band"], ["Cf", "Cs", "Cw"]),
      "warm, fertile", 70, 100, "%", "canon")
p95 = {n: float(np.percentile(C["temp_jul_c"][m & w], 95)) for n, m in REG.items()}
check("canon", "Dorne has the hottest summers of Westeros (95th percentile of summer temperature, Dorne minus the next region)",
      p95["Dorne"] - max(v for n, v in p95.items() if n != "Dorne"), "> 0", 0, 50, "C", "canon")
check("canon", "Dorne: share of arid (Koppen B) climates", share(REG["Dorne"], ["BWh", "BWk", "BSh", "BSk"]),
      "the only desert of Westeros", 5, 100, "%", "canon")
(rcx, rcy), (rax, ray) = cg.FORESTS["Rainwood"]
rain = w & (((x - rcx) / rax) ** 2 + ((y - rcy) / ray) ** 2 < 1)
check("canon", "The Rainwood is a rain forest: mean annual precipitation", float(np.average(C["precip_annual_mm"][rain], weights=area[rain])),
      "a rainy forest", 1000, 1e9, "mm", "canon", accepted="rainwood")
check("science", "Polar / alpine climate share between the Wall and the Land of Always Winter (59-68 N)", share(w & (y > 0) & (y <= 1300), ["EF", "ET"]),
      "Earth 60-70 N land: tundra/ice mostly near cold coasts and high ground", 0, 60, "%", "koppen")

# ---------------- hydrology ----------------
P = C["precip_annual_mm"]; Rf = Hy["runoff_mm"]
m = w & (K["ice_sheet_m"] < 50)
check("science", "Runoff ratio over Westeros (runoff / precipitation)", float((Rf[m] * area[m]).sum() / (P[m] * area[m]).sum()),
      "0.2-0.6 humid mid/high latitudes", 0.2, 0.65, "", "runoff")
Q = Hy["discharge_m3s"]
chan = (Q >= 30) & Hh["land"]
dchan = ndimage.distance_transform_edt(~chan)
riv = {}
for name, poly in cg.RIVERS.items():
    pts = []
    for (x0, y0), (x1, y1) in zip(poly[:-1], poly[1:]):
        for t in np.linspace(0, 1, 12, endpoint=False):
            pts.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
    lat, lon = cg.to_latlon(*np.array(pts).T)
    j = ((90 - lat) / 180 * H).astype(int); i = ((lon + 180) / 360 * W).astype(int)
    riv[name] = float((dchan[j, i] <= 2).mean() * 100)
check("canon", "Canon rivers followed by model rivers (>= 30 m3/s within 2 cells), mean over rivers", float(np.mean(list(riv.values()))),
      "the canon river network", 70, 100, "%", "canon", "; ".join(f"{k} {v:.0f}%" for k, v in riv.items()))
lk = Hy["lake"]
for name, ((cx, cy), (ax, ay)) in cg.LAKES.items():
    if name.startswith("lake "):          # small unnamed lakes are below the planet grid
        continue
    e = ((x - cx) / max(ax, 15)) ** 2 + ((y - cy) / max(ay, 15)) ** 2 < 1.5
    check("canon", f"{name} exists in the model (lake cells in its basin)", float((lk & e & w).sum()), ">= 1", 1, 1e9, "cells", "canon")
check("canon", "Winterfell stands on dry land", float(Hh["land"][jw, iw] and not lk[jw, iw]), 1, 1, 1, "", "canon")

sci = [c for c in checks if c["kind"] == "science"]; can = [c for c in checks if c["kind"] == "canon"]
ps, pc = sum(c["passed"] for c in sci), sum(c["passed"] for c in can)
pa = sum(bool(c["accepted"]) for c in can)
lines = ["# Validation of the Westeros planet model", "", "Generated by `scripts/validate_westeros.py`.", "",
         f"**Science checks: {ps} / {len(sci)} passed** (must all pass). **Canon checks: {pc} / {len(can)} met, "
         f"{pa} accepted deviations, {len(can) - pc - pa} open** "
         "(a canon check that is not met marks a canon feature the science does not support; an accepted deviation is one "
         "the user has accepted, see CANON.md).", "",
         "Regional climate summary (mean coldest / warmest season, precipitation, main Koppen classes):", ""]
for n, msk in REG.items():
    mm = msk & w
    vals, cnt = np.unique(kop[mm], return_counts=True); o = np.argsort(-cnt)[:3]
    lines.append(f"- {n}: {C['temp_jan_c'][mm].mean():.1f} / {C['temp_jul_c'][mm].mean():.1f} C, {P[mm].mean():.0f} mm/yr; "
                 + ", ".join(f"{vals[k]} {100 * cnt[k] / cnt.sum():.0f}%" for k in o))
lines += ["", "| Kind | Check | Value | Reference | Accepted band | Result | Source |", "|---|---|---|---|---|---|---|"]
for c in checks:
    u = f" {c['unit']}" if c["unit"] else ""; note = f" ({c['note']})" if c["note"] else ""
    lines.append(f"| {c['kind']} | {c['name']}{note} | {c['value']}{u} | {c['reference']} | {c['band'][0]}–{c['band'][1]}{u} | "
                 f"{'PASS' if c['passed'] else ('FAIL' if c['kind'] == 'science' else ('ACCEPTED DEVIATION' if c['accepted'] else 'NOT MET'))} | {c['source']} |")
lines += ["", "## Sources", ""] + [f"- **{k}**: [{t}]({u})" for k, (t, u) in SOURCES.items()]
open(DOC, "w").write("\n".join(lines) + "\n")
json.dump(dict(science_passed=ps, science_total=len(sci), canon_met=pc, canon_accepted_deviations=pa, canon_total=len(can), checks=checks),
          open(f"{OUT}/validation.json", "w"), indent=1)
for c in checks:
    print(("PASS " if c["passed"] else "ACCEPTED " if c["accepted"] else "FAIL ") + f"[{c['kind']}] {c['name']}: {c['value']} (band {c['band']}) {c['note'][:200]}")
print(f"science {ps}/{len(sci)}, canon {pc}/{len(can)} met, {pa} accepted deviations, {len(can) - pc - pa} open")
sys.exit(0 if ps == len(sci) else 1)
