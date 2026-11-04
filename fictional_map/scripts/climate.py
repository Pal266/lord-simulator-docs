"""
Step 4 of the world pipeline: climate and biomes.

Simplified physical model, two seasons (northern July / northern January):
  * Temperature: latitude (insolation) + elevation lapse rate (6.5 C/km)
    + seasonal amplitude that grows with latitude and continentality (distance from the upwind ocean)
    + sea-surface anomalies from ocean currents (cold eastern / warm western boundary currents).
  * Winds: three-cell circulation - trade easterlies, westerlies, polar easterlies;
    belts shift ~5 degrees with the seasons.
  * Rain belts: ITCZ (pulled poleward over large continents in summer = monsoons),
    dry subtropical highs, wet mid-latitude storm tracks, dry poles.
  * Moisture is carried along the winds: evaporates over warm ocean, rains out over land,
    extra rain on windward slopes, rain shadow behind mountains.
  * Biomes: Koppen/Whittaker-style classification from temperature, precipitation and seasonality.

Inputs : world_height.npz, world_plates.json
Outputs: biome_map.png, climate_maps.png, world_climate.npz, world_climate.json
"""
import json, math, os
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
HD = np.load(f"{OUT}/world_height.npz")
META = json.load(open(f"{OUT}/world_plates.json"))
elev = HD["elevation_m"].astype(float)
land = HD["land"]
H, W = elev.shape
R = META["radius_km"]
TILT = 23.0
SEASON_SHIFT = 5.0                       # degrees the wind/rain belts move with the seasons
GLOBAL_MEAN_PRECIP = 982.0               # mm/yr, GPCP 1979-2016 global mean (2.69 mm/day)

jj, ii = np.mgrid[0:H, 0:W]
LATd = 90 - (jj + 0.5) / H * 180
LAT = np.radians(LATd)
COS = np.cos(LAT)
AREA = COS
cell_km = 2 * np.pi * R / W * np.maximum(COS, 0.02)       # E-W size of a cell
elev_land = np.where(land, np.maximum(elev, 0), 0.0)


def bump(x, c, w):
    return np.exp(-((x - c) / w) ** 2)


def wind_u(lat_d, shift):
    """+1 = westerly (blows towards the east), -1 = easterly."""
    a = np.abs(lat_d - shift)
    return np.where((a > 30) & (a < 60), 1, -1)


# ---------- ocean current anomalies (SST) ----------
def along_row_distance(mask, direction):
    """km from each cell to the nearest `mask` cell found by walking in `direction` (+1 east, -1 west)."""
    dist = np.full((H, W), 1e9)
    cur = np.full(H, 1e9)
    cols = list(range(W)) * 2
    if direction > 0:                      # nearest land to the EAST -> walk westwards
        cols = cols[::-1]
    for k, c in enumerate(cols):
        cur = np.where(mask[:, c], 0.0, cur + cell_km[:, c])
        if k >= W:
            dist[:, c] = cur
    return dist


d_land_east = along_row_distance(land, +1)
d_land_west = along_row_distance(land, -1)
alat = np.abs(LATd)
sst_anom = (-5.0 * bump(alat, 27, 11) * np.exp(-d_land_east / 700)      # cold eastern-boundary currents
            + 5.0 * bump(alat, 57, 10) * np.exp(-d_land_east / 1100)    # warm drift towards high-lat west coasts
            + 3.5 * bump(alat, 25, 13) * np.exp(-d_land_west / 600)     # warm western-boundary currents
            - 3.5 * bump(alat, 55, 8) * np.exp(-d_land_west / 600))     # cold currents off high-lat east coasts
sst_anom = np.where(land, 0, ndimage.gaussian_filter(sst_anom, 2, mode="wrap"))

# ---------- per-season geometry: distance travelled over land since the ocean, carried SST anomaly ----------
def upwind_land(shift):
    u = wind_u(LATd[:, 0], shift)
    dist = np.zeros((H, W)); anom = np.zeros((H, W))
    cur_d = np.zeros(H); cur_a = np.zeros(H)
    rows = np.arange(H)
    for k in range(2 * W):
        c = np.where(u > 0, k % W, (W - 1 - k % W))
        is_land = land[rows, c]
        cur_d = np.where(is_land, cur_d + cell_km[rows, c], 0.0)
        cur_a = np.where(is_land, cur_a, sst_anom[rows, c])
        if k >= W:
            dist[rows, c] = cur_d; anom[rows, c] = cur_a
    return dist, anom


# ---------- temperature ----------
T_mean_sl = -24 + 51 * np.cos(LAT) ** 1.15          # fitted to Earth's zonal-mean sea-level temperature profile
lapse = -6.5 * elev_land / 1000.0
temps = {}
ups = {}
for name, shift in (("jul", SEASON_SHIFT), ("jan", -SEASON_SHIFT)):
    d_up, a_up = upwind_land(shift)
    d_up = ndimage.gaussian_filter(d_up, (3, 1), mode="wrap")
    a_up = ndimage.gaussian_filter(a_up, (3, 1), mode="wrap")
    ups[name] = d_up
    cont_f = np.where(land, 0.35 + 1.0 * (1 - np.exp(-d_up / 900)), 0.25)
    amp = (2 + 22 * np.abs(np.sin(LAT)) ** 1.2) * cont_f
    sign = np.sign(LATd) * (1 if name == "jul" else -1)
    coast_mod = np.where(land, a_up * np.exp(-d_up / 500), sst_anom)
    # land in the tropics/subtropics is warmer than the ocean at the same latitude
    # (less evaporative cooling, clear skies under the subtropical highs)
    sub_band = np.clip(bump(np.abs(LATd), 24, 10), 0, 1)
    land_warm = np.where(land, (1.5 + 2.5 * sub_band) * np.clip(np.cos(LAT) * 1.5 - 0.5, 0, 1), 0)
    T = T_mean_sl + sign * amp + lapse + coast_mod + land_warm
    # sea ice dampens the coldest ocean
    T = np.where(~land, np.maximum(T, -30), T)
    temps[name] = np.maximum(ndimage.gaussian_filter(T, 0.7, mode="wrap"), -75)
T_ann = (temps["jul"] + temps["jan"]) / 2

# ---------- precipitation ----------
_r = np.random.default_rng(META["seed"] + 4000)
_lon = np.radians((ii + 0.5) / W * 360)
BELT_WOBBLE = sum(a * np.sin(k * _lon + _r.uniform(0, 6.3)) * np.cos(m * LAT + _r.uniform(0, 6.3))
                  for a, k, m in ((3.0, 2, 1), (2.0, 3, 2), (1.5, 5, 3), (1.0, 8, 2)))
def land_band_fraction(lat_lo, lat_hi):
    m = (LATd >= lat_lo) & (LATd <= lat_hi)
    col = (land & m).sum(0) / max(m[:, 0].sum(), 1)
    return ndimage.uniform_filter1d(col.astype(float), size=61, mode="wrap")


precip = {}
for name, shift in (("jul", SEASON_SHIFT), ("jan", -SEASON_SHIFT)):
    T = temps[name]
    cap = np.exp(0.045 * (np.clip(T, -40, 35) - 27))          # moisture capacity (Clausius-Clapeyron-like)
    if name == "jul":
        itcz = 4 + 9 * land_band_fraction(5, 35)[None, :]        # monsoon pull over northern continents
    else:
        itcz = -4 - 9 * land_band_fraction(-35, -5)[None, :]
    ls = LATd - shift + BELT_WOBBLE                            # belts meander, not ruler-straight
    conv = (0.075 * bump(LATd, itcz, 7)                        # ITCZ convection
            + 0.045 * (bump(ls, 50, 12) + bump(ls, -50, 12))   # mid-latitude storm tracks
            + 0.012)
    lss = LATd - 0.5 * shift + BELT_WOBBLE                   # subtropical highs move less than the ITCZ
    sub = np.clip(bump(lss, 25, 8) + bump(lss, -25, 8), 0, 1)
    conv *= 1 - 0.97 * sub                                       # subtropical highs: no convection
    subsid = 0.08 * sub                                         # descending dry air dilutes moisture
    conv *= np.where(np.abs(LATd) > 70, 0.5, 1.0)
    evap = np.where(land, 0.010 * np.clip(conv / 0.03, 0.1, 1.6), 0.06 * np.clip(1 + sst_anom / 10, 0.3, 1.5))   # land = evapotranspiration
    u = wind_u(LATd[:, 0], shift)
    rows = np.arange(H)
    q = np.zeros(H)
    prevh = np.zeros(H)
    P = np.zeros((H, W))
    step = COS[:, 0]
    for k in range(3 * W):
        c = np.where(u > 0, k % W, (W - 1 - k % W))
        cp = cap[rows, c]
        q = q * (1 - subsid[rows, c] * step)
        q = q + evap[rows, c] * step * np.maximum(cp - q, 0)
        h = elev_land[rows, c] / 1000.0
        dh = np.maximum(h - prevh, 0)
        rain = q * np.clip(conv[rows, c] * step + 0.22 * dh, 0, 0.5)
        over = 0.3 * np.maximum(q - cp * 1.05, 0)                # supersaturation rains out gradually
        rain = np.minimum(rain + over, q)
        rec = 0.22 + 0.33 * np.clip(conv[rows, c] / 0.07, 0, 1)    # wet regions recycle more (evapotranspiration)
        q = q - rain + np.where(land[rows, c], rec * rain, 0)
        prevh = h
        if k >= 2 * W:
            P[rows, c] = rain / np.maximum(step, 0.05)
    P = ndimage.gaussian_filter(np.clip(P, 0, None), (3.0, 1.2), mode="wrap")
    precip[name] = P

P_raw = precip["jul"] + precip["jan"]
scale = GLOBAL_MEAN_PRECIP / ((P_raw * AREA).sum() / AREA.sum())
for k in precip:
    precip[k] *= scale
for k in precip:
    precip[k] = np.clip(precip[k], 0, 4000)
P_ann = precip["jul"] + precip["jan"]            # each season is half a year
nh = LATd >= 0
P_summer = np.where(nh, precip["jul"], precip["jan"])
P_winter = np.where(nh, precip["jan"], precip["jul"])
T_warm = np.maximum(temps["jul"], temps["jan"])
T_cold = np.minimum(temps["jul"], temps["jan"])

# ---------- biomes ----------
BIOMES = [
    # id, key, Ukrainian name, colour
    (0, "ocean", "Океан", (38, 78, 128)),
    (1, "sea_ice", "Морський лід (взимку)", (205, 222, 235)),
    (2, "ice_cap", "Льодовиковий щит", (242, 246, 250)),
    (3, "tundra", "Тундра", (158, 168, 140)),
    (4, "alpine", "Високогір'я", (150, 140, 134)),
    (5, "taiga", "Тайга (хвойні ліси)", (52, 102, 82)),
    (6, "temperate_forest", "Листяні та мішані ліси", (82, 140, 66)),
    (7, "temperate_rainforest", "Помірні дощові ліси", (36, 112, 72)),
    (8, "mediterranean", "Середземноморський чагарник", (160, 160, 70)),
    (9, "subtropical_forest", "Вологі субтропічні ліси", (70, 150, 90)),
    (10, "steppe", "Степ / прерія", (196, 190, 112)),
    (11, "cold_desert", "Холодна пустеля", (190, 178, 150)),
    (12, "hot_desert", "Спекотна пустеля", (232, 206, 140)),
    (13, "savanna", "Савана", (200, 168, 80)),
    (14, "tropical_seasonal", "Тропічні сезонні ліси", (110, 160, 50)),
    (15, "tropical_rainforest", "Тропічні дощові ліси", (20, 110, 40)),
]
# --- Koppen-Geiger classification (Peel et al. 2007 rules, two-season approximation) ---
# The two modelled seasons stand for the warmest / coldest month; monthly extremes of precipitation
# are approximated from the half-year totals (driest month ~ 0.6 x half-year mean month).
KOPPEN = ["Af", "Am", "Aw", "BWh", "BWk", "BSh", "BSk", "Cs", "Cw", "Cf", "Ds", "Dw", "Df", "ET", "EF"]
K = {k: i for i, k in enumerate(KOPPEN)}
summer_share = P_summer / np.maximum(P_ann, 1e-6)
Pth = 20 * T_ann + np.where(summer_share >= 0.7, 280, np.where(summer_share >= 0.3, 140, 0))
P_dry_month = 0.6 * np.minimum(P_summer, P_winter) / 6
P_dry_summer_month = 0.6 * P_summer / 6
P_wet_winter_month = 1.4 * P_winter / 6
P_dry_winter_month = 0.6 * P_winter / 6
P_wet_summer_month = 1.4 * P_summer / 6

kg = np.full((H, W), -1)
E = T_warm < 10
kg = np.where(E, np.where(T_warm < 0, K["EF"], K["ET"]), kg)
B = (kg < 0) & (P_ann < Pth)
desert = P_ann < 0.5 * Pth
hot = T_ann >= 18
kg = np.where(B, np.where(desert, np.where(hot, K["BWh"], K["BWk"]), np.where(hot, K["BSh"], K["BSk"])), kg)
A = (kg < 0) & (T_cold >= 18)
kg = np.where(A & (P_dry_month >= 60), K["Af"], kg)
kg = np.where(A & (kg < 0) & (P_dry_month >= 100 - P_ann / 25), K["Am"], kg)
kg = np.where(A & (kg < 0), K["Aw"], kg)
dry_s = (P_dry_summer_month < 40) & (P_dry_summer_month < P_wet_winter_month / 3)
dry_w = P_dry_winter_month < P_wet_summer_month / 10
C = (kg < 0) & (T_cold > 0)
kg = np.where(C, np.where(dry_s, K["Cs"], np.where(dry_w, K["Cw"], K["Cf"])), kg)
Dz = kg < 0
kg = np.where(Dz, np.where(dry_s, K["Ds"], np.where(dry_w, K["Dw"], K["Df"])), kg)
koppen = np.where(land, kg, -1).astype(np.int8)

# --- biomes derived from the Koppen class ---
b = np.full((H, W), 6)
b = np.where(koppen == K["EF"], 2, b)
b = np.where(koppen == K["ET"], np.where((elev_land > 2200) & (np.abs(LATd) < 60), 4, 3), b)
b = np.where(koppen == K["BWh"], 12, b)
b = np.where(koppen == K["BWk"], 11, b)
b = np.where((koppen == K["BSh"]) | (koppen == K["BSk"]), 10, b)
b = np.where(koppen == K["Af"], 15, b)
b = np.where(koppen == K["Am"], 14, b)
b = np.where(koppen == K["Aw"], 13, b)
b = np.where(koppen == K["Cs"], 8, b)
cfw = (koppen == K["Cf"]) | (koppen == K["Cw"])
b = np.where(cfw & (T_warm >= 22), 9, b)                                   # Cfa / Cwa
b = np.where(cfw & (T_warm < 22) & (P_ann > 1700), 7, b)                  # wet Cfb / Cfc
b = np.where(cfw & (T_warm < 22) & (P_ann <= 1700), 6, b)                 # Cfb / Cfc
dz = (koppen == K["Df"]) | (koppen == K["Dw"]) | (koppen == K["Ds"])
b = np.where(dz & (T_warm >= 18), 6, b)                                    # Dfa / Dfb: mixed forest
b = np.where(dz & (T_warm < 18), 5, b)                                     # Dfc / Dfd: taiga
biome = np.where(land, b, np.where(T_cold < -4, 1, 0)).astype(np.int8)
# remove single-pixel speckle
biome = np.where(land, ndimage.median_filter(biome, size=3, mode="wrap"), biome).astype(np.int8)
biome = np.where(land & (biome <= 1), 3, biome).astype(np.int8)

# ---------- render ----------
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

dx = 2 * np.pi * R / W * np.maximum(COS, 0.05) * 1000
dy = np.pi * R / H * 1000
e2 = np.where(land, elev, 0)
gx = (np.roll(e2, -1, 1) - np.roll(e2, 1, 1)) / (2 * dx)
gy = (np.vstack([e2[:1], e2[:-1]]) - np.vstack([e2[1:], e2[-1:]])) / (2 * dy)
nx, ny = -gx * 22, -gy * 22
shade = (nx * -0.6 + ny * 0.6 + 0.55) / (np.sqrt(nx ** 2 + ny ** 2 + 1) * math.sqrt(0.36 + 0.36 + 0.3025))
shade = np.clip(shade, 0, 1); shade = shade / shade[land].mean()

pal = np.array([c for *_, c in BIOMES], float)
rgb = pal[biome]
rgb = np.where(land[..., None], rgb * (0.55 + 0.45 * shade)[..., None], rgb)
depth = np.clip(-elev / 6000, 0, 1)
rgb = np.where((~land & (biome == 0))[..., None], rgb * (1.15 - 0.45 * depth)[..., None], rgb)
coast = land ^ ndimage.binary_erosion(land)
rgb[coast] *= 0.6

S = 1.25
img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((int(W * S), int(H * S)), Image.LANCZOS)
present = [bm for bm in BIOMES if (biome == bm[0]).any()]
cols_n = 3
rows_n = math.ceil(len(present) / cols_n)
LEG = 20 + rows_n * 30
canvas = Image.new("RGB", (img.width, img.height + LEG), (24, 26, 32))
canvas.paste(img, (0, 0))
d = ImageDraw.Draw(canvas)
f = ImageFont.truetype(FONT, 18)
for k, (_, _, nm, c) in enumerate(present):
    x = 24 + (k % cols_n) * (img.width // cols_n)
    y = img.height + 14 + (k // cols_n) * 30
    d.rectangle([x, y + 2, x + 30, y + 20], fill=c, outline=(200, 200, 200))
    d.text((x + 42, y), nm, font=f, fill=(230, 230, 230))
canvas.save(f"{OUT}/biome_map.png", optimize=True)


def ramp(z, stops):
    xs = [s[0] for s in stops]
    out = np.zeros(z.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(z, xs, [s[1][c] for s in stops])
    return out


T_stops = [(-35, (60, 20, 120)), (-20, (60, 80, 200)), (-5, (110, 180, 230)), (5, (190, 230, 210)),
           (15, (240, 230, 120)), (22, (245, 160, 60)), (30, (200, 40, 30))]
P_stops = [(0, (150, 100, 50)), (250, (210, 180, 110)), (500, (230, 225, 160)), (1000, (130, 200, 120)),
           (1800, (40, 150, 140)), (3000, (30, 80, 170)), (4500, (60, 30, 120))]


def panel(field, stops, title, ticks, unit, mask_sea_dim):
    rgbp = ramp(field, stops)
    if mask_sea_dim:
        rgbp = np.where(land[..., None], rgbp, rgbp * 0.55 + 0.45 * np.array([30, 40, 60]))
    rgbp[coast] = rgbp[coast] * 0.4
    s = 0.9
    im = Image.fromarray(np.clip(rgbp, 0, 255).astype(np.uint8)).resize((int(W * s), int(H * s)), Image.LANCZOS)
    pc = Image.new("RGB", (im.width, im.height + 110), (24, 26, 32))
    pc.paste(im, (0, 44))
    dd = ImageDraw.Draw(pc)
    dd.text((14, 10), title, font=ImageFont.truetype(FONTB, 20), fill=(235, 235, 235))
    x0, x1, yb = 30, im.width - 30, im.height + 56
    lo, hi = stops[0][0], stops[-1][0]
    zs = np.linspace(lo, hi, x1 - x0)
    for k_, c in enumerate(ramp(zs, stops)):
        dd.line([(x0 + k_, yb), (x0 + k_, yb + 18)], fill=tuple(int(v) for v in c))
    ff = ImageFont.truetype(FONT, 16)
    for t in ticks:
        x = x0 + (t - lo) / (hi - lo) * (x1 - x0)
        dd.line([(x, yb + 18), (x, yb + 25)], fill=(220, 220, 220))
        dd.text((x - 14, yb + 27), f"{t}", font=ff, fill=(220, 220, 220))
    dd.text((x1 - 60, yb - 22), unit, font=ff, fill=(220, 220, 220))
    return pc


p1 = panel(T_ann, T_stops, "Середньорічна температура", [-30, -20, -10, 0, 10, 20, 30], "°C", False)
p2 = panel(P_ann, P_stops, "Річні опади", [0, 500, 1000, 2000, 3000, 4000], "мм/рік", True)
cm = Image.new("RGB", (p1.width, p1.height + p2.height), (24, 26, 32))
cm.paste(p1, (0, 0)); cm.paste(p2, (0, p1.height))
cm.save(f"{OUT}/climate_maps.png", optimize=True)

# ---------- export ----------
np.savez_compressed(f"{OUT}/world_climate.npz",
                    temp_jul_c=temps["jul"].astype(np.float32), temp_jan_c=temps["jan"].astype(np.float32),
                    temp_annual_c=T_ann.astype(np.float32),
                    precip_jul_half_mm=precip["jul"].astype(np.float32),
                    precip_jan_half_mm=precip["jan"].astype(np.float32),
                    precip_annual_mm=P_ann.astype(np.float32), biome=biome, koppen=koppen, sst_anomaly_c=sst_anom.astype(np.float32))
land_area = AREA[land].sum()
share = {key: round(float(AREA[land & (biome == i)].sum() / land_area * 100), 1) for i, key, _, _ in BIOMES if i >= 2}
stats = dict(axial_tilt_deg=TILT, season_shift_deg=SEASON_SHIFT, global_mean_precip_mm=GLOBAL_MEAN_PRECIP,
             land_mean_temp_c=round(float((T_ann * AREA)[land].sum() / land_area), 1),
             land_mean_precip_mm=round(float((P_ann * AREA)[land].sum() / land_area)),
             hottest_c=round(float(T_warm[land].max()), 1), coldest_c=round(float(T_cold[land].min()), 1),
             wettest_mm=round(float(P_ann[land].max())), driest_mm=round(float(P_ann[land].min())),
             biome_share_of_land_pct=dict(sorted(share.items(), key=lambda kv: -kv[1])),
             koppen_share_of_land_pct={k: round(float(AREA[land & (koppen == i)].sum() / land_area * 100), 1) for i, k in enumerate(KOPPEN)},
             koppen_codes=KOPPEN,
             biome_legend={key: name for _, key, name, _ in BIOMES})
json.dump(stats, open(f"{OUT}/world_climate.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(stats, ensure_ascii=False))
