# Outputs

Generated files from the analysis pipeline are written here.

## Directory structure (auto-created by scripts)

```
outputs/
├── tables/        # Regression coefficient CSVs, facts.json, results_readable.txt
├── figures/       # Figure PDFs (Fig 1–4, Extended Data Fig 1)
├── panels/        # Intermediate analysis panels (.parquet)
└── source_data/   # Source_Data.xlsx (11 sheets)
```

## Notes

- This directory is in `.gitignore` — generated files are not tracked by git.
- Each script auto-creates its output subdirectory if it does not exist.
- To re-run from scratch, delete the relevant subdirectory before running the script.
