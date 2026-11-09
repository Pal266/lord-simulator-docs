"""
Canon geography of Westeros as control points (not run directly; imported by the other scripts).

Coordinates are written at CANON scale, in kilometres: x = east, y = north, origin = Castle Black (middle of the Wall).

* The outline - coast, islands, lakes and rivers - is digitised from the reference locator map of Westeros supplied by
  the project owner (data/westeros_outline.json), scaled by the Wall: the Wall, coast to coast, is 300 miles = 480 km in
  the books. The map ends a little north of the Wall's latitude band shown on it; the coast of the far north (the Land
  of Always Winter) is invented.
* Mountain regions (MOUNTAINS) are outlined from the canon relief map of Westeros supplied by the project owner, which
  draws mountains, hills and forests; inside each outline the relief follows the rock texture of that map
  (data/relief_texture.png, a 5 km raster in canon km). The relief map was registered onto the outline above by its
  coastline (thin-plate spline, median residual ~9 km). Summit heights come from the canon and the tectonic setting
  (../CANON.md). The canon names of the rivers are read from the same map.
* Places, uplands and forests are placed from the books' textual geography (relative positions,
  stated distances) and fitted onto the map's outline with a thin-plate warp anchored on features that both share
  (the Wall, Skagos, Bear Island, the Long Lake, Torrhen's Square, White Harbor, Moat Cailin, the Iron Islands, the
  Trident's mouth, the Gods Eye, Gulltown, King's Landing, Tarth, Starfall, Sunspear, the Arbor). See ../CANON.md.

SCALE shrinks every distance (user decision: half the canon area -> lengths x 0.71). LAT0 places Castle Black on the
planet. to_latlon() converts canon-scale km to latitude / longitude on an Earth-sized planet: y along the meridian
(111.2 km per degree), x along the parallel at that latitude.
"""
import json, math, os
import numpy as np

SCALE = 0.71                 # lengths x 0.71 = area x 0.5 (see USAGE.md, 'Model decisions')
LAT0, LON0 = 59.0, 0.0       # Castle Black (see USAGE.md: chosen so that both the Haunted Forest and Dorne's desert fit)
KM_PER_DEG = 111.195         # Earth radius 6371 km


def to_latlon(x_km, y_km):
    x = np.asarray(x_km, float) * SCALE; y = np.asarray(y_km, float) * SCALE
    lat = LAT0 + y / KM_PER_DEG
    lon = LON0 + x / (KM_PER_DEG * np.cos(np.radians(lat)))
    return lat, lon


def from_latlon(lat, lon):
    """Inverse of to_latlon (canon-scale km)."""
    lat = np.asarray(lat, float); lon = np.asarray(lon, float)
    y = (lat - LAT0) * KM_PER_DEG
    x = (lon - LON0) * KM_PER_DEG * np.cos(np.radians(lat))
    return x / SCALE, y / SCALE


# ---------------- the outline: coast, islands, lakes, rivers (digitised from the reference map) ----------------
_OUT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "westeros_outline.json")))
COAST = [tuple(p) for p in _OUT["coast"]]                       # closed ring of the mainland
ISLANDS = {k: [tuple(p) for p in v] for k, v in _OUT["islands"].items()}   # name: outline (named isles, then "isle N")
LAKES = {k: (tuple(c), tuple(s)) for k, (c, s) in _OUT["lakes"].items()}     # name: centre, half-lengths (x, y) km
RIVERS = {k: [tuple(p) for p in v] for k, v in _OUT["rivers"].items()}       # name: polyline from source to mouth


def island_ring(spec, n=None):
    """Outline (canon km, x and y arrays) of an ISLANDS entry."""
    p = np.array(spec, float)
    return p[:, 0], p[:, 1]


def island_centre(spec):
    p = np.array(spec, float)
    return float(p[:, 0].mean()), float(p[:, 1].mean())


def island_halfwidth(spec):
    """Radius (canon km) of the circle with the island's area: a measure of how wide the island is."""
    x, y = island_ring(spec)
    area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    return math.sqrt(area / math.pi)


# ---------------- placed features (textual geography fitted onto the outline) ----------------
MOUNTAINS = {   # mountain regions read from the relief map: outline (canon km), typical summit height (m)
    "Frostfangs": ([(-834, 787), (-350, 628), (-382, 311), (-451, 187), (-434, 11), (-549, -66), (-686, 43), (-751, 199), (-797, 344), (-808, 559)], 3000),
    "Northern mountains (clan lands)": ([(-631, -37), (-140, -34), (37, -155), (58, -426), (-47, -576), (-214, -685), (-459, -664), (-580, -426), (-668, -211)], 1600),
    "Rills and Stony Shore hills": ([(-1148, -674), (-436, -685), (-403, -964), (-489, -1197), (-732, -1171), (-941, -1083), (-1113, -957)], 800),
    "Mountains of the Moon": ([(-261, -1650), (85, -1614), (522, -1640), (737, -1700), (736, -1825), (525, -2022), (408, -2297), (119, -2295), (-98, -2209), (-222, -2060), (-300, -1794)], 3200),
    "Westerlands mountains (Golden Tooth)": ([(-948, -2252), (-583, -2209), (-505, -2362), (-553, -2558), (-492, -2761), (-564, -2925), (-764, -2921), (-885, -2752), (-966, -2570), (-996, -2362)], 1800),
    "Red Mountains (Dornish Marches)": ([(-851, -3506), (-588, -3497), (-267, -3372), (-78, -3271), (57, -3296), (-54, -3495), (-269, -3709), (-444, -3895), (-557, -4001), (-620, -4134), (-663, -4257), (-845, -4253), (-973, -4142), (-939, -3881), (-916, -3669)], 2600),
    "Stormlands hills": ([(14, -3170), (410, -3199), (466, -3316), (277, -3385), (153, -3462), (70, -3557), (-28, -3495), (-55, -3313)], 1000),
    "Dornish coastal hills": ([(-57, -3774), (200, -3781), (513, -3855), (677, -3904), (688, -3993), (518, -4023), (293, -3980), (78, -3917), (-74, -3864)], 900),
    "Skagos mountains": ([(463, 150), (633, 183), (701, 40), (696, -157), (578, -200), (473, -128), (436, 2)], 1300),
}


def mountain_field(x, y, taper_km=25.0):
    """Mountain weight 0..1 and summit height (m) at canon x, y (arrays): inside a MOUNTAINS outline (a generous
    envelope) the weight follows where the relief map draws rock (its texture), rises from the outline over taper_km
    and towards the core of the range; where outlines overlap the higher range counts."""
    from matplotlib.path import Path
    from scipy import ndimage as _nd
    x = np.asarray(x, float); y = np.asarray(y, float)
    tex = relief_texture(x, y)
    w_out = np.zeros(x.shape); h_out = np.zeros(x.shape)
    pts = np.column_stack([x.ravel(), y.ravel()])
    for name, (poly, h) in MOUNTAINS.items():
        p = np.array(poly, float)
        inside = Path(p).contains_points(pts).reshape(x.shape)
        if not inside.any():
            continue
        # distance to the outline (canon km), for the foothill taper
        seg_a, seg_b = p, np.roll(p, -1, axis=0)
        d = np.full(x.shape, np.inf)
        for (ax, ay), (bx, by) in zip(seg_a, seg_b):
            vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy + 1e-9
            t = np.clip(((x - ax) * vx + (y - ay) * vy) / L2, 0, 1)
            d = np.minimum(d, np.hypot(x - ax - t * vx, y - ay - t * vy))
        # a range rises towards its core (the farthest point from its outline), not to a plateau: foothills over
        # taper_km, then a gentle rise to the crest zone; the map's rock texture shapes the inner massifs
        dmax = _core_depth(name, p)
        # where the map draws rock (texture) sets the extent: ragged outlines, isolated massifs and passes as drawn
        rock = np.clip((tex - ROCK_TEXTURE[0]) / (ROCK_TEXTURE[1] - ROCK_TEXTURE[0]), 0, 1) ** 0.8
        w = np.where(inside, np.clip(d / taper_km, 0, 1) ** 0.7 * (0.6 + 0.4 * np.clip(d / dmax, 0, 1)), 0.0) * rock
        better = w * h > w_out * h_out
        w_out = np.where(better, w, w_out); h_out = np.where(better, h, h_out)
    return w_out, h_out


_CORE = {}


def _core_depth(name, p):
    """Largest distance (canon km) from the outline of a mountain region to its inside."""
    if name not in _CORE:
        from matplotlib.path import Path
        gx, gy = np.meshgrid(np.arange(p[:, 0].min(), p[:, 0].max(), 5.0), np.arange(p[:, 1].min(), p[:, 1].max(), 5.0))
        ins = Path(p).contains_points(np.column_stack([gx.ravel(), gy.ravel()]))
        gx, gy = gx.ravel()[ins], gy.ravel()[ins]
        d = np.full(gx.shape, np.inf)
        for (ax, ay), (bx, by) in zip(p, np.roll(p, -1, axis=0)):
            vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy + 1e-9
            t = np.clip(((gx - ax) * vx + (gy - ay) * vy) / L2, 0, 1)
            d = np.minimum(d, np.hypot(gx - ax - t * vx, gy - ay - t * vy))
        _CORE[name] = float(d.max()) if d.size else 1.0
    return _CORE[name]


_TEX = None


def relief_texture(x, y):
    """0..1: how much rock the relief map draws around canon x, y (5 km raster; 0.5 outside the map)."""
    global _TEX
    from PIL import Image
    from scipy import ndimage as _nd
    if _TEX is None:
        _TEX = np.asarray(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "relief_texture.png")),
                          float) / 255.0
    j = (RELIEF_TEXTURE["y1"] - np.asarray(y, float)) / RELIEF_TEXTURE["res"] - 0.5
    i = (np.asarray(x, float) - RELIEF_TEXTURE["x0"]) / RELIEF_TEXTURE["res"] - 0.5
    return _nd.map_coordinates(_TEX, [j, i], order=1, mode="nearest")


RELIEF_TEXTURE = {"x0": -1950.0, "y1": 1750.0, "res": 5.0}   # data/relief_texture.png: canon raster, row 0 = north
ROCK_TEXTURE = (0.15, 0.55)   # texture below the first value: plain; above the second: full mountain


HILLS = {   # broad uplands: centre, radius (km), height above the surrounding plain (m)
    "Lonely Hills": ((173, -673), 154, 500),
    "Haunted Forest uplands": ((78, 212), 320, 250),
    "Vale foothills": ((258, -2062), 205, 500),
    "Barrowlands swells": ((-623, -1286), 179, 80),
}
LOWLANDS = {   # low plains / marsh: centre, radius (km), target elevation (m)
    "the Neck": ((-295, -1751), 192, 8),
    "Riverlands": ((-230, -2260), 423, 90),
    "the Reach": ((-483, -3226), 423, 120),
    "Crownlands coast": ((117, -2822), 179, 60),
}
ICE_SHEET = {"from_y_km": 1300.0, "max_ice_m": 2400.0}   # Land of Always Winter: beyond the northern edge of the reference map
FORESTS = {   # for the vegetation step: centre, half-lengths (x, y) km
    "Wolfswood": ((-612, -718), (269, 179)),
    "Haunted Forest": ((74, 197), (385, 282)),
    "Kingswood": ((189, -3042), (115, 77)),
    "Rainwood": ((418, -3377), (115, 77)),
}
PLACES = {   # for checks and orientation
    "Castle Black": (0, 0),
    "Eastwatch-by-the-Sea": (240, 33),
    "Westwatch-by-the-Bridge": (-240, -33),
    "Hardhome": (362, 270),
    "Fist of the First Men": (-65, 193),
    "Winterfell": (-312, -730),
    "Castle Cerwyn": (-363, -762),
    "Deepwood Motte": (-712, -521),
    "Last Hearth": (187, -202),
    "Karhold": (535, -320),
    "the Dreadfort": (119, -602),
    "Torrhen's Square": (-628, -1002),
    "Barrowton": (-620, -1298),
    "White Harbor": (-41, -1340),
    "Moat Cailin": (-319, -1608),
    "the Twins": (-286, -1891),
    "Riverrun": (-547, -2237),
    "Harrenhal": (-85, -2420),
    "the Eyrie": (211, -2121),
    "Gulltown": (547, -2332),
    "King's Landing": (143, -2865),
    "Dragonstone": (490, -2645),
    "Casterly Rock": (-1050, -2680),
    "Pyke": (-1033, -2146),
    "Highgarden": (-613, -3306),
    "Oldtown": (-1134, -3915),
    "Storm's End": (344, -3299),
    "Sunspear": (552, -4079),
    "Starfall": (-772, -4019),
}

# ---------------- the rest of the known world, as coarse context (latitude / longitude polygons) ----------------
# Not modelled in detail: present only so that winds, ocean currents and moisture around Westeros are right.
ESSOS = [(68, 14), (70, 40), (72, 80), (68, 110), (50, 120), (30, 110), (18, 95), (15, 70), (20, 45), (28, 30),
         (34, 18), (37, 12), (41, 10.5), (47, 12), (52, 15), (56, 13), (59, 20), (62, 24), (64, 16)]
SOTHORYOS = [(28, -5), (27, 10), (24, 25), (20, 40), (8, 45), (-5, 35), (-10, 15), (-5, 0), (10, -8), (22, -10)]
# Canon distances (canon scale) and their sources:
#   wall          - the Wall is ~300 miles long, coast to coast (the books; https://awoiaf.westeros.org/index.php/Wall)
#   deepwood      - Deepwood Motte lies 100 leagues north-west of Winterfell (https://awoiaf.westeros.org/index.php/Winterfell)
CANON_DISTANCES = [   # (from, to, canon km, source key)
    ("Westwatch-by-the-Bridge", "Eastwatch-by-the-Sea", 480.0, "wall"),
    ("Winterfell", "Deepwood Motte", 480.0, "deepwood"),
]
