"""
charts.py
Plotly Express chart builders for the DIS application.
Charts described in paper (p.1): scatter plots, graphs, pie charts.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def bar_tonnes_by_model(pivot_df: pd.DataFrame) -> go.Figure:
    """Bar chart: total Tonnes per model."""
    model_col = next((c for c in pivot_df.columns if "model" in c.lower()), None)
    agg = pivot_df.groupby(model_col)["Tonnes"].sum().reset_index()
    fig = px.bar(
        agg,
        x=model_col,
        y="Tonnes",
        title="Total Tonnes by Model",
        color=model_col,
        text_auto=".3s",
    )
    fig.update_layout(showlegend=False)
    return fig


def bar_ounces_by_model(pivot_df: pd.DataFrame) -> go.Figure:
    """Bar chart: total Ounces per model."""
    model_col = next((c for c in pivot_df.columns if "model" in c.lower()), None)
    agg = pivot_df.groupby(model_col)["Ounces"].sum().reset_index()
    fig = px.bar(
        agg,
        x=model_col,
        y="Ounces",
        title="Total Ounces by Model",
        color=model_col,
        text_auto=".3s",
    )
    fig.update_layout(showlegend=False)
    return fig


def scatter_grade_vs_tonnes(df: pd.DataFrame) -> go.Figure:
    """Scatter plot: Grade vs Tonnes, coloured by lode."""
    fig = px.scatter(
        df,
        x="tonnes",
        y="grade_gt",
        color="lode",
        symbol="model_id",
        hover_data=["resource_class", "status", "cutoff_gt"],
        title="Grade vs Tonnes (by Lode)",
        labels={"tonnes": "Tonnes", "grade_gt": "Grade (g/t Au)", "lode": "Lode"},
        opacity=0.7,
    )
    return fig


def pie_resource_class(df: pd.DataFrame) -> go.Figure:
    """Pie chart: Ounces breakdown by resource classification."""
    agg = df.groupby("resource_class")["ounces"].sum().reset_index()
    fig = px.pie(
        agg,
        names="resource_class",
        values="ounces",
        title="Ounces by Resource Classification",
    )
    return fig


def pie_status(df: pd.DataFrame) -> go.Figure:
    """Pie chart: Ounces breakdown by mined/unmined status."""
    agg = df.groupby("status")["ounces"].sum().reset_index()
    fig = px.pie(
        agg,
        names="status",
        values="ounces",
        title="Ounces by Status (Mined / Unmined / Premined)",
    )
    return fig
