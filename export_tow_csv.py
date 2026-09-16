"""Export the Old World unit data (Old World Builder + Online Rules Index join) to data/tow-units.csv.

One row per unit, editable columns only; all probabilities, CE100, Wounds100 and E100 are worked out by the page.

  python export_tow_csv.py <units_*.json> <data/tow-units.csv>
"""
import csv
import json
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = json.load(open(src, encoding="utf-8"))

ARMY_NAMES = {
    "beastmen-brayherds": "Beastmen Brayherds", "chaos-dwarfs": "Chaos Dwarfs", "daemons-of-chaos": "Daemons of Chaos",
    "dark-elves": "Dark Elves", "dwarfen-mountain-holds": "Dwarfen Mountain Holds", "empire-of-man": "Empire of Man",
    "grand-cathay": "Grand Cathay", "high-elf-realms": "High Elf Realms", "kingdom-of-bretonnia": "Kingdom of Bretonnia",
    "lizardmen": "Lizardmen", "ogre-kingdoms": "Ogre Kingdoms", "orc-and-goblin-tribes": "Orc & Goblin Tribes",
    "renegade-crowns": "Renegade Crowns", "skaven": "Skaven", "tomb-kings-of-khemri": "Tomb Kings of Khemri",
    "vampire-counts": "Vampire Counts", "warriors-of-chaos": "Warriors of Chaos", "wood-elf-realms": "Wood Elf Realms",
}
COLUMNS = ["id", "unit_name", "army", "category", "troop_type", "points", "points_per_model", "min_models",
           "M", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "armour", "shield", "ward", "regeneration",
           "weapon", "weapon_S", "weapon_AP", "weapon_rules", "armour_bane", "cleaving_blow", "poisoned",
           "requires_two_hands", "fight_in_extra_rank", "extra_attacks", "horde", "stubborn", "unbreakable",
           "unstable", "indomitable", "hatred", "frenzy", "named", "mounts", "special_rules"]


def cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else ""
    return str(v)


def strength(s):
    kind, val = s or ["mod", 0]
    if kind == "abs":
        return str(val)
    return "S" if not val else (f"S+{val}" if val > 0 else f"S{val}")


def mounts(ms):
    return " | ".join(f"WS{m.get('WS', '')} S{m.get('S', '')} I{m.get('I', '')} A{m.get('A', '')}" for m in ms or [])


with open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        weapon = r.get("weapon") or {}
        w.writerow([cell(x) for x in [
            r["index_slug"], r["unit"], ARMY_NAMES.get(r["army"], r["army"]), r.get("category"), r.get("troop_type"),
            r.get("points"), r.get("points_per_model"), r.get("min_models"),
            r.get("m"), r.get("ws"), r.get("bs"), r.get("s"), r.get("t"), r.get("w"), r.get("i"), r.get("a"), r.get("ld"),
            None if (r.get("armour") or 7) >= 7 else r.get("armour"), r.get("shield"), r.get("ward"), r.get("regen"),
            weapon.get("name"), strength(weapon.get("s")), weapon.get("ap") or 0,
            ", ".join(x for x in weapon.get("rules") or [] if x and x != "-"),
            r.get("armour_bane") or None, r.get("cleaving_blow"), r.get("poisoned"), r.get("requires_two_hands"),
            r.get("fight_in_extra_rank"), r.get("extra_attacks") or None, r.get("horde"), r.get("stubborn"),
            r.get("unbreakable"), r.get("unstable"), r.get("indomitable") or None, r.get("hatred"), r.get("frenzy"),
            r.get("named"), mounts(r.get("mount")), r.get("special_rules"),
        ]])
print(f"wrote {len(rows)} units, {len(COLUMNS)} columns to {out}")
