# Regional model — scientific decisions

Region step 1 (`scripts/regional_model.py`) turns the coarse planet data into a 100 m terrain model.
This file records every scientific decision, why it was made and what it rests on. Checks: [VALIDATION.md](VALIDATION.md).

## 1. Glacial history: ice-free, but periglacial

- The planet has permanent polar ice sheets and land close to the north pole, i.e. an "icehouse" climate
  in which glacial cycles like Earth's Quaternary are expected.
- At the Last Glacial Maximum Earth was about 6 °C colder on average and about 14 °C colder in the Arctic
  (Tierney et al. 2020). Interpolated to 57.8° N this gives about 9.7 °C of cooling here.
- The region's July temperature would then have been about +10.5 °C. Ice sheets need summers near 0 °C,
  so **the region was never covered by ice**: no moraines, eskers, drumlins or glacial lakes.
- The mean annual temperature would have been about −3 °C: **permafrost** (periglacial conditions).
  Its legacy is smoothed hillslopes (modelled as hillslope diffusion).
- Sea level was ~120 m lower at glacial maxima, so the whole sea floor inside the square (max depth ~55 m) was
  dry land; rivers cut down to the lower base level and the shelf was flooded again in the Holocene.

## 2. Valleys: stream-power erosion on a soft sedimentary platform

- The region lies on a stable continental platform far from plate boundaries (planet model), typically covered by
  soft sedimentary rocks. Erodibility K = 1·10⁻⁶ (for discharge in m³/yr, m = 0.5) — higher than the planet average,
  because platform cover rocks are soft.
- Erosion runs for 2.6 million years (the Quaternary) with hillslope diffusion D = 0.005 m²/yr.
- Wet climate (runoff ~580 mm/yr): closed hollows on the uplands overflow or silt up, so no upland lakes remain.
- Result: dendritic valleys, local relief ~17 m per km, median slope 0.9°, 90% of slopes below 2.4°.

## 3. The main river

- Discharge 15 000 m³/s (planet model).
- Width from hydraulic geometry w = a·Q^0.5 with a = 5 (same rule as the planet model) → ~610 m.
- Depth from Manning's equation with n = 0.030 (sand bed) and a water-surface slope of 2.5·10⁻⁵ → ~20 m, velocity ~1.2 m/s.
- Meanders: sine-generated curve (Langbein & Leopold 1966) with sinuosity ~1.5 and wavelength ~11 channel widths
  (~6.7 km); straighter in the last 8 km before the coast. An older course provides cut-off oxbow lakes.
- Floodplain 10–18 km wide with natural levees, backswamps and oxbow lakes.

## 4. Sediment supply

- The first version used the Lena River as analogue (~26 Mt/yr). That was wrong: the Lena drains a lowland basin,
  while this river's basin is high — 57% above 1000 m, 22% above 2000 m, 10% above 4000 m under the polar ice sheet,
  with more than 30% of the water coming from mountains and ice.
- Two independent estimates are combined:
  - **Mackenzie concentration** — the Arctic river with large mountain tributaries carries 127 Mt/yr in 330 km³/yr of
    water; at this river's discharge that is **~182 Mt/yr** (lower bound, because this basin's mountains are higher);
  - **BQART** (Syvitski & Milliman 2007, explains 96% of the variation between 488 rivers) with B = 1: **~336 Mt/yr**
    (upper bound; the lithology factor for this planet is unknown).
- Central value: geometric mean **~248 Mt/yr** (like the pre-dam Mississippi). Set `SEDIMENT_CASE=low` or `high`
  in the environment to run the bounds.

## 5. The delta

- Modern marine deltas began to grow 8000–7000 years ago, when sea-level rise slowed (Stanley & Warne 1994).
  Delta age here: 7500 years.
- Less than 30% of the Lena's load reaches the open sea, so 70% of the load stays in the delta.
- Volume = load × age × 0.7 / 1600 kg/m³ ≈ **810 km³**.
- The delta plain (topset +3 m at the apex to +0.4 m at the shore) progrades over the old sea floor with a foreset of
  ~0.3° until its volume equals the budget; river-dominated, so 1.5 times longer along the river axis than across it.
- Result: delta plain ~7 300 km², coast advanced up to ~115 km seaward, 16 distributary mouths, many delta lakes.

## 6. The open coast

- Shoreface outside the delta follows Dean's equilibrium profile h = A·x^(2/3) with A = 0.1 (fine sand ~0.2 mm),
  down to a closure depth of 8 m, then the planet's sea floor.
- Beaches 0.6–3 m high on the outer 200 m of land.

## Open questions and known limitations (v1)

- **Square position (decided 2026-11-04):** the square stays where it is (option A). With the revised load its eastern
  half is delta plain (channels, islands, lakes) and the open sea lies east of the square.
- **Delta morphology (to fix):** distributaries fan out almost as straight rays from one point and delta lakes are too
  many; real distributaries branch progressively and meander.
- The planet's own erosion model (16 Mt/yr for this basin) under-predicts sediment flux; it is not used here.
- The delta is built geometrically and then mass-balanced; channel switching and lobe abandonment are not simulated.
- Floodplain relief (levees, scroll bars) is drawn from rules, not simulated.
- The 100 m grid cannot show streams draining less than ~5 km²; those come with the 3 m plot detailing.
- The coast is smooth at the 1–10 km scale (no spits or barrier islands yet).
