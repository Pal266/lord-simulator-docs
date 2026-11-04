"""
Scientific validation of the regional model (region step 1).

Checks are of three kinds:
  * Earth data   - the model's decision or value is compared with published observations;
  * physics      - the model must conserve mass / satisfy the equation it claims to use;
  * planet       - the regional model must stay consistent with the planet it was cut from.

Usage:  python validate_region.py
Writes ../VALIDATION.md and ../output/validation_region.json; exits with code 1 if any check fails.
"""
import json, os, sys
import numpy as np
from region_common import HALF_M, REGION_DIR, REGION_OUT

SOURCES = {
    "tierney": ("Tierney et al. 2020, Glacial cooling and climate sensitivity revisited (Nature) - University of Arizona summary",
                "https://news.arizona.edu/news/how-cold-was-ice-age-researchers-now-know"),
    "stanley": ("Stanley & Warne 1994, Worldwide initiation of Holocene marine deltas by deceleration of sea-level rise (abstract)",
                "https://www.searchanddiscovery.com/abstracts/html/1994/annual/abstracts/0264c.htm"),
    "fedorova": ("Fedorova et al. 2015, Lena Delta hydrology and geochemistry (Biogeosciences)",
                 "https://epic2-clone.awi.de/37164/1/Fedorova_et_al_2015_BG.pdf"),
    "mackenzie": ("Mackenzie River: 127 Mt/yr of sediment in 330 km3/yr of water (Arctic journal)",
                  "https://journalhosting.ucalgary.ca/index.php/arctic/article/download/63079/47019/180209"),
    "lenadelta": ("An Overview of the Lena River Delta Setting (Journal of Coastal Research)",
                  "https://journals.flvc.org/jcr/article/view/80930"),
    "bqart": ("Cohen et al. 2011, presenting the BQART equation of Syvitski & Milliman 2007 (Computers & Geosciences)",
              "https://floodobservatory.colorado.edu/Publications/Cohen_computers_and_geosciences_2011.pdf"),
    "dean": ("Bosboom & Stive, Coastal Dynamics, 7.2.3 Equilibrium shoreface profile: engineering applications",
             "https://geo.libretexts.org/Bookshelves/Oceanography/Coastal_Dynamics_(Bosboom_and_Stive)/07%3A_Cross-shore_transport_and_profile_development/7.02%3A_Equilibrium_shorface_profile/7.2.3%3A_Engineering_applications"),
    "ue": ("Unreal Engine Landscape Technical Guide", "https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine"),
    "planet": ("This planet's model (fictional_map/output, region_context.json)", "output/region_context.json"),
}

st = json.load(open(os.path.join(REGION_OUT, "regional_model.json")))
ctx = json.load(open(os.path.join(REGION_OUT, "region_context.json")))
m = np.load(os.path.join(REGION_OUT, "regional_model.npz"))
z = m["elevation_m"]; xs = m["x_m"]; ys = m["y_m"]
inside = (np.abs(xs)[None, :] <= HALF_M) & (np.abs(ys)[:, None] <= HALF_M)
checks = []


def check(kind, name, value, ref, lo, hi, unit, src, note=""):
    checks.append(dict(kind=kind, name=name, value=value if isinstance(value, bool) else round(float(value), 3),
                       reference=ref, band=[round(lo, 2), round(hi, 2)], unit=unit, source=src, passed=bool(lo <= value <= hi), note=note))


# --- decisions against Earth data ---
check("Earth data", "LGM July temperature in the region (glaciers need summers near 0 C)", st["lgm"]["july_c"],
      f"cooling {st['lgm']['cooling_c']} C (6 global, 14 Arctic)", 2.0, 40.0, "C", "tierney",
      "positive LGM summers -> the region stayed ice-free; it was periglacial")
check("Earth data", "Delta age (start of Holocene progradation)", st["sediment"]["delta_age_yr"], "8000-7000 yr",
      7000, 8000, "yr", "stanley")
sd = st["sediment"]
check("Earth data", "Sediment load between the Mackenzie-concentration and BQART (B = 1) estimates", sd["load_mt_yr"],
      f"{sd['mackenzie_concentration_mt_yr']}-{sd['bqart_b1_mt_yr']} Mt/yr", sd["mackenzie_concentration_mt_yr"],
      sd["bqart_b1_mt_yr"], "Mt/yr", "mackenzie", "high basin: 57% above 1000 m; Lena (lowland) is not a valid analogue")
check("Earth data", "Share of the load kept in the delta", st["sediment"]["retention"], "> 0.7 (less than 30% reaches the sea)",
      0.7, 0.9, "", "lenadelta")

# --- physics / internal consistency ---
check("physics", "Delta volume built / sediment budget", st["sediment"]["built_volume_km3"] / st["sediment"]["target_volume_km3"],
      1.0, 0.9, 1.15, "", "bqart", "mass conservation")
ch = st["channel"]
check("physics", "Main channel capacity (Manning) / river discharge", ch["capacity_m3s"] / ch["discharge_m3s"], 1.0,
      0.9, 1.1, "", "fedorova", "continuity Q = w d v with Manning velocity")

# Dean profile fit on the open coast (outside the delta)
shore = m["shoreface"]; sea = m["sea"]; land = ~sea
from scipy import ndimage
cd = ndimage.distance_transform_edt(~land) * 100.0
# with the delta the square's own coast is delta front, so the open-coast profile is checked over the whole model domain
sel = shore & m["open_sea"] & (cd > 50) & (cd < 1500) & (z < 0)
A_fit = float(np.median((-z[sel]) / cd[sel] ** (2 / 3))) if sel.any() else 0.0
check("Earth data", "Open-coast shoreface coefficient A (h = A x^2/3), whole model domain", A_fit, "0.055-0.10 (D50 ~ 0.2 mm)",
      0.05, 0.15, "m^1/3", "dean")

# --- consistency with the planet ---
pre_land = float(((m["pre_delta_m"] > 0) & inside).sum() / inside.sum() * 100)
check("planet", "Land share of the square before the Holocene delta vs planet (the planet model has no deltas)", pre_land,
      ctx["land_pct"], ctx["land_pct"] - 5, ctx["land_pct"] + 5, "%", "planet")
check("planet", "Mean land elevation vs planet sample", st["square"]["mean_land_elev_m"],
      st["square"]["planet_mean_land_elev_m"], st["square"]["planet_mean_land_elev_m"] - 20,
      st["square"]["planet_mean_land_elev_m"] + 20, "m", "planet")
check("Earth data", "Height range fits Unreal Z scale 100 (-256 ... +256 m)", float(max(abs(z[inside].min()), z[inside].max())),
      "<= 256", 0, 255.99, "m", "ue")

passed = sum(c["passed"] for c in checks)
lines = ["# Scientific validation — region `great_river_mouth`", "",
         "Generated by `scripts/validate_region.py`. Kinds: **Earth data** (compared with published observations), "
         "**physics** (the model satisfies its own equations), **planet** (consistent with the planet it was cut from).", "",
         f"**Result: {passed} / {len(checks)} checks passed.**", "",
         "| Kind | Check | Model | Reference | Accepted band | Result | Source |", "|---|---|---|---|---|---|---|"]
for c in checks:
    u = f" {c['unit']}" if c["unit"] else ""
    note = f" ({c['note']})" if c["note"] else ""
    lines.append(f"| {c['kind']} | {c['name']}{note} | {c['value']}{u} | {c['reference']} | {c['band'][0]}–{c['band'][1]}{u} | "
                 f"{'PASS' if c['passed'] else 'FAIL'} | {c['source']} |")
lines += ["", "## Sources", ""] + [f"- **{k}**: [{t}]({u})" for k, (t, u) in SOURCES.items()]
open(os.path.join(REGION_DIR, "VALIDATION.md"), "w").write("\n".join(lines) + "\n")
json.dump(dict(passed=passed, total=len(checks), checks=checks), open(os.path.join(REGION_OUT, "validation_region.json"), "w"), indent=1)
for c in checks:
    print(("PASS " if c["passed"] else "FAIL ") + f"[{c['kind']}] {c['name']}: {c['value']} (band {c['band']})")
print(f"{passed}/{len(checks)} passed")
sys.exit(0 if passed == len(checks) else 1)
