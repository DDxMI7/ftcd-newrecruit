#!/usr/bin/env python3
"""
Generates nsl.cat — Neu Swabian League (NSL) faction catalogue for FTCD.

Ships sourced from Perlkonig's ftShipBuilder NSL preset (index 1 in presets.json).
System costs computed per FTCD rulebook §11 formulas. Arc labels derived from
Perlkonig's (leftArc, numArcs) fields.

Usage:  python3 scripts/gen_nsl.py
Output: nsl.cat
"""
import json, math, hashlib
from pathlib import Path

REPO    = Path(__file__).parent.parent
PRESETS = REPO / "data/raw/ftShipBuilder-main/src/stores/presets.json"
OUT     = REPO / "nsl.cat"

# ─── IDs — matching nac.cat (known-good) ─────────────────────────────────────
GS_ID     = "ftcd-0001-gs01"
CAT_ID    = "nsl-cat-0001"
PUB_ID    = "3900-a3b1-799d"
PTS_ID    = "7d62-4668-5257"
MASS_ID   = "4771-3924-56de"
CAT_SHIP  = "876f-9a8d-ca03"
CAT_DRIVE = "3fe9-8946-3e85"
CAT_FC    = "961b-8d52-88f1"
CAT_WPN   = "163f-ce9f-f57f"
PT_SHIP   = "347a-bc89-60a9"
PT_WPN    = "e5fe-386e-cbe0"
CH_THRUST = "1045-6c03-1199"
CH_HULL   = "2ff8-07a0-ca6e"
CH_FC_N   = "771f-37f8-a88b"
CH_SCR    = "d6cb-8b81-48f6"
CH_CLS    = "8e6f-96da-1dac"
CH_RNG    = "51be-ce4a-2bbd"
CH_DICE   = "d860-b2b9-437a"
CH_ARCS   = "8e45-571a-a876"
CUSTOM_ID = "51af-a23a-9d57"   # custom.cat (ship designer)

NSL_FLEET_INDEX = 1


# ─── FTCD physics ─────────────────────────────────────────────────────────────
def drive_mass(total: int, thrust: int) -> int:
    return 0 if thrust == 0 else max(1, round(total * 0.05 * thrust))

def ftl_mass(total: int) -> int:
    return max(1, round(total * 0.1))

def armour_count(armour_data: list) -> int:
    return sum(v for layer in armour_data for v in layer)


# ─── System costs ─────────────────────────────────────────────────────────────
def beam_stats(class_n: int, num_arcs: int) -> tuple:
    """Returns (mass, pts, dice_str, range_mu)."""
    rng  = 12 * class_n
    dice = f"{class_n}d6"
    if class_n == 1:
        return 1, 3, dice, rng
    if class_n == 2:
        return (3, 9, dice, rng) if num_arcs >= 6 else (2, 6, dice, rng)
    if class_n == 3:
        return (6, 18, dice, rng)   # any arc configuration
    if class_n == 4:
        return (8, 24, dice, rng) if num_arcs == 1 else (12, 36, dice, rng)
    return 1, 3, dice, rng


# ─── Arc label ────────────────────────────────────────────────────────────────
_ARC_ORDER = ["F", "FP", "P", "AP", "A", "AS", "S", "FS"]

def arc_label(left_arc: str, num_arcs: int) -> str:
    if num_arcs >= 6:
        return "All"
    try:
        i = _ARC_ORDER.index(left_arc)
    except ValueError:
        return f"{left_arc}+{num_arcs}"
    return "/".join(_ARC_ORDER[(i + j) % len(_ARC_ORDER)] for j in range(num_arcs))


# ─── Deterministic ID ─────────────────────────────────────────────────────────
def fid(*parts) -> str:
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:12]
    return f"{h[:4]}-{h[4:8]}-{h[8:]}"


# ─── XML helpers ──────────────────────────────────────────────────────────────
def costs_xml(pts: int, mass: int) -> str:
    return (f'<costs>'
            f'<cost name="pts" typeId="{PTS_ID}" value="{pts}"/>'
            f'<cost name="Mass" typeId="{MASS_ID}" value="{mass}"/>'
            f'</costs>')


def mandatory_entry(eid: str, name: str, pts: int, mass: int,
                    cat_id: str = "", profile: str = "") -> str:
    cat_xml = (f'<categoryLinks>'
               f'<categoryLink id="{fid(eid,"cl")}" name="" hidden="false" '
               f'targetId="{cat_id}" primary="true"/>'
               f'</categoryLinks>') if cat_id else ""
    return (
        f'        <selectionEntry id="{eid}" name="{name}" type="upgrade"\n'
        f'                        hidden="false" collective="false" import="true">\n'
        f'          <constraints>\n'
        f'            <constraint id="{fid(eid,"min")}" type="min" value="1"'
        f' field="selections" scope="parent" shared="false"/>\n'
        f'            <constraint id="{fid(eid,"max")}" type="max" value="1"'
        f' field="selections" scope="parent" shared="false"/>\n'
        f'          </constraints>\n'
        f'          {profile}\n'
        f'          {costs_xml(pts, mass)}\n'
        f'          {cat_xml}\n'
        f'        </selectionEntry>'
    )


def weapon_profile(eid: str, w_name: str, class_n: int,
                   range_mu: int, dice: str, arcs: str) -> str:
    return (
        f'<profiles><profile id="{fid(eid,"prof")}" name="{w_name}" '
        f'publicationId="{PUB_ID}" profileTypeId="{PT_WPN}" '
        f'typeId="{PT_WPN}" typeName="Weapon">'
        f'<characteristics>'
        f'<characteristic name="Class" typeId="{CH_CLS}">{class_n}</characteristic>'
        f'<characteristic name="Max Range (MU)" typeId="{CH_RNG}">{range_mu}</characteristic>'
        f'<characteristic name="Damage Dice" typeId="{CH_DICE}">{dice}</characteristic>'
        f'<characteristic name="Fire Arcs" typeId="{CH_ARCS}">{arcs}</characteristic>'
        f'</characteristics></profile></profiles>'
    )


# ─── Ship builder ─────────────────────────────────────────────────────────────
def build_ship_entry(ship: dict) -> str:
    name       = ship["name"]
    total_mass = ship["mass"]
    hull_pts   = ship["hull"]["points"]
    thrust     = next((s["thrust"] for s in ship["systems"] if s["name"] == "drive"), 0)
    has_ftl    = any(s["name"] == "ftl"         for s in ship["systems"])
    has_adfc   = any(s["name"] == "adfc"        for s in ship["systems"])
    n_fc       = sum(1 for s in ship["systems"] if s["name"] == "fireControl")
    hangars    = [s for s in ship["systems"] if s["name"] == "hangar"]
    magazines  = [s for s in ship["systems"] if s["name"] == "magazine"]
    n_pds      = sum(1 for w in ship["weapons"]  if w["name"] == "pds")
    beams      = [w for w in ship["weapons"]  if w["name"] == "beam"]
    sl_list    = [o for o in ship["ordnance"] if o["name"] == "salvoLauncher"]
    torp_pulse = [w for w in ship["weapons"]  if w["name"] == "torpedoPulse"]
    n_fighters = len(ship["fighters"])
    armour_n   = armour_count(ship["armour"])
    screens    = 0   # NSL ships use no screens in Perlkonig designs

    ship_class = ship["class"]
    entry_name = f"{name} ({ship_class}, Mass {total_mass})"
    sid  = fid("nsl", name)
    entries = []

    # ── Main drive ────────────────────────────────────────────────────────────
    dm = drive_mass(total_mass, thrust)
    entries.append(mandatory_entry(
        fid("nsl", name, "drive"),
        f"Main Drive (Thrust {thrust})",
        dm * 2, dm, CAT_DRIVE,
    ))

    # ── FTL drive ─────────────────────────────────────────────────────────────
    if has_ftl:
        fm = ftl_mass(total_mass)
        entries.append(mandatory_entry(
            fid("nsl", name, "ftl"),
            "FTL Drive",
            fm * 2, fm, CAT_DRIVE,
        ))

    # ── ADFC ──────────────────────────────────────────────────────────────────
    if has_adfc:
        entries.append(mandatory_entry(
            fid("nsl", name, "adfc"),
            "Area Defence Fire Control (ADFC)",
            8, 2, CAT_FC,
        ))

    # ── Fire Control(s) ───────────────────────────────────────────────────────
    for i in range(n_fc):
        entries.append(mandatory_entry(
            fid("nsl", name, "fc", i),
            f"Fire Control ({i+1}/{n_fc})",
            4, 1, CAT_FC,
        ))

    # ── Armour ────────────────────────────────────────────────────────────────
    if armour_n > 0:
        entries.append(mandatory_entry(
            fid("nsl", name, "armour"),
            f"Armour ({armour_n} boxes)",
            armour_n * 2, armour_n,
        ))

    # ── Hangars ───────────────────────────────────────────────────────────────
    for i, _ in enumerate(hangars):
        entries.append(mandatory_entry(
            fid("nsl", name, "hangar", i),
            f"Fighter Hangar ({i+1}/{len(hangars)})",
            27, 9,
        ))

    # ── Magazines ─────────────────────────────────────────────────────────────
    for mag in magazines:
        cap = mag.get("capacity", 1)
        entries.append(mandatory_entry(
            fid("nsl", name, "mag", mag["id"]),
            f"SML Magazine ({cap} salvos)",
            cap * 6, cap * 2,
        ))

    # ── PDS ───────────────────────────────────────────────────────────────────
    for i in range(n_pds):
        entries.append(mandatory_entry(
            fid("nsl", name, "pds", i),
            f"Point Defence System ({i+1}/{n_pds})",
            3, 1, CAT_WPN,
        ))

    # ── Beam batteries ────────────────────────────────────────────────────────
    for idx, w in enumerate(beams):
        cls       = w["class"]
        num_arcs  = w.get("numArcs", 3)
        left_arc  = w.get("leftArc", "F")
        arcs_lbl  = arc_label(left_arc, num_arcs)
        b_mass, b_pts, b_dice, b_rng = beam_stats(cls, num_arcs)
        w_name  = f"Beam Battery Class {cls} ({arcs_lbl})"
        eid     = fid("nsl", name, "beam", idx)
        profile = weapon_profile(eid, w_name, cls, b_rng, b_dice, arcs_lbl)
        entries.append(mandatory_entry(eid, w_name, b_pts, b_mass, CAT_WPN, profile))

    # ── Salvo Launchers ───────────────────────────────────────────────────────
    for idx, sl in enumerate(sl_list):
        num_arcs = sl.get("numArcs", 3)
        left_arc = sl.get("leftArc", "F")
        arcs_lbl = arc_label(left_arc, num_arcs)
        eid      = fid("nsl", name, "sml", idx)
        entries.append(mandatory_entry(
            eid,
            f"Salvo Missile Launcher ({arcs_lbl})",
            9, 3, CAT_WPN,
        ))

    # ── Torpedo pulse → Torpedo class 1 ──────────────────────────────────────
    for idx, tp in enumerate(torp_pulse):
        num_arcs = tp.get("numArcs", 3)
        left_arc = tp.get("leftArc", "F")
        arcs_lbl = arc_label(left_arc, num_arcs)
        eid      = fid("nsl", name, "torp", idx)
        entries.append(mandatory_entry(
            eid,
            f"Torpedo Class 1 ({arcs_lbl})",
            18, 6, CAT_WPN,
        ))

    # ── Fighter groups ────────────────────────────────────────────────────────
    for i in range(n_fighters):
        entries.append(mandatory_entry(
            fid("nsl", name, "ftr", i),
            f"Fighter Group — Standard ({i+1}/{n_fighters})",
            18, 0,
        ))

    entries_xml = "\n".join(entries)

    return (
        f'  <selectionEntry id="{sid}" name="{entry_name}"\n'
        f'                  hidden="false" collective="false" import="true" type="unit">\n'
        f'    <profiles>\n'
        f'      <profile id="{fid(sid,"prof")}" name="{name}" publicationId="{PUB_ID}"\n'
        f'               profileTypeId="{PT_SHIP}" typeId="{PT_SHIP}" typeName="Ship Stats">\n'
        f'        <characteristics>\n'
        f'          <characteristic name="Thrust" typeId="{CH_THRUST}">{thrust}</characteristic>\n'
        f'          <characteristic name="Hull Points" typeId="{CH_HULL}">{hull_pts}</characteristic>\n'
        f'          <characteristic name="Firecons" typeId="{CH_FC_N}">{n_fc}</characteristic>\n'
        f'          <characteristic name="Screens" typeId="{CH_SCR}">{screens}</characteristic>\n'
        f'        </characteristics>\n'
        f'      </profile>\n'
        f'    </profiles>\n'
        f'    {costs_xml(0, 0)}\n'
        f'    <constraints>\n'
        f'      <constraint id="{fid(sid,"con")}" type="max" value="{total_mass}"\n'
        f'                  field="Mass" scope="self" shared="false" includeChildSelections="true"/>\n'
        f'    </constraints>\n'
        f'    <categoryLinks>\n'
        f'      <categoryLink id="{fid(sid,"cl")}" name="Ship" hidden="false"\n'
        f'                    targetId="{CAT_SHIP}" primary="true"/>\n'
        f'    </categoryLinks>\n'
        f'    <selectionEntries>\n'
        f'{entries_xml}\n'
        f'    </selectionEntries>\n'
        f'  </selectionEntry>'
    )


# ─── Main ─────────────────────────────────────────────────────────────────────
def generate() -> str:
    data  = json.loads(PRESETS.read_text(encoding="utf-8"))
    fleet = data[NSL_FLEET_INDEX]
    ships = fleet["ships"]

    ships_xml = "\n\n".join(build_ship_entry(s) for s in ships)

    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<catalogue id="{CAT_ID}" name="Neu Swabian League (NSL)"
           revision="1" battleScribeVersion="2.03"
           gameSystemId="{GS_ID}" gameSystemRevision="1"
           authorName="" authorContact="" authorUrl=""
           xmlns="http://www.battlescribe.net/schema/catalogueSchema">

  <readme>Neu Swabian League (NSL) Kriegsraumflotte for Full Thrust Cross Dimensions.
Ships match Perlkonig's ftShipBuilder NSL presets. Generated by scripts/gen_nsl.py.</readme>

  <publications>
    <publication id="{PUB_ID}" name="Full Thrust Cross Dimensions"
                 shortName="FTCD" publisher="Ground Zero Games"
                 publicationDate="2010" publisherUrl="http://groundzerogames.net"/>
  </publications>

  <catalogueLinks>
    <catalogueLink id="nsl-link-custom-0001" targetId="{CUSTOM_ID}"
                   name="FTCD Ship Designer" type="catalogue" importRootEntries="true"/>
  </catalogueLinks>

  <selectionEntries>
{ships_xml}
  </selectionEntries>

</catalogue>
"""


if __name__ == "__main__":
    xml = generate()
    OUT.write_text(xml, encoding="utf-8")
    n_ships = xml.count('type="unit"')
    print(f"Generated {OUT}")
    print(f"  {n_ships} ship entries")
    print(f"  File size: {len(xml.encode()):,} bytes")
