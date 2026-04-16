# Based on PAPER - "Case Study of Using An Excel Pivot Table to Create a Depletion Information System (DIS) for Monitoring and Reporting" By P.F.Forman
# Short description within 350 characters -
Python web application to build a Depletion Information System (DIS) for reconciling geological resource/reserve block models. It removes manual work of repeated script runs and Excel’s 65,536-row limitation in alternative methodology of Excel’s Pivot tables. Also adds interactive charts, automatic validation, and an audit trail.
# Core problem:
Traditionally, Excel Pivot Table is used to build a Depletion Information System (DIS) for reconciling geological resource/reserve block models.
Monthly depletion/reconciliation of multiple large geological resource/reserve  block models (in few GigaBytes) is slow and labour-intensive when done via repeated manual local mining software script runs and formatting.
Alternatives has been extracting data from each geological resource/reserve  block model via local mining software script → import into Excel → tag with model ID → merge all into one spreadsheet → build pivot table. The pivot table allows interactive querying across models for different cut-offs, resource classifications, and mined/unmined areas.
# Solving core problem:
A modern Python web application that reproduces and enhances the Depletion Information System. It removes Excel's 65,536-row limitation and adds interactive charts, automatic validation, and an audit trail.
# Human-in-loop:
DIS results must be verified against local mining software script outputs before use.
