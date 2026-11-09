"""
Step 5 of the Westeros pipeline: export the continental model (continent.py) as engine layers for all of Westeros.

The layers are a background / world-map level: the regions (asoiaf_map/regions/*) add the detail on top. They are cut on
the same global plot grid (frame.py), so a region's plots sit exactly on a known part of a continental tile.

  * heightmap.png - per continental tile of 100 x 100 km (10 x 10 global plots): 16-bit heights, vertices every 500 m,
                    neighbouring tiles share their edge vertices; bilinear samples of the continental surface;
  * surface.png   - per tile, 8-bit class at every vertex: 0 sea, 1 land, 2 lake, 3 ice sheet (today);
  * water.json    - for the whole continent, in the continental frame: rivers (>= RIVER_Q_MIN, canon rivers >= CANON_Q_MIN) as centre lines with
                    water-surface height, discharge, width and depth; lakes as outlines with their level.

Height encoding differs from the plots (the continent spans the sea floor to the highest peaks):
height_m = HEIGHT_OFFSET_M + value * HEIGHT_STEP_M.

Usage:   python export_continent.py        (after continent.py)
Outputs: ../export/continent/ (manifest.json, water.json, tile_X{I}_Y{J}/heightmap.png, surface.png; not in Git),
         ../output/continent_export_overview.jpg
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.measure import approximate_polygon, find_contours
from shapely.geometry import Polygon
import frame

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output")
EXPORT = os.path.join(HERE, "..", "export", "continent")

TILE_PLOTS = 10                          # a continental tile = 10 x 10 global plots = 100 x 100 km
SPACING_M = 500.0                        # vertex spacing = the continental grid spacing
HEIGHT_OFFSET_M, HEIGHT_STEP_M = -6000.0, 0.2      # 16-bit: -6000 ... 7107 m in 0.2 m steps
RIVER_Q_MIN = 10.0                       # m3/s: rivers exported as lines (width >= ~16 m)
CANON_Q_MIN = 1.0                        # m3/s: smaller canon (map) rivers are exported too, from where they carry this
CANON_ZONE_CELLS = 3                     # a model channel within this many cells of a canon course follows that course
LAKE_MIN_CELLS = 4                       # lakes of >= 1 km2 are exported as outlines
LAKE_SIMPLIFY_M = 100.0                  # outline simplification tolerance
WIDTH_A, MANNING_N = 5.0, 0.035          # w = 5 Q^0.5 (hydraulic geometry, Leopold & Maddock 1953) and Manning's n
SLOPE_REACH_M = 2000.0                   # channel slope averaged along the course over this reach
SEA, LAND, LAKE, ICE = 0, 1, 2, 3


def encode(z):
    return np.clip(np.round((z - HEIGHT_OFFSET_M) / HEIGHT_STEP_M), 0, 65535).astype(np.uint16)


C = np.load(os.path.join(OUT, "continent.npz"))
xs, ys = C["x_m"].astype(np.float64), C["y_m"].astype(np.float64); dx = float(C["dx_m"])
z = C["elevation_m"]; land = C["land"]; lake = C["lake"]; Q = C["discharge_m3s"]; lake_level = C["lake_level_m"]
H, W = z.shape
cls = np.full((H, W), SEA, np.uint8); cls[land] = LAND; cls[land & C["ice_now"]] = ICE; cls[lake] = LAKE


def to_rc(x, y):
    """Continental x, y (m) -> fractional (row, col) of the continental grid."""
    return (ys[0] - y) / dx, (x - xs[0]) / dx


def cell_xy(r, c):
    return xs[0] + c * dx, ys[0] - r * dx


# ---------------- tiles ----------------
tile_m = TILE_PLOTS * frame.TILE_M
nv = int(round(tile_m / SPACING_M)) + 1
# tile (I, J) covers global plots (10 I ... 10 I + 9, 10 J ... 10 J + 9); every tile that overlaps the grid is exported
# (beyond the grid's edge, deep in the sea margin, the edge values are extended)
I_lo = math.floor((xs[0] - frame.tile_nw(0, 0)[0]) / tile_m); I_hi = math.floor((xs[-1] - frame.tile_nw(0, 0)[0]) / tile_m)
J_lo = math.floor((frame.tile_nw(0, 0)[1] - ys[0]) / tile_m); J_hi = math.floor((frame.tile_nw(0, 0)[1] - ys[-1]) / tile_m)
os.makedirs(EXPORT, exist_ok=True)
tiles = []
off = np.arange(nv) * SPACING_M
for J in range(J_lo, J_hi + 1):
    for I in range(I_lo, I_hi + 1):
        x0, y0 = frame.tile_nw(TILE_PLOTS * I, TILE_PLOTS * J)
        X, Y = np.meshgrid(x0 + off, y0 - off)
        r, c = to_rc(X, Y)
        h = ndimage.map_coordinates(z, [r, c], order=1, mode="nearest")
        s = cls[np.clip(np.round(r).astype(int), 0, H - 1), np.clip(np.round(c).astype(int), 0, W - 1)]
        name = f"tile_X{I}_Y{J}"
        d = os.path.join(EXPORT, name); os.makedirs(d, exist_ok=True)
        Image.fromarray(encode(h)).save(os.path.join(d, "heightmap.png"))
        Image.fromarray(s).save(os.path.join(d, "surface.png"), optimize=True)
        tiles.append(dict(name=name, I=I, J=J, global_plots=[TILE_PLOTS * I, TILE_PLOTS * J],
                          nw_continental_m=[round(x0, 3), round(y0, 3)], land_pct=round(100 * float((s != SEA).mean()), 2),
                          min_m=round(float(h.min()), 1), max_m=round(float(h.max()), 1)))
print(f"{len(tiles)} tiles of {nv} x {nv} vertices")

# ---------------- rivers ----------------
rec = C["receiver"].ravel()
riv = (land & ~lake & (Q >= RIVER_Q_MIN)).ravel()
# canon rivers with less water (desert rivers such as the Greenblood): from every channel cell next to a canon course
# with >= CANON_Q_MIN, the channel is followed downstream until it meets a larger river, a lake or the sea
zone = ndimage.binary_dilation(C["canon_river"], iterations=CANON_ZONE_CELLS)
wet = (land & ~lake).ravel()
small = ndimage.maximum_filter(Q, size=2 * CANON_ZONE_CELLS + 1) < RIVER_Q_MIN    # reaches with no larger river nearby
for k in np.nonzero((zone & small & land & ~lake & (Q >= CANON_Q_MIN)).ravel())[0]:
    while wet[k] and not riv[k]:
        riv[k] = True
        if rec[k] == k:
            break
        k = rec[k]
idx = np.nonzero(riv)[0]
donors = np.bincount(rec[idx], minlength=riv.size)                 # river cells flowing into each cell
start = riv & ((donors == 0) | (donors >= 2))                      # channel heads and junctions start a line
zf = z.ravel(); Qf = Q.ravel()
rivers = []
for s0 in np.nonzero(start)[0]:
    path = [s0]; k = s0
    while True:
        n_ = rec[k]
        if n_ == k:
            break
        path.append(n_)
        if not riv[n_] or start[n_]:                               # mouth (sea / lake) or the next junction
            break
        k = n_
    if len(path) < 2:
        continue
    p = np.array(path); r_, c_ = np.divmod(p, W)
    px, py = cell_xy(r_, c_)
    ws = np.minimum.accumulate(zf[p].astype(np.float64))           # the water surface never rises downstream
    sd = np.r_[0, np.cumsum(np.hypot(np.diff(px), np.diff(py)))]
    win = max(1, int(round(SLOPE_REACH_M / dx)))
    slope = np.clip(-np.gradient(ndimage.uniform_filter1d(ws, win, mode="nearest"), sd), 2e-4, 0.05) if len(p) > 1 else np.full(1, 2e-4)
    q = np.maximum(Qf[p], CANON_Q_MIN)                             # the mouth cell may be sea / lake: keep the river's flow
    q[-1] = q[-2]
    w = WIDTH_A * q ** 0.5
    dep = (q * MANNING_N / (w * slope ** 0.5)) ** 0.6
    rivers.append(dict(points_m=[[round(float(a), 1), round(float(b), 1), round(float(c), 2)] for a, b, c in zip(px, py, ws)],
                       discharge_m3s=[round(float(v), 1) for v in q], width_m=[round(float(v), 1) for v in w],
                       depth_m=[round(float(v), 2) for v in dep]))
print(f"{len(rivers)} river lines, {sum(len(r['points_m']) for r in rivers)} points")

# ---------------- lakes ----------------
lab, n = ndimage.label(lake)
lakes = []
for k, sl in enumerate(ndimage.find_objects(lab), start=1):
    m = lab[sl] == k
    if m.sum() < LAKE_MIN_CELLS:
        continue
    pad = np.pad(m, 1).astype(float)
    cont = max(find_contours(pad, 0.5), key=len)
    cont = approximate_polygon(cont, LAKE_SIMPLIFY_M / dx)
    rr = cont[:, 0] - 1 + sl[0].start; cc = cont[:, 1] - 1 + sl[1].start
    ox, oy = cell_xy(rr, cc)
    poly = Polygon(np.column_stack([ox, oy]))
    if not poly.is_valid:
        poly = poly.buffer(0)
        if poly.geom_type != "Polygon":
            poly = max(poly.geoms, key=lambda g: g.area)
    ring = np.array(poly.exterior.coords)[:-1]
    if len(ring) < 3:
        continue
    lakes.append(dict(outline_m=[[round(float(a), 1), round(float(b), 1)] for a, b in ring],
                      level_m=round(float(np.nanmedian(lake_level[sl][m])), 2), area_km2=round(float(m.sum() * dx * dx / 1e6), 2)))
print(f"{len(lakes)} lakes")
json.dump(dict(frame="continental: x = east, y = north, metres (frame.py); z = height above mean sea level",
               rivers=rivers, lakes=lakes), open(os.path.join(EXPORT, "water.json"), "w"), separators=(",", ":"))

# ---------------- manifest ----------------
man = dict(
    description="Westeros continental layers (background / world map); regions add the detail on top",
    continental_frame="azimuthal-equidistant projection centred on %.1f N %.1f E (asoiaf_map/scripts/frame.py); x = east, y = north, metres" % frame.CENTRE,
    global_grid="global plots of %.0f m; global plot (0, 0) has Winterfell in its middle; continental tile (I, J) covers global plots "
                "(%d I ... %d I + %d, %d J ... %d J + %d)" % (frame.TILE_M, TILE_PLOTS, TILE_PLOTS, TILE_PLOTS - 1, TILE_PLOTS, TILE_PLOTS, TILE_PLOTS - 1),
    tiles=dict(size_m=tile_m, vertices=nv, vertex_spacing_m=SPACING_M, naming="tile_X{I}_Y{J}; I grows east, J grows south",
               tile_frame="pixel (i, j) = vertex at x = i * spacing east and y = j * spacing south of the tile's north-west corner",
               tile_origin="north-west corner of tile (I, J) = north-west corner of global plot (10 I, 10 J), listed per tile as nw_continental_m",
               shared_edges="neighbouring tiles share their edge vertices exactly", list=tiles),
    layers=[dict(name="height", file="tile_X{I}_Y{J}/heightmap.png", format=f"PNG, 16-bit grayscale, {nv} x {nv}, row 0 = north",
                 encoding=f"height_m = {HEIGHT_OFFSET_M} + value * {HEIGHT_STEP_M}", datum="mean sea level"),
            dict(name="surface", file="tile_X{I}_Y{J}/surface.png", format=f"PNG, 8-bit, {nv} x {nv}",
                 classes={"0": "sea", "1": "land", "2": "lake", "3": "ice sheet"}),
            dict(name="water", file="water.json",
                 format="JSON, continental frame (metres, y = north): rivers - centre-line points [x, y, water-surface z] with "
                        "discharge_m3s, width_m, depth_m per point; lakes - closed outlines [x, y] with level_m and area_km2")],
    places={n_: [round(v, 1) for v in frame.canon_xy(n_)] for n_ in ("Winterfell", "Castle Black", "the Eyrie", "Riverrun", "Highgarden", "Sunspear")})
json.dump(man, open(os.path.join(EXPORT, "manifest.json"), "w"), indent=1, ensure_ascii=False)

# ---------------- overview (1/10) ----------------
s_ = 10
zz = z[::s_, ::s_]
stops = [(-4000, (20, 40, 90)), (0, (90, 140, 200)), (1, (70, 120, 70)), (300, (120, 160, 90)), (800, (190, 180, 120)),
         (1600, (150, 120, 90)), (2600, (240, 240, 240))]
rgb = np.stack([np.interp(zz, [a for a, _ in stops], [col[i] for _, col in stops]) for i in range(3)], -1)
gy, gx = np.gradient(zz); rgb *= np.clip(1 + (gx - gy) / 150, 0.6, 1.4)[..., None]
img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(img)
for rv in rivers:
    pts = [((a - xs[0]) / dx / s_, (ys[0] - b) / dx / s_) for a, b, _ in rv["points_m"]]
    dr.line(pts, fill=(40, 90, 220), width=1 if rv["discharge_m3s"][-1] < 300 else 2)
for lk in lakes:
    dr.polygon([((a - xs[0]) / dx / s_, (ys[0] - b) / dx / s_) for a, b in lk["outline_m"]], fill=(60, 120, 210))
for t in tiles:
    x0, y0 = t["nw_continental_m"]
    dr.rectangle([(x0 - xs[0]) / dx / s_, (ys[0] - y0) / dx / s_, (x0 + tile_m - xs[0]) / dx / s_, (ys[0] - y0 + tile_m) / dx / s_],
                 outline=(0, 0, 0))
img.save(os.path.join(OUT, "continent_export_overview.jpg"), quality=88)
print(os.path.join(EXPORT, "manifest.json"))
