"""Integration test: run every Streamlit page headlessly against the REAL IPL files.

These tests are skipped automatically when data/matches.csv or data/deliveries.csv is missing.
They are not unit tests - they use the actual dataset, not synthetic data.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.data_loader import DATA_DIR, missing_files

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["app.py"] + sorted(f"pages/{p.name}" for p in (ROOT / "pages").glob("*.py"))

pytestmark = pytest.mark.skipif(bool(missing_files(DATA_DIR)), reason="real IPL data files not present")


@pytest.mark.parametrize("page", PAGES)
def test_page_runs_without_exception(page):
    # AppTest silently swallows SyntaxError, so compile the file explicitly first.
    compile((ROOT / page).read_text(encoding="utf-8"), page, "exec")
    at = AppTest.from_file(str(ROOT / page), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]
    # A page that failed to load renders nothing, so also require real content.
    assert len(at.main) > 0 and len(at.sidebar) > 0 and len(at.metric) + len(at.dataframe) > 0, page
