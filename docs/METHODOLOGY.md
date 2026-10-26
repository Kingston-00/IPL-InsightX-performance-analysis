# Methodology

## 1. Data acquisition
Two CSV files (matches and deliveries) were downloaded from a public GitHub repository (Apache-2.0) and saved unchanged
in `data/`. No API key or login was required. Source and provenance caveats: `data/DATASET_GUIDE.md`.

## 2. Data validation (`src/data_loader.py`, `src/data_cleaning.py`)
* Files must exist, be non-empty and parse as CSV, otherwise a `DataFileError` with a plain message is raised; the app shows a setup page.
* Required columns are checked after renaming known aliases; all missing columns are listed in one `DataValidationError`.
* Match ids are compared between the two files (ids only in one file are counted and reported; unknown ids are dropped from deliveries).
* Numeric columns are converted with `errors="coerce"`; invalid rows are counted in the quality summary.
* Sanity checks: winner must be one of the two teams, team1 != team2, venue and Player of the Match missing counts.

## 3. Data cleaning
1. Read as text in chunks; strip padding; `NA` -> missing.
2. Normalise column names (lower snake case + alias table).
3. Remove duplicate match ids (none found in this dataset).
4. Delivery rows are **not** de-duplicated on (match, inning, over, ball) because wides/no-balls legitimately repeat a ball number; only rows identical in every column are reported (none found).
5. Standardise renamed teams and merge venue spelling variants (documented dictionaries; originals retained).
6. Classify each match: `decisive` (runs/wickets and has a winner), `tie`, `no result`. A missing winner is **not** treated as an error.
7. Mark innings 3+ as super overs and exclude them from player statistics.

## 4. Feature preparation
Per delivery: `is_legal_ball` (not a wide/no-ball), `is_ball_faced` (not a wide/penalty), `bowler_runs` (bat runs + wides + no-ball extras),
`is_bowler_wicket` (bowled, caught, caught and bowled, lbw, stumped, hit wicket), `is_dismissal` (any wicket except retired hurt).
Per match: batting-first/second team and innings totals, aggregated to **one row per match and innings before merging** so nothing is double counted.

## 5. Exploratory analysis
Counts, group-bys and descriptive statistics (`describe`, correlation) in `notebooks/ipl_exploratory_data_analysis.ipynb`, using the same functions as the app.

## 6. Statistical calculations
| Quantity | Definition |
|---|---|
| Win | decisive match won by the team |
| Loss | decisive match won by the opponent |
| Win % (decided) | wins / (wins + losses) x 100 |
| Win % (all) | wins / matches played x 100 |
| Toss-winner win % | (decisive matches where toss winner = winner) / decisive matches x 100 |
| Strike rate | batter runs / balls faced x 100 |
| Batting average | batter runs / dismissals (blank if never dismissed) |
| Economy | runs charged to bowler x 6 / legal balls |
| Bowling average / strike rate | runs / wickets ; legal balls / wickets |
| Innings | a (match, inning) in which the player faced a ball or was dismissed |
| KPI wickets | all dismissals except retired hurt, regular innings |

All divisions use `safe_divide`, which returns "not available" instead of raising an error when the denominator is zero.
Minimum-sample thresholds (balls faced, legal balls, matches) are user-adjustable and always displayed.

## 7. Visualisation
Plotly for interactive charts (hover shows sample sizes), Matplotlib/Seaborn in the notebook. One accent colour for single
series, a fixed colour order for multiple series, titled axes, no dual-axis charts. The app theme is dark navy with blue and gold accents.

## 8. Interpretation rules
Toss, chasing and venue results are described as **observed patterns**. Win percentages show their denominator; small
samples are flagged by showing counts beside percentages. No causal statements, no predictions.

## 9. Testing
* 45 unit tests on small synthetic datasets with hand-calculated expected values (cleaning, wins, win %, run totals, wickets, toss, empty data, zero denominators, no-winner matches, filtering).
* 15 integration tests that run all 9 pages, the sidebar filters, an empty-filter case and the missing-file setup page against the real data (they only check that the app runs without raising exceptions and shows the expected messages; they do not verify chart appearance).
* Synthetic data appears only in tests and is never shown as IPL results.
* The notebook was executed top to bottom on the real data without errors.

## 10. Limitations
See `docs/PROJECT_REPORT.md`, section 20.
