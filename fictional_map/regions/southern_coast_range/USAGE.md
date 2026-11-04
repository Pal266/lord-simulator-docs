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
        ├── scripts/
        │   ├── region_common.py shared helpers (projection, tiles, sampling) — not run directly
        │   ├── region_flow.py   flow routing / erosion kernels — not run directly
        │   ├── extract_region.py region step 0: cut the region out of the planet
        │   ├── regional_model.py region step 1: 100 m model (rivers, glaciers, lakes)
        │   └── validate_region.py scientific checks of the regional model
        └── output/              region results
```

## 2. Requirements

- **Python 3.10 or newer.** On Windows install it from python.org and tick "Add python.exe to PATH".
- **Libraries:** from the repository root run

  ```
  pip install -r fictional_map/requirements.txt
  ```

  This installs `numpy`, `scipy`, `pillow` and `numba`.
- **Disk space:** the planet outputs take about 50 MB, this region's outputs about 25 MB. The final Unreal heightmaps will take about
  130 MB per plot (about 2 GB for all 16), so they are generated on your machine and are **not** stored in Git.
- **Memory:** 4 GB of free RAM is enough for everything that exists today.

All commands below are run from the folder that contains the script (`cd` into it first).
On Windows use `python`, on Linux/macOS `python3`.

## 3. Order of work

```
planet pipeline (once per world seed)          region pipeline (per region)
plates → heightmap → climate → hydrology  ──►   extract_region → regional_model → validate_region → (next steps, section 8)
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
| `tiles.count_x/count_y`, `tiles.size_km` | Plot grid: 4 × 4 plots of 25 km | Yes, but keep plots square. |
| `tiles.vertices` | Vertices per plot side (8129 = largest size recommended by Epic) | Use a recommended size: 8129, 4033, 2017, 1009. |
| `unreal.scale_xy_cm` | Distance between vertices in Unreal = plot size / (vertices − 1) | Recalculate if you change size or vertices. |
| `unreal.scale_z` | Unreal Z scale; **1000** here, giving −2560 … +2560 m (the mountains reach ~2 km) | Raise only if the relief leaves that range. |
| `model_resolution_m` | Grid of the regional process model (100 m) | Yes; smaller is slower. |

Coordinates inside the region: **x = east, y = north, in metres, (0, 0) = centre of the square**.
The square spans x and y from −50 000 to +50 000 m.

Plot names: **`tile_x{col}_y{row}`**, column 0 = west, row 0 = north. Plot `tile_x2_y1` spans
x = 0 … 25 000 m and y = 0 … 25 000 m.

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
| `region_overview.png` | Left: the region on the planet (800 × 800 km). Right: the region with the 16 plots and the river (it continues ~18 km east of the square to the sea) |

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
| `regional_model.npz` | 100 m grids over the domain: `x_m`, `y_m` (axes), `elevation_m` (final), `elevation_fluvial_m` (before the ice ages), masks `sea`, `lake`, `rivers`, `ice_lgm`, `ice_now`, `trough_axis`, `cirque`, `moraine`; fields `discharge_m3s`, `trough_halfwidth_m`, `ela_now_m`, `ela_lgm_m`, `terminus_lgm_m`, `summer_temp_c`, `winter_temp_c`, `precip_mm` |
| `regional_model.json` | Key numbers: LGM cooling and ELAs, glacier count and extent, square statistics (heights, shares of mountains/foothills/plain, lakes, slopes, largest river) |
| `regional_relief.png` | Shaded relief of the 100 km square with lakes, rivers and the 16 plots |
| `regional_landforms.png` | Landform map: LGM ice extent (light blue), trough axes, cirques, moraines (brown), lakes and rivers |

`validate_region.py` writes `VALIDATION.md` (in this folder) and `output/validation_region.json`, and exits with code 1
if any check fails. **The regional model is only accepted when every check passes.**

To change the model, edit the parameter block at the top of `regional_model.py` (each parameter has a comment),
record the reason in `MODEL_NOTES.md`, then run both scripts again.

## 8. Next region steps (not written yet)

These scripts do not exist yet. Each will be documented here, with its exact command, when it is added.

1. **Plot detailing at ~3 m** — each 25 km plot refined separately so neighbouring plots match exactly on their shared edges.
2. **Export for Unreal** — one 16-bit PNG heightmap per plot (8129 × 8129) plus layer masks (forest, meadow, rock, snow, water).

## 9. Importing a plot into Unreal Engine 5.8.4 (once heightmaps exist)

Each plot is its own landscape (the player switches between plots).

1. Open or create the plot's level.
2. **Landscape mode → Manage → New → Import from File**, and choose `tile_x{col}_y{row}.png`.
3. Check that the resolution reads **8129 × 8129**.
4. Set **Scale X = 307.574, Scale Y = 307.574, Scale Z = 1000**.
5. Location: **0, 0, 0** when every plot is a separate level. If several plots are placed in one world,
   use X = col × 2 500 000 cm and Y = row × 2 500 000 cm so their shared edges meet.
6. **Import.** Sea level is height 0 m (heightmap value 32768); place the sea or water body at Z = 0.

Height encoding of the heightmaps: `value = 32768 + height_m × 12.8` (16-bit). With Z scale 1000 this covers
−2560 m … +2559.9 m with about 8 cm precision.

## 10. Troubleshooting

| Problem | Cause and fix |
|---|---|
| `Missing planet outputs in …` | Run the planet pipeline (section 4) first. |
| `ModuleNotFoundError: numba` (or numpy, scipy, PIL) | Run `pip install -r fictional_map/requirements.txt`. |
| `hydrology.py` takes long the first time | `numba` compiles once and caches the result; later runs are faster. |
| `validate.py` or `validate_region.py` reports FAIL | The result is not accepted. Do not use it; the model has to be fixed first. |
| `validate_region.py` says `region_context.json` is missing | Run `extract_region.py` first. |
| `No suitable font found for map labels` | Labels need DejaVu Sans or Arial (Cyrillic). Windows and macOS have Arial; on Linux install DejaVu (`fonts-dejavu`). The lookup is in `fictional_map/scripts/fonts.py`. |
