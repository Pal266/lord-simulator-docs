# Westeros — canon, science and every decision

This map follows the rule of the fictional-world map: **realism comes first**. Canon geography (A Song of Ice and
Fire) is the starting point; the science checks it; a canon feature that does not survive the checks is changed and
listed in [Canon deviations](#canon-deviations).

## 1. Sources of canon facts

- The books (A Game of Thrones … A Dance with Dragons) and *The World of Ice and Fire*, through
  [A Wiki of Ice and Fire](https://awoiaf.westeros.org/index.php/Winterfell) and the
  [Wikipedia article on the world of the series](https://en.wikipedia.org/wiki/World_of_A_Song_of_Ice_and_Fire).
- Facts used: the Wall is ~300 miles (480 km) long, coast to coast; Westeros is "roughly the size of South America"; the
  North is nearly as big as the other kingdoms combined; Winterfell lies at the eastern edge of the Wolfswood, north of
  the western branch of the White Knife, south-west of the Long Lake, west of the Kingsroad, south of the northern
  mountains, 100 leagues south-east of Deepwood Motte, over natural hot springs; the North has hard winters and
  occasional brief summer snows; the Neck is bog and marsh; beyond the Wall lie the Haunted Forest and, far north, the
  Land of Always Winter; Dorne is the hottest, driest kingdom with the continent's only desert.
- **Outline (user decision).** The coast, the islands, the lakes and the rivers are digitised from the reference
  locator map of Westeros supplied by the project owner (`scripts/data/westeros_outline.json`, 2.8 km per map pixel),
  scaled by the Wall: 480 km from Westwatch to Eastwatch. The map ends north of the Wall at about 1 280 canon km; the
  coast beyond that edge (the Land of Always Winter) is invented. An earlier outline built only from textual facts and
  fan-measured distances had the right length but was 25–35 % too narrow; it was replaced.
- **Placed features.** Places, mountain ranges, uplands, lowlands and forests are not drawn on the map. They come from
  the textual geography and are fitted onto the map's outline with a thin-plate warp anchored on 17 features that both
  share (the Wall's ends, Skagos, Bear Island, the Long Lake, Torrhen's Square, White Harbor, Moat Cailin, the Iron
  Islands, the Trident's mouth, the Gods Eye, Gulltown, King's Landing, Tarth, Starfall, Sunspear, the Arbor). Ports
  sit on the coast; Harrenhal on the north shore of the Gods Eye; the Frostfangs and the Red Mountains follow the
  map's geography (west of the Milkwater; along Dorne's northern border).

## 2. Size (user decision, checked by the climate)

- The user asked for a smaller continent (up to −50 %). Chosen: **half the canon area — all distances × 0.71**
  (`SCALE`). The Wall is ~340 km, Castle Black – Winterfell ~560 km, the Wall – southern Dorne ~3 000 km; the land
  area is ~4.2 million km².
- Why not smaller: the continent must span enough latitude for both a cold North and a hot, dry Dorne. With lengths × 0.5
  it would span only ~16° from the Wall to Dorne.

## 3. Position on the planet

- An Earth-sized planet (radius 6 371 km) with Earth's axial tilt (23°): **classical Earth seasons** (user decision;
  not the books' multi-year seasons).
- **Castle Black at 59° N** (`LAT0`). Winterfell then lies at ~54° N, Dorne's south coast at ~32° N, the far north at ~69° N.
  - The first choice, 61° N, gave tundra (warmest month < 10 °C) just north of the Wall. Canon has the Haunted Forest
    there, and forest needs a warmest month of at least ~10 °C. At 59° N the band north of the Wall is boreal forest (Df).
  - Moving further south would make the North milder still (see section 5, change 4).

## 4. Tectonic interpretation (why the ranges are where canon puts them)

| Feature | Interpretation | Earth analogue |
|---|---|---|
| The North | An old crystalline shield, ground down by repeated glaciations: low, rolling, rocky, many lakes | Baltic and Canadian shields |
| Northern mountains (clan lands) | Old orogen on the shield, ~1.5 km summits | Scandinavian mountains (Caledonian) |
| Frostfangs | A higher range in the north-west, heavily glaciated (~3 km summits) | Coast Mountains / Scandinavian Alps |
| Mountains of the Moon | Collisional orogen on the east side, rejuvenated by rift-shoulder uplift along the Narrow Sea (~3–3.5 km) | Alps (heights), Appalachians + rift shoulder (setting) |
| Red Mountains | Suture where a Dornish block collided with the Westeros core; it continues south along western Dorne | Pyrenees (Iberia against Europe, ~3.4 km) |
| Westerlands hills, gold | An old volcanic-arc terrane: orogenic gold in old arcs | Victorian goldfields, Sierra Nevada foothills |
| The Narrow Sea | Rift between Westeros and Essos, a young passive margin; the Stepstones are remnants of the broken land bridge (the "Arm of Dorne") | Red Sea, Tyrrhenian Sea |
| The Neck | A low, subsiding basin of peat bogs and marshes between the North and the Riverlands | the Fens, Polesia |
| Winterfell's hot springs | No volcano is needed: rainwater circulates kilometres deep along faults in crystalline crust and returns hot | Bath, England (~46 °C), Hot Springs, Arkansas |
| Land of Always Winter | An ice sheet on a low bedrock platform, 68–71° N, ~2.4 km thick | Greenland |

The relief is built from these features (`scripts/canon_world.py`): continental platform ~260 m (the North +120 m),
the ranges with the summit heights above, the uplands and lowlands of `canon_geography.py`, coastal lowlands, a
continental shelf (~70 km), a slope and an abyssal plain at ~4.3 km. The canon rivers get valleys that descend all the
way to the sea, and the canon lakes get closed basins. Then the planet's water erodes everything for 5 million years
(`hydrology.py`, the same model as the fictional world).

## 4a. Mountains and rivers from the canon relief map

- **Source.** The relief map of Westeros supplied by the project owner draws the mountains, hills and forests. It was
  registered onto the outline by its coastline (thin-plate spline, median residual ~9 canon km).
- **Mountain regions** (`MOUNTAINS`, outlines from that map; summit heights from the canon and the tectonic setting):

  | Region | Summit height | Setting |
  |---|---|---|
  | Frostfangs | 3 000 m | high glaciated range (Coast Mountains, Scandinavian Alps) |
  | Northern mountains (clan lands) | 1 600 m | old orogen on the shield (Scandinavian mountains) |
  | Rills and Stony Shore hills | 800 m | worn uplands of the shield (Scottish uplands) |
  | Mountains of the Moon | 3 200 m | collisional orogen lifted by the Narrow Sea rift (Alps) |
  | Westerlands mountains (Golden Tooth) | 1 800 m | old volcanic arc (Sierra Nevada foothills, Victoria) |
  | Red Mountains (Dornish Marches) | 2 600 m | suture of the Dornish block (Pyrenees) |
  | Stormlands hills | 1 000 m | eastern end of the Dornish Marches (low mountains) |
  | Dornish coastal hills (the Tor, Ghost Hill) | 900 m | worn uplands along Dorne's north coast |
  | Skagos mountains | 1 300 m | island massif (Hebridean / Scandinavian coastal mountains) |

  The outlines are generous envelopes; inside them the relief map's rock texture decides where the mountains are
  (ragged edges, isolated massifs and passes as drawn), the height rises over ~25 km from the outline and towards the
  core of the range, and massifs of ~50 km add variety. The ranges stand on the lowland around them (the lowest land
  within ~150 km); the planet grid gives their mass to the climate. Resulting summits: Frostfangs ~3 650 m, Mountains of
  the Moon ~3 400 m, Red Mountains ~2 900 m, Westerlands ~2 200 m, northern mountains ~2 000 m, Rills ~1 100 m.
- **Science checks** (`validate_continent.py`): the mountain share of the land by the UNEP-WCMC criteria (Kapos et al.
  2000; Earth ~24 %), summit height against the width of each range (real ranges stay below ~0.07: Alps, Andes,
  Pyrenees), the highest summit, and the glaciation (the North's LGM ice sheet; the Mountains of the Moon carry a
  separate mountain ice field, as the Alps did).
- **Rivers.** The rivers of the map keep their courses: their beds never rise downstream, and where a course crosses
  higher ground the river has cut a gorge through it (antecedent or superimposed drainage: the Indus, the Columbia, the
  water gaps of the Appalachians), with a mean bed gradient of at most 6 m/km and at least 0.2 m/km (no river is
  flat). The beds are cut before the erosion and once more on the final surface, where erosion or the ice had shifted a
  valley a few km off the canon course; canon lakes are left untouched, and a river may cross a lake. Two map rivers
  began just beside a deeper valley (a stream cannot rise above a lower valley 3 km away: it would be captured), so
  their sources were moved down their own courses to the divide: river 5 by ~30 canon km, river 32 by ~10 canon km. Canon names read from the relief map:
  the Milkwater; the White Knife (headwaters, below the Long Lake, upper course, main course, estuary) and its western
  branch; the Last River, Weeping Water, Broken Branch; the Saltspear and the Fever; the Green Fork, Blue Fork, Red Fork,
  Tumblestone and the Trident; the Blackwater Rush; the Wendwater; the Mander with the Blueburn and the Cockleswhent; the
  Honeywine; the Torentine, Brimstone, Scourge and the Greenblood. The others, unlabelled on the map, are "river N".

## 4b. Coasts and islands

- **Coasts.** The outline is the digitised map (forms down to ~6 km). Below that, the model coastline is the zero level
  of (signed distance to the outline + self-affine noise with Hurst exponent 0.6, wavelengths 1.6–6 km): the level set
  of a self-affine surface is a fractal curve of dimension ~2 − H (Mandelbrot), and real coasts measure 1.1–1.5
  ([Mandelbrot 1967](https://doi.org/10.1126/science.156.3775.636): west coast of Britain ~1.25; Norway ~1.5).
  Coastal canon places damp the noise around them, so they stay on the coast.
- **Islands.** Every island of the map is its own outline (`ISLANDS`, 107 isles). Names follow the canon:
  - the Iron Islands, from the relations in each isle's article on
    [A Wiki of Ice and Fire](https://awoiaf.westeros.org/index.php/Iron_Islands): Great Wyk the largest and westernmost
    ([Great Wyk](https://awoiaf.westeros.org/index.php/Great_Wyk)); Old Wyk north-east of it and west of Orkmont
    ([Old Wyk](https://awoiaf.westeros.org/index.php/Old_Wyk)); Blacktyde the northernmost, north of Orkmont and
    north-west of Harlaw ([Blacktyde](https://awoiaf.westeros.org/index.php/Blacktyde)); Harlaw the easternmost and
    second in size ([Harlaw](https://awoiaf.westeros.org/index.php/Harlaw)); Saltcliffe south of Great Wyk; Pyke east of
    Saltcliffe and south-west of Harlaw ([Pyke](https://awoiaf.westeros.org/index.php/Pyke_(island)));
  - the Three Sisters in the Bite: Longsister the westernmost and largest, Littlesister the smallest (the central isle,
    as in *The Lands of Ice and Fire*), Sweetsister the easternmost
    ([Littlesister](https://awoiaf.westeros.org/index.php/Littlesister));
  - identified by position: Skagos and Skane, Bear Island, Fair Isle, the Arbor, Dragonstone with Driftmark (west) and
    Claw Isle, Tarth, Estermont, two of the Shield Islands (Greenshield, Southshield; the other two are below the map's
    resolution); the rest are "isle N". The Lonely Light lies outside the map.
- Islands smaller than the planet grid get their own relief: a dome from the coast, 12 m × √(area in km²), at most
  800 m (Hebrides, Orkney, Channel Islands rise 100–800 m), on a shelf 60 m deep at the coast.

## 5. Climate model (shared with the fictional world, four changes)

- `climate.py` is the fictional world's model: insolation, lapse rate, continentality, ocean currents, three-cell winds,
  moisture carried along the winds with orographic rain and rain shadows, and Köppen classes (Peel et al. 2007).
- **Change:** the subtropical highs (horse latitudes, about 30° N and S) now move with the full seasonal shift: ~35° N in
  July and ~25° N in January. Before, they were centred at 25° and moved half as far. The subtropical ridge moves
  poleward in summer ([Horse latitudes](https://en.wikipedia.org/wiki/Horse_latitudes);
  [Penn State METEO 3](https://courses.ems.psu.edu/meteo3/book/export/html/2048)), and this summer drought is what
  makes 35–40° N west coasts Mediterranean.
- Essos and Sothoryos are coarse context only (`ESSOS`, `SOTHORYOS`), so that winds, currents and moisture around
  Westeros are right. The global checks of the fictional world (land share, global Köppen shares) do not apply: this
  planet's unknown lands are not modelled.
- **Change 4 — temperatures calibrated on Earth.** The temperature formula was run on Earth's land mask (0.25°) and
  compared with the January / July normals of 72 stations (WMO 1981–2010 / 1991–2020 normals: western and central
  Europe, the Mediterranean, North America, East Asia, Chile, Argentina, South Africa, Australia, New Zealand). The old
  formula had winters 6 °C too cold on average and 4–9 °C too cold in Iberia, the nearest analogue of the Reach (Madrid
  −1.4 °C against +6.3 °C): its seasonal range grew too fast inland and the mild air of the warm ocean drifts did not
  reach far enough. Refitted: the seasonal range of land (`AMP_LAT`, `CONT`) and the warm-drift air over land
  (`MARITIME_WARM`, `MARITIME_KM`; it reaches ~2 800 km inland, as western Europe's mild winters reach Poland). Winter
  bias now ~0 °C, median error 1.5 °C in winter and 1.5 °C in summer.
  Ranges hold the maritime air back (Bergen +1.9 °C against Oslo −3 °C; Vancouver +4 °C against Prince George
  −8 °C): ground higher than the place, crossed by the wind since the coast, counts as extra distance inland, ~430 km
  per 1 000 m (`BARRIER_KM_PER_M`), fitted on the same stations with Earth's relief (ETOPO, 20′ grid). The effect is
  moderate: it halves the warm error of stations in the lee of ranges (+1.45 → +0.7 °C). The NE Pacific and the NE Atlantic coasts need the
  same warm-drift strength, so the Sunset Sea gets it too. What the formula still misses are the cold poles inside huge
  continents (Yakutsk, Winnipeg: cold air pooling far from every sea), which narrow Westeros does not have.
  Summer marine layer: along open-ocean coasts washed by a cold current, sea breezes and the coastal winds of the
  subtropical highs bring in cool sea air whatever the zonal wind (Los Angeles 22 °C, Rabat 23 °C, Cape Town 21 °C in
  summer, 28–35 °C inland). Within ~100 km of such a coast the summer is cooled by 1.66 × the current's SST anomaly and
  the dry-summer warming is suppressed (`MARINE_K`, `MARINE_KM`); enclosed seas (the Mediterranean, the Sea of Dorne)
  have no such current (`MARINE_OPEN_KM`: at least 2 000 km of open sea to the west). Summer error on the stations:
  3.7 → 3.2 °C (RMS), 1.9 → 1.5 °C (median); Oldtown, on the west coast at ~34° N, has 21.6 °C in July instead of 29 °C.
- **Precipitation checked on Earth: the Stormlands.** The same `climate.py`, run on Earth (land mask and ETOPO relief),
  was compared with the precipitation normals of 78 stations, deserts and east coasts among them. It misses the moist
  sea air that the western flanks of the subtropical highs bring to the east coasts of continents (Washington, Shanghai,
  Tokyo, Sydney get ~26 % of their real rain in the model). A fitted return flow fixed that on Earth (east coasts
  ~86 %, deserts kept at ~14 % of the land) - but only when it comes from a wide open ocean: allowed from any sea, it
  turned the Sahara and Arabia green. The Stormlands face the Narrow Sea with Essos behind it, so the return flow does
  not reach Westeros, and it was not added to the model (it would change no layer). The Rainwood therefore stays
  semi-arid (~310 mm a year), as the Earth analogues at the same latitude on the western shore of a narrow sea are:
  Valencia ~450 mm, Alicante and Murcia ~300 mm. The very wet coasts of narrow seas (Dubrovnik, Rize) lie on their
  far shore, under high mountains. User decision: accepted deviation.
- **The North after the calibration.** The North is a west coast at 49–59° N under westerlies from an open ocean, so
  its winters are maritime, as in Scotland, southern Scandinavia and northern Germany: Winterfell −1.9 / +19.5 °C (like
  Berlin or Copenhagen: snow most winters, the coldest month a little below freezing; the Rills and the clan mountains
  upwind make it ~1 °C colder). Cold-winter climates (Df) hold the
  northern half of the North; the south and the coasts are temperate (Cf). Harsh winters begin at the Wall (Castle
  Black −3.3 °C, the Haunted Forest band −9.5 °C). The colder North of the earlier model came from its cold bias.
  User decision: the science result is kept; the deviation is accepted (see "Canon deviations").
- **Change 2 — dry summers are hot.** Without soil moisture the sun heats the air instead of evaporating water (Bowen
  ratio), under clear skies: at 30–35° N, Baghdad and Phoenix reach 35 °C in July against 27–28 °C in Shanghai and
  Atlanta. Land with a dry summer half-year warms by up to 6 °C in the subtropics and lower mid-latitudes
  (`ARID_SUMMER_WARMING`).
- **Change 3 — rain shadow.** Air that has just descended a range is warmed adiabatically and dried, so it rains less
  than the loss of moisture on the windward side alone would give (the Great Basin, Patagonia, the Negev): convection is
  reduced by exp(−descent / 2 km), the descent forgotten over ~300 km downwind (`LEE_DESCENT_KM`, `LEE_FADE_KM`).
- **Dorne.** With these and the relief map (Dorne's interior is a sandy lowland, not an upland) Dorne is the hottest
  part of Westeros (July ~26 °C on average, the hottest summers by ~2 °C) with a hot desert (BWh, ~17 %) in the lee of the Red Mountains, the rest
  hot steppe and Mediterranean. The Greenblood rises in the Red Mountains: a river crossing a desert must be fed by
  mountain water (the Nile, the Colorado, the Euphrates), so its headwaters were extended from the desert, where the
  map begins it, into the mountains' southern foothills (as the Scourge and the Vaith rise near Yronwood). The extension
  rises south of the basin of the unnamed river that drains the same foothills north-east to the Sea of Dorne, so the two
  canon rivers do not cross and the Greenblood's mountain water is not captured by it. The Red Mountains' southern slopes lie in
  the lee and are dry themselves (runoff ~10–20 mm a year), so the Greenblood stays a small perennial desert river,
  ~10 m³/s at its mouth; the Brimstone and the Scourge carry less than ~1 m³/s for most of their courses (dry
  riverbeds that run after rain, like the wadis of the Negev). The engine layers export the canon rivers from where they
  carry 1 m³/s, so the Greenblood is in them along its whole course.
- **The Long Lake.** A ribbon lake ~75 km long and ~6 km wide on the former ice-sheet bed: a trough overdeepened by
  the Last Glacial Maximum ice, like Loch Ness or the Finger Lakes, so it is ~15 000 years old. On the planet grid it was
  lost: the hollow-filling and the 5 million years of sediment fill of the erosion step are far longer than the lake's
  age. The named lakes are therefore cut again into the eroded planet surface, 20 m below the lowest cell of their rim
  (`hydrology.py`, `LAKE_FLOOR_M`); a lake narrower than a cell keeps the cells its axis crosses. The continental model
  has it at its canon size (~1 300 km²).

## 6. Results so far (planet scale)

| Region | Coldest / warmest season | Precipitation | Main climates |
|---|---|---|---|
| Land of Always Winter | −17 / +3 °C | ~350 mm | tundra (ET) |
| Haunted Forest band | −9.5 / +12.9 °C | ~800 mm | boreal forest (Df, Dw), tundra on high ground |
| The North | −0.8 / +17.7 °C | ~1 080 mm | cold-winter forest (Df ~51 %) in the north, temperate (Cf ~38 %) in the south |
| Winterfell | −1.9 / +19.5 °C | ~900 mm | Df: farming like northern Germany or southern Sweden |
| Riverlands / Vale / Westerlands band | +1.2 / +17.8 °C | ~1 040 mm | temperate (Cf, Cs), Df and tundra in the mountains |
| Reach / Crownlands / Stormlands | +6.5 / +23.5 °C | ~570 mm | Mediterranean (Cs ~85 %), steppe in the south-east; Oldtown 21.6 °C in July (marine layer) |
| Dorne | +7.8 / +25.3 °C (hottest summers) | ~350 mm | hot steppe (BSh), hot desert (BWh ~17 %), Mediterranean |

All checks: `output/VALIDATION.md` (written by `scripts/validate_westeros.py`).

## Canon deviations

| Canon | Model | Status |
|---|---|---|
| The Greenblood rises in Dorne's desert (map) | Its headwaters reach into the Red Mountains' southern foothills | A perennial river across a desert needs mountain water |
| The Rainwood and the stormy, rainy Stormlands | Mediterranean Stormlands; the Rainwood semi-arid steppe (~310 mm a year) | **Accepted deviation** (user decision): the Narrow Sea is too narrow to feed an east-coast rain belt (section 5, precipitation checked on Earth). The canon check of the Rainwood in `validate_westeros.py` (≥ 1 000 mm) is reported as an accepted deviation |
| The Reach is green and fertile | Temperate, mostly Mediterranean (Cs ~85 %), steppe in the south-east | Like Iberia or California's Central Valley: fertile, dry in summer |
| The North has cold, snowy winters | Snowy but mild maritime winters south of the Wall (Winterfell −1.9 °C, cold-winter climates (D) on ~57 % of the North); harsh winters from the Wall north | **Accepted deviation** (user decision): Earth-calibrated temperatures (section 5, change 4). The two canon checks of the North in `validate_westeros.py` (cold-winter share ≥ 70 %, Winterfell's coldest season ≤ −3 °C) are reported as accepted deviations |
| Winterfell – Castle Black ~600 miles (fan measurement) | ~800 canon km on the reference map | The map's geometry is used |
| The Wall is 300 miles long | ~213 miles (340 km) | Follows from the user's size decision (lengths × 0.71) |
| Coast of the Land of Always Winter | Unknown in canon (beyond the map's edge) | Invented: a closed northern coast at ~69° N; ice sheet on it |
| Seasons last years | Classical Earth seasons | User decision |
