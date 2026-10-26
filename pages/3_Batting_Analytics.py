"""Batting analytics page."""
import plotly.express as px
import streamlit as st

from src import ui
from src.batting_analytics import (batting_innings, batting_stats, runs_by_over, runs_distribution,
                                   season_runs, team_batting_summary)

ui.setup_page("Batting Analytics")
data = ui.get_data()
sel = ui.sidebar_filters(data)
ui.page_header("Batting Analytics", "Run scorers, strike rates and scoring patterns.")
ui.require_matches(sel)
ui.require_deliveries(data, sel)
st.caption(f"Current filters: {sel.description}")

innings = batting_innings(sel.deliveries)
c1, c2 = st.columns([1, 3])
top_n = c1.slider("Players to show", 5, 25, 10)
min_balls = c1.slider("Minimum balls faced (strike-rate ranking)", 0, 1500, 300, step=50)
c2.info(f"Strike rate = runs / balls faced x 100. Only batters with at least **{min_balls}** balls faced are ranked by strike rate, "
        "because a few lucky balls would otherwise top the list. Wides are not balls faced; super overs are excluded.")

stats = batting_stats(sel.deliveries, innings)
if stats.empty:
    st.warning("No batting data in the current selection.")
    st.stop()

st.header("Leaderboards")
tabs = st.tabs(["Most runs", "Most fours", "Most sixes", "Best strike rate"])
boards = [("runs", "Runs", stats.sort_values("runs", ascending=False)),
          ("fours", "Fours", stats.sort_values("fours", ascending=False)),
          ("sixes", "Sixes", stats.sort_values("sixes", ascending=False)),
          ("strike_rate", "Strike rate", stats[stats["balls"] >= min_balls].sort_values("strike_rate", ascending=False))]
for tab, (col, label, frame) in zip(tabs, boards):
    with tab:
        frame = frame.head(top_n)
        if frame.empty:
            st.info("No batter meets the minimum-balls threshold.")
            continue
        fig = px.bar(frame.sort_values(col), x=col, y="batter", orientation="h", text=col,
                     hover_data={"innings": True, "runs": True, "balls": True, "strike_rate": ":.2f", "average": ":.2f"},
                     color_discrete_sequence=[ui.GOLD])
        ui.show_chart(ui.style_fig(fig, f"Top {len(frame)} by {label.lower()}", height=max(340, 28 * len(frame) + 120), x_title=label, y_title=""))
ui.table(stats.head(100))
ui.download_csv(stats, "batting statistics", "ipl_batting_stats.csv")

st.header("Team batting")
team_bat = team_batting_summary(sel.deliveries, sel.matches)
fig = px.bar(team_bat.sort_values("runs"), x="runs", y="team", orientation="h", hover_data={"innings": True, "avg_innings_score": True, "run_rate": True},
             color_discrete_sequence=[ui.BLUE])
ui.show_chart(ui.style_fig(fig, "Total runs scored by team (including extras)", height=max(340, 30 * len(team_bat) + 120), x_title="Runs", y_title=""))
ui.table(team_bat)
ui.download_csv(team_bat, "team batting summary", "ipl_team_batting.csv")

st.header("Scoring trends")
c1, c2 = st.columns(2)
with c1:
    sr = season_runs(sel.deliveries, sel.matches)
    fig = px.line(sr, x="season", y="run_rate", markers=True, hover_data={"runs": True, "avg_innings_score": True},
                  color_discrete_sequence=[ui.GOLD])
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, "Run rate by season", height=340, x_title="Season", y_title="Runs per over"))
with c2:
    ro = runs_by_over(sel.deliveries)
    fig = px.bar(ro, x="over", y="run_rate", hover_data={"runs": True, "legal_balls": True}, color_discrete_sequence=[ui.BLUE])
    ui.show_chart(ui.style_fig(fig, "Run rate in each over of the innings", height=340, x_title="Over number", y_title="Runs per over"))
dist = runs_distribution(sel.deliveries)
fig = px.bar(dist, x="runs_off_bat", y="deliveries", text="share_pct", color_discrete_sequence=[ui.BLUE])
fig.update_traces(texttemplate="%{text}%")
ui.show_chart(ui.style_fig(fig, "Scoring distribution: runs off the bat per ball faced", height=340, x_title="Runs off the bat", y_title="Deliveries"))
ui.download_csv(sr, "season scoring", "ipl_season_scoring.csv")

st.header("Compare batters")
names = stats["batter"].tolist()
chosen = st.multiselect("Batters", names, default=names[:3])
if chosen:
    cmp = stats[stats["batter"].isin(chosen)]
    ui.table(cmp)
    long = cmp.melt(id_vars="batter", value_vars=["average", "strike_rate"], var_name="metric", value_name="value")
    fig = px.bar(long, x="batter", y="value", color="metric", barmode="group", color_discrete_sequence=[ui.BLUE, ui.GOLD])
    ui.show_chart(ui.style_fig(fig, "Average and strike rate", height=340, x_title="", y_title="Value"))
