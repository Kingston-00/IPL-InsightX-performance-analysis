"""Headline numbers and plain-language insights, all computed from the data given."""
from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd

from .batting_analytics import batting_stats, regular_deliveries, runs_distribution
from .bowling_analytics import bowling_stats, dismissal_types
from .player_analytics import player_of_match_counts
from .team_analytics import team_summary
from .toss_analytics import chase_vs_defend, toss_win_match_win
from .venue_analytics import highest_team_total


@dataclass
class Insight:
    """One finding with its value, sample size and the calculation behind it."""
    title: str
    finding: str
    value: str
    sample_size: str
    method: str


def headline_kpis(matches: pd.DataFrame, deliveries: pd.DataFrame | None) -> dict:
    """Home-page KPI numbers. Delivery-based KPIs are None when no deliveries are available."""
    teams = set(matches["team1"]) | set(matches["team2"]) if not matches.empty else set()
    kpis = {"matches": len(matches), "teams": len(teams),
            "seasons": matches["season"].nunique() if not matches.empty else 0,
            "players": None, "runs": None, "wickets": None}
    if deliveries is not None and not deliveries.empty:
        reg = regular_deliveries(deliveries)
        players = set()
        for col in ("batter", "non_striker", "bowler"):
            players.update(reg[col].dropna().astype(str).unique())
        kpis["players"] = len(players)
        kpis["runs"] = int(reg["total_runs"].sum())
        # Wickets = every dismissal that ended a batter's innings (retired hurt excluded).
        kpis["wickets"] = int(reg["is_dismissal"].sum())
    return kpis


def generate_insights(matches: pd.DataFrame, deliveries: pd.DataFrame | None, min_balls_sr: int = 500) -> list[Insight]:
    """Build insights for the selected data. Insights the data cannot support are skipped."""
    out: list[Insight] = []
    if matches.empty:
        return out

    teams = team_summary(matches)
    if not teams.empty and teams.iloc[0]["wins"] > 0:
        t = teams.iloc[0]
        out.append(Insight("Most wins", f"{t['team']} has the most recorded wins.", f"{int(t['wins'])} wins",
                           f"{int(t['matches'])} matches played by the team",
                           "Wins = matches won by runs or wickets. Ties and no-results are not wins."))
    eligible = teams[teams["decided"] >= 20]
    if not eligible.empty:
        t = eligible.sort_values("win_pct_decided", ascending=False).iloc[0]
        out.append(Insight("Highest win rate", f"Among teams with at least 20 decided matches, {t['team']} has the highest win rate.",
                           f"{t['win_pct_decided']:.1f}%", f"{int(t['decided'])} decided matches",
                           "Win % = wins / (wins + losses). Ties and no-results excluded."))

    season_counts = matches["season"].value_counts()
    if len(season_counts):
        s = season_counts.idxmax()
        out.append(Insight("Busiest season", f"{s} had the most recorded matches.", f"{season_counts.max()} matches",
                           f"{len(matches)} matches in the selection", "Count of match records per season (playoffs included)."))
    venues = matches["venue"].value_counts()
    if len(venues) and venues.index[0] != "Unknown venue":
        out.append(Insight("Most-used venue", f"{venues.index[0]} hosted the most recorded matches.", f"{venues.iloc[0]} matches",
                           f"{len(matches)} matches in the selection",
                           "Count of matches per venue after merging known spelling variants. A high count does not mean the venue favours batters or bowlers."))
    decisions = matches["toss_decision"].value_counts()
    if len(decisions):
        out.append(Insight("Most common toss decision", f"Toss winners most often chose to {decisions.idxmax()}.",
                           f"{decisions.max() / decisions.sum() * 100:.1f}% of tosses", f"{int(decisions.sum())} tosses",
                           "Share of matches by toss decision."))
    tw = toss_win_match_win(matches)
    if tw["decisive_matches"]:
        out.append(Insight("Toss and match result",
                           "The toss winner won the match in the share of matches shown. This is an observed association, not proof that the toss causes the result.",
                           f"{tw['pct']:.1f}%", f"{tw['decisive_matches']} decisive matches",
                           "Toss winner = match winner, divided by decisive matches (ties and no-results excluded)."))
    cd = chase_vs_defend(matches)
    if cd["decisive_matches"]:
        out.append(Insight("Chasing vs defending",
                           f"Teams batting second won {cd['chasing_pct']:.1f}% of decisive matches; teams batting first won {cd['batting_first_pct']:.1f}%.",
                           f"{cd['won_chasing']} vs {cd['won_batting_first']} wins", f"{cd['decisive_matches']} decisive matches",
                           "Batting order is taken from the ball-by-ball data (innings 1 vs innings 2)."))
    pom = player_of_match_counts(matches)
    if not pom.empty:
        out.append(Insight("Most Player of the Match awards", f"{pom.iloc[0]['player']} won the most awards.",
                           f"{int(pom.iloc[0]['awards'])} awards", f"{int(pom['awards'].sum())} awards given",
                           "Count of Player of the Match entries (ties for first place show only one name)."))
    top = highest_team_total(matches)
    if top:
        out.append(Insight("Highest team total", f"{top['team']} scored the highest innings total ({top['venue']}, {top['season']}).",
                           f"{top['runs']} runs", "Both regular innings of every selected match",
                           "Sum of total_runs (including extras) in innings 1 and 2; super overs excluded."))

    if deliveries is not None and not deliveries.empty:
        d = deliveries[deliveries["match_id"].isin(matches["match_id"])]
        bat = batting_stats(d)
        if not bat.empty:
            b = bat.iloc[0]
            out.append(Insight("Most runs", f"{b['batter']} scored the most runs.", f"{int(b['runs'])} runs",
                               f"{int(b['innings'])} innings", "Sum of runs off the bat in regular innings (extras excluded)."))
            sr = bat[bat["balls"] >= min_balls_sr].sort_values("strike_rate", ascending=False)
            if not sr.empty:
                s = sr.iloc[0]
                out.append(Insight("Best strike rate", f"{s['batter']} has the highest strike rate among batters who faced at least {min_balls_sr} balls.",
                                   f"{s['strike_rate']:.1f}", f"{int(s['balls'])} balls faced",
                                   "Strike rate = runs / balls faced x 100. Wides are not balls faced."))
        bowl = bowling_stats(d)
        if not bowl.empty and bowl.iloc[0]["wickets"] > 0:
            w = bowl.iloc[0]
            out.append(Insight("Most wickets", f"{w['bowler']} took the most wickets.", f"{int(w['wickets'])} wickets",
                               f"{int(w['legal_balls'])} legal balls bowled",
                               "Wickets credited to the bowler (bowled, caught, lbw, stumped, caught & bowled, hit wicket)."))
        dist = runs_distribution(d)
        if not dist.empty:
            common = dist.sort_values("deliveries", ascending=False).iloc[0]
            label = "a dot ball (no runs)" if common["runs_off_bat"] == 0 else f"{int(common['runs_off_bat'])} run(s) off the bat"
            out.append(Insight("Most common scoring pattern", f"The most common result of a ball faced is {label}.",
                               f"{common['share_pct']:.1f}%", f"{int(dist['deliveries'].sum())} balls faced",
                               "Share of balls faced (wides excluded) by runs scored off the bat, regular innings."))
        dis = dismissal_types(d)
        if not dis.empty:
            out.append(Insight("Most common dismissal", f"'{dis.iloc[0]['dismissal_kind']}' is the most frequent dismissal type.",
                               f"{dis.iloc[0]['wickets'] / dis['wickets'].sum() * 100:.1f}%", f"{int(dis['wickets'].sum())} dismissals",
                               "Count of wicket deliveries by dismissal kind in regular innings."))
    return out


def insights_table(insights: list[Insight]) -> pd.DataFrame:
    """Insights as a DataFrame (used for the CSV download)."""
    return pd.DataFrame([asdict(i) for i in insights])
