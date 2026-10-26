# IPL Performance Analysis Using Data Analytics - "IPL InsightX"

## 1. Title page
| | |
|---|---|
| Project title | IPL Performance Analysis Using Data Analytics (application name: IPL InsightX) |
| Subject | Data Science and Ecosystem - Analytics theme |
| Submitted by | *[Your name, register number]* |
| Department / College | *[Department, College name]* |
| Guide / Faculty | *[Faculty name]* |
| Academic year | *[Year]* |

## 2. Abstract
IPL InsightX is a local web application that analyses 17 seasons (2008-2024) of Indian Premier League data: 1,095 matches
and 260,920 ball-by-ball records. A documented cleaning pipeline standardises team and venue names, separates decisive,
tied and no-result matches, and removes super overs from player statistics. The Streamlit dashboard provides team,
player, batting, bowling, toss, venue and season analysis with interactive filters, downloadable tables and
auto-generated insights. All statistics are computed from the data; none are typed in. The work is validated by 60 automated tests and
an executed Jupyter notebook. The study is descriptive: it reports patterns, not causes or predictions.

## 3. Introduction
Cricket generates detailed data, and the IPL has been recorded ball by ball since 2008. Data analytics turns such records
into understandable evidence about how teams and players perform.

## 4. Problem statement
Raw IPL data cannot be summarised by simply counting rows: some matches are tied or abandoned, teams were renamed, a wide
is not a ball faced, and a run out is not a bowler's wicket. The problem is to produce correct, reproducible and
explainable performance statistics, and to present them in an interactive form.

## 5. Objectives
1. Load and validate historical IPL match and delivery data.
2. Clean it reproducibly and report data quality.
3. Analyse teams, batters, bowlers, toss decisions, venues and seasons with documented formulas.
4. Provide filters, charts, downloads and generated insights in a dashboard.
5. Document and test the work.

## 6. Scope
In scope: descriptive and comparative analytics on the supplied dataset. Out of scope: machine learning, match
prediction, live data, fantasy-sports advice, fielding analysis, player salaries.

## 7. Existing system
Official IPL and cricket websites publish tables and records but not customisable, explainable analysis. Public notebooks
often count tied or abandoned matches incorrectly, treat all extras as the bowler's runs, or ignore renamed teams.

## 8. Proposed system
A Streamlit application with a reusable Python analytics layer. Definitions are explicit, denominators are shown, and the
same code serves the app, the notebook and the tests.

## 9. System requirements
| | |
|---|---|
| OS | Windows 10/11 (also runs on macOS/Linux) |
| Python | 3.11 or newer (built with 3.12.10) |
| RAM | about 2 GB free while loading |
| Disk | about 100 MB including the data |
| Network | only for installing packages and viewing plotly.js in the notebook |

## 10. Technology stack
Streamlit 1.66 (interface), Pandas 3.1 and NumPy 2.5 (data), Plotly 7.1 (interactive charts), Matplotlib 3.11 and
Seaborn 0.13 (notebook charts), Jupyter/ipykernel (notebook), Pytest 9 (tests), Python `logging` (diagnostics).

## 11. Dataset description
Two CSV files: `matches.csv` (1,095 rows, 20 columns) and `deliveries.csv` (260,920 rows, 17 columns), seasons 2008-2024,
dates 18 Apr 2008 to 26 May 2024. Source, licence and caveats: `data/DATASET_GUIDE.md`. Columns: `docs/DATA_DICTIONARY.md`.

## 12. Data collection methodology
The files were downloaded from a public GitHub repository (no login, no API key) and stored unchanged. The repository does
not state the original source; the layout matches a Cricsheet-based Kaggle dataset. This is not independently confirmed (see the guide).

## 13. Data preprocessing
Verified results of the quality checks on the real files:
* 0 invalid ids, 0 duplicate match ids, 0 unreadable seasons or dates, 0 invalid delivery numbers, 0 match-id mismatches between files.
* Outcomes: 1,076 decisive, 14 tied, 5 no-result matches.
* 4 team names standardised; 15 franchises remain. Venue spellings merged (original venue count shown in the notebook).
* 161 super-over delivery rows excluded from player statistics.
* 5 matches have no Player of the Match.

## 14. Exploratory data analysis
The notebook `notebooks/ipl_exploratory_data_analysis.ipynb` follows the sequence load -> inspect -> quality -> missing values ->
duplicates -> cleaning -> descriptive statistics -> team/player/toss/venue/season analysis -> charts -> findings -> limitations.
It was executed on the real data (31 code cells, no errors).

## 15. System architecture
```
data/*.csv -> data_loader (chunked read, strip) -> data_cleaning (validate, standardise, label, helper columns)
           -> IPLData bundle (cached by Streamlit)
           -> analytics modules (team, batting, bowling, player, toss, venue, season, insights)
           -> ui.py (global filters, charts, downloads) -> app.py + pages/1..8
```

## 16. Methodology
See `docs/METHODOLOGY.md`.

## 17. Module descriptions
| Module | Role |
|---|---|
| `data_loader.py` | Reads CSVs safely, friendly errors |
| `data_cleaning.py` | Column aliases, validation, standardisation, outcome labels, helper columns, quality report |
| `team_analytics.py` | Wins, losses, ties, win %, head-to-head, venue and bat-first/chase records |
| `batting_analytics.py` | Runs, balls, strike rate, average, highest score, over-wise and team scoring |
| `bowling_analytics.py` | Wickets, economy, average, strike rate, dismissal types, venue/season bowling |
| `player_analytics.py` | Profiles, comparison, Player of the Match |
| `toss_analytics.py` | Toss vs result, chase vs defend, venue toss trends |
| `venue_analytics.py`, `season_analytics.py` | Venue and season summaries |
| `insights.py` | KPIs and auto-generated, sourced insights |
| `ui.py` | Page setup, cached loading, filters, chart style, CSV downloads |

## 18. Important formulas
Win % (decided) = wins / (wins + losses) x 100 | Strike rate = runs / balls x 100 | Batting average = runs / dismissals |
Economy = runs x 6 / legal balls | Bowling average = runs / wickets | Bowling strike rate = balls / wickets |
Toss-winner win % = toss winner won / decisive matches x 100.

## 19. Results and discussion
### Verified results (calculated by the application/notebook on the supplied dataset)
| Measure | Result |
|---|---|
| Matches / teams / seasons | 1,095 / 15 / 17 |
| Players seen in ball-by-ball data | 732 |
| Total runs (regular innings, incl. extras) / dismissals | 347,470 / 12,908 |
| Most wins | Mumbai Indians, 142 wins in 261 matches |
| Most runs | V Kohli, 8,004 runs in 244 innings |
| Most wickets | YS Chahal, 205 |
| Most Player of the Match awards | AB de Villiers, 25 |
| Busiest season / venue | 2013 (76 matches) / Wankhede Stadium, Mumbai (118 matches) |
| Highest team total | 287 by Sunrisers Hyderabad (2024, M Chinnaswamy Stadium) |
| Toss winner also won the match | 548 of 1,076 decisive matches = 50.9% |
| Toss winner who chose to field / bat won | 374 of 692 = 54.0% / 174 of 384 = 45.3% |
| Won batting first vs chasing | 492 (45.7%) vs 584 (54.3%) |
| Most common toss decision | field (704 of 1,095 matches) |

### Discussion
The toss winner won barely more than half of decisive matches, so the toss alone is a weak indicator. Chasing teams won
more often than teams batting first in this dataset. These are observed patterns; they do not show cause, and results
for individual teams or venues rest on smaller samples (the app shows the counts).

### Expected outputs (not results)
Rankings and percentages change when the season range, teams, venues or stage filters change; the numbers above apply to
the full dataset only. Re-run the app or notebook to reproduce them.

### Testing
60 automated tests passed on the final run (45 unit tests on synthetic data; 15 integration tests on the real data that check the pages run
without errors). Chart appearance is not covered by the automated tests; the pages were also opened in a real Chrome browser (headless) and inspected by eye, which found and fixed a season-axis ordering bug and a truncated KPI card.

## 20. Limitations
* Dataset may differ slightly from official records; provenance not independently verified.
* Super overs excluded; ties not counted as wins.
* Fours/sixes are counted from runs off the bat, not boundary flags.
* Franchise continuity is a judgement (documented merges only).
* Venue and team subsets can have small samples.
* No fielding, player role, pitch, weather or opposition-strength data.
* Descriptive only; no prediction.

## 21. Future enhancements
Player-vs-player matchups, phase analysis (powerplay/death) per player, adjusting for opposition strength, a data-update
script for new seasons, optional prediction models in a separate module (not part of this analytics project), deployment online.

## 22. Conclusion
The project delivers a tested, documented analytics application whose statistics follow explicit definitions and whose
conclusions stay within what the data supports.

## 23. References
1. Dataset files: https://github.com/avinashyadav16/ipl-analytics (Datasets folder).
2. Cricsheet ball-by-ball data: https://cricsheet.org (possible original source; verify before citing).
3. Kaggle, "IPL Complete Dataset (2008-2024)" by patrickb1912 (possible related source; verify before citing).
4. Streamlit documentation: https://docs.streamlit.io
5. Pandas documentation: https://pandas.pydata.org/docs
6. Plotly Python documentation: https://plotly.com/python
7. McKinney, W. *Python for Data Analysis*, O'Reilly.
