"""Venue analytics. Match counts alone never prove a venue favours batting or bowling."""
from __future__ import annotations

import pandas as pd

from .data_cleaning import safe_divide


def venue_summary(matches: pd.DataFrame) -> pd.DataFrame:
    """Matches, average 1st-innings score, highest total and bat-first/chase win % per venue."""
    cols = ["venue", "city", "matches", "seasons_used", "avg_first_innings", "highest_total",
            "decisive", "batting_first_wins", "chasing_wins", "batting_first_win_pct"]
    if matches.empty:
        return pd.DataFrame(columns=cols)
    m = matches.copy()
    m["highest_in_match"] = m[["first_innings_runs", "second_innings_runs"]].max(axis=1)
    m["known_dec"] = m["decisive"] & m["won_batting_first"].notna()
    m["bf_win"] = m["won_batting_first"].where(m["known_dec"]).fillna(0)
    grouped = m.groupby("venue").agg(
        city=("city", lambda s: s.dropna().mode().iloc[0] if s.notna().any() else ""),
        matches=("match_id", "size"), seasons_used=("season", "nunique"),
        avg_first_innings=("first_innings_runs", "mean"), highest_total=("highest_in_match", "max"),
        decisive=("known_dec", "sum"), batting_first_wins=("bf_win", "sum")).reset_index()
    grouped["chasing_wins"] = grouped["decisive"] - grouped["batting_first_wins"]
    grouped["batting_first_win_pct"] = safe_divide(grouped["batting_first_wins"], grouped["decisive"], 100).round(1)
    grouped["avg_first_innings"] = grouped["avg_first_innings"].round(1)
    return grouped.sort_values("matches", ascending=False).reset_index(drop=True)[cols]


def venue_usage_by_season(matches: pd.DataFrame) -> pd.DataFrame:
    """Matches per venue per season (long format, chronological)."""
    if matches.empty:
        return pd.DataFrame(columns=["season", "venue", "matches"])
    return matches.groupby(["season", "venue"]).size().reset_index(name="matches").sort_values(["season", "venue"])


def highest_team_total(matches: pd.DataFrame) -> dict | None:
    """The highest single-innings total recorded in the given matches (None if unknown)."""
    if matches.empty:
        return None
    a = matches[["match_id", "batting_first", "first_innings_runs", "venue", "season"]].rename(
        columns={"batting_first": "team", "first_innings_runs": "runs"})
    b = matches[["match_id", "batting_second", "second_innings_runs", "venue", "season"]].rename(
        columns={"batting_second": "team", "second_innings_runs": "runs"})
    both = pd.concat([a, b], ignore_index=True).dropna(subset=["runs"])
    if both.empty:
        return None
    top = both.loc[both["runs"].idxmax()]
    return {"team": top["team"], "runs": int(top["runs"]), "venue": top["venue"], "season": int(top["season"])}
