#!/usr/bin/env python3
"""
generate-bsi.py — generates a BattleScribe index (.bsi) file from catalogue files.

The .bsi format is XML that lists all .gst and .cat files in a repository.
New Recruit uses this index to discover and load game data.

Usage:
  python3 scripts/generate-bsi.py --name "Game Name" --output index.bsi file1.gst file2.cat ...
"""

import argparse
import xml.etree.ElementTree as ET
import xml.dom.minidom
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone


def get_file_id(path: Path) -> str:
    """Extract the id attribute from the root element of a catalogue file."""
    try:
        tree = ET.parse(path)
        return tree.getroot().get('id', '')
    except ET.ParseError as e:
        print(f"Warning: Could not parse {path}: {e}", file=sys.stderr)
        return ''


def get_file_name(path: Path) -> str:
    """Extract the name attribute from the root element."""
    try:
        tree = ET.parse(path)
        return tree.getroot().get('name', path.stem)
    except ET.ParseError:
        return path.stem


def get_revision(path: Path) -> str:
    """Extract the revision attribute."""
    try:
        tree = ET.parse(path)
        return tree.getroot().get('revision', '1')
    except ET.ParseError:
        return '1'


def file_hash(path: Path) -> str:
    """MD5 hash of file contents."""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def generate_bsi(files: list[Path], name: str, description: str, output: Path):
    root = ET.Element('dataIndex')
    root.set('battleScribeVersion', '2.03')
    root.set('name', name)
    root.set('description', description)
    root.set('battleScribeVersion', '2.03')
    root.set('xmlns', 'http://www.battlescribe.net/schema/dataIndexSchema')

    data_files = ET.SubElement(root, 'dataFiles')

    for f in sorted(files):
        f = Path(f)
        if not f.exists():
            print(f"Warning: {f} does not exist, skipping", file=sys.stderr)
            continue

        suffix = f.suffix.lower()
        if suffix not in ('.gst', '.cat'):
            continue

        file_type = 'gameSystem' if suffix == '.gst' else 'catalogue'
        file_id   = get_file_id(f)
        file_name = get_file_name(f)
        revision  = get_revision(f)

        entry = ET.SubElement(data_files, 'dataFile')
        entry.set('id',            file_id)
        entry.set('name',          file_name)
        entry.set('type',          file_type)
        entry.set('revision',      revision)
        # URL points to the raw GitHub file — users set their base URL
        entry.set('dataFileUrl',   f.name)
        entry.set('filePath',      str(f))
        entry.set('md5',           file_hash(f))

    # Pretty-print
    raw = ET.tostring(root, encoding='unicode')
    pretty = xml.dom.minidom.parseString(raw).toprettyxml(indent='  ', encoding='UTF-8')

    with open(output, 'wb') as out:
        out.write(pretty)

    print(f"✅ Generated {output} with {len(list(data_files))} entries")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate BattleScribe .bsi index file')
    parser.add_argument('files', nargs='+', help='.gst and .cat files to index')
    parser.add_argument('--name', default='Full Thrust Cross Dimensions', help='Game system name')
    parser.add_argument('--description', default='', help='Repository description')
    parser.add_argument('--output', default='index.bsi', help='Output .bsi file path')
    args = parser.parse_args()

    # Expand globs
    import glob
    all_files = []
    for pattern in args.files:
        expanded = glob.glob(pattern, recursive=True)
        all_files.extend(expanded if expanded else [pattern])

    generate_bsi(
        files=[Path(f) for f in all_files],
        name=args.name,
        description=args.description,
        output=Path(args.output)
    )
