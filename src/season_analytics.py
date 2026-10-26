"""Season-level analytics (always in chronological order)."""
from __future__ import annotations

import pandas as pd

from .batting_analytics import batting_stats
from .bowling_analytics import bowling_stats
from .team_analytics import season_team_summary


def season_overview(matches: pd.DataFrame) -> pd.DataFrame:
    """Matches, teams, venues and average first-innings score per season."""
    cols = ["season", "matches", "teams", "venues", "avg_first_innings"]
    if matches.empty:
        return pd.DataFrame(columns=cols)
    teams = pd.concat([matches[["season", "team1"]].rename(columns={"team1": "team"}),
                       matches[["season", "team2"]].rename(columns={"team2": "team"})])
    out = matches.groupby("season").agg(
        matches=("match_id", "size"), venues=("venue", "nunique"),
        avg_first_innings=("first_innings_runs", "mean")).reset_index()
    out["teams"] = out["season"].map(teams.groupby("season")["team"].nunique())
    out["avg_first_innings"] = out["avg_first_innings"].round(1)
    return out.sort_values("season").reset_index(drop=True)[cols]


def season_team_participation(matches: pd.DataFrame) -> pd.DataFrame:
    """Teams that played in each season (long format: season, team, matches)."""
    return season_team_summary(matches)[["season", "team", "matches"]] if not matches.empty else pd.DataFrame(
        columns=["season", "team", "matches"])


def most_successful_team(matches: pd.DataFrame) -> pd.DataFrame:
    """Team with the most wins in each season (ties in wins are all listed)."""
    cols = ["season", "team", "wins", "matches", "win_pct_decided"]
    if matches.empty:
        return pd.DataFrame(columns=cols)
    s = season_team_summary(matches)
    best = s.groupby("season")["wins"].transform("max")
    return s[(s["wins"] == best) & (best > 0)][cols].sort_values("season").reset_index(drop=True)


def season_champions(matches: pd.DataFrame) -> pd.DataFrame:
    """Winner of the match labelled 'Final' in each season, when present in the data."""
    final = matches[matches["match_type"].eq("Final")]
    return final[["season", "winner"]].rename(columns={"winner": "champion"}).sort_values("season").reset_index(drop=True)


def season_leaders(matches: pd.DataFrame, deliveries: pd.DataFrame) -> pd.DataFrame:
    """Top run scorer and top wicket taker for each season."""
    cols = ["season", "top_run_scorer", "runs", "top_wicket_taker", "wickets"]
    if matches.empty or deliveries is None or deliveries.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    for season in sorted(matches["season"].unique()):
        ids = matches.loc[matches["season"] == season, "match_id"]
        d = deliveries[deliveries["match_id"].isin(ids)]
        bat = batting_stats(d)
        bowl = bowling_stats(d)
        rows.append({
            "season": season,
            "top_run_scorer": bat.iloc[0]["batter"] if not bat.empty else None,
            "runs": int(bat.iloc[0]["runs"]) if not bat.empty else None,
            "top_wicket_taker": bowl.iloc[0]["bowler"] if not bowl.empty and bowl.iloc[0]["wickets"] > 0 else None,
            "wickets": int(bowl.iloc[0]["wickets"]) if not bowl.empty and bowl.iloc[0]["wickets"] > 0 else None,
        })
    return pd.DataFrame(rows, columns=cols)


def season_player_of_match(matches: pd.DataFrame) -> pd.DataFrame:
    """Player of the Match awards per season and player."""
    if matches.empty:
        return pd.DataFrame(columns=["season", "player", "awards"])
    out = (matches.dropna(subset=["player_of_match"]).groupby(["season", "player_of_match"]).size()
           .reset_index(name="awards").rename(columns={"player_of_match": "player"}))
    return out.sort_values(["season", "awards"], ascending=[True, False]).reset_index(drop=True)
