"""
loader.py
Ingests CSV block model files, validates required fields,
and tags each row with a model_id.
"""

import pandas as pd
from pathlib import Path

REQUIRED_FIELDS = {"lode", "tonnes", "grade_gt", "resource_class", "status", "cutoff_gt"}


def load_model(source, model_id: str) -> pd.DataFrame:
    """
    Load a CSV block model from a file path or file-like object.
    Tags every row with model_id.
    Raises ValueError if required fields are missing.
    """
    if isinstance(source, (str, Path)):
        df = pd.read_csv(source)
    else:
        df = pd.read_csv(source)

    missing = REQUIRED_FIELDS - set(df.columns.str.lower())
    if missing:
        raise ValueError(f"Model '{model_id}' is missing required fields: {missing}")

    df.columns = df.columns.str.lower()
    df["model_id"] = model_id
    df["tonnes"] = pd.to_numeric(df["tonnes"], errors="coerce")
    df["grade_gt"] = pd.to_numeric(df["grade_gt"], errors="coerce")
    df["cutoff_gt"] = pd.to_numeric(df["cutoff_gt"], errors="coerce")
    df = df.dropna(subset=["tonnes", "grade_gt"])
    return df


def load_models(sources: list) -> pd.DataFrame:
    """
    Load and merge multiple (source, model_id) pairs into one DataFrame.
    sources: list of (source, model_id) tuples
    """
    frames = []
    for source, model_id in sources:
        frames.append(load_model(source, model_id))
    return pd.concat(frames, ignore_index=True)
