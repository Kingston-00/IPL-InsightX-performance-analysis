# IPL InsightX - IPL Performance Analysis Using Data Analytics

An interactive analytics dashboard for historical Indian Premier League data, built for the *Data Science and Ecosystem*
course (theme: **Analytics**). It covers team, player, batting, bowling, toss, venue and season analysis using 17 seasons
(2008-2024) of real match and ball-by-ball data.

## Problem statement
Raw cricket data is large and full of traps (ties, abandoned matches, renamed teams, extras that are nobody's fault).
The project turns it into correct, documented statistics that a beginner can explore, explain and defend in a viva.

## Objectives
Team performance, batting and bowling leaders, toss and chase patterns, venue statistics, season trends and data-driven
insights - every number calculated from the dataset and filtered consistently.

## Features
* Home dashboard with KPIs, team wins, season trends, top players, toss insights and quick insights.
* 8 pages: Team, Player, Batting, Bowling, Toss and Match, Venue, Season, and an *Insights Explorer*.
* Global sidebar filters (season range, teams, venues, match stage, result type) that persist across pages, plus a reset button.
* CSV download of every main table, including filtered match records and an insights summary.
* Data-quality summary and a helpful setup page if the CSV files are missing.
* Exploratory Jupyter notebook (executed on the real data) and 60 automated tests.

## Technology stack
Python 3.12, Streamlit, Pandas, NumPy, Plotly, Matplotlib, Seaborn, Jupyter, Pytest, `logging`.
No API keys, accounts or cloud services.

## Directory structure
```
app.py                  home dashboard
pages/                  the 8 analysis pages (Streamlit multipage)
src/                    data_loader, data_cleaning, *_analytics modules, insights, ui helpers
data/                   matches.csv, deliveries.csv, DATASET_GUIDE.md
notebooks/              ipl_exploratory_data_analysis.ipynb
tests/                  unit tests (synthetic data) + integration tests (real data)
docs/                   report, methodology, data dictionary, viva questions, presentation outline
assets/logo.svg         logo
.streamlit/config.toml  dark theme
```

## How the project works (beginner's guide)
Think of the project as a small factory with four stations:
1. **`data/`** - the raw material: two CSV tables (one row per match, one row per ball). Never edited.
2. **`src/data_loader.py` and `src/data_cleaning.py`** - the cleaning station: read the CSVs, strip stray spaces, fix types, rename old team names, label ties and abandoned matches, and report problems.
3. **`src/*_analytics.py`** - the calculators: each file answers one family of questions (teams, batting, bowling, players, toss, venues, seasons). They take a table in and give a table out, so they are easy to test.
4. **`app.py`, `pages/`, `src/ui.py`** - the shop window: Streamlit pages that call the calculators and draw charts, tables, filters and download buttons.

`tests/` checks the calculators with tiny made-up tables whose answers were worked out by hand, and checks that every page opens with the real data. `notebooks/` shows the same analysis step by step, and `docs/` holds the report, viva questions and presentation outline.

## Dataset requirements
`data/matches.csv` and `data/deliveries.csv` (already included). Source, columns, coverage and limitations:
`data/DATASET_GUIDE.md`. If you use other files, they need the required columns listed there.

## Installation (Windows PowerShell)
```powershell
# 1. Check Python (3.11 or newer; built with 3.12)
python --version

# 2. Create and activate a virtual environment inside the project folder
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
python -m pip install -r requirements.txt
```
If PowerShell says *running scripts is disabled*, either allow scripts for this window only:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```
or skip activation and call the environment's Python directly, e.g. `.\.venv\Scripts\python.exe -m streamlit run app.py`.

## Run the application
```powershell
streamlit run app.py
```
Open http://localhost:8501 if the browser does not open by itself. The first load takes a few seconds (cleaning
260,000 deliveries); after that it is cached.

## Run the notebook
```powershell
python -m jupyter notebook notebooks\ipl_exploratory_data_analysis.ipynb
```
The saved notebook was executed against the real dataset. Plotly charts load plotly.js from the internet when viewed.

## Run the tests
```powershell
python -m pytest -q
```
`tests/test_data_cleaning.py`, `test_team_analytics.py` and `test_player_analytics.py` use tiny **synthetic** data with
hand-calculated answers. `test_app_pages.py` and `test_app_filters.py` start every page headlessly against the **real**
data and are skipped automatically if the CSV files are absent.

## Common errors and solutions
| Problem | Fix |
|---|---|
| `streamlit` is not recognised | Activate the virtual environment, or use `.\.venv\Scripts\python.exe -m streamlit run app.py` |
| Page says "Dataset setup needed" | Put `matches.csv` and `deliveries.csv` in the `data` folder (see DATASET_GUIDE.md) and refresh |
| "missing required column(s)" | Your CSV uses other column names; compare with the required columns in DATASET_GUIDE.md |
| "No matches fit the current filters" | Press **Reset filters** in the sidebar |
| Port 8501 busy | `streamlit run app.py --server.port 8502` |
| "Dataset setup needed" even though the files are in `data` - message mentions memory, or `OpenBLAS error: Memory allocation failed` in the terminal | The computer is short of free RAM. Close browsers/other editors, then start with `run_app.bat` (double-click it) or in PowerShell: `$env:OPENBLAS_NUM_THREADS="1"; streamlit run app.py`. Loading needs roughly 0.5-1 GB free |

## Limitations
Results describe this dataset only and may differ slightly from official records; super overs are excluded from player
statistics; ties are not wins; toss and venue findings are descriptive patterns, not causes; no machine learning or
predictions are included (the theme is analytics). More in `docs/PROJECT_REPORT.md`.
