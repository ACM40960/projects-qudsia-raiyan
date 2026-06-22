"""
End-to-end pipeline runner for the Irish BER retrofit-prioritisation project.

This script runs the full project workflow:

1. Data cleaning
2. Exploratory data analysis
3. Model training
4. Final best-model evaluation
5. Explainability analysis
6. Results summary

Run from the project root:

    python src/run_pipeline.py
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


PIPELINE_STEPS = [
    ("Data cleaning", "src/data_cleaning.py"),
    ("Exploratory data analysis", "src/eda.py"),
    ("Model training", "src/train_models.py"),
    ("Final model evaluation", "src/evaluate_models.py"),
    ("Explainability analysis", "src/explainability.py"),
    ("Results summary", "src/results_summary.py"),
]


def run_step(step_name, script_path):
    """Run one pipeline step and stop if it fails."""
    print("\n" + "=" * 70)
    print(f"Running step: {step_name}")
    print("=" * 70)

    full_script_path = PROJECT_ROOT / script_path

    if not full_script_path.exists():
        raise FileNotFoundError(f"Script not found: {full_script_path}")

    result = subprocess.run(
        [sys.executable, str(full_script_path)],
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Pipeline failed during step: {step_name}. "
            f"Script: {script_path}"
        )

    print(f"Completed step: {step_name}")


def main():
    """Run all project pipeline steps."""
    print("Starting end-to-end project pipeline...")

    for step_name, script_path in PIPELINE_STEPS:
        run_step(step_name, script_path)

    print("\n" + "=" * 70)
    print("End-to-end project pipeline completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()