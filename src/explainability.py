"""
Explainability analysis for the Irish BER retrofit-prioritisation project.

This script:
1. Loads the best trained model.
2. Recreates the same modelling sample and train/test split.
3. Computes permutation importance on the test set.
4. Saves feature-importance tables and plots.

Run from the project root:

    python src/explainability.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance

from config import (
    MODEL_READY_DATA_FILE,
    RESULTS_TABLES_DIR,
    RESULTS_FIGURES_DIR,
    RANDOM_STATE,
    MODEL_SAMPLE_SIZE,
    PROJECT_ROOT,
)

from preprocessing import TARGET_COLUMN
from train_models import stratified_sample


MODELS_DIR = PROJECT_ROOT / "models"
BEST_MODEL_FILE = MODELS_DIR / "best_model.joblib"


def load_data():
    """Load model-ready data and reproduce the modelling sample."""
    df = pd.read_csv(MODEL_READY_DATA_FILE, low_memory=False)
    df = stratified_sample(df, MODEL_SAMPLE_SIZE)

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    return X_train, X_test, y_train, y_test


def compute_permutation_importance(model, X_test, y_test):
    """
    Compute permutation importance at original feature level.

    Since the full pipeline accepts the raw dataframe, permutation importance
    here measures how much model performance decreases when each original
    feature column is randomly shuffled.
    """
    print("Computing permutation importance...")

    # Use a smaller test sample for speed.
    if len(X_test) > 10000:
        X_perm, _, y_perm, _ = train_test_split(
            X_test,
            y_test,
            train_size=10000,
            stratify=y_test,
            random_state=RANDOM_STATE,
        )
    else:
        X_perm = X_test
        y_perm = y_test

    result = permutation_importance(
        model,
        X_perm,
        y_perm,
        n_repeats=5,
        random_state=RANDOM_STATE,
        scoring="f1_macro",
        n_jobs=1,
    )

    importance_df = pd.DataFrame(
        {
            "feature": X_perm.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    ).sort_values(by="importance_mean", ascending=False)

    return importance_df


def save_importance_plot(importance_df, top_n=15):
    """Save top feature importance plot."""
    top_features = importance_df.head(top_n).sort_values(
        by="importance_mean",
        ascending=True,
    )

    plt.figure(figsize=(10, 7))
    plt.barh(top_features["feature"], top_features["importance_mean"])
    plt.xlabel("Mean decrease in macro F1 after permutation")
    plt.ylabel("Feature")
    plt.title("Top Feature Importances by Permutation Importance")
    plt.tight_layout()

    output_path = RESULTS_FIGURES_DIR / "permutation_importance_top_features.png"
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    """Run explainability analysis."""
    print("Starting explainability analysis...")

    if not BEST_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Best model not found: {BEST_MODEL_FILE}\n"
            "Run python src/train_models.py first."
        )

    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    model = joblib.load(BEST_MODEL_FILE)

    _, X_test, _, y_test = load_data()

    importance_df = compute_permutation_importance(model, X_test, y_test)

    importance_path = RESULTS_TABLES_DIR / "permutation_importance.csv"
    importance_df.to_csv(importance_path, index=False)

    save_importance_plot(importance_df, top_n=15)

    print("Explainability analysis complete.")
    print(f"Permutation importance saved to: {importance_path}")
    print("Top 10 features:")
    print(importance_df.head(10))


if __name__ == "__main__":
    main()