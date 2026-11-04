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

- The closest Earth analogue is the **Lena River**: similar discharge (16 800 m³/s), cold climate, huge lowland basin.
  Its load is ~680 kg/s suspended plus ~170 kg/s bedload (Fedorova et al. 2015).
- Scaled to this river's discharge with the BQART exponent Q^0.31 (Syvitski & Milliman 2007): **~26 Mt/yr**.
- The BQART equation itself, with all basin factors B = 1, gives ~336 Mt/yr, mostly because this river's basin
  includes 8 km mountains under the polar ice cap. Without data for the factor B this is treated as an upper bound
  only. It is the main open uncertainty of the region (see "Open questions").

## 5. The delta

- Modern marine deltas began to grow 8000–7000 years ago, when sea-level rise slowed (Stanley & Warne 1994).
  Delta age here: 7500 years.
- Less than 30% of the Lena's load reaches the open sea, so 70% of the load stays in the delta.
- Volume = load × age × 0.7 / 1600 kg/m³ (bulk density of young deltaic sediment) ≈ 85 km³.
- Winter sea ice and a shallow semi-enclosed sea mean weak waves: a **river-dominated (bird's-foot) delta** with
  8 distributary mouths, natural levees, marsh islands and shallow interdistributary bays.
  The distributary network is grown until its volume matches the sediment budget.

## 6. The open coast

- Shoreface outside the delta follows Dean's equilibrium profile h = A·x^(2/3) with A = 0.1 (fine sand ~0.2 mm),
  down to a closure depth of 8 m, then the planet's sea floor.
- Beaches 0.6–3 m high on the outer 200 m of land.

## Open questions and known limitations (v1)

- **Sediment supply** is the largest uncertainty (26 Mt/yr from the Lena analogue vs up to 336 Mt/yr from BQART).
  A much larger load would push the coast tens of kilometres seaward and turn most of the eastern plots into delta plain.
  The planet's own erosion model (16 Mt/yr for this basin) is too coarse to settle it.
- The delta is built geometrically and then mass-balanced; channel switching and lobe abandonment are not simulated.
- Floodplain relief (levees, scroll bars) is drawn from rules, not simulated.
- The 100 m grid cannot show streams draining less than ~5 km²; those come with the 3 m plot detailing.
- The coast is smooth at the 1–10 km scale (no spits or barrier islands yet).
