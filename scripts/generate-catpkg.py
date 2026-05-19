#!/usr/bin/env python3
"""
generate-catpkg.py — generates a catpkg.json index from catalogue files.

The catpkg.json format is used by New Recruit's "Add from GitHub" feature
to discover and load game data from a repository release.

Usage:
  python3 scripts/generate-catpkg.py --output ftcd.catpkg.json \
    --base-url https://raw.githubusercontent.com/USER/REPO/main \
    catalogues/system/*.gst catalogues/factions/*.cat
"""

import argparse
import glob
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def get_attr(path: Path, attr: str, default: str = '') -> str:
    try:
        return ET.parse(path).getroot().get(attr, default)
    except ET.ParseError:
        return default


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def generate_catpkg(files: list[Path], base_url: str, output: Path):
    base_url = base_url.rstrip('/')
    repo_url = 'https://github.com/DDxMI7/ftcd-newrecruit'

    entries = []
    gst_name = 'Full Thrust Cross Dimensions'

    for f in sorted(files):
        f = Path(f)
        if not f.exists() or f.suffix.lower() not in ('.gst', '.cat'):
            continue

        file_type = 'gameSystem' if f.suffix.lower() == '.gst' else 'catalogue'
        rel = str(f)
        url = f'{base_url}/{rel}'
        name = get_attr(f, 'name', f.stem)
        if file_type == 'gameSystem':
            gst_name = name

        entries.append({
            'id': get_attr(f, 'id'),
            'name': name,
            'type': file_type,
            'revision': int(get_attr(f, 'revision', '1')),
            'battleScribeVersion': get_attr(f, 'battleScribeVersion', '2.03'),
            'fileUrl': url,
            'githubUrl': url,
            'bugTrackerUrl': f'{repo_url}/issues',
            'reportBugUrl': f'{repo_url}/issues/new',
            'sha256': sha256(f),
        })

    pkg = {
        'name': gst_name,
        'battleScribeVersion': '2.03',
        'description': 'BattleScribe/New Recruit catalogues for Full Thrust Cross Dimensions (FTCD)',
        'repositoryFiles': entries,
    }

    output.write_text(json.dumps(pkg, indent=2))
    print(f'Generated {output} with {len(entries)} entries')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--output', default='ftcd.catpkg.json')
    parser.add_argument('--base-url', default='')
    args = parser.parse_args()

    all_files = []
    for pattern in args.files:
        expanded = glob.glob(pattern, recursive=True)
        all_files.extend(expanded if expanded else [pattern])

    generate_catpkg(
        files=[Path(f) for f in all_files],
        base_url=args.base_url,
        output=Path(args.output),
    )
