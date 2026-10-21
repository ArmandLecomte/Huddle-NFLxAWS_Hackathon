# 🏈 Interactive NFL Game Simulation

Walk through a real NFL game **one play at a time** and see *why* each decision
is made. Built with matplotlib — step forward and back with the arrow keys.

## ▶️ Run it

```bash
cd huddle-simulation
python game_simulation.py                 # opening game: DAL @ TB (Week 1)
python game_simulation.py --game 2021091201   # a specific game (PIT @ BUF)
python game_simulation.py --list          # list every available game + playId
```

## 🎮 Controls

Use the on-screen **◀ Prev play** / **Next play ▶** buttons, or the keyboard:

| Key | Action |
|-----|--------|
| **→** / Space / n   | Next play |
| **←** / p / Backspace | Previous play |
| **q** / Esc         | Quit |

> If the arrow keys ever feel unresponsive, click the window first so it has
> keyboard focus — or just use the buttons, which always work. (matplotlib's
> default arrow-key bindings are cleared on startup so they reach the viewer.)

## 🖥️ What you see on each play

**Top — the field**
- The line of scrimmage (blue), the first-down marker (yellow dashed), and a
  yellow arrow showing which way the offense is attacking.
- A dot + arrow showing where the ball ended up (green = gain, red = loss).

**Bottom — the explanation panel**
- **Situation bar**: quarter, game clock, down & distance, possession, and the score.
- **ON THE FIELD**: the real NFL play-by-play description.
- **WHY THIS PLAY?**: plain-language reasoning behind the call — based on the
  down & distance, field position, formation, play action, and game situation.
- **DEFENSE**: how the defense lined up (the coverage scheme) and what it means.
- **OUTCOME**: a color-coded result (complete, incomplete, sack, interception, scramble).

## 📊 About the data

This uses the NFL pass-rush dataset in `../data/`, where **every play is a
quarterback dropback** (a passing play). Runs, kicks, and special teams are not
in the data — so the simulation walks through the **key passing plays** of a
game in order. That's still the best window into how an offense attacks and how
a defense counters.

## 🗂️ Files

| File | Purpose |
|------|---------|
| `game_simulation.py` | The interactive matplotlib viewer (run this) |
| `game_logic.py`      | Loads a game and turns each play into a narrated snapshot with decision reasoning |

## 🧠 How the reasoning is generated

`game_logic.build_snapshot()` reads real fields from each play (`down`,
`yardsToGo`, `yardlineSide`/`yardlineNumber`, `offenseFormation`,
`pff_playAction`, `pff_passCoverage`, score, quarter, clock) and composes an
explanation from them — e.g. "3rd & long is a passing down, the defense knows it,
so the offense must beat tight coverage." The outcome text is derived from
`passResult` and `playResult`. Nothing is invented: every statement is tied to a
column in the data.
