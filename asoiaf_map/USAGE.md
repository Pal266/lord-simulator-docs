# Westeros map — how to generate the layers

A physically plausible map of Westeros, built in levels that fit inside each other:

1. **Planet** (0.25°, ~28 km): relief from the canon geography, climate with Earth's seasons, rivers.
2. **Continent** (500 m): all of Westeros on one grid — relief, rivers, lakes, the Last Glacial Maximum ice sheet —
   exported as engine layers.
3. **Regions** (detailed blocks of 10 × 10 km plots, to be added): each will be cut from the same continental model and
   placed on one global plot grid, so regions generated at different times join without seams.

## 1. Requirements

Python 3.10+ and:

```
pip install -r asoiaf_map/requirements.txt
```

Memory: ~6 GB for the continent at 500 m. Generated files (`output/`, `export/`) are
not stored in Git.

## 2. Files

```
asoiaf_map/
├── USAGE.md, requirements.txt
├── CANON.md                      canon facts and their sources, scale, position, tectonics, canon deviations
└── scripts/                      planet and continent (run from this folder)
    ├── canon_geography.py        canon geography: outline, ranges, uplands, places (imported)
    ├── data/westeros_outline.json  coast, islands, lakes, rivers digitised from the reference map
    ├── data/relief_texture.png   rock texture of the canon relief map (5 km raster) for the mountain regions
    ├── frame.py                  continental frame and global plot grid (imported)
    ├── flow.py, fonts.py         flow-routing / erosion kernels, map fonts (imported)
    ├── canon_world.py            step 1: planet relief
    ├── climate.py                step 2: climate, Köppen classes
    ├── hydrology.py              step 3: runoff, rivers, lakes, erosion on the planet grid
    ├── validate_westeros.py      checks of steps 1–3
    ├── continent.py              step 4: continental model
    ├── validate_continent.py     checks of step 4
    ├── export_continent.py       step 5: continental engine layers (all of Westeros)
    └── validate_continent_export.py  checks of step 5
```

## 3. Order of work

Planet and continent, from `asoiaf_map/scripts/`:

```
python canon_world.py          # ~25 s
python climate.py              # ~5 s
python hydrology.py            # ~45 s
python validate_westeros.py    # science checks must pass; canon checks are reported
python continent.py            # ~20 min -> output/continent.npz
python validate_continent.py
python export_continent.py     # ~20 s  -> export/continent/
python validate_continent_export.py
```

Every validator writes its report to `output/` (`VALIDATION*.md`) and exits with code 1 if a check fails.
A result is accepted only when all science checks pass. The checks compare the model with published Earth data
(hypsometry, landscape spectra, coastline fractal dimension, relief isotropy, lake shares, ice-sheet extents); the sources
are listed in each report.

## 4. The global plot grid

- **Continental frame** (`scripts/frame.py`): azimuthal-equidistant projection centred on 52° N 0° E; x = east,
  y = north, metres.
- **Global plots**: 10 × 10 km, global plot (0, 0) has Winterfell in its middle; index i grows east, j grows south.
  `frame.tile_nw(i, j)` gives the continental position of the plot's north-west corner.
- A region will be a block of global plots; every value computed from continental coordinates only, so a plot is the
  same whichever region produces it.

## 5. Continental layers — all of Westeros (`export/continent/`)

A background / world-map level for the whole continent; the regions add the detail on top. `manifest.json` lists
every tile with its continental position.

- **Tiles** `tile_X{I}_Y{J}`: 100 × 100 km = 10 × 10 global plots; tile (I, J) covers global plots
  (10 I … 10 I + 9, 10 J … 10 J + 9). 201 × 201 vertices every 500 m, row 0 = north; neighbouring tiles share their edge
  vertices.
- **`heightmap.png`**: 16-bit, `height_m = −6000 + value × 0.2` (sea floor to the highest peaks). Bilinear samples of the continental surface.
- **`surface.png`**: 8-bit class per vertex: 0 sea, 1 land, 2 lake, 3 ice sheet.
- **`water.json`** (one file for the continent), continental frame (metres, x east, **y north**): rivers of at least
  10 m³/s, and the map's (canon) rivers from where they carry 1 m³/s (desert rivers such as the Greenblood), as centre lines `[x, y, water-surface z]` with `discharge_m3s`, `width_m`, `depth_m` per point; lakes of at
  least 1 km² as outlines with `level_m` and `area_km2`.

The 500 m surface carries the large forms (ranges, valleys, big rivers, lakes); the regions will add the detail on
top of it.

## 6. Model decisions

In short below; the canon sources and the full reasoning are in [CANON.md](CANON.md).

- **Size:** half the canon area — all canon distances × 0.71 (`canon_geography.SCALE`). Smaller would not span the
  latitudes needed for both a cold North and a hot, dry Dorne.
- **Position and seasons:** an Earth-sized planet with Earth's axial tilt — Earth's seasons, not the books' multi-year
  ones. Castle Black at 59° N (`LAT0`): Winterfell ~54° N, Dorne's south coast ~32° N. At 61° N the band north of the
  Wall was tundra; canon puts the Haunted Forest there, which needs a warmest month of at least ~10 °C.
- **Canon geography** (`canon_geography.py`): the coast, islands, lakes and rivers are digitised from the reference
  locator map (scaled by the Wall, 480 km); places, ranges and uplands come from the books' textual geography, fitted
  onto that outline.
- **Mountains** (`canon_geography.MOUNTAINS`): outlined from the canon relief map (Frostfangs, the northern mountains,
  the Rills and the Stony Shore, the Mountains of the Moon, the Westerlands, the Red Mountains with the Dornish
  Marches); heights from the canon and the tectonic setting; checked against Earth's mountain share (~24 % of the land)
  and the proportions of real ranges.
- **Rivers** keep their canon courses: their beds never rise downstream; where a course crosses higher ground the river
  has cut a gorge (antecedent drainage, as the Indus or the Columbia), with a mean bed gradient of at most 6 m/km.
- **Tectonics** behind the relief (`canon_world.py`): the North is an old glaciated shield (Baltic, Canadian shields);
  the northern mountains an old orogen (Scandinavian mountains); the Frostfangs a high glaciated range; the Mountains
  of the Moon a collisional orogen lifted again by the Narrow Sea rift (Alps, Red Sea); the Red Mountains a suture of
  a Dornish block (Pyrenees); the Westerlands an old volcanic arc with orogenic gold; the Neck a subsiding peat basin
  (Fens, Polesia); the Land of Always Winter an ice sheet on a low platform (Greenland). Winterfell's hot springs need
  no volcano: deep circulation of rainwater along faults (Bath, England).
- **Climate** (`climate.py`): the fictional world's model with four changes — the subtropical highs centred at 30°
  with the full seasonal shift (~35° N in July); dry summers are hot (up to +6 °C: Bowen ratio, clear skies); a rain
  shadow behind ranges (descending air dries); temperatures calibrated on 72 Earth stations (seasonal range, the
  reach of the warm ocean drifts, ranges holding the maritime air back,
  the cool summer marine layer of cold-current coasts). Dorne is then the hottest region with a hot desert in the lee of the Red Mountains,
  the Reach Mediterranean, and the North maritime (Winterfell −1.9 °C in winter), with harsh winters from the Wall
  north.
  Essos and Sothoryos are coarse context only.
- **Coasts and islands** (`continent.py`): the map's outline with fractal detail below 6 km (dimension ~1.25, like
  Britain's coast); every island of the map modelled separately (the Iron Islands as seven isles, the Three Sisters as
  three) — see CANON.md.
- **Erosion** (`continent.py`): stochastic flow paths on a rough initial surface, so drainage networks branch and the
  relief has no grid-aligned artefacts (checked by an isotropy test).
- **Glaciation** (`continent.py`): the Last Glacial Maximum ice sheet of the North reaches ~56° N, so Winterfell (~54° N)
  lay just beyond it; the Mountains of the Moon carried their own ice field, as the Alps did.

### Canon deviations

See [CANON.md](CANON.md#canon-deviations): the Greenblood's headwaters reach into the Red Mountains; the Reach is
Mediterranean with dry patches; the Wall is ~340 km (size decision); the far north is invented; Earth's seasons.
