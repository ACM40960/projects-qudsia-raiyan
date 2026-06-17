"""
Data cleaning pipeline for the Irish BER retrofit-prioritisation project.

This script:
1. Loads selected columns from the raw BER dataset.
2. Creates a binary retrofit_priority target.
3. Keeps only safe modelling features.
4. Cleans basic data types.
5. Saves a model-ready dataset to data/processed/.
6. Saves summary tables to results/tables/.

Run from the project root with:

    python src/data_cleaning.py
"""

import pandas as pd

from config import (
    RAW_DATA_FILE,
    MODEL_READY_DATA_FILE,
    CLEANING_SUMMARY_FILE,
    MODEL_READY_COLUMNS_FILE,
    DATA_PROCESSED_DIR,
    RESULTS_TABLES_DIR,
    VALID_RATINGS,
    PRIORITY_RATINGS,
)


# Candidate columns chosen from the initial inspection.
# We avoid direct leakage columns such as BerRating and CO2Rating.
CANDIDATE_COLUMNS = [
    "CountyName",
    "DwellingTypeDescr",
    "Year_of_Construction",
    "TypeofRating",
    "EnergyRating",
    "GroundFloorArea(sq m)",
    "UValueWall",
    "UValueRoof",
    "UValueFloor",
    "UValueWindow",
    "UvalueDoor",
    "WallArea",
    "RoofArea",
    "FloorArea",
    "WindowArea",
    "DoorArea",
    "NoStoreys",
    "MainSpaceHeatingFuel",
    "MainWaterHeatingFuel",
    "ThermalEra",
    "GlazingPercent",
    "Volume",
]


RENAME_MAP = {
    "CountyName": "county_name",
    "DwellingTypeDescr": "dwelling_type",
    "Year_of_Construction": "year_of_construction",
    "TypeofRating": "type_of_rating",
    "EnergyRating": "energy_rating",
    "GroundFloorArea(sq m)": "ground_floor_area",
    "UValueWall": "u_value_wall",
    "UValueRoof": "u_value_roof",
    "UValueFloor": "u_value_floor",
    "UValueWindow": "u_value_window",
    "UvalueDoor": "u_value_door",
    "WallArea": "wall_area",
    "RoofArea": "roof_area",
    "FloorArea": "floor_area",
    "WindowArea": "window_area",
    "DoorArea": "door_area",
    "NoStoreys": "no_storeys",
    "MainSpaceHeatingFuel": "main_space_heating_fuel",
    "MainWaterHeatingFuel": "main_water_heating_fuel",
    "ThermalEra": "thermal_era",
    "GlazingPercent": "glazing_percent",
    "Volume": "volume",
}


NUMERIC_COLUMNS = [
    "year_of_construction",
    "ground_floor_area",
    "u_value_wall",
    "u_value_roof",
    "u_value_floor",
    "u_value_window",
    "u_value_door",
    "wall_area",
    "roof_area",
    "floor_area",
    "window_area",
    "door_area",
    "no_storeys",
    "glazing_percent",
    "volume",
]


CATEGORICAL_COLUMNS = [
    "county_name",
    "dwelling_type",
    "type_of_rating",
    "main_space_heating_fuel",
    "main_water_heating_fuel",
    "thermal_era",
]


def get_available_columns(raw_path):
    """Read only the header row and return available columns."""
    return pd.read_csv(raw_path, nrows=0).columns.tolist()


def load_selected_data(raw_path):
    """Load only candidate columns that exist in the raw dataset."""
    available_columns = get_available_columns(raw_path)

    selected_columns = [col for col in CANDIDATE_COLUMNS if col in available_columns]
    missing_columns = [col for col in CANDIDATE_COLUMNS if col not in available_columns]

    if "EnergyRating" not in selected_columns:
        raise ValueError("EnergyRating column is required to create the target variable.")

    print(f"Selected {len(selected_columns)} columns from raw dataset.")
    if missing_columns:
        print("Warning: these candidate columns were not found and will be skipped:")
        for col in missing_columns:
            print(f"  - {col}")

    df = pd.read_csv(raw_path, usecols=selected_columns, low_memory=False)
    return df


def clean_basic_values(df):
    """Rename columns, clean strings, and convert numeric columns."""
    df = df.rename(columns=RENAME_MAP)

    # Strip whitespace from text columns
    text_columns = df.select_dtypes(include=["object"]).columns
    for col in text_columns:
        df[col] = df[col].astype("string").str.strip()

    # Convert numerical columns safely
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def create_target(df):
    """Create binary retrofit_priority target from BER energy rating."""
    df = df.copy()

    # Keep only valid BER labels
    df = df[df["energy_rating"].isin(VALID_RATINGS)].copy()

    # 1 = retrofit priority, 0 = not retrofit priority
    df["retrofit_priority"] = df["energy_rating"].isin(PRIORITY_RATINGS).astype(int)

    return df


def remove_leakage_columns(df):
    """
    Remove columns that directly reveal the target.

    energy_rating is used only to create retrofit_priority, so it is removed
    before modelling.
    """
    leakage_columns = ["energy_rating"]

    existing_leakage_columns = [col for col in leakage_columns if col in df.columns]
    df = df.drop(columns=existing_leakage_columns)

    return df


def save_summary(df_before, df_after):
    """Save useful summary tables for documentation."""
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)

    summary = pd.DataFrame(
        {
            "metric": [
                "rows_before_cleaning",
                "columns_before_cleaning",
                "rows_after_cleaning",
                "columns_after_cleaning",
                "retrofit_priority_count_0",
                "retrofit_priority_count_1",
                "retrofit_priority_proportion_0",
                "retrofit_priority_proportion_1",
            ],
            "value": [
                df_before.shape[0],
                df_before.shape[1],
                df_after.shape[0],
                df_after.shape[1],
                df_after["retrofit_priority"].value_counts().get(0, 0),
                df_after["retrofit_priority"].value_counts().get(1, 0),
                df_after["retrofit_priority"].value_counts(normalize=True).get(0, 0),
                df_after["retrofit_priority"].value_counts(normalize=True).get(1, 0),
            ],
        }
    )

    summary.to_csv(CLEANING_SUMMARY_FILE, index=False)

    columns_table = pd.DataFrame({"column_name": df_after.columns})
    columns_table.to_csv(MODEL_READY_COLUMNS_FILE, index=False)


def main():
    """Run the full data-cleaning pipeline."""
    print("Starting data-cleaning pipeline...")

    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Raw data file not found: {RAW_DATA_FILE}\n"
            "Check that the CSV is inside data/raw/ and that the filename is correct."
        )

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw_selected = load_selected_data(RAW_DATA_FILE)
    rows_before = raw_selected.shape[0]
    cols_before = raw_selected.shape[1]

    cleaned = clean_basic_values(raw_selected)
    cleaned = create_target(cleaned)
    cleaned = remove_leakage_columns(cleaned)


    cleaned.to_csv(MODEL_READY_DATA_FILE, index=False)

    save_summary(
    df_before=raw_selected,
    df_after=cleaned,
    )

    print("Data-cleaning pipeline complete.")
    print(f"Saved model-ready data to: {MODEL_READY_DATA_FILE}")
    print(f"Final shape: {cleaned.shape}")
    print("Target distribution:")
    print(cleaned["retrofit_priority"].value_counts(normalize=True))


if __name__ == "__main__":
    main()