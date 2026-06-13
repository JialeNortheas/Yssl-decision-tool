"""
YSSL Decision Tool — scoring engine
===================================
Prescriptive outreach prioritisation for the XN project.

The tool answers: "Given a GOAL and a CONSTRAINT, who are the top targets to
contact, and why?" It reads the populated CRM workbook and produces a ranked,
explainable list. Every score is transparent and rule-based — no black box,
nothing typed by hand. A supervised classifier (logistic regression / random
forest) can be layered on later once the Interactions tab accumulates real
outcomes; until then a weighted multi-criteria score is the honest, defensible
model for data that carries no engagement history.

Maps to the sponsor's three Tuesday questions:
  Q1 creatives outside creative jobs  -> CREATOR_RELEVANCE feature
  Q2 compliance burden                -> COMPLIANCE_RISK feature (penalty)
  Q3 IP-cost barrier                  -> IP_SUPPORT_FIT feature
"""

from __future__ import annotations
import os
import pandas as pd

WORKBOOK = os.environ.get(
    "YSSL_WORKBOOK",
    "https://raw.githubusercontent.com/JialeNortheas/yssl-crm-data/main/YSSL_CRM_Library_Populated_v2_2026-06-09.xlsx",
)

REGION_BY_PROVINCE = {
    "NB": "Canada-East", "NS": "Canada-East", "PE": "Canada-East", "NL": "Canada-East",
    "QC": "Quebec", "ON": "Ontario",
    "MB": "Canada-West", "SK": "Canada-West", "AB": "Canada-West", "BC": "Canada-West",
    "YT": "North", "NT": "North", "NU": "North",
}

# Goal -> feature weights (0..1). Each goal is a preset profile the founder picks.
GOALS = {
    "Find creative partners": dict(creator=1.0, reachable=0.8, active=0.7, low_risk=0.3, ip_fit=0.5),
    "Low-risk outreach":      dict(creator=0.4, reachable=0.9, active=0.8, low_risk=1.0, ip_fit=0.2),
    "Regional expansion":     dict(creator=0.5, reachable=0.8, active=0.9, low_risk=0.5, ip_fit=0.3),
    "IP / brand support push":dict(creator=0.9, reachable=0.8, active=0.7, low_risk=0.4, ip_fit=1.0),
}


def load_crm(path: str = WORKBOOK) -> pd.DataFrame:
    """Load Contacts and Companies into one unified, scored-ready frame."""
    contacts = pd.read_excel(path, sheet_name="Contacts")
    companies = pd.read_excel(path, sheet_name="Companies")

    contacts = contacts.assign(entity="Contact",
                               name=contacts["full_name"],
                               org=contacts["company_name"])
    companies = companies.assign(entity="Company",
                                 name=companies["company_name"],
                                 org=companies["company_name"],
                                 is_creator=False)

    keep = ["entity", "name", "org", "role", "email", "phone", "province",
            "is_creator", "record_type", "activity_group", "company_type",
            "source_file"]
    for c in keep:
        for df in (contacts, companies):
            if c not in df.columns:
                df[c] = pd.NA
    df = pd.concat([contacts[keep], companies[keep]], ignore_index=True)

    df["region"] = df["province"].map(REGION_BY_PROVINCE).fillna("Other")
    df["has_email"] = df["email"].notna() & (df["email"].astype(str).str.strip() != "")
    df["has_phone"] = df["phone"].notna() & (df["phone"].astype(str).str.strip() != "")
    df["reachable"] = df["has_email"] | df["has_phone"]
    df["is_creator"] = df["is_creator"].fillna(False).astype(bool)
    df["compliance_risk"] = df["activity_group"].eq("Dormant Contact")
    df["active"] = df["record_type"].eq("Active")
    return df


def _features(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorised normalised 0..1 feature columns for the whole frame."""
    import numpy as np
    return pd.DataFrame({
        "creator":   df["is_creator"].astype(float),
        "reachable": np.where(df["reachable"], 1.0, np.where(df["has_phone"], 0.4, 0.0)),
        "active":    df["active"].astype(float),
        "low_risk":  (~df["compliance_risk"]).astype(float),
        "ip_fit":    np.where(df["is_creator"], 1.0, 0.2),  # creators face the IP-cost barrier
    }, index=df.index)


def score_records(df: pd.DataFrame, goal: str) -> pd.DataFrame:
    """Add a 0-100 opportunity_score and a plain-English reason for the goal."""
    import numpy as np
    weights = GOALS[goal]
    wsum = sum(weights.values())
    feats = _features(df)
    raw = sum(feats[k] * w for k, w in weights.items())
    df = df.copy()
    df["opportunity_score"] = (100 * raw / wsum).round(1)

    # Vectorised plain-English reason string
    parts = []
    parts.append(np.where(df["is_creator"], "creative role; ", ""))
    parts.append(np.where(df["has_email"], "has email; ",
                 np.where(df["has_phone"], "phone only; ", "no direct contact; ")))
    parts.append(np.where(df["active"], "active segment; ", ""))
    parts.append(np.where(df["compliance_risk"], "⚠ compliance flag; ", ""))
    parts.append(np.where(df["region"].ne("Other"), df["region"].astype(str), ""))
    why = parts[0]
    for p in parts[1:]:
        why = np.char.add(why.astype(str), p.astype(str))
    df["why"] = pd.Series(why, index=df.index).str.strip().str.rstrip(";").str.strip()
    return df


def recommend(goal: str, *, region: str | None = None, require_email: bool = False,
              entity: str | None = None, top_n: int = 3,
              path: str = WORKBOOK) -> pd.DataFrame:
    """Top-N ranked recommendations for a goal under optional constraints."""
    df = score_records(load_crm(path), goal)
    if region and region != "Any":
        df = df[df["region"] == region]
    if require_email:
        df = df[df["has_email"]]
    if entity and entity != "Any":
        df = df[df["entity"] == entity]
    cols = ["name", "org", "entity", "role", "region", "activity_group",
            "opportunity_score", "why"]
    return df.sort_values("opportunity_score", ascending=False).head(top_n)[cols].reset_index(drop=True)


if __name__ == "__main__":
    for g in GOALS:
        print(f"\n=== GOAL: {g} (top 3, require_email) ===")
        out = recommend(g, require_email=True, top_n=3)
        print(out.to_string(index=False))
