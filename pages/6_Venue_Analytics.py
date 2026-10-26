"""Venue analytics page."""
import plotly.express as px
import streamlit as st

from src import ui
from src.team_analytics import venue_team_summary

from src.venue_analytics import highest_team_total, venue_summary, venue_usage_by_season

ui.setup_page("Venue Analytics")
data = ui.get_data()
sel = ui.sidebar_filters(data, venues=False)
ui.page_header("Venue Analytics", "Where matches were played and what happened there.")
ui.require_matches(sel)
st.caption(f"Current filters: {sel.description}")
st.info("Venue spellings of the same stadium are merged (see the data-quality notes). Match counts do not show that a venue "
        "favours batters or bowlers - check the sample size (matches) before reading any percentage.")

vs = venue_summary(sel.matches)
min_m = st.slider("Minimum matches for the venue ranking", 1, 50, 5)
shown = vs[vs["matches"] >= min_m]

st.header("Most-used venues")
top = shown.head(15)
fig = px.bar(top.iloc[::-1], x="matches", y="venue", orientation="h", text="matches", hover_data={"city": True, "seasons_used": True},
             color_discrete_sequence=[ui.BLUE])
ui.show_chart(ui.style_fig(fig, "Matches per venue", height=max(340, 28 * len(top) + 120), x_title="Matches", y_title=""))

st.header("Scoring and batting-first results")
if data.has_deliveries and shown["avg_first_innings"].notna().any():
    s2 = shown.dropna(subset=["avg_first_innings"]).head(15)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(s2.sort_values("avg_first_innings"), x="avg_first_innings", y="venue", orientation="h",
                     hover_data={"matches": True, "highest_total": True}, color_discrete_sequence=[ui.GOLD])
        ui.show_chart(ui.style_fig(fig, "Average first-innings score", height=420, x_title="Runs", y_title=""))
    with c2:
        s3 = s2[s2["decisive"] > 0]
        fig = px.bar(s3.sort_values("batting_first_win_pct"), x="batting_first_win_pct", y="venue", orientation="h",
                     hover_data={"decisive": True, "batting_first_wins": True, "chasing_wins": True}, color_discrete_sequence=[ui.BLUE])
        fig.add_vline(x=50, line_dash="dot", line_color="#9aa6bf")
        ui.show_chart(ui.style_fig(fig, "% of decisive matches won by the team batting first", height=420, x_title="Batting-first win %", y_title=""))
else:
    st.info("Scoring statistics need ball-by-ball data.")
ui.table(shown)
ui.download_csv(shown, "venue summary", "ipl_venue_summary.csv")

st.header("Single venue summary")
venue = st.selectbox("Venue", vs["venue"].tolist())
row = vs[vs["venue"] == venue].iloc[0]
ui.metric_row([("Matches", int(row["matches"]), None), ("Seasons used", int(row["seasons_used"]), None),
               ("Avg 1st-innings score", None if row["avg_first_innings"] != row["avg_first_innings"] else float(row["avg_first_innings"]), "Mean of first-innings totals"),
               ("Highest total", None if row["highest_total"] != row["highest_total"] else int(row["highest_total"]), "Either innings"),
               ("Batting-first win %", None if row["batting_first_win_pct"] != row["batting_first_win_pct"] else float(row["batting_first_win_pct"]),
                f"{int(row['batting_first_wins'])} of {int(row['decisive'])} decisive matches")])
vm = sel.matches[sel.matches["venue"] == venue]
c1, c2 = st.columns(2)
with c1:
    teams = venue_team_summary(vm)
    teams = teams[teams["venue"] == venue].sort_values("wins", ascending=False)
    fig = px.bar(teams, x="team", y="wins", hover_data={"matches": True, "win_pct_decided": ":.1f"}, color_discrete_sequence=[ui.BLUE])
    ui.show_chart(ui.style_fig(fig, "Team wins at this venue", height=340, x_title="", y_title="Wins"))
with c2:
    dec = vm.groupby("toss_decision").size().reset_index(name="matches")
    fig = px.pie(dec, names="toss_decision", values="matches", hole=0.45, color_discrete_sequence=[ui.BLUE, ui.GOLD])
    ui.show_chart(ui.style_fig(fig, "Toss decisions at this venue", height=340))
best = highest_team_total(vm)
if best:
    st.caption(f"Highest recorded total here: {best['runs']} by {best['team']} ({best['season']}).")

st.header("Venue usage by season")
usage = venue_usage_by_season(sel.matches)
top_venues = vs["venue"].head(7).tolist()       # 7 venues + "Other venues" = the 8 palette colours
grouped = usage.assign(venue=usage["venue"].where(usage["venue"].isin(top_venues), "Other venues"))
grouped = grouped.groupby(["season", "venue"], as_index=False)["matches"].sum()
order = top_venues + (["Other venues"] if (grouped["venue"] == "Other venues").any() else [])
fig = px.bar(grouped, x="season", y="matches", color="venue", color_discrete_sequence=ui.COLORWAY,
             category_orders={"venue": order})
fig.update_xaxes(type="category", categoryorder="category ascending")
ui.show_chart(ui.style_fig(fig, "Matches per season at the 7 most-used venues (others grouped)", height=420, x_title="Season", y_title="Matches"))
ui.download_csv(usage, "venue usage by season", "ipl_venue_usage.csv")
