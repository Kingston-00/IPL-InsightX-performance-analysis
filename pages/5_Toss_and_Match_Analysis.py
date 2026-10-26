"""Toss and match analysis page."""
import plotly.express as px
import streamlit as st

from src import ui
from src.team_analytics import wins_by_result_type
from src.toss_analytics import (chase_defend_by_team, chase_vs_defend, toss_by_venue, toss_decision_outcomes,
                                toss_decision_vs_batting_first, toss_decisions_by_season, toss_win_match_win)

ui.setup_page("Toss and Match Analysis")
data = ui.get_data()
sel = ui.sidebar_filters(data)
ui.page_header("Toss and Match Analysis", "How toss decisions, batting order and match results relate.")
ui.require_matches(sel)
st.caption(f"Current filters: {sel.description}")
st.info("Percentages use **decisive matches** (won by runs or wickets) as the denominator; ties and no-result matches are excluded. "
        "Sample sizes are shown next to every percentage. These are observed patterns, not proof of cause.")

tw = toss_win_match_win(sel.matches)
cd = chase_vs_defend(sel.matches)
ui.metric_row([("Decisive matches", tw["decisive_matches"], "Denominator for the percentages"),
               ("Toss winner won match", f"{tw['pct']:.1f}%" if tw["decisive_matches"] else None, f"{tw['toss_winner_won']} of {tw['decisive_matches']}"),
               ("Won batting first", f"{cd['batting_first_pct']:.1f}%" if cd["decisive_matches"] else None, f"{cd['won_batting_first']} of {cd['decisive_matches']}"),
               ("Won chasing", f"{cd['chasing_pct']:.1f}%" if cd["decisive_matches"] else None, f"{cd['won_chasing']} of {cd['decisive_matches']}")])

st.header("Toss decision and result")
out = toss_decision_outcomes(sel.matches)
if out.empty:
    st.info("No decisive matches in the selection.")
else:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(out, x="toss_decision", y="win_pct", text="win_pct", hover_data={"matches": True, "toss_winner_won": True},
                     color_discrete_sequence=[ui.BLUE])
        fig.add_hline(y=50, line_dash="dot", line_color="#9aa6bf", annotation_text="50%")
        ui.show_chart(ui.style_fig(fig, "Toss winner's match win % by toss decision", height=340, x_title="Toss decision", y_title="% of matches won by toss winner"))
    with c2:
        by_season = toss_decisions_by_season(sel.matches)
        fig = px.bar(by_season, x="season", y="share_pct", color="toss_decision", barmode="stack", hover_data={"matches": True},
                     color_discrete_sequence=[ui.BLUE, ui.GOLD])
        fig.update_xaxes(type="category", categoryorder="category ascending")
        ui.show_chart(ui.style_fig(fig, "Toss decisions by season", height=340, x_title="Season", y_title="% of tosses"))
    ui.table(out)
    ui.download_csv(out, "toss outcomes", "ipl_toss_outcomes.csv")

st.header("Batting order check")
chk = toss_decision_vs_batting_first(sel.matches)
if chk.empty:
    st.info("Innings order is not available.")
else:
    st.caption("Batting order is taken from the ball-by-ball data, not assumed from the toss. If 'bat' always means the toss winner batted first, the two sources agree.")
    ui.table(chk)

st.header("Chasing versus defending")
cdt = chase_defend_by_team(sel.matches)
if sel.teams:
    cdt = cdt[cdt["team"].isin(sel.teams)]
if cdt.empty:
    st.info("Innings order is not available.")
else:
    fig = px.bar(cdt, x="team", y="win_pct", color="role", barmode="group", hover_data={"matches": True, "wins": True},
                 color_discrete_sequence=[ui.BLUE, ui.GOLD])
    ui.show_chart(ui.style_fig(fig, "Win % when defending (batting first) vs chasing", x_title="", y_title="Win %"))
    ui.table(cdt)
    ui.download_csv(cdt, "chase vs defend", "ipl_chase_defend.csv")

st.header("Venue toss trends")
min_m = st.slider("Minimum matches at venue", 1, 40, 10)
tv = toss_by_venue(sel.matches, min_m)
if tv.empty:
    st.info("No venue has that many matches in the selection.")
else:
    fig = px.bar(tv.head(15), x="venue", y="field_first_pct", hover_data={"matches": True, "toss_winner_won_pct": ":.1f", "decisive": True},
                 color_discrete_sequence=[ui.BLUE])
    ui.show_chart(ui.style_fig(fig, "% of toss winners who chose to field first", x_title="", y_title="% choosing to field"))
    ui.table(tv)
    ui.download_csv(tv, "venue toss trends", "ipl_venue_toss.csv")

st.header("Match result distribution")
res = wins_by_result_type(sel.matches)
fig = px.pie(res, names="result", values="matches", hole=0.45, color_discrete_sequence=ui.COLORWAY)
ui.show_chart(ui.style_fig(fig, "Won by runs / wickets, tied, no result", height=340))
ui.table(res)
ui.download_matches(sel, key="dl_matches_toss")
