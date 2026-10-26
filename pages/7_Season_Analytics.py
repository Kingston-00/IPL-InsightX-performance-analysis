"""Season analytics page."""
import plotly.express as px
import streamlit as st

from src import ui
from src.batting_analytics import season_runs
from src.season_analytics import (most_successful_team, season_champions, season_leaders, season_overview,
                                  season_player_of_match, season_team_participation)

ui.setup_page("Season Analytics")
data = ui.get_data()
sel = ui.sidebar_filters(data, venues=False, stages=False)
ui.page_header("Season Analytics", "How each IPL season compares. Use the season range in the sidebar.")
ui.require_matches(sel)
st.caption(f"Current filters: {sel.description}")

ov = season_overview(sel.matches)
st.header("Overview")
c1, c2 = st.columns(2)
with c1:
    fig = px.bar(ov, x="season", y="matches", text="matches", color_discrete_sequence=[ui.BLUE])
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, "Matches per season", height=340, x_title="Season", y_title="Matches"))
with c2:
    fig = px.line(ov, x="season", y="teams", markers=True, color_discrete_sequence=[ui.GOLD])
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, "Teams participating", height=340, x_title="Season", y_title="Teams"))
ui.table(ov)
ui.download_csv(ov, "season overview", "ipl_season_overview.csv")

st.header("Scoring")
if data.has_deliveries:
    sr = season_runs(sel.deliveries, sel.matches)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(sr, x="season", y="runs", hover_data={"innings": True}, color_discrete_sequence=[ui.BLUE])
        fig.update_xaxes(type="category", categoryorder="category ascending")
        ui.show_chart(ui.style_fig(fig, "Total runs (including extras)", height=340, x_title="Season", y_title="Runs"))
    with c2:
        fig = px.line(sr, x="season", y="run_rate", markers=True, hover_data={"avg_innings_score": True}, color_discrete_sequence=[ui.GOLD])
        fig.update_xaxes(type="category", categoryorder="category ascending")
        ui.show_chart(ui.style_fig(fig, "Scoring rate (runs per over)", height=340, x_title="Season", y_title="Runs per over"))
    fig = px.line(ov, x="season", y="avg_first_innings", markers=True, color_discrete_sequence=[ui.BLUE])
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, "Average first-innings score", height=320, x_title="Season", y_title="Runs"))
    ui.download_csv(sr, "season scoring", "ipl_season_runs.csv")
else:
    st.info("Scoring statistics need ball-by-ball data.")

st.header("Season leaders")
if data.has_deliveries:
    leaders = season_leaders(sel.matches, sel.deliveries)
    ui.table(leaders)
    ui.download_csv(leaders, "season leaders", "ipl_season_leaders.csv")
    st.caption("Top run scorer = most runs off the bat; top wicket taker = most wickets credited to the bowler (run outs excluded). Ties are broken by data order.")

st.header("Most successful teams and champions")
best = most_successful_team(sel.matches)
champs = season_champions(sel.matches)
c1, c2 = st.columns(2)
with c1:
    st.subheader("Most wins in the season")
    ui.table(best)
with c2:
    st.subheader("Winner of the Final")
    if champs.empty:
        st.info("No match labelled 'Final' in the selection (the stage filter or season range may exclude it).")
    else:
        ui.table(champs)
st.caption("A team with the most wins in a season is not necessarily the champion.")

st.header("Team participation")
part = season_team_participation(sel.matches)
fig = px.density_heatmap(part, x="season", y="team", z="matches", histfunc="sum", color_continuous_scale="Blues")
fig.update_xaxes(type="category", categoryorder="category ascending")
ui.show_chart(ui.style_fig(fig, "Matches played by each team in each season", height=480, x_title="Season", y_title=""))

st.header("Player of the Match by season")
pom = season_player_of_match(sel.matches)
top_only = pom.groupby("season").head(1)
ui.table(top_only.rename(columns={"player": "top award winner"}))
with st.expander("All awards by season"):
    ui.table(pom)
ui.download_csv(pom, "Player of the Match by season", "ipl_season_player_of_match.csv")
