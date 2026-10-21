# 🏈 NFL Data Project — Explained for New Viewers

Analyze real NFL data (2021 season, Weeks 1–8) and explain **why teams and
strategies win** — written for people who don't yet know the sport. Two parts:

- **`notebooks/`** — Jupyter notebooks with matplotlib charts covering the basics,
  offensive strategy, and team comparisons.
- **`simulation/`** — an interactive, play-by-play game viewer you step through
  with the arrow keys, with a plain-language explanation of each decision.

## 📁 Structure

```
data/          the NFL CSVs (games, plays, players, scouting)
notebooks/     3 analysis notebooks + their README
simulation/    interactive game visualizer + its README
```

## ⚙️ Setup

```bash
pip install -r requirements.txt
```

## ▶️ Launch

**Notebooks** (run cells top to bottom, in order 01 → 02 → 03):

```bash
jupyter notebook notebooks/
```

**Interactive game simulation** (needs a desktop/display):

```bash
cd simulation
python game_simulation.py            # opening game: DAL @ TB
python game_simulation.py --list     # list all 122 games
```

Step through plays with the **◀ / ▶ buttons** or the **left/right arrow keys**.

## 📊 About the data

This is the NFL pass-rush dataset, so **every play is a quarterback dropback**
(a passing play). The analysis and simulation focus on the passing game, pressure,
and pass defense. See `notebooks/README.md` and `simulation/README.md` for details.
