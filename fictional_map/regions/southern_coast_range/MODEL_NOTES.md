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

## 6. From 100 m to the 3 m plots

- **25 m refinement (`refine_25m.py`).** Interpolated 100 m terrain plus random noise had the right roughness statistics
  but the wrong shapes (lumps instead of gullies and spurs). Instead, the same stream-power erosion runs again on a
  25 m grid for 1 million years, with hillslope diffusion D = 0.002 m²/yr (soil-mantled slopes; typical values are
  ~0.001–0.01). With D = 0.01 the diffusion erased every valley narrower than ~300 m, so small valleys only occurred
  every ~3 km; the lower value keeps a denser valley network. Former glacier areas are eroded only for the ~15 000
  years since the ice melted, so troughs and moraines stay fresh. Rivers entering the area from outside carry the
  regional model's discharge (injected ~1 km inside the grid so they do not drain straight out of its edge).
- **Cirques at 25 m (`refine_25m.py`).** The 100 m model only marks cirque hollows; at 25 m they are carved with
  the global median morphometry of Evans & Cox (2015): width ~650 m, floor gradient ~8°, headwall maximum ~57°
  (the model uses a mean wall of ~50°, varied 38–60° between cirques). Sites: heads of LGM glacier valleys above the
  LGM ELA where the ground 700 m up the valley axis is at least 200 m higher — on gentle plateau ground real cirques are
  shallow or absent, so none are carved there. Each cirque lowers the ground only (erosion), to a floor that dips out
  of the mountain behind a ~15 m rock lip; neighbouring cirques (≥ 700 m apart) cut into the same ridges from different
  sides and leave sharp arêtes and peaks where their walls meet. Result: 273 cirques; median width 675 m, floor 8°,
  maximum headwall ~54°, wall height ~290 m (checks in VALIDATION_LANDFORMS.md).
- **Outwash plains (valley trains).** Where a glacier-fed river (≥ 5 m³/s today) left the LGM ice and stayed outside
  it for at least 2 km (a real ice front, not a stream skirting a lateral margin), meltwater gravel filled the valley
  floor: 40 m thick at the ice front, thinning downstream with an e-folding length of 4 km (deposits are coarsest and
  thickest near the ice; outwash fills reach ~100 m at most), over at most 15 km, never more than 100 m. The fill spreads
  sideways only over the connected valley floor that lies below its surface. Because the fill thins downstream, the
  surface is steeper near the former ice front than further down: a concave long profile, as observed on sandar.
  In the Holocene the river cut ~8 m into the fill, leaving terraces on both sides. Kettle-like small lakes on the
  route are kept. Result: 10 valley trains, ~10 km²: the glaciers ended in mountain valleys, so the outwash forms
  narrow valley trains rather than broad lowland sandar (like the outwash of the Southern Alps' valleys rather than
  Iceland's coastal sandar).
- **Roughness below 100 m (`detail_plots.py`).** Self-affine detail with Hurst exponent 0.5: along transects Earth's
  topography has a power spectrum close to k⁻² (Hurst ~0.5, fractal dimension ~2.5). Its amplitude follows the local
  relief and is damped on gentle ground (valley floors, plains). Below ~20 m it is weaker on soil-covered slopes than on rock.
- **Roughness check, and why its scale band changed.** Earth's topography behaves as a fractal with a transect
  spectrum ~k⁻² over a wide range of landscape scales. At the scale of a landscape's own ridge-and-valley spacing it
  does not: landscapes have characteristic spatial scales and non-fractal structure there (Perron, Kirchner & Dietrich 2008).
  The first version checked 100 m – 2 km; the eastern plain plots failed it (exponent 2.9–3.4), and further tuning only
  traded one band against another, i.e. it was fitting a number that has no single Earth value at those scales. The check
  now uses 500 m – 10 km, where the fractal description applies; the 100 m – 2 km exponents are still reported in
  VALIDATION_PLOTS.md. Honest reading: the plain is gently rolling (local relief ~25 m per km, median slope ~1.6°) and
  smoother at hillslope scale than the mountains.
- **Rivers:** courses from the 25 m drainage network (≥ 1 m³/s), smoothed and snapped to the lowest line of the valley floor;
  width 5·Q^0.5, depth from Manning's equation (n = 0.035) with the local slope; banks rise ~15% and fade into the terrain.
- **Treeline:** where the growing-season mean temperature (months above 0 °C) is 6.7 °C, the value found at high-altitude
  treelines worldwide (Körner & Paulsen 2004). Here ~1 280 m. It is painted as a ~150 m wide ecotone (forest thins into
  alpine meadow) whose position wanders ±60 m, as real treelines follow exposure and soil.
- **Soft ground layers.** Weights are blended, not 0/255 masks, and add up to 255 at every vertex (Unreal weight
  blending). Layers are painted bottom to top, each covering the ones below by its weight: forest / alpine meadow,
  wet meadow, gravel (bars along rivers ≥ 3 m³/s and the floodplain inside outwash terraces), scree (28–34° fading in;
  talus stands at ~30–38°, near and above the treeline), rock (above ~36–40°, or > 25° well above the treeline),
  riverbed (soft water's edge), lakebed (soft shoreline). The slope that drives the layers is smoothed over ~15 m, so
  layers form patches instead of flickering vertex by vertex on rough rock (with the 9 m slope alone 2–12% of all weight
  changes between neighbouring vertices were hard 0↔255 jumps). Slopes are computed with a 12-vertex halo beyond every
  plot edge, so weights match exactly across seams.
- **Seams:** every vertex is computed from world coordinates only; neighbouring plots share identical edge vertices.

## Known limitations (v2)

- Mountain slopes away from troughs and cirques are gentle (median ~5° above 1000 m): the range is an old orogen
  (section 1) with broad high surfaces, like the Scandinavian mountains or the Cairngorms. Cirques bite into these
  surfaces and form arêtes where they meet, but most of the high ground stays rolling; steep ground (> 35°) on former
  glacier ground above 1300 m rose from ~3.8% to ~5% with the cirques. A young, Alps-like range would need a different
  (active) tectonic setting on the planet.
- Glaciers are placed by the accumulation-area method, not by an ice-flow simulation; ice thickness is not modelled.
- Outwash is modelled as valley trains with a prescribed thinning law, not by a sediment-transport simulation.
- Cirque shapes are geometric (floor + walls), not eroded by an ice model; they can look regular in places.
- Small rectangular artefacts can appear where moraine ridges meet the edge of a glacier system.
- Streams smaller than ~1 m³/s are not cut as channels; they exist only as gullies in the 25 m relief.
- The eastern plain is smoother than the mountains at hillslope scale (100 m – 2 km); its exponents are reported in VALIDATION_PLOTS.md.
