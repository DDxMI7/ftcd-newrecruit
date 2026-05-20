#!/usr/bin/env python3
"""
Generates custom.cat — the FTCD Ship Designer catalogue for New Recruit.

Covers every valid FTCD ship mass (4–10 any, 12–300 even = 152 masses).
For each mass the catalogue pre-computes all hull-integrity / drive / screen
options so that "Mass" and "pts" are tracked automatically in New Recruit
without any formula engine.

Perlkonig builder workflow, adapted for BattleScribe:
  1. Pick ship mass  →  "Custom Ship [Mass X] — <class>"
  2. Choose hull integrity (10–50 % of mass)
  3. Choose drive thrust (0–8, standard or advanced)
  4. Toggle FTL drive (standard or advanced, optional)
  5. Add screens, armour, streamlining
  6. Add weapons and systems from shared list

All values from FTCD rulebook rev 1.2, § 11.4–11.6.

Usage:  python3 scripts/gen_custom_ship.py
Output: custom.cat
"""

import math
import hashlib
import os

# ─── Cost type IDs (must match existing .cat / .gst files) ────────────────────
PTS_ID  = "7d62-4668-5257"
MASS_ID = "4771-3924-56de"
GS_ID   = "ftcd-0001-gs01"
CAT_ID  = "51af-a23a-9d57"          # keep stable so faction catalogueLinks don't break
SHIP_CAT = "876f-9a8d-ca03"          # category defined in .gst

# ─── All valid FTCD ship masses ───────────────────────────────────────────────
# Rules: any 4-10; must be even if > 10; max 300
MASSES = list(range(4, 11)) + list(range(12, 302, 2))   # 152 values


# ─── Deterministic ID generation ─────────────────────────────────────────────
def uid(*parts) -> str:
    key = "|".join(str(p) for p in parts)
    return hashlib.md5(key.encode()).hexdigest()[:12]


def fid(*parts) -> str:
    """Formatted as XXXX-XXXX-XXXX."""
    h = uid(*parts)
    return f"{h[0:4]}-{h[4:8]}-{h[8:12]}"


# ─── FTCD physics ─────────────────────────────────────────────────────────────
def drive_mass(total: int, thrust: int) -> int:
    """Main drive mass = 5 % of total per thrust factor, min 1 (if thrust > 0)."""
    if thrust == 0:
        return 0
    return max(1, round(total * 0.05 * thrust))


def ftl_mass(total: int) -> int:
    """FTL drive mass = 10 % of total, min 1."""
    return max(1, round(total * 0.1))


def screen_mass(total: int, advanced: bool, level: int) -> int:
    """Screen mass = 5 % (std) or 7.5 % (adv) of total, min 3/4; × level."""
    pct   = 0.075 if advanced else 0.05
    min_m = 4     if advanced else 3
    return max(min_m, round(total * pct)) * level


def screen_pts(mass: int, advanced: bool) -> int:
    return mass * (4 if advanced else 3)


def hull_boxes(total: int, pct: int) -> int:
    return math.ceil(total * pct / 100)


# ─── Ship class labelling ──────────────────────────────────────────────────────
_CLASS_TABLE = [
    (  4,  10, "SC"),
    (  8,  16, "CT"),
    ( 14,  28, "FF"),
    ( 24,  36, "DD"),
    ( 30,  44, "DH"),
    ( 40,  60, "CL"),
    ( 50,  70, "CE"),
    ( 60,  90, "CA"),
    ( 80, 110, "BC"),
    (100, 140, "BB"),
    (140, 180, "DN"),
    (160, 300, "SDN"),
    ( 60, 140, "CVE"),
    (120, 180, "CVL"),
    (160, 300, "CVH"),
    (150, 300, "CVA"),
]
_CLASS_NAMES = {
    "SC":  "Scout/Courier",
    "CT":  "Corvette",
    "FF":  "Frigate",
    "DD":  "Destroyer",
    "DH":  "Heavy Destroyer",
    "CL":  "Light Cruiser",
    "CE":  "Escort Cruiser",
    "CA":  "Heavy Cruiser",
    "BC":  "Battlecruiser",
    "BB":  "Battleship",
    "DN":  "Dreadnought",
    "SDN": "Superdreadnought",
    "CVE": "Escort Carrier",
    "CVL": "Light Carrier",
    "CVH": "Heavy Carrier",
    "CVA": "Attack Carrier",
}

# Priority order: warships first, then carriers
_PRIORITY = ["SC","CT","FF","DD","DH","CL","CE","CA","BC","BB","DN","SDN",
             "CVE","CVL","CVH","CVA"]

def ship_class_label(M: int) -> str:
    """Return primary class abbreviation + all applicable, e.g. 'CA / CVE'."""
    matches = [c for lo, hi, c in _CLASS_TABLE if lo <= M <= hi]
    if not matches:
        return "Custom"
    # sort by priority list
    matches.sort(key=lambda c: _PRIORITY.index(c) if c in _PRIORITY else 99)
    # deduplicate preserving order
    seen, ordered = set(), []
    for c in matches:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    abbrevs = " / ".join(ordered)
    # full name of primary class
    primary_name = _CLASS_NAMES.get(ordered[0], "")
    return f"{abbrevs} — {primary_name}" if primary_name else abbrevs


# ─── XML micro-helpers ─────────────────────────────────────────────────────────
def costs(pts: int, mass: int) -> str:
    return (f'<costs>'
            f'<cost name="pts" typeId="{PTS_ID}" value="{pts}"/>'
            f'<cost name="Mass" typeId="{MASS_ID}" value="{mass}"/>'
            f'</costs>')


def sel_entry(eid: str, name: str, mass: int, pts: int,
              extra_constraints: str = "", default: bool = False) -> str:
    default_attr = ' defaultSelected="true"' if default else ''
    inner_c = f"<constraints>{extra_constraints}</constraints>" if extra_constraints else ""
    return (f'<selectionEntry id="{eid}" name="{name}" '
            f'hidden="false" collective="false" import="true" type="upgrade"{default_attr}>'
            f'{inner_c}'
            f'{costs(pts, mass)}'
            f'</selectionEntry>')


def seg(seg_id: str, name: str, min_sel: int, max_sel: int,
        entries: list[str], default_id: str = "") -> str:
    default_attr = f' defaultSelectionEntryId="{default_id}"' if default_id else ""
    entries_xml = "\n          ".join(entries)
    return (
        f'<selectionEntryGroup id="{seg_id}" name="{name}" hidden="false"'
        f'{default_attr} minSelections="{min_sel}" maxSelections="{max_sel}">'
        f'<selectionEntries>'
        f'\n          {entries_xml}\n        '
        f'</selectionEntries>'
        f'</selectionEntryGroup>'
    )


# ─── Per-ship groups ───────────────────────────────────────────────────────────

def hull_group(M: int) -> str:
    entries = []
    default_id = ""
    for pct, label in [(10,"Fragile"),(20,"Weak"),(30,"Average"),(40,"Strong"),(50,"Super")]:
        boxes = hull_boxes(M, pct)
        eid = fid("hull", M, pct)
        if pct == 30:
            default_id = eid
        entries.append(sel_entry(eid,
            f"{label} hull — {boxes} boxes ({pct} %)",
            mass=boxes, pts=boxes * 2, default=(pct == 30)))
    return seg(fid("grp","hull",M), "Hull integrity", 1, 1, entries, default_id)


def drive_group(M: int) -> str:
    entries = []
    default_id = fid("drive", M, 4)
    # Thrust 0
    entries.append(sel_entry(fid("drive",M,0), "No drive (thrust 0)", 0, 0))
    # Standard drives thrust 1-8
    for T in range(1, 9):
        dm = drive_mass(M, T)
        entries.append(sel_entry(fid("drive",M,T),
            f"Drive thrust {T} — {dm} mass  (std, × 2 pts)",
            mass=dm, pts=dm * 2, default=(T == 4)))
    # Advanced drives thrust 1-8
    for T in range(1, 9):
        dm = drive_mass(M, T)
        entries.append(sel_entry(fid("drive-adv",M,T),
            f"Drive thrust {T} — {dm} mass  (advanced, × 3 pts)",
            mass=dm, pts=dm * 3))
    return seg(fid("grp","drive",M), "Main drive", 1, 1, entries, default_id)


def ftl_group(M: int) -> str:
    fm = ftl_mass(M)
    entries = [
        sel_entry(fid("ftl",M),
            f"FTL drive — {fm} mass  (std, × 2 pts)", mass=fm, pts=fm * 2),
        sel_entry(fid("ftl-adv",M),
            f"Advanced FTL drive — {fm} mass  (× 3 pts)", mass=fm, pts=fm * 3),
    ]
    return seg(fid("grp","ftl",M), "FTL drive (optional)", 0, 1, entries)


def screen_group(M: int) -> str:
    entries = []
    for advanced in (False, True):
        for level in (1, 2):
            sm = screen_mass(M, advanced, level)
            sp = screen_pts(sm, advanced)
            tag = "Adv. " if advanced else ""
            eid = fid("screen",M,"adv" if advanced else "std", level)
            pts_label = "× 4" if advanced else "× 3"
            entries.append(sel_entry(eid,
                f"{tag}Defensive screen level {level} — {sm} mass  ({pts_label} pts)",
                mass=sm, pts=sp))
    return seg(fid("grp","screen",M), "Defensive screen", 0, 1, entries)


def armour_group(M: int) -> str:
    """Repeatable: up to 20 armour boxes (1 mass / 2 pts each)."""
    con = (f'<constraint id="{fid("con","armour-max",M)}" '
           f'type="max" value="20" field="selections" scope="parent" shared="false"/>')
    entry = sel_entry(fid("armour",M), "Armour — 1 box  (1 mass / 2 pts)",
                      mass=1, pts=2, extra_constraints=con)
    return seg(fid("grp","armour",M), "Armour (each box)", 0, -1, [entry])


def stream_group(M: int) -> str:
    pm = max(1, math.ceil(M * 0.05))
    fm = max(1, math.ceil(M * 0.10))
    entries = [
        sel_entry(fid("stream","partial",M),
            f"Partial streamlining — {pm} mass  (× 2 pts)", mass=pm, pts=pm * 2),
        sel_entry(fid("stream","full",M),
            f"Full streamlining — {fm} mass  (× 2 pts)", mass=fm, pts=fm * 2),
    ]
    return seg(fid("grp","stream",M), "Streamlining", 0, 1, entries)


# ─── Shared system entries (not ship-mass-dependent) ──────────────────────────
# (key, display-name, mass, pts)
SYSTEMS: list[tuple[str, str, int, int]] = [
    # ── Fire control ──────────────────────────────────────────────────────────
    ("firecon",       "Fire control (FireCon)",                      1,  4),
    ("adfc",          "Area defence fire control (ADFC)",            2,  8),
    # ── Beam batteries ────────────────────────────────────────────────────────
    ("beam1",         "Beam class 1  (all arcs, 1 mass)",            1,  3),
    ("beam2-3arc",    "Beam class 2  (3-arc 180°, 2 mass)",          2,  6),
    ("beam2-6arc",    "Beam class 2  (broadside / 6-arc, 3 mass)",   3,  9),
    ("beam3-1arc",    "Beam class 3  (1 arc, 4 mass)",               4, 12),
    ("beam3-2arc",    "Beam class 3  (2 arcs, 5 mass)",              5, 15),
    ("beam3-3arc",    "Beam class 3  (3 arcs, 6 mass)",              6, 18),
    ("beam3-broad",   "Beam class 3  (broadside, 6 mass)",           6, 18),
    ("beam4-1arc",    "Beam class 4  (1 arc, 8 mass)",               8, 24),
    ("beam4-2arc",    "Beam class 4  (2 arcs, 10 mass)",            10, 30),
    ("beam4-3arc",    "Beam class 4  (3 arcs, 12 mass)",            12, 36),
    ("beam4-broad",   "Beam class 4  (broadside, 12 mass)",         12, 36),
    # ── Grasers ───────────────────────────────────────────────────────────────
    ("graser1-1arc",  "Graser class 1  (1 arc, 2 mass)",             2,  8),
    ("graser1-3arc",  "Graser class 1  (3 arcs, 3 mass)",            3, 12),
    ("graser1-broad", "Graser class 1  (broadside / 6-arc, 4 mass)", 4, 16),
    ("graser2-1arc",  "Graser class 2  (1 arc, 9 mass)",             9, 36),
    ("graser2-2arc",  "Graser class 2  (2 arcs, 12 mass)",          12, 48),
    ("graser2-3arc",  "Graser class 2  (3 arcs, 15 mass)",          15, 60),
    ("graser2-broad", "Graser class 2  (broadside, 15 mass)",       15, 60),
    ("graser3-1arc",  "Graser class 3  (1 arc, 24 mass)",           24, 96),
    ("graser3-3arc",  "Graser class 3  (3 arcs, 36 mass)",          36,144),
    ("graser3-broad", "Graser class 3  (broadside, 36 mass)",       36,144),
    # ── Torpedoes ─────────────────────────────────────────────────────────────
    ("torp1-1arc",    "Torpedo class 1  (1 arc, 4 mass)",            4, 12),
    ("torp1-2arc",    "Torpedo class 1  (2 arcs, 5 mass)",           5, 15),
    ("torp1-3arc",    "Torpedo class 1  (3 arcs, 6 mass)",           6, 18),
    ("torp1-broad",   "Torpedo class 1  (broadside, 6 mass)",        6, 18),
    ("torp2-1arc",    "Torpedo class 2  (1 arc, 8 mass)",            8, 24),
    ("torp2-2arc",    "Torpedo class 2  (2 arcs, 10 mass)",         10, 30),
    ("torp2-3arc",    "Torpedo class 2  (3 arcs, 12 mass)",         12, 36),
    ("torp2-broad",   "Torpedo class 2  (broadside, 12 mass)",      12, 36),
    ("torp3-1arc",    "Torpedo class 3  (1 arc, 16 mass)",          16, 48),
    ("torp3-3arc",    "Torpedo class 3  (3 arcs, 24 mass)",         24, 72),
    ("torp3-broad",   "Torpedo class 3  (broadside, 24 mass)",      24, 72),
    ("torp4-1arc",    "Torpedo class 4  (1 arc, 32 mass)",          32, 96),
    # ── Point defence & special weapons ───────────────────────────────────────
    ("pds",           "Point defence system (PDS)  (1 mass / 3 pts)", 1, 3),
    ("scattergun",    "Scattergun  (1 mass / 4 pts)",                1,  4),
    ("needle",        "Needle weapon  (2 mass / 6 pts)",             2,  6),
    ("submunition",   "Submunition pack  (1 mass / 3 pts)",          1,  3),
    # ── Missiles ──────────────────────────────────────────────────────────────
    ("sml",           "Salvo missile launcher — SML  (3 mass / 9 pts)", 3, 9),
    ("sml-mag",       "SML magazine — 1 standard salvo  (2 mass)",    2,  6),
    ("sml-mag-er",    "SML magazine — 1 ER salvo  (3 mass)",          3,  9),
    ("smr",           "Salvo missile rack — SMR  (4 mass / 12 pts)",  4, 12),
    ("smr-er",        "SMR extended range  (5 mass / 15 pts)",        5, 15),
    ("heavy-miss",    "Heavy missile  (2 mass / 6 pts)",              2,  6),
    ("heavy-miss-er", "Heavy missile ER  (3 mass / 9 pts)",           3,  9),
    # ── Defensive systems ─────────────────────────────────────────────────────
    ("ecm",           "ECM system  (4 mass / 16 pts)",               4, 16),
    ("ecm-area",      "Area effect ECM  (6 mass / 24 pts)",          6, 24),
    # ── Optional systems ──────────────────────────────────────────────────────
    ("sensors-enh",   "Enhanced sensors  (2 mass / 8 pts)",          2,  8),
    ("sensors-sup",   "Superior sensors  (4 mass / 16 pts)",         4, 16),
    ("ortillery",     "Ortillery system  (3 mass / 9 pts)",          3,  9),
    ("minelayer",     "Minelayer  (2 mass + 1 per mine)",            2,  6),
    ("mine",          "Mine capacity (+1 per mine)  (1 mass / 2 pts)",1, 2),
    ("minesweeper",   "Minesweeper  (5 mass / 15 pts)",              5, 15),
    ("marines",       "Marines  (negligible mass)",                   0,  0),
    ("dmg-ctrl",      "Damage control party  (negligible mass)",      0,  0),
    ("weasel-cr",     "Weasel cruiser emitter  (2 mass / 8 pts)",    2,  8),
    ("weasel-cap",    "Weasel capital emitter  (4 mass / 16 pts)",   4, 16),
    # ── Fighter hangars ───────────────────────────────────────────────────────
    ("hangar-std",    "Fighter hangar  (6 fighters, 9 mass / 27 pts)", 9, 27),
    ("ftr-std",       "Fighter group — standard  (6×, 0 mass / 18 pts)", 0, 18),
    ("ftr-fast",      "Fighter group — fast  (6×, 0 mass / 24 pts)",    0, 24),
    ("ftr-heavy",     "Fighter group — heavy  (6×, 0 mass / 30 pts)",   0, 30),
    ("ftr-intercept", "Fighter group — interceptor  (6×, 0 mass / 18 pts)", 0, 18),
    ("ftr-attack",    "Fighter group — attack  (6×, 0 mass / 24 pts)",  0, 24),
    ("ftr-lr",        "Fighter group — long range  (6×, 0 mass / 24 pts)", 0, 24),
    ("ftr-torpedo",   "Fighter group — torpedo  (6×, 0 mass / 36 pts)", 0, 36),
]


def shared_entry(key: str, name: str, mass: int, pts: int) -> str:
    eid = fid("shared", key)
    return (f'<selectionEntry id="{eid}" name="{name}" '
            f'hidden="false" collective="false" import="true" type="upgrade">'
            f'{costs(pts, mass)}'
            f'</selectionEntry>')


def links_xml(M: int, shared_ids: dict) -> str:
    parts = []
    for key, sid in shared_ids.items():
        lid = fid("link", M, key)
        parts.append(
            f'<selectionEntryLink id="{lid}" targetId="{sid}" '
            f'hidden="false" collective="false" import="true"/>'
        )
    return "\n      ".join(parts)


# ─── Full ship entry ──────────────────────────────────────────────────────────

def ship_entry(M: int, shared_ids: dict) -> str:
    label = ship_class_label(M)
    sid = fid("ship", M)

    groups = "\n        ".join([
        hull_group(M),
        drive_group(M),
        ftl_group(M),
        screen_group(M),
        armour_group(M),
        stream_group(M),
    ])

    lxml = links_xml(M, shared_ids)

    return f"""\
  <selectionEntry id="{sid}" name="Custom ship  [Mass {M:3d}]  {label}"
                  hidden="false" collective="false" import="true" type="unit">
    {costs(M, 0)}
    <constraints>
      <constraint id="{fid('con','masscap',M)}" type="max" value="{M}"
                  field="Mass" scope="self" shared="false" includeChildSelections="true"/>
    </constraints>
    <categoryLinks>
      <categoryLink id="{fid('cl','ship',M)}" name="Ship" hidden="false"
                    targetId="{SHIP_CAT}" primary="true"/>
    </categoryLinks>
    <selectionEntryGroups>
        {groups}
    </selectionEntryGroups>
    <selectionEntryLinks>
      {lxml}
    </selectionEntryLinks>
  </selectionEntry>"""


# ─── Main ─────────────────────────────────────────────────────────────────────

def generate() -> str:
    shared_ids = {key: fid("shared", key) for key, *_ in SYSTEMS}

    shared_xml  = "\n  ".join(shared_entry(k, n, m, p) for k, n, m, p in SYSTEMS)
    ships_xml   = "\n\n".join(ship_entry(M, shared_ids) for M in MASSES)

    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<catalogue id="{CAT_ID}" name="FTCD Ship Designer"
           revision="2" battleScribeVersion="2.03"
           gameSystemId="{GS_ID}" gameSystemRevision="1"
           xmlns="http://www.battlescribe.net/schema/catalogueSchema">

  <!--
    FTCD Ship Designer  —  free ship builder for Full Thrust: Cross Dimensions
    Generated by scripts/gen_custom_ship.py  (rulebook rev 1.2, §11.4–11.6)

    All 152 valid FTCD ship masses (4-10 any integer, 12-300 even) are provided.
    Hull-integrity, drive-mass and screen-mass are pre-calculated per ship so
    New Recruit tracks "Mass used / Mass total" and CPV automatically.

    Workflow (mirrors Perlkonig ftShipBuilder):
      1. Add "Custom ship [Mass X]" — pick the mass that matches your design goal.
         New Recruit's search box lets you type e.g. "Mass 64".
      2. Under the ship select:
           Hull integrity  — fragile (10 %) … super (50 %)
           Main drive      — thrust 0–8, standard or advanced
           FTL drive       — standard or advanced (optional)
           Defensive screen — level 1/2, standard or advanced (optional)
           Armour          — add individual boxes (up to 20, optional)
           Streamlining    — partial or full (optional)
      3. Add weapons / systems from the shared list (beams, grasers,
         torpedoes, missiles, PDS, ECM, sensors, fighters …)
      4. Watch the mass budget shrink and CPV grow in real time.

    NOTE  The catalogue is linked from all faction catalogues via
          catalogueLinks (importRootEntries=true), so custom ships appear
          alongside faction ships in every faction roster.
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
    out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "custom.cat"))
    xml = generate()
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    n_ships   = xml.count('type="unit"')
    n_entries = xml.count("<selectionEntry ")
    print(f"Generated {out}")
    print(f"  {len(MASSES)} ship masses  |  {n_ships} ship entries  |  {n_entries} total selectionEntries")
    print(f"  File size: {len(xml.encode()):,} bytes")
