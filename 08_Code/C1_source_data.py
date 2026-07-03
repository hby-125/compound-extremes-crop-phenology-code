# -*- coding: utf-8 -*-
"""C1: Source Data workbook for Nature Climate Change.

Compiles per-figure / per-table source data into a single .xlsx with one
worksheet per display item, as required by Nature submission systems."""
import os, pandas as pd
from pathlib import Path

# ---- Path configuration ----
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA_DIR", ROOT / "data"))
OUTPUTS = Path(os.environ.get("OUTPUTS_DIR", ROOT / "outputs"))
PAN = OUTPUTS / "panels"
TAB = OUTPUTS / "tables"
FIG = OUTPUTS / "figures"
OUT = OUTPUTS
OUT.mkdir(parents=True, exist_ok=True)
xlsx = OUT / "Source_Data.xlsx"

# Helpers
def df_baseline_GSL():
    """Table 1 + Fig 1: GSL coefficients for each crop."""
    src = pd.read_csv(TAB / "table2_baseline.csv", encoding="utf-8-sig")
    src = src[src.dv == "gsl"]
    return src.pivot_table(index="var", columns="crop",
                            values=["coef","se","p"]).reorder_levels([1,0], axis=1).sort_index(axis=1)

def df_maturity():
    src = pd.read_csv(TAB / "table2_baseline.csv", encoding="utf-8-sig")
    src = src[src.dv == "mat_doy"]
    return src.pivot_table(index="var", columns="crop",
                            values=["coef","se","p"]).reorder_levels([1,0], axis=1).sort_index(axis=1)

def df_heterogeneity():
    src = pd.read_csv(TAB / "table3_heterogeneity.csv", encoding="utf-8-sig")
    return src

def df_adaptation():
    src = pd.read_csv(TAB / "table4_adaptation.csv", encoding="utf-8-sig")
    return src

def df_turnover():
    src = pd.read_csv(TAB / "table5_turnover.csv", encoding="utf-8-sig")
    return src

def df_robust():
    src = pd.read_csv(TAB / "table6_robustness.csv", encoding="utf-8-sig")
    return src

# Figure source data
fig1_a = pd.read_csv(FIG / "ED_Figure_1_panel_a_data.csv")
fig1_b = pd.read_csv(FIG / "ED_Figure_1_panel_b_data.csv")

# Multiple testing (B3 output, may be written later)
mt_path = TAB / "p1_multiple_testing.csv"
mt = pd.read_csv(mt_path, encoding="utf-8-sig") if mt_path.exists() else None

# B2 diagnostic
b2_corr = pd.read_csv(TAB / "p1_gs_correlations.csv", index_col=0)
b2_reg  = pd.read_csv(TAB / "p1_growing_season_diag.csv")

# Table 1: GSL baseline ✓
# Table 2: turnover ✓
# Fig 1: GSL coefs by crop (=Table 1 data)
# Fig 2: maturity coefs by crop
# Fig 3: heterogeneity N/S
# Fig 4: adaptation × post-2010
# ED Fig 1: compound trend + map

with pd.ExcelWriter(xlsx, engine="openpyxl") as W:
    df_baseline_GSL().to_excel(W, sheet_name="Fig1_Table1_GSL_coefs")
    df_maturity().to_excel(W, sheet_name="Fig2_Maturity_coefs")
    df_heterogeneity().to_excel(W, sheet_name="Fig3_NorthSouth")
    df_adaptation().to_excel(W, sheet_name="Fig4_Adaptation_post2010")
    df_turnover().to_excel(W, sheet_name="Table2_Turnover")
    df_robust().to_excel(W, sheet_name="EDTable4_Robustness")
    fig1_a.to_excel(W, sheet_name="EDFig1a_compound_trend", index=False)
    fig1_b.head(50000).to_excel(W, sheet_name="EDFig1b_dryhot_pixels", index=False)  # cap to xlsx-safe size
    if mt is not None:
        mt.to_excel(W, sheet_name="ED_MultipleTesting", index=False)
    b2_corr.to_excel(W, sheet_name="ED_GSdiag_corrs")
    b2_reg.to_excel(W, sheet_name="ED_GSdiag_regressions", index=False)

print(f"Source_Data.xlsx written: {xlsx}")
print(f"  Size: {xlsx.stat().st_size/1024:.0f} KB")
