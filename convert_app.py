"""Move the main Statshammer app (repo-root index.html) off the Google Sheet and onto data/aos-units.csv.

Every change is an exact text replacement that must match once, so a change to the app's code fails loudly
instead of silently producing a half-converted page.

  python convert_app.py <original index.html> <data/aos-units.csv> <output index.html>
"""
import sys
from pathlib import Path

src, data_csv, out = (Path(a) for a in sys.argv[1:4])
s = src.read_text(encoding="utf-8")
before = len(s)
csv_text = data_csv.read_text(encoding="utf-8").strip("\n")


def replace_once(old, new, label):
    global s
    n = s.count(old)
    assert n == 1, f"{label}: expected 1 match, found {n}"
    s = s.replace(old, new)


def replace_between(start, end, new, label):
    """Replace from `start` up to and including the first `end` after it."""
    global s
    i = s.find(start)
    assert i >= 0 and s.count(start) == 1, f"{label}: start not unique"
    j = s.find(end, i)
    assert j >= 0, f"{label}: end not found"
    s = s[:i] + new + s[j + len(end):]


# 1. data source
replace_between("const CSV_URL = 'https://docs.google.com/", "';\n", "const DATA_URL = 'data/aos-units.csv';\n", "CSV_URL")

# 2. built-in copy of the data (offline fallback), replacing the old v7 inline CSV
literal = csv_text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
replace_between("const INLINE_CSV=`", "`;", "const INLINE_CSV=`" + literal + "`;", "INLINE_CSV")
replace_once("// ── Inline data (from v7, avoids CORS entirely)", "// ── Built-in copy of data/aos-units.csv (used only if the data file can't be loaded)", "inline comment")

# 3. the points and unit-size lookup tables now live in the data file
replace_between("const UNIT_PTS_LUT={", "};", "// Points now come from the Points column of data/aos-units.csv", "UNIT_PTS_LUT")
replace_between("const UNIT_SIZE_LUT={", "};", "// Unit sizes now come from the Unit Size column of data/aos-units.csv", "UNIT_SIZE_LUT")

# 4. build units from the data file's columns
replace_once(
    "      // Look up authoritative size + champIdx from v7 data; fall back to 1/null\n"
    "      const lut=UNIT_SIZE_LUT[key]||[1,null];\n"
    "      const sz=lut[0];\n"
    "      const ci=lut[1];\n",
    "      // Unit size, points and champion come from data/aos-units.csv\n"
    "      const sz=parseInt(r['Unit Size'])||1;\n"
    "      const ci=kws.some(k=>k.toUpperCase()==='CHAMPION')?0:null;\n",
    "size/champion lookup")
replace_once("        size:sz,\n        champIdx:ci\n      });",
             "        size:sz,\n        champIdx:ci,\n        pts:parseFloat(r.Points)||0\n      });", "unit points")
replace_once("      companion:isCompanion(r.ability)\n    };",
             "      companion:isCompanion(r.ability),\n      models:parseInt(r['Weapon Models'])||null\n    };", "weapon models")
replace_once("    if(wpn.companion){\n      u.companions.push(wpn);",
             "    // Weapons marked Option aren't part of the unit's default loadout, so they aren't counted\n"
             "    if((r.Loadout||'').toLowerCase()==='option') return;\n"
             "    if(wpn.companion){\n      u.companions.push(wpn);", "skip options")
replace_once("      const isC=(wi===ci);\n      const aMean=parseMean(w.attacks);",
             "      const isC=(wi===ci);\n"
             "      // models carrying this weapon: Weapon Models if given (the champion is one of them), else the unit\n"
             "      const n=w.models!=null?(isC?w.models-1:w.models):nNorm;\n"
             "      const aMean=parseMean(w.attacks);", "carriers")
replace_once("        rd+=dNorm*nNorm+(isC?dChamp:0);", "        rd+=dNorm*n+(isC?dChamp:0);", "ranged carriers")
replace_once("        md+=dNorm*nNorm+(isC?dChamp:0);", "        md+=dNorm*n+(isC?dChamp:0);", "melee carriers")
replace_once("      const d=calcDmg(w)*sz;", "      const d=calcDmg(w)*(w.models||sz);", "companion carriers")
replace_once("    const pts=UNIT_PTS_LUT[u.name+'|||'+u.faction]||0;", "    const pts=u.pts||0;", "points")

# 5. the damage simulation uses the same model counts
replace_once("  const nNorm=isComp?sz:(ci!=null?sz-1:sz);",
             "  const nNorm=isComp?(w.models||sz):(w.models!=null?(isC?w.models-1:w.models):(ci!=null?sz-1:sz));", "simWeapon")
replace_once("      tot+=simAttacks(w,nNorm,sv,isC);",
             "      tot+=simAttacks(w,w.models!=null?(isC?w.models-1:w.models):nNorm,sv,isC);", "simAll weapons")
replace_once("      tot+=simAttacks(w,sz,sv,false);", "      tot+=simAttacks(w,w.models||sz,sv,false);", "simAll companions")

# 6. load the data file first, fall back to the built-in copy
replace_between(
    "    if(fromNetwork){\n      // Try direct, then allorigins proxy",
    "      text=INLINE_CSV;\n    }\n",
    "    // Read data/aos-units.csv from the same site; if it can't be reached (e.g. opened from disk), use the built-in copy\n"
    "    let source='DATA FILE';\n"
    "    try{\n"
    "      const r=await fetch(DATA_URL,{cache:'no-cache'});\n"
    "      if(r.ok){text=await r.text();}\n"
    "    }catch(e){}\n"
    "    if(!text){text=INLINE_CSV;source='BUILT-IN COPY';}\n",
    "loadCSV source")
replace_once("    badge.textContent=UNITS.length+' UNITS';", "    badge.textContent=UNITS.length+' UNITS · '+source;", "badge")
replace_once("    const sel=document.getElementById('selFac');\n    FACS.forEach(f=>{",
             "    const sel=document.getElementById('selFac');\n    sel.length=1; // keep \"All Factions\", drop options from a previous load\n    FACS.forEach(f=>{",
             "dropdown reset")
replace_once('title="Refresh data from Google Sheet"', 'title="Reload data/aos-units.csv"', "refresh title")

# 7. warscrolls bought together (Bought With): a 0-point warscroll's damage and effective health count towards its lead
replace_once("        pts:parseFloat(r.Points)||0\n      });",
             "        pts:parseFloat(r.Points)||0,\n        boughtWith:(r['Bought With']||'').trim(),\n        members:[]\n      });",
             "bought with field")
replace_once(
    "    units.push(u);\n  });\n  return units;\n}",
    "    units.push(u);\n  });\n"
    "  // Warscrolls bought together: a 0-point warscroll's damage and effective health count towards the one it comes with\n"
    "  const byKey=new Map(units.map(x=>[x.name+'|||'+x.faction,x]));\n"
    "  units.forEach(m=>{\n"
    "    if(!m.boughtWith)return;\n"
    "    const lead=byKey.get(m.boughtWith+'|||'+m.faction);\n"
    "    if(!lead||lead===m)return;\n"
    "    lead.members.push(m);\n"
    "    m.memberOf=lead;\n"
    "  });\n"
    "  units.forEach(u=>{\n"
    "    if(!u.members.length)return;\n"
    "    u.members.forEach(m=>{u.meleeDmg+=m.meleeDmg;u.rangedDmg+=m.rangedDmg;u.eHealth+=m.eHealth;});\n"
    "    u.totalDmg=u.meleeDmg+u.rangedDmg;\n"
    "    u.d100=u.pts>0?u.totalDmg/u.pts*100:null;\n"
    "    u.e100=u.pts>0?u.eHealth/u.pts*100:null;\n"
    "  });\n"
    "  return units;\n}",
    "group totals")
replace_once("  document.getElementById('wKw').textContent=u.keywords.join(' · ');",
             "  document.getElementById('wKw').textContent=u.keywords.join(' · ')+"
             "(u.members&&u.members.length?'  ·  RATED WITH '+u.members.map(m=>m.name).join(' + ').toUpperCase()"
             ":u.memberOf?'  ·  RATED AS PART OF '+u.memberOf.name.toUpperCase():'');",
             "warscroll group note")
replace_once("  document.getElementById('stPS').textContent=u.faction;",
             "  document.getElementById('stPS').textContent=u.faction+"
             "(u.members&&u.members.length?' · rated with '+u.members.map(m=>m.name).join(' + ')"
             ":u.memberOf?' · rated as part of '+u.memberOf.name:'');",
             "stats group note")
replace_once("      tot+=simAttacks(w,w.models||sz,sv,false);\n    });\n    res.push(tot);",
             "      tot+=simAttacks(w,w.models||sz,sv,false);\n    });\n"
             "    // warscrolls bought with this one fight alongside it\n"
             "    (u.members||[]).forEach(m=>{tot+=simAll(m,1,sv)[0];});\n"
             "    res.push(tot);",
             "simulate members")
replace_once("(u.champIdx!=null?' +champ':'')):'1 model';",
             "(u.champIdx!=null?' +champ':'')):'1 model';\n"
             "  const grpLabel=u.members&&u.members.length?' + '+u.members.map(m=>m.name).join(' + '):'';",
             "distribution label")
replace_once("${szLabel} · ${datasets", "${szLabel}${_wpnActive.has('__all__')?grpLabel:''} · ${datasets", "distribution label use")

for gone in ("docs.google.com/spreadsheets", "allorigins", "UNIT_PTS_LUT[", "UNIT_SIZE_LUT["):
    assert gone not in s, f"still contains {gone}"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s, encoding="utf-8", newline="\n")
print(f"converted app: {before:,} -> {len(s):,} chars; built-in copy has {csv_text.count(chr(10))} data rows; written to {out}")
