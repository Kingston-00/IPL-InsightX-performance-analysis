# Dashboard Guide - what happens in every section and table

This guide explains, page by page, what each chart, card and table shows and what operation produces it. File names in
brackets show where the calculation lives. All numbers are computed from `data/matches.csv` and `data/deliveries.csv`;
nothing is typed in by hand.

---
## 1. What happens before any page opens (the data pipeline)

| Step | Operation | Where |
|---|---|---|
| 1. Read | The CSVs are read in chunks of 20,000 rows as plain text. Spaces padded around headers/values are stripped and the text `NA` becomes a real missing value. Missing/empty/unreadable files give a friendly setup page (and a "not enough memory" message if RAM runs out). | `data_loader.py` |
| 2. Rename columns | Names are lower-cased and aliases are mapped (`id` -> `match_id`, `batsman` -> `batter`, ...). Required columns are checked; every missing one is listed. | `data_cleaning.py` |
| 3. Convert types | Ids, ball numbers, runs and wicket flags become integers; dates become dates; `season` becomes a year (`2007/08` would become 2008). Rows with invalid numbers are counted and dropped, never hidden. | `clean_matches`, `clean_deliveries` |
| 4. Remove duplicates | Duplicate **match ids** are dropped (none found). Deliveries are NOT de-duplicated on over/ball, because wides and no-balls legitimately repeat a ball number; only fully identical rows are counted and reported. | same |
| 5. Standardise names | Renamed teams are merged (Delhi Daredevils -> Delhi Capitals, Kings XI Punjab -> Punjab Kings, Royal Challengers Bangalore -> Bengaluru, Rising Pune Supergiants -> Supergiant). Spelling variants of the same stadium are merged. Originals are kept in `*_original` columns. | `TEAM_NAME_MAP`, `VENUE_NAME_MAP` |
| 6. Label outcomes | Each match becomes **decisive** (won by runs/wickets), **tie** (settled by super over) or **no result**. A missing winner is not treated as an error. | `clean_matches` |
| 7. Flag deliveries | Adds: `is_super_over` (innings 3+), `is_wide`, `is_noball`, `is_legal_ball` (not wide/no-ball), `is_ball_faced` (not wide/penalty), `bowler_runs` (bat runs + wides + no-ball extras), `is_bowler_wicket`, `is_dismissal`. | `clean_deliveries` |
| 8. Join safely | Deliveries are summed to **one row per match and innings** (regular innings only) and joined to matches to get `batting_first`, `batting_second`, `first_innings_runs`, `second_innings_runs`, `won_batting_first`. No match is duplicated. | `add_innings_info` |
| 9. Quality report | Counts of every problem found (the "Data-quality summary" box on the home page). | `quality_table` |
| 10. Cache | The cleaned result is cached by Streamlit; it reloads only if the CSV files change (size/modified time are the cache key). | `ui._load_cached` |

## 2. Sidebar filters (same on every page)
| Filter | Operation |
|---|---|
| Season range | Keeps matches whose season is inside the range. |
| Teams | Keeps matches where **either** team1 or team2 is selected. |
| Venues | Keeps matches at the selected (merged) venues. |
| Match stage | League, Qualifier 1, Eliminator, Final, ... |
| Result type | Won by runs/wickets, Tie, or No result. |
| Reset filters | Restores all filters. |
| Blue info box | Describes the current filters and the number of matches left. |

The deliveries are then filtered to the ball-by-ball rows of exactly those matches, so charts based on matches and charts
based on balls always agree. Choices are remembered when you move to another page. Options only list values that exist in
the chosen seasons, so you cannot pick a team that never played in that range. If the filters leave no matches, a message
asks you to widen them.

---
## 3. Home dashboard (`app.py`)
| Section | What it shows | Operation |
|---|---|---|
| Header + coverage line | Title, seasons available, date range, number of matches and deliveries | Min/max of season and date from the data |
| **KPI cards** | Matches, Teams, Players, Total runs, Wickets, Seasons | Matches = rows; Teams = distinct names in team1+team2; Players = distinct batter, non-striker and bowler names; Total runs = sum of `total_runs` (includes extras) in regular innings; Wickets = dismissals that ended an innings (retired hurt excluded); Seasons = distinct seasons |
| **Team performance** | Horizontal bar chart of wins per team + expandable team table (download) | `team_summary()` - see table definitions below |
| **Season trends** | Matches per season (bars) and average innings score per season (line) | `season_overview()`; `season_runs()` = total runs / innings per season |
| **Top players** | Three bar charts: most runs, most wickets, most Player of the Match awards (top 10) | `batting_stats()` sorted by runs; `bowling_stats()` sorted by wickets (wickets > 0); `player_of_match_counts()` |
| **Toss insights** | Card: % of decisive matches the toss winner also won. Grouped bars: toss winner won/lost by toss decision | `toss_win_match_win()`, `toss_decision_outcomes()` |
| **Quick insights** | Six sentences generated from the selection | `generate_insights()` |
| Download + quality box | Filtered match records CSV; data-quality table and limitations | `download_matches()`, `quality_table()` |

## 4. Team Analytics page
| Section | Content | Operation |
|---|---|---|
| Definitions box | How wins, losses, ties, win % are defined | Text |
| **Team summary** table + download | One row per team | `team_match_table()` makes one row per team per match (each match appears twice). `won` = decisive and winner == team; `lost` = decisive and winner != team; `tied`; `no_result`. Rows are grouped by team and summed. |
| Wins/losses/ties/no-results chart | Grouped bars per team | Same table, reshaped with `melt` |
| Win % chart | Bars of win % (decided) | `wins / (wins + losses) x 100` |
| **Season-wise performance** | Pick teams and a metric (wins or win %) -> line chart and grouped bars; download | `season_team_summary()` (same summary grouped by season and team) |
| **Team versus team** | Choose a team -> wins/losses against each opponent + table | `head_to_head()` (grouped by team and opponent) |
| **Performance by venue** | Choose team and minimum matches -> win % per venue + table | `venue_team_summary()` |
| **Batting first vs chasing** | Win % of each team when batting first and when chasing; download | `batting_first_vs_chasing()`: decisive matches with known innings order, grouped by team and role |

**Team summary columns:** `matches` (played) | `wins` | `losses` | `ties` | `no_results` | `decided` (= wins + losses) |
`win_pct_decided` (= wins / decided x 100) | `win_pct_all` (= wins / matches x 100). Division by zero gives "not available".

## 5. Player Analytics page
| Section | Content | Operation |
|---|---|---|
| Player selector | Every player in the selection | Names from batter, non-striker, bowler and award columns |
| **Batting cards** | Runs, innings, average, strike rate, highest score, balls faced, fours, sixes, Player of the Match | `player_profile()` reads the player's row from `batting_stats()` |
| **Bowling cards** | Wickets, legal balls, runs conceded, economy, average, strike rate | Player's row from `bowling_stats()`; cards show *n/a* when the player never bowled |
| Runs per season chart | Bars | `batting_innings()` joined with season |
| **Compare players** | Select 2+ players -> table, chart of any chosen metric, download | `compare_players()`; missing statistics show "None" |
| Player of the Match table | Awards ranking | Count of `player_of_match` per name |

## 6. Batting Analytics page
| Section | Content | Operation |
|---|---|---|
| Sliders | Players to show; minimum balls faced for strike-rate ranking (default 300) | Ranking only includes batters with `balls >= threshold` |
| **Leaderboard tabs** | Most runs / fours / sixes / best strike rate (bar charts) + full stats table (first 100 rows) + download | `batting_stats()` |
| **Team batting** | Runs per team (bar), table with wickets lost, innings, run rate, average innings score | `team_batting_summary()`: run rate = runs x 6 / legal balls |
| **Scoring trends** | Run rate by season; run rate in each over (1-20); distribution of runs off the bat per ball | `season_runs()`, `runs_by_over()`, `runs_distribution()` |
| Compare batters | Table + average vs strike rate bars | Filter of the stats table |

**Batting table columns:** `innings` (match-innings in which the player faced a ball or was dismissed) | `runs` (off the bat) | `balls`
(faced; wides excluded) | `fours` / `sixes` (deliveries with exactly 4 / 6 off the bat) | `dismissals` (wickets where the player is
`player_dismissed`, retired hurt excluded) | `highest_score` (max runs in one innings) | `average` (runs / dismissals, blank if never out) |
`strike_rate` (runs / balls x 100).

## 7. Bowling Analytics page
| Section | Content | Operation |
|---|---|---|
| Sliders | Players to show; minimum legal balls (default 300 = 50 overs) | Economy/average/strike-rate rankings only include bowlers above it |
| **Leaderboard tabs** | Most wickets, best economy, best average, best strike rate, most runs conceded + table + download | `bowling_stats()` |
| **Teams and seasons** | Wickets by bowling team (bar + table); economy by season (line) | `team_bowling_summary()`, `bowling_by_season()` |
| **Dismissal types** | Bar of all dismissals by kind, coloured by credited-to-bowler or not | `dismissal_types()` |
| **Compare bowlers and venues** | Table for chosen bowlers; economy per venue (minimum balls slider) + table + download | `bowling_by_venue()` |

**Bowling table columns:** `matches` | `legal_balls` (not wide/no-ball) | `overs` (12.3 = 12 overs 3 balls) | `runs_conceded` (bat runs + wides +
no-ball runs; byes, leg-byes, penalty excluded) | `wickets` (bowled, caught, caught & bowled, lbw, stumped, hit wicket; run outs excluded) |
`economy` (runs x 6 / legal balls) | `average` (runs / wickets) | `strike_rate` (legal balls / wickets).

## 8. Toss and Match Analysis page
| Section | Content | Operation |
|---|---|---|
| Info + 4 cards | Decisive matches; toss winner won %; won batting first %; won chasing % | Denominator = decisive matches (ties/no-results excluded); counts shown in the card help text |
| **Toss decision and result** | Toss winner's win % by bat/field, toss decisions by season (stacked %), table + download | `toss_decision_outcomes()`, `toss_decisions_by_season()` |
| **Batting order check** | Cross-table: toss decision vs "toss winner really batted first" | Compares `toss_winner` with `batting_first` from the ball-by-ball data - proves the toss is not just assumed to decide batting order |
| **Chasing vs defending** | Win % per team as the defending (batting-first) and chasing side + table + download | `chase_defend_by_team()` |
| **Venue toss trends** | % of toss winners choosing to field per venue (minimum matches slider) + table | `toss_by_venue()` |
| **Result distribution** | Donut + table of won by runs / wickets / tie / no result; download of filtered match records | `wins_by_result_type()` |

## 9. Venue Analytics page
| Section | Content | Operation |
|---|---|---|
| Minimum matches slider | Hides venues with few matches | Filter on the summary |
| **Most-used venues** | Bar of matches per venue | `venue_summary()` |
| **Scoring and batting-first results** | Average first-innings score; % of decisive matches won by the team batting first | Mean of `first_innings_runs`; batting-first wins / decisive x 100 |
| Venue table + download | `matches`, `seasons_used`, `avg_first_innings`, `highest_total`, `decisive`, `batting_first_wins`, `chasing_wins`, `batting_first_win_pct` | `venue_summary()` |
| **Single venue summary** | Choose a venue -> 5 cards, team wins there, toss-decision donut, highest total | Matches filtered to that venue |
| **Venue usage by season** | Stacked bars of the 7 busiest venues + "Other venues"; download | `venue_usage_by_season()` |

## 10. Season Analytics page
| Section | Content | Operation |
|---|---|---|
| Overview | Matches per season, teams participating, table (`matches`, `teams`, `venues`, `avg_first_innings`) + download | `season_overview()` |
| Scoring | Total runs, runs per over, average first-innings score by season + download | `season_runs()` |
| **Season leaders** | Top run scorer and top wicket taker per season + download | `season_leaders()` runs `batting_stats` and `bowling_stats` for each season |
| **Most successful teams / champions** | Team(s) with the most wins each season; winner of the match labelled "Final" | `most_successful_team()`, `season_champions()` - most wins is not the same as champion |
| Team participation | Heat map: matches played by each team in each season | `season_team_participation()` |
| Player of the Match by season | Top award winner per season; all awards in an expander | `season_player_of_match()` |

## 11. Insights Explorer page
Each card shows **finding, value, sample size and how it is calculated**: most wins, highest win rate (teams with at least 20 decided
matches), busiest season, most-used venue, most common toss decision, toss vs match result, chasing vs defending, most Player of the
Match awards, highest team total, most runs, best strike rate (slider for minimum balls), most common scoring pattern, most wickets,
most common dismissal. Insights the data cannot support are skipped. The whole list downloads as a CSV together with the filters used
(`generate_insights()`, `insights_table()`).

## 12. Downloads
Team summary, season-wise team results, head-to-head, bat-first vs chase, player comparison, Player of the Match awards, batting
stats, team batting, season scoring/overview/leaders, bowling stats, bowling by venue, toss tables, venue summary and usage, insights
summary, and filtered match records. Each CSV contains exactly the rows shown after the current filters.

## 13. Key rules that prevent wrong numbers
1. Ties and no-results are never wins or losses.
2. Super overs are excluded from player and team innings statistics.
3. Extras are credited correctly (wide = not a ball faced; leg-byes are not the bowler's runs; run outs are not the bowler's wickets).
4. Every percentage shows or states its denominator and, on most tables, its sample size.
5. Division by zero returns "not available" instead of crashing or inventing a value.
6. Toss and venue results are described as observed patterns, never as causes.
