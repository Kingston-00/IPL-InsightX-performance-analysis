"""Tiny SYNTHETIC datasets for unit tests only. They are NOT real IPL results.

Matches (4):
  1  2020  A v B  toss A (bat)   winner A by runs     (A bats first)
  2  2020  A v B  toss B (field) winner A by wickets  (B bats first)
  3  2021  B v C  toss C (field) tie, super-over winner B
  4  2021  A v C  toss A (bat)   no result, no winner
"""
import pandas as pd

RAW_MATCHES = pd.DataFrame({
    "id": ["1", "2", "3", "4"],
    "season": ["2020", "2020", "2021", "2021"],
    "date": ["2020-04-01", "2020-04-02", "2021-04-01", "2021-04-02"],
    "team1": ["A", "A", "B", "A"], "team2": ["B", "B", "C", "C"],
    "toss_winner": ["A", "B", "C", "A"], "toss_decision": ["bat", "field", "field", "bat"],
    "winner": ["A", "A", "B", None], "result": ["runs", "wickets", "tie", "no result"],
    "result_margin": ["10", "5", None, None], "venue": ["V1", "V1", "V2", "V2"],
    "player_of_match": ["P1", "P2", "P1", None], "match_type": ["League"] * 4,
})


def _ball(match_id, inning, over, ball, batting, bowling, batter, bowler, bat_runs=0, extra=0, extras_type=None,
          wicket=0, dismissed=None, kind=None):
    return {"match_id": str(match_id), "inning": str(inning), "batting_team": batting, "bowling_team": bowling,
            "over": str(over), "ball": str(ball), "batter": batter, "bowler": bowler, "non_striker": "N",
            "batsman_runs": str(bat_runs), "extra_runs": str(extra), "total_runs": str(bat_runs + extra),
            "extras_type": extras_type, "is_wicket": str(wicket), "player_dismissed": dismissed, "dismissal_kind": kind}


# Match 1, inning 1 (A bats): Bat1 hits 4, 6, a wide (1 extra), a leg-bye (1), then is bowled; Bat2 scores 1.
# Match 1, inning 2 (B bats): Bat3 is run out (not credited to bowler) on ball 1, and scores 2 on ball 2.
RAW_DELIVERIES = pd.DataFrame([
    _ball(1, 1, 0, 1, "A", "B", "Bat1", "Bowl1", bat_runs=4),
    _ball(1, 1, 0, 2, "A", "B", "Bat1", "Bowl1", bat_runs=6),
    _ball(1, 1, 0, 3, "A", "B", "Bat1", "Bowl1", extra=1, extras_type="wides"),
    _ball(1, 1, 0, 3, "A", "B", "Bat1", "Bowl1", extra=1, extras_type="legbyes"),
    _ball(1, 1, 0, 4, "A", "B", "Bat1", "Bowl1", wicket=1, dismissed="Bat1", kind="bowled"),
    _ball(1, 1, 0, 5, "A", "B", "Bat2", "Bowl1", bat_runs=1),
    _ball(1, 2, 0, 1, "B", "A", "Bat3", "Bowl2", wicket=1, dismissed="Bat3", kind="run out"),
    _ball(1, 2, 0, 2, "B", "A", "Bat4", "Bowl2", bat_runs=2),
    _ball(1, 3, 0, 1, "B", "A", "Bat4", "Bowl2", bat_runs=6),      # super-over row: must be excluded from stats
])
