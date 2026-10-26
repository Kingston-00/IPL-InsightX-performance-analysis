"""Team-level analytics built from the matches table.

Definitions
-----------
* Win:   the team won a match decided by runs or wickets (outcome == "decisive").
* Loss:  the team played a decisive match and the other team won.
* Tie:   match tied (decided by a super over). Not counted as a win or a loss.
* No result: abandoned / no winner. Not counted as a win or a loss.
* Win % (decided):  wins / (wins + losses)  - ties and no-results excluded.
* Win % (all):      wins / all matches played.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data_cleaning import safe_divide


def team_match_table(matches: pd.DataFrame) -> pd.DataFrame:
    """Return one row per team per match (each match appears twice, once per team)."""
    if matches.empty:
        return pd.DataFrame(columns=["match_id", "season", "venue", "team", "opponent", "outcome",
                                     "won", "lost", "tied", "no_result", "batted_first", "toss_won"])
    frames = []
    for team_col, opp_col in (("team1", "team2"), ("team2", "team1")):
        part = matches[["match_id", "season", "venue", "outcome", "winner", "batting_first", "toss_winner"]].copy()
        part["team"] = matches[team_col]
        part["opponent"] = matches[opp_col]
        frames.append(part)
    long = pd.concat(frames, ignore_index=True)
    decisive = long["outcome"].eq("decisive")
    long["won"] = decisive & (long["winner"] == long["team"])
    long["lost"] = decisive & (long["winner"] != long["team"])
    long["tied"] = long["outcome"].eq("tie")
    long["no_result"] = long["outcome"].eq("no result")
    long["batted_first"] = np.where(long["batting_first"].notna(), long["batting_first"] == long["team"], np.nan)
    long["toss_won"] = long["toss_winner"] == long["team"]
    return long.drop(columns=["winner", "batting_first", "toss_winner"])


def _summarize(long: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    grouped = long.groupby(by).agg(
        matches=("match_id", "size"), wins=("won", "sum"), losses=("lost", "sum"),
        ties=("tied", "sum"), no_results=("no_result", "sum")).reset_index()
    grouped["decided"] = grouped["wins"] + grouped["losses"]
    grouped["win_pct_decided"] = safe_divide(grouped["wins"], grouped["decided"], 100).round(1)
    grouped["win_pct_all"] = safe_divide(grouped["wins"], grouped["matches"], 100).round(1)
    return grouped


def team_summary(matches: pd.DataFrame) -> pd.DataFrame:
    """Matches, wins, losses, ties, no-results and win % per team."""
    out = _summarize(team_match_table(matches), ["team"])
    return out.sort_values(["wins", "win_pct_decided"], ascending=False).reset_index(drop=True)


def season_team_summary(matches: pd.DataFrame) -> pd.DataFrame:
    """Same summary per team and season (chronological)."""
    out = _summarize(team_match_table(matches), ["season", "team"])
    return out.sort_values(["season", "wins"], ascending=[True, False]).reset_index(drop=True)


def head_to_head(matches: pd.DataFrame, teams: list[str] | None = None) -> pd.DataFrame:
    """Wins of each team against each opponent (rows = team, columns = opponent)."""
    long = team_match_table(matches)
    if teams:
        long = long[long["team"].isin(teams)]
    table = _summarize(long, ["team", "opponent"])
    return table.sort_values(["team", "matches"], ascending=[True, False]).reset_index(drop=True)


def venue_team_summary(matches: pd.DataFrame) -> pd.DataFrame:
    """Team record at each venue."""
    return _summarize(team_match_table(matches), ["team", "venue"]).sort_values(
        ["team", "matches"], ascending=[True, False]).reset_index(drop=True)


def batting_first_vs_chasing(matches: pd.DataFrame) -> pd.DataFrame:
    """Each team's record when batting first and when batting second.

    Only decisive matches with known innings order are used, so
    wins / matches is a clean win percentage.
    """
    long = team_match_table(matches)
    long = long[long["outcome"].eq("decisive") & long["batted_first"].notna()].copy()
    long["role"] = np.where(long["batted_first"].astype(bool), "Batting first (defending)", "Batting second (chasing)")
    out = long.groupby(["team", "role"]).agg(matches=("match_id", "size"), wins=("won", "sum")).reset_index()
    out["win_pct"] = safe_divide(out["wins"], out["matches"], 100).round(1)
    return out


def wins_by_result_type(matches: pd.DataFrame) -> pd.DataFrame:
    """Count of matches by outcome label (runs / wickets / tie / no result)."""
    if matches.empty:
        return pd.DataFrame(columns=["result", "matches"])
    label = matches["result"].fillna(matches["outcome"]).where(matches["outcome"].ne("no result"), "no result")
    return label.value_counts().rename_axis("result").reset_index(name="matches")
