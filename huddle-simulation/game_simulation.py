"""
game_simulation.py
-------------------
Interactive, play-by-play NFL game visualizer built on matplotlib.

Walk through a real game one key passing play at a time:
    →  (right arrow)  next play
    ←  (left arrow)   previous play
    q                 quit

For each play you see:
    * a football field with the line of scrimmage and first-down marker
    * the situation (quarter, clock, down & distance, score)
    * the decision the offense made and WHY it makes sense
    * how the defense responded
    * the outcome of the play

Run it:
    python simulation/game_simulation.py                # default opening game
    python simulation/game_simulation.py --game 2021091201
    python simulation/game_simulation.py --list         # list available games

Note: the dataset only contains quarterback dropbacks (passing plays),
so this walks through the key passing plays of the game in order.
"""

from __future__ import annotations

import argparse
import textwrap

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
from matplotlib.widgets import Button

import game_logic as gl


# matplotlib binds the arrow keys to its built-in "back/forward in view
# history" navigation by default, which swallows our key events. Clear
# those bindings so left/right reach the viewer.
for _key in ("keymap.back", "keymap.forward"):
    try:
        matplotlib.rcParams[_key] = [
            k for k in matplotlib.rcParams[_key]
            if k not in ("left", "right", "c", "v", "backspace")
        ]
    except KeyError:
        pass


# ---------------------------------------------------------------------------
# Field drawing
# ---------------------------------------------------------------------------
FIELD_GREEN = "#1b7a3d"
ENDZONE_BLUE = "#15315c"
ENDZONE_RED = "#7a1b2e"


def _absolute_to_x(absolute_yardline):
    """
    Map absoluteYardlineNumber (distance from the end zone for the
    possession team, 0-120) to an x coordinate on our 0-120 field.
    Returns None if unavailable.
    """
    if absolute_yardline is None:
        return None
    try:
        return float(absolute_yardline)
    except (TypeError, ValueError):
        return None


class GameViewer:
    def __init__(self, game_info, snapshots):
        self.info = game_info
        self.snaps = snapshots
        self.idx = 0

        self.fig = plt.figure(figsize=(15, 9.4))
        try:
            self.fig.canvas.manager.set_window_title(
                f"NFL Game Simulation — {game_info['visitorTeamAbbr']} @ {game_info['homeTeamAbbr']}"
            )
        except AttributeError:
            pass

        # Two stacked areas: field on top, explanation panel below,
        # with a strip at the very bottom reserved for the nav buttons.
        self.ax_field = self.fig.add_axes([0.04, 0.55, 0.92, 0.40])
        self.ax_info = self.fig.add_axes([0.04, 0.12, 0.92, 0.41])
        self.ax_info.axis("off")

        # On-screen navigation buttons (reliable fallback if arrow keys
        # don't reach the window on a given platform/backend).
        self.ax_prev = self.fig.add_axes([0.30, 0.03, 0.17, 0.06])
        self.ax_next = self.fig.add_axes([0.53, 0.03, 0.17, 0.06])
        self.btn_prev = Button(self.ax_prev, "\u25C0  Prev play",
                               color="#dfe6ee", hovercolor="#c3d0e0")
        self.btn_next = Button(self.ax_next, "Next play  \u25B6",
                               color="#dfe6ee", hovercolor="#c3d0e0")
        self.btn_prev.on_clicked(lambda _evt: self.prev())
        self.btn_next.on_clicked(lambda _evt: self.next())

        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.draw()

    # ----- navigation -----
    def next(self):
        if self.idx < len(self.snaps) - 1:
            self.idx += 1
            self.draw()

    def prev(self):
        if self.idx > 0:
            self.idx -= 1
            self.draw()

    def on_key(self, event):
        key = event.key
        if key in ("right", " ", "n", "d", "pagedown"):
            self.next()
        elif key in ("left", "p", "a", "pageup", "backspace"):
            self.prev()
        elif key in ("q", "escape"):
            plt.close(self.fig)

    # ----- field -----
    def draw_field(self, snap):
        ax = self.ax_field
        ax.clear()
        ax.set_xlim(0, gl.FIELD_LENGTH)
        ax.set_ylim(0, 53.3)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("auto")

        home = self.info["homeTeamAbbr"]
        visitor = self.info["visitorTeamAbbr"]

        # Grass
        ax.add_patch(Rectangle((10, 0), 100, 53.3, facecolor=FIELD_GREEN, zorder=0))
        # End zones
        ax.add_patch(Rectangle((0, 0), 10, 53.3, facecolor=ENDZONE_BLUE, zorder=0))
        ax.add_patch(Rectangle((110, 0), 10, 53.3, facecolor=ENDZONE_RED, zorder=0))
        ax.text(5, 26.65, visitor, color="white", fontsize=18, fontweight="bold",
                ha="center", va="center", rotation=90)
        ax.text(115, 26.65, home, color="white", fontsize=18, fontweight="bold",
                ha="center", va="center", rotation=90)

        # Yard lines every 5 yards + numbers every 10
        for yl in range(10, 111, 5):
            ax.plot([yl, yl], [0, 53.3], color="white", linewidth=0.8, alpha=0.6, zorder=1)
        for yd in range(10, 51, 10):
            for xpos in (10 + yd, 110 - yd):
                label = str(yd if yd < 50 else 50)
                ax.text(xpos, 5, label, color="white", fontsize=11, ha="center", alpha=0.85)
                ax.text(xpos, 48, label, color="white", fontsize=11, ha="center", alpha=0.85)
        ax.text(60, 5, "50", color="white", fontsize=11, ha="center", alpha=0.85)
        ax.text(60, 48, "50", color="white", fontsize=11, ha="center", alpha=0.85)

        # Line of scrimmage & first-down marker
        los = _absolute_to_x(snap["absolute_yardline"])
        if los is not None:
            los = max(11, min(109, los))
            ax.plot([los, los], [0, 53.3], color="#2166d1", linewidth=3, zorder=3)
            ax.text(los, 55, "Line of scrimmage", color="#2166d1", fontsize=10,
                    ha="center", fontweight="bold")

            # First-down marker: yardsToGo toward the defense's end zone.
            # absoluteYardlineNumber decreases toward the possession team's
            # target end zone (x = 110 side). We draw the marker downfield.
            try:
                ytg = float(snap["ytg"])
            except (TypeError, ValueError):
                ytg = None
            if ytg is not None:
                fd = los + ytg
                if fd < 110:
                    ax.plot([fd, fd], [0, 53.3], color="#f4d03f", linewidth=2.5,
                            linestyle="--", zorder=3)
                    ax.text(fd, 55, "1st down", color="#c9a400", fontsize=10,
                            ha="center", fontweight="bold")

            # Little arrow showing offense's direction of attack
            ax.add_patch(FancyArrow(los, 26.65, 8, 0, width=0.8, head_width=3,
                                    head_length=2.5, color="#ffd24d", alpha=0.9, zorder=4))

        # Result marker: where the ball ended up (if a gain/loss)
        if los is not None and snap["result_code"] in ("C", "R", "S"):
            end_x = max(11, min(109, los + snap["gained"]))
            color = "#ff6b6b" if snap["gained"] < 0 else "#7CFC00"
            ax.scatter([end_x], [26.65], s=180, color=color, edgecolors="white",
                       linewidth=1.5, zorder=5)
            ax.annotate("", xy=(end_x, 20), xytext=(los, 20),
                        arrowprops=dict(arrowstyle="->", color=color, lw=2), zorder=5)

        # Title bar on the field
        ax.set_title(
            f"{visitor} @ {home}  —  Week {int(self.info['week'])}   "
            f"(Play {self.idx + 1} of {len(self.snaps)})",
            fontsize=14, fontweight="bold", pad=28,
        )

    # ----- explanation panel -----
    def draw_info(self, snap):
        ax = self.ax_info
        ax.clear()
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        # Scoreboard / situation header
        off_is_home = snap["offense"] == snap["home"]
        header = (
            f"{snap['situation']}        SCORE:  {snap['score_line']}"
        )
        ax.text(0.5, 0.97, header, fontsize=15, fontweight="bold",
                ha="center", va="top", family="monospace",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#15315c", edgecolor="none"),
                color="white")

        y = 0.82

        # Play description (the real NFL play-by-play line)
        desc = snap["description"]
        if isinstance(desc, str) and desc:
            wrapped = textwrap.fill("ON THE FIELD:  " + desc, width=120)
            ax.text(0.02, y, wrapped, fontsize=10.5, ha="left", va="top",
                    style="italic", color="#333333")
            y -= 0.06 * (wrapped.count("\n") + 1) + 0.03

        # Decision reasoning
        ax.text(0.02, y, "WHY THIS PLAY? (the decision explained)", fontsize=12,
                fontweight="bold", color="#15315c", ha="left", va="top")
        y -= 0.06
        for reason in snap["reasons"]:
            wrapped = textwrap.fill("•  " + reason, width=118,
                                    subsequent_indent="   ")
            ax.text(0.03, y, wrapped, fontsize=10.5, ha="left", va="top", color="#222222")
            y -= 0.045 * (wrapped.count("\n") + 1) + 0.012

        # Defense response
        if snap["defense_note"]:
            y -= 0.01
            wrapped = textwrap.fill("DEFENSE:  " + snap["defense_note"], width=118,
                                    subsequent_indent="    ")
            ax.text(0.03, y, wrapped, fontsize=10.5, ha="left", va="top", color="#7a1b2e")
            y -= 0.045 * (wrapped.count("\n") + 1) + 0.02

        # Outcome box
        result_colors = {
            "C": "#1b7a3d", "I": "#8a6d00", "S": "#b34700",
            "IN": "#7a1b2e", "R": "#15315c",
        }
        box_color = result_colors.get(snap["result_code"], "#333333")
        wrapped_out = textwrap.fill("OUTCOME:  " + snap["outcome"], width=112,
                                    subsequent_indent="          ")
        ax.text(0.5, max(y - 0.02, 0.08), wrapped_out, fontsize=12, fontweight="bold",
                ha="center", va="top", color="white",
                bbox=dict(boxstyle="round,pad=0.5", facecolor=box_color, edgecolor="none"))

        # Footer controls hint (buttons live below this panel)
        ax.text(0.5, 0.01,
                "Click the buttons below, or use the LEFT / RIGHT arrow keys "
                "(space = next, q = quit)",
                fontsize=10.5, ha="center", va="bottom", color="#555555",
                family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#e8e8e8", edgecolor="none"))

    def draw(self):
        snap = self.snaps[self.idx]
        self.draw_field(snap)
        self.draw_info(snap)
        self.fig.canvas.draw_idle()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Interactive NFL game play-by-play visualizer")
    parser.add_argument("--game", type=int, default=None, help="gameId to visualize")
    parser.add_argument("--list", action="store_true", help="list available games and exit")
    args = parser.parse_args()

    games, plays, players = gl.load_data()
    catalog = gl.list_games(games, plays)

    if args.list:
        print("Available games:\n")
        for _, row in catalog.iterrows():
            print(f"  {row['gameId']}   {row['label']}   [{row['num_plays']} plays]")
        return

    game_id = args.game if args.game is not None else int(catalog.iloc[0]["gameId"])
    if game_id not in catalog["gameId"].values:
        print(f"Game {game_id} not found. Use --list to see available games.")
        return

    game_info, game_plays = gl.load_game(games, plays, game_id)
    snapshots = gl.build_all_snapshots(game_info, game_plays)

    print(f"Loaded {game_info['visitorTeamAbbr']} @ {game_info['homeTeamAbbr']} "
          f"(Week {int(game_info['week'])}) — {len(snapshots)} plays.")
    print("Use the LEFT / RIGHT arrow keys to step through the game. Press q to quit.")

    GameViewer(game_info, snapshots)
    plt.show()


if __name__ == "__main__":
    main()
