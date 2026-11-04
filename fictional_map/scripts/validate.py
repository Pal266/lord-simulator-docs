"""
Scientific validation of the generated world against observed Earth data.

Every check compares a statistic of the generated planet with a published Earth value.
The world has different geography from Earth, so a check passes when the value lies inside a
plausibility band around the Earth value (the band is stated next to each check).

Run after every pipeline step:  python validate.py
Writes ../VALIDATION.md and ../output/validation.json; exits with code 1 if any check fails.
"""
import json, os, sys
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "output")

SOURCES = {
    "segar": ("Segar, Introduction to Ocean Sciences, Appendix 2: Dimensions of Earth and Ocean",
              "https://geo.libretexts.org/Courses/American_Meteorological_Society/Introduction_to_Ocean_Sciences_6e_(Segar)/zz%3A_Back_Matter/22%3A_Appendix_2_-_Dimensions_of_Earth_and_Ocean"),
    "plates": ("Plate tectonics (Wikipedia, with primary references)", "https://en.wikipedia.org/wiki/Plate_tectonics"),
    "gpcp": ("Adler et al., GPCP v2.3 global precipitation summary 2017 (1979-2016 climatology)",
             "https://cisess.umd.edu/assets/1/7/GPCPsummary2017Adler.pdf"),
    "peel": ("Peel, Finlayson & McMahon 2007, Updated world map of the Koppen-Geiger climate classification, HESS 11:1633",
             "https://hess.copernicus.org/articles/11/1633/2007/"),
    "trenberth": ("Trenberth et al. 2007, Estimates of the global water budget and its annual cycle, J. Hydrometeorology 8",
                  "https://acomstaff.acom.ucar.edu/lsmith/GEWEX-JHydroMet8.pdf"),
    "basins": ("Drainage basin (Wikipedia): endorheic basins cover about 18% of land", "https://en.wikipedia.org/wiki/Drainage_basin"),
    "glowabo": ("Verpoorter et al. 2014 (GLOWABO lake inventory), summarised by EARTH Magazine",
                "https://www.earthmagazine.org/article/scientists-complete-global-inventory-lakes"),
    "hack": ("Hack's law (Wikipedia, after Hack 1957)", "https://en.wikipedia.org/wiki/Hack%27s_law"),
    "strahler": ("Strahler number and bifurcation ratio (Wikipedia)", "https://en.wikipedia.org/wiki/Strahler_number"),
    "britannica": ("Encyclopaedia Britannica, Koppen climate classification: world distribution of major climatic types",
                   "https://www.britannica.com/science/Koppen-climate-classification/World-distribution-of-major-climatic-types"),
}

checks = []


def check(step, name, value, earth, lo, hi, unit, src, note=""):
    ok = lo <= value <= hi
    checks.append(dict(step=step, name=name, value=round(float(value), 2), earth=earth, band=[lo, hi],
                       unit=unit, source=src, passed=bool(ok), note=note))


def area_weights(shape):
    H, W = shape
    lat = np.radians(90 - (np.arange(H) + 0.5) / H * 180)
    return np.repeat(np.cos(lat)[:, None], W, 1)


# ---------- step 2: plates ----------
if os.path.exists(f"{OUT}/world_plates.json"):
    pm = json.load(open(f"{OUT}/world_plates.json"))
    major = [p for p in pm["plates"] if p["area_pct"] >= 4.0]
    speeds = [p["speed_cm_yr"] for p in pm["plates"]]
    check("2 Plates", "Number of major plates (>= 4% of surface)", len(major), "7-8", 6, 10, "", "plates")
    check("2 Plates", "Fastest plate speed", max(speeds), "typically 0-10, up to ~16", 1.0, 16.0, "cm/yr", "plates")
    check("2 Plates", "Mean plate speed", float(np.mean(speeds)), "typically 0-10", 0.5, 10.0, "cm/yr", "plates")

# ---------- step 3: relief ----------
if os.path.exists(f"{OUT}/world_height.npz"):
    hd = np.load(f"{OUT}/world_height.npz")
    z, land = hd["elevation_m"], hd["land"]
    A = area_weights(z.shape)
    land_pct = A[land].sum() / A.sum() * 100
    check("3 Relief", "Land share of surface", land_pct, 29.22, 26, 33, "%", "segar")
    check("3 Relief", "Mean land elevation", (z * A)[land].sum() / A[land].sum(), 840, 600, 1100, "m", "segar")
    check("3 Relief", "Mean ocean depth", -(z * A)[~land].sum() / A[~land].sum(), 3800, 3300, 4300, "m", "segar",
          "other references give 3 682 m")
    check("3 Relief", "Highest point", z.max(), 8848, 7000, 9500, "m", "segar")
    check("3 Relief", "Deepest point", -z.min(), 11035, 8500, 11500, "m", "segar",
          "a 28 km grid cell averages trench depth, so the band is wider downwards")
    shelf = (~land) & (z > -2500)
    check("3 Relief", "Continental shelf + slope (sea floor above -2 500 m), share of ocean",
          A[shelf].sum() / A[~land].sum() * 100, 15.3, 10, 22, "%", "segar")

# ---------- step 4: climate ----------
if os.path.exists(f"{OUT}/world_climate.npz"):
    cd = np.load(f"{OUT}/world_climate.npz")
    cm = json.load(open(f"{OUT}/world_climate.json"))
    P = cd["precip_annual_mm"]
    A = area_weights(P.shape)
    land = np.load(f"{OUT}/world_height.npz")["land"]
    pl = (P * A)[land].sum() / A[land].sum()
    po = (P * A)[~land].sum() / A[~land].sum()
    check("4 Climate", "Mean precipitation over land", pl, "818 (2.24 mm/day)", 700, 950, "mm/yr", "gpcp")
    check("4 Climate", "Mean precipitation over ocean", po, "1059 (2.90 mm/day)", 900, 1200, "mm/yr", "gpcp")
    check("4 Climate", "Land / ocean precipitation ratio", pl / po, 0.77, 0.65, 0.92, "", "gpcp")
    ks = cm["koppen_share_of_land_pct"]
    B = sum(v for k, v in ks.items() if k.startswith("B"))
    check("4 Climate", "Arid + semi-arid climates (Koppen B), share of land", B, "about a quarter", 20, 35, "%", "britannica")
    check("4 Climate", "Hot desert (BWh), share of land", ks["BWh"], 14.2, 10, 20, "%", "peel")
    check("4 Climate", "Tropical savanna (Aw), share of land", ks["Aw"], 11.5, 8, 15, "%", "peel")

# ---------- step 5: hydrology ----------
if os.path.exists(f"{OUT}/world_hydrology.json"):
    hy = json.load(open(f"{OUT}/world_hydrology.json"))
    hn = np.load(f"{OUT}/world_hydrology.npz")
    ze = hn["elevation_eroded_m"]
    landh = np.load(f"{OUT}/world_height.npz")["land"]
    A = area_weights(ze.shape)
    check("5 Hydrology", "River discharge to the ocean", hy["runoff_to_ocean_km3"], "40 000", 28000, 52000, "km3/yr", "trenberth")
    check("5 Hydrology", "Runoff ratio over land (runoff / precipitation)", hy["runoff_ratio"], "0.355 (40.0 / 112.6)", 0.28, 0.45, "", "trenberth")
    check("5 Hydrology", "Endorheic (closed) basins, share of land", hy["endorheic_share_of_land_pct"], 18, 12, 24, "%", "basins")
    check("5 Hydrology", "Lake area, share of land", hy["lake_share_of_land_pct"], "3.7 (all lakes > 0.002 km2)", 0.5, 3.7, "%", "glowabo",
          "the 28 km grid only resolves large lakes, so the value must stay below the all-lakes total")
    check("5 Hydrology", "Hack's law exponent h (L ~ A^h)", hy["hack_exponent"], "slightly below 0.6", 0.45, 0.65, "", "hack")
    check("5 Hydrology", "Horton bifurcation ratio", hy["bifurcation_ratio"], "3-5", 3.0, 5.0, "", "strahler",
          "fitted over Strahler orders, highest order excluded")
    check("5 Hydrology", "Mean land elevation after erosion", (ze * A)[landh].sum() / A[landh].sum(), 840, 600, 1100, "m", "segar")
    check("5 Hydrology", "Highest point after erosion", ze.max(), 8848, 7000, 9500, "m", "segar")

# ---------- report ----------
passed = sum(c["passed"] for c in checks)
lines = ["# Scientific validation", "",
         "Generated by `scripts/validate.py`. Each statistic of the generated planet is compared with a published Earth value.",
         "The planet's geography differs from Earth's, so a check passes when the value lies inside the stated plausibility band.",
         "", f"**Result: {passed} / {len(checks)} checks passed.**", ""]
step = None
for c in checks:
    if c["step"] != step:
        step = c["step"]
        lines += ["", f"## Step {step}", "", "| Check | World | Earth | Accepted band | Result | Source |", "|---|---|---|---|---|---|"]
    u = f" {c['unit']}" if c["unit"] else ""
    note = f" ({c['note']})" if c["note"] else ""
    lines.append(f"| {c['name']}{note} | {c['value']}{u} | {c['earth']}{u} | {c['band'][0]}-{c['band'][1]}{u} | "
                 f"{'PASS' if c['passed'] else 'FAIL'} | [{c['source']}](#sources) |")
lines += ["", "## Sources", ""]
for k, (t, url) in SOURCES.items():
    lines.append(f"- **{k}**: [{t}]({url})")
open(os.path.join(ROOT, "VALIDATION.md"), "w").write("\n".join(lines) + "\n")
json.dump(dict(passed=passed, total=len(checks), checks=checks), open(f"{OUT}/validation.json", "w"), indent=1)
for c in checks:
    print(("PASS " if c["passed"] else "FAIL ") + f"{c['step']:10s} {c['name']}: {c['value']} (band {c['band']})")
print(f"{passed}/{len(checks)} passed")
sys.exit(0 if passed == len(checks) else 1)
