"""Batting statistics from ball-by-ball data.

Definitions
-----------
* Runs:        sum of ``batsman_runs`` (runs off the bat; extras excluded).
* Balls faced: every delivery except wides and penalty rows (a no-ball counts).
* Strike rate: runs / balls faced x 100.
* Innings:     distinct (match, inning) in which the player faced a ball or was dismissed.
* Dismissal:   a wicket where the player is ``player_dismissed``, except "retired hurt".
* Average:     runs / dismissals (undefined when the player was never dismissed).
* Fours/sixes: deliveries where batsman_runs is exactly 4 or 6.
  (The data cannot separate a run-four from a boundary-four.)
Only regular innings are used - super overs are excluded.
"""
from __future__ import annotations

import pandas as pd

from .data_cleaning import safe_divide


def regular_deliveries(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Deliveries from innings 1 and 2 only."""
    return deliveries[~deliveries["is_super_over"]]


def batting_innings(deliveries: pd.DataFrame) -> pd.DataFrame:
    """One row per batter innings: runs, balls, fours, sixes, dismissed."""
    reg = regular_deliveries(deliveries)
    if reg.empty:
        return pd.DataFrame(columns=["match_id", "inning", "batter", "batting_team", "runs", "balls",
                                     "fours", "sixes", "dismissed"])
    keys = ["match_id", "inning", "batter"]
    work = reg.assign(
        balls=reg["is_ball_faced"].astype(int),
        fours=(reg["batsman_runs"] == 4).astype(int),
        sixes=(reg["batsman_runs"] == 6).astype(int))
    inn = (work.groupby(keys, observed=True)
           .agg(batting_team=("batting_team", "first"), runs=("batsman_runs", "sum"), balls=("balls", "sum"),
                fours=("fours", "sum"), sixes=("sixes", "sum"))
           .reset_index())
    inn["batter"] = inn["batter"].astype(str)
    inn["batting_team"] = inn["batting_team"].astype(str)

    out = reg[reg["is_dismissal"] & reg["player_dismissed"].notna()]
    out = (out.assign(batter=out["player_dismissed"].astype(str), batting_team=out["batting_team"].astype(str))
           [["match_id", "inning", "batter", "batting_team"]].drop_duplicates(["match_id", "inning", "batter"]))
    out["dismissed"] = True
    inn = inn.merge(out[["match_id", "inning", "batter", "dismissed"]], on=keys, how="outer")
    # A batter dismissed without facing a ball (e.g. run out at the non-striker's end) still batted.
    missing_team = inn["batting_team"].isna()
    if missing_team.any():
        inn = inn.merge(out[keys + ["batting_team"]].rename(columns={"batting_team": "bt2"}), on=keys, how="left")
        inn["batting_team"] = inn["batting_team"].fillna(inn["bt2"])
        inn = inn.drop(columns="bt2")
    inn[["runs", "balls", "fours", "sixes"]] = inn[["runs", "balls", "fours", "sixes"]].fillna(0).astype(int)
    inn["dismissed"] = inn["dismissed"].eq(True)
    return inn


def batting_stats(deliveries: pd.DataFrame, innings: pd.DataFrame | None = None, min_balls: int = 0) -> pd.DataFrame:
    """Career-style batting table for the deliveries given (apply filters first)."""
    inn = batting_innings(deliveries) if innings is None else innings
    cols = ["batter", "innings", "runs", "balls", "fours", "sixes", "dismissals", "highest_score",
            "average", "strike_rate"]
    if inn.empty:
        return pd.DataFrame(columns=cols)
    stats = inn.groupby("batter").agg(
        innings=("match_id", "size"), runs=("runs", "sum"), balls=("balls", "sum"),
        fours=("fours", "sum"), sixes=("sixes", "sum"), dismissals=("dismissed", "sum"),
        highest_score=("runs", "max")).reset_index()
    stats["average"] = safe_divide(stats["runs"], stats["dismissals"]).round(2)
    stats["strike_rate"] = safe_divide(stats["runs"], stats["balls"], 100).round(2)
    stats = stats[stats["balls"] >= min_balls]
    return stats.sort_values("runs", ascending=False).reset_index(drop=True)[cols]


def runs_by_over(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Total runs and run rate for each over number (1-20), all teams."""
    reg = regular_deliveries(deliveries)
    if reg.empty:
        return pd.DataFrame(columns=["over", "runs", "legal_balls", "run_rate"])
    out = reg.groupby("over").agg(runs=("total_runs", "sum"), legal_balls=("is_legal_ball", "sum")).reset_index()
    out["over"] = out["over"] + 1          # the file counts overs from 0
    out["run_rate"] = safe_divide(out["runs"], out["legal_balls"], 6).round(2)
    return out


def runs_distribution(deliveries: pd.DataFrame) -> pd.DataFrame:
    """How many deliveries produced 0,1,2,3,4,5,6 runs off the bat (balls faced only)."""
    reg = regular_deliveries(deliveries)
    reg = reg[reg["is_ball_faced"]]
    if reg.empty:
        return pd.DataFrame(columns=["runs_off_bat", "deliveries", "share_pct"])
    out = reg["batsman_runs"].value_counts().sort_index().rename_axis("runs_off_bat").reset_index(name="deliveries")
    out["share_pct"] = (out["deliveries"] * 100 / out["deliveries"].sum()).round(2)
    return out


def team_batting_summary(deliveries: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Runs, wickets lost and run rate per batting team."""
    reg = regular_deliveries(deliveries)
    if reg.empty:
        return pd.DataFrame(columns=["team", "innings", "runs", "wickets_lost", "run_rate", "avg_innings_score"])
    reg = reg.assign(batting_team=reg["batting_team"].astype(str))
    out = reg.groupby("batting_team").agg(
        runs=("total_runs", "sum"), wickets_lost=("is_dismissal", "sum"),
        legal_balls=("is_legal_ball", "sum")).reset_index().rename(columns={"batting_team": "team"})
    innings_count = reg.drop_duplicates(["match_id", "inning"]).groupby("batting_team").size()
    out["innings"] = out["team"].map(innings_count)
    out["run_rate"] = safe_divide(out["runs"], out["legal_balls"], 6).round(2)
    out["avg_innings_score"] = safe_divide(out["runs"], out["innings"]).round(1)
    return out.drop(columns="legal_balls").sort_values("runs", ascending=False).reset_index(drop=True)


def season_runs(deliveries: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Total runs, innings, average innings score and run rate per season."""
    reg = regular_deliveries(deliveries)
    if reg.empty:
        return pd.DataFrame(columns=["season", "runs", "innings", "avg_innings_score", "run_rate"])
    reg = reg.assign(season=reg["match_id"].map(matches.set_index("match_id")["season"]))
    reg = reg.dropna(subset=["season"])
    out = reg.groupby("season").agg(runs=("total_runs", "sum"), legal_balls=("is_legal_ball", "sum")).reset_index()
    innings = reg.drop_duplicates(["match_id", "inning"]).groupby("season").size()
    out["innings"] = out["season"].map(innings)
    out["avg_innings_score"] = safe_divide(out["runs"], out["innings"]).round(1)
    out["run_rate"] = safe_divide(out["runs"], out["legal_balls"], 6).round(2)
    out["season"] = out["season"].astype(int)
    return out.drop(columns="legal_balls")
