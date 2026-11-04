# How to use the scripts — region `great_river_mouth`

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
    └── great_river_mouth/       ← this map
        ├── region.json          region configuration (position, size, tiles, Unreal settings)
        ├── USAGE.md             this file
        ├── README.md            what the region is and its current status
        ├── MODEL_NOTES.md       scientific decisions of the regional model, with sources
        ├── VALIDATION.md        results of the regional scientific checks (generated)
        ├── scripts/
        │   ├── region_common.py shared helpers (projection, tiles, sampling) — not run directly
        │   ├── region_flow.py   flow routing / erosion kernels — not run directly
        │   ├── extract_region.py region step 0: cut the region out of the planet
        │   ├── regional_model.py region step 1: 100 m process model
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
- **Disk space:** the planet and region outputs take about 70 MB. The final Unreal heightmaps will take about
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
| `unreal.scale_z` | Unreal Z scale; 100 gives a height range of −256 … +256 m | Keep 100 unless the relief leaves that range. |
| `model_resolution_m` | Grid of the regional process model (100 m) | Yes; smaller is slower. |

Coordinates inside the region: **x = east, y = north, in metres, (0, 0) = centre of the square**.
The square spans x and y from −50 000 to +50 000 m.

Plot names: **`tile_x{col}_y{row}`**, column 0 = west, row 0 = north. Plot `tile_x2_y1` spans
x = 0 … 25 000 m and y = 0 … 25 000 m; the river mouth is near its middle.

## 6. Region step 0 — `extract_region.py`

**Purpose:** cut the region out of the planet model and show where it is.

```
cd fictional_map/regions/great_river_mouth/scripts
python extract_region.py            # default sampling 500 m
python extract_region.py --res 250  # finer sampling (only smoother interpolation; no new detail)
```

**Needs:** the planet outputs in `fictional_map/output/` (step 4). Without them the script stops and says which files are missing.

**Writes** (to `output/` of this region):

| File | Content |
|---|---|
| `region_context.npz` | Planet fields sampled over the square: `x_m`, `y_m`, `lat`, `lon`, `elevation_m`, `temp_jan_c`, `temp_jul_c`, `precip_annual_mm`, `biome`, `koppen`, `land` |
| `region_context.json` | Summary: lat/lon range, land share, elevation range, climate, Köppen and biome shares, river discharge, river-mouth position, the x/y range of every plot |
| `river_coarse.json` | Coarse course of the big river (one point per planet cell, upstream → mouth) with discharge |
| `region_overview.png` | Left: the region on the planet (800 × 800 km). Right: the region with the 16 plots and the river |

**How to read the result:** the planet grid is about 28 km × 15 km at this latitude, so the region is covered by only
a few dozen planet cells. `region_context` is the large-scale frame (where the coast is, how high the land is, what the
climate is). Valleys, river channels, the delta, the exact coastline and everything smaller are produced by the next steps.

To open an `.npz` file in Python:

```python
import numpy as np
d = np.load("region_context.npz")
print(d.files)                 # list of arrays
elev = d["elevation_m"]        # 2D array, row 0 = north
```

## 7. Region step 1 — `regional_model.py` and its check `validate_region.py`

**Purpose:** build the 100 m terrain model of the region from physical processes: Quaternary valley erosion,
the main river with meanders, floodplain and oxbow lakes, the Holocene delta, and the open-coast shoreface.
The scientific decisions behind it are in [MODEL_NOTES.md](MODEL_NOTES.md).

```
cd fictional_map/regions/great_river_mouth/scripts
python regional_model.py      # ~4 minutes
SEDIMENT_CASE=low python regional_model.py    # sediment lower bound (Mackenzie concentration); `high` = BQART upper bound
# on Windows (PowerShell):  $env:SEDIMENT_CASE="low"; python regional_model.py
python validate_region.py     # ~2 seconds
```

**Needs:** the planet outputs (section 4) and `output/river_coarse.json` from `extract_region.py` (section 6).
Run `extract_region.py` first whenever `region.json` changes.

**What it computes** (in this order):
1. Planet relief resampled to 100 m and smoothed (planet grid artefacts removed), plus initial small-scale roughness.
2. The main valley along the river's planet course, extended to the actual coastline; floodplain 10–18 km wide.
3. 2.6 million years of stream-power erosion and hillslope diffusion (52 steps of 50 000 years) — this carves the tributary valleys.
4. The meandering main channel (width ~610 m, depth ~20 m), natural levees, backswamps and oxbow lakes.
5. Sediment budget (Mackenzie-concentration and BQART estimates) and the Holocene delta, grown until its volume matches the budget.
6. Dean shoreface along the open coast, beaches, then lakes and rivers.

The model domain (260 × 200 km) is larger than the 100 km square so the delta and the edges are modelled properly;
maps and checks use the square only.

**Writes** (to `output/`):

| File | Content |
|---|---|
| `regional_model.npz` | 100 m grids over the whole domain: `x_m`, `y_m` (axes), `elevation_m`, `pre_delta_m`, masks `sea`, `open_sea`, `lake`, `main_channel`, `distributaries`, `delta_land`, `floodplain`, `rivers`, `shoreface`, `beach`, and `discharge_m3s` |
| `regional_model.json` | Key numbers: glacial-maximum climate, sediment budget, channel geometry, delta size, square statistics, erosion parameters |
| `regional_relief.png` | Shaded relief of the 100 km square with the 16 plots |
| `regional_water.png` | Water map: sea, lakes, main channel, distributaries, rivers ≥ 5 m³/s, floodplain and delta plain |

`validate_region.py` writes `VALIDATION.md` (in this folder) and `output/validation_region.json`, and exits with code 1
if any check fails. **The regional model is only accepted when every check passes.**

To change the model, edit the parameter block at the top of `regional_model.py` (each parameter has a comment) and
record the reason in `MODEL_NOTES.md`; then run both scripts again.

## 8. Next region steps (not written yet)

These scripts do not exist yet. Each will be documented here, with its exact command, when it is added.

1. **Plot detailing at ~3 m** — each 25 km plot refined separately with rules that depend only on world coordinates,
   so neighbouring plots match exactly on their shared edges.
2. **Export for Unreal** — one 16-bit PNG heightmap per plot (8129 × 8129) plus layer masks (forest, field, sand, rock, water).

## 9. Importing a plot into Unreal Engine 5.8.4 (once heightmaps exist)

Each plot is its own landscape (the player switches between plots).

1. Open or create the plot's level.
2. **Landscape mode → Manage → New → Import from File**, and choose `tile_x{col}_y{row}.png`.
3. Check that the resolution reads **8129 × 8129**.
4. Set **Scale X = 307.574, Scale Y = 307.574, Scale Z = 100**.
5. Location: **0, 0, 0** when every plot is a separate level. If several plots are placed in one world,
   use X = col × 2 500 000 cm and Y = row × 2 500 000 cm so their shared edges meet.
6. **Import.** Sea level is height 0 m (heightmap value 32768); place the sea or water body at Z = 0.

Height encoding of the heightmaps: `value = 32768 + height_m × 128` (16-bit). With Z scale 100 this covers
−256 m … +255.99 m with about 8 mm precision.

## 10. Troubleshooting

| Problem | Cause and fix |
|---|---|
| `Missing planet outputs in …` | Run the planet pipeline (section 4) first. |
| `ModuleNotFoundError: numba` (or numpy, scipy, PIL) | Run `pip install -r fictional_map/requirements.txt`. |
| `hydrology.py` takes long the first time | `numba` compiles once and caches the result; later runs are faster. |
| `validate.py` or `validate_region.py` reports FAIL | The result is not accepted. Do not use it; the model has to be fixed first. |
| `regional_model.py` says a file is missing | Run `extract_region.py` first (it writes `river_coarse.json`). |
| `No suitable font found for map labels` | Labels need DejaVu Sans or Arial (Cyrillic). Windows and macOS have Arial; on Linux install DejaVu (`fonts-dejavu`). The lookup is in `fictional_map/scripts/fonts.py`. |
