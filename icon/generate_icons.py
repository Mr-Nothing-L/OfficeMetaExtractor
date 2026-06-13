#!/usr/bin/env python3
"""Generate platform icon assets from icon_nobackground.png.

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
# Source file has a .jpeg extension but contains PNG data with transparency.
SRC_FILE = ICON_DIR / "icon_nobackground.jpeg"
SRC_PNG = ICON_DIR / "icon_nobackground.png"
ICO_OUT = ICON_DIR / "icon_nobackground.ico"
ICNS_OUT = ICON_DIR / "icon_nobackground.icns"

ICO_SIZES = [16, 32, 48, 64, 128, 256]


def _open_source(path: Path) -> Image.Image:
    """Open the source icon robustly, regardless of the declared extension."""
    with open(path, "rb") as f:
        data = f.read()
    return Image.open(io.BytesIO(data)).convert("RGBA")


def _crop_transparent_margins(img: Image.Image) -> Image.Image:
    """Crop empty transparent margins while keeping the content centered."""
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return img
    return img.crop(bbox)


def _normalize_source() -> Image.Image:
    """Create the normalized RGBA PNG source from the upstream asset."""
    img = _open_source(SRC_FILE)
    img = _crop_transparent_margins(img)
    # Keep a high-resolution square source; downsample to 1024x1024 for
    # reasonable file sizes while preserving plenty of detail for all targets.
    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    # Ensure exact square dimensions (thumbnail preserves aspect ratio).
    width, height = img.size
    size = max(width, height)
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.paste(img, ((size - width) // 2, (size - height) // 2))
    square.save(SRC_PNG, format="PNG")
    print(f"Generated: {SRC_PNG} ({square.width}x{square.height})")
    return square


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
    """Generate a multi-resolution Windows .ico file directly from the source.

    We use the original source asset (instead of the normalized 1024x1024
    square) so Windows sees the exact same transparency/contents as the
    upstream image.
    """
    source = _open_source(SRC_FILE)
    icons = []
    for size in ICO_SIZES:
        resized = source.resize((size, size), Image.Resampling.LANCZOS)
        icons.append(resized)
    ICO_OUT.unlink(missing_ok=True)
    _write_multi_ico(ICO_OUT, icons)
    print(f"Generated: {ICO_OUT}")


def generate_icns(source: Image.Image) -> bool:
    """Generate a macOS .icns file using sips + iconutil.

    Returns True on success, False if the macOS tooling is unavailable.
    """
    sips = shutil.which("sips")
    iconutil = shutil.which("iconutil")
    if not sips or not iconutil:
        print("sips/iconutil not found; skipping .icns generation.")
        print("macOS builders should run iconutil manually on icon_nobackground.iconset.")
        return False

    iconset_dir = ICON_DIR / "icon_nobackground.iconset"
    # Save a temporary high-res PNG for sips to consume.
    temp_source = ICON_DIR / "icon_nobackground_source_for_icns.png"
    source.save(temp_source, format="PNG")

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

    try:
        for filename, size in mac_sizes:
            out_path = iconset_dir / filename
            subprocess.run(
                [sips, "-z", str(size), str(size), str(temp_source), "--out", str(out_path)],
                check=True,
                capture_output=True,
            )

        ICNS_OUT.unlink(missing_ok=True)
        subprocess.run([iconutil, "-c", "icns", str(iconset_dir)], check=True)
        print(f"Generated: {ICNS_OUT}")
    finally:
        # Clean up temporary iconset and helper PNG.
        shutil.rmtree(iconset_dir, ignore_errors=True)
        temp_source.unlink(missing_ok=True)

    return True


if __name__ == "__main__":
    if not SRC_FILE.exists():
        print(f"Source icon not found: {SRC_FILE}", file=sys.stderr)
        sys.exit(1)

    source = _normalize_source()
    generate_ico()
    if sys.platform == "darwin":
        try:
            generate_icns(source)
        except Exception as e:
            print(f"Failed to generate .icns: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Run this on macOS to generate icon_nobackground.icns.")
