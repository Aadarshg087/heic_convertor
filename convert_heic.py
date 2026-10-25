r"""
Bulk HEIC -> JPG converter (runs fully offline).

Setup (once):
    pip install pillow pillow-heif

Usage (PowerShell, from any folder):
    python convert_heic.py "C:\Users\You\Pictures\iPhone"
    python convert_heic.py "C:\Photos" --out "C:\Photos_JPG" --quality 95

If no folder is given, the current folder is used.

What it does:
  - Finds .heic/.heif files (including subfolders)
  - Saves JPGs into a separate output folder (originals are never touched)
  - Keeps EXIF data (date taken, GPS location, camera info)
  - Sets the JPG's file date to match the original photo
  - Skips files already converted, so you can safely re-run it
  - Reports any failures at the end instead of stopping
"""
import argparse
import os
import sys
from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

EXTENSIONS = {".heic", ".heif"}


def find_files(root: Path):
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in EXTENSIONS)


def convert(src: Path, dst: Path, quality: int):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        exif = img.info.get("exif")
        rgb = img.convert("RGB")
        save_kwargs = {"quality": quality, "optimize": True}
        if exif:
            save_kwargs["exif"] = exif
        rgb.save(dst, "JPEG", **save_kwargs)
    stat = src.stat()
    os.utime(dst, (stat.st_atime, stat.st_mtime))


def main():
    parser = argparse.ArgumentParser(description="Bulk convert HEIC photos to JPG.")
    parser.add_argument("folder", nargs="?", default=".", help="Folder with HEIC photos")
    parser.add_argument("--out", help="Output folder (default: <folder>/converted_jpg)")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality 1-100 (default 95)")
    args = parser.parse_args()

    root = Path(args.folder).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Folder not found: {root}")

    out_root = Path(args.out).expanduser().resolve() if args.out else root / "converted_jpg"
    files = [f for f in find_files(root) if out_root not in f.parents]

    if not files:
        sys.exit("No HEIC files found.")

    print(f"Found {len(files)} photo(s). Output: {out_root}\n")

    done = skipped = 0
    failed = []

    for i, src in enumerate(files, 1):
        dst = out_root / src.relative_to(root).with_suffix(".jpg")
        if dst.exists():
            skipped += 1
            continue
        try:
            convert(src, dst, args.quality)
            done += 1
        except Exception as e:
            failed.append((src, str(e)))
        if i % 25 == 0 or i == len(files):
            print(f"  {i}/{len(files)} processed")

    print(f"\nConverted: {done} | Skipped (already done): {skipped} | Failed: {len(failed)}")
    for path, err in failed:
        print(f"  FAILED: {path} ({err})")


if __name__ == "__main__":
    main()