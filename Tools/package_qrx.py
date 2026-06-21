#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
EXTENSION_ROOT = ROOT / "Extension"
DEFAULT_OUTPUT = ROOT / "dist" / "QuartzAdBlocker.qrx"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def iter_extension_files():
    for path in sorted(EXTENSION_ROOT.rglob("*")):
        if path.is_file() and path.name != ".DS_Store":
            yield path


def load_manifest():
    manifest_path = EXTENSION_ROOT / "manifest.json"
    try:
        with manifest_path.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
    except FileNotFoundError:
        sys.exit(f"Missing required extension manifest: {manifest_path}")
    except json.JSONDecodeError as error:
        sys.exit(f"Invalid JSON in {manifest_path}: {error}")

    required_fields = ("manifest_version", "name", "version")
    missing_fields = [field for field in required_fields if field not in manifest]
    if missing_fields:
        missing = ", ".join(missing_fields)
        sys.exit(f"Extension manifest is missing required field(s): {missing}")

    return manifest


def make_zip_info(path):
    archive_name = path.relative_to(EXTENSION_ROOT).as_posix()
    info = ZipInfo(archive_name, ZIP_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def package_qrx(output_path):
    manifest = load_manifest()
    files = list(iter_extension_files())
    if not files:
        sys.exit(f"No files found to package in {EXTENSION_ROOT}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w") as archive:
        for path in files:
            archive.writestr(make_zip_info(path), path.read_bytes())

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    print(f"Wrote {output_path}")
    print(f"Packaged {len(files)} files for {manifest['name']} {manifest['version']}")
    print(f"SHA-256: {digest}")


def main():
    parser = argparse.ArgumentParser(
        description="Package the Quartz Ad Blocker extension as a single .qrx file."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Destination .qrx path. Defaults to {DEFAULT_OUTPUT}",
    )
    args = parser.parse_args()

    package_qrx(args.output.resolve())


if __name__ == "__main__":
    main()
