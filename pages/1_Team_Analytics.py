"""Team analytics page."""
import plotly.express as px
import streamlit as st

from src import ui
from src.team_analytics import (batting_first_vs_chasing, head_to_head, season_team_summary, team_summary,
                                venue_team_summary)

ui.setup_page("Team Analytics")
data = ui.get_data()
sel = ui.sidebar_filters(data, venues=True)
ui.page_header("Team Analytics", "Wins, losses, win percentage and trends for each franchise.")
ui.require_matches(sel)
st.caption(f"Current filters: {sel.description}")

with st.expander("How these metrics are defined", expanded=False):
    st.markdown(
        "- **Win**: match won by runs or wickets. **Loss**: the opponent won such a match.\n"
        "- **Tie** (settled by a super over) and **no result** are counted separately: not a win, not a loss.\n"
        "- **Win % (decided)** = wins / (wins + losses). **Win % (all)** = wins / all matches played.\n"
        "- Renamed franchises are merged (Delhi Daredevils -> Delhi Capitals, Kings XI Punjab -> Punjab Kings, "
        "Royal Challengers Bangalore -> Bengaluru). Deccan Chargers, Pune Warriors and Gujarat Lions are separate franchises.\n"
        "- If you pick teams in the sidebar, the page shows the matches involving those teams.")

all_teams = team_summary(sel.matches)
teams_here = sel.teams or all_teams["team"].tolist()
summary = all_teams[all_teams["team"].isin(teams_here)]

st.header("Team summary")
ui.table(summary)
ui.download_csv(summary, "team summary", "ipl_team_summary.csv")
c1, c2 = st.columns(2)
with c1:
    long = summary.melt(id_vars="team", value_vars=["wins", "losses", "ties", "no_results"], var_name="result", value_name="count")
    fig = px.bar(long, x="team", y="count", color="result", barmode="group",
                 color_discrete_sequence=ui.COLORWAY)
    ui.show_chart(ui.style_fig(fig, "Wins, losses, ties and no-results", x_title="", y_title="Matches"))
with c2:
    eligible = summary[summary["decided"] > 0].sort_values("win_pct_decided")
    fig = px.bar(eligible, x="win_pct_decided", y="team", orientation="h", text="win_pct_decided",
                 hover_data={"decided": True, "wins": True}, color_discrete_sequence=[ui.BLUE])
    ui.show_chart(ui.style_fig(fig, "Win % of decided matches", x_title="Win % (wins / (wins + losses))", y_title=""))
st.caption("Teams with few matches have unstable percentages - check the 'decided' column for the sample size.")

st.header("Season-wise performance")
by_season = season_team_summary(sel.matches)
by_season = by_season[by_season["team"].isin(teams_here)]
default_pick = summary.sort_values("matches", ascending=False)["team"].head(5).tolist()
pick = st.multiselect("Teams to compare over time", sorted(teams_here), default=[t for t in (sel.teams or default_pick)][:8])
metric = st.radio("Metric", ["wins", "win_pct_decided"], horizontal=True,
                  format_func=lambda m: "Wins" if m == "wins" else "Win % (decided)")
if pick:
    sub = by_season[by_season["team"].isin(pick)]
    fig = px.line(sub, x="season", y=metric, color="team", markers=True, hover_data={"matches": True, "decided": True})
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, "Trend by season", x_title="Season", y_title="Wins" if metric == "wins" else "Win %"))
    fig = px.bar(sub, x="season", y="wins", color="team", barmode="group")
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, "Season-wise wins comparison", x_title="Season", y_title="Wins"))
else:
    st.info("Choose at least one team.")
ui.download_csv(by_season, "season-wise team results", "ipl_team_by_season.csv")

st.header("Team versus team")
h2h = head_to_head(sel.matches, teams_here)
if len(teams_here) >= 1:
    a = st.selectbox("Team", sorted(teams_here))
    opp = h2h[h2h["team"] == a].sort_values("matches", ascending=False)
    if opp.empty:
        st.info("No matches for this team in the current selection.")
    else:
        fig = px.bar(opp, x="opponent", y=["wins", "losses"], barmode="group", hover_data={"matches": True, "win_pct_decided": ":.1f"})
        ui.show_chart(ui.style_fig(fig, f"{a}: record against each opponent", x_title="Opponent", y_title="Matches"))
        ui.table(opp)
        ui.download_csv(opp, "head-to-head", "ipl_head_to_head.csv")

st.header("Performance by venue")
pv = venue_team_summary(sel.matches)
pv = pv[pv["team"].isin(teams_here)]
t_sel = st.selectbox("Team ", sorted(teams_here), key="venue_team")
min_v = st.slider("Minimum matches at venue", 1, 20, 5)
pvt = pv[(pv["team"] == t_sel) & (pv["matches"] >= min_v)].sort_values("matches", ascending=False)
if pvt.empty:
    st.info("No venue has that many matches for this team in the current selection.")
else:
    fig = px.bar(pvt, x="venue", y="win_pct_decided", hover_data={"matches": True, "wins": True, "losses": True},
                 color_discrete_sequence=[ui.BLUE])
    ui.show_chart(ui.style_fig(fig, f"{t_sel}: win % by venue (min {min_v} matches)", x_title="", y_title="Win % (decided)"))
    ui.table(pvt)

st.header("Batting first versus chasing")
bc = batting_first_vs_chasing(sel.matches)
bc = bc[bc["team"].isin(teams_here)]
if bc.empty:
    st.info("Innings order is not available for the current selection.")
else:
    fig = px.bar(bc, x="team", y="win_pct", color="role", barmode="group", hover_data={"matches": True, "wins": True},
                 color_discrete_sequence=[ui.BLUE, ui.GOLD])
    ui.show_chart(ui.style_fig(fig, "Win % when batting first vs chasing", x_title="", y_title="Win %"))
    st.caption("Only decisive matches are used. Innings order comes from the ball-by-ball data.")
    ui.table(bc)
    ui.download_csv(bc, "batting first vs chasing", "ipl_bat_first_vs_chase.csv")
