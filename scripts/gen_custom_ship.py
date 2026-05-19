#!/usr/bin/env python3
"""
Generates custom.cat — the FTCD Ship Designer catalogue for New Recruit.

For each common ship mass, creates a selectionEntry with:
  - Hull integrity options (10–50%, pre-calculated)
  - Main drive options (thrust 0–8, pre-calculated)
  - FTL drive option (10%, pre-calculated)
  - Screen options (standard/advanced × level 1/2, pre-calculated)
  - Armour (per-box, repeatable)
  - Streamlining options
  - Links to shared weapon/system entries

All mass/pts values from FTCD rulebook rev 1.2, section 11.6.

Usage: python3 scripts/gen_custom_ship.py
Output: custom.cat
"""

import math
import hashlib
import os
import sys

# ─── Cost type IDs (matching all existing .cat files) ─────────────────────────
PTS_ID  = "7d62-4668-5257"
MASS_ID = "4771-3924-56de"
GS_ID   = "ftcd-0001-gs01"

# ─── Ship masses to support ───────────────────────────────────────────────────
MASSES = [6, 8, 10, 12, 14, 16, 20, 24, 30, 36, 44, 60, 90, 120, 180, 240, 300]

# ─── ID generation ────────────────────────────────────────────────────────────
def uid(*parts: str) -> str:
    """Deterministic 4-4-4 hex ID from semantic key parts."""
    key = "|".join(str(p) for p in parts)
    h = hashlib.md5(key.encode()).hexdigest()
    return f"{h[0:4]}-{h[4:8]}-{h[8:12]}"


# ─── FTCD physics ─────────────────────────────────────────────────────────────
def drive_mass(total: int, thrust: int) -> int:
    if thrust == 0:
        return 0
    return max(1, round(total * 0.05 * thrust))

def ftl_mass(total: int) -> int:
    return max(1, round(total * 0.1))

def screen_mass(total: int, advanced: bool, level: int) -> int:
    pct   = 0.075 if advanced else 0.05
    min_m = 4     if advanced else 3
    base  = max(min_m, round(total * pct))
    return base * level

def screen_pts(mass: int, advanced: bool) -> int:
    return mass * (4 if advanced else 3)

def hull_boxes(total: int, pct: int) -> int:
    return math.ceil(total * pct / 100)


# ─── XML helpers ──────────────────────────────────────────────────────────────
def cost(pts: float, mass: float) -> str:
    return (
        f'<costs>'
        f'<cost name="pts" typeId="{PTS_ID}" value="{int(pts)}"/>'
        f'<cost name="Mass" typeId="{MASS_ID}" value="{int(mass)}"/>'
        f'</costs>'
    )

def constraint(ctype: str, value: int, field: str, scope: str,
               include_children: bool = False) -> str:
    inc = "true" if include_children else "false"
    cid = uid("con", ctype, value, field, scope)
    return (
        f'<constraint id="{cid}" type="{ctype}" value="{value}" '
        f'field="{field}" scope="{scope}" shared="false" '
        f'includeChildSelections="{inc}"/>'
    )


# ─── Shared system entries (fixed mass/pts, not ship-mass-dependent) ──────────
# (id_key, name, mass, pts)
SYSTEMS = [
    # Fire control
    ("firecon",       "Fire Control",                             1,  4),
    ("adfc",          "ADFC (Area Defence Fire Control)",         2,  8),
    # Beams — class 1
    ("beam1",         "Beam Battery Class 1 (all arcs)",          1,  3),
    # Beams — class 2
    ("beam2-3arc",    "Beam Battery Class 2 (3-arc, 180°)",       2,  6),
    ("beam2-6arc",    "Beam Battery Class 2 (broadside/6-arc)",   3,  9),
    # Beams — class 3
    ("beam3-1arc",    "Beam Battery Class 3 (1 arc)",             4, 12),
    ("beam3-2arc",    "Beam Battery Class 3 (2 arcs)",            5, 15),
    ("beam3-3arc",    "Beam Battery Class 3 (3 arcs)",            6, 18),
    ("beam3-broad",   "Beam Battery Class 3 (broadside)",         6, 18),
    # Beams — class 4
    ("beam4-1arc",    "Beam Battery Class 4 (1 arc)",             8, 24),
    ("beam4-2arc",    "Beam Battery Class 4 (2 arcs)",           10, 30),
    ("beam4-3arc",    "Beam Battery Class 4 (3 arcs)",           12, 36),
    ("beam4-broad",   "Beam Battery Class 4 (broadside)",        12, 36),
    # Grasers — class 1
    ("graser1-1arc",  "Graser Class 1 (1 arc)",                   2,  8),
    ("graser1-3arc",  "Graser Class 1 (3 arcs)",                  3, 12),
    ("graser1-broad", "Graser Class 1 (broadside/6 arcs)",        4, 16),
    # Grasers — class 2
    ("graser2-1arc",  "Graser Class 2 (1 arc)",                   9, 36),
    ("graser2-2arc",  "Graser Class 2 (2 arcs)",                 12, 48),
    ("graser2-3arc",  "Graser Class 2 (3 arcs)",                 15, 60),
    ("graser2-broad", "Graser Class 2 (broadside)",              15, 60),
    # Grasers — class 3
    ("graser3-1arc",  "Graser Class 3 (1 arc)",                  24, 96),
    ("graser3-3arc",  "Graser Class 3 (3 arcs)",                 36,144),
    ("graser3-broad", "Graser Class 3 (broadside)",              36,144),
    # Torpedoes — class 1
    ("torp1-1arc",    "Torpedo Class 1 (1 arc)",                  4, 12),
    ("torp1-2arc",    "Torpedo Class 1 (2 arcs)",                 5, 15),
    ("torp1-3arc",    "Torpedo Class 1 (3 arcs)",                 6, 18),
    ("torp1-broad",   "Torpedo Class 1 (broadside)",              6, 18),
    # Torpedoes — class 2
    ("torp2-1arc",    "Torpedo Class 2 (1 arc)",                  8, 24),
    ("torp2-2arc",    "Torpedo Class 2 (2 arcs)",                10, 30),
    ("torp2-3arc",    "Torpedo Class 2 (3 arcs)",                12, 36),
    ("torp2-broad",   "Torpedo Class 2 (broadside)",             12, 36),
    # Torpedoes — class 3
    ("torp3-1arc",    "Torpedo Class 3 (1 arc)",                 16, 48),
    ("torp3-3arc",    "Torpedo Class 3 (3 arcs)",                24, 72),
    # Point defence
    ("pds",           "Point Defence System (PDS)",               1,  3),
    ("scattergun",    "Scattergun",                               1,  4),
    ("needle",        "Needle Weapon",                            2,  6),
    ("submunition",   "Submunition Pack",                         1,  3),
    # Missiles
    ("sml",           "Salvo Missile Launcher (SML, launcher)",   3,  9),
    ("sml-mag",       "SML Magazine (1 standard salvo)",          2,  6),
    ("sml-mag-er",    "SML Magazine (1 extended-range salvo)",    3,  9),
    ("smr",           "Salvo Missile Rack (SMR)",                 4, 12),
    ("smr-er",        "SMR (extended range)",                     5, 15),
    ("heavy-miss",    "Heavy Missile",                            2,  6),
    ("heavy-miss-er", "Heavy Missile (extended range)",           3,  9),
    # Optional systems
    ("ecm",           "ECM System",                               4, 16),
    ("ecm-area",      "Area Effect ECM",                          6, 24),
    ("sensors-enh",   "Enhanced Sensors",                         2,  8),
    ("sensors-sup",   "Superior Sensors",                         4, 16),
    ("ortillery",     "Ortillery System",                         3,  9),
    ("minelayer",     "Minelayer",                                2,  6),
    ("minesweeper",   "Minesweeper",                              5, 15),
    ("marines",       "Marines",                                  0,  0),
    ("dmg-ctrl",      "Damage Control Party",                     0,  0),
    # Fighters (per group of 6)
    ("hangar-std",    "Fighter Hangar (standard, 6 fighters)",    9, 27),
    ("ftr-std",       "Fighter Group — Standard (6×)",            0, 18),
    ("ftr-fast",      "Fighter Group — Fast (6×)",                0, 24),
    ("ftr-heavy",     "Fighter Group — Heavy (6×)",               0, 30),
    ("ftr-intercept", "Fighter Group — Interceptor (6×)",         0, 18),
    ("ftr-attack",    "Fighter Group — Attack (6×)",              0, 24),
    ("ftr-torpedo",   "Fighter Group — Torpedo (6×)",             0, 36),
]

SHIP_CATEGORY_ID = "cat-ship-0001"  # defined in .gst


# ─── XML builders ─────────────────────────────────────────────────────────────

def make_shared_entry(key: str, name: str, mass: int, pts: int) -> str:
    eid = uid("shared", key)
    return f"""    <selectionEntry id="{eid}" name="{name}" hidden="false" collective="false" import="true" type="upgrade">
      {cost(pts, mass)}
    </selectionEntry>"""


def make_ship_entry(M: int, shared_ids: dict[str, str]) -> str:
    sid = uid("ship", M)

    # ── Hull integrity group ──────────────────────────────────────────────────
    hull_group_id = uid("grp", "hull", M)
    hull_default_id = uid("hull", M, 30)  # default: average (30%)
    hull_entries = []
    for pct, hull_name in [(10, "Fragile"), (20, "Weak"), (30, "Average"), (40, "Strong"), (50, "Super")]:
        boxes = hull_boxes(M, pct)
        eid = uid("hull", M, pct)
        pts_cost = boxes * 2
        selected = ' defaultSelected="true"' if pct == 30 else ''
        hull_entries.append(f"""\
          <selectionEntry id="{eid}" name="{hull_name} Hull — {boxes} boxes ({pct}%)" type="upgrade" hidden="false" collective="false" import="true"{selected}>
            {cost(pts_cost, boxes)}
          </selectionEntry>""")

    hull_group = f"""\
        <selectionEntryGroup id="{hull_group_id}" name="Hull Integrity" hidden="false"
                             defaultSelectionEntryId="{uid('hull', M, 30)}"
                             minSelections="1" maxSelections="1">
          <selectionEntries>
{chr(10).join(hull_entries)}
          </selectionEntries>
        </selectionEntryGroup>"""

    # ── Armour entry (repeatable, up to 20 boxes) ────────────────────────────
    # maxSelections="-1" = unlimited at group level; inner constraint limits to 20
    armour_group_id = uid("grp", "armour", M)
    armour_eid = uid("armour-box", M)
    armour_group = f"""\
        <selectionEntryGroup id="{armour_group_id}" name="Armour" hidden="false"
                             minSelections="0" maxSelections="-1">
          <selectionEntries>
            <selectionEntry id="{armour_eid}" name="Armour (per box)" type="upgrade" hidden="false" collective="false" import="true">
              <constraints>
                <constraint id="{uid('con','armour-max',M)}" type="max" value="20" field="selections" scope="parent" shared="false"/>
              </constraints>
              {cost(2, 1)}
            </selectionEntry>
          </selectionEntries>
        </selectionEntryGroup>"""

    # ── Streamlining group ────────────────────────────────────────────────────
    stream_group_id = uid("grp", "stream", M)
    partial_m = max(1, math.ceil(M * 0.05))
    full_m    = max(1, math.ceil(M * 0.10))
    stream_group = f"""\
        <selectionEntryGroup id="{stream_group_id}" name="Streamlining" hidden="false"
                             minSelections="0" maxSelections="1">
          <selectionEntries>
            <selectionEntry id="{uid('stream','partial',M)}" name="Partial Streamlining ({partial_m} mass)" type="upgrade" hidden="false" collective="false" import="true">
              {cost(partial_m * 2, partial_m)}
            </selectionEntry>
            <selectionEntry id="{uid('stream','full',M)}" name="Full Streamlining ({full_m} mass)" type="upgrade" hidden="false" collective="false" import="true">
              {cost(full_m * 2, full_m)}
            </selectionEntry>
          </selectionEntries>
        </selectionEntryGroup>"""

    # ── Main drive group ──────────────────────────────────────────────────────
    drive_group_id = uid("grp", "drive", M)
    drive_entries = []
    # Thrust 0 (no drive)
    drive_entries.append(f"""\
          <selectionEntry id="{uid('drive', M, 0)}" name="No Drive (Thrust 0)" type="upgrade" hidden="false" collective="false" import="true">
            {cost(0, 0)}
          </selectionEntry>""")
    for T in range(1, 9):
        dm = drive_mass(M, T)
        eid = uid("drive", M, T)
        drive_entries.append(f"""\
          <selectionEntry id="{eid}" name="Main Drive Thrust {T} ({dm} mass)" type="upgrade" hidden="false" collective="false" import="true">
            {cost(dm * 2, dm)}
          </selectionEntry>""")
    # Advanced drive entries
    for T in range(1, 9):
        dm = drive_mass(M, T)
        eid = uid("drive-adv", M, T)
        drive_entries.append(f"""\
          <selectionEntry id="{eid}" name="Advanced Drive Thrust {T} ({dm} mass)" type="upgrade" hidden="false" collective="false" import="true">
            {cost(dm * 3, dm)}
          </selectionEntry>""")

    drive_group = f"""\
        <selectionEntryGroup id="{drive_group_id}" name="Main Drive" hidden="false"
                             defaultSelectionEntryId="{uid('drive', M, 4)}"
                             minSelections="1" maxSelections="1">
          <selectionEntries>
{chr(10).join(drive_entries)}
          </selectionEntries>
        </selectionEntryGroup>"""

    # ── FTL drive group ───────────────────────────────────────────────────────
    ftl_group_id = uid("grp", "ftl", M)
    fm = ftl_mass(M)
    ftl_group = f"""\
        <selectionEntryGroup id="{ftl_group_id}" name="FTL Drive (optional)" hidden="false"
                             minSelections="0" maxSelections="1">
          <selectionEntries>
            <selectionEntry id="{uid('ftl', M)}" name="FTL Drive ({fm} mass)" type="upgrade" hidden="false" collective="false" import="true">
              {cost(fm * 2, fm)}
            </selectionEntry>
            <selectionEntry id="{uid('ftl-adv', M)}" name="Advanced FTL Drive ({fm} mass)" type="upgrade" hidden="false" collective="false" import="true">
              {cost(fm * 3, fm)}
            </selectionEntry>
          </selectionEntries>
        </selectionEntryGroup>"""

    # ── Screen group ──────────────────────────────────────────────────────────
    screen_group_id = uid("grp", "screen", M)
    screen_entries = []
    for advanced in [False, True]:
        for level in [1, 2]:
            sm = screen_mass(M, advanced, level)
            sp = screen_pts(sm, advanced)
            adv_str = "Advanced " if advanced else ""
            eid = uid("screen", M, "adv" if advanced else "std", level)
            screen_entries.append(f"""\
            <selectionEntry id="{eid}" name="{adv_str}Screen Level {level} ({sm} mass)" type="upgrade" hidden="false" collective="false" import="true">
              {cost(sp, sm)}
            </selectionEntry>""")

    screen_group = f"""\
        <selectionEntryGroup id="{screen_group_id}" name="Defensive Screen" hidden="false"
                             minSelections="0" maxSelections="1">
          <selectionEntries>
{chr(10).join(screen_entries)}
          </selectionEntries>
        </selectionEntryGroup>"""

    # ── Links to shared weapon/system entries ─────────────────────────────────
    links = []
    for key in shared_ids:
        lid = uid("link", M, key)
        links.append(f'      <selectionEntryLink id="{lid}" targetId="{shared_ids[key]}" hidden="false" collective="false" import="true"/>')

    links_xml = "\n".join(links)

    # ── Assemble ship entry ───────────────────────────────────────────────────
    # Basic hull cost = M × 1 pts (from rulebook: "basic hull: total mass × 1")
    ship_class = _ship_class(M)
    return f"""\
    <selectionEntry id="{sid}" name="Custom Ship (Mass {M}) [{ship_class}]" hidden="false" collective="false" import="true" type="unit">
      {cost(M, 0)}
      <constraints>
        <constraint id="{uid('con','masscap',M)}" type="max" value="{M}" field="Mass" scope="self" shared="false" includeChildSelections="true"/>
      </constraints>
      <categoryLinks>
        <categoryLink id="{uid('cl','ship',M)}" name="Ship" hidden="false" targetId="{SHIP_CATEGORY_ID}" primary="true"/>
      </categoryLinks>
      <selectionEntryGroups>
{hull_group}
{armour_group}
{stream_group}
{drive_group}
{ftl_group}
{screen_group}
      </selectionEntryGroups>
      <selectionEntryLinks>
{links_xml}
      </selectionEntryLinks>
    </selectionEntry>"""


def _ship_class(M: int) -> str:
    table = [
        (4,  10,  "SC — Scout/Courier"),
        (8,  16,  "CT — Corvette"),
        (14, 28,  "FF — Frigate"),
        (24, 36,  "DD — Destroyer"),
        (30, 44,  "DH — Heavy Destroyer"),
        (40, 60,  "CL — Light Cruiser"),
        (50, 70,  "CE — Escort Cruiser"),
        (60, 90,  "CA — Heavy Cruiser"),
        (80, 110, "BC — Battlecruiser"),
        (100, 140,"BB — Battleship"),
        (140, 180,"DN — Dreadnought"),
        (160, 300,"SDN — Superdreadnought"),
        (60, 140, "CVE — Escort Carrier"),
        (120, 180,"CVL — Light Carrier"),
        (160, 300,"CVH — Heavy Carrier"),
    ]
    matches = [label for lo, hi, label in table if lo <= M <= hi]
    if matches:
        return matches[0]
    return "Custom"


# ─── Main ──────────────────────────────────────────────────────────────────────

def generate() -> str:
    # Build shared system ID map
    shared_ids: dict[str, str] = {}
    for key, *_ in SYSTEMS:
        shared_ids[key] = uid("shared", key)

    # Shared entries XML
    shared_xml_parts = []
    for key, name, mass, pts in SYSTEMS:
        shared_xml_parts.append(make_shared_entry(key, name, mass, pts))
    shared_xml = "\n".join(shared_xml_parts)

    # Ship entries XML
    ship_xml_parts = []
    for M in MASSES:
        ship_xml_parts.append(make_ship_entry(M, shared_ids))
    ships_xml = "\n\n".join(ship_xml_parts)

    cat_id = uid("cat", "custom-ship-builder")

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<catalogue id="{cat_id}" name="FTCD Ship Designer"
           revision="1" battleScribeVersion="2.03"
           gameSystemId="{GS_ID}"
           gameSystemRevision="1"
           xmlns="http://www.battlescribe.net/schema/catalogueSchema">

  <!--
    FTCD Ship Designer — free ship builder for Full Thrust: Cross Dimensions.

    Usage in New Recruit:
    1. Add this catalogue alongside a faction catalogue.
    2. Create a new roster and select "FTCD Ship Designer" as your force.
    3. Add a "Custom Ship (Mass X)" for the mass range you want.
    4. Select hull integrity, drive, and systems. Mass and CPV are tracked automatically.

    Mass budget: New Recruit shows "Mass used / Mass total" per ship.
    CPV: shown as "pts" in the roster total.

    All values from FTCD rulebook rev 1.2, section 11.6.
  -->

  <selectionEntries>
{ships_xml}
  </selectionEntries>

  <sharedSelectionEntries>
{shared_xml}
  </sharedSelectionEntries>

</catalogue>
"""


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "..", "custom.cat")
    out_path = os.path.normpath(out_path)
    xml = generate()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"Generated {out_path} ({len(xml):,} bytes, {xml.count('<selectionEntry'):} entries)")
