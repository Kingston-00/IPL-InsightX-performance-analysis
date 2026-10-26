"""IPL InsightX - home dashboard. Run with:  streamlit run app.py"""
import os

# Must be set before NumPy is imported: keeps memory use small on computers with little free RAM.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import plotly.express as px
import streamlit as st

from src import ui
from src.batting_analytics import batting_stats, season_runs
from src.bowling_analytics import bowling_stats
from src.insights import generate_insights, headline_kpis
from src.player_analytics import player_of_match_counts
from src.season_analytics import season_overview
from src.team_analytics import team_summary
from src.toss_analytics import toss_decision_outcomes, toss_win_match_win



def home() -> None:
    """Draw the home dashboard."""
    ui.setup_page("Home")
    data = ui.get_data()
    sel = ui.sidebar_filters(data)

    years = data.quality["seasons"]
    st.markdown(
        f"""<div class="hero"><h1>IPL <span>InsightX</span></h1>
        <p>IPL Performance Analysis Using Data Analytics</p>
        <p class="note">Seasons available: {years[0]}-{years[-1]} ({len(years)} seasons)</p></div>""",
        unsafe_allow_html=True)
    st.caption(ui.coverage_text(data))
    ui.require_matches(sel)
    st.caption(f"Current filters: {sel.description}")

    # ---------------------------------------------------------------- KPIs
    kpis = headline_kpis(sel.matches, sel.deliveries)
    ui.metric_row([
        ("Matches", kpis["matches"], "Recorded match records, playoffs included."),
        ("Teams", kpis["teams"], "Distinct franchises (renamed teams are merged)."),
        ("Players", kpis["players"], "Distinct batters, non-strikers and bowlers in the ball-by-ball data."),
        ("Total runs", kpis["runs"], "All runs including extras, regular innings only (super overs excluded)."),
        ("Wickets", kpis["wickets"], "Dismissals that ended a batter's innings (retired hurt excluded), regular innings only."),
        ("Seasons", kpis["seasons"], None),
    ])

    # ----------------------------------------------------- Team performance
    st.header("Team performance")
    teams = team_summary(sel.matches)
    if sel.teams:
        teams = teams[teams["team"].isin(sel.teams)]
    fig = px.bar(teams.sort_values("wins"), x="wins", y="team", orientation="h", text="wins",
                 hover_data={"matches": True, "losses": True, "ties": True, "no_results": True, "win_pct_decided": ":.1f"},
                 color_discrete_sequence=[ui.BLUE])
    ui.show_chart(ui.style_fig(fig, "Recorded wins by team", height=max(360, 30 * len(teams) + 120), x_title="Wins", y_title=""))
    st.caption("A win is a match won by runs or wickets. Tied matches (settled by a super over) and no-result matches "
               "are shown in the table below and are not counted as wins or losses.")
    with st.expander("Team table"):
        ui.table(teams)
        ui.download_csv(teams, "team summary", "ipl_team_summary.csv")

    # ------------------------------------------------------- Season trends
    st.header("Season trends")
    overview = season_overview(sel.matches)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(overview, x="season", y="matches", text="matches", color_discrete_sequence=[ui.BLUE])
        fig.update_xaxes(type="category", categoryorder="category ascending")
        ui.show_chart(ui.style_fig(fig, "Matches per season", height=340, x_title="Season", y_title="Matches"))
    with c2:
        if data.has_deliveries:
            runs = season_runs(sel.deliveries, sel.matches)
            fig = px.line(runs, x="season", y="avg_innings_score", markers=True, color_discrete_sequence=[ui.GOLD],
                          hover_data={"runs": True, "innings": True})
            fig.update_xaxes(type="category", categoryorder="category ascending")
            ui.show_chart(ui.style_fig(fig, "Average innings score by season", height=340, x_title="Season", y_title="Runs per innings"))
        else:
            st.info("Scoring trends need ball-by-ball data.")

    # --------------------------------------------------------- Top players
    st.header("Top players")
    if data.has_deliveries:
        bat = batting_stats(sel.deliveries).head(10)
        bowl = bowling_stats(sel.deliveries)
        bowl = bowl[bowl["wickets"] > 0].head(10)
        pom = player_of_match_counts(sel.matches).head(10)
        cols = st.columns(3)
        for col, (frame, x, y, title) in zip(cols, [(bat, "runs", "batter", "Most runs"),
                                                   (bowl, "wickets", "bowler", "Most wickets"),
                                                   (pom, "awards", "player", "Most Player of the Match awards")]):
            with col:
                if frame.empty:
                    st.info(f"No data for: {title}")
                    continue
                fig = px.bar(frame.sort_values(x), x=x, y=y, orientation="h", text=x, color_discrete_sequence=[ui.GOLD])
                ui.show_chart(ui.style_fig(fig, title, height=400, x_title="", y_title=""))
        st.caption("Eligibility: every player in the selected matches is eligible (no minimum). Runs are runs off the bat; "
                   "wickets are those credited to the bowler (run outs excluded); super overs are excluded.")
    else:
        pom = player_of_match_counts(sel.matches).head(10)
        st.info("Run and wicket rankings need ball-by-ball data. Player of the Match awards are shown instead.")
        ui.table(pom)

    # --------------------------------------------------------------- Toss
    st.header("Toss insights")
    tw = toss_win_match_win(sel.matches)
    outcomes = toss_decision_outcomes(sel.matches)
    if tw["decisive_matches"]:
        c1, c2 = st.columns([1, 2])
        c1.metric("Toss winner also won the match", f"{tw['pct']:.1f}%",
                  help="Toss winner = match winner / decisive matches (ties and no-result excluded).")
        c1.caption(f"Based on {tw['decisive_matches']} decisive matches.")
        long = outcomes.melt(id_vars=["toss_decision", "matches", "win_pct"], value_vars=["toss_winner_won", "toss_winner_lost"],
                             var_name="toss winner", value_name="count")
        long["toss winner"] = long["toss winner"].map({"toss_winner_won": "Won the match", "toss_winner_lost": "Lost the match"})
        fig = px.bar(long, x="toss_decision", y="count", color="toss winner", barmode="group", text="count",
                     color_discrete_map={"Won the match": ui.BLUE, "Lost the match": ui.GOLD},
                     hover_data={"matches": True, "win_pct": ":.1f"})
        with c2:
            ui.show_chart(ui.style_fig(fig, "Match result for the toss winner, by toss decision", height=340,
                                       x_title="Toss decision", y_title="Matches"))
        st.caption("This shows an observed pattern, not a cause: winning the toss does not by itself explain winning the match.")
    else:
        st.info("No decisive matches in the current selection.")

    # ------------------------------------------------------ Quick insights
    st.header("Quick insights")
    insights = generate_insights(sel.matches, sel.deliveries)
    for ins in insights[:6]:
        st.markdown(f"- **{ins.title}:** {ins.finding} (**{ins.value}**; {ins.sample_size})")
    st.caption("More detail on the *Insights Explorer* page.")
    ui.download_matches(sel, key="dl_matches_home")
    ui.quality_expander(data)


pages = [
    st.Page(home, title="Home", icon="🏏", default=True),
    st.Page("pages/1_Team_Analytics.py", title="Team Analytics", url_path="team"),
    st.Page("pages/2_Player_Analytics.py", title="Player Analytics", url_path="player"),
    st.Page("pages/3_Batting_Analytics.py", title="Batting Analytics", url_path="batting"),
    st.Page("pages/4_Bowling_Analytics.py", title="Bowling Analytics", url_path="bowling"),
    st.Page("pages/5_Toss_and_Match_Analysis.py", title="Toss and Match Analysis", url_path="toss"),
    st.Page("pages/6_Venue_Analytics.py", title="Venue Analytics", url_path="venue"),
    st.Page("pages/7_Season_Analytics.py", title="Season Analytics", url_path="season"),
    st.Page("pages/8_Data_Insights.py", title="Insights Explorer", url_path="insights"),
]
st.navigation(pages).run()
