"""Toss and chase/defend analytics.

Percentages use DECISIVE matches only (won by runs or wickets). Ties and
no-result matches are excluded from the denominator, and the sample size is
always returned next to the percentage.
These numbers describe association, not cause.
"""
from __future__ import annotations

import pandas as pd

from .data_cleaning import safe_divide


def decisive_matches(matches: pd.DataFrame) -> pd.DataFrame:
    return matches[matches["decisive"]]


def toss_win_match_win(matches: pd.DataFrame) -> dict:
    """How often the toss winner also won the match (decisive matches only)."""
    dec = decisive_matches(matches)
    n = len(dec)
    wins = int((dec["toss_winner"] == dec["winner"]).sum())
    return {"decisive_matches": n, "toss_winner_won": wins,
            "pct": safe_divide(wins, n, 100)}


def toss_decision_outcomes(matches: pd.DataFrame) -> pd.DataFrame:
    """For each toss decision (bat / field): times chosen and how often the toss winner won."""
    dec = decisive_matches(matches)
    if dec.empty:
        return pd.DataFrame(columns=["toss_decision", "matches", "toss_winner_won", "toss_winner_lost", "win_pct"])
    won = dec["toss_winner"] == dec["winner"]
    out = (dec.assign(toss_winner_won=won).groupby("toss_decision")
           .agg(matches=("match_id", "size"), toss_winner_won=("toss_winner_won", "sum")).reset_index())
    out["toss_winner_lost"] = out["matches"] - out["toss_winner_won"]
    out["win_pct"] = safe_divide(out["toss_winner_won"], out["matches"], 100).round(1)
    return out


def toss_decisions_by_season(matches: pd.DataFrame) -> pd.DataFrame:
    """Toss decisions per season (all matches that have a recorded toss decision)."""
    if matches.empty:
        return pd.DataFrame(columns=["season", "toss_decision", "matches", "share_pct"])
    out = matches.dropna(subset=["toss_decision"]).groupby(["season", "toss_decision"]).size().reset_index(name="matches")
    out["share_pct"] = (out["matches"] * 100 / out.groupby("season")["matches"].transform("sum")).round(1)
    return out


def toss_by_venue(matches: pd.DataFrame, min_matches: int = 1) -> pd.DataFrame:
    """Per venue: matches, % of toss winners choosing to field, % toss winners winning."""
    if matches.empty:
        return pd.DataFrame(columns=["venue", "matches", "field_first_pct", "decisive", "toss_winner_won_pct"])
    base = matches.groupby("venue").agg(
        matches=("match_id", "size"),
        field_first=("toss_decision", lambda s: (s == "field").sum())).reset_index()
    dec = decisive_matches(matches)
    d = dec.assign(tw=dec["toss_winner"] == dec["winner"]).groupby("venue").agg(
        decisive=("match_id", "size"), toss_winner_won=("tw", "sum")).reset_index()
    out = base.merge(d, on="venue", how="left").fillna({"decisive": 0, "toss_winner_won": 0})
    out["field_first_pct"] = safe_divide(out["field_first"], out["matches"], 100).round(1)
    out["toss_winner_won_pct"] = safe_divide(out["toss_winner_won"], out["decisive"], 100).round(1)
    out = out[out["matches"] >= min_matches]
    return out.sort_values("matches", ascending=False).reset_index(drop=True)


def chase_vs_defend(matches: pd.DataFrame) -> dict:
    """Overall: decisive matches won by the team batting first vs the chasing team."""
    dec = decisive_matches(matches).dropna(subset=["won_batting_first"])
    n = len(dec)
    first_wins = int(dec["won_batting_first"].sum())
    return {"decisive_matches": n, "won_batting_first": first_wins, "won_chasing": n - first_wins,
            "batting_first_pct": safe_divide(first_wins, n, 100),
            "chasing_pct": safe_divide(n - first_wins, n, 100)}


def chase_defend_by_team(matches: pd.DataFrame) -> pd.DataFrame:
    """Per team: matches and wins as the chasing team and as the defending (batting-first) team."""
    from .team_analytics import batting_first_vs_chasing
    table = batting_first_vs_chasing(matches)
    if table.empty:
        return pd.DataFrame(columns=["team", "role", "matches", "wins", "win_pct"])
    return table


def toss_decision_vs_batting_first(matches: pd.DataFrame) -> pd.DataFrame:
    """Check: does the toss decision agree with who actually batted first?

    Counts matches by (toss winner chose bat/field) and whether the toss winner
    really batted first. Mismatches would indicate a data problem.
    """
    known = matches.dropna(subset=["batting_first"])
    if known.empty:
        return pd.DataFrame(columns=["toss_decision", "toss_winner_batted_first", "matches"])
    batted_first = known["toss_winner"] == known["batting_first"]
    return (known.assign(toss_winner_batted_first=batted_first)
            .groupby(["toss_decision", "toss_winner_batted_first"]).size().reset_index(name="matches"))
