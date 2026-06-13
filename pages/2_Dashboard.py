"""Dashboard — the three sponsor-question charts (functional backup to Power BI)."""
import os
import streamlit as st
import pandas as pd
import scoring

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard — the three questions")

df = scoring.load_crm()

# Q1 — creatives outside creative jobs
st.subheader("Q1 · Creative professionals in the book")
seg_creators = (df.assign(group=df["activity_group"].fillna("Unknown"))
                  .groupby("group")["is_creator"].mean().mul(100).round(1))
st.bar_chart(seg_creators)
st.caption("Share of creators by segment. 95.8% overall is driven by the MoMA reference "
           "pool; reachable segments are near 0% — a finding, not a flaw.")

# Q2 — compliance burden
st.subheader("Q2 · Compliance / regulatory exposure")
risk = df["activity_group"].value_counts()
st.bar_chart(risk)
st.caption("Dormant Contact = records carrying a compliance / enforcement flag.")

# Q3 — IP-cost history (real external CIPO reference set)
st.subheader("Q3 · IP-protection cost over time (CIPO)")
ip_path = "https://raw.githubusercontent.com/JialeNortheas/yssl-crm-data/main/IP_Cost_History_CIPO.csv"
try:
    ip = pd.read_csv(ip_path)
    pub = ip[ip["basis"] == "CIPO published"]
    pivot = pub.pivot_table(index="year", columns="ip_type",
                            values="amount_cad", aggfunc="max")
    st.line_chart(pivot)
    st.caption("Trademark first-class & patent filing fees, 2023–2026. The ~32% jump in "
               "2024 (one-time 25%+CPI reset) is the barrier the sponsor flagged. "
               "Trademarks have no small-business discount; patents do.")
except Exception:
    st.info("IP_Cost_History_CIPO.csv could not be loaded.")
