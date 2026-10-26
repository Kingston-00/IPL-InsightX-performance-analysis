"""Unit tests for batting, bowling and player logic. Synthetic data only."""
import numpy as np
import pandas as pd

from src.batting_analytics import batting_innings, batting_stats, runs_by_over, runs_distribution
from src.bowling_analytics import bowling_stats, dismissal_types
from src.data_cleaning import prepare_data
from src.insights import generate_insights, headline_kpis
from src.player_analytics import compare_players, player_of_match_counts, player_profile
from tests.fixtures import RAW_DELIVERIES, RAW_MATCHES


def data():
    return prepare_data(RAW_MATCHES, RAW_DELIVERIES)


def test_batter_runs_exclude_extras():
    s = batting_stats(data().deliveries).set_index("batter")
    assert s.loc["Bat1", "runs"] == 10             # 4 + 6; the wide and leg-bye add nothing
    assert s.loc["Bat1", "fours"] == 1 and s.loc["Bat1", "sixes"] == 1


def test_balls_faced_exclude_wides_but_include_legbyes():
    s = batting_stats(data().deliveries).set_index("batter")
    # Bat1 faced: 4, 6, leg-bye, wicket ball = 4 balls (wide not counted)
    assert s.loc["Bat1", "balls"] == 4
    assert s.loc["Bat1", "strike_rate"] == 250.0   # 10 / 4 x 100


def test_batting_average_counts_dismissals_not_all_wickets():
    s = batting_stats(data().deliveries).set_index("batter")
    assert s.loc["Bat1", "dismissals"] == 1 and s.loc["Bat1", "average"] == 10.0
    assert np.isnan(s.loc["Bat2", "average"])      # never dismissed: no average, no division by zero
    assert s.loc["Bat3", "dismissals"] == 1 and s.loc["Bat3", "runs"] == 0


def test_super_over_is_excluded():
    s = batting_stats(data().deliveries).set_index("batter")
    assert s.loc["Bat4", "runs"] == 2              # the 6 in the super over is ignored


def test_player_run_totals_sum_to_team_bat_runs():
    s = batting_stats(data().deliveries)
    assert s["runs"].sum() == 4 + 6 + 1 + 2


def test_highest_score_and_innings():
    inn = batting_innings(data().deliveries)
    assert inn[inn["batter"] == "Bat1"]["runs"].max() == 10
    assert len(inn) == 4


def test_bowler_wickets_exclude_run_outs():
    b = bowling_stats(data().deliveries).set_index("bowler")
    assert b.loc["Bowl1", "wickets"] == 1
    assert b.loc["Bowl2", "wickets"] == 0          # the run out is not credited


def test_bowler_runs_charge_wides_not_legbyes():
    b = bowling_stats(data().deliveries).set_index("bowler")
    # Bowl1: 4 + 6 + wide(1) + leg-bye(0 charged) + 0 + 1 = 12
    assert b.loc["Bowl1", "runs_conceded"] == 12
    # Legal balls: wides do not count -> 5 deliveries minus the wide = 5 (4, 6, legbye, wicket, 1)
    assert b.loc["Bowl1", "legal_balls"] == 5
    assert b.loc["Bowl1", "economy"] == round(12 * 6 / 5, 2)
    assert b.loc["Bowl1", "average"] == 12.0 and b.loc["Bowl1", "strike_rate"] == 5.0


def test_bowling_ratios_do_not_divide_by_zero():
    b = bowling_stats(data().deliveries).set_index("bowler")
    assert np.isnan(b.loc["Bowl2", "average"]) and np.isnan(b.loc["Bowl2", "strike_rate"])


def test_min_balls_threshold():
    assert bowling_stats(data().deliveries, min_balls=6).empty
    assert set(bowling_stats(data().deliveries, min_balls=5)["bowler"]) == {"Bowl1"}
    assert batting_stats(data().deliveries, min_balls=4)["batter"].tolist() == ["Bat1"]


def test_dismissal_types():
    d = dismissal_types(data().deliveries).set_index("dismissal_kind")
    assert d.loc["bowled", "credited_to_bowler"] and not d.loc["run out", "credited_to_bowler"]


def test_runs_by_over_and_distribution():
    r = runs_by_over(data().deliveries)
    assert r["over"].tolist() == [1]
    dist = runs_distribution(data().deliveries).set_index("runs_off_bat")
    assert dist["deliveries"].sum() == 7           # balls faced in regular innings (no wide, no super over)


def test_player_of_match_counts():
    p = player_of_match_counts(data().matches).set_index("player")["awards"]
    assert p.to_dict() == {"P1": 2, "P2": 1}


def test_player_profile_and_unavailable_statistics():
    prof = player_profile("Bat2", data().deliveries, data().matches)
    assert prof["runs"] == 1 and prof["average"] is None and prof["wickets"] is None
    unknown = player_profile("Nobody", data().deliveries, data().matches)
    assert unknown["runs"] is None and unknown["awards"] == 0


def test_compare_players():
    c = compare_players(["Bat1", "Bowl1"], data().deliveries, data().matches).set_index("player")
    assert c.loc["Bat1", "runs"] == 10 and c.loc["Bowl1", "wickets"] == 1
    assert pd.isna(c.loc["Bowl1", "runs"])


def test_kpis_and_insights():
    d = data()
    k = headline_kpis(d.matches, d.deliveries)
    assert k["matches"] == 4 and k["teams"] == 3 and k["seasons"] == 2
    assert k["runs"] == 13 + 2                      # regular innings only
    assert k["wickets"] == 2                        # bowled + run out
    assert k["players"] == 7                        # Bat1-4, Bowl1-2, N
    assert headline_kpis(d.matches, None)["runs"] is None
    titles = [i.title for i in generate_insights(d.matches, d.deliveries)]
    assert "Most wins" in titles and "Most runs" in titles and "Most common scoring pattern" in titles
    pattern = next(i for i in generate_insights(d.matches, d.deliveries) if i.title == "Most common scoring pattern")
    # Balls faced in regular innings: 4, 6, leg-bye(0), wicket ball(0), 1, run out(0), 2 -> three dot balls is the most common.
    assert "dot ball" in pattern.finding and pattern.value == "42.9%" and pattern.sample_size == "7 balls faced"
    assert generate_insights(d.matches.iloc[0:0], None) == []
