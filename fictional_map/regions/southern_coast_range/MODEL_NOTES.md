# Regional model — scientific decisions

Region step 1 (`scripts/regional_model.py`) turns the coarse planet data into a 100 m terrain model.
This file records every scientific decision, why it was made and what it rests on. Checks: [VALIDATION.md](VALIDATION.md).

## 1. Tectonic setting: an old mountain range

- There is no active plate boundary within ~320 km of the square (planet model). The range is therefore an old
  orogen held up by isostasy, like the Scandinavian mountains or the Appalachians, not a young range like the Andes.
- Model: rivers erode the range while the large-scale shape (4 km-smoothed relief) is pulled back towards the planet
  relief every step — slow isostatic uplift balancing erosion.

## 2. River landscape (before the ice ages)

- Stream-power erosion (K = 1·10⁻⁶ for discharge in m³/yr, m = 0.5) with the planet's runoff, plus hillslope diffusion
  (D = 0.01 m²/yr), for 2 million years. This carves the ridge-and-valley pattern: valleys run from the range crest
  in the west across the foothills to the plain in the east.

## 3. Glaciers

- **Equilibrium-line altitude (ELA)** from the empirical relation between annual precipitation and summer temperature
  at the ELA of 70 glaciers worldwide (Ohmura, Kasser & Funk 1992): P = 645 + 296·T + 9·T² (mm, °C).
  Summer temperature at every 100 m cell is the planet's summer temperature corrected with a lapse rate of 6.5 °C/km.
- **Today:** the ELA is ~2.7 km, above the highest summits (~2.1 km). There are no glaciers now; at most perennial
  snow patches on shaded high slopes.
- **Last Glacial Maximum:** Earth was ~6 °C colder on average and ~14 °C colder in the Arctic (Tierney et al. 2020).
  Interpolated to 45.6° S: ~8 °C colder, so the ELA was ~1.2 km lower, at ~1.5 km. Precipitation is kept at today's
  values (LGM was probably somewhat drier, which would raise the ELA a little).
- **Glacier extent:** for every valley, the accumulation area (above the ELA) is 60% of the whole glacier
  (accumulation-area ratio 0.6, typical of cirque and valley glaciers). Result: 44 glaciers covered ~40% of the square;
  the longest reached down to ~460 m.

## 4. Glacial landforms

- **U-shaped troughs:** the ice reshapes each valley to a parabola from an over-deepened floor up to the real
  valley shoulders (cross-section z ∝ y²). Glaciers only erode, so the new profile always lies below the old V-shaped
  valley. Over-deepening is strongest in the middle of a glacier and zero at its front.
  Measured cross-section exponent of the generated troughs: ~1.7 (field values mostly 1.3–2.5; a U-shape can form
  within one glaciation, ~50 000 years).
- **Cirques:** armchair hollows at glacier heads above the LGM ELA; a few hold small tarns.
- **Moraines:** terminal and lateral ridges (~30 m) just outside the lower ice margins.
- **Lakes:** after the ice melted, the over-deepened troughs behind the moraines filled with water: long finger lakes
  in the mountain valleys (like those of Patagonia or New Zealand's Southern Alps).

## 5. Rivers today

- Discharge from the planet's runoff routed over the final terrain. The square's largest river (~130 m³/s at the
  square's edge in this model) drains east towards the sea.

## Known limitations (v1)

- Mountain slopes are gentle for a 2 km range (median ~5°, 90% below ~20° above 1000 m): the planet relief that
  constrains the model is smooth, so the range has broad high surfaces like an old, plateau-like orogen. Steep alpine
  ridges (aretes) are not formed.
- Glaciers are placed by the accumulation-area method, not by an ice-flow simulation; ice thickness is not modelled.
- Glacial sediment (outwash plains in front of the moraines) is not modelled.
- Small rectangular artefacts can appear where moraine ridges meet the edge of a glacier system.
- The 100 m grid cannot show streams draining less than a few km²; those come with the 3 m plot detailing.
