"""Font lookup for map labels (Cyrillic-capable fonts on Linux, Windows and macOS)."""
import os

_REGULAR = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"]
_BOLD = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"]


def _first(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    raise SystemExit("No suitable font found for map labels (DejaVu Sans or Arial). Install DejaVu Sans or Arial.")


FONT = _first(_REGULAR)
FONTB = _first(_BOLD)
