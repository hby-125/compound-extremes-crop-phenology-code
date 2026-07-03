# File manifest — MD5 checksums for input data

> Verify downloaded files against these checksums before running the analysis.

## Grid-level phenology panels

| File | Size (MB) | MD5 |
| --- | --- | --- |
| `data/04_Grid_Panels/grid_panel_maize.csv` | 316.23 | `b82b47ca3e97e52c711d045a365d6492` |
| `data/04_Grid_Panels/grid_panel_wheat.csv` | 220.47 | `801e6e37b0a4c4bbcdb92a6af5c197be` |
| `data/04_Grid_Panels/grid_panel_rice.csv` | 515.45 | `a36262984a860beeb1681b2e1005ff54` |

## Climate data cube

| File | Size (MB) | MD5 |
| --- | --- | --- |
| `data/05_Climate_Data/china_cube_2000_2019.npz` | 101.95 | `c42b35fe9d8f07f8de1432b3cd847151` |

## Verify checksums

```bash
# Linux / macOS / Git Bash
md5sum data/04_Grid_Panels/grid_panel_*.csv data/05_Climate_Data/china_cube_2000_2019.npz

# Compare output with the MD5 column above — all four must match exactly.
```
