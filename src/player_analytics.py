"""Player-level analytics: profiles, comparison and Player of the Match awards."""
from __future__ import annotations

import pandas as pd

from .batting_analytics import batting_stats
from .bowling_analytics import bowling_stats


def player_of_match_counts(matches: pd.DataFrame) -> pd.DataFrame:
    """Number of Player of the Match awards per player (matches with an award only)."""
    if matches.empty or "player_of_match" not in matches.columns:
        return pd.DataFrame(columns=["player", "awards"])
    counts = matches["player_of_match"].dropna().value_counts()
    return counts.rename_axis("player").reset_index(name="awards")


def player_names(deliveries: pd.DataFrame, matches: pd.DataFrame | None = None) -> list[str]:
    """Sorted list of every player seen as batter, non-striker, bowler or award winner."""
    names: set[str] = set()
    if deliveries is not None and not deliveries.empty:
        for col in ("batter", "bowler", "non_striker"):
            names.update(deliveries[col].dropna().astype(str).unique())
    if matches is not None and not matches.empty:
        names.update(matches["player_of_match"].dropna().astype(str).unique())
    return sorted(names)


def player_profile(player: str, deliveries: pd.DataFrame, matches: pd.DataFrame) -> dict:
    """Batting, bowling and award numbers for one player (None where unavailable).

    A statistic is None when the player has no data for it (for example a
    batting average for a player who was never dismissed).
    """
    # Computed on all given deliveries (not just the player's rows) so that
    # dismissals suffered as the non-striker are included.
    bat = batting_stats(deliveries)
    bat = bat[bat["batter"] == player]
    bowl = bowling_stats(deliveries)
    bowl = bowl[bowl["bowler"] == player]
    awards = player_of_match_counts(matches)
    awards = awards[awards["player"] == player]

    def pick(frame: pd.DataFrame, col: str):
        if frame.empty:
            return None
        value = frame.iloc[0][col]
        return None if pd.isna(value) else value

    return {
        "innings": pick(bat, "innings"), "runs": pick(bat, "runs"), "balls_faced": pick(bat, "balls"),
        "fours": pick(bat, "fours"), "sixes": pick(bat, "sixes"), "highest_score": pick(bat, "highest_score"),
        "average": pick(bat, "average"), "strike_rate": pick(bat, "strike_rate"),
        "wickets": pick(bowl, "wickets"), "legal_balls": pick(bowl, "legal_balls"),
        "runs_conceded": pick(bowl, "runs_conceded"), "economy": pick(bowl, "economy"),
        "bowling_average": pick(bowl, "average"), "bowling_strike_rate": pick(bowl, "strike_rate"),
        "awards": int(awards.iloc[0]["awards"]) if not awards.empty else 0,
    }


def compare_players(players: list[str], deliveries: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """One row per player with the profile numbers, ready for a table or chart."""
    bat = batting_stats(deliveries).set_index("batter")
    bowl = bowling_stats(deliveries).set_index("bowler")
    awards = player_of_match_counts(matches).set_index("player")["awards"]
    rows = []
    for p in players:
        rows.append({
            "player": p,
            "runs": bat["runs"].get(p), "innings": bat["innings"].get(p),
            "strike_rate": bat["strike_rate"].get(p), "batting_average": bat["average"].get(p),
            "fours": bat["fours"].get(p), "sixes": bat["sixes"].get(p),
            "wickets": bowl["wickets"].get(p), "economy": bowl["economy"].get(p),
            "bowling_average": bowl["average"].get(p), "player_of_match": int(awards.get(p, 0)),
        })
    out = pd.DataFrame(rows)
    # Real numeric columns, so a statistic the player does not have is shown as empty, not as the word "None".
    numeric = [c for c in out.columns if c != "player"]
    out[numeric] = out[numeric].apply(pd.to_numeric, errors="coerce")
    return out
