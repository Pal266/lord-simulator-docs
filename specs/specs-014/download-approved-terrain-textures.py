#!/usr/bin/env python3
"""Download the project-owner-approved Poly Haven textures. One-off authoring tool.

Promotes exactly 24 ORIGINAL 2K maps only after every channel validates.
Never run from packaged game. Never overwrite any existing approved art.
"""
import hashlib
import io
import json
import shutil
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

ASSETS = {
    "rock": "aerial_rocks_02",
    "scree": "gray_rocks",
    "alpine_meadow": "sparse_grass",
    "forest": "forrest_ground_01",
    "wet_meadow": "leafy_grass",
    "gravel": "gravel_floor_04",
    "riverbed": "river_small_rocks",
    "lakebed": "mud_forest",
}
MAPS = {
    "basecolor": ("diff", "jpg", "JPEG"),
    "normal": ("nor_dx", "png", "PNG"),
    "roughness": ("rough", "jpg", "JPEG"),
}
APPROVED = Path("visuals/approved/terrain/southern-coast-range")
STAGING = Path("visuals/research")

def get(url, limit=40_000_000):
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LordSimulator-ApprovedTerrain/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                out = io.BytesIO()
                while True:
                    part = r.read(1024 * 1024)
                    if not part: break
                    out.write(part)
                    if out.tell() > limit: raise ValueError("Unexpected download size: " + url)
                return out.getvalue()
        except (OSError, TimeoutError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to retrieve {url}: {last}")

def api(kind, asset_id):
    return json.loads(get(f"https://api.polyhaven.com/{kind}/{asset_id}", 8_000_000))

def validate(src, ext, label):
    with Image.open(io.BytesIO(src)) as img:
        img.load()
        if img.size != (2048, 2048) or img.format != label:
            raise ValueError(f"Expected unmodified 2048x2048 {label} but found {img.size} {img.format}")
        if ext == "png" and img.mode not in ("RGB", "RGBA"):
            raise ValueError("Normal map must have RGB channels")

def main():
    if APPROVED.exists() and list(APPROVED.iterdir()):
        raise RuntimeError("Approved directory is not empty; refusing to overwrite")
    STAGING.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix="terrain-cc0-", dir=STAGING) as temp:
        temp = Path(temp)
        for layer, asset_id in ASSETS.items():
            files, info = api("files", asset_id), api("info", asset_id)
            authors = info.get("authors")
            if not authors: raise RuntimeError("Author metadata missing: " + asset_id)
            row = {"layer": layer, "id": asset_id, "authors": authors, "files": []}
            for channel, (name, ext, fmt) in MAPS.items():
                filename_upstream = f"{asset_id}_{name}_2k.{ext}"
                candidates = []
                def scan(obj):
                    if isinstance(obj, dict):
                        for v in obj.values(): scan(v)
                    elif isinstance(obj, list):
                        for v in obj: scan(v)
                    elif isinstance(obj, str):
                        if obj.startswith("https://dl.polyhaven.org/") and obj.split("?")[0].endswith("/" + filename_upstream):
                            candidates.append(obj)
                scan(files)
                if len(candidates) != 1:
                    raise RuntimeError(f"Expected exactly one 2K source URL for {filename_upstream}; got {len(candidates)}. API top-level keys: {list(files)}")
                url = candidates[0]
                if not url.startswith("https://dl.polyhaven.org/"):
                    raise RuntimeError("Unexpected URL " + url)
                payload = get(url)
                validate(payload, ext, fmt)
                filename = f"{layer}-{channel}.{ext}"
                (temp / filename).write_bytes(payload)
                row["files"].append((filename, channel, url, hashlib.sha256(payload).hexdigest(), len(payload)))
                print(f"Validated {filename} ({len(payload)} bytes)", flush=True)
            rows.append(row)
        expected = {f"{layer}-{channel}.{spec[1]}" for layer in ASSETS for channel, spec in MAPS.items()}
        if {x.name for x in temp.iterdir()} != expected:
            raise RuntimeError("Exactly 24 approved maps are required")
        provenance = [
            "# Approved Southern Coast Range texture provenance", "",
            "The project owner explicitly approved the eight Poly Haven CC0 texture sets on 2026-11-05.",
            "These are the unchanged original 2K source channels (Diffuse JPG, Normal DX PNG, Rough JPG).", "",
            "- Provider: Poly Haven",
            "- License: CC0-1.0, https://polyhaven.com/license",
            "- Source rights: commercial use and redistribution permitted; attribution not required.",
            "- Retrieval date (UTC): " + datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "- No project copyright asserted over Poly Haven textures.",
            "- Never modify or replace the approved originals during implementation.", "",
            "| Layer | Source | Creator(s) |", "| --- | --- | --- |"
        ]
        for row in rows:
            authors = ", ".join(f"{k} ({v})" for k, v in row["authors"].items())
            provenance.append(f"| `{row['layer']}` | https://polyhaven.com/a/{row['id']} | {authors} |")
        provenance += ["", "## Immutable source images", "",
                       "| Exact approved path | PBR channel | Source download URL | Bytes | SHA-256 |",
                       "| --- | --- | --- | ---: | --- |"]
        for row in rows:
            for filename, channel, url, digest, size in row["files"]:
                provenance.append(f"| `{APPROVED / filename}` | {channel} | {url} | {size} | `{digest}` |")
        provenance.append("")
        (temp / "texture-provenance.md").write_text("\n".join(provenance), encoding="utf8")
        APPROVED.mkdir(parents=True, exist_ok=True)
        for file in temp.iterdir(): shutil.move(str(file), str(APPROVED / file.name))
        print("PROMOTED 24 validated images plus provenance", flush=True)

if __name__ == "__main__":
    main()
