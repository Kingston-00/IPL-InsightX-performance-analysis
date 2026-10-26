"""Reusable data-cleaning pipeline for IPL match and delivery data.

Main entry point: :func:`prepare_data`, which returns an :class:`IPLData`
bundle holding cleaned tables plus a data-quality report.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

logger = logging.getLogger("ipl_insightx")

# ---------------------------------------------------------------- schemas
# Different public IPL datasets use different column names. After lower-casing
# and replacing spaces, these aliases are renamed to our standard names.
MATCH_ALIASES = {
    "id": "match_id", "matchid": "match_id",
    "winning_team": "winner", "match_winner": "winner",
    "stadium": "venue", "ground": "venue",
    "man_of_the_match": "player_of_match", "mom": "player_of_match",
    "toss_won_by": "toss_winner", "toss_choice": "toss_decision",
    "team_1": "team1", "team_2": "team2",
}
DELIVERY_ALIASES = {
    "id": "match_id", "matchid": "match_id",
    "innings": "inning", "batting_side": "batting_team", "bowling_side": "bowling_team",
    "overs": "over", "balls": "ball", "ball_no": "ball",
    "batsman": "batter", "striker": "batter",
    "batter_runs": "batsman_runs", "runs_off_bat": "batsman_runs",
    "extras": "extra_runs", "extra": "extra_runs",
    "total_run": "total_runs", "runs_total": "total_runs",
    "wicket": "is_wicket", "iswicket": "is_wicket", "is_wicket_delivery": "is_wicket",
    "dismissal_type": "dismissal_kind", "wicket_type": "dismissal_kind",
    "extra_type": "extras_type", "extras_kind": "extras_type",
    "player_out": "player_dismissed",
}
REQUIRED_MATCH_COLUMNS = ["match_id", "season", "team1", "team2", "toss_winner",
                          "toss_decision", "winner", "venue"]
REQUIRED_DELIVERY_COLUMNS = ["match_id", "inning", "batting_team", "bowling_team", "over", "ball",
                             "batter", "bowler", "batsman_runs", "extra_runs", "total_runs", "is_wicket"]

# Franchise renames: same franchise, new name. Deccan Chargers / Sunrisers
# Hyderabad, Pune Warriors / Rising Pune Supergiant and Gujarat Lions / Gujarat
# Titans are different franchises and are deliberately NOT merged.
TEAM_NAME_MAP = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}

# Venue spelling variants / renames of the SAME stadium. Venues in different
# stadiums (e.g. Mullanpur vs Mohali) are not merged.
VENUE_NAME_MAP = {
    "Arun Jaitley Stadium": "Arun Jaitley Stadium, Delhi",
    "Feroz Shah Kotla": "Arun Jaitley Stadium, Delhi",           # renamed in 2019
    "Brabourne Stadium": "Brabourne Stadium, Mumbai",
    "Dr DY Patil Sports Academy": "Dr DY Patil Sports Academy, Mumbai",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium": "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam",
    "Eden Gardens": "Eden Gardens, Kolkata",
    "Himachal Pradesh Cricket Association Stadium": "Himachal Pradesh Cricket Association Stadium, Dharamsala",
    "M Chinnaswamy Stadium": "M Chinnaswamy Stadium, Bengaluru",
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium, Bengaluru",
    "MA Chidambaram Stadium": "MA Chidambaram Stadium, Chepauk, Chennai",
    "MA Chidambaram Stadium, Chepauk": "MA Chidambaram Stadium, Chepauk, Chennai",
    "Maharashtra Cricket Association Stadium": "Maharashtra Cricket Association Stadium, Pune",
    "Subrata Roy Sahara Stadium": "Maharashtra Cricket Association Stadium, Pune",   # earlier name
    "Punjab Cricket Association IS Bindra Stadium": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "Punjab Cricket Association Stadium, Mohali": "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "Rajiv Gandhi International Stadium": "Rajiv Gandhi International Stadium, Uppal, Hyderabad",
    "Rajiv Gandhi International Stadium, Uppal": "Rajiv Gandhi International Stadium, Uppal, Hyderabad",
    "Sardar Patel Stadium, Motera": "Narendra Modi Stadium, Ahmedabad",   # renamed in 2021
    "Sawai Mansingh Stadium": "Sawai Mansingh Stadium, Jaipur",
    "Wankhede Stadium": "Wankhede Stadium, Mumbai",
    "Zayed Cricket Stadium, Abu Dhabi": "Sheikh Zayed Stadium",
}

# Dismissals credited to the bowler.
BOWLER_WICKET_KINDS = {"bowled", "caught", "caught and bowled", "lbw", "stumped", "hit wicket"}
# Not counted as a batter's dismissal (the batter returns / is not out).
NOT_A_DISMISSAL = {"retired hurt"}
REGULAR_INNINGS = (1, 2)


class DataValidationError(Exception):
    """Raised when required columns are missing or a table is unusable."""


@dataclass
class IPLData:
    """Cleaned tables and the data-quality report."""
    matches: pd.DataFrame
    deliveries: pd.DataFrame | None
    quality: dict = field(default_factory=dict)

    @property
    def has_deliveries(self) -> bool:
        return self.deliveries is not None and not self.deliveries.empty

    @property
    def has_extras_type(self) -> bool:
        return self.has_deliveries and bool(self.quality.get("has_extras_type", False))


# ---------------------------------------------------------------- helpers
def normalize_column_names(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    """Lower-case, snake_case and rename known aliases to standard names."""
    out = df.copy()
    cleaned = [re.sub(r"[^0-9a-z]+", "_", str(c).strip().lower()).strip("_") for c in out.columns]
    out.columns = [aliases.get(c, c) for c in cleaned]
    return out.loc[:, ~pd.Index(out.columns).duplicated()]


def check_required_columns(df: pd.DataFrame, required: list[str], table: str) -> None:
    """Raise DataValidationError listing every missing required column."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"{table} is missing required column(s): {', '.join(missing)}. "
            f"Columns found: {', '.join(map(str, df.columns))}."
        )


def standardize_team_names(series: pd.Series, mapping: dict[str, str] = TEAM_NAME_MAP) -> pd.Series:
    """Map historical team names to the current franchise name."""
    return series.replace(mapping)


def parse_season(value) -> float:
    """Turn a season label into a sortable year, e.g. '2007/08' -> 2008.

    Returns NaN when no year can be found.
    """
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    split = re.fullmatch(r"(\d{4})\s*[/-]\s*(\d{2})", text)
    if split:
        return float(split.group(1)[:2] + split.group(2))
    match = re.search(r"\d{4}", text)
    return float(match.group()) if match else np.nan


def safe_divide(numerator, denominator, scale: float = 1.0):
    """Compute numerator * scale / denominator, giving NaN when the denominator is 0.

    Works for scalars and pandas Series (aligned on index).
    """
    if isinstance(numerator, pd.Series) or isinstance(denominator, pd.Series):
        den = denominator.astype("float64")
        return numerator.astype("float64") * scale / den.where(den != 0)
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return np.nan
    return float(numerator) * scale / float(denominator)


# ---------------------------------------------------------------- matches
def clean_matches(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the matches table. Returns (clean_matches, quality_notes)."""
    df = normalize_column_names(raw, MATCH_ALIASES)
    check_required_columns(df, REQUIRED_MATCH_COLUMNS, "matches.csv")
    notes: dict = {"matches_rows_raw": len(df)}

    df["match_id"] = pd.to_numeric(df["match_id"], errors="coerce")
    notes["matches_invalid_id"] = int(df["match_id"].isna().sum())
    df = df.dropna(subset=["match_id"]).copy()
    df["match_id"] = df["match_id"].astype("int64")

    before = len(df)
    df = df.drop_duplicates(subset="match_id", keep="first").copy()
    notes["matches_duplicate_ids_removed"] = before - len(df)

    for col in ("team1", "team2", "toss_winner", "winner"):
        df[f"{col}_original"] = df[col]
        df[col] = standardize_team_names(df[col])

    df["season_label"] = df["season"].astype("string").str.strip()
    df["season"] = df["season"].map(parse_season)
    notes["matches_invalid_season"] = int(df["season"].isna().sum())
    df = df.dropna(subset=["season"]).copy()
    df["season"] = df["season"].astype(int)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        notes["matches_invalid_date"] = int(df["date"].isna().sum())
    else:
        df["date"] = pd.NaT
        notes["matches_invalid_date"] = len(df)

    for col in ("city", "player_of_match", "match_type", "method", "result"):
        if col not in df.columns:
            df[col] = pd.NA
    if "result_margin" in df.columns:
        df["result_margin"] = pd.to_numeric(df["result_margin"], errors="coerce")
    else:
        df["result_margin"] = np.nan
    df["toss_decision"] = df["toss_decision"].str.lower()
    df["result"] = df["result"].str.lower()
    df["match_type"] = df["match_type"].fillna("Unknown")
    df["venue_original"] = df["venue"]
    df["venue"] = df["venue"].fillna("Unknown venue").replace(VENUE_NAME_MAP)
    if "super_over" in df.columns:
        df["super_over"] = df["super_over"].str.upper().eq("Y")
    else:
        df["super_over"] = False

    # Outcome category. A missing winner is not always an error: ties and
    # no-result matches are real outcomes. In this dataset a tied match still
    # has a winner (the super-over winner), but it is NOT counted as a win.
    if df["result"].notna().any():
        outcome = np.select(
            [df["result"].eq("tie"),
             df["result"].isin(["runs", "wickets"]) & df["winner"].notna()],
            ["tie", "decisive"], default="no result")
    else:
        outcome = np.where(df["winner"].notna(), "decisive", "no result")
    df["outcome"] = outcome
    df["decisive"] = df["outcome"].eq("decisive")

    notes["matches_decisive"] = int(df["decisive"].sum())
    notes["matches_tie"] = int((df["outcome"] == "tie").sum())
    notes["matches_no_result"] = int((df["outcome"] == "no result").sum())
    notes["matches_winner_not_a_team"] = int((
        df["decisive"] & (df["winner"] != df["team1"]) & (df["winner"] != df["team2"])).sum())
    notes["matches_same_team_twice"] = int((df["team1"] == df["team2"]).sum())
    notes["matches_missing_venue"] = int((df["venue"] == "Unknown venue").sum())
    notes["matches_missing_player_of_match"] = int(df["player_of_match"].isna().sum())
    return df.sort_values(["season", "date", "match_id"]).reset_index(drop=True), notes


# ------------------------------------------------------------- deliveries
def clean_deliveries(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the deliveries table and add helper columns."""
    df = normalize_column_names(raw, DELIVERY_ALIASES)
    check_required_columns(df, REQUIRED_DELIVERY_COLUMNS, "deliveries.csv")
    notes: dict = {"deliveries_rows_raw": len(df), "has_extras_type": "extras_type" in df.columns}

    int_cols = ["match_id", "inning", "over", "ball", "batsman_runs", "extra_runs", "total_runs", "is_wicket"]
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    invalid = df[int_cols].isna().any(axis=1)
    notes["deliveries_invalid_numeric_rows"] = int(invalid.sum())
    df = df.loc[~invalid].copy()
    df[int_cols] = df[int_cols].astype("int32")

    for col in ("extras_type", "dismissal_kind", "player_dismissed", "fielder", "non_striker"):
        if col not in df.columns:
            df[col] = pd.NA
    df["extras_type"] = df["extras_type"].str.lower()
    df["dismissal_kind"] = df["dismissal_kind"].str.lower()

    for col in ("batting_team", "bowling_team"):
        df[col] = standardize_team_names(df[col])
    missing_player = df[["batter", "bowler", "batting_team"]].isna().any(axis=1)
    notes["deliveries_missing_batter_or_bowler"] = int(missing_player.sum())
    df = df.loc[~missing_player].copy()

    # A repeated (match, inning, over, ball) is legitimate when there are
    # extra deliveries (wides / no-balls) in the same over, so we only report
    # rows that are identical in EVERY column and do not delete them.
    notes["deliveries_exact_duplicate_rows"] = int(df.duplicated(keep="first").sum())

    # Innings 3+ are super overs. They are kept but flagged and excluded from
    # normal batting / bowling statistics.
    df["is_super_over"] = ~df["inning"].isin(REGULAR_INNINGS)
    notes["deliveries_super_over_rows"] = int(df["is_super_over"].sum())

    extra = df["extras_type"].fillna("")
    df["is_wide"] = extra.eq("wides")
    df["is_noball"] = extra.eq("noballs")
    df["is_legal_ball"] = ~(df["is_wide"] | df["is_noball"])           # counts toward overs bowled
    df["is_ball_faced"] = ~(df["is_wide"] | extra.eq("penalty"))        # a no-ball IS faced by the batter
    # Runs charged to the bowler: bat runs + wides + no-balls (not byes, leg-byes, penalty).
    chargeable_extra = df["extra_runs"].where(df["is_wide"] | df["is_noball"], 0)
    df["bowler_runs"] = (df["batsman_runs"] + chargeable_extra).astype("int32")
    kind = df["dismissal_kind"].fillna("")
    df["is_bowler_wicket"] = df["is_wicket"].eq(1) & kind.isin(BOWLER_WICKET_KINDS)
    df["is_dismissal"] = df["is_wicket"].eq(1) & ~kind.isin(NOT_A_DISMISSAL)

    for col in ("batting_team", "bowling_team", "batter", "bowler", "non_striker", "player_dismissed",
                "extras_type", "dismissal_kind", "fielder"):
        df[col] = df[col].astype("category")
    return df.reset_index(drop=True), notes


# ---------------------------------------------------------------- joining
def check_id_consistency(matches: pd.DataFrame, deliveries: pd.DataFrame) -> dict:
    """Compare match identifiers between the two tables."""
    match_ids, delivery_ids = set(matches["match_id"]), set(deliveries["match_id"].unique())
    return {
        "ids_in_deliveries_not_in_matches": len(delivery_ids - match_ids),
        "ids_in_matches_without_deliveries": len(match_ids - delivery_ids),
    }


def add_innings_info(matches: pd.DataFrame, deliveries: pd.DataFrame) -> pd.DataFrame:
    """Add batting-first / batting-second teams and innings totals to matches.

    Totals use the two regular innings only (no super overs). Deliveries are
    aggregated to ONE row per match and innings before merging, so matches
    and deliveries are never double-counted.
    """
    reg = deliveries[~deliveries["is_super_over"]]
    totals = (reg.assign(batting_team=reg["batting_team"].astype(str))
              .groupby(["match_id", "inning"])
              .agg(team=("batting_team", "first"), runs=("total_runs", "sum"), wickets=("is_wicket", "sum"))
              .reset_index())
    first = totals[totals["inning"] == 1].set_index("match_id")
    second = totals[totals["inning"] == 2].set_index("match_id")
    out = matches.copy()
    out["batting_first"] = out["match_id"].map(first["team"])
    out["batting_second"] = out["match_id"].map(second["team"])
    out["first_innings_runs"] = out["match_id"].map(first["runs"])
    out["second_innings_runs"] = out["match_id"].map(second["runs"])
    known = out["decisive"] & out["batting_first"].notna()
    out["won_batting_first"] = np.where(known, (out["winner"] == out["batting_first"]).astype(float), np.nan)
    return out


# ------------------------------------------------------------ main entry
def prepare_data(raw_matches: pd.DataFrame, raw_deliveries: pd.DataFrame | None = None) -> IPLData:
    """Run the full cleaning pipeline and build the data-quality report."""
    matches, quality = clean_matches(raw_matches)
    if matches.empty:
        raise DataValidationError("matches.csv has no usable rows after cleaning.")
    deliveries = None
    if raw_deliveries is not None:
        deliveries, dq = clean_deliveries(raw_deliveries)
        quality.update(dq)
        if deliveries.empty:
            deliveries = None
        else:
            quality.update(check_id_consistency(matches, deliveries))
            matches = add_innings_info(matches, deliveries)
            # Keep only deliveries that belong to a known match.
            deliveries = deliveries[deliveries["match_id"].isin(matches["match_id"])].reset_index(drop=True)
    for col in ("batting_first", "batting_second", "first_innings_runs", "second_innings_runs", "won_batting_first"):
        if col not in matches.columns:
            matches[col] = np.nan
    quality["seasons"] = sorted(matches["season"].unique().tolist())
    quality["date_min"] = matches["date"].min()
    quality["date_max"] = matches["date"].max()
    quality["teams"] = sorted(set(matches["team1"]) | set(matches["team2"]))
    logger.info("Prepared data: %d matches, %s deliveries", len(matches), 0 if deliveries is None else len(deliveries))
    return IPLData(matches=matches, deliveries=deliveries, quality=quality)


QUALITY_LABELS = {
    "matches_rows_raw": "Match rows in file",
    "matches_invalid_id": "Match rows with invalid id (dropped)",
    "matches_duplicate_ids_removed": "Duplicate match ids removed",
    "matches_invalid_season": "Match rows with unreadable season (dropped)",
    "matches_invalid_date": "Match rows with missing/invalid date",
    "matches_decisive": "Matches with a result (won by runs/wickets)",
    "matches_tie": "Tied matches (decided by super over)",
    "matches_no_result": "No-result / abandoned matches (no winner)",
    "matches_winner_not_a_team": "Decisive matches whose winner is neither team",
    "matches_same_team_twice": "Matches with team1 = team2",
    "matches_missing_venue": "Matches with missing venue",
    "matches_missing_player_of_match": "Matches without Player of the Match",
    "deliveries_rows_raw": "Delivery rows in file",
    "deliveries_invalid_numeric_rows": "Delivery rows with invalid numbers (dropped)",
    "deliveries_missing_batter_or_bowler": "Delivery rows missing batter/bowler (dropped)",
    "deliveries_exact_duplicate_rows": "Delivery rows identical in every column (kept, flagged)",
    "deliveries_super_over_rows": "Super-over delivery rows (excluded from player stats)",
    "ids_in_deliveries_not_in_matches": "Match ids in deliveries but not in matches",
    "ids_in_matches_without_deliveries": "Matches without ball-by-ball data",
}


def quality_table(quality: dict) -> pd.DataFrame:
    """Turn the quality dict into a readable two-column table."""
    rows = [(label, quality[key]) for key, label in QUALITY_LABELS.items() if key in quality]
    return pd.DataFrame(rows, columns=["Check", "Count"])
