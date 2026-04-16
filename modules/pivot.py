"""
pivot.py
Generates the DIS pivot table: grouped by model_id x lode,
summarising Tonnes, Ounces, and derived Grade.
"""

import pandas as pd

TROY_OZ_FACTOR = 31.1035


def build_pivot(df: pd.DataFrame, row_fields: list | None = None) -> pd.DataFrame:
    """
    Build the DIS pivot table.

    row_fields: fields to group by (default: ['model_id', 'lode'])
    Returns a DataFrame with columns: Tonnes, Ounces, Grade (g/t Au)
    """
    if row_fields is None:
        row_fields = ["model_id", "lode"]

    pivot = (
        df.groupby(row_fields, as_index=False)
        .agg(
            Tonnes=("tonnes", "sum"),
            Ounces=("ounces", "sum"),
        )
    )
    pivot["Tonnes"] = pivot["Tonnes"].round(1)
    pivot["Ounces"] = pivot["Ounces"].round(3)
    # Back-calculate grade from aggregated tonnes and ounces
    pivot["Grade (g/t Au)"] = (
        (pivot["Ounces"] * TROY_OZ_FACTOR / pivot["Tonnes"])
        .where(pivot["Tonnes"] > 0)
        .round(2)
    )

    # Rename grouping columns to title case for display
    pivot = pivot.rename(columns={f: f.replace("_", " ").title() for f in row_fields})
    return pivot


def build_summary_row(pivot: pd.DataFrame) -> pd.DataFrame:
    """Append a Grand Total row to the pivot table."""
    total = pd.DataFrame(
        {
            col: (
                [round(float(pivot[col].sum()), 3) if pd.api.types.is_numeric_dtype(pivot[col]) else "TOTAL"]
            )
            for col in pivot.columns
        }
    )
    # Recalculate grade for total row
    if "Grade (g/t Au)" in total.columns and "Tonnes" in total.columns and "Ounces" in total.columns:
        t = total["Tonnes"].iloc[0]
        o = total["Ounces"].iloc[0]
        total["Grade (g/t Au)"] = round(o * TROY_OZ_FACTOR / t, 2) if t > 0 else 0.0
    return pd.concat([pivot, total], ignore_index=True)
