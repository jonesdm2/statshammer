# Statshammer on GitHub Pages — no Google Sheet

Both pages read one CSV file in the repo, from the same site.

## What's in this folder

| Path | What it is |
|---|---|
| `index.html` | The main Statshammer app (Warscroll, Unit Stats, Efficiency Matrix, Damage Distribution). Now reads `data/aos-units.csv`. It no longer uses the Google Sheet or the built-in points and unit-size tables. |
| `lab/index.html` | The AoS Maths Lab. Reads `../data/aos-units.csv`. |
| `data/aos-units.csv` | The Age of Sigmar unit data both AoS pages use: one row per weapon, editable columns only. All probabilities, D100 and E100 are worked out by the pages. |
| `tow/index.html` | The Old World Maths Lab (Combat, Break Test, Buffs, Game Mix, Efficiency Matrix). Reads `../data/tow-units.csv`. |
| `data/tow-units.csv` | The Old World unit data: one row per unit (profile, troop type, armour, ward, regeneration, weapon Strength and AP, mounts, rule flags). Built from Old World Builder and the Online Rules Index. |
| `w40k/index.html` | The 40K Maths Lab (Attack, Breakpoints, Buffs, Game Mix, Efficiency Matrix). Reads `../data/w40k-units.csv`. |
| `data/w40k-units.csv` | The Warhammer 40,000 unit data: one row per weapon (unit profile repeated on each row, abilities as text such as `Lethal Hits, Anti-Vehicle 4+`). A unit several factions can take is listed once, under its own faction, with the others in `shared_with`. `model_groups` is filled only when a unit's models differ (for example `4x T3 W1 Sv4+ | 1x T3 W1 Sv4+ Inv5+`); a group with no `Inv` has no invulnerable save. Built from the BSData 11th edition catalogues. |
| `export_w40k_csv.py` | How `data/w40k-units.csv` was made, kept for reference. |
| `export_tow_csv.py` | How `data/tow-units.csv` was made from the extracted Old World data, kept for reference. |
| `convert_app.py` | How `index.html` was converted from the original app, kept for reference. |

Each page also carries a built-in copy of the data. It's only used if the file can't be loaded (for example when the HTML is opened straight from your computer).

## Put it on the site (one time)

1. In the `jonesdm2/statshammer` repository, replace `index.html` with this one, and add the `lab` and `data` folders next to it. Commit and push, or on github.com use **Add file → Upload files**.
2. GitHub Pages serves:
   - the main app at **https://jonesdm2.github.io/statshammer/** (the address statshammer.com already embeds, so nothing changes there)
   - the lab at **https://jonesdm2.github.io/statshammer/lab/**
   - the Old World lab at **https://jonesdm2.github.io/statshammer/tow/** and the 40K lab at **https://jonesdm2.github.io/statshammer/w40k/**
3. To show the lab on statshammer.com, add an Embed/Code block with:
   `<iframe src="https://jonesdm2.github.io/statshammer/lab/" style="width:100%;height:1400px;border:0" loading="lazy"></iframe>`

The Google Sheet is no longer needed by either page. You can unpublish it once the new files are live.

## What changed in the main app

- Points and unit sizes come from the data file's Points and Unit Size columns. They used to come from tables built into the page, which were out of date for 359 units.
- Weapons marked `Option` aren't counted in a unit's damage, and `Weapon Models` sets how many models carry each weapon. This applies to both the averages and the Damage Distribution simulation.
- A unit with the CHAMPION keyword gets its champion on its first weapon, as before.
- Warscrolls bought together are rated together, as in the lab. A 0-point warscroll's `Bought With` names the warscroll it comes with, whose damage, effective health, D100 and E100 then include it. Examples: the three Freeguild Command Corps warscrolls, Neave Blacktalon with her Companions and Lorai, and Gunnar Brand with Singri Brand and The Oathsworn Kin. The Warscroll and Unit Stats tabs label the group, and the Damage Distribution's "All weapons" run includes the whole group.
- ↻ Refresh reloads the data file. The badge says `DATA FILE` or `BUILT-IN COPY`.
- Refresh no longer adds duplicate factions to the dropdown.
- The app's own maths is otherwise unchanged. For exact probabilities, use the lab.

## Unit Card (all three labs)

Each lab has a **Unit Card** tab: everything on the unit's warscroll, datasheet or army list entry that you need at the table, plus the lab's own numbers. On that tab, clicking a unit in the sidebar opens its card without changing the attacker or target. **Print card** prints just the card.

What each card shows:
- **Age of Sigmar:** Move, Health, Save, Control, Ward; every weapon (option weapons marked); each ability's name, type, timing, casting or chanting value and keywords; unit size, points, command models, warscrolls bought together; keywords.
- **The Old World:** every profile row (models, champion, mount, crew); equipment, weapon and armour in combat; special rules; every option with its points cost (command group, equipment, armour, options, mounts); magic item allowance, lores and army composition limits.
- **40K:** every model's stat line; ranged and melee weapons with keywords, including other wargear (marked "option") and other firing modes; core, faction, datasheet and wargear ability names; unit size, points by size and model composition; keywords and faction keywords.

**Ability wording.** The data files don't hold rules text; the cards read it the way army builders do:
- **Age of Sigmar and 40K:** when you open a card, the page downloads the unit's BSData file from GitHub (pinned to the commit the data file was built from) and shows each ability's wording under its name. On the live site this takes a moment the first time for each faction; opened from your computer or in a Claude preview, GitHub can't be reached and only the names show.
- **The Old World:** click a special rule, weapon or option and it opens that page of the Warhammer: The Old World Online Rules Index in a pop-up, as Old World Builder does.

The columns the cards read:
- `data/aos-units.csv`: `warscroll_abilities` (repeated on each of the unit's rows, like the other unit columns), written as `Name [Type · Timing · Casting value 7 · Keywords] | Name [Passive]`, and `rules_source` (`Stormcast Eternals - Library.cat#e914-877f-21fe-8db9`: the BSData file and warscroll the wording is read from). `add_card_columns.py` in the lab sources refreshes both.
- `data/tow-units.csv`: `profiles` (`Name: M4 WS3 … Ld7 | …`), `unit_size`, `equipment`, `equipment_options`, `armour_options`, `options`, `command`, `mount_options` (each `Name (+5 pts per model); …`), `magic_items`, `lores`, `composition_notes`, and `rule_links` (`Furious Charge=special-rules/furious-charge | …`, the Rules Index page for each name).
- `data/w40k-units.csv`: `Ld`, `unit_size`, `points_by_size`, `composition`, `profiles`, `rules`, `datasheet_abilities`, `wargear_abilities`, `faction_keywords`, `rules_refs` (`Hail of Bolts=Imperium - Space Marines.json#4207-56a0-b930-84bd | …`, where each ability's wording is read from), and per weapon `loadout` (`Default`, `Option` or `Mode`), `range`, `weapon_keywords`. Only `Default` weapons count in the maths. To keep the file small enough to edit on github.com, a 40K unit's own columns are filled on its first row only; its other rows carry just the name, faction and id.

## Update the data

- **Small edits:** open `data/aos-units.csv` on github.com → pencil icon → edit → **Commit changes**. The lab shows the new data on its next load; there's nothing to rebuild.
- **Bigger edits:** edit the CSV in Excel or Google Sheets on your computer, save as CSV (UTF-8), and upload it over the old file.
- Keep the header row exactly as it is. The columns are:
  `unit_name, faction, Unit Type, health, save, ward, keywords, weapon_name, weapon_type, attacks, hit, wound, rend, damage, range, ability, Points, Unit Size, move, control, Loadout, Weapon Models, Bought With`
  - `Loadout`: `Default` or `Option`.
  - `Weapon Models`: how many models carry a Default weapon (blank = the whole unit).
  - `Bought With`: for a 0-point warscroll, the name of the warscroll it comes with.
  - Dice in `attacks` / `damage`: whole numbers or `D3`, `D6`, `2D6`, `D3+1` style.

## The badge in the header

- **DATA FILE · date**: read from `data/aos-units.csv` (the normal case on the site).
- **BUILT-IN COPY · date**: the file couldn't be loaded (for example when the HTML is opened straight from your computer), so it's using the copy saved inside the page. That copy is refreshed whenever the page is rebuilt with `build.py`.

## Rebuild the page (only needed after changing the lab's code or to refresh its built-in copy)

```
python build.py data/aos-units.csv "15 Sep 2026" <site folder> <repo folder>
```
