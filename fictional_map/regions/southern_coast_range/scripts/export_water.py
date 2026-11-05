"""
Region step 3: export rivers and lakes as water bodies for Unreal Engine's Water plugin.

The plots' terrain already contains the river channels and lake basins (detail_plots.py). This script exports the
water itself, per plot, in the plot's own Unreal coordinates:

  * rivers - one spline per river line (from its channel head, or the point where it enters the plot, down to the
             next junction, lake or plot edge), with per-point water-surface height, width (w = 5 Q^0.5),
             depth (Manning's equation), discharge and mean velocity v = Q / (w d);
  * lakes  - one closed outline per lake (25 m beyond the shoreline mask, so the shore is covered), with its water level.

Coordinates in water.json: centimetres, relative to the plot's landscape origin (the north-west corner vertex of the
heightmap), X = east, Y = south (heightmap rows), Z = height above sea level - exactly the frame of a landscape
imported at location (0, 0, 0) with Z scale 1000 (see USAGE.md, section 9).

Usage:  python export_water.py          (needs ../output/detail_prep.npz from detail_plots.py)
Writes: ../export/tile_x{c}_y{r}/water.json, ../output/water_summary.json, ../output/water_overview.jpg
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.measure import approximate_polygon, find_contours
from region_common import CFG, HALF_M, REGION_OUT
import detail_plots as dp

SIMPLIFY_M = 1.0          # river centre-line tolerance (the channel is >= 5 m wide)
MAX_SEG_M = 50.0          # longest spline segment (width / depth change smoothly along it)
OVERLAP_M = 30.0          # rivers and lakes continue this far beyond the plot edge (no gap at seams)
WATER_BELOW_BANK_M = 0.3  # water surface below the spline-sampled valley floor, as carved in detail_plots.py
LAKE_MARGIN_CELLS = 1     # lake outline drawn one 25 m cell beyond the lake mask
LAKE_SIMPLIFY_M = 3.0
MIN_LAKE_M2 = 2 * 625.0   # smaller ponds are left out


def to_local(x, y, col, row):
    x0 = -HALF_M + col * dp.TILE_M; y0 = HALF_M - row * dp.TILE_M
    return (x - x0) * 100.0, (y0 - y) * 100.0


def simplify_line(p):
    """Douglas-Peucker on the centre line, then split long segments; returns indices into p."""
    keep = approximate_polygon(p, SIMPLIFY_M)
    # approximate_polygon returns coordinates; map back to indices (they are exact copies of input points)
    tree = {tuple(q): k for k, q in enumerate(map(tuple, p))}
    idx = [tree[tuple(q)] for q in keep]
    out = [idx[0]]
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    for a, b in zip(idx[:-1], idx[1:]):
        n = int(math.ceil((seg[b] - seg[a]) / MAX_SEG_M))
        for k in range(1, n):
            out.append(int(np.searchsorted(seg, seg[a] + k * (seg[b] - seg[a]) / n)))
        out.append(b)
    return np.unique(np.array(out))


def main():
    prep = dict(np.load(dp.PREP))
    P = prep["river_pts"]; L = prep["river_line_len"]
    starts = np.r_[0, np.cumsum(L)[:-1]]
    Q = prep["river_q"]; Wd = prep["river_w"]; D = prep["river_d"]; WS = prep["river_ws"] - WATER_BELOW_BANK_M
    res = float(prep["res"]); x0g = float(prep["x0"]); y0g = float(prep["y0"])
    # lakes (25 m grid): fill islands (a lake water body has no holes - islands rise above the water anyway)
    lake = prep["lake"] & (prep["lake_level"] > -9000)
    lab, nl = ndimage.label(lake)
    area = ndimage.sum(lake, lab, range(1, nl + 1)) * res * res
    level = ndimage.median(prep["lake_level"], lab, range(1, nl + 1))
    summary = dict(rivers=0, river_points=0, river_km=0.0, lakes=0, lake_points=0, plots={})
    tiles = [(c, r) for r in range(CFG["tiles"]["count_y"]) for c in range(CFG["tiles"]["count_x"])]
    for c, r in tiles:
        xa = -HALF_M + c * dp.TILE_M - OVERLAP_M; xb = xa + dp.TILE_M + 2 * OVERLAP_M
        yb = HALF_M - r * dp.TILE_M + OVERLAP_M; ya = yb - dp.TILE_M - 2 * OVERLAP_M
        rivers = []
        for li, (s0, n) in enumerate(zip(starts, L)):
            p = P[s0:s0 + n]
            inside = (p[:, 0] >= xa) & (p[:, 0] <= xb) & (p[:, 1] >= ya) & (p[:, 1] <= yb)
            if not inside.any():
                continue
            # contiguous runs inside the (extended) plot
            d = np.diff(np.r_[0, inside.astype(np.int8), 0])
            for a, b in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]):
                if b - a < 4:
                    continue
                sl = slice(s0 + a, s0 + b)
                k = simplify_line(P[sl]) + s0 + a
                X, Y = to_local(P[k, 0], P[k, 1], c, r)
                ws = WS[k]
                rivers.append(dict(
                    id=f"river_{li:04d}_{a}",
                    length_m=round(float(np.hypot(*np.diff(P[sl], axis=0).T).sum()), 1),
                    points_cm=[[round(float(u), 1), round(float(v), 1), round(float(w_ * 100.0), 1)] for u, v, w_ in zip(X, Y, ws)],
                    width_m=[round(float(v), 2) for v in Wd[k]],
                    depth_m=[round(float(v), 2) for v in D[k]],
                    discharge_m3s=[round(float(v), 2) for v in Q[k]],
                    velocity_ms=[round(float(v), 3) for v in Q[k] / (Wd[k] * D[k])]))
        # lakes: contours of the lake mask cropped to the extended plot
        lakes = []
        ia = max(0, int((xa - x0g) / res) - 2); ib = min(lake.shape[1], int((xb - x0g) / res) + 3)
        ja = max(0, int((y0g - yb) / res) - 2); jb = min(lake.shape[0], int((y0g - ya) / res) + 3)
        sub_lab = lab[ja:jb, ia:ib]
        for lid in np.unique(sub_lab[sub_lab > 0]):
            if area[lid - 1] < MIN_LAKE_M2:
                continue
            m = ndimage.binary_fill_holes(sub_lab == lid)
            m = ndimage.binary_dilation(m, iterations=LAKE_MARGIN_CELLS)
            for cont in find_contours(np.pad(m, 1).astype(float), 0.5):
                cont = approximate_polygon(cont - 1, LAKE_SIMPLIFY_M / res)
                if len(cont) < 4:
                    continue
                xs = x0g + (cont[:, 1] + ia) * res; ys = y0g - (cont[:, 0] + ja) * res
                xs = np.clip(xs, xa, xb); ys = np.clip(ys, ya, yb)        # outline closes along the plot edge
                X, Y = to_local(xs, ys, c, r)
                # outer outlines only (holes were filled); drop degenerate ones squeezed onto the plot edge
                a2 = 0.5 * abs(np.dot(X, np.roll(Y, 1)) - np.dot(Y, np.roll(X, 1))) / 1e4
                if a2 < MIN_LAKE_M2:
                    continue
                lakes.append(dict(id=f"lake_{lid:04d}", level_m=round(float(level[lid - 1]), 2),
                                  area_m2=round(float(area[lid - 1])), outline_cm=[[round(float(u), 1), round(float(v), 1)] for u, v in zip(X[:-1], Y[:-1])]))
        name = f"tile_x{c}_y{r}"
        out = dict(plot=name, units="cm", frame="landscape origin = north-west corner vertex; X east, Y south, Z height above sea level",
                   landscape_scale=[CFG["unreal"]["scale_xy_cm"], CFG["unreal"]["scale_xy_cm"], CFG["unreal"]["scale_z"]],
                   plot_size_cm=dp.TILE_M * 100.0,
                   rivers=rivers, lakes=lakes)
        os.makedirs(os.path.join(dp.EXPORT, name), exist_ok=True)
        json.dump(out, open(os.path.join(dp.EXPORT, name, "water.json"), "w"))
        summary["plots"][name] = dict(rivers=len(rivers), lakes=len(lakes))
        summary["rivers"] += len(rivers); summary["lakes"] += len(lakes)
        summary["river_points"] += sum(len(v["points_cm"]) for v in rivers)
        summary["lake_points"] += sum(len(v["outline_cm"]) for v in lakes)
        summary["river_km"] += sum(v["length_m"] for v in rivers) / 1000
        print(name, len(rivers), "rivers,", len(lakes), "lakes", flush=True)
    summary["river_km"] = round(summary["river_km"], 1)
    json.dump(summary, open(os.path.join(REGION_OUT, "water_summary.json"), "w"), indent=1)
    overview(summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "plots"}))


def overview(summary):
    """Water bodies drawn over the mosaic of plot previews."""
    img = Image.open(dp.MOSAIC).convert("RGB")
    T = img.width // CFG["tiles"]["count_x"]
    dr = ImageDraw.Draw(img)
    s = T / (dp.TILE_M * 100.0)
    for name in summary["plots"]:
        c, r = (int(v[1:]) for v in name.replace("tile_", "").split("_"))
        w = json.load(open(os.path.join(dp.EXPORT, name, "water.json")))
        for lk in w["lakes"]:
            dr.polygon([(c * T + u * s, r * T + v * s) for u, v in lk["outline_cm"]], outline=(20, 60, 200))
        for rv in w["rivers"]:
            pts = [(c * T + u * s, r * T + v * s) for u, v, _ in rv["points_cm"]]
            q = max(rv["discharge_m3s"])
            dr.line(pts, fill=(0, 90, 255), width=1 if q < 20 else 2 if q < 80 else 3)
    img.save(os.path.join(REGION_OUT, "water_overview.jpg"), quality=88)


if __name__ == "__main__":
    main()
