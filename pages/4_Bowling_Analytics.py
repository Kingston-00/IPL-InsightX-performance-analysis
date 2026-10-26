"""Bowling analytics page."""
import plotly.express as px
import streamlit as st

from src import ui
from src.bowling_analytics import (bowling_by_season, bowling_by_venue, bowling_stats, dismissal_types,
                                   team_bowling_summary)

ui.setup_page("Bowling Analytics")
data = ui.get_data()
sel = ui.sidebar_filters(data)
ui.page_header("Bowling Analytics", "Wickets, economy and bowling efficiency.")
ui.require_matches(sel)
ui.require_deliveries(data, sel)
st.caption(f"Current filters: {sel.description}")

c1, c2 = st.columns([1, 3])
top_n = c1.slider("Bowlers to show", 5, 25, 10)
min_balls = c1.slider("Minimum legal balls (economy / average / strike-rate rankings)", 0, 2000, 300, step=50)
c2.info(f"Economy = runs conceded x 6 / legal balls. Rankings of economy, average and strike rate only include bowlers with at least "
        f"**{min_balls}** legal balls (**{min_balls / 6:.0f} overs**). Runs conceded = bat runs + wides + no-ball runs "
        "(byes, leg-byes and penalty runs are not charged to the bowler). Wickets exclude run outs and retirements. Super overs are excluded.")

stats = bowling_stats(sel.deliveries)
if stats.empty:
    st.warning("No bowling data in the current selection.")
    st.stop()
qualified = stats[stats["legal_balls"] >= min_balls]

st.header("Leaderboards")
tabs = st.tabs(["Most wickets", "Best economy", "Best average", "Best strike rate", "Most runs conceded"])
boards = [("wickets", "Wickets", stats[stats["wickets"] > 0].sort_values("wickets", ascending=False)),
          ("economy", "Economy", qualified.sort_values("economy")),
          ("average", "Bowling average", qualified.dropna(subset=["average"]).sort_values("average")),
          ("strike_rate", "Bowling strike rate", qualified.dropna(subset=["strike_rate"]).sort_values("strike_rate")),
          ("runs_conceded", "Runs conceded", stats.sort_values("runs_conceded", ascending=False))]
for tab, (col, label, frame) in zip(tabs, boards):
    with tab:
        frame = frame.head(top_n)
        if frame.empty:
            st.info("No bowler meets the minimum-balls threshold.")
            continue
        fig = px.bar(frame.iloc[::-1], x=col, y="bowler", orientation="h", text=col,
                     hover_data={"matches": True, "overs": True, "wickets": True, "economy": ":.2f", "runs_conceded": True},
                     color_discrete_sequence=[ui.GOLD])
        ui.show_chart(ui.style_fig(fig, f"Top {len(frame)}: {label.lower()}", height=max(340, 28 * len(frame) + 120), x_title=label, y_title=""))
ui.table(stats.head(100))
ui.download_csv(stats, "bowling statistics", "ipl_bowling_stats.csv")

st.header("Teams and seasons")
c1, c2 = st.columns(2)
with c1:
    tb = team_bowling_summary(sel.deliveries)
    fig = px.bar(tb.sort_values("wickets"), x="wickets", y="team", orientation="h", hover_data={"economy": True, "runs_conceded": True},
                 color_discrete_sequence=[ui.BLUE])
    ui.show_chart(ui.style_fig(fig, "Wickets taken by bowling team", height=max(340, 30 * len(tb) + 120), x_title="Wickets (credited to bowlers)", y_title=""))
with c2:
    bs = bowling_by_season(sel.deliveries, sel.matches)
    fig = px.line(bs, x="season", y="economy", markers=True, hover_data={"wickets": True, "runs_conceded": True}, color_discrete_sequence=[ui.GOLD])
    fig.update_xaxes(type="category", categoryorder="category ascending")
    ui.show_chart(ui.style_fig(fig, "Economy rate by season (all bowlers)", height=340, x_title="Season", y_title="Runs per over"))
ui.table(tb)
ui.download_csv(bs, "season bowling summary", "ipl_season_bowling.csv")

st.header("Wickets by dismissal type")
dis = dismissal_types(sel.deliveries)
fig = px.bar(dis, x="dismissal_kind", y="wickets", color="credited_to_bowler", color_discrete_map={True: ui.BLUE, False: ui.GOLD})
ui.show_chart(ui.style_fig(fig, "All dismissals by type", height=340, x_title="Dismissal", y_title="Wickets"))
st.caption("Blue: credited to the bowler. Gold: not credited (for example run outs).")

st.header("Compare bowlers and venues")
names = stats["bowler"].tolist()
chosen = st.multiselect("Bowlers", names, default=names[:3])
if chosen:
    cmp = stats[stats["bowler"].isin(chosen)]
    ui.table(cmp)
    bv = bowling_by_venue(sel.deliveries, sel.matches, chosen)
    min_v = st.slider("Minimum legal balls at a venue", 0, 500, 60, step=30)
    bv = bv[bv["legal_balls"] >= min_v]
    if bv.empty:
        st.info("No venue meets the threshold for these bowlers.")
    else:
        fig = px.bar(bv.head(15), x="venue", y="economy", hover_data={"wickets": True, "legal_balls": True, "runs_conceded": True},
                     color_discrete_sequence=[ui.BLUE])
        ui.show_chart(ui.style_fig(fig, "Economy at each venue (selected bowlers combined)", x_title="", y_title="Economy"))
        ui.table(bv)
        ui.download_csv(bv, "bowling by venue", "ipl_bowling_by_venue.csv")
