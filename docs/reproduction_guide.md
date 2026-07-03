# Reproduction guide — End-to-end 5 steps

> From a fresh machine to all manuscript Figures and Tables.

## Step 0 — Environment

```bash
# Python ≥ 3.10; conda / mamba recommended
conda env create -f environment.yml
conda activate compound-extremes-phenology

# Or with pip:
pip install -r requirements.txt
```

## Step 1 — Get input data

Download the companion dataset from Zenodo:

- **Data DOI**: [10.5281/zenodo.21177297](https://doi.org/10.5281/zenodo.21177297)

Place the downloaded files as:

```
data/
├── 04_Grid_Panels/
│   ├── grid_panel_maize.csv
│   ├── grid_panel_wheat.csv
│   └── grid_panel_rice.csv
└── 05_Climate_Data/
    └── china_cube_2000_2019.npz
```

**MD5 verification**: see `docs/file_manifest.md` for expected checksums.

## Step 2 — Build analysis panels (optional for pure regression reproduction)

If you only want to reproduce regressions and figures, **skip this step** — use the pre-computed `.parquet` files from the data archive instead.

To reconstruct phenology × climate matching from raw inputs:

```bash
cd 08_Code
python build_pheno_climate_panel.py
```

## Step 3 — Run regressions

```bash
cd 08_Code

# Main regressions: Table 1 / Table 2 / ED Tables 1–4
python analysis.py

# Robustness diagnostics:
python B2_growing_season_diag.py       # ED Table 6
python B3_multiple_testing_fast.py     # ED Table 7
```

Outputs are written to `outputs/tables/`.

## Step 4 — Generate figures

```bash
python figures.py             # Draft raster versions for logic/beauty check
python make_figures_vector.py # Final B&W Times vector Figures 1–4
python A1_ed_figure1.py       # Extended Data Figure 1 (a + b panels)
```

Outputs are written to `outputs/figures/`.

## Step 5 — Compile Source Data + manuscript PDF

```bash
python C1_source_data.py      # Compile Source_Data.xlsx (11 sheets)
python build_v3_pdf.py        # Compile v3 manuscript via Tectonic (LaTeX → PDF)
```

## Verification checklist

Compare your outputs against these expected values:

| Output | Manuscript location | Expected value |
|---|---|---|
| Maize GSL dry-hot β | Table 1 | −0.508 (0.030) |
| Maize GSL wet-hot β | Table 1 | +0.589 (0.033) |
| Maize GSL compound F | Table 1 | 705 |
| Wheat Maturity dry-hot β | ED Table 1 | −0.351 (0.029) |
| Winter-wheat → summer-maize turnover dry-hot β | Table 2 | +0.873 (0.044) |
| Correlation dry-hot vs SU (r) | ED Table 6 | 0.007 |
| B3 robust coefficients count | Robustness section | 9 / 12 |

If all 7 values match, reproduction is verified.

## Common issues

1. **Windows + Chinese paths**: PowerShell GBK may garble Chinese directory names. Use Git Bash or WSL, or absolute paths in Python.
2. **pyfixest vs linearmodels**: This study uses pyfixest for two-way FE + cluster-robust SE. If using linearmodels' `PanelOLS`, set `entity_effects=True, time_effects=True, cov_type='clustered'`.
3. **Times New Roman for figures**: The vector figure script requires Times New Roman. Fallback: `serif='Times, DejaVu Serif'` in `figures.py`.
4. **Parquet compression**: `.parquet` files use snappy compression. If downstream tools are old, convert via `pd.read_parquet(...).to_csv(...)`.
5. **`.npz` memory**: `china_cube_2000_2019.npz` needs ≥ 2 GB RAM when expanded.
6. **Hardcoded paths**: Some scripts contain local `H:\` paths. Update the path variables at the top of each script before running.
