
import pandas as pd

from src.etl.ingestion import map_schema_columns


def test_column_mapping():

    df = pd.DataFrame({
        "visit_id": ["1001"],
        "patient_id": ["2001"],
        "sex": ["Female"],
        "medication_count": ["12"]
    })

    mapped_df, report = map_schema_columns(df)

    assert "encounter_id" in mapped_df.columns
    assert "patient_nbr" in mapped_df.columns
    assert "gender" in mapped_df.columns
    assert "num_medications" in mapped_df.columns

    assert report["visit_id"] == "encounter_id"
    assert report["patient_id"] == "patient_nbr"
