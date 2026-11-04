"""
Region step 0: cut the region out of the planet model.

Samples the planet rasters (eroded elevation, climate, biome, Koppen class) on a regular grid over
the 100 x 100 km square, traces the coarse course of the big river through the region, and draws an
overview with the 4 x 4 tile layout.

The planet grid is ~28 km (north-south) x ~15 km (east-west) here, so this is only the large-scale
frame for the regional model; the detail comes from the next steps.

Usage:  python extract_region.py [--res 500]
Outputs (in ../output): region_context.npz, region_context.json, river_coarse.json, region_overview.png
"""
import argparse, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from region_common import (CFG, HALF_M, REGION_OUT, R_M, grid, load_world, sample_world, tile_name, xy_to_latlon)

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--res", type=float, default=500.0, help="sampling resolution in metres (default 500)")
args = ap.parse_args()
os.makedirs(REGION_OUT, exist_ok=True)

wd = load_world()
z_w = wd["hydro"]["elevation_eroded_m"]
Q_w = wd["hydro"]["discharge_m3s"]
rec_w = wd["hydro"]["receiver"].ravel()
H, W = z_w.shape
lat_c = 90 - (np.arange(H) + 0.5) / H * 180
lon_c = (np.arange(W) + 0.5) / W * 360 - 180

# ---------- sample fields ----------
x, y = grid(args.res)
lat, lon = xy_to_latlon(x, y)
ctx = dict(
    x_m=x.astype(np.float32), y_m=y.astype(np.float32), lat=lat.astype(np.float32), lon=lon.astype(np.float32),
    elevation_m=sample_world(z_w, lat, lon, 1).astype(np.float32),
    temp_jan_c=sample_world(wd["climate"]["temp_jan_c"], lat, lon, 1).astype(np.float32),
    temp_jul_c=sample_world(wd["climate"]["temp_jul_c"], lat, lon, 1).astype(np.float32),
    precip_annual_mm=sample_world(wd["climate"]["precip_annual_mm"], lat, lon, 1).astype(np.float32),
    biome=sample_world(wd["climate"]["biome"], lat, lon, 0).astype(np.int8),
    koppen=sample_world(wd["climate"]["koppen"], lat, lon, 0).astype(np.int8),
)
ctx["land"] = ctx["elevation_m"] > 0
np.savez_compressed(os.path.join(REGION_OUT, "region_context.npz"), **ctx)


# ---------- trace the big river (planet flow network) ----------
def latlon_to_xy(la, lo):
    la, lo = np.radians(la), np.radians(lo)
    lat0, lon0 = math.radians(CFG["centre_lat_deg"]), math.radians(CFG["centre_lon_deg"])
    cosc = math.sin(lat0) * np.sin(la) + math.cos(lat0) * np.cos(la) * np.cos(lo - lon0)
    c = np.arccos(np.clip(cosc, -1, 1))
    k = np.where(c > 0, c / np.sin(np.maximum(c, 1e-12)), 1.0)
    return (R_M * k * np.cos(la) * np.sin(lo - lon0),
            R_M * k * (math.cos(lat0) * np.sin(la) - math.sin(lat0) * np.cos(la) * np.cos(lo - lon0)))


land_w = wd["height"]["land"].ravel()
Qf = Q_w.ravel()
cj, ci = np.nonzero(np.ones((H, W), bool))
cx_all, cy_all = latlon_to_xy(lat_c[:, None] * np.ones((1, W)), np.ones((H, 1)) * lon_c[None, :])
in_sq = (np.abs(cx_all) <= HALF_M) & (np.abs(cy_all) <= HALF_M) & wd["height"]["land"]
start = int(np.argmax(np.where(in_sq, Q_w, -1).ravel()))
down = [start]
while land_w[down[-1]] and rec_w[down[-1]] != down[-1] and len(down) < 500:
    down.append(int(rec_w[down[-1]]))
sea_cell = down[-1] if not land_w[down[-1]] else None
mouth = down[-2] if sea_cell is not None and len(down) > 1 else down[-1]
donors = {}
for k in np.nonzero(Qf > 20)[0]:
    donors.setdefault(int(rec_w[k]), []).append(int(k))
up = [start]
while True:
    ds = donors.get(up[-1], [])
    if not ds:
        break
    nxt = max(ds, key=lambda d: Qf[d])
    px, py = latlon_to_xy(lat_c[nxt // W], lon_c[nxt % W])
    up.append(nxt)
    if abs(px) > HALF_M * 2 or abs(py) > HALF_M * 2 or len(up) > 200:
        break
path = up[::-1] + [k for k in down[1:] if land_w[k]]     # upstream -> mouth
rx, ry = latlon_to_xy(lat_c[np.array(path) // W], lon_c[np.array(path) % W])
river = dict(note="coarse planet-scale course of the square's largest river (one point per planet cell), upstream to mouth",
             points=[dict(x_m=round(float(a)), y_m=round(float(b)), discharge_m3s=round(float(Qf[k])))
                     for a, b, k in zip(rx, ry, path)],
             reaches_sea=sea_cell is not None)
if sea_cell is not None:
    sx, sy = latlon_to_xy(lat_c[sea_cell // W], lon_c[sea_cell % W])
    river["sea_point"] = dict(x_m=round(float(sx)), y_m=round(float(sy)))
json.dump(river, open(os.path.join(REGION_OUT, "river_coarse.json"), "w"), indent=1)

# ---------- statistics ----------
codes = wd["climate_meta"]["koppen_codes"]
legend = list(wd["climate_meta"]["biome_legend"].keys())
L = ctx["land"]
# nearest-cell classes: coastal land samples can pick up a sea cell (koppen -1, biome 0/1); skip those
kl = L & (ctx["koppen"] >= 0)
bl = L & (ctx["biome"] >= 2)
kv, kc = np.unique(ctx["koppen"][kl], return_counts=True)
bv, bc = np.unique(ctx["biome"][bl], return_counts=True)
stats = dict(
    centre=[CFG["centre_lat_deg"], CFG["centre_lon_deg"]], size_km=CFG["size_km"], sampling_m=args.res,
    lat_range=[round(float(lat.min()), 3), round(float(lat.max()), 3)],
    lon_range=[round(float(lon.min()), 3), round(float(lon.max()), 3)],
    land_pct=round(float(L.mean() * 100), 1),
    land_elevation_m=[round(float(ctx["elevation_m"][L].min())), round(float(ctx["elevation_m"][L].max()))],
    sea_depth_min_m=round(float(ctx["elevation_m"][~L].min())) if (~L).any() else None,
    temp_jan_c=round(float(ctx["temp_jan_c"][L].mean()), 1), temp_jul_c=round(float(ctx["temp_jul_c"][L].mean()), 1),
    precip_mm=round(float(ctx["precip_annual_mm"][L].mean())),
    koppen_pct={codes[int(k)]: round(float(c / kl.sum() * 100), 1) for k, c in zip(kv, kc)},
    biome_pct={legend[int(b)]: round(float(c / bl.sum() * 100), 1) for b, c in zip(bv, bc)},
    sea_ice_in_winter=bool((ctx["biome"][~L] == 1).any()) if (~L).any() else False,
    river_max_discharge_in_square_m3s=round(float(Qf[start])),
    river_mouth_discharge_m3s=round(float(Qf[mouth])),
    river_mouth_xy_m=[round(float(rx[-1])), round(float(ry[-1]))],
    river_reaches_sea=river["reaches_sea"],
    relief_shares_pct={"mountains_gt_1000m": round(float((ctx["elevation_m"][L] > 1000).mean() * 100), 1),
                       "foothills_300_1000m": round(float(((ctx["elevation_m"][L] > 300) & (ctx["elevation_m"][L] <= 1000)).mean() * 100), 1),
                       "plain_lt_300m": round(float((ctx["elevation_m"][L] <= 300).mean() * 100), 1)},
    tiles={tile_name(c, r): dict(x_range_m=[-HALF_M + c * 25000, -HALF_M + (c + 1) * 25000],
                                 y_range_m=[HALF_M - (r + 1) * 25000, HALF_M - r * 25000])
           for r in range(4) for c in range(4)})
json.dump(stats, open(os.path.join(REGION_OUT, "region_context.json"), "w"), ensure_ascii=False, indent=1)

# ---------- overview image ----------
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
from fonts import FONT, FONTB


def font(sz, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, sz) if FONT else ImageFont.load_default()


def ramp(zv):
    sea = [(-300, (20, 50, 105)), (-100, (40, 90, 150)), (-20, (80, 140, 190)), (0, (130, 185, 215))]
    lnd = [(0, (90, 140, 85)), (200, (125, 160, 95)), (500, (170, 175, 110)), (1000, (175, 145, 100)),
           (1500, (150, 120, 95)), (2000, (230, 230, 230))]
    out = np.zeros(zv.shape + (3,))
    for stops, m in ((sea, zv <= 0), (lnd, zv > 0)):
        xs = [s[0] for s in stops]
        for ch in range(3):
            out[..., ch] = np.where(m, np.interp(zv, xs, [s[1][ch] for s in stops]), out[..., ch])
    return out


# right panel: the region itself
PX = 800
img = Image.fromarray(np.clip(ramp(ctx["elevation_m"]), 0, 255).astype(np.uint8)).resize((PX, PX), Image.BICUBIC)
d = ImageDraw.Draw(img)
to_px = lambda xm, ym: ((xm + HALF_M) / (2 * HALF_M) * PX, (HALF_M - ym) / (2 * HALF_M) * PX)
pts = [to_px(p["x_m"], p["y_m"]) for p in river["points"]] + ([to_px(river["sea_point"]["x_m"], river["sea_point"]["y_m"])] if "sea_point" in river else [])
d.line(pts, fill=(30, 70, 170), width=5)
for k in range(1, 4):
    d.line([(k * PX / 4, 0), (k * PX / 4, PX)], fill=(255, 255, 255), width=2)
    d.line([(0, k * PX / 4), (PX, k * PX / 4)], fill=(255, 255, 255), width=2)
for r in range(4):
    for c in range(4):
        d.text((c * PX / 4 + 8, r * PX / 4 + 6), f"x{c}_y{r}", font=font(16, True), fill=(255, 255, 255),
               stroke_width=2, stroke_fill=(0, 0, 0))

# left panel: planet context +-400 km with the region square
ctx_half = 400000.0
cx, cy = np.meshgrid(np.linspace(-ctx_half, ctx_half, 400), np.linspace(ctx_half, -ctx_half, 400))
cla, clo = xy_to_latlon(cx, cy)
cz = sample_world(z_w, cla, clo, 1)
left = Image.fromarray(np.clip(ramp(cz), 0, 255).astype(np.uint8)).resize((PX, PX), Image.BICUBIC)
dl = ImageDraw.Draw(left)
s = PX / (2 * ctx_half)
dl.rectangle([(ctx_half - HALF_M) * s, (ctx_half - HALF_M) * s, (ctx_half + HALF_M) * s, (ctx_half + HALF_M) * s],
             outline=(255, 40, 40), width=4)
lpts = [((p["x_m"] + ctx_half) * s, (ctx_half - p["y_m"]) * s) for p in river["points"]]
dl.line(lpts, fill=(30, 70, 170), width=4)
dl.text((10, 8), "Регіон на тлі планети (800 × 800 км)", font=font(20, True), fill=(255, 255, 255),
        stroke_width=3, stroke_fill=(0, 0, 0))
d.text((10, PX - 34), "Регіон 100 × 100 км, 16 ділянок по 25 км", font=font(20, True), fill=(255, 255, 255),
       stroke_width=3, stroke_fill=(0, 0, 0))

LEG = 70
out = Image.new("RGB", (2 * PX + 20, PX + LEG), (24, 26, 32))
out.paste(left, (0, 0)); out.paste(img, (PX + 20, 0))
do = ImageDraw.Draw(out)
do.text((14, PX + 10), "Синя лінія: головна ріка квадрата до моря (грубий хід за моделлю планети). Деталізація — наступні кроки.",
        font=font(17), fill=(225, 225, 225))
do.text((14, PX + 38), f"Суша {stats['land_pct']}% · висоти суші {stats['land_elevation_m'][0]}–{stats['land_elevation_m'][1]} м · "
        f"січень {stats['temp_jan_c']} °C, липень {stats['temp_jul_c']} °C · опади {stats['precip_mm']} мм · "
        f"ріка до {stats['river_max_discharge_in_square_m3s']} м³/с у квадраті", font=font(17), fill=(225, 225, 225))
out.save(os.path.join(REGION_OUT, "region_overview.png"), optimize=True)
print(json.dumps({k: v for k, v in stats.items() if k != "tiles"}, ensure_ascii=False))
