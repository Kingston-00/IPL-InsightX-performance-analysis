"""Insights Explorer page."""
import streamlit as st

from src import ui
from src.insights import generate_insights, insights_table

ui.setup_page("Insights Explorer")
data = ui.get_data()
sel = ui.sidebar_filters(data)
ui.page_header("Insights Explorer", "Plain-language findings generated from the currently selected data.")
ui.require_matches(sel)
st.caption(f"Current filters: {sel.description}")
st.info("Every finding is calculated from the selected matches. Each one shows its value, sample size and calculation. "
        "These are descriptions of past matches; none of them claims a cause.")

min_balls = st.slider("Minimum balls faced for the strike-rate insight", 100, 2000, 500, step=100) if data.has_deliveries else 500
insights = generate_insights(sel.matches, sel.deliveries, min_balls)
if not insights:
    st.warning("There is not enough data in the current selection to generate insights.")
    st.stop()

for ins in insights:
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{ins.title}**")
        c1.write(ins.finding)
        c2.metric("Value", ins.value)
        st.caption(f"Sample size: {ins.sample_size}  \nHow it is calculated: {ins.method}")

table = insights_table(insights)
table.insert(0, "filters", sel.description)
ui.download_csv(table, "insights summary", "ipl_insights_summary.csv")
