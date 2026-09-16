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

# 8. maths fixes (Statshammer script check, Sep 2026) and a per-100-points Efficiency Matrix

def replace_n(old, new, n, label):
    global s
    c = s.count(old)
    assert c == n, f"{label}: expected {n} matches, found {c}"
    s = s.replace(old, new)


# 8a. rend can take the save past 6+ (no save at all), and a roll of 1 always fails a save
replace_n("  const es=Math.max(1,Math.min(6,sv+r));\n  const saveFail=es<=6?1-Math.max(0,(7-es)/6):1;",
          "  const es=Math.max(2,sv+r); // 7+ means no save\n  const saveFail=es<=6?1-(7-es)/6:1;",
          2, "save clamp (expected damage)")
replace_once("  const es=Math.max(1,Math.min(6,sv+r));\n  const crit=getCritType(w);",
             "  const es=Math.max(2,sv+r); // 7+ means no save\n  const crit=getCritType(w);",
             "save clamp (simulation)")
# 8b. Crit (Mortal) and Crit (Auto-wound): the non-crit hits are the ones that rolled 2-5, P = hit chance - 1/6
replace_once("  const pCrit=1/6;\n  const pNorm=1-pCrit;",
             "  const pCrit=1/6;\n  const pNorm=Math.max(0,h-pCrit); // hits that were not an unmodified 6",
             "crit non-crit share")
replace_once("    dmg = a*(pCrit*d + pNorm*h*wn*saveFail*d);", "    dmg = a*(pCrit*d + pNorm*wn*saveFail*d);", "crit mortal")
replace_once("    dmg = a*(pCrit*saveFail*d + pNorm*h*wn*saveFail*d);", "    dmg = a*(pCrit*saveFail*d + pNorm*wn*saveFail*d);", "crit auto-wound")
# 8c. the champion's extra attack keeps the weapon's Crit ability (expected damage is linear in attacks)
replace_once("      const dChamp=isC?calcDmgWithAtks(w,aMean+1):0;",
             "      const dChamp=isC&&aMean>0?calcDmg(w)*(aMean+1)/aMean:0;",
             "champion crit")
# 8d. simulation: Crit (2 Hits) scores two hits that each roll to wound; the extra hit does not roll to hit again
replace_once("""        // Extra hit — add one more attack to the queue (cap at 10x original to be safe)
        if(queue<numAtk*10)queue++;
        // The original hit still proceeds to wound normally (no auto-wound)
        const woundRoll=Math.ceil(Math.random()*6);
        if(woundRoll<w.wound)continue;
        if(es<=6&&Math.ceil(Math.random()*6)>=es)continue;
        tot+=rollD(w.damage);""",
             """        // Two hits: each rolls to wound and save on its own (the extra hit does not roll to hit)
        for(let k=0;k<2;k++){
          if(Math.ceil(Math.random()*6)<w.wound)continue;
          if(es<=6&&Math.ceil(Math.random()*6)>=es)continue;
          tot+=rollD(w.damage);
        }""",
             "simulation 2 hits")
# 8e. quadrants: high damage + fragile is HAMMER, tough + low damage is ANVIL (the labels were swapped)
replace_once("""function quad(u){
  const d=u.totalDmg,e=u.eHealth;
  const axD=getAxD(),axE=getAxE();
  const hi=d>=axE,tk=e>=axD;
  if(hi&&tk)  return{lbl:'ELITE',  col:'#f0a500'};
  if(hi&&!tk) return{lbl:'ANVIL',  col:'#0057ff'};
  if(!hi&&tk) return{lbl:'HAMMER', col:'#e8001c'};
  return          {lbl:'SUPPORT',col:'#7090a8'};
}""",
             """// e = effective health, d = damage; L.axD is the health line, L.axE the damage line
function quadAt(e,d,L){
  const hi=d>=L.axE,tk=e>=L.axD;
  if(hi&&tk)  return{lbl:'ELITE',  col:'#f0a500'};
  if(hi&&!tk) return{lbl:'HAMMER', col:'#e8001c'};
  if(!hi&&tk) return{lbl:'ANVIL',  col:'#0057ff'};
  return          {lbl:'SUPPORT',col:'#7090a8'};
}
function quad(u){
  // per 100 points when the matrix is in that mode and the warscroll has a points cost
  if(mxMode==='per100'&&u.d100!=null){
    const fa=baseline==='faction'&&fac&&FAC_AVGS[fac];
    return quadAt(u.e100,u.d100,{axD:fa?FAC_AVGS[fac].avgE100:AVG_E100,axE:fa?FAC_AVGS[fac].avgD100:AVG_D100});
  }
  return quadAt(u.eHealth,u.totalDmg,{axD:getAxD(),axE:getAxE()});
}""",
             "quadrant labels")
# 8f. Efficiency Matrix: per-100-points axes (the default, as used in the videos) or whole unit, and an Exclude heroes filter
replace_once("""    <label class="ckr"><input type="checkbox" id="chkTL" checked onchange="drawMx()"> Trend line</label>""",
             """    <div class="sl">Axes</div>
    <div class="trow">
      <button class="tgl on" id="mxPer" onclick="setMxMode('per100')">Per 100 pts</button>
      <button class="tgl"    id="mxRaw" onclick="setMxMode('raw')">Whole unit</button>
    </div>
    <label class="ckr"><input type="checkbox" id="chkNH" onchange="drawMx()"> Exclude heroes</label>
    <label class="ckr"><input type="checkbox" id="chkTL" checked onchange="drawMx()"> Trend line</label>""",
             "matrix axis controls")
replace_once('<div class="psub" id="mxSub">Raw EH vs D · All AoS baseline</div>',
             '<div class="psub" id="mxSub">E100 vs D100 · All AoS</div>', "matrix subtitle")
replace_once("let _mxExcluded=new Set();",
             "let _mxExcluded=new Set();\n"
             "let mxMode='per100',_mxLines=null;\n"
             "function setMxMode(m){\n"
             "  mxMode=m;\n"
             "  document.getElementById('mxPer').classList.toggle('on',m==='per100');\n"
             "  document.getElementById('mxRaw').classList.toggle('on',m==='raw');\n"
             "  renderList();drawMx();\n"
             "}",
             "matrix mode state")
replace_once("  document.getElementById('mxSub').textContent='Raw EH vs D · '+(fac?fac:'All AoS')+' baseline';\n", "",
             "old subtitle update")
replace_between("  let us=UNITS;\n  if(fac)us=us.filter(u=>u.faction===fac);\n  if(!us.length){\n    ctx.fillStyle",
                "  const qx=tx(axD),qy=ty(axE);\n",
                """  // Warscrolls rated as part of another are plotted with it; per-100 mode needs a points cost
  const per=mxMode==='per100';
  const noHero=document.getElementById('chkNH').checked;
  const hasKw=(u,k)=>u.keywords.some(x=>x.toUpperCase()===k);
  const pool=UNITS.filter(u=>!u.memberOf
    &&(!per||(u.pts>0&&u.d100!=null&&!hasKw(u,'MANIFESTATION')&&!hasKw(u,'FACTION TERRAIN')))
    &&!(noHero&&hasKw(u,'HERO')));
  let us=pool;
  if(fac)us=us.filter(u=>u.faction===fac);
  const lineAt=baseline==='faction'&&fac?'faction':'All-AoS';
  document.getElementById('mxSub').textContent=(per?'E100 vs D100 (per 100 points)':'Effective health vs damage (whole unit)')
    +' · '+(fac||'All AoS')+' · quadrant lines at the '+lineAt+' mean'+(noHero?' · heroes excluded':'');
  if(!us.length){
    ctx.fillStyle='#3a5060';ctx.font='14px Barlow';ctx.textAlign='center';
    ctx.fillText('No data for selected faction',W/2,260);return;
  }

  // Split into included and excluded sets
  const mkKey=u=>u.name+'|||'+u.faction;
  const usIncl=us.filter(u=>!_mxExcluded.has(mkKey(u)));
  const usExcl=us.filter(u=>_mxExcluded.has(mkKey(u)));

  // Update badge
  const badge=document.getElementById('mxExclBadge');
  if(badge)badge.textContent=_mxExcluded.size>0?'('+_mxExcluded.size+' excluded)':'';

  // X = effective health, Y = damage (per 100 points, or for the whole unit)
  const getDv=u=>per?u.e100:u.eHealth;
  const getEv=u=>per?u.d100:u.totalDmg;
  const mean=(xs,f)=>xs.length?xs.reduce((s,u)=>s+f(u),0)/xs.length:0;

  // Quadrant lines: mean of the included warscrolls, game-wide or for the faction (Baseline)
  const poolIncl=pool.filter(u=>!_mxExcluded.has(mkKey(u)));
  const lineSet=lineAt==='faction'&&usIncl.length?usIncl:(poolIncl.length?poolIncl:pool);
  const axD=mean(lineSet,getDv),axE=mean(lineSet,getEv);
  _mxLines={axD,axE,getDv,getEv,per};

  const maxD=Math.max(...us.map(getDv),axD)*1.12||20;
  const maxE=Math.max(...us.map(getEv),axE)*1.12||20;
  const tx=d=>P.l+(d/maxD)*PW;
  const ty=e=>P.t+PH-(e/maxE)*PH;
  const qx=tx(axD),qy=ty(axE);
""", "matrix pool and lines")
replace_once("  ctx.fillText('Damage Output',0,0);ctx.restore();",
             "  ctx.fillText(per?'Damage per 100 points (D100)':'Damage Output',0,0);ctx.restore();", "y label")
replace_once("  ctx.fillText('Effective Health',P.l+PW/2,P.t+PH+38);",
             "  ctx.fillText(per?'Effective health per 100 points (E100)':'Effective Health',P.l+PW/2,P.t+PH+38);", "x label")
replace_once("""    const inclAll=UNITS.filter(u=>!_mxExcluded.has(mkKey(u)));
    const avgEHincl=inclAll.length?inclAll.reduce((s,u)=>s+getDv(u),0)/inclAll.length:AVG_EH;
    const avgDincl=inclAll.length?inclAll.reduce((s,u)=>s+getEv(u),0)/inclAll.length:AVG_D;""",
             """    const avgEHincl=mean(poolIncl,getDv);
    const avgDincl=mean(poolIncl,getEv);""", "all-AoS cross")
replace_once("""    document.getElementById('rADv').textContent=inclAvgEH.toFixed(3);
    document.getElementById('rAEv').textContent=inclAvgD.toFixed(3);""",
             """    document.getElementById('rAD').firstChild.nodeValue='All-AoS avg '+(per?'E100 ':'EH ');
    document.getElementById('rAE').firstChild.nodeValue='All-AoS avg '+(per?'D100 ':'D ');
    document.getElementById('rFD').firstChild.nodeValue='Faction avg '+(per?'E100 ':'EH ');
    document.getElementById('rFE').firstChild.nodeValue='Faction avg '+(per?'D100 ':'D ');
    document.getElementById('rADv').textContent=mean(poolIncl,getDv).toFixed(3);
    document.getElementById('rAEv').textContent=mean(poolIncl,getEv).toFixed(3);""", "strip labels")
replace_once("    const u=near.u,q=quad(u);",
             "    const u=near.u,L=_mxLines,q=L?quadAt(L.getDv(u),L.getEv(u),L):quad(u);", "tooltip quadrant")
replace_once("""    document.getElementById('ttD').textContent=fmtN(u.totalDmg);
    document.getElementById('ttEH').textContent=fmtN(u.eHealth);""",
             """    document.getElementById('ttD').textContent=L&&L.per?fmtN(u.d100)+' per 100 pts':fmtN(u.totalDmg);
    document.getElementById('ttEH').textContent=L&&L.per?fmtN(u.e100)+' per 100 pts':fmtN(u.eHealth);""", "tooltip values")

for gone in ("docs.google.com/spreadsheets", "allorigins", "UNIT_PTS_LUT[", "UNIT_SIZE_LUT["):
    assert gone not in s, f"still contains {gone}"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s, encoding="utf-8", newline="\n")
print(f"converted app: {before:,} -> {len(s):,} chars; built-in copy has {csv_text.count(chr(10))} data rows; written to {out}")
