#!/usr/bin/env python3
"""
FTCD BattleScribe catalogue validator.
Usage: python3 scripts/validate.py [file_or_glob]
       python3 scripts/validate.py catalogues/system/full-thrust-cross-dimensions.gst
       python3 scripts/validate.py catalogues/factions/nsc.cat
       python3 scripts/validate.py all
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

NS = {
    'gs': 'http://www.battlescribe.net/schema/gameSystemSchema',
    'cat': 'http://www.battlescribe.net/schema/catalogueSchema',
}

def check_xml(path):
    try:
        tree = ET.parse(path)
        return tree, None
    except ET.ParseError as e:
        return None, str(e)

def check_ids(tree):
    all_ids = []
    for elem in tree.iter():
        eid = elem.get('id')
        if eid:
            all_ids.append(eid)
    dupes = [i for i, c in defaultdict(int, {x: all_ids.count(x) for x in all_ids}).items() if c > 1]
    return dupes

def check_ftcd_compliance(tree, path):
    issues = []
    root = tree.getroot()
    tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag

    if tag == 'catalogue':
        # Check gameSystemId is present
        if not root.get('gameSystemId'):
            issues.append("Missing gameSystemId attribute on <catalogue>")

        # Check each unit selectionEntry has mass constraint
        for entry in root.iter():
            etag = entry.tag.split('}')[-1] if '}' in entry.tag else entry.tag
            if etag == 'selectionEntry' and entry.get('type') == 'unit':
                name = entry.get('name', '?')
                constraints = [c for c in entry.iter()
                               if (c.tag.split('}')[-1] if '}' in c.tag else c.tag) == 'constraint']
                mass_constraints = [c for c in constraints
                                    if c.get('field') == 'Mass' and c.get('type') == 'max']
                if not mass_constraints:
                    issues.append(f"Unit '{name}' has no Mass constraint")

    return issues

def validate_file(path):
    p = Path(path)
    print(f"\n=== Validating: {p.name} ===")

    # Step 1: XML
    tree, err = check_xml(p)
    if err:
        print(f"  ❌ XML malformed: {err}")
        print(f"  Status: FAIL\n")
        return False
    print(f"  ✅ XML well-formed")

    # Step 2: IDs
    dupes = check_ids(tree)
    if dupes:
        print(f"  ❌ Duplicate IDs: {dupes}")
    else:
        print(f"  ✅ All IDs unique")

    # Step 3: FTCD compliance
    issues = check_ftcd_compliance(tree, p)
    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print(f"  ✅ FTCD compliance OK")

    passed = not dupes and not issues
    print(f"  Status: {'PASS' if passed else 'FAIL'}")
    return passed

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if target == 'all':
        files = (list(Path('.').glob('*.gst')) + list(Path('.').glob('*.cat'))
                 + list(Path('catalogues').rglob('*.gst')) + list(Path('catalogues').rglob('*.cat')))
    else:
        files = list(Path('.').glob(target)) if '*' in target else [Path(target)]

    if not files:
        print(f"No files found matching: {target}")
        sys.exit(1)

    results = [validate_file(f) for f in files]
    total = len(results)
    passed = sum(results)
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    sys.exit(0 if all(results) else 1)
