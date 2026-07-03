# Code for "Compound climate extremes reshape staple-crop phenology and cropping-system turnaround windows across China"

## Overview

This repository contains the complete analysis code for the manuscript **"Compound climate extremes reshape staple-crop phenology and cropping-system turnaround windows across China"**. The scripts cover the full pipeline: climate cube construction, phenology-climate panel matching, econometric regression, robustness diagnostics, figure generation, and Source Data compilation.

- **Code DOI**: `10.5281/zenodo.yyyyyyy` *(to be assigned upon Zenodo publication)*
- **Data DOI**: [10.5281/zenodo.21177297](https://doi.org/10.5281/zenodo.21177297)
- **Version**: v1.0
- **Contact**: <s2508012002@neau.edu.cn>

## Repository structure

```
compound-extremes-crop-phenology-code/
├── README.md
├── LICENSE
├── CITATION.cff
├── environment.yml
├── requirements.txt
├── .gitignore
├── 08_Code/                          # All analysis scripts (13 files)
├── docs/                             # Documentation
│   ├── reproduction_guide.md
│   ├── data_dictionary.md
│   └── file_manifest.md
├── data/                             # Place input data here
│   └── README.md
└── outputs/                          # Generated outputs
    └── README.md
```

## Dependencies

- Python ≥ 3.10
- Core: pandas, numpy, scipy, pyarrow, matplotlib, statsmodels
- Regression: pyfixest (recommended) or linearmodels
- Geospatial: pyproj
- Climate I/O: h5py, netcdf4
- Document: openpyxl

See `environment.yml` (conda) or `requirements.txt` (pip) for the full specification.

## Quick start

```bash
# 1. Clone and set up environment
git clone <repo-url>
cd compound-extremes-crop-phenology-code
conda env create -f environment.yml
conda activate compound-extremes-phenology

# 2. Download input data from Zenodo
#    https://doi.org/10.5281/zenodo.21177297
#    Place the downloaded files as:
#      data/04_Grid_Panels/grid_panel_{maize,wheat,rice}.csv
#      data/05_Climate_Data/china_cube_2000_2019.npz

# 3. Build analysis panels
cd 08_Code
python build_pheno_climate_panel.py

# 4. Run regressions
python analysis.py

# 5. Diagnostics
python B2_growing_season_diag.py
python B3_multiple_testing_fast.py

# 6. Generate figures
python figures.py
python make_figures_vector.py
python A1_ed_figure1.py

# 7. Compile Source Data
python C1_source_data.py
```

## Scripts

Scripts are ordered by pipeline stage:

| Stage | Script | Description |
| --- | --- | --- |
| 1 — Climate | `build_china_cube.py` | Construct `china_cube_2000_2019.npz` from ERA5-Land netCDF files |
| 1 — Climate | `compute_dds.py` | Compute growing-degree-day and compound-event counts |
| 1 — Climate | `probe_nc.py` | Inspect NetCDF file structure and variable metadata |
| 2 — Panel | `build_panels.py` | Build pixel-year phenology panels from grid CSVs |
| 2 — Panel | `build_pheno_climate_panel.py` | Merge phenology with climate via nearest-neighbour matching |
| 3 — Analysis | `analysis.py` | Main regressions: Table 1 (GSL), Table 2 (turnover), ED Tables 1–4 |
| 4 — Diagnostics | `B2_growing_season_diag.py` | Growing-season diagnostic: SU/WSDI substitution + horse-race |
| 4 — Diagnostics | `B3_multiple_testing_fast.py` | Multiple-testing correction (Holm, BH-FDR, sharpened FDR) |
| 5 — Figures | `figures.py` | Draft raster versions of Figures 1–4 |
| 5 — Figures | `make_figures_vector.py` | Final B&W Times vector Figures 1–4 |
| 5 — Figures | `A1_ed_figure1.py` | Extended Data Figure 1 (time-series + spatial map) |
| 6 — Output | `C1_source_data.py` | Compile `Source_Data.xlsx` (11 sheets) from regression outputs |
| 6 — Output | `build_v3_pdf.py` | Compile manuscript PDF via Tectonic LaTeX |

## Input data

This code expects the input data from the companion Zenodo dataset:

- **DOI**: [10.5281/zenodo.21177297](https://doi.org/10.5281/zenodo.21177297)

After downloading, place files under `data/` as described in `data/README.md`.

## Outputs

All generated files are written to `outputs/`:
- `outputs/tables/` — Regression coefficient CSVs + `facts.json` + `results_readable.txt`
- `outputs/figures/` — Figure PDFs
- `outputs/source_data/` — `Source_Data.xlsx`

## Note on paths

Some scripts contain hard-coded local file paths (e.g., `H:\...`). Before running, update the path variables at the top of each script to point to your local `data/` and `outputs/` directories.

## License

Code: **MIT License** — See [LICENSE](LICENSE).

Data (companion archive): **CC BY 4.0** — See [10.5281/zenodo.21177297](https://doi.org/10.5281/zenodo.21177297).
