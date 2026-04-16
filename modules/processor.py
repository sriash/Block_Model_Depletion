"""
processor.py
Calculates ounces and applies DIS filters:
  - cut-off grade
  - resource classification
  - mined/unmined status
"""

import pandas as pd

TROY_OZ_FACTOR = 31.1035  # grams per troy ounce


def calculate_ounces(df: pd.DataFrame) -> pd.DataFrame:
    """Add ounces column: tonnes * grade_gt / 31.1035"""
    df = df.copy()
    df["ounces"] = (df["tonnes"] * df["grade_gt"] / TROY_OZ_FACTOR).round(3)
    return df


def apply_filters(
    df: pd.DataFrame,
    cutoff_min: float | None = None,
    resource_classes: list | None = None,
    statuses: list | None = None,
) -> pd.DataFrame:
    """
    Filter the merged DataFrame by:
      cutoff_min      — keep rows where cutoff_gt >= cutoff_min
      resource_classes — keep rows matching any of the listed classes
      statuses        — keep rows matching any of the listed statuses
    """
    mask = pd.Series(True, index=df.index)

    if cutoff_min is not None:
        mask &= df["cutoff_gt"] >= cutoff_min

    if resource_classes:
        mask &= df["resource_class"].isin(resource_classes)

    if statuses:
        mask &= df["status"].isin(statuses)

    return df[mask].copy()


def get_unique_values(df: pd.DataFrame, field: str) -> list:
    """Return sorted unique values for a given field."""
    return sorted(df[field].dropna().unique().tolist())
