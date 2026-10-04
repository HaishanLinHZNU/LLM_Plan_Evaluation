# Archived statistical materials

`data/human_reference_labels.csv` contains archived reference scores for five development and twenty validation plans, with 56 indicators per plan. It does not document the human audit process.

`configs/dataset_split.csv` records the retained plan assignments. The original randomization seed was not recovered.

`data/predictions_long.csv` contains 4,480 planned validation evaluations across four conditions, including 15 unavailable parsed scores. Retrieved text and retrieval counts are excluded.

Three valid GPT-4o/basic scores are present in the original raw archive and prediction table but absent from the shared resolved JSON. They are retained in this table and identified in `configs/prediction_source_exceptions.csv`.

Run from this directory using Python 3.10 or newer:

```bash
python ./analysis/analyze_archived_results.py
```

The script uses the Python standard library and regenerates the CSV tables in `outputs/tables`. It does not call a model API. Bootstrap settings remain those of the archived analysis script.
