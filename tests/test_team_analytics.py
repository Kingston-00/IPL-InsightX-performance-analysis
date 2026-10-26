"""Unit tests for team, toss, venue and filter logic. Synthetic data only."""
import numpy as np

from src.data_cleaning import prepare_data
from src.season_analytics import most_successful_team, season_overview
from src.team_analytics import batting_first_vs_chasing, head_to_head, team_summary
from src.toss_analytics import chase_vs_defend, toss_decision_outcomes, toss_win_match_win
from src.venue_analytics import venue_summary
from tests.fixtures import RAW_DELIVERIES, RAW_MATCHES


def data():
    return prepare_data(RAW_MATCHES, RAW_DELIVERIES)


def test_team_wins_losses_ties_no_results():
    s = team_summary(data().matches).set_index("team")
    # A: won m1, m2; no result m4.  B: lost m1, m2; tie m3.  C: tie m3, no result m4.
    assert s.loc["A", ["matches", "wins", "losses", "ties", "no_results"]].tolist() == [3, 2, 0, 0, 1]
    assert s.loc["B", ["matches", "wins", "losses", "ties", "no_results"]].tolist() == [3, 0, 2, 1, 0]
    assert s.loc["C", ["matches", "wins", "losses", "ties", "no_results"]].tolist() == [2, 0, 0, 1, 1]


def test_tie_super_over_winner_is_not_counted_as_win():
    s = team_summary(data().matches).set_index("team")
    assert s.loc["B", "wins"] == 0


def test_win_percentage_denominators():
    s = team_summary(data().matches).set_index("team")
    assert s.loc["A", "win_pct_decided"] == 100.0           # 2 / (2 + 0)
    assert s.loc["A", "win_pct_all"] == round(2 / 3 * 100, 1)   # 2 / 3 matches
    assert np.isnan(s.loc["C", "win_pct_decided"])           # zero decided matches: NaN, not an error
    assert s.loc["B", "win_pct_decided"] == 0.0


def test_no_double_counting_of_matches():
    s = team_summary(data().matches)
    assert s["matches"].sum() == 2 * 4        # each match counted once per team


def test_head_to_head():
    h = head_to_head(data().matches)
    ab = h[(h["team"] == "A") & (h["opponent"] == "B")].iloc[0]
    assert (ab["matches"], ab["wins"], ab["losses"]) == (2, 2, 0)


def test_batting_first_vs_chasing():
    t = batting_first_vs_chasing(data().matches).set_index(["team", "role"])
    # m1: A batted first and won. m2 has no deliveries, so innings order is unknown and it is skipped.
    assert t.loc[("A", "Batting first (defending)"), ["matches", "wins"]].tolist() == [1, 1]
    assert t.loc[("B", "Batting second (chasing)"), ["matches", "wins"]].tolist() == [1, 0]


def test_toss_win_match_win():
    r = toss_win_match_win(data().matches)
    # decisive: m1 (toss A, winner A) yes; m2 (toss B, winner A) no.
    assert r == {"decisive_matches": 2, "toss_winner_won": 1, "pct": 50.0}


def test_toss_decision_outcomes_and_denominator():
    o = toss_decision_outcomes(data().matches).set_index("toss_decision")
    assert o.loc["bat", ["matches", "toss_winner_won", "win_pct"]].tolist() == [1, 1, 100.0]
    assert o.loc["field", ["matches", "toss_winner_won", "win_pct"]].tolist() == [1, 0, 0.0]


def test_chase_vs_defend_uses_known_innings_only():
    r = chase_vs_defend(data().matches)
    assert r["decisive_matches"] == 1 and r["won_batting_first"] == 1 and r["chasing_pct"] == 0.0


def test_matches_without_winner_are_excluded_from_toss_percentages():
    only_nr = data().matches[data().matches["outcome"] == "no result"]
    r = toss_win_match_win(only_nr)
    assert r["decisive_matches"] == 0 and np.isnan(r["pct"])


def test_empty_selection_does_not_crash():
    empty = data().matches.iloc[0:0]
    assert team_summary(empty).empty
    assert toss_decision_outcomes(empty).empty
    assert venue_summary(empty).empty
    assert season_overview(empty).empty
    assert most_successful_team(empty).empty
    assert chase_vs_defend(empty)["decisive_matches"] == 0


def test_season_filtering_changes_results():
    m = data().matches
    s2020 = team_summary(m[m["season"] == 2020]).set_index("team")
    assert s2020.loc["A", "matches"] == 2 and "C" not in s2020.index


def test_venue_summary():
    v = venue_summary(data().matches).set_index("venue")
    assert v.loc["V1", "matches"] == 2
    assert v.loc["V1", "avg_first_innings"] == 13.0         # only m1 has innings data
    assert v.loc["V1", "highest_total"] == 13.0


def test_season_overview_is_chronological():
    ov = season_overview(data().matches)
    assert ov["season"].tolist() == [2020, 2021]
    assert ov["matches"].tolist() == [2, 2]


def test_most_successful_team():
    best = most_successful_team(data().matches)
    assert best[["season", "team", "wins"]].values.tolist() == [[2020, "A", 2]]
