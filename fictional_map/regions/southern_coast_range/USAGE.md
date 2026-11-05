# How to use the scripts — region `southern_coast_range`

This file explains, step by step, how to run every script that produces this region's map, what each one needs,
what it writes and how to use the results in Unreal Engine. Keep it up to date: every new script gets its own section here.

---

## 1. What is in this folder

```
fictional_map/
├── scripts/                     planet pipeline (whole world, ~28 km grid)
│   ├── plates.py                step 2: tectonic plates
│   ├── heightmap.py             step 3: global relief
│   ├── climate.py               step 4: climate, Köppen classes, biomes
│   ├── hydrology.py             step 5: runoff, erosion, rivers, lakes
│   ├── validate.py              scientific checks against Earth data
│   └── fonts.py                 font lookup for map labels (Linux/Windows/macOS) — not run directly
├── output/                      planet results (this region is cut from them)
└── regions/
    ├── great_river_mouth/       another region (river mouth and delta)
    └── southern_coast_range/    ← this map
        ├── region.json          region configuration (position, size, tiles, Unreal settings)
        ├── USAGE.md             this file
        ├── README.md            what the region is and its current status
        ├── MODEL_NOTES.md       scientific decisions of the regional model, with sources
        ├── VALIDATION.md        results of the regional scientific checks (generated)
        ├── VALIDATION_LANDFORMS.md results of the cirque / outwash checks (generated)
        ├── VALIDATION_PLOTS.md  results of the plot checks (generated)
        ├── VALIDATION_WATER.md  results of the water checks (generated)
        ├── scripts/
        │   ├── region_common.py shared helpers (projection, tiles, sampling) — not run directly
        │   ├── region_flow.py   flow routing / erosion kernels — not run directly
        │   ├── extract_region.py region step 0: cut the region out of the planet
        │   ├── regional_model.py region step 1: 100 m model (rivers, glaciers, lakes)
        │   ├── validate_region.py scientific checks of the regional model
        │   ├── refine_25m.py    region step 1b: 25 m refinement (gullies and spurs by erosion, cirques, outwash)
        │   ├── validate_landforms.py checks of cirques and outwash plains against Earth data
        │   ├── detail_plots.py  region step 2: 3 m plots + export for Unreal
        │   ├── validate_plots.py checks of the exported plots (seams, roughness spectrum, fidelity, layers)
        │   ├── export_water.py  region step 3: rivers and lakes as water bodies (water.json per plot)
        │   ├── validate_water.py checks of the water bodies against the terrain and Earth data
        │   └── ue_import_water.py runs INSIDE Unreal: places the water bodies of one plot
        ├── export/              Unreal heightmaps and layer masks, one folder per plot (not stored in Git)
        └── output/              region results
```

## 2. Requirements

- **Python 3.10 or newer.** On Windows install it from python.org and tick "Add python.exe to PATH".
- **Libraries:** from the repository root run

  ```
  pip install -r fictional_map/requirements.txt
  ```

  This installs `numpy`, `scipy`, `pillow`, `numba`, `scikit-image` and `matplotlib`.
- **Disk space:** planet outputs ~50 MB; this region's outputs ~0.6 GB (`regional_model.npz`, `refined_25m.npz`, `eroded_25m.npz`, `detail_prep.npz`, not stored in Git). The exported plots
  take ~20 MB each (heightmap ~13 MB plus eight layer maps), ~2 GB for all 100, so they are generated on your machine and are **not** stored in Git.
- **Memory:** 4 GB of free RAM is enough for everything that exists today.

All commands below are run from the folder that contains the script (`cd` into it first).
On Windows use `python`, on Linux/macOS `python3`.

## 3. Order of work

```
planet pipeline (once per world seed)          region pipeline (per region)
plates → heightmap → climate → hydrology  ──►   extract_region → regional_model → validate_region
                                                 → refine_25m → validate_landforms
                                                 → detail_plots → validate_plots
                                                 → export_water → validate_water → Unreal (sections 9, 9a)
                    validate after each step
```

The region reads the planet results from `fictional_map/output/`. If you regenerate the planet (for example with a
different seed), run the region scripts again afterwards.

## 4. Planet pipeline

Run once, in this order, from `fictional_map/scripts/`:

| Command | What it does | Main outputs (in `fictional_map/output/`) | Time* |
|---|---|---|---|
| `python plates.py 7` | Tectonic plates for world seed 7 (the number is the seed; another number gives another planet) | `world_plates.npz/.json`, `plates_map.png`, `history.png` | ~20 s |
| `python heightmap.py` | Global relief from the plates | `world_height.npz/.json`, `relief_map.png`, `heightmap_16bit.png` | ~20 s |
| `python climate.py` | Temperature, precipitation, Köppen classes, biomes | `world_climate.npz/.json`, `biome_map.png`, `climate_maps.png` | ~5 s |
| `python hydrology.py` | Runoff, 5 Myr of river erosion, rivers, lakes, basins | `world_hydrology.npz/.json`, `rivers_map.png`, `basins_map.png` | ~45 s |
| `python validate.py` | Compares the planet with published Earth data | `fictional_map/VALIDATION.md`, `validation.json` | ~1 s |

\* measured on the generation machine; the first `hydrology.py` run is slower because `numba` compiles its kernels.

`validate.py` exits with code 1 if any check fails. **A result is only accepted when every check passes**
(see `fictional_map/VALIDATION.md` for the checks and their sources).

## 5. Region configuration — `region.json`

| Field | Meaning | Can I change it? |
|---|---|---|
| `centre_lat_deg`, `centre_lon_deg` | Centre of the 100 × 100 km square on the planet | Yes — moves the whole map. Re-run all region scripts. |
| `size_km` | Side of the square | Only together with `tiles` (count × size must equal it). |
| `tiles.count_x/count_y`, `tiles.size_km` | Plot grid: 10 × 10 plots of 10 km | Yes, but keep plots square and count × size = `size_km`. Re-run `detail_plots.py`, `export_water.py` and the checks. |
| `tiles.vertices` | Vertices per plot side (4033 here: 2.48 m spacing for 10 km plots) | Use a size recommended by Epic: 8129, 4033, 2017, 1009. |
| `unreal.scale_xy_cm` | Distance between vertices in Unreal = plot size / (vertices − 1) | Recalculate if you change size or vertices. |
| `unreal.scale_z` | Unreal Z scale; **1000** here, giving −2560 … +2560 m (the mountains reach ~2 km) | Raise only if the relief leaves that range. |
| `model_resolution_m` | Grid of the regional process model (100 m) | Yes; smaller is slower. |

Coordinates inside the region: **x = east, y = north, in metres, (0, 0) = centre of the square**.
The square spans x and y from −50 000 to +50 000 m.

Plot names: **`tile_x{col}_y{row}`**, column 0 = west, row 0 = north. Plot `tile_x2_y1` spans
x = −30 000 … −20 000 m and y = 30 000 … 40 000 m (plot `tile_x{c}_y{r}` spans x = −50 000 + 10 000·c … +10 000 m,
y = 50 000 − 10 000·r … −10 000 m).

## 6. Region step 0 — `extract_region.py`

**Purpose:** cut the region out of the planet model and show where it is.

```
cd fictional_map/regions/southern_coast_range/scripts
python extract_region.py            # default sampling 500 m
python extract_region.py --res 250  # finer sampling (only smoother interpolation; no new detail)
```

**Needs:** the planet outputs in `fictional_map/output/` (step 4). Without them the script stops and says which files are missing.

**Writes** (to `output/` of this region):

| File | Content |
|---|---|
| `region_context.npz` | Planet fields sampled over the square: `x_m`, `y_m`, `lat`, `lon`, `elevation_m`, `temp_jan_c`, `temp_jul_c`, `precip_annual_mm`, `biome`, `koppen`, `land` |
| `region_context.json` | Summary: lat/lon range, land share, elevation range, shares of mountains / foothills / plain, climate, Köppen and biome shares, the largest river (discharge in the square and at its mouth, whether it reaches the sea), the x/y range of every plot |
| `river_coarse.json` | Coarse course of the square's largest river from its source to its mouth (one point per planet cell) with discharge, and `reaches_sea` |
| `region_overview.png` | Left: the region on the planet (800 × 800 km). Right: the region with its plot grid and the river (it continues ~18 km east of the square to the sea) |

**How to read the result:** the planet grid is about 28 km × 19 km at this latitude, so the region is covered by only
a few dozen planet cells. `region_context` is the large-scale frame (where the coast is, how high the land is, what the
climate is). Valleys, glacial landforms, river channels, floodplains and everything smaller are produced by the next steps.

To open an `.npz` file in Python:

```python
import numpy as np
d = np.load("region_context.npz")
print(d.files)                 # list of arrays
elev = d["elevation_m"]        # 2D array, row 0 = north
```

## 7. Region step 1 — `regional_model.py` and its check `validate_region.py`

**Purpose:** build the 100 m terrain model of the region: the river landscape of an old mountain range, the glaciers
of the last ice age and the landforms they left (U-shaped troughs, cirques, moraines, finger lakes), today's rivers and lakes.
The scientific decisions behind it are in [MODEL_NOTES.md](MODEL_NOTES.md).

```
cd fictional_map/regions/southern_coast_range/scripts
python regional_model.py      # ~1.5 minutes; no options
python validate_region.py     # ~2 seconds
```

**Needs:** the planet outputs (section 4). `extract_region.py` (section 6) must have been run for `validate_region.py`,
which compares the result with `output/region_context.json`.

**What it computes** (in this order):
1. Planet relief, precipitation, runoff and temperatures resampled to 100 m over a 140 × 140 km domain (larger than the square, to avoid edge effects).
2. 2 million years of river erosion and hillslope diffusion, with slow isostatic uplift that keeps the range's large-scale shape (40 steps of 50 000 years).
3. Today's and the last glacial maximum's equilibrium-line altitude (Ohmura relation, lapse rate 6.5 °C/km, LGM ~8 °C colder).
4. Glacier extent per valley (accumulation-area ratio 0.6), then U-shaped troughs, cirques and moraines.
5. Today's glaciers (none at present), lakes and rivers; where the largest river goes.

**Writes** (to `output/`):

| File | Content |
|---|---|
| `regional_model.npz` (not stored in Git — tens of MB; run the script to create it) | 100 m grids over the domain: `x_m`, `y_m` (axes), `elevation_m` (final), `elevation_fluvial_m` (before the ice ages), masks `sea`, `lake`, `rivers`, `ice_lgm`, `ice_now`, `trough_axis`, `cirque`, `moraine`; fields `discharge_m3s`, `trough_halfwidth_m`, `ela_now_m`, `ela_lgm_m`, `terminus_lgm_m`, `summer_temp_c`, `winter_temp_c`, `precip_mm` |
| `regional_model.json` | Key numbers: LGM cooling and ELAs, glacier count and extent, square statistics (heights, shares of mountains/foothills/plain, lakes, slopes, largest river) |
| `regional_relief.png` | Shaded relief of the 100 km square with lakes, rivers and the plot grid (drawn with the grid of the run that made it) |
| `regional_landforms.png` | Landform map: LGM ice extent (light blue), trough axes, cirques, moraines (brown), lakes and rivers |

`validate_region.py` writes `VALIDATION.md` (in this folder) and `output/validation_region.json`, and exits with code 1
if any check fails. **The regional model is only accepted when every check passes.**

To change the model, edit the parameter block at the top of `regional_model.py` (each parameter has a comment),
record the reason in `MODEL_NOTES.md`, then run both scripts again.

## 8. Region step 2 — `refine_25m.py`, `detail_plots.py`, `validate_plots.py`

**Purpose:** turn the 100 m model into the 100 Unreal plots (4033 × 4033 vertices, ~2.48 m apart) that join without steps.

```
cd fictional_map/regions/southern_coast_range/scripts
python refine_25m.py                          # once, ~7 minutes, ~3 GB RAM: 25 m erosion, cirques, outwash
python refine_25m.py --reuse-erosion          # ~1.5 minutes: keep the erosion stage, redo cirques and outwash only
python validate_landforms.py                  # seconds: cirque and outwash checks
python detail_plots.py --tiles x2_y1 --preview  # seconds: 1/8-resolution preview of one plot
python detail_plots.py --tiles x1_y1 x2_y1      # selected plots, full resolution (~1 minute each)
python detail_plots.py --tiles all              # all 100 plots (~1.5 s per km2: ~85 s per plot, ~2.5 hours, ~2 GB on disk)
python validate_plots.py                        # checks every plot present in export/
```

The first run of `detail_plots.py` builds `output/detail_prep.npz` (river courses, lake levels, treeline);
add `--reprep` to rebuild it after re-running `regional_model.py` or `refine_25m.py`.

**What `refine_25m.py` does:** re-runs the regional erosion physics on a 25 m grid over the square (+2 km margin),
so slopes get real gullies and spurs instead of random lumps. Areas covered by glaciers in the last ice age are eroded
only for the ~15 000 years since the ice melted, so troughs and moraines stay fresh. Lakes and the sea are fixed;
rivers coming from outside the area carry the regional model's discharge.
After the erosion it adds two glacial landforms of the last ice age (parameters at the top of the script, reasons in
MODEL_NOTES.md):
- **Cirques** at glacier valley heads above the LGM snowline where the mountain behind rises at least 200 m within 700 m:
  a floor dipping ~8° out of the mountain behind a low rock lip, and headwalls of ~50° (varying 38–60°) up to the
  surrounding ground. Size, wall steepness and orientation vary between cirques. Where the walls of neighbouring cirques
  meet, sharp ridges (arêtes) and peaks remain.
- **Outwash plains (valley trains)** where glacier-fed rivers (≥ 5 m³/s today) left the LGM ice: the valley floor is
  filled with gravel 40 m thick at the ice front, thinning downstream (e-folding 4 km, at most 15 km, never more than
  100 m), spreading sideways over the valley floor; the river then cut ~8 m into the fill, leaving terraces.

The erosion stage is saved to `output/eroded_25m.npz`; `--reuse-erosion` starts from it, which is useful when only the
cirque / outwash parameters change. `validate_landforms.py` writes `VALIDATION_LANDFORMS.md` and
`output/validation_landforms.json` (exit code 1 on failure).

**What `detail_plots.py` does for every vertex** (only world coordinates are used, so neighbouring plots share
exactly the same edge vertices):
1. cubic interpolation of the 25 m surface;
2. fine relief below 100 m with Earth-like roughness statistics (Hurst exponent 0.5), stronger on steep and rocky ground,
   weak on valley floors, plains and soil-covered slopes, none on lake floors;
3. river channels along the river courses (width = 5·Q^0.5, depth from Manning's equation), banks blending into the terrain;
4. lake floors below the lake level. Lakes are the closed basins of the 25 m surface, each flat at its spill level:
   the regional lakes' full basins plus kettle lakes and tarns on former glacier ground (closed hollows ≥ 0.5 ha and
   ≥ 2 m deep); other closed pits are model artefacts and are filled. Lake shores are smoothed (no dry hollows below the
   water level beside a lake). River water surfaces never
   rise downstream (the channel cuts through small bumps);
5. ground layers, **blended softly** — the weights of all layers add up to 255 at every vertex, as Unreal's
   weight-blended layers expect:
   rock (slopes above ~36–40°, or steep ground well above the treeline), scree (talus slopes of 28–38° near and above
   the treeline), alpine meadow (above the treeline), forest (below it), wet meadow (flat floodplains of larger rivers),
   gravel (river bars and the Holocene floodplain inside the outwash terraces), riverbed, lakebed. The treeline follows a
   growing-season mean temperature of 6.7 °C and is a ~150 m wide transition that wanders ±60 m.

**Writes** `export/tile_x{c}_y{r}/` per plot:

| File | Content |
|---|---|
| `heightmap.png` | 16-bit grayscale, 4033 × 4033, `value = 32768 + height_m × 12.8` (Z scale 1000) |
| `layer_rock.png`, `layer_scree.png`, `layer_alpine_meadow.png`, `layer_forest.png`, `layer_wet_meadow.png`, `layer_gravel.png`, `layer_riverbed.png`, `layer_lakebed.png` | 8-bit weight maps (0–255, all eight add up to 255 at every vertex) for Unreal weight-blended landscape layers |
| `tile.json` | Height range, mean, layer shares, encoding |

and `output/previews/preview_tile_x{c}_y{r}.png` (505 × 505 shaded preview coloured by layer, not in Git); after
`--tiles all` (or with `--mosaic`) all previews are combined into `output/plots_mosaic.jpg`.

`validate_plots.py` writes `VALIDATION_PLOTS.md` and `output/validation_plots.json` and exits with code 1 if a check fails:
shared edges identical (seams, heights and layer weights), roughness spectrum close to Earth's (~k⁻²), plots faithful to
the 25 m base, heights within the Unreal range, layer weights adding up to 255 everywhere with soft transitions.

## 8a. Region step 3 — `export_water.py`, `validate_water.py`

**Purpose:** the heightmaps already contain the river channels and lake basins; this step exports the **water itself**
for Unreal's Water plugin.

```
cd fictional_map/regions/southern_coast_range/scripts
python export_water.py       # ~1 minute; needs output/detail_prep.npz (detail_plots.py)
python validate_water.py     # ~3 minutes; needs the exported heightmaps
```

**Writes** `export/tile_x{c}_y{r}/water.json` per plot, `output/water_summary.json` and `output/water_overview.png`
(rivers and lakes drawn over the plot previews). `water.json` contains, in centimetres in the plot's landscape frame
(origin = north-west corner vertex, X = east, Y = south, Z = height above sea level):

| Key | Content |
|---|---|
| `rivers[]` | `id`, `length_m`, `points_cm` (spline points on the water surface, ≤ 50 m apart), and per point `width_m` (5·Q^0.5), `depth_m` (Manning), `discharge_m3s`, `velocity_ms` (Q / (width · depth)) |
| `lakes[]` | `id`, `level_m` (water level), `area_m2`, `outline_cm` (closed outline 25 m beyond the shoreline, closed along the plot edge where the lake continues into the next plot) |

Rivers and lakes continue 30 m beyond each plot edge, so the water joins without gaps when plots are shown side by side.

`validate_water.py` writes `VALIDATION_WATER.md` and `output/validation_water.json` (exit code 1 on failure): water
surfaces fall downstream, the splines run inside the carved channels, depths match the channels, flow velocities lie in
the range of natural rivers, lakes fill their basins with no dry hollows beside them, lake share of the square.

## 9. Importing a plot into Unreal Engine 5.8.4

Each plot is its own landscape (the player switches between plots).

1. Open or create the plot's level.
2. **Landscape mode → Manage → New → Import from File**, and choose `tile_x{col}_y{row}.png`.
3. Check that the resolution reads **4033 × 4033**.
4. Set **Scale X = 248.016, Scale Y = 248.016, Scale Z = 1000**.
5. Location: **0, 0, 0** when every plot is a separate level. If several plots are placed in one world,
   use X = col × 1 000 000 cm and Y = row × 1 000 000 cm so their shared edges meet.
6. **Import.** Sea level is height 0 m (heightmap value 32768); place the sea or water body at Z = 0.
7. **Layers:** create eight landscape layers named `rock`, `scree`, `alpine_meadow`, `forest`, `wet_meadow`, `gravel`,
   `riverbed`, `lakebed` in your landscape material (Landscape Layer Blend node, blend type **LB Weight Blend**), create
   a **weight-blended** Layer Info for each, then in Landscape mode → Paint → Layers, right-click each layer →
   *Import from file* and pick the matching `layer_*.png` from the plot's folder. The weights already add up to 255, so
   import order does not matter. Do not use non-weight-blended Layer Infos: they ignore the blending. Each landscape
   component samples only the layers painted on it, so eight layers stay within the usual texture-sampler budget.
8. Water: see section 9a.

Height encoding of the heightmaps: `value = 32768 + height_m × 12.8` (16-bit). With Z scale 1000 this covers
−2560 m … +2559.9 m with about 8 cm precision.

## 9a. Placing the water in Unreal (`ue_import_water.py`)

1. **Edit → Plugins:** enable **Water** and **Python Editor Script Plugin**; restart the editor.
2. Open the plot's level (landscape imported as in section 9, at location 0, 0, 0).
3. In the **Output Log**, switch the command line from *Cmd* to *Python* and run:

   ```
   py "C:/path/to/fictional_map/regions/southern_coast_range/scripts/ue_import_water.py" "C:/path/to/fictional_map/regions/southern_coast_range/export/tile_x1_y2"
   ```

   (forward slashes work on Windows too).
4. The script places a **WaterZone** over the plot, one **WaterBodyRiver** per river and one **WaterBodyLake** per lake,
   all in the outliner folder `Water/tile_x1_y2`, with *Affects Landscape* switched off (the channels and basins are
   already in the heightmap). Running it again replaces that folder's actors.
5. Read the last line it prints in the Output Log: how many rivers got per-point width / depth / velocity. The Water
   plugin does not document these per-point curves for scripting; if your engine version refuses them, every river gets
   its median width, depth and velocity instead (wide rivers then look uniform along their length; you can adjust the
   width at single spline points by hand in the Details panel).
6. Settings at the top of the script: `MIN_RIVER_Q` (skip small rivers) and `MIN_LAKE_M2` (skip small ponds) — raise
   them if a plot has too many water bodies for your target hardware (a plot has up to a few hundred small kettle ponds).

> The script has not been run inside Unreal Engine 5.8.4 by the author of this pipeline (no engine is available where
> it was generated). It uses the Water plugin's scripting functions documented by Epic (WaterBodyRiver / WaterBodyLake,
> `get_water_spline`, spline functions). If it stops with an error, send the Output Log text so it can be fixed.

## 10. Troubleshooting

| Problem | Cause and fix |
|---|---|
| `Missing planet outputs in …` | Run the planet pipeline (section 4) first. |
| `ModuleNotFoundError: numba` (or numpy, scipy, PIL) | Run `pip install -r fictional_map/requirements.txt`. |
| `hydrology.py` takes long the first time | `numba` compiles once and caches the result; later runs are faster. |
| `validate.py` or `validate_region.py` reports FAIL | The result is not accepted. Do not use it; the model has to be fixed first. |
| `validate_region.py` says `region_context.json` is missing | Run `extract_region.py` first. |
| `ue_import_water.py`: `AttributeError: module 'unreal' has no attribute 'WaterBodyRiver'` | The Water plugin is not enabled (section 9a, step 1). |
| Water bodies are invisible in Unreal | They render only inside a WaterZone; check that the WaterZone of the plot exists and covers the plot. |
| `No suitable font found for map labels` | Labels need DejaVu Sans or Arial (Cyrillic). Windows and macOS have Arial; on Linux install DejaVu (`fonts-dejavu`). The lookup is in `fictional_map/scripts/fonts.py`. |
