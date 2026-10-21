# 🏈 NFL Data Analysis — Explained for New Viewers

A set of Jupyter notebooks that use real NFL tracking/play data (2021 season, Weeks 1–8) to explain
**why some teams and strategies are better than others** — written for people who don't yet know
the NFL.

Every chart comes with a plain-language "NFL Basics" note so you learn the sport while you read the data.

## 📓 The notebooks (read in order)

| # | Notebook | What it covers |
|---|----------|----------------|
| 1 | `01_introduction_nfl_basics.ipynb` | How a season/game is structured, scores, downs & distance — the fundamentals |
| 2 | `02_offensive_strategies.ipynb` | How teams move the ball through the air: formations, play action, coverage schemes |
| 3 | `03_team_comparison.ipynb` | Team rankings, QB performance, defensive pressure, and a head-to-head report card |

## 📊 About the data

This is the NFL's **pass-rush tracking dataset** — every play in `plays.csv` is a quarterback
**dropback (a passing play)**. So the analysis focuses on the passing game, pressure, and pass
defense rather than comparing run vs pass.

Data files live in `../data/`:
- `games.csv` — 122 games (teams, dates, weeks)
- `plays.csv` — 8,557 passing plays (down, distance, formation, coverage, result)
- `players.csv` — player info (name, position, team)
- `pffScoutingData.csv` — per-player, per-play scouting (roles, blocks, pressure, sacks)

## ⚙️ Setup

```bash
pip install pandas numpy matplotlib seaborn jupyter
jupyter notebook
```

Then open the notebooks in order and run all cells (Cell → Run All).

> Tip: in `03_team_comparison.ipynb`, change `TEAM_A` and `TEAM_B` in the report-card cell to
> compare any two teams (e.g. `'KC'` vs `'BUF'`).

## 🎯 The big takeaway

A team wins by being **more efficient**, not just more talented:
1. Move the ball consistently (high yards per play)
2. Make smart, accurate throws (high completion %, few interceptions)
3. Pressure the opposing quarterback (sacks, hurries, hits)
4. Convert on 3rd down to keep drives alive

When you watch a game, watch who wins the **3rd down battle** — that team usually wins.
