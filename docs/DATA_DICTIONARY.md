# Data Dictionary

Schema taken from the real files in `data/`. "Used" says where the column matters in the project.

## matches.csv (raw columns)
| Column | Meaning | Type | Example | Used for |
|---|---|---|---|---|
| `id` | Unique match id (renamed `match_id`) | integer | 335982 | Joining with deliveries |
| `season` | Season year | integer | 2008 | Season filters and trends |
| `city` | City of the match (51 missing) | text | Bangalore | Venue summary |
| `date` | Match date | date text | 2008-04-18 | Date coverage, ordering |
| `match_type` | Stage | text | League, Final, Qualifier 1 ... | Stage filter, finals |
| `player_of_match` | Player of the Match (5 missing) | text | BB McCullum | Awards ranking |
| `venue` | Stadium name | text | M Chinnaswamy Stadium | Venue analysis |
| `team1`, `team2` | The two teams | text | Kolkata Knight Riders | Team tables |
| `toss_winner` | Team that won the toss | text | Royal Challengers Bangalore | Toss analysis |
| `toss_decision` | `bat` or `field` | text | field | Toss analysis |
| `winner` | Winning team (for ties: super-over winner; blank for no result) | text | Kolkata Knight Riders | Wins |
| `result` | `runs`, `wickets`, `tie`, `no result` | text | runs | Outcome label |
| `result_margin` | Margin of victory (blank for tie / no result) | number | 140 | Descriptive statistics |
| `target_runs`, `target_overs` | Target in the chase (D/L adjusted if needed) | number | 223, 20 | Not used |
| `super_over` | `Y` if a super over was played | text | N | Tie flag |
| `method` | `D/L` when Duckworth-Lewis applied | text | D/L | Informational |
| `umpire1`, `umpire2` | Umpires | text | Asad Rauf | Not used |

**Columns added by cleaning:** `match_id`, `season_label`, `outcome` (decisive / tie / no result), `decisive` (True/False),
`*_original` (names before standardising), `batting_first`, `batting_second`, `first_innings_runs`,
`second_innings_runs`, `won_batting_first`.

## deliveries.csv (raw columns)
| Column | Meaning | Type | Example | Used for |
|---|---|---|---|---|
| `match_id` | Match id (joins to `matches.id`) | integer | 335982 | Join |
| `inning` | 1, 2 = regular; 3-6 = super over | integer | 1 | Regular-innings filter |
| `batting_team`, `bowling_team` | Teams | text | Kolkata Knight Riders | Team batting / bowling |
| `over` | Over number, starting at 0 | integer | 0 | Runs by over (shown +1) |
| `ball` | Ball number within the over (extra deliveries repeat numbers) | integer | 1 | Ordering |
| `batter`, `bowler`, `non_striker` | Players | text | SC Ganguly | Player statistics |
| `batsman_runs` | Runs scored off the bat | integer | 4 | Runs, fours, sixes, strike rate |
| `extra_runs` | Extras on this ball | integer | 1 | Bowler runs, team totals |
| `total_runs` | `batsman_runs + extra_runs` | integer | 1 | Team totals, KPI |
| `extras_type` | wides, noballs, byes, legbyes, penalty, or blank | text | legbyes | Legal balls, balls faced |
| `is_wicket` | 1 if a wicket fell | integer | 0 | Wicket counts |
| `player_dismissed` | Batter who was out | text | RG Sharma | Batting average |
| `dismissal_kind` | How the batter was out | text | caught | Dismissal types, bowler wickets |
| `fielder` | Fielder involved | text | MS Dhoni | Not used |

**Columns added by cleaning:** `is_super_over`, `is_wide`, `is_noball`, `is_legal_ball`, `is_ball_faced`, `bowler_runs`,
`is_bowler_wicket`, `is_dismissal`.

## Derived metrics (formulas)
| Metric | Formula |
|---|---|
| Win % (decided) | wins / (wins + losses) x 100 |
| Win % (all) | wins / all matches played x 100 |
| Toss-winner win % | matches where toss winner = winner / decisive matches x 100 |
| Strike rate | batter runs / balls faced x 100 |
| Batting average | batter runs / dismissals |
| Economy | bowler runs x 6 / legal balls |
| Bowling average | bowler runs / wickets |
| Bowling strike rate | legal balls / wickets |
