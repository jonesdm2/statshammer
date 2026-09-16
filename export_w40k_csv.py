"""Export the 40K 11th unit data (BSData extract) to data/w40k-units.csv.

One row per weapon, editable columns only; all probabilities, D100 and E100 are worked out by the page.
The maths reads the Default weapons (the unit's default loadout). Option rows (other wargear the unit can take) and
Mode rows (the other firing modes of a default weapon) are there for the Unit Card.
To keep the file small enough to edit on github.com, a unit's columns (shared_with, points ... model_groups, and the
Unit Card's Ld ... faction_keywords) are written on its first row only; every other row carries just the unit's
name, faction and id. The page reads each unit column from the first row that has it.

  python export_w40k_csv.py <units_*.json> <cards_*.json> <data/w40k-units.csv>
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 4 or not sys.argv[3].endswith(".csv"):
    sys.exit("usage: python export_w40k_csv.py <units_*.json> <cards_*.json> <data/w40k-units.csv>")
src, cards_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
rows = json.load(open(src, encoding="utf-8"))
cards = json.load(open(cards_path, encoding="utf-8"))

sys.path.insert(0, r"C:\Users\David Mazzocchi-Jone\Desktop\Statshammer\_channel\tools\unitmetrics")
from data_w40k import parse_weapon  # noqa: E402

# Same filter as build_w40k.py: a unit needs weapons, points, wounds and toughness; Apocalypse-scale models
# (over 1000 pts) distort a matched-play reference.
rows = [r for r in rows if r["weapons"] and r["points"] > 0 and r["wounds"] > 0 and r["toughness"] > 0
        and r["points"] <= 1000]

COLUMNS = ["unit_name", "faction", "shared_with", "id", "points", "models", "T", "W", "Sv", "InSv", "FNP", "OC",
           "move", "keywords", "model_groups", "weapon_name", "weapon_type", "attacks", "skill", "S", "AP",
           "damage", "weapon_models", "abilities", "notes",
           # Unit Card columns
           "Ld", "unit_size", "points_by_size", "composition", "profiles", "rules", "datasheet_abilities",
           "wargear_abilities", "faction_keywords", "rules_refs", "loadout", "range", "weapon_keywords"]
CARD_UNIT = COLUMNS[25:35]

entries = {}
factions = collections.defaultdict(set)
for r in rows:
    entries.setdefault(r["id"], []).append(r)
    factions[r["faction"]].add(r["id"])
faction_size = {f: len(ids) for f, ids in factions.items()}

# A unit several factions can take is listed under the faction its own FACTION keyword names (a Space Marine unit
# under Space Marines, not under whichever chapter comes first); otherwise under the largest of them.
FACTION_HOME = {
    "FACTION: ADEPTUS ASTARTES": "Imperium - Adeptus Astartes - Space Marines",
    "FACTION: ASTRA MILITARUM": "Imperium - Astra Militarum",
    "FACTION: HERETIC ASTARTES": "Chaos - Chaos Space Marines",
    "FACTION: TYRANIDS": "Xenos - Tyranids",
    "FACTION: HARLEQUINS": "Xenos - Aeldari",
    "FACTION: ASURYANI": "Xenos - Aeldari",
    "FACTION: ADEPTUS MECHANICUS": "Imperium - Adeptus Mechanicus",
}


def home_faction(es, facs):
    for k in es[0]["keywords"]:
        if FACTION_HOME.get(k) in facs:
            return FACTION_HOME[k]
    return max(facs, key=lambda f: faction_size[f])


def needs_groups(r) -> bool:
    """The model groups only change the maths when the models differ, or a CHARACTER soaks wounds last."""
    gs = r.get("model_groups") or []
    distinct = {(g["W"], g["Sv"], g["InSv"]) for g in gs}
    return len(gs) > 1 and (len(distinct) > 1 or any(g["character"] for g in gs))


def group_text(r) -> str:
    return " | ".join(f"{g['count']}x T{g['T']} W{g['W']} Sv{g['Sv']}+"
                      + (f" Inv{g['InSv']}+" if g["InSv"] else "") + (" char" if g["character"] else "")
                      for g in r["model_groups"])


def abilities(w) -> str:
    out = []
    if w["lethal"]:
        out.append("Lethal Hits")
    if w["sustained"]:
        out.append(f"Sustained Hits {w['sustained']}")
    if w["devastating"]:
        out.append("Devastating Wounds")
    if w["twin_linked"]:
        out.append("Twin-linked")
    if w["torrent"]:
        out.append("Torrent")
    if w["blast"]:
        out.append("Blast")
    if w["melta"]:
        out.append(f"Melta {w['melta']}")
    if w["rapid_fire"]:
        out.append(f"Rapid Fire {w['rapid_fire']}")
    if w["heavy"]:
        out.append("Heavy")
    if w["lance"]:
        out.append("Lance")
    if w["ignores_cover"]:
        out.append("Ignores Cover")
    for k, v in sorted(w["anti"].items()):
        out.append(f"Anti-{k.title()} {v}+")
    return ", ".join(out)


def span(lo, hi):
    return str(lo) if hi is None or lo == hi else f"{lo}-{hi}"


def card_columns(card):
    if not card:
        return {}
    profiles = card["profiles"]

    def line(s):
        inv = s["InSv"] if s["InSv"] and s["InSv"] != "-" else ""
        return f"M{s['M']} T{s['T']} Sv{s['Sv']} W{s['W']} Ld{s['LD']} OC{s['OC']}" + (f" Inv{inv}" if inv else "")
    return {
        "Ld": re.sub(r"\D", "", profiles[0]["stats"]["LD"]) if profiles else "",
        "unit_size": span(*card["size"]),
        "points_by_size": "; ".join(f"{n}+ models: {p}" for n, p in card["points_by_size"]),
        "composition": "; ".join(f"{span(m['min'], m['max'])} {m['name']}" for p in profiles for m in p["models"]),
        "profiles": " | ".join(f"{' / '.join(m['name'] for m in p['models'])}: {line(p['stats'])}" for p in profiles)
        if len(profiles) > 1 else "",
        "rules": ", ".join(card["rules"]), "datasheet_abilities": ", ".join(card["abilities"]),
        "wargear_abilities": ", ".join(card["wargear_abilities"]), "faction_keywords": ", ".join(card["faction_keywords"]),
        # where each ability's wording lives in BSData (file#id); the Unit Card fetches the text from there
        "rules_refs": " | ".join(f"{n}={f}#{i}" for n, (f, i) in card.get("refs", {}).items()),
    }


def mode_base(name):
    if not name.startswith("➤"):
        return None
    return re.sub(r"\s+-\s+[^-]+$", "", name.lstrip("➤").strip()).lower()


n_units = n_rows = n_options = 0
order = sorted(entries.items(), key=lambda kv: (home_faction(kv[1], sorted({e["faction"] for e in kv[1]})), kv[1][0]["unit"]))
with open(out, "w", encoding="utf-8", newline="") as fh:
    wtr = csv.writer(fh, lineterminator="\n")
    wtr.writerow(COLUMNS)
    for _id, es in order:
        facs = sorted({e["faction"] for e in es})
        home = home_faction(es, facs)
        r = next(e for e in es if e["faction"] == home)
        card = cards.get(_id)
        n_units += 1
        keywords = ", ".join(card["keywords"]) if card else ", ".join(k for k in r["keywords"] if not k.startswith("FACTION:"))
        unit_cols = [r["unit"], home, ", ".join(f for f in facs if f != home), r["id"], r["points"], r["models"],
                     r["toughness"], r["wounds"], r["save"], r["invuln"] or "", r["fnp"] or "", r["oc"], r["move"],
                     keywords, group_text(r) if needs_groups(r) else ""]
        cc = card_columns(card)
        tail_unit = [cc.get(k, "") for k in CARD_UNIT]
        card_weapons = card["weapons"] if card else []
        by_name = {}
        for cw in card_weapons:
            by_name.setdefault(cw["name"].lower(), cw)
        default_names = {w["name"].lower() for w in r["weapons"]}
        default_bases = {mode_base(w["name"]) for w in r["weapons"]} - {None}
        short_cols = [r["unit"], home, "", r["id"]] + [""] * (len(unit_cols) - 4)
        for i, w in enumerate(r["weapons"]):
            cw = by_name.get(w["name"].lower(), {})
            wtr.writerow((unit_cols if i == 0 else short_cols) + [w["name"], "Ranged" if w["ranged"] else "Melee", w["attacks"], w["skill"],
                                      w["strength"], w["ap"], w["damage"], w["models"], abilities(w),
                                      "; ".join(w["conditional"])]
                         + (tail_unit if i == 0 else [""] * len(tail_unit)) + ["Default", cw.get("Range", ""), cw.get("Keywords", "")])
            n_rows += 1
        seen = set()
        for cw in card_weapons:
            nm = cw["name"].lower()
            if nm in default_names or nm in seen:
                continue
            seen.add(nm)
            kind = "Mode" if mode_base(cw["name"]) in default_bases else "Option"
            ranged = cw["type"] == "Ranged"
            fake = {"typeName": "Ranged Weapons" if ranged else "Melee Weapons", "name": cw["name"],
                    "characteristics": [{"name": k, "$text": v} for k, v in cw.items() if k not in ("name", "type")]}
            pw, _ = parse_weapon(fake, 1)
            skill = cw.get("BS" if ranged else "WS", "")
            wtr.writerow(short_cols + [cw["name"], cw["type"], cw.get("A", ""),
                                      re.sub(r"\D", "", skill) if re.search(r"\d", skill) else "",
                                      cw.get("S", ""), cw.get("AP", ""), cw.get("D", ""), "",
                                      abilities(pw) if pw else "", "; ".join(pw["conditional"]) if pw else ""]
                         + [""] * len(tail_unit) + [kind, cw.get("Range", ""), cw.get("Keywords", "")])
            n_rows += 1
            n_options += 1
print(f"wrote {n_units} units, {n_rows} weapon rows ({n_options} options and firing modes) to {out} "
      f"({out.stat().st_size:,} bytes)")
