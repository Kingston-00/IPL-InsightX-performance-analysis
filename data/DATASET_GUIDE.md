# Dataset Guide

## Source
| Item | Detail |
|---|---|
| Files used | `matches_2008-2024.csv` and `deliveries_2008-2024.csv` |
| Downloaded from | https://github.com/avinashyadav16/ipl-analytics (folder `Datasets`, repository licence: Apache-2.0) |
| Direct links | https://raw.githubusercontent.com/avinashyadav16/ipl-analytics/main/Datasets/matches_2008-2024.csv and https://raw.githubusercontent.com/avinashyadav16/ipl-analytics/main/Datasets/deliveries_2008-2024.csv |
| Downloaded on | 26 October 2026 (no login or API key needed) |
| Saved as | `data/matches.csv` and `data/deliveries.csv` - **byte-for-byte as downloaded, not edited** |

**Provenance note.** The repository above does not state where the data originally came from. The column layout matches the
public Kaggle dataset "IPL Complete Dataset (2008-2024)" by *patrickb1912*, which credits ball-by-ball data from
[Cricsheet](https://cricsheet.org). This project has **not** independently confirmed that link, so before citing the original
source in your report, open the Kaggle page and Cricsheet and cite what you can verify. The Kaggle download needs a
free login; if you prefer it, download the two files there and save them with the names above.

## Files required
| File | One row is | Rows in this copy |
|---|---|---|
| `data/matches.csv` | one match | 1,095 |
| `data/deliveries.csv` | one delivery (ball) | 260,920 |

## Expected columns
**matches.csv (required):** `id`, `season`, `team1`, `team2`, `toss_winner`, `toss_decision`, `winner`, `venue`.
Optional but used when present: `date`, `city`, `match_type`, `player_of_match`, `result`, `result_margin`, `target_runs`,
`target_overs`, `super_over`, `method`, `umpire1`, `umpire2`.

**deliveries.csv (required):** `match_id`, `inning`, `batting_team`, `bowling_team`, `over`, `ball`, `batter`, `bowler`,
`batsman_runs`, `extra_runs`, `total_runs`, `is_wicket`.
Optional but used when present: `extras_type`, `non_striker`, `player_dismissed`, `dismissal_kind`, `fielder`.

Other common names are accepted (for example `batsman` for `batter`, `batter_runs` for `batsman_runs`); see
`MATCH_ALIASES` and `DELIVERY_ALIASES` in `src/data_cleaning.py`.

## Coverage (measured by the application on these files)
* Seasons 2008 to 2024 (17 seasons, no gaps); match dates 18 April 2008 to 26 May 2024.
* 1,095 matches: 1,076 decided by runs/wickets, 14 tied (settled by a super over), 5 with no result.
* Every match id in `matches.csv` has ball-by-ball data and vice versa (0 mismatches).
* 161 super-over delivery rows (innings 3 to 6).
* The application never assumes a particular latest season: seasons are detected from the file.

## Data limitations
* Not an official IPL record. Totals can differ slightly from official statistics.
* `deliveries.csv` is padded with spaces to fixed width (72 MB); the loader strips them.
* 5 matches have no winner or Player of the Match; `city` is missing for 51 matches; `result_margin` is missing for ties and no-results.
* The data cannot separate a boundary four from four run-along runs, so "fours" means "deliveries where the bat scored exactly 4".
* No player roles, fielding positions or ball-tracking data.

## Transformations performed (in memory only; the CSV files are never modified)
1. Strip padding spaces; convert `NA` text to missing values.
2. Rename column aliases to standard names; convert ids, seasons, dates and ball-by-ball numbers (invalid rows are counted, not hidden).
3. Standardise team names: Delhi Daredevils -> Delhi Capitals; Kings XI Punjab -> Punjab Kings; Royal Challengers Bangalore -> Royal Challengers Bengaluru; Rising Pune Supergiants -> Rising Pune Supergiant. Original names are kept in `*_original` columns.
   Not merged (different franchises): Deccan Chargers / Sunrisers Hyderabad, Pune Warriors / Rising Pune Supergiant, Gujarat Lions / Gujarat Titans.
4. Merge spelling variants of the same stadium (for example "Feroz Shah Kotla" -> "Arun Jaitley Stadium, Delhi"; three Chinnaswamy spellings). Full list: `VENUE_NAME_MAP` in `src/data_cleaning.py`. The original is kept in `venue_original`.
5. Label every match `decisive`, `tie` or `no result`.
6. Flag super-over innings and exclude them from batting/bowling statistics.
7. Add per-match batting-first / batting-second teams and innings totals (one row per match; no double counting).
8. Add per-delivery helper columns (legal ball, ball faced, runs charged to bowler, wicket credited to bowler).
