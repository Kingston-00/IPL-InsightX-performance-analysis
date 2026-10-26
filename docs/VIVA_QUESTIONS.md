# Viva Questions and Answers

Answers are written to be spoken. Where the answer is a number from the data, a **How to get it** line shows where to read the real value (open the app first; the numbers change with filters).

## A. Basics
**1. What is data analytics?**
Examining data to find patterns and answers that help decisions. Here: using IPL records to see which teams, players and conditions led to success.

**2. What is exploratory data analysis (EDA)?**
Looking at a dataset with summaries and charts before drawing conclusions: checking columns, missing values, ranges and relationships. Our notebook does this.

**3. What is Pandas?**
A Python library for tables of data (DataFrames): loading CSVs, filtering, grouping, joining and calculating.

**4. Why is NumPy used?**
It handles fast number arrays and special values like NaN (missing). We use it for conditions (`np.where`, `np.select`) and missing-number handling.

**5. What is data cleaning?**
Fixing or flagging problems so analysis is trustworthy: stray spaces, wrong types, duplicates, inconsistent names.

**6. What is a missing value?**
A cell with no data (shown as NaN). Example: `winner` is blank for abandoned matches. It may be a real "no result", not an error, so we do not fill it with a guess.

**7. What is a duplicate record?**
The same record stored twice. We removed duplicate match ids (none were found). We did **not** remove deliveries that repeat an over/ball number, because a wide or no-ball is a genuine extra delivery with the same ball number.

**8. What is a DataFrame?**
A table in Pandas with labelled rows and columns, like an Excel sheet inside Python.

**9. What is data visualization?**
Showing data as charts so patterns are quick to see.

**10. Why are bar charts useful?**
They compare amounts across categories, e.g. wins per team, and are easy to read.

**11. What is a histogram?**
A chart showing how often values fall into ranges. Our notebook uses one for innings totals.

**12. What is a correlation?**
A number from -1 to +1 showing how two measures move together. It does not prove one causes the other.

**13. What is a KPI?**
Key Performance Indicator - a headline number, like total matches or total runs on the home page.

**14. What is a dataset?** A collection of related data organised for analysis - here two tables: matches and deliveries.

**15. What is a CSV file?** A plain-text table where values are separated by commas; it opens in Excel and Pandas.

## B. Cricket metrics in this project
**16. What is strike rate?**
Runs scored per 100 balls faced: runs / balls x 100. Wides are not balls faced.

**17. What is bowling economy?**
Runs a bowler gives per over: runs x 6 / legal balls. Wides and no-ball runs count against the bowler; byes and leg-byes do not.

**18. What is batting average?**
Runs divided by number of dismissals. If a batter was never out, the average is undefined, so we show blank instead of dividing by zero.

**19. How is win percentage calculated?**
Wins / (wins + losses) x 100, called "decided" win %. Ties and no-result matches are left out because they are neither a win nor a loss. We also show wins / all matches. Both denominators are displayed.

**20. How is toss-win percentage calculated?**
Matches where the toss winner also won / decisive matches x 100. **How to get it:** Toss and Match Analysis page, first row of cards (on the full data: 548 of 1,076 = 50.9%).

## C. Design and tools
**21. Why did we choose IPL data?**
It is large, real, public, rich (teams, players, venues, seasons) and understandable for the audience, with enough traps (ties, renames, extras) to show good analysis practice.

**22. What is the difference between analytics and machine learning?**
Analytics describes what happened (counts, averages, comparisons). Machine learning builds models to predict. Our theme is analytics, so we describe and compare and make no predictions.

**23. Why is Streamlit used?**
It turns Python scripts into interactive web apps without HTML/JavaScript, with built-in filters, tables, caching and downloads.

**24. What are Pandas and Plotly used for?**
Pandas prepares and calculates the numbers; Plotly draws interactive charts with hover details.

**25. How do we handle missing values?**
We count them, keep them as missing, and never invent values. We classify no-result matches separately and show "n/a" when a statistic cannot be computed.

**26. How do we prevent double-counting?**
Each match is counted once per team; deliveries are summed to one row per match and innings before joining to matches; ties are not counted as wins; super overs are excluded from player statistics; wickets credited to the bowler exclude run outs.

**27. How do you handle a tied match?**
It is a "tie", not a win or loss, even though a super-over winner is recorded. 14 matches in this data were ties.

**28. Why can't you say the toss decides the match?**
Toss winners won about half of decisive matches (50.9%). That is an association in past data; many other factors decide a match.

## D. Wrap-up
**29. What are the limitations of this analysis?**
The data may differ from official records; super overs are excluded; fours/sixes come from bat runs; samples for some teams/venues are small; there is no fielding or pitch data; results are descriptive, not predictive.

**30. What are the future enhancements?**
Matchup analysis, powerplay/death-over phases, updates for new seasons, an online deployment and, separately, prediction models.

**31. What are the main findings?**
Read them from the *Insights Explorer* page. On the full dataset: Mumbai Indians have the most wins (142), V Kohli the most runs (8,004), YS Chahal the most wickets (205), chasing teams won 54.3% of decisive matches, and the toss winner won 50.9%. Always quote the filters you used.

**32. How would you explain the complete project?**
"I took 17 seasons of real IPL match and ball-by-ball data, cleaned it with a documented pipeline, and built a Streamlit dashboard that analyses teams, players, toss, venues and seasons. Every number is computed from the data using explicit formulas, with tests and a notebook to back it up. The findings are patterns, not predictions."

**33. How did you test it?**
45 unit tests on tiny made-up datasets whose answers I calculated by hand, plus 15 tests that run every page on the real data. The synthetic data is used only inside tests.

**34. Where did the data come from?**
A public GitHub repository (Apache-2.0). Its layout matches a Kaggle IPL dataset based on Cricsheet, but that origin is not confirmed by the repository, so I cite the GitHub source and mention the possible origin.

**35. Why merge team names such as Delhi Daredevils and Delhi Capitals?**
It is the same franchise renamed, so splitting it would understate its record. Deccan Chargers and Sunrisers Hyderabad are different franchises, so they are not merged.
