"""Export the 40K 11th unit data (BSData extract) to data/w40k-units.csv.

One row per weapon, editable columns only; all probabilities, D100 and E100 are worked out by the page.

  python export_w40k_csv.py <units_*.json> <data/w40k-units.csv>
"""
import collections
import csv
import json
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = json.load(open(src, encoding="utf-8"))

# Same filter as build_w40k.py: a unit needs weapons, points, wounds and toughness; Apocalypse-scale models
# (over 1000 pts) distort a matched-play reference.
rows = [r for r in rows if r["weapons"] and r["points"] > 0 and r["wounds"] > 0 and r["toughness"] > 0
        and r["points"] <= 1000]

# Keywords the maths uses: every keyword named by an Anti-X rule anywhere in the game, plus the ones the page
# shows on a unit card.
KEEP = {"INFANTRY", "FLY", "VEHICLE", "MONSTER", "PSYKER", "CHARACTER", "CHAOS", "TITANIC", "WALKER", "DAEMON",
        "MOUNTED", "SWARM", "BEAST", "BATTLELINE", "EPIC HERO", "TRANSPORT", "AIRCRAFT"}
COLUMNS = ["unit_name", "faction", "shared_with", "id", "points", "models", "T", "W", "Sv", "InSv", "FNP", "OC",
           "move", "keywords", "model_groups", "weapon_name", "weapon_type", "attacks", "skill", "S", "AP",
           "damage", "weapon_models", "abilities", "notes"]

# One entry per unit; a unit several factions can take is listed once, with the others in shared_with.
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


n_units = 0
with open(out, "w", encoding="utf-8", newline="") as fh:
    wtr = csv.writer(fh, lineterminator="\n")
    wtr.writerow(COLUMNS)
    for _id, es in sorted(entries.items(), key=lambda kv: (kv[1][0]["faction"], kv[1][0]["unit"])):
        facs = sorted({e["faction"] for e in es})
        home = home_faction(es, facs)
        r = next(e for e in es if e["faction"] == home)
        n_units += 1
        kw = ", ".join(k for k in r["keywords"] if k in KEEP)
        groups = group_text(r) if needs_groups(r) else ""
        for w in r["weapons"]:
            wtr.writerow([
                r["unit"], home, ", ".join(f for f in facs if f != home), r["id"], r["points"], r["models"],
                r["toughness"], r["wounds"], r["save"], r["invuln"] or "", r["fnp"] or "", r["oc"], r["move"],
                kw, groups,
                w["name"], "Ranged" if w["ranged"] else "Melee", w["attacks"], w["skill"], w["strength"],
                w["ap"], w["damage"], w["models"], abilities(w), "; ".join(w["conditional"]),
            ])
print(f"wrote {n_units} units to {out} ({out.stat().st_size:,} bytes)")
