"""
app.py
DIS — Depletion Information System
Modern Python web application based on:
  Forman, P.F. (2003) "Case Study of Using An Excel Pivot Table to Create a
  Depletion Information System (DIS) for Monitoring and Reporting"

Run: streamlit run app.py
"""

import datetime
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from modules.loader import load_model, REQUIRED_FIELDS
from modules.processor import calculate_ounces, apply_filters, get_unique_values
from modules.pivot import build_pivot, build_summary_row
from modules.validator import validate, all_pass
from modules.charts import (
    bar_tonnes_by_model,
    bar_ounces_by_model,
    scatter_grade_vs_tonnes,
    pie_resource_class,
    pie_status,
)
from modules.exporter import to_csv_bytes, to_excel_bytes

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DIS — Depletion Information System",
    page_icon="⛏️",
    layout="wide",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "models" not in st.session_state:
    st.session_state.models = {}      # {model_id: DataFrame}
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []   # list of dicts


def log_audit(action: str, filters: dict, row_count: int):
    st.session_state.audit_log.append(
        {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "cutoff_min": filters.get("cutoff_min", "—"),
            "resource_classes": ", ".join(filters.get("resource_classes", [])) or "All",
            "statuses": ", ".join(filters.get("statuses", [])) or "All",
            "rows_returned": row_count,
        }
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.title("⛏️ Depletion Information System (DIS)")
st.caption(
    "Based on Forman (2003) — Multi-model resource block model analysis, "
    "reconciliation and reporting."
)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: Upload Models
# ─────────────────────────────────────────────────────────────────────────────
st.header("1. Load Block Models")

SAMPLE_DIR = Path(__file__).parent / "data"
use_samples = st.checkbox(
    "Use built-in sample data (Area134 + Kara from paper)", value=True
)

if use_samples:
    sample_files = {
        "Area134": SAMPLE_DIR / "sample_area134.csv",
        "Kara": SAMPLE_DIR / "sample_kara.csv",
    }
    for model_id, path in sample_files.items():
        if model_id not in st.session_state.models:
            try:
                df = load_model(path, model_id)
                df = calculate_ounces(df)
                st.session_state.models[model_id] = df
            except Exception as e:
                st.error(f"Could not load sample {model_id}: {e}")
    st.success(f"Loaded sample models: {', '.join(sample_files.keys())}")

else:
    uploaded_files = st.file_uploader(
        "Upload CSV block model files",
        type=["csv", "txt"],
        accept_multiple_files=True,
        help=f"Required columns: {', '.join(sorted(REQUIRED_FIELDS))}",
    )
    if uploaded_files:
        for uf in uploaded_files:
            default_name = Path(uf.name).stem
            col1, col2 = st.columns([2, 1])
            with col1:
                st.text(uf.name)
            with col2:
                model_id = st.text_input(
                    "Model label", value=default_name, key=f"label_{uf.name}"
                )
            if st.button(f"Load {uf.name}", key=f"load_{uf.name}"):
                try:
                    df = load_model(uf, model_id)
                    df = calculate_ounces(df)
                    st.session_state.models[model_id] = df
                    st.success(f"Loaded '{model_id}' — {len(df):,} rows")
                except ValueError as e:
                    st.error(str(e))

if not st.session_state.models:
    st.info("No models loaded yet. Upload CSV files or use the sample data above.")
    st.stop()

# Merge all loaded models
df_all = pd.concat(st.session_state.models.values(), ignore_index=True)

loaded_models = list(st.session_state.models.keys())
st.write(
    f"**{len(loaded_models)} model(s) loaded:** {', '.join(loaded_models)} "
    f"— {len(df_all):,} total rows"
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: Filters (sidebar)
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")
st.sidebar.caption("Changes are logged to the audit trail.")

all_cutoffs = sorted(df_all["cutoff_gt"].dropna().unique().tolist())
cutoff_min = st.sidebar.selectbox(
    "Minimum cut-off grade (g/t Au)",
    options=[None] + all_cutoffs,
    format_func=lambda x: "All" if x is None else f">= {x} g/t Au",
)

all_classes = get_unique_values(df_all, "resource_class")
selected_classes = st.sidebar.multiselect(
    "Resource Classification",
    options=all_classes,
    default=all_classes,
)

all_statuses = get_unique_values(df_all, "status")
selected_statuses = st.sidebar.multiselect(
    "Status",
    options=all_statuses,
    default=all_statuses,
)

# Apply filters
active_filters = {
    "cutoff_min": cutoff_min,
    "resource_classes": selected_classes,
    "statuses": selected_statuses,
}
df_filtered = apply_filters(
    df_all,
    cutoff_min=cutoff_min,
    resource_classes=selected_classes if selected_classes != all_classes else None,
    statuses=selected_statuses if selected_statuses != all_statuses else None,
)

# Audit log entry on filter change
log_audit("Filter applied", active_filters, len(df_filtered))

st.sidebar.metric("Rows after filtering", f"{len(df_filtered):,}")

# Audit trail in sidebar
with st.sidebar.expander("Audit Trail", expanded=False):
    if st.session_state.audit_log:
        audit_df = pd.DataFrame(st.session_state.audit_log)
        st.dataframe(audit_df.tail(20), width='stretch', hide_index=True)
    else:
        st.write("No entries yet.")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: Pivot Table
# ─────────────────────────────────────────────────────────────────────────────
st.header("2. DIS Pivot Table")

row_field_options = ["model_id", "lode", "resource_class", "status"]
row_fields = st.multiselect(
    "Group rows by",
    options=row_field_options,
    default=["model_id", "lode"],
)

if not row_fields:
    st.warning("Select at least one row grouping field.")
    st.stop()

if df_filtered.empty:
    st.warning("No data matches the current filters.")
    st.stop()

pivot_df = build_pivot(df_filtered, row_fields=row_fields)
pivot_with_total = build_summary_row(pivot_df)

st.dataframe(
    pivot_with_total.style.format(
        {
            "Tonnes": "{:,.1f}",
            "Ounces": "{:,.3f}",
            "Grade (g/t Au)": "{:.2f}",
        }
    ),
    width='stretch',
    hide_index=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Validation
# ─────────────────────────────────────────────────────────────────────────────
st.header("3. Validation")
st.caption(
    "Compares pivot table totals against raw row-level aggregates. "
    "Tolerance: ≤ 0.01% difference (rounding noise, per paper p.10)."
)

val_df = validate(df_filtered, pivot_df)

def highlight_status(row):
    color = "background-color: #d4edda" if row["status"] == "PASS" else "background-color: #f8d7da"
    return [color] * len(row)

st.dataframe(
    val_df.style.apply(highlight_status, axis=1).format(
        {
            "raw_tonnes": "{:,.1f}",
            "pivot_tonnes": "{:,.1f}",
            "tonnes_diff_pct": "{:.4f}%",
            "raw_ounces": "{:,.3f}",
            "pivot_ounces": "{:,.3f}",
            "ounces_diff_pct": "{:.4f}%",
        }
    ),
    width='stretch',
    hide_index=True,
)

if all_pass(val_df):
    st.success("All models PASS validation.")
else:
    st.error("One or more models FAILED validation. Check data integrity.")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: Charts
# ─────────────────────────────────────────────────────────────────────────────
st.header("4. Charts")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Tonnes by Model", "Ounces by Model", "Grade vs Tonnes", "By Classification", "By Status"]
)

with tab1:
    st.plotly_chart(bar_tonnes_by_model(pivot_df), width='stretch')

with tab2:
    st.plotly_chart(bar_ounces_by_model(pivot_df), width='stretch')

with tab3:
    st.plotly_chart(scatter_grade_vs_tonnes(df_filtered), width='stretch')

with tab4:
    st.plotly_chart(pie_resource_class(df_filtered), width='stretch')

with tab5:
    st.plotly_chart(pie_status(df_filtered), width='stretch')

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: Export
# ─────────────────────────────────────────────────────────────────────────────
st.header("5. Export")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="Download Pivot Table (CSV)",
        data=to_csv_bytes(pivot_with_total),
        file_name=f"DIS_pivot_{datetime.date.today()}.csv",
        mime="text/csv",
    )

with col2:
    audit_export = pd.DataFrame(st.session_state.audit_log) if st.session_state.audit_log else None
    excel_bytes = to_excel_bytes(pivot_with_total, df_filtered, audit_export)
    st.download_button(
        label="Download Full Report (Excel)",
        data=excel_bytes,
        file_name=f"DIS_report_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.caption(
    "Excel export includes: DIS Pivot Table sheet, Raw Data sheet, Audit Log sheet."
)
