#!/usr/bin/env python3
"""Generate platform icon assets from icon_blackgolden.png.

Usage:
    source venv/bin/activate
    python icon/generate_icons.py

Requires Pillow (installed in project venv).
"""
import io
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from PIL import Image

ICON_DIR = Path(__file__).parent.resolve()
SRC_PNG = ICON_DIR / "icon_blackgolden.png"
ICO_OUT = ICON_DIR / "icon_blackgolden.ico"
ICNS_OUT = ICON_DIR / "icon_blackgolden.icns"

SIZES = [16, 32, 48, 64, 128, 256]


def _write_multi_ico(path: Path, images: list) -> None:
    """Write a multi-resolution Windows .ico file.

    Pillow's ICO writer does not reliably emit multiple resolutions via
    ``append_images`` in all versions, so we build the container directly.
    Each image is stored as a PNG blob inside the .ico container.
    """
    png_blobs = []
    for im in images:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        png_blobs.append(buf.getvalue())

    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)  # reserved, type=icon, count
    entries = b""
    data_offset = 6 + 16 * count
    data = b""

    for im, blob in zip(images, png_blobs):
        width = im.width if im.width < 256 else 0
        height = im.height if im.height < 256 else 0
        size = len(blob)
        entries += struct.pack(
            "<BBBBHHII",
            width,        # bWidth
            height,       # bHeight
            0,            # bColorCount
            0,            # bReserved
            1,            # wPlanes
            32,           # wBitCount
            size,         # dwBytesInRes
            data_offset,  # dwImageOffset
        )
        data += blob
        data_offset += size

    path.write_bytes(header + entries + data)


def generate_ico() -> None:
    """Generate a multi-resolution Windows .ico file."""
    img = Image.open(SRC_PNG).convert("RGBA")
    icons = []
    for size in SIZES:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        icons.append(resized)
    ICO_OUT.unlink(missing_ok=True)
    _write_multi_ico(ICO_OUT, icons)
    print(f"Generated: {ICO_OUT}")


def generate_icns() -> bool:
    """Generate a macOS .icns file using sips + iconutil.

    Returns True on success, False if the macOS tooling is unavailable.
    """
    sips = shutil.which("sips")
    iconutil = shutil.which("iconutil")
    if not sips or not iconutil:
        print("sips/iconutil not found; skipping .icns generation.")
        return False

    iconset_dir = ICON_DIR / "icon_blackgolden.iconset"
    iconset_dir.mkdir(exist_ok=True)

    # macOS iconset sizes
    mac_sizes = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]

    for filename, size in mac_sizes:
        out_path = iconset_dir / filename
        subprocess.run(
            [sips, "-z", str(size), str(size), str(SRC_PNG), "--out", str(out_path)],
            check=True,
            capture_output=True,
        )

    ICNS_OUT.unlink(missing_ok=True)
    subprocess.run([iconutil, "-c", "icns", str(iconset_dir)], check=True)
    print(f"Generated: {ICNS_OUT}")

    # Clean up temporary iconset
    shutil.rmtree(iconset_dir)
    return True


if __name__ == "__main__":
    if not SRC_PNG.exists():
        print(f"Source icon not found: {SRC_PNG}", file=sys.stderr)
        sys.exit(1)

    generate_ico()
    if sys.platform == "darwin":
        try:
            generate_icns()
        except Exception as e:
            print(f"Failed to generate .icns: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Run this on macOS to generate icon_blackgolden.icns.")
