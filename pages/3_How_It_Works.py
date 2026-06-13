"""How it works — the pipeline and the scoring flow, in plain English."""
import streamlit as st

st.set_page_config(page_title="How it works", page_icon="🛠️", layout="wide")
st.title("🛠️ How it works")

st.markdown("""
### The data pipeline (one command rebuilds everything)
Raw public files → **clean & standardise** → **tag creators (O\\*NET)** →
**classify record type** → **segment** → **build the CRM workbook** →
**data dictionary + quality report** → **validate**.
Every value is assigned by rule in code with a fixed snapshot date, so a re-run on
the same inputs always produces the same output.

### The scoring flow (this tool)
**Input** (your goal + constraint) → **Enrich** (reachability, creator, region,
compliance, IP-fit features) → **Score** (transparent weighted 0–100) →
**Rank** → **Recommend** (top targets, each with a plain-English reason).

### Why a transparent score, not a black box
The source data carries no engagement history, so there is nothing to *train* a
supervised model on yet. A weighted multi-criteria score is honest, explainable,
and auditable today. The empty **Interactions** tab is where YSSL logs real
outcomes; once it fills, a logistic-regression / random-forest layer can be added
to learn relationship warmth from actual results.

### Honest framing
This runs on a **public-data CRM scaffold**, not a populated customer database.
The structure and tool accept a future YSSL export without redesign.
""")
