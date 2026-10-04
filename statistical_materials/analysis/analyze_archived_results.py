"""No-rerun analysis of archived plan-evaluation outputs.

This script reads the included validation predictions CSV and reference-label
JSON, and regenerates the archived statistical tables without model API calls.
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT
CONFIG_DIR = ANALYSIS_ROOT / "configs"
DATA_DIR = ANALYSIS_ROOT / "data"
TABLE_DIR = ANALYSIS_ROOT / "outputs" / "tables"
QA_DIR = ANALYSIS_ROOT / "outputs" / "qa_reports"

VALIDATION_SPLIT = DATA_DIR / "validation_reference_labels.json"

CONDITIONS = {
    "gpt4o_final": {
        "model_label": "GPT-4o",
        "prompt_condition": "optimized",
        "raw_path": ROOT.parent / "GPT-4o_optimized-prompt_run-start_2025-02-23_05-05-15_resolved.json",
        "source_timestamp": "25-02-23 05-05-15",
        "legacy_label": "4o finial",
    },
    "gpt4o_basic": {
        "model_label": "GPT-4o",
        "prompt_condition": "basic",
        "raw_path": ROOT.parent / "GPT-4o_basic-prompt_run-start_2025-02-25_20-15-26_resolved.json",
        "source_timestamp": "25-02-25 20-15-26",
        "legacy_label": "4o basic",
    },
    "gpt4o_mini_basic": {
        "model_label": "GPT-4o mini",
        "prompt_condition": "basic",
        "raw_path": ROOT.parent / "GPT-4o-mini_basic-prompt_run-start_2025-02-27_05-53-25_resolved.json",
        "source_timestamp": "25-02-27 05-53-25",
        "legacy_label": "4o-mini basic",
    },
    "gpt4o_mini_final": {
        "model_label": "GPT-4o mini",
        "prompt_condition": "optimized",
        "raw_path": ROOT.parent / "GPT-4o-mini_optimized-prompt_run-start_2025-03-01_17-09-40_resolved.json",
        "source_timestamp": "25-03-01 17-09-40",
        "legacy_label": "4o-mini finial",
    },
}


@dataclass(frozen=True)
class Prediction:
    condition_id: str
    model_label: str
    prompt_condition: str
    county: str
    split: str
    indicator: str
    human_score: int | None
    model_score: int | None
    binary_human_score: int | None
    binary_model_score: int | None
    score_parse_status: str
    raw_result_file: str
    source_timestamp: str


def ensure_dirs() -> None:
    for path in [CONFIG_DIR, DATA_DIR, TABLE_DIR, QA_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse_score(score_text: str | None) -> tuple[int | None, str]:
    if not score_text:
        return None, "missing_score_text"
    patterns = [
        r"###\s*Score:\s*([012])\b",
        r"###Score:\s*([012])\b",
        r"\bScore:\s*([012])\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, score_text)
        if match:
            return int(match.group(1)), "parsed"
    return None, "unparseable_score_text"


def to_binary(score: int | None) -> int | None:
    if score is None:
        return None
    return 0 if score == 0 else 1


def build_dataset_split(validation_data: dict) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for county, items in validation_data.items():
        for item in items:
            rows.append(
                {
                    "county": county,
                    "indicator": item["indicator"],
                    "split": "validation",
                    "human_score": str(item["value"]),
                }
            )
    return rows


def normalize_predictions(validation_data: dict) -> list[Prediction]:
    predictions = []
    with (DATA_DIR / "predictions_long.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["county"] not in validation_data:
                raise ValueError("Prediction outside validation split")
            for name in ("human_score", "model_score", "binary_human_score", "binary_model_score"):
                row[name] = int(row[name]) if row[name] else None
            predictions.append(Prediction(**row))
    return predictions



def write_csv(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def prediction_to_dict(p: Prediction) -> dict:
    return {
        "condition_id": p.condition_id,
        "model_label": p.model_label,
        "prompt_condition": p.prompt_condition,
        "county": p.county,
        "split": p.split,
        "indicator": p.indicator,
        "human_score": p.human_score,
        "model_score": p.model_score,
        "binary_human_score": p.binary_human_score,
        "binary_model_score": p.binary_model_score,
        "score_parse_status": p.score_parse_status,
        "raw_result_file": p.raw_result_file,
        "source_timestamp": p.source_timestamp,
    }


def parsed(rows: Iterable[Prediction], binary: bool = False) -> list[Prediction]:
    out = []
    for row in rows:
        if binary:
            if row.binary_human_score is not None and row.binary_model_score is not None:
                out.append(row)
        elif row.human_score is not None and row.model_score is not None:
            out.append(row)
    return out


def agreement(rows: Iterable[Prediction], binary: bool = False) -> float:
    rows = parsed(rows, binary=binary)
    if not rows:
        return math.nan
    if binary:
        correct = sum(row.binary_human_score == row.binary_model_score for row in rows)
    else:
        correct = sum(row.human_score == row.model_score for row in rows)
    return correct / len(rows) * 100


def table1_county_ternary(predictions: list[Prediction], validation_counties: list[str]) -> list[dict]:
    rows = []
    for county in validation_counties:
        row = {"county": county}
        for condition_id in CONDITIONS:
            subset = [p for p in predictions if p.condition_id == condition_id and p.county == county]
            row[f"{condition_id}_agreement"] = round(agreement(subset), 6)
            row[f"{condition_id}_parsed_n"] = len(parsed(subset))
            row[f"{condition_id}_missing_n"] = len(subset) - len(parsed(subset))
        rows.append(row)
    return rows


def table2_indicator_ternary(predictions: list[Prediction], indicators: list[str]) -> list[dict]:
    rows = []
    for indicator in indicators:
        row = {"indicator": indicator}
        for condition_id in CONDITIONS:
            subset = [p for p in predictions if p.condition_id == condition_id and p.indicator == indicator]
            row[f"{condition_id}_agreement"] = round(agreement(subset), 6)
            row[f"{condition_id}_parsed_n"] = len(parsed(subset))
            row[f"{condition_id}_missing_n"] = len(subset) - len(parsed(subset))
        rows.append(row)
    return rows


def table4_indicator_binary(predictions: list[Prediction], indicators: list[str]) -> list[dict]:
    rows = []
    for indicator in indicators:
        row = {"indicator": indicator}
        for condition_id in CONDITIONS:
            subset = [p for p in predictions if p.condition_id == condition_id and p.indicator == indicator]
            row[f"{condition_id}_binary_agreement"] = round(agreement(subset, binary=True), 6)
            row[f"{condition_id}_parsed_n"] = len(parsed(subset, binary=True))
            row[f"{condition_id}_missing_n"] = len(subset) - len(parsed(subset, binary=True))
        rows.append(row)
    return rows


def condition_summary(predictions: list[Prediction]) -> list[dict]:
    rows = []
    for condition_id, meta in CONDITIONS.items():
        subset = [p for p in predictions if p.condition_id == condition_id]
        county_agreements = [
            agreement([p for p in subset if p.county == county])
            for county in sorted({p.county for p in subset})
        ]
        rows.append(
            {
                "condition_id": condition_id,
                "model_label": meta["model_label"],
                "prompt_condition": meta["prompt_condition"],
                "legacy_label": meta["legacy_label"],
                "overall_item_agreement": round(agreement(subset), 6),
                "mean_county_agreement": round(mean(county_agreements), 6),
                "min_county_agreement": round(min(county_agreements), 6),
                "max_county_agreement": round(max(county_agreements), 6),
                "overall_binary_agreement": round(agreement(subset, binary=True), 6),
                "cohen_kappa_unweighted": round(cohen_kappa(subset), 6),
                "cohen_kappa_linear_weighted": round(cohen_kappa(subset, weights="linear"), 6),
                "binary_cohen_kappa": round(cohen_kappa(subset, binary=True), 6),
                "expected_n": len(subset),
                "parsed_n": len(parsed(subset)),
                "missing_n": len(subset) - len(parsed(subset)),
            }
        )
    return rows


def confusion_matrix(rows: list[Prediction], binary: bool = False) -> dict[str, int]:
    matrix = Counter()
    for row in parsed(rows, binary=binary):
        if binary:
            matrix[f"{row.binary_human_score}->{row.binary_model_score}"] += 1
        else:
            matrix[f"{row.human_score}->{row.model_score}"] += 1
    return dict(sorted(matrix.items()))


def cohen_kappa(rows: list[Prediction], *, binary: bool = False, weights: str | None = None) -> float:
    rows = parsed(rows, binary=binary)
    if not rows:
        return math.nan
    labels = [0, 1] if binary else [0, 1, 2]
    n = len(rows)
    observed = {(a, b): 0 for a in labels for b in labels}
    actual_counts = Counter()
    predicted_counts = Counter()
    for row in rows:
        a = row.binary_human_score if binary else row.human_score
        b = row.binary_model_score if binary else row.model_score
        observed[(a, b)] += 1
        actual_counts[a] += 1
        predicted_counts[b] += 1

    def disagreement_weight(a: int, b: int) -> float:
        if weights == "linear":
            return abs(a - b) / (len(labels) - 1)
        return 0.0 if a == b else 1.0

    observed_disagreement = sum(disagreement_weight(a, b) * count for (a, b), count in observed.items()) / n
    expected_disagreement = 0.0
    for a in labels:
        for b in labels:
            expected = (actual_counts[a] / n) * (predicted_counts[b] / n)
            expected_disagreement += disagreement_weight(a, b) * expected
    if expected_disagreement == 0:
        return math.nan
    return 1 - observed_disagreement / expected_disagreement


def class_metrics(rows: list[Prediction], labels: list[int], binary: bool = False) -> list[dict]:
    out = []
    rows = parsed(rows, binary=binary)
    for label in labels:
        if binary:
            tp = sum(r.binary_human_score == label and r.binary_model_score == label for r in rows)
            fp = sum(r.binary_human_score != label and r.binary_model_score == label for r in rows)
            fn = sum(r.binary_human_score == label and r.binary_model_score != label for r in rows)
        else:
            tp = sum(r.human_score == label and r.model_score == label for r in rows)
            fp = sum(r.human_score != label and r.model_score == label for r in rows)
            fn = sum(r.human_score == label and r.model_score != label for r in rows)
        precision = tp / (tp + fp) if tp + fp else math.nan
        recall = tp / (tp + fn) if tp + fn else math.nan
        f1 = 2 * precision * recall / (precision + recall) if precision + recall and not math.isnan(precision) and not math.isnan(recall) else math.nan
        out.append(
            {
                "label": label,
                "precision": round(precision, 6) if not math.isnan(precision) else "",
                "recall": round(recall, 6) if not math.isnan(recall) else "",
                "f1": round(f1, 6) if not math.isnan(f1) else "",
                "tp": tp,
                "fp": fp,
                "fn": fn,
            }
        )
    return out


def bootstrap_ci_by_county(
    predictions: list[Prediction],
    condition_id: str,
    *,
    binary: bool = False,
    iterations: int = 5000,
    seed: int = 20260724,
) -> tuple[float, float]:
    rng = random.Random(seed)
    subset = [p for p in predictions if p.condition_id == condition_id]
    counties = sorted({p.county for p in subset})
    by_county = {county: [p for p in subset if p.county == county] for county in counties}
    values = []
    for _ in range(iterations):
        sampled = []
        for _ in counties:
            sampled.extend(by_county[rng.choice(counties)])
        values.append(agreement(sampled, binary=binary))
    values.sort()
    low = values[int(0.025 * iterations)]
    high = values[int(0.975 * iterations)]
    return low, high


def paired_prompt_differences(predictions: list[Prediction]) -> list[dict]:
    pairs = [
        ("GPT-4o", "gpt4o_final", "gpt4o_basic"),
        ("GPT-4o mini", "gpt4o_mini_final", "gpt4o_mini_basic"),
    ]
    rows = []
    for model_label, optimized_id, basic_id in pairs:
        counties = sorted({p.county for p in predictions if p.condition_id == optimized_id})
        diffs = []
        for county in counties:
            opt = agreement([p for p in predictions if p.condition_id == optimized_id and p.county == county])
            bas = agreement([p for p in predictions if p.condition_id == basic_id and p.county == county])
            diff = opt - bas
            diffs.append(diff)
            rows.append(
                {
                    "model_label": model_label,
                    "county": county,
                    "optimized_condition": optimized_id,
                    "basic_condition": basic_id,
                    "optimized_agreement": round(opt, 6),
                    "basic_agreement": round(bas, 6),
                    "difference_percentage_points": round(diff, 6),
                }
            )
        rows.append(
            {
                "model_label": model_label,
                "county": "MEAN",
                "optimized_condition": optimized_id,
                "basic_condition": basic_id,
                "optimized_agreement": "",
                "basic_agreement": "",
                "difference_percentage_points": round(mean(diffs), 6),
            }
        )
    return rows


def paired_difference_ci(
    predictions: list[Prediction],
    optimized_id: str,
    basic_id: str,
    *,
    binary: bool = False,
    iterations: int = 5000,
    seed: int = 20260724,
) -> tuple[float, float, float]:
    rng = random.Random(seed)
    counties = sorted({p.county for p in predictions if p.condition_id == optimized_id})
    by_county = {}
    for county in counties:
        opt_rows = [p for p in predictions if p.condition_id == optimized_id and p.county == county]
        bas_rows = [p for p in predictions if p.condition_id == basic_id and p.county == county]
        by_county[county] = agreement(opt_rows, binary=binary) - agreement(bas_rows, binary=binary)
    point = mean(by_county.values())
    values = []
    for _ in range(iterations):
        sampled = [by_county[rng.choice(counties)] for _ in counties]
        values.append(mean(sampled))
    values.sort()
    return point, values[int(0.025 * iterations)], values[int(0.975 * iterations)]


def missing_output_sensitivity(predictions: list[Prediction]) -> list[dict]:
    rows = []
    for condition_id, meta in CONDITIONS.items():
        subset = [p for p in predictions if p.condition_id == condition_id]
        correct = sum(
            p.model_score is not None and p.model_score == p.human_score
            for p in subset
        )
        rows.append(
            {
                "analysis": "expected_denominator_unparseable_as_disagreement",
                "model_label": meta["model_label"],
                "condition_id": condition_id,
                "comparison_condition_id": "",
                "correct_n": correct,
                "denominator_n": len(subset),
                "agreement_or_difference_percentage_points": round(correct / len(subset) * 100, 6),
            }
        )

    for model_label, optimized_id, basic_id in [
        ("GPT-4o", "gpt4o_final", "gpt4o_basic"),
        ("GPT-4o mini", "gpt4o_mini_final", "gpt4o_mini_basic"),
    ]:
        county_differences = []
        intersection_n = 0
        counties = sorted({p.county for p in predictions if p.condition_id == optimized_id})
        for county in counties:
            optimized = {
                p.indicator: p
                for p in predictions
                if p.condition_id == optimized_id and p.county == county
            }
            basic = {
                p.indicator: p
                for p in predictions
                if p.condition_id == basic_id and p.county == county
            }
            indicators = [
                indicator
                for indicator in optimized.keys() & basic.keys()
                if optimized[indicator].model_score is not None
                and basic[indicator].model_score is not None
            ]
            intersection_n += len(indicators)
            optimized_agreement = mean(
                optimized[indicator].model_score == optimized[indicator].human_score
                for indicator in indicators
            ) * 100
            basic_agreement = mean(
                basic[indicator].model_score == basic[indicator].human_score
                for indicator in indicators
            ) * 100
            county_differences.append(optimized_agreement - basic_agreement)
        rows.append(
            {
                "analysis": "paired_intersection_only_optimized_minus_basic",
                "model_label": model_label,
                "condition_id": optimized_id,
                "comparison_condition_id": basic_id,
                "correct_n": "",
                "denominator_n": intersection_n,
                "agreement_or_difference_percentage_points": round(mean(county_differences), 6),
            }
        )
    return rows


def make_run_manifest() -> list[dict]:
    rows = []
    for condition_id, meta in CONDITIONS.items():
        rows.append(
            {
                "condition_id": condition_id,
                "source_type": "shared_resolved_json_and_prediction_table",
                "source_file": "../" + meta["raw_path"].name,
                "model_label": meta["model_label"],
                "model_snapshot_or_alias": "legacy script/assistant setting; exact snapshot not recovered here",
                "prompt_condition": meta["prompt_condition"],
                "dataset_split": "validation subset from 40-county archived run",
                "validation_split_file": "data/validation_reference_labels.json",
                "file_search_used_in_archived_run": "yes",
                "new_model_run_performed": "no",
                "source_timestamp": meta["source_timestamp"],
                "notes": "No-rerun analysis of archived outputs only.",
            }
        )
    return rows


def write_qa_report(predictions, summary_rows, table1_rows, validation_counties):
    lines = ["# Archived validation analysis", "", "No model API calls are made.", ""]
    for row in summary_rows:
        low, high = bootstrap_ci_by_county(predictions, row["condition_id"])
        binary_low, binary_high = bootstrap_ci_by_county(predictions, row["condition_id"], binary=True)
        row["agreement_ci95_low"] = round(low, 6)
        row["agreement_ci95_high"] = round(high, 6)
        row["binary_agreement_ci95_low"] = round(binary_low, 6)
        row["binary_agreement_ci95_high"] = round(binary_high, 6)
        lines.append(f"{row['condition_id']}: mean county agreement {row['mean_county_agreement']:.6f}%; missing scores {row['missing_n']}.")
    (QA_DIR / "archived_result_qa_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")



def main() -> None:
    ensure_dirs()
    validation_data = load_json(VALIDATION_SPLIT)
    validation_counties = list(validation_data)
    indicators = [item["indicator"] for item in next(iter(validation_data.values()))]

    dataset_split_rows = build_dataset_split(validation_data)
    predictions = normalize_predictions(validation_data)
    prediction_rows = [prediction_to_dict(p) for p in predictions]

    write_csv(CONFIG_DIR / "validation_indicator_labels.csv", dataset_split_rows)
    write_csv(CONFIG_DIR / "run_manifest_archived.csv", make_run_manifest())
    write_csv(DATA_DIR / "predictions_long.csv", prediction_rows)

    summary_rows = condition_summary(predictions)
    table1_rows = table1_county_ternary(predictions, validation_counties)
    table2_rows = table2_indicator_ternary(predictions, indicators)
    table4_rows = table4_indicator_binary(predictions, indicators)
    paired_rows = paired_prompt_differences(predictions)

    write_csv(TABLE_DIR / "condition_summary.csv", summary_rows)
    write_csv(TABLE_DIR / "table1_county_ternary.csv", table1_rows)
    write_csv(TABLE_DIR / "table2_indicator_ternary.csv", table2_rows)
    write_csv(TABLE_DIR / "table4_indicator_binary_posthoc.csv", table4_rows)
    write_csv(TABLE_DIR / "paired_prompt_differences_by_county.csv", paired_rows)
    write_csv(TABLE_DIR / "missing_output_sensitivity.csv", missing_output_sensitivity(predictions))

    all_class_rows = []
    all_confusion_rows = []
    for condition_id in CONDITIONS:
        subset = [p for p in predictions if p.condition_id == condition_id]
        for row in class_metrics(subset, labels=[0, 1, 2]):
            all_class_rows.append({"condition_id": condition_id, "scale": "ternary", **row})
        for row in class_metrics(subset, labels=[0, 1], binary=True):
            all_class_rows.append({"condition_id": condition_id, "scale": "binary_posthoc", **row})
        for key, value in confusion_matrix(subset).items():
            all_confusion_rows.append({"condition_id": condition_id, "scale": "ternary", "cell": key, "count": value})
        for key, value in confusion_matrix(subset, binary=True).items():
            all_confusion_rows.append({"condition_id": condition_id, "scale": "binary_posthoc", "cell": key, "count": value})
    write_csv(TABLE_DIR / "class_specific_metrics.csv", all_class_rows)
    write_csv(TABLE_DIR / "confusion_matrices_long.csv", all_confusion_rows)

    write_qa_report(predictions, summary_rows, table1_rows, validation_counties)
    write_csv(TABLE_DIR / "condition_summary_with_ci.csv", summary_rows)

    paired_ci_rows = []
    for model_label, optimized_id, basic_id in [
        ("GPT-4o", "gpt4o_final", "gpt4o_basic"),
        ("GPT-4o mini", "gpt4o_mini_final", "gpt4o_mini_basic"),
    ]:
        point, low, high = paired_difference_ci(predictions, optimized_id, basic_id)
        b_point, b_low, b_high = paired_difference_ci(predictions, optimized_id, basic_id, binary=True)
        paired_ci_rows.append(
            {
                "model_label": model_label,
                "scale": "ternary",
                "optimized_condition": optimized_id,
                "basic_condition": basic_id,
                "mean_difference_percentage_points": round(point, 6),
                "ci95_low": round(low, 6),
                "ci95_high": round(high, 6),
            }
        )
        paired_ci_rows.append(
            {
                "model_label": model_label,
                "scale": "binary_posthoc",
                "optimized_condition": optimized_id,
                "basic_condition": basic_id,
                "mean_difference_percentage_points": round(b_point, 6),
                "ci95_low": round(b_low, 6),
                "ci95_high": round(b_high, 6),
            }
        )
    write_csv(TABLE_DIR / "paired_prompt_differences_with_ci.csv", paired_ci_rows)

    print("No-rerun archived analysis complete.")
    print(f"Predictions: {DATA_DIR / 'predictions_long.csv'}")
    print(f"QA report: {QA_DIR / 'archived_result_qa_report.md'}")


if __name__ == "__main__":
    main()
