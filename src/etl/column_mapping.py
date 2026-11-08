
import pandas as pd

COLUMN_ALIASES = {
    "patient_nbr": [
        "patient_nbr",
        "patient_id",
        "patient_number"
    ],
    "encounter_id": [
        "encounter_id",
        "visit_id",
        "encounter"
    ],
    "gender": [
        "gender",
        "sex"
    ],
    "num_medications": [
        "num_medications",
        "medication_count"
    ],
    "time_in_hospital": [
        "time_in_hospital",
        "length_of_stay"
    ]
}

REQUIRED_COLUMNS = [
    "patient_nbr",
    "encounter_id"
]


def normalize_column_name(name):
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def map_columns(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df.columns = [
        normalize_column_name(col)
        for col in df.columns
    ]

    rename_map = {}

    for canonical, aliases in COLUMN_ALIASES.items():

        matches = [
            alias for alias in aliases
            if alias in df.columns
        ]

        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous mapping for {canonical}: {matches}"
            )

        if matches:
            rename_map[matches[0]] = canonical

    df = df.rename(columns=rename_map)

    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return df
