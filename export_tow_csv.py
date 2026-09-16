"""Export the Old World unit data (Old World Builder + Online Rules Index join) to data/tow-units.csv.

One row per unit, editable columns only; all probabilities, CE100, Wounds100 and E100 are worked out by the page.
The columns from `profiles` on are for the Unit Card: every profile row from the Rules Index, and the unit's
equipment, options, command group, mounts, magic item allowance and lores from Old World Builder (names and
points costs only), and `rule_links`: where each special rule, weapon and piece of equipment lives in the
Warhammer: The Old World Online Rules Index, using Old World Builder's own name-to-page map. The card opens that page
for the wording, as Old World Builder does.

  python export_tow_csv.py <units_*.json> <data/tow-units.csv>
"""
import csv
import glob
import json
import os
import re
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = json.load(open(src, encoding="utf-8"))
DATA = Path(r"C:\Users\David Mazzocchi-Jone\Desktop\Statshammer\_channel\data\tow")
OWB = DATA / "raw" / "public" / "games" / "the-old-world"
INDEX = json.load(open(DATA / "validation" / "index_units.json", encoding="utf-8"))
index_by_slug = {u["slug"]: u for u in INDEX}
owb = {}
for path in glob.glob(str(OWB / "*.json")):
    army = os.path.basename(path)[:-5]
    if army == "magic-items":
        continue
    for cat, units in json.load(open(path, encoding="utf-8")).items():
        for u in units:
            owb.setdefault((army, u["id"]), u)

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
           "unstable", "indomitable", "hatred", "frenzy", "named", "mounts", "special_rules",
           # Unit Card
           "profiles", "unit_size", "equipment", "equipment_options", "armour_options", "options", "command",
           "mount_options", "magic_items", "lores", "composition_notes", "rule_links"]
ITEM_TYPES = {"armor": "armour", "armor-mages": "armour (wizards)", "arcane-item": "arcane item", "enchanted-item": "enchanted item",
              "banner": "banner", "weapon": "weapon", "talisman": "talisman"}


RULES_SRC = DATA / "raw" / "src" / "components" / "rules-index"
RULES_MAP = json.load(open(RULES_SRC / "rules-index-export.json", encoding="utf-8"))
_rm = (RULES_SRC / "rules-map.js").read_text(encoding="utf-8")
_extra = _rm[_rm.index("additionalOWBRules"):_rm.index("export const synonyms")]
for q, bare, url in re.findall(r'(?:"([^"]+)"|([A-Za-z][\w]*))\s*:\s*\{\s*url:\s*"([^"]+)"', _extra):
    RULES_MAP[q or bare] = {"url": url}
_syn = _rm[_rm.index("export const synonyms"):_rm.index("export const rulesMap")]
SYNONYMS = {q or bare: v for q, bare, v in re.findall(r'(?:"([^"]+)"|([A-Za-z][\w]*))\s*:\s*"([^"]+)"', _syn)}


def normalize_rule(s):
    """Old World Builder's normalizeRuleName."""
    s = re.sub(r" *\([^)]*\) *", "", (s or "").lower())
    s = re.sub(r"[{}*\[\]]", "", s)
    s = re.sub(r"^[0-9]x ", "", s)
    return s.replace("“", '"').replace("”", '"').strip()


def rule_url(name):
    n = normalize_rule(name)
    hit = RULES_MAP.get(n) or RULES_MAP.get(SYNONYMS.get(n, ""))
    return hit["url"] if hit else None


def split_top(s, sep=","):
    out, depth, cur = [], 0, ""
    for ch in s or "":
        depth += ch == "("
        depth -= ch == ")" and depth > 0
        if ch == sep and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def links_for(r, owb_unit):
    names = split_top(r.get("special_rules") or "")
    names += [(r.get("weapon") or {}).get("name") or ""]
    for e in r.get("equipment") or []:
        names += split_top(e)
    if owb_unit:
        for group in ("equipment", "armor", "options", "mounts", "command"):
            for o in owb_unit.get(group, []) or []:
                names += split_top(clean(o.get("name_en")))
    out, seen = [], set()
    for n in names:
        n = n.strip()
        if not n or n in seen:
            continue
        seen.add(n)
        url = rule_url(n)
        if url:
            out.append(f"{n}={url}")
    return " | ".join(out)


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


def clean(name):
    return re.sub(r"\s*\{[^}]*\}", "", name or "").strip()


def cost(o):
    pts = o.get("points") or 0
    if not pts:
        return "free"
    return f"+{pts} pts" + (" per model" if o.get("perModel") else "")


def listed(opts, skip_active=False):
    out = []
    for o in opts or []:
        if skip_active and (o.get("active") or o.get("equippedDefault")):
            continue
        text = f"{clean(o.get('name_en'))} ({cost(o)})"
        subs = [f"{clean(x.get('name_en'))} {cost(x)}" for x in o.get("options", []) or []]
        if subs:
            text = text[:-1] + "; " + ", ".join(subs) + ")"
        out.append(text)
    return "; ".join(out)


def profile_text(slug):
    iu = index_by_slug.get(slug)
    if not iu:
        return ""
    parts = []
    for p in iu["profiles"]:
        stats = " ".join(f"{k}{p.get(k, '-') or '-'}" for k in ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"))
        parts.append(f"{p.get('Name', '').replace(':', '')}: {stats}")
    return " | ".join(parts)


def card(r):
    u = owb.get((r["army"], r["owb_id"]))
    if not u:
        return [""] * 11 + [links_for(r, None)]
    lo = u.get("minimum") or r.get("min_models") or 1
    hi = u.get("maximum") or 0
    size = str(lo) if (hi == lo or (not u.get("minimum") and not hi)) else (f"{lo}-{hi}" if hi else f"{lo}+")
    equip = [clean(e.get("name_en")) for e in u.get("equipment", []) if e.get("active") or e.get("equippedDefault")]
    armour = [clean(e.get("name_en")) for e in u.get("armor", []) if e.get("active")]
    always = [clean(o.get("name_en")) for o in u.get("options", []) if o.get("alwaysActive")]
    command = []
    for c in u.get("command", []) or []:
        text = f"{clean(c.get('name_en'))} ({cost(c)}"
        if c.get("magic"):
            text += f"; magic items up to {c['magic'].get('maxPoints', 0)} pts: " + ", ".join(ITEM_TYPES.get(x, x) for x in c["magic"].get("types", []))
        command.append(text + ")")
    items = [f"{clean(i.get('name_en'))} up to {i.get('maxPoints', 0)} pts: " + ", ".join(ITEM_TYPES.get(x, x) for x in i.get("types", []))
             for i in u.get("items", []) or [] if i.get("maxPoints")]
    lores = [l.replace("-", " ").title() for l in u.get("lores", []) or []]
    notes = sorted({(v.get("notes") or {}).get("name_en", "") for v in (u.get("armyComposition") or {}).values()} - {""})
    return [profile_text(r["index_slug"]), size, ", ".join(equip + armour + always),
            listed(u.get("equipment"), skip_active=True), listed(u.get("armor"), skip_active=True),
            listed([o for o in u.get("options", []) if not o.get("alwaysActive")]), "; ".join(command),
            listed([m for m in u.get("mounts", []) if not m.get("active")]), "; ".join(items), ", ".join(lores),
            " / ".join(notes), links_for(r, u)]


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
        ]] + card(r))
print(f"wrote {len(rows)} units, {len(COLUMNS)} columns to {out} ({out.stat().st_size:,} bytes)")
