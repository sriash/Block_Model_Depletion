"""
validator.py
Validates DIS pivot table results against raw row-level aggregates.

As the paper states (p.9): "the premined resources derived using a script passed
over each model compare with resources reported from DIS. (Negligible differences
are due to rounding errors when extracting data out of the model using scripts)."

Tolerance: discrepancies <= 0.01% of the raw total are accepted as rounding noise.
"""

import pandas as pd

TOLERANCE_PCT = 0.01  # 0.01% — matches paper's rounding-error acknowledgement


def validate(df_raw: pd.DataFrame, df_pivot: pd.DataFrame) -> pd.DataFrame:
    """
    Compare pivot table totals (Tonnes, Ounces) against raw aggregates per model.

    Returns a DataFrame with one row per model_id showing:
      - Raw Tonnes / Raw Ounces  (from df_raw)
      - Pivot Tonnes / Pivot Ounces (from df_pivot)
      - Diff % for each
      - Status: PASS / FAIL
    """
    raw_agg = (
        df_raw.groupby("model_id")
        .agg(raw_tonnes=("tonnes", "sum"), raw_ounces=("ounces", "sum"))
        .reset_index()
    )

    # df_pivot uses title-cased column names
    pivot_col_map = {}
    for col in df_pivot.columns:
        cl = col.lower()
        if "model" in cl:
            pivot_col_map[col] = "model_id"
        elif cl == "tonnes":
            pivot_col_map[col] = "pivot_tonnes"
        elif cl == "ounces":
            pivot_col_map[col] = "pivot_ounces"

    # Aggregate pivot by model (in case rows are model x lode)
    pivot_model_col = next(
        (c for c in df_pivot.columns if "model" in c.lower()), None
    )
    if pivot_model_col is None:
        return pd.DataFrame({"error": ["No model column found in pivot table"]})

    tonnes_col = next((c for c in df_pivot.columns if c.lower() == "tonnes"), None)
    ounces_col = next((c for c in df_pivot.columns if c.lower() == "ounces"), None)

    pivot_agg = (
        df_pivot.groupby(pivot_model_col)
        .agg(pivot_tonnes=(tonnes_col, "sum"), pivot_ounces=(ounces_col, "sum"))
        .reset_index()
        .rename(columns={pivot_model_col: "model_id"})
    )

    merged = raw_agg.merge(pivot_agg, on="model_id", how="outer")

    def pct_diff(a, b):
        if a == 0:
            return 0.0
        return abs(a - b) / a * 100

    merged["tonnes_diff_pct"] = merged.apply(
        lambda r: pct_diff(r["raw_tonnes"], r["pivot_tonnes"]), axis=1
    ).round(4)
    merged["ounces_diff_pct"] = merged.apply(
        lambda r: pct_diff(r["raw_ounces"], r["pivot_ounces"]), axis=1
    ).round(4)
    merged["status"] = merged.apply(
        lambda r: "PASS"
        if r["tonnes_diff_pct"] <= TOLERANCE_PCT and r["ounces_diff_pct"] <= TOLERANCE_PCT
        else "FAIL",
        axis=1,
    )

    merged["raw_tonnes"] = merged["raw_tonnes"].round(1)
    merged["raw_ounces"] = merged["raw_ounces"].round(3)
    merged["pivot_tonnes"] = merged["pivot_tonnes"].round(1)
    merged["pivot_ounces"] = merged["pivot_ounces"].round(3)

    return merged[[
        "model_id", "raw_tonnes", "pivot_tonnes", "tonnes_diff_pct",
        "raw_ounces", "pivot_ounces", "ounces_diff_pct", "status"
    ]]


def all_pass(validation_df: pd.DataFrame) -> bool:
    return (validation_df["status"] == "PASS").all()
