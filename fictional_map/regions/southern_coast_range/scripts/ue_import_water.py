"""
Unreal Editor script: place the rivers and lakes of one plot (export/tile_x{c}_y{r}/water.json) as Water plugin
water bodies in the currently open level. Runs INSIDE Unreal Engine, not in the normal Python.

Before running:
  * Plugins: enable "Water" and "Python Editor Script Plugin", restart the editor.
  * Open the plot's level; its landscape must be imported at location (0, 0, 0) with scale 248.016 / 248.016 / 1000
    (USAGE.md, section 9). The water positions in water.json are in that landscape's frame.

Run (Output Log, "Python" command line, or Tools > Execute Python Script with the path edited below):
  py "C:/.../southern_coast_range/scripts/ue_import_water.py" "C:/.../southern_coast_range/export/tile_x1_y2"

What it does:
  * one WaterZone covering the plot (water bodies render only inside a water zone);
  * one WaterBodyRiver per river line: spline through the water-surface points, with width, depth and velocity;
  * one WaterBodyLake per lake outline at its water level;
  * "Affects Landscape" is switched off on every water body: the channels and lake basins are already in the heightmap.
Everything it places goes into the outliner folder "Water/<plot>"; running it again first deletes that folder's actors.

The Water plugin's per-point width / depth / velocity curves are not part of its documented scripting interface.
The script tries to set them per point; if this engine version does not allow it, it falls back to one value per river
(the river's median) and says so in the Output Log. Check the log after the first run.
"""
import json, os, sys
import unreal

PLOT_DIR = sys.argv[1] if len(sys.argv) > 1 else r"C:/path/to/southern_coast_range/export/tile_x0_y0"
MIN_RIVER_Q = 1.0          # m3/s: skip smaller rivers (all exported rivers are >= 1 m3/s)
MIN_LAKE_M2 = 2500.0       # skip smaller ponds (raise this if a plot has too many water bodies for your target hardware)

log = unreal.log
warn = unreal.log_warning
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(p):
    return unreal.Vector(float(p[0]), float(p[1]), float(p[2]))


def try_set(obj, names, value):
    for n in names:
        try:
            obj.set_editor_property(n, value)
            return n
        except Exception:
            continue
    return None


def try_get(obj, names):
    for n in names:
        try:
            v = obj.get_editor_property(n)
            if v is not None:
                return v
        except Exception:
            continue
    return None


def set_curves(body, spline, rv):
    """Per-point width/depth/velocity; returns True if per-point curves were set, False for the median fallback."""
    n = len(rv["points_cm"])
    meta = None
    for getter in ("get_water_spline_metadata",):
        if hasattr(body, getter):
            try:
                meta = getattr(body, getter)()
            except Exception:
                meta = None
    if meta is None:
        meta = try_get(body, ["water_metadata", "spline_metadata"]) or try_get(spline, ["spline_metadata", "water_metadata"])
    if meta is not None and hasattr(unreal, "InterpCurveFloat") and hasattr(unreal, "InterpCurvePointFloat"):
        try:
            def curve(vals):
                c = unreal.InterpCurveFloat()
                pts = []
                for i, v in enumerate(vals):
                    p = unreal.InterpCurvePointFloat()
                    p.set_editor_property("in_val", float(i)); p.set_editor_property("out_val", float(v))
                    p.set_editor_property("interp_mode", unreal.InterpCurveMode.CIM_CURVE_AUTO)
                    pts.append(p)
                c.set_editor_property("points", pts)
                return c
            meta.set_editor_property("river_width", curve([w * 100.0 for w in rv["width_m"]]))
            meta.set_editor_property("depth", curve([d * 100.0 for d in rv["depth_m"]]))
            meta.set_editor_property("water_velocity_scalar", curve(rv["velocity_ms"]))
            if len(meta.get_editor_property("river_width").get_editor_property("points")) == n:
                return True
        except Exception as e:
            warn(f"per-point water curves not settable here ({e}); using one value per river")
    return False


def median(v):
    s = sorted(v)
    return s[len(s) // 2]


def main():
    path = os.path.join(PLOT_DIR, "water.json")
    data = json.load(open(path))
    plot = data["plot"]
    folder = f"Water/{plot}"
    # remove what an earlier run placed
    for a in actors.get_all_level_actors():
        if str(a.get_folder_path()) == folder:
            actors.destroy_actor(a)
    size = float(data.get("plot_size_cm", 1000000.0))
    zone = actors.spawn_actor_from_class(unreal.WaterZone, unreal.Vector(size / 2, size / 2, 0.0))
    if try_set(zone, ["zone_extent"], unreal.Vector2D(size + 20000.0, size + 20000.0)) is None:
        warn("could not set the WaterZone extent; scale the WaterZone to cover the whole plot by hand")
    zone.set_folder_path(folder)
    n_r = n_l = per_point = 0
    for rv in data["rivers"]:
        if max(rv["discharge_m3s"]) < MIN_RIVER_Q or len(rv["points_cm"]) < 2:
            continue
        pts = [vec(p) for p in rv["points_cm"]]
        body = actors.spawn_actor_from_class(unreal.WaterBodyRiver, pts[0])
        body.set_actor_label(rv["id"]); body.set_folder_path(folder)
        try_set(body, ["affects_landscape"], False)
        spline = body.get_water_spline()
        # defaults first: points added afterwards start from these values
        dflt = try_get(spline, ["water_spline_defaults"])
        if dflt is not None:
            try:
                dflt.set_editor_property("default_width", median(rv["width_m"]) * 100.0)
                dflt.set_editor_property("default_depth", median(rv["depth_m"]) * 100.0)
                dflt.set_editor_property("default_velocity", median(rv["velocity_ms"]))
                spline.set_editor_property("water_spline_defaults", dflt)
            except Exception as e:
                warn(f"{rv['id']}: could not set river defaults ({e})")
        spline.set_spline_points(pts, unreal.SplineCoordinateSpace.WORLD, False)
        for i in range(len(pts)):
            spline.set_spline_point_type(i, unreal.SplinePointType.CURVE, False)
        spline.update_spline()
        per_point += set_curves(body, spline, rv)
        try:
            body.on_water_body_changed(True)            # rebuild the river mesh (not available in every version)
        except Exception:
            pass
        n_r += 1
    for lk in data["lakes"]:
        if lk["area_m2"] < MIN_LAKE_M2:
            continue
        z = lk["level_m"] * 100.0
        pts = [unreal.Vector(float(u), float(v), z) for u, v in lk["outline_cm"]]
        body = actors.spawn_actor_from_class(unreal.WaterBodyLake, pts[0])
        body.set_actor_label(lk["id"]); body.set_folder_path(folder)
        try_set(body, ["affects_landscape"], False)
        spline = body.get_water_spline()
        spline.set_spline_points(pts, unreal.SplineCoordinateSpace.WORLD, False)
        spline.set_closed_loop(True, False)
        spline.update_spline()
        n_l += 1
    log(f"{plot}: placed {n_r} rivers ({per_point} with per-point width/depth/velocity, the rest with one value per river) "
        f"and {n_l} lakes in folder {folder}")


main()
