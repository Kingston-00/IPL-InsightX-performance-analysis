"""Integration tests of the sidebar filters and error states (real data for filters, temp folder for setup page)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.data_loader import DATA_DIR, missing_files

ROOT = Path(__file__).resolve().parent.parent
needs_data = pytest.mark.skipif(bool(missing_files(DATA_DIR)), reason="real IPL data files not present")


def _widget(at, key):
    return next(w for w in list(at.multiselect) + list(at.slider) if w.key == key)


@needs_data
@pytest.mark.parametrize("page", ["pages/1_Team_Analytics.py", "pages/5_Toss_and_Match_Analysis.py", "pages/8_Data_Insights.py"])
def test_team_and_season_filters_change_match_count(page):
    at = AppTest.from_file(str(ROOT / page), default_timeout=180).run()
    full = at.sidebar.info[0].value
    _widget(at, "w_teams").set_value(["Mumbai Indians"])
    _widget(at, "w_seasons").set_value((2015, 2019))
    at.run()
    assert not at.exception
    filtered = at.sidebar.info[0].value
    assert filtered != full and "Seasons 2015-2019" in filtered and "Mumbai Indians" in filtered


@needs_data
def test_result_type_filter_selects_tied_matches():
    at = AppTest.from_file(str(ROOT / "pages/5_Toss_and_Match_Analysis.py"), default_timeout=180).run()
    _widget(at, "w_results").set_value(["Tie (super over)"])
    at.run()
    assert not at.exception
    assert "14 matches" in at.sidebar.info[0].value and "result: Tie (super over)" in at.sidebar.info[0].value


@needs_data
def test_empty_filter_result_shows_friendly_warning_not_a_traceback():
    at = AppTest.from_file(str(ROOT / "pages/1_Team_Analytics.py"), default_timeout=180).run()
    # Gujarat Lions (2016-17) never played at the Dubai stadium (UAE seasons were 2014, 2020, 2021).
    _widget(at, "w_teams").set_value(["Gujarat Lions"])
    _widget(at, "w_venues").set_value(["Dubai International Cricket Stadium"])
    at.run()
    assert not at.exception
    assert any("No matches fit" in w.value for w in at.warning)


def test_missing_data_files_show_setup_page(tmp_path, monkeypatch):
    import src.ui as ui
    monkeypatch.setattr(ui, "DATA_DIR", tmp_path)
    monkeypatch.setattr("src.data_loader.DATA_DIR", tmp_path)
    at = AppTest.from_function(_run_get_data, default_timeout=60)
    at.session_state["data_dir"] = str(tmp_path)
    at.run()
    assert not at.exception
    assert any("Missing file" in e.value for e in at.error)


def _run_get_data():
    import streamlit as st
    from pathlib import Path as P
    import src.ui as ui
    ui.DATA_DIR = P(st.session_state["data_dir"])
    ui.get_data()
