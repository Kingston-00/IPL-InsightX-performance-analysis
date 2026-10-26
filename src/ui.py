"""Shared Streamlit helpers: page setup, cached data loading, global filters, charts, downloads."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from .data_cleaning import DataValidationError, IPLData, prepare_data, quality_table
from .data_loader import (DATA_DIR, DELIVERIES_FILE, MATCHES_FILE, DataFileError, load_raw_deliveries,
                          load_raw_matches, missing_files)

logger = logging.getLogger("ipl_insightx")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ASSETS = Path(__file__).resolve().parent.parent / "assets"
# Categorical colours, assigned in this fixed order (blue first, gold second for the brand look).
COLORWAY = ["#3987e5", "#f2b134", "#199e70", "#d95926", "#d55181", "#9085e9", "#e66767", "#6da7ec"]
BLUE, GOLD = COLORWAY[0], COLORWAY[1]

pio.templates["ipl"] = go.layout.Template(layout=dict(
    font=dict(family="Segoe UI, Arial, sans-serif", color="#e8ecf4"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=COLORWAY,
    xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.15)"),
    legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=10, r=10, t=50, b=10),
))
pio.templates.default = "plotly_dark+ipl"

CSS = """
<style>
[data-testid="stMetric"] {background:#151c2e; border:1px solid #26314d; border-radius:12px; padding:14px 16px;}
[data-testid="stMetricLabel"] p {color:#9aa6bf; font-size:0.85rem;}
[data-testid="stMetricValue"] {font-size:1.6rem;}
.hero {padding:18px 22px; border-radius:14px; background:linear-gradient(120deg,#151c2e 0%,#1b2a4a 100%);
       border:1px solid #26314d; margin-bottom:10px;}
.hero h1 {margin:0; font-size:2.2rem;} .hero h1 span {color:#f2b134;}
.hero p {margin:4px 0 0 0; color:#9aa6bf;}
.note {color:#9aa6bf; font-size:0.88rem;}
footer {visibility:hidden;}
</style>
"""


# ------------------------------------------------------------ page setup
def setup_page(title: str, icon: str = "🏏") -> None:
    """Page config, theme CSS and logo. Call first on every page."""
    st.set_page_config(page_title=f"{title} | IPL InsightX", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    logo = ASSETS / "logo.svg"
    if logo.is_file():
        st.logo(str(logo), size="large")


def page_header(title: str, description: str) -> None:
    st.title(title)
    st.caption(description)


# ----------------------------------------------------------- data loading
@st.cache_data(show_spinner="Loading and cleaning IPL data (first run only)...")
def _load_cached(data_dir: str, signature: tuple) -> IPLData:
    """Load + clean. ``signature`` (file sizes and modified times) busts the cache when files change."""
    path = Path(data_dir)
    return prepare_data(load_raw_matches(path), load_raw_deliveries(path))


def _signature(data_dir: Path) -> tuple:
    out = []
    for name in (MATCHES_FILE, DELIVERIES_FILE):
        p = data_dir / name
        out.append((name, p.stat().st_size, p.stat().st_mtime_ns) if p.is_file() else (name, None, None))
    return tuple(out)


def show_setup_help(problem: str) -> None:
    """Friendly setup page used when the data cannot be loaded."""
    st.title("Dataset setup needed")
    st.error(problem)
    st.markdown(
        f"""
**How to fix it**

1. Download an IPL dataset containing `matches` and `deliveries` CSV files
   (see `data/DATASET_GUIDE.md` for the source used by this project).
2. Save them in the project's `data` folder with these exact names:
   - `data/{MATCHES_FILE}`
   - `data/{DELIVERIES_FILE}`
3. Refresh this page (press **R**, or use the menu > *Rerun*).

Required match columns: `id`, `season`, `team1`, `team2`, `toss_winner`, `toss_decision`, `winner`, `venue`.
Required delivery columns: `match_id`, `inning`, `batting_team`, `bowling_team`, `over`, `ball`, `batter`,
`bowler`, `batsman_runs`, `extra_runs`, `total_runs`, `is_wicket`.
"""
    )


def get_data() -> IPLData:
    """Return the cleaned data, or show a setup message and stop the page."""
    absent = missing_files(DATA_DIR)
    if absent:
        show_setup_help("Missing file(s): " + ", ".join(f"data/{n}" for n in absent))
        st.stop()
    try:
        return _load_cached(str(DATA_DIR), _signature(DATA_DIR))
    except (DataFileError, DataValidationError) as exc:
        logger.error("Data problem: %s", exc)
        show_setup_help(str(exc))
        st.stop()
    except Exception:
        logger.exception("Unexpected error while loading data")
        show_setup_help("The data could not be loaded because of an unexpected problem. See the terminal log for details.")
        st.stop()


# --------------------------------------------------------------- filters
RESULT_LABELS = {"decisive": "Won by runs/wickets", "tie": "Tie (super over)", "no result": "No result"}


@dataclass
class Selection:
    """The user's current global filters and the data they produce."""
    matches: pd.DataFrame
    deliveries: pd.DataFrame | None
    season_range: tuple[int, int]
    teams: list[str]
    venues: list[str]
    stages: list[str]
    results: list[str] = field(default_factory=list)

    @property
    def description(self) -> str:
        parts = [f"Seasons {self.season_range[0]}-{self.season_range[1]}"]
        if self.teams:
            parts.append("teams: " + ", ".join(self.teams))
        if self.venues:
            parts.append(f"{len(self.venues)} venue(s)")
        if self.stages:
            parts.append("stage: " + ", ".join(self.stages))
        if self.results:
            parts.append("result: " + ", ".join(self.results))
        return " | ".join(parts) + f" - {len(self.matches)} matches"


def _reset_filters(season_min: int, season_max: int) -> None:
    for key, default in (("seasons", (season_min, season_max)), ("teams", []), ("venues", []), ("stages", []), ("results", [])):
        st.session_state[f"f_{key}"] = default
        st.session_state[f"w_{key}"] = default


def _remember(key: str, default):
    """Keep a filter value alive when the user moves to another page."""
    if f"w_{key}" not in st.session_state:
        st.session_state[f"w_{key}"] = st.session_state.get(f"f_{key}", default)


def sidebar_filters(data: IPLData, *, teams: bool = True, venues: bool = True, stages: bool = True,
                    results: bool = True) -> Selection:
    """Draw the global filters in the sidebar and return the filtered data."""
    matches = data.matches
    s_min, s_max = int(matches["season"].min()), int(matches["season"].max())
    with st.sidebar:
        st.subheader("Filters")
        st.caption(f"Data covers {s_min}-{s_max} ({matches['season'].nunique()} seasons)")
        if s_min < s_max:
            _remember("seasons", (s_min, s_max))
            st.session_state["w_seasons"] = tuple(
                min(max(v, s_min), s_max) for v in st.session_state["w_seasons"])   # stay inside the data
            season_range = st.slider("Season range", s_min, s_max, key="w_seasons")
        else:
            season_range = (s_min, s_max)
            st.caption(f"Only season {s_min} available.")
        st.session_state["f_seasons"] = season_range

        in_seasons = matches[matches["season"].between(*season_range)]
        team_options = sorted(set(in_seasons["team1"]) | set(in_seasons["team2"]))
        venue_options = sorted(in_seasons["venue"].unique())
        stage_options = sorted(in_seasons["match_type"].unique())
        result_options = [RESULT_LABELS[o] for o in ("decisive", "tie", "no result") if o in set(in_seasons["outcome"])]
        chosen = {}
        for key, label, options, enabled in (("teams", "Teams", team_options, teams),
                                             ("venues", "Venues", venue_options, venues),
                                             ("stages", "Match stage", stage_options, stages),
                                             ("results", "Result type", result_options, results)):
            if not enabled:
                chosen[key] = []
                continue
            _remember(key, [])
            st.session_state[f"w_{key}"] = [v for v in st.session_state[f"w_{key}"] if v in options]
            chosen[key] = st.multiselect(label, options, key=f"w_{key}", placeholder=f"All {label.lower()}")
            st.session_state[f"f_{key}"] = chosen[key]
        st.button("Reset filters", on_click=_reset_filters, args=(s_min, s_max), width="stretch")

    sel_matches = in_seasons
    if chosen["teams"]:
        sel_matches = sel_matches[sel_matches["team1"].isin(chosen["teams"]) | sel_matches["team2"].isin(chosen["teams"])]
    if chosen["venues"]:
        sel_matches = sel_matches[sel_matches["venue"].isin(chosen["venues"])]
    if chosen["stages"]:
        sel_matches = sel_matches[sel_matches["match_type"].isin(chosen["stages"])]
    if chosen["results"]:
        wanted = [o for o, label in RESULT_LABELS.items() if label in chosen["results"]]
        sel_matches = sel_matches[sel_matches["outcome"].isin(wanted)]
    deliveries = None
    if data.has_deliveries:
        deliveries = data.deliveries[data.deliveries["match_id"].isin(sel_matches["match_id"])]
    sel = Selection(sel_matches.reset_index(drop=True), deliveries, season_range, chosen["teams"], chosen["venues"],
                    chosen["stages"], chosen["results"])
    with st.sidebar:
        st.info(sel.description)
    return sel


def require_matches(sel: Selection) -> None:
    """Stop with a friendly message when the filters leave no matches."""
    if sel.matches.empty:
        st.warning("No matches fit the current filters. Widen the season range or press **Reset filters**.")
        st.stop()


def require_deliveries(data: IPLData, sel: Selection) -> None:
    """Stop with a message when ball-by-ball data is missing or filtered out."""
    if not data.has_deliveries:
        st.warning("This page needs ball-by-ball data (`data/deliveries.csv`), which is not available.")
        st.stop()
    if sel.deliveries is None or sel.deliveries.empty:
        st.warning("No ball-by-ball data fits the current filters.")
        st.stop()


# ------------------------------------------------------------ components
def metric_row(items: list[tuple[str, object, str | None]]) -> None:
    """Show metric cards. Each item is (label, value, help text). None values show 'n/a'."""
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            shown = "n/a"
        elif isinstance(value, float):
            shown = f"{value:,.2f}"
        elif isinstance(value, (int,)) or hasattr(value, "item"):
            shown = f"{int(value):,}" if float(value).is_integer() else f"{float(value):,.2f}"
        else:
            shown = str(value)
        col.metric(label, shown, help=help_text)


def style_fig(fig: go.Figure, title: str | None = None, height: int = 420, x_title: str | None = None,
              y_title: str | None = None) -> go.Figure:
    """Apply consistent chart layout."""
    fig.update_layout(height=height, title=dict(text=title, x=0.0, font=dict(size=16)) if title else None)
    if x_title is not None:
        fig.update_xaxes(title_text=x_title)
    if y_title is not None:
        fig.update_yaxes(title_text=y_title)
    return fig


def show_chart(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def download_csv(df: pd.DataFrame, label: str, filename: str, key: str | None = None) -> None:
    """CSV download button for a table (what you see is what you download)."""
    st.download_button(f"Download {label} (CSV)", df.to_csv(index=False).encode("utf-8"), file_name=filename,
                       mime="text/csv", key=key or f"dl_{filename}")


def download_matches(sel: Selection, key: str) -> None:
    """Download the match records that match the current filters (internal helper columns removed)."""
    cols = [c for c in sel.matches.columns if not c.endswith("_original")]
    download_csv(sel.matches[cols], "filtered match records", "ipl_filtered_matches.csv", key=key)


def table(df: pd.DataFrame, **kwargs) -> None:
    """Show a sortable table; dates are formatted for display."""
    st.dataframe(df, width="stretch", hide_index=True, **kwargs)


def coverage_text(data: IPLData) -> str:
    q = data.quality
    return (f"Data covers seasons {q['seasons'][0]}-{q['seasons'][-1]} "
            f"({q['date_min']:%d %b %Y} to {q['date_max']:%d %b %Y}), {len(data.matches):,} matches"
            + (f" and {len(data.deliveries):,} deliveries." if data.has_deliveries else "; no ball-by-ball data loaded."))


def quality_expander(data: IPLData) -> None:
    with st.expander("Data-quality summary and limitations"):
        table(quality_table(data.quality))
        st.markdown(
            "- Team names are standardised (e.g. *Delhi Daredevils* -> *Delhi Capitals*); venue spellings are merged.\n"
            "- Tied matches (decided by a super over) and no-result matches are counted separately from wins and losses.\n"
            "- Super-over deliveries are excluded from batting and bowling statistics.\n"
            "- Results describe the loaded dataset only and can differ from official IPL records."
        )
