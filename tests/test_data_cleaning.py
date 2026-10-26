"""Unit tests for loading and cleaning. All data here is synthetic."""
import numpy as np
import pandas as pd
import pytest

from src.data_cleaning import (DataValidationError, clean_matches, normalize_column_names, parse_season,
                               prepare_data, safe_divide, MATCH_ALIASES, standardize_team_names)
from src.data_loader import DataFileError, missing_files, read_csv_clean
from tests.fixtures import RAW_DELIVERIES, RAW_MATCHES


def test_loading_strips_padding_and_na_tokens(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("a  ,b \n 1 ,NA \n 2 ,x  \n")
    df = read_csv_clean(path)
    assert list(df.columns) == ["a", "b"]
    assert df["a"].tolist() == ["1", "2"]
    assert pd.isna(df["b"].iloc[0]) and df["b"].iloc[1] == "x"


def test_missing_and_empty_files(tmp_path):
    assert set(missing_files(tmp_path)) == {"matches.csv", "deliveries.csv"}
    with pytest.raises(DataFileError):
        read_csv_clean(tmp_path / "nope.csv")
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(DataFileError):
        read_csv_clean(empty)
    header_only = tmp_path / "h.csv"
    header_only.write_text("a,b\n")
    with pytest.raises(DataFileError):
        read_csv_clean(header_only)


def test_out_of_memory_gives_memory_message_not_invalid_csv(tmp_path, monkeypatch):
    path = tmp_path / "d.csv"
    path.write_text("a,b\n1,2\n")

    def fake_read_csv(*args, **kwargs):
        raise MemoryError("simulated")

    monkeypatch.setattr(pd, "read_csv", fake_read_csv)
    with pytest.raises(DataFileError, match="Not enough free memory"):
        read_csv_clean(path)


def test_missing_required_columns_gives_clear_error():
    with pytest.raises(DataValidationError, match="winner"):
        clean_matches(RAW_MATCHES.drop(columns=["winner"]))
    with pytest.raises(DataValidationError, match="batsman_runs"):
        prepare_data(RAW_MATCHES, RAW_DELIVERIES.drop(columns=["batsman_runs"]))


def test_column_aliases_are_renamed():
    df = normalize_column_names(pd.DataFrame(columns=["ID", "Man of the Match", "Toss Won By"]), MATCH_ALIASES)
    assert list(df.columns) == ["match_id", "player_of_match", "toss_winner"]


def test_duplicate_match_ids_removed():
    dup = pd.concat([RAW_MATCHES, RAW_MATCHES.iloc[[0]]], ignore_index=True)
    clean, notes = clean_matches(dup)
    assert len(clean) == 4
    assert notes["matches_duplicate_ids_removed"] == 1


def test_repeated_ball_numbers_are_not_deleted_as_duplicates():
    data = prepare_data(RAW_MATCHES, RAW_DELIVERIES)
    # Over 0 ball 3 appears twice (wide + leg-bye) and both rows must be kept.
    assert len(data.deliveries) == len(RAW_DELIVERIES)


def test_outcomes_ties_and_no_results_are_not_errors():
    clean, notes = clean_matches(RAW_MATCHES)
    assert clean.set_index("match_id")["outcome"].to_dict() == {1: "decisive", 2: "decisive", 3: "tie", 4: "no result"}
    assert notes["matches_decisive"] == 2 and notes["matches_tie"] == 1 and notes["matches_no_result"] == 1
    assert notes["matches_winner_not_a_team"] == 0


def test_season_parsing():
    assert parse_season("2020") == 2020
    assert parse_season("2007/08") == 2008
    assert parse_season("2009/10") == 2010
    assert np.isnan(parse_season("unknown"))
    assert np.isnan(parse_season(None))


def test_team_name_standardisation():
    s = standardize_team_names(pd.Series(["Delhi Daredevils", "Mumbai Indians", "Kings XI Punjab"]))
    assert s.tolist() == ["Delhi Capitals", "Mumbai Indians", "Punjab Kings"]


def test_invalid_numbers_are_dropped_and_counted():
    bad = RAW_DELIVERIES.copy()
    bad.loc[0, "batsman_runs"] = "x"
    data = prepare_data(RAW_MATCHES, bad)
    assert data.quality["deliveries_invalid_numeric_rows"] == 1
    assert len(data.deliveries) == len(RAW_DELIVERIES) - 1


def test_id_consistency_is_reported():
    extra = RAW_DELIVERIES.copy()
    extra.loc[0, "match_id"] = "999"
    data = prepare_data(RAW_MATCHES, extra)
    assert data.quality["ids_in_deliveries_not_in_matches"] == 1
    assert data.quality["ids_in_matches_without_deliveries"] == 3
    assert 999 not in set(data.deliveries["match_id"])


def test_innings_info_is_joined_once_per_match():
    data = prepare_data(RAW_MATCHES, RAW_DELIVERIES)
    assert len(data.matches) == 4                       # no duplication from the join
    m1 = data.matches.set_index("match_id").loc[1]
    assert m1["batting_first"] == "A" and m1["batting_second"] == "B"
    assert m1["first_innings_runs"] == 4 + 6 + 1 + 1 + 1   # includes extras, wicket ball adds 0
    assert m1["second_innings_runs"] == 2                  # super over excluded


def test_empty_deliveries_and_no_deliveries():
    data = prepare_data(RAW_MATCHES, None)
    assert not data.has_deliveries
    assert data.matches["batting_first"].isna().all()


def test_safe_divide():
    assert np.isnan(safe_divide(5, 0))
    assert safe_divide(50, 200, 100) == 25.0
    out = safe_divide(pd.Series([1.0, 2.0]), pd.Series([0.0, 4.0]), 100)
    assert np.isnan(out.iloc[0]) and out.iloc[1] == 50.0
