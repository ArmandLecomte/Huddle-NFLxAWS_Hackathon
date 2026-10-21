"""
game_logic.py
--------------
Loads NFL play data for a single game and turns each play into a
narrative "snapshot": the game state before the snap, the decision the
offense/defense made, the outcome, and a plain-language explanation of
*why* those choices make sense.

Important note about the data:
    The NFL "plays.csv" used here is the pass-rush dataset, so every row
    is a quarterback DROPBACK (a passing play). Running plays, kicks and
    special teams are not in the data. The simulation therefore walks
    through the *key passing plays* of a game in order, which is still a
    great way to see how an offense attacks and how a defense responds.
"""

from __future__ import annotations

import os
import pandas as pd


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

FIELD_LENGTH = 120  # yards including both end zones (0-10 and 110-120)
PLAYABLE_START = 10
PLAYABLE_END = 110


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data():
    """Load the four core CSVs. Returns (games, plays, players)."""
    games = pd.read_csv(os.path.join(DATA_DIR, "games.csv"))
    plays = pd.read_csv(os.path.join(DATA_DIR, "plays.csv"))
    players = pd.read_csv(os.path.join(DATA_DIR, "players.csv"))
    return games, plays, players


def list_games(games, plays):
    """Return a dataframe of games with play counts, nicely labelled."""
    counts = plays.groupby("gameId").size().rename("num_plays").reset_index()
    g = games.merge(counts, on="gameId", how="inner")
    g["label"] = (
        g["visitorTeamAbbr"] + " @ " + g["homeTeamAbbr"]
        + "  (Week " + g["week"].astype(str) + ", " + g["gameDate"] + ")"
    )
    return g.sort_values("gameId").reset_index(drop=True)


def load_game(games, plays, game_id):
    """Return (game_info_row, plays_for_game sorted by playId)."""
    info = games[games["gameId"] == game_id].iloc[0]
    gp = plays[plays["gameId"] == game_id].sort_values("playId").reset_index(drop=True)
    return info, gp


# ---------------------------------------------------------------------------
# Human-readable helpers
# ---------------------------------------------------------------------------
_ORDINAL = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}

_COVERAGE_PLAIN = {
    "Cover-0": "all-out man coverage with no deep safety (usually a blitz)",
    "Cover-1": "man coverage with one deep safety helping over the top",
    "Cover-2": "two deep safeties splitting the deep field (zone)",
    "2-Man": "two deep safeties with man coverage underneath",
    "Cover-3": "three deep defenders — a safe zone against deep passes",
    "Quarters": "four deep defenders — very hard to beat deep",
    "Cover-6": "a split-field zone, quarters on one side, cover-2 on the other",
    "Bracket": "two defenders double-teaming one dangerous receiver",
    "Goal Line": "a packed goal-line defense to stop a score",
    "Red Zone": "a tightened red-zone coverage near the end zone",
    "Prevent": "a deep 'prevent' shell to stop big plays late in a half",
    "Miscellaneous": "an unconventional coverage",
}

_FORMATION_PLAIN = {
    "SHOTGUN": "Shotgun (QB stands back ~5 yards, ready to pass)",
    "EMPTY": "Empty (no running backs — pure passing look)",
    "SINGLEBACK": "Singleback (one running back — balanced look)",
    "I_FORM": "I-Formation (two backs stacked — a run-heavy look)",
    "PISTOL": "Pistol (QB a few yards back with a back behind him)",
    "JUMBO": "Jumbo (extra linemen/tight ends — short-yardage power)",
    "WILDCAT": "Wildcat (a non-QB takes the snap — a trick look)",
}

_RESULT_PLAIN = {
    "C": "Complete pass",
    "I": "Incomplete pass",
    "S": "Sack",
    "IN": "Interception",
    "R": "QB scramble",
}


def ordinal_down(down):
    try:
        return _ORDINAL.get(int(down), f"{int(down)}th")
    except (ValueError, TypeError):
        return "?"


def describe_formation(formation):
    if not isinstance(formation, str):
        return "an unlisted formation"
    return _FORMATION_PLAIN.get(formation, formation.title())


def describe_coverage(coverage):
    if not isinstance(coverage, str):
        return "an unlisted coverage"
    return _COVERAGE_PLAIN.get(coverage, coverage)


# ---------------------------------------------------------------------------
# The core: build a narrative snapshot for one play
# ---------------------------------------------------------------------------
def build_snapshot(play, game_info, prev_play=None):
    """
    Turn a single play row into a dict describing the situation, the
    decision, the outcome, and an explanation of the reasoning.
    """
    offense = play["possessionTeam"]
    defense = play["defensiveTeam"]
    down = play["down"]
    ytg = play["yardsToGo"]
    quarter = play["quarter"]
    clock = play["gameClock"]
    home = game_info["homeTeamAbbr"]
    visitor = game_info["visitorTeamAbbr"]

    # Scores are stored from the home/visitor perspective
    home_score = int(play["preSnapHomeScore"])
    vis_score = int(play["preSnapVisitorScore"])
    off_score = home_score if offense == home else vis_score
    def_score = vis_score if offense == home else home_score
    score_diff = off_score - def_score

    result_code = play.get("passResult")
    result_text = _RESULT_PLAIN.get(result_code, "Pass play")
    gained = play.get("playResult", 0)
    gained = 0 if pd.isna(gained) else int(gained)
    play_action = bool(play.get("pff_playAction", 0) == 1)

    # ---- Situation line ----
    situation = (
        f"Q{int(quarter)}  {clock}   |   "
        f"{ordinal_down(down)} & {int(ytg)}   |   "
        f"{offense} ball"
    )
    score_line = f"{visitor} {vis_score}  -  {home_score} {home}"

    # ---- Decision reasoning (why this call makes sense) ----
    reasons = []

    # Down & distance logic
    if down == 1:
        reasons.append(
            "It's 1st down — the offense has the whole playbook available and "
            "is looking to gain chunk yardage to set up an easy 2nd down."
        )
    elif down == 2:
        if ytg <= 3:
            reasons.append(
                f"2nd & short ({int(ytg)}): the offense is in great shape and can "
                "take a shot downfield knowing a short gain still leaves a makeable 3rd down."
            )
        elif ytg >= 8:
            reasons.append(
                f"2nd & long ({int(ytg)}): they need a solid gain to avoid a difficult 3rd down."
            )
        else:
            reasons.append(
                f"2nd & {int(ytg)}: a balanced down — they want to move the chains and stay ahead of schedule."
            )
    elif down == 3:
        if ytg <= 3:
            reasons.append(
                f"3rd & short ({int(ytg)}): a conversion keeps the drive alive, so the defense "
                "crowds the line and the offense needs a quick, reliable throw."
            )
        else:
            reasons.append(
                f"3rd & long ({int(ytg)}): this is a passing down — the defense knows it, so the "
                "offense must beat tight coverage to move the chains."
            )
    elif down == 4:
        reasons.append(
            f"4th & {int(ytg)}: a gutsy decision to go for it. Failing hands the ball to the "
            "other team right here, so the reward must be worth the risk."
        )

    # Field position
    yl_side = play.get("yardlineSide")
    yl_num = play.get("yardlineNumber")
    if isinstance(yl_side, str) and not pd.isna(yl_num):
        if yl_side == offense:
            reasons.append(
                f"The ball is on their own {int(yl_num)} — deep in their half, so a turnover "
                "here would be costly; ball security matters."
            )
        else:
            if yl_num <= 20:
                reasons.append(
                    f"They're in the red zone (opponent's {int(yl_num)}) — the field is short, "
                    "windows are tight, and a touchdown is the goal."
                )
            else:
                reasons.append(
                    f"They've crossed midfield (opponent's {int(yl_num)}) — in scoring range, "
                    "they can be a bit more aggressive."
                )

    # Formation intent
    formation = play.get("offenseFormation")
    if isinstance(formation, str):
        reasons.append(f"Offense lines up in {describe_formation(formation)}.")

    # Play action
    if play_action:
        reasons.append(
            "They use play action — faking a handoff to freeze the defense and open "
            "up receivers downfield."
        )

    # Score/game context
    if quarter >= 4:
        if score_diff <= -9:
            reasons.append(
                "Trailing by two scores late — the offense is in catch-up mode and must take chances."
            )
        elif score_diff >= 9:
            reasons.append(
                "Leading comfortably late — they'll play safer to protect the lead and run clock."
            )
        elif abs(score_diff) <= 8:
            reasons.append("A one-score game in the 4th quarter — every play is high leverage.")

    # Defense's answer
    coverage = play.get("pff_passCoverage")
    cov_type = play.get("pff_passCoverageType")
    defense_note = None
    if isinstance(coverage, str):
        defense_note = (
            f"Defense responds with {coverage} — {describe_coverage(coverage)}."
        )
        if coverage in ("Cover-0", "Cover-1") and down == 3 and ytg >= 7:
            defense_note += (
                " On 3rd & long, man coverage like this is aggressive — if the pass "
                "rush doesn't get home, a receiver can win one-on-one."
            )
        elif coverage in ("Cover-3", "Quarters") and gained >= 15:
            defense_note += (
                " Even a deep zone got beaten here — the QB found a seam between defenders."
            )

    # ---- Outcome explanation ----
    if result_code == "C":
        if gained >= int(ytg):
            outcome = (
                f"[COMPLETE] {gained} yards — that's a FIRST DOWN. The drive continues "
                "with a fresh set of downs."
            )
        elif gained >= 15:
            outcome = f"[COMPLETE] a big {gained}-yard gain — a chunk play that flips field position."
        elif gained > 0:
            outcome = f"[COMPLETE] {gained} yards — a positive gain, but short of the first-down marker."
        else:
            outcome = "[COMPLETE] but for no gain."
    elif result_code == "I":
        outcome = "[INCOMPLETE] no gain, the clock stops, and the down is used up."
    elif result_code == "S":
        outcome = (
            f"[SACK] the defense got to the QB for a loss of {abs(gained)} yards. "
            "The protection broke down or the rush won fast."
        )
    elif result_code == "IN":
        outcome = (
            "[INTERCEPTION] a turnover! The defense takes the ball away; a drive-killing, "
            "potentially game-changing mistake."
        )
    elif result_code == "R":
        outcome = (
            f"[SCRAMBLE] the QB ran for {gained} yards — with no receiver open, he took off and "
            "picked up what he could."
        )
    else:
        outcome = f"Play result: {gained} yards."

    return {
        "offense": offense,
        "defense": defense,
        "down": down,
        "ytg": ytg,
        "quarter": quarter,
        "clock": clock,
        "situation": situation,
        "score_line": score_line,
        "home": home,
        "visitor": visitor,
        "home_score": home_score,
        "vis_score": vis_score,
        "yl_side": yl_side,
        "yl_num": yl_num,
        "absolute_yardline": play.get("absoluteYardlineNumber"),
        "formation": formation,
        "coverage": coverage,
        "cov_type": cov_type,
        "play_action": play_action,
        "result_code": result_code,
        "result_text": result_text,
        "gained": gained,
        "reasons": reasons,
        "defense_note": defense_note,
        "outcome": outcome,
        "description": play.get("playDescription", ""),
    }


def build_all_snapshots(game_info, game_plays):
    """Build a list of snapshots for every play in the game, in order."""
    snaps = []
    prev = None
    for _, play in game_plays.iterrows():
        snaps.append(build_snapshot(play, game_info, prev))
        prev = play
    return snaps
