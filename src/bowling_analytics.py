"""Bowling statistics from ball-by-ball data.

Definitions
-----------
* Legal balls: every delivery except wides and no-balls.
* Runs conceded: runs off the bat + wides + no-ball runs. Byes, leg-byes and
  penalty runs are NOT charged to the bowler.
* Wickets: bowled, caught, caught and bowled, lbw, stumped, hit wicket.
  Run outs, obstructing the field, retired out/hurt are not credited to the bowler.
* Economy:       runs conceded x 6 / legal balls.
* Average:       runs conceded / wickets.
* Strike rate:   legal balls / wickets.
Only regular innings are used - super overs are excluded.
"""
from __future__ import annotations

import pandas as pd

from .batting_analytics import regular_deliveries
from .data_cleaning import safe_divide

BOWLING_COLUMNS = ["bowler", "matches", "legal_balls", "overs", "runs_conceded", "wickets",
                   "economy", "average", "strike_rate"]


def _finish(stats: pd.DataFrame) -> pd.DataFrame:
    stats["overs"] = (stats["legal_balls"] // 6 + (stats["legal_balls"] % 6) / 10).round(1)   # 12.3 = 12 overs 3 balls
    stats["economy"] = safe_divide(stats["runs_conceded"], stats["legal_balls"], 6).round(2)
    stats["average"] = safe_divide(stats["runs_conceded"], stats["wickets"]).round(2)
    stats["strike_rate"] = safe_divide(stats["legal_balls"], stats["wickets"]).round(2)
    return stats


def bowling_stats(deliveries: pd.DataFrame, min_balls: int = 0, by: str = "bowler") -> pd.DataFrame:
    """Bowling table grouped by ``by`` (default one row per bowler)."""
    reg = regular_deliveries(deliveries)
    if reg.empty:
        return pd.DataFrame(columns=BOWLING_COLUMNS)
    reg = reg.assign(bowler=reg["bowler"].astype(str), legal=reg["is_legal_ball"].astype(int))
    stats = reg.groupby(by, observed=True).agg(
        matches=("match_id", "nunique"), legal_balls=("legal", "sum"),
        runs_conceded=("bowler_runs", "sum"), wickets=("is_bowler_wicket", "sum")).reset_index()
    stats = _finish(stats)
    stats = stats[stats["legal_balls"] >= min_balls]
    return stats.sort_values(["wickets", "economy"], ascending=[False, True]).reset_index(drop=True)


def dismissal_types(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Count of wickets (all dismissal kinds, regular innings) by dismissal type."""
    reg = regular_deliveries(deliveries)
    reg = reg[reg["is_wicket"].eq(1) & reg["dismissal_kind"].notna()]
    if reg.empty:
        return pd.DataFrame(columns=["dismissal_kind", "wickets", "credited_to_bowler"])
    out = reg["dismissal_kind"].astype(str).value_counts().rename_axis("dismissal_kind").reset_index(name="wickets")
    out["credited_to_bowler"] = out["dismissal_kind"].isin(reg.loc[reg["is_bowler_wicket"], "dismissal_kind"].astype(str).unique())
    return out


def team_bowling_summary(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Wickets (credited to bowlers), runs conceded and economy per bowling team."""
    reg = regular_deliveries(deliveries)
    if reg.empty:
        return pd.DataFrame(columns=["team", "wickets", "runs_conceded", "legal_balls", "economy"])
    reg = reg.assign(bowling_team=reg["bowling_team"].astype(str), legal=reg["is_legal_ball"].astype(int))
    out = reg.groupby("bowling_team").agg(
        wickets=("is_bowler_wicket", "sum"), runs_conceded=("bowler_runs", "sum"),
        legal_balls=("legal", "sum")).reset_index().rename(columns={"bowling_team": "team"})
    out["economy"] = safe_divide(out["runs_conceded"], out["legal_balls"], 6).round(2)
    return out.sort_values("wickets", ascending=False).reset_index(drop=True)


def bowling_by_season(deliveries: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Season-wise wickets, runs conceded and economy (all bowlers combined)."""
    reg = regular_deliveries(deliveries)
    if reg.empty:
        return pd.DataFrame(columns=["season", "wickets", "runs_conceded", "legal_balls", "economy"])
    reg = reg.assign(season=reg["match_id"].map(matches.set_index("match_id")["season"]),
                     legal=reg["is_legal_ball"].astype(int)).dropna(subset=["season"])
    out = reg.groupby("season").agg(wickets=("is_bowler_wicket", "sum"), runs_conceded=("bowler_runs", "sum"),
                                    legal_balls=("legal", "sum")).reset_index()
    out["season"] = out["season"].astype(int)
    out["economy"] = safe_divide(out["runs_conceded"], out["legal_balls"], 6).round(2)
    return out


def bowling_by_venue(deliveries: pd.DataFrame, matches: pd.DataFrame, bowlers: list[str] | None = None) -> pd.DataFrame:
    """Bowling figures per venue (optionally for selected bowlers)."""
    reg = regular_deliveries(deliveries)
    if bowlers:
        reg = reg[reg["bowler"].isin(bowlers)]
    if reg.empty:
        return pd.DataFrame(columns=["venue", "matches", "legal_balls", "runs_conceded", "wickets", "economy"])
    reg = reg.assign(venue=reg["match_id"].map(matches.set_index("match_id")["venue"]),
                     legal=reg["is_legal_ball"].astype(int)).dropna(subset=["venue"])
    out = reg.groupby("venue").agg(matches=("match_id", "nunique"), legal_balls=("legal", "sum"),
                                   runs_conceded=("bowler_runs", "sum"), wickets=("is_bowler_wicket", "sum")).reset_index()
    out["economy"] = safe_divide(out["runs_conceded"], out["legal_balls"], 6).round(2)
    return out.sort_values("wickets", ascending=False).reset_index(drop=True)
