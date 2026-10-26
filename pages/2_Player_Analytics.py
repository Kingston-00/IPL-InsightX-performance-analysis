"""Player analytics page."""
import plotly.express as px
import streamlit as st

from src import ui
from src.batting_analytics import batting_innings
from src.player_analytics import compare_players, player_names, player_of_match_counts, player_profile

ui.setup_page("Player Analytics")
data = ui.get_data()
sel = ui.sidebar_filters(data, teams=True, venues=True)
ui.page_header("Player Analytics", "Batting, bowling and award statistics for individual players.")
ui.require_matches(sel)
ui.require_deliveries(data, sel)
st.caption(f"Current filters: {sel.description}")

with st.expander("How these statistics are calculated"):
    st.markdown(
        "- **Runs** are runs off the bat (extras are not credited to the batter). **Strike rate** = runs / balls faced x 100; wides are not balls faced.\n"
        "- **Batting average** = runs / dismissals. It is blank when the player was never dismissed in the selection.\n"
        "- **Wickets** exclude run outs and other dismissals not credited to the bowler.\n"
        "- **Economy** = runs conceded x 6 / legal balls. Wides and no-ball runs are charged to the bowler; byes and leg-byes are not.\n"
        "- A statistic shows *n/a* when the player has no data for it. Super overs are excluded.")

players = player_names(sel.deliveries, sel.matches)
default = "V Kohli" if "V Kohli" in players else players[0]
st.header("Player profile")
player = st.selectbox("Player", players, index=players.index(default))
profile = player_profile(player, sel.deliveries, sel.matches)

st.subheader("Batting")
ui.metric_row([("Runs", profile["runs"], None), ("Innings", profile["innings"], None),
               ("Average", profile["average"], "Runs / dismissals"), ("Strike rate", profile["strike_rate"], "Runs / balls faced x 100"),
               ("Highest score", profile["highest_score"], None)])
ui.metric_row([("Balls faced", profile["balls_faced"], None), ("Fours", profile["fours"], "Deliveries with exactly 4 runs off the bat"),
               ("Sixes", profile["sixes"], None), ("Player of the Match", profile["awards"], None)])
st.subheader("Bowling")
ui.metric_row([("Wickets", profile["wickets"], "Credited to the bowler"), ("Legal balls", profile["legal_balls"], None),
               ("Runs conceded", profile["runs_conceded"], None), ("Economy", profile["economy"], "Runs per over"),
               ("Average", profile["bowling_average"], "Runs conceded / wickets"),
               ("Strike rate", profile["bowling_strike_rate"], "Balls per wicket")])

inn = batting_innings(sel.deliveries)
mine = inn[inn["batter"] == player].merge(sel.matches[["match_id", "season", "date"]], on="match_id").sort_values(["date", "inning"])
if not mine.empty:
    by_season = mine.groupby("season").agg(runs=("runs", "sum"), balls=("balls", "sum"), innings=("runs", "size")).reset_index()
    fig = px.bar(by_season, x="season", y="runs", hover_data={"innings": True, "balls": True}, color_discrete_sequence=[ui.BLUE])
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, f"{player}: runs per season", height=340, x_title="Season", y_title="Runs"))

st.header("Compare players")
chosen = st.multiselect("Players to compare (2 or more)", players, default=[p for p in ("V Kohli", "RG Sharma", "MS Dhoni") if p in players][:3])
if len(chosen) < 2:
    st.info("Select at least two players.")
else:
    cmp = compare_players(chosen, sel.deliveries, sel.matches)
    ui.table(cmp)
    ui.download_csv(cmp, "player comparison", "ipl_player_comparison.csv")
    metric = st.selectbox("Chart metric", [c for c in cmp.columns if c != "player"], index=0)
    fig = px.bar(cmp, x="player", y=metric, text=metric, color="player", color_discrete_sequence=ui.COLORWAY)
    ui.show_chart(ui.style_fig(fig, f"Comparison: {metric.replace('_', ' ')}", height=360, x_title="", y_title=metric.replace("_", " ")))
    st.caption("'None' means the player has no data for that statistic in the selection (for example a batter who never bowled).")

st.header("Player of the Match awards")
pom = player_of_match_counts(sel.matches)
ui.table(pom.head(25))
ui.download_csv(pom, "Player of the Match awards", "ipl_player_of_match.csv")
