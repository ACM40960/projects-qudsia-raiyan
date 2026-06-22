# """
# Data cleaning pipeline for the Irish BER retrofit-prioritisation project.

# This script:
# 1. Loads selected columns from the raw BER dataset.
# 2. Creates a binary retrofit_priority target.
# 3. Keeps only safe modelling features.
# 4. Cleans basic data types.
# 5. Saves a model-ready dataset to data/processed/.
# 6. Saves summary tables to results/tables/.

# Run from the project root with:

#     python src/data_cleaning.py
# """

# import pandas as pd

# from config import (
#     RAW_DATA_FILE,
#     MODEL_READY_DATA_FILE,
#     CLEANING_SUMMARY_FILE,
#     MODEL_READY_COLUMNS_FILE,
#     DATA_PROCESSED_DIR,
#     RESULTS_TABLES_DIR,
#     VALID_RATINGS,
#     PRIORITY_RATINGS,
# )


# # Candidate columns chosen from the initial inspection.
# # We avoid direct leakage columns such as BerRating and CO2Rating.
# CANDIDATE_COLUMNS = [
#     "CountyName",
#     "DwellingTypeDescr",
#     "Year_of_Construction",
#     "TypeofRating",
#     "EnergyRating",
#     "GroundFloorArea(sq m)",
#     "UValueWall",
#     "UValueRoof",
#     "UValueFloor",
#     "UValueWindow",
#     "UvalueDoor",
#     "WallArea",
#     "RoofArea",
#     "FloorArea",
#     "WindowArea",
#     "DoorArea",
#     "NoStoreys",
#     "MainSpaceHeatingFuel",
#     "MainWaterHeatingFuel",
#     "ThermalEra",
#     "GlazingPercent",
#     "Volume",
# ]


# RENAME_MAP = {
#     "CountyName": "county_name",
#     "DwellingTypeDescr": "dwelling_type",
#     "Year_of_Construction": "year_of_construction",
#     "TypeofRating": "type_of_rating",
#     "EnergyRating": "energy_rating",
#     "GroundFloorArea(sq m)": "ground_floor_area",
#     "UValueWall": "u_value_wall",
#     "UValueRoof": "u_value_roof",
#     "UValueFloor": "u_value_floor",
#     "UValueWindow": "u_value_window",
#     "UvalueDoor": "u_value_door",
#     "WallArea": "wall_area",
#     "RoofArea": "roof_area",
#     "FloorArea": "floor_area",
#     "WindowArea": "window_area",
#     "DoorArea": "door_area",
#     "NoStoreys": "no_storeys",
#     "MainSpaceHeatingFuel": "main_space_heating_fuel",
#     "MainWaterHeatingFuel": "main_water_heating_fuel",
#     "ThermalEra": "thermal_era",
#     "GlazingPercent": "glazing_percent",
#     "Volume": "volume",
# }


# NUMERIC_COLUMNS = [
#     "year_of_construction",
#     "ground_floor_area",
#     "u_value_wall",
#     "u_value_roof",
#     "u_value_floor",
#     "u_value_window",
#     "u_value_door",
#     "wall_area",
#     "roof_area",
#     "floor_area",
#     "window_area",
#     "door_area",
#     "no_storeys",
#     "glazing_percent",
#     "volume",
# ]


# CATEGORICAL_COLUMNS = [
#     "county_name",
#     "dwelling_type",
#     "type_of_rating",
#     "main_space_heating_fuel",
#     "main_water_heating_fuel",
#     "thermal_era",
# ]


# def get_available_columns(raw_path):
#     """Read only the header row and return available columns."""
#     return pd.read_csv(raw_path, nrows=0).columns.tolist()


# def load_selected_data(raw_path):
#     """Load only candidate columns that exist in the raw dataset."""
#     available_columns = get_available_columns(raw_path)

#     selected_columns = [col for col in CANDIDATE_COLUMNS if col in available_columns]
#     missing_columns = [col for col in CANDIDATE_COLUMNS if col not in available_columns]

#     if "EnergyRating" not in selected_columns:
#         raise ValueError("EnergyRating column is required to create the target variable.")

#     print(f"Selected {len(selected_columns)} columns from raw dataset.")
#     if missing_columns:
#         print("Warning: these candidate columns were not found and will be skipped:")
#         for col in missing_columns:
#             print(f"  - {col}")

#     df = pd.read_csv(raw_path, usecols=selected_columns, low_memory=False)
#     return df


# def clean_basic_values(df):
#     """Rename columns, clean strings, and convert numeric columns."""
#     df = df.rename(columns=RENAME_MAP)

#     # Strip whitespace from text columns
#     text_columns = df.select_dtypes(include=["object"]).columns
#     for col in text_columns:
#         df[col] = df[col].astype("string").str.strip()

#     # Convert numerical columns safely
#     for col in NUMERIC_COLUMNS:
#         if col in df.columns:
#             df[col] = pd.to_numeric(df[col], errors="coerce")

#         # Basic data-quality rules
#     if "year_of_construction" in df.columns:
#         invalid_years = (
#             (df["year_of_construction"] < 1700)
#             | (df["year_of_construction"] > 2023)
#         )
#         df.loc[invalid_years, "year_of_construction"] = pd.NA
#         df["building_age"] = 2023 - df["year_of_construction"]

#     # Replace impossible non-positive physical measurements with missing values
#     physical_measurement_columns = [
#         "ground_floor_area",
#         "wall_area",
#         "roof_area",
#         "floor_area",
#         "window_area",
#         "door_area",
#         "volume",
#     ]

#     for col in physical_measurement_columns:
#         if col in df.columns:
#             df.loc[df[col] <= 0, col] = pd.NA

#     return df


# def create_target(df):
#     """Create binary retrofit_priority target from BER energy rating."""
#     df = df.copy()

#     # Keep only valid BER labels
#     df = df[df["energy_rating"].isin(VALID_RATINGS)].copy()

#     # 1 = retrofit priority, 0 = not retrofit priority
#     df["retrofit_priority"] = df["energy_rating"].isin(PRIORITY_RATINGS).astype(int)

#     return df


# def remove_leakage_columns(df):
#     """
#     Remove columns that directly reveal the target.

#     energy_rating is used only to create retrofit_priority, so it is removed
#     before modelling.
#     """
#     leakage_columns = ["energy_rating"]

#     existing_leakage_columns = [col for col in leakage_columns if col in df.columns]
#     df = df.drop(columns=existing_leakage_columns)

#     return df


# def save_summary(df_before, df_after):
#     """Save useful summary tables for documentation."""
#     RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)

#     summary = pd.DataFrame(
#         {
#             "metric": [
#                 "rows_before_cleaning",
#                 "columns_before_cleaning",
#                 "rows_after_cleaning",
#                 "columns_after_cleaning",
#                 "retrofit_priority_count_0",
#                 "retrofit_priority_count_1",
#                 "retrofit_priority_proportion_0",
#                 "retrofit_priority_proportion_1",
#             ],
#             "value": [
#                 df_before.shape[0],
#                 df_before.shape[1],
#                 df_after.shape[0],
#                 df_after.shape[1],
#                 df_after["retrofit_priority"].value_counts().get(0, 0),
#                 df_after["retrofit_priority"].value_counts().get(1, 0),
#                 df_after["retrofit_priority"].value_counts(normalize=True).get(0, 0),
#                 df_after["retrofit_priority"].value_counts(normalize=True).get(1, 0),
#             ],
#         }
#     )

#     summary.to_csv(CLEANING_SUMMARY_FILE, index=False)

#     columns_table = pd.DataFrame({"column_name": df_after.columns})
#     columns_table.to_csv(MODEL_READY_COLUMNS_FILE, index=False)


# def main():
#     """Run the full data-cleaning pipeline."""
#     print("Starting data-cleaning pipeline...")

#     if not RAW_DATA_FILE.exists():
#         raise FileNotFoundError(
#             f"Raw data file not found: {RAW_DATA_FILE}\n"
#             "Check that the CSV is inside data/raw/ and that the filename is correct."
#         )

#     DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

#     raw_selected = load_selected_data(RAW_DATA_FILE)
#     rows_before = raw_selected.shape[0]
#     cols_before = raw_selected.shape[1]

#     cleaned = clean_basic_values(raw_selected)
#     cleaned = create_target(cleaned)
#     cleaned = remove_leakage_columns(cleaned)


#     cleaned.to_csv(MODEL_READY_DATA_FILE, index=False)

#     save_summary(
#     df_before=raw_selected,
#     df_after=cleaned,
#     )

#     print("Data-cleaning pipeline complete.")
#     print(f"Saved model-ready data to: {MODEL_READY_DATA_FILE}")
#     print(f"Final shape: {cleaned.shape}")
#     print("Target distribution:")
#     print(cleaned["retrofit_priority"].value_counts(normalize=True))


# if __name__ == "__main__":
#     main()


"""
Data cleaning pipeline for the Irish BER retrofit-prioritisation project.

This script:
1. Loads selected columns from the raw BER dataset.
2. Handles placeholder missing values.
3. Applies data-quality checks to physically meaningful variables.
4. Creates a binary retrofit_priority target.
5. Removes target-leakage columns from the modelling dataset.
6. Saves a model-ready dataset to data/processed/.
7. Saves cleaning, leakage, and feature-rationale audit tables.

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
    ASSESSMENT_YEAR,
    MIN_CONSTRUCTION_YEAR,
    DATA_QUALITY_AUDIT_FILE,
    LEAKAGE_AUDIT_FILE,
    SELECTED_FEATURES_RATIONALE_FILE,
    MISSINGNESS_AFTER_CLEANING_FILE,
)


# Candidate columns selected after initial dataset inspection.
# Direct BER output columns such as BerRating and CO2Rating are intentionally excluded.
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


PLACEHOLDER_MISSING_VALUES = {
    "",
    "nan",
    "na",
    "n/a",
    "none",
    "null",
    "missing",
    "not available",
    "unknown",
}


# Columns deliberately excluded from modelling due to leakage risk.
LEAKAGE_AUDIT_ROWS = [
    {
        "column_name": "EnergyRating",
        "decision": "target source only",
        "reason": "Used to define the binary retrofit_priority target, then removed from predictors.",
    },
    {
        "column_name": "BerRating",
        "decision": "dropped",
        "reason": "Numerical BER score closely determines the BER band; using it would create target leakage.",
    },
    {
        "column_name": "CO2Rating",
        "decision": "dropped",
        "reason": "BER-related assessment output closely linked to dwelling energy performance.",
    },
    {
        "column_name": "TotalCO2Emissions",
        "decision": "dropped",
        "reason": "Calculated assessment output; may reveal final BER performance rather than independent dwelling characteristics.",
    },
    {
        "column_name": "TotalPrimaryEnergyFact",
        "decision": "dropped",
        "reason": "Calculated energy-performance output; high leakage risk for BER-derived target.",
    },
    {
        "column_name": "MPCDERValue",
        "decision": "dropped",
        "reason": "Derived assessment value; high leakage risk.",
    },
    {
        "column_name": "EPCDERValue",
        "decision": "dropped",
        "reason": "Derived assessment value; high leakage risk.",
    },
]


FEATURE_RATIONALE_ROWS = [
    {
        "feature": "county_name",
        "decision": "kept",
        "feature_type": "categorical",
        "reason": "Geographical/contextual variable; not a direct BER output.",
    },
    {
        "feature": "dwelling_type",
        "decision": "kept",
        "feature_type": "categorical",
        "reason": "Physical dwelling category that may influence energy performance.",
    },
    {
        "feature": "year_of_construction",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Construction period is strongly linked to building standards and thermal performance.",
    },
    {
        "feature": "type_of_rating",
        "decision": "kept",
        "feature_type": "categorical",
        "reason": "Rating type gives assessment context and is not itself the BER outcome.",
    },
    {
        "feature": "ground_floor_area",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Dwelling size affects heat demand and energy performance.",
    },
    {
        "feature": "u_value_wall",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Wall U-value measures thermal transmittance and heat-loss performance.",
    },
    {
        "feature": "u_value_roof",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Roof U-value measures roof/attic heat-loss performance.",
    },
    {
        "feature": "u_value_floor",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Floor U-value measures thermal performance of the floor.",
    },
    {
        "feature": "u_value_window",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Window U-value captures glazing heat-loss performance.",
    },
    {
        "feature": "u_value_door",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Door U-value captures heat-loss performance through doors.",
    },
    {
        "feature": "wall_area",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Building-envelope area affects total heat loss.",
    },
    {
        "feature": "roof_area",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Roof area affects potential heat loss through the roof.",
    },
    {
        "feature": "floor_area",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Floor area is a physical dwelling-size variable.",
    },
    {
        "feature": "window_area",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Window area affects heat loss and solar gain.",
    },
    {
        "feature": "door_area",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Door area contributes to envelope heat-loss characteristics.",
    },
    {
        "feature": "no_storeys",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Number of storeys describes building form.",
    },
    {
        "feature": "main_space_heating_fuel",
        "decision": "kept",
        "feature_type": "categorical",
        "reason": "Heating fuel type is relevant to energy performance and retrofit need.",
    },
    {
        "feature": "main_water_heating_fuel",
        "decision": "kept",
        "feature_type": "categorical",
        "reason": "Water-heating fuel type is relevant to dwelling energy performance.",
    },
    {
        "feature": "thermal_era",
        "decision": "kept",
        "feature_type": "categorical",
        "reason": "Construction-era grouping helps represent building-standard period.",
    },
    {
        "feature": "glazing_percent",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Glazing proportion affects heat loss and building-envelope performance.",
    },
    {
        "feature": "volume",
        "decision": "kept",
        "feature_type": "numeric",
        "reason": "Building volume affects heating demand.",
    },
    {
        "feature": "building_age",
        "decision": "not used",
        "feature_type": "derived numeric",
        "reason": "Redundant with year_of_construction, so it is not included in the modelling dataset.",
    },
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

    return df, available_columns, selected_columns, missing_columns


def replace_placeholder_missing_values(df):
    """Replace placeholder text values with proper missing values."""
    audit_rows = []
    total_placeholders_replaced = 0

    text_columns = df.select_dtypes(include=["object", "string"]).columns

    for col in text_columns:
        values = df[col].astype("string").str.strip()
        placeholder_mask = values.str.lower().isin(PLACEHOLDER_MISSING_VALUES).fillna(False)

        count = int(placeholder_mask.sum())
        total_placeholders_replaced += count

        df[col] = values
        df.loc[placeholder_mask, col] = pd.NA

        if count > 0:
            audit_rows.append(
                {
                    "check": f"placeholder_missing_values_in_{col}",
                    "affected_values": count,
                    "action": "Converted placeholder text values to missing values.",
                }
            )

    audit_rows.append(
        {
            "check": "total_placeholder_missing_values",
            "affected_values": total_placeholders_replaced,
            "action": "Converted placeholder text values such as nan, NA, None and blank strings to missing values.",
        }
    )

    return df, audit_rows


def convert_numeric_columns(df):
    """Convert expected numeric columns safely."""
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def apply_data_quality_rules(df):
    """Apply conservative physical/data-quality rules and record affected values."""
    audit_rows = []

    if "year_of_construction" in df.columns:
        invalid_year_mask = (
            (df["year_of_construction"] < MIN_CONSTRUCTION_YEAR)
            | (df["year_of_construction"] > ASSESSMENT_YEAR)
        )

        count = int(invalid_year_mask.sum())
        df.loc[invalid_year_mask, "year_of_construction"] = pd.NA

        audit_rows.append(
            {
                "check": "invalid_year_of_construction",
                "affected_values": count,
                "action": f"Set years before {MIN_CONSTRUCTION_YEAR} or after {ASSESSMENT_YEAR} to missing.",
            }
        )

    u_value_columns = [
        "u_value_wall",
        "u_value_roof",
        "u_value_floor",
        "u_value_window",
        "u_value_door",
    ]

    for col in u_value_columns:
        if col in df.columns:
            invalid_mask = (df[col] <= 0) | (df[col] > 10)
            count = int(invalid_mask.sum())
            df.loc[invalid_mask, col] = pd.NA

            audit_rows.append(
                {
                    "check": f"invalid_{col}",
                    "affected_values": count,
                    "action": "Set non-positive or unrealistically high U-values above 10 to missing.",
                }
            )

    if "ground_floor_area" in df.columns:
        invalid_mask = (df["ground_floor_area"] <= 0) | (df["ground_floor_area"] > 1000)
        count = int(invalid_mask.sum())
        df.loc[invalid_mask, "ground_floor_area"] = pd.NA

        audit_rows.append(
            {
                "check": "invalid_ground_floor_area",
                "affected_values": count,
                "action": "Set non-positive or extremely large ground floor areas above 1000 sq m to missing.",
            }
        )

    area_columns = [
        "wall_area",
        "roof_area",
        "floor_area",
        "window_area",
        "door_area",
    ]

    for col in area_columns:
        if col in df.columns:
            invalid_mask = (df[col] < 0) | (df[col] > 5000)
            count = int(invalid_mask.sum())
            df.loc[invalid_mask, col] = pd.NA

            audit_rows.append(
                {
                    "check": f"invalid_{col}",
                    "affected_values": count,
                    "action": "Set negative or extremely large area values above 5000 to missing.",
                }
            )

    if "no_storeys" in df.columns:
        invalid_mask = (df["no_storeys"] <= 0) | (df["no_storeys"] > 20)
        count = int(invalid_mask.sum())
        df.loc[invalid_mask, "no_storeys"] = pd.NA

        audit_rows.append(
            {
                "check": "invalid_no_storeys",
                "affected_values": count,
                "action": "Set non-positive or extremely high storey counts above 20 to missing.",
            }
        )

    if "glazing_percent" in df.columns:
        invalid_mask = (df["glazing_percent"] < 0) | (df["glazing_percent"] > 100)
        count = int(invalid_mask.sum())
        df.loc[invalid_mask, "glazing_percent"] = pd.NA

        audit_rows.append(
            {
                "check": "invalid_glazing_percent",
                "affected_values": count,
                "action": "Set glazing percentages outside the 0 to 100 range to missing.",
            }
        )

    if "volume" in df.columns:
        invalid_mask = (df["volume"] <= 0) | (df["volume"] > 10000)
        count = int(invalid_mask.sum())
        df.loc[invalid_mask, "volume"] = pd.NA

        audit_rows.append(
            {
                "check": "invalid_volume",
                "affected_values": count,
                "action": "Set non-positive or extremely large volume values above 10000 to missing.",
            }
        )

    return df, audit_rows


def clean_basic_values(df):
    """Rename columns, clean strings, convert numerics, and apply quality rules."""
    df = df.rename(columns=RENAME_MAP)

    df, placeholder_audit = replace_placeholder_missing_values(df)
    df = convert_numeric_columns(df)
    df, quality_audit = apply_data_quality_rules(df)

    audit_rows = placeholder_audit + quality_audit

    return df, audit_rows


def create_target(df):
    """Create binary retrofit_priority target from BER energy rating."""
    df = df.copy()

    valid_rating_mask = df["energy_rating"].isin(VALID_RATINGS)
    invalid_rating_count = int((~valid_rating_mask).sum())

    df = df[valid_rating_mask].copy()

    # 1 = retrofit priority, 0 = not retrofit priority
    df["retrofit_priority"] = df["energy_rating"].isin(PRIORITY_RATINGS).astype(int)

    return df, invalid_rating_count


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


def save_cleaning_summary(df_before, df_after):
    """Save high-level cleaning summary."""
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


def save_model_ready_columns(df_after):
    """Save final modelling columns."""
    columns_table = pd.DataFrame({"column_name": df_after.columns})
    columns_table.to_csv(MODEL_READY_COLUMNS_FILE, index=False)


def save_data_quality_audit(audit_rows, invalid_rating_count):
    """Save detailed data-quality audit table."""
    audit_rows = audit_rows.copy()

    audit_rows.append(
        {
            "check": "invalid_or_missing_energy_rating",
            "affected_values": invalid_rating_count,
            "action": "Dropped rows without a valid BER rating because target creation requires EnergyRating.",
        }
    )

    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(DATA_QUALITY_AUDIT_FILE, index=False)


def save_leakage_audit(available_columns):
    """Save leakage audit table documenting excluded target-related columns."""
    leakage_df = pd.DataFrame(LEAKAGE_AUDIT_ROWS)
    leakage_df["available_in_raw_dataset"] = leakage_df["column_name"].isin(available_columns)
    leakage_df.to_csv(LEAKAGE_AUDIT_FILE, index=False)


def save_feature_rationale(final_columns):
    """Save selected-features rationale table."""
    rationale_df = pd.DataFrame(FEATURE_RATIONALE_ROWS)

    model_feature_columns = set(final_columns) - {"retrofit_priority"}

    rationale_df["included_in_model_ready_data"] = rationale_df["feature"].isin(
        model_feature_columns
    )

    rationale_df.to_csv(SELECTED_FEATURES_RATIONALE_FILE, index=False)


def save_missingness_after_cleaning(df_after):
    """Save missingness fraction for final model-ready dataset."""
    missingness = df_after.isna().mean().sort_values(ascending=False)
    missingness.to_csv(MISSINGNESS_AFTER_CLEANING_FILE)


def save_all_outputs(df_before, df_after, audit_rows, invalid_rating_count, available_columns):
    """Save all cleaning-related outputs."""
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)

    save_cleaning_summary(df_before, df_after)
    save_model_ready_columns(df_after)
    save_data_quality_audit(audit_rows, invalid_rating_count)
    save_leakage_audit(available_columns)
    save_feature_rationale(df_after.columns.tolist())
    save_missingness_after_cleaning(df_after)


def main():
    """Run the full data-cleaning pipeline."""
    print("Starting data-cleaning pipeline...")

    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Raw data file not found: {RAW_DATA_FILE}\n"
            "Check that the CSV is inside data/raw/ and that the filename is correct."
        )

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_TABLES_DIR.mkdir(parents=True, exist_ok=True)

    raw_selected, available_columns, selected_columns, missing_columns = load_selected_data(
        RAW_DATA_FILE
    )

    cleaned, audit_rows = clean_basic_values(raw_selected)
    cleaned, invalid_rating_count = create_target(cleaned)
    cleaned = remove_leakage_columns(cleaned)

    cleaned.to_csv(MODEL_READY_DATA_FILE, index=False)

    save_all_outputs(
        df_before=raw_selected,
        df_after=cleaned,
        audit_rows=audit_rows,
        invalid_rating_count=invalid_rating_count,
        available_columns=available_columns,
    )

    print("Data-cleaning pipeline complete.")
    print(f"Saved model-ready data to: {MODEL_READY_DATA_FILE}")
    print(f"Final shape: {cleaned.shape}")
    print("Target distribution:")
    print(cleaned["retrofit_priority"].value_counts(normalize=True))
    print(f"Cleaning summary saved to: {CLEANING_SUMMARY_FILE}")
    print(f"Data-quality audit saved to: {DATA_QUALITY_AUDIT_FILE}")
    print(f"Leakage audit saved to: {LEAKAGE_AUDIT_FILE}")
    print(f"Feature rationale saved to: {SELECTED_FEATURES_RATIONALE_FILE}")


if __name__ == "__main__":
    main()