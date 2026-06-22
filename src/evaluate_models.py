"""
Final evaluation script for the Irish BER retrofit-prioritisation project.

This script evaluates the saved best model on the test set and saves
additional evaluation outputs for documentation.

Run from the project root:

    python src/evaluate_models.py
"""

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

from config import (
    MODEL_READY_DATA_FILE,
    RESULTS_TABLES_DIR,
    RANDOM_STATE,
    MODEL_SAMPLE_SIZE,
    PROJECT_ROOT,
)

from preprocessing import TARGET_COLUMN
from train_models import stratified_sample


MODELS_DIR = PROJECT_ROOT / "models"
BEST_MODEL_FILE = MODELS_DIR / "best_model.joblib"


def load_test_data():
    """Load model-ready data and reproduce the test split."""
    if not MODEL_READY_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Model-ready data not found: {MODEL_READY_DATA_FILE}. "
            "Run python src/data_cleaning.py first."
        )

    df = pd.read_csv(MODEL_READY_DATA_FILE, low_memory=False)
    df = stratified_sample(df, MODEL_SAMPLE_SIZE)

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    return X_test, y_test


def evaluate_best_model(model, X_test, y_test):
    """Evaluate saved best model and return summary metrics."""
    y_pred = model.predict(X_test)

    summary = {
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "precision_priority": precision_score(
            y_test, y_pred, pos_label=1, zero_division=0
        ),
        "recall_priority": recall_score(
            y_test, y_pred, pos_label=1, zero_division=0
        ),
        "f1_priority": f1_score(
            y_test, y_pred, pos_label=1, zero_division=0
        ),
        "f1_macro": f1_score(
            y_test, y_pred, average="macro", zero_division=0
        ),
    }

    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
        summary["roc_auc"] = roc_auc_score(y_test, y_prob)
    else:
        summary["roc_auc"] = None

    return summary, y_pred


def save_outputs(summary, y_test, y_pred):
    """Save final evaluation tables."""
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)

    summary_df = pd.DataFrame([summary]).round(4)
    summary_df.to_csv(
        RESULTS_TABLES_DIR / "best_model_evaluation_summary.csv",
        index=False,
    )

    report = classification_report(
        y_test,
        y_pred,
        target_names=["Not retrofit priority", "Retrofit priority"],
        output_dict=True,
        zero_division=0,
    )

    report_df = pd.DataFrame(report).transpose()
    report_df.to_csv(
        RESULTS_TABLES_DIR / "best_model_classification_report.csv"
    )

    cm = confusion_matrix(y_test, y_pred)

    cm_df = pd.DataFrame(
        cm,
        index=["Actual not priority", "Actual priority"],
        columns=["Predicted not priority", "Predicted priority"],
    )

    cm_df.to_csv(
        RESULTS_TABLES_DIR / "best_model_confusion_matrix.csv"
    )


def main():
    """Run final best-model evaluation."""
    print("Starting final best-model evaluation...")

    if not BEST_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Best model not found: {BEST_MODEL_FILE}. "
            "Run python src/train_models.py first."
        )

    model = joblib.load(BEST_MODEL_FILE)
    X_test, y_test = load_test_data()

    summary, y_pred = evaluate_best_model(model, X_test, y_test)
    save_outputs(summary, y_test, y_pred)

    print("Final best-model evaluation complete.")
    print("Evaluation summary:")
    for metric, value in summary.items():
        print(f"{metric}: {value:.4f}" if value is not None else f"{metric}: None")


if __name__ == "__main__":
    main()