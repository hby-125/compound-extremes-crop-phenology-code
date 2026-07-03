# Input data

Place the downloaded input data files here.

## Download

Download the companion dataset from Zenodo:

- **DOI**: [10.5281/zenodo.21177297](https://doi.org/10.5281/zenodo.21177297)

## Expected structure

```
data/
├── README.md
├── 04_Grid_Panels/
│   ├── grid_panel_maize.csv     (316 MB)
│   ├── grid_panel_wheat.csv     (220 MB)
│   └── grid_panel_rice.csv      (515 MB)
└── 05_Climate_Data/
    └── china_cube_2000_2019.npz  (102 MB)
```

## Verification

After downloading, verify file integrity using the MD5 checksums listed in `docs/file_manifest.md`.

```bash
md5sum data/04_Grid_Panels/*.csv data/05_Climate_Data/*.npz
```

All checksums must match those in the manifest exactly.
