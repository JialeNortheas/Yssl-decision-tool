"""
YSSL Decision Tool — Streamlit app (single front door)
======================================================
Run locally:   streamlit run app.py
Deploy free:   push this folder to GitHub -> share.streamlit.io -> point at app.py

Pages (left sidebar):
  • Get a Recommendation  (this page) — goal + constraint -> top targets + why
  • Browse Contacts       — searchable view of the CRM
  • Dashboard             — the three sponsor-question charts
  • How it works          — the pipeline + scoring flow
"""
import streamlit as st
import pandas as pd
import scoring

st.set_page_config(page_title="YSSL Decision Tool", page_icon="🎯", layout="wide")

st.title("🎯 YSSL Decision Tool")
st.caption("Pick a goal and a constraint. Get the top targets to contact, and why. "
           "Built on the public-data CRM scaffold; accepts a future YSSL export without redesign.")

with st.sidebar:
    st.header("Your choice")
    goal = st.selectbox("Goal", list(scoring.GOALS.keys()))
    region = st.selectbox("Region", ["Any", "Canada-East", "Quebec", "Ontario",
                                      "Canada-West", "North", "Other"])
    entity = st.selectbox("Type", ["Any", "Contact", "Company"])
    require_email = st.checkbox("Only reachable by email", value=True)
    top_n = st.slider("How many recommendations", 3, 20, 3)

@st.cache_data(show_spinner="Scoring the book…")
def get_recs(goal, region, entity, require_email, top_n):
    return scoring.recommend(goal, region=region, entity=entity,
                             require_email=require_email, top_n=top_n)

recs = get_recs(goal, region, entity, require_email, top_n)

st.subheader(f"Top {len(recs)} for: {goal}")
if recs.empty:
    st.warning("No records match those constraints. Try widening the region or "
               "unchecking the email filter (note: most creative contacts in the "
               "public data have no email — that gap is itself a finding).")
else:
    st.dataframe(recs, use_container_width=True, hide_index=True)
    st.bar_chart(recs.set_index("name")["opportunity_score"])
    with st.expander("How is the opportunity score built?"):
        w = scoring.GOALS[goal]
        st.write("Weighted, transparent multi-criteria score (0–100). For this goal:")
        st.json(w)
        st.caption("creator = creative role · reachable = has email/phone · active = "
                   "outreach-ready segment · low_risk = not a compliance flag · "
                   "ip_fit = exposed to the IP-cost barrier. A supervised model can be "
                   "layered once the Interactions tab logs real outcomes.")
