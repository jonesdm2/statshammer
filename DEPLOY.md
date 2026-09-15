# Statshammer on GitHub Pages — no Google Sheet

Both pages read one CSV file in the repo, from the same site.

## What's in this folder

| Path | What it is |
|---|---|
| `index.html` | The main Statshammer app (Warscroll, Unit Stats, Efficiency Matrix, Damage Distribution). Now reads `data/aos-units.csv`. It no longer uses the Google Sheet or the built-in points and unit-size tables. |
| `lab/index.html` | The AoS Maths Lab. Reads `../data/aos-units.csv`. |
| `data/aos-units.csv` | The unit data both pages use: one row per weapon, editable columns only. All probabilities, D100 and E100 are worked out by the pages. |
| `convert_app.py` | How `index.html` was converted from the original app, kept for reference. |

Each page also carries a built-in copy of the data. It's only used if the file can't be loaded (for example when the HTML is opened straight from your computer).

## Put it on the site (one time)

1. In the `jonesdm2/statshammer` repository, replace `index.html` with this one, and add the `lab` and `data` folders next to it. Commit and push, or on github.com use **Add file → Upload files**.
2. GitHub Pages serves:
   - the main app at **https://jonesdm2.github.io/statshammer/** (the address statshammer.com already embeds, so nothing changes there)
   - the lab at **https://jonesdm2.github.io/statshammer/lab/**
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
