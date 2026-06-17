from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data folders
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Results folders
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_TABLES_DIR = RESULTS_DIR / "tables"
RESULTS_FIGURES_DIR = RESULTS_DIR / "figures"

# Raw and processed data paths
RAW_DATA_FILE = DATA_RAW_DIR / "ber_cleaned_20231005.csv"
MODEL_READY_DATA_FILE = DATA_PROCESSED_DIR / "ber_model_ready.csv"

# Output tables
CLEANING_SUMMARY_FILE = RESULTS_TABLES_DIR / "cleaning_summary.csv"
MODEL_READY_COLUMNS_FILE = RESULTS_TABLES_DIR / "model_ready_columns.csv"

# Reproducibility
RANDOM_STATE = 42

# BER target definition
NOT_PRIORITY_RATINGS = ["A1", "A2", "A3", "B1", "B2"]
PRIORITY_RATINGS = ["B3", "C1", "C2", "C3", "D1", "D2", "E1", "E2", "F", "G"]
VALID_RATINGS = NOT_PRIORITY_RATINGS + PRIORITY_RATINGS