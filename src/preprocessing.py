"""
Preprocessing utilities for the Irish BER retrofit-prioritisation project.
"""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_COLUMN = "retrofit_priority"


def get_feature_columns(df):
    """Separate feature columns into numerical and categorical columns."""
    feature_df = df.drop(columns=[TARGET_COLUMN])

    numeric_features = feature_df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_features = feature_df.select_dtypes(include=["object", "string"]).columns.tolist()

    return numeric_features, categorical_features


def make_one_hot_encoder():
    """
    Create a OneHotEncoder compatible with different scikit-learn versions.
    Newer versions use sparse_output; older versions use sparse.
    """
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(numeric_features, categorical_features):
    """Build preprocessing pipeline for numerical and categorical features."""

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", make_one_hot_encoder()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )

    return preprocessor