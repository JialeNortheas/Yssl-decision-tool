"""Browse Contacts — searchable view of the CRM scaffold."""
import streamlit as st
import scoring

st.set_page_config(page_title="Browse Contacts", page_icon="🔎", layout="wide")
st.title("🔎 Browse the CRM")

@st.cache_data
def load():
    return scoring.load_crm()

df = load()

c1, c2, c3 = st.columns(3)
q = c1.text_input("Search name / org / role")
seg = c2.selectbox("Segment", ["Any"] + sorted(df["activity_group"].dropna().unique().tolist()))
reg = c3.selectbox("Region", ["Any"] + sorted(df["region"].dropna().unique().tolist()))

view = df.copy()
if q:
    m = (view["name"].astype(str).str.contains(q, case=False, na=False) |
         view["org"].astype(str).str.contains(q, case=False, na=False) |
         view["role"].astype(str).str.contains(q, case=False, na=False))
    view = view[m]
if seg != "Any":
    view = view[view["activity_group"] == seg]
if reg != "Any":
    view = view[view["region"] == reg]

st.caption(f"{len(view):,} of {len(df):,} records")
st.dataframe(
    view[["entity", "name", "org", "role", "email", "phone", "region",
          "activity_group", "is_creator", "record_type"]],
    use_container_width=True, hide_index=True,
)
